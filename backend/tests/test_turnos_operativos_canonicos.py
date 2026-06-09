"""
Regresión — Turnos Operativos Canónicos (Desayuno/Comida/Cena) NO-LIVE
======================================================================
Blinda los fixes 2026-06-10:
  1. `operational_window._get_turnos_unidad` leía la columna inexistente
     `unidad_negocio_pk` (real: `unidad_negocio_id`) y asumía dict-cursor →
     SIEMPRE caía al fallback hardcodeado. Ahora lee los turnos configurados.
  2. El turno LEGACY 'COMIDA_CENA' fue retirado de la tabla.
  3. `calcular_fecha_operacion_por_unidad` (pantalla "Probar") delega al MISMO
     motor canónico (sin lógica duplicada).

Requiere conexión EDARSAHUB (igual que el resto de tests del repo).
"""
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from core.utils.operational_window import (
    get_operational_window, _get_turnos_unidad, clear_turnos_cache
)
from api.configuracion_operativa_unidades import (
    calcular_fecha_operacion_por_unidad, get_turnos_por_unidad
)

MX = ZoneInfo("America/Mexico_City")
UNIDADES = ['130MID', '130QRO', 'CIENFUEGOS', 'ESTELAR', 'ORIGEN']


def test_motor_lee_turnos_configurados_no_fallback():
    """El motor debe leer turnos reales (no [] → fallback) para todas las unidades."""
    clear_turnos_cache()
    for u in UNIDADES:
        turnos = _get_turnos_unidad(u)
        assert len(turnos) > 0, f"{u}: el motor no cargó turnos (caería al fallback)"
        # ningún turno canónico debe ser el LEGACY
        codes = {t['turno_codigo'] for t in turnos}
        assert 'COMIDA_CENA' not in codes, f"{u}: LEGACY COMIDA_CENA no debe estar en turnos canónicos"


def test_legacy_comida_cena_retirado():
    """La tabla ya no debe contener filas LEGACY 'COMIDA_CENA' en ninguna unidad."""
    for u in UNIDADES:
        codes = {t['turno_codigo'] for t in get_turnos_por_unidad(u)}
        assert 'COMIDA_CENA' not in codes, f"{u}: turno LEGACY no retirado"


def test_clasificacion_comida_cena_por_hora():
    """A las 14:30 → COMIDA; a las 21:30 → CENA (día actual)."""
    clear_turnos_cache()
    r_comida = get_operational_window('130MID', datetime(2026, 6, 9, 14, 30, tzinfo=MX))
    assert r_comida.turno_operativo_codigo == 'COMIDA'

    r_cena = get_operational_window('130MID', datetime(2026, 6, 9, 21, 30, tzinfo=MX))
    assert r_cena.turno_operativo_codigo == 'CENA'
    assert str(r_cena.fecha_operacion) == '2026-06-09'


def test_cena_cruza_medianoche_madrugada_dia_anterior():
    """02:30 (madrugada) en unidad con Cena que cruza medianoche → día anterior."""
    clear_turnos_cache()
    r = get_operational_window('130MID', datetime(2026, 6, 9, 2, 30, tzinfo=MX))
    assert r.turno_operativo_codigo == 'CENA'
    assert str(r.fecha_operacion) == '2026-06-08'


def test_probar_delega_en_motor_canonico():
    """El endpoint 'Probar' devuelve el turno canónico, no la lógica vieja (00:00-23:59)."""
    res = calcular_fecha_operacion_por_unidad('130MID', datetime(2026, 6, 9, 21, 30, tzinfo=MX))
    assert res['turno_detectado'] == 'CENA'
    assert res['estado_operativo'] == 'CENA'
    assert res['window_start'] == '19:00:00'
    assert res['window_end'] == '05:59:00'
    assert res['cruza_medianoche'] is True


if __name__ == '__main__':
    test_motor_lee_turnos_configurados_no_fallback()
    test_legacy_comida_cena_retirado()
    test_clasificacion_comida_cena_por_hora()
    test_cena_cruza_medianoche_madrugada_dia_anterior()
    test_probar_delega_en_motor_canonico()
    print("OK — 5/5 tests de turnos canónicos")
