"""Read worker result artifacts and emit semantic gate fields."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
REMOTE = os.environ.get("EDARSAHUB_QUEUE_REMOTE", "origin")
RESULT_BRANCH = os.environ.get("EDARSAHUB_RESULT_BRANCH", "worker/results")
DEV_BRANCH = "Edarsahub_Desarrollo"
DEFAULT_FIELDS = [
    "gate3_allowed",
    "last_gate_executed",
    "last_gate_certified",
    "real_implementation_percent",
    "next_allowed_gate",
    "blocking_reason_if_any",
]
DECISION_FIELDS = tuple(DEFAULT_FIELDS)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
FIELD_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")
CERTIFICATION_BASIS_RE = re.compile(r"^[A-Z0-9_]{3,128}$")
MAX_STRING_LENGTH = 4096
MAX_SUMMARY_LENGTH = 2000
MAX_CONTAINER_ITEMS = 100
MAX_RECURSION_DEPTH = 4
MAX_SERIALIZED_BYTES = 65536
SENSITIVE_TOKENS = (
    "secret",
    "password",
    "passwd",
    "token",
    "credential",
    "credencial",
    "encrypted",
    "cifrad",
    "api_key",
    "apikey",
    "private_key",
    "access_key",
    "authorization",
    "cookie",
    "bearer",
    "connection_string",
    "conn_str",
)
SECRET_PATTERNS = (
    re.compile(
        r"(?i)\b(?:secret|password|passwd|token|credential|credencial|api_key|apikey|private_key|access_key|authorization|cookie|bearer)\b\s*[:=]\s*\S+"
    ),
    re.compile(r"(?i)\b(?:ghp_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]{16,})\b"),
    re.compile(r"(?i)-----BEGIN (?:[A-Z0-9_-]+\s+)*PRIVATE\s+KEY-----"),
)
VALID_RESULT_STATUSES = frozenset({
    "READ_ONLY_COMPLETE",
    "INTEGRATED",
    "OPERATIONAL_COMPLETE",
    "FRONTEND_BUILD_CERTIFIED",
})
ALLOWED_REPOSITORY_SUMMARY_KEYS = (
    "matched_files",
    "scanned_files",
    "skipped_sensitive",
)
ALLOWED_REPOSITORY_ENTRY_KEYS = (
    "path",
    "matched_terms",
    "candidate_ownership",
    "symbols",
    "imports",
    "routes",
    "tables_referenced",
    "helpers",
    "connections",
    "rbac_contracts",
    "scheduler_contracts",
    "integrations",
)
ALLOWED_PROVENANCE_STATUSES = frozenset({
    "EXPLICIT_SOURCE_KEY",
    "DERIVED_CANONICAL_COMPATIBILITY",
    "INVALID_OR_UNVERIFIED_EXPLICIT_VALUE",
    "MISSING_OR_UNVERIFIED",
    "MISSING_IN_SOURCE",
})
ALLOWED_PROVENANCE_DERIVATIONS = frozenset({
    "NONE",
    "PUBLISHED_WORKER_RESULT_BASE_SHA_INVARIANT",
    "PUBLISHED_SANITIZED_REPOSITORY_CONTRACT_EVIDENCE",
    "FAIL_CLOSED_DEFAULT",
    "FAIL_CLOSED_NULL",
})
_COMMIT_LINEAGE_CACHE: dict[str, bool] = {}


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


def is_sensitive_key(name: str) -> bool:
    lowered = name.strip().lower()
    return any(token in lowered for token in SENSITIVE_TOKENS)


def has_sensitive_marker(text: str) -> bool:
    if any(pattern.search(text) for pattern in SECRET_PATTERNS):
        return True
    lowered = text.lower()
    for token in SENSITIVE_TOKENS:
        if f"{token}=" in lowered or f"{token}:" in lowered:
            return True
    return False


def redact_sensitive_text(text: str, *, max_length: int = MAX_STRING_LENGTH) -> str:
    cleaned = text.replace("\x00", "")
    for pattern in SECRET_PATTERNS:
        cleaned = pattern.sub("[REDACTED]", cleaned)
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned


def is_authentic_lineage_commit(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    candidate = value.strip()
    if not SHA_RE.fullmatch(candidate):
        return False
    cached = _COMMIT_LINEAGE_CACHE.get(candidate)
    if cached is not None:
        return cached
    exists = git(["cat-file", "-e", f"{candidate}^{{commit}}"])
    if exists.returncode != 0:
        _COMMIT_LINEAGE_CACHE[candidate] = False
        return False
    lineage = git(["merge-base", "--is-ancestor", candidate, "HEAD"])
    if lineage.returncode != 0:
        lineage = git(["merge-base", "--is-ancestor", candidate, f"{REMOTE}/{DEV_BRANCH}"])
    authentic = lineage.returncode == 0
    _COMMIT_LINEAGE_CACHE[candidate] = authentic
    return authentic


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
        attempts.append({
            "method": "fetch_branch",
            "status": "PASS" if fetched.returncode == 0 else "FAIL",
            "detail": redact_sensitive_text(fetched.stdout[-500:], max_length=500),
        })

    refs = []
    if branch:
        refs.extend([f"{REMOTE}/{branch}", branch])
    if commit:
        refs.append(commit)
    if path:
        for ref in refs:
            shown = git(["show", f"{ref}:{path}"])
            attempts.append({
                "method": "git_show",
                "ref": ref,
                "status": "PASS" if shown.returncode == 0 else "FAIL",
                "detail": redact_sensitive_text(shown.stdout[-500:], max_length=500),
            })
            if shown.returncode == 0:
                return decode(shown.stdout, path, branch, commit, blob_sha, f"git_show:{ref}:{path}", attempts)

    if blob_sha:
        blob = git(["cat-file", "-p", blob_sha])
        attempts.append({
            "method": "git_cat_file",
            "status": "PASS" if blob.returncode == 0 else "FAIL",
            "detail": redact_sensitive_text(blob.stdout[-500:], max_length=500),
        })
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
        meta["json_error"] = redact_sensitive_text(str(exc), max_length=300)
        return None, meta
    if not isinstance(payload, dict):
        meta["source_result_read_status"] = "RESULT_NOT_OBJECT"
        return None, meta
    return payload, meta


def truthy(value: Any) -> bool:
    return value is True


def has_verifiable_result_provenance(payload: dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    if payload.get("production_touched") is not False:
        return False
    return (
        payload.get("schema") == "edarsahub.worker-result.v2"
        or str(payload.get("status") or "") in VALID_RESULT_STATUSES
    )


def sanitize_repository_summary(summary: Any) -> tuple[dict[str, int] | None, bool]:
    if summary is None:
        return None, True
    if not isinstance(summary, dict):
        return None, False
    if len(summary) > len(ALLOWED_REPOSITORY_SUMMARY_KEYS):
        return None, False
    cleaned: dict[str, int] = {}
    for key, value in summary.items():
        if not isinstance(key, str) or key not in ALLOWED_REPOSITORY_SUMMARY_KEYS:
            return None, False
        if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 1_000_000:
            return None, False
        cleaned[key] = value
    return cleaned, True


def _sanitize_repo_entry_string(value: Any, *, max_length: int = 512, allow_empty: bool = False) -> str | None:
    if not isinstance(value, str) or "\x00" in value:
        return None
    stripped = value.strip()
    if not stripped and not allow_empty:
        return None
    if len(stripped) > max_length or has_sensitive_marker(stripped):
        return None
    return stripped


def sanitize_repository_contract_payload(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    raw_checks = value.get("checks")
    if isinstance(raw_checks, list):
        if not raw_checks or len(raw_checks) > MAX_CONTAINER_ITEMS:
            return None
        candidates = raw_checks
    elif (
        value.get("status") == "PASS"
        and value.get("mode") == "READ_ONLY_REPOSITORY"
        and isinstance(value.get("evidence"), list)
    ):
        candidates = [value]
    else:
        return None

    list_entry_keys = tuple(k for k in ALLOWED_REPOSITORY_ENTRY_KEYS if k not in {"path", "candidate_ownership"})
    sanitized_checks = []
    for check in candidates:
        if not isinstance(check, dict):
            return None
        if check.get("status") != "PASS" or check.get("mode") != "READ_ONLY_REPOSITORY":
            return None
        summary, summary_ok = sanitize_repository_summary(check.get("summary"))
        if not summary_ok:
            return None
        evidence = check.get("evidence")
        if not isinstance(evidence, list) or len(evidence) > MAX_CONTAINER_ITEMS:
            return None
        entries = []
        for entry in evidence:
            if not isinstance(entry, dict):
                return None
            clean_entry: dict[str, Any] = {}
            if "path" in entry:
                clean_path = _sanitize_repo_entry_string(entry.get("path"), max_length=512, allow_empty=False)
                if clean_path is None:
                    return None
                clean_entry["path"] = clean_path
            if "candidate_ownership" in entry:
                clean_owner = _sanitize_repo_entry_string(
                    entry.get("candidate_ownership"), max_length=128, allow_empty=True
                )
                if clean_owner is None:
                    return None
                clean_entry["candidate_ownership"] = clean_owner
            for list_key in list_entry_keys:
                if list_key not in entry:
                    continue
                raw_list = entry.get(list_key)
                if not isinstance(raw_list, list) or len(raw_list) > MAX_CONTAINER_ITEMS:
                    return None
                clean_list: list[str] = []
                for item in raw_list:
                    clean_item = _sanitize_repo_entry_string(item, max_length=256, allow_empty=False)
                    if clean_item is None:
                        return None
                    clean_list.append(clean_item)
                clean_entry[list_key] = clean_list
            entries.append(clean_entry)
        sanitized_checks.append({
            "status": "PASS",
            "mode": "READ_ONLY_REPOSITORY",
            "summary": summary,
            "truncated": bool(check.get("truncated")),
            "evidence": entries,
        })
    result = {"checks": sanitized_checks} if sanitized_checks else None
    if result is not None:
        encoded = json.dumps(result, ensure_ascii=False, sort_keys=True).encode("utf-8")
        if len(encoded) > MAX_SERIALIZED_BYTES:
            return None
    return result


def lookup_canonical_field(
    payload: dict[str, Any], field: str, *, decision_only: bool = False
) -> tuple[Any, bool]:
    if not isinstance(payload, dict):
        return None, True
    container_names = ("decision", "semantic_fields") if decision_only else ("semantic_fields", "decision", "deliverables")
    candidates: list[Any] = []
    if field in payload and payload.get(field) is not None:
        candidates.append(payload.get(field))
    for container_name in container_names:
        if container_name not in payload or payload.get(container_name) is None:
            continue
        container = payload.get(container_name)
        if not isinstance(container, dict):
            return None, True
        if field in container and container.get(field) is not None:
            candidates.append(container.get(field))
    if not candidates:
        return None, False
    first = candidates[0]
    for other in candidates[1:]:
        if type(other) is not type(first) or other != first:
            return None, True
    return first, False


def validate_decision_field(field: str, value: Any) -> Any:
    if field == "gate3_allowed":
        if not isinstance(value, bool):
            raise ValueError(f"INVALID_BOOLEAN_DECISION_FIELD:{field}")
        return value
    if field == "last_gate_certified":
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and "\x00" not in value:
            stripped = value.strip()
            if stripped and len(stripped) <= 256 and not has_sensitive_marker(stripped):
                return stripped
        raise ValueError("INVALID_LAST_GATE_CERTIFIED")
    if field == "real_implementation_percent":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("INVALID_PERCENT_TYPE")
        if math.isnan(float(value)) or math.isinf(float(value)) or float(value) < 0.0 or float(value) > 100.0:
            raise ValueError("INVALID_PERCENT_RANGE")
        return value
    if field == "blocking_reason_if_any":
        if not isinstance(value, str) or "\x00" in value:
            raise ValueError("INVALID_BLOCKING_REASON_TYPE")
        stripped = value.strip()
        if len(stripped) > 256 or has_sensitive_marker(stripped):
            raise ValueError("UNSAFE_OR_OVERSIZED_BLOCKING_REASON")
        return stripped
    if field in {"last_gate_executed", "next_allowed_gate"}:
        if not isinstance(value, str) or "\x00" in value:
            raise ValueError(f"INVALID_STRING_DECISION_FIELD:{field}")
        stripped = value.strip()
        if not stripped or len(stripped) > 256 or has_sensitive_marker(stripped):
            raise ValueError(f"UNSAFE_OR_OVERSIZED_DECISION_FIELD:{field}")
        return stripped
    raise ValueError(f"UNKNOWN_DECISION_FIELD:{field}")


def sanitize_dynamic_value(value: Any, *, depth: int = 0, max_str_len: int = MAX_STRING_LENGTH) -> Any:
    if depth > MAX_RECURSION_DEPTH:
        raise ValueError("MAX_RECURSION_DEPTH_EXCEEDED")
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        if abs(value) > 10**18:
            raise ValueError("INTEGER_OUT_OF_RANGE")
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValueError("NON_FINITE_FLOAT")
        return value
    if isinstance(value, str):
        if "\x00" in value or len(value) > max_str_len:
            raise ValueError("INVALID_OR_OVERSIZED_STRING")
        redacted = redact_sensitive_text(value, max_length=max_str_len).strip()
        if not redacted:
            raise ValueError("EMPTY_STRING_AFTER_SANITIZATION")
        return redacted
    if isinstance(value, list):
        if len(value) > MAX_CONTAINER_ITEMS:
            raise ValueError("LIST_TOO_LARGE")
        return [sanitize_dynamic_value(item, depth=depth + 1, max_str_len=max_str_len) for item in value]
    if isinstance(value, dict):
        if len(value) > MAX_CONTAINER_ITEMS:
            raise ValueError("DICT_TOO_LARGE")
        cleaned_dict: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not FIELD_NAME_RE.fullmatch(key):
                raise ValueError("INVALID_DICT_KEY")
            if is_sensitive_key(key):
                cleaned_dict[key] = "[REDACTED]"
            else:
                cleaned_dict[key] = sanitize_dynamic_value(item, depth=depth + 1, max_str_len=max_str_len)
        return cleaned_dict
    raise ValueError("UNSUPPORTED_DYNAMIC_TYPE")


def sanitize_provenance_entry(entry: Any) -> dict[str, Any]:
    if not isinstance(entry, dict):
        return {
            "status": "INVALID_OR_UNVERIFIED_EXPLICIT_VALUE",
            "source_key": None,
            "derivation": "FAIL_CLOSED_NULL",
        }
    status = entry.get("status")
    source_key = entry.get("source_key")
    derivation = entry.get("derivation")
    clean_status = status if isinstance(status, str) and status in ALLOWED_PROVENANCE_STATUSES else "INVALID_OR_UNVERIFIED_EXPLICIT_VALUE"
    clean_derivation = derivation if isinstance(derivation, str) and derivation in ALLOWED_PROVENANCE_DERIVATIONS else "FAIL_CLOSED_NULL"
    clean_source_key: str | None = None
    if isinstance(source_key, str) and FIELD_NAME_RE.fullmatch(source_key) and not is_sensitive_key(source_key):
        clean_source_key = source_key
    return {
        "status": clean_status,
        "source_key": clean_source_key,
        "derivation": clean_derivation,
    }


def resolve_semantic_field(payload: dict[str, Any], field: str) -> tuple[Any, dict[str, Any], bool]:
    if not FIELD_NAME_RE.fullmatch(field) or is_sensitive_key(field):
        return (
            None,
            {
                "status": "INVALID_OR_UNVERIFIED_EXPLICIT_VALUE",
                "source_key": None,
                "derivation": "FAIL_CLOSED_NULL",
            },
            False,
        )

    if field == "execution_base_sha":
        raw_val, raw_conflict = lookup_canonical_field(payload, "execution_base_sha", decision_only=True)
        base_sha = payload.get("base_sha")
        concurrency = payload.get("concurrency")
        if concurrency is not None and not isinstance(concurrency, dict):
            return (
                None,
                {
                    "status": "INVALID_OR_UNVERIFIED_EXPLICIT_VALUE",
                    "source_key": "execution_base_sha",
                    "derivation": "FAIL_CLOSED_NULL",
                },
                False,
            )
        pickup = concurrency.get("pickup") if isinstance(concurrency, dict) else None
        if pickup is not None and not isinstance(pickup, dict):
            return (
                None,
                {
                    "status": "INVALID_OR_UNVERIFIED_EXPLICIT_VALUE",
                    "source_key": "execution_base_sha",
                    "derivation": "FAIL_CLOSED_NULL",
                },
                False,
            )
        pickup_exec = pickup.get("execution_base_sha") if isinstance(pickup, dict) else None

        sha_candidates: list[str] = []
        for candidate in (raw_val, base_sha, pickup_exec):
            if candidate is None:
                continue
            if not isinstance(candidate, str) or not is_authentic_lineage_commit(candidate):
                status = "INVALID_OR_UNVERIFIED_EXPLICIT_VALUE" if raw_val is not None else "MISSING_OR_UNVERIFIED"
                source_key = "execution_base_sha" if raw_val is not None else None
                return (
                    None,
                    {
                        "status": status,
                        "source_key": source_key,
                        "derivation": "FAIL_CLOSED_NULL",
                    },
                    False,
                )
            sha_candidates.append(candidate.strip())

        if raw_conflict or len(set(sha_candidates)) > 1:
            status = "INVALID_OR_UNVERIFIED_EXPLICIT_VALUE" if raw_val is not None else "MISSING_OR_UNVERIFIED"
            source_key = "execution_base_sha" if raw_val is not None else None
            return (
                None,
                {
                    "status": status,
                    "source_key": source_key,
                    "derivation": "FAIL_CLOSED_NULL",
                },
                False,
            )

        if raw_val is not None:
            if has_verifiable_result_provenance(payload):
                return (
                    raw_val.strip(),
                    {
                        "status": "EXPLICIT_SOURCE_KEY",
                        "source_key": "execution_base_sha",
                        "derivation": "NONE",
                    },
                    True,
                )
            return (
                None,
                {
                    "status": "INVALID_OR_UNVERIFIED_EXPLICIT_VALUE",
                    "source_key": "execution_base_sha",
                    "derivation": "FAIL_CLOSED_NULL",
                },
                False,
            )
        if base_sha is not None and has_verifiable_result_provenance(payload):
            return (
                base_sha.strip(),
                {
                    "status": "DERIVED_CANONICAL_COMPATIBILITY",
                    "source_key": "base_sha",
                    "derivation": "PUBLISHED_WORKER_RESULT_BASE_SHA_INVARIANT",
                },
                False,
            )
        return (
            None,
            {
                "status": "MISSING_OR_UNVERIFIED",
                "source_key": None,
                "derivation": "FAIL_CLOSED_NULL",
            },
            False,
        )

    if field == "repository_evidence":
        raw_val, raw_conflict = lookup_canonical_field(payload, "repository_evidence", decision_only=False)
        if raw_conflict:
            return (
                None,
                {
                    "status": "INVALID_OR_UNVERIFIED_EXPLICIT_VALUE",
                    "source_key": "repository_evidence",
                    "derivation": "FAIL_CLOSED_NULL",
                },
                False,
            )
        if raw_val is not None:
            sanitized = sanitize_repository_contract_payload(raw_val)
            if sanitized is not None and has_verifiable_result_provenance(payload):
                return (
                    sanitized,
                    {
                        "status": "EXPLICIT_SOURCE_KEY",
                        "source_key": "repository_evidence",
                        "derivation": "NONE",
                    },
                    True,
                )
            return (
                None,
                {
                    "status": "INVALID_OR_UNVERIFIED_EXPLICIT_VALUE",
                    "source_key": "repository_evidence",
                    "derivation": "FAIL_CLOSED_NULL",
                },
                False,
            )
        sanitized = sanitize_repository_contract_payload(payload.get("repository_contract_evidence"))
        if sanitized is not None and has_verifiable_result_provenance(payload):
            return (
                sanitized,
                {
                    "status": "DERIVED_CANONICAL_COMPATIBILITY",
                    "source_key": "repository_contract_evidence",
                    "derivation": "PUBLISHED_SANITIZED_REPOSITORY_CONTRACT_EVIDENCE",
                },
                False,
            )
        return (
            None,
            {
                "status": "MISSING_OR_UNVERIFIED",
                "source_key": None,
                "derivation": "FAIL_CLOSED_NULL",
            },
            False,
        )

    is_decision = field in DECISION_FIELDS
    raw_val, raw_conflict = lookup_canonical_field(payload, field, decision_only=is_decision)
    if raw_conflict:
        return (
            None,
            {
                "status": "INVALID_OR_UNVERIFIED_EXPLICIT_VALUE",
                "source_key": field,
                "derivation": "FAIL_CLOSED_NULL",
            },
            False,
        )
    if raw_val is not None:
        try:
            if is_decision:
                sanitized_val = validate_decision_field(field, raw_val)
            elif field == "certification_basis":
                if not isinstance(raw_val, str) or not CERTIFICATION_BASIS_RE.fullmatch(raw_val.strip()) or has_sensitive_marker(raw_val):
                    raise ValueError("INVALID_CERTIFICATION_BASIS")
                sanitized_val = raw_val.strip()
            elif field == "summary_es":
                sanitized_val = sanitize_dynamic_value(raw_val, max_str_len=MAX_SUMMARY_LENGTH)
                if not isinstance(sanitized_val, str):
                    raise ValueError("INVALID_SUMMARY_ES")
            else:
                sanitized_val = sanitize_dynamic_value(raw_val)
            encoded = json.dumps(sanitized_val, ensure_ascii=False, sort_keys=True).encode("utf-8")
            if len(encoded) > MAX_SERIALIZED_BYTES:
                raise ValueError("SERIALIZED_FIELD_TOO_LARGE")
        except (ValueError, TypeError):
            return (
                None,
                {
                    "status": "INVALID_OR_UNVERIFIED_EXPLICIT_VALUE",
                    "source_key": field,
                    "derivation": "FAIL_CLOSED_NULL",
                },
                False,
            )
        return (
            sanitized_val,
            {
                "status": "EXPLICIT_SOURCE_KEY",
                "source_key": field,
                "derivation": "NONE",
            },
            True,
        )
    return (
        None,
        {
            "status": "MISSING_IN_SOURCE",
            "source_key": None,
            "derivation": "FAIL_CLOSED_DEFAULT" if field in DECISION_FIELDS else "FAIL_CLOSED_NULL",
        },
        False,
    )


def _sanitize_short_label(value: Any, *, default: str = "") -> str | None:
    if not isinstance(value, str) or "\x00" in value:
        return default or None
    cleaned = redact_sensitive_text(value.strip(), max_length=256)
    return cleaned if cleaned else (default or None)


def build_report(payload: dict[str, Any], request: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    requested = request.get("required_semantic_fields")
    if not isinstance(requested, list) or not requested:
        requested = DEFAULT_FIELDS

    requested_clean: list[str] = []
    invalid_requested_field = False
    for item in requested[:MAX_CONTAINER_ITEMS]:
        if isinstance(item, str) and FIELD_NAME_RE.fullmatch(item.strip()) and not is_sensitive_key(item.strip()):
            requested_clean.append(item.strip())
        else:
            invalid_requested_field = True

    fields = list(dict.fromkeys([*DEFAULT_FIELDS, *requested_clean]))
    raw_semantic_fields: dict[str, Any] = {}
    semantic_field_provenance: dict[str, dict[str, Any]] = {}
    source_explicit_missing: list[str] = []

    for field in fields:
        field_name = str(field)
        val, prov, is_explicit = resolve_semantic_field(payload, field_name)
        raw_semantic_fields[field_name] = val
        semantic_field_provenance[field_name] = sanitize_provenance_entry(prov)
        if not is_explicit:
            source_explicit_missing.append(field_name)

    source_explicit_missing.sort()
    source_missing = sorted(key for key, value in raw_semantic_fields.items() if value is None)
    decision_explicit_complete = all(
        raw_semantic_fields.get(key) is not None
        and semantic_field_provenance.get(key, {}).get("status") == "EXPLICIT_SOURCE_KEY"
        for key in DECISION_FIELDS
    )
    source_semantic_complete = bool(
        not invalid_requested_field and not source_missing and decision_explicit_complete
    )

    semantic_fields = dict(raw_semantic_fields)
    if not source_semantic_complete:
        fallback_gate = (
            _sanitize_short_label(payload.get("job_id"))
            or _sanitize_short_label(payload.get("status"))
            or "UNKNOWN_SOURCE_RESULT"
        )
        fail_closed = {
            "gate3_allowed": False,
            "last_gate_executed": fallback_gate,
            "last_gate_certified": False,
            "real_implementation_percent": None,
            "next_allowed_gate": "GATE3_HOLD_PENDING_EXPLICIT_SEMANTIC_FIELDS",
            "blocking_reason_if_any": "SOURCE_SEMANTIC_FIELDS_MISSING",
        }
        for key, value in fail_closed.items():
            if semantic_fields.get(key) is None:
                semantic_fields[key] = value
        semantic_fields["gate3_allowed"] = False

    raw_blockers = payload.get("blockers")
    if isinstance(raw_blockers, list):
        source_blockers = [
            redact_sensitive_text(str(item), max_length=256)
            for item in raw_blockers[:MAX_CONTAINER_ITEMS]
            if item is not None
        ]
        blockers_valid = True
    elif raw_blockers is None:
        source_blockers = []
        blockers_valid = True
    else:
        source_blockers = ["INVALID_SOURCE_BLOCKERS_FORMAT"]
        blockers_valid = False

    raw_files_changed = payload.get("files_changed")
    if isinstance(raw_files_changed, list):
        source_files_changed = [
            redact_sensitive_text(str(item), max_length=512)
            for item in raw_files_changed[:MAX_CONTAINER_ITEMS]
            if isinstance(item, str) and item.strip()
        ]
    else:
        source_files_changed = []

    source_pass = (
        str(payload.get("tests") or "").upper() == "PASS"
        and str(payload.get("quality_gate") or "").upper() == "PASS"
        and payload.get("production_touched") is False
        and blockers_valid
        and not source_blockers
    )
    gate3_allowed = bool(source_pass and source_semantic_complete and truthy(raw_semantic_fields.get("gate3_allowed")))
    if not gate3_allowed:
        semantic_fields["gate3_allowed"] = False

    if not source_semantic_complete:
        bridge_verdict = "SOURCE_SEMANTIC_FIELDS_DERIVED_FAIL_CLOSED"
    elif gate3_allowed:
        bridge_verdict = "SOURCE_SEMANTIC_FIELDS_COMPLETE_GATE3_ALLOWED"
    else:
        bridge_verdict = "SOURCE_SEMANTIC_FIELDS_COMPLETE_GATE3_HOLD"

    missing = [] if not source_semantic_complete else sorted(key for key, value in semantic_fields.items() if value is None)
    semantic_complete = not missing and not invalid_requested_field

    if gate3_allowed:
        next_allowed_step = "GATE3_PREP_ALLOWED"
    elif not source_semantic_complete:
        next_allowed_step = "GATE3_HOLD_PENDING_EXPLICIT_SEMANTIC_FIELDS"
    else:
        next_allowed_step = "GATE3_HOLD_SEMANTIC_FIELDS_COMPLETE_NOT_ALLOWED"

    source_percent = payload.get("percent_complete")
    if isinstance(source_percent, bool) or not isinstance(source_percent, (int, float)) or math.isnan(float(source_percent)) or math.isinf(float(source_percent)):
        source_percent = None

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
        "source_explicit_missing_semantic_fields": source_explicit_missing,
        "semantic_field_provenance": semantic_field_provenance,
        "semantic_fields_complete": semantic_complete,
        "missing_semantic_fields": missing,
        "semantic_fields": semantic_fields,
        "gate3_allowed": gate3_allowed,
        "source_status": _sanitize_short_label(payload.get("status")),
        "source_quality_gate": _sanitize_short_label(payload.get("quality_gate")),
        "source_certification": _sanitize_short_label(payload.get("certification")),
        "source_work_completion": _sanitize_short_label(payload.get("work_completion")),
        "source_percent_complete": source_percent,
        "source_production_touched": payload.get("production_touched") if isinstance(payload.get("production_touched"), bool) else None,
        "source_files_changed": source_files_changed,
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
