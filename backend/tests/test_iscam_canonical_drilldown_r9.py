from pathlib import Path

P = Path(__file__).resolve().parents[1] / 'modules' / 'inteligencia_comercial' / 'iscam_routes.py'

def section(text, a, b):
    return text.split(a, 1)[1].split(b, 1)[0]

def test_ventas_periodo_productos_y_tickets_usan_detalle_canonico():
    t=P.read_text(encoding='utf-8')
    b=section(t, '@iscam_router.get("/ventas-periodos/productos")', '# ============================================================================\n# 2) RESUMEN DE CUENTAS')
    assert b.count('Comercial_Inteligencia_VentasDetalleProducto') >= 2
    assert '_period_sql("fecha_operacion"' in b
    assert 'dbo.Sync_Sales' not in b

def test_cuentas_y_comandas_usan_fuentes_canonicas():
    t=P.read_text(encoding='utf-8')
    c=section(t, '# 2) RESUMEN DE CUENTAS', '# 3) COMANDAS DE VENTA')
    assert 'KPIsCanonicosService.resumen_periodo_desglosado' in c
    assert 'Comercial_Inteligencia_VentasDetalleProducto' in c
    m=section(t, '# 3) COMANDAS DE VENTA', '# 4) VENTAS POR FORMAS DE PAGO')
    assert 'Comercial_Inteligencia_VentasDetalleProducto' in m
    assert 'dbo.Sync_Sales' not in m

def test_formas_pago_atribuye_por_apertura():
    t=P.read_text(encoding='utf-8')
    f=section(t, '# 4) VENTAS POR FORMAS DE PAGO', '# 4b) FORMAS DE PAGO POR TICKET')
    assert '_period_sql("FechaApertura"' in f
    assert 'FechaApertura >= %s AND FechaApertura < %s' in f
    assert 'FechaCierre >= %s' not in f
