from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTES = (ROOT / 'core' / 'centro_control' / 'routes.py').read_text(encoding='utf-8')
STORE = (ROOT / 'core' / 'centro_control' / 'sql_store.py').read_text(encoding='utf-8')
FRONT = (ROOT.parent / 'frontend' / 'src' / 'pages' / 'CentroControl.jsx').read_text(encoding='utf-8')


def test_no_process_local_centro_control_state_remains():
    for token in ['_historial_eventos: List', '_alertas_activas: List', '_bitacora_cambios: List', '_metricas_estabilidad: Dict']:
        assert token not in ROUTES


def test_certified_sql_tables_are_the_only_persistence_tables():
    assert 'dbo.Alertas_Sistema' in STORE
    assert 'dbo.Scheduler_BitacoraJobs' in STORE
    assert 'CREATE TABLE' not in STORE.upper()
    assert 'MONGO' not in STORE.upper()


def test_routes_use_sql_store_and_blindaje_truth_endpoint():
    assert 'from core.centro_control import sql_store as cc_store' in ROUTES
    assert '@router.get("/blindaje/modulos")' in ROUTES
    assert 'cc_store.list_alerts' in ROUTES
    assert 'cc_store.list_events' in ROUTES
    assert 'cc_store.list_bitacora' in ROUTES
    assert 'cc_store.metrics()' in ROUTES


def test_frontend_mock_blindaje_removed():
    assert "const modulosBlindados = [" not in FRONT
    assert "api.get('/centro-control/blindaje/modulos')" in FRONT
    assert 'Sin catálogo SQL canónico de blindaje' in FRONT
