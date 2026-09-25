from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Iterable

from core.bos_direction_status_cycle import run_direction_status_cycle
from core.bos_evidence_collector import required_job_ids


def stage_required_evidence(source_results_dir: str | Path, staging_results_dir: str | Path) -> dict[str, object]:
    source = Path(source_results_dir)
    staging = Path(staging_results_dir)
    staging.mkdir(parents=True, exist_ok=True)
    required = required_job_ids()
    present: list[str] = []
    missing: list[str] = []
    for job_id in required:
        src = source / f'{job_id}.json'
        dst = staging / f'{job_id}.json'
        if src.is_file():
            shutil.copyfile(src, dst)
            present.append(job_id)
        else:
            missing.append(job_id)
    return {
        'required_job_ids': list(required),
        'present_job_ids': present,
        'missing_job_ids': missing,
        'required_count': len(required),
        'present_count': len(present),
        'missing_count': len(missing),
    }


def certify_direction_e2e(
    results_dir: str | Path,
    status_root: str | Path,
    generated_at_utc_values: Iterable[str],
) -> dict[str, object]:
    timestamps = list(generated_at_utc_values)
    if len(timestamps) < 3:
        raise ValueError('GATE7_REQUIRES_AT_LEAST_3_CYCLES')
    snapshots: list[dict[str, object]] = []
    history_files: list[str] = []
    for timestamp in timestamps:
        result = run_direction_status_cycle(results_dir, status_root, timestamp)
        snapshot = result['snapshot']
        if not isinstance(snapshot, dict):
            raise RuntimeError('INVALID_SNAPSHOT_TYPE')
        if snapshot.get('schema') != 'edarsahub.bos-direction-status.v1':
            raise RuntimeError('INVALID_SNAPSHOT_SCHEMA')
        if snapshot.get('required_gate_count') != 7:
            raise RuntimeError('INVALID_REQUIRED_GATE_COUNT')
        certified = int(snapshot.get('certified_gate_count') or 0)
        missing = int(snapshot.get('missing_or_uncertified_gate_count') or 0)
        if certified + missing != 7:
            raise RuntimeError('INVALID_GATE_ACCOUNTING')
        snapshots.append(snapshot)
        history_files.append(str(result['history_file']))
    latest_path = Path(status_root) / 'latest.json'
    latest = json.loads(latest_path.read_text(encoding='utf-8'))
    if latest != snapshots[-1]:
        raise RuntimeError('LATEST_DOES_NOT_MATCH_LAST_CYCLE')
    if not all(Path(path).is_file() for path in history_files):
        raise RuntimeError('HISTORY_FILE_MISSING')
    final = snapshots[-1]
    return {
        'schema': 'edarsahub.bos-direction-e2e-certification.v1',
        'status': 'CERTIFIED',
        'cycle_count': len(snapshots),
        'required_gate_count': final['required_gate_count'],
        'certified_gate_count': final['certified_gate_count'],
        'missing_or_uncertified_gate_count': final['missing_or_uncertified_gate_count'],
        'percent_complete': final['percent_complete'],
        'program_certified': final['certified'],
        'latest_file': str(latest_path),
        'history_files': history_files,
        'final_snapshot': final,
        'production_touched': False,
    }
