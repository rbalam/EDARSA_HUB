"""Wake loop productivo para Ventas del Dia.

Este modulo NO contiene ni duplica la logica de negocio de
sync_comercial_abiertas_v2. Solo despierta periodicamente el
SchedulerManager canonico dentro del backend Live de Produccion.

Reglas:
- solo PRODUCTION + PRODUCTION_WEB;
- usa el mismo feature flag del trigger productivo;
- respeta el intervalo canonico del job (default 300 s);
- una sola replica obtiene el lease distribuido de ownership;
- replicas adicionales permanecen en standby y pueden tomar ownership;
- invoca exclusivamente SchedulerManager.run_job_now(JOB_ID);
- el lock de ejecucion y la bitacora siguen en el wrapper canonico;
- apagado limpio y sin tocar el job protegido.
"""

from __future__ import annotations

import asyncio
import logging
import os
import socket
from typing import Any, Dict, Optional

from modules.scheduler_runtime.policy import (
    runtime_environment,
    runtime_role,
)


logger = logging.getLogger(__name__)

JOB_ID = "sync_comercial_abiertas_v2"
WAKE_OWNER_LOCK_ID = "sync_comercial_abiertas_v2_wake_owner"
TRIGGER_ENABLED_ENV = "EDARSA_SCHEDULER_TRIGGER_ENABLED"
JOB_ENABLED_ENV = "SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_ENABLED"
INTERVAL_ENV = "SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_INTERVAL_SECONDS"
DEFAULT_INTERVAL_SECONDS = 300
MIN_INTERVAL_SECONDS = 60

# Lease corto con heartbeat: una replica activa y failover razonable.
WAKE_OWNER_LEASE_SECONDS = 120
WAKE_OWNER_HEARTBEAT_SECONDS = 30
WAKE_OWNER_RETRY_SECONDS = 30

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
        logger.warning(
            "Invalid %s=%r; using %ss",
            INTERVAL_ENV,
            raw,
            DEFAULT_INTERVAL_SECONDS,
        )
        return DEFAULT_INTERVAL_SECONDS

    return max(MIN_INTERVAL_SECONDS, value)


def internal_wake_eligible() -> bool:
    """Fail closed fuera del runtime web productivo autorizado."""
    if runtime_environment() != "PRODUCTION":
        return False

    if runtime_role() != "PRODUCTION_WEB":
        return False

    if not _truthy(TRIGGER_ENABLED_ENV):
        return False

    if not _truthy(JOB_ENABLED_ENV, "true"):
        return False

    return True


async def _run_once() -> Dict[str, Any]:
    """Invoca exclusivamente el SchedulerManager canonico."""
    from core.scheduler.scheduler_manager import get_scheduler_manager

    manager = get_scheduler_manager()
    return await manager.run_job_now(JOB_ID)


async def _try_acquire_owner_lock():
    """Intenta ownership global del wake sin bloquear otra replica."""
    from core.scheduler.locks import get_lock_manager

    lock = get_lock_manager().get_lock(WAKE_OWNER_LOCK_ID)
    acquired = await lock.acquire(
        timeout_seconds=WAKE_OWNER_LEASE_SECONDS,
    )
    if not acquired:
        return None

    await lock.start_heartbeat_loop(
        interval_seconds=WAKE_OWNER_HEARTBEAT_SECONDS,
        extend_seconds=WAKE_OWNER_LEASE_SECONDS,
    )
    return lock


