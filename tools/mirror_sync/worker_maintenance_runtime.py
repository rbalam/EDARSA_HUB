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
import subprocess
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


def _canonical_git_common_dir(root: Path) -> Path:
    """Resolve the shared Git common dir for checkout or linked worktree."""
    proc = subprocess.run(
        [
            "git",
            "rev-parse",
            "--path-format=absolute",
            "--git-common-dir",
        ],
        cwd=str(root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )

    value = proc.stdout.strip()

    if proc.returncode != 0 or not value:
        raise RuntimeError("MAINTENANCE_GIT_COMMON_DIR_UNAVAILABLE")

    path = Path(value)

    if not path.is_absolute():
        path = (root / path).resolve()

    return path


GIT_COMMON_DIR = _canonical_git_common_dir(ROOT)
STATE_DIR = (
    GIT_COMMON_DIR
    / "universal-worker-queue"
    / "maintenance"
)
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
    repair_job_id: str | None = None
    repair_publication_state: str | None = None
    repair_publication_commit: str | None = None
    repair_result_sha256: str | None = None
    repair_commit_sha: str | None = None


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


def _build_runtime_state(
    incident_id: str,
    state: dict[str, Any],
) -> RuntimeIncidentState:
    return RuntimeIncidentState(
        incident_id=incident_id,
        state=str(state.get("state")),
        attempts=int(state.get("attempts") or 0),
        cooldown_until_epoch=state.get("cooldown_until_epoch"),
        target_paths=tuple(state.get("target_paths") or []),
        production_touched=bool(state.get("production_touched")),
        repair_job_id=state.get("repair_job_id"),
        repair_publication_state=state.get(
            "repair_publication_state"
        ),
        repair_publication_commit=state.get(
            "repair_publication_commit"
        ),
        repair_result_sha256=state.get(
            "repair_result_sha256"
        ),
        repair_commit_sha=state.get(
            "repair_commit_sha"
        ),
    )


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

        return _build_runtime_state(
            incident_id,
            existing,
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
        repair_job_id=None,
        repair_publication_state=None,
        repair_publication_commit=None,
        repair_result_sha256=None,
        repair_commit_sha=None,
    )


def supersede_runtime_incident(
    incident_id: str,
    *,
    reason: str = "SUPERSEDED_BY_CURRENT_HEAD",
) -> RuntimeIncidentState:
    state = _load_state(incident_id)

    if state is None:
        raise ValueError("MAINTENANCE_INCIDENT_NOT_FOUND")

    if state.get("state") != MaintenanceState.REPAIR_REQUIRED.value:
        raise ValueError("MAINTENANCE_SUPERSESSION_INVALID_STATE")

    state["state"] = MaintenanceState.SUPERSEDED.value
    state["cooldown_until_epoch"] = None
    state["superseded_reason"] = str(reason or "").strip()

    _atomic_json(
        _incident_path(incident_id),
        state,
    )

    return _build_runtime_state(
        incident_id,
        state,
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
    state["cooldown_until_epoch"] = None

    _atomic_json(_incident_path(incident_id), state)

    return _build_runtime_state(
        incident_id,
        state,
    )


def register_published_repair_attempt(
    incident_id: str,
    repair_job_id: str,
    publication_evidence: dict[str, Any],
    *,
    now_epoch: float | None = None,
) -> RuntimeIncidentState:
    state = _load_state(incident_id)
    if state is None:
        raise ValueError("INCIDENT_NOT_DECLARED")

    job_id = str(repair_job_id or "").strip()
    if not job_id:
        raise ValueError("REPAIR_JOB_ID_REQUIRED")

    publication_status = str(
        publication_evidence.get("status") or ""
    ).strip()

    if publication_status not in {"PUBLISHED", "EXISTS"}:
        raise ValueError("REPAIR_PUBLICATION_NOT_COMMITTED")

    existing_job_id = str(
        state.get("repair_job_id") or ""
    ).strip()

    if existing_job_id:
        if existing_job_id != job_id:
            raise ValueError("REPAIR_JOB_BINDING_MISMATCH")

        return _build_runtime_state(
            incident_id,
            state,
        )

    allowed, reason = repair_attempt_allowed(
        incident_id,
        now_epoch=now_epoch,
    )

    if not allowed:
        raise ValueError(reason)

    attempts = int(state.get("attempts") or 0) + 1

    state["attempts"] = attempts
    state["state"] = MaintenanceState.REPAIR_REQUIRED.value
    state["cooldown_until_epoch"] = None
    state["repair_job_id"] = job_id
    state["repair_publication_state"] = publication_status

    commit_sha = publication_evidence.get("commit_sha")
    state["repair_publication_commit"] = (
        str(commit_sha).strip()
        if commit_sha
        else None
    )

    _atomic_json(
        _incident_path(incident_id),
        state,
    )

    return _build_runtime_state(
        incident_id,
        state,
    )


def _archive_rejected_attempt(
    state: dict[str, Any],
    *,
    now_epoch: float | None = None,
    reason: str | None = None,
) -> None:
    history = state.get(
        "repair_job_history"
    )

    if not isinstance(history, list):
        history = []

    current_job_id = str(
        state.get("repair_job_id")
        or ""
    ).strip()

    if current_job_id:
        already_archived = any(
            isinstance(item, dict)
            and str(
                item.get("job_id")
                or ""
            ).strip()
            == current_job_id
            for item in history
        )

        if not already_archived:
            entry: dict[str, Any] = {
                "job_id": current_job_id,
                "attempt": int(
                    state.get("attempts")
                    or 0
                ),
                "publication_state": (
                    state.get(
                        "repair_publication_state"
                    )
                ),
                "publication_commit": (
                    state.get(
                        "repair_publication_commit"
                    )
                ),
                "terminal_state": (
                    MaintenanceState.REJECTED.value
                ),
            }
            if reason:
                entry["reason"] = reason
            history.append(entry)

        state[
            "repair_job_history"
        ] = history

    state["repair_job_id"] = None
    state[
        "repair_publication_state"
    ] = None
    state[
        "repair_publication_commit"
    ] = None
    state[
        "repair_result_sha256"
    ] = None
    state["repair_commit_sha"] = None

    now_value = (
        time.time()
        if now_epoch is None
        else float(now_epoch)
    )

    state["cooldown_until_epoch"] = (
        now_value
        + REPAIR_COOLDOWN_SECONDS
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

    current_state_value = str(
        state.get("state") or ""
    )
    if (
        current_state_value
        == MaintenanceState.SUPERSEDED.value
    ):
        raise ValueError(
            "MAINTENANCE_INCIDENT_SUPERSEDED"
        )

    if (
        current_state_value
        != MaintenanceState.REPAIR_REQUIRED.value
    ):
        raise ValueError(
            "MAINTENANCE_INCIDENT_INVALID_STATE"
        )

    if (
        isinstance(repair_result, dict)
        and repair_result.get(
            "production_touched"
        )
        is not False
    ):
        state["state"] = (
            MaintenanceState.REJECTED.value
        )
        state["production_touched"] = True
        _archive_rejected_attempt(
            state,
            now_epoch=now_epoch,
            reason="PRODUCTION_TOUCHED",
        )
        _atomic_json(
            _incident_path(incident_id),
            state,
        )
        return MaintenanceDecision(
            incident_id=incident_id,
            state=MaintenanceState.REJECTED,
            reason="PRODUCTION_TOUCHED",
            certified=False,
            production_touched=True,
        )

    if int(state.get("attempts") or 0) < 1:
        state["state"] = (
            MaintenanceState.REJECTED.value
        )
        state["production_touched"] = False
        _archive_rejected_attempt(
            state,
            now_epoch=now_epoch,
            reason="NO_REPAIR_ATTEMPT_REGISTERED",
        )
        _atomic_json(
            _incident_path(incident_id),
            state,
        )
        return MaintenanceDecision(
            incident_id=incident_id,
            state=MaintenanceState.REJECTED,
            reason="NO_REPAIR_ATTEMPT_REGISTERED",
            certified=False,
        )

    bound_job_id = str(
        state.get("repair_job_id") or ""
    ).strip()
    result_job_id = str(
        repair_result.get("job_id") or ""
    ).strip()
    if (
        bound_job_id
        and result_job_id
        and result_job_id != bound_job_id
    ):
        state["state"] = (
            MaintenanceState.REJECTED.value
        )
        state["production_touched"] = False
        _archive_rejected_attempt(
            state,
            now_epoch=now_epoch,
            reason="REPAIR_JOB_ID_MISMATCH",
        )
        _atomic_json(
            _incident_path(incident_id),
            state,
        )
        return MaintenanceDecision(
            incident_id=incident_id,
            state=MaintenanceState.REJECTED,
            reason="REPAIR_JOB_ID_MISMATCH",
            certified=False,
        )

    incident = MaintenanceIncident(
        incident_id=incident_id,
        paths=tuple(state.get("target_paths") or []),
        state=MaintenanceState(
            current_state_value
        ),
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
        _archive_rejected_attempt(
            state,
            now_epoch=now_epoch,
            reason=decision.reason,
        )
    else:
        state["cooldown_until_epoch"] = None
        if result_job_id and not bound_job_id:
            state["repair_job_id"] = (
                result_job_id
            )
        result_sha = (
            str(
                repair_result.get(
                    "result_sha256"
                )
                or ""
            )
            .strip()
            .lower()
            or None
        )
        commit_sha = (
            str(
                repair_result.get(
                    "development_sha"
                )
                or repair_result.get(
                    "candidate_sha"
                )
                or repair_result.get(
                    "commit_created"
                )
                or ""
            )
            .strip()
            .lower()
            or None
        )
        state["repair_result_sha256"] = (
            result_sha
        )
        state["repair_commit_sha"] = (
            commit_sha
        )

    _atomic_json(_incident_path(incident_id), state)
    return decision


def audit_runtime_incident(
    incident_id: str,
    repair_result: dict[str, Any],
    *,
    now_epoch: float | None = None,
    verify_canonical_result: bool = False,
    results_dir: Path | None = None,
    verify_git_diff: bool = False,
    repo_root: Path | None = None,
    require_protected_authorization: bool = False,
) -> MaintenanceDecision:
    state = _load_state(incident_id)
    if state is None:
        raise ValueError("INCIDENT_NOT_DECLARED")

    current_state_value = str(
        state.get("state") or ""
    )
    if (
        current_state_value
        == MaintenanceState.SUPERSEDED.value
    ):
        raise ValueError(
            "MAINTENANCE_INCIDENT_SUPERSEDED"
        )

    if (
        isinstance(repair_result, dict)
        and repair_result.get(
            "production_touched"
        )
        is not False
    ):
        state["state"] = (
            MaintenanceState.REJECTED.value
        )
        state["production_touched"] = True
        _archive_rejected_attempt(
            state,
            now_epoch=now_epoch,
            reason="PRODUCTION_TOUCHED",
        )
        _atomic_json(
            _incident_path(incident_id),
            state,
        )
        return MaintenanceDecision(
            incident_id=incident_id,
            state=MaintenanceState.REJECTED,
            reason="PRODUCTION_TOUCHED",
            certified=False,
            production_touched=True,
        )

    if (
        current_state_value
        != MaintenanceState.REPAIRED_PENDING_AUDIT.value
    ):
        state["state"] = (
            MaintenanceState.REJECTED.value
        )
        state["production_touched"] = False
        _archive_rejected_attempt(
            state,
            now_epoch=now_epoch,
            reason="INCIDENT_NOT_PENDING_AUDIT",
        )
        _atomic_json(
            _incident_path(incident_id),
            state,
        )
        return MaintenanceDecision(
            incident_id=incident_id,
            state=MaintenanceState.REJECTED,
            reason="INCIDENT_NOT_PENDING_AUDIT",
            certified=False,
        )

    if int(state.get("attempts") or 0) < 1:
        state["state"] = (
            MaintenanceState.REJECTED.value
        )
        state["production_touched"] = False
        _archive_rejected_attempt(
            state,
            now_epoch=now_epoch,
            reason="NO_REPAIR_ATTEMPT_REGISTERED",
        )
        _atomic_json(
            _incident_path(incident_id),
            state,
        )
        return MaintenanceDecision(
            incident_id=incident_id,
            state=MaintenanceState.REJECTED,
            reason="NO_REPAIR_ATTEMPT_REGISTERED",
            certified=False,
        )

    incident = MaintenanceIncident(
        incident_id=incident_id,
        paths=tuple(state.get("target_paths") or []),
        state=MaintenanceState(
            current_state_value
        ),
        production_allowed=False,
    )

    bound_job_id = (
        str(state.get("repair_job_id") or "").strip()
        or None
    )
    bound_sha256 = (
        str(
            state.get("repair_result_sha256")
            or ""
        )
        .strip()
        .lower()
        or None
    )
    bound_commit_sha = (
        str(
            state.get("repair_commit_sha") or ""
        )
        .strip()
        .lower()
        or None
    )

    decision = audit_incident(
        incident,
        repair_result,
        require_pending_audit_state=True,
        expected_job_id=bound_job_id,
        expected_result_sha256=bound_sha256,
        expected_commit_sha=bound_commit_sha,
        verify_canonical_result=verify_canonical_result,
        results_dir=results_dir,
        verify_git_diff=verify_git_diff,
        repo_root=repo_root,
        require_protected_authorization=require_protected_authorization,
    )

    state["state"] = decision.state.value
    state["production_touched"] = bool(
        repair_result.get("production_touched")
    )

    if decision.state is MaintenanceState.REJECTED:
        _archive_rejected_attempt(
            state,
            now_epoch=now_epoch,
            reason=decision.reason,
        )

    _atomic_json(_incident_path(incident_id), state)
    return decision


def read_runtime_incident(
    incident_id: str,
) -> RuntimeIncidentState | None:
    state = _load_state(incident_id)
    if state is None:
        return None

    return _build_runtime_state(
        incident_id,
        state,
    )
