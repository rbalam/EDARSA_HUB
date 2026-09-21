#!/usr/bin/env python3
"""Observation-only multi-project scheduler for the EDARSAHUB Universal Worker.

Shadow mode only:
- never moves queue files;
- never executes jobs;
- never acquires writer locks;
- never changes Git branches;
- only reads pending/processing envelopes and emits a deterministic decision.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable, NamedTuple

ROOT = Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
STATE = ROOT / ".git" / "universal-worker-queue"
PENDING = STATE / "pending"
PROCESSING = STATE / "processing"

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


def load_envelopes(folder: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not folder.is_dir():
        return rows
    for path in sorted(folder.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        job = doc.get("job") if isinstance(doc, dict) and isinstance(doc.get("job"), dict) else doc
        if not isinstance(job, dict):
            continue
        rows.append({"path": str(path), "job": job, "meta": normalize_metadata(job)})
    return rows


def fairness_key(row: dict[str, Any], served: dict[str, int] | None = None) -> tuple[Any, ...]:
    served = served or {}
    meta: SchedulingMeta = row["meta"]
    project_served = int(served.get(meta.project_id, 0))
    normalized_service = project_served / max(meta.fairness_weight, 1)
    job_id = str(row["job"].get("job_id") or "")
    return (PRIORITY_ORDER[meta.priority_class], normalized_service, meta.project_id, job_id)


def choose_shadow_slots(
    pending: list[dict[str, Any]],
    active: list[dict[str, Any]],
    *,
    max_slots: int = 4,
    served: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    project_counts: dict[str, int] = {}
    ordered = sorted(pending, key=lambda row: fairness_key(row, served))

    active_meta = [row["meta"] for row in active]
    for row in ordered:
        if len(selected) >= max_slots:
            break
        meta: SchedulingMeta = row["meta"]
        current = project_counts.get(meta.project_id, 0)
        if current >= meta.max_parallelism:
            continue
        blockers = active_meta + [item["meta"] for item in selected]
        if any(not can_shadow_parallel(meta, other) for other in blockers):
            continue
        selected.append(row)
        project_counts[meta.project_id] = current + 1
    return selected


def decision_payload(max_slots: int = 4) -> dict[str, Any]:
    pending = load_envelopes(PENDING)
    active = load_envelopes(PROCESSING)
    selected = choose_shadow_slots(pending, active, max_slots=max_slots)
    return {
        "schema": "edarsahub.worker-shadow-scheduler.v1",
        "mode": "SHADOW_ONLY",
        "authoritative_executor": "edarsahub-universal-worker",
        "max_slots_simulated": max_slots,
        "pending_count": len(pending),
        "active_count": len(active),
        "selected": [
            {
                "job_id": row["job"].get("job_id"),
                "project_id": row["meta"].project_id,
                "bounded_context": row["meta"].bounded_context,
                "priority_class": row["meta"].priority_class,
                "resource_claims": list(row["meta"].resource_claims),
                "conflict_domains": list(row["meta"].conflict_domains),
                "legacy_defaults": row["meta"].legacy_defaults,
            }
            for row in selected
        ],
        "executed_jobs": [],
        "queue_mutations": 0,
        "production_touched": False,
    }


def main() -> int:
    print(json.dumps(decision_payload(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
