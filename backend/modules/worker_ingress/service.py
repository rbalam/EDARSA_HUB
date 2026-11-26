"""Service boundary for remote Universal Worker submission and status.

This module is intentionally thin. It does not implement another queue,
publisher, scheduler, Git client, SQL executor or Worker. Submission is
delegated to the existing canonical job factory and gate-chain publisher.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import logging
import re
import threading
import time
from pathlib import Path
from typing import Any, Mapping

from tools.mirror_sync import gate_chain_publisher
from tools.mirror_sync.worker_job_factory import canonicalize_job
from tools.mirror_sync.worker_result_reader import read_canonical_result
from tools.mirror_sync.worker_result_status import build_job_status

from .semantic_capabilities import (
    SemanticCapabilityError,
    resolve_capability,
)


logger = logging.getLogger("edarsahub.worker_ingress")
_SAFE_CORR_RE = re.compile(r"^[A-Za-z0-9._:-]{1,80}$")
_CORR_SENSITIVE = ("secret", "token", "password", "credential", "jwt", "bearer", "api_key", "apikey")

REPO_ROOT = Path(__file__).resolve().parents[3]
STATE_ROOT = REPO_ROOT / ".git" / "universal-worker-queue"
JOB_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$")

_SENSITIVE_KEYS = {
    "password",
    "password_decrypted",
    "secret",
    "secrets",
    "token",
    "credentials",
    "credential",
    "api_key",
    "apikey",
}

_SAFE_RESULT_KEYS = {
    "status",
    "quality_gate",
    "certification",
    "work_completion",
    "certification_basis",
    "certified_source_sha",
    "converged_head",
    "development_sha",
    "reconciliation_status",
    "published_result_commit",
    "published_result_sha256",
    "attestation_sha256",
    "tests",
    "percent_complete",
    "blockers",
    "files_changed",
    "commit_sha",
    "integrated_commit",
    "git_sync_status",
    "production_touched",
    "completed_at_utc",
    "summary_es",
    "result_detail_evidence",
    "repository_contract_evidence",
    "sql_readonly_evidence",
    "worker_result_semantic_evidence",
    "maintenance_history_evidence",
    "evidence_availability",
    "evidence_status",
    "evidence_truncated",
    "operational_validation",
    "lifecycle_stage",
    "code_certified",
    "operational_validated",
    "operational_validation_status",
    "evidence_breakdown",
}


class WorkerIngressError(ValueError):
    def __init__(self, message: str, *, diagnostic: Mapping[str, Any] | None = None):
        super().__init__(message)
        self.diagnostic = dict(diagnostic) if isinstance(diagnostic, Mapping) else None


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _assert_no_sensitive_keys(value: Any, path: str = "request") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).strip().lower()
            if normalized in _SENSITIVE_KEYS:
                raise WorkerIngressError(f"SENSITIVE_FIELD_FORBIDDEN:{path}.{key}")
            _assert_no_sensitive_keys(nested, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _assert_no_sensitive_keys(nested, f"{path}[{index}]")


_ADMIN_MUTATION_ROLES = frozenset(
    {"superadministrador", "administrador", "superadmin", "admin"}
)


def _assert_mutation_rbac(current_user: Mapping[str, Any]) -> None:
    role = _clean(
        current_user.get("role")
        or current_user.get("rol")
        or current_user.get("sec_perfil")
    ).lower()
    raw_roles = current_user.get("roles") or current_user.get("sec_roles") or ()
    roles = {role} if role else set()
    if isinstance(raw_roles, (list, tuple, set, frozenset)):
        roles.update(_clean(r).lower() for r in raw_roles if _clean(r))
    raw_perms = current_user.get("permissions") or current_user.get("permisos") or ()
    perms = (
        {_clean(p).lower() for p in raw_perms if _clean(p)}
        if isinstance(raw_perms, (list, tuple, set, frozenset))
        else set()
    )
    if not (roles & _ADMIN_MUTATION_ROLES) and not (
        perms & {"worker:submit", "worker.mutation", "worker:mutation", "*"}
    ):
        raise WorkerIngressError("RBAC_MUTATION_FORBIDDEN")


def _find_existing_job_state(job_id: str) -> str | None:
    """Check local queue and remote worker refs to guarantee single publication."""
    import subprocess

    for state, directory in (
        ("RESULT", "results"),
        ("PROCESSING", "processing"),
        ("PENDING", "pending"),
        ("DONE", "done"),
    ):
        if (STATE_ROOT / directory / f"{job_id}.json").is_file():
            return state

    git_dir = STATE_ROOT.parent
    if (git_dir / "HEAD").is_file():
        for state, spec in (
            ("REMOTE_RESULT", f"origin/worker/results:worker_queue/results/{job_id}.json"),
            ("REMOTE_PENDING", f"origin/worker/requests:worker_queue/inbox/{job_id}.json"),
        ):
            try:
                proc = subprocess.run(
                    ["git", f"--git-dir={git_dir}", "cat-file", "-e", spec],
                    capture_output=True,
                    check=False,
                    timeout=5,
                )
                if proc.returncode == 0:
                    return state
            except (OSError, subprocess.SubprocessError):
                continue
    return None


_PUBLICATION_FAILURE_STATUSES = frozenset({
    "RECOVERY_REQUIRED",
    "WRITER_BUSY",
    "CLAIM_BUSY",
    "REMOTE_MOVED_RETRYABLE",
    "BLOCKED_CONVERGENCE",
})


def classify_publication_diagnostic(
    result: Mapping[str, Any],
    *,
    job_id: str | None = None,
) -> dict[str, Any]:
    """Build a secret-free, fail-closed publication diagnostic from publisher output."""
    state = _clean(result.get("status")).upper() or "RECOVERY_REQUIRED"
    raw_reason = _clean(result.get("reason"))
    upper_reason = raw_reason.upper()
    safe_job_id = _clean(job_id or result.get("job_id"))
    if safe_job_id and not JOB_ID_RE.fullmatch(safe_job_id):
        safe_job_id = ""

    if any(
        marker in upper_reason
        for marker in (
            "COULD NOT READ USERNAME",
            "AUTHENTICATION FAILED",
            "TERMINAL PROMPTS DISABLED",
            "HTTP 401",
            "HTTP 403",
            "ACCESS DENIED",
            "CREDENTIAL",
        )
    ):
        category = "GIT_AUTH_FAILURE"
        error_code = "GIT_AUTH_FAILED"
        retryable = False
        recovery_required = True
        recommended_action = (
            "Verify non-interactive Git credential helper / per-URL useHttpPath config "
            "without modifying credentials, then recover the existing draft via gate_chain_publisher.submit()."
        )
    elif state == "BLOCKED_CONVERGENCE" or "CONVERGENCE" in upper_reason or "DIVERGENCE" in upper_reason:
        category = "CONVERGENCE_FAILURE"
        error_code = "BLOCKED_CONVERGENCE"
        retryable = False
        recovery_required = True
        recommended_action = (
            "Inspect GET /api/internal/worker/runtime-convergence and reconcile "
            "Development/Mirror before retrying."
        )
    elif state in {"WRITER_BUSY", "CLAIM_BUSY", "REMOTE_MOVED_RETRYABLE"}:
        category = "CONFLICT_OR_CONTENTION"
        error_code = state
        retryable = True
        recovery_required = False
        recommended_action = (
            "Check get_job_status for the existing job_id; if still unpublished, "
            "retry manually once writer/claim contention clears."
        )
    elif (
        "IDEMPOTENCY_CONFLICT" in upper_reason
        or "RESIDUAL_STATE_INCOMPLETE" in upper_reason
        or "QUEUE_PUBLISHER_RESIDUAL_" in upper_reason
        or "LOCK_BUSY" in upper_reason
    ):
        category = "CONFLICT_OR_CONTENTION"
        if "IDEMPOTENCY_CONFLICT" in upper_reason:
            error_code = "JOB_DRAFT_IDEMPOTENCY_CONFLICT"
        elif "RESIDUAL_STATE_INCOMPLETE" in upper_reason:
            error_code = "QUEUE_PUBLISHER_RESIDUAL_STATE_INCOMPLETE"
        elif "LOCK_BUSY" in upper_reason:
            error_code = "GIT_LOCK_BUSY"
        else:
            error_code = "QUEUE_PUBLISHER_RESIDUAL_CONFLICT"
        retryable = False
        recovery_required = True
        recommended_action = (
            "Do not duplicate the job; inspect existing draft/worktree state and "
            "recover the same job_id canonically."
        )
    else:
        category = "PUBLICATION_FAILURE"
        if "PUSH_FAILED" in upper_reason:
            error_code = "PUSH_FAILED"
        elif "AGENT_GUARD" in upper_reason:
            error_code = "AGENT_GUARD_WORKTREE_FAILED"
        elif "QUEUE_REMOTE_HEAD" in upper_reason:
            error_code = "QUEUE_REMOTE_HEAD_UNAVAILABLE"
        else:
            error_code = state if re.fullmatch(r"[A-Z][A-Z0-9_]{1,80}", state) else "RECOVERY_REQUIRED"
        retryable = False
        recovery_required = True
        recommended_action = (
            "Inspect GET /api/internal/worker/runtime-convergence and existing job_id "
            "draft state before recovering via gate_chain_publisher.submit()."
        )

    return {
        "schema": "edarsahub.worker-publication-diagnostic.v1",
        "category": category,
        "error_code": error_code,
        "status": state,
        "job_id": safe_job_id or None,
        "retryable": retryable,
        "recovery_required": recovery_required,
        "recommended_action": recommended_action,
        "production_touched": False,
    }


def _attach_publication_diagnostic(safe: dict[str, Any]) -> None:
    state = _clean(safe.get("status")).upper()
    if state not in _PUBLICATION_FAILURE_STATUSES:
        return
    diag = classify_publication_diagnostic(safe, job_id=_clean(safe.get("job_id")))
    safe["publication_diagnostic"] = diag
    if "reason" in safe:
        safe["reason"] = diag["error_code"]


def _submit_through_canonical_publisher(canonical_job: dict[str, Any]) -> dict[str, Any]:
    import inspect

    submit_fn = gate_chain_publisher.submit
    try:
        params = inspect.signature(submit_fn).parameters
    except (TypeError, ValueError):
        params = {}
    if {"remote", "queue_branch", "require_convergence"}.issubset(params.keys()):
        return submit_fn(
            canonical_job,
            remote="origin",
            queue_branch="worker/requests",
            require_convergence=False,
        )
    return submit_fn(canonical_job)


def _requester_from_authenticated_user(
    current_user: Mapping[str, Any],
    *,
    project: str,
) -> dict[str, str]:
    email = _clean(current_user.get("email")).lower()
    if not email or "@" not in email:
        raise WorkerIngressError("AUTHENTICATED_REQUESTER_EMAIL_REQUIRED")

    return {
        "email": email,
        "source": "edarsahub-worker-ingress",
        "project": _clean(project) or "EDARSAHUB",
        "chat": "remote-canonical-ingress",
    }


def build_canonical_job(
    request_payload: Mapping[str, Any],
    *,
    current_user: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(request_payload)
    _assert_no_sensitive_keys(payload)

    scheduling = payload.get("scheduling")
    scheduling = dict(scheduling) if isinstance(scheduling, Mapping) else {}

    requester = _requester_from_authenticated_user(
        current_user,
        project=_clean(scheduling.get("project_id")) or "EDARSAHUB",
    )

    raw_job = {
        "job_id": payload.get("job_id"),
        "objective": payload.get("objective"),
        "mode": payload.get("mode"),
        "actions": list(payload.get("actions") or []),
        "checks": list(payload.get("checks") or []),
        "requester": requester,
    }
    if scheduling:
        raw_job["scheduling"] = scheduling

    return canonicalize_job(raw_job)


def submit_job(
    request_payload: Mapping[str, Any],
    *,
    current_user: Mapping[str, Any],
) -> dict[str, Any]:
    """Submit only through the existing canonical publisher."""
    canonical_job = build_canonical_job(
        request_payload,
        current_user=current_user,
    )
    result = gate_chain_publisher.submit(canonical_job)
    if not isinstance(result, dict):
        raise WorkerIngressError("CANONICAL_PUBLISHER_INVALID_RESPONSE")

    safe = dict(result)
    safe["job_id"] = _clean(result.get("job_id")) or canonical_job["job_id"]
    safe["production_touched"] = bool(result.get("production_touched", False))
    safe.pop("template", None)
    _attach_publication_diagnostic(safe)
    return safe


def _legacy_semantic_job_id(
    request_payload: Mapping[str, Any],
    *,
    requester_email: str,
) -> str:
    """Pre-Gate2 semantic id retained only for exact historical retries."""
    bounded_context = _clean(request_payload.get("bounded_context")).upper()
    capability = _clean(request_payload.get("capability")).upper()
    request_key = _clean(request_payload.get("request_key"))
    stable_payload = {
        "requester": requester_email.lower(),
        "objective": _clean(request_payload.get("objective")),
        "bounded_context": bounded_context,
        "mode": _clean(request_payload.get("mode")).upper(),
        "capability": capability,
        "request_key": request_key,
        "constraints": request_payload.get("constraints") or {},
    }
    digest = hashlib.sha256(
        json.dumps(
            stable_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:20].upper()
    prefix = re.sub(r"[^A-Z0-9._-]+", "-", bounded_context)[:32] or "EDARSAHUB"
    cap = re.sub(r"[^A-Z0-9._-]+", "-", capability)[:32] or "CAPABILITY"
    return f"SEM-{prefix}-{cap}-{digest}"[:121]


def _semantic_job_id(
    request_payload: Mapping[str, Any],
    *,
    requester_email: str,
) -> str:
    """Bind new semantic requests to requester+request_key, independent of payload drift."""
    request_key = _clean(request_payload.get("request_key"))
    if not request_key:
        return _legacy_semantic_job_id(
            request_payload,
            requester_email=requester_email,
        )

    identity = {
        "requester": requester_email.lower(),
        "request_key": request_key,
    }
    digest = hashlib.sha256(
        json.dumps(
            identity,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:24].upper()
    return f"SEM-REQUEST-{digest}"


_IDEMPOTENCY_COMPARE_FIELDS = (
    "objective",
    "mode",
    "actions",
    "checks",
    "requester",
    "scheduling",
    "target_repo",
    "target_branch",
    "production_allowed",
    "schema",
)


def _canonical_request_fingerprint(job: Mapping[str, Any]) -> str:
    payload = {
        key: job.get(key)
        for key in _IDEMPOTENCY_COMPARE_FIELDS
    }
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _read_existing_request_job(job_id: str) -> dict[str, Any] | None:
    """Read the already-published canonical request; never mutates queue state."""
    import subprocess

    for directory in ("processing", "pending", "done", "drafts", "published"):
        path = STATE_ROOT / directory / f"{job_id}.json"
        if path.is_file():
            payload = _read_json_if_object(path)
            if payload:
                return payload

    git_dir = STATE_ROOT.parent
    if not (git_dir / "HEAD").is_file():
        return None

    spec = f"origin/worker/requests:worker_queue/inbox/{job_id}.json"
    try:
        proc = subprocess.run(
            ["git", f"--git-dir={git_dir}", "cat-file", "-p", spec],
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0 or not proc.stdout:
        return None
    try:
        payload = json.loads(proc.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _read_unpublished_draft(job_id: str) -> dict[str, Any] | None:
    """Read a local unpublished draft without mutating queue state."""
    if not job_id:
        return None
    path = STATE_ROOT / "drafts" / f"{job_id}.json"
    if not path.is_file():
        return None
    payload = _read_json_if_object(path)
    return payload or None


def _check_unpublished_draft_idempotency(
    canonical_job: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Fail closed if an unpublished draft drifts; surface recovery metadata if exact."""
    existing = _read_unpublished_draft(str(canonical_job.get("job_id") or ""))
    if existing is None:
        return None
    existing_fp = _canonical_request_fingerprint(existing)
    candidate_fp = _canonical_request_fingerprint(canonical_job)
    if existing_fp != candidate_fp or existing.get("base_sha") != canonical_job.get("base_sha"):
        raise WorkerIngressError("IDEMPOTENCY_CONFLICT")
    return {
        "unpublished_draft_recovery": True,
        "draft_fingerprint": existing_fp,
    }


