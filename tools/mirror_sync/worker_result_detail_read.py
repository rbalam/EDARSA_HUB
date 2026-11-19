#!/usr/bin/env python3
"""Bounded sanitized read of one local Universal Worker result.

The caller supplies only a canonical job_id. The helper never accepts a path,
branch, shell command, SQL, environment selector or arbitrary file reference.
Only sanitized failure evidence leaves the local Worker queue.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
from typing import Any

from tools.mirror_sync.worker_result_integrity import (
    is_terminal_status,
)
from tools.mirror_sync.worker_result_semantic_extract import (
    has_sensitive_marker,
    redact_sensitive_text,
    sanitize_repository_contract_payload,
)

_SUCCESS_TERMINAL_STATUSES = frozenset(
    {
        "READ_ONLY_COMPLETE",
        "INTEGRATED",
        "OPERATIONAL_COMPLETE",
        "FRONTEND_BUILD_CERTIFIED",
    }
)


ROOT = Path(os.environ.get("EDARSAHUB_ROOT", "/app"))

RESULTS = (
    ROOT
    / ".git"
    / "universal-worker-queue"
    / "results"
)

JOB_ID_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$"
)

MAX_RESULT_BYTES = 1_000_000
MAX_FAILED_CHECKS = 20
MAX_OUTPUT_BYTES = 8_000
MAX_ASSERTION_LINES = 50


def _safe_label(
    value: Any,
    *,
    max_length: int = 256,
) -> str | None:
    if not isinstance(value, str):
        return None

    value = value.replace("\x00", "").strip()

    if not value:
        return None

    return redact_sensitive_text(
        value,
        max_length=max_length,
    )


def _safe_output(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    rows: list[str] = []

    for raw in value.replace("\x00", "").splitlines():
        if has_sensitive_marker(raw):
            rows.append("[REDACTED]")
            continue

        rows.append(
            redact_sensitive_text(
                raw,
                max_length=1000,
            )
        )

    text = "\n".join(rows)

    if len(text.encode("utf-8")) > MAX_OUTPUT_BYTES:
        text = text[-MAX_OUTPUT_BYTES:]

    return text


def _assertion_lines(output: str) -> list[str]:
    rows: list[str] = []

    for raw in output.splitlines():
        line = raw.strip()
        upper = line.upper()

        interesting = (
            line.startswith("E   ")
            or "ASSERTIONERROR" in upper
            or upper.startswith("FAILED ")
            or " ERROR " in f" {upper} "
            or "MISMATCH" in upper
        )

        if not interesting:
            continue

        safe = _safe_label(
            line,
            max_length=500,
        )

        if safe:
            rows.append(safe)

        if len(rows) >= MAX_ASSERTION_LINES:
            break

    return rows


def _safe_string_list(
    value: Any,
    *,
    max_items: int = 100,
    max_length: int = 512,
) -> list[str]:
    if not isinstance(value, list):
        return []

    rows: list[str] = []

    for item in value[:max_items]:
        safe = _safe_label(
            item,
            max_length=max_length,
        )

        if safe:
            rows.append(safe)

    return rows


def _summarize_repository_evidence(
    sanitized: dict[str, Any],
) -> tuple[dict[str, int], bool]:
    checks_list = sanitized.get("checks") or []
    scanned = 0
    matched = 0
    skipped = 0
    entries = 0
    truncated = False
    for item in checks_list:
        if not isinstance(item, dict):
            continue
        summary = item.get("summary")
        if isinstance(summary, dict):
            scanned += int(summary.get("scanned_files") or 0)
            matched += int(summary.get("matched_files") or 0)
            skipped += int(summary.get("skipped_sensitive") or 0)
        ev_list = item.get("evidence")
        if isinstance(ev_list, list):
            entries += len(ev_list)
        if item.get("truncated") is True:
            truncated = True
    return (
        {
            "check_count": len(checks_list),
            "scanned_files": scanned,
            "matched_files": matched,
            "skipped_sensitive": skipped,
            "entries_returned": entries,
        },
        truncated,
    )


def _extract_repository_contract_evidence(
    payload: dict[str, Any],
    checks: list[Any],
) -> tuple[dict[str, Any] | None, bool, dict[str, int] | None, bool]:
    """Extract and sanitize repository audit evidence reusing the canonical sanitizer."""
    candidates: list[Any] = []
    for raw in checks:
        if not isinstance(raw, dict):
            continue
        if raw.get("type") != "repository_contract_audit":
            continue
        for key in ("repository_evidence", "repository_contract_evidence"):
            if raw.get(key) is not None:
                candidates.append(raw.get(key))
                break

    if not candidates:
        for key in ("repository_contract_evidence", "repository_evidence"):
            if payload.get(key) is not None:
                candidates.append(payload.get(key))
                break

    if not candidates:
        return None, False, None, False

    sanitized_checks: list[dict[str, Any]] = []
    for candidate in candidates:
        clean = sanitize_repository_contract_payload(candidate)
        if clean is None:
            continue
        for item in clean.get("checks") or []:
            if isinstance(item, dict):
                sanitized_checks.append(item)

    if not sanitized_checks:
        return None, True, None, False

    combined = sanitize_repository_contract_payload({"checks": sanitized_checks})
    if combined is None:
        return None, True, None, False

    summary, truncated = _summarize_repository_evidence(combined)
    return combined, True, summary, truncated


def collect(job_id: str) -> dict[str, Any]:
    if not JOB_ID_RE.fullmatch(job_id):
        raise ValueError("RESULT_DETAIL_JOB_ID_INVALID")

    if (
        RESULTS.is_symlink()
        or not RESULTS.is_dir()
    ):
        raise ValueError(
            "RESULT_DETAIL_RESULTS_DIR_UNAVAILABLE"
        )

    path = RESULTS / f"{job_id}.json"

    if (
        path.parent != RESULTS
        or path.is_symlink()
        or not path.is_file()
    ):
        raise ValueError(
            "RESULT_DETAIL_RESULT_NOT_FOUND"
        )

    stat = path.stat()

    if stat.st_size > MAX_RESULT_BYTES:
        raise ValueError(
            "RESULT_DETAIL_RESULT_TOO_LARGE"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError(
            "RESULT_DETAIL_RESULT_NOT_OBJECT"
        )

    checks = payload.get("checks")
    checks = checks if isinstance(checks, list) else []

    failed_checks: list[dict[str, Any]] = []

    for raw in checks:
        if not isinstance(raw, dict):
            continue

        if str(
            raw.get("status") or ""
        ).strip().upper() != "FAIL":
            continue

        output = _safe_output(
            raw.get("output")
        )

        returncode = raw.get("returncode")

        if (
            isinstance(returncode, bool)
            or not isinstance(returncode, int)
        ):
            returncode = None

        failed_checks.append(
            {
                "type": _safe_label(
                    raw.get("type"),
                    max_length=128,
                ),
                "status": "FAIL",
                "returncode": returncode,
                "output": output,
                "assertion_lines": (
                    _assertion_lines(output)
                ),
            }
        )

        if (
            len(failed_checks)
            >= MAX_FAILED_CHECKS
        ):
            break

    percent = payload.get(
        "percent_complete"
    )

    if (
        isinstance(percent, bool)
        or not isinstance(percent, (int, float))
        or percent < 0
        or percent > 100
    ):
        percent = None

    production_touched = payload.get(
        "production_touched"
    )

    if not isinstance(
        production_touched,
        bool,
    ):
        production_touched = None

    raw_status = _safe_label(
        payload.get("status"),
    )
    source_terminal = is_terminal_status(raw_status)
    source_completed_at_utc = _safe_label(
        payload.get("completed_at_utc"),
        max_length=64,
    )

    if not source_terminal:
        return {
            "schema": (
                "edarsahub.worker-result-detail-read.v1"
            ),
            "mode": "READ_ONLY",
            "status": "PASS",
            "source_job_id": job_id,
            "source_terminal": False,
            "source_completed_at_utc": source_completed_at_utc,
            "result_status": raw_status,
            "quality_gate": _safe_label(
                payload.get("quality_gate"),
            ),
            "tests": _safe_label(
                payload.get("tests"),
            ),
            "certification": "NOT_CERTIFIED",
            "work_completion": "NON_TERMINAL",
            "percent_complete": None,
            "blockers": _safe_string_list(
                payload.get("blockers"),
                max_length=500,
            ),
            "files_changed": _safe_string_list(
                payload.get("files_changed"),
                max_length=512,
            ),
            "failed_checks": failed_checks,
            "failed_check_count": len(
                failed_checks
            ),
            "evidence_status": "NON_TERMINAL_SOURCE",
            "evidence_truncated": False,
            "evidence_summary": None,
            "repository_contract_evidence": None,
            "production_touched": (
                production_touched
            ),
            "production_allowed": False,
        }

    (
        repository_contract_evidence,
        raw_repo_seen,
        evidence_summary,
        evidence_truncated,
    ) = _extract_repository_contract_evidence(payload, checks)

    source_failed = bool(failed_checks) or (
        str(raw_status or "").strip().upper()
        not in _SUCCESS_TERMINAL_STATUSES
    )
    if repository_contract_evidence is not None:
        if source_failed:
            evidence_status = "PARTIAL_WITH_FAILURES"
        elif evidence_truncated:
            evidence_status = "TRUNCATED"
        else:
            evidence_status = "COMPLETE"
    elif raw_repo_seen:
        evidence_status = "REJECTED_UNSAFE_OR_OVERSIZED"
    elif source_failed:
        evidence_status = "FAILED_RESULT_NO_STRUCTURED_EVIDENCE"
    else:
        evidence_status = "ABSENT"

    return {
        "schema": (
            "edarsahub.worker-result-detail-read.v1"
        ),
        "mode": "READ_ONLY",
        "status": "PASS",
        "source_job_id": job_id,
        "source_terminal": True,
        "source_completed_at_utc": source_completed_at_utc,
        "result_status": raw_status,
        "quality_gate": _safe_label(
            payload.get("quality_gate"),
        ),
        "tests": _safe_label(
            payload.get("tests"),
        ),
        "certification": _safe_label(
            payload.get("certification"),
        ),
        "work_completion": _safe_label(
            payload.get("work_completion"),
        ),
        "percent_complete": percent,
        "blockers": _safe_string_list(
            payload.get("blockers"),
            max_length=500,
        ),
        "files_changed": _safe_string_list(
            payload.get("files_changed"),
            max_length=512,
        ),
        "failed_checks": failed_checks,
        "failed_check_count": len(
            failed_checks
        ),
        "evidence_status": evidence_status,
        "evidence_truncated": evidence_truncated,
        "evidence_summary": evidence_summary,
        "repository_contract_evidence": repository_contract_evidence,
        "production_touched": (
            production_touched
        ),
        "production_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--job-id",
        required=True,
    )

    args = parser.parse_args()

    try:
        payload = collect(args.job_id)

        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )

        return 0

    except (
        OSError,
        ValueError,
        RuntimeError,
        json.JSONDecodeError,
    ) as exc:

        print(
            json.dumps(
                {
                    "schema": (
                        "edarsahub."
                        "worker-result-detail-read.v1"
                    ),
                    "mode": "READ_ONLY",
                    "status": "FAIL",
                    "error_code": type(exc).__name__,
                    **(
                        {"error_detail": str(exc)}
                        if str(exc).startswith("RESULT_DETAIL_")
                        else {}
                    ),
                    "production_allowed": False,
                },
                sort_keys=True,
            )
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
