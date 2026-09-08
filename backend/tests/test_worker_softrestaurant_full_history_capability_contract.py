from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / 'tools' / 'mirror_sync' / 'universal_job_bridge.py'
DISPATCHER = ROOT / 'tools' / 'mirror_sync' / 'universal_job_dispatcher.py'


def test_bridge_has_closed_softrestaurant_resync_mode():
    text = BRIDGE.read_text(encoding='utf-8')
    assert 'SOFTRESTAURANT_FULL_HISTORY_RESYNC' in text
    assert 'SOFTRESTAURANT_RESYNC_ACTIONS_FORBIDDEN' in text
    assert 'SOFTRESTAURANT_RESYNC_CONFIRMATION_REQUIRED' in text
    assert 'SOFTRESTAURANT_RESYNC_ONLY_SQL_AUDIT_ALLOWED' in text


def test_dispatcher_uses_only_fixed_resync_script():
    text = DISPATCHER.read_text(encoding='utf-8')
    assert 'backend' in text and 'resync_softrestaurant_full_history.py' in text
    assert 'SOFTRESTAURANT_RESYNC_SCRIPT_NOT_FOUND' in text
    assert 'cmd = [PYTHON_BIN, str(script)]' in text
    assert 'cmd.append("--execute")' in text
    assert 'cmd.extend(["--unit", unit.strip().upper()])' in text


def test_resync_mode_has_no_arbitrary_shell_or_path_contract():
    text = DISPATCHER.read_text(encoding='utf-8')
    capability = text.split('if mode == SOFTRESTAURANT_FULL_HISTORY_MODE:', 1)[1].split('worktree, branch = prepare_worktree(', 1)[0]
    assert 'job.get("command")' not in capability
    assert 'job.get("path")' not in capability
    assert 'shell=True' not in capability
    assert 'SOFTRESTAURANT_RESYNC_MAX_SECONDS' in capability


def test_resync_requires_readonly_audit_and_records_mutation_semantics():
    text = DISPATCHER.read_text(encoding='utf-8')
    assert 'SOFTRESTAURANT_RESYNC_SQL_AUDIT_REQUIRED' in text
    assert 'canonical_sql_mutation' in text
    assert 'CERTIFIED_OPERATIONAL' in text
    assert 'OPERATIONAL_COMPLETE' in text
