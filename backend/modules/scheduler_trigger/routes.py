"""Trigger HTTP productivo para el job protegido de Ventas del Dia.

No duplica logica de negocio. Invoca SchedulerManager canonico y falla cerrado
fuera de PRODUCTION_WEB.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hmac
import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException

from modules.scheduler_runtime.policy import (
    PRODUCTION_WEB,
    runtime_environment,
    runtime_policy_snapshot,
    runtime_role,
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
    return str(os.environ.get(name, default)).strip().lower() in {"1", "true", "yes", "on"}


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
    if runtime_environment() != "PRODUCTION":
        raise HTTPException(status_code=403, detail="SCHEDULER_TRIGGER_PRODUCTION_ONLY")

    try:
        role = runtime_role()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=403,
            detail="SCHEDULER_TRIGGER_INVALID_RUNTIME_ROLE",
        ) from exc

    if role != PRODUCTION_WEB:
        raise HTTPException(
            status_code=403,
            detail="SCHEDULER_TRIGGER_PRODUCTION_WEB_ONLY",
        )

    if not _truthy_env(ENABLED_ENV):
        raise HTTPException(status_code=503, detail="SCHEDULER_TRIGGER_DISABLED")

    expected = str(os.environ.get(TOKEN_ENV) or "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="SCHEDULER_TRIGGER_NOT_CONFIGURED",
        )

    provided = _extract_token(authorization, x_edarsa_scheduler_key)
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(
            status_code=401,
            detail="SCHEDULER_TRIGGER_UNAUTHORIZED",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return runtime_policy_snapshot()


@router.get("/health")
async def scheduler_trigger_health(
    authorization: Optional[str] = Header(default=None),
    x_edarsa_scheduler_key: Optional[str] = Header(
        default=None,
        alias="X-EDARSA-Scheduler-Key",
    ),
):
    policy = _authorize_trigger(authorization, x_edarsa_scheduler_key)
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
    policy = _authorize_trigger(authorization, x_edarsa_scheduler_key)

    from core.mongo_stub import get_stub_database
    from core.scheduler import get_scheduler_manager

    manager = get_scheduler_manager(get_stub_database())
    result = await manager.run_job_now(JOB_ID)

    logger.warning(
        "Production scheduler HTTP trigger completed job=%s runtime_role=%s",
        JOB_ID,
        policy.get("role"),
    )

    return {
        "status": result.get("status", "executed"),
        "job_id": JOB_ID,
        "triggered_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": policy.get("environment"),
        "runtime_role": policy.get("role"),
    }
