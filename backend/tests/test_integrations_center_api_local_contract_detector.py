from modules.integrations_center.api_local_contract_detector import (
    API_LOCAL_SQL_QUERY_CONTRACT_VERSION,
    api_local_contract_payload,
    detect_api_local_contract,
)


def test_chapur_instances_reuse_same_api_local_contract_fingerprint():
    backoffice = detect_api_local_contract(
        api_url="http://example.invalid:8009/query",
        system_type="ENTERPRISE",
        system_version="SIN_VERSION_DEFINIDA",
    )
    norte = detect_api_local_contract(
        api_url="http://example.invalid:8007/query",
        system_type="ENTERPRISE",
        system_version="SIN_VERSION_DEFINIDA",
    )

    assert backoffice["schema_fingerprint"] == norte["schema_fingerprint"]
    assert backoffice["contract"] == norte["contract"]


def test_api_local_contract_excludes_instance_identity():
    contract = api_local_contract_payload(
        api_url="http://example.invalid:8009/query",
        system_type="ENTERPRISE",
        system_version="SIN_VERSION_DEFINIDA",
    )
    serialized = repr(contract)

    assert "example.invalid" not in serialized
    assert "8009" not in serialized
    assert "api_key" not in serialized.lower()


def test_endpoint_contract_path_change_changes_fingerprint():
    first = detect_api_local_contract(
        api_url="http://example.invalid:8009/query",
        system_type="ENTERPRISE",
        system_version="SIN_VERSION_DEFINIDA",
    )
    second = detect_api_local_contract(
        api_url="http://example.invalid:8009/query-v2",
        system_type="ENTERPRISE",
        system_version="SIN_VERSION_DEFINIDA",
    )

    assert first["schema_fingerprint"] != second["schema_fingerprint"]


def test_contract_declares_readonly_sql_transport_capability():
    detected = detect_api_local_contract(
        api_url="http://example.invalid/query",
        system_type="ENTERPRISE",
        system_version="SIN_VERSION_DEFINIDA",
    )

    assert detected["transport_type"] == "API_LOCAL"
    assert detected["contract"]["capabilities"]["readonly_sql"] is True
    assert API_LOCAL_SQL_QUERY_CONTRACT_VERSION in repr(detected["contract"])
