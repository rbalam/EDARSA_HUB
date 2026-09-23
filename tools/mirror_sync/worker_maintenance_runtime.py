"""Operational runtime for Worker Repair / Worker Auditor.

This module is intentionally narrow:
- worker infrastructure incidents only
- no application-domain mutation
- no Production
- bounded attempts
- cooldown after terminal failure
- atomic local maintenance state
- repair never self-certifies
- auditor never mutates
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tools.mirror_sync.worker_maintenance_controller import (
    MaintenanceDecision,
    MaintenanceIncident,
    MaintenanceState,
    audit_incident,
    declare_incident,
    repaired_pending_audit,
    repair_plan_for,
)

ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = ROOT / ".git" / "universal-worker-queue" / "maintenance"
INCIDENT_DIR = STATE_DIR / "incidents"

MAX_REPAIR_ATTEMPTS = 2
REPAIR_COOLDOWN_SECONDS = 300


@dataclass(frozen=True)
class RuntimeIncidentState:
    incident_id: str
    state: str
    attempts: int
    cooldown_until_epoch: float | None
    target_paths: tuple[str, ...]
    production_touched: bool = False


def _incident_path(incident_id: str) -> Path:
    safe = str(incident_id or "").strip()
    if not safe:
        raise ValueError("MAINTENANCE_INCIDENT_ID_REQUIRED")
    return INCIDENT_DIR / f"{safe}.json"


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        temp_name = handle.name
    os.replace(temp_name, path)


def _load_state(incident_id: str) -> dict[str, Any] | None:
    path = _incident_path(incident_id)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("MAINTENANCE_STATE_INVALID")
    return data


def declare_runtime_incident(
    incident_id: str,
    target_paths: list[str],
) -> RuntimeIncidentState:
    existing = _load_state(incident_id)

    if existing is not None:
        existing_paths = tuple(existing.get("target_paths") or [])
        requested_paths = tuple(sorted(set(target_paths)))

        if existing_paths != requested_paths:
            raise ValueError("MAINTENANCE_INCIDENT_SCOPE_MISMATCH")

        return RuntimeIncidentState(
            incident_id=incident_id,
            state=str(existing.get("state")),
            attempts=int(existing.get("attempts") or 0),
            cooldown_until_epoch=existing.get("cooldown_until_epoch"),
            target_paths=existing_paths,
            production_touched=bool(existing.get("production_touched")),
        )

    incident = declare_incident(incident_id, target_paths)

    payload = {
        "incident_id": incident.incident_id,
        "state": incident.state.value,
        "attempts": 0,
        "cooldown_until_epoch": None,
        "target_paths": list(incident.paths),
        "production_touched": False,
    }
    _atomic_json(_incident_path(incident_id), payload)

    return RuntimeIncidentState(
        incident_id=incident.incident_id,
        state=incident.state.value,
        attempts=0,
        cooldown_until_epoch=None,
        target_paths=tuple(incident.paths),
        production_touched=False,
    )


def repair_attempt_allowed(
    incident_id: str,
    *,
    now_epoch: float | None = None,
) -> tuple[bool, str]:
    state = _load_state(incident_id)
    if state is None:
        return False, "INCIDENT_NOT_DECLARED"

    now_value = time.time() if now_epoch is None else float(now_epoch)

    cooldown_until = state.get("cooldown_until_epoch")
    if cooldown_until is not None and now_value < float(cooldown_until):
        return False, "REPAIR_COOLDOWN_ACTIVE"

    attempts = int(state.get("attempts") or 0)
    if attempts >= MAX_REPAIR_ATTEMPTS:
        return False, "REPAIR_ATTEMPTS_EXHAUSTED"

    if state.get("state") not in {
        MaintenanceState.REPAIR_REQUIRED.value,
        MaintenanceState.REJECTED.value,
    }:
        return False, "INCIDENT_NOT_REPAIRABLE"

    return True, "REPAIR_ALLOWED"


def register_repair_attempt(
    incident_id: str,
    *,
    now_epoch: float | None = None,
) -> RuntimeIncidentState:
    allowed, reason = repair_attempt_allowed(
        incident_id,
        now_epoch=now_epoch,
    )
    if not allowed:
        raise ValueError(reason)

    state = _load_state(incident_id)
    assert state is not None

    attempts = int(state.get("attempts") or 0) + 1
    state["attempts"] = attempts
    state["state"] = MaintenanceState.REPAIR_REQUIRED.value

    _atomic_json(_incident_path(incident_id), state)

    return RuntimeIncidentState(
        incident_id=incident_id,
        state=str(state["state"]),
        attempts=attempts,
        cooldown_until_epoch=state.get("cooldown_until_epoch"),
        target_paths=tuple(state.get("target_paths") or []),
        production_touched=False,
    )


def register_repair_result(
    incident_id: str,
    repair_result: dict[str, Any],
    *,
    now_epoch: float | None = None,
) -> MaintenanceDecision:
    state = _load_state(incident_id)
    if state is None:
        raise ValueError("INCIDENT_NOT_DECLARED")

    incident = MaintenanceIncident(
        incident_id=incident_id,
        paths=tuple(state.get("target_paths") or []),
        state=MaintenanceState.REPAIR_REQUIRED,
        production_allowed=False,
    )

    decision = repaired_pending_audit(
        incident,
        repair_result,
    )

    state["state"] = decision.state.value
    state["production_touched"] = bool(
        repair_result.get("production_touched")
    )

    if decision.state is MaintenanceState.REJECTED:
        now_value = time.time() if now_epoch is None else float(now_epoch)
        state["cooldown_until_epoch"] = (
            now_value + REPAIR_COOLDOWN_SECONDS
        )
    else:
        state["cooldown_until_epoch"] = None

    _atomic_json(_incident_path(incident_id), state)
    return decision


def audit_runtime_incident(
    incident_id: str,
    repair_result: dict[str, Any],
) -> MaintenanceDecision:
    state = _load_state(incident_id)
    if state is None:
        raise ValueError("INCIDENT_NOT_DECLARED")

    incident = MaintenanceIncident(
        incident_id=incident_id,
        paths=tuple(state.get("target_paths") or []),
        state=MaintenanceState.REPAIRED_PENDING_AUDIT,
        production_allowed=False,
    )

    decision = audit_incident(
        incident,
        repair_result,
    )

    state["state"] = decision.state.value
    state["production_touched"] = bool(
        repair_result.get("production_touched")
    )

    _atomic_json(_incident_path(incident_id), state)
    return decision


def read_runtime_incident(
    incident_id: str,
) -> RuntimeIncidentState | None:
    state = _load_state(incident_id)
    if state is None:
        return None

    return RuntimeIncidentState(
        incident_id=incident_id,
        state=str(state.get("state")),
        attempts=int(state.get("attempts") or 0),
        cooldown_until_epoch=state.get("cooldown_until_epoch"),
        target_paths=tuple(state.get("target_paths") or []),
        production_touched=bool(state.get("production_touched")),
    )
