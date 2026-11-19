"""Service boundary for remote Universal Worker submission and status.

This module is intentionally thin. It does not implement another queue,
publisher, scheduler, Git client, SQL executor or Worker. Submission is
delegated to the existing canonical job factory and gate-chain publisher.
"""
from __future__ import annotations

import hashlib
import json
import re
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
    "evidence_status",
    "evidence_truncated",
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
    return safe


def _semantic_job_id(
    request_payload: Mapping[str, Any],
    *,
    requester_email: str,
) -> str:
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

    if capability.submitter is not None:
        try:
            result = capability.submitter(payload, requester)
        except SemanticCapabilityError as exc:
            raise WorkerIngressError(str(exc)) from exc

        if not isinstance(result, dict):
            raise WorkerIngressError("SEMANTIC_CAPABILITY_INVALID_RESPONSE")

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
    existing_state = _find_existing_job_state(canonical_job["job_id"])
    if existing_state is not None:
        return {
            "status": "EXISTS",
            "job_id": canonical_job["job_id"],
            "existing_lifecycle": existing_state,
            "duplicate_prevented": True,
            "production_touched": False,
            "capability": capability_code,
            "bounded_context": _clean(payload.get("bounded_context")).upper(),
        }

    result = _submit_through_canonical_publisher(canonical_job)
    if not isinstance(result, dict):
        raise WorkerIngressError("CANONICAL_PUBLISHER_INVALID_RESPONSE")

    safe = dict(result)
    safe["job_id"] = _clean(result.get("job_id")) or canonical_job["job_id"]
    safe["production_touched"] = bool(result.get("production_touched", False))
    safe["capability"] = capability_code
    safe["bounded_context"] = _clean(payload.get("bounded_context")).upper()
    safe.pop("template", None)
    return safe


def _read_json_if_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_terminal_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    from tools.mirror_sync.universal_job_result_publisher import (
        sanitize_repository_evidence,
        sanitize_result_detail_evidence,
    )
    from tools.mirror_sync.worker_result_semantic_extract import (
        sanitize_repository_contract_payload,
    )

    fields = {
        key: payload.get(key)
        for key in _SAFE_RESULT_KEYS
        if key in payload
    }
    payload_dict = dict(payload)

    if fields.get("result_detail_evidence") is None:
        extracted = sanitize_result_detail_evidence(payload_dict)
        if extracted is not None:
            fields["result_detail_evidence"] = extracted

    if fields.get("repository_contract_evidence") is not None:
        validated_repo = sanitize_repository_contract_payload(
            fields["repository_contract_evidence"]
        )
        if validated_repo is not None:
            fields["repository_contract_evidence"] = validated_repo
        else:
            fields.pop("repository_contract_evidence", None)
            fields["evidence_status"] = "REJECTED_UNSAFE_OR_OVERSIZED"
    else:
        extracted_repo = sanitize_repository_evidence(payload_dict)
        if extracted_repo is not None:
            fields["repository_contract_evidence"] = extracted_repo

    repo_ev = fields.get("repository_contract_evidence")
    if isinstance(repo_ev, dict):
        is_trunc = any(
            isinstance(item, dict) and item.get("truncated") is True
            for item in (repo_ev.get("checks") or [])
        )
        fields.setdefault("evidence_truncated", is_trunc)
        fields.setdefault("evidence_status", "TRUNCATED" if is_trunc else "COMPLETE")
    elif isinstance(fields.get("result_detail_evidence"), dict):
        detail_checks = fields["result_detail_evidence"].get("checks") or []
        if detail_checks and isinstance(detail_checks[0], dict):
            first = detail_checks[0]
            if "evidence_status" in first:
                fields.setdefault("evidence_status", first["evidence_status"])
            if "evidence_truncated" in first:
                fields.setdefault("evidence_truncated", first["evidence_truncated"])

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


def get_job_status(job_id: str) -> dict[str, Any]:
    value = _clean(job_id)
    if not JOB_ID_RE.fullmatch(value):
        raise WorkerIngressError("JOB_ID_INVALID")

    result_path = STATE_ROOT / "results" / f"{value}.json"
    if result_path.is_file():
        result_read = read_canonical_result(
            result_path,
            expected_job_id=value,
        )
        status = build_job_status(result_read=result_read)
        if result_read.terminal_result_valid and isinstance(
            result_read.payload, dict
        ):
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
            "status": lifecycle,
            "certification": "NOT_CERTIFIED",
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


