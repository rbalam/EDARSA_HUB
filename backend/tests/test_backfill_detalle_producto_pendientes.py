"""Pruebas unitarias del selector de backfill comercial pendiente."""

import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.backfill_detalle_producto_pendientes import _detalle_concilia


def _runtime(ventas="122198.00", tickets=38, pax=89):
    return {
        "ventas": Decimal(ventas),
        "tickets": tickets,
        "pax": pax,
    }


def test_sin_detalle_es_candidato_a_backfill():
    assert _detalle_concilia(None, _runtime()) is False


def test_detalle_exactamente_conciliado_no_se_reprocesa():
    detalle = {
        "ventas": Decimal("122198.00"),
        "tickets": 38,
        "pax": 89,
    }
    assert _detalle_concilia(detalle, _runtime()) is True


def test_tolerancia_monetaria_no_oculta_diferencias_de_tickets_o_pax():
    detalle = {
        "ventas": Decimal("122198.04"),
        "tickets": 37,
        "pax": 89,
    }
    assert _detalle_concilia(detalle, _runtime()) is False

    detalle = {
        "ventas": Decimal("122198.04"),
        "tickets": 38,
        "pax": 86,
    }
    assert _detalle_concilia(detalle, _runtime()) is False


def test_tolerancia_monetaria_canonica_es_aceptada():
    detalle = {
        "ventas": Decimal("122198.04"),
        "tickets": 38,
        "pax": 89,
    }
    assert _detalle_concilia(detalle, _runtime()) is True


def test_diferencia_monetaria_superior_a_tolerancia_se_reprocesa():
    detalle = {
        "ventas": Decimal("122198.06"),
        "tickets": 38,
        "pax": 89,
    }
    assert _detalle_concilia(detalle, _runtime()) is False
