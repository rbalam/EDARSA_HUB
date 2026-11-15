"""Minimal MCP transport for the certified EDARSAHUB semantic ingress."""

from contextvars import ContextVar
import json
import time
from typing import Any

try:
    from mcp.server import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError
except ImportError:  # mcp 1.x (backend-compatible: starlette 0.37)
    from mcp.server.fastmcp import FastMCP as MCPServer
    try:
        from mcp.server.fastmcp.exceptions import ToolError
    except ImportError:
        class ToolError(ValueError):  # type: ignore[no-redef]
            pass
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.middleware.bearer_auth import (
    AuthenticatedUser,
    RequireAuthMiddleware,
)
from mcp.server.auth.provider import TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import AnyHttpUrl
from starlette.routing import Route

from .auth import EdarsahubTokenVerifier
from .client import (
    WorkerMcpAuthorizationError,
    WorkerMcpValidationError,
    get_job_status as backend_get_job_status,
    submit_objective as backend_submit_objective,
)
from .config import WorkerMcpConfig
from .oauth_discovery import MCP_SCOPES
from .oauth_pkce import OAuthValidationError
from .oauth_security import SUPPORTED_SCOPES, require_tool_scope


_BACKEND_URL: str | None = None
SUBMIT_OBJECTIVE_SCOPE = "worker:submit"
GET_JOB_STATUS_SCOPE = "worker:status"
TOOL_REQUIRED_SCOPES: dict[str, str] = {
    "submit_objective": SUBMIT_OBJECTIVE_SCOPE,
    "get_job_status": GET_JOB_STATUS_SCOPE,
}
ADVERTISED_MCP_SCOPE_STRING = " ".join(MCP_SCOPES)
_MAX_INSPECT_BODY_BYTES = 262144
_PENDING_HTTP_AUTH_CHALLENGE: ContextVar[dict[str, Any] | None] = ContextVar(
    "edarsahub_mcp_http_auth_challenge",
    default=None,
)


def build_www_authenticate_header(
    *,
    error: str,
    description: str,
    resource_metadata_url: Any | None = None,
    scope: str | None = None,
) -> str:
    parts = [
        f'error="{error}"',
        f'error_description="{description}"',
    ]
    if resource_metadata_url:
        parts.append(f'resource_metadata="{resource_metadata_url}"')
    if scope:
        parts.append(f'scope="{scope}"')
    return "Bearer " + ", ".join(parts)


def _step_up_scope_string(
    granted_scopes: frozenset[str],
    required_scope: str,
) -> str:
    combined = granted_scopes | {required_scope}
    ordered = [scope for scope in MCP_SCOPES if scope in combined]
    return " ".join(ordered) if ordered else ADVERTISED_MCP_SCOPE_STRING


