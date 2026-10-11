"""Wake acotado de Ventas Cerradas para el runtime Preview.

Contrato:
- solo PREVIEW + PREVIEW_WEB;
- respeta el flag existente de sync_comercial_v2;
- respeta la pausa administrativa persistente;
- usa la cadencia canonica existente (default 900 s);
- obtiene un owner distribuido para evitar ejecuciones por replica;
- invoca el wrapper canonico SchedulerManager.run_job_now(JOB_ID);
- no modifica ni reimplementa sync_comercial_v2_job.py;
- usa un owner/lock distinto al wake de Ventas del Dia;
- nunca es elegible en Produccion.

Este wake existe porque PREVIEW_WEB no es propietario de APScheduler por
politica de runtime. Reactiva exclusivamente el job comercial incremental sin
volver a encender el scheduler embebido completo y sin crear un segundo owner
para sync_comercial_abiertas_v2.
"""

from __future__ import annotations

import asyncio
import logging
import os
import socket
from typing import Any, Dict, Optional

from modules.scheduler_runtime.policy import (
    PREVIEW_WEB,
    runtime_environment,
    runtime_role,
)


logger = logging.getLogger(__name__)

JOB_ID = "sync_comercial_v2"
OWNER_LOCK_ID = "preview_sync_comercial_v2_wake_owner"
JOB_ENABLED_ENV = "SCHEDULER_SYNC_COMERCIAL_V2_ENABLED"
INTERVAL_ENV = "SCHEDULER_SYNC_COMERCIAL_V2_INTERVAL_SECONDS"

DEFAULT_INTERVAL_SECONDS = 900
MIN_INTERVAL_SECONDS = 60

OWNER_LEASE_SECONDS = 120
OWNER_HEARTBEAT_SECONDS = 30
OWNER_RETRY_SECONDS = 30

_wake_task: Optional[asyncio.Task] = None


def _truthy(name: str, default: str = "false") -> bool:
    return str(os.environ.get(name, default)).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _process_identity() -> str:
    return f"{socket.gethostname()}:{os.getpid()}"


def wake_interval_seconds() -> int:
    raw = str(
        os.environ.get(
            INTERVAL_ENV,
            str(DEFAULT_INTERVAL_SECONDS),
        )
    ).strip()

    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = DEFAULT_INTERVAL_SECONDS

    return max(MIN_INTERVAL_SECONDS, value)


def preview_closed_sales_wake_eligible() -> bool:
    """Preview web es el unico runtime autorizado para este wake."""
    try:
        return (
            runtime_environment() == "PREVIEW"
            and runtime_role() == PREVIEW_WEB
            and _truthy(JOB_ENABLED_ENV, "true")
        )
    except RuntimeError:
        return False


def _administratively_paused() -> bool:
    """Respeta la pausa persistente; ante error, falla cerrado."""
    try:
        from core.scheduler.persistent_state_repository import (
            SchedulerPersistentStateRepository,
        )

        paused = {
            str(value).strip()
            for value in SchedulerPersistentStateRepository.get_paused_job_ids()
        }
        return JOB_ID in paused
    except Exception:
        logger.exception(
            "Preview Ventas Cerradas no pudo validar pausa administrativa "
            "job=%s; se omite tick por fail-closed",
            JOB_ID,
        )
        return True


async def _run_once(db) -> Dict[str, Any]:
    from core.scheduler import get_scheduler_manager

    manager = get_scheduler_manager(db)
    return await manager.run_job_now(JOB_ID)


async def _try_acquire_owner_lock():
    from core.scheduler.locks import get_lock_manager

    lock = get_lock_manager().get_lock(OWNER_LOCK_ID)
    acquired = await lock.acquire(
        timeout_seconds=OWNER_LEASE_SECONDS,
    )

    if not acquired:
        return None

    await lock.start_heartbeat_loop(
        interval_seconds=OWNER_HEARTBEAT_SECONDS,
        extend_seconds=OWNER_LEASE_SECONDS,
    )
    return lock


