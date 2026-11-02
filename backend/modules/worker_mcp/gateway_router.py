"""HTTP-only reverse proxy for the existing EDARSAHUB MCP service.

Keep the Universal Worker and its authentication on their existing processes.
Configuration: EDARSAHUB_MCP_UPSTREAM_URL (default local supervisor port).
"""
from __future__ import annotations

import json
import logging
import os
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from starlette.background import BackgroundTask

from . import inprocess
from .config import WorkerMcpConfig, WorkerMcpConfigError
from .oauth_discovery import protected_resource_metadata
from .oauth_server import router as oauth_router
from .public_origin import PublicOriginError, public_https_origin

router = APIRouter(on_startup=[inprocess.start], on_shutdown=[inprocess.stop])
router.include_router(oauth_router)


class _InProcessResponse(Response):
    def __init__(self, inner_path: str):
        super().__init__()
        self._inner_path = inner_path

    async def __call__(self, scope, receive, send):
        await inprocess.dispatch(scope, receive, send, self._inner_path)


@router.api_route("/.well-known/oauth-protected-resource/api/mcp", methods=["GET", "OPTIONS"])
@router.api_route("/api/mcp/.well-known/oauth-protected-resource", methods=["GET", "OPTIONS"])
async def mcp_protected_resource_metadata(request: Request):
    """Publish the public MCP resource and canonical EDARSAHUB OAuth issuer.

    The gateway owns this public metadata because it knows the externally
    reachable origin. The isolated MCP process remains responsible only for
    MCP transport/tool execution; it must never advertise loopback URLs or
    become a second OAuth authority. This keeps discovery canonical across
    in-process and supervisor modes while preserving the same /api/mcp
    resource boundary exposed to ChatGPT and other remote MCP clients.
    """
    if request.method == "OPTIONS":
        return Response(status_code=204)
    try:
        origin = public_https_origin(request)
    except PublicOriginError:
        return JSONResponse(
            status_code=503,
            content={"detail": "MCP_PUBLIC_ORIGIN_UNAVAILABLE"},
        )
    payload = protected_resource_metadata(
        origin + "/api/mcp",
        origin + "/api/mcp/oauth",
    )
    return JSONResponse(
        content=payload,
        headers={"Cache-Control": "no-store"},
    )

_ALLOWED_RESPONSE_HEADERS = {
    "content-type", "cache-control", "www-authenticate", "mcp-session-id",
    "mcp-protocol-version", "retry-after",
}

logger = logging.getLogger("edarsahub.worker_mcp.gateway")

_MAX_CLASSIFY_BYTES = 65536
_KNOWN_PROTOCOL_VERSIONS = {
    "2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25", "2026-07-28",
}
_RPC_METHODS = {
    "initialize", "notifications/initialized", "tools/list", "tools/call", "ping",
}
_RPC_ERROR_CLASSES = {
    -32700: "parse_error", -32600: "invalid_request", -32601: "method_not_found",
    -32602: "invalid_params", -32603: "internal_error",
}
_PLAIN_ERROR_CLASSES = (
    ("invalid content-type", "content_type_invalid"),
    ("missing session id", "session_id_missing"),
    ("invalid host", "host_invalid"),
    ("invalid origin", "origin_invalid"),
)


def _jsonrpc_error_code(body: bytes) -> int | None:
    try:
        error = json.loads(body).get("error")
        code = error.get("code")
    except (ValueError, AttributeError):
        return None
    return code if isinstance(code, int) and not isinstance(code, bool) else None


def _classify_400(body: bytes) -> tuple[str, int | None]:
    """Return a closed-vocabulary error class; never any message text."""
    if len(body) > _MAX_CLASSIFY_BYTES:
        return "oversized", None
    code = _jsonrpc_error_code(body)
    if code is not None:
        return _RPC_ERROR_CLASSES.get(code, "jsonrpc_other"), code
    text = body.decode("utf-8", "ignore").lower()
    for needle, label in _PLAIN_ERROR_CLASSES:
        if needle in text:
            return label, None
    return "unclassified", None


def _request_rpc_method(body: bytes) -> str:
    if not body:
        return "absent"
    if len(body) > _MAX_CLASSIFY_BYTES:
        return "oversized"
    try:
        message = json.loads(body)
    except ValueError:
        return "unparseable"
    if isinstance(message, list):
        return "batch"
    method = message.get("method") if isinstance(message, dict) else None
    return method if method in _RPC_METHODS else "other"


