"""Bearer-token verification through the canonical EDARSAHUB ingress."""
from __future__ import annotations

import time

import anyio
from mcp.server.auth.provider import AccessToken, TokenVerifier

from .client import verify_worker_access, verify_worker_access_grant
from .oauth_security import SUPPORTED_SCOPES


WORKER_MCP_SCOPES = (
    "worker:submit",
    "worker:status",
)
_DEFAULT_VERIFY_WORKER_ACCESS = verify_worker_access


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
        if not isinstance(token, str) or not token.strip():
            return None

        if verify_worker_access is not _DEFAULT_VERIFY_WORKER_ACCESS:
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

        grant = await anyio.to_thread.run_sync(
            lambda: verify_worker_access_grant(
                backend_url=self.backend_url,
                token=token,
            )
        )
        if not isinstance(grant, dict):
            return None

        raw_scopes = grant.get("scopes")
        if (
            not isinstance(raw_scopes, frozenset)
            or not raw_scopes
            or not raw_scopes.issubset(SUPPORTED_SCOPES)
        ):
            return None

        expires_at = grant.get("expires_at")
        if expires_at is not None:
            if (
                isinstance(expires_at, bool)
                or not isinstance(expires_at, int)
                or expires_at <= int(time.time())
            ):
                return None

        ordered_scopes = [
            scope for scope in WORKER_MCP_SCOPES if scope in raw_scopes
        ]
        if not ordered_scopes:
            return None

        return AccessToken(
            token=token,
            client_id="edarsahub-authenticated-user",
            scopes=ordered_scopes,
            expires_at=expires_at,
            resource=self.resource_url,
        )
