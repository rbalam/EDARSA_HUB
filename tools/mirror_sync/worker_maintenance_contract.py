"""Canonical authority contract for EDARSAHUB Worker maintenance roles.

This module contains policy only. It performs no Git, SQL, shell, network,
service, Production, or repository mutation.

Worker Repair and Worker Auditor are maintenance-plane roles. They are not
alternate application-development workers and must never consume normal
EDARSAHUB development jobs.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Final


WORKER_INFRASTRUCTURE_ROOTS: Final[tuple[str, ...]] = (
    "tools/mirror_sync/",
    "backend/modules/worker_runtime_wake/",
    "backend/tests/test_worker_",
    "backend/tests/test_universal_worker_",
    ".github/workflows/universal-worker-",
    ".github/workflows/worker-",
)

FORBIDDEN_APPLICATION_ROOTS: Final[tuple[str, ...]] = (
    "backend/modules/comercial/",
    "backend/modules/finanzas/",
    "backend/modules/inventarios/",
    "backend/modules/operaciones/",
    "backend/modules/crm/",
    "frontend/",
)

PROTECTED_UNIVERSAL_COMPONENTS: Final[frozenset[str]] = frozenset(
    {
        "tools/mirror_sync/universal_job_bridge.py",
        "tools/mirror_sync/universal_job_dispatcher.py",
        "tools/mirror_sync/universal_job_result_publisher.py",
        "tools/mirror_sync/runtime_health_publisher.py",
        "tools/mirror_sync/worker_control_plane.py",
        "tools/mirror_sync/worker_runtime_fingerprint.py",
        "tools/mirror_sync/gate_chain_publisher.py",
        "tools/mirror_sync/git_divergence_guard.py",
    }
)


@dataclass(frozen=True)
class MaintenanceAuthority:
    role: str
    mutation_allowed: bool
    production_allowed: bool
    normal_development_jobs_allowed: bool


REPAIR_AUTHORITY: Final = MaintenanceAuthority(
    role="WORKER_REPAIR",
    mutation_allowed=True,
    production_allowed=False,
    normal_development_jobs_allowed=False,
)

AUDITOR_AUTHORITY: Final = MaintenanceAuthority(
    role="WORKER_AUDITOR",
    mutation_allowed=False,
    production_allowed=False,
    normal_development_jobs_allowed=False,
)


def normalize_repo_path(path: str) -> str:
    value = str(PurePosixPath(path.strip()))

    if not value or value == ".":
        raise ValueError("MAINTENANCE_PATH_EMPTY")

    if value.startswith("../") or value.startswith("/"):
        raise ValueError("MAINTENANCE_PATH_ESCAPE")

    return value


def is_worker_infrastructure_path(path: str) -> bool:
    value = normalize_repo_path(path)

    return any(
        value.startswith(root)
        for root in WORKER_INFRASTRUCTURE_ROOTS
    )


def repair_scope_allowed(paths: list[str] | tuple[str, ...]) -> bool:
    if not paths:
        return False

    normalized = [normalize_repo_path(path) for path in paths]

    if any(
        any(path.startswith(root) for root in FORBIDDEN_APPLICATION_ROOTS)
        for path in normalized
    ):
        return False

    return all(is_worker_infrastructure_path(path) for path in normalized)


def auditor_scope_allowed(paths: list[str] | tuple[str, ...]) -> bool:
    return repair_scope_allowed(paths)
