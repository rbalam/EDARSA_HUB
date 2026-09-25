import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mirror_sync import worker_maintenance_runtime as runtime
from tools.mirror_sync.worker_maintenance_controller import (
    MaintenanceState,
)


def valid_result():
    return {
        "files_changed": [
            "tools/mirror_sync/gate_chain_publisher.py",
        ],
        "production_touched": False,
        "quality_gate": "PASS",
        "tests": "PASS",
        "blockers": [],
        "git_sync_status": "CERTIFIED_GIT_SYNC",
    }


def _redirect_state(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "STATE_DIR", tmp_path)
    monkeypatch.setattr(runtime, "INCIDENT_DIR", tmp_path / "incidents")


def test_runtime_incident_declaration_is_idempotent(tmp_path, monkeypatch):
    _redirect_state(tmp_path, monkeypatch)

    first = runtime.declare_runtime_incident(
        "INCIDENT-IDEMPOTENT",
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )
    second = runtime.declare_runtime_incident(
        "INCIDENT-IDEMPOTENT",
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )

    assert first.incident_id == second.incident_id
    assert first.target_paths == second.target_paths
    assert second.state == MaintenanceState.REPAIR_REQUIRED.value


def test_same_incident_cannot_change_scope(tmp_path, monkeypatch):
    _redirect_state(tmp_path, monkeypatch)

    runtime.declare_runtime_incident(
        "INCIDENT-SCOPE",
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )

    try:
        runtime.declare_runtime_incident(
            "INCIDENT-SCOPE",
            ["tools/mirror_sync/worker_control_plane.py"],
        )
    except ValueError as exc:
        assert "MAINTENANCE_INCIDENT_SCOPE_MISMATCH" in str(exc)
    else:
        raise AssertionError("incident scope mutation must fail closed")


def test_repair_attempts_are_bounded(tmp_path, monkeypatch):
    _redirect_state(tmp_path, monkeypatch)

    runtime.declare_runtime_incident(
        "INCIDENT-ATTEMPTS",
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )

    runtime.register_repair_attempt(
        "INCIDENT-ATTEMPTS",
        now_epoch=1000,
    )
    runtime.register_repair_attempt(
        "INCIDENT-ATTEMPTS",
        now_epoch=1001,
    )

    allowed, reason = runtime.repair_attempt_allowed(
        "INCIDENT-ATTEMPTS",
        now_epoch=1002,
    )

    assert allowed is False
    assert reason == "REPAIR_ATTEMPTS_EXHAUSTED"


def test_failed_repair_enters_cooldown(tmp_path, monkeypatch):
    _redirect_state(tmp_path, monkeypatch)

    runtime.declare_runtime_incident(
        "INCIDENT-COOLDOWN",
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )
    runtime.register_repair_attempt(
        "INCIDENT-COOLDOWN",
        now_epoch=1000,
    )

    result = valid_result()
    result["tests"] = "FAIL"

    decision = runtime.register_repair_result(
        "INCIDENT-COOLDOWN",
        result,
        now_epoch=1000,
    )

    assert decision.state is MaintenanceState.REJECTED

    allowed, reason = runtime.repair_attempt_allowed(
        "INCIDENT-COOLDOWN",
        now_epoch=1001,
    )

    assert allowed is False
    assert reason == "REPAIR_COOLDOWN_ACTIVE"


def test_repair_never_self_certifies(tmp_path, monkeypatch):
    _redirect_state(tmp_path, monkeypatch)

    runtime.declare_runtime_incident(
        "INCIDENT-NO-SELF-CERT",
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )
    runtime.register_repair_attempt(
        "INCIDENT-NO-SELF-CERT",
    )

    decision = runtime.register_repair_result(
        "INCIDENT-NO-SELF-CERT",
        valid_result(),
    )

    assert decision.state is MaintenanceState.REPAIRED_PENDING_AUDIT
    assert decision.certified is False


def test_independent_auditor_certifies_valid_repair(tmp_path, monkeypatch):
    _redirect_state(tmp_path, monkeypatch)

    runtime.declare_runtime_incident(
        "INCIDENT-AUDIT",
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )
    runtime.register_repair_attempt(
        "INCIDENT-AUDIT",
    )

    repair_result = valid_result()

    pending = runtime.register_repair_result(
        "INCIDENT-AUDIT",
        repair_result,
    )
    assert pending.state is MaintenanceState.REPAIRED_PENDING_AUDIT

    certified = runtime.audit_runtime_incident(
        "INCIDENT-AUDIT",
        repair_result,
    )

    assert certified.state is MaintenanceState.CERTIFIED
    assert certified.certified is True
    assert certified.reason == "CERTIFIED_WORKER_REPAIR"


def test_auditor_rejects_production_touch(tmp_path, monkeypatch):
    _redirect_state(tmp_path, monkeypatch)

    runtime.declare_runtime_incident(
        "INCIDENT-PRODUCTION",
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )

    result = valid_result()
    result["production_touched"] = True

    decision = runtime.audit_runtime_incident(
        "INCIDENT-PRODUCTION",
        result,
    )

    assert decision.state is MaintenanceState.REJECTED
    assert decision.certified is False


def test_application_scope_remains_forbidden(tmp_path, monkeypatch):
    _redirect_state(tmp_path, monkeypatch)

    try:
        runtime.declare_runtime_incident(
            "INCIDENT-APP",
            ["frontend/src/App.jsx"],
        )
    except ValueError as exc:
        assert "REPAIR_SCOPE_FORBIDDEN" in str(exc)
    else:
        raise AssertionError("application mutation must remain forbidden")


def test_runtime_has_no_production_capability():
    assert runtime.MAX_REPAIR_ATTEMPTS > 0
    assert runtime.REPAIR_COOLDOWN_SECONDS > 0
    assert "Edarsahub_Produccion" not in Path(runtime.__file__).read_text(
        encoding="utf-8"
    )

def test_runtime_supersession_is_atomic_and_non_actionable(
    tmp_path,
    monkeypatch,
):
    _redirect_state(tmp_path, monkeypatch)

    incident_id = "INCIDENT-SUPERSEDED"

    runtime.declare_runtime_incident(
        incident_id,
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )

    before = runtime.read_runtime_incident(incident_id)
    assert before is not None
    assert before.attempts == 0

    after = runtime.supersede_runtime_incident(
        incident_id,
        reason="SUPERSEDED_BY_CURRENT_HEAD",
    )

    assert after.state == MaintenanceState.SUPERSEDED.value
    assert after.attempts == 0
    assert after.cooldown_until_epoch is None
    assert after.production_touched is False

    allowed, reason = runtime.repair_attempt_allowed(
        incident_id
    )

    assert allowed is False
    assert reason == "INCIDENT_NOT_REPAIRABLE"
