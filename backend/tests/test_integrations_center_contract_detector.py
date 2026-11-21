import pytest

from modules.integrations_center.contract_detector import (
    SQLSERVER_SCHEMA_QUERY_NAME,
    detect_sqlserver_contract,
    sqlserver_contract_from_evidence,
    sqlserver_readonly_query_plan,
)


def _evidence():
    return [
        {
            "name": SQLSERVER_SCHEMA_QUERY_NAME,
            "columns": [
                "table_schema",
                "table_name",
                "column_name",
                "data_type",
                "is_nullable",
                "ordinal_position",
            ],
            "rows": [
                ["dbo", "ventas", "ticket", "bigint", "NO", 1],
                ["dbo", "ventas", "total", "decimal", "NO", 2],
            ],
        }
    ]


def test_metadata_plan_is_select_only_and_bounded():
    plan = sqlserver_readonly_query_plan()
    assert {item["name"] for item in plan} == {SQLSERVER_SCHEMA_QUERY_NAME}
    for item in plan:
        query = item["sql"].strip().upper()
        assert query.startswith("SELECT")
        assert "INFORMATION_SCHEMA." in query
        assert "INSERT " not in query
        assert "UPDATE " not in query
        assert "DELETE " not in query


def test_fingerprint_is_stable_when_evidence_order_changes():
    first = _evidence()
    second = _evidence()
    second[0]["rows"] = list(reversed(second[0]["rows"]))

    assert detect_sqlserver_contract(
        system_type="SOFTRESTAURANT",
        system_version="8",
        evidence=first,
    )["schema_fingerprint"] == detect_sqlserver_contract(
        system_type="SOFTRESTAURANT",
        system_version="8",
        evidence=second,
    )["schema_fingerprint"]


def test_fingerprint_changes_when_schema_changes():
    first = _evidence()
    second = _evidence()
    second[0]["rows"].append(
        ["dbo", "ventas", "impuesto", "decimal", "YES", 3]
    )

    assert detect_sqlserver_contract(
        system_type="SOFTRESTAURANT",
        system_version="8",
        evidence=first,
    )["schema_fingerprint"] != detect_sqlserver_contract(
        system_type="SOFTRESTAURANT",
        system_version="8",
        evidence=second,
    )["schema_fingerprint"]


def test_detector_fails_closed_without_required_evidence():
    evidence = _evidence()
    evidence[0]["rows"] = []
    with pytest.raises(ValueError, match="SCHEMA_EVIDENCE_EMPTY"):
        sqlserver_contract_from_evidence(
            system_type="SOFTRESTAURANT",
            system_version="8",
            evidence=evidence,
        )


def test_detector_does_not_depend_on_connection_identity():
    contract = sqlserver_contract_from_evidence(
        system_type="SOFTRESTAURANT",
        system_version="8",
        evidence=_evidence(),
    )
    assert "host" not in contract
    assert "server_id" not in contract
    assert "empresa_id" not in contract
    assert "unidad_negocio_id" not in contract
