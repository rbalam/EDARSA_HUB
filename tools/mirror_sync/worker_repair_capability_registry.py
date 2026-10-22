"""Persistent learned capability registry for Worker Repair.

This registry lets Worker Repair evolve from new incident families without
adding one Python branch per problem. Learned capabilities remain declarative,
bounded, auditable and fail-closed.

It never executes mutations. It only validates and stores repair recipes that
the existing Worker Repair planner can later materialize into canonical jobs.
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.mirror_sync import worker_maintenance_runtime as maintenance
from tools.mirror_sync.universal_job_bridge import ALLOWED_ACTIONS, ALLOWED_CHECKS


SCHEMA = "edarsahub.worker-repair-learned-capability.v1"
CODE_RE = re.compile(r"^[A-Z0-9][A-Z0-9_]{2,95}$")
SIGNATURE_RE = re.compile(r"^[A-Z0-9][A-Z0-9_.:-]{2,191}$")

REGISTRY_DIR = maintenance.STATE_DIR / "learned_capabilities"

FORBIDDEN_RECIPE_KEYS = {
    "command",
    "shell",
    "script",
    "sql",
    "production_allowed",
    "production",
    "secret",
    "token",
    "password",
}


@dataclass(frozen=True)
class LearnedCapability:
    code: str
    problem_signature: str
    incident_ids: tuple[str, ...]
    incident_patterns: tuple[str, ...]
    required_paths: tuple[str, ...]
    objective: str
    actions: tuple[dict[str, Any], ...]
    checks: tuple[dict[str, Any], ...]
    evidence: dict[str, Any]
    learned_from_incident: str
    reusable: bool = True


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as handle:
        json.dump(
            payload,
            handle,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        temp_name = handle.name
    os.replace(temp_name, path)


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key).lower()
            yield from _walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def _clean_strings(value: Any, field: str) -> tuple[str, ...]:
    if value in (None, []):
        return ()
    if not isinstance(value, list):
        raise ValueError(f"{field.upper()}_INVALID")
    rows: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if not text:
            raise ValueError(f"{field.upper()}_INVALID")
        rows.append(text)
    return tuple(sorted(set(rows)))


def _validate_recipe(
    *,
    required_paths: tuple[str, ...],
    actions: Any,
    checks: Any,
) -> tuple[tuple[dict[str, Any], ...], tuple[dict[str, Any], ...]]:
    if not isinstance(actions, list) or not actions:
        raise ValueError("LEARNED_CAPABILITY_ACTIONS_REQUIRED")

    if not isinstance(checks, list) or not checks:
        raise ValueError("LEARNED_CAPABILITY_CHECKS_REQUIRED")

    allowed_paths = set(required_paths)
    normalized_actions: list[dict[str, Any]] = []

    for raw in actions:
        if not isinstance(raw, dict):
            raise ValueError("LEARNED_CAPABILITY_ACTION_INVALID")

        kind = str(raw.get("type") or "").strip()
        path = str(raw.get("path") or "").strip()

        if kind not in ALLOWED_ACTIONS:
            raise ValueError("LEARNED_CAPABILITY_ACTION_UNSUPPORTED")
        if not path or path not in allowed_paths:
            raise ValueError("LEARNED_CAPABILITY_ACTION_SCOPE_MISMATCH")

        forbidden = FORBIDDEN_RECIPE_KEYS.intersection(_walk_keys(raw))
        if forbidden:
            raise ValueError(
                "LEARNED_CAPABILITY_FORBIDDEN_RECIPE_KEY:"
                + sorted(forbidden)[0]
            )

        normalized_actions.append(dict(raw))

    normalized_checks: list[dict[str, Any]] = []

    for raw in checks:
        if not isinstance(raw, dict):
            raise ValueError("LEARNED_CAPABILITY_CHECK_INVALID")

        kind = str(raw.get("type") or "").strip()

        if kind not in ALLOWED_CHECKS:
            raise ValueError("LEARNED_CAPABILITY_CHECK_UNSUPPORTED")

        forbidden = FORBIDDEN_RECIPE_KEYS.intersection(_walk_keys(raw))
        if forbidden:
            raise ValueError(
                "LEARNED_CAPABILITY_FORBIDDEN_RECIPE_KEY:"
                + sorted(forbidden)[0]
            )

        normalized_checks.append(dict(raw))

    return tuple(normalized_actions), tuple(normalized_checks)


def normalize_learned_capability(
    payload: dict[str, Any],
) -> LearnedCapability:
    if not isinstance(payload, dict):
        raise ValueError("LEARNED_CAPABILITY_NOT_OBJECT")

    if payload.get("schema") != SCHEMA:
        raise ValueError("LEARNED_CAPABILITY_SCHEMA_INVALID")

    if payload.get("production_allowed") is not False:
        raise ValueError("LEARNED_CAPABILITY_PRODUCTION_FORBIDDEN")

    code = str(payload.get("code") or "").strip().upper()
    if not CODE_RE.fullmatch(code):
        raise ValueError("LEARNED_CAPABILITY_CODE_INVALID")

    signature = str(payload.get("problem_signature") or "").strip().upper()
    if not SIGNATURE_RE.fullmatch(signature):
        raise ValueError("LEARNED_CAPABILITY_SIGNATURE_INVALID")

    incident_ids = _clean_strings(payload.get("incident_ids"), "incident_ids")
    patterns = _clean_strings(payload.get("incident_patterns"), "incident_patterns")
    required_paths = _clean_strings(payload.get("required_paths"), "required_paths")

    if not incident_ids and not patterns:
        raise ValueError("LEARNED_CAPABILITY_MATCHER_REQUIRED")
    if not required_paths:
        raise ValueError("LEARNED_CAPABILITY_PATHS_REQUIRED")

    objective = str(payload.get("objective") or "").strip()
    if not objective:
        raise ValueError("LEARNED_CAPABILITY_OBJECTIVE_REQUIRED")

    evidence = payload.get("evidence")
    if not isinstance(evidence, dict):
        raise ValueError("LEARNED_CAPABILITY_EVIDENCE_REQUIRED")

    source_job_id = str(evidence.get("source_job_id") or "").strip()
    blocker_signature = str(evidence.get("blocker_signature") or "").strip()
    if not source_job_id or not blocker_signature:
        raise ValueError("LEARNED_CAPABILITY_EVIDENCE_INCOMPLETE")

    learned_from = str(payload.get("learned_from_incident") or "").strip()
    if not learned_from:
        raise ValueError("LEARNED_CAPABILITY_SOURCE_INCIDENT_REQUIRED")

    actions, checks = _validate_recipe(
        required_paths=required_paths,
        actions=payload.get("actions"),
        checks=payload.get("checks"),
    )

    return LearnedCapability(
        code=code,
        problem_signature=signature,
        incident_ids=incident_ids,
        incident_patterns=patterns,
        required_paths=required_paths,
        objective=objective,
        actions=actions,
        checks=checks,
        evidence=dict(evidence),
        learned_from_incident=learned_from,
        reusable=bool(payload.get("reusable", True)),
    )


def _payload(capability: LearnedCapability) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "code": capability.code,
        "problem_signature": capability.problem_signature,
        "incident_ids": list(capability.incident_ids),
        "incident_patterns": list(capability.incident_patterns),
        "required_paths": list(capability.required_paths),
        "objective": capability.objective,
        "actions": [dict(item) for item in capability.actions],
        "checks": [dict(item) for item in capability.checks],
        "evidence": dict(capability.evidence),
        "learned_from_incident": capability.learned_from_incident,
        "reusable": capability.reusable,
        "production_allowed": False,
    }


def register_learned_capability(
    payload: dict[str, Any],
    *,
    incident: Any,
) -> dict[str, Any]:
    capability = normalize_learned_capability(payload)

    if capability.learned_from_incident != str(incident.incident_id):
        raise ValueError("LEARNED_CAPABILITY_INCIDENT_BINDING_MISMATCH")

    incident_paths = set(incident.target_paths)
    if not set(capability.required_paths).issubset(incident_paths):
        raise ValueError("LEARNED_CAPABILITY_SCOPE_NOT_AUTHORIZED")

    path = REGISTRY_DIR / f"{capability.code}.json"
    serialized = _payload(capability)

    if path.is_file():
        current = json.loads(path.read_text(encoding="utf-8"))
        existing = normalize_learned_capability(current)
        if _payload(existing) != serialized:
            raise ValueError("LEARNED_CAPABILITY_IDEMPOTENCY_CONFLICT")
        return {
            "status": "ALREADY_REGISTERED",
            "code": capability.code,
            "path": str(path),
            "production_touched": False,
        }

    _atomic_json(path, serialized)

    return {
        "status": "REGISTERED",
        "code": capability.code,
        "path": str(path),
        "production_touched": False,
    }


def iter_learned_capabilities() -> tuple[LearnedCapability, ...]:
    if not REGISTRY_DIR.is_dir():
        return ()

    rows: list[LearnedCapability] = []
    for path in sorted(REGISTRY_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows.append(normalize_learned_capability(payload))
    return tuple(rows)


def _matches(
    capability: LearnedCapability,
    *,
    incident_id: str,
    problem_signature: str | None,
) -> bool:
    if incident_id in capability.incident_ids:
        return True

    if capability.reusable:
        for pattern in capability.incident_patterns:
            if fnmatch.fnmatchcase(incident_id, pattern):
                return True

        signature = str(problem_signature or "").strip().upper()
        if signature and signature == capability.problem_signature:
            return True

    return False


def resolve_learned_capability(
    *,
    incident_id: str,
    problem_signature: str | None = None,
    capability_code: str | None = None,
) -> LearnedCapability | None:
    code = str(capability_code or "").strip().upper()

    matches = []
    for capability in iter_learned_capabilities():
        if code and capability.code != code:
            continue
        if _matches(
            capability,
            incident_id=incident_id,
            problem_signature=problem_signature,
        ):
            matches.append(capability)

    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError("LEARNED_CAPABILITY_AMBIGUOUS")

    return matches[0]


def recipe_from_learned(
    capability: LearnedCapability,
) -> dict[str, Any]:
    return {
        "objective": capability.objective,
        "actions": [dict(item) for item in capability.actions],
        "checks": [dict(item) for item in capability.checks],
    }
