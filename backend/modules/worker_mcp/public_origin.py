"""Resolve the externally reachable HTTPS origin behind trusted reverse proxies."""
from __future__ import annotations

from urllib.parse import urlsplit


class PublicOriginError(ValueError):
    pass


def _first_forwarded(value: str | None) -> str:
    return str(value or "").split(",", 1)[0].strip()


def public_https_origin(request) -> str:
    """Return a validated public HTTPS origin from proxy-aware request headers.

    EDARSAHUB Preview is terminated at Cloudflare/Emergent and forwarded to
    FastAPI over an internal hop. Never advertise that internal scheme/host to
    remote MCP/OAuth clients.
    """
    forwarded_proto = _first_forwarded(
        request.headers.get("x-forwarded-proto")
    ).lower()
    forwarded_host = _first_forwarded(
        request.headers.get("x-forwarded-host")
    )

    scheme = forwarded_proto or str(request.url.scheme or "").lower()
    host = forwarded_host or _first_forwarded(request.headers.get("host"))

    if scheme != "https" or not host:
        raise PublicOriginError("PUBLIC_HTTPS_ORIGIN_REQUIRED")

    if any(ch in host for ch in ("\r", "\n", "\t", " ", "/", "\\")):
        raise PublicOriginError("PUBLIC_HOST_INVALID")

    candidate = f"https://{host}"
    parsed = urlsplit(candidate)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise PublicOriginError("PUBLIC_ORIGIN_INVALID")

    return f"https://{parsed.netloc}"
