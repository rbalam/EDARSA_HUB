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


def test_empresa_resuelve_por_codigo_unidad():
    # Sistema_Empresas.CodigoEmpresa = código de unidad (1:1)
    for cod in ["ORIGEN", "CIENFUEGOS", "130MID"]:
        res = rc.resolver_empresa_id(cod)
        assert res.resuelto is True, f"EmpresaID no resuelto para {cod}"
        assert isinstance(res.canonical_id, int)


def test_empresa_inexistente_pendiente():
    res = rc.resolver_empresa_id("UNIDAD_FANTASMA")
    assert res.resuelto is False


def test_sucursal_softrestaurant_resuelve_unica():
    # CIENFUEGOS -> server dedicado -> 1 sola sucursal en el mapeo
    unidad = rc.get_server_by_unidad_codigo("CIENFUEGOS")
    server_id = unidad.get("server_id") or unidad.get("id")
    res = rc.resolver_sucursal_id(server_id)
    assert res.resuelto is True
    assert isinstance(res.canonical_id, int)


def test_sucursal_mpro_sin_origen_sigue_ambiguo():
    # Sin sucursal_origen, el server MPRO compartido NO se puede desambiguar -> AMBIGUO
    unidad = rc.get_server_by_unidad_codigo("ORIGEN")
    server_id = unidad.get("server_id") or unidad.get("id")
    res = rc.resolver_sucursal_id(server_id)
    assert res.resuelto is False
    assert res.motivo == "AMBIGUO_MULTISUCURSAL"


def test_sucursal_mpro_resuelve_con_origen():
    # Con SucursalOrigenID poblado: ORIGEN(0023)->1, 130QRO(0021)->2 (Sistema_Sucursales)
    unidad = rc.get_server_by_unidad_codigo("ORIGEN")
    server_id = unidad.get("server_id") or unidad.get("id")
    r_origen = rc.resolver_sucursal_id(server_id, "0023")
    r_qro = rc.resolver_sucursal_id(server_id, "0021")
    assert r_origen.resuelto is True and r_origen.canonical_id == 1
    assert r_qro.resuelto is True and r_qro.canonical_id == 2


def test_product_resolver_normalizes_mpro_system_aliases(monkeypatch):
    from core.inventarios import resolver_canonico as rc

    rc.clear_resolver_caches()

    monkeypatch.setattr(
        rc,
        "_server_id_de_unidad",
        lambda unidad_codigo: "server-mpro",
    )
    monkeypatch.setattr(
        rc,
        "_tabla_existe",
        lambda table_name: True,
    )

    calls = []

    def fake_fetchall(sql, params=(), as_dict=False):
        calls.append((sql, params))
        if "CodigoFuente, ProductoID" in sql:
            assert params[1] == "MPRO"
            return [("P001", 123)]
        if "SELECT TOP 1 ProductoID" in sql:
            assert params[1] == "MPRO"
            return [(123,)]
        return []

    monkeypatch.setattr(rc, "_fetchall", fake_fetchall)

    for alias in ("MPRO", "ManagementPro", "ManagmentPro", "MANAGEMENT PRO"):
        rc.clear_resolver_caches()
        monkeypatch.setattr(
            rc,
            "_server_id_de_unidad",
            lambda unidad_codigo: "server-mpro",
        )
        monkeypatch.setattr(
            rc,
            "_tabla_existe",
            lambda table_name: True,
        )
        monkeypatch.setattr(rc, "_fetchall", fake_fetchall)

        loaded = rc.precargar_productos_mapeo("130QRO", alias)
        assert loaded == 1

        result = rc.resolver_producto_id("130QRO", alias, "P001")
        assert result.resuelto is True
        assert result.canonical_id == 123


def test_product_resolver_normalizes_softrestaurant_aliases(monkeypatch):
    from core.inventarios import resolver_canonico as rc

    rc.clear_resolver_caches()
    monkeypatch.setattr(
        rc,
        "_server_id_de_unidad",
        lambda unidad_codigo: "server-soft",
    )
    monkeypatch.setattr(
        rc,
        "_tabla_existe",
        lambda table_name: True,
    )

    def fake_fetchall(sql, params=(), as_dict=False):
        if "CodigoFuente, ProductoID" in sql:
            assert params[1] == "SOFTRESTAURANT_PRO"
            return [("A100001", 456)]
        if "SELECT TOP 1 ProductoID" in sql:
            assert params[1] == "SOFTRESTAURANT_PRO"
            return [(456,)]
        return []

    monkeypatch.setattr(rc, "_fetchall", fake_fetchall)

    loaded = rc.precargar_productos_mapeo("CIENFUEGOS", "SoftRestaurant")
    assert loaded == 1

    result = rc.resolver_producto_id(
        "CIENFUEGOS",
        "SOFTRESTAURANT",
        "A100001",
    )
    assert result.resuelto is True
    assert result.canonical_id == 456
