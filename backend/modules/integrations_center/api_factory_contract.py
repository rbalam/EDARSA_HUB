"""Canonical API Factory contract for EDARSAHUB BOS.

This module defines published API metadata and validation rules only.
It does not expose SQL, create public routes, mint credentials, or bypass
domain services/RBAC. Published APIs must bind to canonical BOS capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Sequence


class ApiPublicationStatus(str, Enum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"


class ApiAuthMode(str, Enum):
    OAUTH2 = "OAUTH2"
    API_KEY = "API_KEY"
    SERVICE_TOKEN = "SERVICE_TOKEN"


@dataclass(frozen=True)
class ApiCapabilityBinding:
    domain: str
    capability: str
    operation: str
    homologation_required: bool = True


@dataclass(frozen=True)
class PublishedApiDefinition:
    api_code: str
    version: str
    route: str
    method: str
    status: ApiPublicationStatus
    auth_mode: ApiAuthMode
    bindings: Sequence[ApiCapabilityBinding] = field(default_factory=tuple)
    company_scope_required: bool = True
    unit_scope_required: bool = True
    rate_limit_per_minute: Optional[int] = None
    timezone: str = "America/Merida"
    currency: str = "MXN"
    locale: str = "es-MX"


class ApiFactoryContractError(ValueError):
    pass


def validate_api_definition(definition: PublishedApiDefinition) -> None:
    if not str(definition.api_code or "").strip():
        raise ApiFactoryContractError("API_CODE_REQUIRED")
    if not str(definition.version or "").strip():
        raise ApiFactoryContractError("API_VERSION_REQUIRED")

    route = str(definition.route or "").strip()
    if not route.startswith("/api/"):
        raise ApiFactoryContractError("API_ROUTE_MUST_BE_CANONICAL")

    method = str(definition.method or "").strip().upper()
    if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
        raise ApiFactoryContractError("API_METHOD_NOT_ALLOWED")

    if not definition.bindings:
        raise ApiFactoryContractError("API_CAPABILITY_BINDING_REQUIRED")

    for binding in definition.bindings:
        if not str(binding.domain or "").strip():
            raise ApiFactoryContractError("API_DOMAIN_REQUIRED")
        if not str(binding.capability or "").strip():
            raise ApiFactoryContractError("API_CAPABILITY_REQUIRED")
        if not str(binding.operation or "").strip():
            raise ApiFactoryContractError("API_OPERATION_REQUIRED")

    if (
        definition.rate_limit_per_minute is not None
        and definition.rate_limit_per_minute <= 0
    ):
        raise ApiFactoryContractError("API_RATE_LIMIT_INVALID")


def publication_requires_certified_homologation(
    definition: PublishedApiDefinition,
) -> bool:
    return any(binding.homologation_required for binding in definition.bindings)


def can_publish(
    *,
    definition: PublishedApiDefinition,
    approved: bool,
    rbac_allowed: bool,
    domain_homologation_certified: bool,
) -> bool:
    validate_api_definition(definition)

    if definition.status not in {
        ApiPublicationStatus.APPROVED,
        ApiPublicationStatus.PUBLISHED,
    }:
        return False
    if not approved or not rbac_allowed:
        return False
    if (
        publication_requires_certified_homologation(definition)
        and not domain_homologation_certified
    ):
        return False
    return True
