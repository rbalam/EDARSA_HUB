"""Guardrails estáticos para precios sugeridos y KPIs comerciales UI."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend" / "src" / "pages"


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_precios_sugeridos_routes_exigen_usuario_y_permiso_rbac():
    source = _source(BACKEND / "modules/comercial/routes_precios_sugeridos.py")

    assert "from core.security import get_current_user" in source
    assert "from core.rbac.middleware import require_permission" in source
    assert "Depends(get_current_user)" in source
    assert "require_permission(_PERMISO_PRECIOS_SUGERIDOS)" in source
    assert "usuario: str = Query(..." not in source


def test_precios_sugeridos_service_parametriza_inputs_y_no_regresa_bug_orden():
    source = _source(BACKEND / "modules/comercial/services/precios_sugeridos_consolidado_service.py")

    assert "{Orden}" not in source
    assert "{Descripcion}" not in source
    assert "execute_sql_query_params" in source
    assert "p.ServerID = %s" in source
    assert "p.FamiliaNombre = %s" in source
    assert "p.Nombre LIKE %s OR p.CodigoFuente LIKE %s" in source
    assert "Descripcion = %s" in source
    assert "UsuarioModificacion = %s" in source


def test_dashboard_ejecutivo_ui_usa_consumo_pax_y_ventas_totales():
    source = _source(FRONTEND / "DashboardEjecutivo.js")

    assert "Ventas (neto)" not in source
    assert "Ventas Totales" in source
    assert "data.kpis?.ticket_promedio ?? data.kpis?.consumo_promedio_pax" not in source
    assert "data.kpis?.consumo_promedio_pax ?? data.kpis?.pax_promedio" in source


def test_comercial_ui_no_pinta_ticket_como_pax_promedio():
    source = _source(FRONTEND / "Comercial.js")

    assert "formatCurrency(datosUnidad.pax_promedio ?? 0)" in source
    assert "data.resumen.pax_promedio ?? data.resumen.consumo_promedio_global" in source
    assert "data.resumen.pax_total ?? data.resumen.total_comensales" in source
    assert "data.resumen.ventas_total ?? data.resumen.venta_total" in source
