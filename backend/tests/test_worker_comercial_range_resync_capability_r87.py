from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / 'tools' / 'mirror_sync' / 'universal_job_bridge.py'
DISPATCHER = ROOT / 'tools' / 'mirror_sync' / 'universal_job_dispatcher.py'
SCRIPT = ROOT / 'backend' / 'scripts' / 'resync_comercial_range_worker.py'


def test_bridge_requires_closed_contract_and_confirmation():
    text = BRIDGE.read_text(encoding='utf-8')
    assert 'COMERCIAL_RANGE_RESYNC_MODE = "COMERCIAL_RANGE_RESYNC"' in text
    assert 'COMERCIAL_RANGE_RESYNC_EXACTLY_ONE_UNIT_REQUIRED' in text
    assert 'COMERCIAL_RANGE_RESYNC_CONFIRMATION_REQUIRED' in text
    assert 'COMERCIAL_RANGE_RESYNC_ONLY_SQL_AUDIT_ALLOWED' in text


def test_dispatcher_uses_fixed_script_and_not_job_shell():
    text = DISPATCHER.read_text(encoding='utf-8')
    block = text.split('if mode == COMERCIAL_RANGE_RESYNC_MODE:', 1)[1].split('if mode == ISCAM_DETAIL_BACKFILL_MODE:', 1)[0]
    assert 'resync_comercial_range_worker.py' in block
    assert 'confirm_comercial_range_resync' in block
    assert 'job.get("command")' not in block
    assert 'job.get("shell")' not in block
    assert 'job.get("path")' not in block
    assert 'shell=True' not in block


def test_script_reuses_official_scheduler_handlers():
    text = SCRIPT.read_text(encoding='utf-8')
    assert '_ejecutar_sync_real' in text
    assert '_ejecutar_dry_run' in text
    assert '_get_unidad_config' in text
    assert 'days > 31' in text


def test_script_accepts_both_supported_pos_engines():
    text = SCRIPT.read_text(encoding='utf-8')
    assert '{"SOFTRESTAURANT", "MPRO"}' in text
    assert 'SYSTEM_NOT_SUPPORTED' in text
    assert 'SYSTEM_NOT_SOFTRESTAURANT' not in text
