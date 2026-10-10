"""Trigger HTTP productivo para el job protegido de Ventas del Dia.

Este modulo NO contiene ni duplica la logica de negocio de
sync_comercial_abiertas_v2. Unicamente invoca el SchedulerManager canonico.

Contrato de seguridad:
- solo PRODUCTION;
- deshabilitado por defecto;
- secreto dedicado obligatorio;
- comparacion constante del secreto;
- invoca exclusivamente el job protegido;
- el lock distribuido y la bitacora siguen perteneciendo al wrapper canonico.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hmac
import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException

from modules.scheduler_runtime.policy import (
    runtime_environment,
    runtime_policy_snapshot,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/internal/scheduler-trigger",
    tags=["Internal Scheduler Trigger"],
)

JOB_ID = "sync_comercial_abiertas_v2"
TOKEN_ENV = "EDARSA_SCHEDULER_TRIGGER_KEY"
ENABLED_ENV = "EDARSA_SCHEDULER_TRIGGER_ENABLED"


def _truthy_env(name: str, default: str = "false") -> bool:
    return str(os.environ.get(name, default)).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _extract_token(
    authorization: Optional[str],
    x_edarsa_scheduler_key: Optional[str],
) -> str:
    header = str(authorization or "").strip()
    if header:
        scheme, separator, token = header.partition(" ")
        if separator and scheme.lower() == "bearer" and token.strip():
            return token.strip()

    return str(x_edarsa_scheduler_key or "").strip()


def _authorize_trigger(
    authorization: Optional[str],
    x_edarsa_scheduler_key: Optional[str],
) -> Dict[str, Any]:
    environment = runtime_environment()
    if environment != "PRODUCTION":
        raise HTTPException(
            status_code=403,
            detail="SCHEDULER_TRIGGER_PRODUCTION_ONLY",
        )

    if not _truthy_env(ENABLED_ENV):
        raise HTTPException(
            status_code=503,
            detail="SCHEDULER_TRIGGER_DISABLED",
        )

    expected = str(os.environ.get(TOKEN_ENV) or "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="SCHEDULER_TRIGGER_NOT_CONFIGURED",
        )

    provided = _extract_token(
        authorization,
        x_edarsa_scheduler_key,
    )

    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(
            status_code=401,
            detail="SCHEDULER_TRIGGER_UNAUTHORIZED",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return runtime_policy_snapshot()


async def _latest_event() -> Optional[Dict[str, Any]]:
    from core.scheduler.job_logger import get_job_logger

    rows = await get_job_logger().get_logs(
        job_name=JOB_ID,
        limit=1,
    )
    return rows[0] if rows else None


def _event_identity(event: Optional[Dict[str, Any]]) -> Optional[tuple]:
    if not event:
        return None

    return (
        event.get("run_id"),
        event.get("accion"),
        str(event.get("fecha_accion")),
    )


def _event_summary(
    event: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not event:
        return None

    return {
        "run_id": event.get("run_id"),
        "action": event.get("accion"),
        "timestamp": event.get("fecha_accion"),
        "success": event.get("exito"),
    }


@router.get("/health")
async def scheduler_trigger_health(
    authorization: Optional[str] = Header(default=None),
    x_edarsa_scheduler_key: Optional[str] = Header(
        default=None,
        alias="X-EDARSA-Scheduler-Key",
    ),
):
    policy = _authorize_trigger(
        authorization,
        x_edarsa_scheduler_key,
    )

    return {
        "status": "ready",
        "service": "edarsahub-production-scheduler-trigger",
        "environment": policy.get("environment"),
        "runtime_role": policy.get("role"),
        "trigger_enabled": True,
        "job_id": JOB_ID,
    }


@router.post("/sync-comercial-abiertas-v2")
async def trigger_sync_comercial_abiertas_v2(
    authorization: Optional[str] = Header(default=None),
    x_edarsa_scheduler_key: Optional[str] = Header(
        default=None,
        alias="X-EDARSA-Scheduler-Key",
    ),
):
    policy = _authorize_trigger(
        authorization,
        x_edarsa_scheduler_key,
    )

    before = await _latest_event()

    from core.scheduler.scheduler_manager import get_scheduler_manager

    manager = get_scheduler_manager()
    result = await manager.run_job_now(JOB_ID)

    after = await _latest_event()
    execution_observed = (
        _event_identity(after) is not None
        and _event_identity(after) != _event_identity(before)
    )

    logger.warning(
        "Production scheduler HTTP trigger completed job=%s "
        "execution_observed=%s runtime_role=%s",
        JOB_ID,
        execution_observed,
        policy.get("role"),
    )

    return {
        "status": result.get("status", "executed"),
        "job_id": JOB_ID,
        "triggered_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": policy.get("environment"),
        "runtime_role": policy.get("role"),
        "execution_observed": execution_observed,
        "last_event": _event_summary(after),
    }
