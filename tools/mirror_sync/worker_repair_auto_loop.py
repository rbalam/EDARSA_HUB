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
        if isinstance(det_row, dict):
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
