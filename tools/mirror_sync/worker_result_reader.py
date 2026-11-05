"""Canonical Universal Worker result reader.

One terminal truth:
worker_queue/results/<job_id>.json

This helper classifies result state through the canonical integrity layer
and reconciles provisional local mutation results against the canonical
published marker, SHA-bound test attestation, and worker/results blob
without introducing a second synchronizer. It fails closed on absent,
tampered, or contradictory artifacts.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.mirror_sync.worker_result_integrity import (
    ResultIdentity,
    ResultState,
    inspect_result_file,
    validate_terminal_result_file,
    validate_terminal_result_payload,
)


_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")

_CERTIFIED_STATES = frozenset(
    {
        "CERTIFIED",
        "CERTIFIED_READ_ONLY",
        "CERTIFIED_OPERATIONAL",
        "CERTIFIED_FRONTEND_BUILD",
    }
)

_NON_SUCCESS_TERMINAL_STATUSES = frozenset(
    {
        "BLOCKED",
        "FAILED",
        "REJECTED",
        "INVALID_RESULT_ARTIFACT",
        "CONTRADICTORY_RESULT_ARTIFACT",
        "GIT_TESTS_FAILED",
        "GIT_SCOPE_VIOLATION",
        "GIT_DIVERGENCE_BLOCKED",
        "GIT_PUSH_FAILED",
        "GIT_LOCK_BUSY",
        "CONCURRENT_SCOPE_CONFLICT",
        "FRONTEND_BUILD_FAILED",
    }
)


@dataclass(frozen=True)
class CanonicalResultRead:
    job_id: str
    state: str
    result_path: str
    result_size_bytes: int
    result_sha256: str | None
    terminal_result_valid: bool
    payload: dict[str, Any] | None
    source: str = "worker_queue/results"


def _is_valid_sha(value: Any) -> bool:
    return bool(
        isinstance(value, str)
        and _SHA_RE.fullmatch(value.strip())
    )


def _is_valid_sha256(value: Any) -> bool:
    return bool(
        isinstance(value, str)
        and _SHA256_RE.fullmatch(value.strip())
    )


def _fail_closed_read(
    *,
    job_id: str,
    path: Path,
    identity: ResultIdentity,
    base_payload: dict[str, Any],
    state: ResultState,
    reason: str,
    reconciliation_status: str,
) -> CanonicalResultRead:
    existing_blockers = [
        str(item)
        for item in (base_payload.get("blockers") or [])
        if str(item).strip()
    ]
    if reason not in existing_blockers:
        existing_blockers.append(reason)

    failed_payload = dict(base_payload)
    failed_payload.update(
        {
            "status": (
                "INVALID_RESULT_ARTIFACT"
                if base_payload.get("invalid_result_artifact") is True
                else "CONTRADICTORY_RESULT_ARTIFACT"
            ),
            "quality_gate": "FAIL",
            "tests": "FAIL",
            "certification": "NOT_CERTIFIED",
            "work_completion": "NOT_CERTIFIED",
            "percent_complete": 0,
            "blockers": existing_blockers,
            "production_touched": bool(
                base_payload.get("production_touched", False)
            ),
            "reconciliation_status": reconciliation_status,
            "result_integrity_state": state.value,
            "result_integrity_reason": reason,
        }
    )
    return CanonicalResultRead(
        job_id=job_id,
        state=state.value,
        result_path=str(path),
        result_size_bytes=identity.size_bytes,
        result_sha256=identity.sha256,
        terminal_result_valid=False,
        payload=failed_payload,
    )


def parse_published_marker(marker_path: Path) -> dict[str, Any] | None:
    if not marker_path.is_file():
        return None

    try:
        raw_text = marker_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {"_invalid": "PUBLISHED_MARKER_UNREADABLE"}

    stripped = raw_text.strip()
    if not stripped:
        return {"_invalid": "PUBLISHED_MARKER_EMPTY"}

    if stripped.startswith("{"):
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return {"_invalid": "PUBLISHED_MARKER_INVALID_JSON"}
        if not isinstance(parsed, dict):
            return {"_invalid": "PUBLISHED_MARKER_NOT_OBJECT"}
        result = dict(parsed)
        result["_format"] = "json"
        return result

    kv: dict[str, Any] = {}
    for line in stripped.splitlines():
        clean_line = line.strip()
        if not clean_line:
            continue
        if "=" not in clean_line:
            return {"_invalid": "PUBLISHED_MARKER_INVALID_LINE"}
        key, value = clean_line.split("=", 1)
        clean_key = key.strip()
        clean_val = value.strip()
        if not clean_key or not clean_val:
            return {"_invalid": "PUBLISHED_MARKER_EMPTY_KEY_OR_VALUE"}
        kv[clean_key] = clean_val

    if "certification" not in kv or (
        "published" not in kv and "already_present" not in kv
    ):
        return {"_invalid": "PUBLISHED_MARKER_MISSING_REQUIRED_KEYS"}

    kv["_format"] = "kv"
    return kv


def _resolve_attestations_dir(
    state_root: Path,
    explicit_dir: Path | None = None,
) -> Path | None:
    if explicit_dir is not None:
        return explicit_dir
    local_candidate = state_root / "test_attestations"
    if local_candidate.exists():
        return local_candidate
    git_candidate = (
        state_root.parent
        / "mirror-sync"
        / "reporting"
        / "test_attestations"
    )
    if git_candidate.exists():
        return git_candidate
    return git_candidate


def _verify_attestation_file(
    attestation_path: Path,
    *,
    expected_job_id: str,
    expected_source_sha: str,
    expected_files_changed: list[str],
) -> tuple[bool, str, str | None]:
    if not attestation_path.is_file():
        return False, "attestation_missing", None

    try:
        raw = attestation_path.read_bytes()
    except OSError:
        return False, "attestation_unreadable", None

    if not raw:
        return False, "attestation_empty", None

    att_sha256 = hashlib.sha256(raw).hexdigest()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False, "attestation_invalid_json", att_sha256

    if not isinstance(payload, dict):
        return False, "attestation_not_object", att_sha256

    if payload.get("schema") != "edarsahub.test-attestation.v1":
        return False, "attestation_schema_invalid", att_sha256

    if str(payload.get("job_id") or "").strip() != expected_job_id:
        return False, "attestation_job_id_mismatch", att_sha256

    if (
        str(payload.get("source_sha") or "").strip().lower()
        != expected_source_sha.lower()
    ):
        return False, "attestation_source_sha_mismatch", att_sha256

    if str(payload.get("tests") or "").strip().upper() != "PASS":
        return False, "attestation_tests_not_pass", att_sha256

    if str(payload.get("quality_gate") or "").strip().upper() != "PASS":
        return False, "attestation_quality_gate_not_pass", att_sha256

    if payload.get("production_touched") is not False:
        return False, "attestation_production_touched", att_sha256

    att_files = payload.get("files_changed")
    if not isinstance(att_files, list):
        return False, "attestation_files_changed_not_list", att_sha256

    if [str(x) for x in att_files] != expected_files_changed:
        return False, "attestation_files_changed_mismatch", att_sha256

    return True, "ATTESTATION_VERIFIED", att_sha256


def _read_published_result_bytes(
    *,
    state_root: Path,
    expected_job_id: str,
    marker_commit: str | None,
) -> tuple[bool, str, bytes | None]:
    published_file = (
        state_root / "published_results" / f"{expected_job_id}.json"
    )
    if published_file.is_file():
        try:
            return True, "PUBLISHED_RESULT_FILE", published_file.read_bytes()
        except OSError:
            return False, "published_result_file_unreadable", None

    if not marker_commit:
        return True, "PUBLISHED_RESULT_NOT_REQUIRED", None

    if not _is_valid_sha(marker_commit):
        return False, "published_marker_invalid_commit_sha", None

    git_dir = state_root.parent
    if not (git_dir / "HEAD").is_file():
        return True, "PUBLISHED_RESULT_NO_GIT_REPO", None

    blob_spec = f"{marker_commit}:worker_queue/results/{expected_job_id}.json"
    try:
        proc = subprocess.run(
            [
                "git",
                f"--git-dir={git_dir}",
                "cat-file",
                "-p",
                blob_spec,
            ],
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False, "published_result_git_read_failed", None

    if proc.returncode != 0:
        return False, "published_result_commit_blob_missing", None

    return True, "PUBLISHED_RESULT_GIT_BLOB", proc.stdout


def _verify_published_result_bytes(
    raw: bytes,
    *,
    expected_job_id: str,
    expected_source_sha: str,
    expected_files_changed: list[str],
    expected_certification: str,
) -> tuple[bool, str, dict[str, Any] | None, str | None]:
    if not raw:
        return False, "published_result_empty", None, None

    pub_sha256 = hashlib.sha256(raw).hexdigest()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False, "published_result_invalid_json", None, pub_sha256

    if not isinstance(payload, dict):
        return False, "published_result_not_object", None, pub_sha256

    try:
        validate_terminal_result_payload(
            payload,
            expected_job_id=expected_job_id,
        )
    except ValueError as exc:
        return (
            False,
            f"published_result_schema_invalid:{exc}",
            None,
            pub_sha256,
        )

    if str(payload.get("status") or "").strip().upper() != "INTEGRATED":
        return False, "published_result_status_mismatch", None, pub_sha256

    pub_cert = str(payload.get("certification") or "").strip().upper()
    if pub_cert != expected_certification.upper():
        return (
            False,
            f"published_result_certification_mismatch:{pub_cert}",
            None,
            pub_sha256,
        )

    if str(payload.get("quality_gate") or "").strip().upper() != "PASS":
        return False, "published_result_quality_gate_not_pass", None, pub_sha256

    if str(payload.get("tests") or "").strip().upper() != "PASS":
        return False, "published_result_tests_not_pass", None, pub_sha256

    if payload.get("production_touched") is not False:
        return False, "published_result_production_touched", None, pub_sha256

    if payload.get("blockers") not in ([], None):
        return False, "published_result_blockers_present", None, pub_sha256

    pub_dev_sha = str(payload.get("development_sha") or "").strip().lower()
    if pub_dev_sha != expected_source_sha.lower():
        return (
            False,
            "published_result_development_sha_mismatch",
            None,
            pub_sha256,
        )

    pub_files = payload.get("files_changed")
    if not isinstance(pub_files, list) or [
        str(x) for x in pub_files
    ] != expected_files_changed:
        return (
            False,
            "published_result_files_changed_mismatch",
            None,
            pub_sha256,
        )

    if expected_certification.upper() == "CERTIFIED":
        if str(payload.get("work_completion") or "").strip().upper() not in {
            "COMPLETE",
            "",
        }:
            return (
                False,
                "published_result_work_completion_mismatch",
                None,
                pub_sha256,
            )
        if int(payload.get("percent_complete") or 0) != 100:
            return (
                False,
                "published_result_percent_complete_mismatch",
                None,
                pub_sha256,
            )
        cert_source = payload.get("certified_source_sha")
        if cert_source is not None and (
            str(cert_source).strip().lower() != expected_source_sha.lower()
        ):
            return (
                False,
                "published_result_certified_source_sha_mismatch",
                None,
                pub_sha256,
            )

    return True, "PUBLISHED_RESULT_VERIFIED", payload, pub_sha256


def _validate_internal_invariants(
    payload: dict[str, Any],
) -> tuple[bool, str]:
    status_upper = str(payload.get("status") or "").strip().upper()
    cert_upper = str(payload.get("certification") or "").strip().upper()
    qg_upper = str(payload.get("quality_gate") or "").strip().upper()
    tests_raw = payload.get("tests")
    tests_upper = (
        str(tests_raw).strip().upper() if tests_raw is not None else "PASS"
    )
    work_upper = str(payload.get("work_completion") or "").strip().upper()
    blockers = payload.get("blockers") or []
    prod_touched = payload.get("production_touched")
    percent = int(payload.get("percent_complete") or 0)

    if status_upper in _NON_SUCCESS_TERMINAL_STATUSES:
        if (
            cert_upper in _CERTIFIED_STATES
            or cert_upper == "PENDING_AUDIT_EVIDENCE"
            or work_upper == "COMPLETE"
            or percent == 100
        ):
            return False, "contradictory_failed_status_claims_certified"
        return True, "OK"

    if (
        cert_upper in _CERTIFIED_STATES
        or cert_upper == "PENDING_AUDIT_EVIDENCE"
        or work_upper == "COMPLETE"
    ):
        if prod_touched is not False:
            return False, "contradictory_production_touched_on_certified"
        if qg_upper != "PASS":
            return False, "contradictory_quality_gate_not_pass"
        if tests_upper != "PASS":
            return False, "contradictory_tests_not_pass"
        if blockers:
            return False, "contradictory_blockers_present_on_certified"

    if cert_upper == "CERTIFIED":
        if status_upper != "INTEGRATED":
            return False, "contradictory_certified_requires_integrated_status"
        git_sync = payload.get("git_sync_status")
        if (
            git_sync is not None
            and str(git_sync).strip().upper() != "CERTIFIED_GIT_SYNC"
        ):
            return False, "contradictory_git_sync_not_certified"
        if "files_changed" in payload and not (payload.get("files_changed") or []):
            return False, "contradictory_mutation_certified_without_files"

    elif cert_upper == "PENDING_AUDIT_EVIDENCE":
        if status_upper != "INTEGRATED":
            return False, "contradictory_pending_audit_requires_integrated"
        if work_upper == "COMPLETE" or percent == 100:
            return False, "contradictory_provisional_claims_complete"

    elif cert_upper == "CERTIFIED_READ_ONLY":
        if status_upper != "READ_ONLY_COMPLETE":
            return False, "contradictory_readonly_certification_status"

    elif cert_upper == "CERTIFIED_OPERATIONAL":
        if status_upper != "OPERATIONAL_COMPLETE":
            return False, "contradictory_operational_certification_status"

    elif cert_upper == "CERTIFIED_FRONTEND_BUILD":
        if status_upper != "FRONTEND_BUILD_CERTIFIED":
            return False, "contradictory_frontend_certification_status"

    return True, "OK"


def read_canonical_result(
    result_path: str | Path,
    *,
    expected_job_id: str,
    attestations_dir: Path | None = None,
) -> CanonicalResultRead:
    path = Path(result_path)

    inspection = inspect_result_file(
        path,
        expected_job_id=expected_job_id,
    )

    if inspection.state is not ResultState.RESULT_TERMINAL_VALID:
        return CanonicalResultRead(
            job_id=expected_job_id,
            state=inspection.state.value,
            result_path=str(path),
            result_size_bytes=inspection.size_bytes,
            result_sha256=inspection.sha256 or None,
            terminal_result_valid=False,
            payload=None,
        )

    identity = validate_terminal_result_file(
        path,
        expected_job_id=expected_job_id,
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    if (
        payload.get("invalid_result_artifact") is True
        or str(payload.get("status") or "").strip().upper()
        == "INVALID_RESULT_ARTIFACT"
    ):
        raw_state = str(
            payload.get("result_integrity_state")
            or ResultState.RESULT_INVALID_JSON.value
        )
        try:
            mapped_state = ResultState(raw_state)
        except ValueError:
            mapped_state = ResultState.RESULT_INVALID_JSON
        return _fail_closed_read(
            job_id=expected_job_id,
            path=path,
            identity=identity,
            base_payload=payload,
            state=mapped_state,
            reason=str(
                payload.get("result_integrity_reason")
                or "invalid_result_artifact"
            ),
            reconciliation_status="INVALID_RESULT_ARTIFACT",
        )

    invariants_ok, invariant_reason = _validate_internal_invariants(payload)
    if not invariants_ok:
        return _fail_closed_read(
            job_id=expected_job_id,
            path=path,
            identity=identity,
            base_payload=payload,
            state=ResultState.RESULT_STATUS_MISMATCH,
            reason=invariant_reason,
            reconciliation_status="CONTRADICTORY_RESULT_INVARIANTS",
        )

    status_upper = str(payload.get("status") or "").strip().upper()
    cert_upper = str(payload.get("certification") or "").strip().upper()

    in_results_dir = path.parent.name == "results"
    state_root = path.parent.parent if in_results_dir else None
    marker_path = (
        state_root / "published" / f"{expected_job_id}.json"
        if state_root is not None
        else None
    )
    marker = (
        parse_published_marker(marker_path)
        if marker_path is not None
        else None
    )

    if marker is not None and "_invalid" in marker:
        return _fail_closed_read(
            job_id=expected_job_id,
            path=path,
            identity=identity,
            base_payload=payload,
            state=ResultState.READ_SOURCE_MISMATCH,
            reason=f"invalid_published_marker:{marker['_invalid']}",
            reconciliation_status="TAMPERED_PUBLISHED_MARKER",
        )

    if marker is not None:
        marker_job_id = str(
            marker.get("job_id") or expected_job_id
        ).strip()
        if marker_job_id != expected_job_id:
            return _fail_closed_read(
                job_id=expected_job_id,
                path=path,
                identity=identity,
                base_payload=payload,
                state=ResultState.READ_SOURCE_MISMATCH,
                reason="published_marker_job_id_mismatch",
                reconciliation_status="CONTRADICTORY_CERTIFICATION_EVIDENCE",
            )

        if marker.get("_format") == "json" and "status" in marker:
            if str(marker.get("status") or "").strip().upper() != "PUBLISHED":
                return _fail_closed_read(
                    job_id=expected_job_id,
                    path=path,
                    identity=identity,
                    base_payload=payload,
                    state=ResultState.READ_SOURCE_MISMATCH,
                    reason="published_marker_status_invalid",
                    reconciliation_status="CONTRADICTORY_CERTIFICATION_EVIDENCE",
                )

        marker_sha = marker.get("result_sha256")
        if marker_sha is not None and (
            not _is_valid_sha256(marker_sha)
            or str(marker_sha).strip().lower() != identity.sha256.lower()
        ):
            return _fail_closed_read(
                job_id=expected_job_id,
                path=path,
                identity=identity,
                base_payload=payload,
                state=ResultState.RESULT_SHA_MISMATCH,
                reason="published_marker_result_sha256_mismatch",
                reconciliation_status="TAMPERED_PUBLISHED_MARKER",
            )

    if status_upper != "INTEGRATED":
        if marker is not None:
            marker_cert = str(marker.get("certification") or "").strip().upper()
            if marker_cert and marker_cert != cert_upper:
                return _fail_closed_read(
                    job_id=expected_job_id,
                    path=path,
                    identity=identity,
                    base_payload=payload,
                    state=ResultState.READ_SOURCE_MISMATCH,
                    reason="published_marker_contradicts_non_mutation_result",
                    reconciliation_status="CONTRADICTORY_CERTIFICATION_EVIDENCE",
                )
        if cert_upper in _CERTIFIED_STATES:
            payload.setdefault("work_completion", "COMPLETE")
            payload.setdefault("reconciliation_status", "CERTIFIED_DIRECT")
        return CanonicalResultRead(
            job_id=expected_job_id,
            state=ResultState.RESULT_TERMINAL_VALID.value,
            result_path=str(path),
            result_size_bytes=identity.size_bytes,
            result_sha256=identity.sha256,
            terminal_result_valid=True,
            payload=payload,
        )

    # status_upper == "INTEGRATED"
    development_sha = str(payload.get("development_sha") or "").strip()
    if development_sha and not payload.get("commit_sha"):
        payload["commit_sha"] = development_sha

    files_changed = [
        str(x)
        for x in (payload.get("files_changed") or [])
        if isinstance(x, str) and x.strip()
    ]

    resolved_att_dir = (
        _resolve_attestations_dir(state_root, attestations_dir)
        if state_root is not None
        else attestations_dir
    )

    if marker is None:
        if (
            state_root is not None
            and (
                state_root / "published_results" / f"{expected_job_id}.json"
            ).is_file()
        ):
            return _fail_closed_read(
                job_id=expected_job_id,
                path=path,
                identity=identity,
                base_payload=payload,
                state=ResultState.READ_SOURCE_MISMATCH,
                reason="published_result_without_published_marker",
                reconciliation_status="CONTRADICTORY_CERTIFICATION_EVIDENCE",
            )

        if (
            resolved_att_dir is not None
            and _is_valid_sha(development_sha)
            and (resolved_att_dir / f"{development_sha}.json").exists()
        ):
            att_ok, att_reason, att_sha = _verify_attestation_file(
                resolved_att_dir / f"{development_sha}.json",
                expected_job_id=expected_job_id,
                expected_source_sha=development_sha,
                expected_files_changed=files_changed,
            )
            if not att_ok:
                return _fail_closed_read(
                    job_id=expected_job_id,
                    path=path,
                    identity=identity,
                    base_payload=payload,
                    state=ResultState.READ_SOURCE_MISMATCH,
                    reason=att_reason,
                    reconciliation_status="TAMPERED_ATTESTATION",
                )
            if att_sha:
                payload["attestation_sha256"] = att_sha

        if cert_upper == "PENDING_AUDIT_EVIDENCE":
            payload["work_completion"] = "PENDING_CERTIFICATION"
            payload["percent_complete"] = min(
                int(payload.get("percent_complete") or 95),
                95,
            )
            payload["reconciliation_status"] = (
                "PROVISIONAL_PENDING_AUDIT_EVIDENCE"
            )
        elif cert_upper == "CERTIFIED":
            if not _is_valid_sha(development_sha):
                return _fail_closed_read(
                    job_id=expected_job_id,
                    path=path,
                    identity=identity,
                    base_payload=payload,
                    state=ResultState.RESULT_STATUS_MISMATCH,
                    reason="certified_mutation_missing_development_sha",
                    reconciliation_status="CONTRADICTORY_RESULT_INVARIANTS",
                )
            payload.setdefault("work_completion", "COMPLETE")
            payload["percent_complete"] = 100
            payload.setdefault("certified_source_sha", development_sha)
            payload.setdefault("reconciliation_status", "CERTIFIED_DIRECT")

        return CanonicalResultRead(
            job_id=expected_job_id,
            state=ResultState.RESULT_TERMINAL_VALID.value,
            result_path=str(path),
            result_size_bytes=identity.size_bytes,
            result_sha256=identity.sha256,
            terminal_result_valid=True,
            payload=payload,
        )

    # marker is present for an INTEGRATED result
    marker_cert = str(marker.get("certification") or "").strip().upper()
    marker_commit = (
        str(marker.get("commit")).strip()
        if marker.get("commit") is not None
        else None
    )

    if marker_cert == "PENDING_AUDIT_EVIDENCE":
        if cert_upper == "CERTIFIED":
            return _fail_closed_read(
                job_id=expected_job_id,
                path=path,
                identity=identity,
                base_payload=payload,
                state=ResultState.READ_SOURCE_MISMATCH,
                reason="local_certified_contradicts_provisional_marker",
                reconciliation_status="CONTRADICTORY_CERTIFICATION_EVIDENCE",
            )
        if not _is_valid_sha(development_sha):
            return _fail_closed_read(
                job_id=expected_job_id,
                path=path,
                identity=identity,
                base_payload=payload,
                state=ResultState.READ_SOURCE_MISMATCH,
                reason="provisional_mutation_missing_development_sha",
                reconciliation_status="CONTRADICTORY_CERTIFICATION_EVIDENCE",
            )
        if (
            resolved_att_dir is not None
            and (resolved_att_dir / f"{development_sha}.json").exists()
        ):
            att_ok, att_reason, att_sha = _verify_attestation_file(
                resolved_att_dir / f"{development_sha}.json",
                expected_job_id=expected_job_id,
                expected_source_sha=development_sha,
                expected_files_changed=files_changed,
            )
            if not att_ok:
                return _fail_closed_read(
                    job_id=expected_job_id,
                    path=path,
                    identity=identity,
                    base_payload=payload,
                    state=ResultState.READ_SOURCE_MISMATCH,
                    reason=att_reason,
                    reconciliation_status="TAMPERED_ATTESTATION",
                )
            if att_sha:
                payload["attestation_sha256"] = att_sha

        if state_root is not None:
            pub_ok, pub_reason, pub_raw = _read_published_result_bytes(
                state_root=state_root,
                expected_job_id=expected_job_id,
                marker_commit=marker_commit,
            )
            if not pub_ok:
                return _fail_closed_read(
                    job_id=expected_job_id,
                    path=path,
                    identity=identity,
                    base_payload=payload,
                    state=ResultState.READ_SOURCE_MISMATCH,
                    reason=pub_reason,
                    reconciliation_status="CONTRADICTORY_CERTIFICATION_EVIDENCE",
                )
            if pub_raw is not None:
                v_ok, v_reason, _, pub_sha = _verify_published_result_bytes(
                    pub_raw,
                    expected_job_id=expected_job_id,
                    expected_source_sha=development_sha,
                    expected_files_changed=files_changed,
                    expected_certification="PENDING_AUDIT_EVIDENCE",
                )
                if not v_ok:
                    return _fail_closed_read(
                        job_id=expected_job_id,
                        path=path,
                        identity=identity,
                        base_payload=payload,
                        state=ResultState.READ_SOURCE_MISMATCH,
                        reason=v_reason,
                        reconciliation_status="CONTRADICTORY_CERTIFICATION_EVIDENCE",
                    )
                if pub_sha:
                    payload["published_result_sha256"] = pub_sha

        payload["certification"] = "PENDING_AUDIT_EVIDENCE"
        payload["work_completion"] = "PENDING_CERTIFICATION"
        payload["percent_complete"] = 95
        payload["reconciliation_status"] = (
            "PROVISIONAL_PENDING_AUDIT_EVIDENCE"
        )
        if marker_commit:
            payload["published_result_commit"] = marker_commit
        return CanonicalResultRead(
            job_id=expected_job_id,
            state=ResultState.RESULT_TERMINAL_VALID.value,
            result_path=str(path),
            result_size_bytes=identity.size_bytes,
            result_sha256=identity.sha256,
            terminal_result_valid=True,
            payload=payload,
        )

    if marker_cert != "CERTIFIED":
        return _fail_closed_read(
            job_id=expected_job_id,
            path=path,
            identity=identity,
            base_payload=payload,
            state=ResultState.READ_SOURCE_MISMATCH,
            reason=f"published_marker_not_certified:{marker_cert or 'EMPTY'}",
            reconciliation_status="CONTRADICTORY_CERTIFICATION_EVIDENCE",
        )

    # marker_cert == "CERTIFIED"
    if cert_upper not in {"PENDING_AUDIT_EVIDENCE", "CERTIFIED"}:
        return _fail_closed_read(
            job_id=expected_job_id,
            path=path,
            identity=identity,
            base_payload=payload,
            state=ResultState.READ_SOURCE_MISMATCH,
            reason=f"published_certified_contradicts_local:{cert_upper}",
            reconciliation_status="CONTRADICTORY_CERTIFICATION_EVIDENCE",
        )

    if not _is_valid_sha(development_sha):
        return _fail_closed_read(
            job_id=expected_job_id,
            path=path,
            identity=identity,
            base_payload=payload,
            state=ResultState.READ_SOURCE_MISMATCH,
            reason="certified_marker_missing_valid_development_sha",
            reconciliation_status="CONTRADICTORY_CERTIFICATION_EVIDENCE",
        )

    if not files_changed:
        return _fail_closed_read(
            job_id=expected_job_id,
            path=path,
            identity=identity,
            base_payload=payload,
            state=ResultState.READ_SOURCE_MISMATCH,
            reason="certified_marker_without_files_changed",
            reconciliation_status="CONTRADICTORY_CERTIFICATION_EVIDENCE",
        )

    require_attestation = (
        marker.get("_format") == "kv"
        or bool(marker_commit)
        or (resolved_att_dir is not None and resolved_att_dir.is_dir())
    )
    attestation_sha256: str | None = None
    if require_attestation:
        if resolved_att_dir is None:
            return _fail_closed_read(
                job_id=expected_job_id,
                path=path,
                identity=identity,
                base_payload=payload,
                state=ResultState.READ_SOURCE_MISMATCH,
                reason="attestations_dir_unavailable",
                reconciliation_status="CONTRADICTORY_CERTIFICATION_EVIDENCE",
            )
        att_ok, att_reason, attestation_sha256 = _verify_attestation_file(
            resolved_att_dir / f"{development_sha}.json",
            expected_job_id=expected_job_id,
            expected_source_sha=development_sha,
            expected_files_changed=files_changed,
        )
        if not att_ok:
            return _fail_closed_read(
                job_id=expected_job_id,
                path=path,
                identity=identity,
                base_payload=payload,
                state=ResultState.READ_SOURCE_MISMATCH,
                reason=att_reason,
                reconciliation_status="CONTRADICTORY_CERTIFICATION_EVIDENCE",
            )

    published_payload: dict[str, Any] | None = None
    published_sha256: str | None = None
    if state_root is not None:
        pub_ok, pub_reason, pub_raw = _read_published_result_bytes(
            state_root=state_root,
            expected_job_id=expected_job_id,
            marker_commit=marker_commit,
        )
        if not pub_ok:
            return _fail_closed_read(
                job_id=expected_job_id,
                path=path,
                identity=identity,
                base_payload=payload,
                state=ResultState.READ_SOURCE_MISMATCH,
                reason=pub_reason,
                reconciliation_status="CONTRADICTORY_CERTIFICATION_EVIDENCE",
            )
        if pub_raw is not None:
            (
                v_ok,
                v_reason,
                published_payload,
                published_sha256,
            ) = _verify_published_result_bytes(
                pub_raw,
                expected_job_id=expected_job_id,
                expected_source_sha=development_sha,
                expected_files_changed=files_changed,
                expected_certification="CERTIFIED",
            )
            if not v_ok:
                return _fail_closed_read(
                    job_id=expected_job_id,
                    path=path,
                    identity=identity,
                    base_payload=payload,
                    state=ResultState.READ_SOURCE_MISMATCH,
                    reason=v_reason,
                    reconciliation_status="CONTRADICTORY_CERTIFICATION_EVIDENCE",
                )

    payload["certification"] = "CERTIFIED"
    payload["work_completion"] = "COMPLETE"
    payload["percent_complete"] = 100
    payload["certified_source_sha"] = development_sha
    payload["converged_head"] = str(
        (published_payload or {}).get("converged_head")
        or payload.get("converged_head")
        or development_sha
    )
    payload["certification_basis"] = str(
        (published_payload or {}).get("certification_basis")
        or payload.get("certification_basis")
        or "SHA_BOUND_ATTESTATION_PLUS_ARTIFACT_CONVERGENCE"
    )
    payload["commit_sha"] = development_sha
    payload["published_certification_verified"] = True
    payload["reconciliation_status"] = "RECONCILED_CERTIFIED"
    if marker_commit:
        payload["published_result_commit"] = marker_commit
    if published_sha256:
        payload["published_result_sha256"] = published_sha256
    if attestation_sha256:
        payload["attestation_sha256"] = attestation_sha256

    return CanonicalResultRead(
        job_id=expected_job_id,
        state=ResultState.RESULT_TERMINAL_VALID.value,
        result_path=str(path),
        result_size_bytes=identity.size_bytes,
        result_sha256=identity.sha256,
        terminal_result_valid=True,
        payload=payload,
    )
