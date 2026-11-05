from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

CONTROL = ROOT / "tools/mirror_sync/worker_control_plane.py"
PLANNER = ROOT / "tools/mirror_sync/worker_repair_planner.py"
AUTO = ROOT / "tools/mirror_sync/worker_repair_auto_loop.py"


def test_control_plane_advances_repairs_outside_detector():
    text = CONTROL.read_text(encoding="utf-8")

    assert "automatic_repair = automatic_repair_orchestration()" in text
    assert (
        "automatic_repair_execution = advance_repair_automation("
        in text
    )
    assert '"automatic_repair_execution": automatic_repair_execution' in text


def test_detector_boundary_remains_separate():
    text = CONTROL.read_text(encoding="utf-8")

    start = text.index("def automatic_repair_orchestration(")
    end = text.index("def maintenance_runtime_summary(", start)

    helper = text[start:end]

    assert "publish_planned_repair(" not in helper
    assert "reconcile_repair_result(" not in helper
    assert "CERTIFIED_WORKER_REPAIR" not in helper


def test_auto_loop_only_orchestrates_existing_components():
    text = AUTO.read_text(encoding="utf-8")

    assert "planner.publish_planned_repair(" in text
    assert "execution.reconcile_repair_result(" in text
    assert "execution.read_repair_terminal_result(" in text
    assert "maintenance.audit_runtime_incident(" in text
    assert "ensure_submit_convergence(" in text
    assert "resolve_learned_capability(" in text

    assert "subprocess" not in text
    assert "shell=True" not in text
    assert "universal_job_dispatcher" not in text
    assert "worker/requests" not in text


def test_auto_loop_requires_certified_result_before_audit():
    text = AUTO.read_text(encoding="utf-8")

    assert 'certification != "CERTIFIED"' in text
    assert "WAIT_RESULT_CERTIFICATION" in text


def test_planner_uses_safe_convergence():
    text = PLANNER.read_text(encoding="utf-8")

    assert "ensure_submit_convergence" in text
    assert 'owner="worker-repair-planner"' in text
    assert "DEV_MIRROR_NOT_CONVERGED:" in text


def test_planner_accepts_inherited_requester():
    text = PLANNER.read_text(encoding="utf-8")

    assert "requester: dict[str, Any] | None = None" in text
    assert "_canonical_requester(requester)" in text


def test_production_remains_forbidden():
    control = CONTROL.read_text(encoding="utf-8")
    auto = AUTO.read_text(encoding="utf-8")

    assert '"production_touched": False' in control
    assert '"production_touched": False' in auto
    assert "Edarsahub_Produccion" not in auto


