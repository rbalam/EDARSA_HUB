#!/usr/bin/env python3
"""Publish sanitized worker results and SHA-bound test attestations.

This closes the runtime -> GitHub result path. It never publishes raw executor
output. Successful integrated jobs create a test attestation consumed by the
existing mirror audit exporter; unsuccessful jobs are still published to the
queue results branch as NOT_CERTIFIED/BLOCKED evidence.
"""

from __future__ import annotations

# WORKER_DELIVERABLE_IMPORT_COMPAT_V1
try:
    from tools.mirror_sync.worker_deliverable_contract import evaluate_deliverables
except ModuleNotFoundError:
    from worker_deliverable_contract import evaluate_deliverables

import fcntl
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# WORKER_RESULT_INTEGRITY_IMPORT_COMPAT_V1
try:
    from tools.mirror_sync.worker_result_integrity import (
        ResultState,
        inspect_result_file,
        is_terminal_result_path,
        validate_terminal_result_file,
        validate_terminal_result_payload,
    )
except ModuleNotFoundError:
    from worker_result_integrity import (
        ResultState,
        inspect_result_file,
        is_terminal_result_path,
        validate_terminal_result_file,
        validate_terminal_result_payload,
    )

try:
    from tools.mirror_sync.worker_result_semantic_extract import (
        ALLOWED_PROVENANCE_DERIVATIONS,
        ALLOWED_PROVENANCE_STATUSES,
        CERTIFICATION_BASIS_RE,
        DECISION_FIELDS,
        FIELD_NAME_RE,
        MAX_CONTAINER_ITEMS,
        MAX_SERIALIZED_BYTES,
        MAX_SUMMARY_LENGTH,
        has_sensitive_marker,
        is_authentic_lineage_commit,
        is_sensitive_key,
        redact_sensitive_text,
        sanitize_dynamic_value,
        sanitize_provenance_entry,
        sanitize_repository_contract_payload,
        validate_decision_field,
    )
except ModuleNotFoundError:
    import sys as _sys

    _mirror_dir = str(Path(__file__).resolve().parent)
    if _mirror_dir not in _sys.path:
        _sys.path.insert(0, _mirror_dir)
    from worker_result_semantic_extract import (
        ALLOWED_PROVENANCE_DERIVATIONS,
        ALLOWED_PROVENANCE_STATUSES,
        CERTIFICATION_BASIS_RE,
        DECISION_FIELDS,
        FIELD_NAME_RE,
        MAX_CONTAINER_ITEMS,
        MAX_SERIALIZED_BYTES,
        MAX_SUMMARY_LENGTH,
        has_sensitive_marker,
        is_authentic_lineage_commit,
        is_sensitive_key,
        redact_sensitive_text,
        sanitize_dynamic_value,
        sanitize_provenance_entry,
        sanitize_repository_contract_payload,
        validate_decision_field,
    )

ROOT = Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
STATE = ROOT / ".git" / "universal-worker-queue"
RESULTS = STATE / "results"
REJECTED = STATE / "rejected"
PUBLISHED = STATE / "published"
QUEUE_BRANCH = os.environ.get("EDARSAHUB_QUEUE_BRANCH", "worker/requests")
RESULT_BRANCH = os.environ.get(
    "EDARSAHUB_RESULT_BRANCH",
    "worker/results",
)
REMOTE = os.environ.get("EDARSAHUB_QUEUE_REMOTE", "origin")
GIT_TIMEOUT_SECONDS = int(
    os.environ.get("EDARSAHUB_RESULT_GIT_TIMEOUT_SECONDS", "30")
)

RESULT_BATCH_SIZE = int(
    os.environ.get("EDARSAHUB_RESULT_BATCH_SIZE", "2")
)
DEV_BRANCH = "Edarsahub_Desarrollo"
MIRROR_BRANCH = "mirror/emergent-live"
REPORT_DIR = Path(os.environ.get("MIRROR_SYNC_REPORT_STATE_DIR", "/app/.git/mirror-sync/reporting"))
ATTESTATIONS = REPORT_DIR / "test_attestations"
PUBLISH_LOCK = STATE / "result_publisher.lock"
WORKTREE_PARENT = Path(
    os.environ.get(
        "EDARSAHUB_QUEUE_PUBLISH_WORKTREE_PARENT",
        "/tmp",
    )
)

QUEUE_PUBLISH_MAX_ATTEMPTS = int(
    os.environ.get(
        "EDARSAHUB_QUEUE_PUBLISH_MAX_ATTEMPTS",
        "8",
    )
)


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd or ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=GIT_TIMEOUT_SECONDS,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def git(*args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        result = run(["git", *args], cwd=cwd)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"GIT_TIMEOUT:{' '.join(args)}:"
            f"timeout={GIT_TIMEOUT_SECONDS}s"
        ) from exc

    if check and result.returncode != 0:
        raise RuntimeError(f"GIT_FAILED:{' '.join(args)}:{result.stdout[-1500:]}")
    return result


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("RESULT_NOT_OBJECT")
    return value


def invalid_result_artifact_payload(
    path: Path,
    inspection: Any,
) -> dict[str, Any]:
    """Build a terminal fail-closed result for corrupt local artifacts.

    This prevents zero-byte or non-JSON artifacts from being preserved as if
    they were valid worker results. The artifact remains auditable, but it is
    explicitly NOT_CERTIFIED and cannot open a downstream gate.
    """
    raw_job_id = path.stem.strip()
    allowed = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789._-"
    )
    job_id = (
        raw_job_id
        if raw_job_id and all(ch in allowed for ch in raw_job_id)
        else "INVALID-RESULT-ARTIFACT"
    )
    state = getattr(inspection, "state", "RESULT_INVALID_JSON")
    state_value = getattr(state, "value", str(state))
    reason = str(getattr(inspection, "reason", "") or state_value)
    stamp = now()

    return {
        "schema": "edarsahub.worker-result.v2",
        "job_id": job_id,
        "started_at_utc": stamp,
        "completed_at_utc": stamp,
        "status": "INVALID_RESULT_ARTIFACT",
        "executor": "universal-result-publisher",
        "tests": "FAIL",
        "quality_gate": "FAIL",
        "files_changed": [],
        "summary_es": (
            "El publicador detecto un artifact terminal vacio, corrupto o no "
            "procesable en worker/results y lo convirtio en evidencia "
            "NOT_CERTIFIED para fallar cerrado."
        ),
        "blockers": [
            f"invalid_result_artifact:{state_value}:{reason}",
        ],
        "percent_complete": 0,
        "certification": "NOT_CERTIFIED",
        "production_touched": False,
        "invalid_result_artifact": True,
        "source_result_path": path.as_posix(),
        "result_integrity_state": state_value,
        "result_integrity_reason": reason,
        "result_size_bytes": int(getattr(inspection, "size_bytes", 0) or 0),
        "result_sha256": str(getattr(inspection, "sha256", "") or ""),
    }


