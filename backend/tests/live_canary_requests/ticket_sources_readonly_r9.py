"""Opt-in Worker certification of actual MPRO LOCAL APIs; never default pytest discovery."""
from datetime import datetime
from zoneinfo import ZoneInfo
import re
import requests
import pytest
from core.scheduler.jobs.sync_comercial_abiertas_v2_job import _get_api_local_config
from modules.comercial_v2.ticket_contract import MPRO_EXPRESSIONS
from modules.comercial_v2 import ticket_snapshot
from tools.mirror_sync.sql_readonly_audit import validate_readonly_sql


def read_api(config, sql):
    validate_readonly_sql(sql)
    response = requests.get(config['api_url'], params={'sql': sql}, headers={'X-API-Key': config['api_key']}, timeout=30)
    assert response.status_code == 200, f'API_LOCAL_HTTP_{response.status_code}'
    payload = response.json()
    assert payload.get('success') is not False and not payload.get('error'), 'API_LOCAL_QUERY_FAILED'
    assert isinstance(payload.get('data'), list), 'API_LOCAL_DATA_CONTRACT_INVALID'
    return payload['data']


@pytest.mark.parametrize('unit', ['ORIGEN', '130QRO'])
def test_real_local_customer_and_ticket_schema(unit):
    config = _get_api_local_config(unit)
    assert config, f'API_LOCAL_CONFIG_MISSING:{unit}'
    rows = read_api(config, "SELECT LOWER(TABLE_NAME) AS table_name, LOWER(COLUMN_NAME) AS column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME IN ('Comanda','Comanda_Detalle','Cliente','Tipo_Descuento','Venta')")
    actual = {(r['table_name'], r['column_name']) for r in rows}
    sources = {'h': 'comanda', 'd': 'comanda_detalle', 'cl': 'cliente', 'td': 'tipo_descuento'}
    expected = {(sources[a], c.lower()) for expression in MPRO_EXPRESSIONS.values() for a, c in re.findall(r'\b(h|d|cl|td)\.([A-Za-z_0-9]+)', expression)}
    expected |= {('venta', c.lower()) for c in ('Vn_Folio', 'Vn_ID', 'Vn_Tabla', 'Vn_Documento', 'Vn_Documento_ID')}
    missing = sorted(expected - actual)
    assert not missing, f'LOCAL_SCHEMA_MISSING:{unit}:{missing}'
    operation_date = datetime.now(ZoneInfo('America/Mexico_City')).date().isoformat()
    for name in dir(ticket_snapshot):
        if name.startswith('QUERY_MPRO_'):
            query = getattr(ticket_snapshot, name).format(fecha_operacion=operation_date, sucursal_id=config['sucursal_id'])
            query = query.replace('SELECT\n', 'SELECT TOP (0)\n', 1)
            read_api(config, query)
