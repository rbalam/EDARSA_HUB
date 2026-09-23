#!/usr/bin/env python3
"""Universal GitHub queue bridge for the EDARSAHUB ChatGPT-controlled worker.

The queue lives in the dedicated ``worker/requests`` branch. This program only
receives and validates deterministic jobs produced by ChatGPT and materializes
them locally for the dispatcher. It never asks another AI to reinterpret a job
and it never executes shell text supplied by a request.
"""

from __future__ import annotations

# WORKER_DELIVERABLE_IMPORT_COMPAT_V1
try:
    from tools.mirror_sync.worker_deliverable_contract import normalize_required_deliverables
except ModuleNotFoundError:
    from worker_deliverable_contract import normalize_required_deliverables

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
STATE = ROOT / ".git" / "universal-worker-queue"
PENDING = STATE / "pending"
PROCESSING = STATE / "processing"
REJECTED = STATE / "rejected"
REJECTED_HISTORY = STATE / "rejected_history"
DONE = STATE / "done"
RESULTS = STATE / "results"
CORRECTABLE_REJECTION_REASONS = {"SUMMARY_LANGUAGE_MUST_BE_ES"}
CORRECTABLE_REJECTION_FIELDS = {"human_summary_language"}
REMOTE = os.environ.get("EDARSAHUB_QUEUE_REMOTE", "origin")
CANONICAL_REMOTE = os.environ.get(
    "EDARSAHUB_QUEUE_CANONICAL_REMOTE",
    "https://github.com/rbalam/EDARSA_HUB.git",
)
QUEUE_BRANCH = os.environ.get("EDARSAHUB_QUEUE_BRANCH", "worker/requests")
QUEUE_REF = os.environ.get(
    "EDARSAHUB_QUEUE_REF",
    "refs/remotes/edarsahub-worker-queue/worker/requests",
)
SCHEMA = "edarsahub.worker-job.v2"
JOB_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$")
ALLOWED_ACTIONS = {"replace_text", "write_file", "delete_file"}
ALLOWED_CHECKS = {"git_diff_check", "py_compile", "pytest", "frontend_build", "sql_readonly_audit", "repository_contract_audit"}
READ_ONLY_MODE = "READ_ONLY"
READ_ONLY_CHECKS = {"git_diff_check", "py_compile", "pytest", "sql_readonly_audit", "repository_contract_audit"}
SOFTRESTAURANT_FULL_HISTORY_MODE = "SOFTRESTAURANT_FULL_HISTORY_RESYNC"
MPRO_FULL_HISTORY_MODE = "MPRO_FULL_HISTORY_RESYNC"
COMERCIAL_RANGE_RESYNC_MODE = "COMERCIAL_RANGE_RESYNC"
ISCAM_DETAIL_BACKFILL_MODE = "ISCAM_DETAIL_BACKFILL"
ISCAM_PAYMENTS_ONLY_RESYNC_MODE = "ISCAM_PAYMENTS_ONLY_RESYNC"
SQL_MIGRATION_DEVELOPMENT_MODE = "SQL_MIGRATION_DEVELOPMENT"
FRONTEND_BUILD_CERTIFICATION_MODE = "FRONTEND_BUILD_CERTIFICATION"
UNIT_CODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,31}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_ACTIONS = int(os.environ.get("EDARSAHUB_JOB_MAX_ACTIONS", "100"))
MAX_TEXT_BYTES = int(os.environ.get("EDARSAHUB_JOB_MAX_TEXT_BYTES", "2000000"))
REQUIRE_REQUESTER = os.environ.get("EDARSAHUB_WORKER_REQUIRE_REQUESTER", "0") == "1"


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def resolve_queue_remote() -> str:
    """Return a usable queue remote without requiring a local ``origin`` alias."""
    configured = str(REMOTE or "").strip()
    if configured and ("://" in configured or configured.startswith("git@")):
        return configured
    if configured:
        probe = git("remote", "get-url", configured, check=False)
        if probe.returncode == 0 and probe.stdout.strip():
            return configured
    canonical = str(CANONICAL_REMOTE or "").strip()
    if not canonical:
        raise RuntimeError("QUEUE_REMOTE_NOT_AVAILABLE")
    return canonical


