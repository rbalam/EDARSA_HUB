from pathlib import Path

from core.inventarios.analysis_mpro_canonical import (
    _movement_display_and_theoretical,
)


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server.py"
MPRO = ROOT / "core" / "inventarios" / "analysis_mpro_canonical.py"


def test_mpro_theoretical_does_not_double_count_sales():
    calc = _movement_display_and_theoretical(
        initial_qty=100,
        ledger_net=-30,
        sales_qty=20,
    )
    assert calc["movimientos"] == -10
    assert calc["teorico"] == 70


def test_mpro_analysis_is_nolive_by_contract():
    source = MPRO.read_text(encoding="utf-8")
    forbidden = [
        "get_external_sql_connection",
        "execute_sql_query_func",
        "server['host']",
        'server["host"]',
        "Servidores_Conexiones.password",
    ]
    for token in forbidden:
        assert token not in source

    assert "get_edarsahub_pymssql_connection" in source
    assert "Compras_Inventarios_Fisicos_Sync" in source
    assert "Inventario_MovimientosDetalle" in source
    assert "Comercial_Inteligencia_VentasDetalleProducto" in source
    assert "Sync_Productos_Compuestos" in source
    assert "PRODUCTO_KIT" in source
    assert "Sync_Productos_Recetas" in source


def test_inventory_analysis_mpro_no_longer_returns_pending_guard():
    source = SERVER.read_text(encoding="utf-8")
    marker = '@api_router.post("/reports/inventory-analysis")'
    start = source.index(marker)
    end = source.index("# CAB-003 Fase 1A", start)
    fragment = source[start:end]

    assert "generate_mpro_inventory_analysis_canonical" in fragment
    assert "MPRO_CANONICAL_UNIT_REQUIRED" in fragment
    assert "INVENTORY_ANALYSIS_CANONICAL_PENDING" not in fragment


def test_mpro_analysis_preserves_unit_and_branch_scope():
    source = MPRO.read_text(encoding="utf-8")
    assert "unidad_negocio_id=%s" in source
    assert "resolver_sucursal_id(server_id, sucursal_origen_id)" in source
    assert "m.SucursalID=%s" in source
    assert "m.EmpresaID=%s" in source


def test_mpro_components_prefers_product_kit_contract():
    source = MPRO.read_text(encoding="utf-8")
    assert "FuenteDetalle" in source
    assert "NOT EXISTS" in source
    assert "MPRO_COMPONENTS_SOURCE_INCOMPLETE" in source


def test_mpro_sales_only_apply_to_warehouse_0001():
    source = MPRO.read_text(encoding="utf-8")
    assert '"0001" in selected_header_warehouse_ids' in source
    assert '"ventas_aplicadas": sales_enabled' in source
    assert 'sales_consumption = {}' in source


def test_mpro_drilldown_reconciles_to_user_selected_movements():
    server_source = SERVER.read_text(encoding="utf-8")
    assert 'Autoriza drilldown por unidad canónica para SoftRestaurant y MPRO' in server_source
    assert 'm.EmpresaID = %s AND m.SucursalID = %s' in server_source
    assert 'AND ({origin_filter})' in server_source
    assert 'movement_origin_sql_filter' in server_source
    assert 'RECLASIFICACION_VENTAS' not in server_source
    assert 'get_mpro_sales_consumption_detail' in server_source
    assert '"total": total' in server_source


def test_mpro_sync_keeps_all_concepts_without_deleting_historical_records():
    movement_source = (
        ROOT / "core" / "inventarios" / "sync_movimientos_canonico.py"
    ).read_text(encoding="utf-8")
    assert 'referencia_tipo = f"MOVIMIENTO_POS|{concepto_origen}"' in movement_source
    assert "effective_mpro_inventory_codes" not in movement_source
    assert "tipos_movimiento_autorizados" not in movement_source
    assert "DELETE d" not in movement_source
    assert "DELETE m" not in movement_source


