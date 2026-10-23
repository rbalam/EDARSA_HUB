"""READ_ONLY health snapshot for the existing EDARSAHUB Worker infrastructure.

Does not execute jobs, publish requests, modify queues, or contact Production.
The existing Scheduler owns invocation and locking.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

QUEUE_STATES = ("pending", "processing", "results", "done", "published", "rejected")
MAX_STALE_SECONDS = 900


def _count_json(directory: Path) -> int:
    if not directory.is_dir():
        return 0
    return sum(1 for p in directory.iterdir() if p.is_file() and p.suffix == ".json")


def inspect_workers(root: Path, now: datetime | None = None) -> dict:
    """Observe local queue and runtime only; missing evidence is UNKNOWN, not PASS."""
    now = now or datetime.now(timezone.utc)
    queue = root / ".git" / "universal-worker-queue"
    if not queue.is_dir():
        return {"status": "UNKNOWN", "reason": "QUEUE_NOT_ACCESSIBLE", "observed_at_utc": now.isoformat()}
    counts = {state: _count_json(queue / state) for state in QUEUE_STATES}
    stale_processing = 0
    processing = queue / "processing"
    if processing.is_dir():
        for entry in processing.iterdir():
            if entry.is_file() and entry.suffix == ".json":
                try:
                    if now.timestamp() - entry.stat().st_mtime > MAX_STALE_SECONDS:
                        stale_processing += 1
                except OSError:
                    stale_processing += 1
    alerts = []
    if stale_processing:
        alerts.append({"code": "STALE_PROCESSING", "count": stale_processing})
    if counts["rejected"]:
        alerts.append({"code": "REJECTED_PRESENT", "count": counts["rejected"]})
    return {
        "status": "ATTENTION" if alerts else "OBSERVED",
        "observed_at_utc": now.isoformat(),
        "queue_counts": counts,
        "stale_processing": stale_processing,
        "alerts": alerts,
        "scope": "LOCAL_QUEUE_ONLY",
        "github_actions": "NOT_CONFIGURED",
        "repair_worker": "NOT_VERIFIED",
        "worker_auditor": "NOT_VERIFIED",
    }


def execute_bos_workers_global_watch() -> dict:
    """Return evidence for the canonical Scheduler logger; no persistent writes."""
    root = os.environ.get("EDARSAHUB_ROOT", "").strip()
    if not root:
        return {"status": "UNKNOWN", "reason": "EDARSAHUB_ROOT_REQUIRED"}
    return inspect_workers(Path(root))
