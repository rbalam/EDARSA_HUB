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
        worker_repair_planner.declare_registered_incident(
            incident_id,
            capability_code=capability_code.upper(),
            requester=dict(requester),
        )
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


# Independent, fixed-target READ_ONLY pytest certification.
# No arbitrary paths, commands, actions or checks are accepted.
_WORKER_PYTEST_CONTEXT = "WORKER_REPAIR_KNOWLEDGE_LOOP"
_WORKER_PYTEST_TARGET = (
    "backend/tests/"
    "test_worker_repair_planner_canonical_ingress_capability.py"
)


def _worker_pytest_certification_readonly_builder(request):
    context = str(request.get("bounded_context") or "").strip().upper()

    if context != _WORKER_PYTEST_CONTEXT:
        raise SemanticCapabilityError(
            "SEMANTIC_BOUNDED_CONTEXT_UNSUPPORTED"
        )

    _g3_constraints(request, set())

    return {
        "actions": [],
        "checks": [
            {
                "type": "pytest",
                "paths": [_WORKER_PYTEST_TARGET],
            }
        ],
        "scheduling": _g3_scheduling(context),
    }


register_capability(
    SemanticCapability(
        code="WORKER_PYTEST_CERTIFICATION_READONLY",
        modes=("READ_ONLY",),
        builder=_worker_pytest_certification_readonly_builder,
    )
)


# Gate B - Authorized declarative Development mutation semantic capability.
# Distinct from WORKER_REPAIR_BOUNDED (which stays scoped strictly to Worker runtime repairs).
# No shell commands, arbitrary SQL, delete_file, secrets, or Production paths are accepted.
import hashlib as _gate_b_hashlib
from pathlib import Path as _gate_b_Path

_DEV_REPO_ROOT = _gate_b_Path(__file__).resolve().parents[3]
_DEV_ALLOWED_OPERATIONS = frozenset(
    {"replace_text", "insert_before", "insert_after", "append_once", "write_file"}
)
_DEV_FORBIDDEN_PATH_TOKENS = (
    "production",
    "supervisor",
    "nginx",
    "credential",
    "secret",
    "password",
    "token",
    "private_key",
    "api_key",
    ".env",
)
_DEV_TEST_ROOTS = ("backend/tests/", "tools/tests/")
_DEV_SHA256_RE = _g3_re.compile(r"^[0-9a-f]{64}$")
_DEV_AUTH_REF_RE = _g3_re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{2,120}$")
_DEV_MAX_CHANGES = 15
_DEV_MAX_TESTS = 15
_DEV_MAX_TEXT_BYTES = 120_000


def _dev_validate_path(raw_path: Any, *, allowed_roots: tuple[str, ...] = _G3_ROOTS) -> str:
    if not isinstance(raw_path, str) or not _G3_PATH.fullmatch(raw_path):
        raise SemanticCapabilityError("SEMANTIC_DEV_PATH_INVALID")
    if raw_path.endswith("/"):
        raise SemanticCapabilityError("SEMANTIC_DEV_PATH_INVALID")
    parts = raw_path.split("/")
    if (
        not raw_path.startswith(allowed_roots)
        or any(p in ("", ".", "..") for p in parts)
        or any(p in _G3_DENIED for p in parts)
        or any(
            marker in p.lower()
            for p in parts
            for marker in _DEV_FORBIDDEN_PATH_TOKENS
        )
    ):
        raise SemanticCapabilityError("SEMANTIC_DEV_PATH_FORBIDDEN")
    return raw_path


def _dev_apply_virtual_change(current_text: str, action: dict[str, Any]) -> str:
    op = action["type"]
    if op == "replace_text":
        old = action["old_text"]
        rep = action["replacement"]
        expected = int(action.get("expected_occurrences", 1))
        if current_text.count(old) != expected:
            raise SemanticCapabilityError("SEMANTIC_DEV_OLD_TEXT_OCCURRENCE_MISMATCH")
        return current_text.replace(old, rep)
    if op == "insert_before":
        anchor = action["anchor"]
        if current_text.count(anchor) != 1:
            raise SemanticCapabilityError("SEMANTIC_DEV_ANCHOR_MISMATCH")
        return current_text.replace(anchor, action["replacement"] + anchor, 1)
    if op == "insert_after":
        anchor = action["anchor"]
        if current_text.count(anchor) != 1:
            raise SemanticCapabilityError("SEMANTIC_DEV_ANCHOR_MISMATCH")
        return current_text.replace(anchor, anchor + action["replacement"], 1)
    if op == "append_once":
        rep = action["replacement"]
        if rep in current_text:
            return current_text
        return current_text + rep
    if op == "write_file":
        return action["content"]
    raise SemanticCapabilityError("SEMANTIC_DEV_OPERATION_FORBIDDEN")


