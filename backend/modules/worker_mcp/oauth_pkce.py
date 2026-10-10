"""Side-effect-free OAuth 2.0 PKCE validation primitives for MCP.

Not an authorization server. No tokens or grants are issued by this module.
The actual authorization server must bind grants to an authenticated EDARSAHUB
identity with explicit RBAC approval before any service credential exchange.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import re
from urllib.parse import urlsplit

_ALLOWED_SCOPES = frozenset({"worker:submit", "worker:status"})
_PKCE_RE = re.compile(r"^[A-Za-z0-9._~-]{43,128}$")
_CLIENT_ID_RE = re.compile(r"^[A-Za-z0-9._~-]{8,128}$")


class OAuthValidationError(ValueError):
    """A requested OAuth operation does not satisfy security requirements."""


def validate_pkce_challenge(challenge: str, method: str) -> str:
    """Require SHA-256 PKCE; plain or missing PKCE never falls back."""
    if method != "S256" or not isinstance(challenge, str) or not _PKCE_RE.fullmatch(challenge):
        raise OAuthValidationError("PKCE_S256_REQUIRED")
    # SHA-256 challenges use exactly 43 unpadded URL-safe base64 characters.
    if len(challenge) != 43 or "=" in challenge:
        raise OAuthValidationError("PKCE_INVALID_CHALLENGE")
    return challenge


def verify_pkce(verifier: str, challenge: str) -> bool:
    """Constant-time comparison; rejects short, malformed, or oversized verifiers."""
    if not isinstance(verifier, str) or not _PKCE_RE.fullmatch(verifier):
        return False
    try:
        validate_pkce_challenge(challenge, "S256")
    except OAuthValidationError:
        return False
    actual = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
    return hmac.compare_digest(actual, challenge)


def validate_redirect_uri(uri: str, registered_uris: tuple[str, ...]) -> str:
    """Exact redirect URI matching; never allow wildcards or partial prefixes."""
    if not isinstance(uri, str) or not uri or uri not in registered_uris:
        raise OAuthValidationError("REDIRECT_URI_NOT_REGISTERED")
    parts = urlsplit(uri)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.fragment:
        raise OAuthValidationError("REDIRECT_URI_INVALID")
    return uri


def validate_scopes(raw: str, allowed_for_identity: frozenset[str]) -> frozenset[str]:
    """Never grant a scope based only on a caller's request."""
    if not isinstance(raw, str):
        raise OAuthValidationError("SCOPES_INVALID")
    scopes = raw.split()
    if len(scopes) != len(set(scopes)):
        raise OAuthValidationError("SCOPES_DUPLICATED")
    requested = frozenset(scopes)
    if not requested or not requested.issubset(_ALLOWED_SCOPES):
        raise OAuthValidationError("SCOPES_INVALID")
    if not requested.issubset(allowed_for_identity):
        raise OAuthValidationError("SCOPES_FORBIDDEN")
    return requested


def validate_client_id(value: str, registered_ids: frozenset[str]) -> str:
    """Fail closed: a claimed client ID is not proof of client registration."""
    if not isinstance(value, str) or not _CLIENT_ID_RE.fullmatch(value) or value not in registered_ids:
        raise OAuthValidationError("CLIENT_NOT_REGISTERED")
    return value
