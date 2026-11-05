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



def test_auditor_rejects_files_outside_incident_authorized_paths():
    decision = audit_repair_result(
        {
            "files_changed": [
                "tools/mirror_sync/gate_chain_publisher.py",
                "tools/mirror_sync/worker_control_plane.py",
            ],
            "production_touched": False,
            "quality_gate": "PASS",
            "tests": "PASS",
            "blockers": [],
            "git_sync_status": "CERTIFIED_GIT_SYNC",
        },
        authorized_paths=[
            "tools/mirror_sync/gate_chain_publisher.py",
        ],
    )

    assert decision.certified is False
    assert (
        decision.reason
        == "REPAIR_SCOPE_OUTSIDE_INCIDENT_AUTHORIZATION"
    )


def test_auditor_enforces_job_id_sha256_and_commit_bindings():
    payload = {
        "job_id": "WORKER-REPAIR-ABC-A1",
        "result_sha256": "a" * 64,
        "development_sha": "b" * 40,
        "files_changed": [
            "tools/mirror_sync/gate_chain_publisher.py",
        ],
        "production_touched": False,
        "quality_gate": "PASS",
        "tests": "PASS",
        "blockers": [],
        "git_sync_status": "CERTIFIED_GIT_SYNC",
    }

    assert (
        audit_repair_result(
            payload,
            expected_job_id="WORKER-REPAIR-ABC-A2",
        ).reason
        == "REPAIR_JOB_ID_MISMATCH"
    )
    assert (
        audit_repair_result(
            payload,
            expected_result_sha256="c" * 64,
        ).reason
        == "REPAIR_RESULT_SHA256_MISMATCH"
    )
    assert (
        audit_repair_result(
            payload,
            expected_commit_sha="d" * 40,
        ).reason
        == "REPAIR_COMMIT_SHA_MISMATCH"
    )

    approved = audit_repair_result(
        payload,
        authorized_paths=[
            "tools/mirror_sync/gate_chain_publisher.py",
        ],
        expected_job_id="WORKER-REPAIR-ABC-A1",
        expected_result_sha256="a" * 64,
        expected_commit_sha="b" * 40,
    )
    assert approved.certified is True
    assert (
        approved.reason
        == "CERTIFIED_WORKER_REPAIR"
    )


def test_auditor_checks_protected_component_authorization():
    payload = {
        "files_changed": [
            "tools/mirror_sync/gate_chain_publisher.py",
        ],
        "production_touched": False,
        "quality_gate": "PASS",
        "tests": "PASS",
        "blockers": [],
        "git_sync_status": "CERTIFIED_GIT_SYNC",
    }

    denied = audit_repair_result(
        payload,
        require_protected_authorization=True,
    )
    assert denied.certified is False
    assert (
        denied.reason
        == "PROTECTED_COMPONENT_AUTHORIZATION_REQUIRED"
    )

    payload["protected_component_authorized"] = True
    allowed = audit_repair_result(
        payload,
        require_protected_authorization=True,
    )
    assert allowed.certified is True


def test_auditor_independently_reads_canonical_result_and_published_certification(
    tmp_path,
):
    import json

    queue = tmp_path / "queue"
    results_dir = queue / "results"
    published_dir = queue / "published"
    results_dir.mkdir(parents=True)
    published_dir.mkdir(parents=True)

    job_id = "WORKER-REPAIR-INDEP-A1"
    payload = {
        "schema": "edarsahub.worker-result.v2",
        "job_id": job_id,
        "status": "INTEGRATED",
        "git_sync_status": "CERTIFIED_GIT_SYNC",
        "certification": "PENDING_AUDIT_EVIDENCE",
        "tests": "PASS",
        "quality_gate": "PASS",
        "blockers": [],
        "production_touched": False,
        "completed_at_utc": "2026-11-05T00:00:00Z",
        "files_changed": [
            "tools/mirror_sync/gate_chain_publisher.py",
        ],
        "development_sha": "e" * 40,
    }
    result_file = results_dir / f"{job_id}.json"
    result_file.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    unconfirmed = audit_repair_result(
        {"job_id": job_id},
        expected_job_id=job_id,
        verify_canonical_result=True,
        results_dir=results_dir,
    )
    assert unconfirmed.certified is False
    assert (
        unconfirmed.reason
        == "RESULT_NOT_CERTIFIED"
    )

    published_file = (
        published_dir / f"{job_id}.json"
    )
    published_file.write_text(
        json.dumps(
            {
                "job_id": job_id,
                "status": "PUBLISHED",
                "certification": "CERTIFIED",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    confirmed = audit_repair_result(
        {"job_id": job_id},
        authorized_paths=[
            "tools/mirror_sync/gate_chain_publisher.py",
        ],
        expected_job_id=job_id,
        expected_commit_sha="e" * 40,
        verify_canonical_result=True,
        results_dir=results_dir,
    )
    assert confirmed.certified is True
    assert (
        confirmed.reason
        == "CERTIFIED_WORKER_REPAIR"
    )
