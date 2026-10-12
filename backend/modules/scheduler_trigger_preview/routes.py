"""Trigger HTTP externo para los sincronizadores comerciales de Preview.

Objetivo:
- desacoplar la cadencia de sync_comercial_abiertas_v2 y sync_comercial_v2
  del ciclo de vida visual de Emergent Preview;
- reutilizar SchedulerManager.run_job_now(...) sin duplicar logica de negocio;
- reutilizar los mismos owner locks de los wakes certificados para que el
  canario sea seguro mientras PREVIEW_WEB siga abierto.

Este modulo NO importa los jobs de negocio protegidos.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hmac
import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException

from modules.scheduler_runtime.policy import (
    PREVIEW_WEB,
    runtime_environment,
    runtime_policy_snapshot,
    runtime_role,
)
from modules.scheduler_runtime.preview_closed_sales_wake import (
    JOB_ID as CLOSED_JOB_ID,
    OWNER_HEARTBEAT_SECONDS as CLOSED_OWNER_HEARTBEAT_SECONDS,
    OWNER_LEASE_SECONDS as CLOSED_OWNER_LEASE_SECONDS,
    OWNER_LOCK_ID as CLOSED_OWNER_LOCK_ID,
)
from modules.scheduler_runtime.preview_sales_wake import (
    JOB_ID as OPEN_JOB_ID,
    OWNER_HEARTBEAT_SECONDS as OPEN_OWNER_HEARTBEAT_SECONDS,
    OWNER_LEASE_SECONDS as OPEN_OWNER_LEASE_SECONDS,
    OWNER_LOCK_ID as OPEN_OWNER_LOCK_ID,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/internal/preview-scheduler-trigger",
    tags=["Internal Preview Scheduler Trigger"],
)

TOKEN_ENV = "EDARSA_PREVIEW_SCHEDULER_TRIGGER_KEY"
ENABLED_ENV = "EDARSA_PREVIEW_SCHEDULER_TRIGGER_ENABLED"


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
    if runtime_environment() != "PREVIEW":
        raise HTTPException(
            status_code=403,
            detail="PREVIEW_SCHEDULER_TRIGGER_PREVIEW_ONLY",
        )

    try:
        role = runtime_role()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=403,
            detail="PREVIEW_SCHEDULER_TRIGGER_INVALID_RUNTIME_ROLE",
        ) from exc

    if role != PREVIEW_WEB:
        raise HTTPException(
            status_code=403,
            detail="PREVIEW_SCHEDULER_TRIGGER_PREVIEW_WEB_ONLY",
        )

    if not _truthy_env(ENABLED_ENV):
        raise HTTPException(
            status_code=503,
            detail="PREVIEW_SCHEDULER_TRIGGER_DISABLED",
        )

    expected = str(os.environ.get(TOKEN_ENV) or "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="PREVIEW_SCHEDULER_TRIGGER_NOT_CONFIGURED",
        )

    provided = _extract_token(
        authorization,
        x_edarsa_scheduler_key,
    )

    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(
            status_code=401,
            detail="PREVIEW_SCHEDULER_TRIGGER_UNAUTHORIZED",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return runtime_policy_snapshot()


def _closed_sales_administratively_paused() -> bool:
    """Replica la proteccion fail-closed del owner certificado de Ventas Cerradas."""
    try:
        from core.scheduler.persistent_state_repository import (
            SchedulerPersistentStateRepository,
        )

        paused = {
            str(value).strip()
            for value in SchedulerPersistentStateRepository.get_paused_job_ids()
        }
        return CLOSED_JOB_ID in paused
    except Exception:
        logger.exception(
            "Preview external trigger no pudo validar pausa administrativa "
            "job=%s; se omite ejecucion por fail-closed",
            CLOSED_JOB_ID,
        )
        return True


async def _acquire_owner_lock(
    owner_lock_id: str,
    lease_seconds: int,
    heartbeat_seconds: int,
):
    from core.scheduler.locks import get_lock_manager

    lock = get_lock_manager().get_lock(owner_lock_id)
    acquired = await lock.acquire(timeout_seconds=lease_seconds)
    if not acquired:
        return None

    await lock.start_heartbeat_loop(
        interval_seconds=heartbeat_seconds,
        extend_seconds=lease_seconds,
    )
    return lock


async def _run_canonical_job(
    *,
    job_id: str,
    owner_lock_id: str,
    lease_seconds: int,
    heartbeat_seconds: int,
    policy: Dict[str, Any],
) -> Dict[str, Any]:
    owner_lock = await _acquire_owner_lock(
        owner_lock_id,
        lease_seconds,
        heartbeat_seconds,
    )

    if owner_lock is None:
        return {
            "status": "owner_active",
            "job_id": job_id,
            "execution_observed": False,
            "owner_lock_id": owner_lock_id,
            "environment": policy.get("environment"),
            "runtime_role": policy.get("role"),
        }

    try:
        if (
            job_id == CLOSED_JOB_ID
            and _closed_sales_administratively_paused()
        ):
            return {
                "status": "administratively_paused",
                "job_id": job_id,
                "execution_observed": False,
                "owner_lock_id": owner_lock_id,
                "environment": policy.get("environment"),
                "runtime_role": policy.get("role"),
            }

        from core.mongo_stub import get_stub_database
        from core.scheduler import get_scheduler_manager

        manager = get_scheduler_manager(get_stub_database())
        result = await manager.run_job_now(job_id)

        status = result.get("status", "executed")
        execution_observed = status == "executed"

        logger.warning(
            "Preview external scheduler trigger completed "
            "job=%s status=%s runtime_role=%s",
            job_id,
            status,
            policy.get("role"),
        )

        return {
            "status": status,
            "job_id": job_id,
            "execution_observed": execution_observed,
            "owner_lock_id": owner_lock_id,
            "triggered_at_utc": datetime.now(timezone.utc).isoformat(),
            "environment": policy.get("environment"),
            "runtime_role": policy.get("role"),
        }
    finally:
        try:
            await owner_lock.release()
        except Exception:
            logger.exception(
                "Preview external scheduler trigger owner release failed "
                "job=%s owner_lock=%s",
                job_id,
                owner_lock_id,
            )


@router.get("/health")
async def preview_scheduler_trigger_health(
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
        "service": "edarsahub-preview-commercial-scheduler-trigger",
        "environment": policy.get("environment"),
        "runtime_role": policy.get("role"),
        "trigger_enabled": True,
        "jobs": [
            {
                "job_id": OPEN_JOB_ID,
                "owner_lock_id": OPEN_OWNER_LOCK_ID,
            },
            {
                "job_id": CLOSED_JOB_ID,
                "owner_lock_id": CLOSED_OWNER_LOCK_ID,
            },
        ],
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

    return await _run_canonical_job(
        job_id=OPEN_JOB_ID,
        owner_lock_id=OPEN_OWNER_LOCK_ID,
        lease_seconds=OPEN_OWNER_LEASE_SECONDS,
        heartbeat_seconds=OPEN_OWNER_HEARTBEAT_SECONDS,
        policy=policy,
    )


@router.post("/sync-comercial-v2")
async def trigger_sync_comercial_v2(
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

    return await _run_canonical_job(
        job_id=CLOSED_JOB_ID,
        owner_lock_id=CLOSED_OWNER_LOCK_ID,
        lease_seconds=CLOSED_OWNER_LEASE_SECONDS,
        heartbeat_seconds=CLOSED_OWNER_HEARTBEAT_SECONDS,
        policy=policy,
    )
