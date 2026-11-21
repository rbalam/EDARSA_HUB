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
import re
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


def _normalize_requester_dict(
    requester: Any,
) -> dict[str, Any] | None:
    if not isinstance(requester, dict):
        return None

    email = str(requester.get("email") or "").strip().lower()
    if not email or "@" not in email:
        return None

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


def _extract_requester_from_envelope(
    payload: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None

    candidates = []
    embedded = payload.get("job")
    if isinstance(embedded, dict):
        candidates.append(embedded.get("requester"))
    candidates.append(payload.get("requester"))

    for candidate in candidates:
        normalized = _normalize_requester_dict(candidate)
        if normalized is not None:
            return normalized

    return None


def _source_requester(
    job_id: str,
    *,
    incident_state: Any = None,
    incident_id: str = "",
) -> dict[str, Any] | None:
    if incident_state is not None:
        persisted = _normalize_requester_dict(
            getattr(incident_state, "requester", None)
        )
        if persisted is not None:
            return persisted

    lookup_job_ids: list[str] = []
    for candidate_id in (
        job_id,
        getattr(incident_state, "source_job_id", None)
        if incident_state is not None
        else None,
    ):
        clean_id = str(candidate_id or "").strip()
        if clean_id and clean_id not in lookup_job_ids:
            lookup_job_ids.append(clean_id)

    for candidate_id in lookup_job_ids:
        for directory in (
            "done",
            "rejected",
            "processing",
            "pending",
            "drafts",
        ):
            payload = _load_json(
                QUEUE_ROOT / directory / f"{candidate_id}.json"
            )
            resolved = _extract_requester_from_envelope(payload)
            if resolved is not None:
                return resolved

        rejected_history = QUEUE_ROOT / "rejected_history"
        if rejected_history.is_dir():
            for path in sorted(
                rejected_history.glob(f"{candidate_id}*.json")
            ):
                resolved = _extract_requester_from_envelope(
                    _load_json(path)
                )
                if resolved is not None:
                    return resolved

    target_incident_id = str(
        incident_id
        or getattr(incident_state, "incident_id", "")
        or ""
    ).strip()
    if target_incident_id:
        raw_incident = _load_json(
            maintenance.INCIDENT_DIR / f"{target_incident_id}.json"
        )
        if isinstance(raw_incident, dict):
            resolved = _normalize_requester_dict(
                raw_incident.get("requester")
            )
            if resolved is not None:
                return resolved

            history = raw_incident.get("repair_job_history")
            if isinstance(history, list):
                for entry in reversed(history):
                    if not isinstance(entry, dict):
                        continue
                    hist_job_id = str(
                        entry.get("job_id") or ""
                    ).strip()
                    if not hist_job_id:
                        continue
                    for spec_path in (
                        planner.REPAIR_SPECS
                        / f"{hist_job_id}.json",
                        QUEUE_ROOT / "done" / f"{hist_job_id}.json",
                        QUEUE_ROOT
                        / "rejected"
                        / f"{hist_job_id}.json",
                        QUEUE_ROOT
                        / "drafts"
                        / f"{hist_job_id}.json",
                    ):
                        resolved = _extract_requester_from_envelope(
                            _load_json(spec_path)
                        )
                        if resolved is not None:
                            return resolved

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

    try:
        return (
            learned_registry.resolve_learned_capability_for_blockers(
                blockers
            )
        )
    except ValueError as exc:
        raise ValueError(
            "AUTOMATIC_REPAIR_LEARNED_CAPABILITY_AMBIGUOUS"
        ) from exc


def _repair_result_payload(
    payload: dict[str, Any],
    *,
    result_sha256: str | None = None,
) -> dict[str, Any]:
    return {
        "job_id": payload.get("job_id"),
        "result_sha256": (
            result_sha256
            or payload.get("result_sha256")
        ),
        "status": payload.get("status"),
        "certification": payload.get(
            "certification"
        ),
        "files_changed": payload.get("files_changed"),
        "production_touched": payload.get("production_touched"),
        "quality_gate": payload.get("quality_gate"),
        "tests": payload.get("tests"),
        "blockers": payload.get("blockers"),
        "git_sync_status": payload.get("git_sync_status"),
        "base_sha": payload.get("base_sha"),
        "execution_base_sha": payload.get(
            "execution_base_sha"
        ),
        "candidate_sha": payload.get(
            "candidate_sha"
        ),
        "development_sha": payload.get(
            "development_sha"
        ),
    }


def _derive_capability_code(
    incident_id: str,
    incident_state: Any,
    spec_payload: dict[str, Any],
) -> str:
    persisted_code = str(
        getattr(incident_state, "capability_code", None) or ""
    ).strip().upper()
    if persisted_code and learned_registry.CODE_RE.fullmatch(
        persisted_code
    ):
        return persisted_code

    objective = str(spec_payload.get("objective") or "").strip()
    if objective.upper().startswith("REPARACION "):
        candidate = re.sub(
            r"[^A-Z0-9_]+",
            "_",
            objective[11:].strip().upper(),
        ).strip("_")
        if learned_registry.CODE_RE.fullmatch(candidate):
            return candidate

    sanitized = re.sub(
        r"[^A-Z0-9_]+",
        "_",
        f"LEARNED_{incident_id}".upper(),
    ).strip("_")[:95]
    if len(sanitized) < 3:
        sanitized = "LEARNED_REPAIR_CAPABILITY"
    return sanitized


def _register_certified_repair_capability(
    incident_id: str,
    repair_job_id: str,
    result_payload: dict[str, Any],
    *,
    result_sha256: str | None = None,
) -> dict[str, Any]:
    incident = maintenance.read_runtime_incident(incident_id)
    if incident is None:
        return {
            "status": "SKIPPED_INCIDENT_MISSING",
            "production_touched": False,
        }

    if (
        incident.state != "CERTIFIED"
        or incident.production_touched is not False
    ):
        return {
            "status": "SKIPPED_INCIDENT_NOT_CERTIFIED",
            "production_touched": False,
        }

    spec_path = planner.REPAIR_SPECS / f"{repair_job_id}.json"
    spec_payload = _load_json(spec_path)
    if not isinstance(spec_payload, dict):
        return {
            "status": "SKIPPED_SPEC_NOT_FOUND",
            "production_touched": False,
        }

    actions = spec_payload.get("actions")
    checks = spec_payload.get("checks")
    if (
        not isinstance(actions, list)
        or not actions
        or not isinstance(checks, list)
        or not checks
    ):
        return {
            "status": "SKIPPED_SPEC_INCOMPLETE",
            "production_touched": False,
        }

    code = _derive_capability_code(
        incident_id,
        incident,
        spec_payload,
    )

    try:
        existing_direct = learned_registry.resolve_learned_capability(
            incident_id=incident_id,
            capability_code=code,
        )
    except ValueError:
        existing_direct = None

    if existing_direct is not None:
        return {
            "status": "ALREADY_REGISTERED",
            "code": existing_direct.code,
            "production_touched": False,
        }

    source_job_id = str(
        getattr(incident, "source_job_id", None)
        or repair_job_id
    ).strip()
    source_res = _source_result(source_job_id) or {}
    raw_blockers = source_res.get("blockers") or []
    first_blocker = (
        str(raw_blockers[0]).strip()
        if isinstance(raw_blockers, list) and raw_blockers
        else ""
    )

    blocker_signature = str(
        getattr(incident, "blocker_signature", None)
        or first_blocker
        or getattr(incident, "source_status", None)
        or "CERTIFIED_REPAIR_RESOLVED"
    ).strip()

    raw_problem_sig = str(
        getattr(incident, "problem_signature", None)
        or blocker_signature
        or code
    ).strip().upper()
    problem_signature = re.sub(
        r"[^A-Z0-9_.:-]+",
        "_",
        raw_problem_sig,
    ).strip("_")[:191]
    if not learned_registry.SIGNATURE_RE.fullmatch(
        problem_signature
    ):
        problem_signature = f"REPAIR_SIG_{code}"[:191]

    action_paths = sorted(
        {
            str(item.get("path") or "").strip()
            for item in actions
            if isinstance(item, dict)
            and str(item.get("path") or "").strip()
        }
    )
    required_paths = sorted(
        set(incident.target_paths)
        if incident.target_paths
        else set(action_paths)
    )

    evidence: dict[str, Any] = {
        "source_job_id": source_job_id,
        "blocker_signature": blocker_signature,
        "repair_job_id": repair_job_id,
        "certified": True,
        "certification": "CERTIFIED",
    }
    commit_sha = str(
        result_payload.get("development_sha")
        or result_payload.get("candidate_sha")
        or getattr(incident, "repair_commit_sha", None)
        or ""
    ).strip()
    if commit_sha:
        evidence["repair_commit_sha"] = commit_sha
    effective_sha256 = str(
        result_sha256
        or result_payload.get("result_sha256")
        or getattr(incident, "repair_result_sha256", None)
        or ""
    ).strip()
    if effective_sha256:
        evidence["repair_result_sha256"] = effective_sha256

    capability_payload: dict[str, Any] = {
        "schema": learned_registry.SCHEMA,
        "code": code,
        "problem_signature": problem_signature,
        "incident_ids": [incident_id],
        "incident_patterns": [],
        "required_paths": required_paths,
        "objective": str(
            spec_payload.get("objective")
            or f"Reparacion certificada {code}"
        ).strip(),
        "actions": [
            dict(item)
            for item in actions
            if isinstance(item, dict)
        ],
        "checks": [
            dict(item)
            for item in checks
            if isinstance(item, dict)
        ],
        "evidence": evidence,
        "learned_from_incident": incident_id,
        "reusable": False,
        "production_allowed": False,
    }

    return learned_registry.register_learned_capability(
        capability_payload,
        incident=incident,
        require_certified_incident=True,
    )


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

    result_sha256 = getattr(
        result_read,
        "result_sha256",
        None,
    )
    decision = maintenance.audit_runtime_incident(
        incident_id,
        _repair_result_payload(
            payload,
            result_sha256=result_sha256,
        ),
    )

    response: dict[str, Any] = {
        "incident_id": incident_id,
        "repair_job_id": repair_job_id,
        "action": "AUDITED",
        "state": decision.state.value,
        "reason": decision.reason,
        "certified": decision.certified,
        "production_touched": False,
    }

    if (
        decision.certified is True
        and decision.state.value == "CERTIFIED"
    ):
        try:
            registration = _register_certified_repair_capability(
                incident_id,
                repair_job_id,
                payload,
                result_sha256=result_sha256,
            )
            response["learned_capability_registration"] = (
                registration
            )
        except Exception as exc:
            response["learned_capability_registration"] = {
                "status": "REGISTRATION_FAILED_CLOSED",
                "reason": f"{type(exc).__name__}:{exc}",
                "production_touched": False,
            }

    return response


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


def _candidate_incident_rows(
    detection: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in detection.get("incidents") or []:
        if not isinstance(row, dict):
            continue
        incident_id = str(row.get("incident_id") or "").strip()
        if incident_id:
            rows[incident_id] = row
    return rows


def _certified_target_sets() -> list[tuple[str, set[str]]]:
    certified_sets: list[tuple[str, set[str]]] = []
    if not maintenance.INCIDENT_DIR.is_dir():
        return certified_sets

    for path in sorted(maintenance.INCIDENT_DIR.glob("*.json")):
        payload = _load_json(path)
        if not isinstance(payload, dict):
            continue
        if payload.get("production_touched") is not False:
            continue
        if str(payload.get("state") or "").strip() != "CERTIFIED":
            continue
        paths = {
            str(item).strip()
            for item in (payload.get("target_paths") or [])
            if isinstance(item, str) and str(item).strip()
        }
        if paths:
            certified_sets.append((path.stem, paths))

    return certified_sets


def _persisted_incident_superseded_reason(
    incident_state: Any,
    *,
    certified_sets: list[tuple[str, set[str]]],
) -> str | None:
    if incident_state.production_touched is not False:
        return None
    if incident_state.state not in {
        "REPAIR_REQUIRED",
        "REJECTED",
    }:
        return None
    if incident_state.repair_job_id:
        return None

    target_paths = set(incident_state.target_paths or ())
    if not target_paths:
        return None

    for cert_id, cert_paths in certified_sets:
        if (
            cert_id != incident_state.incident_id
            and target_paths.issubset(cert_paths)
        ):
            return f"SUPERSEDED_BY_CERTIFIED_INCIDENT:{cert_id}"

    try:
        learned = learned_registry.resolve_learned_capability(
            incident_id=incident_state.incident_id,
            problem_signature=getattr(
                incident_state,
                "problem_signature",
                None,
            ),
            capability_code=getattr(
                incident_state,
                "capability_code",
                None,
            ),
        )
    except ValueError:
        learned = None

    if learned is not None:
        evidence = learned.evidence or {}
        if evidence.get("previous_repair_certified") is True:
            source_job_id = str(
                getattr(incident_state, "source_job_id", None)
                or evidence.get("source_job_id")
                or ""
            ).strip()
            source = _source_result(source_job_id)
            if isinstance(source, dict):
                results_dir = QUEUE_ROOT / "results"
                if results_dir.is_dir():
                    source_completed = str(
                        source.get("completed_at_utc") or ""
                    ).strip()
                    for res_path in sorted(
                        results_dir.glob("*.json")
                    ):
                        candidate = _load_json(res_path)
                        if not isinstance(candidate, dict):
                            continue
                        if (
                            candidate.get("status") != "INTEGRATED"
                            or candidate.get("certification")
                            != "CERTIFIED"
                            or candidate.get("quality_gate")
                            != "PASS"
                            or candidate.get("tests") != "PASS"
                            or candidate.get("production_touched")
                            is not False
                        ):
                            continue
                        cand_completed = str(
                            candidate.get("completed_at_utc") or ""
                        ).strip()
                        if (
                            source_completed
                            and cand_completed
                            and cand_completed <= source_completed
                        ):
                            continue
                        changed = {
                            str(p).strip()
                            for p in (
                                candidate.get("files_changed")
                                or []
                            )
                            if isinstance(p, str)
                            and str(p).strip()
                        }
                        if target_paths.issubset(changed):
                            cand_job_id = str(
                                candidate.get("job_id")
                                or res_path.stem
                            ).strip()
                            return (
                                "SUPERSEDED_BY_CERTIFIED_SUCCESSOR:"
                                f"{cand_job_id}"
                            )

    return None


def advance_repair_automation(
    detection: dict[str, Any],
) -> dict[str, Any]:
    """Advance declared repairs through existing canonical components."""
    source_jobs = _candidate_source_jobs(detection)
    detection_rows = _candidate_incident_rows(detection)
    certified_sets = _certified_target_sets()

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

        det_row = detection_rows.get(incident_id)
        is_suppressed_duplicate = isinstance(det_row, dict) and (
            det_row.get("repair_reason")
            == "DUPLICATE_ROOT_CAUSE_SUPPRESSED"
            or det_row.get("state")
            == "DUPLICATE_ROOT_CAUSE_SUPPRESSED"
        )
        if isinstance(det_row, dict) and not is_suppressed_duplicate:
            det_source_job_id = str(
                det_row.get("source_job_id") or ""
            ).strip()
            det_requester = (
                _source_requester(
                    det_source_job_id,
                    incident_state=state,
                    incident_id=incident_id,
                )
                if det_source_job_id
                else None
            )
            updated_state = (
                maintenance.record_runtime_incident_metadata(
                    incident_id,
                    source_job_id=det_source_job_id or None,
                    source_status=str(
                        det_row.get("source_status") or ""
                    ).strip()
                    or None,
                    problem_signature=str(
                        det_row.get("problem_signature") or ""
                    ).strip()
                    or None,
                    blocker_signature=str(
                        det_row.get("blocker_signature") or ""
                    ).strip()
                    or None,
                    capability_code=str(
                        det_row.get("capability_code") or ""
                    ).strip()
                    or None,
                    requester=det_requester,
                )
            )
            if updated_state is not None:
                state = updated_state

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

        if is_suppressed_duplicate:
            selected_incident_id = (
                str(
                    det_row.get("selected_incident_id")
                    or ""
                ).strip()
                or None
            )
            suppressed_source_job_id = (
                str(det_row.get("source_job_id") or "").strip()
                or str(
                    getattr(state, "source_job_id", None) or ""
                ).strip()
                or None
            )
            rows.append(
                {
                    "incident_id": incident_id,
                    "action": "SUPPRESSED_DUPLICATE_ROOT_CAUSE",
                    "reason": "DUPLICATE_ROOT_CAUSE_SUPPRESSED",
                    "selected_incident_id": selected_incident_id,
                    "source_job_id": suppressed_source_job_id,
                    "state": state.state,
                    "production_touched": False,
                }
            )
            continue

        superseded_reason = _persisted_incident_superseded_reason(
            state,
            certified_sets=certified_sets,
        )
        if superseded_reason is not None:
            superseded_state = maintenance.supersede_runtime_incident(
                incident_id,
                reason=superseded_reason,
            )
            rows.append(
                {
                    "incident_id": incident_id,
                    "action": "SUPERSEDED",
                    "state": superseded_state.state,
                    "reason": superseded_reason,
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

        source_job_id = (
            source_jobs.get(incident_id, "")
            or str(
                getattr(state, "source_job_id", None) or ""
            ).strip()
        )

        learned = None

        if not source_job_id:
            try:
                learned = learned_registry.resolve_learned_capability(
                    incident_id=incident_id,
                    problem_signature=getattr(
                        state,
                        "problem_signature",
                        None,
                    ),
                    capability_code=getattr(
                        state,
                        "capability_code",
                        None,
                    ),
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

        if learned is not None and not source_job_id:
            source_job_id = str(
                (learned.evidence or {}).get("source_job_id") or ""
            ).strip()

        requester = _source_requester(
            source_job_id,
            incident_state=state,
            incident_id=incident_id,
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

        maintenance.record_runtime_incident_metadata(
            incident_id,
            source_job_id=source_job_id or None,
            problem_signature=(
                learned.problem_signature
                if learned is not None
                else None
            ),
            capability_code=(
                learned.code
                if learned is not None
                else None
            ),
            requester=requester,
        )

        dup_guard = prevent_duplicate_historical_repair(
            incident_id=incident_id,
            source_job_id=source_job_id,
            problem_signature=(
                learned.problem_signature
                if learned is not None
                else getattr(state, "problem_signature", None)
            ),
            blockers=list((source or {}).get("blockers") or []),
            target_paths=list(getattr(state, "target_paths", ()) or ()),
        )
        if dup_guard.get("duplicate_prevented") is True:
            rows.append(
                {
                    "incident_id": incident_id,
                    "source_job_id": source_job_id,
                    "action": "PREVENTED_DUPLICATE_HISTORICAL_REPAIR",
                    "reason": dup_guard.get("reason"),
                    "matched_lesson_id": dup_guard.get("matched_lesson_id"),
                    "matched_repair_job_id": dup_guard.get("matched_repair_job_id"),
                    "production_touched": False,
                }
            )
            continue

        if execution._repair_rbac_env_enforced():
            try:
                auth_result = execution._default_rbac_authorizer(requester)
            except Exception:
                auth_result = {
                    "allowed": False,
                    "reason": "REQUESTER_RBAC_RUNTIME_ERROR",
                }
            if not isinstance(auth_result, dict) or auth_result.get("allowed") is not True:
                rows.append(
                    {
                        "incident_id": incident_id,
                        "source_job_id": source_job_id,
                        "action": "BLOCKED_RBAC",
                        "reason": (
                            "REPAIR_RBAC_DENIED:"
                            + str(
                                (auth_result or {}).get("reason")
                                if isinstance(auth_result, dict)
                                else "INVALID_RBAC_RESPONSE"
                            )
                        ),
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


# Gate D - Canonical Failure Taxonomy, Persistent Circuit Breaker & Knowledge Loop Cycle.
CIRCUIT_BREAKER_DIR = maintenance.STATE_DIR / "circuit_breakers"
_SAFE_CIRCUIT_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{1,120}$")

FAILURE_TAXONOMY_RULES: tuple[tuple[str, str, tuple[str, ...], bool, bool, str, int], ...] = (
    ("PRODUCTION_POLICY_VIOLATION", "SECURITY", ("PRODUCTION_FORBIDDEN", "PRODUCTION_TOUCHED", "PRODUCTION_POLICY"), False, True, "FAIL_CLOSED_HUMAN_REQUIRED", 0),
    ("SENSITIVE_DATA_EXPOSURE_RISK", "SECURITY", ("SENSITIVE", "SECRET", "PASSWORD", "CREDENTIAL", "REJECTED_UNSAFE", "TOKEN_LEAK"), False, True, "FAIL_CLOSED_HUMAN_REQUIRED", 0),
    ("EMPRESA_OR_SUCURSAL_AUTH_FAILURE", "SECURITY", ("SCOPE_AUTHORIZATION_DENIED", "SUCURSAL_FORBIDDEN", "EMPRESA_FORBIDDEN"), False, True, "FAIL_CLOSED_HUMAN_REQUIRED", 0),
    ("INSUFFICIENT_PERMISSIONS", "SECURITY", ("RBAC_", "INSUFFICIENT_SCOPE", "FORBIDDEN", "UNAUTHORIZED", "ACCESS_DENIED", "AUTHORIZATION_REQUIRED", "AUTHORIZATION_EXPIRED", "AUTHORIZATION_REVOKED"), False, True, "FAIL_CLOSED_HUMAN_REQUIRED", 0),
    ("DATE_OR_TIMEZONE_ERROR", "BUSINESS", ("TIMEZONE", "TZINFO", "INVALID_DATE", "DATETIME", "NAIVE_DATETIME"), False, True, "FAIL_CLOSED_BUSINESS_REVIEW", 0),
    ("STORAGE_OR_RESOURCE_LIMIT", "INFRASTRUCTURE", ("ENOSPC", "NO SPACE LEFT", "MEMORYERROR", "OUT OF MEMORY", "INODE", "POLICY_MAX_"), False, True, "FAIL_CLOSED_INFRA_CAPACITY", 0),
    ("DIRTY_WORKTREE", "INFRASTRUCTURE", ("GIT_WORKTREE_NOT_CLEAN", "WORKTREE_DIRTY", "LOCAL_DIRTY"), False, True, "FAIL_CLOSED_PRESERVE_LOCAL_WORK", 0),
    ("CONTRADICTORY_RESULT", "INFRASTRUCTURE", ("CONTRADICTORY_RESULT_ARTIFACT", "READ_SOURCE_MISMATCH", "RESULT_SHA_MISMATCH"), False, True, "FAIL_CLOSED_FORENSIC_RECONCILE", 0),
    ("MISSING_DEPENDENCY", "INFRASTRUCTURE", ("MODULENOTFOUNDERROR", "IMPORTERROR", "COMMAND NOT FOUND", "VENV_MISSING"), False, True, "FAIL_CLOSED_DEPENDENCY_CHECK", 0),
    ("UNKNOWN_MCP_CAPABILITY", "CONTRACT", ("SEMANTIC_CAPABILITY_UNKNOWN", "CAPABILITY_UNKNOWN", "CAPABILITY_NOT_LOADED"), False, False, "CHECK_CATALOG_AND_RUNTIME_CONVERGENCE", 1),
    ("INVALID_CONTRACT", "CONTRACT", ("INVALID_JOB_TEMPLATE_SCHEMA", "SEMANTIC_CONSTRAINTS_UNSUPPORTED", "SEMANTIC_CAPABILITY_MODE_MISMATCH", "UNSUPPORTED_ACTION", "UNSUPPORTED_CHECK", "FORBIDDEN_TEMPLATE_KEY", "INVALID_SCHEMA"), False, False, "FIX_CONTRACT_SPEC", 0),
    ("DUPLICATE_JOB", "CONTRACT", ("ALREADY_EXISTS", "DUPLICATE", "EXISTS"), False, False, "RECONCILE_EXISTING_JOB", 0),
    ("REVOKED_SESSION_ACCEPTED", "SECURITY", ("REVOKED_SESSION_ACCEPTED", "SESSION_REVOCATION_FAIL_OPEN", "STALE_SID_ACCEPTED"), False, True, "FAIL_CLOSED_HUMAN_REQUIRED", 0),
    ("MISSING_EXPECTED_SHA256", "CONTRACT", ("WRITE_EXISTING_REQUIRES_EXPECTED_SHA256", "EXPECTED_SHA256_REQUIRED", "MISSING_EXPECTED_SHA256"), False, False, "PREPUBLISH_CONTRACT_PARITY_AND_REFRESH_SHA", 0),
    ("SQL_AS_DICT_UNNAMED_COLUMN", "CONTRACT", ("PYMSSQL_AS_DICT_UNNAMED_COLUMN", "COLUMNS WITH NO NAMES", "AS_DICT_UNNAMED_COLUMN"), False, False, "ADD_EXPLICIT_SQL_ALIAS_AND_FAIL_CLOSED", 0),
    ("EXECUTABLE_MODE_STRIP", "INFRASTRUCTURE", ("ATOMIC_WRITE_MODE_STRIP", "EXECUTABLE_BIT_LOST", "PERMISSION_MODE_DRIFT"), False, False, "PRESERVE_POSIX_MODE_IN_MATERIALIZER", 1),
    ("MIRROR_SYNC_STOPPED", "INFRASTRUCTURE", ("MIRROR_SYNC_STOPPED", "MIRROR_NOT_STARTED", "MIRROR_POST_DISCONNECT_STOPPED"), True, False, "RECOVER_AUTHORIZED_MIRROR_SYNC", 2),
    ("CODE_CERTIFIED_WITHOUT_OPERATIONAL_VALIDATION", "INFRASTRUCTURE", ("UNVERIFIED_IN_PREVIEW", "PREVIEW_VALIDATION_MISSING", "CERTIFIED_WITHOUT_PREVIEW_EVIDENCE"), False, False, "RUN_PREVIEW_OPERATIONAL_VALIDATION", 1),
    ("STALE_SOURCE_SHA256", "CONTRACT", ("SOURCE_SHA256_MISMATCH", "SHA256_MISMATCH", "STALE_SHA"), True, False, "REFRESH_SHA_AND_REPLAN", 2),
    ("TEST_FAILURE", "CONTRACT", ("GIT_TESTS_FAILED", "CHECK_FAILED:PYTEST", "ASSERTIONERROR"), False, False, "DIAGNOSE_CAUSAL_AND_REPAIR", 2),
    ("ABSENT_OR_TRUNCATED_EVIDENCE", "CONTRACT", ("EVIDENCE_ABSENT", "EVIDENCE_TRUNCATED", "RESULT_ABSENT"), False, False, "BOUNDED_REQUERY", 1),
    ("GIT_MIRROR_DIVERGENCE", "INFRASTRUCTURE", ("GIT_DIVERGENCE_BLOCKED", "DIVERGENCE", "NON_FAST_FORWARD", "GUARD_CLI_EXIT_MISMATCH", "FINALIZE_SYSTEM_DEPS_DRIFT"), True, False, "CANONICAL_DIVERGENCE_GUARD", 2),
    ("CONTRADICTORY_NOT_FOUND", "INFRASTRUCTURE", ("NOT_FOUND", "BLOB_MISSING", "RESULT_REF_MISSING"), True, False, "RECONCILE_REMOTE_RESULTS", 1),
    ("INCOMPLETE_PUBLICATION", "TRANSIENT", ("PUBLICATION_INCOMPLETE", "PUSH_FAILED", "GIT_PUSH_FAILED"), True, False, "RECONCILE_AND_REPUBLISH", 2),
    ("PENDING_ATTESTATION", "TRANSIENT", ("PENDING_AUDIT_EVIDENCE", "ATTESTATION_MISSING", "PENDING_CERTIFICATION"), True, False, "WAIT_ATTESTATION_CYCLE", 2),
    ("CONCURRENCY_CONFLICT", "TRANSIENT", ("CONCURRENT_SCOPE_CONFLICT", "GIT_LOCK_BUSY", "INDEX.LOCK", "WRITER_LOCK"), True, False, "BOUNDED_RETRY", 2),
    ("STUCK_OR_EXPIRED_JOB", "TRANSIENT", ("SLOT_EXPIRED", "STUCK", "HEARTBEAT_EXPIRED", "TIMED_OUT", "POLICY_TIMEOUT_EXCEEDED"), True, False, "RECOVER_EXPIRED_SLOT", 2),
    ("CONNECTION_LOSS", "INTEGRATION", ("CONNECTIONREFUSED", "CONNECTIONRESET", "NETWORK", "UNREACHABLE", "DNS", "502", "503", "504"), True, False, "BOUNDED_RETRY", 2),
    ("RUNTIME_RESTART_OR_TRANSIENT", "TRANSIENT", ("RESTART", "TRANSIENT", "TEMPORARY", "RETRY"), True, False, "BOUNDED_RETRY", 2),
)


def classify_failure_taxonomy(
    *,
    status: str = "",
    blockers: list[str] | tuple[str, ...] = (),
    error_code: str = "",
    causal_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify a Worker/MCP failure into the canonical taxonomy without blind string-only mutation."""
    tokens = " | ".join(
        [
            str(status or "").strip().upper(),
            str(error_code or "").strip().upper(),
            *(str(b or "").strip().upper() for b in (blockers or ())),
        ]
    )
    has_causal_evidence = isinstance(causal_evidence, dict) and bool(causal_evidence)

    for (
        failure_class,
        domain_category,
        patterns,
        recoverable_auto,
        approval_required,
        strategy,
        max_attempts,
    ) in FAILURE_TAXONOMY_RULES:
        if any(pat in tokens for pat in patterns):
            auto_repair_allowed = bool(
                recoverable_auto
                and not approval_required
                and domain_category not in {"SECURITY", "BUSINESS"}
                and has_causal_evidence
            )
            return {
                "failure_class": failure_class,
                "category": domain_category,
                "recoverable_automatically": recoverable_auto,
                "human_approval_required": approval_required,
                "requires_causal_evidence": True,
                "has_causal_evidence": has_causal_evidence,
                "auto_repair_allowed": auto_repair_allowed,
                "recovery_strategy": strategy,
                "max_attempts": max_attempts,
                "production_touched": False,
            }

    return {
        "failure_class": "UNCLASSIFIED_NON_RECOVERABLE",
        "category": "NON_RECOVERABLE",
        "recoverable_automatically": False,
        "human_approval_required": True,
        "requires_causal_evidence": True,
        "has_causal_evidence": has_causal_evidence,
        "auto_repair_allowed": False,
        "recovery_strategy": "FAIL_CLOSED_HUMAN_REQUIRED",
        "max_attempts": 0,
        "production_touched": False,
    }


def _circuit_path(signature_key: str, *, state_dir: Path | None = None) -> Path:
    clean = str(signature_key or "").strip()
    if not _SAFE_CIRCUIT_KEY_RE.fullmatch(clean):
        raise ValueError("CIRCUIT_KEY_INVALID")
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", clean)
    root = state_dir or CIRCUIT_BREAKER_DIR
    return root / f"{safe_name}.json"


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    import tempfile

    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def evaluate_circuit_breaker(
    signature_key: str,
    *,
    max_failures: int = 3,
    cooldown_seconds: int = 900,
    now_epoch: float | None = None,
    state_dir: Path | None = None,
) -> dict[str, Any]:
    """Fail-closed persistent circuit breaker preventing infinite repair retries."""
    import time

    now_ts = float(now_epoch if now_epoch is not None else time.time())
    path = _circuit_path(signature_key, state_dir=state_dir)
    data = _load_json(path) or {}
    failures = int(data.get("consecutive_failures") or 0)
    last_failure_epoch = float(data.get("last_failure_epoch") or 0.0)

    if failures >= max_failures:
        elapsed = now_ts - last_failure_epoch
        if elapsed < cooldown_seconds:
            return {
                "signature_key": signature_key,
                "state": "OPEN",
                "allow_attempt": False,
                "consecutive_failures": failures,
                "cooldown_remaining_seconds": max(0, int(cooldown_seconds - elapsed)),
                "reason": "CIRCUIT_OPEN_MAX_FAILURES",
                "production_touched": False,
            }
        return {
            "signature_key": signature_key,
            "state": "HALF_OPEN",
            "allow_attempt": True,
            "consecutive_failures": failures,
            "cooldown_remaining_seconds": 0,
            "reason": "CIRCUIT_HALF_OPEN_PROBE",
            "production_touched": False,
        }

    return {
        "signature_key": signature_key,
        "state": "CLOSED",
        "allow_attempt": True,
        "consecutive_failures": failures,
        "cooldown_remaining_seconds": 0,
        "reason": "CIRCUIT_CLOSED",
        "production_touched": False,
    }


def record_circuit_outcome(
    signature_key: str,
    *,
    certified_success: bool,
    failure_class: str = "",
    now_epoch: float | None = None,
    state_dir: Path | None = None,
) -> dict[str, Any]:
    """Record failure or certified recovery without storing any secrets."""
    import time

    now_ts = float(now_epoch if now_epoch is not None else time.time())
    path = _circuit_path(signature_key, state_dir=state_dir)
    prior = _load_json(path) or {}

    if certified_success:
        record = {
            "schema": "edarsahub.worker-circuit-breaker.v1",
            "signature_key": signature_key,
            "consecutive_failures": 0,
            "last_failure_epoch": 0.0,
            "last_certified_epoch": now_ts,
            "last_failure_class": "",
            "production_touched": False,
        }
    else:
        record = {
            "schema": "edarsahub.worker-circuit-breaker.v1",
            "signature_key": signature_key,
            "consecutive_failures": int(prior.get("consecutive_failures") or 0) + 1,
            "last_failure_epoch": now_ts,
            "last_certified_epoch": float(prior.get("last_certified_epoch") or 0.0),
            "last_failure_class": str(failure_class or "UNKNOWN")[:120],
            "production_touched": False,
        }
    _atomic_write_json(path, record)
    return record


CANONICAL_KNOWLEDGE_LESSONS: tuple[dict[str, Any], ...] = (
    {
        "lesson_id": "LESSON-MISSING-EXPECTED-SHA256",
        "failure_class": "MISSING_EXPECTED_SHA256",
        "problem_signature": "WRITE_EXISTING_REQUIRES_EXPECTED_SHA256",
        "root_cause": "write_file sobre archivo existente sin expected_sha256 ni validacion previa contra base_sha.",
        "source_job_id": "EDARSAHUB-BOS-SEC-P1-SESSION-REVOCATION-R3-20261120",
        "certified_repair_job_id": "EDARSAHUB-BOS-WORKER-OPS-PREPUBLISH-CONTRACT-PARITY-R1-20261120",
        "certified_commit_sha": "26f90b3bd07b6a6e0c2b79c0f0c2b8333d2cb27d",
        "certification": "CERTIFIED",
        "operational_validation": "NOT_APPLICABLE",
        "reusable_guardrail": "universal_job_bridge.validate_prepublish_contract",
        "prevention_rule": "Rechazar pre-publicacion todo write_file sobre archivo existente sin expected_sha256 coincidente con HEAD.",
        "production_touched": False,
    },
    {
        "lesson_id": "LESSON-EXECUTABLE-MODE-STRIP",
        "failure_class": "EXECUTABLE_MODE_STRIP",
        "problem_signature": "ATOMIC_WRITE_MODE_STRIP",
        "root_cause": "worker_mutation_materializer._atomic_write reemplazaba scripts ejecutables con modo temporal 0644 perdiendo +x.",
        "source_job_id": "EDARSAHUB-BOS-WORKER-OPS-GUARD-LOCK-FINALIZE-PARITY-R1-20261120",
        "certified_repair_job_id": "EDARSAHUB-BOS-WORKER-OPS-PREPUBLISH-CONTRACT-PARITY-R1-20261120",
        "certified_commit_sha": "26f90b3bd07b6a6e0c2b79c0f0c2b8333d2cb27d",
        "certification": "CERTIFIED",
        "operational_validation": "NOT_APPLICABLE",
        "reusable_guardrail": "worker_mutation_materializer._atomic_write",
        "prevention_rule": "Preservar stat.S_IMODE(target.stat().st_mode) mediante os.chmod antes de os.replace.",
        "production_touched": False,
    },
    {
        "lesson_id": "LESSON-GIT-DIVERGENCE-GUARD-PARITY",
        "failure_class": "GIT_MIRROR_DIVERGENCE",
        "problem_signature": "GUARD_CLI_EXIT_MISMATCH",
        "root_cause": "git_divergence_guard CLI devolvia exit 1 en comandos exitosos y finalize_local_snapshot no excluia deriva esperada de system_deps.txt.",
        "source_job_id": "EDARSAHUB-BOS-WORKER-OPS-GUARD-LOCK-FINALIZE-PARITY-R1-20261120",
        "certified_repair_job_id": "EDARSAHUB-BOS-WORKER-OPS-GUARD-LOCK-FINALIZE-PARITY-R1-20261120",
        "certified_commit_sha": "4926c7d5dc94f35c2ea1433b6d929d188c247bf6",
        "certification": "CERTIFIED",
        "operational_validation": "NOT_APPLICABLE",
        "reusable_guardrail": "git_divergence_guard.main+finalize_local_snapshot.sh",
        "prevention_rule": "Exigir paridad de exit codes fail-closed y exclusion compartida de .emergent/system_deps.txt.",
        "production_touched": False,
    },
    {
        "lesson_id": "LESSON-MIRROR-SYNC-POST-DISCONNECT",
        "failure_class": "MIRROR_SYNC_STOPPED",
        "problem_signature": "MIRROR_POST_DISCONNECT_STOPPED",
        "root_cause": "edarsahub-mirror-sync permanecia STOPPED tras reinicio de contenedor aun estando autorizado con ENABLED.",
        "source_job_id": "EDARSAHUB-BOS-WORKER-OPS-MIRROR-POST-DISCONNECT-RECOVERY-R1-20261120",
        "certified_repair_job_id": "EDARSAHUB-BOS-WORKER-OPS-MIRROR-POST-DISCONNECT-RECOVERY-R1-20261120",
        "certified_commit_sha": "163458aefa9bd29ea05af9930572c34c027cef39",
        "certification": "CERTIFIED",
        "operational_validation": "ACTIVE_IN_PREVIEW",
        "reusable_guardrail": "edarsahub_bootstrap_watchdog.maybe_recover_mirror_sync",
        "prevention_rule": "Recuperar automaticamente Mirror Sync solo cuando ENABLED este activo, sin STOP/PAUSED ni parada administrativa.",
        "production_touched": False,
    },
    {
        "lesson_id": "LESSON-SQL-AS-DICT-UNNAMED-COLUMN",
        "failure_class": "SQL_AS_DICT_UNNAMED_COLUMN",
        "problem_signature": "PYMSSQL_AS_DICT_UNNAMED_COLUMN",
        "root_cause": "Consultas SELECT 1 sin alias bajo pymssql cursor(as_dict=True) fallaban y execute_sql_query* silenciaba errores en [].",
        "source_job_id": "EDARSAHUB-BOS-SEC-P1-SESSION-REVOCATION-R2-20261120",
        "certified_repair_job_id": "EDARSAHUB-BOS-BACKEND-SQL-AS-DICT-FAIL-CLOSED-GUARD-R1-20261120",
        "certified_commit_sha": "709bba11d09a18c5e7fe3285a466d3bb2e5564f2",
        "certification": "CERTIFIED",
        "operational_validation": "NOT_APPLICABLE",
        "reusable_guardrail": "backend/tests/test_sql_as_dict_fail_closed_guard_r1.py",
        "prevention_rule": "Exigir alias explicitos en proyecciones externas as_dict=True y propagacion raise_on_error=True en rutas criticas.",
        "production_touched": False,
    },
    {
        "lesson_id": "LESSON-REVOKED-SESSION-ACCEPTED",
        "failure_class": "REVOKED_SESSION_ACCEPTED",
        "problem_signature": "SESSION_REVOCATION_FAIL_OPEN",
        "root_cause": "Validacion de sesion activa fallaba abierto cuando fetch_one=True devolvia [] o cuando SELECT sin alias fallaba en pymssql.",
        "source_job_id": "EDARSAHUB-BOS-SEC-P1-SESSION-REVOCATION-R2-20261120",
        "certified_repair_job_id": "EDARSAHUB-BOS-SEC-P1-SESSION-REVOCATION-R4-20261120",
        "certified_commit_sha": "653a8663b839b4e9e36b24ab0ee831a3db8089a7",
        "certification": "CERTIFIED",
        "operational_validation": "ACTIVE_IN_PREVIEW",
        "reusable_guardrail": "backend/tests/test_auth_session_revocation_p1_2.py",
        "prevention_rule": "Consultar columna nombrada SesionID, normalizar 0 filas a None y fallar cerrado ante error SQL.",
        "production_touched": False,
    },
    {
        "lesson_id": "LESSON-CODE-CERTIFIED-WITHOUT-PREVIEW-VALIDATION",
        "failure_class": "CODE_CERTIFIED_WITHOUT_OPERATIONAL_VALIDATION",
        "problem_signature": "CERTIFIED_WITHOUT_PREVIEW_EVIDENCE",
        "root_cause": "La certificacion tecnica de codigo (CERTIFIED) no diferenciaba si el comportamiento operativo ya habia sido validado en Preview.",
        "source_job_id": "EDARSAHUB-BOS-SEC-P1-SESSION-REVOCATION-R2-20261120",
        "certified_repair_job_id": "EDARSAHUB-BOS-WORKER-OPS-OPERATIONAL-PARITY-AND-KNOWLEDGE-R1-20261120",
        "certified_commit_sha": None,
        "certification": "PENDING_CERTIFICATION",
        "operational_validation": "PENDING_PREVIEW_VALIDATION",
        "reusable_guardrail": "worker_result_status.build_differentiated_evidence",
        "prevention_rule": "Separar SUBMITTED, INTEGRATED, CERTIFIED y ACTIVE_IN_PREVIEW exigiendo evidencia operativa SHA-bound para Preview.",
        "production_touched": False,
    },
)


def lookup_canonical_lesson(
    *,
    failure_class: str = "",
    problem_signature: str = "",
    source_job_id: str = "",
) -> dict[str, Any] | None:
    fc = str(failure_class or "").strip().upper()
    ps = str(problem_signature or "").strip().upper()
    sj = str(source_job_id or "").strip()

    for lesson in CANONICAL_KNOWLEDGE_LESSONS:
        if ps and str(lesson["problem_signature"]).upper() == ps:
            return dict(lesson)
        if fc and str(lesson["failure_class"]).upper() == fc:
            return dict(lesson)
    if sj:
        for lesson in CANONICAL_KNOWLEDGE_LESSONS:
            if str(lesson["source_job_id"]) == sj:
                return dict(lesson)
    return None


def prevent_duplicate_historical_repair(
    *,
    incident_id: str,
    source_job_id: str = "",
    problem_signature: str | None = None,
    blockers: list[str] | tuple[str, ...] = (),
    target_paths: list[str] | tuple[str, ...] = (),
) -> dict[str, Any]:
    """Prevent re-executing a repair already resolved and certified in historical knowledge."""
    clean_source = str(source_job_id or "").strip()
    clean_sig = str(problem_signature or "").strip().upper()
    classification = classify_failure_taxonomy(
        blockers=blockers,
        error_code=clean_sig,
        causal_evidence={"incident_id": incident_id} if incident_id else None,
    )
    lesson = lookup_canonical_lesson(
        failure_class=classification.get("failure_class") or "",
        problem_signature=clean_sig,
        source_job_id="",
    )
    if (
        lesson is not None
        and lesson.get("certification") == "CERTIFIED"
        and lesson.get("production_touched") is False
        and (
            (clean_source and clean_source == lesson.get("source_job_id"))
            or (clean_sig and clean_sig == str(lesson.get("problem_signature") or "").upper())
        )
    ):
        return {
            "duplicate_prevented": True,
            "reason": f"HISTORICAL_CERTIFIED_LESSON:{lesson['lesson_id']}",
            "matched_lesson_id": lesson["lesson_id"],
            "matched_repair_job_id": lesson["certified_repair_job_id"],
            "matched_commit_sha": lesson["certified_commit_sha"],
            "production_touched": False,
        }

    if maintenance.INCIDENT_DIR.is_dir():
        clean_paths = {str(p).strip() for p in (target_paths or ()) if str(p).strip()}
        for path in sorted(maintenance.INCIDENT_DIR.glob("*.json")):
            payload = _load_json(path)
            if not isinstance(payload, dict):
                continue
            if payload.get("state") != "CERTIFIED" or payload.get("production_touched") is not False:
                continue
            existing_id = str(payload.get("incident_id") or path.stem).strip()
            if existing_id == incident_id:
                continue
            existing_source = str(payload.get("source_job_id") or "").strip()
            existing_paths = {
                str(p).strip()
                for p in (payload.get("target_paths") or [])
                if isinstance(p, str) and str(p).strip()
            }
            if (clean_source and existing_source == clean_source) or (
                clean_paths and existing_paths and clean_paths.issubset(existing_paths)
            ):
                return {
                    "duplicate_prevented": True,
                    "reason": f"HISTORICAL_CERTIFIED_INCIDENT:{existing_id}",
                    "matched_lesson_id": None,
                    "matched_repair_job_id": payload.get("repair_job_id"),
                    "matched_commit_sha": payload.get("repair_commit_sha"),
                    "production_touched": False,
                }

    return {
        "duplicate_prevented": False,
        "reason": "NO_CERTIFIED_DUPLICATE_FOUND",
        "matched_lesson_id": lesson["lesson_id"] if lesson else None,
        "matched_repair_job_id": None,
        "matched_commit_sha": None,
        "production_touched": False,
    }


def assess_knowledge_loop_cycle(
    *,
    incident_id: str,
    status: str = "",
    blockers: list[str] | tuple[str, ...] = (),
    error_code: str = "",
    source_job_id: str = "",
    target_paths: list[str] | tuple[str, ...] = (),
    causal_evidence: dict[str, Any] | None = None,
    max_failures: int = 3,
    cooldown_seconds: int = 900,
    now_epoch: float | None = None,
    state_dir: Path | None = None,
) -> dict[str, Any]:
    """Evaluate Detect -> Classify -> Diagnose -> Circuit Breaker -> Duplicate Guard -> Authorize."""
    classification = classify_failure_taxonomy(
        status=status,
        blockers=blockers,
        error_code=error_code,
        causal_evidence=causal_evidence,
    )
    lesson = lookup_canonical_lesson(
        failure_class=classification.get("failure_class") or "",
        problem_signature=error_code,
        source_job_id=source_job_id,
    )
    duplicate_guard = prevent_duplicate_historical_repair(
        incident_id=incident_id,
        source_job_id=source_job_id,
        problem_signature=error_code,
        blockers=blockers,
        target_paths=target_paths,
    )
    circuit = evaluate_circuit_breaker(
        incident_id,
        max_failures=max_failures,
        cooldown_seconds=cooldown_seconds,
        now_epoch=now_epoch,
        state_dir=state_dir,
    )

    if duplicate_guard["duplicate_prevented"]:
        next_step = "DUPLICATE_HISTORICAL_REPAIR_PREVENTED"
    elif not circuit["allow_attempt"]:
        next_step = "CIRCUIT_OPEN_STOP"
    elif classification["human_approval_required"] or classification["category"] in {"SECURITY", "BUSINESS"}:
        next_step = "HUMAN_APPROVAL_REQUIRED"
    elif not classification["has_causal_evidence"]:
        next_step = "COLLECT_CAUSAL_EVIDENCE_FIRST"
    elif classification["auto_repair_allowed"]:
        next_step = "AUTO_REPAIR_ELIGIBLE"
    else:
        next_step = classification["recovery_strategy"]

    return {
        "schema": "edarsahub.worker-knowledge-loop-assessment.v1",
        "incident_id": incident_id,
        "classification": classification,
        "matched_lesson": lesson,
        "duplicate_repair_check": duplicate_guard,
        "circuit_breaker": circuit,
        "next_step": next_step,
        "learning_allowed_only_if_certified": True,
        "production_touched": False,
    }
