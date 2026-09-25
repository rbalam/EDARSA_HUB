from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'backend' / 'api' / 'admin_scheduler_resync.py'
FRONTEND = ROOT / 'frontend' / 'src' / 'portal-inteligencia' / 'pages' / 'ReportesISCAMPage.jsx'
CLIENT = ROOT / 'frontend' / 'src' / 'portal-inteligencia' / 'api' / 'client.js'


def test_progress_endpoints_use_threadpool_friendly_sync_handlers_and_active_recovery():
    text = BACKEND.read_text(encoding='utf-8')
    assert '@router.get("/resync/iscam-detail/active")' in text
    assert 'def obtener_iscam_detail_batch_activo(' in text
    assert 'async def obtener_iscam_detail_batch_activo(' not in text
    assert 'def obtener_iscam_detail_batch_job(' in text
    assert 'async def obtener_iscam_detail_batch_job(' not in text
    assert 'def crear_iscam_detail_batch_job(' in text
    assert "return {'success': True, 'active': False}" in text


def test_polling_never_relaunches_server_job_and_recovers_with_backoff():
    text = FRONTEND.read_text(encoding='utf-8')
    poll_block = text.split('let pollFailureStartedAt = null;', 1)[1].split('const syncMissingClosedDays', 1)[0]
    retry_block = poll_block.split("if (res.estado !== ESTADO.OK || !res.data?.success) {", 1)[1].split("pollFailureStartedAt = null;", 1)[0]
    assert "apiPost('/admin/scheduler/resync/iscam-detail/jobs'" not in retry_block
    assert 'setSyncJobId(null);' not in retry_block
    assert 'elapsedMs >= 90000' in retry_block
    assert 'timer = setTimeout(poll, scheduleRetry(elapsedMs));' in retry_block
    assert 'return 15000;' in poll_block
    assert "prev?.tipo === 'warning' ? null : prev" in poll_block


def test_frontend_recovers_existing_active_job_after_reload_or_navigation():
    text = FRONTEND.read_text(encoding='utf-8')
    assert "apiGet('/admin/scheduler/resync/iscam-detail/active'" in text
    assert 'Continuando seguimiento sin crear otro trabajo.' in text
    assert 'setSyncJobId(String(res.data.job_id));' in text


def test_api_client_preserves_transport_diagnostics():
    text = CLIENT.read_text(encoding='utf-8')
    assert text.count("error_code: err?.code || null") == 2
    assert text.count("const data = err?.response?.data ?? null;") == 2
    assert text.count("const mensaje = typeof detail === 'string'") == 2
