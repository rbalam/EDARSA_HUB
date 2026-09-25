from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / 'tools' / 'mirror_sync' / 'universal_job_bridge.py'


def _text():
    return BRIDGE.read_text(encoding='utf-8')


def test_bridge_knows_payments_only_mode():
    text = _text()
    assert 'ISCAM_PAYMENTS_ONLY_RESYNC_MODE = "ISCAM_PAYMENTS_ONLY_RESYNC"' in text
    assert text.count('elif mode == ISCAM_PAYMENTS_ONLY_RESYNC_MODE:') == 2


def test_bridge_payments_only_job_contract_is_closed():
    text = _text()
    assert 'ISCAM_PAYMENTS_ONLY_ACTIONS_FORBIDDEN' in text
    assert 'ISCAM_PAYMENTS_ONLY_EXACTLY_ONE_UNIT_REQUIRED' in text
    assert 'ISCAM_PAYMENTS_ONLY_FECHA_INICIO_INVALID' in text
    assert 'ISCAM_PAYMENTS_ONLY_FECHA_FIN_INVALID' in text
    assert 'ISCAM_PAYMENTS_ONLY_CONFIRMATION_REQUIRED' in text


def test_bridge_payments_only_checks_are_readonly_only():
    text = _text()
    assert 'ISCAM_PAYMENTS_ONLY_AUDIT_REQUIRED' in text
    assert 'ISCAM_PAYMENTS_ONLY_ONLY_SQL_AUDIT_ALLOWED' in text


def test_payments_only_does_not_fall_into_actions_required_branch():
    text = _text()
    first = text.index('elif mode == ISCAM_PAYMENTS_ONLY_RESYNC_MODE:')
    following = text.index('elif mode == MPRO_FULL_HISTORY_MODE:', first)
    block = text[first:following]
    assert 'actions not in (None, [])' in block
    assert 'ACTIONS_REQUIRED' not in block
