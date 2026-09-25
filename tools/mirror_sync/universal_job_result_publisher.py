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
    allowed_entry_keys = ("path", "matched_terms", "candidate_ownership", "symbols", "imports", "routes", "tables_referenced", "helpers", "connections", "rbac_contracts", "scheduler_contracts", "integrations")
    for check in result.get("checks") or []:
        if not isinstance(check, dict) or check.get("type") != "repository_contract_audit":
            continue
        payload = check.get("repository_evidence")
        if not isinstance(payload, dict):
            continue
        if payload.get("status") != "PASS":
            continue
        entries = []
        for entry in payload.get("evidence") or []:
            if not isinstance(entry, dict):
                continue
            entries.append({key: entry.get(key) for key in allowed_entry_keys if key in entry})
        sanitized_checks.append({
            "status": "PASS",
            "mode": "READ_ONLY_REPOSITORY",
            "summary": payload.get("summary"),
            "truncated": bool(payload.get("truncated")),
            "evidence": entries,
        })
    return {"checks": sanitized_checks} if sanitized_checks else None



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
        if base_pass and (readonly_evidence is not None or repository_evidence is not None):
            return {
                "certified": True,
                "certification": "CERTIFIED_READ_ONLY",
                "work_completion": "COMPLETE",
                "percent_complete": 100,
                "certification_basis": "READ_ONLY_SQL_PASS_PLUS_SANITIZED_EVIDENCE" if readonly_evidence is not None else "READ_ONLY_REPOSITORY_PASS_PLUS_SANITIZED_EVIDENCE",
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

    if development_head != mirror_head:
        return pending

    ancestry = git(
        "merge-base",
        "--is-ancestor",
        source_sha,
        development_head,
        check=False,
    )
    if ancestry.returncode != 0:
        return pending

    files_changed = [
        str(value)
        for value in (result.get("files_changed") or [])
        if isinstance(value, str) and value
    ]

    if not files_changed:
        return pending

    artifact_check = git(
        "diff",
        "--quiet",
        source_sha,
        development_head,
        "--",
        *files_changed,
        check=False,
    )
    if artifact_check.returncode != 0:
        return pending

    return {
        "certified": True,
        "certification": "CERTIFIED",
        "work_completion": "COMPLETE",
        "percent_complete": 100,
        "certified_source_sha": source_sha,
        "converged_head": development_head,
        "certification_basis":
            "SHA_BOUND_ATTESTATION_PLUS_DESCENDANT_CONVERGENCE",
    }


def sanitize(result: dict[str, Any]) -> dict[str, Any]:
    allowed = (
        "schema", "job_id", "started_at_utc", "completed_at_utc", "status",
        "executor", "base_sha", "candidate_sha", "development_sha", "tests",
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
    frontend_build_evidence = sanitize_frontend_build_evidence(result)
    if frontend_build_evidence is not None:
        public["frontend_build_evidence"] = frontend_build_evidence

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

    # Todo resultado ya publicado es terminal para el publisher, salvo
    # promociones desde evidencia previa no certificada a una certificacion
    # terminal valida del mismo contrato.
    if desired not in {"CERTIFIED", "CERTIFIED_OPERATIONAL", "CERTIFIED_READ_ONLY"}:
        return True

    return f"certification={desired}" in marker_text



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
    """Return terminal artifacts with recent dispatcher results taking precedence."""
    by_name = {path.name: path for path in REJECTED.glob("*.json")}
    by_name.update({path.name: path for path in RESULTS.glob("*.json")})
    return sorted(
        by_name.values(),
        key=lambda path: (path.stat().st_mtime_ns, path.name),
        reverse=True,
    )


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
