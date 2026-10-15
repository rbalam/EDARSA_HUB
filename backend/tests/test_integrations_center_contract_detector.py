from modules.integrations_center.contract_detector import (
    ContractDetectionError,
    build_sql_server_contract,
    detect_sql_server_fingerprint,
    sql_server_metadata_plan,
)


def _evidence():
    return {
        "resources": [
            {
                "TABLE_SCHEMA": "dbo",
                "TABLE_NAME": "ventas",
                "TABLE_TYPE": "BASE TABLE",
            }
        ],
        "fields": [
            {
                "TABLE_SCHEMA": "dbo",
                "TABLE_NAME": "ventas",
                "COLUMN_NAME": "ticket",
                "DATA_TYPE": "bigint",
                "IS_NULLABLE": "NO",
                "ORDINAL_POSITION": 1,
            },
            {
                "TABLE_SCHEMA": "dbo",
                "TABLE_NAME": "ventas",
                "COLUMN_NAME": "total",
                "DATA_TYPE": "decimal",
                "IS_NULLABLE": "NO",
                "ORDINAL_POSITION": 2,
            },
        ],
    }


def test_metadata_plan_is_select_only_and_bounded():
    plan = sql_server_metadata_plan()
    assert {item["name"] for item in plan} == {"resources", "fields"}
    for item in plan:
        query = item["query"].strip().upper()
        assert query.startswith("SELECT")
        assert "INFORMATION_SCHEMA." in query
        assert "INSERT " not in query
        assert "UPDATE " not in query
        assert "DELETE " not in query


def test_fingerprint_is_stable_when_evidence_order_changes():
    first = _evidence()
    second = _evidence()
    second["fields"] = list(reversed(second["fields"]))

    assert detect_sql_server_fingerprint(
        system_type="SOFTRESTAURANT",
        system_version="8",
        evidence=first,
    ) == detect_sql_server_fingerprint(
        system_type="SOFTRESTAURANT",
        system_version="8",
        evidence=second,
    )


def test_fingerprint_changes_when_schema_changes():
    first = _evidence()
    second = _evidence()
    second["fields"].append(
        {
            "TABLE_SCHEMA": "dbo",
            "TABLE_NAME": "ventas",
            "COLUMN_NAME": "impuesto",
            "DATA_TYPE": "decimal",
            "IS_NULLABLE": "YES",
            "ORDINAL_POSITION": 3,
        }
    )

    assert detect_sql_server_fingerprint(
        system_type="SOFTRESTAURANT",
        system_version="8",
        evidence=first,
    ) != detect_sql_server_fingerprint(
        system_type="SOFTRESTAURANT",
        system_version="8",
        evidence=second,
    )


def test_detector_fails_closed_without_required_evidence():
    try:
        build_sql_server_contract(
            system_type="SOFTRESTAURANT",
            system_version="8",
            evidence={"resources": [], "fields": []},
        )
    except ContractDetectionError as exc:
        assert str(exc) == "SQL_SERVER_METADATA_EVIDENCE_REQUIRED"
    else:
        raise AssertionError("expected ContractDetectionError")


def test_detector_does_not_depend_on_connection_identity():
    evidence = _evidence()
    contract = build_sql_server_contract(
        system_type="SOFTRESTAURANT",
        system_version="8",
        evidence=evidence,
    )
    assert "host" not in contract
    assert "server_id" not in contract
    assert "empresa_id" not in contract
    assert "unidad_negocio_id" not in contract
