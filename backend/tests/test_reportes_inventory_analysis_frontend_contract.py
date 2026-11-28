from pathlib import Path


def test_reportes_uses_canonical_unit_for_warehouses_and_physical_inventories():
    source = (Path(__file__).resolve().parents[2] / 'frontend/src/pages/Reportes.js').read_text(encoding='utf-8')
    assert '/config-asignaciones/almacenes/${selectedUnidad}' in source
    assert '/compras/inventarios-fisicos/${selectedUnidad}' in source
    assert '/servers/${filters.server_id}/almacenes' not in source
    assert '/servers/${filters.server_id}/inventarios' not in source
    assert '/compras/inventarios-fisicos/${filters.server_id}' not in source
    assert 'const prevUnidadRef = useRef(selectedUnidad);' in source
