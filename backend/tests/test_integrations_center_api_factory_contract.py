import pytest

from modules.integrations_center.api_factory_contract import (
    ApiAuthMode,
    ApiCapabilityBinding,
    ApiFactoryContractError,
    ApiPublicationStatus,
    PublishedApiDefinition,
    can_publish,
    validate_api_definition,
)


def _definition(**overrides):
    values = {
        "api_code": "sales.daily",
        "version": "v1",
        "route": "/api/public/v1/sales/daily",
        "method": "GET",
        "status": ApiPublicationStatus.APPROVED,
        "auth_mode": ApiAuthMode.SERVICE_TOKEN,
        "bindings": (
            ApiCapabilityBinding(
                domain="sales",
                capability="READ",
                operation="daily_sales",
            ),
        ),
        "rate_limit_per_minute": 60,
    }
    values.update(overrides)
    return PublishedApiDefinition(**values)


def test_valid_definition_uses_bos_capability_binding():
    validate_api_definition(_definition())


def test_api_cannot_publish_without_capability_binding():
    with pytest.raises(
        ApiFactoryContractError,
        match="API_CAPABILITY_BINDING_REQUIRED",
    ):
        validate_api_definition(_definition(bindings=()))


def test_api_cannot_publish_without_certified_domain_homologation():
    assert not can_publish(
        definition=_definition(),
        approved=True,
        rbac_allowed=True,
        domain_homologation_certified=False,
    )


def test_api_cannot_publish_without_rbac():
    assert not can_publish(
        definition=_definition(),
        approved=True,
        rbac_allowed=False,
        domain_homologation_certified=True,
    )


def test_approved_api_can_publish_when_all_guards_pass():
    assert can_publish(
        definition=_definition(),
        approved=True,
        rbac_allowed=True,
        domain_homologation_certified=True,
    )


def test_draft_is_not_publishable_even_when_other_guards_pass():
    assert not can_publish(
        definition=_definition(status=ApiPublicationStatus.DRAFT),
        approved=True,
        rbac_allowed=True,
        domain_homologation_certified=True,
    )
