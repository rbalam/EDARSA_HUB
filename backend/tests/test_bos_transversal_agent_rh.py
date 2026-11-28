import pytest

from core.agent_capability_policy import PolicyContext
from modules.agent_harness.hr_adapter import HRAgentRequest, authorize_hr_agent
from modules.agent_harness.transversal_capability_registry import list_domain_capabilities


def context(capability, scopes):
    caps = frozenset({capability})
    scope_set = frozenset(scopes)
    limits = {
        'runtime_seconds': 60,
        'files_changed': 0,
        'lines_changed': 0,
        'external_calls': 0,
        'sql_rows': 1000,
        'inference_cost_usd': 1.0,
    }
    return PolicyContext(caps, caps, caps, caps, scope_set, scope_set, scope_set, scope_set, limits)


def test_gate4_registry_extends_same_registry_with_hr_read_only_capabilities():
    items = list_domain_capabilities('RH')
    assert {item.code for item in items} == {
        'HR_DOCUMENT_ANALYZE',
        'HR_EMPLOYEE_CASE_SUMMARIZE',
        'HR_RECRUITMENT_ASSIST',
        'HR_PAYROLL_EXPLAIN',
    }
    assert all(not item.side_effect for item in items)
    assert all(not item.approval_required for item in items)
    assert all(item.accepted_permissions == ('RH_VER', 'RECURSOS_HUMANOS_VER') for item in items)


def test_hr_accepts_primary_permission_and_scope():
    req = HRAgentRequest('rh-1', 1, 2, 'HR_DOCUMENT_ANALYZE')
    scopes = {'empresa:1', 'unidad:2', 'domain:rh', 'resource:human-resources'}
    gate, policy = authorize_hr_agent(
        req,
        {'allowed': True, 'permission': 'RH_VER', 'empresa_id': 1, 'unidad_id': 2},
        context(req.capability, scopes),
    )
    assert gate.allowed is True
    assert policy.data_classification.value == 'PII'
    assert policy.external_egress is False
    assert policy.production_allowed is False


def test_hr_accepts_existing_legacy_compatible_permission_alias():
    req = HRAgentRequest('rh-2', 1, 2, 'HR_EMPLOYEE_CASE_SUMMARIZE')
    scopes = {'empresa:1', 'unidad:2', 'domain:rh', 'resource:human-resources'}
    gate, _ = authorize_hr_agent(
        req,
        {'allowed': True, 'permission': 'RECURSOS_HUMANOS_VER', 'empresa_id': 1, 'unidad_id': 2},
        context(req.capability, scopes),
    )
    assert gate.allowed is True


def test_hr_payroll_is_financial_private_and_read_only():
    req = HRAgentRequest('rh-3', 1, 2, 'HR_PAYROLL_EXPLAIN')
    scopes = {'empresa:1', 'unidad:2', 'domain:rh', 'resource:human-resources'}
    gate, policy = authorize_hr_agent(
        req,
        {'allowed': True, 'permission': 'RH_VER', 'empresa_id': 1, 'unidad_id': 2},
        context(req.capability, scopes),
    )
    assert gate.allowed is True
    assert policy.data_classification.value == 'FINANCIAL_PRIVATE'
    assert policy.external_egress is False


def test_hr_fails_closed_on_permission_or_scope():
    req = HRAgentRequest('rh-4', 1, 2)
    scopes = {'empresa:1', 'unidad:2', 'domain:rh', 'resource:human-resources'}
    gate, _ = authorize_hr_agent(
        req,
        {'allowed': True, 'permission': 'OTRO_VER', 'empresa_id': 1, 'unidad_id': 2},
        context(req.capability, scopes),
    )
    assert gate.allowed is False
    assert gate.reasons == ('REQUESTER_PERMISSION_MISMATCH',)

    gate, _ = authorize_hr_agent(
        req,
        {'allowed': True, 'permission': 'RH_VER', 'empresa_id': 1, 'unidad_id': 99},
        context(req.capability, scopes),
    )
    assert gate.allowed is False
    assert gate.reasons == ('REQUESTER_BUSINESS_SCOPE_MISMATCH',)


def test_cross_domain_capability_is_rejected():
    with pytest.raises(Exception, match='HR_CAPABILITY_REQUIRED'):
        HRAgentRequest('rh-5', 1, 2, 'CRM_SUMMARIZE')
