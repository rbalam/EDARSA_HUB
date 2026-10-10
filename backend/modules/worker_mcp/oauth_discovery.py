"""OAuth discovery contract for EDARSAHUB MCP (independent of FastAPI backend).

This module deliberately does not publish authorization or token routes. It must
not be mounted publicly until a consent/RBAC-bound authorization server exists.
"""
from __future__ import annotations

from urllib.parse import urlsplit

MCP_SCOPES = ("worker:status", "worker:submit")


class DiscoveryConfigurationError(ValueError):
    pass


def _https_url(value: str, field: str) -> str:
    if not isinstance(value, str) or not value or value.endswith("/"):
        raise DiscoveryConfigurationError(field)
    url = urlsplit(value)
    if (url.scheme != "https" or not url.netloc or not url.hostname
            or url.username is not None or url.password is not None
            or url.query or url.fragment):
        raise DiscoveryConfigurationError(field)
    return value


def authorization_metadata(issuer_url: str) -> dict:
    """RFC 8414 metadata; publish only when endpoints actually exist."""
    issuer = _https_url(issuer_url, "OAUTH_ISSUER_HTTPS_REQUIRED")
    return {
        "issuer": issuer,
        "authorization_endpoint": issuer + "/authorize",
        "token_endpoint": issuer + "/token",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
        "scopes_supported": list(MCP_SCOPES),
    }


def protected_resource_metadata(resource_url: str, issuer_url: str) -> dict:
    """RFC 9728: resource and issuer are independent trust domains."""
    resource = _https_url(resource_url, "RESOURCE_HTTPS_REQUIRED")
    issuer = _https_url(issuer_url, "OAUTH_ISSUER_HTTPS_REQUIRED")
    return {
        "resource": resource,
        "authorization_servers": [issuer],
        "scopes_supported": list(MCP_SCOPES),
        "bearer_methods_supported": ["header"],
    }


def validate_public_mcp_origin(resource_url: str, public_origin: str) -> None:
    """Guard against advertising metadata for the wrong public resource."""
    resource = _https_url(resource_url, "RESOURCE_HTTPS_REQUIRED")
    origin = _https_url(public_origin, "PUBLIC_ORIGIN_HTTPS_REQUIRED")
    parsed = urlsplit(origin)
    if parsed.path:
        raise DiscoveryConfigurationError("PUBLIC_ORIGIN_MUST_NOT_HAVE_PATH")
    r = urlsplit(resource)
    if (r.scheme, r.netloc) != (parsed.scheme, parsed.netloc):
        raise DiscoveryConfigurationError("PUBLIC_ORIGIN_MISMATCH")
