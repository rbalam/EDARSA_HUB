from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTES = ROOT / 'backend' / 'modules' / 'inteligencia_comercial' / 'iscam_routes.py'
FRONTEND = ROOT / 'frontend' / 'src' / 'portal-inteligencia' / 'pages' / 'ReportesISCAMPage.jsx'


def test_freshness_uses_runtime_and_previous_closed_day():
    text = ROUTES.read_text(encoding='utf-8')
    assert '@iscam_router.get("/freshness")' in text
    assert 'dbo.vw_Comercial_KPIs_Diarios_v2_Runtime' in text
    assert 'ZoneInfo("America/Mexico_City")' in text
    assert 'previous_closed_day = today_local - timedelta(days=1)' in text
    assert '"stale": stale' in text
    assert '"missing_from": missing_from' in text
    assert '"missing_to": missing_to' in text


def test_manual_sync_is_dry_run_gated_and_refetches():
    text = FRONTEND.read_text(encoding='utf-8')
    assert 'apiGet, apiPost, ESTADO' in text
    assert 'RefreshCw' in text
    assert 'Sincronizar faltantes' in text
    assert "'/inteligencia/iscam/freshness'" in text
    assert "'/admin/scheduler/resync/execute'" in text
    assert 'dry_run: true' in text
    assert 'dry_run: false' in text
    assert 'splitDateChunks(syncFrom, syncTo, 1)' in text
    assert 'Promise.all([fetchReport(), fetchFreshness()])' in text