def ensure_dirs() -> None:
    for path in (PENDING, PROCESSING, REJECTED, REJECTED_HISTORY, DONE, RESULTS):
        path.mkdir(parents=True, exist_ok=True)


def safe_repo_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or "\x00" in value:
        return False
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        return False
    if path.parts and path.parts[0] == ".git":
        return False
    return True


def validate_action(action: Any, index: int) -> list[str]:
    errors: list[str] = []
    prefix = f"ACTION_{index}"
    if not isinstance(action, dict):
        return [f"{prefix}_NOT_OBJECT"]
    kind = action.get("type")
    if kind not in ALLOWED_ACTIONS:
        errors.append(f"{prefix}_INVALID_TYPE")
        return errors
    if not safe_repo_path(action.get("path")):
        errors.append(f"{prefix}_INVALID_PATH")
    relative = str(action.get("path") or "")
    repo_path = Path(relative)
    if (
        kind == "write_file"
        and repo_path.parts[:2] == ("backend", "core")
        and not (ROOT / repo_path).exists()
    ):
        errors.append(f"{prefix}_CORE_GROWTH_FORBIDDEN")
    if kind == "replace_text":
        old = action.get("old")
        new = action.get("new")
        if not isinstance(old, str) or not old:
            errors.append(f"{prefix}_OLD_REQUIRED")
        if not isinstance(new, str):
            errors.append(f"{prefix}_NEW_REQUIRED")
        count = action.get("expected_count", 1)
        if not isinstance(count, int) or count < 1 or count > 1000:
            errors.append(f"{prefix}_INVALID_EXPECTED_COUNT")
    elif kind == "write_file":
        content = action.get("content")
        if not isinstance(content, str):
            errors.append(f"{prefix}_CONTENT_REQUIRED")
        elif len(content.encode("utf-8")) > MAX_TEXT_BYTES:
            errors.append(f"{prefix}_CONTENT_TOO_LARGE")
    elif kind == "delete_file":
        expected = action.get("expected_sha256")
        if expected is None:
            errors.append(f"{prefix}_EXPECTED_SHA256_REQUIRED")
        elif not re.fullmatch(r"[0-9a-f]{64}", str(expected)):
            errors.append(f"{prefix}_INVALID_SHA256")
    expected = action.get("expected_sha256")
    if kind != "delete_file" and expected is not None and not re.fullmatch(r"[0-9a-f]{64}", str(expected)):
        errors.append(f"{prefix}_INVALID_SHA256")
    return errors


def validate_check(check: Any, index: int) -> list[str]:
    prefix = f"CHECK_{index}"
    if not isinstance(check, dict):
        return [f"{prefix}_NOT_OBJECT"]
    kind = check.get("type")
    if kind not in ALLOWED_CHECKS:
        return [f"{prefix}_INVALID_TYPE"]
    if kind in {"py_compile", "pytest"}:
        paths = check.get("paths")
        if not isinstance(paths, list) or not paths or not all(safe_repo_path(p) for p in paths):
            return [f"{prefix}_INVALID_PATHS"]
    if kind == "frontend_build":
        directory = check.get("directory", "frontend")
        if not safe_repo_path(directory):
            return [f"{prefix}_INVALID_DIRECTORY"]
    if kind == "sql_readonly_audit":
        queries = check.get("queries")
        if not isinstance(queries, list) or not queries:
            return [f"{prefix}_QUERIES_REQUIRED"]
        for item in queries:
            if not isinstance(item, dict):
                return [f"{prefix}_QUERY_NOT_OBJECT"]
            if not str(item.get("name") or "").strip():
                return [f"{prefix}_QUERY_NAME_REQUIRED"]
            sql = item.get("sql")
            if not isinstance(sql, str) or not sql.strip():
                return [f"{prefix}_QUERY_SQL_REQUIRED"]
    if kind == "repository_contract_audit":
        request = check.get("request")
        if not isinstance(request, dict):
            return [f"{prefix}_REQUEST_REQUIRED"]
        paths = request.get("paths")
        if not isinstance(paths, list) or not paths or not all(safe_repo_path(p) for p in paths):
            return [f"{prefix}_INVALID_PATHS"]
        terms = request.get("search_terms")
        if not isinstance(terms, list) or not terms or not all(isinstance(t, str) and t.strip() for t in terms):
            return [f"{prefix}_SEARCH_TERMS_REQUIRED"]
        for field in ("include_patterns", "exclude_patterns"):
            value = request.get(field, [])
            if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
                return [f"{prefix}_{field.upper()}_INVALID"]
        max_results = request.get("max_results", 500)
        if not isinstance(max_results, int) or max_results < 1 or max_results > 5000:
            return [f"{prefix}_MAX_RESULTS_INVALID"]
    return []


