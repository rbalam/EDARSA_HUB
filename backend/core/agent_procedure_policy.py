from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet

from core.agent_capability_policy import (
    PolicyContext,
    PolicyDecision,
    PolicyRequest,
    RiskLevel,
    evaluate_policy,
)


@dataclass(frozen=True)
class ProcedureSpec:
    name: str
    required_capabilities: FrozenSet[str]
    max_risk: RiskLevel
    external_egress_allowed: bool = False


def evaluate_procedure(
    spec: ProcedureSpec,
    request: PolicyRequest,
    context: PolicyContext,
) -> PolicyDecision:
    reasons: list[str] = []

    if not spec.name.strip():
        reasons.append('PROCEDURE_NAME_REQUIRED')

    if request.procedure != spec.name:
        reasons.append('PROCEDURE_MISMATCH')

    if not spec.required_capabilities:
        reasons.append('PROCEDURE_CAPABILITIES_REQUIRED')
    elif not spec.required_capabilities.issubset(request.capabilities):
        reasons.append('PROCEDURE_REQUIRED_CAPABILITY_MISSING')

    if request.risk > spec.max_risk:
        reasons.append('PROCEDURE_RISK_EXCEEDED')

    if request.external_egress and not spec.external_egress_allowed:
        reasons.append('PROCEDURE_EGRESS_FORBIDDEN')

    policy = evaluate_policy(request, context)
    reasons.extend(policy.reasons)

    return PolicyDecision(
        allowed=not reasons,
        reasons=tuple(dict.fromkeys(reasons)),
        effective_capabilities=policy.effective_capabilities,
        effective_scopes=policy.effective_scopes,
    )
