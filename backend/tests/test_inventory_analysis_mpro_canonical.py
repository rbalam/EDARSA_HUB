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


def test_mpro_drilldown_is_canonical_and_reconciles_totals():
    server_source = SERVER.read_text(encoding="utf-8")
    assert 'Autoriza drilldown por unidad canónica para SoftRestaurant y MPRO' in server_source
    assert 'm.EmpresaID = %s AND m.SucursalID = %s' in server_source
    assert 'RECLASIFICACION_VENTAS' in server_source
    assert 'get_mpro_sales_consumption_detail' in server_source
    assert '"total": total' in server_source


def test_mpro_movement_filter_uses_server_configuration():
    movement_source = (
        ROOT / "core" / "inventarios" / "sync_movimientos_canonico.py"
    ).read_text(encoding="utf-8")
    assert "concepto_origen in tipos_movimiento_autorizados" in movement_source
    assert "MPRO sin tipos_movimiento configurados; fail-closed" in movement_source
