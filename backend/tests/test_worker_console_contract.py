"""Tests básicos del contrato Worker Console (Fase 1, solo lectura)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modules.worker_console import contract as C  # noqa: E402


def test_readonly_requires_empty_actions():
    r = C.validate_job({
        "schema": "edarsahub.worker-job.v2", "job_id": "X",
        "mode": "READ_ONLY", "actions": ["algo"], "objective": "y",
    })
    assert r["valid"] is False
    assert any("actions=[]" in e for e in r["errors"])


def test_readonly_empty_actions_ok():
    r = C.validate_job({
        "schema": "edarsahub.worker-job.v2", "job_id": "X",
        "mode": "READ_ONLY", "actions": [], "objective": "y",
    })
    assert r["valid"] is True


def test_missing_job_id_fails():
    r = C.validate_job({
        "schema": "edarsahub.worker-job.v2", "mode": "READ_ONLY",
        "actions": [], "objective": "y",
    })
    assert r["valid"] is False


def test_interpret_certified_pass():
    interp = C.interpret_result({
        "certification": "CERTIFIED_READ_ONLY", "quality_gate": "PASS",
        "blockers": [], "production_touched": False,
    })
    assert interp["verdict"] == "PASS"
    assert interp["production_touched"] is False


def test_interpret_marker_fallback(tmp_path):
    f = tmp_path / "m.json"
    f.write_text("published=1\ncertification=NOT_CERTIFIED\n", encoding="utf-8")
    doc = C.read_json_file(f)
    assert isinstance(doc, dict)
    assert doc.get("certification") == "NOT_CERTIFIED"



def test_public_control_plane_status_redacts_maintenance():
    source = {
        "schema": "edarsahub.worker-control-plane.v1",
        "maintenance": {"incidents": [{"incident_id": "SENSITIVE"}]},
        "runtime": {"status": "HEALTHY"},
    }
    result = C.public_control_plane_status(source)
    assert "maintenance" not in result
    assert result["runtime"] == {"status": "HEALTHY"}
    assert "maintenance" in source


def test_public_control_plane_status_fails_closed_for_non_dict():
    assert C.public_control_plane_status(None) is None
    assert C.public_control_plane_status([]) is None
    assert C.public_control_plane_status([{"maintenance": {"incident_id": "SENSITIVE"}}]) is None


def test_worker_result_endpoint_does_not_expose_raw_document():
    """Nonprivileged users must not receive arbitrary Worker result payloads."""
    import inspect
    from modules.worker_console import routes

    source = inspect.getsource(routes.result)
    assert '"raw"' not in source
    assert '"interpretation"' in source
