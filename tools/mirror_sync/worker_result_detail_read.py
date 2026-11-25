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
import subprocess
from typing import Any

try:
    from tools.mirror_sync.worker_result_integrity import (
        is_terminal_status,
    )
    from tools.mirror_sync.worker_result_semantic_extract import (
        has_sensitive_marker,
        redact_sensitive_text,
        sanitize_repository_contract_payload,
    )
    from tools.mirror_sync.universal_job_result_publisher import (
        sanitize_maintenance_history_evidence,
        sanitize_readonly_evidence,
        sanitize_semantic_evidence,
    )
except ModuleNotFoundError:
    from worker_result_integrity import (
        is_terminal_status,
    )
    from worker_result_semantic_extract import (
        has_sensitive_marker,
        redact_sensitive_text,
        sanitize_repository_contract_payload,
    )
    from universal_job_result_publisher import (
        sanitize_maintenance_history_evidence,
        sanitize_readonly_evidence,
        sanitize_semantic_evidence,
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


def _read_published_result_fallback(job_id: str) -> dict[str, Any] | None:
    """Read-only fallback to origin/worker/results when absent locally without mutating history."""
    git_dir = RESULTS.parent.parent
    if not (git_dir / "HEAD").is_file():
        return None
    spec = f"origin/worker/results:worker_queue/results/{job_id}.json"
    try:
        proc = subprocess.run(
            ["git", f"--git-dir={git_dir}", "cat-file", "-p", spec],
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0 or not proc.stdout:
        return None
    if len(proc.stdout) > MAX_RESULT_BYTES:
        raise ValueError("RESULT_DETAIL_RESULT_TOO_LARGE")
    try:
        loaded = json.loads(proc.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("RESULT_DETAIL_RESULT_INVALID_JSON") from exc
    if not isinstance(loaded, dict):
        raise ValueError("RESULT_DETAIL_RESULT_NOT_OBJECT")
    return loaded


def _extract_typed_evidence(
    payload: dict[str, Any],
    checks: list[Any],
    *,
    source_failed: bool,
) -> dict[str, Any]:
    """Recover and sanitize repository, SQL, semantic, and maintenance evidence cleanly."""
    basis = str(payload.get("certification_basis") or "").strip().upper()
    check_types = {
        str(c.get("type") or "").strip()
        for c in checks
        if isinstance(c, dict)
    }

    repo_ev, raw_repo_seen, repo_summary, repo_truncated = _extract_repository_contract_evidence(payload, checks)
    repo_applicable = (
        "repository_contract_audit" in check_types
        or "repository_contract_evidence" in payload
        or "repository_evidence" in payload
        or "REPOSITORY" in basis
    )

    sql_applicable = (
        "sql_readonly_audit" in check_types
        or "sql_readonly_evidence" in payload
        or "READ_ONLY_SQL" in basis
    )
    sql_raw_seen = (
        payload.get("sql_readonly_evidence") is not None
        or any(
            isinstance(c, dict)
            and c.get("type") == "sql_readonly_audit"
            and (c.get("sql_evidence") is not None or bool(str(c.get("output") or "").strip()))
            for c in checks
        )
    )
    sql_ev = sanitize_readonly_evidence(payload) if sql_applicable else None
    sql_truncated = bool(
        isinstance(sql_ev, dict)
        and any(
            isinstance(entry, dict) and entry.get("truncated") is True
            for chk in (sql_ev.get("checks") or [])
            if isinstance(chk, dict)
            for entry in (chk.get("evidence") or [])
        )
    )

    sem_applicable = (
        "worker_result_semantic_extract" in check_types
        or "worker_result_semantic_evidence" in payload
        or "SEMANTIC_EXTRACT" in basis
    )
    sem_raw_seen = (
        payload.get("worker_result_semantic_evidence") is not None
        or any(
            isinstance(c, dict)
            and c.get("type") == "worker_result_semantic_extract"
            and (c.get("semantic_evidence") is not None or bool(str(c.get("output") or "").strip()))
            for c in checks
        )
    )
    sem_ev = sanitize_semantic_evidence(payload) if sem_applicable else None

    maint_applicable = (
        "worker_maintenance_history_readonly" in check_types
        or "maintenance_history_evidence" in payload
        or "MAINTENANCE_HISTORY" in basis
    )
    maint_raw_seen = (
        payload.get("maintenance_history_evidence") is not None
        or any(
            isinstance(c, dict)
            and c.get("type") == "worker_maintenance_history_readonly"
            and (c.get("maintenance_history_evidence") is not None or bool(str(c.get("output") or "").strip()))
            for c in checks
        )
    )
    maint_ev = None
    if maint_applicable:
        maint_ev = sanitize_maintenance_history_evidence(payload)
        if maint_ev is None and isinstance(payload.get("maintenance_history_evidence"), dict):
            pub_checks = payload["maintenance_history_evidence"].get("checks")
            if isinstance(pub_checks, list) and pub_checks:
                maint_ev = sanitize_maintenance_history_evidence({
                    "checks": [
                        {
                            "type": "worker_maintenance_history_readonly",
                            "maintenance_history_evidence": item,
                        }
                        for item in pub_checks
                        if isinstance(item, dict)
                    ]
                })

    def _channel_state(
        ev: dict[str, Any] | None,
        *,
        applicable: bool,
        raw_seen: bool,
        truncated: bool = False,
    ) -> str:
        if ev is not None:
            if source_failed:
                return "PARTIAL_WITH_FAILURES"
            return "TRUNCATED" if truncated else "COMPLETE"
        if raw_seen:
            return "REJECTED_UNSAFE_OR_OVERSIZED"
        if applicable:
            return "ABSENT"
        return "NOT_APPLICABLE"

    availability = {
        "repository_contract_evidence": _channel_state(
            repo_ev, applicable=repo_applicable, raw_seen=raw_repo_seen, truncated=repo_truncated
        ),
        "sql_readonly_evidence": _channel_state(
            sql_ev, applicable=sql_applicable, raw_seen=sql_raw_seen, truncated=sql_truncated
        ),
        "worker_result_semantic_evidence": _channel_state(
            sem_ev, applicable=sem_applicable, raw_seen=sem_raw_seen, truncated=False
        ),
        "maintenance_history_evidence": _channel_state(
            maint_ev, applicable=maint_applicable, raw_seen=maint_raw_seen, truncated=False
        ),
    }

    summary: dict[str, int] = dict(repo_summary or {})
    if isinstance(sql_ev, dict):
        sql_checks = [c for c in (sql_ev.get("checks") or []) if isinstance(c, dict)]
        sql_queries = [
            e for c in sql_checks for e in (c.get("evidence") or []) if isinstance(e, dict)
        ]
        summary["sql_check_count"] = len(sql_checks)
        summary["sql_query_count"] = len(sql_queries)
        summary["sql_rows_returned"] = sum(
            len(e.get("rows") or []) for e in sql_queries if isinstance(e.get("rows"), list)
        )
    if isinstance(sem_ev, dict):
        sem_checks = [c for c in (sem_ev.get("checks") or []) if isinstance(c, dict)]
        sem_fields = sem_ev.get("semantic_fields")
        summary["semantic_check_count"] = len(sem_checks)
        summary["semantic_fields_count"] = len(sem_fields) if isinstance(sem_fields, dict) else 0
    if isinstance(maint_ev, dict):
        maint_checks = [c for c in (maint_ev.get("checks") or []) if isinstance(c, dict)]
        summary["maintenance_check_count"] = len(maint_checks)

    any_recovered = any(x is not None for x in (repo_ev, sql_ev, sem_ev, maint_ev))
    any_rejected = any(v == "REJECTED_UNSAFE_OR_OVERSIZED" for v in availability.values())
    any_truncated = bool(repo_truncated or sql_truncated)

    if any_recovered:
        if source_failed:
            overall_status = "PARTIAL_WITH_FAILURES"
        elif any_rejected:
            overall_status = "REJECTED_UNSAFE_OR_OVERSIZED"
        elif any_truncated:
            overall_status = "TRUNCATED"
        else:
            overall_status = "COMPLETE"
    elif any_rejected:
        overall_status = "REJECTED_UNSAFE_OR_OVERSIZED"
    elif source_failed:
        overall_status = "FAILED_RESULT_NO_STRUCTURED_EVIDENCE"
    else:
        overall_status = "ABSENT"

    return {
        "repository_contract_evidence": repo_ev,
        "sql_readonly_evidence": sql_ev,
        "worker_result_semantic_evidence": sem_ev,
        "maintenance_history_evidence": maint_ev,
        "evidence_availability": availability,
        "evidence_summary": summary or None,
        "evidence_truncated": any_truncated,
        "evidence_status": overall_status,
    }


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
    if path.parent != RESULTS or path.is_symlink():
        raise ValueError("RESULT_DETAIL_RESULT_NOT_FOUND")

    if path.is_file():
        stat = path.stat()
        if stat.st_size > MAX_RESULT_BYTES:
            raise ValueError("RESULT_DETAIL_RESULT_TOO_LARGE")
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    else:
        fallback = _read_published_result_fallback(job_id)
        if fallback is None:
            raise ValueError("RESULT_DETAIL_RESULT_NOT_FOUND")
        payload = fallback

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
            "evidence_availability": {
                "repository_contract_evidence": "NON_TERMINAL_SOURCE",
                "sql_readonly_evidence": "NON_TERMINAL_SOURCE",
                "worker_result_semantic_evidence": "NON_TERMINAL_SOURCE",
                "maintenance_history_evidence": "NON_TERMINAL_SOURCE",
            },
            "repository_contract_evidence": None,
            "sql_readonly_evidence": None,
            "worker_result_semantic_evidence": None,
            "maintenance_history_evidence": None,
            "production_touched": (
                production_touched
            ),
            "production_allowed": False,
        }

    source_failed = bool(failed_checks) or (
        str(raw_status or "").strip().upper()
        not in _SUCCESS_TERMINAL_STATUSES
    )
    typed = _extract_typed_evidence(
        payload,
        checks,
        source_failed=source_failed,
    )

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
        "evidence_status": typed["evidence_status"],
        "evidence_truncated": typed["evidence_truncated"],
        "evidence_summary": typed["evidence_summary"],
        "evidence_availability": typed["evidence_availability"],
        "repository_contract_evidence": typed["repository_contract_evidence"],
        "sql_readonly_evidence": typed["sql_readonly_evidence"],
        "worker_result_semantic_evidence": typed["worker_result_semantic_evidence"],
        "maintenance_history_evidence": typed["maintenance_history_evidence"],
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
