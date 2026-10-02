import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / 'tools' / 'mirror_sync' / 'universal_job_bridge.py'


def load_bridge():
    spec = importlib.util.spec_from_file_location('universal_job_bridge_rejected_retry', BRIDGE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def configure_state(module, tmp_path):
    module.PENDING = tmp_path / 'pending'
    module.PROCESSING = tmp_path / 'processing'
    module.REJECTED = tmp_path / 'rejected'
    module.REJECTED_HISTORY = tmp_path / 'rejected_history'
    module.DONE = tmp_path / 'done'
    module.RESULTS = tmp_path / 'results'
    module.ensure_dirs()


def base_job():
    return {
        'schema': 'edarsahub.worker-job.v2',
        'job_id': 'FIX-1',
        'target_repo': 'rbalam/EDARSA_HUB',
        'target_branch': 'Edarsahub_Desarrollo',
        'production_allowed': False,
        'objective': 'Cambio quirurgico',
        'actions': [{'type': 'replace_text', 'path': 'x.py', 'old': 'a', 'new': 'b', 'expected_count': 1}],
        'checks': [{'type': 'git_diff_check'}],
        'requester': {'email': 'ricardo@edarsa.com.mx', 'source': 'chatgpt-classic', 'project': 'EDARSAHUB BOS V1.0', 'chat': 'Worker 3'},
    }


def seed_rejection(module, job, name='FIX-1.json'):
    raw = json.dumps(job, sort_keys=True)
    rejection = {
        'schema': 'edarsahub.worker-rejection.v2',
        'job_id': 'FIX-1',
        'status': 'REJECTED',
        'reasons': ['SUMMARY_LANGUAGE_MUST_BE_ES'],
        'production_touched': False,
    }
    (module.REJECTED / name).write_text(json.dumps(rejection), encoding='utf-8')
    (module.REJECTED / f'{name}.raw').write_text(raw, encoding='utf-8')
    return raw


def test_unchanged_rejected_request_is_not_retried(tmp_path):
    module = load_bridge(); configure_state(module, tmp_path)
    job = base_job(); raw = seed_rejection(module, job)
    decision = module.rejected_correction_retry_decision('FIX-1.json', raw, job)
    assert decision['allowed'] is False
    assert decision['reason'] == 'REJECTED_REQUEST_UNCHANGED'


def test_only_summary_language_correction_is_allowed(tmp_path):
    module = load_bridge(); configure_state(module, tmp_path)
    previous = base_job(); seed_rejection(module, previous)
    corrected = dict(previous); corrected['human_summary_language'] = 'es'
    raw = json.dumps(corrected, sort_keys=True)
    decision = module.rejected_correction_retry_decision('FIX-1.json', raw, corrected)
    assert decision['allowed'] is True
    assert decision['corrected_fields'] == ['human_summary_language']
    assert module.validate(corrected) == []


def test_functional_scope_change_is_rejected(tmp_path):
    module = load_bridge(); configure_state(module, tmp_path)
    previous = base_job(); seed_rejection(module, previous)
    corrected = dict(previous); corrected['human_summary_language'] = 'es'; corrected['objective'] = 'Objetivo distinto'
    decision = module.rejected_correction_retry_decision('FIX-1.json', json.dumps(corrected, sort_keys=True), corrected)
    assert decision['allowed'] is False
    assert decision['reason'] == 'REJECTED_RETRY_SCOPE_CHANGED'
    assert 'objective' in decision['changed_fields']


def test_archive_preserves_rejection_and_raw(tmp_path):
    module = load_bridge(); configure_state(module, tmp_path)
    previous = base_job(); seed_rejection(module, previous)
    archived = module.archive_rejection_for_retry('FIX-1.json')
    assert not (module.REJECTED / 'FIX-1.json').exists()
    assert not (module.REJECTED / 'FIX-1.json.raw').exists()
    assert Path(archived['rejection']).is_file()
    assert Path(archived['raw']).is_file()


def test_second_correction_retry_is_blocked(tmp_path):
    module = load_bridge(); configure_state(module, tmp_path)
    previous = base_job(); seed_rejection(module, previous)
    (module.REJECTED_HISTORY / 'FIX-1.20260915T000000000000Z.json').write_text('{}', encoding='utf-8')
    corrected = dict(previous); corrected['human_summary_language'] = 'es'
    decision = module.rejected_correction_retry_decision('FIX-1.json', json.dumps(corrected, sort_keys=True), corrected)
    assert decision['allowed'] is False
    assert decision['reason'] == 'REJECTED_CORRECTION_RETRY_LIMIT_REACHED'


def test_rejected_does_not_count_as_normal_claim(tmp_path):
    module = load_bridge(); configure_state(module, tmp_path)
    previous = base_job(); seed_rejection(module, previous)
    assert module.already_claimed('FIX-1.json') is False
    (module.RESULTS / 'FIX-1.json').write_text('{}', encoding='utf-8')
    assert module.already_claimed('FIX-1.json') is True
