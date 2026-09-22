import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mirror_sync.worker_maintenance_controller import (
    MaintenanceState,
    audit_incident,
    declare_incident,
    repair_plan_for,
    repaired_pending_audit,
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


def test_incident_declares_worker_repair_only():
    incident = declare_incident(
        "INCIDENT-1",
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )

    assert incident.state is MaintenanceState.REPAIR_REQUIRED
    assert incident.production_allowed is False


def test_application_scope_is_rejected():
    try:
        declare_incident(
            "INCIDENT-2",
            ["frontend/src/App.jsx"],
        )
    except ValueError as exc:
        assert "REPAIR_SCOPE_FORBIDDEN" in str(exc)
    else:
        raise AssertionError("application scope must fail closed")


def test_repair_plan_is_derived_from_incident():
    incident = declare_incident(
        "INCIDENT-3",
        ["tools/mirror_sync/worker_control_plane.py"],
    )

    plan = repair_plan_for(incident)

    assert plan.incident_id == "INCIDENT-3"
    assert plan.production_allowed is False


def test_repair_never_self_certifies():
    incident = declare_incident(
        "INCIDENT-4",
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )

    decision = repaired_pending_audit(
        incident,
        valid_result(),
    )

    assert decision.state is MaintenanceState.REPAIRED_PENDING_AUDIT
    assert decision.certified is False


def test_auditor_certifies_valid_repair():
    incident = declare_incident(
        "INCIDENT-5",
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )

    decision = audit_incident(
        incident,
        valid_result(),
    )

    assert decision.state is MaintenanceState.CERTIFIED
    assert decision.certified is True
    assert decision.reason == "CERTIFIED_WORKER_REPAIR"


def test_auditor_rejects_failed_tests():
    incident = declare_incident(
        "INCIDENT-6",
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )

    result = valid_result()
    result["tests"] = "FAIL"

    decision = audit_incident(
        incident,
        result,
    )

    assert decision.state is MaintenanceState.REJECTED
    assert decision.certified is False


def test_production_touch_is_terminal_rejection():
    incident = declare_incident(
        "INCIDENT-7",
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )

    result = valid_result()
    result["production_touched"] = True

    decision = repaired_pending_audit(
        incident,
        result,
    )

    assert decision.state is MaintenanceState.REJECTED
    assert decision.reason == "PRODUCTION_TOUCHED"


def test_missing_git_certification_is_rejected():
    incident = declare_incident(
        "INCIDENT-8",
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )

    result = valid_result()
    result["git_sync_status"] = None

    decision = repaired_pending_audit(
        incident,
        result,
    )

    assert decision.state is MaintenanceState.REJECTED
    assert decision.reason == "REPAIR_NOT_GIT_CERTIFIED"