def load_publishable_result(path: Path) -> dict[str, Any]:
    """Load a local result or synthesize a fail-closed invalid artifact result."""
    if path.parent.name == "results":
        inspection = inspect_result_file(path)
        if inspection.state != ResultState.RESULT_TERMINAL_VALID:
            return invalid_result_artifact_payload(path, inspection)

    return load(path)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    if is_terminal_result_path(path):
        validate_terminal_result_payload(payload)

    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temp = handle.name
    os.replace(temp, path)
    if is_terminal_result_path(path):
        validate_terminal_result_file(path)


def valid_sha(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 40
        and all(ch in "0123456789abcdef" for ch in value.lower())
    )


def authentic_lineage_sha(value: Any) -> bool:
    return valid_sha(value) and is_authentic_lineage_commit(value)


SENSITIVE_COLUMN_TOKENS = (
    "secret", "password", "passwd", "token", "credential",
    "credencial", "encrypted", "cifrad", "api_key", "apikey",
    "private_key", "access_key",
)


def _sensitive_column(name: Any) -> bool:
    normalized = str(name or "").strip().lower()
    return any(token in normalized for token in SENSITIVE_COLUMN_TOKENS)


def sanitize_readonly_evidence(result: dict[str, Any]) -> dict[str, Any] | None:
    checks = result.get("checks") or []
    sanitized_checks = []
    for check in checks:
        if not isinstance(check, dict) or check.get("type") != "sql_readonly_audit":
            continue
        payload = check.get("sql_evidence")
        if not isinstance(payload, dict):
            raw = check.get("output")
            if isinstance(raw, str):
                try:
                    candidate = json.loads(raw.strip())
                except (json.JSONDecodeError, TypeError):
                    candidate = None
                if isinstance(candidate, dict):
                    payload = candidate
        if not isinstance(payload, dict) or payload.get("status") != "PASS":
            continue
        entries = []
        for entry in payload.get("evidence") or []:
            if not isinstance(entry, dict):
                continue
            columns = [str(value) for value in (entry.get("columns") or [])]
            rows = []
            for row in entry.get("rows") or []:
                if not isinstance(row, list):
                    continue
                rows.append([
                    "[REDACTED]" if index < len(columns) and _sensitive_column(columns[index]) else value
                    for index, value in enumerate(row)
                ])
            entries.append({
                "name": entry.get("name"),
                "columns": columns,
                "rows": rows,
                "row_count_returned": entry.get("row_count_returned"),
                "truncated": entry.get("truncated"),
            })
        sanitized_checks.append({
            "status": "PASS",
            "mode": payload.get("mode"),
            "connection": payload.get("connection"),
            "evidence": entries,
        })
    return {"checks": sanitized_checks} if sanitized_checks else None


def sanitize_repository_evidence(result: dict[str, Any]) -> dict[str, Any] | None:
    sanitized_checks = []
    for check in result.get("checks") or []:
        if not isinstance(check, dict) or check.get("type") != "repository_contract_audit":
            continue
        payload = check.get("repository_evidence")
        sanitized = sanitize_repository_contract_payload(payload)
        if sanitized is None:
            continue
        sanitized_checks.extend(sanitized.get("checks") or [])
    return {"checks": sanitized_checks} if sanitized_checks else None


def _sanitize_semantic_field_map(
    raw_sem_fields: Any,
) -> tuple[dict[str, Any], list[str], bool]:
    if not isinstance(raw_sem_fields, dict) or len(raw_sem_fields) > MAX_CONTAINER_ITEMS:
        return {}, [], True
    safe_sem_fields: dict[str, Any] = {}
    invalidated_keys: list[str] = []
    had_invalid = False
    for raw_key, raw_val in raw_sem_fields.items():
        if not isinstance(raw_key, str) or not FIELD_NAME_RE.fullmatch(raw_key):
            had_invalid = True
            continue
        if is_sensitive_key(raw_key):
            had_invalid = True
            invalidated_keys.append(raw_key)
            continue
        if raw_val is None:
            safe_sem_fields[raw_key] = None
            continue
        if raw_key == "execution_base_sha":
            if isinstance(raw_val, str) and authentic_lineage_sha(raw_val.strip()):
                safe_sem_fields[raw_key] = raw_val.strip()
            else:
                safe_sem_fields[raw_key] = None
                invalidated_keys.append(raw_key)
                had_invalid = True
            continue
        if raw_key == "repository_evidence":
            clean_repo = sanitize_repository_contract_payload(raw_val)
            if clean_repo is not None:
                safe_sem_fields[raw_key] = clean_repo
            else:
                safe_sem_fields[raw_key] = None
                invalidated_keys.append(raw_key)
                had_invalid = True
            continue
        try:
            if raw_key in DECISION_FIELDS:
                clean_val = validate_decision_field(raw_key, raw_val)
            elif raw_key == "certification_basis":
                if (
                    not isinstance(raw_val, str)
                    or not CERTIFICATION_BASIS_RE.fullmatch(raw_val.strip())
                    or has_sensitive_marker(raw_val)
                ):
                    raise ValueError("INVALID_CERTIFICATION_BASIS")
                clean_val = raw_val.strip()
            elif raw_key == "summary_es":
                clean_val = sanitize_dynamic_value(raw_val, max_str_len=MAX_SUMMARY_LENGTH)
                if not isinstance(clean_val, str):
                    raise ValueError("INVALID_SUMMARY_ES")
            else:
                clean_val = sanitize_dynamic_value(raw_val)
            encoded = json.dumps(clean_val, ensure_ascii=False, sort_keys=True).encode("utf-8")
            if len(encoded) > MAX_SERIALIZED_BYTES:
                raise ValueError("FIELD_TOO_LARGE")
            safe_sem_fields[raw_key] = clean_val
        except (ValueError, TypeError):
            safe_sem_fields[raw_key] = False if raw_key in {"gate3_allowed", "last_gate_certified"} else None
            invalidated_keys.append(raw_key)
            had_invalid = True

    total_encoded = json.dumps(safe_sem_fields, ensure_ascii=False, sort_keys=True).encode("utf-8")
    if len(total_encoded) > MAX_SERIALIZED_BYTES:
        return {"gate3_allowed": False}, list(safe_sem_fields.keys()), True
    return safe_sem_fields, invalidated_keys, had_invalid


def _sanitize_provenance_map(
    raw_provenance: Any,
    invalidated_keys: list[str],
) -> tuple[dict[str, dict[str, Any]], bool]:
    if raw_provenance is None:
        return {}, False
    if not isinstance(raw_provenance, dict) or len(raw_provenance) > MAX_CONTAINER_ITEMS:
        return {}, True
    cleaned: dict[str, dict[str, Any]] = {}
    had_invalid = False
    for field, pval in raw_provenance.items():
        if not isinstance(field, str) or not FIELD_NAME_RE.fullmatch(field) or is_sensitive_key(field):
            had_invalid = True
            continue
        if not isinstance(pval, dict):
            had_invalid = True
            cleaned[field] = sanitize_provenance_entry(None)
            continue
        raw_status = pval.get("status")
        raw_derivation = pval.get("derivation")
        raw_source_key = pval.get("source_key")
        if (
            not isinstance(raw_status, str)
            or raw_status not in ALLOWED_PROVENANCE_STATUSES
            or not isinstance(raw_derivation, str)
            or raw_derivation not in ALLOWED_PROVENANCE_DERIVATIONS
            or (
                raw_source_key is not None
                and (
                    not isinstance(raw_source_key, str)
                    or not FIELD_NAME_RE.fullmatch(raw_source_key)
                    or is_sensitive_key(raw_source_key)
                )
            )
        ):
            had_invalid = True
        cleaned[field] = sanitize_provenance_entry(pval)
    for key in invalidated_keys:
        if FIELD_NAME_RE.fullmatch(key) and not is_sensitive_key(key):
            cleaned[key] = {
                "status": "INVALID_OR_UNVERIFIED_EXPLICIT_VALUE",
                "source_key": key,
                "derivation": "FAIL_CLOSED_NULL",
            }
    return cleaned, had_invalid