def test_auto_loop_registers_learned_capability_only_after_certified_audit(
    tmp_path,
    monkeypatch,
):
    from types import SimpleNamespace
    import json
    from tools.mirror_sync import (
        worker_maintenance_runtime as maintenance,
        worker_repair_auto_loop as auto_loop,
        worker_repair_capability_registry as registry,
        worker_repair_execution as execution,
        worker_repair_planner as planner,
    )

    inc_dir = tmp_path / "incidents"
    reg_dir = tmp_path / "learned"
    seed_dir = tmp_path / "seed"
    specs_dir = tmp_path / "specs"
    queue_dir = tmp_path / "queue"

    monkeypatch.setattr(maintenance, "STATE_DIR", tmp_path)
    monkeypatch.setattr(maintenance, "INCIDENT_DIR", inc_dir)
    monkeypatch.setattr(registry, "REGISTRY_DIR", reg_dir)
    monkeypatch.setattr(registry, "SEED_DIR", seed_dir)
    monkeypatch.setattr(planner, "REPAIR_SPECS", specs_dir)
    monkeypatch.setattr(auto_loop, "QUEUE_ROOT", queue_dir)

    incident_id = "WORKER-KLOOP-CERT-TEST-R1"
    target_paths = [
        "tools/mirror_sync/worker_control_plane.py",
        "backend/tests/test_worker_control_plane_contract.py",
    ]
    maintenance.declare_runtime_incident(
        incident_id,
        target_paths,
        source_job_id="SOURCE-JOB-KLOOP-1",
        source_status="GIT_LOCK_BUSY",
        problem_signature="LOCK_BUSY_TEST_SIG",
        blocker_signature="dispatcher_exception:RuntimeError:GIT_LOCK_BUSY",
        capability_code="KLOOP_TEST_CAPABILITY_V1",
        requester={
            "email": "ricardo@edarsa.com.mx",
            "source": "CHATGPT",
            "project": "EDARSAHUB-BOS",
            "chat": "KLOOP-TEST",
        },
    )

    repair_job_id = "WORKER-REPAIR-KLOOP-CERT-A1"
    maintenance.register_published_repair_attempt(
        incident_id,
        repair_job_id,
        {"status": "PUBLISHED", "commit_sha": "a" * 40},
    )

    specs_dir.mkdir(parents=True, exist_ok=True)
    (specs_dir / f"{repair_job_id}.json").write_text(
        json.dumps(
            {
                "job_id": repair_job_id,
                "objective": "Reparacion KLOOP_TEST_CAPABILITY_V1",
                "actions": [
                    {
                        "type": "replace_text",
                        "path": target_paths[0],
                        "old": "a",
                        "new": "b",
                        "expected_count": 1,
                    }
                ],
                "checks": [
                    {
                        "type": "pytest",
                        "paths": [target_paths[1]],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    certified_payload = {
        "job_id": repair_job_id,
        "status": "INTEGRATED",
        "certification": "CERTIFIED",
        "quality_gate": "PASS",
        "tests": "PASS",
        "git_sync_status": "CERTIFIED_GIT_SYNC",
        "production_touched": False,
        "files_changed": target_paths,
        "blockers": [],
        "base_sha": "b" * 40,
        "execution_base_sha": "b" * 40,
        "candidate_sha": "c" * 40,
        "development_sha": "c" * 40,
        "result_sha256": "d" * 64,
    }

    monkeypatch.setattr(
        execution,
        "read_repair_terminal_result",
        lambda _inc_id: SimpleNamespace(
            terminal_result_valid=True,
            state="CERTIFIED_TERMINAL_RESULT",
            payload=certified_payload,
            result_sha256="d" * 64,
        ),
    )

    def fake_reconcile(inc_id):
        dec = maintenance.register_repair_result(
            inc_id,
            certified_payload,
        )
        return {"state": dec.state.value}

    monkeypatch.setattr(
        execution,
        "reconcile_repair_result",
        fake_reconcile,
    )

    first = auto_loop._advance_bound_repair(
        incident_id,
        repair_job_id,
    )
    assert first["action"] == "AUDITED"
    assert first["certified"] is True
    assert first["state"] == "CERTIFIED"
    assert (
        first["learned_capability_registration"]["status"]
        == "REGISTERED"
    )

    second = auto_loop._register_certified_repair_capability(
        incident_id,
        repair_job_id,
        certified_payload,
        result_sha256="d" * 64,
    )
    assert second["status"] == "ALREADY_REGISTERED"


def test_auto_loop_persists_requester_and_supersedes_resolved_incidents(
    tmp_path,
    monkeypatch,
):
    import json
    from tools.mirror_sync import (
        worker_maintenance_runtime as maintenance,
        worker_repair_auto_loop as auto_loop,
        worker_repair_capability_registry as registry,
    )

    inc_dir = tmp_path / "incidents"
    reg_dir = tmp_path / "learned"
    seed_dir = tmp_path / "seed"
    queue_dir = tmp_path / "queue"

    monkeypatch.setattr(maintenance, "STATE_DIR", tmp_path)
    monkeypatch.setattr(maintenance, "INCIDENT_DIR", inc_dir)
    monkeypatch.setattr(registry, "REGISTRY_DIR", reg_dir)
    monkeypatch.setattr(registry, "SEED_DIR", seed_dir)
    monkeypatch.setattr(auto_loop, "QUEUE_ROOT", queue_dir)

    (queue_dir / "rejected_history").mkdir(
        parents=True,
        exist_ok=True,
    )
    (
        queue_dir
        / "rejected_history"
        / "HIST-JOB-1.20261001.json"
    ).write_text(
        json.dumps(
            {
                "job": {
                    "requester": {
                        "email": "carlosruz@edarsa.com.mx",
                        "source": "CHATGPT",
                        "project": "EDARSAHUB-BOS",
                        "chat": "Hist",
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    resolved_req = auto_loop._source_requester("HIST-JOB-1")
    assert resolved_req is not None
    assert resolved_req["email"] == "carlosruz@edarsa.com.mx"

    cert_inc = "CERTIFIED-SIBLING-R2"
    maintenance.declare_runtime_incident(
        cert_inc,
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )
    cert_path = inc_dir / f"{cert_inc}.json"
    cert_data = json.loads(cert_path.read_text(encoding="utf-8"))
    cert_data["state"] = "CERTIFIED"
    cert_path.write_text(
        json.dumps(cert_data),
        encoding="utf-8",
    )

    stale_rejected = "STALE-REJECTED-R1"
    maintenance.declare_runtime_incident(
        stale_rejected,
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )
    stale_path = inc_dir / f"{stale_rejected}.json"
    stale_data = json.loads(stale_path.read_text(encoding="utf-8"))
    stale_data["state"] = "REJECTED"
    stale_path.write_text(
        json.dumps(stale_data),
        encoding="utf-8",
    )

    summary = auto_loop.advance_repair_automation(
        {"incidents": []}
    )
    by_id = {
        row["incident_id"]: row
        for row in summary["incidents"]
    }
    assert by_id[stale_rejected]["action"] == "SUPERSEDED"
    assert by_id[stale_rejected]["state"] == "SUPERSEDED"
