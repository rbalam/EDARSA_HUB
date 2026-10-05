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
