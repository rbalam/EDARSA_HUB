from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXECUTIVE = ROOT / 'backend' / 'modules' / 'comercial' / 'queries' / 'softrestaurant.py'
HEADER = ROOT / 'backend' / 'modules' / 'comercial_v2' / 'sync_comercial_edarsahub.py'
DETAIL = ROOT / 'backend' / 'scripts' / 'poblar_ventas_detalle_producto_canonico.py'


def test_header_reuses_executive_ticket_population_contract():
    executive = EXECUTIVE.read_text(encoding='utf-8')
    header = HEADER.read_text(encoding='utf-8')
    assert 'INNER JOIN turnos ON turnos.idturno = cheques.idturno' in executive
    assert 'turnos.apertura' in executive
    assert 'cheques.cancelado = 0' in executive
    block = header.split('QUERY_SOFTRESTAURANT_VENTAS_CERRADAS_DIA =', 1)[1].split('def build_softrestaurant_ventas_cerradas_query', 1)[0]
    assert 'INNER JOIN turnos AS tr' in block
    assert 'ON tr.idturno = ch.idturno' in block
    assert 'CONVERT(varchar, tr.apertura, 112)' in block
    assert 'ch.cancelado = 0' in block
    assert '09:00:00' not in block
    assert 'cierre IS NOT NULL' not in block
    assert 'idempresa' not in block


def test_detail_is_folio_first_from_valid_headers():
    detail = DETAIL.read_text(encoding='utf-8')
    block = detail.split('def _extract_soft(', 1)[1].split('def _mpro_operational_datetime_range', 1)[0]
    assert 'WITH h AS (' in block
    assert 'INNER JOIN turnos tr' in block
    assert 'ON tr.idturno = ch.idturno' in block
    assert 'ISNULL(ch.cancelado, 0) = 0' in block
    assert 'FROM h' in block
    assert 'LEFT JOIN cheqdet dc' in block
    assert 'ON dc.foliodet = h.folio' in block
    assert '09:00:00' not in block
    assert 'tr.cierre IS NOT NULL' not in block
    assert 'idempresa' not in block


def test_detail_keeps_real_product_amount_and_separates_cheque_adjustment():
    detail = DETAIL.read_text(encoding='utf-8')
    block = detail.split('def _extract_soft(', 1)[1].split('def _mpro_operational_datetime_range', 1)[0]
    assert 'l.importe_bruto * l.importe_neto_ticket / t.bruto_ticket' not in block
    assert 'CAST(l.importe_bruto AS decimal(18,4)) AS importe_neto' in block
    assert 'SOFT_AJUSTE_CHEQUE' in block
