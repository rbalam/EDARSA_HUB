import json

from core.bos_evidence_collector import (
    build_direction_snapshot,
    collect_evidence,
    required_job_ids,
)


def certified_result(job_id):
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


def write_result(root, job_id, payload):
    (root / f'{job_id}.json').write_text(json.dumps(payload), encoding='utf-8')


def test_required_job_ids_are_the_seven_manifest_gates():
    ids = required_job_ids()
    assert len(ids) == 7
    assert len(set(ids)) == 7


def test_empty_directory_produces_zero_real_progress(tmp_path):
    snapshot = build_direction_snapshot(tmp_path)
    assert snapshot['percent_complete'] == 0.0
    assert snapshot['certified'] is False
    assert snapshot['certified_gate_count'] == 0
    assert snapshot['missing_or_uncertified_gate_count'] == 7


def test_all_formal_certified_results_produce_100_percent(tmp_path):
    for job_id in required_job_ids():
        write_result(tmp_path, job_id, certified_result(job_id))
    snapshot = build_direction_snapshot(tmp_path)
    assert snapshot['percent_complete'] == 100.0
    assert snapshot['certified'] is True
    assert snapshot['certified_gate_count'] == 7
    assert snapshot['missing_or_uncertified_gate_count'] == 0


def test_invalid_json_is_fail_closed_and_does_not_count(tmp_path):
    ids = required_job_ids()
    for job_id in ids[1:]:
        write_result(tmp_path, job_id, certified_result(job_id))
    (tmp_path / f'{ids[0]}.json').write_text('{invalid', encoding='utf-8')
    snapshot = build_direction_snapshot(tmp_path)
    assert snapshot['percent_complete'] == 85.71
    assert snapshot['certified'] is False


def test_mismatched_job_id_is_ignored(tmp_path):
    ids = required_job_ids()
    payload = certified_result('SOME-OTHER-JOB')
    write_result(tmp_path, ids[0], payload)
    evidence = collect_evidence(tmp_path)
    assert ids[0] not in evidence


def test_uncertified_result_is_read_but_does_not_count_as_progress(tmp_path):
    ids = required_job_ids()
    payload = certified_result(ids[0])
    payload['certification'] = 'NOT_CERTIFIED'
    write_result(tmp_path, ids[0], payload)
    snapshot = build_direction_snapshot(tmp_path)
    assert snapshot['percent_complete'] == 0.0
    assert snapshot['certified'] is False
    assert snapshot['certified_gate_count'] == 0


def test_snapshot_contract_is_serializable_and_identifies_read_only_mode(tmp_path):
    snapshot = build_direction_snapshot(tmp_path)
    encoded = json.dumps(snapshot)
    assert encoded
    assert snapshot['schema'] == 'edarsahub.bos-direction-status.v1'
    assert snapshot['scope'] == 'BOS_V1_0'
    assert snapshot['evidence_mode'] == 'READ_ONLY_TERMINAL_RESULTS'
