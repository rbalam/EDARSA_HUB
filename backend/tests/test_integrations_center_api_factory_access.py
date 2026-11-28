import pytest

from modules.integrations_center.api_factory_access import (
    ApiConsumerGrant,
    ApiConsumerStatus,
    PublishedApiVersion,
    consumer_can_call,
    validate_api_version,
    validate_consumer_grant,
)
from modules.integrations_center.api_factory_contract import (
    ApiAuthMode,
    ApiCapabilityBinding,
    ApiFactoryContractError,
    ApiPublicationStatus,
    PublishedApiDefinition,
)


def _api(status=ApiPublicationStatus.PUBLISHED):
    return PublishedApiDefinition(
        api_code="sales.daily",
        version="v1",
        route="/api/public/v1/sales/daily",
        method="GET",
        status=status,
        auth_mode=ApiAuthMode.SERVICE_TOKEN,
        bindings=(
            ApiCapabilityBinding(
                domain="sales",
                capability="READ",
                operation="daily_sales",
            ),
        ),
    )


def _grant(**overrides):
    values = {
        "consumer_code": "partner.demo",
        "api_code": "sales.daily",
        "api_version": "v1",
        "status": ApiConsumerStatus.ACTIVE,
        "auth_mode": ApiAuthMode.SERVICE_TOKEN,
        "credential_reference": "credential-ref-demo",
        "company_ids": ("company-a",),
        "unit_ids": ("unit-a",),
        "rate_limit_per_minute": 30,
    }
    values.update(overrides)
    return ApiConsumerGrant(**values)


def test_published_version_must_be_immutable_and_fingerprinted():
    validate_api_version(
        PublishedApiVersion(
            api_code="sales.daily",
            version="v1",
            contract_fingerprint="a" * 64,
        )
    )


def test_mutable_published_version_is_rejected():
    with pytest.raises(
        ApiFactoryContractError,
        match="PUBLISHED_API_VERSION_MUST_BE_IMMUTABLE",
    ):
        validate_api_version(
            PublishedApiVersion(
                api_code="sales.daily",
                version="v1",
                contract_fingerprint="a" * 64,
                immutable=False,
            )
        )


def test_active_consumer_requires_credential_reference():
    with pytest.raises(
        ApiFactoryContractError,
        match="API_CONSUMER_CREDENTIAL_REFERENCE_REQUIRED",
    ):
        validate_consumer_grant(_grant(credential_reference=None))


def test_consumer_scope_is_company_and_unit_fail_closed():
    assert consumer_can_call(
        grant=_grant(),
        api=_api(),
        requested_company_id="company-a",
        requested_unit_id="unit-a",
    )
    assert not consumer_can_call(
        grant=_grant(),
        api=_api(),
        requested_company_id="company-b",
        requested_unit_id="unit-a",
    )
    assert not consumer_can_call(
        grant=_grant(),
        api=_api(),
        requested_company_id="company-a",
        requested_unit_id="unit-b",
    )


def test_suspended_consumer_cannot_call():
    assert not consumer_can_call(
        grant=_grant(status=ApiConsumerStatus.SUSPENDED),
        api=_api(),
        requested_company_id="company-a",
        requested_unit_id="unit-a",
    )


def test_consumer_cannot_call_non_published_api():
    assert not consumer_can_call(
        grant=_grant(),
        api=_api(status=ApiPublicationStatus.APPROVED),
        requested_company_id="company-a",
        requested_unit_id="unit-a",
    )
