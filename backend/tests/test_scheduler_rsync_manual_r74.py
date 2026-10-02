from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'backend' / 'api' / 'admin_scheduler_resync.py'
FRONTEND = ROOT / 'frontend' / 'src' / 'components' / 'admin' / 'ResyncPanel.jsx'


def test_kpi_dry_run_does_not_report_detail_failure_as_origin_failure():
    text = BACKEND.read_text(encoding='utf-8')
    dry = text.split('async def _ejecutar_dry_run(', 1)[1].split('async def _ejecutar_sync_real(', 1)[0]
    assert "'success': True" in dry
    assert "'stage': 'HEADER_KPI'" in dry
    assert "'detail_success': detalle_success" in dry
    assert 'Fallo en validacion auxiliar DETALLE_ISCAM' in dry
    assert 'execute_query_on_server(config, query)' in dry
    assert 'ConnectionStatus.ONLINE' in dry


def test_real_kpi_success_is_not_blocked_by_auxiliary_detail():
    text = BACKEND.read_text(encoding='utf-8')
    real = text.split('async def _ejecutar_sync_real(', 1)[1]
    assert "'success': bool(resultado.success)" in real
    assert "'header_success': bool(resultado.success)" in real
    assert "'warning_message': detalle_warning" in real
    assert "'error_message': resultado.error_message" in real


def test_frontend_rsync_uses_long_timeout_and_surfaces_real_error():
    text = FRONTEND.read_text(encoding='utf-8')
    assert "}, { timeout: 120000 });" in text
    assert "errorData?.error_message" in text
    assert "resultadoError?.error_message" in text
    assert "TIMEOUT_CLIENTE" in text
    assert "error.response?.data?.detail || 'Error de ejecución'" not in text


def test_frontend_surfaces_auxiliary_detail_warning():
    text = FRONTEND.read_text(encoding='utf-8')
    assert 'r.data.warning_message || resultado.warning_message' in text
    assert 'Advertencia' in text
