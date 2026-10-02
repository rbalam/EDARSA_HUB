from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
M=ROOT/"backend/modules/comercial/resync_batch_jobs.py"
A=ROOT/"backend/api/admin_scheduler_resync.py"

def test_batch_contract():
    t=M.read_text(encoding="utf-8")
    assert 'LOCK_NAME = "sync_comercial_v2"' in t
    assert "_ejecutar_dry_run" in t and "_ejecutar_sync_real" in t
    assert "start_heartbeat_loop" in t and "await lock.release()" in t
    assert "BLOCK_DAYS = 5" in t and "MAX_ATTEMPTS = 3" in t
    assert "force_release" not in t
    assert "sync_comercial_abiertas_v2" not in t
    assert "force_refresh_existing" in t
    assert "Sistema_Sync_ResyncLog" in t

def test_api_contract():
    t=A.read_text(encoding="utf-8")
    assert "class ComercialRangeBatchRequest" in t
    assert '@router.post("/resync/comercial-range/jobs"' in t
    assert '@router.get("/resync/comercial-range/active")' in t
    assert '@router.get("/resync/comercial-range/jobs/{job_id}")' in t
    assert '@router.post("/resync/comercial-range/jobs/{job_id}/resume")' in t
