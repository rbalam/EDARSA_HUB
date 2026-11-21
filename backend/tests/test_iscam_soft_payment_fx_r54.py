from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENRICH = ROOT / 'backend' / 'core' / 'scheduler' / 'jobs' / 'inteligencia_comercial_enrich.py'


def _soft_payment_query_block():
    text = ENRICH.read_text(encoding='utf-8')
    return text.split('def _extract_softrestaurant', 1)[1].split('# ============================================================================\n# EXTRACCIÓN MPRO', 1)[0]


def test_softrestaurant_payments_use_historical_payment_exchange_rate_first():
    block = _soft_payment_query_block()
    fx = 'COALESCE(NULLIF(cp.tipodecambio, 0), NULLIF(fp.tipodecambio, 0), 1)'
    assert block.count(fx) == 2
    assert 'ISNULL(cp.importe, 0)' in block
    assert 'ISNULL(cp.propina, 0)' in block


def test_softrestaurant_payment_fx_is_not_hardcoded_to_usd_rate():
    block = _soft_payment_query_block()
    assert '* 16' not in block
    assert '= 16' not in block
    assert 'cp.tipodecambio' in block
    assert 'fp.tipodecambio' in block


def test_mpro_extractor_is_outside_softrestaurant_fx_change():
    text = ENRICH.read_text(encoding='utf-8')
    mpro = text.split('def _extract_mpro', 1)[1]
    assert 'cp.Cp_Importe AS importe' in mpro
    assert 'cp.Cp_Propina AS propina' in mpro