def _sanitize_string_list(value: Any, *, max_item_len: int = 256) -> list[str]:
    if not isinstance(value, list):
        return []
    result_list: list[str] = []
    for item in value[:MAX_CONTAINER_ITEMS]:
        if isinstance(item, str) and item.strip() and "\x00" not in item:
            result_list.append(redact_sensitive_text(item.strip(), max_length=max_item_len))
    return result_list


def sanitize_semantic_evidence(result: dict[str, Any]) -> dict[str, Any] | None:
    allowed_payload_keys = (
        "status", "mode", "bridge_verdict", "runtime_gap_confirmed",
        "source_result_reader_capability_current_state",
        "can_read_worker_results_by_branch_path",
        "can_read_worker_results_by_blob_sha",
        "can_emit_semantic_fields_from_source_result",
        "source_semantic_fields_complete", "source_missing_semantic_fields",
        "source_explicit_missing_semantic_fields", "semantic_field_provenance",
        "semantic_fields_complete", "missing_semantic_fields",
        "semantic_fields", "gate3_allowed",
        "source_result_read_status", "source_result_path",
        "source_result_branch", "source_result_commit",
        "source_result_blob_sha", "source_result_size_bytes",
        "source_result_sha256", "source_result_loader",
        "source_status", "source_quality_gate", "source_certification",
        "source_work_completion", "source_percent_complete",
        "source_production_touched", "source_files_changed",
        "source_blockers", "required_runtime_change",
        "next_allowed_step",
    )
    checks = []
    promoted: dict[str, Any] = {}
    any_check_failed = False

    for check in result.get("checks") or []:
        if not isinstance(check, dict) or check.get("type") != "worker_result_semantic_extract":
            continue
        payload = check.get("semantic_evidence")
        if not isinstance(payload, dict):
            raw = check.get("output")
            if isinstance(raw, str):
                try:
                    candidate = json.loads(raw.strip())
                except (json.JSONDecodeError, TypeError):
                    candidate = None
                if isinstance(candidate, dict):
                    payload = candidate
        if not isinstance(payload, dict):
            any_check_failed = True
            continue

        check_passed = (
            str(check.get("status") or "PASS").upper() == "PASS"
            and check.get("returncode") in (0, None)
            and str(payload.get("status") or "").upper() == "PASS"
        )
        if not check_passed:
            any_check_failed = True

        safe_payload = {key: payload.get(key) for key in allowed_payload_keys if key in payload}
        safe_sem_fields, invalidated_keys, sem_fields_invalid = _sanitize_semantic_field_map(
            safe_payload.get("semantic_fields")
        )
        safe_provenance, provenance_invalid = _sanitize_provenance_map(
            safe_payload.get("semantic_field_provenance"),
            invalidated_keys,
        )
        if "semantic_field_provenance" in safe_payload or safe_provenance:
            safe_payload["semantic_field_provenance"] = safe_provenance
        safe_payload["semantic_fields"] = safe_sem_fields

        for list_field in (
            "source_missing_semantic_fields",
            "source_explicit_missing_semantic_fields",
            "missing_semantic_fields",
            "source_files_changed",
            "source_blockers",
        ):
            if list_field in safe_payload:
                safe_payload[list_field] = _sanitize_string_list(safe_payload.get(list_field))

        if invalidated_keys:
            src_missing = set(safe_payload.get("source_missing_semantic_fields") or [])
            src_explicit_missing = set(safe_payload.get("source_explicit_missing_semantic_fields") or [])
            for key in invalidated_keys:
                if FIELD_NAME_RE.fullmatch(key) and not is_sensitive_key(key):
                    src_missing.add(key)
                    src_explicit_missing.add(key)
            safe_payload["source_missing_semantic_fields"] = sorted(src_missing)
            safe_payload["source_explicit_missing_semantic_fields"] = sorted(src_explicit_missing)

        for str_field in (
            "source_result_path",
            "source_result_branch",
            "source_result_commit",
            "source_result_blob_sha",
            "source_result_loader",
            "source_status",
            "source_quality_gate",
            "source_certification",
            "source_work_completion",
        ):
            if str_field in safe_payload and isinstance(safe_payload[str_field], str):
                safe_payload[str_field] = redact_sensitive_text(safe_payload[str_field], max_length=512)

        decision_provenance_explicit = all(
            safe_sem_fields.get(key) is not None
            and safe_provenance.get(key, {}).get("status") == "EXPLICIT_SOURCE_KEY"
            for key in DECISION_FIELDS
        )
        had_invalid = sem_fields_invalid or provenance_invalid or not check_passed
        source_complete = bool(
            not had_invalid
            and safe_payload.get("source_semantic_fields_complete") is True
            and decision_provenance_explicit
            and not (safe_payload.get("source_missing_semantic_fields") or [])
        )
        sem_complete = bool(
            not had_invalid
            and safe_payload.get("semantic_fields_complete") is True
            and not (safe_payload.get("missing_semantic_fields") or [])
        )
        gate3_ok = bool(
            source_complete
            and sem_complete
            and safe_payload.get("gate3_allowed") is True
            and safe_sem_fields.get("gate3_allowed") is True
        )

        safe_payload["source_semantic_fields_complete"] = source_complete
        if had_invalid:
            safe_payload["semantic_fields_complete"] = False
        safe_payload["gate3_allowed"] = gate3_ok
        if isinstance(safe_payload.get("semantic_fields"), dict):
            safe_payload["semantic_fields"]["gate3_allowed"] = gate3_ok
            if not source_complete:
                safe_payload["bridge_verdict"] = "SOURCE_SEMANTIC_FIELDS_DERIVED_FAIL_CLOSED"
                safe_payload["next_allowed_step"] = "GATE3_HOLD_PENDING_EXPLICIT_SEMANTIC_FIELDS"
                safe_payload["semantic_fields"].setdefault(
                    "next_allowed_gate", "GATE3_HOLD_PENDING_EXPLICIT_SEMANTIC_FIELDS"
                )
            elif not gate3_ok:
                safe_payload["bridge_verdict"] = "SOURCE_SEMANTIC_FIELDS_COMPLETE_GATE3_HOLD"
                safe_payload["next_allowed_step"] = "GATE3_HOLD_SEMANTIC_FIELDS_COMPLETE_NOT_ALLOWED"

        checks.append({
            "status": check.get("status"),
            "returncode": check.get("returncode"),
            "payload": safe_payload,
        })
        for key, value in safe_payload.items():
            promoted.setdefault(key, value)

    if not checks:
        return None

    all_source_complete = (
        not any_check_failed
        and all(c["payload"].get("source_semantic_fields_complete") is True for c in checks)
    )
    all_semantic_complete = (
        not any_check_failed
        and all(c["payload"].get("semantic_fields_complete") is True for c in checks)
    )
    all_gate3_allowed = (
        all_source_complete
        and all_semantic_complete
        and all(c["payload"].get("gate3_allowed") is True for c in checks)
    )

    promoted["source_semantic_fields_complete"] = all_source_complete
    promoted["semantic_fields_complete"] = all_semantic_complete
    promoted["gate3_allowed"] = all_gate3_allowed

    for union_field in (
        "source_missing_semantic_fields",
        "source_explicit_missing_semantic_fields",
        "missing_semantic_fields",
    ):
        merged: set[str] = set()
        for c in checks:
            merged.update(c["payload"].get(union_field) or [])
        if union_field in promoted or merged:
            promoted[union_field] = sorted(merged)

    if len(checks) > 1 or any_check_failed or not all_gate3_allowed:
        merged_sem_fields = dict(promoted.get("semantic_fields") or {})
        merged_sem_fields["gate3_allowed"] = all_gate3_allowed
        if any(
            (c["payload"].get("semantic_fields") or {}).get("last_gate_certified") is False
            for c in checks
        ):
            merged_sem_fields["last_gate_certified"] = False
        for c in checks:
            c_sem = c["payload"].get("semantic_fields") or {}
            if c_sem.get("blocking_reason_if_any"):
                merged_sem_fields["blocking_reason_if_any"] = c_sem["blocking_reason_if_any"]
                break
        if not all_source_complete:
            promoted["bridge_verdict"] = "SOURCE_SEMANTIC_FIELDS_DERIVED_FAIL_CLOSED"
            promoted["next_allowed_step"] = "GATE3_HOLD_PENDING_EXPLICIT_SEMANTIC_FIELDS"
            merged_sem_fields["next_allowed_gate"] = "GATE3_HOLD_PENDING_EXPLICIT_SEMANTIC_FIELDS"
        elif not all_gate3_allowed:
            promoted["bridge_verdict"] = "SOURCE_SEMANTIC_FIELDS_COMPLETE_GATE3_HOLD"
            promoted["next_allowed_step"] = "GATE3_HOLD_SEMANTIC_FIELDS_COMPLETE_NOT_ALLOWED"
            for c in checks:
                c_next = (c["payload"].get("semantic_fields") or {}).get("next_allowed_gate")
                if isinstance(c_next, str) and c_next != "GATE3_PREP_ALLOWED":
                    merged_sem_fields["next_allowed_gate"] = c_next
                    break
            else:
                merged_sem_fields["next_allowed_gate"] = "GATE3_HOLD_SEMANTIC_FIELDS_COMPLETE_NOT_ALLOWED"
        promoted["semantic_fields"] = merged_sem_fields

    return {"checks": checks, **promoted}



