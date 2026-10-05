"""EDARSAHUB SQL-first authentication bridge for MCP."""
from __future__ import annotations

from typing import Any, Mapping

from mcp.server.auth.provider import AccessToken, TokenVerifier

from core.security import verify_token
from tools.mirror_sync.worker_requester_rbac import authorize_requester


WORKER_MCP_SCOPES = (
    "worker:submit",
    "worker:status",
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


class EdarsahubTokenVerifier(TokenVerifier):
    """Validate the existing EDARSAHUB JWT and SQL-first requester authority."""

    def __init__(self, *, resource_url: str):
        self.resource_url = _clean(resource_url)

    async def verify_token(
        self,
        token: str,
    ) -> AccessToken | None:
        try:
            payload = verify_token(token)
        except Exception:
            return None

        if not isinstance(payload, Mapping):
            return None

        email = _clean(payload.get("email")).lower()
        if not email or "@" not in email:
            return None

        authorization = authorize_requester(
            {
                "email": email,
                "source": "edarsahub-worker-mcp",
                "project": "EDARSAHUB",
                "chat": "mcp",
            }
        )

        if authorization.get("allowed") is not True:
            return None

        user_id = _clean(
            payload.get("user_id")
            or payload.get("usuario_id")
            or payload.get("sub")
            or payload.get("id")
        )

        role = _clean(payload.get("role"))

        return AccessToken(
            token=token,
            client_id=user_id or email,
            scopes=list(WORKER_MCP_SCOPES),
            subject=email,
            resource=self.resource_url,
            claims={
                "email": email,
                "role": role,
                "user_id": user_id,
            },
        )
