"""Canonical scheduling metadata and conflict policy for Universal Worker.

This module is the single source of truth for scheduling normalization.
It does not execute jobs, touch Git, access SQL, or enable parallel execution.
"""
from __future__ import annotations

from typing import Any, NamedTuple

PRIORITY_ORDER = {"P0": 0, "P1": 10, "HIGH": 20, "NORMAL": 50, "LOW": 80}


GLOBAL_CONFLICT_DOMAINS = {"CORE", "GLOBAL_GIT_WRITER", "GLOBAL_FRONTEND_REGISTRY", "GLOBAL_NAVIGATION"}


class SchedulingMeta(NamedTuple):
    project_id: str
    bounded_context: str
    resource_claims: tuple[str, ...]
    conflict_domains: tuple[str, ...]
    priority_class: str
    fairness_weight: int
    max_parallelism: int
    mode: str
    legacy_defaults: bool


def _norm(values: Iterable[Any]) -> tuple[str, ...]:
    return tuple(sorted({str(v).strip() for v in values if str(v).strip()}))


def _safe_int(value: Any, default: int, minimum: int = 1, maximum: int = 64) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, n))


def normalize_metadata(job: dict[str, Any]) -> SchedulingMeta:
    sched = job.get("scheduling")
    legacy = not isinstance(sched, dict)
    sched = sched if isinstance(sched, dict) else {}

    project_id = str(sched.get("project_id") or ("LEGACY_GLOBAL" if legacy else "UNSPECIFIED")).strip()
    bounded_context = str(sched.get("bounded_context") or ("LEGACY_GLOBAL" if legacy else project_id)).strip()

    claims = _norm(sched.get("resource_claims") or ())
    domains = _norm(sched.get("conflict_domains") or ())
    if legacy:
        domains = ("GLOBAL_GIT_WRITER",)

    priority = str(sched.get("priority_class") or "NORMAL").upper().strip()
    if priority not in PRIORITY_ORDER:
        priority = "NORMAL"

    return SchedulingMeta(
        project_id=project_id,
        bounded_context=bounded_context,
        resource_claims=claims,
        conflict_domains=domains,
        priority_class=priority,
        fairness_weight=_safe_int(sched.get("fairness_weight"), 1),
        max_parallelism=_safe_int(sched.get("max_parallelism"), 1),
        mode=str(job.get("mode") or "").upper().strip(),
        legacy_defaults=legacy,
    )


def claims_conflict(a: SchedulingMeta, b: SchedulingMeta) -> bool:
    ad = set(a.conflict_domains)
    bd = set(b.conflict_domains)
    if ad & bd:
        return True
    return bool(set(a.resource_claims) & set(b.resource_claims))


def can_shadow_parallel(a: SchedulingMeta, b: SchedulingMeta) -> bool:
    if claims_conflict(a, b):
        return False
    if a.mode == "READ_ONLY" and b.mode == "READ_ONLY":
        return True
    if a.legacy_defaults or b.legacy_defaults:
        return False
    if not a.resource_claims or not b.resource_claims:
        return False
    return True


def fairness_key(row: dict[str, Any], served: dict[str, int] | None = None) -> tuple[Any, ...]:
    served = served or {}
    meta: SchedulingMeta = row["meta"]
    project_served = int(served.get(meta.project_id, 0))
    normalized_service = project_served / max(meta.fairness_weight, 1)
    job_id = str(row["job"].get("job_id") or "")
    return (PRIORITY_ORDER[meta.priority_class], normalized_service, meta.project_id, job_id)
