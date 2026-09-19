from __future__ import annotations

import re
from dataclasses import dataclass

MOBILE_OPERATION_SCHEMA = 'edarsahub.bos-mobile-operation.v1'
MOBILE_RESULT_SCHEMA = 'edarsahub.bos-mobile-result.v1'
MOBILE_RESULT_STATUSES = frozenset({'ACCEPT', 'REJECT', 'CONFLICT', 'RETRY', 'REQUIRES_REVIEW'})
_SHA256 = re.compile(r'^[0-9a-f]{64}$')


class MobileContractError(ValueError):
    pass


def _required(value: object, field: str) -> str:
    token = str(value or '').strip()
    if not token:
        raise MobileContractError(f'{field}_REQUIRED')
    return token


@dataclass(frozen=True)
class MobileOperationEnvelope:
    operation_uuid: str
    idempotency_key: str
    user_id: str
    installation_id: str
    device_id: str
    empresa_id: int
    unidad_id: int
    base_version: str
    occurred_at_utc: str
    payload_sha256: str
    operation_type: str
    schema: str = MOBILE_OPERATION_SCHEMA

    def __post_init__(self) -> None:
        for value, field in (
            (self.operation_uuid, 'OPERATION_UUID'),
            (self.idempotency_key, 'IDEMPOTENCY_KEY'),
            (self.user_id, 'USER_ID'),
            (self.installation_id, 'INSTALLATION_ID'),
            (self.device_id, 'DEVICE_ID'),
            (self.base_version, 'BASE_VERSION'),
            (self.occurred_at_utc, 'OCCURRED_AT_UTC'),
            (self.operation_type, 'OPERATION_TYPE'),
        ):
            _required(value, field)
        if self.empresa_id <= 0 or self.unidad_id <= 0:
            raise MobileContractError('BUSINESS_SCOPE_INVALID')
        if self.schema != MOBILE_OPERATION_SCHEMA:
            raise MobileContractError('MOBILE_OPERATION_SCHEMA_INVALID')
        digest = str(self.payload_sha256 or '').strip().lower()
        if not _SHA256.fullmatch(digest):
            raise MobileContractError('PAYLOAD_SHA256_INVALID')
        object.__setattr__(self, 'payload_sha256', digest)

    def to_contract(self) -> dict[str, object]:
        return {
            'schema': self.schema,
            'operation_uuid': self.operation_uuid,
            'idempotency_key': self.idempotency_key,
            'user_id': self.user_id,
            'installation_id': self.installation_id,
            'device_id': self.device_id,
            'empresa_id': self.empresa_id,
            'unidad_id': self.unidad_id,
            'base_version': self.base_version,
            'occurred_at_utc': self.occurred_at_utc,
            'payload_sha256': self.payload_sha256,
            'operation_type': self.operation_type,
            'mobile_is_source_of_truth': False,
            'server_authoritative': True,
        }


@dataclass(frozen=True)
class MobileOperationResult:
    operation_uuid: str
    status: str
    server_version: str
    reason: str = ''
    schema: str = MOBILE_RESULT_SCHEMA

    def __post_init__(self) -> None:
        _required(self.operation_uuid, 'OPERATION_UUID')
        _required(self.server_version, 'SERVER_VERSION')
        if self.schema != MOBILE_RESULT_SCHEMA:
            raise MobileContractError('MOBILE_RESULT_SCHEMA_INVALID')
        if self.status not in MOBILE_RESULT_STATUSES:
            raise MobileContractError('MOBILE_RESULT_STATUS_INVALID')
        if self.status != 'ACCEPT' and not str(self.reason or '').strip():
            raise MobileContractError('MOBILE_RESULT_REASON_REQUIRED')
