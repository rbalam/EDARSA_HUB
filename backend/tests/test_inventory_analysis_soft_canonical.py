from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server.py"
SOFT = ROOT / "core" / "inventarios" / "analysis_soft_sources.py"


def test_soft_analysis_sources_are_canonical_nolive():
    source = SOFT.read_text(encoding="utf-8")
    assert "Inventario_MovimientosDetalle" in source
    assert "Inventario_Movimientos" in source
    assert "Inventario_TipoMovimiento" in source
    assert "Comercial_Inteligencia_VentasDetalleProducto" in source
    assert "RecetasService.get_componentes_bulk" in source
    assert "Compras_Inventarios_Movimientos_Sync" not in source
    assert "get_external_sql_connection" not in source


def test_soft_report_uses_canonical_activity_helper():
    source = SERVER.read_text(encoding="utf-8")
    marker = "async def _generate_soft_inventory_analysis_canonical"
    start = source.index(marker)
    fragment = source[start:start + 40000]
    assert "fetch_soft_activity_canonical" in fragment
    assert "actividad canonica movimientos=" in fragment


def test_soft_report_recovers_missing_final_detail_by_folio():
    source = SERVER.read_text(encoding="utf-8")
    marker = "async def _generate_soft_inventory_analysis_canonical"
    start = source.index(marker)
    fragment = source[start:start + 30000]
    assert "missing_detail_folios" in fragment
    assert "detalle recuperado por folio para completar cobertura" in fragment


def test_soft_selected_concepts_are_resolvable_by_nature():
    sync_source = (ROOT / "modules" / "compras" / "sync_service.py").read_text(
        encoding="utf-8"
    )
    movement_source = (
        ROOT / "core" / "inventarios" / "sync_movimientos_canonico.py"
    ).read_text(encoding="utf-8")

    for code in (
        "EAL", "ECA", "ECS", "ECO", "EDE", "EEH", "EPR", "ETR",
        "SDE", "SDV", "SPR", "STR",
    ):
        assert f'"{code}"' in sync_source

    # Los mapeos específicos conservan prioridad, pero cualquier concepto
    # SoftRestaurant seleccionado debe poder resolver su naturaleza E/S.
    assert 'if concepto.startswith("E"):' in sync_source
    assert 'if concepto.startswith("S"):' in sync_source
    assert "return 3" in sync_source
    assert "return 4" in sync_source
    assert "map_tipo_movimiento_softrestaurant" in movement_source

def test_soft_ledger_accepts_canonical_warehouse_id_scope():
    source = SOFT.read_text(encoding="utf-8")
    assert "CONVERT(varchar(50), a.AlmacenID)" in source
    assert "a.CodigoAlmacen" in source
    assert "a.NombreAlmacen" in source
    assert "params.extend(warehouses)" in source

def test_inventory_backfill_does_not_hardcode_unit_exclusions():
    backfill = (ROOT / "tests" / "backfill_inventario.py").read_text(encoding="utf-8")
    assert "CIENFUEGOS se omite" not in backfill
    assert "UNIDADES = [u.strip()" in backfill
    assert "s.activo = 1" in backfill
    assert "u.activo = 1" in backfill

def test_soft_sync_reads_both_inventory_movement_sources_without_sales_sync():
    movement_source = (
        ROOT / "core" / "inventarios" / "sync_movimientos_canonico.py"
    ).read_text(encoding="utf-8")

    assert "def _query_origen_soft_movsinv" in movement_source
    assert "def _query_origen_soft_presentaciones" in movement_source
    assert "FROM movsinv i" in movement_source
    assert "FROM movtosalmacen m" in movement_source
    assert "source_movto" in movement_source
    assert "def _merge_soft_movement_sources" in movement_source
    assert "duplicados_fuente_omitidos" in movement_source
    assert "RTRIM(LTRIM(i.idinsumo)) AS producto_cod" in movement_source
    assert "RTRIM(LTRIM(ip.idinsumo)) AS producto_cod" in movement_source
    assert "Comercial_Inteligencia_VentasDetalleProducto" not in movement_source


def test_soft_source_merge_prefers_movsinv_for_same_natural_key():
    from core.inventarios.sync_movimientos_canonico import (
        _merge_soft_movement_sources,
    )

    direct = [{
        "fecha": "2026-10-10 12:00:00",
        "almacen_cod": "200",
        "concepto": "SDE",
        "producto_cod": "A100",
        "source_movto": "123",
        "folio": "I:M:123",
    }]
    presentation = [{
        "fecha": "2026-10-10 12:00:00",
        "almacen_cod": "200",
        "concepto": "SDE",
        "producto_cod": "A100",
        "source_movto": "123",
        "folio": "123",
    }]

    merged, duplicates = _merge_soft_movement_sources(
        direct,
        presentation,
    )

    assert duplicates == 1
    assert merged == direct


