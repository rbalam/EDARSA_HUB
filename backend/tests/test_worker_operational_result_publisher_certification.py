import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLISHER_PATH = ROOT / 'tools' / 'mirror_sync' / 'universal_job_result_publisher.py'


def load_publisher():
    spec = importlib.util.spec_from_file_location('worker_result_publisher_under_test', PUBLISHER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def operational_result(**overrides):
    result = {
        'status': 'OPERATIONAL_COMPLETE',
        'certification': 'CERTIFIED_OPERATIONAL',
        'tests': 'PASS',
        'quality_gate': 'PASS',
        'blockers': [],
        'production_touched': False,
        'percent_complete': 100,
    }
    result.update(overrides)
    return result


def test_operational_complete_is_certified_without_sha_attestation():
    publisher = load_publisher()
    evidence = publisher.certification_evidence(operational_result())
    assert evidence['certification'] == 'CERTIFIED_OPERATIONAL'
    assert evidence['work_completion'] == 'COMPLETE'
    assert evidence['percent_complete'] == 100
    assert evidence['certification_basis'] == 'DISPATCHER_OPERATIONAL_CERTIFICATION_PLUS_VALIDATIONS'


def test_operational_certification_requires_all_guards():
    publisher = load_publisher()
    cases = [
        {'certification': 'NOT_CERTIFIED'},
        {'tests': 'FAIL'},
        {'quality_gate': 'FAIL'},
        {'blockers': ['x']},
        {'production_touched': True},
    ]
    for overrides in cases:
        evidence = publisher.certification_evidence(operational_result(**overrides))
        assert evidence['certification'] == 'NOT_CERTIFIED'
        assert evidence['percent_complete'] <= 95


def test_marker_allows_operational_repromotion(tmp_path):
    publisher = load_publisher()
    marker = tmp_path / 'result.marker'
    marker.write_text('certification=NOT_CERTIFIED\n', encoding='utf-8')
    assert publisher.marker_satisfied(marker, {'certification': 'CERTIFIED_OPERATIONAL'}) is False
    marker.write_text('certification=CERTIFIED_OPERATIONAL\n', encoding='utf-8')
    assert publisher.marker_satisfied(marker, {'certification': 'CERTIFIED_OPERATIONAL'}) is True
