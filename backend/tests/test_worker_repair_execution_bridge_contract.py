from __future__ import annotations

import inspect
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mirror_sync import worker_maintenance_runtime as runtime
from tools.mirror_sync import worker_repair_execution as execution


def _redirect_state(tmp_path, monkeypatch):
    monkeypatch.setattr(
        runtime,
        "STATE_DIR",
        tmp_path,
    )
    monkeypatch.setattr(
        runtime,
        "INCIDENT_DIR",
        tmp_path / "incidents",
    )


def _job(
    incident_id: str,
    attempt: int = 1,
):
    return {
        "schema": "edarsahub.worker-job.v2",
        "job_id": execution.deterministic_repair_job_id(
            incident_id,
            attempt,
        ),
        "target_repo": "rbalam/EDARSA_HUB",
        "target_branch": "Edarsahub_Desarrollo",
        "production_allowed": False,
        "objective": "Reparacion deterministica Worker.",
        "human_summary_language": "es",
        "mode": "MUTATION",
        "actions": [
            {
                "type": "replace_text",
                "path": (
                    "tools/mirror_sync/"
                    "worker_control_plane.py"
                ),
                "old": "OLD",
                "new": "NEW",
                "expected_count": 1,
            }
        ],
        "checks": [
            {
                "type": "git_diff_check",
            }
        ],
    }


def test_repair_job_identity_is_deterministic():
    first = execution.deterministic_repair_job_id(
        "WORKER-abc",
        1,
    )
    second = execution.deterministic_repair_job_id(
        "WORKER-abc",
        1,
    )

    assert first == second
    assert first.startswith("WORKER-REPAIR-")
    assert first.endswith("-A1")


def test_execution_bridge_has_no_direct_executor():
    source = Path(
        execution.__file__
    ).read_text(encoding="utf-8")

    assert "subprocess" not in source
    assert "os.system" not in source
    assert "shell=True" not in source
    assert "universal_job_dispatcher" not in source
    assert "worker_queue/inbox" not in source
    assert "audit_runtime_incident(" not in source


def test_validate_repair_job_is_scope_bound(
    tmp_path,
    monkeypatch,
):
    _redirect_state(tmp_path, monkeypatch)

    incident_id = "WORKER-SCOPE"

    runtime.declare_runtime_incident(
        incident_id,
        [
            "tools/mirror_sync/"
            "worker_control_plane.py"
        ],
    )

    validated = execution.validate_repair_worker_job(
        incident_id,
        _job(incident_id),
    )

    assert validated["production_allowed"] is False

    bad = _job(incident_id)
    bad["actions"][0]["path"] = "frontend/src/App.jsx"

    with pytest.raises(
        ValueError,
        match="REPAIR_ACTION_SCOPE_MISMATCH",
    ):
        execution.validate_repair_worker_job(
            incident_id,
            bad,
        )


def test_publication_registers_exactly_one_attempt(
    tmp_path,
    monkeypatch,
):
    _redirect_state(tmp_path, monkeypatch)

    incident_id = "WORKER-PUBLISH"

    runtime.declare_runtime_incident(
        incident_id,
        [
            "tools/mirror_sync/"
            "worker_control_plane.py"
        ],
    )

    job = _job(incident_id)

    calls = []

    def fake_publish(plan, **kwargs):
        calls.append(plan["job_id"])
        return {
            "status": "PUBLISHED",
            "job_id": plan["job_id"],
            "commit_sha": "a" * 40,
            "production_touched": False,
        }

    monkeypatch.setattr(
        execution.gate_chain_publisher,
        "publish",
        fake_publish,
    )

    first = execution.publish_repair_job(
        incident_id,
        job,
    )

    second = execution.publish_repair_job(
        incident_id,
        job,
    )

    state = runtime.read_runtime_incident(
        incident_id
    )

    assert first["attempts"] == 1
    assert second["attempts"] == 1
    assert state is not None
    assert state.attempts == 1
    assert state.repair_job_id == job["job_id"]
    assert len(calls) == 2


