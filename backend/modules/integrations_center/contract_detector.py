"""Observed-contract detector for homologation.

This module never opens external connections by itself. It defines the
read-only metadata query plan and converts already-collected evidence into the
canonical contract consumed by homologation.compute_schema_fingerprint.

Execution of the query plan belongs to a controlled worker/audit flow using the
existing sql_readonly_audit + canonical connection resolver. Opening
Integrations Center must never trigger an external/live schema probe.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Sequence

from .homologation import (
    canonical_contract_payload,
    compute_schema_fingerprint,
)


SQLSERVER_SCHEMA_QUERY_NAME = "homologation_sqlserver_schema"

SQLSERVER_SCHEMA_QUERY = """
SELECT
    TABLE_SCHEMA AS table_schema,
    TABLE_NAME AS table_name,
    COLUMN_NAME AS column_name,
    DATA_TYPE AS data_type,
    IS_NULLABLE AS is_nullable,
    ORDINAL_POSITION AS ordinal_position
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA NOT IN ('sys', 'INFORMATION_SCHEMA')
ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
""".strip()


def sqlserver_readonly_query_plan() -> List[Dict[str, str]]:
    return [
        {
            "name": SQLSERVER_SCHEMA_QUERY_NAME,
            "sql": SQLSERVER_SCHEMA_QUERY,
        }
    ]


def _rows_from_evidence(
    evidence: Sequence[Mapping[str, Any]],
    query_name: str,
) -> List[Dict[str, Any]]:
    match = next(
        (
            item
            for item in evidence
            if str(item.get("name") or "").strip() == query_name
        ),
        None,
    )
    if not match:
        raise ValueError("SCHEMA_EVIDENCE_NOT_FOUND")

    columns = [str(value) for value in (match.get("columns") or [])]
    rows = match.get("rows") or []

    if not columns:
        raise ValueError("SCHEMA_EVIDENCE_COLUMNS_REQUIRED")

    normalized: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, (list, tuple)):
            raise ValueError("SCHEMA_EVIDENCE_ROW_INVALID")
        if len(row) != len(columns):
            raise ValueError("SCHEMA_EVIDENCE_SHAPE_MISMATCH")
        normalized.append(dict(zip(columns, row)))

    return normalized


def sqlserver_contract_from_evidence(
    *,
    evidence: Sequence[Mapping[str, Any]],
    system_type: str,
    system_version: str | None = None,
    capabilities: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    rows = _rows_from_evidence(
        evidence,
        SQLSERVER_SCHEMA_QUERY_NAME,
    )

    resources_by_name: Dict[str, Dict[str, Any]] = {}

    for row in rows:
        schema = str(row.get("table_schema") or "").strip()
        table = str(row.get("table_name") or "").strip()
        column = str(row.get("column_name") or "").strip()
        data_type = str(row.get("data_type") or "").strip().lower()

        if not table or not column or not data_type:
            raise ValueError("SCHEMA_EVIDENCE_REQUIRED_VALUE_MISSING")

        resource_name = f"{schema}.{table}" if schema else table
        resource = resources_by_name.setdefault(
            resource_name,
            {
                "name": resource_name,
                "kind": "TABLE",
                "fields": [],
            },
        )
        resource["fields"].append(
            {
                "name": column,
                "type": data_type,
                "nullable": (
                    str(row.get("is_nullable") or "").strip().upper()
                    != "NO"
                ),
            }
        )

    if not resources_by_name:
        raise ValueError("SCHEMA_EVIDENCE_EMPTY")

    return canonical_contract_payload(
        transport_type="SQL_SERVER",
        system_type=system_type,
        system_version=system_version,
        resources=list(resources_by_name.values()),
        capabilities=capabilities or {"read": True},
    )


def detect_sqlserver_contract(
    *,
    evidence: Sequence[Mapping[str, Any]],
    system_type: str,
    system_version: str | None = None,
    capabilities: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    contract = sqlserver_contract_from_evidence(
        evidence=evidence,
        system_type=system_type,
        system_version=system_version,
        capabilities=capabilities,
    )
    fingerprint = compute_schema_fingerprint(**contract)
    return {
        "status": "DETECTED",
        "transport_type": contract["transport_type"],
        "system_type": contract["system_type"],
        "system_version": contract["system_version"],
        "schema_fingerprint": fingerprint,
        "resource_count": len(contract["resources"]),
        "contract": contract,
        "evidence_source": "CONTROLLED_READ_ONLY_AUDIT",
    }


def empty_detection_state() -> Dict[str, Any]:
    return {
        "status": "NOT_RUN",
        "schema_fingerprint": None,
        "evidence_source": None,
        "execution_policy": "CONTROLLED_READ_ONLY_WORKER_ONLY",
    }
