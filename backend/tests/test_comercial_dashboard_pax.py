"""
Regresión — Dashboard Comercial: PAX y PAX Promedio + Detalle de Movimientos
============================================================================
Blinda los fixes 2026-06-10:

  BUG 1 (PAX=0): `_get_kpis_periodo_edarsahub` y los fallbacks de
    `_get_kpis_periodo_edarsahub_flexible` aliasaban `SUM(pax_total) AS pax_total`
    pero leían `row.get('pax')` (clave inexistente) → PAX siempre 0, y por ende
    "Pax Promedio" ($0). Ahora leen `row.get('pax_total')`.

  BUG 2 (Detalle vacío): el endpoint `/comercial/detalle-movimientos` consultaba
    la VISTA `vw_Comercial_KPIs_Diarios_v2_Runtime` con `ISNULL(activo,1)=1`, pero
    esa columna NO existe en la vista → error SQL silenciado → "No hay movimientos".
    Se eliminó el filtro `activo` (la vista no lo expone).

Los valores deben COINCIDIR con el servicio canónico (KPIsCanonicosService).
Requiere conexión EDARSAHUB.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from modules.comercial.service import (
    _get_kpis_periodo_edarsahub, _query_edarsahub_tablero,
)
from core.kpis_canonicos.service import KPIsCanonicosService

# 130MID en EDARSAHUB
SERVER_130MID = 'a5547321-1139-4d2b-9d53-182ca737b6b6'
DESDE, HASTA = '2026-06-01', '2026-06-30'


def test_pax_no_es_cero_y_coincide_con_canonico():
    """El dashboard debe leer PAX real (>0) y coincidir con el canónico."""
    kpi = _get_kpis_periodo_edarsahub(SERVER_130MID, DESDE, HASTA, 'DEFAULT')
    assert kpi['existe_data'], "Debe haber datos de 130MID en junio"
    assert kpi['pax'] > 0, "PAX no debe ser 0 (bug del alias pax_total)"
    assert kpi['cheques'] > 0

    # Coincidencia con el servicio canónico (misma fuente base)
    ag = KPIsCanonicosService.agregados_por_unidad('2026-06-01', '2026-07-01')
    canon = next((a for a in ag if a['unidad_codigo'] == '130MID'), None)
    assert canon is not None
    assert abs(kpi['pax'] - int(canon['pax'])) <= 1, \
        f"PAX dashboard ({kpi['pax']}) debe coincidir con canónico ({int(canon['pax'])})"


def test_pax_promedio_derivado_correcto():
    """El consumo por persona canónico es ventas_total / pax_total."""
    kpi = _get_kpis_periodo_edarsahub(SERVER_130MID, DESDE, HASTA, 'DEFAULT')
    consumo_persona = kpi['ventas'] / kpi['pax'] if kpi['pax'] else 0
    assert consumo_persona > 0


def test_detalle_view_sin_columna_activo_devuelve_filas():
    """La vista NO tiene 'activo'; la query del detalle (sin ese filtro) sí trae filas."""
    q = f"""
        SELECT COUNT(*) AS total, ISNULL(SUM(pax_total),0) AS pax
        FROM vw_Comercial_KPIs_Diarios_v2_Runtime
        WHERE server_id = '{SERVER_130MID}'
          AND fecha_operacion >= '{DESDE}' AND fecha_operacion <= '{HASTA}'
          AND ventas_total > 0
    """
    rows = _query_edarsahub_tablero(q)
    assert rows and int(rows[0]['total']) > 0, "El detalle debe devolver días con ventas"
    assert int(rows[0]['pax']) > 0


def test_vista_runtime_no_expone_columna_activo():
    """Documenta el bug: 'activo' NO es columna de la vista runtime."""
    cols = _query_edarsahub_tablero(
        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_NAME = 'vw_Comercial_KPIs_Diarios_v2_Runtime'"
    )
    nombres = {c['COLUMN_NAME'].lower() for c in (cols or [])}
    assert 'pax_total' in nombres
    assert 'activo' not in nombres, "Si la vista expone 'activo', revisar el filtro del detalle"


if __name__ == '__main__':
    test_pax_no_es_cero_y_coincide_con_canonico()
    test_pax_promedio_derivado_correcto()
    test_detalle_view_sin_columna_activo_devuelve_filas()
    test_vista_runtime_no_expone_columna_activo()
    print("OK — 4/4 tests dashboard comercial PAX/detalle")
