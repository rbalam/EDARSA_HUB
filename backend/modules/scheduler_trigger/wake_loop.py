"""Wake loop productivo para Ventas del Dia.

Este modulo NO contiene ni duplica la logica de negocio de
sync_comercial_abiertas_v2. Solo despierta periodicamente el
SchedulerManager canonico dentro del backend Live de Produccion.

Reglas:
- solo PRODUCTION + PRODUCTION_WEB;
- usa el mismo feature flag del trigger productivo;
- respeta el intervalo canonico del job (default 300 s);
- invoca exclusivamente SchedulerManager.run_job_now(JOB_ID);
- el lock distribuido y la bitacora siguen en el wrapper canonico;
- una sola tarea asyncio por proceso y apagado limpio.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, Optional

from modules.scheduler_runtime.policy import (
    runtime_environment,
    runtime_role,
)


logger = logging.getLogger(__name__)

JOB_ID = "sync_comercial_abiertas_v2"
TRIGGER_ENABLED_ENV = "EDARSA_SCHEDULER_TRIGGER_ENABLED"
JOB_ENABLED_ENV = "SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_ENABLED"
INTERVAL_ENV = "SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_INTERVAL_SECONDS"
DEFAULT_INTERVAL_SECONDS = 300
MIN_INTERVAL_SECONDS = 60

_wake_task: Optional[asyncio.Task] = None


def _truthy(name: str, default: str = "false") -> bool:
    return str(os.environ.get(name, default)).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


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


async def _wake_loop() -> None:
    interval = wake_interval_seconds()

    logger.warning(
        "Production internal wake loop started job=%s interval=%ss",
        JOB_ID,
        interval,
    )

    try:
        while True:
            await asyncio.sleep(interval)

            if not internal_wake_eligible():
                logger.warning(
                    "Production internal wake loop stopped by policy "
                    "environment=%s role=%s trigger_enabled=%s job_enabled=%s",
                    runtime_environment(),
                    runtime_role(),
                    _truthy(TRIGGER_ENABLED_ENV),
                    _truthy(JOB_ENABLED_ENV, "true"),
                )
                return

            try:
                result = await _run_once()
                logger.warning(
                    "Production internal wake completed job=%s status=%s",
                    JOB_ID,
                    result.get("status"),
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "Production internal wake failed job=%s",
                    JOB_ID,
                )
    except asyncio.CancelledError:
        logger.info(
            "Production internal wake loop cancelled job=%s",
            JOB_ID,
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
