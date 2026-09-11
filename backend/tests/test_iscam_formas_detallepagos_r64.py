from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTES = ROOT / 'backend' / 'modules' / 'inteligencia_comercial' / 'iscam_routes.py'


def _text():
    return ROUTES.read_text(encoding='utf-8')


def _helper():
    text = _text()
    return text.split('def _formas_pago_desde_detalle', 1)[1].split('# ============================================================================\n# 4) VENTAS POR FORMAS DE PAGO', 1)[0]


def test_formas_uses_certified_payment_detail_for_amounts():
    block = _helper()
    assert 'dbo.Finanzas_CortesCaja_DetallePagos' in block
    assert 'SUM(ISNULL(Importe,0)) AS total' in block
    assert 'SUM(ISNULL(Propina,0)) AS propina' in block
    assert 'TotalVenta' not in block
    assert 'TotalEfectivo' not in block
    assert 'TotalTarjetaDebito' not in block
    assert 'TotalTarjetaCredito' not in block


def test_formas_keeps_cortes_table_only_as_metadata():
    block = _helper()
    assert 'FROM dbo.Finanzas_CortesCaja c' in block
    assert 'c.FolioCorte' in block
    assert 'c.CajaNombre' in block
    assert 'c.FechaApertura = p.FechaHora' in block


def test_formas_maps_known_payment_families_and_falls_back_to_otros():
    block = _helper()
    for token in ('%EFECTIVO%', '%DOLAR%', '%CREDITO%', '%DEBITO%', '%CLIP%', '%INTERNACIONAL%', '%AMEX%', '%VALE%'):
        assert token in block
    assert 'CASE WHEN NOT' in block


def test_route_returns_new_helper_before_legacy_body():
    text = _text()
    route = text.split('async def ventas_formas_pago', 1)[1].split('@iscam_router.get("/formas-pago/por-ticket")', 1)[0]
    assert 'return _formas_pago_desde_detalle(unidad, nombre, d, h, group_by, limit, export_all)' in route


def test_formas_change_does_not_touch_sync_sales_or_product_detail():
    block = _helper()
    assert 'dbo.Sync_Sales' not in block
    assert 'Comercial_Inteligencia_VentasDetalleProducto' not in block
