from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / 'api' / 'admin_scheduler_resync.py'


def _section(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]


def test_manual_resync_dry_run_uses_origin_connection():
    text = SOURCE.read_text(encoding='utf-8')
    dry_run = _section(text, 'async def _ejecutar_dry_run(', 'async def _ejecutar_sync_real(')
    assert 'execute_query_on_server(config, query)' in dry_run
    assert 'conn = get_sql_connection()' not in dry_run
    assert "unidad_config.get('unidad_negocio_pk')" in dry_run
    assert 'ConnectionStatus.ONLINE' in dry_run


def test_manual_resync_normalizes_system_and_preserves_unit_pk():
    text = SOURCE.read_text(encoding='utf-8')
    config = _section(text, 'def _get_unidad_config(', '# =============================================================================\n# VALIDACIONES')
    assert "'unidad_negocio_pk': str(server_data.get('unidad_negocio_pk', ''))" in config
    assert "if 'SOFT' in raw_sistema" in config
    assert "sistema = 'SOFTRESTAURANT'" in config


def test_manual_resync_real_uses_canonical_pydantic_field():
    text = SOURCE.read_text(encoding='utf-8')
    real = _section(text, 'async def _ejecutar_sync_real(', '@router.get("/resync/history")')
    assert 'unidad_negocio_pk=unidad_negocio_pk' in real
    assert 'unidad_negocio_id=unidad_negocio_id' not in real
    assert "if sistema == 'SOFTRESTAURANT'" in real


def test_manual_resync_dry_run_failure_is_not_reported_as_success():
    text = SOURCE.read_text(encoding='utf-8')
    endpoint = _section(text, 'async def ejecutar_resync(', '@router.get("/resync/history")')
    assert "if not resultado_simulado.get('success')" in endpoint
    assert "accion='DRY_RUN_FAILED'" in endpoint
