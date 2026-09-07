from pathlib import Path

P = Path(__file__).resolve().parents[1] / 'modules' / 'inteligencia_comercial' / 'iscam_routes.py'

def sec(text,a,b): return text.split(a,1)[1].split(b,1)[0]

def test_ventas_drill_usa_uuid_unidad():
    t=P.read_text(encoding='utf-8')
    s=sec(t,'@iscam_router.get("/ventas-periodos/productos")','# ============================================================================\n# 2) RESUMEN DE CUENTAS')
    assert s.count('UnidadesService.resolver_pk(unidad)') >= 2
    assert '(str(unidad_pk), periodo)' in s
    assert '(str(unidad_pk), periodo, producto)' in s

def test_cuentas_detalle_usa_uuid_unidad():
    t=P.read_text(encoding='utf-8')
    s=sec(t,'# 2) RESUMEN DE CUENTAS','# 3) COMANDAS DE VENTA')
    assert s.count('UnidadesService.resolver_pk(unidad)') >= 2
    assert '(str(unidad_pk), folio)' in s
    assert '(str(unidad_pk), d, h)' in s

def test_comandas_usa_uuid_unidad():
    t=P.read_text(encoding='utf-8')
    s=sec(t,'# 3) COMANDAS DE VENTA','# 4) VENTAS POR FORMAS DE PAGO')
    assert 'UnidadesService.resolver_pk(unidad)' in s
    assert '(str(unidad_pk), d, h)' in s
    assert '(limit, str(unidad_pk), d, h)' in s
