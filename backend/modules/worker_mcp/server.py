"""Minimal MCP transport for the certified EDARSAHUB semantic ingress."""
from __future__ import annotations

from typing import Any

from mcp.server import MCPServer
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import AnyHttpUrl

from .auth import EdarsahubTokenVerifier
from .client import (
    get_job_status as backend_get_job_status,
    submit_objective as backend_submit_objective,
)
from .config import WorkerMcpConfig


_BACKEND_URL: str | None = None


def _bearer_token() -> str:
    access_token = get_access_token()
    if access_token is None or not access_token.token:
        raise PermissionError("MCP_AUTH_REQUIRED")
    return str(access_token.token)


def _backend_url() -> str:
    if not _BACKEND_URL:
        raise RuntimeError("MCP_BACKEND_NOT_CONFIGURED")
    return _BACKEND_URL


def submit_objective_tool(
    objective: str,
    bounded_context: str,
    mode: str,
    capability: str,
    request_key: str | None = None,
    constraints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Submit one approved semantic objective to the EDARSAHUB Universal Worker."""
    payload: dict[str, Any] = {
        "objective": objective,
        "bounded_context": bounded_context,
        "mode": mode,
        "capability": capability,
        "constraints": constraints or {},
    }
    if request_key:
        payload["request_key"] = request_key

    result = backend_submit_objective(
        backend_url=_backend_url(),
        token=_bearer_token(),
        payload=payload,
    )

    return {
        "status": result.get("status"),
        "job_id": result.get("job_id"),
        "capability": result.get("capability"),
        "bounded_context": result.get("bounded_context"),
        "production_touched": bool(
            result.get("production_touched", False)
        ),
    }


def get_job_status_tool(
    job_id: str,
) -> dict[str, Any]:
    """Read the canonical status of one Universal Worker job."""
    result = backend_get_job_status(
        backend_url=_backend_url(),
        token=_bearer_token(),
        job_id=job_id,
    )
    return {
        "job_id": result.get("job_id"),
        "lifecycle": result.get("lifecycle"),
        "status": result.get("status"),
        "certification": result.get("certification"),
        "quality_gate": result.get("quality_gate"),
        "tests": result.get("tests"),
        "percent_complete": result.get("percent_complete"),
        "blockers": result.get("blockers"),
        "files_changed": result.get("files_changed"),
        "commit_sha": result.get("commit_sha"),
        "git_sync_status": result.get("git_sync_status"),
        "production_touched": result.get(
            "production_touched",
            False,
        ),
        "summary_es": result.get("summary_es"),
    }


def build_mcp_server(
    config: WorkerMcpConfig,
    *,
    token_verifier: TokenVerifier | None = None,
) -> MCPServer:
    global _BACKEND_URL
    _BACKEND_URL = config.backend_url.rstrip("/")

    verifier = token_verifier or EdarsahubTokenVerifier(
        backend_url=config.backend_url,
        resource_url=config.resource_url,
    )

    mcp = MCPServer(
        "EDARSAHUB Universal Worker",
        instructions=(
            "Use submit_objective to send approved semantic objectives to "
            "EDARSAHUB. Use get_job_status to read their canonical status. "
            "No low-level worker actions are exposed."
        ),
        token_verifier=verifier,
        auth=AuthSettings(
            issuer_url=AnyHttpUrl(config.issuer_url),
            resource_server_url=AnyHttpUrl(
                config.resource_url
            ),
            required_scopes=[],
            validate_token_resource=False,
        ),
    )

    mcp.tool(
        name="submit_objective",
        title="Submit EDARSAHUB objective",
        annotations=ToolAnnotations(
            read_only_hint=False,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        ),
    )(submit_objective_tool)

    mcp.tool(
        name="get_job_status",
        title="Get EDARSAHUB Worker job status",
        annotations=ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        ),
    )(get_job_status_tool)

    return mcp


def build_transport_security(
    config: WorkerMcpConfig,
) -> TransportSecuritySettings:
    return TransportSecuritySettings(
        allowed_hosts=list(config.allowed_hosts),
        allowed_origins=list(config.allowed_origins),
    )
