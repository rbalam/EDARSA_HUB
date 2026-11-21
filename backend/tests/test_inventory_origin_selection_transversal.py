"""Regresiones transversales de conceptos origen MPRO/SoftRestaurant (sin SQL LIVE)."""
from pathlib import Path

from core.inventarios.movement_filter_config import (
    movement_origin_sql_filter,
    normalize_movement_codes,
)
from core.inventarios.analysis_mpro_canonical import _fetch_ledger_net


ROOT = Path(__file__).resolve().parents[1]


class Cursor:
    def __init__(self, rows):
        self.rows = rows
        self.statements = []

    def execute(self, sql, params):
        self.statements.append((sql, tuple(params)))

    def fetchall(self):
        return self.rows


def test_any_source_code_is_selectable_including_adjustments():
    selected = ["010", "011", {"codigo": "106"}, {"ConceptoOrigen": " 508 "}, "010"]
    assert normalize_movement_codes(selected) == ["010", "011", "106", "508"]
    sql, params = movement_origin_sql_filter(selected)
    assert sql.count("%s") == 4
    assert params == ["010", "011", "106", "508"]
    assert "MOVIMIENTO_POS|%" in sql


def test_unselected_movements_display_zero_but_do_not_delete_ledger():
    where, params = movement_origin_sql_filter([])
    assert where == "1=0"
    assert params == []


def test_130qro_coca_cola_mpro_selected_transfer_106_yields_24_not_31():
    """Ejemplo reportado: dos entradas por traspaso de 12; ventas aparte."""
    cursor = Cursor([{"ProductoID": "7", "neto": 24}])
    totals = _fetch_ledger_net(
        cursor,
        empresa_id=9,
        sucursal_id=130,
        product_ids_by_code={"0000000160": 7},
        fecha_ini="2026-10-16",
        fecha_fin="2026-10-23",
        warehouses=["0021"],
        selected_movement_codes=["106"],
    )
    assert totals == {"0000000160": 24.0}
    sql, params = cursor.statements[0]
    assert "Inventario_MovimientosDetalle" in sql
    assert "AND (" in sql and "MOVIMIENTO_POS|%" in sql
    # En el SQL el concepto se filtra antes que el almacen. Verificar
    # la secuencia completa, no el ultimo parametro (que es un almacen).
    assert params == (
        9, 130, "2026-10-16", "2026-10-23", 7,
        "106", "0021", "0021", "0021",
    )
    assert sql.count("%s") == len(params)
    assert sql.index("AND (m.ReferenciaTipo") < sql.index("AND (CONVERT(varchar(50), a.AlmacenID)")
    assert "m.EmpresaID=%s" in sql and "m.SucursalID=%s" in sql
    source = (ROOT / "core/inventarios/analysis_mpro_canonical.py").read_text(encoding="utf-8")
    assert "movements = ledger" in source
    assert "theoretical = initial + movements - sales" in source


def test_legacy_movements_without_traceable_origin_not_guessed_from_canonical_type():
    sql, params = movement_origin_sql_filter(["106"])
    assert "tm.Codigo" not in sql
    assert "MOVIMIENTO_POS|%" in sql
    assert params == ["106"]


def test_report_detail_both_use_same_origin_filter_for_both_engines():
    mpro = (ROOT / "core/inventarios/analysis_mpro_canonical.py").read_text(encoding="utf-8")
    soft = (ROOT / "core/inventarios/analysis_soft_sources.py").read_text(encoding="utf-8")
    server = (ROOT / "server.py").read_text(encoding="utf-8")
    assert "movement_origin_sql_filter(selected_movement_codes)" in mpro
    assert soft.count("movement_origin_sql_filter(selected_movement_codes)") == 2
    assert "selected_movement_codes=server.get(\"tipos_movimiento\") or []" in server
    assert "origin_filter, origin_params = movement_origin_sql_filter(" in server
    assert "AND ({origin_filter})" in server


def test_no_protected_commercial_sync_files_changed_by_inventory_contract():
    protected = ("sync_comercial_abiertas_v2_job.py", "sync_comercial_v2_job.py")
    module = (ROOT / "core/inventarios/movement_filter_config.py").read_text(encoding="utf-8")
    for name in protected:
        assert name not in module


def test_mpro_report_binds_source_concepts_before_warehouse_filters():
    """Regresion real: MPRO 130QRO transferencia 106 no debe recibir '0021' como concepto."""
    cursor = Cursor([{"ProductoID": "7", "neto": 24}])
    totals = _fetch_ledger_net(
        cursor,
        empresa_id=9,
        sucursal_id=130,
        product_ids_by_code={"0000000160": 7},
        fecha_ini="2026-10-16",
        fecha_fin="2026-10-23",
        warehouses=["0021", "BODEGA"],
        selected_movement_codes=["050", "106"],
    )
    assert totals == {"0000000160": 24.0}
    sql, params = cursor.statements[0]
    # El filtro por concepto aparece ANTES del filtro por almacen en SQL.
    assert sql.index("AND (m.ReferenciaTipo") < sql.index("AND (CONVERT(varchar(50), a.AlmacenID)")
    assert params == (
        9, 130, "2026-10-16", "2026-10-23", 7,
        "050", "106",
        "0021", "BODEGA",
        "0021", "BODEGA",
        "0021", "BODEGA",
    )
    assert sql.count("%s") == len(params)


def test_mpro_report_binds_source_concepts_with_no_warehouse_filter():
    cursor = Cursor([{"ProductoID": "7", "neto": 24}])
    _fetch_ledger_net(
        cursor,
        empresa_id=9,
        sucursal_id=130,
        product_ids_by_code={"0000000160": 7},
        fecha_ini="2026-10-16",
        fecha_fin="2026-10-23",
        warehouses=[],
        selected_movement_codes=["106"],
    )
    sql, params = cursor.statements[0]
    assert params == (9, 130, "2026-10-16", "2026-10-23", 7, "106")
    assert sql.count("%s") == len(params)


def test_movement_origin_predicate_escapes_literal_percent_for_pymssql():
    # pymssql Cursor.execute(sql, tuple(params)) aplica formato tipo %s.
    # Un wildcard % literal sin escapar rompe la interpolacion.
    sql, params = movement_origin_sql_filter(["106", "050"])
    assert "MOVIMIENTO_POS|%%" in sql
    assert sql.count("%s") == len(params)
    formatted = sql % tuple(params)
    assert "MOVIMIENTO_POS|%'" in formatted
    assert "'MOVIMIENTO_POS|%%'" not in formatted
    # Debe conservar los codigos de origen sin convertirlos a enteros.
    assert params == ["106", "050"]


def test_missing_selected_concepts_still_fail_closed():
    sql, params = movement_origin_sql_filter([])
    assert sql == "1=0"
    assert params == []
