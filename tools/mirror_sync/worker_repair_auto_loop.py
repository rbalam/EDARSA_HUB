"""Automatic orchestration loop for Worker Repair.

This module only coordinates existing canonical components.

It does not:
- execute repair actions directly;
- create a Worker, queue, dispatcher or publisher;
- certify its own mutation;
- touch Production.

Repository mutation remains exclusively in Universal Worker.
Certification remains independently evaluated through Worker Auditor.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from tools.mirror_sync.git_divergence_guard import (
    ensure_submit_convergence,
)
from tools.mirror_sync import worker_maintenance_runtime as maintenance
from tools.mirror_sync import worker_repair_capability_registry as learned_registry
from tools.mirror_sync import worker_repair_execution as execution
from tools.mirror_sync import worker_repair_planner as planner


ROOT = Path(__file__).resolve().parents[2]
QUEUE_ROOT = maintenance.GIT_COMMON_DIR / "universal-worker-queue"


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    return value if isinstance(value, dict) else None


def _source_result(job_id: str) -> dict[str, Any] | None:
    if not job_id:
        return None

    return _load_json(
        QUEUE_ROOT / "results" / f"{job_id}.json"
    )


def _source_requester(job_id: str) -> dict[str, Any] | None:
    if not job_id:
        return None

    for directory in (
        "done",
        "rejected",
        "processing",
        "pending",
    ):
        payload = _load_json(
            QUEUE_ROOT / directory / f"{job_id}.json"
        )

        if not payload:
            continue

        candidates = []

        embedded = payload.get("job")
        if isinstance(embedded, dict):
            candidates.append(embedded.get("requester"))

        candidates.append(payload.get("requester"))

        for requester in candidates:
            if not isinstance(requester, dict):
                continue

            email = str(requester.get("email") or "").strip().lower()

            if not email:
                continue

            return {
                "email": email,
                "source": str(
                    requester.get("source") or "worker_repair"
                ).strip(),
                "project": str(
                    requester.get("project") or "EDARSAHUB-BOS"
                ).strip(),
                "chat": str(
                    requester.get("chat") or "Worker Repair"
                ).strip(),
            }

    return None


def _learned_capability(
    incident_id: str,
    source_result: dict[str, Any] | None,
):
    try:
        direct = learned_registry.resolve_learned_capability(
            incident_id=incident_id,
        )
    except ValueError:
        raise

    if direct is not None:
        return direct

    if not isinstance(source_result, dict):
        return None

    blockers = {
        str(value or "").strip().upper()
        for value in source_result.get("blockers") or []
        if str(value or "").strip()
    }

    if not blockers:
        return None

    matches = []

    for capability in learned_registry.iter_learned_capabilities():
        evidence = capability.evidence or {}

        blocker_signature = str(
            evidence.get("blocker_signature") or ""
        ).strip().upper()

        if blocker_signature and blocker_signature in blockers:
            matches.append(capability)

    if not matches:
        return None

    if len(matches) != 1:
        raise ValueError(
            "AUTOMATIC_REPAIR_LEARNED_CAPABILITY_AMBIGUOUS"
        )

    return matches[0]


def _repair_result_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "files_changed": payload.get("files_changed"),
        "production_touched": payload.get("production_touched"),
        "quality_gate": payload.get("quality_gate"),
        "tests": payload.get("tests"),
        "blockers": payload.get("blockers"),
        "git_sync_status": payload.get("git_sync_status"),
    }


def _advance_bound_repair(
    incident_id: str,
    repair_job_id: str,
) -> dict[str, Any]:
    result_read = execution.read_repair_terminal_result(
        incident_id
    )

    if not result_read.terminal_result_valid:
        return {
            "incident_id": incident_id,
            "repair_job_id": repair_job_id,
            "action": "WAIT_RESULT",
            "result_state": result_read.state,
            "production_touched": False,
        }

    payload = result_read.payload or {}

    certification = str(
        payload.get("certification") or ""
    ).strip()

    if (
        payload.get("status") == "INTEGRATED"
        and payload.get("quality_gate") == "PASS"
        and payload.get("tests") == "PASS"
        and payload.get("production_touched") is False
        and certification != "CERTIFIED"
    ):
        convergence = ensure_submit_convergence(
            ROOT,
            job_id=repair_job_id + "-CERTIFICATION",
            owner="worker-repair-auto-loop",
            owner_pid=os.getpid(),
        )

        return {
            "incident_id": incident_id,
            "repair_job_id": repair_job_id,
            "action": "WAIT_RESULT_CERTIFICATION",
            "convergence": convergence,
            "production_touched": False,
        }

    reconciled = execution.reconcile_repair_result(
        incident_id
    )

    if reconciled.get("state") != "REPAIRED_PENDING_AUDIT":
        return {
            "incident_id": incident_id,
            "repair_job_id": repair_job_id,
            "action": "RECONCILED",
            "reconciliation": reconciled,
            "production_touched": False,
        }

    if certification != "CERTIFIED":
        return {
            "incident_id": incident_id,
            "repair_job_id": repair_job_id,
            "action": "WAIT_RESULT_CERTIFICATION",
            "production_touched": False,
        }

    decision = maintenance.audit_runtime_incident(
        incident_id,
        _repair_result_payload(payload),
    )

    return {
        "incident_id": incident_id,
        "repair_job_id": repair_job_id,
        "action": "AUDITED",
        "state": decision.state.value,
        "reason": decision.reason,
        "certified": decision.certified,
        "production_touched": False,
    }


def _candidate_source_jobs(
    detection: dict[str, Any],
) -> dict[str, str]:
    result: dict[str, str] = {}

    for row in detection.get("incidents") or []:
        if not isinstance(row, dict):
            continue

        incident_id = str(
            row.get("incident_id") or ""
        ).strip()

        source_job_id = str(
            row.get("source_job_id") or ""
        ).strip()

        if incident_id and source_job_id:
            result[incident_id] = source_job_id

    return result


def advance_repair_automation(
    detection: dict[str, Any],
) -> dict[str, Any]:
    """Advance declared repairs through existing canonical components."""
    source_jobs = _candidate_source_jobs(detection)

    incident_ids = set(source_jobs)

    if maintenance.INCIDENT_DIR.is_dir():
        incident_ids.update(
            path.stem
            for path in maintenance.INCIDENT_DIR.glob("*.json")
        )

    rows = []

    for incident_id in sorted(incident_ids):
        state = maintenance.read_runtime_incident(
            incident_id
        )

        if state is None:
            continue

        if state.state in {
            "CERTIFIED",
            "SUPERSEDED",
        }:
            rows.append(
                {
                    "incident_id": incident_id,
                    "action": "TERMINAL",
                    "state": state.state,
                    "production_touched": False,
                }
            )
            continue

        if state.repair_job_id:
            try:
                rows.append(
                    _advance_bound_repair(
                        incident_id,
                        state.repair_job_id,
                    )
                )
            except Exception as exc:
                rows.append(
                    {
                        "incident_id": incident_id,
                        "repair_job_id": state.repair_job_id,
                        "action": "WAIT_OR_BLOCKED",
                        "reason": f"{type(exc).__name__}:{exc}",
                        "production_touched": False,
                    }
                )
            continue

        allowed, reason = maintenance.repair_attempt_allowed(
            incident_id
        )

        if not allowed:
            rows.append(
                {
                    "incident_id": incident_id,
                    "action": "WAIT",
                    "reason": reason,
                    "production_touched": False,
                }
            )
            continue

        source_job_id = source_jobs.get(
            incident_id,
            "",
        )

        learned = None

        if not source_job_id:
            try:
                learned = learned_registry.resolve_learned_capability(
                    incident_id=incident_id,
                )
            except ValueError as exc:
                rows.append(
                    {
                        "incident_id": incident_id,
                        "action": "WAIT_CAPABILITY",
                        "reason": str(exc),
                        "production_touched": False,
                    }
                )
                continue

            if learned is not None:
                source_job_id = str(
                    (learned.evidence or {}).get("source_job_id")
                    or ""
                ).strip()

        source = _source_result(source_job_id)

        if learned is None:
            try:
                learned = _learned_capability(
                    incident_id,
                    source,
                )
            except ValueError as exc:
                rows.append(
                    {
                        "incident_id": incident_id,
                        "action": "WAIT_CAPABILITY",
                        "reason": str(exc),
                        "production_touched": False,
                    }
                )
                continue

        requester = _source_requester(
            source_job_id
        )

        if requester is None:
            rows.append(
                {
                    "incident_id": incident_id,
                    "source_job_id": source_job_id,
                    "action": "WAIT_REQUESTER",
                    "production_touched": False,
                }
            )
            continue

        try:
            publication = planner.publish_planned_repair(
                incident_id,
                capability_code=(
                    learned.code
                    if learned is not None
                    else None
                ),
                problem_signature=(
                    learned.problem_signature
                    if learned is not None
                    else None
                ),
                requester=requester,
            )
        except Exception as exc:
            rows.append(
                {
                    "incident_id": incident_id,
                    "source_job_id": source_job_id,
                    "action": "WAIT_OR_BLOCKED",
                    "reason": f"{type(exc).__name__}:{exc}",
                    "production_touched": False,
                }
            )
            continue

        rows.append(
            {
                "incident_id": incident_id,
                "source_job_id": source_job_id,
                "action": "PUBLISHED",
                "repair_job_id": (
                    publication.get("publication") or {}
                ).get("repair_job_id"),
                "capability": publication.get("capability"),
                "production_touched": False,
            }
        )

    return {
        "schema": "edarsahub.worker-repair-auto-loop.v1",
        "incidents": rows,
        "production_touched": False,
    }
