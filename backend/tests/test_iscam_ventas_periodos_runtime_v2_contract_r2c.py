from pathlib import Path


def _block():
    text = Path('modules/inteligencia_comercial/iscam_routes.py').read_text(encoding='utf-8')
    return text.split('@iscam_router.get(\"/ventas-periodos\")', 1)[1].split('@iscam_router.get(\"/ventas-periodos/productos\")', 1)[0]


def test_iscam_ventas_periodos_uses_runtime_v2_header():
    block = _block()
    assert 'dbo.vw_Comercial_KPIs_Diarios_v2_Runtime' in block
    assert 'k.fecha_operacion' in block
    assert 'k.ventas_total' in block
    assert 'k.tickets_total' in block
    assert 'k.pax_total' in block
    assert 'dbo.Sync_Sales' not in block
    assert "s.status = 'COMPLETED'" not in block


def test_iscam_ventas_periodos_keeps_public_response_contract():
    block = _block()
    for key in ('periodo', 'venta_total', 'cheques', 'clientes', 'cheque_promedio', 'consumo_promedio'):
        assert key in block
