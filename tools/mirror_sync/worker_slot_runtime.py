"""Canonical Universal Worker slot runtime.

Gate4B1 foundation defines the runtime contract but does not enable
parallel execution. Effective capacity remains READ_ONLY=1, MUTATION=1.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
STATE = ROOT / ".git" / "universal-worker-queue"
RUNTIME = STATE / "runtime"

SCHEMA = "edarsahub.worker-slot-runtime.v1"

SLOT_IDS = (
    "readonly-1",
    "readonly-2",
    "readonly-3",
    "readonly-4",
    "mutation-1",
)

GATE4B1_EFFECTIVE_SLOT_IDS = (
    "readonly-1",
    "mutation-1",
)

SLOT_CLASSES = {
    "READ_ONLY",
    "MUTATION",
}

SLOT_STATES = {
    "CLAIMED",
    "RUNNING",
    "TERMINALIZING",
}

JOB_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,255}$")


class SlotRuntimeError(RuntimeError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_utc(value: Any) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise SlotRuntimeError("SLOT_TIMESTAMP_REQUIRED")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SlotRuntimeError("SLOT_TIMESTAMP_INVALID") from exc
    if parsed.tzinfo is None:
        raise SlotRuntimeError("SLOT_TIMESTAMP_TIMEZONE_REQUIRED")
    return parsed.astimezone(timezone.utc)


def slots_directory() -> Path:
    return RUNTIME / "slots"


def _validate_slot_id(slot_id: str) -> str:
    value = str(slot_id or "").strip()
    if value not in SLOT_IDS:
        raise SlotRuntimeError("SLOT_ID_INVALID")
    return value


def slot_path(slot_id: str) -> Path:
    return slots_directory() / f"{_validate_slot_id(slot_id)}.json"


def _validate_string(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise SlotRuntimeError(f"{field.upper()}_INVALID")
    return text


def _validate_pid(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise SlotRuntimeError(f"{field.upper()}_INVALID")
    try:
        pid = int(value)
    except (TypeError, ValueError) as exc:
        raise SlotRuntimeError(f"{field.upper()}_INVALID") from exc
    if pid < 0:
        raise SlotRuntimeError(f"{field.upper()}_INVALID")
    return pid


def _validate_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise SlotRuntimeError(f"{field.upper()}_INVALID")
    result = []
    for item in value:
        text = str(item or "").strip()
        if not text:
            raise SlotRuntimeError(f"{field.upper()}_INVALID")
        result.append(text)
    return result


def _validate_payload(
    slot_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise SlotRuntimeError("SLOT_PAYLOAD_INVALID")

    expected_slot_id = _validate_slot_id(slot_id)

    if payload.get("schema") != SCHEMA:
        raise SlotRuntimeError("SLOT_SCHEMA_INVALID")

    if payload.get("slot_id") != expected_slot_id:
        raise SlotRuntimeError("SLOT_ID_MISMATCH")

    slot_class = str(payload.get("slot_class") or "").strip()
    if slot_class not in SLOT_CLASSES:
        raise SlotRuntimeError("SLOT_CLASS_INVALID")

    state = str(payload.get("state") or "").strip()
    if state not in SLOT_STATES:
        raise SlotRuntimeError("SLOT_STATE_INVALID")

    job_id = str(payload.get("job_id") or "").strip()
    if not JOB_ID_RE.fullmatch(job_id):
        raise SlotRuntimeError("JOB_ID_INVALID")

    _validate_string(payload.get("mode"), "mode")
    _validate_string(payload.get("project_id"), "project_id")
    _validate_string(payload.get("bounded_context"), "bounded_context")

    _validate_string_list(
        payload.get("resource_claims"),
        "resource_claims",
    )
    _validate_string_list(
        payload.get("conflict_domains"),
        "conflict_domains",
    )

    _parse_utc(payload.get("claimed_at_utc"))
    _parse_utc(payload.get("heartbeat_at_utc"))

    _validate_pid(payload.get("worker_pid"), "worker_pid")
    _validate_pid(payload.get("execution_pid"), "execution_pid")

    if not isinstance(payload.get("legacy_defaults"), bool):
        raise SlotRuntimeError("LEGACY_DEFAULTS_INVALID")

    return dict(payload)


def atomic_slot_write(
    slot_id: str,
    payload: dict[str, Any],
) -> None:
    path = slot_path(slot_id)
    validated = _validate_payload(slot_id, payload)
    path.parent.mkdir(parents=True, exist_ok=True)

    temp_name = None

    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            delete=False,
        ) as handle:
            json.dump(
                validated,
                handle,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            temp_name = handle.name

        os.replace(temp_name, path)

    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def load_slot(slot_id: str) -> dict[str, Any] | None:
    path = slot_path(slot_id)

    if not path.exists():
        return None

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SlotRuntimeError("CORRUPT_SLOT_RUNTIME") from exc

    return _validate_payload(slot_id, value)


def load_active_slots() -> list[dict[str, Any]]:
    directory = slots_directory()

    if not directory.exists():
        return []

    rows = []

    for path in sorted(directory.glob("*.json")):
        slot_id = path.stem

        if slot_id not in SLOT_IDS:
            raise SlotRuntimeError("UNKNOWN_SLOT_RUNTIME_FILE")

        slot = load_slot(slot_id)

        if slot is not None:
            rows.append(slot)

    return rows


def reclaim_stale_slot(
    slot_id: str,
    *,
    heartbeat_stale_seconds: int,
) -> dict[str, Any]:
    existing = load_slot(slot_id)
    if existing is None:
        return {
            "reclaimed": False,
            "reason": "EMPTY",
            "slot_id": slot_id,
        }

    if slot_is_live(
        existing,
        heartbeat_stale_seconds=heartbeat_stale_seconds,
    ):
        return {
            "reclaimed": False,
            "reason": "LIVE",
            "slot_id": slot_id,
            "job_id": existing["job_id"],
            "state": existing["state"],
        }

    stale_job_id = existing["job_id"]
    stale_state = existing["state"]
    release_slot(slot_id)
    return {
        "reclaimed": True,
        "reason": "STALE",
        "slot_id": slot_id,
        "job_id": stale_job_id,
        "state": stale_state,
    }


def create_slot(
    *,
    slot_id: str,
    slot_class: str,
    job_id: str,
    mode: str,
    project_id: str,
    bounded_context: str,
    resource_claims: list[str],
    conflict_domains: list[str],
    worker_pid: int,
    execution_pid: int = 0,
    legacy_defaults: bool,
) -> dict[str, Any]:
    path = slot_path(slot_id)
    if path.exists():
        raise SlotRuntimeError("SLOT_ALREADY_CLAIMED")

    now = _utc_now()

    payload = {
        "schema": SCHEMA,
        "slot_id": slot_id,
        "slot_class": slot_class,
        "job_id": job_id,
        "mode": mode,
        "project_id": project_id,
        "bounded_context": bounded_context,
        "resource_claims": list(resource_claims),
        "conflict_domains": list(conflict_domains),
        "claimed_at_utc": now,
        "heartbeat_at_utc": now,
        "worker_pid": worker_pid,
        "execution_pid": execution_pid,
        "state": "CLAIMED",
        "legacy_defaults": legacy_defaults,
    }

    atomic_slot_write(slot_id, payload)
    return payload


def heartbeat_slot(
    slot_id: str,
    *,
    execution_pid: int | None = None,
) -> dict[str, Any]:
    payload = load_slot(slot_id)

    if payload is None:
        raise SlotRuntimeError("SLOT_NOT_FOUND")

    payload["heartbeat_at_utc"] = _utc_now()

    if execution_pid is not None:
        payload["execution_pid"] = execution_pid

    atomic_slot_write(slot_id, payload)
    return payload


def update_slot_state(
    slot_id: str,
    state: str,
    *,
    execution_pid: int | None = None,
) -> dict[str, Any]:
    payload = load_slot(slot_id)

    if payload is None:
        raise SlotRuntimeError("SLOT_NOT_FOUND")

    payload["state"] = state
    payload["heartbeat_at_utc"] = _utc_now()

    if execution_pid is not None:
        payload["execution_pid"] = execution_pid

    atomic_slot_write(slot_id, payload)
    return payload


def release_slot(slot_id: str) -> None:
    path = slot_path(slot_id)

    if not path.exists():
        return

    # Validate before release. Corrupt runtime must fail closed.
    load_slot(slot_id)
    path.unlink()


def derive_legacy_current_job_id(
    slots: list[dict[str, Any]] | None = None,
) -> str | None:
    active = load_active_slots() if slots is None else list(slots)

    if not active:
        return None

    if len(active) != 1:
        raise SlotRuntimeError(
            "LEGACY_CURRENT_JOB_PROJECTION_CONFLICT"
        )

    return str(active[0]["job_id"])


def slot_is_live(
    slot: dict[str, Any],
    *,
    heartbeat_stale_seconds: int,
) -> bool:
    _validate_payload(str(slot.get("slot_id") or ""), slot)

    heartbeat = _parse_utc(slot["heartbeat_at_utc"])
    age = (
        datetime.now(timezone.utc) - heartbeat
    ).total_seconds()

    if age > heartbeat_stale_seconds:
        return False

    pid = _validate_pid(slot["execution_pid"], "execution_pid")

    if slot["state"] == "RUNNING":
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except OSError:
            return False

    return True


def slot_runtime_summary() -> dict[str, Any]:
    slots = load_active_slots()

    readonly = [
        slot
        for slot in slots
        if slot["slot_class"] == "READ_ONLY"
    ]

    mutation = [
        slot
        for slot in slots
        if slot["slot_class"] == "MUTATION"
    ]

    return {
        "active_slots": len(slots),
        "readonly_slots_active": len(readonly),
        "readonly_slots_capacity": 1,
        "mutation_slots_active": len(mutation),
        "mutation_slots_capacity": 1,
        "slot_job_ids": [
            slot["job_id"]
            for slot in slots
        ],
        "slot_states": {
            slot["slot_id"]: slot["state"]
            for slot in slots
        },
    }
