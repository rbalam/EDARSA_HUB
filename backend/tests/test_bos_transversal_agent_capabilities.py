import pytest

from core.agent_capability_policy import PolicyContext
from modules.agent_harness.coa_communications_adapter import COACommunicationRequest, authorize_coa_communication
from modules.agent_harness.finance_reconciliation_adapter import FinanceReconciliationRequest, authorize_finance_reconciliation
from modules.agent_harness.transversal_capability_registry import CapabilityRegistryError, get_domain_capability, list_domain_capabilities


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


def test_registry_is_transversal_and_has_no_side_effects_in_first_slice():
    finance = list_domain_capabilities('FINANZAS')
    communications = list_domain_capabilities('COMMUNICATIONS')
    assert {x.code for x in finance} == {'FINANCE_RECONCILIATION_ANALYZE', 'FINANCE_RECONCILIATION_PROPOSE'}
    assert {x.code for x in communications} == {'COMMUNICATION_READ', 'COMMUNICATION_CLASSIFY', 'COMMUNICATION_DRAFT_REPLY'}
    assert all(not item.side_effect for item in finance + communications)
    with pytest.raises(CapabilityRegistryError, match='CAPABILITY_NOT_REGISTERED'):
        get_domain_capability('COMMUNICATION_SEND')


def test_finance_reconciliation_authorized_with_canonical_rbac_scope():
    req = FinanceReconciliationRequest('fin-1', 1, 2, 'FINANCE_RECONCILIATION_ANALYZE')
    scopes = {'empresa:1', 'unidad:2', 'domain:finanzas', 'resource:bank-reconciliation'}
    gate, policy = authorize_finance_reconciliation(
        req,
        {'allowed': True, 'permission': 'TES_CUADRES_Z_VER', 'empresa_id': 1, 'unidad_id': 2},
        context(req.capability, scopes),
    )
    assert gate.allowed is True
    assert policy.production_allowed is False
    assert policy.external_egress is False
    assert policy.data_classification.value == 'FINANCIAL_PRIVATE'


def test_finance_reconciliation_fails_closed_on_permission_or_scope():
    req = FinanceReconciliationRequest('fin-2', 1, 2)
    scopes = {'empresa:1', 'unidad:2', 'domain:finanzas', 'resource:bank-reconciliation'}
    gate, _ = authorize_finance_reconciliation(
        req,
        {'allowed': True, 'permission': 'OTRO_VER', 'empresa_id': 1, 'unidad_id': 2},
        context(req.capability, scopes),
    )
    assert gate.allowed is False
    assert gate.reasons == ('REQUESTER_PERMISSION_MISMATCH',)


def test_coa_draft_authorized_without_send_capability():
    req = COACommunicationRequest('coa-1', 1, 2, 'COMMUNICATION_DRAFT_REPLY', 'email')
    scopes = {'empresa:1', 'unidad:2', 'domain:communications', 'channel:email'}
    gate, policy = authorize_coa_communication(
        req,
        {'allowed': True, 'permission': 'NOTIFICACIONES_VER', 'empresa_id': 1, 'unidad_id': 2},
        context(req.capability, scopes),
    )
    assert gate.allowed is True
    assert policy.production_allowed is False
    assert policy.external_egress is False
    assert policy.data_classification.value == 'CONFIDENTIAL'


def test_coa_fails_closed_on_business_scope_and_channel():
    req = COACommunicationRequest('coa-2', 1, 2, 'COMMUNICATION_READ', 'whatsapp')
    scopes = {'empresa:1', 'unidad:2', 'domain:communications', 'channel:whatsapp'}
    gate, _ = authorize_coa_communication(
        req,
        {'allowed': True, 'permission': 'NOTIFICACIONES_VER', 'empresa_id': 1, 'unidad_id': 99},
        context(req.capability, scopes),
    )
    assert gate.allowed is False
    assert gate.reasons == ('REQUESTER_BUSINESS_SCOPE_MISMATCH',)
    with pytest.raises(Exception, match='CHANNEL_NOT_ALLOWED'):
        COACommunicationRequest('coa-3', 1, 2, 'COMMUNICATION_READ', 'sms')
