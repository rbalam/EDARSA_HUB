from decimal import Decimal
from pathlib import Path

import pytest

from scripts.poblar_ventas_detalle_producto_canonico import SOFT_AJUSTE_CHEQUE, SOFT_AJUSTE_ENCABEZADO, _soft_add_ticket_adjustments

ROOT = Path(__file__).resolve().parents[2]
ROUTES = ROOT / 'backend' / 'modules' / 'inteligencia_comercial' / 'iscam_routes.py'
FRONT = ROOT / 'frontend' / 'src' / 'portal-inteligencia' / 'pages' / 'ReportesISCAMPage.jsx'


def _row(ticket='T1', product='P1', product_total='100', header='90', discount='10'):
    return {
        'id_transaccion': ticket, 'numero_ticket': ticket,
        'importe_neto_ticket': Decimal(header), 'descuento_ticket': Decimal(discount),
        'importe_neto': Decimal(product_total), 'importe_bruto': Decimal(product_total),
        'producto_codigo_fuente': product, 'producto_nombre': product,
        'cantidad': Decimal('1'), 'precio_unitario': Decimal(product_total),
    }


def test_discounted_ticket_adds_separate_adjustment_without_touching_product():
    out = _soft_add_ticket_adjustments([_row()])
    assert out[0]['producto_codigo_fuente'] == 'P1'
    assert out[0]['importe_neto'] == Decimal('100')
    assert out[1]['producto_codigo_fuente'] == SOFT_AJUSTE_CHEQUE
    assert out[1]['importe_neto'] == Decimal('-10')
    assert sum(r['importe_neto'] for r in out) == Decimal('90')


def test_unexplained_difference_is_reconciled_to_same_header_folio():
    out = _soft_add_ticket_adjustments([_row(header='90', discount='0')])
    assert out[0]['producto_codigo_fuente'] == 'P1'
    assert out[0]['importe_neto'] == Decimal('100')
    assert out[1]['producto_codigo_fuente'] == SOFT_AJUSTE_ENCABEZADO
    assert out[1]['id_transaccion'] == 'T1'
    assert out[1]['numero_ticket'] == 'T1'
    assert out[1]['importe_neto'] == Decimal('-10')
    assert sum(r['importe_neto'] for r in out) == Decimal('90')


def test_iscam_routes_separate_adjustments_from_products():
    text = ROUTES.read_text(encoding='utf-8')
    assert "producto_codigo_fuente NOT LIKE '__ISCAM_AJUSTE_%'" in text
    assert "producto_codigo_fuente LIKE '__ISCAM_AJUSTE_%'" in text
    assert 'resumen_conciliacion' in text
    assert 'ajustes_cheque' in text


def test_frontend_exposes_reconciliation():
    text = FRONT.read_text(encoding='utf-8')
    assert 'Resumen de conciliación' in text
    assert 'Ajustes del cheque' in text
    assert 'Diferencias encontradas' in text
