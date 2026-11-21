"""Derived per-job result status.

This is an index/reference layer, never a second terminal source of truth.
"""
from __future__ import annotations

import re
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


PREVIEW_VALIDATION_SCHEMA = "edarsahub.preview-operational-validation.v1"
_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA64_RE = re.compile(r"^[0-9a-f]{64}$")
_SENSITIVE_PREVIEW_KEYS = frozenset(
    {
        "password",
        "secret",
        "token",
        "credential",
        "credentials",
        "api_key",
        "apikey",
        "private_key",
        "authorization",
        "cookie",
    }
)


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, dict):
        for k, v in value.items():
            low = str(k or "").strip().lower()
            if any(tok in low for tok in _SENSITIVE_PREVIEW_KEYS):
                return True
            if _contains_sensitive_key(v):
                return True
    elif isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def validate_operational_preview_evidence(
    raw_evidence: Any,
    *,
    expected_job_id: str,
    expected_commit_sha: str | None = None,
) -> dict[str, Any]:
    """Validate Preview operational evidence fail-closed without mutating historical results."""
    if raw_evidence is None:
        return {
            "valid": False,
            "present": False,
            "status": "PENDING_PREVIEW_VALIDATION",
            "reason": "PREVIEW_EVIDENCE_ABSENT",
            "preview_activated": False,
            "operational_tests": "NOT_RUN",
            "functional_result": "UNVERIFIED",
        }

    if not isinstance(raw_evidence, dict):
        return {
            "valid": False,
            "present": True,
            "status": "PREVIEW_VALIDATION_FAILED",
            "reason": "PREVIEW_EVIDENCE_NOT_OBJECT",
            "preview_activated": False,
            "operational_tests": "FAIL",
            "functional_result": "FAIL",
        }

    if _contains_sensitive_key(raw_evidence):
        return {
            "valid": False,
            "present": True,
            "status": "PREVIEW_VALIDATION_FAILED",
            "reason": "PREVIEW_EVIDENCE_SENSITIVE_FIELD_FORBIDDEN",
            "preview_activated": False,
            "operational_tests": "FAIL",
            "functional_result": "FAIL",
        }

    if str(raw_evidence.get("schema") or "").strip() != PREVIEW_VALIDATION_SCHEMA:
        return {
            "valid": False,
            "present": True,
            "status": "PREVIEW_VALIDATION_FAILED",
            "reason": "PREVIEW_EVIDENCE_SCHEMA_INVALID",
            "preview_activated": False,
            "operational_tests": "FAIL",
            "functional_result": "FAIL",
        }

    ev_job_id = str(raw_evidence.get("job_id") or "").strip()
    if not ev_job_id or ev_job_id != str(expected_job_id or "").strip():
        return {
            "valid": False,
            "present": True,
            "status": "PREVIEW_VALIDATION_FAILED",
            "reason": "PREVIEW_EVIDENCE_JOB_ID_MISMATCH",
            "preview_activated": False,
            "operational_tests": "FAIL",
            "functional_result": "FAIL",
        }

    ev_sha = str(raw_evidence.get("commit_sha") or "").strip().lower()
    if not _SHA40_RE.fullmatch(ev_sha):
        return {
            "valid": False,
            "present": True,
            "status": "PREVIEW_VALIDATION_FAILED",
            "reason": "PREVIEW_EVIDENCE_COMMIT_SHA_INVALID",
            "preview_activated": False,
            "operational_tests": "FAIL",
            "functional_result": "FAIL",
        }

    expected_sha_clean = str(expected_commit_sha or "").strip().lower()
    if expected_sha_clean and ev_sha != expected_sha_clean:
        return {
            "valid": False,
            "present": True,
            "status": "PREVIEW_VALIDATION_FAILED",
            "reason": "PREVIEW_EVIDENCE_COMMIT_SHA_MISMATCH",
            "preview_activated": False,
            "operational_tests": "FAIL",
            "functional_result": "FAIL",
        }

    if raw_evidence.get("production_touched") is not False:
        return {
            "valid": False,
            "present": True,
            "status": "PREVIEW_VALIDATION_FAILED",
            "reason": "PREVIEW_EVIDENCE_PRODUCTION_TOUCHED",
            "preview_activated": False,
            "operational_tests": "FAIL",
            "functional_result": "FAIL",
        }

    validated_at = str(raw_evidence.get("validated_at_utc") or "").strip()
    if not validated_at:
        return {
            "valid": False,
            "present": True,
            "status": "PREVIEW_VALIDATION_FAILED",
            "reason": "PREVIEW_EVIDENCE_TIMESTAMP_REQUIRED",
            "preview_activated": False,
            "operational_tests": "FAIL",
            "functional_result": "FAIL",
        }

    ev_digest = raw_evidence.get("evidence_sha256")
    if ev_digest is not None and not _SHA64_RE.fullmatch(str(ev_digest).strip().lower()):
        return {
            "valid": False,
            "present": True,
            "status": "PREVIEW_VALIDATION_FAILED",
            "reason": "PREVIEW_EVIDENCE_DIGEST_INVALID",
            "preview_activated": False,
            "operational_tests": "FAIL",
            "functional_result": "FAIL",
        }

    preview_activated = raw_evidence.get("preview_activated") is True
    op_tests = str(raw_evidence.get("operational_tests") or "").strip().upper()
    func_res = str(raw_evidence.get("functional_result") or "").strip().upper()

    if preview_activated and op_tests == "PASS" and func_res == "PASS":
        sanitized: dict[str, Any] = {
            "schema": PREVIEW_VALIDATION_SCHEMA,
            "job_id": ev_job_id,
            "commit_sha": ev_sha,
            "preview_activated": True,
            "operational_tests": "PASS",
            "functional_result": "PASS",
            "validated_at_utc": validated_at,
            "production_touched": False,
        }
        if ev_digest is not None:
            sanitized["evidence_sha256"] = str(ev_digest).strip().lower()
        if isinstance(raw_evidence.get("checks_passed"), int) and not isinstance(raw_evidence.get("checks_passed"), bool):
            sanitized["checks_passed"] = raw_evidence["checks_passed"]
        if isinstance(raw_evidence.get("checks_total"), int) and not isinstance(raw_evidence.get("checks_total"), bool):
            sanitized["checks_total"] = raw_evidence["checks_total"]
        return {
            "valid": True,
            "present": True,
            "status": "ACTIVE_IN_PREVIEW",
            "reason": "PREVIEW_OPERATIONAL_VALIDATED",
            "preview_activated": True,
            "operational_tests": "PASS",
            "functional_result": "PASS",
            "sanitized": sanitized,
        }

    return {
        "valid": False,
        "present": True,
        "status": "PREVIEW_VALIDATION_FAILED",
        "reason": "PREVIEW_OPERATIONAL_CHECKS_NOT_PASS",
        "preview_activated": preview_activated,
        "operational_tests": op_tests if op_tests in {"PASS", "FAIL"} else "FAIL",
        "functional_result": func_res if func_res in {"PASS", "FAIL"} else "FAIL",
    }


