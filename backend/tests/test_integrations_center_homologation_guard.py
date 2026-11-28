import pytest

from modules.integrations_center.homologation import HomologationStatus
from modules.integrations_center.homologation_guard import (
    HomologationGuardError,
    domain_homologation_status,
    require_certified_domain,
)


def _state(domain_status="CERTIFIED", overall="CERTIFIED"):
    return {
        "status": overall,
        "domains": [
            {"domain": "sales", "status": domain_status},
            {"domain": "inventory", "status": "PENDING"},
        ],
    }


def test_certified_domain_is_allowed():
    require_certified_domain(_state(), "sales")


def test_global_certification_does_not_authorize_pending_domain():
    with pytest.raises(
        HomologationGuardError,
        match="HOMOLOGATION_DOMAIN_NOT_CERTIFIED:inventory:PENDING",
    ):
        require_certified_domain(_state(), "inventory")


def test_unknown_domain_fails_closed():
    assert (
        domain_homologation_status(_state(), "recipes")
        == HomologationStatus.NOT_ASSESSED
    )


def test_non_certified_binding_fails_closed_even_if_domain_says_certified():
    assert (
        domain_homologation_status(
            _state(overall="REVALIDATION_REQUIRED"),
            "sales",
        )
        == HomologationStatus.NOT_ASSESSED
    )


def test_missing_domain_name_is_rejected():
    with pytest.raises(
        HomologationGuardError,
        match="HOMOLOGATION_DOMAIN_REQUIRED",
    ):
        require_certified_domain(_state(), "")
