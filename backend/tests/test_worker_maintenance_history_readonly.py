"""G4 Maintenance historical inventory security and integration contract."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.mirror_sync import worker_maintenance_history_readonly as audit
from tools.mirror_sync import worker_maintenance_runtime as maintenance
from tools.mirror_sync import worker_repair_capability_registry as registry
from tools.mirror_sync import worker_repair_planner as planner


def _write(directory, name, payload):
    (directory / name).write_text(json.dumps(payload), encoding="utf-8")


def test_g4_aggregate_and_sensitive_identifiers_never_leave_helper(tmp_path, monkeypatch):
    incident_dir = tmp_path / "incidents"
    incident_dir.mkdir()
    _write(incident_dir, "one.json", {
        "incident_id": "SECRET_INCIDENT_123", "state": "REPAIR_REQUIRED",
        "problem_signature": "PROCESSING_STALE_DURING_LONG_RUNNING_CHECK_WITHOUT_SLOT_HEARTBEAT",
        "source_job_id": "SECRET_SOURCE_JOB_123", "capability_code": "TEST_CAPABILITY",
        "repair_job_id": "SECRET_REPAIR_JOB", "attempts": 2,
        "metadata": {"password": "PRIVATE_PASSWORD"},
    })
    monkeypatch.setattr(maintenance, "INCIDENT_DIR", incident_dir)
    monkeypatch.setattr(planner, "registered_capabilities", lambda: ("TEST_CAPABILITY",))
    monkeypatch.setattr(registry, "iter_learned_capabilities", lambda: ())
    result = audit.collect()
    serialized = json.dumps(result)
    assert result["incident_count"] == 1
    assert result["pending_total"] == 1
    assert result["pending_sample"][0]["capability_registered"] is True
    assert result["certification"] == "EVIDENCE_ONLY_NOT_G4_CERTIFIED"
    for secret in ("SECRET_INCIDENT_123", "SECRET_SOURCE_JOB_123", "SECRET_REPAIR_JOB", "PRIVATE_PASSWORD"):
        assert secret not in serialized


def test_g4_recurrence_and_missing_fields(tmp_path, monkeypatch):
    incident_dir = tmp_path / "incidents"
    incident_dir.mkdir()
    for i in range(3):
        _write(incident_dir, f"{i}.json", {
            "incident_id": f"WORKER-{i}", "state": "REJECTED",
            "problem_signature": "RECURRING_FAILURE", "attempts": 2,
        })
    monkeypatch.setattr(maintenance, "INCIDENT_DIR", incident_dir)
    monkeypatch.setattr(planner, "registered_capabilities", lambda: ())
    monkeypatch.setattr(registry, "iter_learned_capabilities", lambda: ())
    report = audit.collect()
    assert report["recurring_signatures"] == [{"signature": "SIG:" + audit._fingerprint("RECURRING_FAILURE"), "count": 3}]
    assert report["missing_fields"]["capability_code"] == 3
    assert report["missing_fields"]["source_job_id"] == 3
    assert report["states"]["REJECTED"] == 3


def test_g4_rejects_symlinks_and_excessive_files(tmp_path, monkeypatch):
    incident_dir = tmp_path / "incidents"
    incident_dir.mkdir()
    target = tmp_path / "private.json"
    target.write_text('{"secret":"should-not-read"}', encoding="utf-8")
    (incident_dir / "incident.json").symlink_to(target)
    monkeypatch.setattr(maintenance, "INCIDENT_DIR", incident_dir)
    with pytest.raises(ValueError, match="G4_UNSAFE_INCIDENT_PATH"):
        audit.collect()
    (incident_dir / "incident.json").unlink()
    monkeypatch.setattr(audit, "MAX_FILES", 0)
    _write(incident_dir, "real.json", {"incident_id": "ONE"})
    with pytest.raises(ValueError, match="G4_INCIDENT_LIMIT_EXCEEDED"):
        audit.collect()


def test_g4_request_contract_accepted_only_with_zero_parameters():
    from tools.mirror_sync import universal_job_bridge as bridge
    check = {"type": "worker_maintenance_history_readonly"}
    assert bridge.validate_check(check, 0) == []
    assert bridge.validate_check({**check, "path": "/etc"}, 0)
    assert check["type"] in bridge.READ_ONLY_CHECKS
    assert check["type"] in bridge.ALLOWED_CHECKS


def test_g4_registered_in_canonical_dispatcher_and_publisher():
    from tools.mirror_sync import gate_chain_publisher as publisher
    assert "worker_maintenance_history_readonly" in publisher.ALLOWED_CHECKS
    dispatcher = Path(__file__).resolve().parents[2] / "tools/mirror_sync/universal_job_dispatcher.py"
    source = dispatcher.read_text(encoding="utf-8")
    assert 'elif kind == "worker_maintenance_history_readonly":' in source
    assert 'response["maintenance_history_evidence"]' in source


def test_publisher_certifies_maintenance_history_readonly_and_truncates_large_repo_evidence():
    from tools.mirror_sync import universal_job_result_publisher as pub
    from tools.mirror_sync import worker_result_semantic_extract as ex

    maint_result = {
        "schema": "edarsahub.worker-result.v2",
        "job_id": "SEM-WORKER_REPAIR_KNOWLEDGE_LOOP-MAINT-TEST1",
        "status": "READ_ONLY_COMPLETE",
        "quality_gate": "PASS",
        "tests": "PASS",
        "percent_complete": 100,
        "production_touched": False,
        "files_changed": [],
        "blockers": [],
        "checks": [
            {
                "type": "worker_maintenance_history_readonly",
                "status": "PASS",
                "maintenance_history_evidence": {
                    "schema": "edarsahub.worker-maintenance-history-readonly.v1",
                    "mode": "READ_ONLY",
                    "status": "PASS",
                    "incident_count": 3,
                    "pending_total": 1,
                    "production_allowed": False,
                },
            }
        ],
    }
    cert = pub.certification_evidence(maint_result)
    assert cert["certified"] is True
    assert cert["certification"] == "CERTIFIED_READ_ONLY"
    assert cert["percent_complete"] == 100
    public = pub.sanitize(maint_result)
    assert public["certification"] == "CERTIFIED_READ_ONLY"
    assert "maintenance_history_evidence" in public

    # Large valid repository_contract_audit (> 65536 bytes) truncates cleanly instead of returning None
    large_entries = [
        {
            "path": f"backend/modules/mod_{i}/service.py",
            "candidate_ownership": "backend",
            "matched_terms": ["crm", "rbac"],
            "symbols": [f"symbol_{i}_{j}_long_name_for_size_budget" for j in range(25)],
        }
        for i in range(95)
    ]
    raw_repo = {
        "status": "PASS",
        "mode": "READ_ONLY_REPOSITORY",
        "summary": {"scanned_files": 95, "matched_files": 95, "skipped_sensitive": 0},
        "truncated": False,
        "evidence": large_entries,
    }
    assert len(json.dumps(raw_repo).encode("utf-8")) > ex.MAX_SERIALIZED_BYTES
    sanitized = ex.sanitize_repository_contract_payload(raw_repo)
    assert sanitized is not None
    assert sanitized["checks"][0]["truncated"] is True
    assert len(sanitized["checks"][0]["evidence"]) > 0
    assert len(json.dumps(sanitized, ensure_ascii=False, sort_keys=True).encode("utf-8")) <= ex.MAX_SERIALIZED_BYTES

    # Sensitive markers must still fail closed
    bad_repo = {
        **raw_repo,
        "evidence": [{"path": "backend/modules/x.py", "matched_terms": ["password=LEAKED"]}],
    }
    assert ex.sanitize_repository_contract_payload(bad_repo) is None
