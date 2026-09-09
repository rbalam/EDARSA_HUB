from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYNC = ROOT / 'backend' / 'modules' / 'comercial_v2' / 'sync_comercial_edarsahub.py'
DETAIL = ROOT / 'backend' / 'scripts' / 'poblar_ventas_detalle_producto_canonico.py'
EXECUTIVE = ROOT / 'backend' / 'modules' / 'comercial' / 'queries' / 'softrestaurant.py'


def test_r40_regression_is_replaced_by_validated_apertura_contract():
    executive = EXECUTIVE.read_text(encoding='utf-8')
    header = SYNC.read_text(encoding='utf-8')
    detail = DETAIL.read_text(encoding='utf-8')
    assert 'WHERE CONVERT(varchar, turnos.apertura, 112)' in executive
    assert 'AND cheques.cancelado = 0' in executive
    query_block = header.split('QUERY_SOFTRESTAURANT_VENTAS_CERRADAS_DIA =', 1)[1].split('def _resolve_softrestaurant_empresa_id_for_window', 1)[0]
    assert "apertura >= '{inicio_operativo}'" in query_block
    assert "apertura < '{fin_operativo}'" in query_block
    assert 'cancelado = 0' in query_block
    assert 'cierre IS NOT NULL' in query_block
    assert 'idempresa' in query_block
    builder = header.split('def build_softrestaurant_ventas_cerradas_query', 1)[1].split('QUERY_SOFTRESTAURANT_VENTAS_ABIERTAS', 1)[0]
    assert 'get_operational_datetime_range_for_fecha_operacion' not in builder
    assert "inicio_operativo = fecha_actual.strftime('%Y-%m-%d 09:00:00')" in builder
    assert "fin_operativo = fecha_siguiente.strftime('%Y-%m-%d 09:00:00')" in builder
    detail_range = detail.split('def _soft_operational_datetime_range', 1)[1].split('def _extract_soft(', 1)[0]
    assert 'get_operational_datetime_range_for_fecha_operacion' not in detail_range
    assert 'from core.utils.operational_window import' not in detail_range
    assert 'replace(hour=9)' in detail_range
