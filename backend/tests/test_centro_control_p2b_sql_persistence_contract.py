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


def test_metrics_do_not_fabricate_check_success_or_score():
    assert 'tasa_exito = 100.0' not in STORE
    assert '"checks_exitosos": total_checks' not in STORE
    assert '"checks_exitosos": None' in STORE
    assert '"tasa_exito_checks": None' in STORE
    assert '"score_estabilidad": None' in STORE
    assert 'INSUFFICIENT_CANONICAL_CHECK_RESULT_EVIDENCE' in STORE
    assert 'sin_evidencia_canonica_suficiente' in ROUTES


def test_blindaje_requires_explicit_registry_evidence():
    assert "LIKE '%Blindaje%'" not in STORE
    assert "LIKE '%CentroControl%'" not in STORE
    assert '"status": "NO_CANONICAL_SQL_REGISTRY"' in STORE
    assert '"registry_tables": []' in STORE
    assert 'P2A_R2_NO_EXPLICIT_REGISTRY_CERTIFIED' in STORE
