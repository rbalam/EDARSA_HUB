import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PUBLISHER = ROOT / 'tools' / 'mirror_sync' / 'universal_job_result_publisher.py'


def _publisher_module():
    spec = importlib.util.spec_from_file_location('universal_job_result_publisher', PUBLISHER)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_frontend_build_certified_result_publishes_certified_frontend_build():
    publisher = _publisher_module()
    result = {
        'status': 'FRONTEND_BUILD_CERTIFIED',
        'certification': 'CERTIFIED_FRONTEND_BUILD',
        'tests': 'PASS',
        'quality_gate': 'PASS',
        'blockers': [],
        'production_touched': False,
        'files_changed': [],
        'percent_complete': 100,
    }

    evidence = publisher.certification_evidence(result)

    assert evidence['certified'] is True
    assert evidence['certification'] == 'CERTIFIED_FRONTEND_BUILD'
    assert evidence['work_completion'] == 'COMPLETE'
    assert evidence['percent_complete'] == 100
    assert evidence['certification_basis'] == 'FRONTEND_BUILD_CERTIFICATION_PASS_PLUS_NON_MUTATING_RESULT'


def test_frontend_build_certified_result_requires_no_file_changes():
    publisher = _publisher_module()
    result = {
        'status': 'FRONTEND_BUILD_CERTIFIED',
        'certification': 'CERTIFIED_FRONTEND_BUILD',
        'tests': 'PASS',
        'quality_gate': 'PASS',
        'blockers': [],
        'production_touched': False,
        'files_changed': ['frontend/src/App.js'],
        'percent_complete': 100,
    }

    evidence = publisher.certification_evidence(result)

    assert evidence['certification'] == 'NOT_CERTIFIED'
    assert evidence['work_completion'] == 'NOT_CERTIFIED'
    assert evidence['percent_complete'] <= 95