def _header_categories(request: Request) -> dict[str, str]:
    content_type = request.headers.get("content-type")
    accept = (request.headers.get("accept") or "").lower()
    version = request.headers.get("mcp-protocol-version")
    if not content_type:
        content_type_class = "absent"
    elif content_type.split(";")[0].strip().lower() == "application/json":
        content_type_class = "json"
    else:
        content_type_class = "other"
    accept_class = "+".join(
        label for label, token in (("json", "application/json"), ("sse", "text/event-stream"))
        if token in accept
    ) or ("absent" if not accept else "other")
    if version is None:
        version_class = "absent"
    else:
        version_class = version if version in _KNOWN_PROTOCOL_VERSIONS else "unknown"
    return {
        "content_type": content_type_class,
        "accept": accept_class,
        "protocol_version": version_class,
        "has_session": str("mcp-session-id" in request.headers).lower(),
        "has_auth": str("authorization" in request.headers).lower(),
    }


def _log_upstream_400(request: Request, request_body: bytes, response_body: bytes) -> None:
    """Observability only: values come from fixed vocabularies, never from payloads."""
    try:
        error_class, code = _classify_400(response_body)
        cats = _header_categories(request)
        logger.warning(
            "mcp_upstream_400 method=%s rpc_method=%s content_type=%s accept=%s "
            "protocol_version=%s has_session=%s has_auth=%s request_bytes=%d "
            "error_class=%s jsonrpc_code=%s",
            request.method, _request_rpc_method(request_body), cats["content_type"],
            cats["accept"], cats["protocol_version"], cats["has_session"],
            cats["has_auth"], len(request_body), error_class, code,
        )
    except Exception:  # noqa: BLE001 - logging must never alter the proxied response
        pass


def _upstream() -> str:
    target = os.getenv("EDARSAHUB_MCP_UPSTREAM_URL", "").rstrip("/")
    parsed = urlparse(target)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in ("127.0.0.1", "localhost")
        or not parsed.port
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("MCP_UPSTREAM_LOCAL_ONLY")
    return target


@router.api_route("/api/mcp", methods=["GET", "POST", "DELETE", "OPTIONS", "HEAD"])
@router.api_route("/api/mcp/", methods=["GET", "POST", "DELETE", "OPTIONS", "HEAD"])
async def mcp_gateway(request: Request):
    """Preserve streaming and MCP protocol headers; never log bearer tokens."""
    if inprocess.enabled():
        return _InProcessResponse("/mcp")
    try:
        upstream = _upstream()
    except ValueError:
        return Response(status_code=503, content="MCP upstream not configured")

    headers = {
        name: value for name, value in request.headers.items()
        if name.lower() in {
            "authorization", "accept", "content-type", "mcp-session-id",
            "mcp-protocol-version", "last-event-id", "origin",
        }
    }
    client = httpx.AsyncClient(timeout=httpx.Timeout(connect=5, read=None, write=30, pool=5))
    try:
        outgoing = client.build_request(
            request.method,
            upstream + "/mcp",
            headers=headers,
            content=await request.body(),
        )
        reply = await client.send(outgoing, stream=True)
    except httpx.RequestError:
        await client.aclose()
        return Response(status_code=502, content="MCP upstream unavailable")

    response_headers = {
        name: value for name, value in reply.headers.items()
        if name.lower() in _ALLOWED_RESPONSE_HEADERS
    }
    if reply.status_code == 400:
        try:
            error_body = await reply.aread()
        except httpx.HTTPError:
            return Response(status_code=502, content="MCP upstream unavailable")
        finally:
            await reply.aclose()
            await client.aclose()
        _log_upstream_400(request, await request.body(), error_body)
        return Response(content=error_body, status_code=400, headers=response_headers)
    # The upstream advertises loopback resource metadata. Never expose it to clients.
    challenge = response_headers.get("www-authenticate")
    if challenge and "resource_metadata=" in challenge:
        try:
            public_origin = public_https_origin(request)
        except PublicOriginError:
            response_headers["www-authenticate"] = "Bearer"
        else:
            public_resource = (
                public_origin
                + "/api/mcp/.well-known/oauth-protected-resource"
            )
            import re
            response_headers["www-authenticate"] = re.sub(
                r'resource_metadata="[^"]+"',
                'resource_metadata="' + public_resource + '"',
                challenge,
            )

    async def close_connections():
        await reply.aclose()
        await client.aclose()

    return StreamingResponse(
        reply.aiter_raw(),
        status_code=reply.status_code,
        headers=response_headers,
        background=BackgroundTask(close_connections),
    )
