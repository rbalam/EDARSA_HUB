"""Trigger OIDC de Inventarios para Development/Preview.

Permite que GitHub Actions active el job canonico sync_compras usando las
credenciales writer del runtime Preview, sin exponerlas a GitHub.

No implementa logica de negocio y prohibe Production.
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
    runtime_role,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/internal/preview-inventory-scheduler-trigger",
    tags=["Internal Preview Inventory Scheduler Trigger"],
)

OIDC_ISSUER = "https://token.actions.githubusercontent.com"
OIDC_JWKS_URL = f"{OIDC_ISSUER}/.well-known/jwks"
OIDC_AUDIENCE = "edarsahub-preview-inventory-scheduler"
EXPECTED_REPOSITORY = "rbalam/EDARSA_HUB"
EXPECTED_REF = "refs/heads/Edarsahub_Desarrollo"
EXPECTED_WORKFLOW_REF = (
    f"{EXPECTED_REPOSITORY}/.github/workflows/"
    f"inventory-preview-external-owner.yml@{EXPECTED_REF}"
)
ALLOWED_EVENTS = {"schedule", "workflow_dispatch", "push"}

_jwks_client = PyJWKClient(
    OIDC_JWKS_URL,
    cache_keys=True,
    lifespan=3600,
)


def _truthy(name: str, default: str = "true") -> bool:
    return str(os.environ.get(name, default)).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _extract_bearer_token(authorization: Optional[str]) -> str:
    header = str(authorization or "").strip()
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
            "Preview inventory OIDC verification failed: %s",
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=401,
            detail="PREVIEW_INVENTORY_TRIGGER_INVALID_OIDC",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    checks = {
        "repository": EXPECTED_REPOSITORY,
        "ref": EXPECTED_REF,
        "workflow_ref": EXPECTED_WORKFLOW_REF,
    }
    for key, expected in checks.items():
        if claims.get(key) != expected:
            raise HTTPException(
                status_code=403,
                detail=f"PREVIEW_INVENTORY_TRIGGER_WRONG_{key.upper()}",
            )

    if claims.get("event_name") not in ALLOWED_EVENTS:
        raise HTTPException(
            status_code=403,
            detail="PREVIEW_INVENTORY_TRIGGER_WRONG_EVENT",
        )

    expected_subject_prefix = f"repo:{EXPECTED_REPOSITORY}:"
    if not str(claims.get("sub") or "").startswith(expected_subject_prefix):
        raise HTTPException(
            status_code=403,
            detail="PREVIEW_INVENTORY_TRIGGER_WRONG_SUBJECT",
        )

    return claims


def _authorize(authorization: Optional[str]) -> Dict[str, Any]:
    if runtime_environment() != "PREVIEW":
        raise HTTPException(
            status_code=403,
            detail="PREVIEW_INVENTORY_TRIGGER_PREVIEW_ONLY",
        )

    try:
        role = runtime_role()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=403,
            detail="PREVIEW_INVENTORY_TRIGGER_INVALID_RUNTIME_ROLE",
        ) from exc

    if role != PREVIEW_WEB:
        raise HTTPException(
            status_code=403,
            detail="PREVIEW_INVENTORY_TRIGGER_PREVIEW_WEB_ONLY",
        )

    if not _truthy("EDARSA_PREVIEW_INVENTORY_TRIGGER_ENABLED", "true"):
        raise HTTPException(
            status_code=503,
            detail="PREVIEW_INVENTORY_TRIGGER_DISABLED",
        )

    token = _extract_bearer_token(authorization)
    if not token:
        raise HTTPException(
            status_code=401,
            detail="PREVIEW_INVENTORY_TRIGGER_OIDC_REQUIRED",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _decode_github_oidc(token)


@router.get("/health")
async def preview_inventory_trigger_health(
    authorization: Optional[str] = Header(default=None),
):
    claims = _authorize(authorization)
    return {
        "status": "ready",
        "service": "edarsahub-preview-inventory-scheduler-trigger",
        "environment": "PREVIEW",
        "runtime_role": PREVIEW_WEB,
        "job_id": "sync_compras",
        "auth": "github_oidc",
        "oidc_run_id": claims.get("run_id"),
    }


@router.post("/sync-compras")
async def trigger_preview_sync_compras(
    authorization: Optional[str] = Header(default=None),
):
    claims = _authorize(authorization)

    from core.mongo_stub import get_stub_database
    from core.scheduler import get_scheduler_manager

    manager = get_scheduler_manager(get_stub_database())
    result = await manager.run_job_now("sync_compras")
    payload = dict(result or {})
    payload.setdefault("status", "ERROR")
    payload.setdefault("job_id", "sync_compras")
    payload["triggered_at_utc"] = datetime.now(timezone.utc).isoformat()
    payload["environment"] = "PREVIEW"
    payload["runtime_role"] = PREVIEW_WEB
    payload["auth"] = "github_oidc"
    payload["oidc_run_id"] = claims.get("run_id")
    payload["production_touched"] = False
    return payload
