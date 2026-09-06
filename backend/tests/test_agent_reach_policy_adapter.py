from core.agent_capability_policy import (
    BudgetRequest, DataClassification, PolicyContext, PolicyRequest, RiskLevel
)
from core.agent_reach_policy_adapter import authorize_agent_reach


def context():
    caps = frozenset({'EXTERNAL_RESEARCH'})
    scopes = frozenset({'external:web'})
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
            'external_calls': 5, 'sql_rows': 0, 'inference_cost_usd': 1.0,
        },
    )


def request(**changes):
    values = dict(
        capabilities=frozenset({'EXTERNAL_RESEARCH'}),
        scopes=frozenset({'external:web'}),
        risk=RiskLevel.R1,
        data_classification=DataClassification.PUBLIC,
        budgets=BudgetRequest(external_calls=2),
        external_egress=True,
        production_allowed=False,
        privilege_expansion=False,
        procedure='agent-reach-external-research',
    )
    values.update(changes)
    return PolicyRequest(**values)


def test_allows_public_external_research_and_only_prepares_request():
    result = authorize_agent_reach('  latest   public menu trends  ', request(), context())
    assert result.allowed is True
    assert result.prepared is not None
    assert result.prepared.query == 'latest public menu trends'
    assert result.prepared.max_external_calls == 2


def test_blocks_private_data_egress():
    result = authorize_agent_reach(
        'research competitors',
        request(data_classification=DataClassification.CONFIDENTIAL),
        context(),
    )
    assert result.allowed is False
    assert 'AGENT_REACH_PUBLIC_DATA_ONLY' in result.reasons


def test_blocks_secret_and_data_access_patterns():
    for query in ('password=abc', 'mongodb://host/db', 'DELETE FROM users', 'api_key=abc'):
        result = authorize_agent_reach(query, request(), context())
        assert result.allowed is False
        assert 'AGENT_REACH_SENSITIVE_OR_DATA_ACCESS_PATTERN' in result.reasons


def test_blocks_missing_capability_and_scope():
    denied = request(capabilities=frozenset({'OTHER'}))
    result = authorize_agent_reach('public research', denied, context())
    assert result.allowed is False


def test_blocks_budget_and_risk_overreach():
    result = authorize_agent_reach(
        'public research',
        request(risk=RiskLevel.R2, budgets=BudgetRequest(external_calls=6)),
        context(),
    )
    assert result.allowed is False
    assert 'AGENT_REACH_RISK_EXCEEDED' in result.reasons
