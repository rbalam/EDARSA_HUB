from __future__ import annotations

import json
import os
from pathlib import Path

from core.bos_direction_e2e_certification import certify_direction_e2e, stage_required_evidence
from core.bos_evidence_collector import required_job_ids


def certified_result(job_id: str) -> dict[str, object]:
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


def test_gate7_all_certified_fixture(tmp_path):
    results = tmp_path / 'results'
    results.mkdir()
    for job_id in required_job_ids():
        (results / f'{job_id}.json').write_text(json.dumps(certified_result(job_id)), encoding='utf-8')
    status = tmp_path / 'status'
    dossier = certify_direction_e2e(results, status, [
        '2026-09-09T01:20:01Z',
        '2026-09-09T01:20:02Z',
        '2026-09-09T01:20:03Z',
    ])
    assert dossier['status'] == 'CERTIFIED'
    assert dossier['cycle_count'] == 3
    assert dossier['required_gate_count'] == 7
    assert dossier['certified_gate_count'] == 7
    assert dossier['missing_or_uncertified_gate_count'] == 0
    assert dossier['percent_complete'] == 100.0
    assert dossier['program_certified'] is True


def test_gate7_missing_evidence_fails_closed(tmp_path):
    results = tmp_path / 'results'
    results.mkdir()
    status = tmp_path / 'status'
    dossier = certify_direction_e2e(results, status, [
        '2026-09-09T01:21:01Z',
        '2026-09-09T01:21:02Z',
        '2026-09-09T01:21:03Z',
    ])
    assert dossier['required_gate_count'] == 7
    assert dossier['certified_gate_count'] == 0
    assert dossier['missing_or_uncertified_gate_count'] == 7
    assert dossier['percent_complete'] == 0.0
    assert dossier['program_certified'] is False


def test_gate7_real_evidence_is_staged_then_runs_three_cycles(tmp_path):
    # Exact R3 fix: mirror the Worker's canonical ROOT resolution. The Worker
    # uses /app when EDARSAHUB_ROOT is not explicitly exported.
    runtime_root = Path(str(os.environ.get('EDARSAHUB_ROOT') or '/app'))
    canonical_results = runtime_root / '.git' / 'universal-worker-queue' / 'results'
    assert canonical_results.is_dir(), f'CANONICAL_WORKER_RESULTS_DIR_REQUIRED:{canonical_results}'
    staged_results = tmp_path / 'real-evidence'
    audit = stage_required_evidence(canonical_results, staged_results)
    assert audit['required_count'] == 7
    assert audit['present_count'] + audit['missing_count'] == 7
    status = tmp_path / 'status'
    dossier = certify_direction_e2e(staged_results, status, [
        '2026-09-09T01:22:01Z',
        '2026-09-09T01:22:02Z',
        '2026-09-09T01:22:03Z',
    ])
    assert dossier['cycle_count'] == 3
    assert dossier['required_gate_count'] == 7
    assert int(dossier['certified_gate_count']) + int(dossier['missing_or_uncertified_gate_count']) == 7
    assert Path(str(dossier['latest_file'])).is_file()
    assert all(Path(path).is_file() for path in dossier['history_files'])
    assert dossier['production_touched'] is False
