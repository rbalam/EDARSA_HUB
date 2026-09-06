from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from core.agent_capability_policy import PolicyContext, PolicyRequest
from core.agent_reach_policy_adapter import AgentReachDecision, authorize_agent_reach
from core.ai_gateway_policy_adapter import (
    ModelCandidate, ModelRouteDecision, ModelRouteRequest, authorize_model_route
)


@dataclass(frozen=True)
class ExecutionGateDecision:
    allowed: bool
    reasons: tuple[str, ...]
    downstream: AgentReachDecision | ModelRouteDecision | None


def _requester_reasons(requester_authorization: Any) -> tuple[str, ...]:
    if not isinstance(requester_authorization, dict):
        return ('REQUESTER_AUTHORIZATION_REQUIRED',)
    if requester_authorization.get('allowed') is not True:
        reason = str(requester_authorization.get('reason') or 'REQUESTER_RBAC_DENIED').strip()
        return (reason or 'REQUESTER_RBAC_DENIED',)
    return ()


def authorize_external_research_execution(
    requester_authorization: Any,
    query: str,
    request: PolicyRequest,
    context: PolicyContext,
) -> ExecutionGateDecision:
    reasons = _requester_reasons(requester_authorization)
    if reasons:
        return ExecutionGateDecision(False, reasons, None)
    downstream = authorize_agent_reach(query, request, context)
    return ExecutionGateDecision(downstream.allowed, downstream.reasons, downstream)


def authorize_ai_inference_execution(
    requester_authorization: Any,
    route: ModelRouteRequest,
    request: PolicyRequest,
    context: PolicyContext,
    candidates: Iterable[ModelCandidate],
) -> ExecutionGateDecision:
    reasons = _requester_reasons(requester_authorization)
    if reasons:
        return ExecutionGateDecision(False, reasons, None)
    downstream = authorize_model_route(route, request, context, candidates)
    return ExecutionGateDecision(downstream.allowed, downstream.reasons, downstream)
