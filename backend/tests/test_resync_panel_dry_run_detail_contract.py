from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PANEL = (ROOT / 'frontend/src/components/admin/ResyncPanel.jsx').read_text(encoding='utf-8')


def test_dry_run_result_renders_backend_detail_rows():
    assert 'Array.isArray(resultado.detalle)' in PANEL
    assert 'dry-run-detail-${r.tipo.codigo}' in PANEL
    assert 'Fuente de consulta:' in PANEL
    assert 'Registros detallados:' in PANEL
    assert 'detalle.map((fila, detalleIdx)' in PANEL


def test_softrestaurant_business_metrics_are_visible():
    for label in (
        'Venta',
        'Propina',
        'Total c/ propina',
        'PAX',
        'Cheques',
        'Alimentos',
        'Bebidas',
        'Otros',
        'Cortesías',
        'Descuentos',
        'Subtotal',
        'IVA',
    ):
        assert label in PANEL

    for field in (
        'fila.ventas_total',
        'fila.propinas_total',
        'fila.total_con_propina',
        'fila.pax_total',
        'fila.tickets_total',
        'fila.alimentos',
        'fila.bebidas',
        'fila.otros',
        'fila.cortesias',
        'fila.descuentos',
        'fila.subtotal',
        'fila.iva',
    ):
        assert field in PANEL


def test_empty_detail_blocks_real_execution_warning():
    assert 'No ejecute REAL hasta validar la respuesta.' in PANEL