def _job_matches_domain(job_id: str, payload: Mapping[str, Any], domain_upper: str) -> bool:
    """Strictly isolate jobs by domain so RRHH, CRM, Finanzas, etc. are never mixed."""
    scheduling = payload.get("scheduling")
    if isinstance(scheduling, Mapping):
        bc = _clean(scheduling.get("bounded_context")).upper()
        if bc == domain_upper:
            return True
    jid_upper = job_id.upper()
    tokens = [tok for tok in re.split(r"[^A-Z0-9]+", jid_upper) if tok]
    if f"SEM-{domain_upper}-" in jid_upper:
        return True
    if f"-{domain_upper}-" in jid_upper or jid_upper.startswith(f"{domain_upper}-"):
        return True
    return domain_upper in tokens


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
    Fails closed (mutation_allowed=False) when context is ambiguous or authorization is unverified.
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
            "pending_jobs": [],
            "active_authorizations": {
                "identity_verified": identity_verified,
                "actor_email": requester.get("email") or None,
                "rbac_mutation_authorized": rbac_mutation_ok,
            },
            "gate_dependencies": [],
            "policy_tier": "HUMAN_APPROVAL_REQUIRED",
            "mutation_allowed": False,
            "next_allowed_action": "REQUEST_MINIMUM_INFO",
            "reason": "AMBIGUOUS_DOMAIN_CONTEXT",
            "missing_fields": ["domain"],
            "production_touched": False,
        }

    # Discover domain-scoped in-flight jobs (PENDING / PROCESSING)
    pending_jobs: list[dict[str, Any]] = []
    for lifecycle, dirname in (("PROCESSING", "processing"), ("PENDING", "pending")):
        folder = STATE_ROOT / dirname
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.json")):
            payload = _read_json_if_object(path)
            jid = _clean(payload.get("job_id")) or path.stem
            if jid and _job_matches_domain(jid, payload, domain_upper):
                pending_jobs.append({"job_id": jid, "lifecycle": lifecycle})

    # Discover latest certified gate strictly within this domain
    last_certified: dict[str, Any] | None = None
    results_dir = STATE_ROOT / "results"
    if results_dir.is_dir():
        candidates = sorted(
            results_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for path in candidates:
            jid = path.stem
            # Fast pre-check by filename or lightweight JSON read
            raw = _read_json_if_object(path)
            if not raw or not _job_matches_domain(jid, raw, domain_upper):
                continue
            read = read_canonical_result(path, expected_job_id=jid)
            if not read.terminal_result_valid or not isinstance(read.payload, dict):
                continue
            cert = _clean(read.payload.get("certification")).upper()
            if cert in {"CERTIFIED", "CERTIFIED_READ_ONLY", "CERTIFIED_OPERATIONAL", "CERTIFIED_FRONTEND_BUILD"}:
                last_certified = {
                    "job_id": jid,
                    "status": read.payload.get("status"),
                    "certification": cert,
                    "commit_sha": (
                        read.payload.get("certified_source_sha")
                        or read.payload.get("development_sha")
                        or read.payload.get("commit_sha")
                    ),
                    "completed_at_utc": read.payload.get("completed_at_utc"),
                }
                break

    # Optional registered gate-chain reconciliation (read-only)
    chains_root = config_dir or (REPO_ROOT / "worker_queue" / "config" / "gate_chains")
    matched_chain: dict[str, Any] | None = None
    chain_reconcile: dict[str, Any] | None = None
    gate_dependencies: list[dict[str, Any]] = []
    policy_tier = "READ_ONLY"
    chain_auth_reason = "AUTHORIZED"

    if chains_root.is_dir():
        for cpath in sorted(chains_root.glob("*.json")):
            cfg = _read_json_if_object(cpath)
            if not cfg or cfg.get("schema") != "edarsahub.gate-chain.v1":
                continue
            cid = _clean(cfg.get("chain_id"))
            cfg_domain = _clean(cfg.get("domain") or cfg.get("bounded_context")).upper()
            if chain_clean:
                if cid == chain_clean:
                    matched_chain = cfg
                    break
            elif cfg_domain == domain_upper and cfg.get("enabled") is True:
                matched_chain = cfg
                break

    active_objective = hint_clean or None
    if matched_chain is not None:
        chain_clean = _clean(matched_chain.get("chain_id"))
        active_objective = active_objective or _clean(matched_chain.get("objective")) or None
        chain_reconcile = reconcile_chain(matched_chain, STATE_ROOT)
        next_gid = _clean(chain_reconcile.get("next_gate_id"))
        cur_gid = _clean(chain_reconcile.get("current_gate_id"))
        if next_gid:
            gate_dependencies.append({"requires_certified_gate": cur_gid or None, "next_gate_id": next_gid})
            target_gate = next(
                (g for g in matched_chain.get("gates") or [] if _clean(g.get("gate_id")) == next_gid),
                None,
            )
            if isinstance(target_gate, Mapping):
                policy_tier, _ = classify_policy_tier(target_gate)
                auth_ok, chain_auth_reason = evaluate_gate_authorization(
                    target_gate,
                    authorization_classes=matched_chain.get("authorization_classes") or (),
                    authorization_context=authorization_context or matched_chain.get("authorization_context"),
                )
                if not auth_ok:
                    policy_tier = "HUMAN_APPROVAL_REQUIRED"
    elif rbac_mutation_ok and active_objective:
        policy_tier = "DEVELOPMENT_MUTATION"

    # Decide next_allowed_action fail-closed
    missing_fields: list[str] = []
    if pending_jobs:
        next_action = "WAIT_FOR_IN_FLIGHT_JOB"
        reason = "DOMAIN_HAS_IN_FLIGHT_JOB"
        mutation_allowed = False
    elif not identity_verified:
        next_action = "HUMAN_APPROVAL_REQUIRED"
        reason = "AUTHENTICATED_IDENTITY_UNVERIFIED"
        missing_fields.append("authenticated_user")
        mutation_allowed = False
    elif chain_reconcile is not None:
        cstate = _clean(chain_reconcile.get("state")).upper()
        if cstate == "COMPLETE":
            next_action = "COMPLETE"
            reason = "CHAIN_COMPLETE"
            mutation_allowed = False
        elif cstate == "WAIT":
            next_action = "WAIT_FOR_IN_FLIGHT_JOB"
            reason = _clean(chain_reconcile.get("reason")) or "CHAIN_WAITING"
            mutation_allowed = False
        elif cstate == "STOP" or policy_tier == "HUMAN_APPROVAL_REQUIRED" or chain_auth_reason != "AUTHORIZED":
            next_action = "HUMAN_APPROVAL_REQUIRED"
            reason = chain_auth_reason if chain_auth_reason != "AUTHORIZED" else (_clean(chain_reconcile.get("reason")) or "CHAIN_STOPPED")
            mutation_allowed = False
        elif cstate == "READY":
            if policy_tier == "DEVELOPMENT_MUTATION" and not rbac_mutation_ok:
                next_action = "HUMAN_APPROVAL_REQUIRED"
                reason = "RBAC_MUTATION_FORBIDDEN"
                mutation_allowed = False
            else:
                next_action = "CONTINUE_AUTONOMOUS"
                reason = "CHAIN_TRANSITION_READY"
                mutation_allowed = policy_tier == "DEVELOPMENT_MUTATION" and rbac_mutation_ok
        else:
            next_action = "REQUEST_MINIMUM_INFO"
            reason = f"CHAIN_STATE_{cstate or 'UNKNOWN'}"
            mutation_allowed = False
    elif not active_objective and last_certified is None:
        next_action = "REQUEST_MINIMUM_INFO"
        reason = "NO_ACTIVE_OBJECTIVE_OR_PRIOR_GATE"
        missing_fields.append("objective_hint")
        mutation_allowed = False
    elif not rbac_mutation_ok:
        next_action = "CONTINUE_AUTONOMOUS"
        policy_tier = "READ_ONLY"
        reason = "READ_ONLY_ONLY_WITHOUT_MUTATION_RBAC"
        mutation_allowed = False
    else:
        next_action = "CONTINUE_AUTONOMOUS"
        reason = "AUTHORIZED_CONTEXT_RESOLVED"
        mutation_allowed = True

    return {
        "schema": "edarsahub.worker-go-context.v1",
        "project": project_clean,
        "domain": domain_upper,
        "active_objective": active_objective,
        "chain_id": chain_clean or None,
        "last_certified_gate": last_certified,
        "pending_jobs": pending_jobs,
        "active_authorizations": {
            "identity_verified": identity_verified,
            "actor_email": requester.get("email") or None,
            "rbac_mutation_authorized": rbac_mutation_ok,
            "chain_authorization_status": chain_auth_reason,
        },
        "gate_dependencies": gate_dependencies,
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
    elif code == "SEMANTIC_BOUNDED_CONTEXT_UNSUPPORTED" or code == "SEMANTIC_CONTEXT_INVALID":
        rejected_field = "bounded_context"
        expected_ctx = cap_meta.get("bounded_context_rule") if cap_meta else "VALID_DOMAIN_TOKEN"
        allowed_correction = f"Set bounded_context to satisfy rule: {expected_ctx}."
    elif code == "SEMANTIC_CAPABILITY_MODE_MISMATCH":
        rejected_field = "mode"
        modes = ", ".join(cap_meta.get("modes", [])) if cap_meta else "READ_ONLY"
        allowed_correction = f"Use an allowed mode for {capability or 'capability'}: {modes}."
    elif code in {"SEMANTIC_CONSTRAINTS_UNSUPPORTED", "SEMANTIC_CONSTRAINTS_INVALID"}:
        rejected_field = "constraints"
        allowed_keys = cap_meta.get("allowed_constraints", []) if cap_meta else []
        keys_str = ", ".join(allowed_keys) if allowed_keys else "(none - pass {})"
        allowed_correction = (
            f"Pass constraints as a JSON object with only allowed keys: {keys_str}. "
            f"Never pass raw Worker fields: {', '.join(RAW_WORKER_FIELDS_FORBIDDEN)}."
        )
    elif code in {"SEMANTIC_SOURCE_SHA256_MISMATCH", "SEMANTIC_SOURCE_SHA256_REQUIRED"}:
        rejected_field = "constraints.change_spec[].source_sha256"
        allowed_correction = (
            "Refresh the live 64-hex SHA-256 of the target file in Edarsahub_Desarrollo "
            "before re-submitting; never reuse stale hashes."
        )
    elif code in {"SEMANTIC_PATH_FORBIDDEN", "SEMANTIC_PATH_INVALID", "SEMANTIC_DEV_PATH_FORBIDDEN", "SEMANTIC_DEV_PATH_INVALID"}:
        rejected_field = "constraints.paths" if "DEV" not in code else "constraints.change_spec[].path"
        roots = ", ".join(cap_meta.get("allowed_path_roots", [])) if cap_meta else "backend/modules/, backend/tests/, frontend/src/, tools/mirror_sync/"
        allowed_correction = f"Use only relative non-sensitive paths under allowed roots: {roots}."
    elif code == "SEMANTIC_DEV_OPERATION_FORBIDDEN":
        rejected_field = "constraints.change_spec[].operation"
        allowed_correction = "Use only declarative operations: replace_text, insert_before, insert_after, append_once, write_file."
    elif code == "SEMANTIC_DEV_WRITE_LARGE_SHRINK_BLOCKED":
        rejected_field = "constraints.change_spec[].content"
        allowed_correction = (
            "Overwriting a >=4096-byte file with <75% of its size is blocked; "
            "use targeted replace_text, insert_before, insert_after, or append_once instead."
        )
    elif code in {"RBAC_MUTATION_FORBIDDEN", "AUTHENTICATED_REQUESTER_EMAIL_REQUIRED"}:
        rejected_field = "rbac"
        allowed_correction = "Authenticated admin/worker:submit RBAC identity is required for MUTATION mode."
    elif code == "SCOPE_AUTHORIZATION_DENIED":
        rejected_field = "authorization_scope"
        allowed_correction = "Target domain, empresa_id, or unidad_negocio_pk is outside the caller's authorized scope."
    elif code == "SENSITIVE_FIELD_FORBIDDEN":
        rejected_field = "request"
        allowed_correction = "Remove sensitive credential/secret/token keys from the request payload."
    elif code == "SCHEMA_VALIDATION_ERROR":
        rejected_field = "request_schema"
        allowed_correction = (
            "Send required WorkerObjectiveRequest fields (objective, bounded_context, mode, capability, optional request_key, constraints) "
            "with valid types and no extra top-level keys."
        )

    return {
        "schema": "edarsahub.worker-semantic-diagnostic.v1",
        "error_code": code,
        "status": code,
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


def preflight_semantic_objective(
    request_payload: Mapping[str, Any],
    *,
    current_user: Mapping[str, Any],
    authorization_scope: Mapping[str, Any] | None = None,
    loaded_capabilities: tuple[str, ...] | list[str] | None = None,
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

        if capability.submitter is not None:
            # Direct-submitter capability (e.g. WORKER_REPAIR_BOUNDED): validate context & constraints without mutating
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
        existing_state = _find_existing_job_state(canonical_job["job_id"])
        if existing_state is not None:
            return {
                "schema": "edarsahub.worker-semantic-preflight.v1",
                "ok": True,
                "status": "EXISTS",
                "job_id": canonical_job["job_id"],
                "existing_lifecycle": existing_state,
                "duplicate_detected": True,
                "duplicate_prevented": True,
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
