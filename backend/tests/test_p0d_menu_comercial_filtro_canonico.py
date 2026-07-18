"""
Regresión P0-D - Una Sola Verdad Comercial
===========================================
Garantiza que el Menú Comercial (modules/comercial/service.py) filtre la vista
canónica vw_Comercial_KPIs_Diarios_v2_Runtime por la columna de TEXTO
`unidad_negocio_id` y NO por `unidad_negocio_pk` (que en la vista es un GUID),
y que NO fuerce `sucursal_id = '{sucursal_id}'` en las queries de KPI mensual.

Estos errores causaban que el Menú Comercial devolviera $0 mientras Tablero V2 e
Inteligencia mostraban ~$1.57M para Junio 2026.

Test estático: NO depende de conexión a EDARSAHUB ni de datos vivos.
"""
import re
from pathlib import Path

SERVICE = Path(__file__).resolve().parents[1] / "modules" / "comercial" / "service.py"


def _extraer_bloque(nombre_funcion: str) -> str:
    lines = SERVICE.read_text(encoding="utf-8").splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith(f"def {nombre_funcion}("):
            start = i
            break
    assert start is not None, f"No se encontró def {nombre_funcion}("
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("def "):
            end = j
            break
    return "\n".join(lines[start:end])


def test_kpis_periodo_usa_unidad_negocio_id():
    bloque = _extraer_bloque("_get_kpis_periodo_edarsahub")
    assert "unidad_negocio_id = '{unidad_negocio_pk}'" in bloque, (
        "Debe filtrar por la columna canónica unidad_negocio_id"
    )
    assert "unidad_negocio_pk = '{unidad_negocio_pk}'" not in bloque, (
        "NO debe filtrar por unidad_negocio_pk (GUID en la vista)"
    )


def test_kpis_periodo_no_fuerza_sucursal_default():
    bloque = _extraer_bloque("_get_kpis_periodo_edarsahub")
    # No debe existir el filtro AND sucursal_id = '{sucursal_id}' dentro del SELECT canónico
    assert "AND sucursal_id = '{sucursal_id}'" not in bloque, (
        "NO debe forzar sucursal_id en la query de KPI mensual canónica"
    )


def test_kpis_periodo_usa_ventas_total():
    bloque = _extraer_bloque("_get_kpis_periodo_edarsahub")
    assert "SUM(ventas_total)" in bloque
    assert "SUM(ventas_sin_propina)" not in bloque


def test_gatekeeper_ultimo_dia_usa_unidad_negocio_id():
    """El 'portero' query_ultimo_dia dentro de _obtener_kpis_tablero_desde_edarsahub
    también debe filtrar por unidad_negocio_id y no forzar sucursal_id."""
    bloque = _extraer_bloque("_obtener_kpis_tablero_desde_edarsahub")
    m = re.search(r"query_ultimo_dia = f\"\"\"(.*?)\"\"\"", bloque, re.DOTALL)
    assert m, "No se encontró query_ultimo_dia"
    query = m.group(1)
    assert "unidad_negocio_id = '{unidad_negocio_pk}'" in query
    assert "unidad_negocio_pk = '{unidad_negocio_pk}'" not in query
    assert "AND sucursal_id = '{sucursal_id}'" not in query
