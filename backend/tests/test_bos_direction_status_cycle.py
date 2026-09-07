import json
from pathlib import Path

import pytest

from core.bos_direction_status_cycle import run_direction_status_cycle
from core.bos_evidence_collector import required_job_ids


def certified_result(job_id: str):
    return {'job_id': job_id, 'status': 'INTEGRATED', 'certification': 'CERTIFIED', 'work_completion': 'COMPLETE', 'quality_gate': 'PASS', 'percent_complete': 100, 'production_touched': False, 'blockers': []}


def write_all_evidence(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    for job_id in required_job_ids():
        (root / f'{job_id}.json').write_text(json.dumps(certified_result(job_id)), encoding='utf-8')


def test_cycle_writes_history_and_latest(tmp_path):
    results = tmp_path / 'results'
    status = tmp_path / 'status'
    write_all_evidence(results)
    result = run_direction_status_cycle(results, status, '2026-09-07T04:09:00Z')
    history = Path(result['history_file'])
    latest = Path(result['latest_file'])
    assert history.exists()
    assert latest.exists()
    assert json.loads(history.read_text(encoding='utf-8')) == result['snapshot']
    assert json.loads(latest.read_text(encoding='utf-8')) == result['snapshot']


def test_retry_same_timestamp_is_idempotent(tmp_path):
    results = tmp_path / 'results'
    status = tmp_path / 'status'
    write_all_evidence(results)
    first = run_direction_status_cycle(results, status, '2026-09-07T04:09:00Z')
    second = run_direction_status_cycle(results, status, '2026-09-07T04:09:00Z')
    assert first['snapshot'] == second['snapshot']
    assert len(list((status / 'history').glob('*.json'))) == 1


def test_history_is_append_only_and_latest_moves_forward(tmp_path):
    results = tmp_path / 'results'
    status = tmp_path / 'status'
    write_all_evidence(results)
    run_direction_status_cycle(results, status, '2026-09-07T04:09:00Z')
    run_direction_status_cycle(results, status, '2026-09-07T05:09:00Z')
    assert len(list((status / 'history').glob('*.json'))) == 2
    latest = json.loads((status / 'latest.json').read_text(encoding='utf-8'))
    assert latest['generated_at_utc'] == '2026-09-07T05:09:00Z'


def test_collision_with_different_payload_fails_closed(tmp_path):
    results = tmp_path / 'results'
    status = tmp_path / 'status'
    write_all_evidence(results)
    run_direction_status_cycle(results, status, '2026-09-07T04:09:00Z')
    history = next((status / 'history').glob('*.json'))
    history.write_text('{"tampered": true}\n', encoding='utf-8')
    with pytest.raises(RuntimeError, match='HISTORY_COLLISION'):
        run_direction_status_cycle(results, status, '2026-09-07T04:09:00Z')


def test_invalid_timestamp_fails_closed(tmp_path):
    with pytest.raises(ValueError):
        run_direction_status_cycle(tmp_path, tmp_path / 'status', '2026/09/07 04:09')