def build_differentiated_evidence(
    payload: dict[str, Any],
    *,
    job_id: str,
    terminal_valid: bool,
    commit_sha: str | None = None,
    preview_evidence: Any = None,
) -> dict[str, Any]:
    """Build differentiated technical certification vs operational Preview validation state."""
    raw_status = str(payload.get("status") or "").strip().upper()
    cert = str(payload.get("certification") or "").strip().upper()
    qg = str(payload.get("quality_gate") or "PENDING").strip().upper() or "PENDING"
    tests = str(payload.get("tests") or "PENDING").strip().upper() or "PENDING"
    git_sync = str(payload.get("git_sync_status") or "").strip().upper()
    mode = str(payload.get("slot_class") or payload.get("mode") or "").strip().upper()

    is_readonly = (
        mode == "READ_ONLY"
        or raw_status == "READ_ONLY_COMPLETE"
        or cert == "CERTIFIED_READ_ONLY"
    )
    code_certified = bool(terminal_valid and cert in _CERTIFIED_VALUES)

    has_attestation = bool(
        payload.get("attestation_sha256")
        or (
            code_certified
            and str(payload.get("certification_basis") or "").strip()
        )
    )
    attestation_state = (
        "VERIFIED"
        if has_attestation
        else ("NOT_APPLICABLE" if is_readonly else "PENDING")
    )
    git_sync_state = (
        git_sync
        if git_sync
        else ("NOT_APPLICABLE" if is_readonly else "UNVERIFIED")
    )

    effective_preview_raw = (
        preview_evidence
        if preview_evidence is not None
        else payload.get("operational_validation")
    )

    if not terminal_valid:
        lifecycle_stage = "INVALID"
        op_status = "NOT_APPLICABLE"
        op_validated = False
        preview_act = "NOT_APPLICABLE"
        op_tests = "NOT_APPLICABLE"
        func_res = "NOT_APPLICABLE"
        preview_reason = "TERMINAL_RESULT_INVALID"
        sanitized_preview = None
    elif is_readonly:
        lifecycle_stage = "CERTIFIED" if code_certified else "REJECTED"
        op_status = "NOT_APPLICABLE"
        op_validated = False
        preview_act = "NOT_APPLICABLE"
        op_tests = "NOT_APPLICABLE"
        func_res = "NOT_APPLICABLE"
        preview_reason = "READ_ONLY_JOB"
        sanitized_preview = None
    elif raw_status == "INTEGRATED":
        preview_eval = validate_operational_preview_evidence(
            effective_preview_raw,
            expected_job_id=job_id,
            expected_commit_sha=commit_sha,
        )
        sanitized_preview = preview_eval.get("sanitized")
        if code_certified and preview_eval["valid"]:
            lifecycle_stage = "ACTIVE_IN_PREVIEW"
            op_status = "ACTIVE_IN_PREVIEW"
            op_validated = True
            preview_act = "ACTIVE"
            op_tests = "PASS"
            func_res = "PASS"
            preview_reason = preview_eval["reason"]
        elif preview_eval["present"] and not preview_eval["valid"]:
            lifecycle_stage = "CERTIFIED" if code_certified else "INTEGRATED"
            op_status = "PREVIEW_VALIDATION_FAILED"
            op_validated = False
            preview_act = "ACTIVE" if preview_eval["preview_activated"] else "UNVERIFIED"
            op_tests = preview_eval["operational_tests"]
            func_res = preview_eval["functional_result"]
            preview_reason = preview_eval["reason"]
        else:
            # Code certification NEVER auto-declares ACTIVE_IN_PREVIEW
            lifecycle_stage = "CERTIFIED" if code_certified else "INTEGRATED"
            op_status = "PENDING_PREVIEW_VALIDATION"
            op_validated = False
            preview_act = "UNVERIFIED"
            op_tests = "NOT_RUN"
            func_res = "UNVERIFIED"
            preview_reason = "CODE_CERTIFIED_AWAITING_PREVIEW_VALIDATION" if code_certified else "INTEGRATED_AWAITING_CERTIFICATION_AND_PREVIEW"
    elif code_certified:
        lifecycle_stage = "CERTIFIED"
        op_status = "PENDING_PREVIEW_VALIDATION"
        op_validated = False
        preview_act = "UNVERIFIED"
        op_tests = "NOT_RUN"
        func_res = "UNVERIFIED"
        preview_reason = "CODE_CERTIFIED_AWAITING_PREVIEW_VALIDATION"
        sanitized_preview = None
    else:
        lifecycle_stage = "REJECTED"
        op_status = "NOT_APPLICABLE"
        op_validated = False
        preview_act = "NOT_APPLICABLE"
        op_tests = "NOT_APPLICABLE"
        func_res = "NOT_APPLICABLE"
        preview_reason = "NOT_INTEGRATED"
        sanitized_preview = None

    return {
        "lifecycle_stage": lifecycle_stage,
        "code_certified": code_certified,
        "operational_validated": op_validated,
        "operational_validation_status": op_status,
        "operational_validation_reason": preview_reason,
        "sanitized_preview_evidence": sanitized_preview,
        "evidence_breakdown": {
            "quality_gate": qg if terminal_valid else "FAIL",
            "tests": tests if terminal_valid else "FAIL",
            "git_sync": git_sync_state,
            "attestation": attestation_state,
            "preview_activation": preview_act,
            "operational_tests": op_tests,
            "functional_result": func_res,
        },
    }


