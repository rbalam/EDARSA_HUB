"""Pure fail-closed OAuth grant policy for the EDARSAHUB MCP boundary.

Security primitives only: does not issue tokens, register clients, create grants,
expose routes, or bypass canonical RBAC.
"""
from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlsplit

from .oauth_pkce import OAuthValidationError, validate_scopes

SUPPORTED_SCOPES = frozenset({"worker:status", "worker:submit"})


def require_tool_scope(required_scope: str, granted_scopes: frozenset[str]) -> None:
    """The MCP tool registry must supply its server-defined required scope."""
    if required_scope not in SUPPORTED_SCOPES:
        raise OAuthValidationError("TOOL_SCOPE_NOT_CONFIGURED")
    if not isinstance(granted_scopes, frozenset) or required_scope not in granted_scopes:
        raise OAuthValidationError("INSUFFICIENT_SCOPE")


def _validate_resource(url: str) -> None:
    if not isinstance(url, str) or not url:
        raise OAuthValidationError("RESOURCE_INVALID")
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as exc:
        raise OAuthValidationError("RESOURCE_INVALID") from exc
    if (
        parts.scheme != "https"
        or not parts.netloc
        or not parts.hostname
        or (port is not None and not (1 <= port <= 65535))
        or any(ch.isspace() for ch in url)
        or "\\" in url
        or parts.username is not None
        or parts.password is not None
        or parts.query
        or parts.fragment
        or url.endswith("/")
    ):
        raise OAuthValidationError("RESOURCE_INVALID")


def validate_grant(
    *,
    requested_scopes: str,
    identity_scopes: frozenset[str],
    consented_scopes: frozenset[str],
    resource: str,
    registered_resource: str,
    expires_at: datetime,
    revoked: bool,
) -> frozenset[str]:
    """Reject grants without active identity permissions and explicit consent."""
    if revoked:
        raise OAuthValidationError("GRANT_REVOKED")
    if not isinstance(expires_at, datetime) or expires_at.tzinfo is None:
        raise OAuthValidationError("EXPIRATION_INVALID")
    if expires_at <= datetime.now(timezone.utc):
        raise OAuthValidationError("GRANT_EXPIRED")
    _validate_resource(resource)
    _validate_resource(registered_resource)
    if resource != registered_resource:
        raise OAuthValidationError("RESOURCE_MISMATCH")
    granted = validate_scopes(requested_scopes, identity_scopes)
    if not isinstance(consented_scopes, frozenset) or not granted.issubset(consented_scopes):
        raise OAuthValidationError("CONSENT_REQUIRED")
    return granted
