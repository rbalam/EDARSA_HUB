from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANAGER = ROOT / "core/scheduler/scheduler_manager.py"


def _closed_block():
    text = MANAGER.read_text(encoding="utf-8")
    start = text.index("async def _run_sync_comercial_v2_job")
    end = text.index("async def _run_sync_comercial_abiertas_v2_job")
    return text[start:end]


def test_closed_sales_runs_off_main_event_loop():
    block = _closed_block()
    assert "await asyncio.to_thread(" in block
    assert "asyncio.run(" in block
    assert "execute_sync_comercial_v2()" in block
    assert "execute_sync_comercial_v2(self.db)" not in block


def test_closed_sales_keeps_lock_heartbeat():
    block = _closed_block()
    assert "await lock.start_heartbeat_loop(" in block
    assert "interval_seconds=30" in block
    assert "extend_seconds=600" in block


def test_open_sales_wrapper_remains_present():
    text = MANAGER.read_text(encoding="utf-8")
    assert "async def _run_sync_comercial_abiertas_v2_job" in text
