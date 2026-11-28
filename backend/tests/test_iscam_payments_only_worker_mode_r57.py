from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISPATCHER = ROOT / 'tools' / 'mirror_sync' / 'universal_job_dispatcher.py'


def _mode_block():
    text = DISPATCHER.read_text(encoding='utf-8')
    return text.split('if mode == ISCAM_PAYMENTS_ONLY_RESYNC_MODE:', 1)[1].split('if mode == MPRO_FULL_HISTORY_MODE:', 1)[0]


def test_payments_only_operational_mode_is_closed():
    text = DISPATCHER.read_text(encoding='utf-8')
    assert 'ISCAM_PAYMENTS_ONLY_RESYNC_MODE = "ISCAM_PAYMENTS_ONLY_RESYNC"' in text
    block = _mode_block()
    assert 'ISCAM_PAYMENTS_ONLY_ACTIONS_FORBIDDEN' in block
    assert 'ISCAM_PAYMENTS_ONLY_EXACTLY_ONE_UNIT_REQUIRED' in block
    assert 'ISCAM_PAYMENTS_ONLY_CONFIRMATION_REQUIRED' in block
    assert 'ISCAM_PAYMENTS_ONLY_SQL_AUDIT_REQUIRED' in block


def test_payments_only_mode_invokes_only_closed_payment_script():
    block = _mode_block()
    assert 'resync_iscam_pagos_unidad.py' in block
    assert 'resync_softrestaurant_full_history.py' not in block
    assert 'backfill_detalle_producto_pendientes.py' not in block
    assert 'sync_cortes' not in block
    assert 'enrich_unidad' not in block


def test_payments_only_mode_requires_explicit_dates_and_execute_confirmation():
    block = _mode_block()
    assert 'fecha_inicio' in block
    assert 'fecha_fin' in block
    assert 'confirm_payments_only_resync' in block
    assert 'cmd.append("--execute")' in block