def _extract_tool_scope_checks(raw_body: bytes) -> list[tuple[str, str]]:
    if not raw_body:
        return []
    try:
        decoded = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return []

    items = decoded if isinstance(decoded, list) else [decoded]
    checks: list[tuple[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("method") != "tools/call":
            continue
        params = item.get("params")
        if not isinstance(params, dict):
            continue
        tool_name = params.get("name")
        if isinstance(tool_name, str) and tool_name in TOOL_REQUIRED_SCOPES:
            checks.append((tool_name, TOOL_REQUIRED_SCOPES[tool_name]))
    return checks


class McpOAuthBoundaryEndpoint:
    """ASGI OAuth 2.1 + RFC 6750/9728 boundary for MCP HTTP requests.

    - Emits HTTP 401 with WWW-Authenticate advertising available MCP scopes
      without granting any scope automatically.
    - Emits HTTP 403 insufficient_scope with WWW-Authenticate step-up scope
      challenge when a tool call lacks its required scope, preserving HTTP 200
      for valid operations and keeping get_job_status accessible with
      worker:status.
    """

    def __init__(
        self,
        app: Any,
        *,
        resource_metadata_url: Any | None = None,
    ):
        self.app = app
        self.resource_metadata_url = resource_metadata_url

    async def _send_json(
        self,
        send: Any,
        *,
        status_code: int,
        payload: dict[str, Any],
        www_authenticate: str | None = None,
    ) -> None:
        body_bytes = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        headers: list[tuple[bytes, bytes]] = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body_bytes)).encode("ascii")),
            (b"cache-control", b"no-store"),
        ]
        if www_authenticate:
            headers.append(
                (b"www-authenticate", www_authenticate.encode("utf-8"))
            )
        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": headers,
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body_bytes,
                "more_body": False,
            }
        )

    async def _send_unauthorized(
        self,
        send: Any,
        description: str = "Authentication required",
    ) -> None:
        challenge = build_www_authenticate_header(
            error="invalid_token",
            description=description,
            resource_metadata_url=self.resource_metadata_url,
            scope=ADVERTISED_MCP_SCOPE_STRING,
        )
        await self._send_json(
            send,
            status_code=401,
            payload={
                "error": "invalid_token",
                "error_description": description,
            },
            www_authenticate=challenge,
        )

    async def _send_insufficient_scope(
        self,
        send: Any,
        *,
        required_scope: str,
        granted_scopes: frozenset[str],
        tool_name: str | None = None,
    ) -> None:
        description = f"Insufficient scope; required scope: {required_scope}"
        challenge = build_www_authenticate_header(
            error="insufficient_scope",
            description=description,
            resource_metadata_url=self.resource_metadata_url,
            scope=_step_up_scope_string(granted_scopes, required_scope),
        )
        payload: dict[str, Any] = {
            "error": "insufficient_scope",
            "error_description": description,
            "required_scope": required_scope,
            "code": "INSUFFICIENT_SCOPE",
        }
        if tool_name:
            payload["tool"] = tool_name
        await self._send_json(
            send,
            status_code=403,
            payload=payload,
            www_authenticate=challenge,
        )

    async def _send_forbidden(self, send: Any, *, code: str) -> None:
        await self._send_json(
            send,
            status_code=403,
            payload={
                "error": "access_denied",
                "error_description": "Authorization forbidden for requested operation",
                "code": code,
            },
        )

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        auth_user = scope.get("user")
        if not isinstance(auth_user, AuthenticatedUser):
            await self._send_unauthorized(send)
            return

        access_token = getattr(auth_user, "access_token", None)
        if access_token is None or not getattr(access_token, "token", None):
            await self._send_unauthorized(send)
            return

        expires_at = getattr(access_token, "expires_at", None)
        if expires_at is not None:
            if (
                isinstance(expires_at, bool)
                or not isinstance(expires_at, (int, float))
                or expires_at <= time.time()
            ):
                await self._send_unauthorized(
                    send,
                    description="Access token expired",
                )
                return

        raw_scopes = getattr(auth_user, "scopes", None)
        if not isinstance(raw_scopes, (list, tuple, set, frozenset)):
            await self._send_unauthorized(send)
            return
        granted_scopes = frozenset(
            str(item) for item in raw_scopes if isinstance(item, str) and item
        )
        if not granted_scopes or not granted_scopes.issubset(SUPPORTED_SCOPES):
            await self._send_unauthorized(send)
            return

        downstream_receive = receive
        if str(scope.get("method") or "").upper() == "POST":
            buffered_messages: list[dict[str, Any]] = []
            body_chunks: list[bytes] = []
            total_bytes = 0
            overflow = False
            while True:
                message = await receive()
                buffered_messages.append(message)
                msg_type = message.get("type")
                if msg_type == "http.request":
                    chunk = message.get("body", b"") or b""
                    total_bytes += len(chunk)
                    if total_bytes > _MAX_INSPECT_BODY_BYTES:
                        overflow = True
                        break
                    body_chunks.append(chunk)
                    if not message.get("more_body", False):
                        break
                else:
                    break

            if not overflow:
                for tool_name, required_scope in _extract_tool_scope_checks(
                    b"".join(body_chunks)
                ):
                    try:
                        require_tool_scope(required_scope, granted_scopes)
                    except OAuthValidationError:
                        await self._send_insufficient_scope(
                            send,
                            required_scope=required_scope,
                            granted_scopes=granted_scopes,
                            tool_name=tool_name,
                        )
                        return

            replay_index = 0

            async def _replay_receive() -> dict[str, Any]:
                nonlocal replay_index
                if replay_index < len(buffered_messages):
                    msg = buffered_messages[replay_index]
                    replay_index += 1
                    return msg
                return await receive()

            downstream_receive = _replay_receive

        ctx_token = _PENDING_HTTP_AUTH_CHALLENGE.set(None)
        suppressed = False
        try:
            async def _intercept_send(event: dict[str, Any]) -> None:
                nonlocal suppressed
                pending = _PENDING_HTTP_AUTH_CHALLENGE.get()
                if pending is not None and event.get("type") == "http.response.start":
                    suppressed = True
                    _PENDING_HTTP_AUTH_CHALLENGE.set(None)
                    kind = pending.get("kind")
                    if pending.get("status") == 401 or kind == "invalid_token":
                        await self._send_unauthorized(send)
                    elif kind == "insufficient_scope":
                        await self._send_insufficient_scope(
                            send,
                            required_scope=str(
                                pending.get("required_scope")
                                or SUBMIT_OBJECTIVE_SCOPE
                            ),
                            granted_scopes=granted_scopes,
                            tool_name=pending.get("tool_name"),
                        )
                    else:
                        await self._send_forbidden(
                            send,
                            code=str(
                                pending.get("code")
                                or "AUTHORIZATION_FORBIDDEN"
                            ),
                        )
                    return
                if suppressed and event.get("type") == "http.response.body":
                    return
                await send(event)

            await self.app(scope, downstream_receive, _intercept_send)
        finally:
            _PENDING_HTTP_AUTH_CHALLENGE.reset(ctx_token)