def test_soft_sync_prefixes_movsinv_natural_references():
    movement_source = (
        ROOT / "core" / "inventarios" / "sync_movimientos_canonico.py"
    ).read_text(encoding="utf-8")

    assert "'I:M:' + CAST(i.movto AS VARCHAR(24))" in movement_source
    assert "'I:T:' + CAST(i.traspaso AS VARCHAR(24))" in movement_source
    assert "'I:C:' + CAST(i.idcompra AS VARCHAR(24))" in movement_source
    assert "'I:F:' + CAST(i.invfisico AS VARCHAR(24))" in movement_source

def test_soft_movement_sync_uses_server_authorized_origin_concepts():
    movement_source = (
        ROOT / "core" / "inventarios" / "sync_movimientos_canonico.py"
    ).read_text(encoding="utf-8")
    job_source = (
        ROOT / "core" / "scheduler" / "jobs" / "sync_compras_job.py"
    ).read_text(encoding="utf-8")

    # La configuración viene de la autoridad canónica por servidor.
    assert "s.tipos_movimiento" in job_source
    assert "'tipos_movimiento': server.get('tipos_movimiento', [])" in job_source

    # Ambos motores filtran antes de homologar ConceptoOrigen -> TipoMovimientoID.
    assert "tipos_movimiento_autorizados" in movement_source
    assert "concepto_origen in tipos_movimiento_autorizados" in movement_source
    assert "filtrados_no_autorizados" in movement_source
    assert "MPRO sin tipos_movimiento configurados; fail-closed" in movement_source


def test_inventory_movement_authorization_does_not_touch_commercial_syncs():
    movement_source = (
        ROOT / "core" / "inventarios" / "sync_movimientos_canonico.py"
    ).read_text(encoding="utf-8")
    job_source = (
        ROOT / "core" / "scheduler" / "jobs" / "sync_compras_job.py"
    ).read_text(encoding="utf-8")

    protected_names = ("sync_comercial_abiertas_v2", "sync_comercial_v2")
    for protected_name in protected_names:
        assert protected_name not in movement_source
        assert protected_name not in job_source

def test_soft_sync_compras_runs_almacenes_before_movimientos():
    job_source = (
        ROOT / "core" / "scheduler" / "jobs" / "sync_compras_job.py"
    ).read_text(encoding="utf-8")

    assert '("almacenes", sync_almacenes_from_server, "ALMACENES")' in job_source
    assert 'sync_steps.extend(_core_inventory_sync_steps())' in job_source
    assert "_execute_inventory_sql_with_timeout" in job_source


def test_soft_movements_keep_resolvable_rows_when_some_are_pending():
    movement_source = (
        ROOT / "core" / "inventarios" / "sync_movimientos_canonico.py"
    ).read_text(encoding="utf-8")

    assert "PARTIAL_WITH_PENDING" in movement_source
    assert "No hay movimientos SoftRestaurant resolubles en la ventana" in movement_source
    assert "DELETE FROM Inventario_Movimientos" not in movement_source
    assert "DELETE d" not in movement_source

def test_inventory_owner_can_scope_softrestaurant_without_mpro():
    job_source = (
        ROOT / "core" / "scheduler" / "jobs" / "sync_compras_job.py"
    ).read_text(encoding="utf-8")

    assert "SYNC_COMPRAS_SYSTEM_FILTER" in job_source
    assert "def _system_allowed_by_sync_filter" in job_source
    assert "_system_allowed_by_sync_filter(row.get('system_type'))" in job_source


def test_inventory_github_owner_is_non_production_and_canonical():
    owner_source = (
        ROOT / "tools" / "run_inventory_github_owner.py"
    ).read_text(encoding="utf-8")

    assert "GITHUB_INVENTORY_OWNER_PRODUCTION_FORBIDDEN" in owner_source
    assert "run_sync_compras_job" in owner_source
    assert '"production_touched"] = False' in owner_source

def test_soft_movements_prefer_visible_inventory_code_for_same_canonical_product():
    source = SOFT.read_text(encoding="utf-8")
    server_source = SERVER.read_text(encoding="utf-8")

    assert "visible_product_codes" in source
    assert "OUTER APPLY" in source
    assert "pmo.ProductoID=d.ProductoID" in source
    assert "CASE WHEN pmo.CodigoFuente IN" in source
    assert "visible_product_codes=sorted(productos.keys())" in server_source



def test_soft_presentation_warehouses_do_not_apply_sales():
    source = SOFT.read_text(encoding="utf-8")
    server_source = SERVER.read_text(encoding="utf-8")

    assert "include_sales: bool = True" in source
    assert "if not include_sales:" in source
    assert "soft_sales_enabled" in server_source
    assert "unidad_natural == 'presentaciones'" in server_source
    assert "include_sales=soft_sales_enabled" in server_source


def test_report_payload_preserves_warehouse_type_for_backend_rule():
    frontend = (ROOT.parent / "frontend" / "src" / "pages" / "Reportes.js").read_text(
        encoding="utf-8"
    )
    assert "tipo_almacen: almacenTipo" in frontend
    assert "unidad_natural: a.unidad_natural" in frontend