def sanitize_result_detail_evidence(
    result: dict[str, Any],
) -> dict[str, Any] | None:
    """Publish only bounded, already-sanitized Worker failure evidence."""

    safe_checks: list[dict[str, Any]] = []

    for check in result.get("checks") or []:
        if (
            not isinstance(check, dict)
            or check.get("type")
            != "worker_result_detail_read"
        ):
            continue

        payload = check.get(
            "result_detail_evidence"
        )

        if not isinstance(
            payload,
            dict,
        ):
            raw = check.get("output")

            if isinstance(raw, str):
                try:
                    candidate = json.loads(
                        raw.strip()
                    )
                except (
                    json.JSONDecodeError,
                    TypeError,
                ):
                    candidate = None

                if isinstance(
                    candidate,
                    dict,
                ):
                    payload = candidate

        if (
            not isinstance(payload, dict)
            or payload.get("status")
            != "PASS"
        ):
            continue

        failed_checks = []

        for item in (
            payload.get(
                "failed_checks"
            )
            or []
        )[:20]:

            if not isinstance(
                item,
                dict,
            ):
                continue

            safe_output = (
                redact_sensitive_text(
                    str(
                        item.get(
                            "output"
                        )
                        or ""
                    ),
                    max_length=8000,
                )
            )

            assertions = []

            for line in (
                item.get(
                    "assertion_lines"
                )
                or []
            )[:50]:

                if not isinstance(
                    line,
                    str,
                ):
                    continue

                assertions.append(
                    redact_sensitive_text(
                        line,
                        max_length=500,
                    )
                )

            returncode = (
                item.get(
                    "returncode"
                )
            )

            if (
                isinstance(
                    returncode,
                    bool,
                )
                or not isinstance(
                    returncode,
                    int,
                )
            ):
                returncode = None

            failed_checks.append(
                {
                    "type":
                        redact_sensitive_text(
                            str(
                                item.get(
                                    "type"
                                )
                                or ""
                            ),
                            max_length=128,
                        ),
                    "status": (
                        "FAIL"
                        if str(
                            item.get(
                                "status"
                            )
                            or ""
                        ).upper()
                        == "FAIL"
                        else None
                    ),
                    "returncode":
                        returncode,
                    "output":
                        safe_output,
                    "assertion_lines":
                        assertions,
                }
            )

        safe_checks.append(
            {
                "source_job_id":
                    redact_sensitive_text(
                        str(
                            payload.get(
                                "source_job_id"
                            )
                            or ""
                        ),
                        max_length=121,
                    ),
                "result_status":
                    redact_sensitive_text(
                        str(
                            payload.get(
                                "result_status"
                            )
                            or ""
                        ),
                        max_length=128,
                    ),
                "quality_gate":
                    payload.get(
                        "quality_gate"
                    ),
                "tests":
                    payload.get(
                        "tests"
                    ),
                "certification":
                    payload.get(
                        "certification"
                    ),
                "percent_complete":
                    payload.get(
                        "percent_complete"
                    ),
                "blockers":
                    _sanitize_string_list(
                        payload.get(
                            "blockers"
                        ),
                        max_item_len=500,
                    ),
                "files_changed":
                    _sanitize_string_list(
                        payload.get(
                            "files_changed"
                        ),
                        max_item_len=512,
                    ),
                "failed_checks":
                    failed_checks,
                "production_touched":
                    payload.get(
                        "production_touched"
                    )
                    is True,
            }
        )

    if not safe_checks:
        return None

    return {
        "checks": safe_checks,
    }


