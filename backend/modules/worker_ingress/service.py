"""Service boundary for remote Universal Worker submission and status.

This module is intentionally thin. It does not implement another queue,
publisher, scheduler, Git client, SQL executor or Worker. Submission is
delegated to the existing canonical job factory and gate-chain publisher.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from tools.mirror_sync import gate_chain_publisher
from tools.mirror_sync.worker_job_factory import canonicalize_job
from tools.mirror_sync.worker_result_reader import read_canonical_result
from tools.mirror_sync.worker_result_status import build_job_status


REPO_ROOT = Path(__file__).resolve().parents[3]
STATE_ROOT = REPO_ROOT / ".git" / "universal-worker-queue"
JOB_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$")

_SENSITIVE_KEYS = {
    "password",
    "password_decrypted",
    "secret",
    "secrets",
    "token",
    "credentials",
    "credential",
    "api_key",
    "apikey",
}

_SAFE_RESULT_KEYS = {
    "status",
    "quality_gate",
    "certification",
    "tests",
    "percent_complete",
    "blockers",
    "files_changed",
    "commit_sha",
    "integrated_commit",
    "git_sync_status",
    "production_touched",
    "completed_at_utc",
    "summary_es",
}


class WorkerIngressError(ValueError):
    pass


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _assert_no_sensitive_keys(value: Any, path: str = "request") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).strip().lower()
            if normalized in _SENSITIVE_KEYS:
                raise WorkerIngressError(f"SENSITIVE_FIELD_FORBIDDEN:{path}.{key}")
            _assert_no_sensitive_keys(nested, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _assert_no_sensitive_keys(nested, f"{path}[{index}]")


def _requester_from_authenticated_user(
    current_user: Mapping[str, Any],
    *,
    project: str,
) -> dict[str, str]:
    email = _clean(current_user.get("email")).lower()
    if not email or "@" not in email:
        raise WorkerIngressError("AUTHENTICATED_REQUESTER_EMAIL_REQUIRED")

    return {
        "email": email,
        "source": "edarsahub-worker-ingress",
        "project": _clean(project) or "EDARSAHUB",
        "chat": "remote-canonical-ingress",
    }


def build_canonical_job(
    request_payload: Mapping[str, Any],
    *,
    current_user: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(request_payload)
    _assert_no_sensitive_keys(payload)

    scheduling = payload.get("scheduling")
    scheduling = dict(scheduling) if isinstance(scheduling, Mapping) else {}

    requester = _requester_from_authenticated_user(
        current_user,
        project=_clean(scheduling.get("project_id")) or "EDARSAHUB",
    )

    raw_job = {
        "job_id": payload.get("job_id"),
        "objective": payload.get("objective"),
        "mode": payload.get("mode"),
        "actions": list(payload.get("actions") or []),
        "checks": list(payload.get("checks") or []),
        "requester": requester,
    }
    if scheduling:
        raw_job["scheduling"] = scheduling

    return canonicalize_job(raw_job)


def submit_job(
    request_payload: Mapping[str, Any],
    *,
    current_user: Mapping[str, Any],
) -> dict[str, Any]:
    """Submit only through the existing canonical publisher."""
    canonical_job = build_canonical_job(
        request_payload,
        current_user=current_user,
    )
    result = gate_chain_publisher.submit(canonical_job)
    if not isinstance(result, dict):
        raise WorkerIngressError("CANONICAL_PUBLISHER_INVALID_RESPONSE")

    safe = dict(result)
    safe["job_id"] = _clean(result.get("job_id")) or canonical_job["job_id"]
    safe["production_touched"] = bool(result.get("production_touched", False))
    safe.pop("template", None)
    return safe


def _read_json_if_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_terminal_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: payload.get(key)
        for key in _SAFE_RESULT_KEYS
        if key in payload
    }


def get_job_status(job_id: str) -> dict[str, Any]:
    value = _clean(job_id)
    if not JOB_ID_RE.fullmatch(value):
        raise WorkerIngressError("JOB_ID_INVALID")

    result_path = STATE_ROOT / "results" / f"{value}.json"
    if result_path.is_file():
        result_read = read_canonical_result(
            result_path,
            expected_job_id=value,
        )
        status = build_job_status(result_read=result_read)
        payload = result_read.payload or {}
        status.update(_safe_terminal_fields(payload))
        status["lifecycle"] = "RESULT"
        return status

    lifecycle_dirs = (
        ("PROCESSING", "processing"),
        ("PENDING", "pending"),
        ("PUBLISHED", "published"),
        ("DONE", "done"),
        ("REJECTED", "rejected"),
        ("DRAFT", "drafts"),
    )

    for lifecycle, directory in lifecycle_dirs:
        path = STATE_ROOT / directory / f"{value}.json"
        if not path.is_file():
            continue
        payload = _read_json_if_object(path)
        response = {
            "job_id": value,
            "lifecycle": lifecycle,
            "status": payload.get("status") or lifecycle,
            "production_touched": bool(payload.get("production_touched", False)),
        }
        response.update(_safe_terminal_fields(payload))
        return response

    return {
        "job_id": value,
        "lifecycle": "NOT_FOUND",
        "status": "NOT_FOUND",
        "production_touched": False,
    }
