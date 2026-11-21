from modules.integrations_center.homologation import (
    DomainCertification,
    HomologationProfile,
    HomologationStatus,
)
from modules.integrations_center.homologation_binding import (
    resolve_homologation_binding,
)


def _profile(profile_id="sr-v8", fingerprint="abc", status=HomologationStatus.CERTIFIED):
    return HomologationProfile(
        profile_id=profile_id,
        system_type="SOFTRESTAURANT",
        transport_type="SQL_SERVER",
        schema_fingerprint=fingerprint,
        source_contract_version="8",
        edarsahub_contract_version="sales-v1",
        status=status,
        domains=(
            DomainCertification("sales", HomologationStatus.CERTIFIED),
        ),
    )


def test_exact_certified_profile_is_reused():
    result = resolve_homologation_binding(
        system_type="softrestaurant",
        transport_type="sql_server",
        observed_fingerprint="abc",
        profiles=[_profile()],
    )
    assert result["status"] == "CERTIFIED"
    assert result["profile_id"] == "sr-v8"
    assert result["certification_source"] == "REUSED"


def test_known_system_without_profile_is_pending_not_certified():
    result = resolve_homologation_binding(
        system_type="SOFTRESTAURANT",
        transport_type="SQL_SERVER",
        observed_fingerprint="abc",
        profiles=[],
    )
    assert result["status"] == "PENDING"
    assert result["profile_id"] is None


def test_changed_schema_requires_revalidation():
    result = resolve_homologation_binding(
        system_type="SOFTRESTAURANT",
        transport_type="SQL_SERVER",
        observed_fingerprint="changed",
        profiles=[_profile()],
    )
    assert result["status"] == "REVALIDATION_REQUIRED"
    assert result["profile_id"] is None


def test_missing_observed_fingerprint_never_reuses_certification():
    result = resolve_homologation_binding(
        system_type="SOFTRESTAURANT",
        transport_type="SQL_SERVER",
        observed_fingerprint=None,
        profiles=[_profile()],
    )
    assert result["status"] == "REVALIDATION_REQUIRED"
    assert result["certification_source"] is None


def test_ambiguous_exact_profiles_fail_closed():
    result = resolve_homologation_binding(
        system_type="SOFTRESTAURANT",
        transport_type="SQL_SERVER",
        observed_fingerprint="abc",
        profiles=[
            _profile("sr-v8-a"),
            _profile("sr-v8-b"),
        ],
    )
    assert result["status"] == "REVALIDATION_REQUIRED"
    assert result["profile_id"] is None


def test_non_certified_profile_cannot_be_reused():
    result = resolve_homologation_binding(
        system_type="SOFTRESTAURANT",
        transport_type="SQL_SERVER",
        observed_fingerprint="abc",
        profiles=[_profile(status=HomologationStatus.IN_PROGRESS)],
    )
    assert result["status"] == "IN_PROGRESS"
    assert result["profile_id"] is None
