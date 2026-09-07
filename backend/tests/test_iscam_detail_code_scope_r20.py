from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTES = ROOT / 'backend' / 'modules' / 'inteligencia_comercial' / 'iscam_routes.py'


def between(text, a, b):
    return text[text.index(a):text.index(b)]


def test_direct_detail_endpoints_resolve_canonical_unit_code():
    text = ROUTES.read_text(encoding='utf-8')
    products = between(text, 'async def ventas_periodos_productos', 'async def ventas_periodos_tickets')
    tickets = between(text, 'async def ventas_periodos_tickets', '# ============================================================================\n# 2) RESUMEN DE CUENTAS')
    accounts = between(text, 'async def resumen_cuentas', 'async def cuenta_detalle')
    account_detail = between(text, 'async def cuenta_detalle', '# ============================================================================\n# 3) COMANDAS DE VENTA')
    comandas = between(text, 'async def comandas_venta', '# ============================================================================\n# 4) VENTAS POR FORMAS DE PAGO')
    assert 'resolver_codigo(unidad)' in products
    assert 'resolver_codigo(unidad)' in tickets
    assert 'resolver_codigo(unidad)' in account_detail
    assert 'resolver_codigo(unidad)' in comandas
    assert 'resolver_pk(unidad)' in accounts
    assert 'resolver_codigo(unidad)' in accounts


def test_kpi_header_paths_keep_uuid_pk_contract():
    text = ROUTES.read_text(encoding='utf-8')
    header = between(text, 'async def ventas_periodos(', 'async def ventas_periodos_productos')
    accounts = between(text, 'async def resumen_cuentas', 'async def cuenta_detalle')
    assert 'unidad_pk = UnidadesService.resolver_pk(unidad)' in header
    assert 'unidad_pks=[str(unidad_pk)]' in header
    grouped_prefix = accounts[:accounts.index('unidad_pk = UnidadesService.resolver_codigo(unidad)')]
    assert 'unidad_pk = UnidadesService.resolver_pk(unidad)' in grouped_prefix
    assert 'unidad_pks=[str(unidad_pk)]' in grouped_prefix
