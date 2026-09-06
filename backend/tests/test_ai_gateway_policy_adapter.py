from core.agent_capability_policy import (
    BudgetRequest, DataClassification, PolicyContext, PolicyRequest, RiskLevel
)
from core.ai_gateway_policy_adapter import (
    ModelCandidate, ModelRouteRequest, authorize_model_route
)


def context():
    caps = frozenset({'AI_INFERENCE'})
    scopes = frozenset({
        'ai:provider:provider-a',
        'ai:model:provider-a/model-cheap',
        'ai:model:provider-a/model-expensive',
    })
    return PolicyContext(
        user_allowed_capabilities=caps,
        agent_allowed_capabilities=caps,
        environment_allowed_capabilities=caps,
        policy_allowed_capabilities=caps,
        user_allowed_scopes=scopes,
        agent_allowed_scopes=scopes,
        environment_allowed_scopes=scopes,
        policy_allowed_scopes=scopes,
        budget_limits={
            'runtime_seconds': 60, 'files_changed': 0, 'lines_changed': 0,
            'external_calls': 2, 'sql_rows': 0, 'inference_cost_usd': 1.0,
        },
    )


def request(**changes):
    values = dict(
        capabilities=frozenset({'AI_INFERENCE'}),
        scopes=frozenset({
            'ai:provider:provider-a',
            'ai:model:provider-a/model-cheap',
            'ai:model:provider-a/model-expensive',
        }),
        risk=RiskLevel.R1,
        data_classification=DataClassification.PUBLIC,
        budgets=BudgetRequest(external_calls=1, inference_cost_usd=0.50),
        external_egress=True,
        production_allowed=False,
        privilege_expansion=False,
        procedure='ai-model-routing',
    )
    values.update(changes)
    return PolicyRequest(**values)


def candidates():
    common = dict(
        capabilities=frozenset({'TEXT'}),
        allowed_data_classifications=frozenset({DataClassification.PUBLIC}),
        max_risk=RiskLevel.R2,
    )
    return [
        ModelCandidate('provider-a', 'model-expensive', input_cost_per_1k_usd=0.05, output_cost_per_1k_usd=0.10, **common),
        ModelCandidate('provider-a', 'model-cheap', input_cost_per_1k_usd=0.01, output_cost_per_1k_usd=0.02, **common),
        ModelCandidate('provider-b', 'model-hidden', input_cost_per_1k_usd=0.001, output_cost_per_1k_usd=0.001, **common),
    ]


def route():
    return ModelRouteRequest(frozenset({'TEXT'}), 1000, 1000)


def test_selects_lowest_cost_authorized_model_deterministically():
    result = authorize_model_route(route(), request(), context(), candidates())
    assert result.allowed is True
    assert result.prepared is not None
    assert result.prepared.provider == 'provider-a'
    assert result.prepared.model == 'model-cheap'
    assert round(result.prepared.estimated_cost_usd, 4) == 0.03


def test_cannot_route_to_provider_without_effective_scope():
    only_hidden = [candidates()[2]]
    result = authorize_model_route(route(), request(), context(), only_hidden)
    assert result.allowed is False
    assert 'AI_GATEWAY_NO_AUTHORIZED_ROUTE' in result.reasons


def test_private_data_is_blocked_by_global_policy_before_provider_choice():
    result = authorize_model_route(
        route(),
        request(data_classification=DataClassification.CONFIDENTIAL),
        context(),
        candidates(),
    )
    assert result.allowed is False
    assert 'EGRESS_DATA_CLASSIFICATION_FORBIDDEN' in result.reasons


def test_cost_budget_blocks_expensive_route():
    result = authorize_model_route(
        route(),
        request(budgets=BudgetRequest(external_calls=1, inference_cost_usd=0.01)),
        context(),
        candidates(),
    )
    assert result.allowed is False
    assert 'AI_GATEWAY_NO_AUTHORIZED_ROUTE' in result.reasons


def test_skill_or_procedure_cannot_grant_missing_ai_capability():
    denied = request(capabilities=frozenset({'OTHER'}))
    result = authorize_model_route(route(), denied, context(), candidates())
    assert result.allowed is False
    assert result.prepared is None


def test_risk_overreach_is_blocked():
    result = authorize_model_route(
        route(),
        request(risk=RiskLevel.R3),
        context(),
        candidates(),
    )
    assert result.allowed is False
    assert 'AI_GATEWAY_RISK_EXCEEDED' in result.reasons
