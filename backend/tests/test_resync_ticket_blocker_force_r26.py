from decimal import Decimal

import pytest

from scripts.poblar_ventas_detalle_producto_canonico import (
    SOFT_AJUSTE_ENCABEZADO,
    SoftTicketReconciliationError,
    _soft_add_ticket_adjustments,
)


def _row(ticket_key="SOFT:9001", numero_ticket="7001", detail="-2.00"):
    return {
        "id_transaccion": ticket_key,
        "numero_ticket": numero_ticket,
        "folio_origen": ticket_key.split(":", 1)[-1],
        "importe_neto_ticket": Decimal("0"),
        "descuento_ticket": Decimal("0"),
        "importe_neto": Decimal(detail),
        "importe_bruto": Decimal(detail),
        "pax_ticket": 1,
        "producto_codigo_fuente": "TEST",
        "producto_nombre": "TEST",
        "cantidad": Decimal("1"),
        "precio_unitario": Decimal(detail),
        "es_kpi_valido": 1,
    }


def test_unexplained_zero_header_exposes_auditable_ticket_blocker():
    with pytest.raises(SoftTicketReconciliationError, match="diferencia no explicada") as caught:
        _soft_add_ticket_adjustments([_row()])
    blocker = caught.value.blocker
    assert blocker["ticket_key"] == "SOFT:9001"
    assert blocker["numero_ticket"] == "7001"
    assert blocker["encabezado"] == "0"
    assert blocker["detalle"] == "-2.00"
    assert blocker["diferencia_detalle_menos_encabezado"] == "-2.00"
    assert blocker["force_allowed"] is True


def test_explicit_authorization_closes_only_the_requested_ticket_to_header():
    out = _soft_add_ticket_adjustments(
        [_row()],
        forced_ticket_keys={"SOFT:9001"},
    )
    assert len(out) == 2
    assert out[0]["importe_neto"] == Decimal("-2.00")
    assert out[-1]["producto_codigo_fuente"] == SOFT_AJUSTE_ENCABEZADO
    assert "FORZADO AUTORIZADO" in out[-1]["producto_nombre"]
    assert out[-1]["importe_neto"] == Decimal("2.00")
    assert sum(row["importe_neto"] for row in out) == Decimal("0.00")


def test_force_is_scoped_to_exact_ticket_key():
    with pytest.raises(SoftTicketReconciliationError):
        _soft_add_ticket_adjustments(
            [_row()],
            forced_ticket_keys={"SOFT:OTHER"},
        )
