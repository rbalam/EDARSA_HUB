"""Regression contract for SoftRestaurant inventory drilldown RBAC/totals."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_backend_softrestaurant_drilldown_uses_canonical_unit_scope():
    source = _read("backend/server.py")
    assert "async def _resolve_detalle_producto_scope" in source
    assert 'matched_by == "unidad"' in source
    assert "resolve_authorized_unidad_scope(" in source
    assert "COMPRAS_VER" in source
    assert "request.server_id = canonical_server_id(token)" in source
    assert source.count("await _resolve_detalle_producto_scope(request, current_user)") == 2


def test_frontends_only_switch_softrestaurant_to_canonical_unit_token():
    reportes = _read("frontend/src/pages/Reportes.js")
    compras = _read("frontend/src/pages/Compras.js")
    assert reportes.count("selectedServer?.system_type === 'SoftRestaurant' ? selectedUnidad : filters.server_id") == 2
    assert compras.count("?.system_type === 'SoftRestaurant') ? selectedUnidad : selectedServer") == 2


def test_softrestaurant_consumption_modal_exposes_canonical_total():
    hook = _read("frontend/src/hooks/useDetalleProducto.js")
    modal = _read("frontend/src/components/compras/DetalleProductoModal.jsx")
    assert "systemType: systemType || ''" in hook
    assert "TOTAL VENTAS / CONSUMO:" in modal
    assert "fmt(totales.total || 0)" in modal
    assert "SOFTRESTAURANT" in modal