def _assert_idempotent_request_binding(
    canonical_job: Mapping[str, Any],
    *,
    request_key: str,
) -> None:
    if not request_key:
        return
    existing = _read_existing_request_job(str(canonical_job.get("job_id") or ""))
    if existing is None:
        raise WorkerIngressError("IDEMPOTENCY_BINDING_UNVERIFIABLE")
    if _canonical_request_fingerprint(existing) != _canonical_request_fingerprint(canonical_job):
        raise WorkerIngressError("IDEMPOTENCY_CONFLICT")


def _resolve_existing_semantic_job(
    canonical_job: Mapping[str, Any],
    *,
    request_payload: Mapping[str, Any],
    requester_email: str,
) -> tuple[str, str] | None:
    """Resolve stable-id jobs first, then exact legacy retries, and fail closed on drift."""
    request_key = _clean(request_payload.get("request_key"))
    stable_job_id = str(canonical_job.get("job_id") or "")
    stable_state = _find_existing_job_state(stable_job_id)
    if stable_state is not None:
        _assert_idempotent_request_binding(
            canonical_job,
            request_key=request_key,
        )
        return stable_job_id, stable_state

    if not request_key:
        return None

    legacy_job_id = _legacy_semantic_job_id(
        request_payload,
        requester_email=requester_email,
    )
    if legacy_job_id == stable_job_id:
        return None

    legacy_state = _find_existing_job_state(legacy_job_id)
    if legacy_state is None:
        return None

    legacy_job = dict(canonical_job)
    legacy_job["job_id"] = legacy_job_id
    _assert_idempotent_request_binding(
        legacy_job,
        request_key=request_key,
    )
    return legacy_job_id, legacy_state


