from core.agent_capability_policy import (
    BudgetRequest,
    DataClassification,
    PolicyContext,
    PolicyRequest,
    RiskLevel,
    evaluate_policy,
)


def context(**overrides):
    base = dict(
        user_allowed_capabilities=frozenset({'EXTERNAL_RESEARCH', 'CODE_READ'}),
        agent_allowed_capabilities=frozenset({'EXTERNAL_RESEARCH', 'CODE_READ'}),
        environment_allowed_capabilities=frozenset({'EXTERNAL_RESEARCH', 'CODE_READ'}),
        policy_allowed_capabilities=frozenset({'EXTERNAL_RESEARCH', 'CODE_READ'}),
        user_allowed_scopes=frozenset({'repo:EDARSA_HUB', 'env:development'}),
        agent_allowed_scopes=frozenset({'repo:EDARSA_HUB', 'env:development'}),
        environment_allowed_scopes=frozenset({'repo:EDARSA_HUB', 'env:development'}),
        policy_allowed_scopes=frozenset({'repo:EDARSA_HUB', 'env:development'}),
        budget_limits={
            'runtime_seconds': 300,
            'files_changed': 10,
            'lines_changed': 1000,
            'external_calls': 20,
            'sql_rows': 5000,
            'inference_cost_usd': 5.0,
        },
    )
    base.update(overrides)
    return PolicyContext(**base)


def request(**overrides):
    base = dict(
        capabilities=frozenset({'EXTERNAL_RESEARCH'}),
        scopes=frozenset({'repo:EDARSA_HUB', 'env:development'}),
        risk=RiskLevel.R1,
        data_classification=DataClassification.PUBLIC,
        budgets=BudgetRequest(runtime_seconds=60, external_calls=3),
        external_egress=True,
        production_allowed=False,
        privilege_expansion=False,
        approval_granted=False,
        procedure='research',
    )
    base.update(overrides)
    return PolicyRequest(**base)


def test_effective_permissions_are_intersection_and_allow_valid_request():
    decision = evaluate_policy(request(), context())
    assert decision.allowed is True
    assert decision.reasons == ()
    assert decision.effective_capabilities == frozenset({'EXTERNAL_RESEARCH'})


def test_missing_capability_in_any_authority_layer_denies_fail_closed():
    ctx = context(agent_allowed_capabilities=frozenset({'CODE_READ'}))
    decision = evaluate_policy(request(), ctx)
    assert decision.allowed is False
    assert 'CAPABILITY_NOT_EFFECTIVE' in decision.reasons


def test_scope_must_be_effective_across_all_layers():
    ctx = context(policy_allowed_scopes=frozenset({'env:development'}))
    decision = evaluate_policy(request(), ctx)
    assert decision.allowed is False
    assert 'SCOPE_NOT_EFFECTIVE' in decision.reasons


def test_production_and_privilege_expansion_are_forbidden():
    decision = evaluate_policy(
        request(production_allowed=True, privilege_expansion=True),
        context(),
    )
    assert decision.allowed is False
    assert 'PRODUCTION_FORBIDDEN' in decision.reasons
    assert 'PRIVILEGE_EXPANSION_FORBIDDEN' in decision.reasons


def test_r4_requires_explicit_approval():
    denied = evaluate_policy(request(risk=RiskLevel.R4), context())
    allowed = evaluate_policy(request(risk=RiskLevel.R4, approval_granted=True), context())
    assert denied.allowed is False
    assert 'R4_APPROVAL_REQUIRED' in denied.reasons
    assert allowed.allowed is True


def test_external_egress_only_allows_public_data():
    decision = evaluate_policy(
        request(data_classification=DataClassification.SECRET),
        context(),
    )
    assert decision.allowed is False
    assert 'EGRESS_DATA_CLASSIFICATION_FORBIDDEN' in decision.reasons


def test_missing_budget_limit_denies_fail_closed():
    limits = dict(context().budget_limits)
    limits.pop('external_calls')
    decision = evaluate_policy(request(), context(budget_limits=limits))
    assert decision.allowed is False
    assert 'BUDGET_LIMIT_MISSING:external_calls' in decision.reasons


def test_budget_excess_denies():
    decision = evaluate_policy(
        request(budgets=BudgetRequest(runtime_seconds=301, external_calls=3)),
        context(),
    )
    assert decision.allowed is False
    assert 'BUDGET_EXCEEDED:runtime_seconds' in decision.reasons


def test_procedure_name_does_not_grant_authority():
    decision = evaluate_policy(
        request(
            capabilities=frozenset({'SECRET_TOOL'}),
            procedure='superadmin-skill',
        ),
        context(),
    )
    assert decision.allowed is False
    assert 'CAPABILITY_NOT_EFFECTIVE' in decision.reasons
