"""Canonical execution bridge for Worker Repair.

This module connects an already-declared Worker maintenance incident to the
existing Universal Worker publication and terminal-result infrastructure.

It does not:
- generate repair code or actions;
- create another queue, dispatcher, scheduler, or control plane;
- execute repository mutation directly;
- touch Production or SQL;
- certify its own repair.

A deterministic ``edarsahub.worker-job.v2`` payload must already exist.
Repository mutation remains exclusively the responsibility of Universal Worker.
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from tools.mirror_sync import gate_chain_publisher
from tools.mirror_sync import worker_maintenance_contract as maintenance_contract
from tools.mirror_sync import worker_maintenance_runtime as maintenance
from tools.mirror_sync.worker_result_reader import read_canonical_result


ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / ".git" / "universal-worker-queue" / "results"

TARGET_REPO = "rbalam/EDARSA_HUB"
TARGET_BRANCH = "Edarsahub_Desarrollo"


def _result_completed_epoch(
    payload: dict[str, Any],
) -> float | None:
    value = payload.get(
        "completed_at_utc"
    )

    if not isinstance(value, str):
        return None

    value = value.strip()

    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        ).timestamp()
    except ValueError:
        return None


def deterministic_repair_job_id(
    incident_id: str,
    attempt_number: int,
) -> str:
    incident = str(incident_id or "").strip()

    if not incident:
        raise ValueError("INCIDENT_ID_REQUIRED")

    if not isinstance(attempt_number, int) or attempt_number < 1:
        raise ValueError("ATTEMPT_NUMBER_INVALID")

    digest = hashlib.sha256(
        f"{incident}\n{attempt_number}".encode("utf-8")
    ).hexdigest()[:20]

    return f"WORKER-REPAIR-{digest}-A{attempt_number}"


def _action_paths(
    worker_job: dict[str, Any],
) -> tuple[str, ...]:
    paths: set[str] = set()

    for action in worker_job.get("actions") or []:
        if not isinstance(action, dict):
            raise ValueError("REPAIR_ACTION_INVALID")

        path = str(action.get("path") or "").strip()

        if not path:
            raise ValueError("REPAIR_ACTION_PATH_REQUIRED")

        paths.add(path)

    return tuple(sorted(paths))


def _repair_rbac_env_enforced() -> bool:
    return (
        os.environ.get("EDARSAHUB_WORKER_REPAIR_ENFORCE_RBAC", "0") == "1"
        or os.environ.get("EDARSAHUB_WORKER_REQUIRE_REQUESTER", "0") == "1"
    )


def _default_rbac_authorizer(requester: Any) -> dict[str, Any]:
    from tools.mirror_sync.worker_requester_rbac import authorize_requester

    return authorize_requester(requester)


def authorize_repair_execution(
    worker_job: dict[str, Any],
    *,
    incident: Any = None,
    authorizer: Any = None,
) -> dict[str, Any]:
    """Fail-closed pre-mutation authorization reusing worker_requester_rbac and maintenance contract.

    Validates requester identity, environment target, READ_ONLY vs MUTATION separation,
    bounded-context path scope, and canonical SQL SUPERADMIN RBAC before any repair mutation.
    """
    if not isinstance(worker_job, dict):
        raise ValueError("REPAIR_JOB_NOT_OBJECT")

    if worker_job.get("production_allowed") is not False:
        raise ValueError("REPAIR_PRODUCTION_FORBIDDEN")

    if str(worker_job.get("target_repo") or TARGET_REPO).strip() != TARGET_REPO:
        raise ValueError("REPAIR_TARGET_REPO_INVALID")

    if str(worker_job.get("target_branch") or TARGET_BRANCH).strip() != TARGET_BRANCH:
        raise ValueError("REPAIR_TARGET_BRANCH_INVALID")

    mode = str(worker_job.get("mode") or "MUTATION").strip().upper()
    actions = worker_job.get("actions")

    if mode == "READ_ONLY":
        if isinstance(actions, list) and len(actions) > 0:
            raise ValueError("REPAIR_READ_ONLY_MUTATION_FORBIDDEN")
        if actions not in (None, []):
            raise ValueError("REPAIR_READ_ONLY_MUTATION_FORBIDDEN")
        requester = worker_job.get("requester")
        if not isinstance(requester, dict):
            raise ValueError("REPAIR_RBAC_DENIED:REQUESTER_REQUIRED")
        email = str(requester.get("email") or "").strip().lower()
        source = str(requester.get("source") or "").strip()
        if not email or "@" not in email:
            raise ValueError("REPAIR_RBAC_DENIED:REQUESTER_EMAIL_INVALID")
        if not source:
            raise ValueError("REPAIR_RBAC_DENIED:REQUESTER_SOURCE_REQUIRED")
        return {
            "allowed": True,
            "mode": "READ_ONLY",
            "reason": "READ_ONLY_NON_MUTATING",
            "requester_email": email,
            "production_touched": False,
        }

    if mode != "MUTATION":
        raise ValueError("REPAIR_MODE_MUST_BE_MUTATION")

    if not isinstance(actions, list) or not actions:
        raise ValueError("REPAIR_ACTIONS_REQUIRED")

    action_paths = _action_paths(worker_job)
    incident_id = getattr(incident, "incident_id", None) if incident is not None else None
    capability_code = getattr(incident, "capability_code", None) if incident is not None else None
    if not maintenance_contract.repair_scope_allowed(
        action_paths,
        incident_id=incident_id,
        capability_code=capability_code,
    ):
        raise ValueError("REPAIR_BOUNDED_CONTEXT_FORBIDDEN")

    requester = worker_job.get("requester")
    if not isinstance(requester, dict):
        raise ValueError("REPAIR_RBAC_DENIED:REQUESTER_REQUIRED")

    auth_fn = authorizer or _default_rbac_authorizer
    try:
        auth_result = auth_fn(requester)
    except Exception as exc:
        raise ValueError("REPAIR_RBAC_DENIED:REQUESTER_RBAC_RUNTIME_ERROR") from exc

    if not isinstance(auth_result, dict) or auth_result.get("allowed") is not True:
        reason = (
            str(auth_result.get("reason") or "UNKNOWN").strip()
            if isinstance(auth_result, dict)
            else "INVALID_RBAC_RESPONSE"
        )
        raise ValueError(f"REPAIR_RBAC_DENIED:{reason}")

    return {
        "allowed": True,
        "mode": "MUTATION",
        "reason": str(auth_result.get("reason") or "SUPERADMIN_CANONICAL"),
        "authorization": dict(auth_result),
        "production_touched": False,
    }


def validate_repair_worker_job(
    incident_id: str,
    worker_job: dict[str, Any],
    *,
    enforce_rbac: bool | None = None,
    rbac_authorizer: Any = None,
) -> dict[str, Any]:
    incident = maintenance.read_runtime_incident(
        incident_id
    )

    if incident is None:
        raise ValueError("INCIDENT_NOT_DECLARED")

    allowed, reason = maintenance.repair_attempt_allowed(
        incident_id
    )

    existing_binding = incident.repair_job_id

    if not allowed and not existing_binding:
        raise ValueError(reason)

    template = gate_chain_publisher.validate_template(
        worker_job
    )

    if template.get("target_repo") != TARGET_REPO:
        raise ValueError("REPAIR_TARGET_REPO_INVALID")

    if template.get("target_branch") != TARGET_BRANCH:
        raise ValueError("REPAIR_TARGET_BRANCH_INVALID")

    if template.get("production_allowed") is not False:
        raise ValueError("REPAIR_PRODUCTION_FORBIDDEN")

    mode = str(template.get("mode") or "MUTATION").strip().upper()
    actions = template.get("actions")

    if mode == "READ_ONLY":
        if actions not in (None, []):
            raise ValueError("REPAIR_READ_ONLY_MUTATION_FORBIDDEN")
        raise ValueError("REPAIR_MODE_MUST_BE_MUTATION")

    if mode != "MUTATION":
        raise ValueError("REPAIR_MODE_MUST_BE_MUTATION")

    if not isinstance(actions, list) or not actions:
        raise ValueError("REPAIR_ACTIONS_REQUIRED")

    action_paths = _action_paths(template)
    incident_paths = set(incident.target_paths)

    if not action_paths:
        raise ValueError("REPAIR_ACTION_SCOPE_EMPTY")

    if not set(action_paths).issubset(incident_paths):
        raise ValueError("REPAIR_ACTION_SCOPE_MISMATCH")

    if not maintenance_contract.repair_scope_allowed(
        action_paths,
        incident_id=incident.incident_id,
        capability_code=getattr(incident, "capability_code", None),
    ):
        raise ValueError("REPAIR_BOUNDED_CONTEXT_FORBIDDEN")

    next_attempt = incident.attempts + 1

    expected_job_id = (
        existing_binding
        or deterministic_repair_job_id(
            incident.incident_id,
            next_attempt,
        )
    )

    actual_job_id = str(
        template.get("job_id") or ""
    ).strip()

    if actual_job_id != expected_job_id:
        raise ValueError("REPAIR_JOB_ID_NOT_DETERMINISTIC")

    effective_rbac = (
        bool(enforce_rbac)
        if enforce_rbac is not None
        else (rbac_authorizer is not None or _repair_rbac_env_enforced())
    )
    if effective_rbac:
        authorize_repair_execution(
            template,
            incident=incident,
            authorizer=rbac_authorizer,
        )

    return template


def publish_repair_job(
    incident_id: str,
    worker_job: dict[str, Any],
    *,
    remote: str = "origin",
    queue_branch: str = "worker/requests",
    enforce_rbac: bool | None = None,
    rbac_authorizer: Any = None,
) -> dict[str, Any]:
    template = validate_repair_worker_job(
        incident_id,
        worker_job,
        enforce_rbac=enforce_rbac,
        rbac_authorizer=rbac_authorizer,
    )

    plan = {
        "status": "READY_TO_PUBLISH",
        "job_id": template["job_id"],
        "template": template,
    }

    publication = gate_chain_publisher.publish(
        plan,
        remote=remote,
        queue_branch=queue_branch,
    )

    status = str(
        publication.get("status") or ""
    ).strip()

    if status not in {"PUBLISHED", "EXISTS"}:
        raise RuntimeError(
            "REPAIR_PUBLICATION_NOT_COMMITTED"
        )

    state = maintenance.register_published_repair_attempt(
        incident_id,
        str(template["job_id"]),
        publication,
    )

    return {
        "incident_id": incident_id,
        "repair_job_id": state.repair_job_id,
        "attempts": state.attempts,
        "publication_status": (
            state.repair_publication_state
        ),
        "publication_commit": (
            state.repair_publication_commit
        ),
        "production_touched": False,
    }


def read_repair_terminal_result(
    incident_id: str,
):
    incident = maintenance.read_runtime_incident(
        incident_id
    )

    if incident is None:
        raise ValueError("INCIDENT_NOT_DECLARED")

    job_id = str(
        incident.repair_job_id or ""
    ).strip()

    if not job_id:
        raise ValueError("REPAIR_JOB_NOT_BOUND")

    result_path = RESULTS_DIR / f"{job_id}.json"

    return read_canonical_result(
        result_path,
        expected_job_id=job_id,
    )


def reconcile_repair_result(
    incident_id: str,
) -> dict[str, Any]:
    incident = maintenance.read_runtime_incident(
        incident_id
    )

    if incident is None:
        raise ValueError("INCIDENT_NOT_DECLARED")

    if incident.state in {
        "REPAIRED_PENDING_AUDIT",
        "CERTIFIED",
    }:
        return {
            "incident_id": incident.incident_id,
            "state": incident.state,
            "terminal_result_valid": True,
            "reconciled": False,
            "production_touched": (
                incident.production_touched
            ),
        }

    result_read = read_repair_terminal_result(
        incident_id
    )

    if not result_read.terminal_result_valid:
        return {
            "incident_id": incident_id,
            "state": incident.state,
            "terminal_result_valid": False,
            "result_state": result_read.state,
            "reconciled": False,
            "production_touched": False,
        }

    payload = result_read.payload or {}

    repair_result = {
        "job_id": str(
            payload.get("job_id")
            or incident.repair_job_id
            or ""
        ),
        "result_sha256": (
            result_read.result_sha256
        ),
        "status": payload.get("status"),
        "certification": payload.get(
            "certification"
        ),
        "files_changed": payload.get(
            "files_changed"
        ),
        "production_touched": payload.get(
            "production_touched"
        ),
        "quality_gate": payload.get(
            "quality_gate"
        ),
        "tests": payload.get("tests"),
        "blockers": payload.get("blockers"),
        "git_sync_status": payload.get(
            "git_sync_status"
        ),
        "base_sha": payload.get("base_sha"),
        "execution_base_sha": payload.get(
            "execution_base_sha"
        ),
        "candidate_sha": payload.get(
            "candidate_sha"
        ),
        "development_sha": payload.get(
            "development_sha"
        ),
    }

    decision = maintenance.register_repair_result(
        incident_id,
        repair_result,
        now_epoch=(
            _result_completed_epoch(
                payload
            )
        ),
    )

    return {
        "incident_id": incident_id,
        "repair_job_id": incident.repair_job_id,
        "state": decision.state.value,
        "reason": decision.reason,
        "certified": decision.certified,
        "terminal_result_valid": True,
        "result_sha256": result_read.result_sha256,
        "result_path": result_read.result_path,
        "reconciled": True,
        "production_touched": bool(
            repair_result.get("production_touched")
        ),
    }
