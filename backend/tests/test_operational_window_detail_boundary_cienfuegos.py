"""
Regresion — frontera FechaOperacion vs detalle comercial CIENFUEGOS
==================================================================
Caso real 2026-08-18:
- COMIDA inicia 13:00.
- El motor canonico admite 5 minutos de tolerancia al inicio.
- Folio 104591 ocurrio a las 12:56:40 y pertenece a FechaOperacion 2026-08-18.

Este test blinda que la ventana datetime usada para consultar el POS represente
la misma particion temporal que get_operational_window().
"""

import os
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.utils.operational_window import (
    clear_turnos_cache,
    get_operational_datetime_range_for_fecha_operacion,
    get_operational_window,
)

MX = ZoneInfo("America/Mexico_City")


def test_cienfuegos_folio_104591_pertenece_al_18_agosto():
    clear_turnos_cache()
    timestamp = datetime(2026, 8, 18, 12, 56, 40, tzinfo=MX)

    resultado = get_operational_window("CIENFUEGOS", timestamp)

    assert resultado.fecha_operacion == date(2026, 8, 18)


def test_rango_detalle_incluye_misma_tolerancia_del_motor_canonico():
    clear_turnos_cache()

    inicio, fin, metadata = get_operational_datetime_range_for_fecha_operacion(
        "CIENFUEGOS",
        date(2026, 8, 18),
    )

    folio_104591 = datetime(2026, 8, 18, 12, 56, 40)

    assert inicio == datetime(2026, 8, 18, 12, 55, 0)
    assert fin == datetime(2026, 8, 19, 12, 55, 0)
    assert inicio <= folio_104591 < fin
    assert metadata["tolerancia_inicio_minutos"] == 5


def test_rangos_consecutivos_no_tienen_hueco_ni_solapamiento():
    clear_turnos_cache()

    inicio_18, fin_18, _ = get_operational_datetime_range_for_fecha_operacion(
        "CIENFUEGOS",
        date(2026, 8, 18),
    )
    inicio_19, fin_19, _ = get_operational_datetime_range_for_fecha_operacion(
        "CIENFUEGOS",
        date(2026, 8, 19),
    )

    assert inicio_18 < fin_18
    assert fin_18 == inicio_19
    assert inicio_19 < fin_19


if __name__ == "__main__":
    test_cienfuegos_folio_104591_pertenece_al_18_agosto()
    test_rango_detalle_incluye_misma_tolerancia_del_motor_canonico()
    test_rangos_consecutivos_no_tienen_hueco_ni_solapamiento()
    print("OK — frontera operativa CIENFUEGOS validada")
