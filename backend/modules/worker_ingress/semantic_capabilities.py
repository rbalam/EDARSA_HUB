"""Registered semantic capabilities for the remote Worker ingress.

The public semantic boundary never accepts raw Worker actions/checks. Each
capability expands an objective into one deterministic Worker request.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping


class SemanticCapabilityError(ValueError):
    pass


@dataclass(frozen=True)
class SemanticCapability:
    code: str
    modes: tuple[str, ...]
    builder: Callable[[Mapping[str, Any]], dict[str, Any]]


_CAPABILITIES: dict[str, SemanticCapability] = {}


def register_capability(capability: SemanticCapability) -> None:
    code = str(capability.code or "").strip().upper()
    if not code:
        raise SemanticCapabilityError("SEMANTIC_CAPABILITY_CODE_REQUIRED")
    if code in _CAPABILITIES:
        raise SemanticCapabilityError("SEMANTIC_CAPABILITY_DUPLICATE")
    if not capability.modes:
        raise SemanticCapabilityError("SEMANTIC_CAPABILITY_MODE_REQUIRED")
    _CAPABILITIES[code] = capability


def registered_capabilities() -> tuple[str, ...]:
    return tuple(sorted(_CAPABILITIES))


def resolve_capability(code: str) -> SemanticCapability:
    value = str(code or "").strip().upper()
    capability = _CAPABILITIES.get(value)
    if capability is None:
        raise SemanticCapabilityError("SEMANTIC_CAPABILITY_UNKNOWN")
    return capability


def _read_only_canary_builder(request: Mapping[str, Any]) -> dict[str, Any]:
    constraints = request.get("constraints")
    constraints = dict(constraints) if isinstance(constraints, Mapping) else {}
    if constraints:
        unknown = sorted(constraints)
        raise SemanticCapabilityError(
            "SEMANTIC_CONSTRAINTS_UNSUPPORTED:" + ",".join(unknown)
        )

    bounded_context = str(request.get("bounded_context") or "").strip().upper()
    return {
        "actions": [],
        "checks": [{"type": "git_diff_check"}],
        "scheduling": {
            "project_id": "EDARSAHUB",
            "bounded_context": bounded_context,
            "priority_class": "NORMAL",
            "fairness_weight": 1,
            "max_parallelism": 1,
            "resource_claims": [],
            "conflict_domains": [bounded_context],
        },
    }


register_capability(
    SemanticCapability(
        code="READ_ONLY_CANARY",
        modes=("READ_ONLY",),
        builder=_read_only_canary_builder,
    )
)

# Bounded repository inspection only. No caller-supplied paths, search terms,
# actions or checks cross the semantic boundary.
_RH_OFFBOARDING_AUDIT_REQUEST = {
    "paths": ["backend/modules", "frontend/src", "tools/mirror_sync"],
    "search_terms": [
        "finiquito", "liquidacion", "liquidación", "baja", "offboarding",
        "nomina", "nómina", "payroll", "clearance", "entrega de equipo",
        "desvinculacion", "desvinculación", "prestaciones",
    ],
    "max_results": 200,
}


def _repository_contract_audit_builder(request: Mapping[str, Any]) -> dict[str, Any]:
    constraints = request.get("constraints")
    if constraints is not None and (
        not isinstance(constraints, Mapping) or bool(constraints)
    ):
        raise SemanticCapabilityError("SEMANTIC_CONSTRAINTS_UNSUPPORTED")
    bounded_context = str(request.get("bounded_context") or "").strip().upper()
    if bounded_context != "RH":
        raise SemanticCapabilityError("SEMANTIC_BOUNDED_CONTEXT_UNSUPPORTED")
    return {
        "actions": [],
        "checks": [
            {
                "type": "repository_contract_audit",
                "request": {
                    **_RH_OFFBOARDING_AUDIT_REQUEST,
                    "paths": list(_RH_OFFBOARDING_AUDIT_REQUEST["paths"]),
                    "search_terms": list(_RH_OFFBOARDING_AUDIT_REQUEST["search_terms"]),
                },
            },
        ],
        "scheduling": {
            "project_id": "EDARSAHUB",
            "bounded_context": bounded_context,
            "priority_class": "NORMAL",
            "fairness_weight": 1,
            "max_parallelism": 1,
            "resource_claims": [],
            "conflict_domains": [bounded_context],
        },
    }


register_capability(
    SemanticCapability(
        code="REPOSITORY_CONTRACT_AUDIT",
        modes=("READ_ONLY",),
        builder=_repository_contract_audit_builder,
    )
)
