from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

PLAN_SCHEMA = 'edarsahub.bos-plan.v1'
VALID_RISK = ('R0', 'R1', 'R2', 'R3', 'R4')
VALID_DATA_CLASSIFICATIONS = frozenset({
    'PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'PII', 'FINANCIAL_PRIVATE', 'SECRET'
})


class PlanError(ValueError):
    pass


def _token(value: str, field: str) -> str:
    result = str(value or '').strip()
    if not result:
        raise PlanError(f'{field}_REQUIRED')
    return result


def _tokens(values: Iterable[str], field: str) -> tuple[str, ...]:
    result = tuple(_token(value, field) for value in values)
    if len(result) != len(set(result)):
        raise PlanError(f'{field}_DUPLICATED')
    return result


@dataclass(frozen=True)
class PlanStep:
    id: str
    domain: str
    procedure: str
    required_capabilities: tuple[str, ...] = ()
    required_scopes: tuple[str, ...] = ()
    risk: str = 'R0'
    data_classification: str = 'PUBLIC'
    executor: str = 'worker'
    depends_on: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, 'id', _token(self.id, 'STEP_ID'))
        object.__setattr__(self, 'domain', _token(self.domain, 'STEP_DOMAIN'))
        object.__setattr__(self, 'procedure', _token(self.procedure, 'STEP_PROCEDURE'))
        object.__setattr__(self, 'executor', _token(self.executor, 'STEP_EXECUTOR'))
        object.__setattr__(self, 'required_capabilities', _tokens(self.required_capabilities, 'STEP_CAPABILITY'))
        object.__setattr__(self, 'required_scopes', _tokens(self.required_scopes, 'STEP_SCOPE'))
        object.__setattr__(self, 'depends_on', _tokens(self.depends_on, 'STEP_DEPENDENCY'))
        if self.risk not in VALID_RISK:
            raise PlanError('STEP_RISK_INVALID')
        if self.data_classification not in VALID_DATA_CLASSIFICATIONS:
            raise PlanError('STEP_DATA_CLASSIFICATION_INVALID')
        if self.id in self.depends_on:
            raise PlanError('STEP_SELF_DEPENDENCY')


@dataclass(frozen=True)
class Plan:
    request_id: str
    steps: tuple[PlanStep, ...]
    schema: str = PLAN_SCHEMA

    def __post_init__(self) -> None:
        object.__setattr__(self, 'request_id', _token(self.request_id, 'REQUEST_ID'))
        object.__setattr__(self, 'steps', tuple(self.steps))
        if self.schema != PLAN_SCHEMA:
            raise PlanError('PLAN_SCHEMA_INVALID')
        if not self.steps:
            raise PlanError('PLAN_STEPS_REQUIRED')
        if not all(isinstance(step, PlanStep) for step in self.steps):
            raise PlanError('PLAN_STEP_INVALID')
        ids = tuple(step.id for step in self.steps)
        if len(ids) != len(set(ids)):
            raise PlanError('PLAN_STEP_DUPLICATED')
        known = set(ids)
        for step in self.steps:
            missing = set(step.depends_on) - known
            if missing:
                raise PlanError('PLAN_DEPENDENCY_NOT_FOUND')
        self._validate_acyclic()

    def _validate_acyclic(self) -> None:
        dependencies = {step.id: set(step.depends_on) for step in self.steps}
        ready = sorted(step_id for step_id, deps in dependencies.items() if not deps)
        visited: list[str] = []
        while ready:
            current = ready.pop(0)
            visited.append(current)
            for step_id in sorted(dependencies):
                if current in dependencies[step_id]:
                    dependencies[step_id].remove(current)
                    if not dependencies[step_id] and step_id not in visited and step_id not in ready:
                        ready.append(step_id)
                        ready.sort()
        if len(visited) != len(dependencies):
            raise PlanError('PLAN_CYCLE_DETECTED')

    def topological_steps(self) -> tuple[PlanStep, ...]:
        by_id = {step.id: step for step in self.steps}
        dependencies = {step.id: set(step.depends_on) for step in self.steps}
        ready = sorted(step_id for step_id, deps in dependencies.items() if not deps)
        ordered: list[PlanStep] = []
        while ready:
            current = ready.pop(0)
            ordered.append(by_id[current])
            for step_id in sorted(dependencies):
                if current in dependencies[step_id]:
                    dependencies[step_id].remove(current)
                    if not dependencies[step_id] and all(item.id != step_id for item in ordered) and step_id not in ready:
                        ready.append(step_id)
                        ready.sort()
        return tuple(ordered)


class Planner:
    def build(self, request_id: str, steps: Iterable[PlanStep]) -> Plan:
        return Plan(request_id=request_id, steps=tuple(steps))