def sanitize_frontend_build_evidence(result: dict[str, Any]) -> dict[str, Any] | None:
    """Expose only the tail needed to diagnose frontend build failures.

    Never publishes environment variables or raw executor metadata.
    Potentially sensitive lines are replaced before publication.
    """
    evidence = []
    sensitive_tokens = ("secret", "token", "password", "authorization", "cookie", "apikey", "api_key")
    for check in result.get("checks") or []:
        if not isinstance(check, dict) or check.get("type") != "frontend_build":
            continue
        raw = str(check.get("output") or "")
        safe_lines = []
        for line in raw.splitlines():
            lowered = line.lower()
            if any(token in lowered for token in sensitive_tokens):
                safe_lines.append("[REDACTED_SENSITIVE_LINE]")
            else:
                safe_lines.append(line)
        tail = "\n".join(safe_lines)[-4000:]
        evidence.append({
            "status": check.get("status"),
            "returncode": check.get("returncode"),
            "started_at_utc": check.get("started_at_utc"),
            "completed_at_utc": check.get("completed_at_utc"),
            "output_tail": tail,
        })
    return {"checks": evidence} if evidence else None


GENERIC_READ_ONLY_CHECKS = frozenset({"py_compile", "pytest", "git_diff_check"})


def generic_readonly_evidence(result: dict[str, Any]) -> dict[str, Any] | None:
    checks = result.get("checks") or []
    if not isinstance(checks, list) or not checks:
        return None
    sanitized = []
    for check in checks:
        if not isinstance(check, dict):
            return None
        kind = str(check.get("type") or "")
        if kind not in GENERIC_READ_ONLY_CHECKS:
            return None
        if str(check.get("status") or "").upper() != "PASS":
            return None
        sanitized.append({"type": kind, "status": "PASS"})
    return {"checks": sanitized}


def branches_preserve_job_artifacts(
    source_sha: str,
    development_head: str,
    mirror_head: str,
    files_changed: list[str],
) -> bool:
    """Certify the job artifacts, not global branch SHA identity.

    Both DEV and MIRROR must descend from the job source SHA and must preserve
    every file changed by that job byte-for-byte relative to source_sha.
    Unrelated later commits or platform-managed mirror metadata do not block
    certification of this job; any mutation of a job-owned artifact fails
    closed.
    """
    if not files_changed:
        return False

    for head in (development_head, mirror_head):
        ancestry = git(
            "merge-base",
            "--is-ancestor",
            source_sha,
            head,
            check=False,
        )
        if ancestry.returncode != 0:
            return False

        artifact_check = git(
            "diff",
            "--quiet",
            source_sha,
            head,
            "--",
            *files_changed,
            check=False,
        )
        if artifact_check.returncode != 0:
            return False

    return True


def certification_evidence(result: dict[str, Any]) -> dict[str, Any]:
    source_sha = result.get("development_sha")

    pending = {
        "certified": False,
        "certification": "PENDING_AUDIT_EVIDENCE",
        "work_completion": "PENDING_CERTIFICATION",
        "percent_complete": 95,
    }

    if result.get("status") == "INVALID_RESULT_ARTIFACT":
        return {
            "certified": False,
            "certification": "NOT_CERTIFIED",
            "work_completion": "INVALID_RESULT_ARTIFACT",
            "percent_complete": 0,
            "certification_basis": "INVALID_RESULT_ARTIFACT_FAIL_CLOSED",
        }

    if result.get("status") == "READ_ONLY_COMPLETE":
        readonly_evidence = sanitize_readonly_evidence(result)
        repository_evidence = sanitize_repository_evidence(result)
        semantic_evidence = sanitize_semantic_evidence(result)
        result_detail_evidence = sanitize_result_detail_evidence(result)
        generic_evidence = generic_readonly_evidence(result)
        base_pass = (
            str(result.get("tests", "")).upper() == "PASS"
            and str(result.get("quality_gate", "")).upper() == "PASS"
            and result.get("production_touched") is False
            and not (result.get("blockers") or [])
        )

        required_deliverables = result.get(
            "required_deliverables"
        )

        if required_deliverables is not None:
            deliverable_evaluation = evaluate_deliverables(
                required_deliverables,
                result.get("deliverables"),
            )

            if (
                base_pass
                and not deliverable_evaluation.complete
            ):
                return {
                    "certified": False,
                    "certification": "PENDING_DELIVERABLES",
                    "work_completion": "PENDING_DELIVERABLES",
                    "percent_complete": min(
                        int(
                            result.get(
                                "percent_complete"
                            )
                            or 0
                        ),
                        95,
                    ),
                    "required_deliverables": list(
                        deliverable_evaluation.required
                    ),
                    "completed_deliverables": list(
                        deliverable_evaluation.completed
                    ),
                    "missing_deliverables": list(
                        deliverable_evaluation.missing
                    ),
                    "certification_basis":
                        "CHECKS_PASS_BUT_REQUIRED_DELIVERABLES_MISSING",
                }
        if base_pass and (
            readonly_evidence is not None
            or repository_evidence is not None
            or semantic_evidence is not None
            or result_detail_evidence is not None
        ):
            if readonly_evidence is not None:
                basis = "READ_ONLY_SQL_PASS_PLUS_SANITIZED_EVIDENCE"
            elif semantic_evidence is not None:
                basis = "READ_ONLY_SEMANTIC_EXTRACT_PASS_PLUS_SANITIZED_EVIDENCE"
            elif result_detail_evidence is not None:
                basis = "READ_ONLY_RESULT_DETAIL_PASS_PLUS_SANITIZED_EVIDENCE"
            else:
                basis = "READ_ONLY_REPOSITORY_PASS_PLUS_SANITIZED_EVIDENCE"
            return {
                "certified": True,
                "certification": "CERTIFIED_READ_ONLY",
                "work_completion": "COMPLETE",
                "percent_complete": 100,
                "certification_basis": basis,
            }
        if base_pass and generic_evidence is not None and (result.get("files_changed") or []) == []:
            return {
                "certified": True,
                "certification": "CERTIFIED_READ_ONLY",
                "work_completion": "COMPLETE",
                "percent_complete": 100,
                "certification_basis": "GENERIC_READ_ONLY_NON_MUTATING_CHECKS_PASS",
            }
        return {
            **pending,
            "certification": "NOT_CERTIFIED",
            "work_completion": "NOT_CERTIFIED",
            "percent_complete": min(int(result.get("percent_complete") or 0), 95),
        }

    if result.get("status") == "OPERATIONAL_COMPLETE":
        operational_certified = (
            str(result.get("certification") or "").upper() == "CERTIFIED_OPERATIONAL"
            and str(result.get("tests", "")).upper() == "PASS"
            and str(result.get("quality_gate", "")).upper() == "PASS"
            and not (result.get("blockers") or [])
            and result.get("production_touched") is False
        )
        if operational_certified:
            return {
                "certified": True,
                "certification": "CERTIFIED_OPERATIONAL",
                "work_completion": "COMPLETE",
                "percent_complete": 100,
                "certification_basis": "DISPATCHER_OPERATIONAL_CERTIFICATION_PLUS_VALIDATIONS",
            }
        return {
            **pending,
            "certification": "NOT_CERTIFIED",
            "work_completion": "NOT_CERTIFIED",
            "percent_complete": min(int(result.get("percent_complete") or 0), 95),
        }

    if result.get("status") == "FRONTEND_BUILD_CERTIFIED":
        frontend_certified = (
            str(result.get("certification") or "").upper() == "CERTIFIED_FRONTEND_BUILD"
            and str(result.get("tests", "")).upper() == "PASS"
            and str(result.get("quality_gate", "")).upper() == "PASS"
            and not (result.get("blockers") or [])
            and result.get("production_touched") is False
            and (result.get("files_changed") or []) == []
        )
        if frontend_certified:
            return {
                "certified": True,
                "certification": "CERTIFIED_FRONTEND_BUILD",
                "work_completion": "COMPLETE",
                "percent_complete": 100,
                "certification_basis": "FRONTEND_BUILD_CERTIFICATION_PASS_PLUS_NON_MUTATING_RESULT",
            }
        return {
            **pending,
            "certification": "NOT_CERTIFIED",
            "work_completion": "NOT_CERTIFIED",
            "percent_complete": min(
                int(result.get("percent_complete") or 0),
                95,
            ),
        }

    if result.get("status") != "INTEGRATED":
        return {
            **pending,
            "certification": "NOT_CERTIFIED",
            "work_completion": "NOT_CERTIFIED",
            "percent_complete": min(
                int(result.get("percent_complete") or 0),
                95,
            ),
        }

    if str(result.get("tests", "")).upper() != "PASS":
        return pending

    if str(result.get("quality_gate", "")).upper() != "PASS":
        return pending

    if result.get("production_touched") is not False:
        return pending

    if not valid_sha(source_sha):
        return pending

    attestation_path = (
        ATTESTATIONS / f"{source_sha}.json"
    )
    if not attestation_path.is_file():
        return pending

    try:
        attestation = load(attestation_path)
    except Exception:
        return pending

    if attestation.get("source_sha") != source_sha:
        return pending
    if attestation.get("job_id") != result.get("job_id"):
        return pending
    if str(attestation.get("tests", "")).upper() != "PASS":
        return pending
    if str(attestation.get("quality_gate", "")).upper() != "PASS":
        return pending
    if attestation.get("production_touched") is not False:
        return pending

    # Certification is allowed against a later converged descendant.
    # This is necessary when infrastructure fixes are integrated after
    # a job but the job's own files remain unchanged.
    runtime_git("fetch", REMOTE, DEV_BRANCH)
    runtime_git("fetch", REMOTE, MIRROR_BRANCH)

    development_head = git(
        "rev-parse",
        f"{REMOTE}/{DEV_BRANCH}",
    ).stdout.strip()

    mirror_head = git(
        "rev-parse",
        f"{REMOTE}/{MIRROR_BRANCH}",
    ).stdout.strip()

    files_changed = [
        str(value)
        for value in (result.get("files_changed") or [])
        if isinstance(value, str) and value
    ]

    if not branches_preserve_job_artifacts(
        source_sha,
        development_head,
        mirror_head,
        files_changed,
    ):
        return pending

    return {
        "certified": True,
        "certification": "CERTIFIED",
        "work_completion": "COMPLETE",
        "percent_complete": 100,
        "certified_source_sha": source_sha,
        "converged_head": development_head,
        "certification_basis":
            "SHA_BOUND_ATTESTATION_PLUS_ARTIFACT_CONVERGENCE",
    }


