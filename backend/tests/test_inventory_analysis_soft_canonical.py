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


def test_soft_verified_non_sales_concepts_are_covered_without_sales_double_count():
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

    mapping_block = sync_source[
        sync_source.index("TIPO_MOVIMIENTO_SR_TO_EDARSAHUB = {"):
        sync_source.index("def registrar_concepto_movimiento_no_mapeado")
    ]
    for sales_code in ("SPV", "SCP", "SCS"):
        assert f'"{sales_code}":' not in mapping_block

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

    soft_block = movement_source[
        movement_source.index("# SoftRestaurant usa DOS fuentes complementarias verificadas:"):
        movement_source.index("def sync_movimientos_canonico")
    ]

    assert "FROM movsinv i" in soft_block
    assert "FROM movtosalmacen m" in soft_block
    assert "NOT EXISTS" in soft_block
    assert "RTRIM(LTRIM(i.idinsumo)) AS producto_cod" in soft_block
    assert "RTRIM(LTRIM(ip.idinsumo)) AS producto_cod" in soft_block
    assert "SPV" not in soft_block
    assert "Comercial_Inteligencia_VentasDetalleProducto" not in soft_block


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

    # SoftRestaurant filtra antes de homologar ConceptoOrigen -> TipoMovimientoID.
    assert "tipos_movimiento_autorizados" in movement_source
    assert "if is_softrestaurant:" in movement_source
    assert "concepto_origen in tipos_movimiento_autorizados" in movement_source
    assert "filtrados_no_autorizados" in movement_source
    assert "Sin tipos de movimiento autorizados para este servidor" in movement_source


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

