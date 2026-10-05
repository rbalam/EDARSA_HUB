"""ASGI entrypoint for the EDARSAHUB Universal Worker MCP service."""
from __future__ import annotations

from .config import WorkerMcpConfig
from .server import (
    build_mcp_server,
    build_transport_security,
)


config = WorkerMcpConfig.from_env()
mcp = build_mcp_server(config)

app = mcp.streamable_http_app(
    json_response=True,
    stateless_http=True,
    transport_security=build_transport_security(config),
    host=config.bind_host,
)