def _attach_oauth_stepup_boundary(starlette_app: Any) -> Any:
    routes = getattr(starlette_app, "routes", None)
    if not isinstance(routes, list):
        return starlette_app
    for idx, route in enumerate(routes):
        endpoint = getattr(route, "endpoint", None)
        if isinstance(route, Route) and isinstance(
            endpoint,
            RequireAuthMiddleware,
        ):
            routes[idx] = Route(
                route.path,
                endpoint=McpOAuthBoundaryEndpoint(
                    endpoint.app,
                    resource_metadata_url=endpoint.resource_metadata_url,
                ),
            )
    return starlette_app


def _bearer_token() -> str:
    access_token = get_access_token()
    if access_token is None or not access_token.token:
        raise PermissionError("MCP_AUTH_REQUIRED")
    return str(access_token.token)


_DEFAULT_BEARER_TOKEN = _bearer_token


def _authorized_bearer_token(required_scope: str) -> str:
    access_token = get_access_token()
    if access_token is None:
        if _bearer_token is not _DEFAULT_BEARER_TOKEN:
            token = _bearer_token()
            if not token:
                _PENDING_HTTP_AUTH_CHALLENGE.set(
                    {"status": 401, "kind": "invalid_token"}
                )
                raise PermissionError("MCP_AUTH_REQUIRED")
            return str(token)
        _PENDING_HTTP_AUTH_CHALLENGE.set(
            {"status": 401, "kind": "invalid_token"}
        )
        raise PermissionError("MCP_AUTH_REQUIRED")

    if not access_token.token:
        _PENDING_HTTP_AUTH_CHALLENGE.set(
            {"status": 401, "kind": "invalid_token"}
        )
        raise PermissionError("MCP_AUTH_REQUIRED")

    expires_at = getattr(access_token, "expires_at", None)
    if expires_at is not None:
        if (
            isinstance(expires_at, bool)
            or not isinstance(expires_at, (int, float))
            or expires_at <= time.time()
        ):
            _PENDING_HTTP_AUTH_CHALLENGE.set(
                {"status": 401, "kind": "invalid_token"}
            )
            raise PermissionError("MCP_TOKEN_EXPIRED")

    raw_scopes = getattr(access_token, "scopes", None)
    if not isinstance(raw_scopes, (list, tuple, set, frozenset)):
        _PENDING_HTTP_AUTH_CHALLENGE.set(
            {
                "status": 403,
                "kind": "insufficient_scope",
                "required_scope": required_scope,
            }
        )
        raise PermissionError("MCP_SCOPE_FORBIDDEN:INSUFFICIENT_SCOPE")

    granted_scopes = frozenset(
        str(item) for item in raw_scopes if isinstance(item, str) and item
    )
    try:
        require_tool_scope(required_scope, granted_scopes)
    except OAuthValidationError as exc:
        _PENDING_HTTP_AUTH_CHALLENGE.set(
            {
                "status": 403,
                "kind": "insufficient_scope",
                "required_scope": required_scope,
            }
        )
        raise PermissionError(f"MCP_SCOPE_FORBIDDEN:{exc}") from exc

    return str(access_token.token)


def _backend_url() -> str:
    if not _BACKEND_URL:
        raise RuntimeError("MCP_BACKEND_NOT_CONFIGURED")
    return _BACKEND_URL


