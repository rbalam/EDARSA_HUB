"""Regresiones de detalle canónico SoftRestaurant.

No requieren SQL LIVE: prueban la misma ventana, identidad, almacenes,
producto y recetas empleadas por el análisis de inventarios.
"""
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from core.inventarios import analysis_soft_sources as sources


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executed = []

    def execute(self, sql, params):
        self.executed.append((sql, tuple(params)))

    def fetchall(self):
        return list(self.rows)


def _id(value):
    return SimpleNamespace(resuelto=True, canonical_id=value)


def test_movement_detail_uses_canonical_ledger_full_window_and_warehouse_scope():
    cursor = FakeCursor([
        {
            "fecha": datetime(2026, 10, 20, 11),
            "concepto": "ECA",
            "descripcion": "Entrada",
            "naturaleza": "E",
            "cantidad": 40,
            "almacen": "PRODUCCION",
            "referencia": "ABC",
            "referencia_tipo": "MOVIMIENTO_POS|ECA",
        },
        {
            "fecha": datetime(2026, 10, 20, 12),
            "concepto": "SCA",
            "descripcion": "Salida",
            "naturaleza": "S",
            "cantidad": 4,
            "almacen": "PRODUCCION",
            "referencia": "XYZ",
            "referencia_tipo": "MOVIMIENTO_POS|SCA",
        },
    ])
    with patch.object(sources, "resolver_empresa_id", return_value=_id(12)), patch.object(
        sources, "resolver_sucursal_id", return_value=_id(34)
    ):
        detail = sources.get_soft_movement_detail(
            cursor,
            server_id="srv",
            unidad_codigo="CF",
            sucursal_origen_id="1",
            componente_codigo="A100235",
            fecha_ini="2026-10-19 09:00:01",
            fecha_fin="2026-10-21 19:59:59",
            warehouses=["100"],
        )
    sql, params = cursor.executed[0]
    assert "Inventario_MovimientosDetalle" in sql
    assert "EXISTS (" in sql  # Evita multiplicar filas por mappings duplicados.
    assert "TOP 1000" not in sql
    assert params[:6] == (12, 34, "2026-10-19 09:00:01", "2026-10-21 19:59:59", "srv", "A100235")
    assert params[-3:] == ("100", "100", "100")
    assert detail["totales"] == {"entradas": 40.0, "salidas": 4.0, "neto": 36.0}
    assert len(detail["rows"]) == 2
    assert detail["rows"][0]["concepto"] == "ECA"


def test_sales_detail_uses_same_recipe_explosion_as_parent_report():
    cursor = FakeCursor([
        {"fecha_operacion": "2026-10-19", "producto_codigo_fuente": "BEBIDA1", "cantidad": 2},
        {"fecha_operacion": "2026-10-20", "producto_codigo_fuente": "BEBIDA1", "cantidad": 3},
    ])
    def fake_columns(_cursor, _table):
        return {"unidad_negocio_id", "fecha_operacion", "producto_codigo_fuente", "cantidad"}
    with patch.object(sources, "_fetch_table_columns", side_effect=fake_columns), patch.object(
        sources.RecetasService, "get_componentes_bulk",
        return_value=[{"producto_codigo_fuente": "BEBIDA1",
                       "componente_codigo_fuente": "A100235", "cantidad": 0.33}],
    ):
        detail = sources.get_soft_sales_consumption_detail(
            cursor, unidad_codigo="CF", server_id="srv", componente_codigo="A100235",
            fecha_ini="2026-10-19 00:00:00", fecha_fin="2026-10-20 23:59:59",
        )
    sql, params = cursor.executed[0]
    assert "Comercial_Inteligencia_VentasDetalleProducto" in sql
    assert "CAST(fecha_operacion AS date), producto_codigo_fuente" in sql
    assert params == ("CF", "2026-10-19 00:00:00", "2026-10-20 23:59:59")
    assert len(detail["rows"]) == 2
    assert round(detail["total"], 4) == 1.65


def test_sales_detail_no_recipe_consumption_returns_zero():
    cursor = FakeCursor([{"fecha_operacion": "2026-10-19",
                          "producto_codigo_fuente": "NO_RECIPE", "cantidad": 5}])
    with patch.object(sources, "_fetch_table_columns", return_value={
        "unidad_negocio_id", "fecha_operacion", "producto_codigo_fuente", "cantidad",
    }), patch.object(sources.RecetasService, "get_componentes_bulk", return_value=[]):
        detail = sources.get_soft_sales_consumption_detail(
            cursor, unidad_codigo="CF", server_id="srv", componente_codigo="A100235",
            fecha_ini="2026-10-19", fecha_fin="2026-10-20",
        )
    assert detail == {"rows": [], "total": 0.0}


def test_movements_fail_closed_without_canonical_identity():
    cursor = FakeCursor([])
    with patch.object(sources, "resolver_empresa_id", return_value=SimpleNamespace(
        resuelto=False
    )), patch.object(sources, "resolver_sucursal_id", return_value=_id(5)):
        try:
            sources.get_soft_movement_detail(
                cursor, server_id="srv", unidad_codigo="CF", sucursal_origen_id="1",
                componente_codigo="A100235", fecha_ini="2026-10-19",
                fecha_fin="2026-10-20",
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Debe rechazar identidad canónica no resuelta")
    assert cursor.executed == []


def test_grouped_product_codes_use_parameterized_movement_filter():
    cursor = FakeCursor([])
    with patch.object(sources, "resolver_empresa_id", return_value=_id(12)), patch.object(
        sources, "resolver_sucursal_id", return_value=_id(34)
    ):
        sources.get_soft_movement_detail(
            cursor, server_id="srv", unidad_codigo="CF", sucursal_origen_id="1",
            componente_codigo="A100235, A100236",
            fecha_ini="2026-10-19", fecha_fin="2026-10-20",
        )
    sql, params = cursor.executed[0]
    assert "pmo.CodigoFuente IN (%s,%s)" in sql
    assert params[-3:] == ("srv", "A100235", "A100236")


def test_grouped_product_codes_sum_sales_recipe_factors_once():
    cursor = FakeCursor([
        {"fecha_operacion": "2026-10-19", "producto_codigo_fuente": "BEBIDA1", "cantidad": 2},
    ])
    components = [
        {"producto_codigo_fuente": "BEBIDA1", "componente_codigo_fuente": "A100235", "cantidad": 0.5},
        {"producto_codigo_fuente": "BEBIDA1", "componente_codigo_fuente": "A100236", "cantidad": 0.25},
    ]
    with patch.object(sources, "_fetch_table_columns", return_value={
        "unidad_negocio_id", "fecha_operacion", "producto_codigo_fuente", "cantidad",
    }), patch.object(sources.RecetasService, "get_componentes_bulk", return_value=components):
        detail = sources.get_soft_sales_consumption_detail(
            cursor, unidad_codigo="CF", server_id="srv",
            componente_codigo="A100235,A100236",
            fecha_ini="2026-10-19", fecha_fin="2026-10-20",
        )
    assert detail["total"] == 1.5
    assert len(detail["rows"]) == 1
