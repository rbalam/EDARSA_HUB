from __future__ import annotations

import re
from dataclasses import dataclass

from core.agent_capability_policy import (
    DataClassification,
    PolicyContext,
    PolicyDecision,
    PolicyRequest,
    RiskLevel,
)
from core.agent_procedure_policy import ProcedureSpec, evaluate_procedure


AGENT_REACH_PROCEDURE = ProcedureSpec(
    name='agent-reach-external-research',
    required_capabilities=frozenset({'EXTERNAL_RESEARCH'}),
    max_risk=RiskLevel.R1,
    external_egress_allowed=True,
)

_BLOCKED_PATTERNS = (
    re.compile(r'(?i)password\s*[:=]'),
    re.compile(r'(?i)secret\s*[:=]'),
    re.compile(r'(?i)token\s*[:=]'),
    re.compile(r'(?i)api[_ -]?key\s*[:=]'),
    re.compile(r'(?i)bearer\s+[A-Za-z0-9._-]+'),
    re.compile(r'(?i)mongodb(?:\+srv)?://'),
    re.compile(r'(?i)(?:server|host)\s*=.*(?:sql|database)'),
    re.compile(r'(?i)\b(?:insert|update|delete|drop|alter|truncate|merge|create)\b\s+'),
)


@dataclass(frozen=True)
class AgentReachPreparedRequest:
    query: str
    max_external_calls: int
    effective_scopes: frozenset[str]
    procedure: str


@dataclass(frozen=True)
class AgentReachDecision:
    allowed: bool
    reasons: tuple[str, ...]
    policy: PolicyDecision
    prepared: AgentReachPreparedRequest | None


def sanitize_external_query(value: str) -> tuple[str | None, tuple[str, ...]]:
    query = ' '.join(str(value or '').split()).strip()
    reasons: list[str] = []
    if not query:
        reasons.append('AGENT_REACH_QUERY_REQUIRED')
    if len(query) > 2000:
        reasons.append('AGENT_REACH_QUERY_TOO_LONG')
    if any(pattern.search(query) for pattern in _BLOCKED_PATTERNS):
        reasons.append('AGENT_REACH_SENSITIVE_OR_DATA_ACCESS_PATTERN')
    return (query if not reasons else None, tuple(reasons))


def authorize_agent_reach(
    query: str,
    request: PolicyRequest,
    context: PolicyContext,
) -> AgentReachDecision:
    reasons: list[str] = []
    if request.data_classification != DataClassification.PUBLIC:
        reasons.append('AGENT_REACH_PUBLIC_DATA_ONLY')
    if not request.external_egress:
        reasons.append('AGENT_REACH_EGRESS_REQUIRED')
    if request.risk > RiskLevel.R1:
        reasons.append('AGENT_REACH_RISK_EXCEEDED')
    if request.budgets.external_calls <= 0:
        reasons.append('AGENT_REACH_EXTERNAL_CALL_BUDGET_REQUIRED')

    policy = evaluate_procedure(AGENT_REACH_PROCEDURE, request, context)
    reasons.extend(policy.reasons)
    sanitized, sanitize_reasons = sanitize_external_query(query)
    reasons.extend(sanitize_reasons)
    unique_reasons = tuple(dict.fromkeys(reasons))

    if unique_reasons or sanitized is None:
        return AgentReachDecision(False, unique_reasons, policy, None)

    prepared = AgentReachPreparedRequest(
        query=sanitized,
        max_external_calls=request.budgets.external_calls,
        effective_scopes=policy.effective_scopes,
        procedure=AGENT_REACH_PROCEDURE.name,
    )
    return AgentReachDecision(True, (), policy, prepared)