def test_mpro_server_filters_show_complete_selectable_catalog():
    server_source = SERVER.read_text(encoding="utf-8")
    frontend = (ROOT.parent / "frontend" / "src" / "pages" / "Servidores.js").read_text(
        encoding="utf-8"
    )
    assert "Inventario_ConceptoMapeoOrigen" in server_source
    assert '"autorizado_analisis": True' in server_source
    assert "effective_mpro_inventory_codes" not in server_source
    assert "normalize_movement_codes" in server_source
    assert "const response = await api.get('/servers')" in frontend
    assert "const persistedServer = await readServerFiltersFromSql(serverId)" in frontend
    assert "setFilterLoadError(" in frontend
    assert "filterLoadError ? (" in frontend
    assert "setPersistedFiltersSnapshot(persistedFilters)" in frontend
    assert "disabled={!persistedFiltersSnapshot || Boolean(filterLoadError) || loadingOptions || savingFilters}" in frontend
    assert "const changedKeys = filterKeys.filter(" in frontend
    assert "await api.put(`/servers/${selectedServer.id}`, payload)" in frontend
    assert "setPersistedFiltersSnapshot(null);" in frontend
    assert "La lectura posterior no permitió verificar el servidor y sus movimientos" in frontend
    assert "autorizado_analisis === false" not in frontend
    assert "No participa en análisis" not in frontend


def test_mpro_report_filters_ledger_at_read_time_and_keeps_sales_separate():
    source = MPRO.read_text(encoding="utf-8")
    assert "movement_origin_sql_filter(selected_movement_codes)" in source
    assert "AND ({selected_filter})" in source
    assert "movements = ledger" in source
    assert "theoretical = initial + movements - sales" in source


def test_mpro_drilldown_preserves_origin_concept_labels():
    server_source = SERVER.read_text(encoding="utf-8")
    assert "referencia_tipo" in server_source
    assert "MOVIMIENTO_POS|" in server_source
    assert "MPRO_INVENTORY_MOVEMENT_POLICY" in server_source


def test_mpro_report_and_drilldown_accept_same_warehouse_identifiers():
    report = MPRO.read_text(encoding="utf-8")
    detail = SERVER.read_text(encoding="utf-8")
    for fragment in (
        "CONVERT(varchar(50), a.AlmacenID)",
        "a.CodigoAlmacen IN",
        "a.NombreAlmacen IN",
    ):
        assert fragment in report
    for fragment in (
        "CONVERT(varchar(50), al.AlmacenID)",
        "al.CodigoAlmacen IN",
        "al.NombreAlmacen IN",
    ):
        assert fragment in detail
    assert "params.extend(almacenes_limpios)" in detail
    assert "if tipo in ('E', 'EN', 'ENTRADA')" in detail
    assert "cantidad if tipo in ('E', 'EN', 'ENTRADA') else -cantidad" in detail



def test_mpro_movement_sync_uses_control_1_not_transaction_quantity():
    """CTRL_1 must match Fisico.Fi_Cantidad_Control_1, including GR products."""
    sync = (ROOT / "core" / "inventarios" / "sync_movimientos_canonico.py").read_text(
        encoding="utf-8"
    )
    from core.inventarios.sync_movimientos_canonico import _query_origen

    query = _query_origen("MPRO", 30, "0021")
    assert "Mv_Cantidad_Control_1, 0) AS cantidad" in query
    assert "Mv_Cantidad_1, 0) AS cantidad" not in query
    assert "Sc_Cve_Sucursal = '0021'" in query
    assert "Mv_Cantidad_Control_1" in sync
    # No fixed factor of 1000: quantities are already in CTRL_1 from source.


def test_soft_movement_sql_source_remains_independent_from_mpro_ctrl1():
    from core.inventarios.sync_movimientos_canonico import _query_origen

    soft_query = _query_origen("SOFTRESTAURANT", 30)
    assert "FROM movsinv i" in soft_query
    assert "Mv_Cantidad_Control_1" not in soft_query