def _development_mutation_bounded_builder(request: Mapping[str, Any]) -> dict[str, Any]:
    context = _g3_context(request)
    c = _g3_constraints(
        request,
        {"change_spec", "verification_tests", "authorization_ref", "job_id_override"},
    )

    change_spec = c.get("change_spec")
    if not isinstance(change_spec, list) or not 1 <= len(change_spec) <= _DEV_MAX_CHANGES:
        raise SemanticCapabilityError("SEMANTIC_DEV_CHANGE_SPEC_INVALID")

    auth_ref = c.get("authorization_ref")
    if auth_ref is not None and (
        not isinstance(auth_ref, str) or not _DEV_AUTH_REF_RE.fullmatch(auth_ref.strip())
    ):
        raise SemanticCapabilityError("SEMANTIC_DEV_AUTHORIZATION_REF_INVALID")

    job_id_override = c.get("job_id_override")
    if job_id_override is not None and (
        not isinstance(job_id_override, str) or not _G3_JOB_ID.fullmatch(job_id_override.strip())
    ):
        raise SemanticCapabilityError("SEMANTIC_DEV_JOB_ID_OVERRIDE_INVALID")

    raw_tests = c.get("verification_tests", [])
    if not isinstance(raw_tests, list) or len(raw_tests) > _DEV_MAX_TESTS:
        raise SemanticCapabilityError("SEMANTIC_DEV_VERIFICATION_TESTS_INVALID")
    verified_tests: list[str] = []
    for test_path in raw_tests:
        clean_test = _dev_validate_path(test_path, allowed_roots=_DEV_TEST_ROOTS)
        if not clean_test.endswith(".py"):
            raise SemanticCapabilityError("SEMANTIC_DEV_VERIFICATION_TESTS_INVALID")
        if clean_test not in verified_tests:
            verified_tests.append(clean_test)

    # Track virtual file state to support chained deterministic edits to the same file
    virtual_files: dict[str, str] = {}
    built_actions: list[dict[str, Any]] = []
    touched_py_paths: list[str] = []

    for item in change_spec:
        if not isinstance(item, Mapping):
            raise SemanticCapabilityError("SEMANTIC_DEV_CHANGE_ITEM_INVALID")
        allowed_item_keys = {
            "operation",
            "path",
            "source_sha256",
            "old_text",
            "replacement",
            "anchor",
            "content",
            "expected_occurrences",
            "overwrite",
        }
        if set(item.keys()) - allowed_item_keys:
            raise SemanticCapabilityError("SEMANTIC_DEV_CHANGE_KEYS_UNSUPPORTED")

        op = str(item.get("operation") or "").strip()
        if op not in _DEV_ALLOWED_OPERATIONS:
            raise SemanticCapabilityError("SEMANTIC_DEV_OPERATION_FORBIDDEN")

        rel_path = _dev_validate_path(item.get("path"))
        disk_path = _DEV_REPO_ROOT / rel_path

        if rel_path in virtual_files:
            live_text = virtual_files[rel_path]
            file_exists = True
        elif disk_path.is_file():
            live_text = disk_path.read_text(encoding="utf-8")
            file_exists = True
        else:
            live_text = ""
            file_exists = False

        supplied_sha = item.get("source_sha256")
        if op == "write_file":
            content = item.get("content")
            if not isinstance(content, str) or not content:
                raise SemanticCapabilityError("SEMANTIC_DEV_CONTENT_REQUIRED")
            if len(content.encode("utf-8")) > _DEV_MAX_TEXT_BYTES:
                raise SemanticCapabilityError("SEMANTIC_DEV_CONTENT_TOO_LARGE")
            overwrite = bool(item.get("overwrite", False))
            if file_exists:
                if not overwrite:
                    raise SemanticCapabilityError("SEMANTIC_DEV_FILE_ALREADY_EXISTS")
                if not isinstance(supplied_sha, str) or not _DEV_SHA256_RE.fullmatch(supplied_sha.strip().lower()):
                    raise SemanticCapabilityError("SEMANTIC_SOURCE_SHA256_REQUIRED")
                actual_sha = _gate_b_hashlib.sha256(live_text.encode("utf-8")).hexdigest()
                if supplied_sha.strip().lower() != actual_sha:
                    raise SemanticCapabilityError("SEMANTIC_SOURCE_SHA256_MISMATCH")
            action: dict[str, Any] = {
                "type": "write_file",
                "path": rel_path,
                "content": content,
            }
            if file_exists and isinstance(supplied_sha, str):
                action["source_sha256"] = supplied_sha.strip().lower()
            virtual_files[rel_path] = content
        else:
            if not file_exists:
                raise SemanticCapabilityError("SEMANTIC_SOURCE_FILE_MISSING")
            if not isinstance(supplied_sha, str) or not _DEV_SHA256_RE.fullmatch(supplied_sha.strip().lower()):
                raise SemanticCapabilityError("SEMANTIC_SOURCE_SHA256_REQUIRED")
            actual_sha = _gate_b_hashlib.sha256(live_text.encode("utf-8")).hexdigest()
            if supplied_sha.strip().lower() != actual_sha:
                raise SemanticCapabilityError("SEMANTIC_SOURCE_SHA256_MISMATCH")

            action = {
                "type": op,
                "path": rel_path,
                "source_sha256": actual_sha,
            }
            if op == "replace_text":
                old_text = item.get("old_text")
                replacement = item.get("replacement")
                expected_occ = item.get("expected_occurrences", 1)
                if not isinstance(old_text, str) or not old_text or not isinstance(replacement, str):
                    raise SemanticCapabilityError("SEMANTIC_DEV_REPLACE_FIELDS_INVALID")
                if type(expected_occ) is not int or not 1 <= expected_occ <= 20:
                    raise SemanticCapabilityError("SEMANTIC_DEV_EXPECTED_OCCURRENCES_INVALID")
                if len(replacement.encode("utf-8")) > _DEV_MAX_TEXT_BYTES:
                    raise SemanticCapabilityError("SEMANTIC_DEV_CONTENT_TOO_LARGE")
                action["old_text"] = old_text
                action["replacement"] = replacement
                action["expected_occurrences"] = expected_occ
            elif op in {"insert_before", "insert_after"}:
                anchor = item.get("anchor")
                replacement = item.get("replacement")
                if not isinstance(anchor, str) or not anchor or not isinstance(replacement, str):
                    raise SemanticCapabilityError("SEMANTIC_DEV_INSERT_FIELDS_INVALID")
                if len(replacement.encode("utf-8")) > _DEV_MAX_TEXT_BYTES:
                    raise SemanticCapabilityError("SEMANTIC_DEV_CONTENT_TOO_LARGE")
                action["anchor"] = anchor
                action["replacement"] = replacement
            elif op == "append_once":
                replacement = item.get("replacement")
                if not isinstance(replacement, str) or not replacement:
                    raise SemanticCapabilityError("SEMANTIC_DEV_APPEND_FIELDS_INVALID")
                if len(replacement.encode("utf-8")) > _DEV_MAX_TEXT_BYTES:
                    raise SemanticCapabilityError("SEMANTIC_DEV_CONTENT_TOO_LARGE")
                action["replacement"] = replacement
                action["expected_occurrences"] = 1

            virtual_files[rel_path] = _dev_apply_virtual_change(live_text, action)

        built_actions.append(action)
        if rel_path.endswith(".py") and rel_path not in touched_py_paths:
            touched_py_paths.append(rel_path)

    checks: list[dict[str, Any]] = []
    if touched_py_paths:
        checks.append({"type": "py_compile", "paths": touched_py_paths})
    if verified_tests:
        checks.append({"type": "pytest", "paths": verified_tests})
    checks.append({"type": "git_diff_check"})

    scheduling = {
        "project_id": "EDARSAHUB",
        "bounded_context": context,
        "priority_class": "NORMAL",
        "fairness_weight": 1,
        "max_parallelism": 1,
        "resource_claims": [],
        "conflict_domains": ["GLOBAL_GIT_WRITER", context],
    }
    expansion: dict[str, Any] = {
        "actions": built_actions,
        "checks": checks,
        "scheduling": scheduling,
    }
    if job_id_override:
        expansion["job_id_override"] = job_id_override.strip()
    return expansion


