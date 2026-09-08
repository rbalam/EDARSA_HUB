from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYNC = ROOT / 'backend' / 'modules' / 'comercial_v2' / 'sync_comercial_edarsahub.py'
DETAIL = ROOT / 'backend' / 'scripts' / 'poblar_ventas_detalle_producto_canonico.py'


def test_soft_header_and_detail_share_turnos_population_contract():
    header = SYNC.read_text(encoding='utf-8')
    detail = DETAIL.read_text(encoding='utf-8')
    header_query = header.split('QUERY_SOFTRESTAURANT_VENTAS_CERRADAS_DIA =', 1)[1].split('def _resolve_softrestaurant_empresa_id_for_window', 1)[0]
    detail_query = detail.split('def _extract_soft(', 1)[1].split('def _mpro_operational_datetime_range', 1)[0]
    assert 'INNER JOIN turnos AS tr' in header_query
    assert 'tr.idturno = ch.idturno' in header_query
    assert 'tr.idempresa = ch.idempresa' in header_query
    assert 'tr.apertura >=' in header_query and 'tr.apertura <' in header_query
    assert 'tr.cierre IS NOT NULL' in header_query
    assert 'ch.cancelado = 0' in header_query
    assert 'INNER JOIN turnos tr' in detail_query
    assert 'tr.idturno = ch.idturno' in detail_query
    assert 'tr.idempresa = ch.idempresa' in detail_query


def test_no_fixed_0900_window_remains_in_soft_header_or_detail_window_helpers():
    header = SYNC.read_text(encoding='utf-8')
    detail = DETAIL.read_text(encoding='utf-8')
    builder = header.split('def build_softrestaurant_ventas_cerradas_query', 1)[1].split('QUERY_SOFTRESTAURANT_VENTAS_ABIERTAS', 1)[0]
    detail_window = detail.split('def _soft_operational_datetime_range', 1)[1].split('def _softrestaurant_empresa_id_for_window', 1)[0]
    assert "09:00:00" not in builder
    assert "09:00:00" not in detail_window
    assert 'get_operational_datetime_range_for_fecha_operacion' in builder
    assert 'get_operational_datetime_range_for_fecha_operacion' in detail_window