def sanitize(result: dict[str, Any]) -> dict[str, Any]:
    allowed = (
        "schema", "job_id", "started_at_utc", "completed_at_utc", "status",
        "executor", "base_sha", "execution_base_sha", "requested_base_sha",
        "candidate_sha", "development_sha", "tests",
        "quality_gate", "files_changed", "summary_es", "blockers",
        "percent_complete", "certification", "production_touched",
        "operation", "dry_run", "units", "canonical_sql_mutation",
        "operation_summary", "reasons", "received_at_utc", "source",
        "required_deliverables", "deliverables", "missing_deliverables",
        "invalid_result_artifact", "source_result_path",
        "result_integrity_state", "result_integrity_reason",
        "result_size_bytes", "result_sha256",
    )
    public = {key: result.get(key) for key in allowed if key in result}
    raw_base = result.get("base_sha")
    raw_exec = result.get("execution_base_sha")
    concurrency = result.get("concurrency")
    concurrency_bad = concurrency is not None and not isinstance(concurrency, dict)
    pickup = concurrency.get("pickup") if isinstance(concurrency, dict) else None
    pickup_bad = pickup is not None and not isinstance(pickup, dict)
    raw_pickup_exec = pickup.get("execution_base_sha") if isinstance(pickup, dict) else None

    sha_triplet = [val for val in (raw_base, raw_exec, raw_pickup_exec) if val is not None]
    sha_triplet_valid = (
        not concurrency_bad
        and not pickup_bad
        and all(isinstance(val, str) and authentic_lineage_sha(val.strip()) for val in sha_triplet)
        and len({val.strip() for val in sha_triplet if isinstance(val, str)}) <= 1
    )
    if not sha_triplet_valid:
        public.pop("base_sha", None)
        public.pop("execution_base_sha", None)
    else:
        if "base_sha" in public:
            if raw_base is None:
                public.pop("base_sha", None)
            else:
                public["base_sha"] = raw_base.strip()
        if "execution_base_sha" in public:
            if raw_exec is None:
                public.pop("execution_base_sha", None)
            else:
                public["execution_base_sha"] = raw_exec.strip()

    if "requested_base_sha" in public:
        req_sha = public.get("requested_base_sha")
        if not isinstance(req_sha, str) or not authentic_lineage_sha(req_sha.strip()):
            public.pop("requested_base_sha", None)
        else:
            public["requested_base_sha"] = req_sha.strip()

    if "summary_es" in public:
        raw_summary = public.get("summary_es")
        if raw_summary is None:
            public.pop("summary_es", None)
        else:
            try:
                clean_summary = sanitize_dynamic_value(raw_summary, max_str_len=MAX_SUMMARY_LENGTH)
                if not isinstance(clean_summary, str):
                    raise ValueError("INVALID_SUMMARY_ES")
                public["summary_es"] = clean_summary
            except (ValueError, TypeError):
                public.pop("summary_es", None)
    public["published_at_utc"] = now()
    public["source_repo"] = "rbalam/EDARSA_HUB"
    public["source_branch"] = "Edarsahub_Desarrollo"
    public["human_summary_language"] = "es"
    public["human_summary_level"] = "13yo-non-programmer"
    readonly_evidence = sanitize_readonly_evidence(result)
    if readonly_evidence is not None:
        public["sql_readonly_evidence"] = readonly_evidence
    repository_evidence = sanitize_repository_evidence(result)
    if repository_evidence is not None:
        public["repository_contract_evidence"] = repository_evidence
    semantic_evidence = sanitize_semantic_evidence(result)
    if semantic_evidence is not None:
        public["worker_result_semantic_evidence"] = semantic_evidence
        for key in (
            "bridge_verdict",
            "runtime_gap_confirmed",
            "source_result_reader_capability_current_state",
            "can_read_worker_results_by_branch_path",
            "can_read_worker_results_by_blob_sha",
            "can_emit_semantic_fields_from_source_result",
            "source_semantic_fields_complete",
            "source_missing_semantic_fields",
            "source_explicit_missing_semantic_fields",
            "semantic_field_provenance",
            "semantic_fields_complete",
            "missing_semantic_fields",
            "semantic_fields",
            "gate3_allowed",
            "source_result_read_status",
            "source_result_path",
            "source_result_branch",
            "source_result_commit",
            "source_result_blob_sha",
            "source_result_size_bytes",
            "source_result_sha256",
            "source_result_loader",
            "source_status",
            "source_quality_gate",
            "source_certification",
            "source_work_completion",
            "source_percent_complete",
            "source_production_touched",
            "source_files_changed",
            "source_blockers",
            "required_runtime_change",
            "next_allowed_step",
        ):
            if key in semantic_evidence:
                public[key] = semantic_evidence[key]
    frontend_build_evidence = sanitize_frontend_build_evidence(result)
    if frontend_build_evidence is not None:
        public["frontend_build_evidence"] = frontend_build_evidence

    result_detail_evidence = sanitize_result_detail_evidence(result)
    if result_detail_evidence is not None:
        public["result_detail_evidence"] = result_detail_evidence

    evidence = certification_evidence(result)

    public["certification"] = evidence["certification"]
    public["work_completion"] = evidence["work_completion"]
    public["percent_complete"] = evidence["percent_complete"]

    for key in (
        "certified_source_sha",
        "converged_head",
        "certification_basis",
        "required_deliverables",
        "completed_deliverables",
        "missing_deliverables",
    ):
        if key in evidence:
            public[key] = evidence[key]

    return public


