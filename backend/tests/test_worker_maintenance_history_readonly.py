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
    assert report["recurring_signatures"] == [{"signature": "RECURRING_FAILURE", "count": 3}]
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
