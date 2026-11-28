"""MCP adapter for the EDARSAHUB Universal Worker."""

__all__ = ["build_mcp_server"]


def __getattr__(name):
    if name == "build_mcp_server":
        from .server import build_mcp_server
        return build_mcp_server
    raise AttributeError(name)
