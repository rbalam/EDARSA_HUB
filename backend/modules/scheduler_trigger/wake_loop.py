"""Wake productivo de Ventas del Dia para PRODUCTION_WEB.

Contrato:
- solo PRODUCTION + PRODUCTION_WEB;
- usa el feature flag del trigger productivo y el flag del job;
- respeta la cadencia canonica existente;
- adquiere un owner lock distribuido para evitar ejecucion por replica;
- invoca exclusivamente SchedulerManager.run_job_now(JOB_ID);
- no importa ni modifica directamente el job protegido;
- apagado limpio y fail-closed fuera del runtime autorizado.
"""

from __future__ import annotations

import asyncio
import logging
import os
import socket
from typing import Any, Dict, Optional

from modules.scheduler_runtime.policy import (
    PRODUCTION_WEB,
    runtime_environment,
    runtime_role,
)


logger = logging.getLogger(__name__)

JOB_ID = "sync_comercial_abiertas_v2"
OWNER_LOCK_ID = "sync_comercial_abiertas_v2_wake_owner"
TRIGGER_ENABLED_ENV = "EDARSA_SCHEDULER_TRIGGER_ENABLED"
JOB_ENABLED_ENV = "SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_ENABLED"
INTERVAL_ENV = "SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_INTERVAL_SECONDS"

DEFAULT_INTERVAL_SECONDS = 300
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


def production_wake_eligible() -> bool:
    try:
        return (
            runtime_environment() == "PRODUCTION"
            and runtime_role() == PRODUCTION_WEB
            and _truthy(TRIGGER_ENABLED_ENV)
            and _truthy(JOB_ENABLED_ENV, "true")
        )
    except RuntimeError:
        return False


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
    loop = asyncio.get_running_loop()
    next_tick = loop.time() + interval

    logger.warning(
        "Production Ventas del Dia wake owner acquired "
        "job=%s owner=%s interval=%ss",
        JOB_ID,
        owner,
        interval,
    )

    while True:
        if not production_wake_eligible():
            return

        delay = max(0.0, next_tick - loop.time())
        await asyncio.sleep(delay)

        if not getattr(owner_lock, "_locked", False):
            logger.warning(
                "Production Ventas del Dia wake owner lease lost "
                "job=%s owner=%s",
                JOB_ID,
                owner,
            )
            return

        if not production_wake_eligible():
            return

        try:
            result = await _run_once(db)
            logger.warning(
                "Production Ventas del Dia wake completed "
                "job=%s status=%s owner=%s",
                JOB_ID,
                result.get("status"),
                owner,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "Production Ventas del Dia wake failed "
                "job=%s owner=%s",
                JOB_ID,
                owner,
            )

        next_tick += interval
        now = loop.time()
        if next_tick <= now:
            missed = int((now - next_tick) // interval) + 1
            next_tick += missed * interval
            logger.warning(
                "Production Ventas del Dia wake coalesced "
                "missed_ticks=%s job=%s owner=%s",
                missed,
                JOB_ID,
                owner,
            )


async def _wake_loop(db) -> None:
    interval = wake_interval_seconds()
    owner = _process_identity()
    standby_logged = False

    logger.warning(
        "Production Ventas del Dia wake started "
        "job=%s interval=%ss process=%s",
        JOB_ID,
        interval,
        owner,
    )

    try:
        while production_wake_eligible():
            try:
                owner_lock = await _try_acquire_owner_lock()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "Production Ventas del Dia owner acquisition failed "
                    "job=%s process=%s",
                    JOB_ID,
                    owner,
                )
                owner_lock = None

            if owner_lock is None:
                if not standby_logged:
                    logger.warning(
                        "Production Ventas del Dia wake standby "
                        "job=%s process=%s reason=owner_exists",
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
                        "Production Ventas del Dia owner release failed "
                        "job=%s process=%s",
                        JOB_ID,
                        owner,
                    )

            if production_wake_eligible():
                await asyncio.sleep(OWNER_RETRY_SECONDS)

    except asyncio.CancelledError:
        logger.info(
            "Production Ventas del Dia wake cancelled "
            "job=%s process=%s",
            JOB_ID,
            owner,
        )
        raise


def start_production_sales_wake(db) -> Dict[str, Any]:
    global _wake_task

    if not production_wake_eligible():
        return {
            "started": False,
            "reason": "not_production_web_or_disabled",
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
        name="edarsahub-production-ventas-dia-wake",
    )

    return {
        "started": True,
        "reason": "started",
        "job_id": JOB_ID,
        "interval_seconds": wake_interval_seconds(),
        "process": _process_identity(),
    }


async def stop_production_sales_wake() -> Dict[str, Any]:
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
