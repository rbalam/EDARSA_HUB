"""Authenticated HTTP boundary for the Universal Worker canonical ingress."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status

from core.rbac.middleware import require_explicit_permission
from modules.worker_mcp.oauth_pkce import OAuthValidationError
from modules.worker_mcp.oauth_server import enforce_internal_jwt_mcp_scope

from .schemas import WorkerObjectiveRequest, WorkerSubmitRequest
from .service import (
    WorkerIngressError,
    get_job_status,
    submit_job,
    submit_objective,
)
from .service_credential import (
    WorkerServiceCredentialError,
    exchange_service_credential,
)


router = APIRouter(
    prefix="/internal/worker",
    tags=["worker-ingress-internal"],
)

WORKER_ADMIN_DEPENDENCY = require_explicit_permission("RBAC_ADMIN")


def _bearer_credential(authorization: str | None) -> str:
    header = str(authorization or "").strip()
    if not header.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SERVICE_CREDENTIAL_REQUIRED",
        )
    credential = header[7:].strip()
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SERVICE_CREDENTIAL_REQUIRED",
        )
    return credential


def _raise_for_submit_status(result: dict[str, Any]) -> None:
    state = str(result.get("status") or "").upper()

    if state == "INVALID_JOB":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result,
        )
    if state == "REQUESTER_DENIED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result,
        )
    if state in {
        "RECOVERY_REQUIRED",
        "WRITER_BUSY",
        "CLAIM_BUSY",
        "REMOTE_MOVED_RETRYABLE",
        "BLOCKED_CONVERGENCE",
    }:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=result,
        )


@router.post("/auth/exchange")
def exchange_worker_service_credential(
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
):
    """Exchange a revocable MCP service credential for a short internal JWT."""
    credential = _bearer_credential(authorization)
    try:
        return exchange_service_credential(credential)
    except WorkerServiceCredentialError as exc:
        code = (
            status.HTTP_403_FORBIDDEN
            if exc.code.startswith("SERVICE_IDENTITY")
            or exc.code.startswith("SERVICE_PERMISSION")
            or exc.code.startswith("SERVICE_SQL_IDENTITY")
            else status.HTTP_401_UNAUTHORIZED
        )
        raise HTTPException(
            status_code=code,
            detail=exc.code,
        ) from exc


def _require_ingress_mcp_scope(
    *,
    authorization: str | None,
    required_scope: str,
    current_user: dict | None,
) -> None:
    try:
        enforce_internal_jwt_mcp_scope(
            authorization=authorization,
            required_scope=required_scope,
            current_user=current_user,
        )
    except OAuthValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "INSUFFICIENT_SCOPE",
                "required_scope": required_scope,
                "code": str(exc),
            },
        ) from exc


def _require_submit_mcp_scope_dependency(
    current_user: dict = Depends(WORKER_ADMIN_DEPENDENCY),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> None:
    _require_ingress_mcp_scope(
        authorization=authorization,
        required_scope="worker:submit",
        current_user=current_user,
    )


@router.post(
    "/jobs",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(_require_submit_mcp_scope_dependency)],
)
def submit_worker_job(
    request: WorkerSubmitRequest,
    current_user: dict = Depends(WORKER_ADMIN_DEPENDENCY),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    _require_ingress_mcp_scope(
        authorization=authorization,
        required_scope="worker:submit",
        current_user=current_user,
    )
    try:
        result = submit_job(
            request.model_dump(exclude_none=True),
            current_user=current_user,
        )
    except WorkerIngressError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    _raise_for_submit_status(result)
    return result


@router.post(
    "/objectives",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(_require_submit_mcp_scope_dependency)],
)
def submit_worker_objective(
    request: WorkerObjectiveRequest,
    current_user: dict = Depends(WORKER_ADMIN_DEPENDENCY),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    _require_ingress_mcp_scope(
        authorization=authorization,
        required_scope="worker:submit",
        current_user=current_user,
    )
    try:
        result = submit_objective(
            request.model_dump(exclude_none=True),
            current_user=current_user,
        )
    except WorkerIngressError as exc:
        from .service import build_semantic_diagnostic

        message = str(exc)
        code = (
            status.HTTP_422_UNPROCESSABLE_ENTITY
            if message.startswith("SEMANTIC_")
            else status.HTTP_400_BAD_REQUEST
        )
        diagnostic = exc.diagnostic or build_semantic_diagnostic(
            message,
            request_payload=request.model_dump(exclude_none=True),
        )
        raise HTTPException(status_code=code, detail=diagnostic) from exc

    _raise_for_submit_status(result)
    return result


@router.get("/jobs/{job_id}")
def read_worker_job_status(
    job_id: str,
    current_user: dict = Depends(WORKER_ADMIN_DEPENDENCY),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    if job_id != "MCP-AUTH-PROBE":
        _require_ingress_mcp_scope(
            authorization=authorization,
            required_scope="worker:status",
            current_user=current_user,
        )
    del current_user
    try:
        result = get_job_status(job_id)
    except WorkerIngressError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if result.get("lifecycle") == "NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result,
        )
    return result


@router.get("/capabilities")
def list_worker_semantic_capabilities(
    current_user: dict = Depends(WORKER_ADMIN_DEPENDENCY),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    """Read-only discovery of registered semantic capabilities and allowed constraints."""
    _require_ingress_mcp_scope(
        authorization=authorization,
        required_scope="worker:status",
        current_user=current_user,
    )
    del current_user
    from .semantic_capabilities import (
        RAW_WORKER_FIELDS_FORBIDDEN,
        capability_catalog,
    )

    return {
        "schema": "edarsahub.worker-semantic-capabilities.v1",
        "production_allowed": False,
        "raw_worker_fields_forbidden": list(RAW_WORKER_FIELDS_FORBIDDEN),
        "capabilities": capability_catalog(),
    }



@router.get("/runtime-convergence")
def read_worker_runtime_convergence(
    current_user: dict = Depends(WORKER_ADMIN_DEPENDENCY),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    """Read-only convergence report across Git HEAD, Worker runtime, and MCP capability catalog."""
    _require_ingress_mcp_scope(
        authorization=authorization,
        required_scope="worker:status",
        current_user=current_user,
    )
    del current_user
    from tools.mirror_sync.worker_runtime_fingerprint import (
        build_mcp_runtime_convergence_report,
    )
    from .semantic_capabilities import capability_catalog

    report = build_mcp_runtime_convergence_report()
    report["capability_catalog"] = capability_catalog()
    return report



@router.get("/context")
def read_worker_go_context(
    domain: str,
    project: str = "EDARSAHUB",
    chain_id: str | None = None,
    objective_hint: str | None = None,
    current_user: dict = Depends(WORKER_ADMIN_DEPENDENCY),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    """Read-only canonical GO context resolution for cross-chat continuity."""
    _require_ingress_mcp_scope(
        authorization=authorization,
        required_scope="worker:status",
        current_user=current_user,
    )
    from .service import resolve_go_context

    return resolve_go_context(
        domain=domain,
        current_user=current_user,
        project=project,
        chain_id=chain_id,
        objective_hint=objective_hint,
    )



@router.post("/objectives/preflight")
def preflight_worker_objective(
    request: WorkerObjectiveRequest,
    current_user: dict = Depends(WORKER_ADMIN_DEPENDENCY),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    """Read-only canonical semantic preflight before publication."""
    _require_ingress_mcp_scope(
        authorization=authorization,
        required_scope="worker:status",
        current_user=current_user,
    )
    from .service import preflight_semantic_objective

    return preflight_semantic_objective(
        request.model_dump(exclude_none=True),
        current_user=current_user,
        enforce_runtime_convergence=True,
    )
