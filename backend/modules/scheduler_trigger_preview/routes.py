"""Trigger HTTP externo para los sincronizadores comerciales de Preview.

Objetivo:
- desacoplar la cadencia de sync_comercial_abiertas_v2 y sync_comercial_v2
  del ciclo de vida visual de Emergent Preview;
- reutilizar SchedulerManager.run_job_now(...) sin duplicar logica de negocio;
- reutilizar los mismos owner locks de los wakes certificados para que el
  canario sea seguro mientras PREVIEW_WEB siga abierto;
- autenticar exclusivamente GitHub Actions mediante OIDC, sin secreto
  compartido persistente.

Este modulo NO importa los jobs de negocio protegidos.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException
import jwt
from jwt import PyJWKClient

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

ENABLED_ENV = "EDARSA_PREVIEW_SCHEDULER_TRIGGER_ENABLED"

OIDC_ISSUER = "https://token.actions.githubusercontent.com"
OIDC_JWKS_URL = f"{OIDC_ISSUER}/.well-known/jwks"
OIDC_AUDIENCE = "edarsahub-preview-commercial-scheduler"
EXPECTED_REPOSITORY = "rbalam/EDARSA_HUB"
EXPECTED_REF = "refs/heads/Edarsahub_Desarrollo"
EXPECTED_WORKFLOW_REF = (
    f"{EXPECTED_REPOSITORY}/.github/workflows/"
    f"preview-commercial-external-owner.yml@{EXPECTED_REF}"
)
ALLOWED_EVENTS = {"schedule", "workflow_dispatch"}

_jwks_client = PyJWKClient(
    OIDC_JWKS_URL,
    cache_keys=True,
    lifespan=3600,
)


def _truthy_env(name: str, default: str = "false") -> bool:
    return str(os.environ.get(name, default)).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _extract_bearer_token(authorization: Optional[str]) -> str:
    header = str(authorization or "").strip()
    if not header:
        return ""

    scheme, separator, token = header.partition(" ")
    if not separator or scheme.lower() != "bearer":
        return ""

    return token.strip()


def _decode_github_oidc(token: str) -> Dict[str, Any]:
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=OIDC_AUDIENCE,
            issuer=OIDC_ISSUER,
            options={
                "require": [
                    "exp",
                    "iat",
                    "iss",
                    "aud",
                    "sub",
                    "repository",
                    "ref",
                    "workflow_ref",
                    "event_name",
                ]
            },
        )
    except Exception as exc:
        logger.warning(
            "Preview scheduler GitHub OIDC verification failed: %s",
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=401,
            detail="PREVIEW_SCHEDULER_TRIGGER_INVALID_OIDC",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if claims.get("repository") != EXPECTED_REPOSITORY:
        raise HTTPException(
            status_code=403,
            detail="PREVIEW_SCHEDULER_TRIGGER_WRONG_REPOSITORY",
        )

    if claims.get("ref") != EXPECTED_REF:
        raise HTTPException(
            status_code=403,
            detail="PREVIEW_SCHEDULER_TRIGGER_WRONG_REF",
        )

    if claims.get("workflow_ref") != EXPECTED_WORKFLOW_REF:
        raise HTTPException(
            status_code=403,
            detail="PREVIEW_SCHEDULER_TRIGGER_WRONG_WORKFLOW",
        )

    if claims.get("event_name") not in ALLOWED_EVENTS:
        raise HTTPException(
            status_code=403,
            detail="PREVIEW_SCHEDULER_TRIGGER_WRONG_EVENT",
        )

    expected_subject_prefix = f"repo:{EXPECTED_REPOSITORY}:"
    if not str(claims.get("sub") or "").startswith(expected_subject_prefix):
        raise HTTPException(
            status_code=403,
            detail="PREVIEW_SCHEDULER_TRIGGER_WRONG_SUBJECT",
        )

    return claims


def _authorize_trigger(
    authorization: Optional[str],
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

    # OIDC estricto es el control primario. Este flag queda solo como kill switch.
    if not _truthy_env(ENABLED_ENV, "true"):
        raise HTTPException(
            status_code=503,
            detail="PREVIEW_SCHEDULER_TRIGGER_DISABLED",
        )

    token = _extract_bearer_token(authorization)
    if not token:
        raise HTTPException(
            status_code=401,
            detail="PREVIEW_SCHEDULER_TRIGGER_OIDC_REQUIRED",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = _decode_github_oidc(token)

    policy = runtime_policy_snapshot()
    policy["oidc_repository"] = claims.get("repository")
    policy["oidc_ref"] = claims.get("ref")
    policy["oidc_workflow_ref"] = claims.get("workflow_ref")
    policy["oidc_event_name"] = claims.get("event_name")
    policy["oidc_run_id"] = claims.get("run_id")
    return policy


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
            "auth": "github_oidc",
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
                "auth": "github_oidc",
            }

        from core.mongo_stub import get_stub_database
        from core.scheduler import get_scheduler_manager

        manager = get_scheduler_manager(get_stub_database())
        result = await manager.run_job_now(job_id)

        status = result.get("status", "executed")
        execution_observed = status == "executed"

        logger.warning(
            "Preview external scheduler trigger completed "
            "job=%s status=%s runtime_role=%s oidc_run_id=%s",
            job_id,
            status,
            policy.get("role"),
            policy.get("oidc_run_id"),
        )

        return {
            "status": status,
            "job_id": job_id,
            "execution_observed": execution_observed,
            "owner_lock_id": owner_lock_id,
            "triggered_at_utc": datetime.now(timezone.utc).isoformat(),
            "environment": policy.get("environment"),
            "runtime_role": policy.get("role"),
            "auth": "github_oidc",
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
):
    policy = _authorize_trigger(authorization)

    return {
        "status": "ready",
        "service": "edarsahub-preview-commercial-scheduler-trigger",
        "environment": policy.get("environment"),
        "runtime_role": policy.get("role"),
        "trigger_enabled": True,
        "auth": "github_oidc",
        "oidc_repository": policy.get("oidc_repository"),
        "oidc_ref": policy.get("oidc_ref"),
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
):
    policy = _authorize_trigger(authorization)

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
):
    policy = _authorize_trigger(authorization)

    return await _run_canonical_job(
        job_id=CLOSED_JOB_ID,
        owner_lock_id=CLOSED_OWNER_LOCK_ID,
        lease_seconds=CLOSED_OWNER_LEASE_SECONDS,
        heartbeat_seconds=CLOSED_OWNER_HEARTBEAT_SECONDS,
        policy=policy,
    )