async def _run_as_owner(db, owner_lock, interval: int, owner: str) -> None:
    """Ejecuta al adquirir ownership y luego cada intervalo canonico."""
    loop = asyncio.get_running_loop()
    next_tick = loop.time()

    logger.warning(
        "Preview Ventas Cerradas owner acquired job=%s owner=%s interval=%ss",
        JOB_ID,
        owner,
        interval,
    )

    while True:
        if not preview_closed_sales_wake_eligible():
            return

        delay = max(0.0, next_tick - loop.time())
        await asyncio.sleep(delay)

        if not getattr(owner_lock, "_locked", False):
            logger.warning(
                "Preview Ventas Cerradas owner lease lost job=%s owner=%s",
                JOB_ID,
                owner,
            )
            return

        if not preview_closed_sales_wake_eligible():
            return

        if _administratively_paused():
            logger.warning(
                "Preview Ventas Cerradas tick omitido job=%s owner=%s "
                "reason=administrative_pause_or_pause_state_unavailable",
                JOB_ID,
                owner,
            )
        else:
            logger.warning(
                "Preview Ventas Cerradas tick job=%s owner=%s",
                JOB_ID,
                owner,
            )

            try:
                result = await _run_once(db)
                logger.warning(
                    "Preview Ventas Cerradas call completed "
                    "job=%s status=%s owner=%s",
                    JOB_ID,
                    result.get("status"),
                    owner,
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "Preview Ventas Cerradas call failed job=%s owner=%s",
                    JOB_ID,
                    owner,
                )

        next_tick += interval
        now = loop.time()
        if next_tick <= now:
            missed = int((now - next_tick) // interval) + 1
            next_tick += missed * interval
            logger.warning(
                "Preview Ventas Cerradas coalesced missed_ticks=%s "
                "job=%s owner=%s",
                missed,
                JOB_ID,
                owner,
            )


async def _wake_loop(db) -> None:
    interval = wake_interval_seconds()
    owner = _process_identity()
    standby_logged = False

    logger.warning(
        "Preview Ventas Cerradas wake started job=%s interval=%ss process=%s",
        JOB_ID,
        interval,
        owner,
    )

    try:
        while preview_closed_sales_wake_eligible():
            try:
                owner_lock = await _try_acquire_owner_lock()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "Preview Ventas Cerradas owner acquisition failed "
                    "job=%s process=%s",
                    JOB_ID,
                    owner,
                )
                owner_lock = None

            if owner_lock is None:
                if not standby_logged:
                    logger.warning(
                        "Preview Ventas Cerradas standby job=%s process=%s "
                        "reason=owner_exists",
                        JOB_ID,
                        owner,
                    )
                    standby_logged = True
                await asyncio.sleep(OWNER_RETRY_SECONDS)
                continue

            standby_logged = False
            try:
                await _run_as_owner(
                    db=db,
                    owner_lock=owner_lock,
                    interval=interval,
                    owner=owner,
                )
            finally:
                try:
                    await owner_lock.release()
                except Exception:
                    logger.exception(
                        "Preview Ventas Cerradas owner release failed "
                        "job=%s process=%s",
                        JOB_ID,
                        owner,
                    )

            if preview_closed_sales_wake_eligible():
                await asyncio.sleep(OWNER_RETRY_SECONDS)

    except asyncio.CancelledError:
        logger.info(
            "Preview Ventas Cerradas wake cancelled job=%s process=%s",
            JOB_ID,
            owner,
        )
        raise


def start_preview_closed_sales_wake(db) -> Dict[str, Any]:
    """Inicia una sola tarea por proceso y solo en PREVIEW_WEB."""
    global _wake_task

    if not preview_closed_sales_wake_eligible():
        return {
            "started": False,
            "reason": "not_preview_web_or_job_disabled",
            "job_id": JOB_ID,
        }

    if _wake_task is not None and not _wake_task.done():
        return {
            "started": False,
            "reason": "already_running",
            "job_id": JOB_ID,
            "interval_seconds": wake_interval_seconds(),
            "process": _process_identity(),
        }

    _wake_task = asyncio.create_task(
        _wake_loop(db),
        name="edarsahub-preview-ventas-cerradas-wake",
    )

    return {
        "started": True,
        "reason": "started",
        "job_id": JOB_ID,
        "interval_seconds": wake_interval_seconds(),
        "process": _process_identity(),
    }


async def stop_preview_closed_sales_wake() -> Dict[str, Any]:
    """Cancela limpiamente la tarea local del wake de Preview."""
    global _wake_task

    task = _wake_task
    _wake_task = None

    if task is None:
        return {
            "stopped": False,
            "reason": "not_running",
            "job_id": JOB_ID,
        }

    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass

    return {
        "stopped": True,
        "reason": "stopped",
        "job_id": JOB_ID,
    }


def preview_closed_sales_wake_status() -> Dict[str, Any]:
    """Estado local para diagnostico, sin exponer secretos."""
    task = _wake_task
    return {
        "job_id": JOB_ID,
        "eligible": preview_closed_sales_wake_eligible(),
        "running": task is not None and not task.done(),
        "interval_seconds": wake_interval_seconds(),
        "process": _process_identity(),
    }
