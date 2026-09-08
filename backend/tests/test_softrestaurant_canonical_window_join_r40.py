from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYNC = ROOT / 'backend' / 'modules' / 'comercial_v2' / 'sync_comercial_edarsahub.py'
DETAIL = ROOT / 'backend' / 'scripts' / 'poblar_ventas_detalle_producto_canonico.py'
EXECUTIVE = ROOT / 'backend' / 'modules' / 'comercial' / 'queries' / 'softrestaurant.py'


def test_r40_is_superseded_by_executive_apertura_contract():
    executive = EXECUTIVE.read_text(encoding='utf-8')
    header = SYNC.read_text(encoding='utf-8')
    detail = DETAIL.read_text(encoding='utf-8')
    assert 'WHERE CONVERT(varchar, turnos.apertura, 112)' in executive
    assert 'AND cheques.cancelado = 0' in executive
    query_block = header.split('QUERY_SOFTRESTAURANT_VENTAS_CERRADAS_DIA =', 1)[1].split('def build_softrestaurant_ventas_cerradas_query', 1)[0]
    assert 'CONVERT(varchar, tr.apertura, 112)' in query_block
    assert 'ch.cancelado = 0' in query_block
    assert 'cierre IS NOT NULL' not in query_block
    assert 'idempresa' not in query_block
    builder = header.split('def build_softrestaurant_ventas_cerradas_query', 1)[1].split('QUERY_SOFTRESTAURANT_VENTAS_ABIERTAS', 1)[0]
    assert 'get_operational_datetime_range_for_fecha_operacion' not in builder
    assert "fecha_actual += timedelta(days=1)" in builder
    assert 'fecha_siguiente' not in builder
    detail_range = detail.split('def _soft_operational_datetime_range', 1)[1].split('def _extract_soft(', 1)[0]
    assert 'get_operational_datetime_range_for_fecha_operacion' not in detail_range
