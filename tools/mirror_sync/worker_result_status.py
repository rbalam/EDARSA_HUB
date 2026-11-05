"""Derived per-job result status.

This is an index/reference layer, never a second terminal source of truth.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


READ_CONTRACT_VERSION = "v1"

_CERTIFIED_VALUES = frozenset(
    {
        "CERTIFIED",
        "CERTIFIED_READ_ONLY",
        "CERTIFIED_OPERATIONAL",
        "CERTIFIED_FRONTEND_BUILD",
    }
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _derive_work_completion(
    payload: dict[str, Any],
    *,
    terminal_valid: bool,
    state: str,
) -> str:
    if not terminal_valid:
        if state == "RESULT_ABSENT":
            return "RESULT_ABSENT"
        return str(
            payload.get("work_completion")
            or "INVALID_RESULT_ARTIFACT"
        )

    explicit = payload.get("work_completion")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()

    cert = str(payload.get("certification") or "").strip().upper()
    if cert in _CERTIFIED_VALUES:
        return "COMPLETE"
    if cert == "PENDING_AUDIT_EVIDENCE":
        return "PENDING_CERTIFICATION"
    if cert in {"PENDING_DELIVERABLES", "OBJECTIVE_PENDING"}:
        return cert
    return "NOT_CERTIFIED"


def build_job_status(
    *,
    result_read: Any,
) -> dict[str, Any]:
    payload = (
        dict(result_read.payload)
        if isinstance(result_read.payload, dict)
        else {}
    )
    terminal_valid = bool(result_read.terminal_result_valid)
    state = str(result_read.state or "")

    if not terminal_valid:
        if state == "RESULT_ABSENT":
            status_val = "RESULT_ABSENT"
            blockers_val = list(
                payload.get("blockers")
                or ["result_absent:RESULT_ABSENT"]
            )
            reconciliation_val = "RESULT_ABSENT_FAIL_CLOSED"
        else:
            raw_status = str(payload.get("status") or "").strip().upper()
            status_val = (
                raw_status
                if raw_status
                in {
                    "INVALID_RESULT_ARTIFACT",
                    "CONTRADICTORY_RESULT_ARTIFACT",
                }
                else "INVALID_RESULT_ARTIFACT"
            )
            blockers_val = list(
                payload.get("blockers")
                or [f"invalid_result_artifact:{state}"]
            )
            reconciliation_val = str(
                payload.get("reconciliation_status")
                or "INVALID_RESULT_ARTIFACT"
            )

        return {
            "job_id": result_read.job_id,
            "status": status_val,
            "quality_gate": "FAIL",
            "tests": "FAIL",
            "certification": "NOT_CERTIFIED",
            "work_completion": _derive_work_completion(
                payload,
                terminal_valid=False,
                state=state,
            ),
            "percent_complete": 0,
            "blockers": blockers_val,
            "production_touched": bool(
                payload.get("production_touched", False)
            ),
            "worker_mode": payload.get("slot_class") or payload.get("mode"),
            "result_path": result_read.result_path,
            "result_sha": result_read.result_sha256,
            "result_size_bytes": result_read.result_size_bytes,
            "terminal_result_valid": False,
            "result_state": state,
            "reconciliation_status": reconciliation_val,
            "completed_at_utc": payload.get("completed_at_utc"),
            "generated_at_utc": utc_now(),
            "read_contract_version": READ_CONTRACT_VERSION,
        }

    commit_sha = (
        payload.get("commit_sha")
        or payload.get("certified_source_sha")
        or payload.get("development_sha")
        or payload.get("integrated_commit")
    )

    status_dict: dict[str, Any] = {
        "job_id": result_read.job_id,
        "status": payload.get("status"),
        "quality_gate": payload.get("quality_gate"),
        "tests": payload.get("tests"),
        "certification": payload.get("certification"),
        "work_completion": _derive_work_completion(
            payload,
            terminal_valid=True,
            state=state,
        ),
        "percent_complete": payload.get("percent_complete"),
        "blockers": payload.get("blockers"),
        "production_touched": payload.get("production_touched"),
        "worker_mode": payload.get("slot_class") or payload.get("mode"),
        "result_path": result_read.result_path,
        "result_sha": result_read.result_sha256,
        "result_size_bytes": result_read.result_size_bytes,
        "terminal_result_valid": True,
        "result_state": state,
        "completed_at_utc": payload.get("completed_at_utc"),
        "generated_at_utc": utc_now(),
        "read_contract_version": READ_CONTRACT_VERSION,
    }
    if commit_sha:
        status_dict["commit_sha"] = commit_sha

    for optional_key in (
        "certified_source_sha",
        "converged_head",
        "certification_basis",
        "reconciliation_status",
        "published_result_commit",
        "published_result_sha256",
        "attestation_sha256",
    ):
        if payload.get(optional_key) is not None:
            status_dict[optional_key] = payload.get(optional_key)

    return status_dict
