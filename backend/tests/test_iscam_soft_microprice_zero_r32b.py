from decimal import Decimal
import pytest

from scripts.poblar_ventas_detalle_producto_canonico import (
    SOFT_AJUSTE_ENCABEZADO,
    _soft_add_ticket_adjustments,
)


def row(ticket, header, detail, price):
    return {
        "id_transaccion": f"SOFT:{ticket}",
        "numero_ticket": str(ticket),
        "folio_origen": str(ticket),
        "importe_neto_ticket": Decimal(str(header)),
        "descuento_ticket": Decimal("0"),
        "importe_neto": Decimal(str(detail)),
        "importe_bruto": Decimal(str(detail)),
        "pax_ticket": 1,
        "producto_codigo_fuente": "TEST",
        "producto_nombre": "TEST",
        "cantidad": Decimal("1"),
        "precio_unitario": Decimal(str(price)),
        "es_kpi_valido": 1,
    }


def test_microprice_zero_header_is_reconciled():
    out = _soft_add_ticket_adjustments([
        row("16308", "0", "0.197", "0.001"),
    ])
    assert out[-1]["producto_codigo_fuente"] == SOFT_AJUSTE_ENCABEZADO
    assert sum(x["importe_neto"] for x in out) == Decimal("0.000")


def test_regular_zero_header_still_fails_closed():
    with pytest.raises(RuntimeError, match="diferencia no explicada"):
        _soft_add_ticket_adjustments([
            row("regular", "0", "180", "30"),
        ])
