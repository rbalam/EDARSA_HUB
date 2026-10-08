"""HTTP-only reverse proxy for the existing EDARSAHUB MCP service.

Keep the Universal Worker and its authentication on their existing processes.
Configuration: EDARSAHUB_MCP_UPSTREAM_URL (default local supervisor port).
"""
from __future__ import annotations

import os
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import Response, StreamingResponse
from starlette.background import BackgroundTask

router = APIRouter()

_ALLOWED_RESPONSE_HEADERS = {
    "content-type", "cache-control", "www-authenticate", "mcp-session-id",
    "mcp-protocol-version", "retry-after",
}


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
    # The upstream advertises loopback resource metadata. Never expose it to clients.
    challenge = response_headers.get("www-authenticate")
    if challenge and "resource_metadata=" in challenge:
        public_resource = str(request.base_url).rstrip("/") + "/.well-known/oauth-protected-resource/api/mcp"
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
