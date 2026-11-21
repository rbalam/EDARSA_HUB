from __future__ import annotations

import pytest

from modules.agent_harness.marketing_cx import (
    CANONICAL_CUSTOMER_SOURCES, CUSTOMER_MASTER, Customer360Request,
    MarketingActivationRequest, MarketingPolicyError,
)


def activation(**overrides):
    values = dict(
        activation_id='mk-1', customer_id=10, empresa_id=1, unidad_id=2,
        purpose='retention-offer', legal_basis='consent', consent_granted=True,
        channel='email', scope='customer:10', budget_limit=100.0,
        quiet_hours_respected=True, opted_out=False,
    )
    values.update(overrides)
    return MarketingActivationRequest(**values)


def test_customer360_uses_canonical_customer_master_without_copy():
    view = Customer360Request(customer_id=10, empresa_id=1, unidad_id=2).view_contract()
    assert view['customer_master'] == 'dbo.Cliente_Catalogo'
    assert view['materialized_customer_copy'] is False
    assert CUSTOMER_MASTER in CANONICAL_CUSTOMER_SOURCES
    assert 'dbo.CRM_Cuentas' in CANONICAL_CUSTOMER_SOURCES
    assert 'dbo.RRR_Eventos' in CANONICAL_CUSTOMER_SOURCES


def test_activation_is_envelope_only_and_requires_communications_executor():
    envelope = activation().to_envelope()
    assert envelope['communications_executor_required'] is True
    assert envelope['direct_send_allowed'] is False
    assert envelope['customer_master'] == CUSTOMER_MASTER


def test_consent_is_fail_closed():
    with pytest.raises(MarketingPolicyError, match='CONSENT_REQUIRED'):
        activation(consent_granted=False)


def test_opt_out_is_fail_closed():
    with pytest.raises(MarketingPolicyError, match='CUSTOMER_OPTED_OUT'):
        activation(opted_out=True)


def test_quiet_hours_are_fail_closed():
    with pytest.raises(MarketingPolicyError, match='QUIET_HOURS_VIOLATION'):
        activation(quiet_hours_respected=False)


def test_unknown_channel_is_denied():
    with pytest.raises(MarketingPolicyError, match='CHANNEL_NOT_APPROVED'):
        activation(channel='raw-socket')


def test_budget_is_mandatory_and_positive():
    with pytest.raises(MarketingPolicyError, match='BUDGET_LIMIT_INVALID'):
        activation(budget_limit=0)


def test_scope_and_purpose_are_mandatory():
    with pytest.raises(MarketingPolicyError, match='SCOPE_REQUIRED'):
        activation(scope='')
    with pytest.raises(MarketingPolicyError, match='PURPOSE_REQUIRED'):
        activation(purpose='')