register_capability(
    SemanticCapability(
        code="DEVELOPMENT_MUTATION_BOUNDED",
        modes=("MUTATION",),
        builder=_development_mutation_bounded_builder,
    )
)


RAW_WORKER_FIELDS_FORBIDDEN: tuple[str, ...] = (
    "actions",
    "checks",
    "production_allowed",
    "requester",
    "target_repo",
    "target_branch",
)

_CAPABILITY_METADATA: dict[str, dict[str, Any]] = {
    "READ_ONLY_CANARY": {
        "bounded_context_rule": "ANY_VALID_TOKEN",
        "allowed_constraints": (),
        "allowed_path_roots": (),
    },
    "REPOSITORY_CONTRACT_AUDIT": {
        "bounded_context_rule": "RH",
        "allowed_constraints": (),
        "allowed_path_roots": ("backend/modules", "frontend/src", "tools/mirror_sync"),
    },
    "REPOSITORY_CONTRACT_AUDIT_BOUNDED": {
        "bounded_context_rule": "ANY_VALID_TOKEN",
        "allowed_constraints": ("max_results", "paths", "search_terms"),
        "allowed_path_roots": _G3_ROOTS,
    },
    "WORKER_RESULT_SEMANTIC_EXTRACT": {
        "bounded_context_rule": "ANY_VALID_TOKEN",
        "allowed_constraints": ("source_job_id",),
        "allowed_path_roots": (),
    },
    "WORKER_RESULT_DETAIL_READ": {
        "bounded_context_rule": "ANY_VALID_TOKEN",
        "allowed_constraints": ("source_job_id",),
        "allowed_path_roots": (),
    },
    "WORKER_MAINTENANCE_HISTORY_READONLY": {
        "bounded_context_rule": "WORKER_REPAIR_KNOWLEDGE_LOOP",
        "allowed_constraints": (),
        "allowed_path_roots": (),
    },
    "WORKER_PYTEST_CERTIFICATION_READONLY": {
        "bounded_context_rule": "WORKER_REPAIR_KNOWLEDGE_LOOP",
        "allowed_constraints": (),
        "allowed_path_roots": (),
    },
    "WORKER_REPAIR_BOUNDED": {
        "bounded_context_rule": _WORKER_REPAIR_CONTEXT,
        "allowed_constraints": ("capability_code", "incident_id"),
        "allowed_path_roots": (),
    },
    "DEVELOPMENT_MUTATION_BOUNDED": {
        "bounded_context_rule": "ANY_VALID_TOKEN",
        "allowed_constraints": (
            "authorization_ref",
            "change_spec",
            "job_id_override",
            "verification_tests",
        ),
        "allowed_path_roots": _G3_ROOTS,
    },
}


def capability_catalog() -> list[dict[str, Any]]:
    """Return read-only declarative metadata for all registered semantic capabilities."""
    items: list[dict[str, Any]] = []
    for code in registered_capabilities():
        cap = _CAPABILITIES[code]
        meta = _CAPABILITY_METADATA.get(code, {})
        items.append(
            {
                "code": cap.code,
                "modes": list(cap.modes),
                "bounded_context_rule": meta.get(
                    "bounded_context_rule",
                    "CAPABILITY_OWNED",
                ),
                "allowed_constraints": list(
                    meta.get("allowed_constraints", ())
                ),
                "allowed_path_roots": list(
                    meta.get("allowed_path_roots", ())
                ),
                "raw_worker_fields_forbidden": True,
            }
        )
    return items
