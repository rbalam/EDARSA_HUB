from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYNC = ROOT / 'backend' / 'modules' / 'comercial_v2' / 'sync_comercial_edarsahub.py'
DETAIL = ROOT / 'backend' / 'scripts' / 'poblar_ventas_detalle_producto_canonico.py'


def test_softrestaurant_selection_does_not_gate_by_empresa_id():
    header = SYNC.read_text(encoding='utf-8')
    detail = DETAIL.read_text(encoding='utf-8')
    query_block = header.split('QUERY_SOFTRESTAURANT_VENTAS_CERRADAS_DIA =', 1)[1].split('def build_softrestaurant_ventas_cerradas_query', 1)[0]
    detail_block = detail.split('def _extract_soft(', 1)[1].split('def _mpro_operational_datetime_range', 1)[0]
    assert 'idempresa' not in query_block
    assert 'idempresa' not in detail_block
    assert '_resolve_softrestaurant_empresa_id_for_window' not in header
    assert '_softrestaurant_empresa_id_for_window' not in detail


def test_softrestaurant_matches_executive_apertura_contract():
    header = SYNC.read_text(encoding='utf-8')
    assert 'CONVERT(varchar, tr.apertura, 112)' in header
    assert 'COUNT(DISTINCT ch.folio)' in header
    assert 'ch.cancelado = 0' in header
