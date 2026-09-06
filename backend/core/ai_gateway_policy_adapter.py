from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Iterable

from core.agent_capability_policy import (
    DataClassification,
    PolicyContext,
    PolicyDecision,
    PolicyRequest,
    RiskLevel,
)
from core.agent_procedure_policy import ProcedureSpec, evaluate_procedure


AI_GATEWAY_PROCEDURE = ProcedureSpec(
    name='ai-model-routing',
    required_capabilities=frozenset({'AI_INFERENCE'}),
    max_risk=RiskLevel.R2,
    external_egress_allowed=True,
)


@dataclass(frozen=True)
class ModelCandidate:
    provider: str
    model: str
    capabilities: FrozenSet[str]
    allowed_data_classifications: FrozenSet[DataClassification]
    max_risk: RiskLevel
    input_cost_per_1k_usd: float
    output_cost_per_1k_usd: float


@dataclass(frozen=True)
class ModelRouteRequest:
    required_model_capabilities: FrozenSet[str]
    estimated_input_tokens: int
    estimated_output_tokens: int


@dataclass(frozen=True)
class PreparedModelRoute:
    provider: str
    model: str
    estimated_cost_usd: float
    effective_scopes: FrozenSet[str]
    procedure: str


@dataclass(frozen=True)
class ModelRouteDecision:
    allowed: bool
    reasons: tuple[str, ...]
    policy: PolicyDecision
    prepared: PreparedModelRoute | None


def _candidate_scope(provider: str, model: str) -> tuple[str, str]:
    return (f'ai:provider:{provider}', f'ai:model:{provider}/{model}')


def _estimate_cost(candidate: ModelCandidate, route: ModelRouteRequest) -> float:
    return (
        (route.estimated_input_tokens / 1000.0) * candidate.input_cost_per_1k_usd
        + (route.estimated_output_tokens / 1000.0) * candidate.output_cost_per_1k_usd
    )


def authorize_model_route(
    route: ModelRouteRequest,
    request: PolicyRequest,
    context: PolicyContext,
    policy_candidates: Iterable[ModelCandidate],
) -> ModelRouteDecision:
    reasons: list[str] = []

    if not request.external_egress:
        reasons.append('AI_GATEWAY_EGRESS_REQUIRED')
    if request.risk > RiskLevel.R2:
        reasons.append('AI_GATEWAY_RISK_EXCEEDED')
    if not route.required_model_capabilities:
        reasons.append('AI_GATEWAY_MODEL_CAPABILITY_REQUIRED')
    if route.estimated_input_tokens < 0 or route.estimated_output_tokens < 0:
        reasons.append('AI_GATEWAY_TOKEN_ESTIMATE_INVALID')

    policy = evaluate_procedure(AI_GATEWAY_PROCEDURE, request, context)
    reasons.extend(policy.reasons)

    compatible: list[tuple[float, str, str, ModelCandidate]] = []
    if not reasons:
        for candidate in policy_candidates:
            provider = candidate.provider.strip()
            model = candidate.model.strip()
            if not provider or not model:
                continue
            if candidate.input_cost_per_1k_usd < 0 or candidate.output_cost_per_1k_usd < 0:
                continue
            if not route.required_model_capabilities.issubset(candidate.capabilities):
                continue
            if request.data_classification not in candidate.allowed_data_classifications:
                continue
            if request.risk > candidate.max_risk:
                continue
            provider_scope, model_scope = _candidate_scope(provider, model)
            if provider_scope not in policy.effective_scopes:
                continue
            if model_scope not in policy.effective_scopes:
                continue
            estimated_cost = _estimate_cost(candidate, route)
            if estimated_cost > request.budgets.inference_cost_usd:
                continue
            compatible.append((estimated_cost, provider, model, candidate))

    if not compatible:
        reasons.append('AI_GATEWAY_NO_AUTHORIZED_ROUTE')

    unique_reasons = tuple(dict.fromkeys(reasons))
    if unique_reasons:
        return ModelRouteDecision(False, unique_reasons, policy, None)

    estimated_cost, provider, model, _candidate = min(
        compatible, key=lambda item: (item[0], item[1], item[2])
    )
    return ModelRouteDecision(
        True,
        (),
        policy,
        PreparedModelRoute(
            provider=provider,
            model=model,
            estimated_cost_usd=estimated_cost,
            effective_scopes=policy.effective_scopes,
            procedure=AI_GATEWAY_PROCEDURE.name,
        ),
    )
