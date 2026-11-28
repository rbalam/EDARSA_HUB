from decimal import Decimal
from pathlib import Path

from scripts.poblar_ventas_detalle_producto_canonico import (
    SOFT_AJUSTE_ANTICIPO_CERO,
    SOFT_AJUSTE_ENCABEZADO,
    _soft_add_ticket_adjustments,
    _validate,
)

ROOT = Path(__file__).resolve().parents[2]
DETAIL = ROOT / 'backend' / 'scripts' / 'poblar_ventas_detalle_producto_canonico.py'


def _row(ticket, header, detail, pax=1, product='P1'):
    return {
        'id_transaccion': f'SOFT:{ticket}',
        'numero_ticket': str(ticket),
        'folio_origen': str(ticket),
        'importe_neto_ticket': Decimal(str(header)),
        'descuento_ticket': Decimal('0'),
        'importe_neto': Decimal(str(detail)),
        'importe_bruto': Decimal(str(detail)),
        'pax_ticket': pax,
        'producto_codigo_fuente': product,
        'producto_nombre': product,
        'cantidad': Decimal('1'),
        'precio_unitario': Decimal(str(detail)),
        'es_kpi_valido': 1,
    }


def test_soft_detail_population_is_header_folio_first():
    text = DETAIL.read_text(encoding='utf-8')
    block = text.split('def _extract_soft(', 1)[1].split('def _mpro_operational_datetime_range', 1)[0]
    assert 'WITH h AS (' in block
    assert 'FROM h' in block
    assert 'LEFT JOIN cheqdet dc' in block
    assert 'ON dc.foliodet = h.folio' in block


def test_missing_or_short_detail_is_completed_by_same_header_folio():
    out = _soft_add_ticket_adjustments([_row('77', '125', '0', product='HEADER_SIN_DETALLE')])
    assert out[-1]['producto_codigo_fuente'] == SOFT_AJUSTE_ENCABEZADO
    assert out[-1]['numero_ticket'] == '77'
    assert out[-1]['folio_origen'] == '77'
    assert out[-1]['importe_neto'] == Decimal('125')
    assert sum(x['importe_neto'] for x in out) == Decimal('125')


def test_validation_uses_exact_header_ticket_population_after_adjustment():
    src = []
    src.extend(_soft_add_ticket_adjustments([_row('10', '90', '100', pax=2)]))
    src.extend(_soft_add_ticket_adjustments([_row('11', '50', '40', pax=1)]))
    result = _validate(src, {'ventas': Decimal('140'), 'tickets': 2, 'pax': 3})
    assert result['ok'] is True
    assert result['ventas_por_ticket'] == Decimal('140')
    assert result['ventas_detalle'] == Decimal('140')
    assert result['tickets_por_ticket'] == 2
    assert result['pax_por_ticket'] == 3
    assert result['tickets_no_conciliados'] == []


def test_small_residual_is_adjusted_exactly_to_header():
    src = _soft_add_ticket_adjustments([
        _row('12', '100.00', '100.01', pax=1),
    ])
    assert src[-1]['producto_codigo_fuente'] == SOFT_AJUSTE_ENCABEZADO
    assert src[-1]['importe_neto'] == Decimal('-0.01')
    assert sum(x['importe_neto'] for x in src) == Decimal('100.00')

    result = _validate(src, {'ventas': Decimal('100.00'), 'tickets': 1, 'pax': 1})
    assert result['ok'] is True
    assert result['ventas_detalle'] == Decimal('100.00')
    assert result['tickets_no_conciliados'] == []


def test_zero_header_accepts_real_franqicia_spelling():
    rows = [
        _row('20833', '0.00', '195.00', pax=1, product='A ENSALADA CESAR'),
        _row('20833', '0.00', '-200.00', pax=1, product='FRANQICIA DJ'),
    ]
    out = _soft_add_ticket_adjustments(rows)
    assert out[-1]['importe_neto'] == Decimal('5.00')
    assert sum(x['importe_neto'] for x in out) == Decimal('0.00')

    result = _validate(out, {'ventas': Decimal('0.00'), 'tickets': 1, 'pax': 1})
    assert result['ok'] is True
    assert result['ventas_detalle'] == Decimal('0.00')
    assert result['tickets_no_conciliados'] == []


def test_zero_header_accepts_negative_advance_application():
    rows = [
        _row('21167', '0.00', '1985.00', pax=1, product='CONSUMO POSITIVO'),
        _row('21167', '0.00', '-2000.00', pax=1, product='ANTICIPO S/VENTAS APLICACION'),
    ]
    out = _soft_add_ticket_adjustments(rows)
    assert out[-1]['producto_codigo_fuente'] == SOFT_AJUSTE_ANTICIPO_CERO
    assert out[-1]['importe_neto'] == Decimal('15.00')
    assert sum(x['importe_neto'] for x in out) == Decimal('0.00')

    result = _validate(out, {'ventas': Decimal('0.00'), 'tickets': 1, 'pax': 1})
    assert result['ok'] is True
    assert result['ventas_detalle'] == Decimal('0.00')
    assert result['tickets_no_conciliados'] == []