def create_attestation(public: dict[str, Any]) -> Path | None:
    sha = public.get("development_sha")
    if public.get("status") != "INTEGRATED" or not isinstance(sha, str) or len(sha) != 40:
        return None
    if str(public.get("tests", "")).upper() != "PASS" or str(public.get("quality_gate", "")).upper() != "PASS":
        return None
    payload = {
        "schema": "edarsahub.test-attestation.v1",
        "job_id": public.get("job_id"),
        "source_sha": sha,
        "tests": "PASS",
        "quality_gate": "PASS",
        "production_touched": public.get("production_touched") is True,
        "summary_es": public.get("summary_es"),
        "files_changed": public.get("files_changed") or [],
        "generated_at_utc": now(),
    }
    path = ATTESTATIONS / f"{sha}.json"
    atomic_json(path, payload)
    return path


def prepare_queue_worktree() -> tuple[Path, str]:
    """Create an isolated temporary checkout without registering a Git worktree.

    worker/requests is an infrastructure queue, not an agent development
    branch. Agent Guard reserves registered worktrees for agent/* branches.
    A temporary clone keeps publication isolated while preserving the
    canonical Agent Guard contract.
    """
    runtime_git("fetch", REMOTE, RESULT_BRANCH)
    base = git("rev-parse", f"{REMOTE}/{RESULT_BRANCH}").stdout.strip()

    WORKTREE_PARENT.mkdir(parents=True, exist_ok=True)

    worktree_root = Path(
        tempfile.mkdtemp(
            prefix="edarsahub-worker-result-publish-",
            dir=str(WORKTREE_PARENT),
        )
    )

    # git clone requiere que la ruta destino no exista.
    shutil.rmtree(worktree_root)

    origin_url = git("remote", "get-url", REMOTE).stdout.strip()

    clone = run(
        runtime_git_command(
            "clone",
            "--quiet",
            "--no-checkout",
            origin_url,
            str(worktree_root),
        ),
        cwd=ROOT,
    )

    if clone.returncode != 0 or not worktree_root.is_dir():
        shutil.rmtree(worktree_root, ignore_errors=True)
        raise RuntimeError(
            "RESULT_WORKTREE_NOT_CREATED:"
            + clone.stdout[-1500:]
        )

    git("checkout", "--detach", base, cwd=worktree_root)

    return worktree_root, base



def resolve_runtime_git_credential_helper() -> str:
    configured = subprocess.run(
        [
            "git",
            "config",
            "--local",
            "--get",
            "credential.helper",
        ],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    ).stdout.strip()

    if configured and not configured.startswith("cache "):
        return configured

    credential_file = Path("/root/.git-credentials")
    if credential_file.is_file():
        return f"store --file={credential_file}"

    return configured


def runtime_git_command(*args: str) -> list[str]:
    helper = resolve_runtime_git_credential_helper()

    cmd = [
        "git",
        "-c",
        "credential.helper=",
    ]

    if helper:
        cmd.extend(
            [
                "-c",
                f"credential.helper={helper}",
                "-c",
                "credential.useHttpPath=true",
            ]
        )

    cmd.extend(args)
    return cmd


def runtime_git(
    *args: str,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        runtime_git_command(*args),
        cwd=str(cwd or ROOT),
        env=runtime_git_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"RUNTIME_GIT_FAILED:{' '.join(args)}:{proc.stdout[-800:]}"
        )
    return proc


def runtime_git_env() -> dict[str, str]:
    env = dict(os.environ)
    env.setdefault("HOME", "/root")
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def marker_satisfied(marker: Path, public: dict[str, Any]) -> bool:
    if not marker.exists():
        return False

    marker_text = marker.read_text(
        encoding="utf-8",
        errors="replace",
    )

    desired = public.get("certification")

    # A stale NOT_CERTIFIED marker must not suppress a newer local result.
    # PENDING_AUDIT_EVIDENCE is a real promotion step because publishing it
    # creates the SHA-bound attestation required for the final certification.
    promotable = {
        "PENDING_AUDIT_EVIDENCE",
        "CERTIFIED",
        "CERTIFIED_OPERATIONAL",
        "CERTIFIED_READ_ONLY",
    }
    if desired in promotable:
        return f"certification={desired}" in marker_text

    return True



def result_identity(path: Path, payload: dict[str, Any]) -> str:
    """Return the canonical remote identity for a result.

    The authoritative identity is the embedded job_id. The local filename
    is only a storage key and may differ for historical/concurrency artifacts.
    """
    value = str(payload.get("job_id") or "").strip()

    if value:
        if any(
            ch not in
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
            for ch in value
        ):
            raise ValueError("INVALID_JOB_ID")
        return value

    fallback = path.stem

    if not fallback or any(
        ch not in
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
        for ch in fallback
    ):
        raise ValueError("INVALID_JOB_ID")

    return fallback