def build_semantic_job(
    request_payload: Mapping[str, Any],
    *,
    current_user: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(request_payload)
    _assert_no_sensitive_keys(payload)

    objective = _clean(payload.get("objective"))
    bounded_context = _clean(payload.get("bounded_context")).upper()
    requested_mode = _clean(payload.get("mode")).upper()
    capability_code = _clean(payload.get("capability")).upper()

    if not objective:
        raise WorkerIngressError("OBJECTIVE_REQUIRED")
    if not bounded_context:
        raise WorkerIngressError("BOUNDED_CONTEXT_REQUIRED")

    try:
        capability = resolve_capability(capability_code)
    except SemanticCapabilityError as exc:
        raise WorkerIngressError(str(exc)) from exc

    allowed_modes = tuple(str(mode).upper() for mode in capability.modes)
    if requested_mode not in allowed_modes:
        raise WorkerIngressError("SEMANTIC_CAPABILITY_MODE_MISMATCH")

    if capability.builder is None:
        raise WorkerIngressError("SEMANTIC_CAPABILITY_DIRECT_SUBMISSION_REQUIRED")

    try:
        expansion = capability.builder(payload)
    except SemanticCapabilityError as exc:
        raise WorkerIngressError(str(exc)) from exc

    if not isinstance(expansion, dict):
        raise WorkerIngressError("SEMANTIC_CAPABILITY_INVALID_EXPANSION")

    requester = _requester_from_authenticated_user(
        current_user,
        project="EDARSAHUB",
    )

    if requested_mode == "MUTATION":
        _assert_mutation_rbac(current_user)

    job_id = _clean(expansion.get("job_id_override")) or _semantic_job_id(
        payload,
        requester_email=requester["email"],
    )
    if not JOB_ID_RE.fullmatch(job_id):
        raise WorkerIngressError("JOB_ID_INVALID")

    raw_job = {
        "job_id": job_id,
        "objective": objective,
        "mode": requested_mode,
        "actions": list(expansion.get("actions") or []),
        "checks": list(expansion.get("checks") or []),
        "scheduling": dict(expansion.get("scheduling") or {}),
        "requester": requester,
    }
    if expansion.get("authorization_ref"):
        raw_job["authorization_ref"] = str(expansion["authorization_ref"]).strip()
    canonical = canonicalize_job(raw_job)
    return gate_chain_publisher.validate_template(canonical)


def submit_objective(
    request_payload: Mapping[str, Any],
    *,
    current_user: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(request_payload)
    _assert_no_sensitive_keys(payload)

    objective = _clean(payload.get("objective"))
    bounded_context = _clean(payload.get("bounded_context")).upper()
    capability_code = _clean(payload.get("capability")).upper()
    requested_mode = _clean(payload.get("mode")).upper()

    if not objective:
        raise WorkerIngressError("OBJECTIVE_REQUIRED")
    if not bounded_context:
        raise WorkerIngressError("BOUNDED_CONTEXT_REQUIRED")

    try:
        capability = resolve_capability(capability_code)
    except SemanticCapabilityError as exc:
        raise WorkerIngressError(str(exc)) from exc

    allowed_modes = tuple(str(mode).upper() for mode in capability.modes)
    if requested_mode not in allowed_modes:
        raise WorkerIngressError("SEMANTIC_CAPABILITY_MODE_MISMATCH")

    requester = _requester_from_authenticated_user(
        current_user,
        project="EDARSAHUB",
    )

    if requested_mode == "MUTATION":
        preflight = preflight_semantic_objective(
            payload,
            current_user=current_user,
            enforce_runtime_convergence=True,
        )
        if preflight.get("ok") is not True:
            raise WorkerIngressError(
                str(preflight.get("error_code") or "PREFLIGHT_REJECTED")
            )

    if capability.submitter is not None:
        submit_payload = (
            {**payload, "_current_user": dict(current_user)}
            if capability_code in {"CROSS_DOMAIN_HANDOFF_REGISTER", "GATE_AUTHORIZATION_LIFECYCLE"}
            else payload
        )
        try:
            result = capability.submitter(submit_payload, requester)
        except SemanticCapabilityError as exc:
            raise WorkerIngressError(str(exc)) from exc

        if not isinstance(result, dict):
            raise WorkerIngressError("SEMANTIC_CAPABILITY_INVALID_RESPONSE")

        if capability_code == "GATE_AUTHORIZATION_LIFECYCLE":
            gate_id = _clean(result.get("gate_id"))
            auth_id = _clean(result.get("authorization_id"))
            return {
                "status": _clean(result.get("status")) or "OK",
                "job_id": auth_id or gate_id or "GATE_AUTHORIZATION",
                "gate_id": gate_id or None,
                "authorization_id": auth_id or None,
                "active": result.get("active"),
                "revoked": result.get("revoked"),
                "expired": result.get("expired"),
                "expires_at_utc": result.get("expires_at_utc"),
                "scope_digest": result.get("scope_digest"),
                "allowed_paths": result.get("allowed_paths") or ((result.get("scope") or {}).get("allowed_paths") if isinstance(result.get("scope"), Mapping) else None),
                "duplicate_prevented": bool(result.get("duplicate_prevented", False)),
                "production_touched": False,
                "capability": capability_code,
                "bounded_context": bounded_context,
            }

        if capability_code == "CROSS_DOMAIN_HANDOFF_REGISTER":
            handoff_id = _clean(result.get("handoff_id"))
            if not handoff_id:
                raise WorkerIngressError("HANDOFF_ID_INVALID")
            handoff_payload = {
                "status": _clean(result.get("status")) or "REGISTERED",
                "job_id": _clean(result.get("job_id")) or handoff_id,
                "handoff_id": handoff_id,
                "dependency_id": result.get("dependency_id"),
                "source_domain": result.get("source_domain") or bounded_context,
                "target_domain": result.get("target_domain"),
                "classification": result.get("classification"),
                "lifecycle_state": result.get("lifecycle_state"),
                "certification": result.get("certification"),
                "next_allowed_action": result.get("next_allowed_action"),
                "duplicate_prevented": bool(result.get("duplicate_prevented", False)),
                "handoff_updated": bool(result.get("handoff_updated", False)),
                "reused_certified_resolution": bool(result.get("reused_certified_resolution", False)),
                "production_touched": False,
                "capability": capability_code,
                "bounded_context": bounded_context,
            }
            for extra_key in (
                "executor_status",
                "has_executor",
                "compatible_capabilities",
                "exception_code",
                "resolution_stage",
                "successor_status",
                "resumed_job_id",
                "source_resumed",
            ):
                if extra_key in result:
                    handoff_payload[extra_key] = result.get(extra_key)
            return handoff_payload

        publication = result.get("publication")
        if not isinstance(publication, dict):
            raise WorkerIngressError("SEMANTIC_REPAIR_PUBLICATION_MISSING")

        publication_state = _clean(
            publication.get("publication_status")
        ).upper()
        if publication_state not in {"PUBLISHED", "EXISTS"}:
            raise WorkerIngressError(
                "SEMANTIC_REPAIR_PUBLICATION_NOT_COMMITTED"
            )

        job_id = _clean(
            publication.get("repair_job_id")
            or result.get("job_id")
            or (result.get("job") or {}).get("job_id")
        )
        if not job_id:
            raise WorkerIngressError("SEMANTIC_REPAIR_JOB_ID_MISSING")

        safe = {
            "status": "SUBMITTED",
            "job_id": job_id,
            "production_touched": False,
            "capability": capability_code,
            "bounded_context": bounded_context,
        }
        return safe

    canonical_job = build_semantic_job(
        payload,
        current_user=current_user,
    )
    existing = _resolve_existing_semantic_job(
        canonical_job,
        request_payload=payload,
        requester_email=requester["email"],
    )
    if existing is not None:
        existing_job_id, existing_state = existing
        return {
            "status": "EXISTS",
            "job_id": existing_job_id,
            "existing_lifecycle": existing_state,
            "duplicate_prevented": True,
            "production_touched": False,
            "capability": capability_code,
            "bounded_context": _clean(payload.get("bounded_context")).upper(),
        }

    _check_unpublished_draft_idempotency(canonical_job)

    result = _submit_through_canonical_publisher(canonical_job)
    if not isinstance(result, dict):
        raise WorkerIngressError("CANONICAL_PUBLISHER_INVALID_RESPONSE")

    safe = dict(result)
    safe["job_id"] = _clean(result.get("job_id")) or canonical_job["job_id"]
    safe["production_touched"] = bool(result.get("production_touched", False))
    safe["capability"] = capability_code
    safe["bounded_context"] = _clean(payload.get("bounded_context")).upper()
    safe.pop("template", None)
    _attach_publication_diagnostic(safe)
    return safe


def _read_json_if_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


_RESTRICTED_EVIDENCE_DOMAINS = frozenset({"SEC_RBAC"})
_STATUS_READ_PERMS = frozenset({"rbac_admin", "worker:status", "worker.status", "worker:read", "*"})


def _extract_user_roles_and_perms(current_user: Mapping[str, Any]) -> tuple[set[str], set[str]]:
    role = _clean(
        current_user.get("role")
        or current_user.get("rol")
        or current_user.get("sec_perfil")
    ).lower()
    raw_roles = current_user.get("roles") or current_user.get("sec_roles") or ()
    roles = {role} if role else set()
    if isinstance(raw_roles, (list, tuple, set, frozenset)):
        roles.update(_clean(r).lower() for r in raw_roles if _clean(r))
    raw_perms = current_user.get("permissions") or current_user.get("permisos") or ()
    perms = (
        {_clean(p).lower() for p in raw_perms if _clean(p)}
        if isinstance(raw_perms, (list, tuple, set, frozenset))
        else set()
    )
    return roles, perms


def _infer_canonical_job_domain(
    job_id: str,
    payload: Mapping[str, Any] | None = None,
) -> str | None:
    req_index = _load_canonical_request_index(STATE_ROOT)
    req_entry = req_index.get(job_id)
    if isinstance(req_entry, Mapping):
        req_bc = _clean(req_entry.get("bounded_context")).upper()
        if req_bc:
            return req_bc
    payload_bc = _extract_bounded_context(payload)
    if payload_bc:
        return payload_bc
    upper = _clean(job_id).upper()
    if upper.startswith("SEM-"):
        rest = upper[4:]
        if not rest.startswith("REQUEST-"):
            head = rest.split("-", 1)[0].strip()
            if head:
                return head
    return None


def assert_status_read_access(
    job_id: str,
    *,
    current_user: Mapping[str, Any],
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fail-closed RBAC and domain access verification for reading job status/evidence."""
    if not isinstance(current_user, Mapping):
        raise WorkerIngressError("RBAC_STATUS_READ_FORBIDDEN")
    actor_id = _clean(
        current_user.get("email")
        or current_user.get("id")
        or current_user.get("user_id")
    )
    if not actor_id:
        raise WorkerIngressError("RBAC_STATUS_READ_FORBIDDEN")
    roles, perms = _extract_user_roles_and_perms(current_user)
    is_admin = bool(roles & _ADMIN_MUTATION_ROLES) or bool(perms & {"rbac_admin", "*"})
    if not is_admin and not (perms & _STATUS_READ_PERMS):
        raise WorkerIngressError("RBAC_STATUS_READ_FORBIDDEN")

    domain = _infer_canonical_job_domain(job_id, payload)
    raw_allowed = (
        current_user.get("allowed_domains")
        or current_user.get("domains")
        or current_user.get("bounded_contexts")
    )
    if isinstance(raw_allowed, (list, tuple, set, frozenset)):
        allowed_set = {_clean(d).upper() for d in raw_allowed if _clean(d)}
        if "*" not in allowed_set:
            if not domain or domain not in allowed_set:
                raise WorkerIngressError("RBAC_DOMAIN_ACCESS_FORBIDDEN")

    has_sql = isinstance(payload, Mapping) and (
        payload.get("sql_readonly_evidence") is not None
        or any(
            isinstance(c, Mapping) and c.get("type") == "sql_readonly_audit"
            for c in (payload.get("checks") or [])
        )
    )
    if (domain in _RESTRICTED_EVIDENCE_DOMAINS or has_sql) and not is_admin:
        raise WorkerIngressError("RBAC_DOMAIN_ACCESS_FORBIDDEN")

    return {"authorized": True, "domain": domain, "is_admin": is_admin}


def _safe_terminal_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    from tools.mirror_sync.universal_job_result_publisher import (
        sanitize_maintenance_history_evidence,
        sanitize_readonly_evidence,
        sanitize_repository_evidence,
        sanitize_result_detail_evidence,
        sanitize_semantic_evidence,
    )
    from tools.mirror_sync.worker_result_semantic_extract import (
        sanitize_repository_contract_payload,
    )

    fields = {
        key: payload.get(key)
        for key in _SAFE_RESULT_KEYS
        if key in payload
    }
    # Never expose raw un-revalidated typed evidence directly from payload copy.
    for typed_key in (
        "sql_readonly_evidence",
        "worker_result_semantic_evidence",
        "maintenance_history_evidence",
        "repository_contract_evidence",
        "result_detail_evidence",
        "evidence_availability",
    ):
        fields.pop(typed_key, None)

    payload_dict = dict(payload)
    checks_list = payload_dict.get("checks") if isinstance(payload_dict.get("checks"), list) else []
    check_types = {
        str(c.get("type") or "").strip()
        for c in checks_list
        if isinstance(c, Mapping)
    }
    basis = _clean(payload_dict.get("certification_basis")).upper()

    # 1. Maintenance history evidence (local checks[] or published payload)
    maint_applicable = (
        "worker_maintenance_history_readonly" in check_types
        or "maintenance_history_evidence" in payload_dict
        or "MAINTENANCE_HISTORY" in basis
    )
    maint_raw_seen = (
        payload_dict.get("maintenance_history_evidence") is not None
        or any(
            isinstance(c, Mapping)
            and c.get("type") == "worker_maintenance_history_readonly"
            and (c.get("maintenance_history_evidence") is not None or bool(_clean(c.get("output"))))
            for c in checks_list
        )
    )
    maintenance = sanitize_maintenance_history_evidence(payload_dict)
    if maintenance is None:
        published_maint = payload_dict.get("maintenance_history_evidence")
        if isinstance(published_maint, Mapping):
            m_checks = published_maint.get("checks")
            if isinstance(m_checks, list) and m_checks:
                maintenance = sanitize_maintenance_history_evidence({
                    "checks": [
                        {
                            "type": "worker_maintenance_history_readonly",
                            "maintenance_history_evidence": item,
                        }
                        for item in m_checks
                        if isinstance(item, Mapping)
                    ],
                })
    if maintenance is not None:
        fields["maintenance_history_evidence"] = maintenance

    # 2. Result detail evidence (re-sanitized for both local and published shapes)
    extracted_detail = sanitize_result_detail_evidence(payload_dict)
    if extracted_detail is None and isinstance(payload_dict.get("result_detail_evidence"), Mapping):
        pub_detail_checks = payload_dict["result_detail_evidence"].get("checks")
        if isinstance(pub_detail_checks, list) and pub_detail_checks:
            extracted_detail = sanitize_result_detail_evidence({
                "checks": [
                    {
                        "type": "worker_result_detail_read",
                        "status": "PASS",
                        "result_detail_evidence": {"status": "PASS", **item},
                    }
                    for item in pub_detail_checks
                    if isinstance(item, Mapping)
                ]
            })
    if extracted_detail is not None:
        fields["result_detail_evidence"] = extracted_detail

    # 3. Repository contract evidence
    repo_applicable = (
        "repository_contract_audit" in check_types
        or "repository_contract_evidence" in payload_dict
        or "REPOSITORY" in basis
    )
    repo_raw_seen = (
        payload_dict.get("repository_contract_evidence") is not None
        or any(
            isinstance(c, Mapping)
            and c.get("type") == "repository_contract_audit"
            and c.get("repository_evidence") is not None
            for c in checks_list
        )
    )
    repo_ev: dict[str, Any] | None = None
    if payload_dict.get("repository_contract_evidence") is not None:
        repo_ev = sanitize_repository_contract_payload(payload_dict["repository_contract_evidence"])
    else:
        repo_ev = sanitize_repository_evidence(payload_dict)
    if repo_ev is not None:
        fields["repository_contract_evidence"] = repo_ev
    repo_truncated = bool(
        isinstance(repo_ev, dict)
        and any(
            isinstance(item, dict) and item.get("truncated") is True
            for item in (repo_ev.get("checks") or [])
        )
    )

    # 4. SQL readonly evidence (local checks[] or published sql_readonly_evidence)
    sql_applicable = (
        "sql_readonly_audit" in check_types
        or "sql_readonly_evidence" in payload_dict
        or "READ_ONLY_SQL" in basis
    )
    sql_raw_seen = (
        payload_dict.get("sql_readonly_evidence") is not None
        or any(
            isinstance(c, Mapping)
            and c.get("type") == "sql_readonly_audit"
            and (c.get("sql_evidence") is not None or bool(_clean(c.get("output"))))
            for c in checks_list
        )
    )
    sql_ev = sanitize_readonly_evidence(payload_dict) if sql_applicable else None
    if sql_ev is not None:
        fields["sql_readonly_evidence"] = sql_ev
    sql_truncated = bool(
        isinstance(sql_ev, dict)
        and any(
            isinstance(entry, dict) and entry.get("truncated") is True
            for chk in (sql_ev.get("checks") or [])
            if isinstance(chk, dict)
            for entry in (chk.get("evidence") or [])
        )
    )

    # 5. Semantic extract evidence (local checks[] or published worker_result_semantic_evidence)
    sem_applicable = (
        "worker_result_semantic_extract" in check_types
        or "worker_result_semantic_evidence" in payload_dict
        or "SEMANTIC_EXTRACT" in basis
    )
    sem_raw_seen = (
        payload_dict.get("worker_result_semantic_evidence") is not None
        or any(
            isinstance(c, Mapping)
            and c.get("type") == "worker_result_semantic_extract"
            and (c.get("semantic_evidence") is not None or bool(_clean(c.get("output"))))
            for c in checks_list
        )
    )
    sem_ev = sanitize_semantic_evidence(payload_dict) if sem_applicable else None
    if sem_ev is not None:
        fields["worker_result_semantic_evidence"] = sem_ev

    def _ev_channel(ev: dict[str, Any] | None, *, applicable: bool, raw_seen: bool, truncated: bool = False) -> str:
        if ev is not None:
            return "TRUNCATED" if truncated else "COMPLETE"
        if raw_seen:
            return "REJECTED_UNSAFE_OR_OVERSIZED"
        if applicable:
            return "ABSENT"
        return "NOT_APPLICABLE"

    availability = {
        "repository_contract_evidence": _ev_channel(
            repo_ev, applicable=repo_applicable, raw_seen=repo_raw_seen, truncated=repo_truncated
        ),
        "sql_readonly_evidence": _ev_channel(
            sql_ev, applicable=sql_applicable, raw_seen=sql_raw_seen, truncated=sql_truncated
        ),
        "worker_result_semantic_evidence": _ev_channel(
            sem_ev, applicable=sem_applicable, raw_seen=sem_raw_seen, truncated=False
        ),
        "maintenance_history_evidence": _ev_channel(
            maintenance, applicable=maint_applicable, raw_seen=maint_raw_seen, truncated=False
        ),
    }
    fields["evidence_availability"] = availability

    any_recovered = any(x is not None for x in (repo_ev, sql_ev, sem_ev, maintenance))
    any_rejected = any(v == "REJECTED_UNSAFE_OR_OVERSIZED" for v in availability.values())
    any_absent = any(v == "ABSENT" for v in availability.values())
    any_truncated = bool(repo_truncated or sql_truncated)

    if any_rejected and not any_recovered:
        fields["evidence_status"] = "REJECTED_UNSAFE_OR_OVERSIZED"
        fields["evidence_truncated"] = False
    elif any_recovered:
        fields["evidence_truncated"] = any_truncated
        fields["evidence_status"] = (
            "REJECTED_UNSAFE_OR_OVERSIZED"
            if any_rejected
            else ("TRUNCATED" if any_truncated else "COMPLETE")
        )
    elif isinstance(fields.get("result_detail_evidence"), dict):
        detail_checks = fields["result_detail_evidence"].get("checks") or []
        if detail_checks and isinstance(detail_checks[0], dict):
            first = detail_checks[0]
            if "evidence_status" in first:
                fields.setdefault("evidence_status", first["evidence_status"])
            if "evidence_truncated" in first:
                fields.setdefault("evidence_truncated", first["evidence_truncated"])
            if isinstance(first.get("evidence_availability"), dict):
                fields["evidence_availability"] = dict(first["evidence_availability"])
        fields.setdefault("evidence_status", "ABSENT" if any_absent else "NOT_APPLICABLE")
        fields.setdefault("evidence_truncated", False)
    else:
        fields["evidence_status"] = "ABSENT" if any_absent else "NOT_APPLICABLE"
        fields["evidence_truncated"] = False

    return fields


def _read_remote_worker_result(job_id: str) -> dict[str, Any] | None:
    """Read-only fallback to origin/worker/results when a certified job is absent locally."""
    import subprocess
    from tools.mirror_sync.worker_result_integrity import (
        validate_terminal_result_payload,
    )

    git_dir = STATE_ROOT.parent
    if not (git_dir / "HEAD").is_file():
        return None
    spec = f"origin/worker/results:worker_queue/results/{job_id}.json"
    try:
        proc = subprocess.run(
            ["git", f"--git-dir={git_dir}", "cat-file", "-p", spec],
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0 or not proc.stdout:
        return None
    try:
        payload = json.loads(proc.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    try:
        validate_terminal_result_payload(payload, expected_job_id=job_id)
    except ValueError:
        return None
    if (
        payload.get("invalid_result_artifact") is True
        or str(payload.get("status") or "").strip().upper() == "INVALID_RESULT_ARTIFACT"
    ):
        return None
    response: dict[str, Any] = {
        "job_id": job_id,
        "lifecycle": "RESULT",
        "terminal_result_valid": True,
        "result_state": "RESULT_TERMINAL_VALID",
        "reconciliation_status": "REMOTE_RESULTS_VERIFIED",
        "production_touched": bool(payload.get("production_touched", False)),
    }
    response.update(_safe_terminal_fields(payload))
    if not response.get("commit_sha"):
        commit_sha = (
            payload.get("certified_source_sha")
            or payload.get("development_sha")
            or payload.get("integrated_commit")
        )
        if commit_sha:
            response["commit_sha"] = commit_sha
    return response


def get_job_status(
    job_id: str,
    *,
    current_user: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    value = _clean(job_id)
    if not JOB_ID_RE.fullmatch(value):
        raise WorkerIngressError("JOB_ID_INVALID")
    if current_user is not None:
        assert_status_read_access(value, current_user=current_user)

    preview_path = STATE_ROOT / "preview_validations" / f"{value}.json"
    preview_evidence = (
        _read_json_if_object(preview_path)
        if preview_path.is_file()
        else None
    )

    result_path = STATE_ROOT / "results" / f"{value}.json"
    if result_path.is_file():
        result_read = read_canonical_result(
            result_path,
            expected_job_id=value,
        )
        status = build_job_status(
            result_read=result_read,
            preview_evidence=preview_evidence,
        )
        if result_read.terminal_result_valid and isinstance(
            result_read.payload, dict
        ):
            if current_user is not None:
                assert_status_read_access(
                    value,
                    current_user=current_user,
                    payload=result_read.payload,
                )
            status.update(_safe_terminal_fields(result_read.payload))
            if not status.get("commit_sha"):
                commit_sha = (
                    result_read.payload.get("certified_source_sha")
                    or result_read.payload.get("development_sha")
                    or result_read.payload.get("integrated_commit")
                )
                if commit_sha:
                    status["commit_sha"] = commit_sha
        status["lifecycle"] = "RESULT"
        return status

    rejected_path = STATE_ROOT / "rejected" / f"{value}.json"
    if rejected_path.is_file():
        payload = _read_json_if_object(rejected_path)
        response: dict[str, Any] = {
            "job_id": value,
            "lifecycle": "REJECTED",
            "status": str(payload.get("status") or "REJECTED"),
            "quality_gate": "FAIL",
            "tests": "FAIL",
            "certification": "NOT_CERTIFIED",
            "work_completion": "REJECTED",
            "percent_complete": 0,
            "blockers": list(payload.get("blockers") or ["job_rejected"]),
            "terminal_result_valid": False,
            "result_state": "RESULT_REJECTED",
            "production_touched": False,
        }
        for key in ("completed_at_utc", "summary_es"):
            if key in payload:
                response[key] = payload[key]
        return response

    published_path = STATE_ROOT / "published" / f"{value}.json"
    done_path = STATE_ROOT / "done" / f"{value}.json"
    if published_path.is_file() or done_path.is_file():
        absent_read = read_canonical_result(
            result_path,
            expected_job_id=value,
        )
        status = build_job_status(result_read=absent_read)
        status["lifecycle"] = "RESULT"
        return status

    non_terminal_dirs = (
        ("PROCESSING", "processing"),
        ("PENDING", "pending"),
        ("DRAFT", "drafts"),
    )

    for lifecycle, directory in non_terminal_dirs:
        path = STATE_ROOT / directory / f"{value}.json"
        if not path.is_file():
            continue
        payload = _read_json_if_object(path)
        return {
            "job_id": value,
            "lifecycle": lifecycle,
            "lifecycle_stage": "SUBMITTED",
            "status": lifecycle,
            "certification": "NOT_CERTIFIED",
            "code_certified": False,
            "operational_validated": False,
            "operational_validation_status": "PENDING_PREVIEW_VALIDATION",
            "work_completion": lifecycle,
            "percent_complete": 0,
            "terminal_result_valid": False,
            "result_state": "RESULT_NON_TERMINAL",
            "production_touched": False,
            "summary_es": payload.get("summary_es"),
        }

    remote_result = _read_remote_worker_result(value)
    if remote_result is not None:
        return remote_result

    return {
        "job_id": value,
        "lifecycle": "NOT_FOUND",
        "status": "NOT_FOUND",
        "production_touched": False,
    }


_AMBIGUOUS_DOMAINS = frozenset({"", "*", "ALL", "ANY", "GENERAL", "GLOBAL", "UNKNOWN", "DEFAULT", "MISC"})
_DOMAIN_TOKEN_RE = re.compile(r"^[A-Z0-9][A-Z0-9._-]{1,119}$")
_CERTIFIED_CONTEXT_STATES = frozenset({
    "CERTIFIED",
    "CERTIFIED_READ_ONLY",
    "CERTIFIED_OPERATIONAL",
    "CERTIFIED_FRONTEND_BUILD",
})
_EPOCH_ZERO_UTC = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _parse_utc_timestamp(value: Any) -> datetime | None:
    raw = _clean(value)
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _extract_bounded_context(payload: Mapping[str, Any] | None) -> str:
    """Extract canonical bounded_context from either raw job or worker queue envelope."""
    if not isinstance(payload, Mapping):
        return ""
    scheduling = payload.get("scheduling")
    if isinstance(scheduling, Mapping):
        bc = _clean(scheduling.get("bounded_context")).upper()
        if bc:
            return bc
    inner = payload.get("job")
    if isinstance(inner, Mapping):
        inner_sched = inner.get("scheduling")
        if isinstance(inner_sched, Mapping):
            bc = _clean(inner_sched.get("bounded_context")).upper()
            if bc:
                return bc
    return ""


def _extract_envelope_job(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {}
    inner = payload.get("job")
    if isinstance(inner, Mapping):
        return dict(inner)
    return dict(payload)


_GO_CONTEXT_CACHE_LOCK = threading.Lock()
_GO_CONTEXT_CACHE: dict[str, dict[str, Any]] = {}
_GO_CONTEXT_DISK_INDEX_SCHEMA = "edarsahub.go-context-snapshot-index.v1"
_GO_CONTEXT_DISK_INDEX_NAME = "go_context_snapshot_index.v1.json"


def _queue_dir_signature(folder: Path) -> str:
    """Fast directory signature (mtime_ns + json file count) for zero-stale cache invalidation."""
    try:
        if not folder.is_dir():
            return "ABSENT"
        st = folder.stat()
        import os

        count = 0
        latest_mtime = st.st_mtime_ns
        with os.scandir(folder) as it:
            for entry in it:
                if entry.name.endswith(".json") and entry.is_file(follow_symlinks=False):
                    count += 1
        return f"{latest_mtime}:{count}"
    except OSError:
        return "ERROR"


def _scan_json_dir_stats(folder: Path) -> dict[str, tuple[int, int]]:
    """Fast os.scandir map of stem -> (mtime_ns, size) for incremental disk-index validation."""
    import os

    out: dict[str, tuple[int, int]] = {}
    if not folder.is_dir():
        return out
    try:
        with os.scandir(folder) as it:
            for entry in it:
                name = entry.name
                if not name.endswith(".json"):
                    continue
                try:
                    st = entry.stat(follow_symlinks=False)
                except OSError:
                    continue
                if entry.is_file(follow_symlinks=False):
                    out[name[:-5]] = (int(st.st_mtime_ns), int(st.st_size))
    except OSError:
        return out
    return out


def _fast_extract_result_bounded_context(path: Path) -> str:
    """Avoid parsing multi-megabyte result JSONs unless they actually contain 'bounded_context'."""
    try:
        raw_bytes = path.read_bytes()
    except OSError:
        return ""
    if b"bounded_context" not in raw_bytes:
        return ""
    try:
        obj = json.loads(raw_bytes.decode("utf-8", errors="replace"))
    except (ValueError, json.JSONDecodeError):
        return ""
    return _extract_bounded_context(obj) if isinstance(obj, Mapping) else ""


def _read_disk_snapshot_index(state_root: Path) -> dict[str, Any]:
    path = state_root / "runtime" / _GO_CONTEXT_DISK_INDEX_NAME
    if not path.is_file():
        return {}
    data = _read_json_if_object(path)
    if data.get("schema") != _GO_CONTEXT_DISK_INDEX_SCHEMA:
        return {}
    return data


def _write_disk_snapshot_index_best_effort(state_root: Path, payload: dict[str, Any]) -> None:
    import os
    import tempfile

    runtime_dir = state_root / "runtime"
    try:
        runtime_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=runtime_dir,
            prefix="go_context_idx_",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            tmp_name = handle.name
        os.replace(tmp_name, runtime_dir / _GO_CONTEXT_DISK_INDEX_NAME)
    except OSError:
        return


def _load_cached_queue_snapshot(state_root: Path) -> tuple[dict[str, Any], bool]:
    """Return a cached, directory-signature-validated snapshot with incremental disk persistence.

    Eliminates both warm-cache and cold-cache 504 timeouts across MCP/backend restarts while
    guaranteeing immediate invalidation whenever any individual queue artifact changes.
    """
    dirs = ("done", "processing", "pending", "drafts", "rejected", "results", "published")
    sig = tuple((d, _queue_dir_signature(state_root / d)) for d in dirs)
    cache_key = str(state_root)

    with _GO_CONTEXT_CACHE_LOCK:
        entry = _GO_CONTEXT_CACHE.get(cache_key)
        if entry is not None and entry.get("sig") == sig:
            return entry["snapshot"], True

    disk_idx = _read_disk_snapshot_index(state_root)
    disk_req_entries = disk_idx.get("req_entries") if isinstance(disk_idx.get("req_entries"), dict) else {}
    disk_res_entries = disk_idx.get("res_entries") if isinstance(disk_idx.get("res_entries"), dict) else {}
    disk_dirty = not bool(disk_idx)

    # 1. Build lightweight request_index incrementally using per-file (mtime_ns, size)
    request_index: dict[str, dict[str, Any]] = {}
    new_req_entries: dict[str, list[Any]] = {}
    for source_name, dirname in (
        ("DONE", "done"),
        ("PROCESSING", "processing"),
        ("PENDING", "pending"),
        ("DRAFT", "drafts"),
    ):
        folder = state_root / dirname
        stats = _scan_json_dir_stats(folder)
        for stem in sorted(stats):
            mtime_ns, size = stats[stem]
            dkey = f"{dirname}/{stem}"
            cached = disk_req_entries.get(dkey)
            if (
                isinstance(cached, list)
                and len(cached) == 6
                and cached[0] == mtime_ns
                and cached[1] == size
            ):
                jid, bc, mode, objective = cached[2], cached[3], cached[4], cached[5]
            else:
                disk_dirty = True
                raw = _read_json_if_object(folder / f"{stem}.json")
                if not raw:
                    new_req_entries[dkey] = [mtime_ns, size, "", "", None, None]
                    continue
                inner = _extract_envelope_job(raw)
                jid = _clean(inner.get("job_id") or raw.get("job_id")) or stem
                if not jid:
                    new_req_entries[dkey] = [mtime_ns, size, "", "", None, None]
                    continue
                bc = _extract_bounded_context(raw)
                mode = _clean(inner.get("mode")).upper() or None
                objective = _clean(inner.get("objective"))[:240] or None
                cached = [mtime_ns, size, jid, bc, mode, objective]
            new_req_entries[dkey] = cached
            if not jid:
                continue
            existing = request_index.get(jid)
            if existing is None or (not existing.get("bounded_context") and bc):
                request_index[jid] = {
                    "job_id": jid,
                    "bounded_context": bc,
                    "request_source": source_name,
                    "mode": mode,
                    "objective": objective,
                }

    # 2. Collect known non-draft stems via fast scandir
    res_stats = _scan_json_dir_stats(state_root / "results")
    done_stats = _scan_json_dir_stats(state_root / "done")
    rej_stats = _scan_json_dir_stats(state_root / "rejected")
    proc_stats = _scan_json_dir_stats(state_root / "processing")
    pend_stats = _scan_json_dir_stats(state_root / "pending")
    known_non_draft_ids: set[str] = (
        set(res_stats) | set(done_stats) | set(rej_stats) | set(proc_stats) | set(pend_stats)
    )

    # 3. Pre-index unpublished drafts (typically < 50 files)
    unpublished_drafts: list[tuple[str, dict[str, Any]]] = []
    drafts_dir = state_root / "drafts"
    draft_stats = _scan_json_dir_stats(drafts_dir)
    for jid_stem in sorted(draft_stats):
        if jid_stem in known_non_draft_ids:
            continue
        payload = _read_json_if_object(drafts_dir / f"{jid_stem}.json")
        if not payload:
            continue
        jid = _clean(payload.get("job_id")) or jid_stem
        if not jid or jid in known_non_draft_ids:
            continue
        unpublished_drafts.append((jid, payload))

    # 4. Pre-index result headers incrementally (zero re-reading of unchanged results across cold starts!)
    results_dir = state_root / "results"
    result_index_by_domain: dict[str, list[tuple[str, Path, str]]] = {}
    legacy_result_stems: list[tuple[str, Path]] = []
    new_res_entries: dict[str, list[Any]] = {}
    for jid in sorted(res_stats):
        path = results_dir / f"{jid}.json"
        req_entry = request_index.get(jid)
        req_bc = _clean(req_entry.get("bounded_context")).upper() if isinstance(req_entry, Mapping) else ""
        if req_bc:
            result_index_by_domain.setdefault(req_bc, []).append((jid, path, "REQUEST_SCHEDULING"))
            continue
        mtime_ns, size = res_stats[jid]
        cached_res = disk_res_entries.get(jid)
        if (
            isinstance(cached_res, list)
            and len(cached_res) == 3
            and cached_res[0] == mtime_ns
            and cached_res[1] == size
        ):
            payload_bc = str(cached_res[2] or "")
        else:
            disk_dirty = True
            payload_bc = _fast_extract_result_bounded_context(path)
            cached_res = [mtime_ns, size, payload_bc]
        new_res_entries[jid] = cached_res
        if payload_bc:
            result_index_by_domain.setdefault(payload_bc, []).append((jid, path, "PAYLOAD_SCHEDULING"))
        else:
            legacy_result_stems.append((jid, path))

    if disk_dirty or len(new_req_entries) != len(disk_req_entries) or len(new_res_entries) != len(disk_res_entries):
        _write_disk_snapshot_index_best_effort(
            state_root,
            {
                "schema": _GO_CONTEXT_DISK_INDEX_SCHEMA,
                "updated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "req_entries": new_req_entries,
                "res_entries": new_res_entries,
                "production_touched": False,
            },
        )

    snapshot = {
        "request_index": request_index,
        "known_non_draft_ids": known_non_draft_ids,
        "unpublished_drafts": unpublished_drafts,
        "result_index_by_domain": result_index_by_domain,
        "legacy_result_stems": legacy_result_stems,
        "disk_index_reused": bool(disk_idx and not disk_dirty),
    }
    with _GO_CONTEXT_CACHE_LOCK:
        if len(_GO_CONTEXT_CACHE) >= 16:
            _GO_CONTEXT_CACHE.clear()
        _GO_CONTEXT_CACHE[cache_key] = {"sig": sig, "snapshot": snapshot}
    return snapshot, False


def _load_canonical_request_index(state_root: Path) -> dict[str, dict[str, Any]]:
    """Build read-only request index associating job_id with canonical scheduling & metadata."""
    index: dict[str, dict[str, Any]] = {}
    for source_name, dirname in (
        ("DONE", "done"),
        ("PROCESSING", "processing"),
        ("PENDING", "pending"),
        ("DRAFT", "drafts"),
    ):
        folder = state_root / dirname
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.json"), key=lambda p: p.name):
            raw = _read_json_if_object(path)
            if not raw:
                continue
            inner = _extract_envelope_job(raw)
            jid = _clean(inner.get("job_id") or raw.get("job_id")) or path.stem
            if not jid:
                continue
            bc = _extract_bounded_context(raw)
            existing = index.get(jid)
            if existing is None or (not existing.get("bounded_context") and bc):
                index[jid] = {
                    "job_id": jid,
                    "bounded_context": bc,
                    "request_source": source_name,
                    "mode": _clean(inner.get("mode")).upper() or None,
                    "objective": _clean(inner.get("objective")) or None,
                    "job": inner,
                }
    return index


def _legacy_job_id_matches_domain(job_id: str, domain_upper: str) -> bool:
    jid_upper = job_id.upper()
    if f"SEM-{domain_upper}-" in jid_upper:
        return True
    if f"-{domain_upper}-" in jid_upper or jid_upper.startswith(f"{domain_upper}-"):
        return True
    tokens = [tok for tok in re.split(r"[^A-Z0-9]+", jid_upper) if tok]
    return domain_upper in tokens


def _resolve_job_domain(
    job_id: str,
    payload: Mapping[str, Any] | None,
    domain_upper: str,
    *,
    request_index: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[bool, str | None]:
    """Strictly isolate jobs by canonical request binding before any legacy fallback."""
    if isinstance(request_index, Mapping):
        req_entry = request_index.get(job_id)
        if isinstance(req_entry, Mapping):
            req_bc = _clean(req_entry.get("bounded_context")).upper()
            if req_bc:
                return (req_bc == domain_upper, "REQUEST_SCHEDULING" if req_bc == domain_upper else None)
    payload_bc = _extract_bounded_context(payload)
    if payload_bc:
        return (payload_bc == domain_upper, "PAYLOAD_SCHEDULING" if payload_bc == domain_upper else None)
    if _legacy_job_id_matches_domain(job_id, domain_upper):
        return (True, "LEGACY_JOB_ID_TOKEN")
    return (False, None)


def _job_matches_domain(
    job_id: str,
    payload: Mapping[str, Any],
    domain_upper: str,
    *,
    request_index: Mapping[str, Mapping[str, Any]] | None = None,
) -> bool:
    """Strictly isolate jobs by domain so RRHH, CRM, Finanzas, etc. are never mixed."""
    matched, _ = _resolve_job_domain(
        job_id,
        payload,
        domain_upper,
        request_index=request_index,
    )
    return matched


def _evaluate_explicit_mutation_authorization(
    *,
    domain_upper: str,
    authorization_context: Mapping[str, Any] | None,
    now_utc: datetime | None = None,
) -> tuple[bool, str, str | None]:
    """Require explicit, traceable, non-revoked, non-expired, domain-scoped mutation auth.

    Never infers mutation authorization from RBAC alone or from objective_hint text.
    """
    if not isinstance(authorization_context, Mapping) or not authorization_context:
        return False, "NO_EXPLICIT_MUTATION_AUTHORIZATION", None

    auth_id = _clean(
        authorization_context.get("authorization_id")
        or authorization_context.get("authorization_ref")
    )
    if authorization_context.get("production_allowed") is True:
        return False, "PRODUCTION_FORBIDDEN", auth_id or None
    if authorization_context.get("revoked") is True:
        return False, "AUTHORIZATION_REVOKED", auth_id or None
    if not auth_id:
        return False, "AUTHORIZATION_NOT_TRACEABLE", None

    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    expires_raw = authorization_context.get("expires_at_utc")
    if expires_raw is not None:
        expires_dt = _parse_utc_timestamp(expires_raw)
        if expires_dt is None or expires_dt <= now:
            return False, "AUTHORIZATION_EXPIRED", auth_id

    raw_classes = authorization_context.get("authorization_classes") or ()
    auth_classes = {
        _clean(c).upper()
        for c in (raw_classes if isinstance(raw_classes, (list, tuple, set, frozenset)) else (raw_classes,))
        if _clean(c)
    }
    explicitly_granted = (
        authorization_context.get("mutation_authorized") is True
        or bool(auth_classes & {"DEVELOPMENT_MUTATION", "PREAUTHORIZED_CODE_MUTATION"})
    )
    if not explicitly_granted:
        return False, "MUTATION_NOT_EXPLICITLY_AUTHORIZED", auth_id

    scope_obj = authorization_context.get("scope")
    granted_scope = scope_obj if isinstance(scope_obj, Mapping) else authorization_context
    raw_domains = granted_scope.get("domains")
    if raw_domains is None:
        raw_domains = granted_scope.get("domain")
    if isinstance(raw_domains, (list, tuple, set, frozenset)):
        domain_vals = {_clean(d).upper() for d in raw_domains if _clean(d)}
    else:
        single = _clean(raw_domains).upper()
        domain_vals = {single} if single else set()
    if not domain_vals or "*" in domain_vals or domain_upper not in domain_vals:
        return False, "SCOPE_AUTHORIZATION_DENIED", auth_id

    return True, "EXPLICIT_AUTHORIZATION_VERIFIED", auth_id


def _load_certified_domain_results(
    *,
    state_root: Path,
    domain_upper: str,
    request_index: Mapping[str, Mapping[str, Any]],
    snapshot: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return certified results for one domain sorted deterministically by verifiable UTC timestamps."""
    from tools.mirror_sync.worker_result_reader import parse_published_marker

    results_dir = state_root / "results"
    if not results_dir.is_dir():
        return []
    published_dir = state_root / "published"
    entries: list[tuple[tuple[int, datetime, int, datetime, str], dict[str, Any]]] = []

    candidates: list[tuple[str, Path, str | None]] = []
    if isinstance(snapshot, Mapping):
        for jid, path, source in (snapshot.get("result_index_by_domain") or {}).get(domain_upper, ()):
            candidates.append((jid, path, source))
        for jid, path in snapshot.get("legacy_result_stems") or ():
            if _legacy_job_id_matches_domain(jid, domain_upper):
                candidates.append((jid, path, "LEGACY_JOB_ID_TOKEN"))
    else:
        for path in sorted(results_dir.glob("*.json"), key=lambda p: p.name):
            jid = path.stem
            raw = _read_json_if_object(path)
            if not raw:
                continue
            matched, binding_source = _resolve_job_domain(
                jid,
                raw,
                domain_upper,
                request_index=request_index,
            )
            if matched:
                candidates.append((jid, path, binding_source))

    for jid, path, binding_source in candidates:
        read = read_canonical_result(path, expected_job_id=jid)
        if not read.terminal_result_valid or not isinstance(read.payload, dict):
            continue

        payload = read.payload
        if payload.get("production_touched") is not False:
            continue
        if _clean(payload.get("tests")).upper() != "PASS" or _clean(payload.get("quality_gate")).upper() != "PASS":
            continue
        if payload.get("blockers"):
            continue

        cert = _clean(payload.get("certification")).upper()
        completed_at_utc = _clean(payload.get("completed_at_utc")) or None
        certified_at_utc = completed_at_utc
        published_commit = _clean(payload.get("published_result_commit")) or None
        cert_source = "CANONICAL_RESULT"

        marker_path = published_dir / f"{jid}.json"
        if marker_path.is_file():
            marker = parse_published_marker(marker_path)
            if isinstance(marker, dict) and "_invalid" not in marker:
                m_cert = _clean(marker.get("certification")).upper()
                if m_cert in _CERTIFIED_CONTEXT_STATES:
                    cert = m_cert
                    cert_source = "PUBLISHED_MARKER"
                    m_pub = _clean(marker.get("published"))
                    if m_pub:
                        certified_at_utc = m_pub
                    m_commit = _clean(marker.get("commit"))
                    if m_commit:
                        published_commit = m_commit

        if cert not in _CERTIFIED_CONTEXT_STATES:
            continue

        cert_dt = _parse_utc_timestamp(certified_at_utc)
        comp_dt = _parse_utc_timestamp(completed_at_utc)
        req_entry = request_index.get(jid) or {}
        record = {
            "job_id": jid,
            "status": payload.get("status"),
            "certification": cert,
            "certification_source": cert_source,
            "commit_sha": (
                payload.get("certified_source_sha")
                or payload.get("development_sha")
                or payload.get("candidate_sha")
                or payload.get("commit_sha")
            ),
            "published_result_commit": published_commit,
            "completed_at_utc": completed_at_utc,
            "certified_at_utc": certified_at_utc,
            "certified_timestamp_verified": cert_dt is not None,
            "mode": req_entry.get("mode") or _clean(payload.get("mode")).upper() or None,
            "domain_binding_source": binding_source,
            "lifecycle": "RESULT",
        }
        sort_key = (
            1 if cert_dt is not None else 0,
            cert_dt or _EPOCH_ZERO_UTC,
            1 if comp_dt is not None else 0,
            comp_dt or _EPOCH_ZERO_UTC,
            jid,
        )
        entries.append((sort_key, record))

    entries.sort(key=lambda pair: pair[0], reverse=True)
    return [record for _, record in entries]


def resolve_go_context(
    *,
    domain: str,
    current_user: Mapping[str, Any],
    project: str = "EDARSAHUB",
    chain_id: str | None = None,
    objective_hint: str | None = None,
    authorization_context: Mapping[str, Any] | None = None,
    config_dir: Path | None = None,
) -> dict[str, Any]:
    """Canonical GO context resolver across chats using only existing queue & gate-chain registries.

    Never creates per-chat databases or parallel operational memory.
    Fails closed (mutation_allowed=False) when context is ambiguous, drafts are pending recovery,
    policy_tier is READ_ONLY, or explicit mutation authorization is absent/unverified.
    """
    from tools.mirror_sync.gate_chain_controller import (
        classify_policy_tier,
        evaluate_gate_authorization,
    )
    from tools.mirror_sync.gate_chain_reconciler import reconcile_chain

    domain_upper = _clean(domain).upper()
    project_clean = _clean(project) or "EDARSAHUB"
    hint_clean = _clean(objective_hint)
    chain_clean = _clean(chain_id)

    try:
        requester = _requester_from_authenticated_user(current_user, project=project_clean)
        identity_verified = True
    except WorkerIngressError:
        requester = {"email": "", "source": "edarsahub-worker-ingress", "project": project_clean}
        identity_verified = False

    try:
        _assert_mutation_rbac(current_user)
        rbac_mutation_ok = True
    except WorkerIngressError:
        rbac_mutation_ok = False

    if (
        not domain_upper
        or domain_upper in _AMBIGUOUS_DOMAINS
        or not _DOMAIN_TOKEN_RE.fullmatch(domain_upper)
    ):
        return {
            "schema": "edarsahub.worker-go-context.v1",
            "project": project_clean,
            "domain": domain_upper or None,
            "active_objective": hint_clean or None,
            "chain_id": chain_clean or None,
            "last_certified_gate": None,
            "certified_successors": [],
            "pending_jobs": [],
            "pending_drafts": [],
            "lifecycle_summary": {"DRAFT": [], "PENDING": [], "PROCESSING": [], "RESULT": []},
            "active_authorizations": {
                "identity_verified": identity_verified,
                "actor_email": requester.get("email") or None,
                "rbac_mutation_authorized": rbac_mutation_ok,
                "explicit_mutation_authorized": False,
                "explicit_authorization_status": "AMBIGUOUS_DOMAIN_CONTEXT",
                "explicit_authorization_id": None,
                "chain_authorization_status": "NOT_EVALUATED",
            },
            "gate_dependencies": [],
            "policy_tier": "HUMAN_APPROVAL_REQUIRED",
            "mutation_allowed": False,
            "next_allowed_action": "REQUEST_MINIMUM_INFO",
            "reason": "AMBIGUOUS_DOMAIN_CONTEXT",
            "missing_fields": ["domain"],
            "production_touched": False,
        }

    t_start = time.monotonic()
    # Build or reuse directory-signature-validated queue snapshot (eliminates 504 timeouts!)
    snapshot, cache_hit = _load_cached_queue_snapshot(STATE_ROOT)
    request_index = snapshot["request_index"]
    known_non_draft_ids = snapshot["known_non_draft_ids"]

    # Discover domain-scoped in-flight jobs (PROCESSING / PENDING) strictly separated by lifecycle
    processing_ids: list[str] = []
    pending_ids: list[str] = []
    pending_jobs: list[dict[str, Any]] = []
    seen_in_flight: set[str] = set()
    for lifecycle, dirname in (("PROCESSING", "processing"), ("PENDING", "pending")):
        folder = STATE_ROOT / dirname
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.json"), key=lambda p: p.name):
            payload = _read_json_if_object(path)
            inner = _extract_envelope_job(payload)
            jid = _clean(inner.get("job_id") or payload.get("job_id")) or path.stem
            if not jid or jid in seen_in_flight:
                continue
            matched, binding_source = _resolve_job_domain(
                jid,
                payload,
                domain_upper,
                request_index=request_index,
            )
            if matched:
                seen_in_flight.add(jid)
                pending_jobs.append({
                    "job_id": jid,
                    "lifecycle": lifecycle,
                    "domain_binding_source": binding_source,
                })
                if lifecycle == "PROCESSING":
                    processing_ids.append(jid)
                else:
                    pending_ids.append(jid)

    # Discover domain-scoped unpublished drafts pending idempotent recovery (DRAFT)
    # Exclude drafts explicitly recorded as historical abandoned in the canonical reconciliation ledger
    # so ancient abandoned drafts do not hijack active domain continuity.
    hist_ledger = _read_json_if_object(STATE_ROOT / "maintenance" / "historical_reconciliation_ledger.json")
    hist_drafts_map = (
        hist_ledger.get("historical_drafts_classified")
        if isinstance(hist_ledger.get("historical_drafts_classified"), Mapping)
        else {}
    )
    pending_drafts: list[dict[str, Any]] = []
    historical_reconciled_drafts: list[dict[str, Any]] = []
    draft_ids: list[str] = []
    for jid, payload in snapshot["unpublished_drafts"]:
        matched, binding_source = _resolve_job_domain(
            jid,
            payload,
            domain_upper,
            request_index=request_index,
        )
        if matched:
            if jid in hist_drafts_map:
                historical_reconciled_drafts.append({
                    "job_id": jid,
                    "lifecycle": "HISTORICAL_DRAFT_RECONCILED",
                    "classification": hist_drafts_map[jid].get("classification"),
                    "domain_binding_source": binding_source,
                })
                continue
            draft_ids.append(jid)
            pending_drafts.append({
                "job_id": jid,
                "lifecycle": "DRAFT",
                "recovery_required": True,
                "draft_fingerprint": _canonical_request_fingerprint(payload),
                "domain_binding_source": binding_source,
            })

    # Discover certified results for this domain ordered by verifiable UTC timestamp (never mtime)
    certified_results = _load_certified_domain_results(
        state_root=STATE_ROOT,
        domain_upper=domain_upper,
        request_index=request_index,
        snapshot=snapshot,
    )
    last_certified: dict[str, Any] | None = certified_results[0] if certified_results else None
    certified_successors: list[dict[str, Any]] = certified_results[:5]
    certified_by_job_id = {row["job_id"]: row for row in certified_results}

    # Optional registered gate-chain reconciliation (read-only) with strict domain validation
    chains_root = config_dir or (REPO_ROOT / "worker_queue" / "config" / "gate_chains")
    matched_chain: dict[str, Any] | None = None
    chain_reconcile: dict[str, Any] | None = None
    chain_error: str | None = None
    gate_dependencies: list[dict[str, Any]] = []
    policy_tier = "READ_ONLY"
    chain_auth_reason = "NOT_APPLICABLE"

    domain_enabled_chains: list[dict[str, Any]] = []
    requested_chain_cfg: dict[str, Any] | None = None
    if chains_root.is_dir():
        for cpath in sorted(chains_root.glob("*.json"), key=lambda p: p.name):
            cfg = _read_json_if_object(cpath)
            if not cfg or cfg.get("schema") != "edarsahub.gate-chain.v1":
                continue
            cid = _clean(cfg.get("chain_id"))
            cfg_domain = _clean(cfg.get("domain") or cfg.get("bounded_context")).upper()
            if chain_clean:
                if cid == chain_clean:
                    requested_chain_cfg = cfg
                    break
            elif cfg_domain == domain_upper and cfg.get("enabled") is True:
                domain_enabled_chains.append(cfg)

    if chain_clean:
        if requested_chain_cfg is None:
            chain_error = "CHAIN_NOT_FOUND"
        else:
            cfg_domain = _clean(
                requested_chain_cfg.get("domain") or requested_chain_cfg.get("bounded_context")
            ).upper()
            if not cfg_domain or cfg_domain != domain_upper:
                chain_error = "CHAIN_DOMAIN_MISMATCH"
            else:
                matched_chain = requested_chain_cfg
    elif len(domain_enabled_chains) > 1:
        chain_error = "AMBIGUOUS_DOMAIN_CHAINS"
    elif len(domain_enabled_chains) == 1:
        matched_chain = domain_enabled_chains[0]

    active_objective = hint_clean or None
    chain_mutation_authorized = False
    if matched_chain is not None:
        chain_clean = _clean(matched_chain.get("chain_id"))
        active_objective = active_objective or _clean(matched_chain.get("objective")) or None
        chain_reconcile = reconcile_chain(matched_chain, STATE_ROOT)
        chain_auth_reason = "AUTHORIZED"
        next_gid = _clean(chain_reconcile.get("next_gate_id"))
        cur_gid = _clean(chain_reconcile.get("current_gate_id"))
        gates_by_id = {
            _clean(g.get("gate_id")): g
            for g in (matched_chain.get("gates") or [])
            if isinstance(g, Mapping) and _clean(g.get("gate_id"))
        }
        if next_gid:
            cur_gate = gates_by_id.get(cur_gid) if cur_gid else None
            cur_job_id = _clean(cur_gate.get("job_id")) if isinstance(cur_gate, Mapping) else ""
            cur_cert = certified_by_job_id.get(cur_job_id) if cur_job_id else None
            target_gate = gates_by_id.get(next_gid)
            next_job_id = _clean(target_gate.get("job_id")) if isinstance(target_gate, Mapping) else ""
            gate_dependencies.append({
                "requires_certified_gate": cur_gid or None,
                "predecessor_job_id": cur_job_id or None,
                "predecessor_verified": (cur_cert is not None) if cur_gid else True,
                "predecessor_certified_at_utc": cur_cert.get("certified_at_utc") if cur_cert else None,
                "next_gate_id": next_gid,
                "next_job_id": next_job_id or None,
            })
            if isinstance(target_gate, Mapping):
                policy_tier, _ = classify_policy_tier(target_gate)
                auth_ok, chain_auth_reason = evaluate_gate_authorization(
                    target_gate,
                    authorization_classes=matched_chain.get("authorization_classes") or (),
                    authorization_context=authorization_context or matched_chain.get("authorization_context"),
                )
                if not auth_ok:
                    policy_tier = "HUMAN_APPROVAL_REQUIRED"
                elif policy_tier == "DEVELOPMENT_MUTATION":
                    chain_mutation_authorized = True

    effective_authorization_context = authorization_context
    materialized_gate_auth: dict[str, Any] | None = None
    if effective_authorization_context is None:
        try:
            from tools.mirror_sync.worker_lifecycle_recovery import (
                resolve_active_domain_authorization,
            )

            resolved_gate = resolve_active_domain_authorization(
                domain_upper,
                state_root=STATE_ROOT,
                required_class="DEVELOPMENT_MUTATION",
            )
            if isinstance(resolved_gate, Mapping):
                effective_authorization_context = resolved_gate
                materialized_gate_auth = {
                    "gate_id": resolved_gate.get("gate_id"),
                    "authorization_id": resolved_gate.get("authorization_id"),
                    "expires_at_utc": resolved_gate.get("expires_at_utc"),
                    "allowed_paths": list(((resolved_gate.get("scope") or {}).get("allowed_paths") or [])),
                }
        except Exception:
            effective_authorization_context = None

    explicit_auth_ok, explicit_auth_reason, explicit_auth_id = _evaluate_explicit_mutation_authorization(
        domain_upper=domain_upper,
        authorization_context=effective_authorization_context,
    )
    if explicit_auth_ok and materialized_gate_auth is not None:
        explicit_auth_reason = "MATERIALIZED_GATE_AUTHORIZATION_VERIFIED"

    # Cross-domain handoffs & autonomous resolution return (Fase 4)
    cross_domain_handoffs: dict[str, Any] = {
        "schema": "edarsahub.worker-go-context-handoffs.v1",
        "domain": domain_upper,
        "outgoing_handoffs": [],
        "incoming_handoffs": [],
        "satisfied_resolutions": [],
        "unsatisfied_dependencies": [],
        "counts": {
            "outgoing": 0,
            "incoming": 0,
            "satisfied_resolutions": 0,
            "unsatisfied_dependencies": 0,
        },
        "production_touched": False,
    }
    try:
        from tools.mirror_sync import worker_cross_domain_handoff as _handoff_mod

        cross_domain_handoffs = _handoff_mod.summarize_handoffs_for_domain(
            domain_upper,
            state_root=STATE_ROOT,
        )
    except Exception:
        pass

    # Decide next_allowed_action fail-closed.
    # NEVER infer DEVELOPMENT_MUTATION or mutation_allowed from RBAC + objective_hint text.
    missing_fields: list[str] = []
    mutation_allowed = False
    if pending_jobs:
        next_action = "WAIT_FOR_IN_FLIGHT_JOB"
        reason = "DOMAIN_HAS_IN_FLIGHT_JOB"
        mutation_allowed = False
    elif pending_drafts:
        next_action = "RECOVER_PENDING_DRAFT"
        policy_tier = "READ_ONLY"
        reason = "DOMAIN_HAS_UNPUBLISHED_DRAFT_PENDING_RECOVERY"
        mutation_allowed = False
    elif not identity_verified:
        next_action = "HUMAN_APPROVAL_REQUIRED"
        policy_tier = "HUMAN_APPROVAL_REQUIRED"
        reason = "AUTHENTICATED_IDENTITY_UNVERIFIED"
        missing_fields.append("authenticated_user")
        mutation_allowed = False
    elif chain_error == "CHAIN_NOT_FOUND":
        next_action = "REQUEST_MINIMUM_INFO"
        policy_tier = "READ_ONLY"
        reason = "CHAIN_NOT_FOUND"
        missing_fields.append("chain_id")
        chain_auth_reason = "CHAIN_NOT_FOUND"
        mutation_allowed = False
    elif chain_error == "CHAIN_DOMAIN_MISMATCH":
        next_action = "HUMAN_APPROVAL_REQUIRED"
        policy_tier = "HUMAN_APPROVAL_REQUIRED"
        reason = "CHAIN_DOMAIN_MISMATCH"
        chain_auth_reason = "CHAIN_DOMAIN_MISMATCH"
        mutation_allowed = False
    elif chain_error == "AMBIGUOUS_DOMAIN_CHAINS":
        next_action = "REQUEST_MINIMUM_INFO"
        policy_tier = "HUMAN_APPROVAL_REQUIRED"
        reason = "AMBIGUOUS_DOMAIN_CHAINS"
        missing_fields.append("chain_id")
        chain_auth_reason = "AMBIGUOUS_DOMAIN_CHAINS"
        mutation_allowed = False
    elif chain_reconcile is not None:
        cstate = _clean(chain_reconcile.get("state")).upper()
        if cstate == "COMPLETE":
            next_action = "COMPLETE"
            policy_tier = "READ_ONLY"
            reason = "CHAIN_COMPLETE"
            mutation_allowed = False
        elif cstate == "DISABLED":
            next_action = "HUMAN_APPROVAL_REQUIRED"
            policy_tier = "HUMAN_APPROVAL_REQUIRED"
            reason = "CHAIN_DISABLED"
            chain_auth_reason = "CHAIN_DISABLED"
            mutation_allowed = False
        elif cstate == "WAIT":
            next_action = "WAIT_FOR_IN_FLIGHT_JOB"
            reason = _clean(chain_reconcile.get("reason")) or "CHAIN_WAITING"
            mutation_allowed = False
        elif cstate == "STOP" or policy_tier == "HUMAN_APPROVAL_REQUIRED" or chain_auth_reason != "AUTHORIZED":
            next_action = "HUMAN_APPROVAL_REQUIRED"
            reason = (
                chain_auth_reason
                if chain_auth_reason != "AUTHORIZED"
                else (_clean(chain_reconcile.get("reason")) or "CHAIN_STOPPED")
            )
            mutation_allowed = False
        elif cstate == "READY":
            if policy_tier == "DEVELOPMENT_MUTATION" and not rbac_mutation_ok:
                next_action = "HUMAN_APPROVAL_REQUIRED"
                reason = "RBAC_MUTATION_FORBIDDEN"
                mutation_allowed = False
            elif policy_tier == "DEVELOPMENT_MUTATION":
                next_action = "CONTINUE_AUTONOMOUS"
                reason = "CHAIN_TRANSITION_READY"
                mutation_allowed = True
            else:
                next_action = "CONTINUE_AUTONOMOUS"
                policy_tier = "READ_ONLY"
                reason = "CHAIN_READ_ONLY_TRANSITION_READY"
                mutation_allowed = False
        else:
            next_action = "REQUEST_MINIMUM_INFO"
            reason = f"CHAIN_STATE_{cstate or 'UNKNOWN'}"
            mutation_allowed = False
    elif authorization_context is not None and not explicit_auth_ok:
        next_action = "HUMAN_APPROVAL_REQUIRED"
        policy_tier = "HUMAN_APPROVAL_REQUIRED"
        reason = explicit_auth_reason
        mutation_allowed = False
    elif explicit_auth_ok:
        if not rbac_mutation_ok:
            next_action = "HUMAN_APPROVAL_REQUIRED"
            policy_tier = "HUMAN_APPROVAL_REQUIRED"
            reason = "RBAC_MUTATION_FORBIDDEN"
            mutation_allowed = False
        else:
            next_action = "CONTINUE_AUTONOMOUS"
            policy_tier = "DEVELOPMENT_MUTATION"
            reason = "EXPLICIT_MUTATION_AUTHORIZATION_VERIFIED"
            mutation_allowed = True
    elif cross_domain_handoffs["satisfied_resolutions"] or cross_domain_handoffs["incoming_handoffs"]:
        next_action = "CONTINUE_AUTONOMOUS"
        policy_tier = "READ_ONLY"
        reason = (
            "CROSS_DOMAIN_HANDOFF_RESOLUTION_AVAILABLE"
            if cross_domain_handoffs["satisfied_resolutions"]
            else "CROSS_DOMAIN_INCOMING_HANDOFF_AVAILABLE"
        )
        mutation_allowed = False
    elif not active_objective and last_certified is None:
        next_action = "REQUEST_MINIMUM_INFO"
        policy_tier = "READ_ONLY"
        reason = "NO_ACTIVE_OBJECTIVE_OR_PRIOR_GATE"
        missing_fields.append("objective_hint")
        mutation_allowed = False
    else:
        next_action = "CONTINUE_AUTONOMOUS"
        policy_tier = "READ_ONLY"
        reason = "READ_ONLY_CONTEXT_RESOLVED" if rbac_mutation_ok else "READ_ONLY_ONLY_WITHOUT_MUTATION_RBAC"
        mutation_allowed = False

    # Hard fail-closed invariant: READ_ONLY or unverified context NEVER permits mutation.
    effective_explicit_mutation = chain_mutation_authorized or explicit_auth_ok
    if policy_tier != "DEVELOPMENT_MUTATION" or not (identity_verified and rbac_mutation_ok and effective_explicit_mutation):
        mutation_allowed = False

    resolution_ms = round((time.monotonic() - t_start) * 1000.0, 2)
    resume_from_job_id = (
        pending_jobs[0]["job_id"]
        if pending_jobs
        else (
            pending_drafts[0]["job_id"]
            if pending_drafts
            else (last_certified["job_id"] if isinstance(last_certified, dict) else None)
        )
    )
    continuity = {
        "schema": "edarsahub.worker-objective-continuity.v1",
        "isolated_from_other_domains": True,
        "recommended_next_step": next_action,
        "resume_from_job_id": resume_from_job_id,
        "cache_hit": cache_hit,
        "disk_index_reused": bool(snapshot.get("disk_index_reused", False)),
        "resolution_ms": resolution_ms,
        "production_touched": False,
    }

    return {
        "schema": "edarsahub.worker-go-context.v1",
        "project": project_clean,
        "domain": domain_upper,
        "active_objective": active_objective,
        "chain_id": chain_clean or None,
        "last_certified_gate": last_certified,
        "certified_successors": certified_successors,
        "pending_jobs": pending_jobs,
        "pending_drafts": pending_drafts,
        "historical_reconciled_drafts": historical_reconciled_drafts,
        "lifecycle_summary": {
            "DRAFT": draft_ids,
            "PENDING": pending_ids,
            "PROCESSING": processing_ids,
            "RESULT": [row["job_id"] for row in certified_results[:10]],
        },
        "active_authorizations": {
            "identity_verified": identity_verified,
            "actor_email": requester.get("email") or None,
            "rbac_mutation_authorized": rbac_mutation_ok,
            "explicit_mutation_authorized": effective_explicit_mutation,
            "explicit_authorization_status": (
                "CHAIN_GATE_AUTHORIZED"
                if chain_mutation_authorized
                else explicit_auth_reason
            ),
            "explicit_authorization_id": explicit_auth_id,
            "materialized_gate_authorization": materialized_gate_auth,
            "chain_authorization_status": chain_auth_reason,
        },
        "gate_dependencies": gate_dependencies,
        "cross_domain_handoffs": cross_domain_handoffs,
        "continuity": continuity,
        "policy_tier": policy_tier,
        "mutation_allowed": mutation_allowed,
        "next_allowed_action": next_action,
        "reason": reason,
        "missing_fields": missing_fields,
        "production_touched": False,
    }


_SECURITY_ERROR_PREFIXES = (
    "RBAC_",
    "SCOPE_",
    "SENSITIVE_FIELD_FORBIDDEN",
    "AUTHENTICATED_REQUESTER_EMAIL_REQUIRED",
    "PRODUCTION_FORBIDDEN",
    "SEMANTIC_PATH_FORBIDDEN",
    "SEMANTIC_DEV_PATH_FORBIDDEN",
    "SEMANTIC_DEV_OPERATION_FORBIDDEN",
    "SEMANTIC_REPAIR_PRODUCTION_POLICY_VIOLATION",
    "HANDOFF_SECRET_TRANSFER_FORBIDDEN",
    "HANDOFF_UNTRUSTED_PROMPT_BLOCKED",
    "HANDOFF_CIRCULAR_DEPENDENCY",
    "HANDOFF_MAX_DELEGATION_DEPTH_EXCEEDED",
    "HANDOFF_PRODUCTION_FORBIDDEN",
    "HANDOFF_AUTHORIZATION_",
    "HANDOFF_RBAC_",
    "HANDOFF_SOURCE_DOMAIN_FORBIDDEN",
    "HANDOFF_TARGET_DOMAIN_RESTRICTED",
    "HANDOFF_RECURSIVE_CAPABILITY_FORBIDDEN",
)


def _normalize_error_code(raw: str) -> str:
    head = str(raw or "").strip().split(":", 1)[0].strip().upper()
    return head or "VALIDATION_ERROR"


def build_semantic_diagnostic(
    error_code: str,
    *,
    request_payload: Mapping[str, Any] | None = None,
    loaded_capabilities: tuple[str, ...] | list[str] | None = None,
) -> dict[str, Any]:
    """Build a secret-free structured diagnostic explaining why a semantic request was rejected."""
    from .semantic_capabilities import (
        RAW_WORKER_FIELDS_FORBIDDEN,
        capability_catalog,
        registered_capabilities,
    )
    from tools.mirror_sync.worker_runtime_fingerprint import diagnose_capability_failure

    code = _normalize_error_code(error_code)
    payload = dict(request_payload) if isinstance(request_payload, Mapping) else {}
    capability = _clean(payload.get("capability")).upper()
    bounded_context = _clean(payload.get("bounded_context")).upper()
    mode = _clean(payload.get("mode")).upper()

    reg_caps = registered_capabilities()
    loaded = tuple(loaded_capabilities) if loaded_capabilities is not None else reg_caps
    catalog_map = {item["code"]: item for item in capability_catalog()}
    cap_meta = catalog_map.get(capability)

    is_security = any(code.startswith(pref) for pref in _SECURITY_ERROR_PREFIXES)
    runtime_diag = diagnose_capability_failure(
        capability_code=capability,
        registered_capabilities=reg_caps,
        loaded_capabilities=loaded,
        runtime_aligned=True,
        error_code=code,
    )

    if runtime_diag["classification"] == "CAPABILITY_NOT_LOADED_STALE_RUNTIME":
        classification = "RUNTIME_DRIFT_ERROR"
    elif is_security:
        classification = "SECURITY_DENIAL_EXPECTED"
    else:
        classification = "CONTRACT_VALIDATION_ERROR"

    rejected_field = "request"
    allowed_correction = "Consult GET /api/internal/worker/capabilities for registered contracts."
    http_status = 422 if (code.startswith("SEMANTIC_") or code == "SCHEMA_VALIDATION_ERROR") else 400

    if code == "SEMANTIC_CAPABILITY_UNKNOWN":
        rejected_field = "capability"
        if runtime_diag["classification"] == "CAPABILITY_NOT_LOADED_STALE_RUNTIME":
            allowed_correction = (
                "Capability exists in code but is missing in active runtime; verify "
                "GET /api/internal/worker/runtime-convergence before retrying."
            )
        else:
            allowed_correction = (
                "Use a registered capability from GET /api/internal/worker/capabilities "
                f"(registered: {', '.join(reg_caps)})."
            )
    elif code == "OBJECTIVE_REQUIRED":
        rejected_field = "objective"
        allowed_correction = "Provide a non-empty semantic objective string (3..4000 chars)."
    elif code == "BOUNDED_CONTEXT_REQUIRED":
        rejected_field = "bounded_context"
        allowed_correction = "Provide a valid bounded_context token matching ^[A-Za-z0-9][A-Za-z0-9._-]{1,119}$."
    elif code == "SEMANTIC_BOUNDED_CONTEXT_UNSUPPORTED" or code == "SEMANTIC_CONTEXT_INVALID":
        rejected_field = "bounded_context"
        expected_ctx = cap_meta.get("bounded_context_rule") if cap_meta else "VALID_DOMAIN_TOKEN"
        allowed_correction = f"Set bounded_context to satisfy rule: {expected_ctx}."
    elif code == "SEMANTIC_CAPABILITY_MODE_MISMATCH":
        rejected_field = "mode"
        modes = ", ".join(cap_meta.get("modes", [])) if cap_meta else "READ_ONLY"
        allowed_correction = f"Use an allowed mode for {capability or 'capability'}: {modes}."
    elif code == "RUNTIME_NOT_CONVERGED":
        classification = "RUNTIME_DRIFT_ERROR"
        rejected_field = "runtime_convergence"
        http_status = 409
        allowed_correction = (
            "Do not publish the mutation. Reconcile GET /api/internal/worker/runtime-convergence "
            "until overall_converged=true, then retry the same request_key."
        )
    elif code == "IDEMPOTENCY_CONFLICT":
        classification = "IDEMPOTENCY_CONFLICT"
        rejected_field = "request_key"
        http_status = 409
        allowed_correction = (
            "Reuse the exact original semantic payload for this request_key, or use a new "
            "request_key only for a genuinely distinct objective."
        )
    elif code == "IDEMPOTENCY_BINDING_UNVERIFIABLE":
        classification = "IDEMPOTENCY_STATE_ERROR"
        rejected_field = "request_key"
        http_status = 409
        allowed_correction = (
            "Do not republish. Reconcile the existing canonical request artifact for this "
            "request_key/job before retrying."
        )
    elif code in {"SEMANTIC_CONSTRAINTS_UNSUPPORTED", "SEMANTIC_CONSTRAINTS_INVALID"}:
        rejected_field = "constraints"
        allowed_keys = cap_meta.get("allowed_constraints", []) if cap_meta else []
        keys_str = ", ".join(allowed_keys) if allowed_keys else "(none - pass {})"
        allowed_correction = (
            f"Pass constraints as a JSON object with only allowed keys: {keys_str}. "
            f"Never pass raw Worker fields: {', '.join(RAW_WORKER_FIELDS_FORBIDDEN)}."
        )
    elif code == "SEMANTIC_SOURCE_JOB_INVALID":
        rejected_field = "constraints.source_job_id"
        allowed_correction = (
            "Provide constraints.source_job_id as a valid Worker job_id matching "
            "^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$."
        )
    elif code in {"SEMANTIC_SQL_PROFILE_INVALID", "SEMANTIC_SQL_PROFILE_UNKNOWN"}:
        rejected_field = "constraints.profile_code"
        allowed_correction = (
            "Select a registered READ_ONLY SQL profile_code from list_capabilities "
            "(SQL_READONLY_PROFILE_AUDIT); arbitrary SQL is forbidden."
        )
    elif code == "SEMANTIC_SQL_PROFILE_DOMAIN_FORBIDDEN":
        rejected_field = "bounded_context"
        allowed_correction = (
            "Use a bounded_context authorized for the selected SQL_READONLY_PROFILE_AUDIT profile_code."
        )
    elif code == "SEMANTIC_PATHS_INVALID":
        rejected_field = "constraints.paths"
        allowed_correction = "Provide constraints.paths as a list of 1..20 relative non-sensitive paths under allowed roots."
    elif code == "SEMANTIC_TERMS_INVALID":
        rejected_field = "constraints.search_terms"
        allowed_correction = "Provide constraints.search_terms as a list of 1..20 tokens matching ^[A-Za-z0-9_.-]{2,64}$."
    elif code == "SEMANTIC_LIMIT_INVALID":
        rejected_field = "constraints.max_results"
        allowed_correction = "Provide constraints.max_results as an integer between 1 and 100."
    elif code == "SEMANTIC_DEV_CHANGE_SPEC_INVALID":
        rejected_field = "constraints.change_spec"
        allowed_correction = "Provide constraints.change_spec as a non-empty list of 1..15 declarative edit items."
    elif code == "SEMANTIC_DEV_CHANGE_ITEM_INVALID":
        rejected_field = "constraints.change_spec[]"
        allowed_correction = "Each entry in constraints.change_spec must be a JSON object with operation and path."
    elif code == "SEMANTIC_DEV_CHANGE_KEYS_UNSUPPORTED":
        rejected_field = "constraints.change_spec[]"
        allowed_correction = (
            "Use only allowed change_spec keys: operation, path, source_sha256, expected_sha256, "
            "old_text, replacement, anchor, content, expected_occurrences, overwrite."
        )
    elif code == "SEMANTIC_DEV_AUTHORIZATION_REF_INVALID":
        rejected_field = "constraints.authorization_ref"
        allowed_correction = "Provide constraints.authorization_ref matching ^[A-Za-z0-9][A-Za-z0-9._:/-]{2,120}$."
    elif code == "SEMANTIC_DEV_JOB_ID_OVERRIDE_INVALID":
        rejected_field = "constraints.job_id_override"
        allowed_correction = "Provide constraints.job_id_override matching ^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$."
    elif code == "SEMANTIC_DEV_VERIFICATION_TESTS_INVALID":
        rejected_field = "constraints.verification_tests"
        allowed_correction = "Provide constraints.verification_tests as up to 15 .py paths under backend/tests/ or tools/tests/."
    elif code in {"SEMANTIC_SOURCE_SHA256_MISMATCH", "SEMANTIC_SOURCE_SHA256_REQUIRED"}:
        rejected_field = "constraints.change_spec[].source_sha256"
        allowed_correction = (
            "Refresh the live 64-hex SHA-256 of the target file in Edarsahub_Desarrollo "
            "before re-submitting; never reuse stale hashes."
        )
    elif code == "SEMANTIC_SOURCE_FILE_MISSING":
        rejected_field = "constraints.change_spec[].path"
        allowed_correction = "Target file does not exist for incremental edit; verify path or use operation=write_file."
    elif code in {"SEMANTIC_PATH_FORBIDDEN", "SEMANTIC_PATH_INVALID", "SEMANTIC_DEV_PATH_FORBIDDEN", "SEMANTIC_DEV_PATH_INVALID"}:
        rejected_field = "constraints.paths" if "DEV" not in code else "constraints.change_spec[].path"
        roots = ", ".join(cap_meta.get("allowed_path_roots", [])) if cap_meta else "backend/modules/, backend/tests/, frontend/src/, tools/mirror_sync/"
        allowed_correction = f"Use only relative non-sensitive paths under allowed roots: {roots}."
    elif code == "SEMANTIC_DEV_OPERATION_FORBIDDEN":
        rejected_field = "constraints.change_spec[].operation"
        allowed_correction = "Use only declarative operations: replace_text, insert_before, insert_after, append_once, write_file."
    elif code == "SEMANTIC_DEV_REPLACE_FIELDS_INVALID":
        rejected_field = "constraints.change_spec[].old_text"
        allowed_correction = "Provide non-empty string old_text and string replacement for replace_text."
    elif code == "SEMANTIC_DEV_EXPECTED_OCCURRENCES_INVALID":
        rejected_field = "constraints.change_spec[].expected_occurrences"
        allowed_correction = "Provide expected_occurrences as an integer between 1 and 20."
    elif code == "SEMANTIC_DEV_OLD_TEXT_OCCURRENCE_MISMATCH":
        rejected_field = "constraints.change_spec[].old_text"
        allowed_correction = "Ensure old_text matches expected_occurrences exactly in the live target file."
    elif code == "SEMANTIC_DEV_INSERT_FIELDS_INVALID":
        rejected_field = "constraints.change_spec[].anchor"
        allowed_correction = "Provide non-empty string anchor and string replacement for insert_before/insert_after."
    elif code == "SEMANTIC_DEV_ANCHOR_MISMATCH":
        rejected_field = "constraints.change_spec[].anchor"
        allowed_correction = "Ensure anchor appears exactly once in the live target file."
    elif code == "SEMANTIC_DEV_APPEND_FIELDS_INVALID":
        rejected_field = "constraints.change_spec[].replacement"
        allowed_correction = "Provide a non-empty string replacement for append_once."
    elif code == "SEMANTIC_DEV_CONTENT_REQUIRED":
        rejected_field = "constraints.change_spec[].content"
        allowed_correction = "Provide a non-empty UTF-8 string in content for write_file."
    elif code == "SEMANTIC_DEV_CONTENT_TOO_LARGE":
        rejected_field = "constraints.change_spec[].content"
        allowed_correction = "Keep replacement or file content within the 120000-byte limit."
    elif code == "SEMANTIC_DEV_FILE_ALREADY_EXISTS":
        rejected_field = "constraints.change_spec[].overwrite"
        allowed_correction = "Target file already exists; set overwrite=true with live source_sha256 or use replace_text."
    elif code == "SEMANTIC_DEV_WRITE_LARGE_SHRINK_BLOCKED":
        rejected_field = "constraints.change_spec[].content"
        allowed_correction = (
            "Overwriting a >=4096-byte file with <75% of its size is blocked; "
            "use targeted replace_text, insert_before, insert_after, or append_once instead."
        )
    elif code in {"RBAC_MUTATION_FORBIDDEN", "AUTHENTICATED_REQUESTER_EMAIL_REQUIRED"}:
        rejected_field = "rbac"
        http_status = 403
        allowed_correction = "Authenticated admin/worker:submit RBAC identity is required for MUTATION mode."
    elif code == "SCOPE_AUTHORIZATION_DENIED":
        rejected_field = "authorization_scope"
        http_status = 403
        allowed_correction = "Target domain, empresa_id, or unidad_negocio_pk is outside the caller's authorized scope."
    elif code == "SENSITIVE_FIELD_FORBIDDEN":
        rejected_field = "request"
        allowed_correction = "Remove sensitive credential/secret/token keys from the request payload."
    elif code == "HANDOFF_SECRET_TRANSFER_FORBIDDEN":
        rejected_field = "constraints"
        http_status = 403
        allowed_correction = "Remove secrets, credentials, tokens, or private keys from cross-domain handoff payloads."
    elif code == "HANDOFF_UNTRUSTED_PROMPT_BLOCKED":
        rejected_field = "objective"
        http_status = 403
        allowed_correction = "Remove untrusted prompt override or policy-bypass text from the handoff request."
    elif code in {"HANDOFF_CIRCULAR_DEPENDENCY", "HANDOFF_MAX_DELEGATION_DEPTH_EXCEEDED", "HANDOFF_RECURSIVE_CAPABILITY_FORBIDDEN"}:
        rejected_field = "constraints.target_domain"
        http_status = 409
        allowed_correction = "Break circular or recursive cross-domain delegation before registering the handoff."
    elif code == "HANDOFF_RATE_LIMIT_EXCEEDED":
        rejected_field = "request_key"
        http_status = 429
        allowed_correction = "Wait for the handoff rate-limit window to reset or reuse an existing active handoff."
    elif code.startswith("CONSENT_") or code == "SELF_PRIVILEGE_ESCALATION_FORBIDDEN":
        rejected_field = "constraints.consent_evidence"
        http_status = 403
        allowed_correction = "Obtain verifiable human consent bound to the authenticated SQL user and exact Gate scope digest via the canonical approval channel."
    elif code.startswith("AUTHORIZATION_CONFLICT"):
        rejected_field = "constraints.gate_id"
        http_status = 409
        allowed_correction = "Do not overwrite an active Gate authorization with a diverging scope; inspect or revoke the existing gate_id first."
    elif code.startswith("AUTHORIZATION_") or code == "GATE_AUTHORIZATION_NOT_FOUND":
        rejected_field = "constraints.authorization_ref"
        http_status = 403
        allowed_correction = "Verify domain, exact paths, authorized operations, live SHA256, base HEAD, and non-revoked/non-expired Gate authorization."
    elif code.startswith("HANDOFF_AUTHORIZATION_") or code.startswith("HANDOFF_RBAC_") or code in {"HANDOFF_SOURCE_DOMAIN_FORBIDDEN", "HANDOFF_TARGET_DOMAIN_RESTRICTED"}:
        rejected_field = "constraints.authorization_ref"
        http_status = 403
        allowed_correction = "Provide a valid, non-expired, non-revoked materialized authorization scoped to the domain."
    elif code.startswith("HANDOFF_"):
        rejected_field = "constraints"
        http_status = 422
        allowed_correction = "Validate target_domain, request_key, acceptance_criteria, and constraints against list_capabilities (CROSS_DOMAIN_HANDOFF_REGISTER)."
    elif code == "SCHEMA_VALIDATION_ERROR":
        rejected_field = "request_schema"
        allowed_correction = (
            "Send required WorkerObjectiveRequest fields (objective, bounded_context, mode, capability, optional request_key, constraints) "
            "with valid types and no extra top-level keys."
        )

    raw_corr = _clean(payload.get("request_key"))
    safe_corr = (
        raw_corr
        if raw_corr
        and _SAFE_CORR_RE.fullmatch(raw_corr)
        and not any(tok in raw_corr.lower() for tok in _CORR_SENSITIVE)
        else None
    )
    logger.warning(
        "worker_ingress_semantic_rejected timestamp_utc=%s http_status=%s error_code=%s "
        "rejected_field=%s capability=%s correlation_id=%s",
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        http_status,
        code,
        rejected_field,
        capability or "UNKNOWN",
        safe_corr or "none",
    )

    return {
        "schema": "edarsahub.worker-semantic-diagnostic.v1",
        "error_code": code,
        "status": code,
        "http_status": http_status,
        "classification": classification,
        "runtime_diagnosis": runtime_diag["classification"],
        "rejected_field": rejected_field,
        "capability": capability or None,
        "bounded_context": bounded_context or None,
        "mode": mode or None,
        "allowed_modes": list(cap_meta.get("modes", [])) if cap_meta else [],
        "allowed_constraints": list(cap_meta.get("allowed_constraints", [])) if cap_meta else [],
        "allowed_bounded_context": cap_meta.get("bounded_context_rule") if cap_meta else None,
        "allowed_path_roots": list(cap_meta.get("allowed_path_roots", [])) if cap_meta else [],
        "registered_capabilities": list(reg_caps),
        "allowed_correction": allowed_correction,
        "production_touched": False,
    }


def _verify_authorization_scope(
    *,
    bounded_context: str,
    authorization_scope: Mapping[str, Any] | None,
) -> None:
    if not isinstance(authorization_scope, Mapping) or not authorization_scope:
        return
    req_domain = bounded_context.strip().lower()
    for field, target in (
        ("domains", req_domain),
        ("domain", req_domain),
    ):
        allowed = authorization_scope.get(field)
        if allowed is None:
            continue
        vals = (
            {str(v).strip().lower() for v in allowed if str(v).strip()}
            if isinstance(allowed, (list, tuple, set, frozenset))
            else {str(allowed).strip().lower()}
        )
        if vals and "*" not in vals and target not in vals:
            raise WorkerIngressError("SCOPE_AUTHORIZATION_DENIED")

    for req_key, granted_key in (
        ("requested_empresa_id", "allowed_empresa_ids"),
        ("requested_unidad_negocio_pk", "allowed_unidad_negocio_pks"),
    ):
        req_val = _clean(authorization_scope.get(req_key)).lower()
        if not req_val:
            continue
        raw_granted = authorization_scope.get(granted_key)
        granted = (
            {str(v).strip().lower() for v in raw_granted if str(v).strip()}
            if isinstance(raw_granted, (list, tuple, set, frozenset))
            else set()
        )
        if "*" not in granted and req_val not in granted:
            raise WorkerIngressError("SCOPE_AUTHORIZATION_DENIED")


def _require_mutation_runtime_convergence() -> dict[str, Any]:
    """Fail closed before any mutation publication when the active runtime is stale."""
    from tools.mirror_sync.worker_runtime_fingerprint import (
        build_mcp_runtime_convergence_report,
    )

    report = build_mcp_runtime_convergence_report()
    if report.get("overall_converged") is not True:
        raise WorkerIngressError("RUNTIME_NOT_CONVERGED")
    return report


def preflight_semantic_objective(
    request_payload: Mapping[str, Any],
    *,
    current_user: Mapping[str, Any],
    authorization_scope: Mapping[str, Any] | None = None,
    loaded_capabilities: tuple[str, ...] | list[str] | None = None,
    enforce_runtime_convergence: bool = False,
) -> dict[str, Any]:
    """Canonical pre-publication semantic preflight validating contract, RBAC, scope, SHA-256, and duplicates."""
    payload = dict(request_payload) if isinstance(request_payload, Mapping) else {}
    try:
        _assert_no_sensitive_keys(payload)
        objective = _clean(payload.get("objective"))
        bounded_context = _clean(payload.get("bounded_context")).upper()
        capability_code = _clean(payload.get("capability")).upper()
        requested_mode = _clean(payload.get("mode")).upper()

        if not objective:
            raise WorkerIngressError("OBJECTIVE_REQUIRED")
        if not bounded_context:
            raise WorkerIngressError("BOUNDED_CONTEXT_REQUIRED")

        _verify_authorization_scope(
            bounded_context=bounded_context,
            authorization_scope=authorization_scope,
        )

        try:
            capability = resolve_capability(capability_code)
        except SemanticCapabilityError as exc:
            raise WorkerIngressError(str(exc)) from exc

        if loaded_capabilities is not None:
            loaded_set = {str(c).strip().upper() for c in loaded_capabilities if str(c).strip()}
            if capability.code not in loaded_set:
                raise WorkerIngressError("SEMANTIC_CAPABILITY_UNKNOWN")

        allowed_modes = tuple(str(m).upper() for m in capability.modes)
        if requested_mode not in allowed_modes:
            raise WorkerIngressError("SEMANTIC_CAPABILITY_MODE_MISMATCH")

        _requester_from_authenticated_user(current_user, project="EDARSAHUB")
        if requested_mode == "MUTATION":
            _assert_mutation_rbac(current_user)
            if enforce_runtime_convergence:
                _require_mutation_runtime_convergence()

        if capability.submitter is not None:
            # Direct-submitter capability (e.g. WORKER_REPAIR_BOUNDED, CROSS_DOMAIN_HANDOFF_REGISTER): validate without mutating
            constraints = payload.get("constraints")
            if not isinstance(constraints, Mapping):
                raise WorkerIngressError("SEMANTIC_CONSTRAINTS_INVALID")
            from .semantic_capabilities import capability_catalog

            meta = {item["code"]: item for item in capability_catalog()}.get(capability.code, {})
            ctx_rule = meta.get("bounded_context_rule")
            if ctx_rule and ctx_rule != "ANY_VALID_TOKEN" and bounded_context != ctx_rule:
                raise WorkerIngressError("SEMANTIC_BOUNDED_CONTEXT_UNSUPPORTED")
            allowed_keys = set(meta.get("allowed_constraints", ()))
            if set(constraints.keys()) - allowed_keys:
                raise WorkerIngressError("SEMANTIC_CONSTRAINTS_UNSUPPORTED")
            if capability.code == "GATE_AUTHORIZATION_LIFECYCLE":
                from tools.mirror_sync import worker_lifecycle_recovery as lifecycle_mod

                try:
                    pf_auth = lifecycle_mod.preflight_gate_authorization_lifecycle(
                        payload,
                        current_user=current_user,
                        state_root=STATE_ROOT,
                        repo_root=REPO_ROOT,
                    )
                except lifecycle_mod.GateAuthorizationError as exc:
                    raise WorkerIngressError(str(exc)) from exc
                return {
                    "schema": "edarsahub.worker-semantic-preflight.v1",
                    "ok": True,
                    "status": pf_auth.get("status") or "PREFLIGHT_READY",
                    "action": pf_auth.get("action"),
                    "gate_id": pf_auth.get("gate_id"),
                    "authorization_id": pf_auth.get("authorization_id"),
                    "scope_digest": pf_auth.get("scope_digest"),
                    "duplicate_detected": bool(pf_auth.get("duplicate_detected", False)),
                    "capability": capability.code,
                    "bounded_context": bounded_context,
                    "mode": requested_mode,
                    "production_allowed": False,
                    "production_touched": False,
                }
            if capability.code == "CROSS_DOMAIN_HANDOFF_REGISTER":
                from tools.mirror_sync import worker_cross_domain_handoff as handoff_mod

                try:
                    checked = handoff_mod.validate_handoff_constraints(
                        payload,
                        current_user=current_user,
                        state_root=STATE_ROOT,
                        dry_run=True,
                    )
                except handoff_mod.HandoffError as exc:
                    raise WorkerIngressError(str(exc)) from exc
                if checked.get("duplicate") is True and not checked.get("pending_update"):
                    existing_h = checked["existing_handoff"]
                    return {
                        "schema": "edarsahub.worker-semantic-preflight.v1",
                        "ok": True,
                        "status": "EXISTS",
                        "handoff_id": existing_h["handoff_id"],
                        "job_id": existing_h.get("resolution_job_id") or existing_h["handoff_id"],
                        "lifecycle_state": existing_h.get("lifecycle_state"),
                        "executor_status": existing_h.get("executor_status"),
                        "duplicate_detected": True,
                        "duplicate_prevented": True,
                        "capability": capability.code,
                        "bounded_context": bounded_context,
                        "mode": requested_mode,
                        "production_allowed": False,
                        "production_touched": False,
                    }
                cls = checked["classification"]
                return {
                    "schema": "edarsahub.worker-semantic-preflight.v1",
                    "ok": True,
                    "status": "PREFLIGHT_READY",
                    "handoff_id": checked["handoff_id"],
                    "dependency_id": checked["dependency_id"],
                    "target_domain": checked["target_domain"],
                    "classification": cls["classification"],
                    "lifecycle_state": cls["lifecycle_state"],
                    "next_allowed_action": cls["next_allowed_action"],
                    "executor_status": cls.get("executor_status"),
                    "has_executor": cls.get("has_executor"),
                    "compatible_capabilities": cls.get("compatible_capabilities", []),
                    "exception_code": cls.get("exception_code"),
                    "handoff_update": bool(checked.get("pending_update", False)),
                    "duplicate_detected": False,
                    "capability": capability.code,
                    "bounded_context": bounded_context,
                    "mode": requested_mode,
                    "production_allowed": False,
                    "production_touched": False,
                }
            return {
                "schema": "edarsahub.worker-semantic-preflight.v1",
                "ok": True,
                "status": "PREFLIGHT_READY",
                "capability": capability.code,
                "bounded_context": bounded_context,
                "mode": requested_mode,
                "duplicate_detected": False,
                "production_allowed": False,
                "production_touched": False,
            }

        canonical_job = build_semantic_job(payload, current_user=current_user)
        # P2A: Revalidate materialized Gate authorization before publish whenever authorization_ref matches an artifact
        job_auth_ref = _clean(canonical_job.get("authorization_ref"))
        if requested_mode == "MUTATION" and job_auth_ref:
            from tools.mirror_sync import worker_lifecycle_recovery as lifecycle_mod

            inspected = lifecycle_mod.inspect_gate_authorization(job_auth_ref, state_root=STATE_ROOT)
            if inspected.get("found") is True:
                req_paths = [
                    _clean(a.get("path"))
                    for a in (canonical_job.get("actions") or [])
                    if isinstance(a, Mapping) and _clean(a.get("path"))
                ]
                req_ops = [
                    _clean(a.get("type"))
                    for a in (canonical_job.get("actions") or [])
                    if isinstance(a, Mapping) and _clean(a.get("type"))
                ]
                reval = lifecycle_mod.revalidate_gate_authorization_for_mutation(
                    job_auth_ref,
                    domain=bounded_context,
                    requested_paths=req_paths,
                    requested_operations=req_ops,
                    state_root=STATE_ROOT,
                    repo_root=REPO_ROOT,
                    verify_live_sha=True,
                )
                if reval.get("authorized") is not True:
                    raise WorkerIngressError(str(reval.get("reason") or "AUTHORIZATION_DENIED"))
        requester = _requester_from_authenticated_user(
            current_user,
            project="EDARSAHUB",
        )
        existing = _resolve_existing_semantic_job(
            canonical_job,
            request_payload=payload,
            requester_email=requester["email"],
        )
        if existing is not None:
            existing_job_id, existing_state = existing
            return {
                "schema": "edarsahub.worker-semantic-preflight.v1",
                "ok": True,
                "status": "EXISTS",
                "job_id": existing_job_id,
                "existing_lifecycle": existing_state,
                "duplicate_detected": True,
                "duplicate_prevented": True,
                "capability": capability.code,
                "bounded_context": bounded_context,
                "mode": requested_mode,
                "production_allowed": False,
                "production_touched": False,
            }

        draft_recovery = _check_unpublished_draft_idempotency(canonical_job)
        preflight_ready: dict[str, Any] = {
            "schema": "edarsahub.worker-semantic-preflight.v1",
            "ok": True,
            "status": "PREFLIGHT_READY",
            "job_id": canonical_job["job_id"],
            "capability": capability.code,
            "bounded_context": bounded_context,
            "mode": requested_mode,
            "action_count": len(canonical_job.get("actions") or []),
            "check_types": [c.get("type") for c in (canonical_job.get("checks") or []) if isinstance(c, dict)],
            "duplicate_detected": False,
            "production_allowed": False,
            "production_touched": False,
        }
        if draft_recovery is not None:
            preflight_ready.update(draft_recovery)
        return preflight_ready
    except WorkerIngressError as exc:
        diag = build_semantic_diagnostic(
            str(exc),
            request_payload=payload,
            loaded_capabilities=loaded_capabilities,
        )
        return {
            **diag,
            "schema": "edarsahub.worker-semantic-preflight.v1",
            "ok": False,
            "status": "PREFLIGHT_REJECTED",
        }
