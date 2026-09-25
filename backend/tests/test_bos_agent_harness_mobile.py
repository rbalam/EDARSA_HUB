from __future__ import annotations

import pytest

from modules.agent_harness.mobile import MobileContractError, MobileOperationEnvelope, MobileOperationResult


def envelope(**overrides):
    values = dict(
        operation_uuid='11111111-1111-1111-1111-111111111111',
        idempotency_key='idem-1', user_id='u1', installation_id='i1', device_id='d1',
        empresa_id=1, unidad_id=2, base_version='v10', occurred_at_utc='2026-09-11T06:00:00Z',
        payload_sha256='a' * 64, operation_type='inventory-count',
    )
    values.update(overrides)
    return MobileOperationEnvelope(**values)


def test_mobile_is_never_source_of_truth():
    contract = envelope().to_contract()
    assert contract['mobile_is_source_of_truth'] is False
    assert contract['server_authoritative'] is True


def test_offline_contract_requires_idempotency_and_device_identity():
    with pytest.raises(MobileContractError, match='IDEMPOTENCY_KEY_REQUIRED'):
        envelope(idempotency_key='')
    with pytest.raises(MobileContractError, match='DEVICE_ID_REQUIRED'):
        envelope(device_id='')
    with pytest.raises(MobileContractError, match='INSTALLATION_ID_REQUIRED'):
        envelope(installation_id='')


def test_business_scope_is_required():
    with pytest.raises(MobileContractError, match='BUSINESS_SCOPE_INVALID'):
        envelope(unidad_id=0)


def test_payload_hash_is_sha256():
    with pytest.raises(MobileContractError, match='PAYLOAD_SHA256_INVALID'):
        envelope(payload_sha256='not-a-hash')


def test_server_result_accepts_only_canonical_statuses():
    for status in ('ACCEPT', 'REJECT', 'CONFLICT', 'RETRY', 'REQUIRES_REVIEW'):
        reason = '' if status == 'ACCEPT' else 'policy'
        assert MobileOperationResult('op-1', status, 'v11', reason).status == status
    with pytest.raises(MobileContractError, match='MOBILE_RESULT_STATUS_INVALID'):
        MobileOperationResult('op-1', 'LAST_WRITE_WINS', 'v11', 'bad')


def test_non_accept_requires_reason():
    with pytest.raises(MobileContractError, match='MOBILE_RESULT_REASON_REQUIRED'):
        MobileOperationResult('op-1', 'CONFLICT', 'v11')


def test_no_generic_last_write_wins_contract():
    with pytest.raises(MobileContractError, match='MOBILE_RESULT_STATUS_INVALID'):
        MobileOperationResult('op-1', 'OVERWRITE', 'v12', 'forbidden')
