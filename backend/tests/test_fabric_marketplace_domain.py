import pytest
from modules.fabric_marketplace.domain import (
    Product, Release, Listing, Visibility, InstallationRequest,
)


def test_product_requires_owner():
    with pytest.raises(ValueError):
        Product("p", "publisher", "")


def test_release_binds_artifact_and_manifest():
    release = Release("r", "p", "1.0.0", "a" * 64, "b" * 64)
    assert release.product_id == "p"
    with pytest.raises(ValueError):
        Release("r", "p", "1.0.0", "invalid", "b" * 64)


def test_listing_requires_certification_reference():
    with pytest.raises(ValueError):
        Listing("p", "r", Visibility.PUBLIC, "")
    with pytest.raises(ValueError):
        Listing("p", "r", "UNKNOWN", "cert")
    assert Listing("p", "r", Visibility.PRIVATE, "cert").release_id == "r"


def test_installation_requires_entitlement_and_authorization():
    with pytest.raises(ValueError):
        InstallationRequest("r", "org", "", "auth")
    with pytest.raises(ValueError):
        InstallationRequest("r", "org", "entitlement", "")
    assert InstallationRequest("r", "org", "entitlement", "auth").organization_ref == "org"
