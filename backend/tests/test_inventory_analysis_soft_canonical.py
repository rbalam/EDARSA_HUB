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
