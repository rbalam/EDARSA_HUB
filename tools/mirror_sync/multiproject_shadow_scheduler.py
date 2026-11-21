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

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable, NamedTuple

ROOT = Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
STATE = ROOT / ".git" / "universal-worker-queue"
PENDING = STATE / "pending"
PROCESSING = STATE / "processing"

# Canonical scheduling authority is loaded as a sibling module so this
# adapter remains independent of cwd and implicit PYTHONPATH configuration.
_SCHEDULING_PATH = Path(__file__).resolve().with_name("worker_scheduling.py")
_SCHEDULING_SPEC = importlib.util.spec_from_file_location(
    "edarsahub_worker_scheduling",
    _SCHEDULING_PATH,
)
if _SCHEDULING_SPEC is None or _SCHEDULING_SPEC.loader is None:
    raise ImportError("WORKER_SCHEDULING_SPEC_UNAVAILABLE")
_worker_scheduling = importlib.util.module_from_spec(_SCHEDULING_SPEC)
sys.modules[_SCHEDULING_SPEC.name] = _worker_scheduling
_SCHEDULING_SPEC.loader.exec_module(_worker_scheduling)


# Public legacy names remain available here, but their values come from the
# single canonical scheduling authority.
PRIORITY_ORDER = _worker_scheduling.PRIORITY_ORDER
GLOBAL_CONFLICT_DOMAINS = _worker_scheduling.GLOBAL_CONFLICT_DOMAINS


# Preserve the historical scheduler API without defining a second model.
SchedulingMeta = _worker_scheduling.SchedulingMeta


def _norm(values: Iterable[Any]) -> tuple[str, ...]:
    return tuple(sorted({str(v).strip() for v in values if str(v).strip()}))


def _safe_int(value: Any, default: int, minimum: int = 1, maximum: int = 64) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, n))


def normalize_metadata(job: dict[str, Any]) -> SchedulingMeta:
    """Legacy adapter to the canonical scheduling normalizer."""
    return _worker_scheduling.normalize_metadata(job)


def claims_conflict(a: SchedulingMeta, b: SchedulingMeta) -> bool:
    """Legacy adapter to the canonical scheduling conflict policy."""
    return _worker_scheduling.claims_conflict(a, b)


def can_shadow_parallel(a: SchedulingMeta, b: SchedulingMeta) -> bool:
    """Legacy adapter; Gate4B1A remains observation-only and serial at runtime."""
    return _worker_scheduling.can_shadow_parallel(a, b)


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


def fairness_key(
    row: dict[str, Any],
    served: dict[str, int] | None = None,
) -> tuple[Any, ...]:
    """Legacy adapter to the canonical weighted-fairness ordering."""
    return _worker_scheduling.fairness_key(row, served)


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
