from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / "tools/mirror_sync/universal_job_bridge.py"
DISPATCHER = ROOT / "tools/mirror_sync/universal_job_dispatcher.py"
GUARD = ROOT / "tools/mirror_sync/git_divergence_guard.py"
HEALTH = ROOT / "tools/mirror_sync/runtime_health_publisher.py"
CONTROL = ROOT / "tools/mirror_sync/worker_control_plane.py"
SCRIPT = ROOT / "backend/scripts/run_comercial_open_day_sync_worker.py"


def test_bridge_has_closed_open_day_sync_mode():
    text = BRIDGE.read_text(encoding="utf-8")
    assert (
        'COMERCIAL_OPEN_DAY_SYNC_MODE = '
        '"COMERCIAL_OPEN_DAY_SYNC"'
    ) in text
    assert "COMERCIAL_OPEN_DAY_SYNC_FECHA_INVALID" in text
    assert (
        "COMERCIAL_OPEN_DAY_SYNC_CONFIRMATION_REQUIRED"
        in text
    )
    assert (
        "COMERCIAL_OPEN_DAY_SYNC_ONLY_SQL_AUDIT_ALLOWED"
        in text
    )


def test_dispatcher_uses_fixed_script_without_job_shell():
    text = DISPATCHER.read_text(encoding="utf-8")
    block = text.split(
        "if mode == COMERCIAL_OPEN_DAY_SYNC_MODE:", 1
    )[1].split(
        "if mode == COMERCIAL_RANGE_RESYNC_MODE:", 1
    )[0]
    assert "run_comercial_open_day_sync_worker.py" in block
    assert "confirm_comercial_open_day_sync" in block
    assert 'job.get("command")' not in block
    assert 'job.get("shell")' not in block
    assert "shell=True" not in block


def test_fixed_script_reuses_protected_scheduler_handler():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "run_sync_comercial_abiertas_v2_manual" in text
    assert "fecha=fecha" in text
    assert "comercial_open_day_summary" in text


def test_open_day_operational_mode_has_long_grace_no_git_writer():
    guard = GUARD.read_text(encoding="utf-8")
    health = HEALTH.read_text(encoding="utf-8")
    control = CONTROL.read_text(encoding="utf-8")
    assert "COMERCIAL_OPEN_DAY_SYNC" in guard
    assert "COMERCIAL_OPEN_DAY_SYNC" in health
    assert "COMERCIAL_OPEN_DAY_SYNC" in control
