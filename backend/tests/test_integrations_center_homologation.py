from modules.integrations_center.homologation import (
    CertificationSource,
    DomainCertification,
    HomologationProfile,
    HomologationStatus,
    aggregate_domain_status,
    compatibility_status,
    compute_schema_fingerprint,
    empty_connection_homologation,
)


def _contract(host=None, company=None):
    return {
        "transport_type": "SQL_SERVER",
        "system_type": "SOFTRESTAURANT",
        "system_version": "8",
        "resources": [
            {
                "name": "ventas",
                "kind": "TABLE",
                "fields": [
                    {"name": "total", "type": "DECIMAL", "nullable": False},
                    {"name": "ticket", "type": "BIGINT", "nullable": False},
                ],
            }
        ],
        "capabilities": {"read": True, "sync": True},
    }


def test_fingerprint_is_reusable_across_connection_instances():
    first = compute_schema_fingerprint(**_contract(host="chapur-norte", company=1))
    second = compute_schema_fingerprint(**_contract(host="chapur-centro", company=2))
    assert first == second


def test_fingerprint_changes_when_contract_changes():
    original = _contract()
    changed = _contract()
    changed["resources"][0]["fields"].append(
        {"name": "impuesto", "type": "decimal", "nullable": True}
    )
    assert compute_schema_fingerprint(**original) != compute_schema_fingerprint(**changed)


def test_certified_profile_requires_matching_fingerprint():
    fingerprint = compute_schema_fingerprint(**_contract())
    profile = HomologationProfile(
        profile_id="softrestaurant-enterprise-v8",
        system_type="SOFTRESTAURANT",
        transport_type="SQL_SERVER",
        schema_fingerprint=fingerprint,
        status=HomologationStatus.CERTIFIED,
    )
    assert compatibility_status(
        profile=profile,
        observed_fingerprint=fingerprint,
    ) == HomologationStatus.CERTIFIED
    assert compatibility_status(
        profile=profile,
        observed_fingerprint="different",
    ) == HomologationStatus.REVALIDATION_REQUIRED


def test_domain_aggregation_is_fail_closed():
    domains = [
        DomainCertification("sales", HomologationStatus.CERTIFIED),
        DomainCertification("inventory", HomologationStatus.PENDING),
    ]
    assert aggregate_domain_status(domains) == HomologationStatus.PARTIAL

    blocked = domains + [
        DomainCertification("purchases", HomologationStatus.BLOCKED)
    ]
    assert aggregate_domain_status(blocked) == HomologationStatus.BLOCKED


def test_unbound_connection_is_never_implicitly_certified():
    value = empty_connection_homologation()
    assert value["status"] == "NOT_ASSESSED"
    assert value["profile_id"] is None
    assert value["certification_source"] is None


def test_reused_is_binding_source_not_profile_status():
    assert CertificationSource.REUSED.value == "REUSED"
    assert "REUSED_CERTIFICATION" not in {
        status.value for status in HomologationStatus
    }
