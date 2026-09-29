from __future__ import annotations

import json
from types import SimpleNamespace

from tools.mirror_sync import worker_maintenance_runtime as runtime
from tools.mirror_sync import worker_repair_execution as execution
from tools.mirror_sync import worker_repair_planner as planner


TARGET = "tools/mirror_sync/gate_chain_publisher.py"


def _redirect_state(tmp_path, monkeypatch):
    state = (
        tmp_path
        / "maintenance"
    )

    monkeypatch.setattr(
        runtime,
        "STATE_DIR",
        state,
    )

    monkeypatch.setattr(
        runtime,
        "INCIDENT_DIR",
        state / "incidents",
    )

    monkeypatch.setattr(
        planner,
        "REPAIR_SPECS",
        state / "repair_specs",
    )


def _failed_result():
    return {
        "files_changed": [],
        "production_touched": False,
        "quality_gate": "FAIL",
        "tests": "FAIL",
        "blockers": [
            "dispatcher_exception:"
            "RuntimeError:"
            "GIT_WORKTREE_NOT_CLEAN"
        ],
        "git_sync_status": None,
    }


def test_rejected_attempt_releases_active_binding_and_preserves_history(
    tmp_path,
    monkeypatch,
):
    _redirect_state(
        tmp_path,
        monkeypatch,
    )

    incident_id = (
        "INCIDENT-RETRY-BINDING"
    )

    runtime.declare_runtime_incident(
        incident_id,
        [TARGET],
    )

    a1 = (
        execution.deterministic_repair_job_id(
            incident_id,
            1,
        )
    )

    runtime.register_published_repair_attempt(
        incident_id,
        a1,
        {
            "status": "PUBLISHED",
            "commit_sha": "a" * 40,
        },
        now_epoch=1000,
    )

    decision = runtime.register_repair_result(
        incident_id,
        _failed_result(),
        now_epoch=1000,
    )

    assert (
        decision.state.value
        == "REJECTED"
    )

    state = runtime.read_runtime_incident(
        incident_id
    )

    assert state is not None
    assert state.state == "REJECTED"
    assert state.attempts == 1
    assert state.repair_job_id is None
    assert (
        state.repair_publication_state
        is None
    )
    assert (
        state.repair_publication_commit
        is None
    )

    raw = json.loads(
        (
            runtime.INCIDENT_DIR
            / f"{incident_id}.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    history = raw.get(
        "repair_job_history"
    )

    assert isinstance(
        history,
        list,
    )

    assert history[-1]["job_id"] == a1
    assert history[-1]["attempt"] == 1
    assert (
        history[-1]["terminal_state"]
        == "REJECTED"
    )

    allowed, reason = (
        runtime.repair_attempt_allowed(
            incident_id,
            now_epoch=1301,
        )
    )

    assert allowed is True
    assert reason == "REPAIR_ALLOWED"


def test_planner_materializes_a2_after_rejected_a1(
    tmp_path,
    monkeypatch,
):
    _redirect_state(
        tmp_path,
        monkeypatch,
    )

    incident_id = (
        "INCIDENT-PLANNER-A2"
    )

    runtime.declare_runtime_incident(
        incident_id,
        [TARGET],
    )

    a1 = (
        execution.deterministic_repair_job_id(
            incident_id,
            1,
        )
    )

    runtime.register_published_repair_attempt(
        incident_id,
        a1,
        {
            "status": "PUBLISHED",
            "commit_sha": "b" * 40,
        },
        now_epoch=1000,
    )

    runtime.register_repair_result(
        incident_id,
        _failed_result(),
        now_epoch=1000,
    )

    monkeypatch.setattr(
        planner,
        "convergence_state",
        lambda: {
            "local": "c" * 40,
            "development": "c" * 40,
            "mirror": "c" * 40,
            "converged": True,
        },
    )

    monkeypatch.setattr(
        planner,
        "_canonical_requester",
        lambda: {
            "email": "worker@example.com",
            "source": "worker_repair",
            "project": "EDARSAHUB-BOS",
            "chat": "retry-test",
        },
    )

    monkeypatch.setattr(
        planner,
        "_CAPABILITIES",
        {},
    )

    planner.register_capability(
        planner.RepairCapability(
            code="RETRY_TEST",
            incident_ids=(
                incident_id,
            ),
            required_paths=(
                TARGET,
            ),
            builder=lambda _i, _c: {
                "objective": (
                    "Retry binding test"
                ),
                "actions": [
                    {
                        "type": "write_file",
                        "path": TARGET,
                        "content": "x",
                    }
                ],
                "checks": [
                    {
                        "type": "py_compile",
                        "paths": [TARGET],
                    }
                ],
            },
        )
    )

    planned = (
        planner.build_deterministic_repair_job(
            incident_id,
            capability_code="RETRY_TEST",
        )
    )

    expected_a2 = (
        execution.deterministic_repair_job_id(
            incident_id,
            2,
        )
    )

    assert (
        planned["job"]["job_id"]
        == expected_a2
    )

    assert expected_a2 != a1


def test_second_publication_exhausts_retry_budget(
    tmp_path,
    monkeypatch,
):
    _redirect_state(
        tmp_path,
        monkeypatch,
    )

    incident_id = (
        "INCIDENT-TWO-ATTEMPTS"
    )

    runtime.declare_runtime_incident(
        incident_id,
        [TARGET],
    )

    a1 = (
        execution.deterministic_repair_job_id(
            incident_id,
            1,
        )
    )

    runtime.register_published_repair_attempt(
        incident_id,
        a1,
        {
            "status": "PUBLISHED",
            "commit_sha": "d" * 40,
        },
        now_epoch=1000,
    )

    runtime.register_repair_result(
        incident_id,
        _failed_result(),
        now_epoch=1000,
    )

    a2 = (
        execution.deterministic_repair_job_id(
            incident_id,
            2,
        )
    )

    state = (
        runtime.register_published_repair_attempt(
            incident_id,
            a2,
            {
                "status": "PUBLISHED",
                "commit_sha": "e" * 40,
            },
            now_epoch=1301,
        )
    )

    assert state.attempts == 2
    assert state.repair_job_id == a2

    allowed, reason = (
        runtime.repair_attempt_allowed(
            incident_id,
            now_epoch=1302,
        )
    )

    assert allowed is False
    assert (
        reason
        == "REPAIR_ATTEMPTS_EXHAUSTED"
    )


def test_result_timestamp_drives_cooldown_epoch():
    epoch = (
        execution._result_completed_epoch(
            {
                "completed_at_utc":
                "2026-09-29T03:02:02Z",
            }
        )
    )

    assert isinstance(
        epoch,
        float,
    )

    assert (
        execution._result_completed_epoch(
            {
                "completed_at_utc":
                "not-a-date",
            }
        )
        is None
    )
