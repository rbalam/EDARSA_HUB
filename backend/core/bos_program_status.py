from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class MilestoneSpec:
    milestone_id: str
    evidence_job_ids: tuple[str, ...]
    weight: float = 1.0


@dataclass(frozen=True)
class FrontSpec:
    front_id: str
    milestones: tuple[MilestoneSpec, ...]


@dataclass(frozen=True)
class MilestoneStatus:
    milestone_id: str
    certified: bool
    matched_job_id: str | None
    reasons: tuple[str, ...]
    weight: float


@dataclass(frozen=True)
class FrontStatus:
    front_id: str
    percent_complete: float
    certified: bool
    milestones: tuple[MilestoneStatus, ...]


@dataclass(frozen=True)
class ProgramStatus:
    percent_complete: float
    certified: bool
    fronts: tuple[FrontStatus, ...]


def _is_certified_result(result: Mapping[str, object]) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if result.get('status') != 'INTEGRATED':
        reasons.append('STATUS_NOT_INTEGRATED')
    if result.get('certification') != 'CERTIFIED':
        reasons.append('CERTIFICATION_NOT_CERTIFIED')
    if result.get('work_completion') != 'COMPLETE':
        reasons.append('WORK_NOT_COMPLETE')
    if result.get('quality_gate') != 'PASS':
        reasons.append('QUALITY_GATE_NOT_PASS')
    if result.get('percent_complete') != 100:
        reasons.append('PERCENT_NOT_100')
    if result.get('production_touched') is not False:
        reasons.append('PRODUCTION_TOUCH_NOT_FALSE')
    blockers = result.get('blockers')
    if blockers not in (None, []):
        reasons.append('BLOCKERS_PRESENT')
    return (not reasons, tuple(reasons))


def evaluate_milestone(
    spec: MilestoneSpec,
    evidence_by_job_id: Mapping[str, Mapping[str, object]],
) -> MilestoneStatus:
    if spec.weight <= 0:
        raise ValueError('Milestone weight must be greater than zero')
    if not spec.evidence_job_ids:
        return MilestoneStatus(
            milestone_id=spec.milestone_id,
            certified=False,
            matched_job_id=None,
            reasons=('EVIDENCE_JOB_REQUIRED',),
            weight=spec.weight,
        )

    observed_reasons: list[str] = []
    for job_id in spec.evidence_job_ids:
        result = evidence_by_job_id.get(job_id)
        if result is None:
            observed_reasons.append(f'EVIDENCE_MISSING:{job_id}')
            continue
        certified, reasons = _is_certified_result(result)
        if certified:
            return MilestoneStatus(
                milestone_id=spec.milestone_id,
                certified=True,
                matched_job_id=job_id,
                reasons=(),
                weight=spec.weight,
            )
        observed_reasons.extend(f'{job_id}:{reason}' for reason in reasons)

    return MilestoneStatus(
        milestone_id=spec.milestone_id,
        certified=False,
        matched_job_id=None,
        reasons=tuple(observed_reasons),
        weight=spec.weight,
    )


def evaluate_front(
    spec: FrontSpec,
    evidence_by_job_id: Mapping[str, Mapping[str, object]],
) -> FrontStatus:
    if not spec.milestones:
        return FrontStatus(spec.front_id, 0.0, False, ())

    statuses = tuple(
        evaluate_milestone(milestone, evidence_by_job_id)
        for milestone in spec.milestones
    )
    total_weight = sum(status.weight for status in statuses)
    certified_weight = sum(status.weight for status in statuses if status.certified)
    percent = round((certified_weight / total_weight) * 100.0, 2)
    return FrontStatus(
        front_id=spec.front_id,
        percent_complete=percent,
        certified=all(status.certified for status in statuses),
        milestones=statuses,
    )


def evaluate_program(
    fronts: Sequence[FrontSpec],
    evidence_by_job_id: Mapping[str, Mapping[str, object]],
) -> ProgramStatus:
    if not fronts:
        return ProgramStatus(0.0, False, ())

    front_statuses = tuple(evaluate_front(front, evidence_by_job_id) for front in fronts)
    all_milestones = tuple(
        milestone
        for front in front_statuses
        for milestone in front.milestones
    )
    if not all_milestones:
        return ProgramStatus(0.0, False, front_statuses)

    total_weight = sum(milestone.weight for milestone in all_milestones)
    certified_weight = sum(
        milestone.weight for milestone in all_milestones if milestone.certified
    )
    percent = round((certified_weight / total_weight) * 100.0, 2)
    certified = all(front.certified for front in front_statuses)
    return ProgramStatus(percent, certified, front_statuses)
