"""Runtime ownership policy for the EDARSAHUB scheduler."""

from __future__ import annotations

import os
from typing import Dict


ROLE_ENV = "EDARSA_RUNTIME_ROLE"
ROLE_REQUIRED_ENV = "EDARSA_RUNTIME_ROLE_REQUIRED"

LEGACY_EMBEDDED = "LEGACY_EMBEDDED"
PREVIEW_WEB = "PREVIEW_WEB"
PRODUCTION_WEB = "PRODUCTION_WEB"
PRODUCTION_SCHEDULER = "PRODUCTION_SCHEDULER"

VALID_ROLES = {
    LEGACY_EMBEDDED,
    PREVIEW_WEB,
    PRODUCTION_WEB,
    PRODUCTION_SCHEDULER,
}


def _truthy(name: str, default: str = "false") -> bool:
    return str(os.environ.get(name, default)).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def runtime_environment() -> str:
    raw = str(
        os.environ.get("EDARSA_ENV")
        or os.environ.get("APP_ENV")
        or os.environ.get("ENVIRONMENT")
        or ""
    ).strip().upper()

    if "PROD" in raw:
        return "PRODUCTION"
    if "PREVIEW" in raw:
        return "PREVIEW"
    if "DEV" in raw:
        return "DEVELOPMENT"
    if "TEST" in raw:
        return "TEST"
    return "UNKNOWN"


def scheduler_enabled() -> bool:
    return _truthy("SCHEDULER_ENABLED", "true")


def runtime_role_required() -> bool:
    return _truthy(ROLE_REQUIRED_ENV, "false")


def runtime_role() -> str:
    raw = str(os.environ.get(ROLE_ENV) or "").strip().upper()
    if not raw:
        return LEGACY_EMBEDDED
    if raw not in VALID_ROLES:
        raise RuntimeError(f"INVALID_EDARSA_RUNTIME_ROLE:{raw}")
    return raw


def runtime_policy_snapshot() -> Dict[str, object]:
    role = runtime_role()
    required = runtime_role_required()
    explicitly_configured = bool(str(os.environ.get(ROLE_ENV) or "").strip())

    return {
        "environment": runtime_environment(),
        "role": role,
        "role_required": required,
        "role_explicit": explicitly_configured,
        "scheduler_enabled": scheduler_enabled(),
        "legacy_fallback_active": (
            role == LEGACY_EMBEDDED and not explicitly_configured
        ),
    }


def should_start_embedded_scheduler() -> bool:
    """Return whether the FastAPI web process may own APScheduler."""
    if not scheduler_enabled():
        return False
    if runtime_role_required() and not str(os.environ.get(ROLE_ENV) or "").strip():
        return False
    return runtime_role() == LEGACY_EMBEDDED


def require_standalone_production_scheduler() -> Dict[str, object]:
    """Validate that this process is the explicit production scheduler owner."""
    snapshot = runtime_policy_snapshot()

    if not snapshot["scheduler_enabled"]:
        raise RuntimeError("PRODUCTION_SCHEDULER_DISABLED")
    if snapshot["environment"] != "PRODUCTION":
        raise RuntimeError(
            "PRODUCTION_SCHEDULER_REQUIRES_PRODUCTION_ENVIRONMENT"
        )
    if snapshot["role"] != PRODUCTION_SCHEDULER:
        raise RuntimeError(
            "PRODUCTION_SCHEDULER_REQUIRES_EXPLICIT_RUNTIME_ROLE"
        )
    if not snapshot["role_explicit"]:
        raise RuntimeError("PRODUCTION_SCHEDULER_ROLE_NOT_EXPLICIT")

    return snapshot
