from core.agent_capability_policy import (
    BudgetRequest, DataClassification, PolicyContext, PolicyRequest, RiskLevel
)
from core.agent_execution_gate import (
    authorize_ai_inference_execution, authorize_external_research_execution
)
from core.ai_gateway_policy_adapter import ModelCandidate, ModelRouteRequest


def policy_context(capability, scopes, inference_limit=1.0):
    caps = frozenset({capability})
    scopes = frozenset(scopes)
    return PolicyContext(
        user_allowed_capabilities=caps, agent_allowed_capabilities=caps,
        environment_allowed_capabilities=caps, policy_allowed_capabilities=caps,
        user_allowed_scopes=scopes, agent_allowed_scopes=scopes,
        environment_allowed_scopes=scopes, policy_allowed_scopes=scopes,
        budget_limits={
            'runtime_seconds': 60, 'files_changed': 0, 'lines_changed': 0,
            'external_calls': 5, 'sql_rows': 0, 'inference_cost_usd': inference_limit,
        },
    )


def test_e2e_rbac_to_agent_reach_prepared_request():
    scopes = frozenset({'external:web'})
    request = PolicyRequest(
        capabilities=frozenset({'EXTERNAL_RESEARCH'}), scopes=scopes,
        risk=RiskLevel.R1, data_classification=DataClassification.PUBLIC,
        budgets=BudgetRequest(external_calls=2), external_egress=True,
        procedure='agent-reach-external-research',
    )
    result = authorize_external_research_execution(
        {'allowed': True, 'reason': 'SUPERADMIN_CANONICAL'},
        ' public market research ', request,
        policy_context('EXTERNAL_RESEARCH', scopes),
    )
    assert result.allowed is True
    assert result.downstream is not None
    assert result.downstream.prepared.query == 'public market research'


def test_e2e_rbac_denial_stops_before_downstream():
    scopes = frozenset({'external:web'})
    request = PolicyRequest(
        capabilities=frozenset({'EXTERNAL_RESEARCH'}), scopes=scopes,
        risk=RiskLevel.R1, data_classification=DataClassification.PUBLIC,
        budgets=BudgetRequest(external_calls=1), external_egress=True,
        procedure='agent-reach-external-research',
    )
    result = authorize_external_research_execution(
        {'allowed': False, 'reason': 'REQUESTER_NOT_SUPERADMIN'},
        'public research', request, policy_context('EXTERNAL_RESEARCH', scopes),
    )
    assert result.allowed is False
    assert result.reasons == ('REQUESTER_NOT_SUPERADMIN',)
    assert result.downstream is None


def test_e2e_rbac_to_ai_gateway_authorized_route():
    scopes = frozenset({'ai:provider:p1', 'ai:model:p1/m1'})
    request = PolicyRequest(
        capabilities=frozenset({'AI_INFERENCE'}), scopes=scopes,
        risk=RiskLevel.R1, data_classification=DataClassification.PUBLIC,
        budgets=BudgetRequest(external_calls=1, inference_cost_usd=0.20),
        external_egress=True, procedure='ai-model-routing',
    )
    candidate = ModelCandidate(
        provider='p1', model='m1', capabilities=frozenset({'TEXT'}),
        allowed_data_classifications=frozenset({DataClassification.PUBLIC}),
        max_risk=RiskLevel.R2, input_cost_per_1k_usd=0.01, output_cost_per_1k_usd=0.02,
    )
    result = authorize_ai_inference_execution(
        {'allowed': True, 'reason': 'SUPERADMIN_CANONICAL'},
        ModelRouteRequest(frozenset({'TEXT'}), 1000, 1000),
        request, policy_context('AI_INFERENCE', scopes), [candidate],
    )
    assert result.allowed is True
    assert result.downstream is not None
    assert result.downstream.prepared.provider == 'p1'
    assert result.downstream.prepared.model == 'm1'


def test_e2e_private_data_and_privilege_expansion_fail_closed():
    scopes = frozenset({'ai:provider:p1', 'ai:model:p1/m1'})
    request = PolicyRequest(
        capabilities=frozenset({'AI_INFERENCE'}), scopes=scopes,
        risk=RiskLevel.R1, data_classification=DataClassification.CONFIDENTIAL,
        budgets=BudgetRequest(external_calls=1, inference_cost_usd=0.20),
        external_egress=True, privilege_expansion=True, procedure='ai-model-routing',
    )
    candidate = ModelCandidate(
        provider='p1', model='m1', capabilities=frozenset({'TEXT'}),
        allowed_data_classifications=frozenset({DataClassification.PUBLIC}),
        max_risk=RiskLevel.R2, input_cost_per_1k_usd=0.01, output_cost_per_1k_usd=0.02,
    )
    result = authorize_ai_inference_execution(
        {'allowed': True, 'reason': 'SUPERADMIN_CANONICAL'},
        ModelRouteRequest(frozenset({'TEXT'}), 1000, 1000),
        request, policy_context('AI_INFERENCE', scopes), [candidate],
    )
    assert result.allowed is False
    assert 'PRIVILEGE_EXPANSION_FORBIDDEN' in result.reasons
    assert 'EGRESS_DATA_CLASSIFICATION_FORBIDDEN' in result.reasons
