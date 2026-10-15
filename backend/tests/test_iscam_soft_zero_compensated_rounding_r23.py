from decimal import Decimal

import pytest

from scripts.poblar_ventas_detalle_producto_canonico import (
    SOFT_AJUSTE_ENCABEZADO,
    _soft_add_ticket_adjustments,
    _validate,
)


def _row(ticket, detail, price):
    return {
        "id_transaccion": f"SOFT:{ticket}",
        "numero_ticket": str(ticket),
        "folio_origen": str(ticket),
        "importe_neto_ticket": Decimal("0"),
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


@pytest.mark.parametrize(
    "ticket,positive,negative",
    [
        ("94617", "2899.5000", "-2900.0000"),
        ("94615", "1699.5000", "-1700.0000"),
        ("94616", "1699.5000", "-1700.0000"),
        ("94614", "3399.0000", "-3400.0000"),
    ],
)
def test_zero_header_accepts_compensated_rounding_residual(ticket, positive, negative):
    out = _soft_add_ticket_adjustments([
        _row(ticket, positive, "1500"),
        _row(ticket, negative, "-1000"),
    ])

    assert out[-1]["producto_codigo_fuente"] == SOFT_AJUSTE_ENCABEZADO
    assert "REDONDEO PARTIDAS COMPENSADAS" in out[-1]["producto_nombre"]
    assert sum(row["importe_neto"] for row in out) == Decimal("0")

    result = _validate(out, {"ventas": Decimal("0"), "tickets": 1, "pax": 1})
    assert result["ok"] is True


def test_zero_header_single_negative_residual_still_fails_closed():
    with pytest.raises(RuntimeError, match="diferencia no explicada"):
        _soft_add_ticket_adjustments([
            _row("single-negative", "-1.00", "-1.00"),
        ])


def test_zero_header_large_compensated_difference_still_fails_closed():
    with pytest.raises(RuntimeError, match="diferencia no explicada"):
        _soft_add_ticket_adjustments([
            _row("large-gap", "100.00", "100.00"),
            _row("large-gap", "-102.00", "-102.00"),
        ])
