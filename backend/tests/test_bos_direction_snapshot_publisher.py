import json
from pathlib import Path

from core.bos_direction_snapshot_publisher import (
    publish_direction_snapshot,
    render_direction_snapshot,
    serialize_direction_snapshot,
)
from core.bos_evidence_collector import required_job_ids


def certified_result(job_id: str):
    return {
        'job_id': job_id,
        'status': 'INTEGRATED',
        'certification': 'CERTIFIED',
        'work_completion': 'COMPLETE',
        'quality_gate': 'PASS',
        'percent_complete': 100,
        'production_touched': False,
        'blockers': [],
    }


def write_all_evidence(root: Path):
    for job_id in required_job_ids():
        (root / f'{job_id}.json').write_text(
            json.dumps(certified_result(job_id)),
            encoding='utf-8',
        )


def test_render_adds_explicit_generation_time_without_changing_certification(tmp_path):
    write_all_evidence(tmp_path)
    snapshot = render_direction_snapshot(tmp_path, '2026-09-07T03:58:00Z')
    assert snapshot['generated_at_utc'] == '2026-09-07T03:58:00Z'
    assert snapshot['percent_complete'] == 100.0
    assert snapshot['certified'] is True
    assert isinstance(snapshot['fronts'], list)
    assert isinstance(snapshot['fronts'][0]['milestones'], list)


def test_publish_writes_canonical_json_snapshot_and_returns_exact_same_shape(tmp_path):
    results = tmp_path / 'results'
    results.mkdir()
    write_all_evidence(results)
    output = tmp_path / 'status' / 'latest.json'
    returned = publish_direction_snapshot(results, output, '2026-09-07T03:58:00Z')
    stored = json.loads(output.read_text(encoding='utf-8'))
    assert stored == returned
    assert stored['schema'] == 'edarsahub.bos-direction-status.v1'
    assert stored['required_gate_count'] == 7
    assert stored['certified_gate_count'] == 7


def test_missing_evidence_is_published_fail_closed_not_as_100(tmp_path):
    output = tmp_path / 'latest.json'
    snapshot = publish_direction_snapshot(tmp_path, output, '2026-09-07T03:58:00Z')
    assert snapshot['percent_complete'] == 0.0
    assert snapshot['certified'] is False
    assert snapshot['missing_or_uncertified_gate_count'] == 7


def test_serialization_is_deterministic():
    first = serialize_direction_snapshot({'b': 2, 'a': 1})
    second = serialize_direction_snapshot({'a': 1, 'b': 2})
    assert first == second
    assert first.endswith('\n')
