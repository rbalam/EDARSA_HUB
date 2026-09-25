"""Canonical Universal Worker job envelope factory.

All ChatGPT projects/chats must publish Worker requests through this boundary.
It owns transport invariants so callers cannot drift on repository, branch,
Production policy, summary language, or scheduling metadata.

This module performs no Git, SQL, network, service, or Production mutation.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

WORKER_JOB_SCHEMA = "edarsahub.worker-job.v2"
CANONICAL_TARGET_REPO = "rbalam/EDARSA_HUB"
CANONICAL_TARGET_BRANCH = "Edarsahub_Desarrollo"
CANONICAL_SUMMARY_LANGUAGE = "es"

_FIXED_FIELDS = {
    "schema": WORKER_JOB_SCHEMA,
    "target_repo": CANONICAL_TARGET_REPO,
    "target_branch": CANONICAL_TARGET_BRANCH,
    "production_allowed": False,
    "human_summary_language": CANONICAL_SUMMARY_LANGUAGE,
}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _require_requester(job: dict[str, Any]) -> dict[str, Any]:
    requester = job.get("requester")
    if not isinstance(requester, dict):
        raise ValueError("REQUESTER_REQUIRED")

    email = _clean(requester.get("email")).lower()
    source = _clean(requester.get("source"))

    if not email or "@" not in email:
        raise ValueError("REQUESTER_EMAIL_INVALID")
    if not source:
        raise ValueError("REQUESTER_SOURCE_REQUIRED")

    normalized = dict(requester)
    normalized["email"] = email
    normalized["source"] = source
    normalized["project"] = _clean(requester.get("project"))
    normalized["chat"] = _clean(requester.get("chat"))
    return normalized


def _canonical_scheduling(
    job: dict[str, Any],
    requester: dict[str, Any],
) -> dict[str, Any]:
    scheduling = job.get("scheduling")
    scheduling = dict(scheduling) if isinstance(scheduling, dict) else {}

    project_id = _clean(
        scheduling.get("project_id")
        or requester.get("project")
        or "EDARSAHUB"
    )
    bounded_context = _clean(
        scheduling.get("bounded_context")
        or project_id
    )

    scheduling["project_id"] = project_id
    scheduling["bounded_context"] = bounded_context
    scheduling.setdefault("priority_class", "NORMAL")
    scheduling.setdefault("fairness_weight", 1)
    scheduling.setdefault("max_parallelism", 1)
    scheduling.setdefault("resource_claims", [])
    scheduling.setdefault("conflict_domains", ["GLOBAL_GIT_WRITER"])

    return scheduling


def canonicalize_job(template: dict[str, Any]) -> dict[str, Any]:
    """Return one deterministic Worker envelope for every caller.

    Missing canonical transport fields are supplied here. Conflicting explicit
    values are rejected rather than silently rewritten.
    """
    if not isinstance(template, dict):
        raise ValueError("JOB_NOT_OBJECT")

    job = deepcopy(template)

    for field, canonical in _FIXED_FIELDS.items():
        supplied = job.get(field)
        if supplied is not None and supplied != canonical:
            raise ValueError(f"CANONICAL_FIELD_CONFLICT:{field}")
        job[field] = canonical

    if not _clean(job.get("job_id")):
        raise ValueError("JOB_ID_REQUIRED")
    if not _clean(job.get("objective")):
        raise ValueError("OBJECTIVE_REQUIRED")

    requester = _require_requester(job)
    job["requester"] = requester
    job["scheduling"] = _canonical_scheduling(job, requester)

    return job
