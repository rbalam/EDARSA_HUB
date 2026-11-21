from pathlib import Path


def test_inventory_analysis_uses_canonical_unit_scope():
    server_source = Path("server.py").read_text(encoding="utf-8")

    marker = '@api_router.post("/reports/inventory-analysis")'
    start = server_source.index(marker)
    fragment = server_source[start:start + 7000]

    assert "resolve_authorized_unidad_scope" in fragment
    assert '"OPERACIONES_VER"' in fragment
    assert "unidad_scope.server_id" in fragment
    assert "unidad_scope.sucursal_origen_id" in fragment
    assert "validate_server_access_unified" in fragment
    assert "Compatibilidad temporal" in fragment


def test_reportes_sends_selected_canonical_unit():
    frontend_source = Path(
        "../frontend/src/pages/Reportes.js"
    ).read_text(encoding="utf-8")

    marker = "api.post('/reports/inventory-analysis'"
    start = frontend_source.index(marker)
    fragment = frontend_source[start:start + 2500]

    assert "unidad: String(selectedUnidad || '').trim()" in fragment
    assert "server_id: String(filters.server_id || '').trim()" in fragment
