from pathlib import Path

P = Path(__file__).resolve().parents[1] / 'modules' / 'inteligencia_comercial' / 'iscam_routes.py'

def test_no_direct_isoformat_for_row_fecha():
    text = P.read_text(encoding='utf-8')
    assert 'r[\"fecha\"].isoformat() if r[\"fecha\"] else None' not in text
    assert text.count('_iso(r[\"fecha\"])') >= 2

def test_cuentas_none_safe_date():
    text = P.read_text(encoding='utf-8')
    start = text.index('@iscam_router.get(\"/cuentas\")')
    end = text.index('@iscam_router.get(\"/cuentas/detalle\")', start)
    assert '_iso(r[\"fecha\"])' in text[start:end]

def test_ticket_drill_safe_date():
    text = P.read_text(encoding='utf-8')
    start = text.index('@iscam_router.get(\"/ventas-periodos/tickets\")')
    end = text.index('# ============================================================================\n# 2) RESUMEN DE CUENTAS', start)
    assert '_iso(r[\"fecha\"])' in text[start:end]
