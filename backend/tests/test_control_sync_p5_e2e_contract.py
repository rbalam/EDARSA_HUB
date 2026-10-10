from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'backend'
FRONTEND = ROOT / 'frontend'
APP = (FRONTEND / 'src' / 'App.js').read_text(encoding='utf-8')
SYNC_PAGE = (FRONTEND / 'src' / 'pages' / 'SyncMonitor.js').read_text(encoding='utf-8')
CC_PAGE = (FRONTEND / 'src' / 'pages' / 'CentroControl.jsx').read_text(encoding='utf-8')
SYNC_ROUTES = (BACKEND / 'modules' / 'sync_monitor' / 'routes.py').read_text(encoding='utf-8')
CC_ROUTES = (BACKEND / 'core' / 'centro_control' / 'routes.py').read_text(encoding='utf-8')
NAV = json.loads((FRONTEND / 'src' / 'config' / 'enterpriseNavigationRegistry.json').read_text(encoding='utf-8'))

def _menu_by_path(path):
    return [v for v in NAV.get('menuMappings', {}).values() if v.get('expectedPath') == path]

def test_both_pages_have_protected_app_routes():
    assert '<Route path="centro-control" element={<CentroControl />} />' in APP
    assert '<Route path="admin/sync-monitor" element={<SyncMonitor />} />' in APP
    assert '<Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>' in APP

def test_both_menu_entries_are_active_and_resolve_to_real_routes():
    cc = _menu_by_path('/centro-control')
    sm = _menu_by_path('/admin/sync-monitor')
    assert cc and cc[0].get('status') == 'active'
    assert sm and sm[0].get('status') == 'active'

def test_sync_monitor_data_loading_error_and_empty_states_exist():
    assert '/api/admin/sync-monitor' in SYNC_PAGE
    assert 'Cargando monitor...' in SYNC_PAGE
    assert 'Error cargando datos' in SYNC_PAGE
    assert 'Sin procesos registrados' in SYNC_PAGE
    assert 'Sin errores en las últimas 24 horas' in SYNC_PAGE
    assert 'Sin actividad reciente' in SYNC_PAGE
    assert 'SIN_SLA_THRESHOLD_CONFIGURADO' in SYNC_PAGE
    assert 'SIN_TELEMETRIA' in SYNC_PAGE

def test_centro_control_loads_canonical_endpoints_and_empty_states():
    assert "api.get('/centro-control/blindaje/modulos')" in CC_PAGE
    assert "api.post('/centro-control/regresiones')" in CC_PAGE
    assert "api.post('/centro-control/alertas/acknowledge'" in CC_PAGE
    assert 'Cargando Centro de Control...' in CC_PAGE
    assert 'EstadoVacio' in CC_PAGE
    assert 'Sin catálogo SQL canónico de blindaje' in CC_PAGE
    assert 'data-testid="centro-control"' in CC_PAGE

def test_sync_monitor_has_strict_explicit_rbac_on_all_endpoints():
    assert SYNC_ROUTES.count('require_explicit_permission("sync_monitor_VER")') >= 3
    assert 'Depends(get_current_user)' not in SYNC_ROUTES

def test_centro_control_replaces_exactly_32_http_dependencies_with_sql_rbac():
    assert 'from core.rbac.middleware import require_explicit_permission' in CC_ROUTES
    assert CC_ROUTES.count('Depends(require_explicit_permission("CENTRO_CONTROL_VER"))') == 32
    assert 'Depends(get_current_user)' not in CC_ROUTES

def test_websocket_handlers_are_preserved():
    assert '@router.websocket' in CC_ROUTES
    assert 'get_notification_manager()' in CC_ROUTES
    assert 'WebSocketDisconnect' in CC_ROUTES

def test_persistence_and_no_mock_contract_survives_p5():
    assert 'from core.centro_control import sql_store as cc_store' in CC_ROUTES
    assert 'const modulosBlindados = [' not in CC_PAGE
