"""API Factory access contract for EDARSAHUB BOS.

Defines immutable API versions and consumer authorization scopes.
No credentials or secret material are stored here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Sequence

from .api_factory_contract import (
    ApiAuthMode,
    ApiFactoryContractError,
    ApiPublicationStatus,
    PublishedApiDefinition,
    validate_api_definition,
)


class ApiConsumerStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


@dataclass(frozen=True)
class PublishedApiVersion:
    api_code: str
    version: str
    contract_fingerprint: str
    input_schema_version: Optional[str] = None
    output_schema_version: Optional[str] = None
    immutable: bool = True


@dataclass(frozen=True)
class ApiConsumerGrant:
    consumer_code: str
    api_code: str
    api_version: str
    status: ApiConsumerStatus
    auth_mode: ApiAuthMode
    credential_reference: Optional[str] = None
    company_ids: Sequence[str] = field(default_factory=tuple)
    unit_ids: Sequence[str] = field(default_factory=tuple)
    rate_limit_per_minute: Optional[int] = None


def validate_api_version(version: PublishedApiVersion) -> None:
    if not str(version.api_code or "").strip():
        raise ApiFactoryContractError("API_VERSION_CODE_REQUIRED")
    if not str(version.version or "").strip():
        raise ApiFactoryContractError("API_VERSION_REQUIRED")

    fingerprint = str(version.contract_fingerprint or "").strip().lower()
    if (
        len(fingerprint) != 64
        or any(ch not in "0123456789abcdef" for ch in fingerprint)
    ):
        raise ApiFactoryContractError("API_CONTRACT_FINGERPRINT_INVALID")

    if not version.immutable:
        raise ApiFactoryContractError(
            "PUBLISHED_API_VERSION_MUST_BE_IMMUTABLE"
        )


def validate_consumer_grant(grant: ApiConsumerGrant) -> None:
    if not str(grant.consumer_code or "").strip():
        raise ApiFactoryContractError("API_CONSUMER_CODE_REQUIRED")
    if not str(grant.api_code or "").strip():
        raise ApiFactoryContractError("API_CONSUMER_API_CODE_REQUIRED")
    if not str(grant.api_version or "").strip():
        raise ApiFactoryContractError("API_CONSUMER_API_VERSION_REQUIRED")

    if (
        grant.status == ApiConsumerStatus.ACTIVE
        and not str(grant.credential_reference or "").strip()
    ):
        raise ApiFactoryContractError(
            "API_CONSUMER_CREDENTIAL_REFERENCE_REQUIRED"
        )

    if (
        grant.rate_limit_per_minute is not None
        and grant.rate_limit_per_minute <= 0
    ):
        raise ApiFactoryContractError("API_CONSUMER_RATE_LIMIT_INVALID")


def consumer_can_call(
    *,
    grant: ApiConsumerGrant,
    api: PublishedApiDefinition,
    requested_company_id: Optional[str],
    requested_unit_id: Optional[str],
) -> bool:
    validate_api_definition(api)
    validate_consumer_grant(grant)

    if api.status != ApiPublicationStatus.PUBLISHED:
        return False
    if grant.status != ApiConsumerStatus.ACTIVE:
        return False
    if grant.api_code != api.api_code or grant.api_version != api.version:
        return False
    if grant.auth_mode != api.auth_mode:
        return False

    if api.company_scope_required:
        if (
            not requested_company_id
            or requested_company_id not in set(grant.company_ids)
        ):
            return False

    if api.unit_scope_required:
        if (
            not requested_unit_id
            or requested_unit_id not in set(grant.unit_ids)
        ):
            return False

    return True
