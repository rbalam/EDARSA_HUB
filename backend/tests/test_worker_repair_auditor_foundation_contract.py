import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mirror_sync.worker_auditor import (
    audit_repair_result,
    auditor_can_mutate,
)
from tools.mirror_sync.worker_maintenance_contract import (
    AUDITOR_AUTHORITY,
    REPAIR_AUTHORITY,
    repair_scope_allowed,
)
from tools.mirror_sync.worker_repair import (
    build_repair_plan,
    repair_requires_independent_audit,
)


def test_repair_and_auditor_are_distinct_authorities():
    assert REPAIR_AUTHORITY.role == "WORKER_REPAIR"
    assert REPAIR_AUTHORITY.mutation_allowed is True

    assert AUDITOR_AUTHORITY.role == "WORKER_AUDITOR"
    assert AUDITOR_AUTHORITY.mutation_allowed is False


def test_neither_role_can_touch_production():
    assert REPAIR_AUTHORITY.production_allowed is False
    assert AUDITOR_AUTHORITY.production_allowed is False


def test_neither_role_is_normal_development_worker():
    assert REPAIR_AUTHORITY.normal_development_jobs_allowed is False
    assert AUDITOR_AUTHORITY.normal_development_jobs_allowed is False


def test_repair_scope_is_worker_infrastructure_only():
    assert repair_scope_allowed(
        ["tools/mirror_sync/gate_chain_publisher.py"]
    )

    assert not repair_scope_allowed(
        ["frontend/src/App.jsx"]
    )

    assert not repair_scope_allowed(
        ["backend/modules/comercial/routes.py"]
    )


def test_repair_plan_requires_independent_audit():
    plan = build_repair_plan(
        "INCIDENT-1",
        ["tools/mirror_sync/gate_chain_publisher.py"],
    )

    assert repair_requires_independent_audit(plan) is True


def test_auditor_is_read_only():
    assert auditor_can_mutate() is False


def test_auditor_certifies_only_valid_worker_repair():
    decision = audit_repair_result(
        {
            "files_changed": [
                "tools/mirror_sync/gate_chain_publisher.py",
            ],
            "production_touched": False,
            "quality_gate": "PASS",
            "tests": "PASS",
            "blockers": [],
            "git_sync_status": "CERTIFIED_GIT_SYNC",
        }
    )

    assert decision.certified is True
    assert decision.reason == "CERTIFIED_WORKER_REPAIR"
    assert decision.mutation_performed is False
    assert decision.production_touched is False


def test_auditor_rejects_application_code_mutation():
    decision = audit_repair_result(
        {
            "files_changed": [
                "frontend/src/App.jsx",
            ],
            "production_touched": False,
            "quality_gate": "PASS",
            "tests": "PASS",
            "blockers": [],
            "git_sync_status": "CERTIFIED_GIT_SYNC",
        }
    )

    assert decision.certified is False


def test_auditor_rejects_production_touch():
    decision = audit_repair_result(
        {
            "files_changed": [
                "tools/mirror_sync/gate_chain_publisher.py",
            ],
            "production_touched": True,
            "quality_gate": "PASS",
            "tests": "PASS",
            "blockers": [],
            "git_sync_status": "CERTIFIED_GIT_SYNC",
        }
    )

    assert decision.certified is False
    assert decision.reason == "PRODUCTION_TOUCHED"