def test_different_job_cannot_rebind_attempt(
    tmp_path,
    monkeypatch,
):
    _redirect_state(tmp_path, monkeypatch)

    incident_id = "WORKER-BINDING"

    runtime.declare_runtime_incident(
        incident_id,
        [
            "tools/mirror_sync/"
            "worker_control_plane.py"
        ],
    )

    runtime.register_published_repair_attempt(
        incident_id,
        execution.deterministic_repair_job_id(
            incident_id,
            1,
        ),
        {
            "status": "PUBLISHED",
            "commit_sha": "b" * 40,
        },
    )

    with pytest.raises(
        ValueError,
        match="REPAIR_JOB_BINDING_MISMATCH",
    ):
        runtime.register_published_repair_attempt(
            incident_id,
            "WORKER-REPAIR-other-A1",
            {
                "status": "PUBLISHED",
                "commit_sha": "c" * 40,
            },
        )


def test_invalid_terminal_result_does_not_transition(
    tmp_path,
    monkeypatch,
):
    _redirect_state(tmp_path, monkeypatch)

    incident_id = "WORKER-WAIT"

    runtime.declare_runtime_incident(
        incident_id,
        [
            "tools/mirror_sync/"
            "worker_control_plane.py"
        ],
    )

    job_id = execution.deterministic_repair_job_id(
        incident_id,
        1,
    )

    runtime.register_published_repair_attempt(
        incident_id,
        job_id,
        {
            "status": "PUBLISHED",
            "commit_sha": "d" * 40,
        },
    )

    monkeypatch.setattr(
        execution,
        "read_repair_terminal_result",
        lambda _incident_id: SimpleNamespace(
            terminal_result_valid=False,
            state="RESULT_MISSING",
        ),
    )

    result = execution.reconcile_repair_result(
        incident_id
    )

    state = runtime.read_runtime_incident(
        incident_id
    )

    assert result["terminal_result_valid"] is False
    assert state is not None
    assert state.state == "REPAIR_REQUIRED"


def test_valid_terminal_result_becomes_pending_audit(
    tmp_path,
    monkeypatch,
):
    _redirect_state(tmp_path, monkeypatch)

    incident_id = "WORKER-RESULT"

    target = (
        "tools/mirror_sync/"
        "worker_control_plane.py"
    )

    runtime.declare_runtime_incident(
        incident_id,
        [target],
    )

    job_id = execution.deterministic_repair_job_id(
        incident_id,
        1,
    )

    runtime.register_published_repair_attempt(
        incident_id,
        job_id,
        {
            "status": "PUBLISHED",
            "commit_sha": "e" * 40,
        },
    )

    monkeypatch.setattr(
        execution,
        "read_repair_terminal_result",
        lambda _incident_id: SimpleNamespace(
            terminal_result_valid=True,
            state="RESULT_TERMINAL_VALID",
            result_sha256="f" * 64,
            result_path="/tmp/result.json",
            payload={
                "job_id": job_id,
                "files_changed": [target],
                "production_touched": False,
                "quality_gate": "PASS",
                "tests": "PASS",
                "blockers": [],
                "git_sync_status": (
                    "CERTIFIED_GIT_SYNC"
                ),
            },
        ),
    )

    result = execution.reconcile_repair_result(
        incident_id
    )

    state = runtime.read_runtime_incident(
        incident_id
    )

    assert result["state"] == (
        "REPAIRED_PENDING_AUDIT"
    )
    assert result["certified"] is False
    assert state is not None
    assert state.state == (
        "REPAIRED_PENDING_AUDIT"
    )


def test_bridge_does_not_self_certify():
    source = inspect.getsource(
        execution.reconcile_repair_result
    )

    assert "audit_runtime_incident" not in source
    assert "CERTIFIED_WORKER_REPAIR" not in source
