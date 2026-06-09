"""
Tests del resolver canónico centralizado (core/inventarios/resolver_canonico.py).
Solo lectura contra EDARSAHUB. Validan la LÓGICA, sin escribir nada.

Ejecutar: cd /app/backend && python -m pytest tests/test_resolver_canonico.py -v
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, "/app/backend")
load_dotenv(Path("/app/backend/.env"))

import logging
logging.disable(logging.CRITICAL)

from core.inventarios import resolver_canonico as rc


def test_tipo_movimiento_resuelve_codigo_canonico_existente():
    res = rc.resolver_tipo_movimiento_por_codigo("ENTRADA_COMPRA")
    assert res.resuelto is True
    assert isinstance(res.canonical_id, int)
    assert res.motivo == "OK"


def test_tipo_movimiento_codigo_inexistente_queda_pendiente():
    res = rc.resolver_tipo_movimiento_por_codigo("CODIGO_QUE_NO_EXISTE_XYZ")
    assert res.resuelto is False
    assert res.canonical_id is None
    assert res.motivo == "PENDIENTE_SIN_MAPEO"


def test_producto_real_se_resuelve_via_puente():
    # Tras canonización (Paso 2), un código real debe resolver a un ProductoID int.
    unidad = rc.get_server_by_unidad_codigo("CIENFUEGOS")
    server_id = unidad.get("server_id") or unidad.get("id")
    from core.sql_first.db import get_sql_connection
    cur = get_sql_connection().cursor(as_dict=True)
    cur.execute(
        "SELECT TOP 1 CodigoFuente, SystemType FROM Sync_Productos_Insumos WHERE ServerID = %s "
        "AND CodigoFuente IS NOT NULL AND LTRIM(RTRIM(CodigoFuente)) <> ''",
        (str(server_id),),
    )
    row = cur.fetchone()
    assert row is not None
    res = rc.resolver_producto_id("CIENFUEGOS", row["SystemType"], row["CodigoFuente"])
    assert res.resuelto is True
    assert isinstance(res.canonical_id, int)
    assert res.motivo == "OK"


def test_producto_codigo_inexistente_queda_pendiente():
    # Código que no existe -> PENDIENTE_SIN_MAPEO (nunca inventa ID)
    res = rc.resolver_producto_id("CIENFUEGOS", "SOFTRESTAURANT_PRO", "CODIGO_FALSO_XYZ")
    assert res.resuelto is False
    assert res.canonical_id is None
    assert res.motivo == "PENDIENTE_SIN_MAPEO"


def test_producto_unidad_desconocida():
    res = rc.resolver_producto_id("UNIDAD_INEXISTENTE", "SOFTRESTAURANT_PRO", "ABC")
    assert res.resuelto is False
    assert res.motivo == "UNIDAD_DESCONOCIDA"


def test_almacen_inexistente_queda_pendiente():
    # Sucursal/empresa válidas pero código inexistente -> PENDIENTE, nunca inventa
    res = rc.resolver_almacen_id(5, 1, "ALMACEN_FANTASMA_999")
    assert res.resuelto is False
    assert res.canonical_id is None


def test_concepto_db_driven_resuelve_epc():
    # Sub-fase B: catálogo DB-driven Inventario_ConceptoMapeoOrigen
    res = rc.resolver_tipo_movimiento_desde_concepto("SOFTRESTAURANT_PRO", "EPC")
    assert res.resuelto is True
    assert res.canonical_id == 1
    assert res.motivo == "OK"


def test_concepto_no_mapeado_queda_pendiente():
    res = rc.resolver_tipo_movimiento_desde_concepto("SOFTRESTAURANT_PRO", "CONCEPTO_INEXISTENTE_ZZZ")
    assert res.resuelto is False
    assert res.motivo in ("PENDIENTE_SIN_MAPEO", "CATALOGO_CONCEPTOS_AUSENTE")


def test_sucursal_softrestaurant_resuelve_unica():
    # CIENFUEGOS -> server dedicado -> 1 sola sucursal en el mapeo
    unidad = rc.get_server_by_unidad_codigo("CIENFUEGOS")
    server_id = unidad.get("server_id") or unidad.get("id")
    res = rc.resolver_sucursal_id(server_id)
    assert res.resuelto is True
    assert isinstance(res.canonical_id, int)


def test_sucursal_mpro_compartido_es_ambiguo_sin_origen():
    # ORIGEN/130QRO comparten servidor MPRO y SucursalOrigenID es NULL -> AMBIGUO (no adivina)
    unidad = rc.get_server_by_unidad_codigo("ORIGEN")
    server_id = unidad.get("server_id") or unidad.get("id")
    res = rc.resolver_sucursal_id(server_id)
    assert res.resuelto is False
    assert res.motivo == "AMBIGUO_MULTISUCURSAL"
