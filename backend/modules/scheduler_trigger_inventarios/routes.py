"""Trigger HTTP productivo para el sync canónico de Compras/Inventarios.

Objetivo:
- desacoplar la cadencia de sync_compras del ciclo de vida de Emergent Preview;
- mantener la ejecución dentro del backend productivo canónico;
- reutilizar SchedulerManager, el guardrail de sync_compras y su lock SQL;
- no tocar ni depender de sincronizadores comerciales.

Seguridad:
- solo PRODUCTION + PRODUCTION_WEB;
- deshabilitado por defecto;
- secreto dedicado del scheduler productivo;
- comparación constante del secreto;
- exige SCHEDULER_SYNC_COMPRAS_ENABLED=true;
- exige SCHEDULER_SYNC_COMPRAS_EXECUTION_ENABLED=true.
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
    prefix="/api/internal/inventory-scheduler-trigger",
    tags=["Internal Inventory Scheduler Trigger"],
)

JOB_ID = "sync_compras"
TOKEN_ENV = "EDARSA_SCHEDULER_TRIGGER_KEY"
ENABLED_ENV = "EDARSA_INVENTORY_SCHEDULER_TRIGGER_ENABLED"
JOB_ENABLED_ENV = "SCHEDULER_SYNC_COMPRAS_ENABLED"
EXECUTION_ENABLED_ENV = "SCHEDULER_SYNC_COMPRAS_EXECUTION_ENABLED"


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


def _readiness() -> Dict[str, Any]:
    return {
        "trigger_enabled": _truthy_env(ENABLED_ENV),
        "job_enabled": _truthy_env(JOB_ENABLED_ENV, "true"),
        "execution_enabled": _truthy_env(EXECUTION_ENABLED_ENV),
    }


def _authorize_trigger(
    authorization: Optional[str],
    x_edarsa_scheduler_key: Optional[str],
) -> Dict[str, Any]:
    if runtime_environment() != "PRODUCTION":
        raise HTTPException(
            status_code=403,
            detail="INVENTORY_SCHEDULER_TRIGGER_PRODUCTION_ONLY",
        )

    try:
        role = runtime_role()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=403,
            detail="INVENTORY_SCHEDULER_TRIGGER_INVALID_RUNTIME_ROLE",
        ) from exc

    if role != PRODUCTION_WEB:
        raise HTTPException(
            status_code=403,
            detail="INVENTORY_SCHEDULER_TRIGGER_PRODUCTION_WEB_ONLY",
        )

    readiness = _readiness()
    if not readiness["trigger_enabled"]:
        raise HTTPException(
            status_code=503,
            detail="INVENTORY_SCHEDULER_TRIGGER_DISABLED",
        )

    expected = str(os.environ.get(TOKEN_ENV) or "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="INVENTORY_SCHEDULER_TRIGGER_NOT_CONFIGURED",
        )

    provided = _extract_token(
        authorization,
        x_edarsa_scheduler_key,
    )
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(
            status_code=401,
            detail="INVENTORY_SCHEDULER_TRIGGER_UNAUTHORIZED",
            headers={"WWW-Authenticate": "Bearer"},
        )

    policy = runtime_policy_snapshot()
    policy.update(readiness)
    return policy


def _require_job_ready(policy: Dict[str, Any]) -> None:
    if not policy.get("job_enabled"):
        raise HTTPException(
            status_code=503,
            detail="SYNC_COMPRAS_JOB_DISABLED",
        )

    if not policy.get("execution_enabled"):
        raise HTTPException(
            status_code=503,
            detail="SYNC_COMPRAS_EXECUTION_GUARD_DISABLED",
        )


@router.get("/health")
async def inventory_scheduler_trigger_health(
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

    ready = bool(
        policy.get("job_enabled")
        and policy.get("execution_enabled")
    )

    return {
        "status": "ready" if ready else "degraded",
        "service": "edarsahub-inventory-scheduler-trigger",
        "environment": policy.get("environment"),
        "runtime_role": policy.get("role"),
        "trigger_enabled": policy.get("trigger_enabled"),
        "job_enabled": policy.get("job_enabled"),
        "execution_enabled": policy.get("execution_enabled"),
        "job_id": JOB_ID,
    }


@router.post("/sync-compras")
async def trigger_sync_compras(
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
    _require_job_ready(policy)

    from core.scheduler.scheduler_manager import get_scheduler_manager

    manager = get_scheduler_manager()
    result = await manager.run_job_now(JOB_ID)

    status = str(result.get("status") or "").upper()
    logger.warning(
        "Inventory scheduler HTTP trigger completed job=%s status=%s "
        "runtime_role=%s",
        JOB_ID,
        status,
        policy.get("role"),
    )

    if status in {"FAILED", "DISABLED", "WARNING", "ERROR"}:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "SYNC_COMPRAS_NOT_HEALTHY",
                "result": result,
            },
        )

    return {
        **result,
        "job_id": JOB_ID,
        "triggered_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": policy.get("environment"),
        "runtime_role": policy.get("role"),
    }
