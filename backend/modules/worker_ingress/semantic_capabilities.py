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
    builder: Callable[[Mapping[str, Any]], dict[str, Any]] | None = None
    submitter: Callable[
        [Mapping[str, Any], Mapping[str, Any]],
        dict[str, Any],
    ] | None = None


_CAPABILITIES: dict[str, SemanticCapability] = {}


def register_capability(capability: SemanticCapability) -> None:
    code = str(capability.code or "").strip().upper()
    if not code:
        raise SemanticCapabilityError("SEMANTIC_CAPABILITY_CODE_REQUIRED")
    if code in _CAPABILITIES:
        raise SemanticCapabilityError("SEMANTIC_CAPABILITY_DUPLICATE")
    if not capability.modes:
        raise SemanticCapabilityError("SEMANTIC_CAPABILITY_MODE_REQUIRED")
    if (capability.builder is None) == (capability.submitter is None):
        raise SemanticCapabilityError("SEMANTIC_CAPABILITY_HANDLER_INVALID")
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


# G3 - Additional bounded semantic READ_ONLY capabilities.
import re as _g3_re

_G3_JOB_ID = _g3_re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$")
_G3_TERM = _g3_re.compile(r"^[A-Za-z0-9_.-]{2,64}$")
_G3_PATH = _g3_re.compile(r"^[A-Za-z0-9_./-]+$")
_G3_ROOTS = (
    "backend/modules/",
    "backend/tests/",
    "frontend/src/",
    "tools/mirror_sync/",
)
_G3_DENIED = {
    ".git", ".env", ".venv", "venv",
    "node_modules", "__pycache__", "dist", "build",
}
_G3_SENSITIVE = (
    "secret", "credential", "password", "token",
    "private_key", "api_key",
)

def _g3_context(request):
    context = str(request.get("bounded_context") or "").strip().upper()
    if not _g3_re.fullmatch(r"[A-Z0-9][A-Z0-9._-]{1,119}", context):
        raise SemanticCapabilityError("SEMANTIC_CONTEXT_INVALID")
    return context

def _g3_constraints(request, allowed):
    value = request.get("constraints")
    if not isinstance(value, Mapping):
        raise SemanticCapabilityError("SEMANTIC_CONSTRAINTS_INVALID")
    if set(value) - set(allowed):
        raise SemanticCapabilityError("SEMANTIC_CONSTRAINTS_UNSUPPORTED")
    return dict(value)

def _g3_scheduling(context):
    return {
        "project_id": "EDARSAHUB",
        "bounded_context": context,
        "priority_class": "NORMAL",
        "fairness_weight": 1,
        "max_parallelism": 1,
        "resource_claims": [],
        "conflict_domains": [context],
    }

def _g3_repository_builder(request):
    context = _g3_context(request)
    c = _g3_constraints(
        request, {"paths", "search_terms", "max_results"}
    )
    paths = c.get("paths")
    terms = c.get("search_terms")
    limit = c.get("max_results", 100)

    if not isinstance(paths, list) or not 1 <= len(paths) <= 20:
        raise SemanticCapabilityError("SEMANTIC_PATHS_INVALID")
    if not isinstance(terms, list) or not 1 <= len(terms) <= 20:
        raise SemanticCapabilityError("SEMANTIC_TERMS_INVALID")
    if type(limit) is not int or not 1 <= limit <= 100:
        raise SemanticCapabilityError("SEMANTIC_LIMIT_INVALID")

    for value in paths:
        if not isinstance(value, str) or not _G3_PATH.fullmatch(value):
            raise SemanticCapabilityError("SEMANTIC_PATH_INVALID")

        # Directory paths ending in / are valid.
        parts = value.rstrip("/").split("/")

        if (
            not value.startswith(_G3_ROOTS)
            or any(p in ("", ".", "..") for p in parts)
            or any(p in _G3_DENIED for p in parts)
            or any(
                marker in p.lower()
                for p in parts
                for marker in _G3_SENSITIVE
            )
        ):
            raise SemanticCapabilityError("SEMANTIC_PATH_FORBIDDEN")

    if any(
        not isinstance(t, str) or not _G3_TERM.fullmatch(t)
        for t in terms
    ):
        raise SemanticCapabilityError("SEMANTIC_TERMS_INVALID")

    return {
        "actions": [],
        "checks": [{
            "type": "repository_contract_audit",
            "request": {
                "paths": paths,
                "search_terms": terms,
                "max_results": limit,
            },
        }],
        "scheduling": _g3_scheduling(context),
    }

def _g3_result_builder(request):
    context = _g3_context(request)
    c = _g3_constraints(request, {"source_job_id"})
    job_id = c.get("source_job_id")

    if not isinstance(job_id, str) or not _G3_JOB_ID.fullmatch(job_id):
        raise SemanticCapabilityError("SEMANTIC_SOURCE_JOB_INVALID")

    return {
        "actions": [],
        "checks": [{
            "type": "worker_result_semantic_extract",
            "request": {
                "source_result": {
                    "branch": "worker/results",
                    "path": (
                        "worker_queue/results/"
                        + job_id + ".json"
                    ),
                },
            },
        }],
        "scheduling": _g3_scheduling(context),
    }

