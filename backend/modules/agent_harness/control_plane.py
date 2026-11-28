from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

CONTROL_PLANE_SCHEMA = 'edarsahub.bos-control-plane-snapshot.v1'
GATE_TERMINAL = frozenset({'CERTIFIED', 'CERTIFIED_READ_ONLY', 'BLOCKED', 'FAILED', 'REJECTED'})


class ControlPlaneError(ValueError):
    pass


def _required(value: object, field: str) -> str:
    token = str(value or '').strip()
    if not token:
        raise ControlPlaneError(f'{field}_REQUIRED')
    return token


@dataclass(frozen=True)
class GateState:
    gate_id: str
    status: str
    percent_complete: int
    blockers: tuple[str, ...] = ()
    production_touched: bool = False

    def __post_init__(self) -> None:
        _required(self.gate_id, 'GATE_ID')
        if self.status not in GATE_TERMINAL:
            raise ControlPlaneError('GATE_STATUS_NOT_TERMINAL')
        if not 0 <= self.percent_complete <= 100:
            raise ControlPlaneError('GATE_PERCENT_INVALID')
        if self.production_touched:
            raise ControlPlaneError('PRODUCTION_TOUCHED_FORBIDDEN')
        if self.status in {'CERTIFIED', 'CERTIFIED_READ_ONLY'} and self.percent_complete != 100:
            raise ControlPlaneError('CERTIFIED_GATE_NOT_COMPLETE')
        if self.status in {'CERTIFIED', 'CERTIFIED_READ_ONLY'} and self.blockers:
            raise ControlPlaneError('CERTIFIED_GATE_HAS_BLOCKERS')


@dataclass(frozen=True)
class BudgetEnvelope:
    budget_name: str
    limit: float
    consumed: float

    def __post_init__(self) -> None:
        _required(self.budget_name, 'BUDGET_NAME')
        if self.limit < 0 or self.consumed < 0:
            raise ControlPlaneError('BUDGET_NEGATIVE')
        if self.consumed > self.limit:
            raise ControlPlaneError('BUDGET_EXCEEDED')

    @property
    def remaining(self) -> float:
        return self.limit - self.consumed


@dataclass(frozen=True)
class EvidenceSummary:
    request_id: str
    worker_job_id: str
    certified_success: bool
    production_touched: bool

    def __post_init__(self) -> None:
        _required(self.request_id, 'REQUEST_ID')
        _required(self.worker_job_id, 'WORKER_JOB_ID')
        if self.production_touched:
            raise ControlPlaneError('EVIDENCE_PRODUCTION_TOUCHED')


@dataclass(frozen=True)
class ControlPlaneSnapshot:
    gates: tuple[GateState, ...]
    budgets: tuple[BudgetEnvelope, ...]
    evidence: tuple[EvidenceSummary, ...]
    schema: str = CONTROL_PLANE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != CONTROL_PLANE_SCHEMA:
            raise ControlPlaneError('CONTROL_PLANE_SCHEMA_INVALID')
        gate_ids = [gate.gate_id for gate in self.gates]
        if len(gate_ids) != len(set(gate_ids)):
            raise ControlPlaneError('DUPLICATE_GATE_ID')
        budget_names = [budget.budget_name for budget in self.budgets]
        if len(budget_names) != len(set(budget_names)):
            raise ControlPlaneError('DUPLICATE_BUDGET_NAME')

    @property
    def certified_gates(self) -> tuple[str, ...]:
        return tuple(sorted(g.gate_id for g in self.gates if g.status in {'CERTIFIED', 'CERTIFIED_READ_ONLY'}))

    @property
    def blockers(self) -> tuple[str, ...]:
        return tuple(sorted({blocker for gate in self.gates for blocker in gate.blockers}))

    @property
    def healthy(self) -> bool:
        return not self.blockers and all(not item.production_touched for item in self.evidence)


class ControlPlane:
    def snapshot(
        self,
        *,
        gates: Iterable[GateState],
        budgets: Iterable[BudgetEnvelope] = (),
        evidence: Iterable[EvidenceSummary] = (),
    ) -> ControlPlaneSnapshot:
        gate_items = tuple(sorted(tuple(gates), key=lambda item: item.gate_id))
        budget_items = tuple(sorted(tuple(budgets), key=lambda item: item.budget_name))
        evidence_items = tuple(sorted(tuple(evidence), key=lambda item: (item.request_id, item.worker_job_id)))
        if not all(isinstance(item, GateState) for item in gate_items):
            raise ControlPlaneError('GATE_STATE_TYPE_INVALID')
        if not all(isinstance(item, BudgetEnvelope) for item in budget_items):
            raise ControlPlaneError('BUDGET_TYPE_INVALID')
        if not all(isinstance(item, EvidenceSummary) for item in evidence_items):
            raise ControlPlaneError('EVIDENCE_TYPE_INVALID')
        return ControlPlaneSnapshot(gates=gate_items, budgets=budget_items, evidence=evidence_items)