def build_job_status(
    *,
    result_read: Any,
    preview_evidence: Any = None,
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
            "lifecycle_stage": "INVALID",
            "code_certified": False,
            "operational_validated": False,
            "operational_validation_status": "NOT_APPLICABLE",
            "evidence_breakdown": {
                "quality_gate": "FAIL",
                "tests": "FAIL",
                "git_sync": "UNVERIFIED",
                "attestation": "PENDING",
                "preview_activation": "NOT_APPLICABLE",
                "operational_tests": "NOT_APPLICABLE",
                "functional_result": "NOT_APPLICABLE",
            },
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

    diff_ev = build_differentiated_evidence(
        payload,
        job_id=result_read.job_id,
        terminal_valid=True,
        commit_sha=str(commit_sha) if commit_sha else None,
        preview_evidence=preview_evidence,
    )
    status_dict["lifecycle_stage"] = diff_ev["lifecycle_stage"]
    status_dict["code_certified"] = diff_ev["code_certified"]
    status_dict["operational_validated"] = diff_ev["operational_validated"]
    status_dict["operational_validation_status"] = diff_ev["operational_validation_status"]
    status_dict["evidence_breakdown"] = diff_ev["evidence_breakdown"]
    if diff_ev["sanitized_preview_evidence"] is not None:
        status_dict["operational_validation"] = diff_ev["sanitized_preview_evidence"]

    return status_dict
