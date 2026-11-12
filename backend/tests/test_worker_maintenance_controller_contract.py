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

def test_superseded_is_terminal_noncertified_state():
    assert MaintenanceState.SUPERSEDED.value == "SUPERSEDED"



def test_pending_audit_rejects_unauthorized_incident_file_scope():
    incident = declare_incident(
        "INCIDENT-SCOPE-MISMATCH",
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )
    result = valid_result()
    result["files_changed"] = [
        "tools/mirror_sync/worker_control_plane.py",
    ]

    decision = repaired_pending_audit(
        incident,
        result,
    )
    assert decision.state is MaintenanceState.REJECTED
    assert decision.certified is False
    assert (
        decision.reason
        == "REPAIR_SCOPE_OUTSIDE_INCIDENT_AUTHORIZATION"
    )


def test_audit_incident_rejects_non_pending_when_required():
    incident = declare_incident(
        "INCIDENT-STATE-GATE",
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )

    decision = audit_incident(
        incident,
        valid_result(),
        require_pending_audit_state=True,
    )
    assert decision.state is MaintenanceState.REJECTED
    assert decision.certified is False
    assert (
        decision.reason
        == "INCIDENT_NOT_PENDING_AUDIT"
    )


def test_d2_2_gitignore_scope_requires_exact_incident_and_capability():
    from tools.mirror_sync.worker_maintenance_contract import (
        D2_2_CAPABILITY_CODE,
        D2_2_INCIDENT_ID,
    )

    incident = declare_incident(
        D2_2_INCIDENT_ID,
        [
            ".gitignore",
            "tools/mirror_sync/shared_app_safety_guard.sh",
            "backend/tests/test_worker_d2_2_runtime_artifact_contract.py",
        ],
        capability_code=D2_2_CAPABILITY_CODE,
    )
    assert incident.state is MaintenanceState.REPAIR_REQUIRED
    assert incident.capability_code == D2_2_CAPABILITY_CODE

    for bad_incident, bad_capability in (
        ("OTHER-INCIDENT", D2_2_CAPABILITY_CODE),
        (D2_2_INCIDENT_ID, "OTHER_CAPABILITY"),
        ("OTHER-INCIDENT", "OTHER_CAPABILITY"),
    ):
        try:
            declare_incident(
                bad_incident,
                [".gitignore"],
                capability_code=bad_capability,
            )
        except ValueError as exc:
            assert "REPAIR_SCOPE_FORBIDDEN" in str(exc)
        else:
            raise AssertionError("D2.2 exception must fail closed")


def test_d2_2_pending_audit_accepts_only_exact_authority_context():
    from tools.mirror_sync.worker_maintenance_contract import (
        D2_2_CAPABILITY_CODE,
        D2_2_INCIDENT_ID,
    )

    incident = declare_incident(
        D2_2_INCIDENT_ID,
        [".gitignore"],
        capability_code=D2_2_CAPABILITY_CODE,
    )
    result = {
        "files_changed": [".gitignore"],
        "production_touched": False,
        "quality_gate": "PASS",
        "tests": "PASS",
        "blockers": [],
        "git_sync_status": "CERTIFIED_GIT_SYNC",
    }
    decision = repaired_pending_audit(incident, result)
    assert decision.state is MaintenanceState.REPAIRED_PENDING_AUDIT
