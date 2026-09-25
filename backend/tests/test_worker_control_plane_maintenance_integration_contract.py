from pathlib import Path

from tools.mirror_sync import worker_control_plane as control


def test_control_plane_exposes_maintenance_summary():
    payload = control.maintenance_runtime_summary()

    assert payload["schema"] == "edarsahub.worker-maintenance-summary.v1"
    assert payload["production_touched"] is False
    assert isinstance(payload["incident_count"], int)
    assert isinstance(payload["incidents"], list)


def test_control_plane_maintenance_integration_is_read_only():
    source = Path(control.__file__).read_text(encoding="utf-8")

    assert "read_runtime_incident" in source

    helper = source[
        source.index("def maintenance_runtime_summary"):
        source.index("def cycle")
    ]

    assert "declare_runtime_incident(" not in helper
    assert "register_repair_attempt(" not in helper
    assert "register_repair_result(" not in helper
    assert "audit_runtime_incident(" not in helper


def test_cycle_surfaces_maintenance_without_second_control_plane():
    source = Path(control.__file__).read_text(encoding="utf-8")

    assert '"maintenance": maintenance_runtime_summary()' in source
    assert "worker_maintenance_runtime" in source
    assert "second_control_plane" not in source.lower()


def test_production_remains_fail_closed():
    source = Path(control.__file__).read_text(encoding="utf-8")

    assert '"production_touched": False' in source
    assert "Edarsahub_Produccion" not in source
