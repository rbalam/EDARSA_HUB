from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYNC = ROOT / 'backend' / 'modules' / 'comercial_v2' / 'sync_comercial_edarsahub.py'
DETAIL = ROOT / 'backend' / 'scripts' / 'poblar_ventas_detalle_producto_canonico.py'


def test_header_resolves_empresa_from_each_operational_window():
    text = SYNC.read_text(encoding='utf-8')
    block = text.split('def build_softrestaurant_ventas_cerradas_query', 1)[1].split('QUERY_SOFTRESTAURANT_VENTAS_ABIERTAS', 1)[0]
    assert '_resolve_softrestaurant_empresa_id_for_window(' in block
    assert 'get_operational_datetime_range_for_fecha_operacion' in block
    assert "inicio_operativo = inicio_dt.strftime('%Y-%m-%d %H:%M:%S')" in block
    assert "fin_operativo = fin_dt.strftime('%Y-%m-%d %H:%M:%S')" in block


def test_header_uses_same_exclusive_operational_boundary_as_detail():
    header = SYNC.read_text(encoding='utf-8')
    detail = DETAIL.read_text(encoding='utf-8')
    assert "tr.apertura >= '{inicio_operativo}'" in header
    assert "tr.apertura < '{fin_operativo}'" in header
    assert 'get_operational_datetime_range_for_fecha_operacion' in detail
    assert "tr.apertura >= %s" in detail
    assert "tr.apertura < %s" in detail


def test_header_fails_closed_on_ambiguous_empresa():
    text = SYNC.read_text(encoding='utf-8')
    helper = text.split('def _resolve_softrestaurant_empresa_id_for_window', 1)[1].split('def build_softrestaurant_ventas_cerradas_query', 1)[0]
    assert 'if len(candidates) == 1:' in helper
    assert 'if not candidates:' in helper
    assert 'multiples idempresa' in helper
