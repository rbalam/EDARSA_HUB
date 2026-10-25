"""In-process MCP transport for the FastAPI backend (stateless; safe across replicas)."""
from __future__ import annotations

import logging
import os
from contextlib import AsyncExitStack

logger = logging.getLogger(__name__)

_app = None
_stack: AsyncExitStack | None = None


def enabled() -> bool:
    return os.getenv("EDARSAHUB_MCP_INPROCESS", "").strip() == "1"


async def start() -> None:
    global _app, _stack
    if not enabled() or _app is not None:
        return
    try:
        from .config import WorkerMcpConfig
        from .server import build_mcp_server, build_transport_security

        config = WorkerMcpConfig.from_env()
        mcp = build_mcp_server(
            config,
            stateless_http=True,
            json_response=True,
            streamable_http_path="/mcp",
            transport_security=build_transport_security(config),
        )
        app = mcp.streamable_http_app()
        stack = AsyncExitStack()
        await stack.enter_async_context(mcp.session_manager.run())
        _app, _stack = app, stack
        logger.info("MCP_INPROCESS_READY")
    except Exception as exc:  # noqa: BLE001 - MCP must never block ERP startup
        logger.error("MCP_INPROCESS_START_FAILED type=%s code=%s", type(exc).__name__, str(exc)[:80])


async def stop() -> None:
    global _app, _stack
    if _stack is not None:
        await _stack.aclose()
    _app, _stack = None, None


async def dispatch(scope, receive, send, inner_path: str) -> None:
    if _app is None:
        await send({"type": "http.response.start", "status": 503,
                    "headers": [(b"content-type", b"text/plain")]})
        await send({"type": "http.response.body", "body": b"MCP in-process unavailable"})
        return
    inner = dict(scope, path=inner_path, raw_path=inner_path.encode(), root_path="")
    await _app(inner, receive, send)
