from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / 'tools' / 'mirror_sync' / 'universal_job_bridge.py'
DISPATCHER = ROOT / 'tools' / 'mirror_sync' / 'universal_job_dispatcher.py'


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def base_job():
    return {
        'schema': 'edarsahub.worker-job.v2',
        'job_id': 'READONLY-CONTRACT-TEST-001',
        'target_repo': 'rbalam/EDARSA_HUB',
        'target_branch': 'Edarsahub_Desarrollo',
        'production_allowed': False,
        'objective': 'generic readonly contract test',
        'human_summary_language': 'es',
        'mode': 'READ_ONLY',
        'actions': [],
        'checks': [
            {'type': 'git_diff_check'},
            {'type': 'py_compile', 'paths': ['tools/mirror_sync/universal_job_bridge.py']},
            {'type': 'pytest', 'paths': ['backend/tests/test_worker_generic_readonly.py']},
        ],
    }


def test_bridge_accepts_generic_readonly_with_empty_actions_and_safe_checks():
    bridge = load_module(BRIDGE, 'generic_readonly_bridge_ok')
    assert bridge.validate(base_job()) == []


def test_bridge_requires_actions_to_be_exact_empty_list():
    bridge = load_module(BRIDGE, 'generic_readonly_bridge_actions')
    missing = base_job()
    missing.pop('actions')
    assert 'READ_ONLY_ACTIONS_MUST_BE_EMPTY_LIST' in bridge.validate(missing)
    mutated = base_job()
    mutated['actions'] = [{'type': 'write_file', 'path': 'x.txt', 'content': 'x'}]
    assert 'READ_ONLY_ACTIONS_MUST_BE_EMPTY_LIST' in bridge.validate(mutated)


def test_bridge_rejects_mutating_readonly_checks_and_production():
    bridge = load_module(BRIDGE, 'generic_readonly_bridge_checks')
    job = base_job()
    job['checks'] = [{'type': 'frontend_build', 'directory': 'frontend'}]
    assert 'READ_ONLY_ONLY_NON_MUTATING_CHECKS_ALLOWED' in bridge.validate(job)
    prod = base_job()
    prod['production_allowed'] = True
    assert 'PRODUCTION_MUST_BE_FALSE' in bridge.validate(prod)


def test_bridge_accepts_combined_repository_and_sql_readonly_checks():
    bridge = load_module(BRIDGE, 'generic_readonly_bridge_combined')
    job = base_job()
    job['checks'] = [
        {
            'type': 'repository_contract_audit',
            'request': {
                'paths': ['backend', 'tools/mirror_sync'],
                'search_terms': ['worker', 'sql'],
                'max_results': 10,
            },
        },
        {
            'type': 'sql_readonly_audit',
            'queries': [{'name': 'identity', 'sql': 'SELECT DB_NAME() AS db_name'}],
        },
    ]
    assert bridge.validate(job) == []


def load_dispatcher():
    mirror_sync = ROOT / 'tools' / 'mirror_sync'
    sys.path.insert(0, str(mirror_sync))
    try:
        return load_module(DISPATCHER, 'generic_readonly_dispatcher')
    finally:
        sys.path.remove(str(mirror_sync))


def test_readonly_py_compile_redirects_bytecode(monkeypatch):
    dispatcher = load_dispatcher()
    captured = {}

    class Completed:
        returncode = 0
        stdout = ''

    def fake_run(args, cwd=None, check=False, timeout=None, env_extra=None):
        captured['args'] = args
        captured['env_extra'] = env_extra or {}
        return Completed()

    monkeypatch.setattr(dispatcher, 'run', fake_run)
    result = dispatcher.run_check(ROOT, {'type': 'py_compile', 'paths': ['tools/mirror_sync/universal_job_bridge.py']}, readonly=True)
    assert result['status'] == 'PASS'
    assert 'PYTHONPYCACHEPREFIX' in captured['env_extra']
    assert str(captured['env_extra']['PYTHONPYCACHEPREFIX']).startswith('/tmp/')


def test_readonly_pytest_disables_repo_cache_and_bytecode(monkeypatch):
    dispatcher = load_dispatcher()
    captured = {}

    class Completed:
        returncode = 0
        stdout = ''

    def fake_run(args, cwd=None, check=False, timeout=None, env_extra=None):
        captured['args'] = args
        captured['env_extra'] = env_extra or {}
        return Completed()

    monkeypatch.setattr(dispatcher, 'run', fake_run)
    result = dispatcher.run_check(ROOT, {'type': 'pytest', 'paths': ['backend/tests/test_worker_generic_readonly.py']}, readonly=True)
    assert result['status'] == 'PASS'
    assert ['-p', 'no:cacheprovider'] == captured['args'][captured['args'].index('-p'):captured['args'].index('-p') + 2]
    assert captured['env_extra']['PYTHONDONTWRITEBYTECODE'] == '1'


def test_dispatcher_has_dedicated_readonly_terminal_and_no_shell_execution():
    text = DISPATCHER.read_text(encoding='utf-8')
    assert 'READ_ONLY_COMPLETE' in text
    assert 'CERTIFIED_READ_ONLY' in text
    assert 'READ_ONLY_ACTIONS_MUST_BE_EMPTY_LIST' in text
    assert 'READ_ONLY_ONLY_NON_MUTATING_CHECKS_ALLOWED' in text
    assert 'readonly_tracked_repo_mutation_detected' in text
    assert 'shell=True' not in text
