"""Canonical homologation contract for EDARSAHUB integrations.

This module is intentionally persistence-agnostic. It defines the states,
versioned profile shape, deterministic fingerprinting rules, and aggregate
status semantics used by Integrations Center and future API Factory adapters.

No connection is considered certified merely because its vendor/system name
matches a previously known product.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence


class HomologationStatus(str, Enum):
    NOT_ASSESSED = "NOT_ASSESSED"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    PARTIAL = "PARTIAL"
    CERTIFIED = "CERTIFIED"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class CertificationSource(str, Enum):
    DIRECT = "DIRECT"
    REUSED = "REUSED"


@dataclass(frozen=True)
class DomainCertification:
    domain: str
    status: HomologationStatus
    source_contract_version: Optional[str] = None
    edarsahub_contract_version: Optional[str] = None
    certified_at_utc: Optional[str] = None
    certified_by: Optional[str] = None


@dataclass(frozen=True)
class HomologationProfile:
    profile_id: str
    system_type: str
    transport_type: str
    schema_fingerprint: str
    source_contract_version: Optional[str] = None
    edarsahub_contract_version: Optional[str] = None
    status: HomologationStatus = HomologationStatus.NOT_ASSESSED
    domains: Sequence[DomainCertification] = field(default_factory=tuple)
    certified_at_utc: Optional[str] = None
    certified_by: Optional[str] = None
    last_validated_at_utc: Optional[str] = None


def aggregate_domain_status(
    domains: Iterable[DomainCertification],
) -> HomologationStatus:
    items = list(domains)
    if not items:
        return HomologationStatus.NOT_ASSESSED

    statuses = {item.status for item in items}

    if HomologationStatus.BLOCKED in statuses:
        return HomologationStatus.BLOCKED
    if HomologationStatus.REVALIDATION_REQUIRED in statuses:
        return HomologationStatus.REVALIDATION_REQUIRED

    relevant = {
        item.status
        for item in items
        if item.status != HomologationStatus.NOT_APPLICABLE
    }
    if not relevant:
        return HomologationStatus.NOT_APPLICABLE
    if relevant == {HomologationStatus.CERTIFIED}:
        return HomologationStatus.CERTIFIED
    if HomologationStatus.IN_PROGRESS in relevant:
        return HomologationStatus.IN_PROGRESS
    if HomologationStatus.CERTIFIED in relevant:
        return HomologationStatus.PARTIAL
    if HomologationStatus.PENDING in relevant:
        return HomologationStatus.PENDING
    if HomologationStatus.PARTIAL in relevant:
        return HomologationStatus.PARTIAL
    return HomologationStatus.NOT_ASSESSED


def canonical_contract_payload(
    *,
    transport_type: str,
    system_type: str,
    system_version: Optional[str],
    resources: Sequence[Mapping[str, Any]],
    capabilities: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Return the normalized contract used to compute a reusable fingerprint.

    Hostname, credentials, company, unit, and branch identifiers are
    deliberately excluded because they identify a connection instance rather
    than the reusable source contract.
    """

    normalized_resources = []
    for resource in resources:
        fields = resource.get("fields") or []
        normalized_fields = sorted(
            [
                {
                    "name": str(field.get("name") or "").strip(),
                    "type": str(field.get("type") or "").strip().lower(),
                    "nullable": bool(field.get("nullable", True)),
                }
                for field in fields
            ],
            key=lambda item: (item["name"], item["type"]),
        )
        normalized_resources.append(
            {
                "name": str(resource.get("name") or "").strip(),
                "kind": str(resource.get("kind") or "").strip().upper(),
                "fields": normalized_fields,
            }
        )

    normalized_resources.sort(key=lambda item: (item["kind"], item["name"]))

    normalized_capabilities = {
        str(key): value
        for key, value in sorted((capabilities or {}).items())
    }

    return {
        "transport_type": str(transport_type or "").strip().upper(),
        "system_type": str(system_type or "").strip().upper(),
        "system_version": str(system_version or "").strip() or None,
        "resources": normalized_resources,
        "capabilities": normalized_capabilities,
    }


def compute_schema_fingerprint(**contract: Any) -> str:
    payload = canonical_contract_payload(**contract)
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compatibility_status(
    *,
    profile: HomologationProfile,
    observed_fingerprint: str,
) -> HomologationStatus:
    if profile.status != HomologationStatus.CERTIFIED:
        return profile.status

    if not observed_fingerprint:
        return HomologationStatus.REVALIDATION_REQUIRED

    if observed_fingerprint != profile.schema_fingerprint:
        return HomologationStatus.REVALIDATION_REQUIRED

    return HomologationStatus.CERTIFIED


def empty_connection_homologation() -> Dict[str, Any]:
    return {
        "status": HomologationStatus.NOT_ASSESSED.value,
        "profile_id": None,
        "certification_source": None,
        "schema_fingerprint": None,
        "source_contract_version": None,
        "edarsahub_contract_version": None,
        "last_validated_at_utc": None,
        "domains": [],
    }
