from core.agent_capability_policy import (
    BudgetRequest,
    DataClassification,
    PolicyContext,
    PolicyRequest,
    RiskLevel,
)
from core.agent_procedure_policy import ProcedureSpec, evaluate_procedure


def context(**overrides):
    base = dict(
        user_allowed_capabilities=frozenset({'CODE_READ', 'TEST_EXECUTE'}),
        agent_allowed_capabilities=frozenset({'CODE_READ', 'TEST_EXECUTE'}),
        environment_allowed_capabilities=frozenset({'CODE_READ', 'TEST_EXECUTE'}),
        policy_allowed_capabilities=frozenset({'CODE_READ', 'TEST_EXECUTE'}),
        user_allowed_scopes=frozenset({'repo:EDARSA_HUB', 'env:development'}),
        agent_allowed_scopes=frozenset({'repo:EDARSA_HUB', 'env:development'}),
        environment_allowed_scopes=frozenset({'repo:EDARSA_HUB', 'env:development'}),
        policy_allowed_scopes=frozenset({'repo:EDARSA_HUB', 'env:development'}),
        budget_limits={
            'runtime_seconds': 300,
            'files_changed': 10,
            'lines_changed': 1000,
            'external_calls': 10,
            'sql_rows': 5000,
            'inference_cost_usd': 5.0,
        },
    )
    base.update(overrides)
    return PolicyContext(**base)


def request(**overrides):
    base = dict(
        capabilities=frozenset({'CODE_READ', 'TEST_EXECUTE'}),
        scopes=frozenset({'repo:EDARSA_HUB', 'env:development'}),
        risk=RiskLevel.R1,
        data_classification=DataClassification.INTERNAL,
        budgets=BudgetRequest(runtime_seconds=60),
        external_egress=False,
        production_allowed=False,
        privilege_expansion=False,
        approval_granted=False,
        procedure='validator',
    )
    base.update(overrides)
    return PolicyRequest(**base)


def spec(**overrides):
    base = dict(
        name='validator',
        required_capabilities=frozenset({'CODE_READ', 'TEST_EXECUTE'}),
        max_risk=RiskLevel.R2,
        external_egress_allowed=False,
    )
    base.update(overrides)
    return ProcedureSpec(**base)


def test_valid_procedure_still_requires_policy_authority():
    decision = evaluate_procedure(spec(), request(), context())
    assert decision.allowed is True


def test_procedure_name_never_grants_authority():
    ctx = context(policy_allowed_capabilities=frozenset({'CODE_READ'}))
    decision = evaluate_procedure(spec(), request(), ctx)
    assert decision.allowed is False
    assert 'CAPABILITY_NOT_EFFECTIVE' in decision.reasons


def test_required_capabilities_must_be_requested_explicitly():
    decision = evaluate_procedure(
        spec(),
        request(capabilities=frozenset({'CODE_READ'})),
        context(),
    )
    assert decision.allowed is False
    assert 'PROCEDURE_REQUIRED_CAPABILITY_MISSING' in decision.reasons


def test_procedure_mismatch_denies():
    decision = evaluate_procedure(spec(), request(procedure='coder'), context())
    assert decision.allowed is False
    assert 'PROCEDURE_MISMATCH' in decision.reasons


def test_risk_cannot_exceed_procedure_contract():
    decision = evaluate_procedure(spec(max_risk=RiskLevel.R1), request(risk=RiskLevel.R2), context())
    assert decision.allowed is False
    assert 'PROCEDURE_RISK_EXCEEDED' in decision.reasons


def test_egress_requires_both_procedure_and_policy_permission():
    denied_by_procedure = evaluate_procedure(
        spec(external_egress_allowed=False),
        request(external_egress=True, data_classification=DataClassification.PUBLIC),
        context(),
    )
    assert denied_by_procedure.allowed is False
    assert 'PROCEDURE_EGRESS_FORBIDDEN' in denied_by_procedure.reasons

    allowed = evaluate_procedure(
        spec(external_egress_allowed=True),
        request(external_egress=True, data_classification=DataClassification.PUBLIC),
        context(),
    )
    assert allowed.allowed is True


def test_empty_procedure_contract_fails_closed():
    decision = evaluate_procedure(
        spec(name='', required_capabilities=frozenset()),
        request(procedure=''),
        context(),
    )
    assert decision.allowed is False
    assert 'PROCEDURE_NAME_REQUIRED' in decision.reasons
    assert 'PROCEDURE_CAPABILITIES_REQUIRED' in decision.reasons
