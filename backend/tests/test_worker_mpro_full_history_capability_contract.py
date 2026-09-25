from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / 'tools' / 'mirror_sync' / 'universal_job_bridge.py'
DISPATCHER = ROOT / 'tools' / 'mirror_sync' / 'universal_job_dispatcher.py'
SCRIPT = ROOT / 'backend' / 'scripts' / 'resync_mpro_full_history.py'


def test_bridge_has_closed_mpro_resync_mode():
    text = BRIDGE.read_text(encoding='utf-8')
    assert 'MPRO_FULL_HISTORY_RESYNC' in text
    assert 'MPRO_RESYNC_ACTIONS_FORBIDDEN' in text
    assert 'MPRO_RESYNC_EXACTLY_ONE_UNIT_REQUIRED' in text
    assert 'MPRO_RESYNC_CONFIRMATION_REQUIRED' in text
    assert 'MPRO_RESYNC_ONLY_SQL_AUDIT_ALLOWED' in text


def test_dispatcher_uses_only_fixed_mpro_script():
    text = DISPATCHER.read_text(encoding='utf-8')
    assert 'resync_mpro_full_history.py' in text
    assert 'MPRO_RESYNC_SCRIPT_NOT_FOUND' in text
    capability = text.split('if mode == MPRO_FULL_HISTORY_MODE:', 1)[1].split('if mode == SOFTRESTAURANT_FULL_HISTORY_MODE:', 1)[0]
    assert 'job.get("command")' not in capability
    assert 'job.get("path")' not in capability
    assert 'shell=True' not in capability
    assert 'CERTIFIED_OPERATIONAL' in capability


def test_mpro_script_is_canonical_idempotent_and_execute_gated():
    text = SCRIPT.read_text(encoding='utf-8')
    assert 'resolve_pos_runtime_context' in text
    assert 'get_external_sql_connection' in text
    assert 'Comanda_Corte' in text
    assert 'sync_cortes_z_context' in text
    assert "parser.add_argument('--execute', action='store_true')" in text
    assert "result.get('estatus') != 'COMPLETADO'" in text
