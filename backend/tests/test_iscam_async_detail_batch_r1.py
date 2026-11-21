from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'backend' / 'api' / 'admin_scheduler_resync.py'
BACKFILL = ROOT / 'backend' / 'scripts' / 'backfill_detalle_producto_pendientes.py'
FRONTEND = ROOT / 'frontend' / 'src' / 'portal-inteligencia' / 'pages' / 'ReportesISCAMPage.jsx'


def test_async_detail_job_is_background_sequential_and_bounded():
    text = BACKEND.read_text(encoding='utf-8')
    assert '@router.post("/resync/iscam-detail/jobs", status_code=202)' in text
    assert 'background_tasks.add_task(_run_iscam_detail_batch_job' in text
    assert "max_attempts = 2" in text
    assert "'max_retries_per_day': 1" in text
    assert "'execution_mode': 'SEQUENTIAL_SINGLE_REAL_PASS'" in text
    assert "commit=True" in text
    assert "'JOB_PARTIAL'" in text
    assert "_ISCAM_BATCH_STALE_SECONDS = 600" in text


def test_async_detail_job_uses_existing_sql_log_as_persistent_progress_store():
    text = BACKEND.read_text(encoding='utf-8')
    assert "TipoSync = 'iscam_detail_batch'" in text
    assert 'OUTPUT INSERTED.ResyncLogID AS job_id' in text
    assert "Estado IN ('JOB_QUEUED', 'JOB_RUNNING')" in text
    assert "RegistrosAfectados = %s" in text


def test_frontend_starts_one_job_and_polls_with_recovery():
    text = FRONTEND.read_text(encoding='utf-8')
    assert "const [syncJobId, setSyncJobId] = useState(null);" in text
    assert "apiPost('/admin/scheduler/resync/iscam-detail/jobs'" in text
    assert "apiGet(`/admin/scheduler/resync/iscam-detail/jobs/${syncJobId}`)" in text
    assert "apiGet('/admin/scheduler/resync/iscam-detail/active'" in text
    assert "pollFailureStartedAt" in text
    assert "elapsedMs < 90000" in text
    assert "return 15000;" in text
    assert "Sincronización en curso · reconectando al seguimiento" in text
    assert "consecutivePollErrors >= 3" not in text
    assert "Proceso terminado sin bucle:" in text
    assert "Días procesados" in text


def test_timeout_codes_are_explicit_for_one_retry_only():
    text = BACKFILL.read_text(encoding='utf-8')
    assert '("TIMED OUT", "POS_TIMEOUT")' in text
    assert '("TIMEOUT", "POS_TIMEOUT")' in text
    assert '("DBPROCESS IS DEAD", "POS_CONNECTION_UNAVAILABLE")' in text
