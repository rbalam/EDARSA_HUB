"""Canonical integrity contract for Universal Worker terminal results.

This module is global infrastructure.

It contains no domain-specific, Gate-specific, chat-specific or application
business logic.

Responsibilities:
- classify result state;
- validate terminal payload structure;
- reject empty/partial/non-terminal publication into results/;
- calculate immutable result identity;
- validate a materialized terminal result after atomic write.

It performs no Git push, queue dispatch, SQL, Production mutation or service
restart.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


RESULT_SCHEMA_PREFIX = "edarsahub.worker-result."

NON_TERMINAL_STATUSES = frozenset(
    {
        "",
        "PENDING",
        "QUEUED",
        "RECEIVED",
        "CLAIMED",
        "PROCESSING",
        "RUNNING",
        "PUBLISHED",
        "WAITING",
        "RETRYING",
    }
)


class ResultState(str, Enum):
    RESULT_ABSENT = "RESULT_ABSENT"
    RESULT_EMPTY = "RESULT_EMPTY"
    RESULT_INVALID_JSON = "RESULT_INVALID_JSON"
    RESULT_SCHEMA_INVALID = "RESULT_SCHEMA_INVALID"
    RESULT_JOB_ID_MISMATCH = "RESULT_JOB_ID_MISMATCH"
    RESULT_NON_TERMINAL = "RESULT_NON_TERMINAL"
    RESULT_TERMINAL_VALID = "RESULT_TERMINAL_VALID"
    RESULT_STATUS_MISMATCH = "RESULT_STATUS_MISMATCH"
    RESULT_SHA_MISMATCH = "RESULT_SHA_MISMATCH"
    RESULT_SIZE_MISMATCH = "RESULT_SIZE_MISMATCH"
    STATUS_STALE = "STATUS_STALE"
    READ_SOURCE_MISMATCH = "READ_SOURCE_MISMATCH"


@dataclass(frozen=True)
class ResultIdentity:
    job_id: str
    result_path: str
    sha256: str
    size_bytes: int
    schema: str
    status: str
    quality_gate: str
    certification: str
    completed_at_utc: str


@dataclass(frozen=True)
class ResultInspection:
    state: ResultState
    path: str
    size_bytes: int = 0
    sha256: str = ""
    job_id: str = ""
    status: str = ""
    reason: str = ""


def is_terminal_result_path(path: str | Path) -> bool:
    value = Path(path)

    return (
        value.name.endswith(".json")
        and value.parent.name == "results"
    )


def is_terminal_status(status: Any) -> bool:
    value = str(status or "").strip().upper()

    return bool(value) and value not in NON_TERMINAL_STATUSES


def _require_field(
    payload: dict[str, Any],
    key: str,
) -> None:
    if key not in payload:
        raise ValueError(f"RESULT_REQUIRED_FIELD_MISSING:{key}")


def validate_terminal_result_payload(
    payload: dict[str, Any],
    *,
    expected_job_id: str | None = None,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("RESULT_PAYLOAD_NOT_OBJECT")

    required = (
        "schema",
        "job_id",
        "status",
        "quality_gate",
        "certification",
        "blockers",
        "production_touched",
        "completed_at_utc",
    )

    for key in required:
        _require_field(payload, key)

    schema = str(payload.get("schema") or "").strip()

    if not schema.startswith(RESULT_SCHEMA_PREFIX):
        raise ValueError("RESULT_SCHEMA_INVALID")

    job_id = str(payload.get("job_id") or "").strip()

    if not job_id:
        raise ValueError("RESULT_JOB_ID_EMPTY")

    if expected_job_id is not None and job_id != expected_job_id:
        raise ValueError("RESULT_JOB_ID_MISMATCH")

    status = str(payload.get("status") or "").strip().upper()

    if not is_terminal_status(status):
        raise ValueError("RESULT_NON_TERMINAL")

    quality_gate = str(payload.get("quality_gate") or "").strip()

    if not quality_gate:
        raise ValueError("RESULT_QUALITY_GATE_EMPTY")

    certification = str(payload.get("certification") or "").strip()

    if not certification:
        raise ValueError("RESULT_CERTIFICATION_EMPTY")

    blockers = payload.get("blockers")

    if not isinstance(blockers, list):
        raise ValueError("RESULT_BLOCKERS_NOT_LIST")

    if not isinstance(payload.get("production_touched"), bool):
        raise ValueError("RESULT_PRODUCTION_TOUCHED_NOT_BOOL")

    completed_at_utc = str(payload.get("completed_at_utc") or "").strip()

    if not completed_at_utc:
        raise ValueError("RESULT_COMPLETED_AT_EMPTY")

    files_changed = payload.get("files_changed")

    if files_changed is not None and not isinstance(files_changed, list):
        raise ValueError("RESULT_FILES_CHANGED_NOT_LIST")

    slot_class = str(payload.get("slot_class") or "").strip().upper()

    read_only = (
        slot_class == "READ_ONLY"
        or status == "READ_ONLY_COMPLETE"
    )

    if read_only:
        if payload.get("production_touched") is not False:
            raise ValueError("READ_ONLY_PRODUCTION_TOUCHED")

        if payload.get("files_changed") not in (None, []):
            raise ValueError("READ_ONLY_FILES_CHANGED")

        for field in (
            "mutations_executed",
            "ddl_executed",
            "dml_executed",
            "backend_touched",
            "frontend_touched",
        ):
            if payload.get(field) is True:
                raise ValueError(f"READ_ONLY_MUTATION_FIELD_TRUE:{field}")

    return payload


def result_identity_from_bytes(
    raw: bytes,
    *,
    path: str,
    expected_job_id: str | None = None,
) -> ResultIdentity:
    if not raw:
        raise ValueError("RESULT_EMPTY")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("RESULT_INVALID_JSON") from exc

    validate_terminal_result_payload(
        payload,
        expected_job_id=expected_job_id,
    )

    return ResultIdentity(
        job_id=str(payload["job_id"]),
        result_path=path,
        sha256=hashlib.sha256(raw).hexdigest(),
        size_bytes=len(raw),
        schema=str(payload["schema"]),
        status=str(payload["status"]),
        quality_gate=str(payload["quality_gate"]),
        certification=str(payload["certification"]),
        completed_at_utc=str(payload["completed_at_utc"]),
    )


def validate_terminal_result_file(
    path: str | Path,
    *,
    expected_job_id: str | None = None,
) -> ResultIdentity:
    target = Path(path)

    if not target.is_file():
        raise ValueError("RESULT_ABSENT")

    raw = target.read_bytes()

    return result_identity_from_bytes(
        raw,
        path=target.as_posix(),
        expected_job_id=expected_job_id,
    )


def inspect_result_file(
    path: str | Path,
    *,
    expected_job_id: str | None = None,
) -> ResultInspection:
    target = Path(path)

    if not target.is_file():
        return ResultInspection(
            state=ResultState.RESULT_ABSENT,
            path=target.as_posix(),
            reason="FILE_NOT_FOUND",
        )

    raw = target.read_bytes()
    size = len(raw)
    sha = hashlib.sha256(raw).hexdigest()

    if size == 0:
        return ResultInspection(
            state=ResultState.RESULT_EMPTY,
            path=target.as_posix(),
            size_bytes=0,
            sha256=sha,
            reason="ZERO_BYTE_RESULT",
        )

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ResultInspection(
            state=ResultState.RESULT_INVALID_JSON,
            path=target.as_posix(),
            size_bytes=size,
            sha256=sha,
            reason="JSON_PARSE_FAILED",
        )

    if not isinstance(payload, dict):
        return ResultInspection(
            state=ResultState.RESULT_SCHEMA_INVALID,
            path=target.as_posix(),
            size_bytes=size,
            sha256=sha,
            reason="JSON_ROOT_NOT_OBJECT",
        )

    schema = str(payload.get("schema") or "")

    if not schema.startswith(RESULT_SCHEMA_PREFIX):
        return ResultInspection(
            state=ResultState.RESULT_SCHEMA_INVALID,
            path=target.as_posix(),
            size_bytes=size,
            sha256=sha,
            job_id=str(payload.get("job_id") or ""),
            status=str(payload.get("status") or ""),
            reason="SCHEMA_INVALID",
        )

    job_id = str(payload.get("job_id") or "").strip()

    if expected_job_id is not None and job_id != expected_job_id:
        return ResultInspection(
            state=ResultState.RESULT_JOB_ID_MISMATCH,
            path=target.as_posix(),
            size_bytes=size,
            sha256=sha,
            job_id=job_id,
            status=str(payload.get("status") or ""),
            reason="EXPECTED_JOB_ID_DIFFERS",
        )

    status = str(payload.get("status") or "").strip()

    if not is_terminal_status(status):
        return ResultInspection(
            state=ResultState.RESULT_NON_TERMINAL,
            path=target.as_posix(),
            size_bytes=size,
            sha256=sha,
            job_id=job_id,
            status=status,
            reason="NON_TERMINAL_STATUS",
        )

    try:
        validate_terminal_result_payload(
            payload,
            expected_job_id=expected_job_id,
        )
    except ValueError as exc:
        return ResultInspection(
            state=ResultState.RESULT_SCHEMA_INVALID,
            path=target.as_posix(),
            size_bytes=size,
            sha256=sha,
            job_id=job_id,
            status=status,
            reason=str(exc),
        )

    return ResultInspection(
        state=ResultState.RESULT_TERMINAL_VALID,
        path=target.as_posix(),
        size_bytes=size,
        sha256=sha,
        job_id=job_id,
        status=status,
        reason="TERMINAL_CONTRACT_VALID",
    )


def compare_result_identity(
    *,
    identity: ResultIdentity,
    expected_sha256: str | None = None,
    expected_size_bytes: int | None = None,
    expected_status: str | None = None,
) -> ResultState:
    if (
        expected_sha256 is not None
        and identity.sha256 != expected_sha256
    ):
        return ResultState.RESULT_SHA_MISMATCH

    if (
        expected_size_bytes is not None
        and identity.size_bytes != expected_size_bytes
    ):
        return ResultState.RESULT_SIZE_MISMATCH

    if (
        expected_status is not None
        and identity.status != expected_status
    ):
        return ResultState.RESULT_STATUS_MISMATCH

    return ResultState.RESULT_TERMINAL_VALID


def classify_source_consistency(
    *,
    canonical_sha256: str,
    observed_sha256: str,
) -> ResultState:
    if (
        not canonical_sha256
        or not observed_sha256
        or canonical_sha256 != observed_sha256
    ):
        return ResultState.READ_SOURCE_MISMATCH

    return ResultState.RESULT_TERMINAL_VALID