async def _run_as_owner(owner_lock, interval: int, owner: str) -> None:
    """Ejecuta ticks a cadencia fija mientras conserve ownership."""
    loop = asyncio.get_running_loop()
    next_tick = loop.time() + interval

    logger.warning(
        "Production internal wake owner acquired job=%s "
        "owner=%s lease=%ss heartbeat=%ss",
        JOB_ID,
        owner,
        WAKE_OWNER_LEASE_SECONDS,
        WAKE_OWNER_HEARTBEAT_SECONDS,
    )

    while True:
        if not internal_wake_eligible():
            return

        delay = max(0.0, next_tick - loop.time())
        await asyncio.sleep(delay)

        # El heartbeat marca _locked=False si el lease se pierde.
        if not getattr(owner_lock, "_locked", False):
            logger.warning(
                "Production internal wake owner lease lost "
                "job=%s owner=%s",
                JOB_ID,
                owner,
            )
            return

        if not internal_wake_eligible():
            return

        logger.warning(
            "Production internal wake tick job=%s owner=%s",
            JOB_ID,
            owner,
        )

        try:
            result = await _run_once()
            logger.warning(
                "Production internal wake completed "
                "job=%s status=%s owner=%s",
                JOB_ID,
                result.get("status"),
                owner,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "Production internal wake failed job=%s owner=%s",
                JOB_ID,
                owner,
            )

        # Cadencia de inicio cada N segundos. Si una ejecucion supera el
        # intervalo, coalesce: no dispara una rafaga para recuperar ticks.
        next_tick += interval
        now = loop.time()
        if next_tick <= now:
            missed = int((now - next_tick) // interval) + 1
            next_tick += missed * interval
            logger.warning(
                "Production internal wake coalesced missed_ticks=%s "
                "job=%s owner=%s",
                missed,
                JOB_ID,
                owner,
            )


async def _wake_loop() -> None:
    interval = wake_interval_seconds()
    owner = _process_identity()
    standby_logged = False

    logger.warning(
        "Production internal wake loop started "
        "job=%s interval=%ss process=%s",
        JOB_ID,
        interval,
        owner,
    )

    try:
        while True:
            if not internal_wake_eligible():
                logger.warning(
                    "Production internal wake loop stopped by policy "
                    "environment=%s role=%s trigger_enabled=%s "
                    "job_enabled=%s process=%s",
                    runtime_environment(),
                    runtime_role(),
                    _truthy(TRIGGER_ENABLED_ENV),
                    _truthy(JOB_ENABLED_ENV, "true"),
                    owner,
                )
                return

            try:
                owner_lock = await _try_acquire_owner_lock()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "Production internal wake owner acquisition failed "
                    "job=%s process=%s",
                    JOB_ID,
                    owner,
                )
                owner_lock = None

            if owner_lock is None:
                if not standby_logged:
                    logger.warning(
                        "Production internal wake standby "
                        "job=%s process=%s reason=owner_exists",
                        JOB_ID,
                        owner,
                    )
                    standby_logged = True
                await asyncio.sleep(WAKE_OWNER_RETRY_SECONDS)
                continue

            standby_logged = False
            try:
                await _run_as_owner(
                    owner_lock=owner_lock,
                    interval=interval,
                    owner=owner,
                )
            finally:
                try:
                    await owner_lock.release()
                except Exception:
                    logger.exception(
                        "Production internal wake owner release failed "
                        "job=%s process=%s",
                        JOB_ID,
                        owner,
                    )

            await asyncio.sleep(WAKE_OWNER_RETRY_SECONDS)

    except asyncio.CancelledError:
        logger.info(
            "Production internal wake loop cancelled "
            "job=%s process=%s",
            JOB_ID,
            owner,
        )
        raise


def start_internal_wake_loop() -> Dict[str, Any]:
    """Inicia una sola tarea asyncio por proceso."""
    global _wake_task

    if not internal_wake_eligible():
        return {
            "started": False,
            "reason": "policy",
            "environment": runtime_environment(),
            "runtime_role": runtime_role(),
        }

    if _wake_task is not None and not _wake_task.done():
        return {
            "started": False,
            "reason": "already_running",
            "interval_seconds": wake_interval_seconds(),
            "process": _process_identity(),
        }

    _wake_task = asyncio.create_task(
        _wake_loop(),
        name="prod-sync-comercial-abiertas-v2-wake",
    )

    return {
        "started": True,
        "reason": "started",
        "interval_seconds": wake_interval_seconds(),
        "job_id": JOB_ID,
        "process": _process_identity(),
    }


async def stop_internal_wake_loop() -> None:
    """Cancela la tarea del proceso sin afectar el job protegido."""
    global _wake_task

    task = _wake_task
    _wake_task = None

    if task is None:
        return

    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass
