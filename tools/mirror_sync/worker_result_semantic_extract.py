"""Read worker result artifacts and emit semantic gate fields."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from collections import deque
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
REMOTE = os.environ.get("EDARSAHUB_QUEUE_REMOTE", "origin")
RESULT_BRANCH = os.environ.get("EDARSAHUB_RESULT_BRANCH", "worker/results")
DEFAULT_FIELDS = [
    "gate3_allowed",
    "last_gate_executed",
    "last_gate_certified",
    "real_implementation_percent",
    "next_allowed_gate",
    "blocking_reason_if_any",
]


def git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=120,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def source(request: dict[str, Any]) -> dict[str, Any]:
    value = request.get("source_result")
    if isinstance(value, dict):
        return value
    return request


def read_artifact(request: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    src = source(request)
    path = str(src.get("path") or src.get("source_result_path") or "").strip()
    branch = str(src.get("branch") or src.get("source_result_branch") or RESULT_BRANCH).strip()
    commit = str(src.get("commit") or src.get("source_result_commit") or "").strip()
    blob_sha = str(src.get("blob_sha") or src.get("source_result_blob_sha") or "").strip()
    attempts: list[dict[str, str]] = []

    if branch:
        fetched = git(["fetch", REMOTE, branch])
        attempts.append({"method": "fetch_branch", "status": "PASS" if fetched.returncode == 0 else "FAIL", "detail": fetched.stdout[-500:]})

    refs = []
    if branch:
        refs.extend([f"{REMOTE}/{branch}", branch])
    if commit:
        refs.append(commit)
    if path:
        for ref in refs:
            shown = git(["show", f"{ref}:{path}"])
            attempts.append({"method": "git_show", "ref": ref, "status": "PASS" if shown.returncode == 0 else "FAIL", "detail": shown.stdout[-500:]})
            if shown.returncode == 0:
                return decode(shown.stdout, path, branch, commit, blob_sha, f"git_show:{ref}:{path}", attempts)

    if blob_sha:
        blob = git(["cat-file", "-p", blob_sha])
        attempts.append({"method": "git_cat_file", "status": "PASS" if blob.returncode == 0 else "FAIL", "detail": blob.stdout[-500:]})
        if blob.returncode == 0:
            return decode(blob.stdout, path, branch, commit, blob_sha, f"git_cat_file:{blob_sha}", attempts)

    return None, {
        "source_result_read_status": "RESULT_READ_FAILED",
        "source_result_path": path,
        "source_result_branch": branch,
        "source_result_commit": commit,
        "source_result_blob_sha": blob_sha,
        "read_attempts": attempts,
    }


def decode(text: str, path: str, branch: str, commit: str, blob_sha: str, loader: str, attempts: list[dict[str, str]]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    meta = {
        "source_result_read_status": "RESULT_READ_OK",
        "source_result_path": path,
        "source_result_branch": branch,
        "source_result_commit": commit,
        "source_result_blob_sha": blob_sha,
        "source_result_size_bytes": len(text.encode("utf-8")),
        "source_result_sha256": sha,
        "source_result_loader": loader,
        "read_attempts": attempts,
    }
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        meta["source_result_read_status"] = "RESULT_INVALID_JSON"
        meta["json_error"] = str(exc)
        return None, meta
    if not isinstance(payload, dict):
        meta["source_result_read_status"] = "RESULT_NOT_OBJECT"
        return None, meta
    return payload, meta


def find_key(payload: Any, key: str) -> Any:
    if isinstance(payload, dict) and key in payload:
        return payload[key]
    queue: deque[tuple[Any, int]] = deque([(payload, 0)])
    while queue:
        current, depth = queue.popleft()
        if depth > 8:
            continue
        if isinstance(current, dict):
            for current_key, value in current.items():
                if current_key == key:
                    return value
                if isinstance(value, (dict, list)):
                    queue.append((value, depth + 1))
        elif isinstance(current, list):
            for value in current[:200]:
                if isinstance(value, (dict, list)):
                    queue.append((value, depth + 1))
    return None


def truthy(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "1", "allowed", "pass"}
    return False


def build_report(payload: dict[str, Any], request: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    requested = request.get("required_semantic_fields")
    if not isinstance(requested, list) or not requested:
        requested = DEFAULT_FIELDS

    fields = list(dict.fromkeys([*DEFAULT_FIELDS, *(str(field) for field in requested)]))
    raw_semantic_fields = {str(field): find_key(payload, str(field)) for field in fields}
    source_missing = sorted(key for key, value in raw_semantic_fields.items() if value is None)
    source_semantic_complete = not source_missing

    semantic_fields = dict(raw_semantic_fields)
    if not source_semantic_complete:
        fail_closed = {
            "gate3_allowed": False,
            "last_gate_executed": payload.get("job_id") or payload.get("status") or "UNKNOWN_SOURCE_RESULT",
            "last_gate_certified": False,
            "real_implementation_percent": None,
            "next_allowed_gate": "GATE3_HOLD_PENDING_EXPLICIT_SEMANTIC_FIELDS",
            "blocking_reason_if_any": "SOURCE_SEMANTIC_FIELDS_MISSING",
        }
        for key, value in fail_closed.items():
            if semantic_fields.get(key) is None:
                semantic_fields[key] = value

    source_blockers = payload.get("blockers") or []
    source_pass = (
        str(payload.get("tests") or "").upper() == "PASS"
        and str(payload.get("quality_gate") or "").upper() == "PASS"
        and payload.get("production_touched") is False
        and not source_blockers
    )
    gate3_allowed = bool(source_pass and source_semantic_complete and truthy(raw_semantic_fields.get("gate3_allowed")))

    if not source_semantic_complete:
        bridge_verdict = "SOURCE_SEMANTIC_FIELDS_DERIVED_FAIL_CLOSED"
    elif gate3_allowed:
        bridge_verdict = "SOURCE_SEMANTIC_FIELDS_COMPLETE_GATE3_ALLOWED"
    else:
        bridge_verdict = "SOURCE_SEMANTIC_FIELDS_COMPLETE_GATE3_HOLD"

    missing = [] if not source_semantic_complete else sorted(key for key, value in semantic_fields.items() if value is None)
    semantic_complete = not missing

    if gate3_allowed:
        next_allowed_step = "GATE3_PREP_ALLOWED"
    elif not source_semantic_complete:
        next_allowed_step = "GATE3_HOLD_PENDING_EXPLICIT_SEMANTIC_FIELDS"
    else:
        next_allowed_step = "GATE3_HOLD_SEMANTIC_FIELDS_COMPLETE_NOT_ALLOWED"

    return {
        "status": "PASS",
        "mode": "READ_ONLY_WORKER_RESULT_SEMANTIC_EXTRACT",
        "bridge_verdict": bridge_verdict,
        "runtime_gap_confirmed": False,
        "source_result_reader_capability_current_state": "CAN_READ_SOURCE_RESULT_ARTIFACT",
        "can_read_worker_results_by_branch_path": str(meta.get("source_result_loader") or "").startswith("git_show"),
        "can_read_worker_results_by_blob_sha": str(meta.get("source_result_loader") or "").startswith("git_cat_file"),
        "can_emit_semantic_fields_from_source_result": True,
        "source_semantic_fields_complete": source_semantic_complete,
        "source_missing_semantic_fields": source_missing,
        "semantic_fields_complete": semantic_complete,
        "missing_semantic_fields": missing,
        "semantic_fields": semantic_fields,
        "gate3_allowed": gate3_allowed,
        "source_status": payload.get("status"),
        "source_quality_gate": payload.get("quality_gate"),
        "source_certification": payload.get("certification"),
        "source_work_completion": payload.get("work_completion"),
        "source_percent_complete": payload.get("percent_complete"),
        "source_production_touched": payload.get("production_touched"),
        "source_files_changed": payload.get("files_changed") or [],
        "source_blockers": source_blockers,
        "required_runtime_change": None,
        "next_allowed_step": next_allowed_step,
        **meta,
    }


def failure_report(request: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "FAIL",
        "mode": "READ_ONLY_WORKER_RESULT_SEMANTIC_EXTRACT",
        "bridge_verdict": "GAP_CONFIRMED",
        "runtime_gap_confirmed": True,
        "source_result_reader_capability_current_state": "CANNOT_READ_SOURCE_RESULT_ARTIFACT",
        "can_read_worker_results_by_branch_path": False,
        "can_read_worker_results_by_blob_sha": False,
        "can_emit_semantic_fields_from_source_result": False,
        "semantic_fields_complete": False,
        "missing_semantic_fields": list(request.get("required_semantic_fields") or DEFAULT_FIELDS),
        "semantic_fields": {},
        "gate3_allowed": False,
        "required_runtime_change": "SOURCE_RESULT_READER_BRIDGE_REQUIRED",
        "next_allowed_step": "EDARSAHUB-WORKER-SOURCE-RESULT-READER-BRIDGE-MUTATION-R1",
        **meta,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request-json", required=True)
    args = parser.parse_args(argv)
    request = json.loads(args.request_json)
    if not isinstance(request, dict):
        raise SystemExit("REQUEST_NOT_OBJECT")
    payload, meta = read_artifact(request)
    if payload is None:
        print(json.dumps(failure_report(request, meta), ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(build_report(payload, request, meta), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
