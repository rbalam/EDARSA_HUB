"""Bearer-token verification through the canonical EDARSAHUB ingress."""
from __future__ import annotations

import anyio
from mcp.server.auth.provider import AccessToken, TokenVerifier

from .client import verify_worker_access


WORKER_MCP_SCOPES = (
    "worker:submit",
    "worker:status",
)


class EdarsahubTokenVerifier(TokenVerifier):
    """Fail closed by asking the canonical RBAC-protected ingress."""

    def __init__(
        self,
        *,
        backend_url: str,
        resource_url: str,
    ):
        self.backend_url = backend_url.rstrip("/")
        self.resource_url = resource_url

    async def verify_token(
        self,
        token: str,
    ) -> AccessToken | None:
        allowed = await anyio.to_thread.run_sync(
            lambda: verify_worker_access(
                backend_url=self.backend_url,
                token=token,
            )
        )
        if not allowed:
            return None

        return AccessToken(
            token=token,
            client_id="edarsahub-authenticated-user",
            scopes=list(WORKER_MCP_SCOPES),
            resource=self.resource_url,
        )
