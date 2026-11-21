"""Scheduler acotado para jobs habilitados en Preview.

Restaura exclusivamente los jobs que la configuracion canonica mantiene
habilitados y que perdieron owner periodico cuando PREVIEW_WEB dejo de iniciar
el APScheduler embebido completo.

Los dos sincronizadores comerciales tienen owners dedicados y quedan excluidos
de este APScheduler para evitar ejecuciones duplicadas:
- sync_comercial_abiertas_v2
- sync_comercial_v2

Los jobs con enabled=False siguen apagados.
Las pausas administrativas persistentes siguen siendo respetadas por
SchedulerManager.start().
Produccion nunca es elegible.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from modules.scheduler_runtime.policy import (
    PREVIEW_WEB,
    runtime_environment,
    runtime_role,
)


logger = logging.getLogger(__name__)

EXTERNAL_OWNER_JOB_IDS = frozenset(
    {
        "sync_comercial_abiertas_v2",
        "sync_comercial_v2",
    }
)


def preview_scoped_scheduler_eligible() -> bool:
    try:
        return (
            runtime_environment() == "PREVIEW"
            and runtime_role() == PREVIEW_WEB
        )
    except RuntimeError:
        return False


async def start_preview_scoped_scheduler(db) -> Dict[str, Any]:
    """Inicia los jobs habilitados sin duplicar los owners comerciales."""
    if not preview_scoped_scheduler_eligible():
        return {
            "started": False,
            "reason": "not_preview_web",
            "excluded_job_ids": sorted(EXTERNAL_OWNER_JOB_IDS),
        }

    from core.scheduler import start_scheduler

    manager = await start_scheduler(
        db,
        exclude_job_ids=EXTERNAL_OWNER_JOB_IDS,
    )
    status = manager.get_status()

    logger.warning(
        "Preview scoped scheduler state running=%s jobs=%s excluded=%s",
        status.get("running"),
        status.get("jobs_count"),
        sorted(EXTERNAL_OWNER_JOB_IDS),
    )

    return {
        "started": bool(status.get("running")),
        "reason": "started" if status.get("running") else "not_running",
        "jobs_count": int(status.get("jobs_count") or 0),
        "excluded_job_ids": sorted(EXTERNAL_OWNER_JOB_IDS),
        "jobs": status.get("jobs") or [],
    }