register_capability(
    SemanticCapability(
        code="REPOSITORY_CONTRACT_AUDIT_BOUNDED",
        modes=("READ_ONLY",),
        builder=_g3_repository_builder,
    )
)

register_capability(
    SemanticCapability(
        code="WORKER_RESULT_SEMANTIC_EXTRACT",
        modes=("READ_ONLY",),
        builder=_g3_result_builder,
    )
)


# D2.2 - Bounded Worker Repair semantic mutation boundary.
# The caller never provides Worker actions/checks/paths. The declared
# Maintenance incident and registered Repair capability own the mutation scope.
_WORKER_REPAIR_CONTEXT = "WORKER_RUNTIME_CONVERGENCE"
_WORKER_REPAIR_CODE = _g3_re.compile(r"^[A-Z0-9][A-Z0-9._-]{2,120}$")


def _worker_repair_bounded_submitter(
    request: Mapping[str, Any],
    requester: Mapping[str, Any],
) -> dict[str, Any]:
    context = _g3_context(request)
    if context != _WORKER_REPAIR_CONTEXT:
        raise SemanticCapabilityError("SEMANTIC_BOUNDED_CONTEXT_UNSUPPORTED")

    c = _g3_constraints(
        request,
        {"incident_id", "capability_code"},
    )
    incident_id = c.get("incident_id")
    capability_code = c.get("capability_code")

    if (
        not isinstance(incident_id, str)
        or not _G3_JOB_ID.fullmatch(incident_id)
    ):
        raise SemanticCapabilityError("SEMANTIC_INCIDENT_ID_INVALID")
    if (
        not isinstance(capability_code, str)
        or not _WORKER_REPAIR_CODE.fullmatch(capability_code.upper())
    ):
        raise SemanticCapabilityError("SEMANTIC_REPAIR_CAPABILITY_INVALID")

    from tools.mirror_sync import worker_repair_planner

    try:
        result = worker_repair_planner.publish_planned_repair(
            incident_id,
            capability_code=capability_code.upper(),
            requester=dict(requester),
        )
    except ValueError as exc:
        raise SemanticCapabilityError(str(exc)) from exc

    if not isinstance(result, dict):
        raise SemanticCapabilityError("SEMANTIC_REPAIR_INVALID_RESPONSE")
    if result.get("production_touched") is not False:
        raise SemanticCapabilityError("SEMANTIC_REPAIR_PRODUCTION_POLICY_VIOLATION")
    return result


register_capability(
    SemanticCapability(
        code="WORKER_REPAIR_BOUNDED",
        modes=("MUTATION",),
        submitter=_worker_repair_bounded_submitter,
    )
)


# Knowledge Loop - bounded local Worker failure evidence.
# The semantic caller supplies only a canonical source_job_id.
def _worker_result_detail_builder(request):
    context = _g3_context(request)

    c = _g3_constraints(
        request,
        {"source_job_id"},
    )

    job_id = c.get("source_job_id")

    if (
        not isinstance(job_id, str)
        or not _G3_JOB_ID.fullmatch(job_id)
    ):
        raise SemanticCapabilityError(
            "SEMANTIC_SOURCE_JOB_INVALID"
        )

    return {
        "actions": [],
        "checks": [
            {
                "type": "worker_result_detail_read",
                "request": {
                    "job_id": job_id,
                },
            },
        ],
        "scheduling": _g3_scheduling(
            context
        ),
    }


register_capability(
    SemanticCapability(
        code="WORKER_RESULT_DETAIL_READ",
        modes=("READ_ONLY",),
        builder=_worker_result_detail_builder,
    )
)

# G4 Maintenance history: expose only the already-registered, bounded,
# sanitizing Worker check. No caller-supplied paths, actions or checks.
def _maintenance_history_readonly_builder(request: Mapping[str, Any]) -> dict[str, Any]:
    context = str(request.get("bounded_context") or "").strip().upper()
    if context != "WORKER_REPAIR_KNOWLEDGE_LOOP":
        raise SemanticCapabilityError("SEMANTIC_BOUNDED_CONTEXT_UNSUPPORTED")

    constraints = request.get("constraints")
    if constraints is not None and (
        not isinstance(constraints, Mapping) or bool(constraints)
    ):
        raise SemanticCapabilityError("SEMANTIC_CONSTRAINTS_UNSUPPORTED")

    return {
        "actions": [],
        "checks": [{"type": "worker_maintenance_history_readonly"}],
        "scheduling": _g3_scheduling(context),
    }


register_capability(
    SemanticCapability(
        code="WORKER_MAINTENANCE_HISTORY_READONLY",
        modes=("READ_ONLY",),
        builder=_maintenance_history_readonly_builder,
    )
)

