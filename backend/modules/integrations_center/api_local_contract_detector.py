"""Canonical detector for API_LOCAL query transports.

The fingerprint describes the reusable transport contract, not a concrete
installation. Host, port, API key, company, unit and branch identifiers are
excluded deliberately.
"""

from __future__ import annotations

from urllib.parse import urlparse
from typing import Any, Dict, Mapping, Optional

from .homologation import canonical_contract_payload, compute_schema_fingerprint


API_LOCAL_SQL_QUERY_CONTRACT_VERSION = "API_LOCAL_SQL_QUERY_V1"


def api_local_contract_payload(
    *,
    api_url: str,
    system_type: str,
    system_version: Optional[str],
    capabilities: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    parsed = urlparse(str(api_url or "").strip())
    path = parsed.path or "/"
    if not path.startswith("/"):
        path = "/" + path

    resources = [
        {
            "name": path,
            "kind": "HTTP_ENDPOINT",
            "fields": [
                {"name": "method", "type": "GET", "nullable": False},
                {"name": "query_param", "type": "sql", "nullable": False},
                {"name": "auth_header", "type": "X-API-Key", "nullable": False},
                {"name": "response", "type": "data:list[object]", "nullable": False},
            ],
        }
    ]

    merged_capabilities = {
        "read": True,
        "readonly_sql": True,
        "transport": "API_LOCAL",
        "contract_version": API_LOCAL_SQL_QUERY_CONTRACT_VERSION,
    }
    merged_capabilities.update(dict(capabilities or {}))

    return canonical_contract_payload(
        transport_type="API_LOCAL",
        system_type=system_type,
        system_version=system_version,
        resources=resources,
        capabilities=merged_capabilities,
    )


def detect_api_local_contract(
    *,
    api_url: str,
    system_type: str,
    system_version: Optional[str],
    capabilities: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    contract = api_local_contract_payload(
        api_url=api_url,
        system_type=system_type,
        system_version=system_version,
        capabilities=capabilities,
    )
    return {
        "status": "DETECTED",
        "transport_type": contract["transport_type"],
        "system_type": contract["system_type"],
        "system_version": contract["system_version"],
        "schema_fingerprint": compute_schema_fingerprint(**contract),
        "resource_count": len(contract["resources"]),
        "contract": contract,
        "evidence_source": "CANONICAL_API_LOCAL_ADAPTER_CONTRACT",
    }
