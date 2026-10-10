from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "modules/sync_historicos/parent_executor.py"
SCRIPT = ROOT / "scripts/run_sync_historical_parent.py"
BRIDGE = ROOT.parent / "tools/mirror_sync/universal_job_bridge.py"
DISPATCHER = ROOT.parent / "tools/mirror_sync/universal_job_dispatcher.py"


def test_parent_orchestrator_keeps_atomic_boundary_and_safe_controls():
    text = PARENT.read_text(encoding="utf-8")
    assert "execute_atomic_unit_sync" in text
    assert "CancelRequested" in text
    assert "PauseRequested" in text
    assert "CANCELLED_SAFE" in text
    assert "PERMANENT_FAILURE" in text
    assert "retry_backoff_seconds" in text
    assert "2 **" in text


def test_parent_entrypoint_accepts_only_persisted_parent_id():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "--parent-sync-control-id" in text
    assert "--command" not in text
    assert "--path" not in text
    assert "--sql" not in text


def test_worker_parent_mode_is_closed_and_fixed():
    bridge = BRIDGE.read_text(encoding="utf-8")
    dispatcher = DISPATCHER.read_text(encoding="utf-8")
    assert 'SYNC_HISTORICAL_PARENT_MODE = "SYNC_HISTORICAL_PARENT"' in bridge
    assert 'SYNC_HISTORICAL_PARENT_MODE = "SYNC_HISTORICAL_PARENT"' in dispatcher
    block = dispatcher.split(
        "if mode == SYNC_HISTORICAL_PARENT_MODE:", 1
    )[1].split("if mode == SYNC_HISTORICAL_ATOMIC_MODE:", 1)[0]
    assert "run_sync_historical_parent.py" in block
    assert 'job.get("command")' not in block
    assert 'job.get("path")' not in block
    assert "shell=True" not in block


def test_protected_open_sales_sync_absent():
    text = (
        PARENT.read_text(encoding="utf-8")
        + SCRIPT.read_text(encoding="utf-8")
    ).lower()
    assert "sync_comercial_abiertas_v2" not in text
