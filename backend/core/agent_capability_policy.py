from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, Enum
from typing import FrozenSet, Mapping


class RiskLevel(IntEnum):
    R0 = 0
    R1 = 1
    R2 = 2
    R3 = 3
    R4 = 4


class DataClassification(str, Enum):
    PUBLIC = 'PUBLIC'
    INTERNAL = 'INTERNAL'
    CONFIDENTIAL = 'CONFIDENTIAL'
    PII = 'PII'
    FINANCIAL_PRIVATE = 'FINANCIAL_PRIVATE'
    SECRET = 'SECRET'


@dataclass(frozen=True)
class BudgetRequest:
    runtime_seconds: int = 0
    files_changed: int = 0
    lines_changed: int = 0
    external_calls: int = 0
    sql_rows: int = 0
    inference_cost_usd: float = 0.0


@dataclass(frozen=True)
class PolicyRequest:
    capabilities: FrozenSet[str]
    scopes: FrozenSet[str]
    risk: RiskLevel
    data_classification: DataClassification
    budgets: BudgetRequest = field(default_factory=BudgetRequest)
    external_egress: bool = False
    production_allowed: bool = False
    privilege_expansion: bool = False
    approval_granted: bool = False
    procedure: str | None = None


@dataclass(frozen=True)
class PolicyContext:
    user_allowed_capabilities: FrozenSet[str]
    agent_allowed_capabilities: FrozenSet[str]
    environment_allowed_capabilities: FrozenSet[str]
    policy_allowed_capabilities: FrozenSet[str]
    user_allowed_scopes: FrozenSet[str]
    agent_allowed_scopes: FrozenSet[str]
    environment_allowed_scopes: FrozenSet[str]
    policy_allowed_scopes: FrozenSet[str]
    budget_limits: Mapping[str, float]


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reasons: tuple[str, ...]
    effective_capabilities: FrozenSet[str]
    effective_scopes: FrozenSet[str]


def _intersection(*sets: FrozenSet[str]) -> FrozenSet[str]:
    if not sets:
        return frozenset()
    result = sets[0]
    for value in sets[1:]:
        result = result.intersection(value)
    return frozenset(result)


def _budget_reasons(request: BudgetRequest, limits: Mapping[str, float]) -> list[str]:
    values = {
        'runtime_seconds': request.runtime_seconds,
        'files_changed': request.files_changed,
        'lines_changed': request.lines_changed,
        'external_calls': request.external_calls,
        'sql_rows': request.sql_rows,
        'inference_cost_usd': request.inference_cost_usd,
    }
    reasons: list[str] = []
    for key, value in values.items():
        limit = limits.get(key)
        if limit is None:
            reasons.append(f'BUDGET_LIMIT_MISSING:{key}')
        elif value < 0:
            reasons.append(f'BUDGET_REQUEST_INVALID:{key}')
        elif value > limit:
            reasons.append(f'BUDGET_EXCEEDED:{key}')
    return reasons


def evaluate_policy(request: PolicyRequest, context: PolicyContext) -> PolicyDecision:
    effective_capabilities = _intersection(
        request.capabilities,
        context.user_allowed_capabilities,
        context.agent_allowed_capabilities,
        context.environment_allowed_capabilities,
        context.policy_allowed_capabilities,
    )
    effective_scopes = _intersection(
        request.scopes,
        context.user_allowed_scopes,
        context.agent_allowed_scopes,
        context.environment_allowed_scopes,
        context.policy_allowed_scopes,
    )

    reasons: list[str] = []

    if not request.capabilities:
        reasons.append('CAPABILITY_REQUIRED')
    elif effective_capabilities != request.capabilities:
        reasons.append('CAPABILITY_NOT_EFFECTIVE')

    if not request.scopes:
        reasons.append('SCOPE_REQUIRED')
    elif effective_scopes != request.scopes:
        reasons.append('SCOPE_NOT_EFFECTIVE')

    if request.production_allowed:
        reasons.append('PRODUCTION_FORBIDDEN')

    if request.privilege_expansion:
        reasons.append('PRIVILEGE_EXPANSION_FORBIDDEN')

    if request.risk == RiskLevel.R4 and not request.approval_granted:
        reasons.append('R4_APPROVAL_REQUIRED')

    if request.external_egress and request.data_classification != DataClassification.PUBLIC:
        reasons.append('EGRESS_DATA_CLASSIFICATION_FORBIDDEN')

    reasons.extend(_budget_reasons(request.budgets, context.budget_limits))

    return PolicyDecision(
        allowed=not reasons,
        reasons=tuple(reasons),
        effective_capabilities=effective_capabilities,
        effective_scopes=effective_scopes,
    )
