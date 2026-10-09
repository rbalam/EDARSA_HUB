from pathlib import Path

from modules.sync_historicos.atomic_executor import registered_atomic_handlers


ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = ROOT / "modules/sync_historicos/atomic_executor.py"
SCRIPT = ROOT / "scripts/run_sync_historical_atomic.py"
BRIDGE = ROOT.parent / "tools/mirror_sync/universal_job_bridge.py"
DISPATCHER = ROOT.parent / "tools/mirror_sync/universal_job_dispatcher.py"


def test_atomic_executor_is_closed_registry_and_reuses_official_handler():
    text = EXECUTOR.read_text(encoding="utf-8")
    assert registered_atomic_handlers() == ("comercial_ventas_cerradas",)
    assert "_ejecutar_sync_real" in text
    assert "_ejecutar_dry_run" in text
    assert "eval(" not in text
    assert "exec(" not in text
    assert "subprocess" not in text


def test_atomic_entrypoint_accepts_only_persisted_control_id():
    text = SCRIPT.read_text(encoding="utf-8")
    assert '--sync-control-id' in text
    assert '--sql' not in text
    assert '--command' not in text
    assert '--path' not in text


def test_protected_open_sales_sync_is_not_referenced_by_atomic_executor():
    text = (
        EXECUTOR.read_text(encoding="utf-8")
        + SCRIPT.read_text(encoding="utf-8")
    ).lower()
    assert "sync_comercial_abiertas_v2" not in text


def test_worker_generic_historical_mode_is_closed():
    bridge = BRIDGE.read_text(encoding="utf-8")
    dispatcher = DISPATCHER.read_text(encoding="utf-8")
    assert 'SYNC_HISTORICAL_ATOMIC_MODE = "SYNC_HISTORICAL_ATOMIC"' in bridge
    assert 'SYNC_HISTORICAL_ATOMIC_MODE = "SYNC_HISTORICAL_ATOMIC"' in dispatcher
    block = dispatcher.split(
        "if mode == SYNC_HISTORICAL_ATOMIC_MODE:", 1
    )[1].split("if mode == MPRO_FULL_HISTORY_MODE:", 1)[0]
    assert "run_sync_historical_atomic.py" in block
    assert 'job.get("command")' not in block
    assert 'job.get("path")' not in block
    assert "shell=True" not in block