def validate(job: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(job, dict):
        return ["JOB_NOT_OBJECT"]
    if job.get("schema") != SCHEMA:
        errors.append("INVALID_SCHEMA")
    job_id = str(job.get("job_id") or "")
    if not JOB_ID.fullmatch(job_id):
        errors.append("INVALID_JOB_ID")
    if job.get("target_repo") != "rbalam/EDARSA_HUB":
        errors.append("INVALID_TARGET_REPO")
    if job.get("target_branch") != "Edarsahub_Desarrollo":
        errors.append("INVALID_TARGET_BRANCH")
    if job.get("production_allowed") is not False:
        errors.append("PRODUCTION_MUST_BE_FALSE")
    if not str(job.get("objective") or "").strip():
        errors.append("OBJECTIVE_REQUIRED")
    if job.get("human_summary_language") != "es":
        errors.append("SUMMARY_LANGUAGE_MUST_BE_ES")

    if "required_deliverables" in job:
        try:
            normalize_required_deliverables(
                job.get("required_deliverables")
            )
        except ValueError as exc:
            errors.append(str(exc))
    requester = job.get("requester")
    if requester is None:
        if REQUIRE_REQUESTER:
            errors.append("REQUESTER_REQUIRED")
    elif not isinstance(requester, dict):
        errors.append("REQUESTER_MUST_BE_OBJECT")
    else:
        email = str(requester.get("email") or "").strip()
        source = str(requester.get("source") or "").strip()
        if not email or "@" not in email:
            errors.append("REQUESTER_EMAIL_INVALID")
        if not source:
            errors.append("REQUESTER_SOURCE_REQUIRED")
        for field in ("project", "chat"):
            value = requester.get(field)
            if value is not None and not isinstance(value, str):
                errors.append(f"REQUESTER_{field.upper()}_MUST_BE_STRING")
    mode = str(job.get("mode") or "MUTATION")
    actions = job.get("actions")
    if mode == "READ_ONLY_SQL":
        if actions not in (None, []):
            errors.append("READ_ONLY_SQL_ACTIONS_FORBIDDEN")
    elif mode == READ_ONLY_MODE:
        if actions != []:
            errors.append("READ_ONLY_ACTIONS_MUST_BE_EMPTY_LIST")
    elif mode == COMERCIAL_RANGE_RESYNC_MODE:
        if actions not in (None, []):
            errors.append("COMERCIAL_RANGE_RESYNC_ACTIONS_FORBIDDEN")
        units = job.get("units", [])
        if not isinstance(units, list) or len(units) != 1 or not all(isinstance(u, str) and UNIT_CODE_RE.fullmatch(u.strip()) for u in units):
            errors.append("COMERCIAL_RANGE_RESYNC_EXACTLY_ONE_UNIT_REQUIRED")
        if not isinstance(job.get("fecha_inicio"), str) or not DATE_RE.fullmatch(job.get("fecha_inicio", "")):
            errors.append("COMERCIAL_RANGE_RESYNC_FECHA_INICIO_INVALID")
        if not isinstance(job.get("fecha_fin"), str) or not DATE_RE.fullmatch(job.get("fecha_fin", "")):
            errors.append("COMERCIAL_RANGE_RESYNC_FECHA_FIN_INVALID")
        dry_run = job.get("dry_run", True)
        if not isinstance(dry_run, bool):
            errors.append("COMERCIAL_RANGE_RESYNC_DRY_RUN_INVALID")
        if dry_run is False and job.get("confirm_comercial_range_resync") is not True:
            errors.append("COMERCIAL_RANGE_RESYNC_CONFIRMATION_REQUIRED")
    elif mode == ISCAM_DETAIL_BACKFILL_MODE:
        if actions not in (None, []):
            errors.append("ISCAM_DETAIL_BACKFILL_ACTIONS_FORBIDDEN")
        units = job.get("units", [])
        if not isinstance(units, list) or not units or len(units) > 32 or not all(isinstance(u, str) and UNIT_CODE_RE.fullmatch(u.strip()) for u in units):
            errors.append("ISCAM_DETAIL_BACKFILL_UNITS_INVALID")
        if not isinstance(job.get("fecha_inicio"), str) or not DATE_RE.fullmatch(job.get("fecha_inicio", "")):
            errors.append("ISCAM_DETAIL_BACKFILL_FECHA_INICIO_INVALID")
        if not isinstance(job.get("fecha_fin"), str) or not DATE_RE.fullmatch(job.get("fecha_fin", "")):
            errors.append("ISCAM_DETAIL_BACKFILL_FECHA_FIN_INVALID")
        dry_run = job.get("dry_run", True)
        if not isinstance(dry_run, bool):
            errors.append("ISCAM_DETAIL_BACKFILL_DRY_RUN_INVALID")
        if dry_run is False and job.get("confirm_detail_backfill") is not True:
            errors.append("ISCAM_DETAIL_BACKFILL_CONFIRMATION_REQUIRED")
    elif mode == ISCAM_PAYMENTS_ONLY_RESYNC_MODE:
        if actions not in (None, []):
            errors.append("ISCAM_PAYMENTS_ONLY_ACTIONS_FORBIDDEN")
        units = job.get("units", [])
        if not isinstance(units, list) or len(units) != 1 or not all(isinstance(u, str) and UNIT_CODE_RE.fullmatch(u.strip()) for u in units):
            errors.append("ISCAM_PAYMENTS_ONLY_EXACTLY_ONE_UNIT_REQUIRED")
        if not isinstance(job.get("fecha_inicio"), str) or not DATE_RE.fullmatch(job.get("fecha_inicio", "")):
            errors.append("ISCAM_PAYMENTS_ONLY_FECHA_INICIO_INVALID")
        if not isinstance(job.get("fecha_fin"), str) or not DATE_RE.fullmatch(job.get("fecha_fin", "")):
            errors.append("ISCAM_PAYMENTS_ONLY_FECHA_FIN_INVALID")
        dry_run = job.get("dry_run", True)
        if not isinstance(dry_run, bool):
            errors.append("ISCAM_PAYMENTS_ONLY_DRY_RUN_INVALID")
        if dry_run is False and job.get("confirm_payments_only_resync") is not True:
            errors.append("ISCAM_PAYMENTS_ONLY_CONFIRMATION_REQUIRED")
    elif mode == SQL_MIGRATION_DEVELOPMENT_MODE:
        if actions not in (None, []):
            errors.append("SQL_MIGRATION_ACTIONS_FORBIDDEN")
        for forbidden_field in ("sql", "command", "shell", "script", "path"):
            if job.get(forbidden_field) is not None:
                errors.append(f"SQL_MIGRATION_FORBIDDEN_FIELD:{forbidden_field}")
        migration_path = str(job.get("migration_path") or "")
        migration_parts = Path(migration_path).parts
        if (
            not safe_repo_path(migration_path)
            or len(migration_parts) < 4
            or migration_parts[:3] != ("backend", "database", "migrations")
            or not migration_path.lower().endswith(".sql")
        ):
            errors.append("SQL_MIGRATION_PATH_INVALID")
        migration_sha256 = str(job.get("migration_sha256") or "").lower()
        if not re.fullmatch(r"[0-9a-f]{64}", migration_sha256):
            errors.append("SQL_MIGRATION_SHA256_INVALID")
        if job.get("confirm_sql_migration") is not True:
            errors.append("SQL_MIGRATION_CONFIRMATION_REQUIRED")
        preflight_checks = job.get("preflight_checks")
        if not isinstance(preflight_checks, list) or not preflight_checks:
            errors.append("SQL_MIGRATION_PREFLIGHT_REQUIRED")
        elif any(not isinstance(c, dict) or c.get("type") != "sql_readonly_audit" for c in preflight_checks):
            errors.append("SQL_MIGRATION_PREFLIGHT_ONLY_SQL_AUDIT_ALLOWED")
        else:
            for index, check in enumerate(preflight_checks, 1):
                errors.extend(validate_check(check, index))
    elif mode == FRONTEND_BUILD_CERTIFICATION_MODE:
        if actions not in (None, []):
            errors.append("FRONTEND_BUILD_CERTIFICATION_ACTIONS_FORBIDDEN")
    elif mode == MPRO_FULL_HISTORY_MODE:
        if actions not in (None, []):
            errors.append("MPRO_RESYNC_ACTIONS_FORBIDDEN")
        units = job.get("units", [])
        if not isinstance(units, list) or len(units) != 1 or not all(isinstance(u, str) and UNIT_CODE_RE.fullmatch(u.strip()) for u in units):
            errors.append("MPRO_RESYNC_EXACTLY_ONE_UNIT_REQUIRED")
        dry_run = job.get("dry_run", True)
        if not isinstance(dry_run, bool):
            errors.append("MPRO_RESYNC_DRY_RUN_INVALID")
        if dry_run is False and job.get("confirm_full_history_resync") is not True:
            errors.append("MPRO_RESYNC_CONFIRMATION_REQUIRED")
    elif mode == SOFTRESTAURANT_FULL_HISTORY_MODE:
        if actions not in (None, []):
            errors.append("SOFTRESTAURANT_RESYNC_ACTIONS_FORBIDDEN")
        units = job.get("units", [])
        if not isinstance(units, list) or len(units) > 32 or not all(isinstance(u, str) and UNIT_CODE_RE.fullmatch(u.strip()) for u in units):
            errors.append("SOFTRESTAURANT_RESYNC_UNITS_INVALID")
        dry_run = job.get("dry_run", True)
        if not isinstance(dry_run, bool):
            errors.append("SOFTRESTAURANT_RESYNC_DRY_RUN_INVALID")
        if dry_run is False and job.get("confirm_full_history_resync") is not True:
            errors.append("SOFTRESTAURANT_RESYNC_CONFIRMATION_REQUIRED")
    else:
        if not isinstance(actions, list) or not actions:
            errors.append("ACTIONS_REQUIRED")
        elif len(actions) > MAX_ACTIONS:
            errors.append("TOO_MANY_ACTIONS")
        else:
            for index, action in enumerate(actions, 1):
                errors.extend(validate_action(action, index))
    checks = job.get("checks", [{"type": "git_diff_check"}])
    if mode == "READ_ONLY_SQL":
        if not isinstance(checks, list) or not checks:
            errors.append("READ_ONLY_SQL_CHECK_REQUIRED")
        elif any(not isinstance(c, dict) or c.get("type") != "sql_readonly_audit" for c in checks):
            errors.append("READ_ONLY_SQL_ONLY_AUDIT_CHECKS_ALLOWED")
    elif mode == READ_ONLY_MODE:
        if not isinstance(checks, list) or not checks:
            errors.append("READ_ONLY_CHECK_REQUIRED")
        elif any(not isinstance(c, dict) or c.get("type") not in READ_ONLY_CHECKS for c in checks):
            errors.append("READ_ONLY_ONLY_NON_MUTATING_CHECKS_ALLOWED")
    elif mode == COMERCIAL_RANGE_RESYNC_MODE:
        if not isinstance(checks, list) or not checks:
            errors.append("COMERCIAL_RANGE_RESYNC_AUDIT_REQUIRED")
        elif any(not isinstance(c, dict) or c.get("type") != "sql_readonly_audit" for c in checks):
            errors.append("COMERCIAL_RANGE_RESYNC_ONLY_SQL_AUDIT_ALLOWED")
    elif mode == ISCAM_DETAIL_BACKFILL_MODE:
        if not isinstance(checks, list) or not checks:
            errors.append("ISCAM_DETAIL_BACKFILL_AUDIT_REQUIRED")
        elif any(not isinstance(c, dict) or c.get("type") != "sql_readonly_audit" for c in checks):
            errors.append("ISCAM_DETAIL_BACKFILL_ONLY_SQL_AUDIT_ALLOWED")
    elif mode == ISCAM_PAYMENTS_ONLY_RESYNC_MODE:
        if not isinstance(checks, list) or not checks:
            errors.append("ISCAM_PAYMENTS_ONLY_AUDIT_REQUIRED")
        elif any(not isinstance(c, dict) or c.get("type") != "sql_readonly_audit" for c in checks):
            errors.append("ISCAM_PAYMENTS_ONLY_ONLY_SQL_AUDIT_ALLOWED")
    elif mode == SQL_MIGRATION_DEVELOPMENT_MODE:
        if not isinstance(checks, list) or not checks:
            errors.append("SQL_MIGRATION_POST_AUDIT_REQUIRED")
        elif any(not isinstance(c, dict) or c.get("type") != "sql_readonly_audit" for c in checks):
            errors.append("SQL_MIGRATION_POST_ONLY_SQL_AUDIT_ALLOWED")
    elif mode == FRONTEND_BUILD_CERTIFICATION_MODE:
        if not isinstance(checks, list) or not checks:
            errors.append("FRONTEND_BUILD_CERTIFICATION_CHECK_REQUIRED")
        elif not any(isinstance(c, dict) and c.get("type") == "frontend_build" for c in checks):
            errors.append("FRONTEND_BUILD_CERTIFICATION_FRONTEND_BUILD_REQUIRED")
        elif any(not isinstance(c, dict) or c.get("type") not in {"frontend_build", "git_diff_check", "repository_contract_audit"} for c in checks):
            errors.append("FRONTEND_BUILD_CERTIFICATION_ONLY_ALLOWED_CHECKS")
    elif mode == MPRO_FULL_HISTORY_MODE:
        if not isinstance(checks, list) or not checks:
            errors.append("MPRO_RESYNC_AUDIT_REQUIRED")
        elif any(not isinstance(c, dict) or c.get("type") != "sql_readonly_audit" for c in checks):
            errors.append("MPRO_RESYNC_ONLY_SQL_AUDIT_ALLOWED")
    elif mode == SOFTRESTAURANT_FULL_HISTORY_MODE:
        if not isinstance(checks, list) or not checks:
            errors.append("SOFTRESTAURANT_RESYNC_AUDIT_REQUIRED")
        elif any(not isinstance(c, dict) or c.get("type") != "sql_readonly_audit" for c in checks):
            errors.append("SOFTRESTAURANT_RESYNC_ONLY_SQL_AUDIT_ALLOWED")
    if not isinstance(checks, list):
        errors.append("CHECKS_MUST_BE_LIST")
    else:
        for index, check in enumerate(checks, 1):
            errors.extend(validate_check(check, index))
    return errors


def queue_files() -> list[str]:
    remote = resolve_queue_remote()
    git("fetch", "--quiet", remote, f"+{QUEUE_BRANCH}:{QUEUE_REF}")
    listing = git(
        "ls-tree", "-r", "--name-only", QUEUE_REF, "worker_queue/inbox"
    )
    return [
        line.strip()
        for line in listing.stdout.splitlines()
        if line.strip().startswith("worker_queue/inbox/") and line.strip().endswith(".json")
    ]


def read_remote(path: str) -> str:
    return git("show", f"{QUEUE_REF}:{path}").stdout


def already_claimed(name: str) -> bool:
    # worker_queue/inbox is immutable audit history. Normal lifecycle evidence
    # remains terminal. REJECTED is evaluated separately so a strictly
    # metadata-only contract correction can retry the same immutable job
    # identity while preserving its prior rejection evidence.
    return any(
        (folder / name).exists()
        for folder in (PENDING, PROCESSING, DONE, RESULTS)
    )


def _read_json_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def rejected_correction_retry_decision(name: str, raw: str, job: dict[str, Any]) -> dict[str, Any]:
    rejection_path = REJECTED / name
    if not rejection_path.exists():
        return {"present": False, "allowed": True}
    raw_path = REJECTED / f"{name}.raw"
    if not raw_path.is_file():
        return {"present": True, "allowed": False, "reason": "REJECTED_RETRY_RAW_EVIDENCE_MISSING"}
    previous_raw = raw_path.read_text(encoding="utf-8")
    if previous_raw == raw:
        return {"present": True, "allowed": False, "reason": "REJECTED_REQUEST_UNCHANGED"}
    rejection = _read_json_file(rejection_path)
    reasons = {str(value) for value in (rejection.get("reasons") or [])}
    if not reasons or not reasons.issubset(CORRECTABLE_REJECTION_REASONS):
        return {"present": True, "allowed": False, "reason": "REJECTED_REASON_NOT_CORRECTABLE", "previous_reasons": sorted(reasons)}
    if list(REJECTED_HISTORY.glob(f"{Path(name).stem}.*.json")):
        return {"present": True, "allowed": False, "reason": "REJECTED_CORRECTION_RETRY_LIMIT_REACHED"}
    try:
        previous_job = json.loads(previous_raw)
    except json.JSONDecodeError:
        return {"present": True, "allowed": False, "reason": "REJECTED_RETRY_PREVIOUS_JSON_INVALID"}
    if not isinstance(previous_job, dict):
        return {"present": True, "allowed": False, "reason": "REJECTED_RETRY_PREVIOUS_JOB_INVALID"}
    keys = set(previous_job) | set(job)
    changed_fields = sorted(key for key in keys if previous_job.get(key) != job.get(key))
    if not changed_fields:
        return {"present": True, "allowed": False, "reason": "REJECTED_REQUEST_UNCHANGED"}
    if set(changed_fields) - CORRECTABLE_REJECTION_FIELDS:
        return {"present": True, "allowed": False, "reason": "REJECTED_RETRY_SCOPE_CHANGED", "changed_fields": changed_fields}
    if job.get("human_summary_language") != "es":
        return {"present": True, "allowed": False, "reason": "REJECTED_RETRY_CORRECTION_INVALID", "changed_fields": changed_fields}
    return {
        "present": True,
        "allowed": True,
        "reason": "REJECTED_CONTRACT_CORRECTION_ALLOWED",
        "previous_reasons": sorted(reasons),
        "corrected_fields": changed_fields,
    }


def archive_rejection_for_retry(name: str) -> dict[str, str]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    rejection_path = REJECTED / name
    raw_path = REJECTED / f"{name}.raw"
    archived_rejection = REJECTED_HISTORY / f"{Path(name).stem}.{stamp}.json"
    archived_raw = REJECTED_HISTORY / f"{Path(name).stem}.{stamp}.json.raw"
    os.replace(rejection_path, archived_rejection)
    os.replace(raw_path, archived_raw)
    return {
        "rejection": str(archived_rejection),
        "raw": str(archived_raw),
    }


def write_rejection(source: str, reason: list[str], raw: str = "") -> None:
    name = Path(source).name
    payload = {
        "schema": "edarsahub.worker-rejection.v2",
        "job_id": Path(source).stem,
        "source": source,
        "status": "REJECTED",
        "reasons": reason,
        "summary_es": "El worker recibio la orden de ChatGPT, pero la rechazo porque el contrato determinista no es valido. Consulta 'reasons' para conocer el motivo exacto.",
        "received_at_utc": datetime.now(timezone.utc).isoformat(),
        "production_touched": False,
    }
    (REJECTED / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if raw:
        (REJECTED / f"{name}.raw").write_text(raw, encoding="utf-8")


def receive() -> int:
    ensure_dirs()
    accepted = rejected = skipped = 0
    for path in queue_files():
        name = Path(path).name
        if already_claimed(name):
            skipped += 1
            continue
        raw = read_remote(path)
        try:
            job = json.loads(raw)
        except json.JSONDecodeError:
            if (REJECTED / name).exists():
                skipped += 1
                continue
            write_rejection(path, ["INVALID_JSON"], raw)
            rejected += 1
            continue
        retry_decision = rejected_correction_retry_decision(name, raw, job)
        if retry_decision.get("present") and not retry_decision.get("allowed"):
            skipped += 1
            continue
        errors = validate(job)
        if errors:
            if retry_decision.get("present"):
                skipped += 1
                continue
            write_rejection(path, errors, raw)
            rejected += 1
            continue

        requester_authorization = {
            "allowed": True,
            "reason": "LEGACY_REQUESTER_NOT_ENFORCED",
        }
        if job.get("requester") is not None:
            try:
                from worker_requester_rbac import authorize_requester
                requester_authorization = authorize_requester(job.get("requester"))
            except Exception:
                requester_authorization = {
                    "allowed": False,
                    "reason": "REQUESTER_RBAC_RUNTIME_ERROR",
                }
            if not requester_authorization.get("allowed"):
                write_rejection(
                    path,
                    [f"REQUESTER_RBAC_DENIED:{requester_authorization.get('reason', 'UNKNOWN')}"],
                    raw,
                )
                rejected += 1
                continue

        retry_archive = None
        if retry_decision.get("present"):
            retry_archive = archive_rejection_for_retry(name)
        envelope = {
            "received_at_utc": datetime.now(timezone.utc).isoformat(),
            "queue_branch": QUEUE_BRANCH,
            "queue_path": path,
            "requester_authorization": requester_authorization,
            "job": job,
        }
        if retry_decision.get("present"):
            envelope["_worker_rejected_correction_retry"] = {
                "retry_count": 1,
                "previous_reasons": retry_decision.get("previous_reasons", []),
                "corrected_fields": retry_decision.get("corrected_fields", []),
                "archived_evidence": retry_archive,
            }
        (PENDING / name).write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        accepted += 1
    print(f"UNIVERSAL_QUEUE_ACCEPTED={accepted}")
    print(f"UNIVERSAL_QUEUE_REJECTED={rejected}")
    print(f"UNIVERSAL_QUEUE_SKIPPED={skipped}")
    return 0


def status() -> int:
    ensure_dirs()
    print(f"UNIVERSAL_QUEUE_PENDING={len(list(PENDING.glob('*.json')))}")
    print(f"UNIVERSAL_QUEUE_PROCESSING={len(list(PROCESSING.glob('*.json')))}")
    print(f"UNIVERSAL_QUEUE_REJECTED={len(list(REJECTED.glob('*.json')))}")
    print(f"UNIVERSAL_QUEUE_DONE={len(list(DONE.glob('*.json')))}")
    print(f"UNIVERSAL_QUEUE_RESULTS={len(list(RESULTS.glob('*.json')))}")
    return 0


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "receive"
    if command == "receive":
        return receive()
    if command == "status":
        return status()
    print("usage: universal_job_bridge.py [receive|status]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
