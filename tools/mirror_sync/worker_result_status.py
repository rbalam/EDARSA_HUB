"""Derived per-job result status.

This is an index/reference layer, never a second terminal source of truth.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


READ_CONTRACT_VERSION = "v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_job_status(
    *,
    result_read: Any,
) -> dict[str, Any]:
    payload = result_read.payload or {}

    return {
        "job_id": result_read.job_id,
        "status": payload.get("status"),
        "quality_gate": payload.get("quality_gate"),
        "certification": payload.get("certification"),
        "percent_complete": payload.get("percent_complete"),
        "blockers": payload.get("blockers"),
        "production_touched": payload.get("production_touched"),
        "worker_mode": payload.get("slot_class") or payload.get("mode"),
        "result_path": result_read.result_path,
        "result_sha": result_read.result_sha256,
        "result_size_bytes": result_read.result_size_bytes,
        "terminal_result_valid": result_read.terminal_result_valid,
        "result_state": result_read.state,
        "completed_at_utc": payload.get("completed_at_utc"),
        "generated_at_utc": utc_now(),
        "read_contract_version": READ_CONTRACT_VERSION,
    }
