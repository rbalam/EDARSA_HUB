from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYNC = ROOT / 'backend' / 'modules' / 'comercial_v2' / 'sync_comercial_edarsahub.py'
DETAIL = ROOT / 'backend' / 'scripts' / 'poblar_ventas_detalle_producto_canonico.py'


def test_softrestaurant_resolves_empresa_for_same_apertura_window():
    header = SYNC.read_text(encoding='utf-8')
    detail = DETAIL.read_text(encoding='utf-8')
    query_block = header.split('QUERY_SOFTRESTAURANT_VENTAS_CERRADAS_DIA =', 1)[1].split('def _resolve_softrestaurant_empresa_id_for_window', 1)[0]
    detail_block = detail.split('def _extract_soft(', 1)[1].split('def _mpro_operational_datetime_range', 1)[0]
    assert 'idempresa' in query_block
    assert 'idempresa' in detail_block
    assert '_resolve_softrestaurant_empresa_id_for_window' in header
    assert '_softrestaurant_empresa_id_for_window' in detail


def test_softrestaurant_restored_apertura_contract():
    header = SYNC.read_text(encoding='utf-8')
    assert "apertura >= '{inicio_operativo}'" in header
    assert "apertura < '{fin_operativo}'" in header
    assert "inicio_operativo = fecha_actual.strftime('%Y-%m-%d 09:00:00')" in header
    assert "fin_operativo = fecha_siguiente.strftime('%Y-%m-%d 09:00:00')" in header
    assert 'cierre IS NOT NULL' in header
    assert 'cancelado = 0' in header
