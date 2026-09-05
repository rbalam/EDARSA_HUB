from pathlib import Path


def _block():
    text = Path('modules/inteligencia_comercial/iscam_routes.py').read_text(encoding='utf-8')
    return text.split('@iscam_router.get(\"/ventas-periodos\")', 1)[1].split('@iscam_router.get(\"/ventas-periodos/productos\")', 1)[0]


def test_iscam_ventas_periodos_reuses_exact_executive_contract():
    block = _block()
    assert 'KPIsCanonicosService.resumen_periodo_desglosado' in block
    assert 'acumulado_cerrado' in block
    assert 'CERRADO_SIN_DIA_OPERATIVO_ACTUAL' in block
    assert 'dbo.vw_Comercial_KPIs_Diarios_v2_Runtime' not in block
    assert 'dbo.Sync_Sales' not in block
    assert 'SUM(' not in block
    assert 'venta / cheques' not in block
    assert 'venta / cli' not in block


def test_iscam_ventas_periodos_keeps_public_response_contract():
    block = _block()
    for key in ('periodo', 'venta_total', 'propinas', 'cheques', 'clientes', 'cheque_promedio', 'consumo_promedio'):
        assert key in block
    assert 'KPIsCanonicosService.resumen_periodo_desglosado.acumulado_cerrado' in block
