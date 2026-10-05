"""Minimal MCP server for the EDARSAHUB Universal Worker.

Public MCP surface:
- submit_objective
- get_job_status

The MCP adapter never constructs worker-job.v2 and never exposes the low-level
/jobs endpoint. It delegates to the certified semantic ingress services.
"""
from __future__ import annotations

from typing import Any, Mapping

from mcp.server import MCPServer
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import AnyHttpUrl

from tools.mirror_sync.worker_requester_rbac import authorize_requester

from modules.worker_ingress.service import (
    get_job_status as _get_job_status,
    submit_objective as _submit_objective,
)

from .auth import EdarsahubTokenVerifier
from .config import WorkerMcpConfig


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _authenticated_user() -> dict[str, str]:
    access_token = get_access_token()
    if access_token is None:
        raise PermissionError("MCP_AUTH_REQUIRED")

    claims = (
        access_token.claims
        if isinstance(access_token.claims, Mapping)
        else {}
    )
    email = _clean(
        claims.get("email")
        or access_token.subject
    ).lower()

    if not email or "@" not in email:
        raise PermissionError("MCP_AUTH_IDENTITY_INVALID")

    authorization = authorize_requester(
        {
            "email": email,
            "source": "edarsahub-worker-mcp-tool",
            "project": "EDARSAHUB",
            "chat": "mcp",
        }
    )
    if authorization.get("allowed") is not True:
        raise PermissionError("MCP_AUTH_FORBIDDEN")

    return {
        "id": _clean(
            claims.get("user_id")
            or access_token.client_id
        ),
        "email": email,
        "role": _clean(claims.get("role")),
    }


def submit_objective_tool(
    objective: str,
    bounded_context: str,
    mode: str,
    capability: str,
    request_key: str | None = None,
    constraints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Submit one approved semantic objective to the EDARSAHUB Universal Worker."""
    current_user = _authenticated_user()

    payload: dict[str, Any] = {
        "objective": objective,
        "bounded_context": bounded_context,
        "mode": mode,
        "capability": capability,
        "constraints": constraints or {},
    }
    if request_key:
        payload["request_key"] = request_key

    result = _submit_objective(
        payload,
        current_user=current_user,
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
    _authenticated_user()

    result = _get_job_status(job_id)
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
    verifier = token_verifier or EdarsahubTokenVerifier(
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