def _raise_mapped_upstream_error(
    exc: WorkerMcpAuthorizationError | WorkerMcpValidationError,
    *,
    default_required_scope: str,
    tool_name: str,
) -> None:
    if isinstance(exc, WorkerMcpValidationError):
        status_num = int(exc.status_code or 422)
        raise ToolError(
            f"VALIDATION_ERROR_{status_num}:{exc.reason_code}"
        ) from exc

    if exc.status_code == 401 or exc.code == "AUTHENTICATION_REQUIRED":
        _PENDING_HTTP_AUTH_CHALLENGE.set(
            {"status": 401, "kind": "invalid_token"}
        )
        raise PermissionError("MCP_AUTH_REQUIRED") from exc

    if exc.code == "INSUFFICIENT_SCOPE":
        req_scope = exc.required_scope or default_required_scope
        _PENDING_HTTP_AUTH_CHALLENGE.set(
            {
                "status": 403,
                "kind": "insufficient_scope",
                "required_scope": req_scope,
                "tool_name": tool_name,
            }
        )
        raise PermissionError(
            "MCP_SCOPE_FORBIDDEN:INSUFFICIENT_SCOPE"
        ) from exc

    _PENDING_HTTP_AUTH_CHALLENGE.set(
        {
            "status": 403,
            "kind": "access_denied",
            "code": exc.code,
            "tool_name": tool_name,
        }
    )
    raise PermissionError(f"MCP_AUTHORIZATION_FORBIDDEN:{exc.code}") from exc


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

    token = _authorized_bearer_token(SUBMIT_OBJECTIVE_SCOPE)
    try:
        result = backend_submit_objective(
            backend_url=_backend_url(),
            token=token,
            payload=payload,
        )
    except (WorkerMcpAuthorizationError, WorkerMcpValidationError) as exc:
        _raise_mapped_upstream_error(
            exc,
            default_required_scope=SUBMIT_OBJECTIVE_SCOPE,
            tool_name="submit_objective",
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
    token = _authorized_bearer_token(GET_JOB_STATUS_SCOPE)
    try:
        result = backend_get_job_status(
            backend_url=_backend_url(),
            token=token,
            job_id=job_id,
        )
    except (WorkerMcpAuthorizationError, WorkerMcpValidationError) as exc:
        _raise_mapped_upstream_error(
            exc,
            default_required_scope=GET_JOB_STATUS_SCOPE,
            tool_name="get_job_status",
        )
    return {
        "job_id": result.get("job_id"),
        "lifecycle": result.get("lifecycle"),
        "status": result.get("status"),
        "certification": result.get("certification"),
        "work_completion": result.get("work_completion"),
        "certification_basis": result.get("certification_basis"),
        "certified_source_sha": result.get("certified_source_sha"),
        "converged_head": result.get("converged_head"),
        "quality_gate": result.get("quality_gate"),
        "tests": result.get("tests"),
        "percent_complete": result.get("percent_complete"),
        "blockers": result.get("blockers"),
        "files_changed": result.get("files_changed"),
        "commit_sha": result.get("commit_sha"),
        "git_sync_status": result.get("git_sync_status"),
        "terminal_result_valid": result.get("terminal_result_valid"),
        "result_state": result.get("result_state"),
        "production_touched": result.get(
            "production_touched",
            False,
        ),
        "summary_es": result.get("summary_es"),
        "result_detail_evidence": result.get(
            "result_detail_evidence"
        ),
    }


def build_mcp_server(
    config: WorkerMcpConfig,
    *,
    token_verifier: TokenVerifier | None = None,
    **settings: Any,
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
        **settings,
    )

    mcp.tool(
        name="submit_objective",
        title="Submit EDARSAHUB objective",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(submit_objective_tool)

    mcp.tool(
        name="get_job_status",
        title="Get EDARSAHUB Worker job status",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(get_job_status_tool)

    orig_streamable_http_app = mcp.streamable_http_app

    def _wrapped_streamable_http_app(*app_args: Any, **app_kwargs: Any) -> Any:
        starlette_app = orig_streamable_http_app(*app_args, **app_kwargs)
        return _attach_oauth_stepup_boundary(starlette_app)

    mcp.streamable_http_app = _wrapped_streamable_http_app  # type: ignore[method-assign]
    return mcp


def build_transport_security(
    config: WorkerMcpConfig,
) -> TransportSecuritySettings:
    return TransportSecuritySettings(
        allowed_hosts=list(config.allowed_hosts),
        allowed_origins=list(config.allowed_origins),
    )
