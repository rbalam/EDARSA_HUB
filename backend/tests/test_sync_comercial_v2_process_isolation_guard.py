from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOB = ROOT / "core/scheduler/jobs/sync_comercial_v2_job.py"
MANAGER = ROOT / "core/scheduler/scheduler_manager.py"
WORKER = ROOT / "scripts/sync_comercial_v2_header_worker.py"

def test_process_isolation_contract():
    job = JOB.read_text(encoding="utf-8")
    manager = MANAGER.read_text(encoding="utf-8")
    worker = WORKER.read_text(encoding="utf-8")
    assert "isolated_headers: bool = False" in job
    assert "def _run_header_sync_isolated(" in job
    assert "subprocess.run(" in job
    assert "SYNC_HEADER_PROCESS_TIMEOUT_SECONDS" in job
    assert "isolated_headers=True" in manager
    assert 'p.add_argument("--run-id", required=True)' in worker
