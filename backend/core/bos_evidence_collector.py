from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Mapping

from core.bos_program_manifest import BOS_V1_FRONTS
from core.bos_program_status import ProgramStatus, evaluate_program


def required_job_ids() -> tuple[str, ...]:
    return tuple(
        job_id
        for front in BOS_V1_FRONTS
        for milestone in front.milestones
        for job_id in milestone.evidence_job_ids
    )


def _load_result_file(path: Path, expected_job_id: str) -> Mapping[str, object] | None:
    try:
        raw = path.read_text(encoding='utf-8')
        payload = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None
    if payload.get('job_id') != expected_job_id:
        return None
    return payload


def collect_evidence(results_dir: str | Path) -> dict[str, Mapping[str, object]]:
    root = Path(results_dir)
    evidence: dict[str, Mapping[str, object]] = {}
    for job_id in required_job_ids():
        result = _load_result_file(root / f'{job_id}.json', job_id)
        if result is not None:
            evidence[job_id] = result
    return evidence


def build_program_status(results_dir: str | Path) -> ProgramStatus:
    return evaluate_program(BOS_V1_FRONTS, collect_evidence(results_dir))


def build_direction_snapshot(results_dir: str | Path) -> dict[str, object]:
    status = build_program_status(results_dir)
    snapshot = asdict(status)
    snapshot['schema'] = 'edarsahub.bos-direction-status.v1'
    snapshot['scope'] = 'BOS_V1_0'
    snapshot['evidence_mode'] = 'READ_ONLY_TERMINAL_RESULTS'
    snapshot['required_gate_count'] = 7
    snapshot['certified_gate_count'] = sum(
        1
        for front in status.fronts
        for milestone in front.milestones
        if milestone.certified
    )
    snapshot['missing_or_uncertified_gate_count'] = (
        snapshot['required_gate_count'] - snapshot['certified_gate_count']
    )
    return snapshot