def publish_one(path: Path) -> bool:
    PUBLISHED.mkdir(parents=True, exist_ok=True)
    marker = PUBLISHED / path.name

    result = load_publishable_result(path)
    public = sanitize(result)

    if marker_satisfied(marker, public):
        return False
    job_id = result_identity(path, public)

    last_error = None

    for attempt in range(1, QUEUE_PUBLISH_MAX_ATTEMPTS + 1):
        worktree = None

        try:
            worktree, base = prepare_queue_worktree()

            destination = (
                worktree
                / "worker_queue"
                / "results"
                / f"{job_id}.json"
            )

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            destination.write_text(
                json.dumps(
                    public,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            git(
                "add",
                "--",
                str(destination.relative_to(worktree)),
                cwd=worktree,
            )

            staged = git(
                "diff",
                "--cached",
                "--quiet",
                cwd=worktree,
                check=False,
            )

            if staged.returncode == 0:
                marker.write_text(
                    f"already_present={now()}\n"
                    f"certification={public.get('certification')}\n",
                    encoding="utf-8",
                )

                create_attestation(public)
                return False

            git(
                "-c",
                "user.name=EDARSAHUB Worker",
                "-c",
                "user.email=worker@edarsahub.local",
                "commit",
                "-m",
                f"worker-result({job_id}): publish execution result",
                cwd=worktree,
            )

            commit = git(
                "rev-parse",
                "HEAD",
                cwd=worktree,
            ).stdout.strip()

            runtime_git(
                "fetch",
                REMOTE,
                RESULT_BRANCH,
                cwd=worktree,
            )

            current = git(
                "rev-parse",
                f"{REMOTE}/{RESULT_BRANCH}",
                cwd=worktree,
            ).stdout.strip()

            if current != base:
                last_error = (
                    "QUEUE_BRANCH_MOVED:"
                    f"attempt={attempt}:"
                    f"base={base}:"
                    f"current={current}"
                )

                print(
                    "UNIVERSAL_RESULT_PUBLISH_RETRY="
                    f"{job_id}:"
                    f"attempt={attempt}:"
                    "reason=QUEUE_BRANCH_MOVED"
                )

                continue

            push_env = os.environ.copy()
            push_env["EDARSA_ALLOW_PUSH"] = "1"

            try:
                push_env.update(runtime_git_env())
                push_env["EDARSA_ALLOW_PUSH"] = "1"

                push = subprocess.run(
                    runtime_git_command(
                        "push",
                        REMOTE,
                        f"{commit}:refs/heads/{RESULT_BRANCH}",
                    ),
                    cwd=str(worktree),
                    env=push_env,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=GIT_TIMEOUT_SECONDS,
                )
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError(
                    "QUEUE_RESULT_PUSH_TIMEOUT:"
                    f"{job_id}:"
                    f"timeout={GIT_TIMEOUT_SECONDS}s"
                ) from exc

            if push.returncode != 0:
                output = push.stdout[-1500:]

                # Otro escritor pudo mover worker/results
                # entre el recheck y el push. Reintentar
                # desde el nuevo HEAD es seguro porque el
                # artefacto se reconstruye en un clone limpio.
                concurrent_markers = (
                    "fetch first",
                    "cannot lock ref",
                    "non-fast-forward",
                    "stale info",
                )

                if any(
                    marker_text in output
                    for marker_text in concurrent_markers
                ):
                    last_error = (
                        "QUEUE_RESULT_PUSH_CONCURRENT:"
                        f"attempt={attempt}:"
                        + output
                    )

                    print(
                        "UNIVERSAL_RESULT_PUBLISH_RETRY="
                        f"{job_id}:"
                        f"attempt={attempt}:"
                        "reason=CONCURRENT_QUEUE_PUSH"
                    )

                    continue

                raise RuntimeError(
                    "QUEUE_RESULT_PUSH_FAILED:"
                    + output
                )

            create_attestation(public)

            marker.write_text(
                f"published={now()}\n"
                f"commit={commit}\n"
                f"certification={public.get('certification')}\n",
                encoding="utf-8",
            )

            print(
                f"UNIVERSAL_RESULT_PUBLISHED={job_id}"
            )
            print(
                f"QUEUE_RESULT_COMMIT={commit}"
            )

            if public.get("development_sha"):
                print(
                    "RESULT_DEVELOPMENT_SHA="
                    f"{public['development_sha']}"
                )

            return True

        finally:
            if worktree is not None:
                shutil.rmtree(
                    worktree,
                    ignore_errors=True,
                )

    raise RuntimeError(
        "QUEUE_RESULT_PUBLISH_RETRIES_EXHAUSTED:"
        f"{job_id}:"
        f"{last_error or 'UNKNOWN'}"
    )

def publishable_paths() -> list[Path]:
    """Return terminal artifacts without starving certification promotions.

    A mutation result needs two publication passes: the first publishes
    PENDING_AUDIT_EVIDENCE and creates the SHA-bound attestation; a later pass
    can promote it to CERTIFIED once DEV/MIRROR preserve the job artifacts.
    Prioritize those pending markers so sustained arrival of newer results
    cannot keep an older successful job at 95% indefinitely. Fresh results
    keep their existing newest-first order.
    """
    by_name = {path.name: path for path in REJECTED.glob("*.json")}
    by_name.update({path.name: path for path in RESULTS.glob("*.json")})

    def priority(path: Path) -> tuple[int, int, str]:
        marker = PUBLISHED / path.name
        pending_audit = False
        if marker.is_file():
            marker_text = marker.read_text(
                encoding="utf-8",
                errors="replace",
            )
            pending_audit = (
                "certification=PENDING_AUDIT_EVIDENCE"
                in marker_text
            )

        mtime = path.stat().st_mtime_ns
        if pending_audit:
            return (0, mtime, path.name)
        return (1, -mtime, path.name)

    return sorted(by_name.values(), key=priority)


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    REJECTED.mkdir(parents=True, exist_ok=True)
    PUBLISH_LOCK.parent.mkdir(parents=True, exist_ok=True)

    with PUBLISH_LOCK.open("a+", encoding="utf-8") as lock_handle:
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("UNIVERSAL_RESULT_PUBLISHER_SINGLE_WRITER=BUSY")
            return 0

        count = 0
        errors = 0
        attempted = 0

        if RESULT_BATCH_SIZE < 1:
            raise RuntimeError(
                "INVALID_RESULT_BATCH_SIZE:"
                f"{RESULT_BATCH_SIZE}"
            )

        for path in publishable_paths():
            marker = PUBLISHED / path.name

            # Un resultado ya certificado es terminal.
            # Saltarlo antes de load()/sanitize() evita revalidar
            # historicos y, sobre todo, evita fetches Git remotos
            # innecesarios en certification_evidence().
            if marker.exists():
                marker_text = marker.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
                if "certification=CERTIFIED" in marker_text:
                    continue

            try:
                public = sanitize(load(path))
            except Exception:
                # Los errores de parsing deben seguir entrando por
                # publish_one para producir evidencia/error normal.
                public = None

            if (
                public is not None
                and marker_satisfied(marker, public)
            ):
                continue

            if attempted >= RESULT_BATCH_SIZE:
                break

            attempted += 1

            try:
                if publish_one(path):
                    count += 1
            except Exception as exc:
                errors += 1
                print(
                    f"UNIVERSAL_RESULT_PUBLISH_ERROR="
                    f"{path.name}:"
                    f"{type(exc).__name__}:"
                    f"{exc}"
                )

        print(
            "UNIVERSAL_RESULTS_ATTEMPTED_COUNT="
            f"{attempted}"
        )
        print(
            "UNIVERSAL_RESULTS_PUBLISHED_COUNT="
            f"{count}"
        )
        print(
            "UNIVERSAL_RESULTS_PUBLISH_ERROR_COUNT="
            f"{errors}"
        )
        print(
            "UNIVERSAL_RESULTS_BATCH_SIZE="
            f"{RESULT_BATCH_SIZE}"
        )

        return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
