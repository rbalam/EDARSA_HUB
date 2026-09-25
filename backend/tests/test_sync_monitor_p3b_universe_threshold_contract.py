from pathlib import Path

SERVICE = (Path(__file__).resolve().parents[1] / 'modules' / 'sync_monitor' / 'service.py').read_text(encoding='utf-8')


def test_no_operational_stale_threshold_hardcodes_remain():
    assert 'STALE_THRESHOLDS' not in SERVICE
    for token in ['"VENTAS": 30', '"INVENTARIOS": 120', '"COMPRAS": 360', '"CATALOGOS": 1440']:
        assert token not in SERVICE


def test_missing_canonical_sla_is_explicit_not_stale():
    assert 'P3A_R3_NO_CANONICAL_SYNC_SLA_CONFIG_CERTIFIED' in SERVICE
    assert 'return "SIN_SLA_THRESHOLD_CONFIGURADO"' in SERVICE
    assert 'return "SIN_TELEMETRIA"' in SERVICE
    assert 'threshold_minutes is None' in SERVICE


def test_certified_universe_sources_are_explicit():
    assert '"server_catalog": "dbo.Servidores_Conexiones"' in SERVICE
    assert '"process_sources": ["dbo.Compras_Sync_Log", "dbo.Comercial_SyncLog_v2"]' in SERVICE
    assert '"generic_telemetry_source": "dbo.Sync_Logs"' in SERVICE
    assert 'GLOBAL_UNSCOPED_NO_SERVER_ID' in SERVICE


def test_generic_sync_logs_not_merged_into_server_processes():
    assert 'all_syncs = compras_syncs + comercial_syncs' in SERVICE
    assert 'all_syncs = compras_syncs + comercial_syncs + sync_logs_genericos' not in SERVICE


def test_sync_logs_query_uses_certified_columns_only():
    assert 'SELECT TOP 20 id, service, type, message, timestamp, operador' in SERVICE
