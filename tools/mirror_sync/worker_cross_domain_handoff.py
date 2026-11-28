"""Canonical Cross-Domain Multichat Coordination & Autonomous Handoff Engine.

Eliminates manual prompt/result copy-pasting between domain chats while
reusing existing Universal Worker V4 infrastructure:
- Canonical queue & maintenance storage (`.git/universal-worker-queue/maintenance/handoffs/`)
- Existing MCP semantic ingress & Capability Registry (`CROSS_DOMAIN_HANDOFF_REGISTER`)
- Autonomous Execution Policy (`gate_chain_controller.py`)
- Exclusive publication via `gate_chain_publisher.submit()`
- Materialized Gate authorizations & recovery (`worker_lifecycle_recovery.py`)
- Knowledge Loop & circuit breakers (`worker_repair_capability_registry.py`, `worker_repair_auto_loop.py`)
- Independent terminal certification (`worker_result_reader.py`)
- Control Plane reconciliation & Centro de Control read-only visibility

Safety invariants (fail-closed):
- Never touches Production (`production_allowed=False`, `production_touched=False`).
- A handoff request NEVER grants permissions or authorization to `target_domain`.
- Functional development is NEVER transferred to Worker infrastructure domains.
- Protects against circular dependencies, recursive delegations, request storms,
  cross-chat duplicates, expired/revoked authorizations, secret transfers,
  untrusted external prompt injections, and restart/connectivity interruptions.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    from tools.mirror_sync import gate_chain_controller as policy_ctrl
    from tools.mirror_sync import gate_chain_publisher as gcp
    from tools.mirror_sync import worker_lifecycle_recovery as lifecycle_rec
    from tools.mirror_sync import worker_repair_auto_loop as auto_loop
    from tools.mirror_sync import worker_repair_capability_registry as learned_registry
    from tools.mirror_sync import worker_result_reader as result_reader
    from tools.mirror_sync import worker_scheduling as scheduling_mod
except ModuleNotFoundError:
    import gate_chain_controller as policy_ctrl
    import gate_chain_publisher as gcp
    import worker_lifecycle_recovery as lifecycle_rec
    import worker_repair_auto_loop as auto_loop
    import worker_repair_capability_registry as learned_registry
    import worker_result_reader as result_reader
    import worker_scheduling as scheduling_mod


SCHEMA_HANDOFF = "edarsahub.cross-domain-handoff.v1"
SCHEMA_HANDOFF_CLASSIFICATION = "edarsahub.cross-domain-handoff-classification.v1"
SCHEMA_HANDOFF_RECONCILE = "edarsahub.cross-domain-handoff-reconcile.v1"
SCHEMA_HANDOFF_OVERVIEW = "edarsahub.cross-domain-handoff-overview.v1"

HANDOFFS_SUBDIR = "handoffs"
RATE_LIMIT_STATE_FILENAME = "_rate_limit_state.json"

TERMINAL_CERTIFICATIONS = frozenset(policy_ctrl.TERMINAL_CERTIFICATIONS)
TERMINAL_STATUSES = frozenset(policy_ctrl.TERMINAL_STATUSES)

HANDOFF_LIFECYCLE_STATES = frozenset({
    "REGISTERED",
    "CLASSIFIED",
    "WAITING_AUTHORIZATION",
    "QUEUED_IN_TARGET_DOMAIN",
    "IN_PROGRESS",
    "RESOLVED_CERTIFIED",
    "RETURNED_TO_SOURCE",
    "BLOCKED_POLICY",
    "BLOCKED_CYCLE",
    "ESCALATED_HUMAN_REQUIRED",
    "SUPERSEDED",
})

ACTIVE_HANDOFF_STATES = frozenset({
    "REGISTERED",
    "CLASSIFIED",
    "WAITING_AUTHORIZATION",
    "QUEUED_IN_TARGET_DOMAIN",
    "IN_PROGRESS",
})

EXCEPTION_HANDOFF_STATES = frozenset({
    "WAITING_AUTHORIZATION",
    "BLOCKED_POLICY",
    "BLOCKED_CYCLE",
    "ESCALATED_HUMAN_REQUIRED",
})

HANDOFF_CLASSIFICATIONS = frozenset({
    "CERTIFIED_RESOLUTION_EXISTS",
    "EQUIVALENT_ACTIVE_WORK_EXISTS",
    "REUSABLE_CAPABILITY_AVAILABLE",
    "AUTONOMOUS_RECOVERY_ELIGIBLE",
    "REQUIRES_ADDITIONAL_AUTHORIZATION",
    "TARGET_BOUNDED_CONTEXT_REQUIRED",
    "NO_COMPATIBLE_CAPABILITY",
})

UPDATABLE_HANDOFF_STATES = frozenset({
    "REGISTERED",
    "CLASSIFIED",
    "WAITING_AUTHORIZATION",
    "QUEUED_IN_TARGET_DOMAIN",
    "ESCALATED_HUMAN_REQUIRED",
})

SEMANTIC_REASSIGNABLE_EXCEPTIONS = frozenset({
    "HANDOFF_CANARY_INSUFFICIENT_FOR_OBJECTIVE",
    "HANDOFF_SEMANTIC_CRITERIA_UNMET",
    "NO_COMPATIBLE_CAPABILITY_AVAILABLE",
})


def _is_semantic_blocker_reassignable(handoff: Mapping[str, Any]) -> bool:
    """True when a handoff is blocked by a semantically insufficient capability (e.g. READ_ONLY_CANARY)."""
    if handoff.get("dependency_satisfied") is True:
        return False
    exec_st = _clean(handoff.get("executor_status")).upper()
    exc_code = _clean(handoff.get("exception_code")).upper()
    return exec_st == "SEMANTIC_BLOCKER" or exc_code in SEMANTIC_REASSIGNABLE_EXCEPTIONS

MAX_HISTORY_ENTRIES = 100
NO_EXECUTOR_STALL_SECONDS = max(
    60, int(os.environ.get("EDARSAHUB_HANDOFF_NO_EXECUTOR_STALL_SECONDS", "900"))
)

_SYNTHETIC_SERVICE_EMAILS = frozenset({
    "worker@edarsahub.local",
    "worker-publisher@edarsahub.local",
    "system@edarsahub.local",
    "noreply@edarsahub.local",
})

RESOLUTION_STAGES = frozenset({
    "AUDIT_EXECUTED",
    "DIAGNOSTIC_COMPLETED",
    "CAPABILITY_AVAILABLE",
    "AUTHORIZATION_MATERIALIZED",
    "BLOCKER_RESOLVED",
    "IMPLEMENTATION_INTEGRATED",
    "RESULT_CERTIFIED",
    "SUCCESSOR_EXECUTED",
    "BLOCKER_IDENTIFIED_EVIDENCE_CERTIFIED",
})

SUCCESSOR_STATUSES = frozenset({
    "NO_SUCCESSOR_DEFINED",
    "WAITING_AUTHORIZATION",
    "CAPABILITY_REQUIRED",
    "REUSE_EXISTING_JOB",
    "SUCCESSOR_SUBMITTED",
    "SUCCESSOR_CERTIFIED",
    "SUCCESSOR_BLOCKED_PREFLIGHT",
    "SUCCESSOR_BLOCKED_SECURITY",
})

_GENERIC_ACCEPTANCE_CRITERIA = frozenset({
    "terminal_certification_valid",
    "tests_pass",
    "quality_gate_pass",
    "production_touched_false",
})

WORKER_INFRA_DOMAINS = frozenset({
    "WORKER_CONTROL_PLANE",
    "WORKER_RUNTIME_CONVERGENCE",
    "WORKER_SELF_HEALING",
    "WORKER_REPAIR_KNOWLEDGE_LOOP",
    "WORKER_INGRESS",
    "WORKER_MCP",
    "WORKER_OPERATIONS",
    "WORKER_CONSOLE",
})

SAFE_REUSABLE_READONLY_CAPABILITIES = frozenset({
    "READ_ONLY_CANARY",
    "REPOSITORY_CONTRACT_AUDIT_BOUNDED",
    "SQL_READONLY_PROFILE_AUDIT",
    "WORKER_PYTEST_CERTIFICATION_READONLY",
    "WORKER_RESULT_DETAIL_READ",
    "WORKER_RESULT_SEMANTIC_EXTRACT",
    "WORKER_MAINTENANCE_HISTORY_READONLY",
    "SQL_CONNECTIONS_BOOTSTRAP_READONLY",
    "SEC_RBAC_SQL_PERMISSION_MATRIX_READONLY",
})

RESTRICTED_DOMAINS = frozenset({"SEC_RBAC", "AUTH_RBAC", "SEGURIDAD"})

FORBIDDEN_DOMAINS = frozenset({
    "",
    "*",
    "ALL",
    "ANY",
    "GENERAL",
    "GLOBAL",
    "UNKNOWN",
    "DEFAULT",
    "MISC",
    "PRODUCTION",
    "PROD",
    "EDARSAHUB_PRODUCCION",
})

_DOMAIN_RE = re.compile(r"^[A-Z0-9][A-Z0-9._-]{1,119}$")
_TOKEN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{2,160}$")
_JOB_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$")

MAX_DELEGATION_DEPTH = max(1, int(os.environ.get("EDARSAHUB_HANDOFF_MAX_DELEGATION_DEPTH", "3")))
RATE_LIMIT_WINDOW_SECONDS = max(30, int(os.environ.get("EDARSAHUB_HANDOFF_RATE_WINDOW_SECONDS", "300")))
RATE_LIMIT_PAIR_MAX = max(2, int(os.environ.get("EDARSAHUB_HANDOFF_RATE_PAIR_MAX", "12")))
RATE_LIMIT_GLOBAL_MAX = max(5, int(os.environ.get("EDARSAHUB_HANDOFF_RATE_GLOBAL_MAX", "40")))
MAX_HANDOFF_DISPATCHES_PER_CYCLE = max(1, int(os.environ.get("EDARSAHUB_HANDOFF_MAX_DISPATCHES_PER_CYCLE", "2")))
MAX_ACCEPTANCE_CRITERIA = 12
MAX_OBJECTIVE_CHARS = 2000

_SENSITIVE_KEY_TOKENS = frozenset({
    "password",
    "passwd",
    "password_decrypted",
    "secret",
    "secrets",
    "token",
    "access_token",
    "refresh_token",
    "credential",
    "credentials",
    "api_key",
    "apikey",
    "private_key",
    "client_secret",
    "authorization_header",
    "cookie",
})

_SECRET_VALUE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bgh[opsu]_[A-Za-z0-9_]{12,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{16,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{16,}", re.IGNORECASE),
    re.compile(r"-----BEGIN\s+[A-Z0-9 ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(?:password|passwd|secret|api[_-]?key|client[_-]?secret|access[_-]?token)\s*[:=]\s*\S+"),
    re.compile(r"(?i)https?://[^/\s:@]+:[^/\s@]+@"),
)

_UNTRUSTED_PROMPT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\bignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?\b"),
    re.compile(r"(?i)\bdisregard\s+(?:all\s+)?(?:previous|prior|system)\s+(?:instructions?|rules?|policy)\b"),
    re.compile(r"(?i)\bbypass\s+(?:rbac|auth|authentication|authorization|guardrails?|security)\b"),
    re.compile(r"(?i)\boverride\s+(?:system\s+prompt|policy|rbac|governance|production)\b"),
    re.compile(r"(?i)\bproduction_allowed\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bedarsahub_produccion\b"),
    re.compile(r"(?i)\bgit\s+push\s+(?:--force|-f)\b"),
    re.compile(r"(?i)\bgit\s+reset\s+--hard\b"),
    re.compile(r"(?i)\bgit\s+clean\s+-[a-z]*f"),
    re.compile(r"(?i)\bsource\s+backend/\.env\b"),
    re.compile(r"(?i)\b(?:drop\s+table|truncate\s+table|rm\s+-rf\s+/)\b"),
    re.compile(r"(?i)\bjailbreak\b"),
)

_ADMIN_ROLES = frozenset({"superadministrador", "administrador", "superadmin", "admin"})


class HandoffError(ValueError):
    """Base fail-closed error for cross-domain handoff contract violations."""


class HandoffSecurityError(HandoffError):
    """Fail-closed security error (secrets, prompt injection, cycle, RBAC, auth)."""


class HandoffConflictError(HandoffError):
    """Fail-closed idempotency conflict when request_key drifts."""


class HandoffRateLimitError(HandoffError):
    """Fail-closed storm protection rejection."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _default_state_root() -> Path:
    root = Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
    return root / ".git" / "universal-worker-queue"


def handoffs_dir(state_root: Path | None = None) -> Path:
    qroot = state_root or _default_state_root()
    return qroot / "maintenance" / HANDOFFS_SUBDIR


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=".handoff_",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        tmp = handle.name
    os.replace(tmp, path)


def _read_json_safe(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _assert_no_secrets(value: Any, path: str = "handoff") -> None:
    if isinstance(value, Mapping):
        for raw_key, nested in value.items():
            low = str(raw_key).strip().lower()
            if low in _SENSITIVE_KEY_TOKENS:
                raise HandoffSecurityError(f"HANDOFF_SECRET_TRANSFER_FORBIDDEN:{path}.{raw_key}")
            _assert_no_secrets(nested, f"{path}.{raw_key}")
    elif isinstance(value, (list, tuple)):
        for idx, item in enumerate(value):
            _assert_no_secrets(item, f"{path}[{idx}]")
    elif isinstance(value, str):
        for pat in _SECRET_VALUE_PATTERNS:
            if pat.search(value):
                raise HandoffSecurityError(f"HANDOFF_SECRET_TRANSFER_FORBIDDEN:{path}")


def _assert_no_untrusted_prompt(value: Any, path: str = "handoff") -> None:
    if isinstance(value, Mapping):
        for raw_key, nested in value.items():
            _assert_no_untrusted_prompt(nested, f"{path}.{raw_key}")
    elif isinstance(value, (list, tuple)):
        for idx, item in enumerate(value):
            _assert_no_untrusted_prompt(item, f"{path}[{idx}]")
    elif isinstance(value, str):
        for pat in _UNTRUSTED_PROMPT_PATTERNS:
            if pat.search(value):
                raise HandoffSecurityError(f"HANDOFF_UNTRUSTED_PROMPT_BLOCKED:{path}")


def validate_domain_token(raw: Any, *, field_name: str) -> str:
    token = _clean(raw).upper()
    if not token or token in FORBIDDEN_DOMAINS or not _DOMAIN_RE.fullmatch(token):
        raise HandoffError(f"HANDOFF_DOMAIN_INVALID:{field_name}")
    if "PRODUCTION" in token or "PRODUCCION" in token:
        raise HandoffSecurityError("HANDOFF_PRODUCTION_FORBIDDEN")
    return token


def _validate_optional_token(raw: Any, *, field_name: str, job_id_style: bool = False) -> str | None:
    if raw is None or _clean(raw) == "":
        return None
    text = _clean(raw)
    regex = _JOB_ID_RE if job_id_style else _TOKEN_ID_RE
    if not regex.fullmatch(text):
        raise HandoffError(f"HANDOFF_FIELD_INVALID:{field_name}")
    return text


def _normalize_acceptance_criteria(raw: Any) -> list[str]:
    if raw is None:
        return [
            "terminal_certification_valid",
            "tests_pass",
            "quality_gate_pass",
            "production_touched_false",
        ]
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_ACCEPTANCE_CRITERIA:
        raise HandoffError("HANDOFF_ACCEPTANCE_CRITERIA_INVALID")
    out: list[str] = []
    for item in raw:
        text = _clean(item)
        if not text or len(text) > 240:
            raise HandoffError("HANDOFF_ACCEPTANCE_CRITERIA_INVALID")
        _assert_no_secrets(text, "acceptance_criteria")
        _assert_no_untrusted_prompt(text, "acceptance_criteria")
        if text not in out:
            out.append(text)
    return out


def compute_handoff_id(
    *,
    source_domain: str,
    target_domain: str,
    request_key: str,
) -> str:
    identity = {
        "source_domain": source_domain.upper(),
        "target_domain": target_domain.upper(),
        "request_key": request_key.strip(),
    }
    digest = hashlib.sha256(
        json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16].upper()
    src = re.sub(r"[^A-Z0-9]+", "", source_domain.upper())[:14] or "SRC"
    tgt = re.sub(r"[^A-Z0-9]+", "", target_domain.upper())[:14] or "TGT"
    return f"HO-{src}-{tgt}-{digest}"


def _handoff_core_fingerprint(
    *,
    source_domain: str,
    target_domain: str,
    source_objective: str,
    source_job_id: str | None,
    incident_id: str | None,
    dependency_id: str,
    acceptance_criteria: list[str],
    handoff_mode: str,
) -> str:
    basis = {
        "source_domain": source_domain,
        "target_domain": target_domain,
        "source_objective": source_objective,
        "source_job_id": source_job_id,
        "incident_id": incident_id,
        "dependency_id": dependency_id,
        "acceptance_criteria": list(acceptance_criteria),
        "handoff_mode": handoff_mode,
    }
    return hashlib.sha256(
        json.dumps(basis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _ensure_history(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Ensure immutable audit history exists even for legacy P0 handoff records."""
    hist = record.get("history")
    if isinstance(hist, list) and hist:
        return hist
    initial = {
        "event": "REGISTERED_INITIAL",
        "at_utc": _clean(record.get("created_at_utc")) or utc_now(),
        "lifecycle_state": record.get("lifecycle_state"),
        "classification": record.get("classification"),
        "requested_capability": record.get("requested_capability"),
        "auto_dispatch": bool(record.get("auto_dispatch", False)),
        "resolution_job_id": record.get("resolution_job_id"),
    }
    record["history"] = [initial]
    return record["history"]


def _append_history(
    record: dict[str, Any],
    event: str,
    *,
    actor_email: str | None = None,
    details: Mapping[str, Any] | None = None,
) -> None:
    hist = _ensure_history(record)
    entry: dict[str, Any] = {
        "event": _clean(event).upper() or "UPDATED",
        "at_utc": utc_now(),
        "lifecycle_state": record.get("lifecycle_state"),
        "classification": record.get("classification"),
        "requested_capability": record.get("requested_capability"),
        "auto_dispatch": bool(record.get("auto_dispatch", False)),
        "resolution_job_id": record.get("resolution_job_id"),
    }
    if actor_email:
        entry["actor_email"] = _clean(actor_email).lower()
    if isinstance(details, Mapping) and details:
        safe_details: dict[str, Any] = {}
        for k, v in details.items():
            if str(k).strip().lower() in _SENSITIVE_KEY_TOKENS:
                continue
            safe_details[str(k)] = v
        if safe_details:
            entry["details"] = safe_details
    hist.append(entry)
    if len(hist) > MAX_HISTORY_ENTRIES:
        record["history"] = [hist[0], *hist[-(MAX_HISTORY_ENTRIES - 1):]]


def _handoff_fingerprint(
    *,
    source_domain: str,
    target_domain: str,
    source_objective: str,
    source_job_id: str | None,
    incident_id: str | None,
    dependency_id: str,
    requested_capability: str | None,
    requested_constraints: Mapping[str, Any],
    acceptance_criteria: list[str],
    handoff_mode: str,
) -> str:
    basis = {
        "source_domain": source_domain,
        "target_domain": target_domain,
        "source_objective": source_objective,
        "source_job_id": source_job_id,
        "incident_id": incident_id,
        "dependency_id": dependency_id,
        "requested_capability": requested_capability,
        "requested_constraints": dict(requested_constraints),
        "acceptance_criteria": list(acceptance_criteria),
        "handoff_mode": handoff_mode,
    }
    return hashlib.sha256(
        json.dumps(basis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def load_handoff(handoff_id: str, *, state_root: Path | None = None) -> dict[str, Any] | None:
    clean_id = _clean(handoff_id)
    if not clean_id or not _JOB_ID_RE.fullmatch(clean_id):
        return None
    path = handoffs_dir(state_root) / f"{clean_id}.json"
    if not path.is_file():
        return None
    doc = _read_json_safe(path)
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA_HANDOFF:
        return None
    return doc


def save_handoff(record: Mapping[str, Any], *, state_root: Path | None = None) -> Path:
    hid = _clean(record.get("handoff_id"))
    if not hid or not _JOB_ID_RE.fullmatch(hid):
        raise HandoffError("HANDOFF_ID_INVALID")
    if record.get("production_allowed") is not False or record.get("production_touched") is not False:
        raise HandoffSecurityError("HANDOFF_PRODUCTION_FORBIDDEN")
    path = handoffs_dir(state_root) / f"{hid}.json"
    _atomic_write_json(path, dict(record))
    return path


def list_handoffs(*, state_root: Path | None = None) -> list[dict[str, Any]]:
    folder = handoffs_dir(state_root)
    if not folder.is_dir():
        return []
    items: list[dict[str, Any]] = []
    for path in sorted(folder.glob("*.json")):
        if path.name.startswith("_"):
            continue
        doc = _read_json_safe(path)
        if isinstance(doc, dict) and doc.get("schema") == SCHEMA_HANDOFF:
            items.append(doc)
    items.sort(
        key=lambda r: (str(r.get("updated_at_utc") or ""), str(r.get("handoff_id") or "")),
        reverse=True,
    )
    return items


def _extract_roles_and_perms(current_user: Mapping[str, Any] | None) -> tuple[set[str], set[str], bool]:
    if not isinstance(current_user, Mapping):
        return set(), set(), False
    role = _clean(
        current_user.get("role")
        or current_user.get("rol")
        or current_user.get("sec_perfil")
    ).lower()
    roles = {role} if role else set()
    raw_roles = current_user.get("roles") or current_user.get("sec_roles") or ()
    if isinstance(raw_roles, (list, tuple, set, frozenset)):
        roles.update(_clean(r).lower() for r in raw_roles if _clean(r))
    raw_perms = current_user.get("permissions") or current_user.get("permisos") or ()
    perms = (
        {_clean(p).lower() for p in raw_perms if _clean(p)}
        if isinstance(raw_perms, (list, tuple, set, frozenset))
        else set()
    )
    raw_scopes = current_user.get("scopes") or ()
    if isinstance(raw_scopes, str):
        perms.update(_clean(s).lower() for s in raw_scopes.split() if _clean(s))
    elif isinstance(raw_scopes, (list, tuple, set, frozenset)):
        perms.update(_clean(s).lower() for s in raw_scopes if _clean(s))
    role_code = _clean(current_user.get("role_code") or current_user.get("_sql_rol_codigo")).lower()
    if role_code:
        roles.add(role_code)
    is_admin = bool(roles & _ADMIN_ROLES) or bool(perms & {"rbac_admin", "*"})
    return roles, perms, is_admin


def _resolve_canonical_sql_service_identity(email: str) -> dict[str, Any]:
    """Resolve real canonical SQL user, effective permissions, and Worker scopes (fail-closed)."""
    clean_email = _clean(email).lower()
    if not clean_email or "@" not in clean_email or clean_email in _SYNTHETIC_SERVICE_EMAILS:
        raise HandoffSecurityError("HANDOFF_DISPATCH_IDENTITY_UNVERIFIABLE:INVALID_EMAIL")

    try:
        from modules.auth.repository import AuthRepository
        from core.rbac_sql.service import RBACSQLService
        from modules.worker_mcp.oauth_server import resolve_identity_scopes
        from tools.mirror_sync.worker_requester_rbac import authorize_requester
    except Exception as exc:
        raise HandoffSecurityError(
            f"HANDOFF_DISPATCH_IDENTITY_UNVERIFIABLE:CANONICAL_RBAC_UNAVAILABLE:{type(exc).__name__}"
        ) from exc

    try:
        user = AuthRepository.get_user_by_email(clean_email)
    except Exception as exc:
        raise HandoffSecurityError(
            f"HANDOFF_DISPATCH_IDENTITY_UNVERIFIABLE:SQL_LOOKUP_FAILED:{type(exc).__name__}"
        ) from exc

    if not isinstance(user, Mapping) or not bool(user.get("active")):
        raise HandoffSecurityError("HANDOFF_DISPATCH_IDENTITY_UNVERIFIABLE:USER_NOT_FOUND_OR_INACTIVE")

    sql_user_id = user.get("_sql_usuario_id") or user.get("UsuarioID")
    if not sql_user_id:
        raise HandoffSecurityError("HANDOFF_DISPATCH_IDENTITY_UNVERIFIABLE:SQL_USER_ID_MISSING")

    if not RBACSQLService.can_access_permission(sql_user_id, "RBAC_ADMIN"):
        raise HandoffSecurityError("HANDOFF_DISPATCH_RBAC_DENIED:RBAC_ADMIN_REQUIRED")

    authz = authorize_requester({
        "email": clean_email,
        "source": "edarsahub-worker-handoff",
        "project": "EDARSAHUB",
        "chat": "autonomous-handoff-dispatch",
    })
    if not isinstance(authz, Mapping) or authz.get("allowed") is not True:
        reason = _clean((authz or {}).get("reason")) or "REQUESTER_DENIED"
        raise HandoffSecurityError(f"HANDOFF_DISPATCH_RBAC_DENIED:{reason}")

    effective_perms = [
        _clean(p)
        for p in (RBACSQLService.get_effective_permissions(sql_user_id) or ())
        if _clean(p)
    ]
    identity_scopes = sorted(resolve_identity_scopes(dict(user)))
    if "worker:submit" not in identity_scopes:
        raise HandoffSecurityError("HANDOFF_DISPATCH_RBAC_DENIED:WORKER_SUBMIT_SCOPE_REQUIRED")

    return {
        "id": _clean(user.get("id") or sql_user_id),
        "usuario_id": int(sql_user_id),
        "email": _clean(user.get("email") or clean_email).lower(),
        "role": _clean(user.get("role")),
        "role_code": _clean(user.get("role_code") or user.get("_sql_rol_codigo")),
        "active": True,
        "permissions": sorted({*effective_perms, *identity_scopes}),
        "scopes": identity_scopes,
        "auth_source": "SQL_CANONICAL_RBAC",
        "identity_verified": True,
    }


def _resolve_canonical_dispatch_identity(
    handoff: Mapping[str, Any],
    *,
    current_user: Mapping[str, Any] | None = None,
    identity_resolver: Any = None,
) -> dict[str, Any]:
    """Fail-closed canonical dispatch identity resolver — never fabricates SUPERADMIN or ['*']."""
    source_domain = _clean(handoff.get("source_domain")).upper()
    target_domain = _clean(handoff.get("target_domain")).upper()
    handoff_mode = _clean(handoff.get("handoff_mode") or "READ_ONLY").upper()

    if current_user is not None:
        if not isinstance(current_user, Mapping):
            raise HandoffSecurityError("HANDOFF_DISPATCH_IDENTITY_UNVERIFIABLE:INVALID_USER_OBJECT")
        if current_user.get("active") is False:
            raise HandoffSecurityError("HANDOFF_DISPATCH_IDENTITY_UNVERIFIABLE:USER_INACTIVE")
        email = _clean(current_user.get("email")).lower()
        if not email or "@" not in email or email in _SYNTHETIC_SERVICE_EMAILS:
            raise HandoffSecurityError("HANDOFF_DISPATCH_IDENTITY_UNVERIFIABLE:EMAIL_REQUIRED")
        roles, perms, is_admin = _extract_roles_and_perms(current_user)
        if not roles and not perms:
            raise HandoffSecurityError("HANDOFF_DISPATCH_IDENTITY_UNVERIFIABLE:ROLES_OR_PERMISSIONS_REQUIRED")
        _verify_caller_rbac_and_scope(
            current_user=current_user,
            requester=None,
            source_domain=source_domain,
            target_domain=target_domain,
            handoff_mode=handoff_mode,
        )
        has_dispatch_authority = is_admin or bool(perms & {"worker:submit", "worker.submit", "rbac_admin"})
        if not has_dispatch_authority:
            raise HandoffSecurityError("HANDOFF_DISPATCH_RBAC_DENIED:SUBMIT_PERMISSION_REQUIRED")
        return dict(current_user)

    requester_email = _clean(handoff.get("requester_email")).lower()
    if not requester_email or "@" not in requester_email or requester_email in _SYNTHETIC_SERVICE_EMAILS:
        raise HandoffSecurityError("HANDOFF_DISPATCH_IDENTITY_UNVERIFIABLE:REQUESTER_EMAIL_MISSING")

    resolver = identity_resolver or _resolve_canonical_sql_service_identity
    try:
        resolved = resolver(requester_email)
    except HandoffSecurityError:
        raise
    except Exception as exc:
        raise HandoffSecurityError(
            f"HANDOFF_DISPATCH_IDENTITY_UNVERIFIABLE:{type(exc).__name__}"
        ) from exc

    if not isinstance(resolved, Mapping) or resolved.get("active") is False:
        raise HandoffSecurityError("HANDOFF_DISPATCH_IDENTITY_UNVERIFIABLE:RESOLVED_IDENTITY_INVALID")

    return _resolve_canonical_dispatch_identity(
        handoff,
        current_user=resolved,
        identity_resolver=None,
    )


def _revalidate_dispatch_authorization(
    handoff: Mapping[str, Any],
    *,
    actor: Mapping[str, Any],
    state_root: Path,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Revalidate production safety, RBAC scope, and live materialized authorizations at dispatch time."""
    if handoff.get("production_allowed") is not False or handoff.get("production_touched") is not False:
        raise HandoffSecurityError("HANDOFF_PRODUCTION_FORBIDDEN")

    source_domain = validate_domain_token(handoff.get("source_domain"), field_name="source_domain")
    target_domain = validate_domain_token(handoff.get("target_domain"), field_name="target_domain")
    handoff_mode = _clean(handoff.get("handoff_mode") or "READ_ONLY").upper()

    _verify_caller_rbac_and_scope(
        current_user=actor,
        requester=None,
        source_domain=source_domain,
        target_domain=target_domain,
        handoff_mode=handoff_mode,
    )

    auth_ref = _clean(handoff.get("authorization_ref")) or None
    auth_eval = _verify_authorization_ref(
        auth_ref,
        source_domain=source_domain,
        target_domain=target_domain,
        handoff_mode=handoff_mode,
        state_root=state_root,
        now_utc=now_utc,
    )

    if handoff_mode == "MUTATION":
        target_auth = lifecycle_rec.resolve_active_domain_authorization(
            target_domain,
            state_root=state_root,
            required_class="DEVELOPMENT_MUTATION",
            now_utc=now_utc,
        )
        gate_spec = {
            "gate_id": f"HANDOFF-DISPATCH-{_clean(handoff.get('handoff_id'))[:32] or target_domain}",
            "job_id": f"HO-{target_domain}",
            "mutation_class": "CODE_MUTATION",
            "authorization_class": "DEVELOPMENT_MUTATION",
            "require_traceable_authorization": True,
            "production_allowed": False,
            "required_scope": {"domain": [target_domain]},
        }
        decision = policy_ctrl.evaluate_autonomous_policy(
            gate_spec,
            authorization_classes=(target_auth.get("authorization_classes") or ()) if isinstance(target_auth, Mapping) else (),
            authorization_context=target_auth,
            now_utc=now_utc,
        )
        if not decision.get("allowed"):
            raise HandoffSecurityError(
                f"HANDOFF_DISPATCH_TARGET_AUTHORIZATION_DENIED:{decision.get('reason')}"
            )

    return auth_eval


def _verify_authorization_ref(
    authorization_ref: str | None,
    *,
    source_domain: str,
    target_domain: str,
    handoff_mode: str,
    state_root: Path,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Verify a materialized Gate authorization fail-closed without escalating target privileges."""
    auth_dir = state_root / "maintenance" / "authorizations"
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    if not authorization_ref:
        # Check if target_domain independently holds a valid active authorization (for classification only)
        target_active = lifecycle_rec.resolve_active_domain_authorization(
            target_domain,
            state_root=state_root,
            required_class="DEVELOPMENT_MUTATION",
            now_utc=now,
        )
        return {
            "supplied": False,
            "verified": False,
            "status": "NO_AUTHORIZATION_REF_SUPPLIED",
            "authorization_id": None,
            "source_domain_covered": False,
            "target_domain_independently_authorized": bool(target_active),
            "target_authorization_id": target_active.get("authorization_id") if isinstance(target_active, Mapping) else None,
        }

    matched_doc: dict[str, Any] | None = None
    if auth_dir.is_dir():
        for path in sorted(auth_dir.glob("*.json")):
            doc = _read_json_safe(path)
            if not isinstance(doc, dict) or doc.get("schema") != lifecycle_rec.SCHEMA_GATE_AUTHORIZATION:
                continue
            if authorization_ref in {
                _clean(doc.get("authorization_id")),
                _clean(doc.get("authorization_ref")),
                _clean(doc.get("gate_id")),
            }:
                matched_doc = doc
                break

    if matched_doc is None:
        raise HandoffSecurityError("HANDOFF_AUTHORIZATION_NOT_FOUND")
    if matched_doc.get("production_allowed") is True:
        raise HandoffSecurityError("HANDOFF_PRODUCTION_FORBIDDEN")
    if matched_doc.get("revoked") is True:
        raise HandoffSecurityError("HANDOFF_AUTHORIZATION_REVOKED")

    expires_raw = matched_doc.get("expires_at_utc")
    if expires_raw is not None:
        expires_dt = policy_ctrl._parse_utc(expires_raw)
        if expires_dt is None or expires_dt <= now:
            raise HandoffSecurityError("HANDOFF_AUTHORIZATION_EXPIRED")

    granted_domains = {
        _clean(d).upper()
        for d in ((matched_doc.get("scope") or {}).get("domains") or ())
        if _clean(d)
    }
    if not granted_domains or "*" in granted_domains:
        raise HandoffSecurityError("HANDOFF_AUTHORIZATION_SCOPE_INVALID")
    if source_domain not in granted_domains:
        raise HandoffSecurityError("HANDOFF_AUTHORIZATION_DOMAIN_MISMATCH")

    # Independent check for target_domain: source authorization alone NEVER escalates target_domain
    target_covered = target_domain in granted_domains
    if not target_covered:
        target_active = lifecycle_rec.resolve_active_domain_authorization(
            target_domain,
            state_root=state_root,
            required_class="DEVELOPMENT_MUTATION",
            now_utc=now,
        )
        target_covered = bool(target_active)
        target_auth_id = target_active.get("authorization_id") if isinstance(target_active, Mapping) else None
    else:
        target_auth_id = _clean(matched_doc.get("authorization_id"))

    if handoff_mode == "MUTATION":
        gate_spec = {
            "gate_id": _clean(matched_doc.get("gate_id")) or f"HANDOFF-{source_domain}",
            "mutation_class": "CODE_MUTATION",
            "authorization_class": "DEVELOPMENT_MUTATION",
            "require_traceable_authorization": True,
            "production_allowed": False,
            "required_scope": {"domain": [source_domain]},
        }
        ok, reason = policy_ctrl.evaluate_gate_authorization(
            gate_spec,
            authorization_classes=matched_doc.get("authorization_classes") or (),
            authorization_context=matched_doc,
            now_utc=now,
        )
        if not ok:
            raise HandoffSecurityError(f"HANDOFF_AUTHORIZATION_DENIED:{reason}")

    return {
        "supplied": True,
        "verified": True,
        "status": "MATERIALIZED_AUTHORIZATION_VERIFIED",
        "authorization_id": _clean(matched_doc.get("authorization_id")),
        "gate_id": _clean(matched_doc.get("gate_id")),
        "expires_at_utc": matched_doc.get("expires_at_utc"),
        "source_domain_covered": True,
        "target_domain_independently_authorized": target_covered,
        "target_authorization_id": target_auth_id,
    }


def _check_circular_and_recursive_delegation(
    *,
    source_domain: str,
    target_domain: str,
    delegation_chain: list[str],
    existing_handoffs: Iterable[Mapping[str, Any]],
    ignore_handoff_id: str | None = None,
) -> list[str]:
    """Detect direct self-delegation, transitive dependency cycles, and depth overflow."""
    if source_domain == target_domain:
        raise HandoffSecurityError("HANDOFF_CIRCULAR_DEPENDENCY:SELF_DELEGATION")

    normalized_chain: list[str] = []
    for raw_dom in delegation_chain:
        dom = validate_domain_token(raw_dom, field_name="delegation_chain")
        if dom in normalized_chain:
            raise HandoffSecurityError("HANDOFF_CIRCULAR_DEPENDENCY:CHAIN_REPEAT")
        normalized_chain.append(dom)

    if not normalized_chain:
        normalized_chain = [source_domain]
    elif normalized_chain[-1] != source_domain:
        if source_domain in normalized_chain:
            raise HandoffSecurityError("HANDOFF_CIRCULAR_DEPENDENCY:SOURCE_REPEAT")
        normalized_chain.append(source_domain)

    if target_domain in normalized_chain:
        raise HandoffSecurityError("HANDOFF_CIRCULAR_DEPENDENCY:TARGET_IN_CHAIN")

    full_chain = [*normalized_chain, target_domain]
    # Depth counts hops (edges), so [A, B] has depth 1
    if len(full_chain) - 1 > MAX_DELEGATION_DEPTH:
        raise HandoffSecurityError(
            f"HANDOFF_MAX_DELEGATION_DEPTH_EXCEEDED:{len(full_chain) - 1}>{MAX_DELEGATION_DEPTH}"
        )

    # Build directed adjacency graph of active cross-domain handoffs: u -> v
    graph: dict[str, set[str]] = {}
    for item in existing_handoffs:
        if not isinstance(item, Mapping):
            continue
        if ignore_handoff_id and _clean(item.get("handoff_id")) == ignore_handoff_id:
            continue
        state = _clean(item.get("lifecycle_state")).upper()
        if state not in ACTIVE_HANDOFF_STATES:
            continue
        src = _clean(item.get("source_domain")).upper()
        tgt = _clean(item.get("target_domain")).upper()
        if src and tgt:
            graph.setdefault(src, set()).add(tgt)

    # Adding source_domain -> target_domain creates a cycle iff target_domain can reach source_domain
    visited: set[str] = set()
    stack = [target_domain]
    while stack:
        node = stack.pop()
        if node == source_domain:
            raise HandoffSecurityError(
                f"HANDOFF_CIRCULAR_DEPENDENCY:{source_domain}->{target_domain}"
            )
        if node in visited:
            continue
        visited.add(node)
        for nxt in graph.get(node, ()):
            if nxt not in visited:
                stack.append(nxt)

    return full_chain


def _check_rate_limit(
    *,
    source_domain: str,
    target_domain: str,
    state_root: Path,
    now_epoch: float | None = None,
    dry_run: bool = False,
    pair_limit: int = RATE_LIMIT_PAIR_MAX,
    global_limit: int = RATE_LIMIT_GLOBAL_MAX,
    window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
) -> dict[str, Any]:
    """Sliding-window request storm protection (per domain-pair and global)."""
    now_ts = float(now_epoch if now_epoch is not None else time.time())
    cutoff = now_ts - float(window_seconds)
    path = handoffs_dir(state_root) / RATE_LIMIT_STATE_FILENAME
    raw = _read_json_safe(path) or {}
    events = raw.get("events") if isinstance(raw.get("events"), list) else []
    recent = [
        ev
        for ev in events
        if isinstance(ev, dict) and float(ev.get("ts") or 0.0) >= cutoff
    ]
    pair_key = f"{source_domain}->{target_domain}"
    pair_count = sum(1 for ev in recent if ev.get("pair") == pair_key)
    global_count = len(recent)

    if pair_count >= pair_limit:
        raise HandoffRateLimitError(
            f"HANDOFF_RATE_LIMIT_EXCEEDED:PAIR:{pair_key}:{pair_count}>={pair_limit}"
        )
    if global_count >= global_limit:
        raise HandoffRateLimitError(
            f"HANDOFF_RATE_LIMIT_EXCEEDED:GLOBAL:{global_count}>={global_limit}"
        )

    if not dry_run:
        recent.append({"ts": now_ts, "pair": pair_key})
        _atomic_write_json(
            path,
            {
                "schema": "edarsahub.cross-domain-handoff-rate-limit.v1",
                "updated_at_utc": utc_now(),
                "window_seconds": window_seconds,
                "events": recent[-500:],
                "production_touched": False,
            },
        )
    return {
        "pair": pair_key,
        "pair_count": pair_count,
        "global_count": global_count,
        "window_seconds": window_seconds,
        "allowed": True,
    }


def _verify_caller_rbac_and_scope(
    *,
    current_user: Mapping[str, Any] | None,
    requester: Mapping[str, Any] | None,
    source_domain: str,
    target_domain: str,
    handoff_mode: str,
) -> str:
    """Validate requester identity, RBAC, and domain scope without escalating target_domain."""
    email = ""
    if isinstance(current_user, Mapping):
        email = _clean(current_user.get("email")).lower()
    if not email and isinstance(requester, Mapping):
        email = _clean(requester.get("email")).lower()
    if not email or "@" not in email:
        raise HandoffSecurityError("HANDOFF_REQUESTER_IDENTITY_REQUIRED")

    if isinstance(current_user, Mapping):
        roles, perms, is_admin = _extract_roles_and_perms(current_user)
        if handoff_mode == "MUTATION" and not is_admin and not (
            perms & {"worker:submit", "worker.mutation", "worker:mutation", "*"}
        ):
            raise HandoffSecurityError("HANDOFF_RBAC_MUTATION_FORBIDDEN")

        raw_allowed = (
            current_user.get("allowed_domains")
            or current_user.get("domains")
            or current_user.get("bounded_contexts")
        )
        if isinstance(raw_allowed, (list, tuple, set, frozenset)):
            allowed_set = {_clean(d).upper() for d in raw_allowed if _clean(d)}
            if "*" not in allowed_set and source_domain not in allowed_set:
                raise HandoffSecurityError("HANDOFF_SOURCE_DOMAIN_FORBIDDEN")

        if target_domain in RESTRICTED_DOMAINS and not is_admin:
            raise HandoffSecurityError("HANDOFF_TARGET_DOMAIN_RESTRICTED")

    return email


def _extract_result_bounded_context(payload: Mapping[str, Any], job_id: str, state_root: Path) -> str:
    sched = payload.get("scheduling")
    if isinstance(sched, Mapping):
        bc = _clean(sched.get("bounded_context")).upper()
        if bc:
            return bc
    for sub in ("done", "processing", "pending", "drafts"):
        req_doc = _read_json_safe(state_root / sub / f"{job_id}.json")
        if not isinstance(req_doc, dict):
            continue
        inner = req_doc.get("job") if isinstance(req_doc.get("job"), Mapping) else req_doc
        rsched = inner.get("scheduling") if isinstance(inner, Mapping) else None
        if isinstance(rsched, Mapping):
            bc = _clean(rsched.get("bounded_context")).upper()
            if bc:
                return bc
    return ""


def _verify_terminal_result_certification(
    job_id: str,
    *,
    state_root: Path,
) -> dict[str, Any] | None:
    """Independent fail-closed verification of a Worker terminal result."""
    clean_id = _clean(job_id)
    if not clean_id or not _JOB_ID_RE.fullmatch(clean_id):
        return None
    res_path = state_root / "results" / f"{clean_id}.json"
    if not res_path.is_file():
        return None
    read = result_reader.read_canonical_result(res_path, expected_job_id=clean_id)
    if not read.terminal_result_valid or not isinstance(read.payload, dict):
        return None
    payload = read.payload
    if payload.get("production_touched") is not False:
        return None
    if _clean(payload.get("tests")).upper() != "PASS":
        return None
    if _clean(payload.get("quality_gate")).upper() != "PASS":
        return None
    if payload.get("blockers"):
        return None

    cert = _clean(payload.get("certification")).upper()
    published_commit = _clean(payload.get("published_result_commit")) or None
    cert_source = "CANONICAL_RESULT"

    marker_path = state_root / "published" / f"{clean_id}.json"
    if marker_path.is_file():
        marker = result_reader.parse_published_marker(marker_path)
        if isinstance(marker, dict) and "_invalid" not in marker:
            m_cert = _clean(marker.get("certification")).upper()
            if m_cert in TERMINAL_CERTIFICATIONS:
                cert = m_cert
                cert_source = "PUBLISHED_MARKER"
                m_commit = _clean(marker.get("commit"))
                if m_commit:
                    published_commit = m_commit

    if cert not in TERMINAL_CERTIFICATIONS:
        return None

    return {
        "job_id": clean_id,
        "status": _clean(payload.get("status")).upper(),
        "certification": cert,
        "certification_source": cert_source,
        "tests": "PASS",
        "quality_gate": "PASS",
        "commit_sha": (
            payload.get("certified_source_sha")
            or payload.get("development_sha")
            or payload.get("candidate_sha")
            or payload.get("commit_sha")
        ),
        "published_result_commit": published_commit,
        "completed_at_utc": _clean(payload.get("completed_at_utc")) or utc_now(),
        "summary_es": _clean(payload.get("summary_es"))[:500] or None,
        "production_touched": False,
    }


def _find_existing_certified_resolution(
    *,
    target_domain: str,
    requested_capability: str | None,
    requested_constraints: Mapping[str, Any],
    resolution_job_id: str | None,
    state_root: Path,
    existing_handoffs: Iterable[Mapping[str, Any]],
) -> dict[str, Any] | None:
    """Check if a valid certified terminal resolution already exists for this need."""
    # 1. Explicit resolution_job_id already certified
    if resolution_job_id:
        verified = _verify_terminal_result_certification(resolution_job_id, state_root=state_root)
        if verified is not None:
            return verified

    # 2. Certified handoff with identical target + capability + constraints
    if requested_capability:
        for item in existing_handoffs:
            if not isinstance(item, Mapping):
                continue
            if _clean(item.get("target_domain")).upper() != target_domain:
                continue
            if _clean(item.get("requested_capability")).upper() != requested_capability:
                continue
            if dict(item.get("requested_constraints") or {}) != dict(requested_constraints):
                continue
            cand_jid = _clean(item.get("resolution_job_id"))
            if cand_jid:
                verified = _verify_terminal_result_certification(cand_jid, state_root=state_root)
                if verified is not None:
                    return verified

    # 3. Direct scan of certified results in target_domain matching profile_code / pytest suite / repo audit
    if requested_capability in {
        "SQL_READONLY_PROFILE_AUDIT",
        "WORKER_PYTEST_CERTIFICATION_READONLY",
        "REPOSITORY_CONTRACT_AUDIT_BOUNDED",
    }:
        results_dir = state_root / "results"
        if results_dir.is_dir():
            target_profile = _clean(requested_constraints.get("profile_code")).upper()
            target_paths = (
                sorted(str(p).strip() for p in (requested_constraints.get("paths") or ()) if str(p).strip())
                if requested_capability == "REPOSITORY_CONTRACT_AUDIT_BOUNDED"
                else []
            )
            target_terms = (
                sorted(str(t).strip() for t in (requested_constraints.get("search_terms") or ()) if str(t).strip())
                if requested_capability == "REPOSITORY_CONTRACT_AUDIT_BOUNDED"
                else []
            )
            published_dir = state_root / "published"
            done_dir = state_root / "done"
            deadline = time.monotonic() + 4.0
            scanned = 0
            for res_path in sorted(results_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
                if scanned >= 80 or time.monotonic() > deadline:
                    break
                jid = res_path.stem
                # Fast pre-filter before parsing multi-MB result payloads (prevents 504 timeouts)
                if not (published_dir / f"{jid}.json").is_file() and res_path.stat().st_size > 524288:
                    continue
                req_preview = _read_json_safe(done_dir / f"{jid}.json") or {}
                inner_preview = req_preview.get("job") if isinstance(req_preview.get("job"), Mapping) else req_preview
                if isinstance(inner_preview, Mapping) and inner_preview:
                    sched_bc = _clean(((inner_preview.get("scheduling") or {}) if isinstance(inner_preview.get("scheduling"), Mapping) else {}).get("bounded_context")).upper()
                    if sched_bc and sched_bc != target_domain:
                        continue
                scanned += 1
                verified = _verify_terminal_result_certification(jid, state_root=state_root)
                if verified is None:
                    continue
                raw = _read_json_safe(res_path) or {}
                bc = _extract_result_bounded_context(raw, jid, state_root)
                if bc != target_domain:
                    continue
                checks = raw.get("checks") if isinstance(raw.get("checks"), list) else []
                if requested_capability == "SQL_READONLY_PROFILE_AUDIT" and target_profile:
                    if any(
                        isinstance(c, Mapping)
                        and c.get("type") == "sql_readonly_audit"
                        and _clean(c.get("profile_code")).upper() == target_profile
                        for c in checks
                    ):
                        return verified
                elif requested_capability == "WORKER_PYTEST_CERTIFICATION_READONLY":
                    if any(isinstance(c, Mapping) and c.get("type") == "pytest" for c in checks):
                        return verified
                elif requested_capability == "REPOSITORY_CONTRACT_AUDIT_BOUNDED" and target_paths and target_terms:
                    req_doc = _read_json_safe(state_root / "done" / f"{jid}.json") or {}
                    inner = req_doc.get("job") if isinstance(req_doc.get("job"), Mapping) else req_doc
                    req_checks = inner.get("checks") if isinstance(inner, Mapping) and isinstance(inner.get("checks"), list) else []
                    for c in req_checks:
                        if not isinstance(c, Mapping) or c.get("type") != "repository_contract_audit":
                            continue
                        creq = c.get("request") if isinstance(c.get("request"), Mapping) else {}
                        c_paths = sorted(str(p).strip() for p in (creq.get("paths") or ()) if str(p).strip())
                        c_terms = sorted(str(t).strip() for t in (creq.get("search_terms") or ()) if str(t).strip())
                        if c_paths == target_paths and c_terms == target_terms:
                            return verified
    return None


def _find_equivalent_active_work(
    *,
    target_domain: str,
    requested_capability: str | None,
    requested_constraints: Mapping[str, Any],
    ignore_handoff_id: str | None,
    state_root: Path,
    existing_handoffs: Iterable[Mapping[str, Any]],
) -> dict[str, Any] | None:
    """Detect equivalent in-flight work in target_domain so chats never duplicate jobs."""
    if requested_capability:
        for item in existing_handoffs:
            if not isinstance(item, Mapping):
                continue
            hid = _clean(item.get("handoff_id"))
            if ignore_handoff_id and hid == ignore_handoff_id:
                continue
            if _clean(item.get("lifecycle_state")).upper() not in {"IN_PROGRESS", "QUEUED_IN_TARGET_DOMAIN"}:
                continue
            if _clean(item.get("target_domain")).upper() != target_domain:
                continue
            if _clean(item.get("requested_capability")).upper() != requested_capability:
                continue
            if dict(item.get("requested_constraints") or {}) != dict(requested_constraints):
                continue
            active_jid = _clean(item.get("resolution_job_id"))
            if active_jid:
                return {"source": "ACTIVE_HANDOFF", "job_id": active_jid, "handoff_id": hid}

    for lifecycle, dirname in (("PROCESSING", "processing"), ("PENDING", "pending")):
        folder = state_root / dirname
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.json")):
            doc = _read_json_safe(path)
            if not isinstance(doc, dict):
                continue
            inner = doc.get("job") if isinstance(doc.get("job"), Mapping) else doc
            sched = inner.get("scheduling") if isinstance(inner, Mapping) else None
            bc = _clean(sched.get("bounded_context")).upper() if isinstance(sched, Mapping) else ""
            if bc != target_domain:
                continue
            if requested_capability == "SQL_READONLY_PROFILE_AUDIT":
                target_profile = _clean(requested_constraints.get("profile_code")).upper()
                checks = inner.get("checks") if isinstance(inner.get("checks"), list) else []
                if target_profile and any(
                    isinstance(c, Mapping) and _clean(c.get("profile_code")).upper() == target_profile
                    for c in checks
                ):
                    return {"source": f"QUEUE_{lifecycle}", "job_id": _clean(inner.get("job_id")) or path.stem}
            elif requested_capability == "WORKER_PYTEST_CERTIFICATION_READONLY":
                checks = inner.get("checks") if isinstance(inner.get("checks"), list) else []
                if any(isinstance(c, Mapping) and c.get("type") == "pytest" for c in checks):
                    return {"source": f"QUEUE_{lifecycle}", "job_id": _clean(inner.get("job_id")) or path.stem}
    return None


def _context_rule_matches(rule: str, target_domain: str) -> bool:
    clean_rule = _clean(rule).upper()
    dom = _clean(target_domain).upper()
    if not dom:
        return False
    if clean_rule == "ANY_VALID_TOKEN":
        return True
    if not clean_rule or clean_rule == "CAPABILITY_OWNED":
        return False
    allowed = {part.strip().upper() for part in clean_rule.split("|") if part.strip()}
    return dom in allowed


def resolve_compatible_capabilities(
    *,
    target_domain: str,
    handoff_mode: str = "READ_ONLY",
    requested_capability: str | None = None,
    requested_constraints: Mapping[str, Any] | None = None,
    incident_id: str | None = None,
) -> dict[str, Any]:
    """Resolve compatible capabilities from the canonical Capability Registry & Knowledge Loop."""
    dom = _clean(target_domain).upper()
    mode = _clean(handoff_mode or "READ_ONLY").upper()
    req_cap = _clean(requested_capability).upper() or None
    req_constraints = dict(requested_constraints or {}) if isinstance(requested_constraints, Mapping) else {}
    allowed_modes = {"READ_ONLY", "READ_ONLY_SQL"} if mode == "READ_ONLY" else {"MUTATION"}

    try:
        from modules.worker_ingress import semantic_capabilities as sem_caps

        catalog_entries = list(sem_caps.capability_catalog())
    except Exception as exc:
        return {
            "compatible": False,
            "executable": False,
            "selected_capability": None,
            "selected_mode": None,
            "resolution_source": "CAPABILITY_REGISTRY_UNAVAILABLE",
            "compatible_capabilities": [],
            "has_compatible_capabilities": False,
            "exception_code": "NO_COMPATIBLE_CAPABILITY_REGISTRY_UNAVAILABLE",
            "reason": f"CAPABILITY_REGISTRY_UNAVAILABLE:{type(exc).__name__}",
        }

    catalog_by_code = {_clean(item.get("code")).upper(): item for item in catalog_entries}
    compatible_list: list[dict[str, Any]] = []
    for entry in catalog_entries:
        code = _clean(entry.get("code")).upper()
        if not code or code == "CROSS_DOMAIN_HANDOFF_REGISTER":
            continue
        entry_modes = {_clean(m).upper() for m in (entry.get("modes") or ()) if _clean(m)}
        if not (entry_modes & allowed_modes):
            continue
        ctx_rule = _clean(entry.get("bounded_context_rule"))
        if not _context_rule_matches(ctx_rule, dom):
            continue
        compatible_list.append({
            "code": code,
            "modes": sorted(entry_modes & allowed_modes),
            "bounded_context_rule": ctx_rule,
            "required_constraints": list(entry.get("required_constraints") or []),
            "allowed_constraints": list(entry.get("allowed_constraints") or []),
            "domain_specific": ctx_rule.upper() != "ANY_VALID_TOKEN",
            "auto_dispatch_safe": code in SAFE_REUSABLE_READONLY_CAPABILITIES and mode == "READ_ONLY",
        })

    # Prioritize domain-specific capabilities ahead of generic ANY_VALID_TOKEN ones
    compatible_list.sort(key=lambda item: (not item["domain_specific"], item["code"]))

    if req_cap:
        if req_cap == "CROSS_DOMAIN_HANDOFF_REGISTER":
            return {
                "compatible": False,
                "executable": False,
                "selected_capability": None,
                "selected_mode": None,
                "resolution_source": "CAPABILITY_REGISTRY",
                "compatible_capabilities": compatible_list,
                "has_compatible_capabilities": bool(compatible_list),
                "exception_code": "HANDOFF_RECURSIVE_CAPABILITY_FORBIDDEN",
                "reason": "RECURSIVE_CAPABILITY_FORBIDDEN",
            }
        entry = catalog_by_code.get(req_cap)
        if entry is None:
            return {
                "compatible": False,
                "executable": False,
                "selected_capability": None,
                "selected_mode": None,
                "resolution_source": "CAPABILITY_REGISTRY",
                "compatible_capabilities": compatible_list,
                "has_compatible_capabilities": bool(compatible_list),
                "exception_code": "NO_COMPATIBLE_CAPABILITY_UNKNOWN",
                "reason": f"CAPABILITY_NOT_REGISTERED:{req_cap}",
            }
        entry_modes = {_clean(m).upper() for m in (entry.get("modes") or ()) if _clean(m)}
        matched_modes = sorted(entry_modes & allowed_modes)
        if not matched_modes:
            return {
                "compatible": False,
                "executable": False,
                "selected_capability": None,
                "selected_mode": None,
                "resolution_source": "CAPABILITY_REGISTRY",
                "compatible_capabilities": compatible_list,
                "has_compatible_capabilities": bool(compatible_list),
                "exception_code": "NO_COMPATIBLE_CAPABILITY_MODE_MISMATCH",
                "reason": f"CAPABILITY_MODE_INCOMPATIBLE:{req_cap}:{mode}",
            }
        ctx_rule = _clean(entry.get("bounded_context_rule"))
        if not _context_rule_matches(ctx_rule, dom):
            return {
                "compatible": False,
                "executable": False,
                "selected_capability": None,
                "selected_mode": None,
                "resolution_source": "CAPABILITY_REGISTRY",
                "compatible_capabilities": compatible_list,
                "has_compatible_capabilities": bool(compatible_list),
                "exception_code": "NO_COMPATIBLE_CAPABILITY_DOMAIN_MISMATCH",
                "reason": f"CAPABILITY_DOMAIN_INCOMPATIBLE:{req_cap}:{dom}",
            }

        cap_obj = sem_caps.resolve_capability(req_cap)
        if mode == "READ_ONLY" and req_cap in SAFE_REUSABLE_READONLY_CAPABILITIES and cap_obj.builder is not None:
            exec_mode = "READ_ONLY_SQL" if "READ_ONLY_SQL" in matched_modes else "READ_ONLY"
            try:
                cap_obj.builder({
                    "objective": "Dry-run reusable capability compatibility check",
                    "bounded_context": dom,
                    "mode": exec_mode,
                    "capability": req_cap,
                    "constraints": dict(req_constraints),
                })
            except Exception as exc:
                return {
                    "compatible": False,
                    "executable": False,
                    "selected_capability": None,
                    "selected_mode": None,
                    "resolution_source": "CAPABILITY_REGISTRY",
                    "compatible_capabilities": compatible_list,
                    "has_compatible_capabilities": bool(compatible_list),
                    "exception_code": "NO_COMPATIBLE_CAPABILITY_CONTRACT_INVALID",
                    "reason": f"CAPABILITY_CONTRACT_INCOMPATIBLE:{req_cap}:{_clean(exc)[:120]}",
                }
            return {
                "compatible": True,
                "executable": True,
                "selected_capability": req_cap,
                "selected_mode": exec_mode,
                "resolution_source": "CAPABILITY_REGISTRY",
                "compatible_capabilities": compatible_list,
                "has_compatible_capabilities": bool(compatible_list),
                "exception_code": None,
                "reason": f"CAPABILITY_COMPATIBLE:{req_cap}",
            }

        if mode == "MUTATION":
            return {
                "compatible": True,
                "executable": False,
                "selected_capability": req_cap,
                "selected_mode": "MUTATION",
                "resolution_source": "CAPABILITY_REGISTRY",
                "compatible_capabilities": compatible_list,
                "has_compatible_capabilities": bool(compatible_list),
                "exception_code": None,
                "reason": f"MUTATION_CAPABILITY_COMPATIBLE_REQUIRES_TARGET_OWNER:{req_cap}",
            }

        return {
            "compatible": False,
            "executable": False,
            "selected_capability": None,
            "selected_mode": None,
            "resolution_source": "CAPABILITY_REGISTRY",
            "compatible_capabilities": compatible_list,
            "has_compatible_capabilities": bool(compatible_list),
            "exception_code": "NO_COMPATIBLE_CAPABILITY_NOT_REUSABLE",
            "reason": f"CAPABILITY_NOT_SAFE_REUSABLE:{req_cap}",
        }

    # No requested_capability supplied yet: check Knowledge Loop learned capability for Worker infra domains
    if dom in WORKER_INFRA_DOMAINS and incident_id:
        try:
            learned = learned_registry.resolve_learned_capability(incident_id=incident_id)
            if learned is not None and learned.reusable:
                return {
                    "compatible": True,
                    "executable": True,
                    "selected_capability": learned.code,
                    "selected_mode": mode,
                    "resolution_source": "KNOWLEDGE_LOOP_LEARNED_REGISTRY",
                    "compatible_capabilities": compatible_list,
                    "has_compatible_capabilities": True,
                    "exception_code": None,
                    "reason": f"LEARNED_CAPABILITY_MATCHED:{learned.code}",
                }
        except Exception:
            pass

    if not compatible_list:
        return {
            "compatible": False,
            "executable": False,
            "selected_capability": None,
            "selected_mode": None,
            "resolution_source": "CAPABILITY_REGISTRY",
            "compatible_capabilities": [],
            "has_compatible_capabilities": False,
            "exception_code": "NO_COMPATIBLE_CAPABILITY_AVAILABLE",
            "reason": f"NO_COMPATIBLE_CAPABILITY_FOR_DOMAIN:{dom}:{mode}",
        }

    return {
        "compatible": False,
        "executable": False,
        "selected_capability": None,
        "selected_mode": None,
        "resolution_source": "CAPABILITY_REGISTRY",
        "compatible_capabilities": compatible_list,
        "has_compatible_capabilities": True,
        "exception_code": None,
        "reason": f"CAPABILITY_ASSIGNMENT_REQUIRED:{dom}",
    }


def _is_reusable_capability_available(
    *,
    target_domain: str,
    requested_capability: str | None,
    requested_constraints: Mapping[str, Any],
    incident_id: str | None,
    handoff_mode: str = "READ_ONLY",
) -> tuple[bool, str | None]:
    """Check existing Capability Registry & Knowledge Loop for reusable resolution capabilities."""
    res = resolve_compatible_capabilities(
        target_domain=target_domain,
        handoff_mode=handoff_mode,
        requested_capability=requested_capability,
        requested_constraints=requested_constraints,
        incident_id=incident_id,
    )
    if res.get("compatible") is True and res.get("executable") is True and res.get("selected_capability"):
        return True, str(res["selected_capability"])
    return False, None


_SOURCE_JOB_RECOVERY_MARKERS = (
    "AGENT_GUARD_WORKTREE_FAILED",
    "UNPUBLISHED_DRAFT_RECOVERY",
    "EXISTING_DRAFT",
    "RECOVER_EXISTING_DRAFT",
    "PRESERVE_ORIGINAL_JOB_ID",
    "EXISTING_JOB_RECOVERED",
    "BORRADOR",
    "DRAFT",
    "RECUPERAR",
    "RECOVER",
)


def _is_source_job_recovery_handoff(handoff: Mapping[str, Any]) -> bool:
    """Identify handoffs specifically requesting canonical recovery of an existing source_job_id."""
    target_domain = _clean(handoff.get("target_domain")).upper()
    if target_domain not in WORKER_INFRA_DOMAINS:
        return False
    source_job_id = _clean(handoff.get("source_job_id"))
    if not source_job_id or not _JOB_ID_RE.fullmatch(source_job_id):
        return False
    if _clean(handoff.get("requested_capability")):
        return False
    handoff_mode = _clean(handoff.get("handoff_mode") or "READ_ONLY").upper()
    if handoff_mode not in {"READ_ONLY", "READ_ONLY_SQL"}:
        return False
    if _clean(handoff.get("classification_reason")).upper() == "UNPUBLISHED_DRAFT_RECOVERY":
        return True
    haystack = " ".join(
        [
            _clean(handoff.get("source_objective")),
            _clean(handoff.get("request_key")),
            " ".join(str(c) for c in (handoff.get("acceptance_criteria") or ())),
        ]
    ).upper()
    return any(marker in haystack for marker in _SOURCE_JOB_RECOVERY_MARKERS)


def _verify_source_job_terminal_recovery(
    handoff: Mapping[str, Any],
    *,
    state_root: Path,
) -> dict[str, Any] | None:
    """Fail-closed verification that a recovery handoff's source_job_id already reached valid terminal certification.

    Verifies:
    1. Handoff is strictly a source_job_id recovery request targeting Worker infrastructure.
    2. Handoff payload fingerprint integrity (payload_fingerprint == initial_payload_fingerprint when set).
    3. Independent terminal certification of source_job_id (tests=PASS, quality_gate=PASS, blockers=[], production_touched=False).
    4. Exact identity & bounded_context match (source_job_id & source_domain).
    5. Exact canonical draft/done payload fingerprint match when both draft and done exist.
    6. Semantic acceptance criteria compatibility (never closes on insufficient evidence or canary substitute).
    """
    if not _is_source_job_recovery_handoff(handoff):
        return None

    source_job_id = _clean(handoff.get("source_job_id"))
    source_domain = _clean(handoff.get("source_domain")).upper()
    if not source_job_id or not source_domain:
        return None

    cur_fp = _clean(handoff.get("payload_fingerprint"))
    init_fp = _clean(handoff.get("initial_payload_fingerprint"))
    if cur_fp and init_fp and cur_fp != init_fp:
        return None

    verified = _verify_terminal_result_certification(source_job_id, state_root=state_root)
    if verified is None:
        return None

    res_doc = _read_json_safe(state_root / "results" / f"{source_job_id}.json")
    if not isinstance(res_doc, dict):
        return None
    if _clean(res_doc.get("job_id")) != source_job_id:
        return None

    res_bc = _extract_result_bounded_context(res_doc, source_job_id, state_root)
    if res_bc != source_domain:
        return None

    draft_doc = _read_json_safe(state_root / "drafts" / f"{source_job_id}.json")
    done_raw = _read_json_safe(state_root / "done" / f"{source_job_id}.json")
    done_inner = (
        done_raw.get("job")
        if isinstance(done_raw, dict) and isinstance(done_raw.get("job"), Mapping)
        else done_raw
    )
    if isinstance(done_inner, Mapping) and _clean(done_inner.get("job_id")) not in {"", source_job_id}:
        return None

    draft_fp = lifecycle_rec._canonical_draft_fingerprint(draft_doc) if isinstance(draft_doc, Mapping) else None
    done_fp = lifecycle_rec._canonical_draft_fingerprint(done_inner) if isinstance(done_inner, Mapping) else None
    if draft_fp and done_fp and draft_fp != done_fp:
        return None
    if not done_fp and not (state_root / "published" / f"{source_job_id}.json").is_file():
        return None

    # Ensure checks inside terminal result actually passed (fail-closed against empty/failed evidence)
    checks = res_doc.get("checks")
    if isinstance(checks, list):
        for chk in checks:
            if isinstance(chk, Mapping):
                chk_st = _clean(chk.get("status")).upper()
                if chk_st and chk_st != "PASS":
                    return None

    # Validate semantic criteria before allowing terminal resolution reuse
    sem_preview = evaluate_handoff_semantic_satisfaction(
        handoff,
        verified,
        capability_used=_clean(res_doc.get("capability") or "").upper() or None,
    )
    if sem_preview.get("satisfied") is not True:
        return None

    return {
        **verified,
        "source_job_recovery_verified": True,
        "source_job_fingerprint": done_fp or draft_fp,
        "recovery_verification": {
            "identity_matched": True,
            "domain_matched": True,
            "fingerprint_matched": bool(draft_fp and done_fp and draft_fp == done_fp),
            "handoff_payload_integrity_matched": bool(not cur_fp or not init_fp or cur_fp == init_fp),
            "terminal_certification_verified": True,
            "semantic_criteria_verified": True,
        },
    }


def _is_autonomous_recovery_eligible(
    *,
    target_domain: str,
    source_job_id: str | None,
    incident_id: str | None,
    requested_capability: str | None,
    state_root: Path,
) -> tuple[bool, str]:
    """Strictly scope autonomous recovery to Worker infrastructure domains — NEVER business dev."""
    if target_domain not in WORKER_INFRA_DOMAINS:
        return False, "NON_WORKER_DOMAIN_RECOVERY_FORBIDDEN"

    cap_code = _clean(requested_capability).upper()
    if cap_code == "WORKER_REPAIR_BOUNDED" and incident_id:
        return True, "WORKER_REPAIR_BOUNDED_INCIDENT"

    if source_job_id:
        res_doc = _read_json_safe(state_root / "results" / f"{source_job_id}.json")
        if isinstance(res_doc, dict):
            st = _clean(res_doc.get("status")).upper()
            if st in lifecycle_rec.CONCURRENCY_BLOCKED_STATUSES and (state_root / "drafts" / f"{source_job_id}.json").is_file():
                return True, f"CONCURRENCY_BLOCKED_JOB:{st}"
        if (state_root / "drafts" / f"{source_job_id}.json").is_file() and not (
            (state_root / "results" / f"{source_job_id}.json").is_file()
            or (state_root / "pending" / f"{source_job_id}.json").is_file()
            or (state_root / "processing" / f"{source_job_id}.json").is_file()
        ):
            return True, "UNPUBLISHED_DRAFT_RECOVERY"

    if incident_id and (state_root / "maintenance" / "incidents" / f"{incident_id}.json").is_file():
        return True, "REGISTERED_MAINTENANCE_INCIDENT"

    return False, "NOT_RECOVERY_ELIGIBLE"


def classify_handoff_request(
    handoff: Mapping[str, Any],
    *,
    state_root: Path | None = None,
    existing_handoffs: Iterable[Mapping[str, Any]] | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Deterministically classify a cross-domain handoff request (Fase 3)."""
    qroot = state_root or _default_state_root()
    all_handoffs = list(existing_handoffs) if existing_handoffs is not None else list_handoffs(state_root=qroot)

    hid = _clean(handoff.get("handoff_id"))
    source_domain = _clean(handoff.get("source_domain")).upper()
    target_domain = _clean(handoff.get("target_domain")).upper()
    handoff_mode = _clean(handoff.get("handoff_mode") or "READ_ONLY").upper()
    requested_capability = _clean(handoff.get("requested_capability")).upper() or None
    requested_constraints = (
        dict(handoff.get("requested_constraints") or {})
        if isinstance(handoff.get("requested_constraints"), Mapping)
        else {}
    )
    source_job_id = _clean(handoff.get("source_job_id")) or None
    incident_id = _clean(handoff.get("incident_id")) or None
    resolution_job_id = _clean(handoff.get("resolution_job_id")) or None

    # 1. Existing certified terminal resolution
    certified = _find_existing_certified_resolution(
        target_domain=target_domain,
        requested_capability=requested_capability,
        requested_constraints=requested_constraints,
        resolution_job_id=resolution_job_id,
        state_root=qroot,
        existing_handoffs=all_handoffs,
    )
    if certified is not None:
        return {
            "schema": SCHEMA_HANDOFF_CLASSIFICATION,
            "classification": "CERTIFIED_RESOLUTION_EXISTS",
            "reason": "EXISTING_CERTIFIED_TERMINAL_RESOLUTION_REUSED",
            "resolution_job_id": certified["job_id"],
            "certified_evidence": certified,
            "lifecycle_state": "RESOLVED_CERTIFIED",
            "next_allowed_action": "RETURN_CERTIFIED_RESOLUTION",
            "requires_human_intervention": False,
            "dispatch_eligible": False,
            "has_executor": True,
            "executor_status": "RESOLVED",
            "compatible_capabilities": [],
            "exception_code": None,
            "exception_reason": None,
            "production_touched": False,
        }

    # 1b. Recovery handoff whose source_job_id already reached verified terminal certification
    source_recovered = _verify_source_job_terminal_recovery(
        handoff,
        state_root=qroot,
    )
    if source_recovered is not None:
        return {
            "schema": SCHEMA_HANDOFF_CLASSIFICATION,
            "classification": "CERTIFIED_RESOLUTION_EXISTS",
            "reason": "SOURCE_JOB_TERMINAL_CERTIFICATION_VERIFIED",
            "resolution_job_id": source_recovered["job_id"],
            "certified_evidence": source_recovered,
            "lifecycle_state": "RESOLVED_CERTIFIED",
            "next_allowed_action": "RETURN_CERTIFIED_RESOLUTION",
            "requires_human_intervention": False,
            "dispatch_eligible": False,
            "has_executor": True,
            "executor_status": "RESOLVED",
            "compatible_capabilities": [],
            "exception_code": None,
            "exception_reason": None,
            "production_touched": False,
        }

    # 2. Equivalent active in-flight work
    active_work = _find_equivalent_active_work(
        target_domain=target_domain,
        requested_capability=requested_capability,
        requested_constraints=requested_constraints,
        ignore_handoff_id=hid,
        state_root=qroot,
        existing_handoffs=all_handoffs,
    )
    if active_work is not None:
        return {
            "schema": SCHEMA_HANDOFF_CLASSIFICATION,
            "classification": "EQUIVALENT_ACTIVE_WORK_EXISTS",
            "reason": f"EQUIVALENT_ACTIVE_JOB:{active_work['source']}",
            "resolution_job_id": active_work["job_id"],
            "lifecycle_state": "IN_PROGRESS",
            "next_allowed_action": "WAIT_FOR_IN_FLIGHT_JOB",
            "requires_human_intervention": False,
            "dispatch_eligible": False,
            "has_executor": True,
            "executor_status": "IN_FLIGHT_JOB",
            "compatible_capabilities": [],
            "exception_code": None,
            "exception_reason": None,
            "production_touched": False,
        }

    # 3. Resolve compatible capabilities via Capability Registry & Knowledge Loop
    cap_resolution = resolve_compatible_capabilities(
        target_domain=target_domain,
        handoff_mode=handoff_mode,
        requested_capability=requested_capability,
        requested_constraints=requested_constraints,
        incident_id=incident_id,
    )
    compat_caps = list(cap_resolution.get("compatible_capabilities") or [])
    reusable_ok = bool(cap_resolution.get("compatible") and cap_resolution.get("executable"))
    reusable_code = cap_resolution.get("selected_capability")
    auto_dispatch = bool(handoff.get("auto_dispatch", True))

    if reusable_ok and requested_capability in SAFE_REUSABLE_READONLY_CAPABILITIES:
        return {
            "schema": SCHEMA_HANDOFF_CLASSIFICATION,
            "classification": "REUSABLE_CAPABILITY_AVAILABLE",
            "reason": f"REUSABLE_CAPABILITY_MATCHED:{reusable_code}",
            "reusable_capability": reusable_code,
            "resolution_job_id": None,
            "lifecycle_state": "CLASSIFIED",
            "next_allowed_action": (
                "SUBMIT_TARGET_RESOLUTION" if auto_dispatch else "ACTIVATE_AUTHORIZED_AUTO_DISPATCH"
            ),
            "requires_human_intervention": False,
            "dispatch_eligible": True,
            "has_executor": auto_dispatch,
            "executor_status": "DISPATCH_READY" if auto_dispatch else "DISPATCH_DISABLED_NO_EXECUTOR",
            "compatible_capabilities": compat_caps,
            "exception_code": None,
            "exception_reason": None,
            "production_touched": False,
        }

    # 4. Autonomous recovery eligibility (strictly Worker infrastructure domains only)
    recovery_ok, recovery_reason = _is_autonomous_recovery_eligible(
        target_domain=target_domain,
        source_job_id=source_job_id,
        incident_id=incident_id,
        requested_capability=requested_capability,
        state_root=qroot,
    )
    if recovery_ok:
        return {
            "schema": SCHEMA_HANDOFF_CLASSIFICATION,
            "classification": "AUTONOMOUS_RECOVERY_ELIGIBLE",
            "reason": recovery_reason,
            "resolution_job_id": None,
            "lifecycle_state": "CLASSIFIED",
            "next_allowed_action": (
                "RECOVER_EXISTING_CAPABILITY" if auto_dispatch else "ACTIVATE_AUTHORIZED_AUTO_DISPATCH"
            ),
            "requires_human_intervention": False,
            "dispatch_eligible": True,
            "has_executor": auto_dispatch,
            "executor_status": "DISPATCH_READY" if auto_dispatch else "DISPATCH_DISABLED_NO_EXECUTOR",
            "compatible_capabilities": compat_caps,
            "exception_code": None,
            "exception_reason": None,
            "production_touched": False,
        }

    if reusable_ok:
        return {
            "schema": SCHEMA_HANDOFF_CLASSIFICATION,
            "classification": "REUSABLE_CAPABILITY_AVAILABLE",
            "reason": f"REUSABLE_CAPABILITY_MATCHED:{reusable_code}",
            "reusable_capability": reusable_code,
            "resolution_job_id": None,
            "lifecycle_state": "CLASSIFIED",
            "next_allowed_action": (
                "SUBMIT_TARGET_RESOLUTION" if auto_dispatch else "ACTIVATE_AUTHORIZED_AUTO_DISPATCH"
            ),
            "requires_human_intervention": False,
            "dispatch_eligible": True,
            "has_executor": auto_dispatch,
            "executor_status": "DISPATCH_READY" if auto_dispatch else "DISPATCH_DISABLED_NO_EXECUTOR",
            "compatible_capabilities": compat_caps,
            "exception_code": None,
            "exception_reason": None,
            "production_touched": False,
        }

    # 4b. Explicit requested capability is incompatible with Capability Registry (or no compatible capability exists)
    if requested_capability and not cap_resolution.get("compatible"):
        exc_code = _clean(cap_resolution.get("exception_code")) or "NO_COMPATIBLE_CAPABILITY_AVAILABLE"
        exc_reason = _clean(cap_resolution.get("reason")) or f"NO_COMPATIBLE_CAPABILITY:{requested_capability}"
        return {
            "schema": SCHEMA_HANDOFF_CLASSIFICATION,
            "classification": "NO_COMPATIBLE_CAPABILITY",
            "reason": exc_reason,
            "resolution_job_id": None,
            "lifecycle_state": "ESCALATED_HUMAN_REQUIRED",
            "next_allowed_action": "ASSIGN_COMPATIBLE_CAPABILITY",
            "requires_human_intervention": True,
            "human_intervention_reason": (
                f"Excepcion concreta de capacidad para {target_domain} ({exc_code}): {exc_reason}."
            ),
            "dispatch_eligible": False,
            "has_executor": False,
            "executor_status": "NO_COMPATIBLE_CAPABILITY",
            "compatible_capabilities": compat_caps,
            "exception_code": exc_code,
            "exception_reason": exc_reason,
            "production_touched": False,
        }

    # 5. Mutation / privileged request requires explicit independent target_domain authorization & policy
    if handoff_mode == "MUTATION" or requested_capability in {"DEVELOPMENT_MUTATION_BOUNDED", "COA_FISCAL_STATUS_SEED_DEVELOPMENT"}:
        target_auth = lifecycle_rec.resolve_active_domain_authorization(
            target_domain,
            state_root=qroot,
            required_class="DEVELOPMENT_MUTATION",
            now_utc=now_utc,
        )
        gate_spec = {
            "gate_id": f"HANDOFF-{hid[:32] or target_domain}",
            "job_id": f"HO-{target_domain}",
            "mutation_class": "CODE_MUTATION",
            "authorization_class": "DEVELOPMENT_MUTATION",
            "require_traceable_authorization": True,
            "production_allowed": False,
            "required_scope": {"domain": [target_domain]},
        }
        policy_decision = policy_ctrl.evaluate_autonomous_policy(
            gate_spec,
            authorization_classes=(target_auth.get("authorization_classes") or ()) if isinstance(target_auth, Mapping) else (),
            authorization_context=target_auth,
            now_utc=now_utc,
        )
        if not policy_decision.get("allowed"):
            return {
                "schema": SCHEMA_HANDOFF_CLASSIFICATION,
                "classification": "REQUIRES_ADDITIONAL_AUTHORIZATION",
                "reason": f"TARGET_DOMAIN_AUTHORIZATION_REQUIRED:{policy_decision.get('reason')}",
                "policy_decision": policy_decision,
                "resolution_job_id": None,
                "lifecycle_state": "WAITING_AUTHORIZATION",
                "next_allowed_action": "HUMAN_APPROVAL_REQUIRED",
                "requires_human_intervention": True,
                "human_intervention_reason": (
                    f"El dominio receptor {target_domain} requiere autorizacion explicita vigente "
                    f"({policy_decision.get('reason')}); la solicitud de {source_domain} no concede permisos."
                ),
                "dispatch_eligible": False,
                "has_executor": False,
                "executor_status": "AUTHORIZATION_REQUIRED",
                "compatible_capabilities": compat_caps,
                "exception_code": "TARGET_DOMAIN_AUTHORIZATION_REQUIRED",
                "exception_reason": str(policy_decision.get("reason") or "AUTHORIZATION_REQUIRED"),
                "production_touched": False,
            }
        return {
            "schema": SCHEMA_HANDOFF_CLASSIFICATION,
            "classification": "TARGET_BOUNDED_CONTEXT_REQUIRED",
            "reason": "TARGET_BOUNDED_CONTEXT_OWNED_MUTATION",
            "policy_decision": policy_decision,
            "resolution_job_id": None,
            "lifecycle_state": "QUEUED_IN_TARGET_DOMAIN",
            "next_allowed_action": "ASSIGN_TARGET_DOMAIN_EXECUTOR",
            "requires_human_intervention": False,
            "dispatch_eligible": False,
            "has_executor": False,
            "executor_status": "TARGET_OWNER_EXECUTION_REQUIRED",
            "compatible_capabilities": compat_caps,
            "exception_code": None,
            "exception_reason": None,
            "production_touched": False,
        }

    # 6. No compatible capability exists in Capability Registry at all -> concrete exception (never indefinite WAIT)
    if not cap_resolution.get("has_compatible_capabilities"):
        exc_code = _clean(cap_resolution.get("exception_code")) or "NO_COMPATIBLE_CAPABILITY_AVAILABLE"
        exc_reason = _clean(cap_resolution.get("reason")) or f"NO_COMPATIBLE_CAPABILITY_FOR_DOMAIN:{target_domain}"
        return {
            "schema": SCHEMA_HANDOFF_CLASSIFICATION,
            "classification": "NO_COMPATIBLE_CAPABILITY",
            "reason": exc_reason,
            "resolution_job_id": None,
            "lifecycle_state": "ESCALATED_HUMAN_REQUIRED",
            "next_allowed_action": "REGISTER_OR_ASSIGN_COMPATIBLE_CAPABILITY",
            "requires_human_intervention": True,
            "human_intervention_reason": (
                f"No existe ninguna capacidad compatible en Capability Registry para {target_domain} ({exc_code})."
            ),
            "dispatch_eligible": False,
            "has_executor": False,
            "executor_status": "NO_COMPATIBLE_CAPABILITY",
            "compatible_capabilities": [],
            "exception_code": exc_code,
            "exception_reason": exc_reason,
            "production_touched": False,
        }

    # 7. Functional/domain work owned by another bounded context without assigned capability yet (never WAIT_FOR_IN_FLIGHT_JOB!)
    return {
        "schema": SCHEMA_HANDOFF_CLASSIFICATION,
        "classification": "TARGET_BOUNDED_CONTEXT_REQUIRED",
        "reason": f"BOUNDED_CONTEXT_OWNER_REQUIRED:{target_domain}",
        "resolution_job_id": None,
        "lifecycle_state": "QUEUED_IN_TARGET_DOMAIN",
        "next_allowed_action": "ASSIGN_COMPATIBLE_CAPABILITY",
        "requires_human_intervention": False,
        "dispatch_eligible": False,
        "has_executor": False,
        "executor_status": "UNASSIGNED_NO_EXECUTOR",
        "compatible_capabilities": compat_caps,
        "exception_code": None,
        "exception_reason": None,
        "production_touched": False,
    }


def validate_handoff_constraints(
    request: Mapping[str, Any],
    *,
    current_user: Mapping[str, Any] | None = None,
    requester: Mapping[str, Any] | None = None,
    state_root: Path | None = None,
    now_utc: datetime | None = None,
    now_epoch: float | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Validate cross-domain handoff request fail-closed (used by preflight & registration)."""
    qroot = state_root or _default_state_root()
    _assert_no_secrets(request, "request")
    _assert_no_untrusted_prompt(request, "request")

    source_domain = validate_domain_token(request.get("bounded_context"), field_name="source_domain")
    handoff_mode = _clean(request.get("mode") or "READ_ONLY").upper()
    if handoff_mode not in {"READ_ONLY", "MUTATION"}:
        raise HandoffError("HANDOFF_MODE_INVALID")

    source_objective = _clean(request.get("objective"))
    if not source_objective or len(source_objective) < 5 or len(source_objective) > MAX_OBJECTIVE_CHARS:
        raise HandoffError("HANDOFF_OBJECTIVE_INVALID")

    constraints = request.get("constraints")
    if not isinstance(constraints, Mapping):
        raise HandoffError("SEMANTIC_CONSTRAINTS_INVALID")

    allowed_keys = {
        "target_domain",
        "source_job_id",
        "incident_id",
        "dependency_id",
        "authorization_ref",
        "acceptance_criteria",
        "requested_capability",
        "requested_constraints",
        "delegation_chain",
        "priority_class",
        "auto_dispatch",
        "resolution_job_id",
        "successor_spec",
    }
    extra = sorted(set(constraints.keys()) - allowed_keys)
    if extra:
        raise HandoffError(f"SEMANTIC_CONSTRAINTS_UNSUPPORTED:{','.join(extra)}")

    target_domain = validate_domain_token(constraints.get("target_domain"), field_name="target_domain")
    request_key = _clean(request.get("request_key"))
    if not request_key or not _TOKEN_ID_RE.fullmatch(request_key):
        raise HandoffError("HANDOFF_REQUEST_KEY_REQUIRED")

    source_job_id = _validate_optional_token(constraints.get("source_job_id"), field_name="source_job_id", job_id_style=True)
    incident_id = _validate_optional_token(constraints.get("incident_id"), field_name="incident_id", job_id_style=True)
    resolution_job_id = _validate_optional_token(constraints.get("resolution_job_id"), field_name="resolution_job_id", job_id_style=True)
    authorization_ref = _validate_optional_token(constraints.get("authorization_ref"), field_name="authorization_ref", job_id_style=False)
    acceptance_criteria = _normalize_acceptance_criteria(constraints.get("acceptance_criteria"))

    raw_req_cap = constraints.get("requested_capability")
    requested_capability = _clean(raw_req_cap).upper() or None
    if requested_capability and not _DOMAIN_RE.fullmatch(requested_capability):
        raise HandoffError("HANDOFF_REQUESTED_CAPABILITY_INVALID")
    if requested_capability == "CROSS_DOMAIN_HANDOFF_REGISTER":
        raise HandoffSecurityError("HANDOFF_RECURSIVE_CAPABILITY_FORBIDDEN")

    raw_req_constraints = constraints.get("requested_constraints")
    if raw_req_constraints is None:
        requested_constraints: dict[str, Any] = {}
    elif isinstance(raw_req_constraints, Mapping):
        requested_constraints = dict(raw_req_constraints)
    else:
        raise HandoffError("HANDOFF_REQUESTED_CONSTRAINTS_INVALID")

    priority_class = _clean(constraints.get("priority_class") or "NORMAL").upper()
    if priority_class not in scheduling_mod.PRIORITY_ORDER:
        raise HandoffError("HANDOFF_PRIORITY_CLASS_INVALID")

    raw_chain = constraints.get("delegation_chain")
    if raw_chain is None:
        delegation_chain_in: list[str] = []
    elif isinstance(raw_chain, list):
        delegation_chain_in = [str(x) for x in raw_chain]
    else:
        raise HandoffError("HANDOFF_DELEGATION_CHAIN_INVALID")

    successor_spec = _validate_successor_spec(
        constraints.get("successor_spec"),
        source_domain=source_domain,
    )

    requester_email = _verify_caller_rbac_and_scope(
        current_user=current_user,
        requester=requester,
        source_domain=source_domain,
        target_domain=target_domain,
        handoff_mode=handoff_mode,
    )

    handoff_id = compute_handoff_id(
        source_domain=source_domain,
        target_domain=target_domain,
        request_key=request_key,
    )
    explicit_dep_id = _validate_optional_token(constraints.get("dependency_id"), field_name="dependency_id", job_id_style=False)
    existing = load_handoff(handoff_id, state_root=qroot)
    dependency_id = explicit_dep_id or (
        _clean(existing.get("dependency_id")) if isinstance(existing, Mapping) and _clean(existing.get("dependency_id")) else f"DEP-{handoff_id}"
    )

    fingerprint = _handoff_fingerprint(
        source_domain=source_domain,
        target_domain=target_domain,
        source_objective=source_objective,
        source_job_id=source_job_id,
        incident_id=incident_id,
        dependency_id=dependency_id,
        requested_capability=requested_capability,
        requested_constraints=requested_constraints,
        acceptance_criteria=acceptance_criteria,
        handoff_mode=handoff_mode,
    )
    core_fp = _handoff_core_fingerprint(
        source_domain=source_domain,
        target_domain=target_domain,
        source_objective=source_objective,
        source_job_id=source_job_id,
        incident_id=incident_id,
        dependency_id=dependency_id,
        acceptance_criteria=acceptance_criteria,
        handoff_mode=handoff_mode,
    )
    auto_dispatch_supplied = "auto_dispatch" in constraints
    auto_dispatch = bool(constraints.get("auto_dispatch", True))

    if existing is not None:
        existing_core_fp = _clean(existing.get("core_fingerprint")) or _handoff_core_fingerprint(
            source_domain=_clean(existing.get("source_domain")).upper(),
            target_domain=_clean(existing.get("target_domain")).upper(),
            source_objective=_clean(existing.get("source_objective")),
            source_job_id=_clean(existing.get("source_job_id")) or None,
            incident_id=_clean(existing.get("incident_id")) or None,
            dependency_id=_clean(existing.get("dependency_id")),
            acceptance_criteria=list(existing.get("acceptance_criteria") or []),
            handoff_mode=_clean(existing.get("handoff_mode") or "READ_ONLY").upper(),
        )
        existing_state = _clean(existing.get("lifecycle_state")).upper()
        existing_cap = _clean(existing.get("requested_capability")).upper() or None
        existing_constraints = (
            dict(existing.get("requested_constraints") or {})
            if isinstance(existing.get("requested_constraints"), Mapping)
            else {}
        )
        existing_auto = bool(existing.get("auto_dispatch", False))
        existing_res_jid = _clean(existing.get("resolution_job_id")) or None

        exact_payload_match = _clean(existing.get("payload_fingerprint")) == fingerprint
        semantic_reassignable = _is_semantic_blocker_reassignable(existing)
        wants_cap_reassignment = (
            semantic_reassignable
            and requested_capability is not None
            and (requested_capability != existing_cap or requested_constraints != existing_constraints)
        )
        if wants_cap_reassignment and requested_capability == "READ_ONLY_CANARY":
            domain_criteria = [c for c in acceptance_criteria if c not in _GENERIC_ACCEPTANCE_CRITERIA]
            if domain_criteria:
                raise HandoffError("HANDOFF_CANARY_INSUFFICIENT_FOR_OBJECTIVE")
        wants_cap_assignment = (
            (existing_cap is None and requested_capability is not None)
            or wants_cap_reassignment
        )
        wants_auto_dispatch_activation = (
            auto_dispatch_supplied
            and existing_auto is False
            and auto_dispatch is True
        )
        wants_auth_upgrade = (
            authorization_ref is not None
            and authorization_ref != (_clean(existing.get("authorization_ref")) or None)
        )
        wants_resolution_link = (
            resolution_job_id is not None
            and resolution_job_id != existing_res_jid
        )

        if successor_spec is not None:
            if not exact_payload_match or existing_core_fp != core_fp or wants_auto_dispatch_activation or wants_auth_upgrade or wants_resolution_link:
                raise HandoffConflictError("HANDOFF_SUCCESSOR_PAYLOAD_CONFLICT")
            if existing.get("successor_spec") is not None and existing.get("successor_spec") != successor_spec:
                raise HandoffConflictError("HANDOFF_SUCCESSOR_ALREADY_DEFINED")
            if existing.get("successor_spec") is None:
                _validate_existing_successor_registration(existing, successor_spec, current_user=current_user)
                return {
                    "duplicate": False, "pending_update": False, "successor_update": True,
                    "existing_handoff": existing, "successor_spec": successor_spec,
                    "handoff_id": handoff_id, "dependency_id": dependency_id,
                    "source_domain": source_domain, "target_domain": target_domain,
                    "request_key": request_key, "payload_fingerprint": fingerprint,
                    "production_touched": False,
                }

        # Pure idempotent replay (exact same payload and no pending enrichment requested)
        if exact_payload_match and not (
            wants_auto_dispatch_activation or wants_auth_upgrade or wants_resolution_link
        ):
            return {
                "duplicate": True,
                "pending_update": False,
                "existing_handoff": existing,
                "handoff_id": handoff_id,
                "dependency_id": dependency_id,
                "source_domain": source_domain,
                "target_domain": target_domain,
                "request_key": request_key,
                "payload_fingerprint": fingerprint,
                "production_touched": False,
            }

        # Controlled enrichment or semantic-blocker recovery of an existing handoff without duplicating it:
        # preserves identity, history, RBAC, acceptance criteria, and prior evidence.
        can_update_pending = (
            existing_core_fp == core_fp
            and (existing_state in UPDATABLE_HANDOFF_STATES or semantic_reassignable)
            and existing.get("dependency_satisfied") is not True
            and (existing_res_jid is None or wants_resolution_link or semantic_reassignable)
            and (
                wants_cap_assignment
                or wants_auto_dispatch_activation
                or wants_auth_upgrade
                or wants_resolution_link
            )
            and (
                existing_cap is None
                or wants_cap_reassignment
                or (
                    requested_capability == existing_cap
                    and requested_constraints == existing_constraints
                )
                or (semantic_reassignable and wants_resolution_link and requested_capability is None)
            )
        )
        if not can_update_pending:
            raise HandoffConflictError("IDEMPOTENCY_CONFLICT")

        # Validate capability compatibility via Capability Registry if assigning a capability
        eff_cap = requested_capability if wants_cap_assignment else existing_cap
        eff_constraints = requested_constraints if wants_cap_assignment else existing_constraints
        if wants_cap_assignment:
            cap_check = resolve_compatible_capabilities(
                target_domain=target_domain,
                handoff_mode=handoff_mode,
                requested_capability=eff_cap,
                requested_constraints=eff_constraints,
                incident_id=incident_id,
            )
            if not cap_check.get("compatible"):
                raise HandoffError(
                    f"HANDOFF_CAPABILITY_INCOMPATIBLE:{cap_check.get('exception_code') or 'INCOMPATIBLE'}"
                )

        # Verify authorization_ref if supplied or preserved
        eff_auth_ref = authorization_ref or (_clean(existing.get("authorization_ref")) or None)
        auth_eval = _verify_authorization_ref(
            eff_auth_ref,
            source_domain=source_domain,
            target_domain=target_domain,
            handoff_mode=handoff_mode,
            state_root=qroot,
            now_utc=now_utc,
        )

        # Activating auto_dispatch requires verifiable dispatch identity & RBAC (fail-closed)
        eff_auto = True if wants_auto_dispatch_activation else existing_auto
        if wants_auto_dispatch_activation:
            _resolve_canonical_dispatch_identity(
                {
                    **existing,
                    "requested_capability": eff_cap,
                    "requested_constraints": eff_constraints,
                    "auto_dispatch": eff_auto,
                    "authorization_ref": eff_auth_ref,
                },
                current_user=current_user,
            )

        updated_candidate = dict(existing)
        updated_candidate["requested_capability"] = eff_cap
        updated_candidate["requested_constraints"] = dict(eff_constraints)
        updated_candidate["auto_dispatch"] = eff_auto
        updated_candidate["authorization_ref"] = eff_auth_ref
        updated_candidate["authorization_verification"] = auth_eval
        if wants_cap_reassignment and not wants_resolution_link:
            # Clear stale insufficient canary resolution before re-classifying with real capability
            updated_candidate["resolution_job_id"] = None
        if wants_resolution_link:
            updated_candidate["resolution_job_id"] = resolution_job_id
        updated_candidate["core_fingerprint"] = core_fp
        updated_candidate.setdefault("initial_payload_fingerprint", existing.get("payload_fingerprint"))
        updated_candidate["payload_fingerprint"] = _handoff_fingerprint(
            source_domain=source_domain,
            target_domain=target_domain,
            source_objective=source_objective,
            source_job_id=source_job_id,
            incident_id=incident_id,
            dependency_id=dependency_id,
            requested_capability=eff_cap,
            requested_constraints=eff_constraints,
            acceptance_criteria=acceptance_criteria,
            handoff_mode=handoff_mode,
        )
        all_handoffs = list_handoffs(state_root=qroot)
        classification = classify_handoff_request(
            updated_candidate,
            state_root=qroot,
            existing_handoffs=all_handoffs,
            now_utc=now_utc,
        )
        return {
            "duplicate": False,
            "pending_update": True,
            "existing_handoff": existing,
            "candidate": updated_candidate,
            "classification": classification,
            "update_changes": {
                "capability_assigned": eff_cap if wants_cap_assignment else None,
                "allow_reassign_capability": bool(wants_cap_reassignment),
                "auto_dispatch_activated": wants_auto_dispatch_activation,
                "authorization_ref_updated": wants_auth_upgrade,
                "resolution_job_id_linked": resolution_job_id if wants_resolution_link else None,
                "actor_email": requester_email,
            },
            "handoff_id": handoff_id,
            "dependency_id": dependency_id,
            "source_domain": source_domain,
            "target_domain": target_domain,
            "request_key": request_key,
            "payload_fingerprint": updated_candidate["payload_fingerprint"],
            "production_touched": False,
        }

    all_handoffs = list_handoffs(state_root=qroot)
    full_chain = _check_circular_and_recursive_delegation(
        source_domain=source_domain,
        target_domain=target_domain,
        delegation_chain=delegation_chain_in,
        existing_handoffs=all_handoffs,
        ignore_handoff_id=handoff_id,
    )

    auth_eval = _verify_authorization_ref(
        authorization_ref,
        source_domain=source_domain,
        target_domain=target_domain,
        handoff_mode=handoff_mode,
        state_root=qroot,
        now_utc=now_utc,
    )

    rate_eval = _check_rate_limit(
        source_domain=source_domain,
        target_domain=target_domain,
        state_root=qroot,
        now_epoch=now_epoch,
        dry_run=dry_run,
    )

    risk_level = "HIGH" if handoff_mode == "MUTATION" else "LOW"
    candidate_record: dict[str, Any] = {
        "schema": SCHEMA_HANDOFF,
        "handoff_id": handoff_id,
        "source_domain": source_domain,
        "target_domain": target_domain,
        "owner_domain": target_domain,
        "source_objective": source_objective,
        "source_job_id": source_job_id,
        "incident_id": incident_id,
        "dependency_id": dependency_id,
        "request_key": request_key,
        "authorization_ref": authorization_ref,
        "acceptance_criteria": acceptance_criteria,
        "resolution_job_id": resolution_job_id,
        "certification": "NOT_CERTIFIED",
        "lifecycle_state": "REGISTERED",
        "next_allowed_action": "CONTINUE_AUTONOMOUS",
        "handoff_mode": handoff_mode,
        "requested_capability": requested_capability,
        "requested_constraints": requested_constraints,
        "priority_class": priority_class,
        "auto_dispatch": auto_dispatch,
        "delegation_chain": full_chain,
        "delegation_depth": len(full_chain) - 1,
        "requester_email": requester_email,
        "risk_level": risk_level,
        "grants_target_permissions": False,
        "authorization_verification": auth_eval,
        "core_fingerprint": core_fp,
        "initial_payload_fingerprint": fingerprint,
        "payload_fingerprint": fingerprint,
        "dependency_satisfied": False,
        "evidence_link": None,
        "source_resumed": False,
        "resumed_job_id": None,
        "successor_spec": successor_spec,
        "successor_status": "PENDING_RESOLUTION" if successor_spec else "NO_SUCCESSOR_DEFINED",
        "successor_certification": None,
        "successor_evidence_link": None,
        "resolution_stage": None,
        "semantic_validation": None,
        "requires_human_intervention": False,
        "human_intervention_reason": None,
        "has_executor": False,
        "executor_status": "UNASSIGNED_NO_EXECUTOR",
        "compatible_capabilities": [],
        "exception_code": None,
        "exception_reason": None,
        "dispatch_attempts": 0,
        "production_allowed": False,
        "production_touched": False,
    }

    classification = classify_handoff_request(
        candidate_record,
        state_root=qroot,
        existing_handoffs=all_handoffs,
        now_utc=now_utc,
    )
    return {
        "duplicate": False,
        "candidate": candidate_record,
        "classification": classification,
        "rate_limit": rate_eval,
        "handoff_id": handoff_id,
        "dependency_id": dependency_id,
        "source_domain": source_domain,
        "target_domain": target_domain,
        "request_key": request_key,
        "payload_fingerprint": fingerprint,
        "production_touched": False,
    }


def _build_dispatch_job_for_handoff(
    handoff: Mapping[str, Any],
    *,
    current_user: Mapping[str, Any] | None = None,
    identity_resolver: Any = None,
) -> dict[str, Any] | None:
    """Build one canonical edarsahub.worker-job.v2 envelope using verified canonical identity & RBAC (fail-closed)."""
    cap_code = _clean(handoff.get("requested_capability")).upper()
    if not cap_code or cap_code not in SAFE_REUSABLE_READONLY_CAPABILITIES:
        return None

    target_domain = validate_domain_token(handoff.get("target_domain"), field_name="target_domain")
    handoff_mode = _clean(handoff.get("handoff_mode") or "READ_ONLY").upper()
    requested_constraints = (
        dict(handoff.get("requested_constraints") or {})
        if isinstance(handoff.get("requested_constraints"), Mapping)
        else {}
    )

    cap_check = resolve_compatible_capabilities(
        target_domain=target_domain,
        handoff_mode=handoff_mode,
        requested_capability=cap_code,
        requested_constraints=requested_constraints,
        incident_id=_clean(handoff.get("incident_id")) or None,
    )
    if not (cap_check.get("compatible") and cap_check.get("executable")):
        return None

    # Fail-closed canonical identity resolution via verified caller or SQL RBAC
    actor = _resolve_canonical_dispatch_identity(
        handoff,
        current_user=current_user,
        identity_resolver=identity_resolver,
    )

    from modules.worker_ingress import semantic_capabilities as sem_caps
    from modules.worker_ingress import service as ingress_service

    cap = sem_caps.resolve_capability(cap_code)
    if cap.builder is None:
        return None
    mode = _clean(cap_check.get("selected_mode")) or ("READ_ONLY_SQL" if "READ_ONLY_SQL" in cap.modes else "READ_ONLY")

    req = {
        "objective": (
            f"[HANDOFF {handoff['handoff_id']} {handoff['source_domain']}->{target_domain}] "
            f"{handoff['source_objective']}"
        )[:3900],
        "bounded_context": target_domain,
        "mode": mode,
        "capability": cap_code,
        "request_key": f"handoff-{handoff['handoff_id']}",
        "constraints": requested_constraints,
    }
    job = ingress_service.build_semantic_job(req, current_user=actor)
    # Apply canonical priority_class from worker_scheduling
    priority = _clean(handoff.get("priority_class") or "NORMAL").upper()
    if priority in scheduling_mod.PRIORITY_ORDER and isinstance(job.get("scheduling"), dict):
        job["scheduling"]["priority_class"] = priority
    return job


def dispatch_handoff_resolution(
    handoff: dict[str, Any],
    *,
    state_root: Path | None = None,
    repo_root: Path | None = None,
    current_user: Mapping[str, Any] | None = None,
    identity_resolver: Any = None,
    submit_fn: Any = None,
    now_utc: datetime | None = None,
    now_epoch: float | None = None,
) -> dict[str, Any]:
    """Publish resolution work exclusively via gate_chain_publisher.submit() with RBAC & auth revalidation."""
    qroot = state_root or _default_state_root()
    hid = _clean(handoff.get("handoff_id"))
    now_ts = float(now_epoch if now_epoch is not None else time.time())
    cb_dir = qroot / "maintenance" / "circuit_breakers"
    cb_key = f"handoff_dispatch:{hid[:64]}"

    # Fail-closed identity verification & authorization revalidation BEFORE any dispatch attempt
    try:
        verified_actor = _resolve_canonical_dispatch_identity(
            handoff,
            current_user=current_user,
            identity_resolver=identity_resolver,
        )
        revalidated_auth = _revalidate_dispatch_authorization(
            handoff,
            actor=verified_actor,
            state_root=qroot,
            now_utc=now_utc,
        )
    except HandoffSecurityError as exc:
        err_code = str(exc)
        is_auth_err = "AUTHORIZATION" in err_code
        handoff["lifecycle_state"] = "WAITING_AUTHORIZATION" if is_auth_err else "BLOCKED_POLICY"
        handoff["next_allowed_action"] = "HUMAN_APPROVAL_REQUIRED"
        handoff["requires_human_intervention"] = True
        handoff["human_intervention_reason"] = f"Revalidacion fail-closed al despachar: {err_code}"
        handoff["has_executor"] = False
        handoff["executor_status"] = "AUTHORIZATION_REQUIRED" if is_auth_err else "BLOCKED"
        handoff["exception_code"] = err_code
        handoff["exception_reason"] = err_code
        handoff["exception_recorded_at_utc"] = utc_now()
        handoff["last_dispatch_error"] = err_code
        handoff["updated_at_utc"] = utc_now()
        _append_history(
            handoff,
            "DISPATCH_BLOCKED_SECURITY",
            details={"error_code": err_code},
        )
        save_handoff(handoff, state_root=qroot)
        return {
            "dispatched": False,
            "status": "DISPATCH_BLOCKED_SECURITY",
            "error_code": err_code,
            "handoff": handoff,
            "production_touched": False,
        }

    handoff["authorization_verification"] = revalidated_auth
    handoff["last_authorization_revalidated_at_utc"] = utc_now()

    cb_prior = _read_json_safe(auto_loop._circuit_path(cb_key, state_dir=cb_dir)) or {}
    consec_fail = int(cb_prior.get("consecutive_failures") or 0)
    backoff_s = lifecycle_rec.compute_exponential_backoff(consec_fail)
    circuit = auto_loop.evaluate_circuit_breaker(
        cb_key,
        max_failures=3,
        cooldown_seconds=max(60, backoff_s),
        now_epoch=now_ts,
        state_dir=cb_dir,
    )
    if not circuit.get("allow_attempt"):
        handoff["lifecycle_state"] = "ESCALATED_HUMAN_REQUIRED"
        handoff["next_allowed_action"] = "HUMAN_APPROVAL_REQUIRED"
        handoff["requires_human_intervention"] = True
        handoff["human_intervention_reason"] = f"CIRCUIT_BREAKER_OPEN:{circuit.get('reason')}"
        handoff["has_executor"] = False
        handoff["executor_status"] = "BLOCKED"
        handoff["exception_code"] = "CIRCUIT_BREAKER_OPEN"
        handoff["exception_reason"] = str(circuit.get("reason") or "CIRCUIT_BREAKER_OPEN")
        handoff["exception_recorded_at_utc"] = utc_now()
        handoff["updated_at_utc"] = utc_now()
        _append_history(
            handoff,
            "DISPATCH_CIRCUIT_OPEN",
            actor_email=verified_actor.get("email"),
            details={"reason": circuit.get("reason")},
        )
        save_handoff(handoff, state_root=qroot)
        return {"dispatched": False, "status": "CIRCUIT_OPEN", "handoff": handoff, "production_touched": False}

    classification = _clean(handoff.get("classification")).upper()
    publisher = submit_fn or gcp.submit

    # Path A: Autonomous concurrency/draft recovery strictly inside Worker infra domains
    if classification == "AUTONOMOUS_RECOVERY_ELIGIBLE" and _clean(handoff.get("target_domain")).upper() in WORKER_INFRA_DOMAINS:
        source_job_id = _clean(handoff.get("source_job_id"))
        if source_job_id:
            res_doc = _read_json_safe(qroot / "results" / f"{source_job_id}.json")
            if isinstance(res_doc, dict) and _clean(res_doc.get("status")).upper() in lifecycle_rec.CONCURRENCY_BLOCKED_STATUSES:
                try:
                    rec = lifecycle_rec.resume_authorized_concurrency_blocked_objective(
                        source_job_id,
                        repo_root=repo_root,
                        state_root=qroot,
                        circuit_state_dir=cb_dir,
                        submit_fn=publisher,
                        now_epoch=now_ts,
                    )
                except Exception as exc:
                    auto_loop.record_circuit_outcome(
                        cb_key,
                        certified_success=False,
                        failure_class=f"HANDOFF_RECOVERY_EXC:{type(exc).__name__}",
                        now_epoch=now_ts,
                        state_dir=cb_dir,
                    )
                    handoff["last_dispatch_error"] = type(exc).__name__
                    handoff["updated_at_utc"] = utc_now()
                    _append_history(handoff, "RECOVERY_DEFERRED", actor_email=verified_actor.get("email"), details={"error": type(exc).__name__})
                    save_handoff(handoff, state_root=qroot)
                    return {"dispatched": False, "status": "RECOVERY_DEFERRED_CONNECTIVITY", "handoff": handoff, "production_touched": False}
                if rec.get("resumed") is True:
                    auto_loop.record_circuit_outcome(cb_key, certified_success=True, now_epoch=now_ts, state_dir=cb_dir)
                    handoff["resolution_job_id"] = rec.get("resume_job_id")
                    handoff["lifecycle_state"] = "IN_PROGRESS"
                    handoff["next_allowed_action"] = "WAIT_FOR_IN_FLIGHT_JOB"
                    handoff["has_executor"] = True
                    handoff["executor_status"] = "IN_FLIGHT_JOB"
                    handoff["exception_code"] = None
                    handoff["exception_reason"] = None
                    handoff["dispatch_attempts"] = int(handoff.get("dispatch_attempts") or 0) + 1
                    handoff["updated_at_utc"] = utc_now()
                    _append_history(
                        handoff,
                        "DISPATCHED_RECOVERY",
                        actor_email=verified_actor.get("email"),
                        details={"job_id": rec.get("resume_job_id")},
                    )
                    save_handoff(handoff, state_root=qroot)
                    return {
                        "dispatched": True,
                        "status": "SUBMITTED",
                        "job_id": rec.get("resume_job_id"),
                        "publication_channel": "gate_chain_publisher.submit",
                        "handoff": handoff,
                        "production_touched": False,
                    }
                handoff["lifecycle_state"] = "WAITING_AUTHORIZATION" if "POLICY" in str(rec.get("action") or "") else "QUEUED_IN_TARGET_DOMAIN"
                handoff["next_allowed_action"] = (
                    "HUMAN_APPROVAL_REQUIRED"
                    if handoff["lifecycle_state"] == "WAITING_AUTHORIZATION"
                    else "ASSIGN_COMPATIBLE_CAPABILITY"
                )
                handoff["requires_human_intervention"] = handoff["lifecycle_state"] == "WAITING_AUTHORIZATION"
                handoff["human_intervention_reason"] = str(rec.get("reason") or "") if handoff["requires_human_intervention"] else None
                handoff["has_executor"] = False
                handoff["executor_status"] = "AUTHORIZATION_REQUIRED" if handoff["requires_human_intervention"] else "UNASSIGNED_NO_EXECUTOR"
                handoff["updated_at_utc"] = utc_now()
                save_handoff(handoff, state_root=qroot)
                return {"dispatched": False, "status": str(rec.get("action") or "DEFERRED"), "handoff": handoff, "production_touched": False}

    # Path B: Reusable certified READ_ONLY / READ_ONLY_SQL capability using verified canonical identity
    canonical_job = _build_dispatch_job_for_handoff(
        handoff,
        current_user=verified_actor,
        identity_resolver=identity_resolver,
    )
    if canonical_job is None:
        handoff["has_executor"] = False
        handoff["executor_status"] = "NO_COMPATIBLE_CAPABILITY"
        handoff["exception_code"] = "NO_DISPATCHABLE_CAPABILITY"
        handoff["exception_reason"] = "NO_DISPATCHABLE_JOB_BUILT"
        handoff["exception_recorded_at_utc"] = utc_now()
        handoff["updated_at_utc"] = utc_now()
        _append_history(
            handoff,
            "DISPATCH_NO_COMPATIBLE_CAPABILITY",
            actor_email=verified_actor.get("email"),
        )
        save_handoff(handoff, state_root=qroot)
        return {"dispatched": False, "status": "NO_DISPATCHABLE_JOB", "handoff": handoff, "production_touched": False}

    try:
        pub_out = publisher(canonical_job, require_convergence=False)
    except TypeError:
        pub_out = publisher(canonical_job)
    except Exception as exc:
        auto_loop.record_circuit_outcome(
            cb_key,
            certified_success=False,
            failure_class=f"HANDOFF_DISPATCH_EXC:{type(exc).__name__}",
            now_epoch=now_ts,
            state_dir=cb_dir,
        )
        handoff["dispatch_attempts"] = int(handoff.get("dispatch_attempts") or 0) + 1
        handoff["last_dispatch_error"] = type(exc).__name__
        handoff["updated_at_utc"] = utc_now()
        _append_history(
            handoff,
            "DISPATCH_ERROR_BACKOFF",
            actor_email=verified_actor.get("email"),
            details={"error": type(exc).__name__},
        )
        save_handoff(handoff, state_root=qroot)
        return {"dispatched": False, "status": "DISPATCH_ERROR_BACKOFF", "handoff": handoff, "production_touched": False}

    pub_status = _clean((pub_out or {}).get("status")).upper()
    pub_job_id = _clean((pub_out or {}).get("job_id")) or canonical_job["job_id"]
    if pub_status in {"SUBMITTED", "ALREADY_SUBMITTED", "PUBLISHED", "EXISTS", "ALREADY_PROCESSING", "ALREADY_COMPLETED"}:
        auto_loop.record_circuit_outcome(cb_key, certified_success=True, now_epoch=now_ts, state_dir=cb_dir)
        handoff["resolution_job_id"] = pub_job_id
        handoff["dispatch_attempts"] = int(handoff.get("dispatch_attempts") or 0) + 1
        handoff["publication_channel"] = "gate_chain_publisher.submit"
        handoff["dispatch_identity_email"] = _clean(verified_actor.get("email")).lower()
        handoff["dispatch_auth_source"] = _clean(verified_actor.get("auth_source")) or "VERIFIED_CALLER"
        handoff["lifecycle_state"] = "IN_PROGRESS"
        handoff["next_allowed_action"] = "WAIT_FOR_IN_FLIGHT_JOB"
        handoff["requires_human_intervention"] = False
        handoff["human_intervention_reason"] = None
        handoff["has_executor"] = True
        handoff["executor_status"] = "IN_FLIGHT_JOB"
        handoff["exception_code"] = None
        handoff["exception_reason"] = None
        handoff["updated_at_utc"] = utc_now()
        _append_history(
            handoff,
            "DISPATCHED",
            actor_email=verified_actor.get("email"),
            details={
                "job_id": pub_job_id,
                "capability": _clean(handoff.get("requested_capability")).upper(),
                "publication_status": pub_status,
            },
        )
        save_handoff(handoff, state_root=qroot)
        return {
            "dispatched": True,
            "status": pub_status,
            "job_id": pub_job_id,
            "publication_channel": "gate_chain_publisher.submit",
            "handoff": handoff,
            "production_touched": False,
        }

    auto_loop.record_circuit_outcome(
        cb_key,
        certified_success=False,
        failure_class=f"HANDOFF_DISPATCH_STATUS:{pub_status or 'UNKNOWN'}",
        now_epoch=now_ts,
        state_dir=cb_dir,
    )
    handoff["dispatch_attempts"] = int(handoff.get("dispatch_attempts") or 0) + 1
    handoff["last_dispatch_error"] = pub_status or "UNKNOWN"
    handoff["updated_at_utc"] = utc_now()
    _append_history(
        handoff,
        "DISPATCH_REJECTED",
        actor_email=verified_actor.get("email"),
        details={"status": pub_status or "UNKNOWN"},
    )
    save_handoff(handoff, state_root=qroot)
    return {"dispatched": False, "status": pub_status or "DISPATCH_REJECTED", "handoff": handoff, "production_touched": False}


def _validate_successor_spec(
    raw_spec: Any,
    *,
    source_domain: str,
) -> dict[str, Any] | None:
    """Validate an optional pre-defined authorized successor spec (no raw actions/checks, no cross-domain drift)."""
    if raw_spec is None:
        return None
    if not isinstance(raw_spec, Mapping):
        raise HandoffError("HANDOFF_SUCCESSOR_SPEC_INVALID")
    _assert_no_secrets(raw_spec, "successor_spec")
    _assert_no_untrusted_prompt(raw_spec, "successor_spec")
    if raw_spec.get("production_allowed") is True:
        raise HandoffSecurityError("HANDOFF_PRODUCTION_FORBIDDEN")

    allowed_fields = {
        "objective",
        "bounded_context",
        "mode",
        "capability",
        "request_key",
        "constraints",
        "gate_id",
        "authorization_ref",
        "production_allowed",
    }
    extra = sorted(set(raw_spec.keys()) - allowed_fields)
    if extra:
        raise HandoffError(f"HANDOFF_SUCCESSOR_SPEC_UNSUPPORTED:{','.join(extra)}")

    objective = _clean(raw_spec.get("objective"))
    if not objective or len(objective) < 5 or len(objective) > MAX_OBJECTIVE_CHARS:
        raise HandoffError("HANDOFF_SUCCESSOR_OBJECTIVE_INVALID")

    bc = validate_domain_token(raw_spec.get("bounded_context") or source_domain, field_name="successor_bounded_context")
    if bc != source_domain:
        raise HandoffSecurityError("HANDOFF_SUCCESSOR_DOMAIN_MISMATCH")

    mode = _clean(raw_spec.get("mode") or "READ_ONLY").upper()
    if mode not in {"READ_ONLY", "READ_ONLY_SQL", "MUTATION"}:
        raise HandoffError("HANDOFF_SUCCESSOR_MODE_INVALID")

    cap = _clean(raw_spec.get("capability")).upper()
    if not cap or not _DOMAIN_RE.fullmatch(cap):
        raise HandoffError("HANDOFF_SUCCESSOR_CAPABILITY_INVALID")
    if cap == "CROSS_DOMAIN_HANDOFF_REGISTER":
        raise HandoffSecurityError("HANDOFF_RECURSIVE_CAPABILITY_FORBIDDEN")

    req_key = _clean(raw_spec.get("request_key"))
    if not req_key or not _TOKEN_ID_RE.fullmatch(req_key):
        raise HandoffError("HANDOFF_SUCCESSOR_REQUEST_KEY_REQUIRED")

    raw_constraints = raw_spec.get("constraints")
    if raw_constraints is None:
        constraints: dict[str, Any] = {}
    elif isinstance(raw_constraints, Mapping):
        constraints = dict(raw_constraints)
    else:
        raise HandoffError("HANDOFF_SUCCESSOR_CONSTRAINTS_INVALID")
    if set(constraints.keys()) & {"actions", "checks", "production_allowed"}:
        raise HandoffSecurityError("HANDOFF_SUCCESSOR_RAW_FIELDS_FORBIDDEN")

    auth_ref = _validate_optional_token(
        raw_spec.get("authorization_ref") or constraints.get("authorization_ref"),
        field_name="successor_authorization_ref",
        job_id_style=False,
    )
    gate_id = _validate_optional_token(raw_spec.get("gate_id"), field_name="successor_gate_id", job_id_style=True)

    return {
        "objective": objective,
        "bounded_context": bc,
        "mode": mode,
        "capability": cap,
        "request_key": req_key,
        "constraints": constraints,
        "gate_id": gate_id,
        "authorization_ref": auth_ref,
        "production_allowed": False,
    }


def evaluate_handoff_semantic_satisfaction(
    handoff: Mapping[str, Any],
    certified_evidence: Mapping[str, Any],
    *,
    capability_used: str | None = None,
    semantic_assessment: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Section 7: Verify terminal evidence truly satisfies semantic acceptance criteria (never accept canary as functional substitute)."""
    criteria = [str(c).strip() for c in (handoff.get("acceptance_criteria") or ()) if str(c).strip()]
    domain_criteria = [c for c in criteria if c not in _GENERIC_ACCEPTANCE_CRITERIA]
    eff_cap = _clean(capability_used or handoff.get("requested_capability")).upper() or None
    cert = _clean(certified_evidence.get("certification")).upper()
    status = _clean(certified_evidence.get("status")).upper()

    if isinstance(semantic_assessment, Mapping):
        explicit_sat = semantic_assessment.get("satisfied")
        unmet = [str(x).strip() for x in (semantic_assessment.get("unmet_criteria") or ()) if str(x).strip()]
        met = [str(x).strip() for x in (semantic_assessment.get("met_criteria") or ()) if str(x).strip()]
        blockers = [str(x).strip() for x in (semantic_assessment.get("blockers") or ()) if str(x).strip()]
        stage = _clean(semantic_assessment.get("resolution_stage")).upper()
        if stage not in RESOLUTION_STAGES:
            stage = "BLOCKER_IDENTIFIED_EVIDENCE_CERTIFIED" if (explicit_sat is False or unmet or blockers) else "RESULT_CERTIFIED"
        if explicit_sat is False or unmet or blockers:
            return {
                "satisfied": False,
                "resolution_stage": stage,
                "capability_used": eff_cap,
                "met_criteria": met,
                "unmet_criteria": unmet or domain_criteria,
                "blockers": blockers,
                "exception_code": _clean(semantic_assessment.get("blocker_code")) or "HANDOFF_SEMANTIC_CRITERIA_UNMET",
                "summary": _clean(semantic_assessment.get("summary")) or "La evidencia certificada documenta un bloqueo o criterios de aceptacion aun insatisfechos.",
                "details": dict(semantic_assessment.get("details") or {}) if isinstance(semantic_assessment.get("details"), Mapping) else {},
            }
        return {
            "satisfied": True,
            "resolution_stage": stage,
            "capability_used": eff_cap,
            "met_criteria": met or criteria,
            "unmet_criteria": [],
            "blockers": [],
            "exception_code": None,
            "summary": _clean(semantic_assessment.get("summary")) or "Criterios semanticos de aceptacion verificados con evidencia terminal certificada.",
            "details": dict(semantic_assessment.get("details") or {}) if isinstance(semantic_assessment.get("details"), Mapping) else {},
        }

    # Fail-closed guard: READ_ONLY_CANARY NEVER substitutes for domain-specific acceptance criteria
    if eff_cap == "READ_ONLY_CANARY" and domain_criteria:
        return {
            "satisfied": False,
            "resolution_stage": "AUDIT_EXECUTED",
            "capability_used": eff_cap,
            "met_criteria": [c for c in criteria if c in _GENERIC_ACCEPTANCE_CRITERIA],
            "unmet_criteria": domain_criteria,
            "blockers": ["READ_ONLY_CANARY_CANNOT_SATISFY_DOMAIN_OBJECTIVE"],
            "exception_code": "HANDOFF_CANARY_INSUFFICIENT_FOR_OBJECTIVE",
            "summary": "READ_ONLY_CANARY no sustituye una resolucion funcional o tecnica real; la dependencia permanece insatisfecha.",
            "details": {},
        }

    default_stage = "IMPLEMENTATION_INTEGRATED" if status == "INTEGRATED" else ("RESULT_CERTIFIED" if cert in TERMINAL_CERTIFICATIONS else "AUDIT_EXECUTED")
    return {
        "satisfied": True,
        "resolution_stage": default_stage,
        "capability_used": eff_cap,
        "met_criteria": criteria,
        "unmet_criteria": [],
        "blockers": [],
        "exception_code": None,
        "summary": "Evidencia terminal certificada compatible con los criterios de aceptacion.",
        "details": {},
    }


def _validate_existing_successor_registration(
    handoff: Mapping[str, Any], spec: Mapping[str, Any], *, current_user: Mapping[str, Any] | None
) -> None:
    if handoff.get("production_allowed") is not False or handoff.get("production_touched") is not False:
        raise HandoffSecurityError("HANDOFF_PRODUCTION_FORBIDDEN")
    if handoff.get("lifecycle_state") != "RETURNED_TO_SOURCE" or handoff.get("dependency_satisfied") is not True or handoff.get("certification") not in TERMINAL_CERTIFICATIONS:
        raise HandoffConflictError("HANDOFF_SUCCESSOR_REQUIRES_CERTIFIED_RETURN")
    if handoff.get("source_resumed") or handoff.get("resumed_job_id"):
        raise HandoffConflictError("HANDOFF_SUCCESSOR_ALREADY_EXECUTED")
    _resolve_canonical_dispatch_identity(
        {**handoff, "target_domain": handoff["source_domain"],
         "handoff_mode": "MUTATION" if spec["mode"] == "MUTATION" else "READ_ONLY"},
        current_user=current_user,
    )
    compat = resolve_compatible_capabilities(
        target_domain=handoff["source_domain"],
        handoff_mode="MUTATION" if spec["mode"] == "MUTATION" else "READ_ONLY",
        requested_capability=spec["capability"], requested_constraints=spec["constraints"],
    )
    if not compat.get("compatible"):
        raise HandoffError("HANDOFF_SUCCESSOR_CAPABILITY_INCOMPATIBLE")
    if spec["mode"] == "MUTATION" and not spec.get("authorization_ref"):
        raise HandoffSecurityError("HANDOFF_SUCCESSOR_AUTHORIZATION_REQUIRED")


def register_handoff_successor(
    handoff_id: str,
    successor_spec: Mapping[str, Any],
    *,
    current_user: Mapping[str, Any] | None = None,
    requester: Mapping[str, Any] | None = None,
    state_root: Path | None = None,
) -> dict[str, Any]:
    """Attach a strictly validated pre-defined successor spec to an existing handoff without duplicating it."""
    qroot = state_root or _default_state_root()
    handoff = load_handoff(handoff_id, state_root=qroot)
    if handoff is None:
        raise HandoffError("HANDOFF_NOT_FOUND")
    source_domain = validate_domain_token(handoff.get("source_domain"), field_name="source_domain")
    target_domain = validate_domain_token(handoff.get("target_domain"), field_name="target_domain")
    actor_email = _verify_caller_rbac_and_scope(
        current_user=current_user,
        requester=requester,
        source_domain=source_domain,
        target_domain=target_domain,
        handoff_mode=_clean(handoff.get("handoff_mode") or "READ_ONLY").upper(),
    )
    validated_spec = _validate_successor_spec(successor_spec, source_domain=source_domain)
    assert validated_spec is not None
    import fcntl
    lock_path = handoffs_dir(qroot) / f"{handoff_id}.successor.lock"
    with open(lock_path, "a+", encoding="utf-8") as lock_fh:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
        try:
            handoff = load_handoff(handoff_id, state_root=qroot)
            if handoff is None:
                raise HandoffError("HANDOFF_NOT_FOUND")
            existing_spec = handoff.get("successor_spec")
            if existing_spec is not None:
                if existing_spec == validated_spec:
                    return handoff
                raise HandoffConflictError("HANDOFF_SUCCESSOR_ALREADY_DEFINED")
            _validate_existing_successor_registration(handoff, validated_spec, current_user=current_user)
            handoff["successor_spec"] = validated_spec
            if not handoff.get("source_resumed"):
                handoff["successor_status"] = "PENDING_RESOLUTION"
            handoff["updated_at_utc"] = utc_now()
            _append_history(
                handoff, "SUCCESSOR_REGISTERED", actor_email=actor_email,
                details={"capability": validated_spec["capability"], "mode": validated_spec["mode"],
                         "request_key": validated_spec["request_key"],
                         "authorization_ref": validated_spec.get("authorization_ref")},
            )
            save_handoff(handoff, state_root=qroot)
            return handoff
        finally:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)


def execute_handoff_successor(
    handoff: dict[str, Any],
    *,
    current_user: Mapping[str, Any] | None = None,
    identity_resolver: Any = None,
    state_root: Path | None = None,
    repo_root: Path | None = None,
    submit_fn: Any = None,
    enforce_runtime_convergence: bool = False,
    now_utc: datetime | None = None,
    now_epoch: float | None = None,
) -> dict[str, Any]:
    """P2B (Steps 1-14): Autonomously execute an explicitly defined, authorized successor once handoff is satisfied."""
    qroot = state_root or _default_state_root()
    rroot = repo_root or Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
    source_domain = _clean(handoff.get("source_domain")).upper()

    if handoff.get("dependency_satisfied") is not True or _clean(handoff.get("certification")).upper() not in TERMINAL_CERTIFICATIONS:
        return {"executed": False, "successor_status": "DEPENDENCY_NOT_SATISFIED", "handoff": handoff, "production_touched": False}

    # Already resumed idempotently -> REUSE_EXISTING_JOB without duplicate publication!
    if handoff.get("source_resumed") is True and _clean(handoff.get("resumed_job_id")):
        existing_jid = _clean(handoff.get("resumed_job_id"))
        verified = _verify_terminal_result_certification(existing_jid, state_root=qroot)
        if verified is not None and not handoff.get("successor_certification"):
            handoff["successor_certification"] = verified["certification"]
            handoff["successor_evidence_link"] = verified
            handoff["successor_status"] = "SUCCESSOR_CERTIFIED"
            handoff["updated_at_utc"] = utc_now()
            _append_history(handoff, "SUCCESSOR_CERTIFIED", details={"resumed_job_id": existing_jid, "certification": verified["certification"]})
            save_handoff(handoff, state_root=qroot)
        return {
            "executed": False,
            "reused": True,
            "successor_status": handoff.get("successor_status") or "REUSE_EXISTING_JOB",
            "resumed_job_id": existing_jid,
            "handoff": handoff,
            "production_touched": False,
        }

    spec = handoff.get("successor_spec")
    if not isinstance(spec, Mapping) or not spec:
        handoff["successor_status"] = "NO_SUCCESSOR_DEFINED"
        handoff["updated_at_utc"] = utc_now()
        save_handoff(handoff, state_root=qroot)
        return {"executed": False, "successor_status": "NO_SUCCESSOR_DEFINED", "handoff": handoff, "production_touched": False}

    try:
        validated_spec = _validate_successor_spec(spec, source_domain=source_domain)
    except HandoffError as exc:
        handoff["successor_status"] = "SUCCESSOR_BLOCKED_SECURITY"
        handoff["exception_code"] = str(exc)
        handoff["updated_at_utc"] = utc_now()
        _append_history(handoff, "SUCCESSOR_BLOCKED", details={"reason": str(exc)})
        save_handoff(handoff, state_root=qroot)
        return {"executed": False, "successor_status": "SUCCESSOR_BLOCKED_SECURITY", "reason": str(exc), "handoff": handoff, "production_touched": False}
    assert validated_spec is not None

    cap_code = validated_spec["capability"]
    succ_mode = validated_spec["mode"]
    succ_constraints = dict(validated_spec["constraints"])

    # Step 5: Verify capability compatibility in Capability Registry
    cap_check = resolve_compatible_capabilities(
        target_domain=source_domain,
        handoff_mode="MUTATION" if succ_mode == "MUTATION" else "READ_ONLY",
        requested_capability=cap_code,
        requested_constraints=succ_constraints,
    )
    if not cap_check.get("compatible"):
        reason = _clean(cap_check.get("exception_code")) or "CAPABILITY_REQUIRED"
        handoff["successor_status"] = "CAPABILITY_REQUIRED"
        handoff["exception_code"] = reason
        handoff["updated_at_utc"] = utc_now()
        _append_history(handoff, "SUCCESSOR_CAPABILITY_REQUIRED", details={"capability": cap_code, "reason": reason})
        save_handoff(handoff, state_root=qroot)
        return {"executed": False, "successor_status": "CAPABILITY_REQUIRED", "reason": reason, "handoff": handoff, "production_touched": False}

    # Step 6a: Canonical identity & RBAC (fail-closed, zero artificial SUPERADMIN/wildcard)
    try:
        verified_actor = _resolve_canonical_dispatch_identity(
            {
                **handoff,
                "source_domain": source_domain,
                "target_domain": source_domain,
                "handoff_mode": "MUTATION" if succ_mode == "MUTATION" else "READ_ONLY",
            },
            current_user=current_user,
            identity_resolver=identity_resolver,
        )
    except HandoffSecurityError as exc:
        handoff["successor_status"] = "SUCCESSOR_BLOCKED_SECURITY"
        handoff["exception_code"] = str(exc)
        handoff["requires_human_intervention"] = True
        handoff["human_intervention_reason"] = f"Identidad/RBAC del sucesor no verificable: {exc}"
        handoff["updated_at_utc"] = utc_now()
        _append_history(handoff, "SUCCESSOR_BLOCKED_IDENTITY", details={"reason": str(exc)})
        save_handoff(handoff, state_root=qroot)
        return {"executed": False, "successor_status": "SUCCESSOR_BLOCKED_SECURITY", "reason": str(exc), "handoff": handoff, "production_touched": False}

    # Step 6b: Verify active materialized authorization for successor
    succ_auth_ref = _clean(validated_spec.get("authorization_ref") or succ_constraints.get("authorization_ref")) or None
    if succ_mode == "MUTATION" or succ_auth_ref:
        if not succ_auth_ref:
            active_auth = lifecycle_rec.resolve_active_domain_authorization(
                source_domain,
                state_root=qroot,
                required_class="DEVELOPMENT_MUTATION",
                now_utc=now_utc,
            )
            succ_auth_ref = _clean((active_auth or {}).get("authorization_id")) or None
        if not succ_auth_ref:
            handoff["successor_status"] = "WAITING_AUTHORIZATION"
            handoff["requires_human_intervention"] = True
            handoff["human_intervention_reason"] = f"El sucesor en {source_domain} requiere autorizacion vigente materializada."
            handoff["updated_at_utc"] = utc_now()
            _append_history(handoff, "SUCCESSOR_WAITING_AUTHORIZATION", details={"domain": source_domain})
            save_handoff(handoff, state_root=qroot)
            return {"executed": False, "successor_status": "WAITING_AUTHORIZATION", "reason": "SUCCESSOR_AUTHORIZATION_MISSING", "handoff": handoff, "production_touched": False}

        req_paths: list[str] = []
        req_ops: list[str] = []
        if isinstance(succ_constraints.get("change_spec"), list):
            for item in succ_constraints["change_spec"]:
                if isinstance(item, Mapping):
                    if _clean(item.get("path")):
                        req_paths.append(_clean(item.get("path")))
                    if _clean(item.get("operation")):
                        req_ops.append(_clean(item.get("operation")))
        reval = lifecycle_rec.revalidate_gate_authorization_for_mutation(
            succ_auth_ref,
            domain=source_domain,
            requested_paths=req_paths,
            requested_operations=req_ops,
            state_root=qroot,
            repo_root=rroot,
            verify_live_sha=True,
            now_utc=now_utc,
        )
        if reval.get("authorized") is not True:
            reason = str(reval.get("reason") or "AUTHORIZATION_DENIED")
            handoff["successor_status"] = "WAITING_AUTHORIZATION"
            handoff["requires_human_intervention"] = True
            handoff["human_intervention_reason"] = f"Autorizacion del sucesor rechazada ({reason})."
            handoff["exception_code"] = reason
            handoff["updated_at_utc"] = utc_now()
            _append_history(handoff, "SUCCESSOR_WAITING_AUTHORIZATION", details={"reason": reason, "authorization_ref": succ_auth_ref})
            save_handoff(handoff, state_root=qroot)
            return {"executed": False, "successor_status": "WAITING_AUTHORIZATION", "reason": reason, "handoff": handoff, "production_touched": False}
        if succ_mode == "MUTATION" and cap_code == "DEVELOPMENT_MUTATION_BOUNDED" and "authorization_ref" not in succ_constraints:
            succ_constraints["authorization_ref"] = succ_auth_ref

    # Step 7 & 8: Build canonical job, check duplicates/completed work, and execute real preflight
    from modules.worker_ingress import service as ingress_service

    succ_req = {
        "objective": validated_spec["objective"],
        "bounded_context": source_domain,
        "mode": succ_mode,
        "capability": cap_code,
        "request_key": validated_spec["request_key"],
        "constraints": succ_constraints,
    }
    try:
        canonical_job = ingress_service.build_semantic_job(succ_req, current_user=verified_actor)
    except Exception as exc:
        reason = _clean(exc) or type(exc).__name__
        handoff["successor_status"] = "SUCCESSOR_BLOCKED_PREFLIGHT"
        handoff["exception_code"] = reason
        handoff["updated_at_utc"] = utc_now()
        _append_history(handoff, "SUCCESSOR_PREFLIGHT_REJECTED", details={"reason": reason})
        save_handoff(handoff, state_root=qroot)
        return {"executed": False, "successor_status": "SUCCESSOR_BLOCKED_PREFLIGHT", "reason": reason, "handoff": handoff, "production_touched": False}

    candidate_jid = canonical_job["job_id"]
    # Reuse already-completed certified successor or active in-flight successor (ZERO duplicates!)
    existing_cert = _verify_terminal_result_certification(candidate_jid, state_root=qroot)
    if existing_cert is not None:
        handoff["resumed_job_id"] = candidate_jid
        handoff["source_resumed"] = True
        handoff["second_go_required"] = False
        handoff["successor_status"] = "REUSE_EXISTING_JOB"
        handoff["successor_certification"] = existing_cert["certification"]
        handoff["successor_evidence_link"] = existing_cert
        handoff["resolution_stage"] = "SUCCESSOR_EXECUTED"
        handoff["updated_at_utc"] = utc_now()
        _append_history(handoff, "SUCCESSOR_REUSED_CERTIFIED", details={"resumed_job_id": candidate_jid, "certification": existing_cert["certification"]})
        save_handoff(handoff, state_root=qroot)
        return {
            "executed": False,
            "reused": True,
            "successor_status": "REUSE_EXISTING_JOB",
            "resumed_job_id": candidate_jid,
            "handoff": handoff,
            "production_touched": False,
        }

    for dirname in ("pending", "processing"):
        if (qroot / dirname / f"{candidate_jid}.json").is_file():
            handoff["resumed_job_id"] = candidate_jid
            handoff["source_resumed"] = True
            handoff["successor_status"] = "REUSE_EXISTING_JOB"
            handoff["updated_at_utc"] = utc_now()
            _append_history(handoff, "SUCCESSOR_REUSED_IN_FLIGHT", details={"resumed_job_id": candidate_jid, "queue_dir": dirname})
            save_handoff(handoff, state_root=qroot)
            return {
                "executed": False,
                "reused": True,
                "successor_status": "REUSE_EXISTING_JOB",
                "resumed_job_id": candidate_jid,
                "handoff": handoff,
                "production_touched": False,
            }

    if enforce_runtime_convergence:
        try:
            ingress_service._require_mutation_runtime_convergence()
        except Exception as exc:
            reason = _clean(exc) or "RUNTIME_NOT_CONVERGED"
            handoff["successor_status"] = "SUCCESSOR_BLOCKED_PREFLIGHT"
            handoff["exception_code"] = reason
            handoff["updated_at_utc"] = utc_now()
            save_handoff(handoff, state_root=qroot)
            return {"executed": False, "successor_status": "SUCCESSOR_BLOCKED_PREFLIGHT", "reason": reason, "handoff": handoff, "production_touched": False}

    # Step 9-12: Publish ONCE through canonical gate_chain_publisher.submit()
    publisher = submit_fn or gcp.submit
    try:
        pub_out = publisher(canonical_job, require_convergence=False)
    except TypeError:
        pub_out = publisher(canonical_job)
    except Exception as exc:
        reason = f"SUCCESSOR_PUBLISH_ERROR:{type(exc).__name__}"
        handoff["successor_status"] = "SUCCESSOR_BLOCKED_PREFLIGHT"
        handoff["exception_code"] = reason
        handoff["updated_at_utc"] = utc_now()
        _append_history(handoff, "SUCCESSOR_PUBLISH_ERROR", details={"error": type(exc).__name__})
        save_handoff(handoff, state_root=qroot)
        return {"executed": False, "successor_status": "SUCCESSOR_BLOCKED_PREFLIGHT", "reason": reason, "handoff": handoff, "production_touched": False}

    pub_status = _clean((pub_out or {}).get("status")).upper()
    pub_job_id = _clean((pub_out or {}).get("job_id")) or candidate_jid
    if pub_status in {"SUBMITTED", "ALREADY_SUBMITTED", "PUBLISHED", "EXISTS", "ALREADY_PROCESSING", "ALREADY_COMPLETED"}:
        handoff["resumed_job_id"] = pub_job_id
        handoff["source_resumed"] = True
        handoff["second_go_required"] = False
        handoff["successor_status"] = "REUSE_EXISTING_JOB" if pub_status in {"EXISTS", "ALREADY_SUBMITTED", "ALREADY_PROCESSING", "ALREADY_COMPLETED"} else "SUCCESSOR_SUBMITTED"
        handoff["resolution_stage"] = "SUCCESSOR_EXECUTED"
        handoff["updated_at_utc"] = utc_now()
        _append_history(
            handoff,
            "SUCCESSOR_DISPATCHED",
            actor_email=verified_actor.get("email"),
            details={
                "resumed_job_id": pub_job_id,
                "capability": cap_code,
                "publication_status": pub_status,
                "authorization_ref": succ_auth_ref,
            },
        )
        # Check if immediately certified
        cert_now = _verify_terminal_result_certification(pub_job_id, state_root=qroot)
        if cert_now is not None:
            handoff["successor_certification"] = cert_now["certification"]
            handoff["successor_evidence_link"] = cert_now
            handoff["successor_status"] = "SUCCESSOR_CERTIFIED"
        save_handoff(handoff, state_root=qroot)
        return {
            "executed": True,
            "reused": pub_status in {"EXISTS", "ALREADY_SUBMITTED", "ALREADY_PROCESSING", "ALREADY_COMPLETED"},
            "successor_status": handoff["successor_status"],
            "resumed_job_id": pub_job_id,
            "publication_channel": "gate_chain_publisher.submit",
            "handoff": handoff,
            "production_touched": False,
        }

    handoff["successor_status"] = "SUCCESSOR_BLOCKED_PREFLIGHT"
    handoff["exception_code"] = pub_status or "SUCCESSOR_PUBLISH_REJECTED"
    handoff["updated_at_utc"] = utc_now()
    save_handoff(handoff, state_root=qroot)
    return {"executed": False, "successor_status": "SUCCESSOR_BLOCKED_PREFLIGHT", "reason": pub_status, "handoff": handoff, "production_touched": False}


def return_certified_handoff_to_source(
    handoff: dict[str, Any],
    *,
    certified_evidence: Mapping[str, Any],
    semantic_assessment: Mapping[str, Any] | None = None,
    capability_used: str | None = None,
    current_user: Mapping[str, Any] | None = None,
    identity_resolver: Any = None,
    state_root: Path | None = None,
    repo_root: Path | None = None,
    submit_fn: Any = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Fase 4 + P2B + Section 7: Verify semantic satisfaction, link certified evidence, and auto-execute authorized successor."""
    qroot = state_root or _default_state_root()
    cert = _clean(certified_evidence.get("certification")).upper()
    if cert not in TERMINAL_CERTIFICATIONS or certified_evidence.get("production_touched") is not False:
        raise HandoffSecurityError("HANDOFF_TERMINAL_CERTIFICATION_INVALID")

    sem_eval = evaluate_handoff_semantic_satisfaction(
        handoff,
        certified_evidence,
        capability_used=capability_used,
        semantic_assessment=semantic_assessment,
    )

    now_str = utc_now()
    handoff["resolution_job_id"] = _clean(certified_evidence.get("job_id")) or handoff.get("resolution_job_id")
    handoff["certification"] = cert
    handoff["resolution_stage"] = sem_eval["resolution_stage"]
    handoff["semantic_validation"] = sem_eval
    handoff["updated_at_utc"] = now_str
    handoff["evidence_link"] = {
        "resolution_job_id": handoff["resolution_job_id"],
        "status": certified_evidence.get("status"),
        "certification": cert,
        "certification_source": certified_evidence.get("certification_source"),
        "tests": certified_evidence.get("tests"),
        "quality_gate": certified_evidence.get("quality_gate"),
        "commit_sha": certified_evidence.get("commit_sha"),
        "published_result_commit": certified_evidence.get("published_result_commit"),
        "completed_at_utc": certified_evidence.get("completed_at_utc"),
        "summary_es": certified_evidence.get("summary_es"),
        "acceptance_criteria_verified": bool(sem_eval["satisfied"]),
        "resolution_stage": sem_eval["resolution_stage"],
        "source_job_recovery_verified": bool(certified_evidence.get("source_job_recovery_verified", False)),
        "source_job_fingerprint": certified_evidence.get("source_job_fingerprint"),
        "recovery_verification": certified_evidence.get("recovery_verification"),
        "production_touched": False,
    }

    # Section 7 fail-closed: if certified evidence does NOT semantically satisfy acceptance criteria,
    # preserve dependency_satisfied=False and record concrete blocker/unmet criteria!
    if sem_eval["satisfied"] is not True:
        handoff["dependency_satisfied"] = False
        handoff["lifecycle_state"] = "ESCALATED_HUMAN_REQUIRED"
        handoff["next_allowed_action"] = "RESOLVE_SEMANTIC_BLOCKER"
        handoff["requires_human_intervention"] = True
        handoff["human_intervention_reason"] = sem_eval.get("summary")
        handoff["has_executor"] = False
        handoff["executor_status"] = "SEMANTIC_BLOCKER"
        handoff["exception_code"] = sem_eval.get("exception_code") or "HANDOFF_SEMANTIC_CRITERIA_UNMET"
        handoff["exception_reason"] = sem_eval.get("summary")
        handoff["exception_recorded_at_utc"] = now_str
        handoff["returned_at_utc"] = now_str
        _append_history(
            handoff,
            "SEMANTIC_VALIDATION_UNSATISFIED",
            details={
                "resolution_job_id": handoff["resolution_job_id"],
                "resolution_stage": sem_eval["resolution_stage"],
                "exception_code": handoff["exception_code"],
                "unmet_criteria": sem_eval.get("unmet_criteria"),
                "blockers": sem_eval.get("blockers"),
            },
        )
        save_handoff(handoff, state_root=qroot)
        return handoff

    handoff["dependency_satisfied"] = True
    handoff["lifecycle_state"] = "RETURNED_TO_SOURCE"
    handoff["next_allowed_action"] = "CONTINUE_AUTONOMOUS"
    handoff["requires_human_intervention"] = False
    handoff["human_intervention_reason"] = None
    handoff["has_executor"] = True
    handoff["executor_status"] = "RESOLVED"
    handoff["exception_code"] = None
    handoff["exception_reason"] = None
    handoff["resolved_at_utc"] = handoff.get("resolved_at_utc") or now_str
    handoff["returned_at_utc"] = now_str
    _append_history(
        handoff,
        "RETURNED_CERTIFIED_TO_SOURCE",
        details={
            "resolution_job_id": handoff["resolution_job_id"],
            "certification": cert,
            "certification_source": certified_evidence.get("certification_source"),
            "resolution_stage": sem_eval["resolution_stage"],
        },
    )

    # Auto-resume previously authorized concurrency-blocked source_job_id once without asking for another GO
    source_job_id = _clean(handoff.get("source_job_id"))
    source_domain = _clean(handoff.get("source_domain")).upper()
    if source_job_id and not handoff.get("source_resumed"):
        src_res = _read_json_safe(qroot / "results" / f"{source_job_id}.json")
        src_draft = qroot / "drafts" / f"{source_job_id}.json"
        if (
            isinstance(src_res, dict)
            and _clean(src_res.get("status")).upper() in lifecycle_rec.CONCURRENCY_BLOCKED_STATUSES
            and src_draft.is_file()
        ):
            src_auth = lifecycle_rec.resolve_active_domain_authorization(
                source_domain,
                state_root=qroot,
                required_class="DEVELOPMENT_MUTATION",
                now_utc=now_utc,
            )
            if isinstance(src_auth, Mapping) and src_auth:
                try:
                    resume_out = lifecycle_rec.resume_authorized_concurrency_blocked_objective(
                        source_job_id,
                        repo_root=repo_root,
                        state_root=qroot,
                        authorization_context=src_auth,
                        submit_fn=submit_fn,
                    )
                except Exception as exc:
                    resume_out = {"resumed": False, "error": type(exc).__name__}
                if resume_out.get("resumed") is True:
                    handoff["source_resumed"] = True
                    handoff["resumed_job_id"] = resume_out.get("resume_job_id")
                    handoff["successor_status"] = "SUCCESSOR_SUBMITTED"
                    handoff["resolution_stage"] = "SUCCESSOR_EXECUTED"
                    handoff["second_go_required"] = False

    save_handoff(handoff, state_root=qroot)

    # P2B: Execute explicitly defined authorized successor_spec if present and not yet resumed
    if isinstance(handoff.get("successor_spec"), Mapping) and not handoff.get("source_resumed"):
        execute_handoff_successor(
            handoff,
            current_user=current_user,
            identity_resolver=identity_resolver,
            state_root=qroot,
            repo_root=repo_root,
            submit_fn=submit_fn,
            now_utc=now_utc,
        )

    return handoff


def link_certified_resolution_to_handoff(
    handoff_id: str,
    resolution_job_id: str,
    *,
    semantic_assessment: Mapping[str, Any] | None = None,
    capability_used: str | None = None,
    current_user: Mapping[str, Any] | None = None,
    requester: Mapping[str, Any] | None = None,
    identity_resolver: Any = None,
    state_root: Path | None = None,
    repo_root: Path | None = None,
    submit_fn: Any = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Bind an independently certified terminal Worker resolution to the original handoff with semantic validation."""
    qroot = state_root or _default_state_root()
    handoff = load_handoff(handoff_id, state_root=qroot)
    if handoff is None:
        raise HandoffError("HANDOFF_NOT_FOUND")
    if handoff.get("production_allowed") is not False or handoff.get("production_touched") is not False:
        raise HandoffSecurityError("HANDOFF_PRODUCTION_FORBIDDEN")

    actor_email = None
    if current_user is not None or requester is not None:
        actor_email = _verify_caller_rbac_and_scope(
            current_user=current_user,
            requester=requester,
            source_domain=_clean(handoff.get("source_domain")).upper(),
            target_domain=_clean(handoff.get("target_domain")).upper(),
            handoff_mode=_clean(handoff.get("handoff_mode") or "READ_ONLY").upper(),
        )

    clean_jid = _validate_optional_token(resolution_job_id, field_name="resolution_job_id", job_id_style=True)
    if not clean_jid:
        raise HandoffError("HANDOFF_FIELD_INVALID:resolution_job_id")

    verified = _verify_terminal_result_certification(clean_jid, state_root=qroot)
    if verified is None:
        raise HandoffSecurityError("HANDOFF_TERMINAL_CERTIFICATION_INVALID")

    res_raw = _read_json_safe(qroot / "results" / f"{clean_jid}.json") or {}
    res_bc = _extract_result_bounded_context(res_raw, clean_jid, qroot)
    target_domain = _clean(handoff.get("target_domain")).upper()
    if res_bc and res_bc != target_domain:
        raise HandoffSecurityError(f"HANDOFF_RESOLUTION_DOMAIN_MISMATCH:{res_bc}!={target_domain}")

    _ensure_history(handoff)
    _append_history(
        handoff,
        "CERTIFIED_RESOLUTION_LINKED",
        actor_email=actor_email,
        details={
            "resolution_job_id": clean_jid,
            "certification": verified.get("certification"),
            "certification_source": verified.get("certification_source"),
        },
    )
    returned = return_certified_handoff_to_source(
        handoff,
        certified_evidence=verified,
        semantic_assessment=semantic_assessment,
        capability_used=capability_used,
        current_user=current_user,
        identity_resolver=identity_resolver,
        state_root=qroot,
        repo_root=repo_root,
        submit_fn=submit_fn,
        now_utc=now_utc,
    )
    return {
        "status": returned["lifecycle_state"],
        "handoff_updated": True,
        "duplicate_prevented": True,
        "handoff_id": returned["handoff_id"],
        "job_id": returned["resolution_job_id"],
        "dependency_id": returned["dependency_id"],
        "request_key": returned["request_key"],
        "source_domain": returned["source_domain"],
        "target_domain": returned["target_domain"],
        "classification": returned.get("classification"),
        "lifecycle_state": returned["lifecycle_state"],
        "certification": returned["certification"],
        "dependency_satisfied": bool(returned.get("dependency_satisfied", False)),
        "resolution_stage": returned.get("resolution_stage"),
        "successor_status": returned.get("successor_status"),
        "source_resumed": bool(returned.get("source_resumed", False)),
        "resumed_job_id": returned.get("resumed_job_id"),
        "next_allowed_action": returned["next_allowed_action"],
        "production_touched": False,
        "handoff": returned,
    }


def update_pending_handoff(
    handoff_id: str,
    *,
    requested_capability: str | None = None,
    requested_constraints: Mapping[str, Any] | None = None,
    auto_dispatch: bool | None = None,
    authorization_ref: str | None = None,
    resolution_job_id: str | None = None,
    allow_reassign_capability: bool = False,
    current_user: Mapping[str, Any] | None = None,
    requester: Mapping[str, Any] | None = None,
    state_root: Path | None = None,
    repo_root: Path | None = None,
    submit_fn: Any = None,
    identity_resolver: Any = None,
    now_utc: datetime | None = None,
    now_epoch: float | None = None,
) -> dict[str, Any]:
    """Assign a compatible capability and/or activate authorized auto_dispatch on a pending handoff without duplicating it."""
    qroot = state_root or _default_state_root()
    existing = load_handoff(handoff_id, state_root=qroot)
    if existing is None:
        raise HandoffError("HANDOFF_NOT_FOUND")
    if existing.get("production_allowed") is not False or existing.get("production_touched") is not False:
        raise HandoffSecurityError("HANDOFF_PRODUCTION_FORBIDDEN")

    state = _clean(existing.get("lifecycle_state")).upper()
    semantic_blocker_existing = _is_semantic_blocker_reassignable(existing)
    if (state not in UPDATABLE_HANDOFF_STATES and not semantic_blocker_existing) or existing.get("dependency_satisfied") is True:
        raise HandoffConflictError(f"HANDOFF_UPDATE_NOT_ALLOWED_IN_STATE:{state}")
    if _clean(existing.get("resolution_job_id")) and not resolution_job_id and not semantic_blocker_existing:
        raise HandoffConflictError("HANDOFF_ALREADY_HAS_RESOLUTION_JOB")

    source_domain = validate_domain_token(existing.get("source_domain"), field_name="source_domain")
    target_domain = validate_domain_token(existing.get("target_domain"), field_name="target_domain")
    handoff_mode = _clean(existing.get("handoff_mode") or "READ_ONLY").upper()

    _assert_no_secrets(
        {
            "requested_capability": requested_capability,
            "requested_constraints": requested_constraints,
            "authorization_ref": authorization_ref,
            "resolution_job_id": resolution_job_id,
        },
        "handoff_update",
    )
    _assert_no_untrusted_prompt(
        {
            "requested_capability": requested_capability,
            "requested_constraints": requested_constraints,
        },
        "handoff_update",
    )

    actor_email = _verify_caller_rbac_and_scope(
        current_user=current_user,
        requester=requester,
        source_domain=source_domain,
        target_domain=target_domain,
        handoff_mode=handoff_mode,
    )

    handoff = dict(existing)
    _ensure_history(handoff)
    handoff.setdefault("initial_payload_fingerprint", existing.get("payload_fingerprint"))
    handoff.setdefault(
        "core_fingerprint",
        _handoff_core_fingerprint(
            source_domain=source_domain,
            target_domain=target_domain,
            source_objective=_clean(handoff.get("source_objective")),
            source_job_id=_clean(handoff.get("source_job_id")) or None,
            incident_id=_clean(handoff.get("incident_id")) or None,
            dependency_id=_clean(handoff.get("dependency_id")),
            acceptance_criteria=list(handoff.get("acceptance_criteria") or []),
            handoff_mode=handoff_mode,
        ),
    )

    changes: dict[str, Any] = {}

    if authorization_ref is not None:
        clean_auth_ref = _validate_optional_token(authorization_ref, field_name="authorization_ref", job_id_style=False)
        auth_eval = _verify_authorization_ref(
            clean_auth_ref,
            source_domain=source_domain,
            target_domain=target_domain,
            handoff_mode=handoff_mode,
            state_root=qroot,
            now_utc=now_utc,
        )
        handoff["authorization_ref"] = clean_auth_ref
        handoff["authorization_verification"] = auth_eval
        changes["authorization_ref"] = clean_auth_ref

    if requested_capability is not None:
        clean_cap = _clean(requested_capability).upper()
        if not clean_cap or not _DOMAIN_RE.fullmatch(clean_cap):
            raise HandoffError("HANDOFF_REQUESTED_CAPABILITY_INVALID")
        if clean_cap == "CROSS_DOMAIN_HANDOFF_REGISTER":
            raise HandoffSecurityError("HANDOFF_RECURSIVE_CAPABILITY_FORBIDDEN")

        prev_cap = _clean(handoff.get("requested_capability")).upper() or None
        semantic_reassign = _is_semantic_blocker_reassignable(handoff)
        if prev_cap is not None and prev_cap != clean_cap and not (allow_reassign_capability or semantic_reassign):
            raise HandoffConflictError("IDEMPOTENCY_CONFLICT:CAPABILITY_ALREADY_ASSIGNED")
        if semantic_reassign and clean_cap == "READ_ONLY_CANARY":
            dom_crit = [c for c in (handoff.get("acceptance_criteria") or ()) if str(c).strip() not in _GENERIC_ACCEPTANCE_CRITERIA]
            if dom_crit:
                raise HandoffError("HANDOFF_CANARY_INSUFFICIENT_FOR_OBJECTIVE")
        if semantic_reassign and handoff.get("resolution_job_id"):
            prior_list = list(handoff.get("prior_insufficient_resolutions") or [])
            prior_list.append({
                "resolution_job_id": handoff.get("resolution_job_id"),
                "previous_capability": prev_cap,
                "exception_code": handoff.get("exception_code"),
                "evidence_link": handoff.get("evidence_link"),
                "archived_at_utc": utc_now(),
            })
            handoff["prior_insufficient_resolutions"] = prior_list[-20:]
            handoff["resolution_job_id"] = None
            handoff["evidence_link"] = None
            handoff["semantic_validation"] = None
            changes["reassigned_from_semantic_blocker"] = prev_cap

        new_constraints = (
            dict(requested_constraints)
            if isinstance(requested_constraints, Mapping)
            else dict(handoff.get("requested_constraints") or {})
        )
        cap_check = resolve_compatible_capabilities(
            target_domain=target_domain,
            handoff_mode=handoff_mode,
            requested_capability=clean_cap,
            requested_constraints=new_constraints,
            incident_id=_clean(handoff.get("incident_id")) or None,
        )
        if not cap_check.get("compatible"):
            exc_code = _clean(cap_check.get("exception_code")) or "NO_COMPATIBLE_CAPABILITY_AVAILABLE"
            handoff["exception_code"] = exc_code
            handoff["exception_reason"] = _clean(cap_check.get("reason"))
            handoff["exception_recorded_at_utc"] = utc_now()
            handoff["compatible_capabilities"] = list(cap_check.get("compatible_capabilities") or [])
            handoff["updated_at_utc"] = utc_now()
            _append_history(
                handoff,
                "CAPABILITY_ASSIGNMENT_REJECTED",
                actor_email=actor_email,
                details={"attempted_capability": clean_cap, "exception_code": exc_code},
            )
            save_handoff(handoff, state_root=qroot)
            raise HandoffError(f"HANDOFF_CAPABILITY_INCOMPATIBLE:{exc_code}")

        handoff["requested_capability"] = clean_cap
        handoff["requested_constraints"] = new_constraints
        changes["requested_capability"] = clean_cap
        changes["requested_constraints_keys"] = sorted(new_constraints.keys())
    elif requested_constraints is not None:
        if not isinstance(requested_constraints, Mapping):
            raise HandoffError("HANDOFF_REQUESTED_CONSTRAINTS_INVALID")
        cur_cap = _clean(handoff.get("requested_capability")).upper() or None
        if cur_cap:
            cap_check = resolve_compatible_capabilities(
                target_domain=target_domain,
                handoff_mode=handoff_mode,
                requested_capability=cur_cap,
                requested_constraints=dict(requested_constraints),
                incident_id=_clean(handoff.get("incident_id")) or None,
            )
            if not cap_check.get("compatible"):
                raise HandoffError(
                    f"HANDOFF_CAPABILITY_INCOMPATIBLE:{cap_check.get('exception_code') or 'CONTRACT_INVALID'}"
                )
        handoff["requested_constraints"] = dict(requested_constraints)
        changes["requested_constraints_keys"] = sorted(dict(requested_constraints).keys())

    if auto_dispatch is not None:
        new_auto = bool(auto_dispatch)
        if new_auto is True:
            verified_actor = _resolve_canonical_dispatch_identity(
                handoff,
                current_user=current_user,
                identity_resolver=identity_resolver,
            )
            _revalidate_dispatch_authorization(
                handoff,
                actor=verified_actor,
                state_root=qroot,
                now_utc=now_utc,
            )
            handoff["auto_dispatch_authorized_by"] = _clean(verified_actor.get("email")).lower()
            handoff["auto_dispatch_authorized_at_utc"] = utc_now()
        handoff["auto_dispatch"] = new_auto
        changes["auto_dispatch"] = new_auto

    if resolution_job_id is not None:
        return link_certified_resolution_to_handoff(
            handoff["handoff_id"],
            resolution_job_id,
            current_user=current_user,
            requester=requester,
            state_root=qroot,
            repo_root=repo_root,
            submit_fn=submit_fn,
            now_utc=now_utc,
        )

    # Recompute canonical payload_fingerprint while preserving identity, request_key, dependency_id, and history
    handoff["payload_fingerprint"] = _handoff_fingerprint(
        source_domain=source_domain,
        target_domain=target_domain,
        source_objective=_clean(handoff.get("source_objective")),
        source_job_id=_clean(handoff.get("source_job_id")) or None,
        incident_id=_clean(handoff.get("incident_id")) or None,
        dependency_id=_clean(handoff.get("dependency_id")),
        requested_capability=_clean(handoff.get("requested_capability")).upper() or None,
        requested_constraints=dict(handoff.get("requested_constraints") or {}),
        acceptance_criteria=list(handoff.get("acceptance_criteria") or []),
        handoff_mode=handoff_mode,
    )

    all_handoffs = list_handoffs(state_root=qroot)
    cls = classify_handoff_request(
        handoff,
        state_root=qroot,
        existing_handoffs=all_handoffs,
        now_utc=now_utc,
    )
    now_str = utc_now()
    handoff["updated_at_utc"] = now_str
    handoff["classification"] = cls["classification"]
    handoff["classification_reason"] = cls["reason"]
    handoff["lifecycle_state"] = cls["lifecycle_state"]
    handoff["next_allowed_action"] = cls["next_allowed_action"]
    handoff["requires_human_intervention"] = bool(cls.get("requires_human_intervention", False))
    handoff["human_intervention_reason"] = cls.get("human_intervention_reason")
    handoff["has_executor"] = bool(cls.get("has_executor", False))
    handoff["executor_status"] = cls.get("executor_status")
    handoff["compatible_capabilities"] = list(cls.get("compatible_capabilities") or [])
    handoff["exception_code"] = cls.get("exception_code")
    handoff["exception_reason"] = cls.get("exception_reason")
    if cls.get("exception_code"):
        handoff["exception_recorded_at_utc"] = now_str
    if cls.get("resolution_job_id"):
        handoff["resolution_job_id"] = cls["resolution_job_id"]

    _append_history(
        handoff,
        "PENDING_HANDOFF_UPDATED",
        actor_email=actor_email,
        details=changes,
    )
    save_handoff(handoff, state_root=qroot)

    if cls["classification"] == "CERTIFIED_RESOLUTION_EXISTS" and isinstance(cls.get("certified_evidence"), Mapping):
        handoff = return_certified_handoff_to_source(
            handoff,
            certified_evidence=cls["certified_evidence"],
            state_root=qroot,
            repo_root=repo_root,
            submit_fn=submit_fn,
            now_utc=now_utc,
        )
        return {
            "status": "RETURNED_TO_SOURCE",
            "handoff_updated": True,
            "duplicate_prevented": True,
            "reused_certified_resolution": True,
            "handoff_id": handoff["handoff_id"],
            "job_id": handoff.get("resolution_job_id") or handoff["handoff_id"],
            "dependency_id": handoff["dependency_id"],
            "request_key": handoff["request_key"],
            "source_domain": handoff["source_domain"],
            "target_domain": handoff["target_domain"],
            "classification": handoff["classification"],
            "lifecycle_state": handoff["lifecycle_state"],
            "certification": handoff["certification"],
            "next_allowed_action": handoff["next_allowed_action"],
            "has_executor": handoff.get("has_executor", True),
            "executor_status": handoff.get("executor_status"),
            "exception_code": handoff.get("exception_code"),
            "production_touched": False,
            "handoff": handoff,
        }

    dispatch_out: dict[str, Any] | None = None
    if cls.get("dispatch_eligible") is True and handoff.get("auto_dispatch") is True:
        dispatch_out = dispatch_handoff_resolution(
            handoff,
            state_root=qroot,
            repo_root=repo_root,
            current_user=current_user,
            identity_resolver=identity_resolver,
            submit_fn=submit_fn,
            now_utc=now_utc,
            now_epoch=now_epoch,
        )
        handoff = dispatch_out["handoff"]
        if handoff.get("resolution_job_id"):
            verified = _verify_terminal_result_certification(str(handoff["resolution_job_id"]), state_root=qroot)
            if verified is not None:
                handoff = return_certified_handoff_to_source(
                    handoff,
                    certified_evidence=verified,
                    state_root=qroot,
                    repo_root=repo_root,
                    submit_fn=submit_fn,
                    now_utc=now_utc,
                )

    return {
        "status": (
            "RETURNED_TO_SOURCE"
            if handoff.get("lifecycle_state") == "RETURNED_TO_SOURCE"
            else ("SUBMITTED" if handoff.get("lifecycle_state") == "IN_PROGRESS" else "UPDATED")
        ),
        "handoff_updated": True,
        "duplicate_prevented": True,
        "dispatched": bool((dispatch_out or {}).get("dispatched", False)),
        "dispatch_status": (dispatch_out or {}).get("status"),
        "handoff_id": handoff["handoff_id"],
        "job_id": handoff.get("resolution_job_id") or handoff["handoff_id"],
        "dependency_id": handoff["dependency_id"],
        "request_key": handoff["request_key"],
        "source_domain": handoff["source_domain"],
        "target_domain": handoff["target_domain"],
        "classification": handoff["classification"],
        "lifecycle_state": handoff["lifecycle_state"],
        "certification": handoff["certification"],
        "next_allowed_action": handoff["next_allowed_action"],
        "has_executor": bool(handoff.get("has_executor", False)),
        "executor_status": handoff.get("executor_status"),
        "compatible_capabilities": list(handoff.get("compatible_capabilities") or []),
        "exception_code": handoff.get("exception_code"),
        "production_touched": False,
        "handoff": handoff,
    }


def register_cross_domain_handoff(
    request: Mapping[str, Any],
    *,
    current_user: Mapping[str, Any] | None = None,
    requester: Mapping[str, Any] | None = None,
    state_root: Path | None = None,
    repo_root: Path | None = None,
    submit_fn: Any = None,
    identity_resolver: Any = None,
    now_utc: datetime | None = None,
    now_epoch: float | None = None,
) -> dict[str, Any]:
    """Fase 2 & 3 entry point: validate, persist atomically (or enrich pending without duplicating), classify, and dispatch."""
    qroot = state_root or _default_state_root()
    validated = validate_handoff_constraints(
        request,
        current_user=current_user,
        requester=requester,
        state_root=qroot,
        now_utc=now_utc,
        now_epoch=now_epoch,
        dry_run=False,
    )

    if validated.get("successor_update") is True:
        updated = register_handoff_successor(
            validated["handoff_id"], validated["successor_spec"],
            current_user=current_user, requester=requester, state_root=qroot,
        )
        return {
            "status": "SUCCESSOR_REGISTERED", "handoff_updated": True,
            "duplicate_prevented": True, "handoff_id": updated["handoff_id"],
            "job_id": updated.get("resolution_job_id") or updated["handoff_id"],
            "dependency_id": updated["dependency_id"], "lifecycle_state": updated["lifecycle_state"],
            "certification": updated["certification"], "successor_status": updated["successor_status"],
            "production_touched": False, "handoff": updated,
        }

    if validated.get("duplicate") is True:
        existing = dict(validated["existing_handoff"])
        return {
            "status": "EXISTS",
            "duplicate_prevented": True,
            "handoff_updated": False,
            "handoff_id": existing["handoff_id"],
            "job_id": existing.get("resolution_job_id") or existing["handoff_id"],
            "dependency_id": existing["dependency_id"],
            "source_domain": existing["source_domain"],
            "target_domain": existing["target_domain"],
            "classification": existing.get("classification"),
            "lifecycle_state": existing.get("lifecycle_state"),
            "certification": existing.get("certification"),
            "next_allowed_action": existing.get("next_allowed_action"),
            "has_executor": bool(existing.get("has_executor", bool(existing.get("resolution_job_id")))),
            "executor_status": existing.get("executor_status"),
            "exception_code": existing.get("exception_code"),
            "production_touched": False,
            "handoff": existing,
        }

    if validated.get("pending_update") is True:
        changes = dict(validated.get("update_changes") or {})
        constraints = request.get("constraints") if isinstance(request.get("constraints"), Mapping) else {}
        return update_pending_handoff(
            validated["handoff_id"],
            requested_capability=changes.get("capability_assigned"),
            requested_constraints=(
                dict(constraints.get("requested_constraints") or {})
                if changes.get("capability_assigned") is not None
                else None
            ),
            auto_dispatch=True if changes.get("auto_dispatch_activated") else None,
            authorization_ref=constraints.get("authorization_ref") if changes.get("authorization_ref_updated") else None,
            resolution_job_id=changes.get("resolution_job_id_linked"),
            allow_reassign_capability=bool(changes.get("allow_reassign_capability", False)),
            current_user=current_user,
            requester=requester,
            state_root=qroot,
            repo_root=repo_root,
            submit_fn=submit_fn,
            identity_resolver=identity_resolver,
            now_utc=now_utc,
            now_epoch=now_epoch,
        )

    now_str = utc_now()
    handoff = dict(validated["candidate"])
    cls = dict(validated["classification"])
    handoff["created_at_utc"] = now_str
    handoff["updated_at_utc"] = now_str
    handoff["classification"] = cls["classification"]
    handoff["classification_reason"] = cls["reason"]
    handoff["lifecycle_state"] = cls["lifecycle_state"]
    handoff["next_allowed_action"] = cls["next_allowed_action"]
    handoff["requires_human_intervention"] = bool(cls.get("requires_human_intervention", False))
    handoff["human_intervention_reason"] = cls.get("human_intervention_reason")
    handoff["has_executor"] = bool(cls.get("has_executor", False))
    handoff["executor_status"] = cls.get("executor_status")
    handoff["compatible_capabilities"] = list(cls.get("compatible_capabilities") or [])
    handoff["exception_code"] = cls.get("exception_code")
    handoff["exception_reason"] = cls.get("exception_reason")
    if cls.get("exception_code"):
        handoff["exception_recorded_at_utc"] = now_str
    if cls.get("resolution_job_id"):
        handoff["resolution_job_id"] = cls["resolution_job_id"]
    _ensure_history(handoff)

    save_handoff(handoff, state_root=qroot)

    # Automatic return immediately when a certified terminal resolution already exists!
    if cls["classification"] == "CERTIFIED_RESOLUTION_EXISTS" and isinstance(cls.get("certified_evidence"), Mapping):
        handoff = return_certified_handoff_to_source(
            handoff,
            certified_evidence=cls["certified_evidence"],
            state_root=qroot,
            repo_root=repo_root,
            submit_fn=submit_fn,
            now_utc=now_utc,
        )
        return {
            "status": "RETURNED_TO_SOURCE",
            "duplicate_prevented": False,
            "handoff_updated": False,
            "reused_certified_resolution": True,
            "handoff_id": handoff["handoff_id"],
            "job_id": handoff.get("resolution_job_id") or handoff["handoff_id"],
            "dependency_id": handoff["dependency_id"],
            "source_domain": handoff["source_domain"],
            "target_domain": handoff["target_domain"],
            "classification": handoff["classification"],
            "lifecycle_state": handoff["lifecycle_state"],
            "certification": handoff["certification"],
            "next_allowed_action": handoff["next_allowed_action"],
            "has_executor": True,
            "executor_status": "RESOLVED",
            "exception_code": None,
            "production_touched": False,
            "handoff": handoff,
        }

    # Optional autonomous dispatch through gate_chain_publisher.submit()
    if cls.get("dispatch_eligible") is True and handoff.get("auto_dispatch") is True:
        disp = dispatch_handoff_resolution(
            handoff,
            state_root=qroot,
            repo_root=repo_root,
            current_user=current_user,
            identity_resolver=identity_resolver,
            submit_fn=submit_fn,
            now_utc=now_utc,
            now_epoch=now_epoch,
        )
        handoff = disp["handoff"]
        # Re-check immediately if submitted job was ALREADY_COMPLETED and certified
        if handoff.get("resolution_job_id"):
            verified = _verify_terminal_result_certification(str(handoff["resolution_job_id"]), state_root=qroot)
            if verified is not None:
                handoff = return_certified_handoff_to_source(
                    handoff,
                    certified_evidence=verified,
                    state_root=qroot,
                    repo_root=repo_root,
                    submit_fn=submit_fn,
                    now_utc=now_utc,
                )

    return {
        "status": "SUBMITTED" if handoff.get("lifecycle_state") == "IN_PROGRESS" else handoff["lifecycle_state"],
        "duplicate_prevented": False,
        "handoff_updated": False,
        "handoff_id": handoff["handoff_id"],
        "job_id": handoff.get("resolution_job_id") or handoff["handoff_id"],
        "dependency_id": handoff["dependency_id"],
        "source_domain": handoff["source_domain"],
        "target_domain": handoff["target_domain"],
        "classification": handoff["classification"],
        "lifecycle_state": handoff["lifecycle_state"],
        "certification": handoff["certification"],
        "next_allowed_action": handoff["next_allowed_action"],
        "has_executor": bool(handoff.get("has_executor", False)),
        "executor_status": handoff.get("executor_status"),
        "compatible_capabilities": list(handoff.get("compatible_capabilities") or []),
        "exception_code": handoff.get("exception_code"),
        "production_touched": False,
        "handoff": handoff,
    }


def preflight_supersede_cross_domain_handoff(
    request: Mapping[str, Any],
    *,
    current_user: Mapping[str, Any] | None = None,
    requester: Mapping[str, Any] | None = None,
    state_root: Path | None = None,
) -> dict[str, Any]:
    """Fail-closed administrative supersession, distinct from certified resolution."""
    qroot = state_root or _default_state_root()
    if _clean(request.get("mode")).upper() != "MUTATION":
        raise HandoffSecurityError("HANDOFF_SUPERSEDE_MUTATION_MODE_REQUIRED")
    c = request.get("constraints")
    if not isinstance(c, Mapping):
        raise HandoffError("SEMANTIC_CONSTRAINTS_INVALID")
    _assert_no_secrets(c, "handoff_supersede")
    _assert_no_untrusted_prompt(c, "handoff_supersede")
    hid = _validate_optional_token(c.get("handoff_id"), field_name="handoff_id", job_id_style=True)
    jid = _validate_optional_token(c.get("superseded_by_job_id"), field_name="superseded_by_job_id", job_id_style=True)
    source_id = _validate_optional_token(c.get("expected_source_job_id"), field_name="expected_source_job_id", job_id_style=True)
    auth = _validate_optional_token(c.get("authorization_ref"), field_name="authorization_ref", job_id_style=False)
    reason = _clean(c.get("reason"))
    notice_only = c.get("notification_only") is True
    if "notification_only" in c and type(c["notification_only"]) is not bool:
        raise HandoffSecurityError("HANDOFF_SUPERSEDE_NOTICE_FLAG_INVALID")
    notice_key = _clean(c.get("expected_notice_request_key"))
    notice_gate = _clean(c.get("expected_notice_gate_id"))
    evidence_auth = _clean(c.get("certified_job_authorization_ref"))
    if not all((hid, jid, auth)) or (not notice_only and not source_id):
        raise HandoffSecurityError("HANDOFF_SUPERSEDE_PROOFS_REQUIRED")
    if notice_only and not all((notice_key, notice_gate, evidence_auth)):
        raise HandoffSecurityError("HANDOFF_SUPERSEDE_NOTICE_PROOFS_REQUIRED")
    if not notice_only and any(k in c for k in (
        "expected_notice_request_key", "expected_notice_gate_id",
        "certified_job_authorization_ref",
    )):
        raise HandoffSecurityError("HANDOFF_SUPERSEDE_NOTICE_FIELDS_FORBIDDEN")
    if not 12 <= len(reason) <= 500:
        raise HandoffError("HANDOFF_SUPERSEDE_REASON_INVALID")
    handoff = load_handoff(hid, state_root=qroot)
    if handoff is None:
        raise HandoffError("HANDOFF_NOT_FOUND")
    if handoff.get("production_allowed") is not False or handoff.get("production_touched") is not False:
        raise HandoffSecurityError("HANDOFF_PRODUCTION_FORBIDDEN")
    source = _clean(handoff.get("source_domain")).upper()
    owner = _clean(handoff.get("target_domain")).upper()
    if _clean(request.get("bounded_context")).upper() != owner:
        raise HandoffSecurityError("HANDOFF_SUPERSEDE_OWNER_DOMAIN_MISMATCH")
    if notice_only:
        requested = handoff.get("requested_constraints")
        if not isinstance(requested, Mapping):
            raise HandoffSecurityError("HANDOFF_SUPERSEDE_NOTICE_CONSTRAINTS_MISSING")
        if (
            source_id is not None
            or _clean(handoff.get("source_job_id"))
            or _clean(handoff.get("incident_id"))
            or _clean(handoff.get("resolution_job_id"))
            or _clean(handoff.get("handoff_mode")).upper() != "READ_ONLY"
            or handoff.get("auto_dispatch") is not False
            or handoff.get("has_executor") is not False
            or _clean(handoff.get("requested_capability")).upper() != "GATE_AUTHORIZATION_LIFECYCLE"
            or _clean(requested.get("action")).upper() not in {"CONSENT_STATUS", "INSPECT"}
            or _clean(requested.get("gate_id")) != notice_gate
            or _clean(handoff.get("request_key")) != notice_key
        ):
            raise HandoffSecurityError("HANDOFF_SUPERSEDE_NOT_INFORMATIONAL_NOTICE")
    elif _clean(handoff.get("source_job_id")) != source_id:
        raise HandoffSecurityError("HANDOFF_SUPERSEDE_SOURCE_JOB_MISMATCH")
    try:
        actor = lifecycle_rec._validate_authorized_actor_identity(current_user)
    except lifecycle_rec.GateAuthorizationError as exc:
        raise HandoffSecurityError(f"HANDOFF_SUPERSEDE_SQL_RBAC_DENIED:{exc}") from exc
    _verify_caller_rbac_and_scope(
        current_user=current_user, requester=requester,
        source_domain=source, target_domain=owner, handoff_mode="MUTATION",
    )
    auth_check = _verify_authorization_ref(
        auth, source_domain=owner, target_domain=owner,
        handoff_mode="MUTATION", state_root=qroot,
    )
    if auth_check.get("verified") is not True:
        raise HandoffSecurityError("HANDOFF_SUPERSEDE_AUTHORIZATION_UNVERIFIED")
    evidence = _verify_terminal_result_certification(jid, state_root=qroot)
    if evidence is None or evidence.get("status") != "INTEGRATED" or evidence.get("certification") != "CERTIFIED":
        raise HandoffSecurityError("HANDOFF_SUPERSEDE_SOURCE_NOT_CERTIFIED")
    raw = _read_json_safe(qroot / "results" / f"{jid}.json") or {}
    certified_domain = _extract_result_bounded_context(raw, jid, qroot)
    if certified_domain != (owner if notice_only else source):
        raise HandoffSecurityError("HANDOFF_SUPERSEDE_SOURCE_DOMAIN_MISMATCH")
    if notice_only:
        certified_request = _read_json_safe(qroot / "done" / f"{jid}.json") or {}
        if (
            _clean(certified_request.get("authorization_ref")) != evidence_auth
            or not evidence_auth.startswith(f"GO-{notice_gate}-")
            or not evidence_auth[len(f"GO-{notice_gate}-"):].isdigit()
            or len(evidence_auth[len(f"GO-{notice_gate}-"):]) != 8
        ):
            raise HandoffSecurityError("HANDOFF_SUPERSEDE_NOTICE_CERTIFIED_GATE_MISMATCH")
    state = _clean(handoff.get("lifecycle_state")).upper()
    if state == "SUPERSEDED":
        if (_clean(handoff.get("superseded_by_job_id")) != jid
            or _clean(handoff.get("supersession_reason")) != reason
            or _clean(handoff.get("supersession_authorization_ref")) != auth
            or (handoff.get("informational_notice_closed") is True) != notice_only
            or (notice_only and (
                _clean(handoff.get("supersession_notice_gate_id")) != notice_gate
                or _clean(handoff.get("supersession_notice_request_key")) != notice_key
                or _clean(handoff.get("supersession_evidence_authorization_ref")) != evidence_auth
            ))
        ):
            raise HandoffConflictError("HANDOFF_SUPERSEDE_IDEMPOTENCY_CONFLICT")
        return {"status": "EXISTS", "handoff_id": hid, "superseded_by_job_id": jid,
                "duplicate_prevented": True, "production_touched": False}
    if (state not in UPDATABLE_HANDOFF_STATES or handoff.get("dependency_satisfied") is True
        or _clean(handoff.get("resolution_job_id")) or handoff.get("source_resumed") is True):
        raise HandoffConflictError("HANDOFF_SUPERSEDE_STATE_NOT_ELIGIBLE")
    return {"status": "PREFLIGHT_READY", "handoff_id": hid, "superseded_by_job_id": jid,
            "actor_email": actor["email"], "authorization_ref": auth,
            "reason": reason, "evidence": evidence,
            "notification_only": notice_only, "notice_gate_id": notice_gate if notice_only else None,
            "notice_request_key": notice_key if notice_only else None,
            "evidence_authorization_ref": evidence_auth if notice_only else None,
            "production_touched": False}


def supersede_cross_domain_handoff(
    request: Mapping[str, Any],
    *,
    current_user: Mapping[str, Any] | None = None,
    requester: Mapping[str, Any] | None = None,
    state_root: Path | None = None,
) -> dict[str, Any]:
    """Retire a stale handoff atomically; preserve NOT_CERTIFIED and original history."""
    import fcntl
    qroot = state_root or _default_state_root()
    initial = preflight_supersede_cross_domain_handoff(
        request, current_user=current_user, requester=requester, state_root=qroot,
    )
    if initial["status"] == "EXISTS":
        return initial
    hid = initial["handoff_id"]
    with open(handoffs_dir(qroot) / f"{hid}.supersede.lock", "a+", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            pf = preflight_supersede_cross_domain_handoff(
                request, current_user=current_user, requester=requester, state_root=qroot,
            )
            if pf["status"] == "EXISTS":
                return pf
            record = load_handoff(hid, state_root=qroot)
            if record is None:
                raise HandoffError("HANDOFF_NOT_FOUND")
            ev = pf["evidence"]
            _ensure_history(record)
            record.update(
                lifecycle_state="SUPERSEDED",
                superseded_by_job_id=pf["superseded_by_job_id"],
                supersession_reason=pf["reason"],
                supersession_authorization_ref=pf["authorization_ref"],
                supersession_evidence={
                    "job_id": ev["job_id"], "certification": ev["certification"],
                    "certification_source": ev["certification_source"],
                    "commit_sha": ev.get("commit_sha"),
                    "published_result_commit": ev.get("published_result_commit"),
                    "production_touched": False,
                },
                superseded_at_utc=utc_now(), next_allowed_action="NONE",
                requires_human_intervention=False, human_intervention_reason=None,
                has_executor=False, executor_status="SUPERSEDED",
                dependency_satisfied=False, certification="NOT_CERTIFIED",
                resolution_job_id=None, source_resumed=False,
                exception_code=None, exception_reason=None,
            )
            record["updated_at_utc"] = record["superseded_at_utc"]
            if pf.get("notification_only") is True:
                record["informational_notice_closed"] = True
                record["supersession_notice_gate_id"] = pf["notice_gate_id"]
                record["supersession_notice_request_key"] = pf["notice_request_key"]
                record["supersession_evidence_authorization_ref"] = pf["evidence_authorization_ref"]
            details = {"superseded_by_job_id": pf["superseded_by_job_id"],
                       "authorization_ref": pf["authorization_ref"],
                       "reason": pf["reason"]}
            if pf.get("notification_only") is True:
                details["notification_only"] = True
                details["notice_gate_id"] = pf["notice_gate_id"]
            _append_history(record, "ADMINISTRATIVELY_SUPERSEDED",
                            actor_email=pf["actor_email"], details=details)
            save_handoff(record, state_root=qroot)
            return {"status": "SUPERSEDED", "handoff_id": hid,
                    "superseded_by_job_id": pf["superseded_by_job_id"],
                    "lifecycle_state": "SUPERSEDED", "dependency_satisfied": False,
                    "certification": "NOT_CERTIFIED", "production_touched": False}
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def reconcile_cross_domain_handoffs(
    *,
    state_root: Path | None = None,
    repo_root: Path | None = None,
    max_dispatches: int = MAX_HANDOFF_DISPATCHES_PER_CYCLE,
    no_executor_stall_seconds: int = NO_EXECUTOR_STALL_SECONDS,
    submit_fn: Any = None,
    identity_resolver: Any = None,
    now_utc: datetime | None = None,
    now_epoch: float | None = None,
) -> dict[str, Any]:
    """Periodic Control Plane reconciliation: certify returns, flag requests without executor, dispatch eligible work."""
    qroot = state_root or _default_state_root()
    handoffs = list_handoffs(state_root=qroot)
    returned_ids: list[str] = []
    dispatched_ids: list[str] = []
    reclassified_ids: list[str] = []
    without_executor_ids: list[str] = []
    stalled_no_executor_ids: list[str] = []
    errors: list[dict[str, str]] = []
    dispatches_left = max(0, int(max_dispatches))
    now_dt = now_utc or datetime.now(timezone.utc)
    if now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=timezone.utc)

    for record in handoffs:
        hid = _clean(record.get("handoff_id"))
        state = _clean(record.get("lifecycle_state")).upper()
        if state in {"BLOCKED_CYCLE", "BLOCKED_POLICY", "SUPERSEDED"}:
            continue
        if state == "RETURNED_TO_SOURCE":
            try:
                resumed_jid = _clean(record.get("resumed_job_id"))
                if resumed_jid and not record.get("successor_certification"):
                    succ_cert = _verify_terminal_result_certification(resumed_jid, state_root=qroot)
                    if succ_cert is not None:
                        record["successor_certification"] = succ_cert["certification"]
                        record["successor_evidence_link"] = succ_cert
                        record["successor_status"] = "SUCCESSOR_CERTIFIED"
                        record["resolution_stage"] = "SUCCESSOR_EXECUTED"
                        record["updated_at_utc"] = utc_now()
                        _append_history(
                            record,
                            "SUCCESSOR_CERTIFIED",
                            details={"resumed_job_id": resumed_jid, "certification": succ_cert["certification"]},
                        )
                        save_handoff(record, state_root=qroot)
                elif (
                    isinstance(record.get("successor_spec"), Mapping)
                    and not record.get("source_resumed")
                    and dispatches_left > 0
                ):
                    succ_out = execute_handoff_successor(
                        record,
                        identity_resolver=identity_resolver,
                        state_root=qroot,
                        repo_root=repo_root,
                        submit_fn=submit_fn,
                        now_utc=now_dt,
                        now_epoch=now_epoch,
                    )
                    if succ_out.get("executed") is True:
                        dispatched_ids.append(hid)
                        dispatches_left -= 1
            except Exception as exc:
                errors.append({"handoff_id": hid, "error": type(exc).__name__})
            continue
        try:
            # 0. Preserve Section 7 semantic unsatisfied state when this exact resolution_job_id was already evaluated as unsatisfied
            existing_sem = record.get("semantic_validation")
            existing_ev = record.get("evidence_link")
            if (
                isinstance(existing_sem, Mapping)
                and existing_sem.get("satisfied") is False
                and _clean((existing_ev or {}).get("resolution_job_id")) == _clean(record.get("resolution_job_id"))
                and _clean(record.get("resolution_job_id"))
            ):
                continue

            # 1. Check if bound resolution_job_id reached terminal certification
            res_jid = _clean(record.get("resolution_job_id"))
            if res_jid:
                verified = _verify_terminal_result_certification(res_jid, state_root=qroot)
                if verified is not None:
                    return_certified_handoff_to_source(
                        record,
                        certified_evidence=verified,
                        state_root=qroot,
                        repo_root=repo_root,
                        submit_fn=submit_fn,
                        now_utc=now_dt,
                    )
                    returned_ids.append(hid)
                    continue

            # 2. Re-classify open handoffs to detect newly certified results, compatible capabilities, or missing executor
            cls = classify_handoff_request(
                record,
                state_root=qroot,
                existing_handoffs=handoffs,
                now_utc=now_dt,
            )
            if cls["classification"] == "CERTIFIED_RESOLUTION_EXISTS" and isinstance(cls.get("certified_evidence"), Mapping):
                record["classification"] = cls["classification"]
                record["classification_reason"] = cls["reason"]
                return_certified_handoff_to_source(
                    record,
                    certified_evidence=cls["certified_evidence"],
                    state_root=qroot,
                    repo_root=repo_root,
                    submit_fn=submit_fn,
                    now_utc=now_dt,
                )
                returned_ids.append(hid)
                continue

            has_exec = bool(cls.get("has_executor", False)) or bool(res_jid)
            exec_status = cls.get("executor_status") or ("IN_FLIGHT_JOB" if res_jid else "UNASSIGNED_NO_EXECUTOR")
            compat_caps = list(cls.get("compatible_capabilities") or [])
            next_action = cls["next_allowed_action"]

            # Keep technical planning visible without asking a human to approve an absent plan.
            technical_plan_required = (
                _clean(record.get("target_domain")).upper() in WORKER_INFRA_DOMAINS
                and _clean(record.get("handoff_mode") or "READ_ONLY").upper() == "READ_ONLY"
                and not _clean(record.get("requested_capability"))
                and cls.get("next_allowed_action") == "ASSIGN_COMPATIBLE_CAPABILITY"
                and cls.get("requires_human_intervention") is False
                and not has_exec
            )
            if technical_plan_required:
                cls = {**cls, "exception_code": "TECHNICAL_RESOLUTION_PLAN_REQUIRED",
                       "exception_reason": "Bounded technical plan required; no consent inferred."}

            # Determine whether this handoff is already in steady-state stall escalation
            # so reconciliation never oscillates between CLASSIFIED/QUEUED and ESCALATED_HUMAN_REQUIRED
            # and never rewrites the file when nothing meaningful changed.
            ref_dt = policy_ctrl._parse_utc(record.get("created_at_utc") or record.get("updated_at_utc"))
            age_s = (now_dt - ref_dt).total_seconds() if ref_dt is not None else 0.0
            stall_applicable = (
                not has_exec
                and not technical_plan_required
                and not _clean(record.get("resolution_job_id"))
                and age_s >= float(no_executor_stall_seconds)
                and cls["lifecycle_state"] in {"REGISTERED", "CLASSIFIED", "QUEUED_IN_TARGET_DOMAIN"}
            )
            already_stalled_escalated = (
                stall_applicable
                and state == "ESCALATED_HUMAN_REQUIRED"
                and _clean(record.get("exception_code")) == (cls.get("exception_code") or "HANDOFF_NO_EXECUTOR_STALLED")
            )
            effective_state = "ESCALATED_HUMAN_REQUIRED" if already_stalled_escalated else cls["lifecycle_state"]
            effective_next_action = (
                (
                    "ACTIVATE_AUTHORIZED_AUTO_DISPATCH"
                    if _clean(record.get("requested_capability"))
                    else "ASSIGN_COMPATIBLE_CAPABILITY"
                )
                if already_stalled_escalated
                else next_action
            )
            effective_exception_code = (
                (cls.get("exception_code") or "HANDOFF_NO_EXECUTOR_STALLED")
                if already_stalled_escalated
                else cls.get("exception_code")
            )

            needs_update = (
                cls["classification"] != record.get("classification")
                or effective_state != state
                or effective_next_action != record.get("next_allowed_action")
                or record.get("has_executor") is not has_exec
                or record.get("executor_status") != exec_status
                or record.get("exception_code") != effective_exception_code
            )
            if needs_update:
                _ensure_history(record)
                record["classification"] = cls["classification"]
                record["classification_reason"] = cls["reason"]
                record["lifecycle_state"] = effective_state
                record["next_allowed_action"] = effective_next_action
                record["requires_human_intervention"] = (
                    True if already_stalled_escalated else bool(cls.get("requires_human_intervention", False))
                )
                if not already_stalled_escalated:
                    record["human_intervention_reason"] = cls.get("human_intervention_reason")
                    record["exception_reason"] = cls.get("exception_reason")
                record["has_executor"] = has_exec
                record["executor_status"] = exec_status
                record["compatible_capabilities"] = compat_caps
                record["exception_code"] = effective_exception_code
                if effective_exception_code and not already_stalled_escalated:
                    record["exception_recorded_at_utc"] = utc_now()
                if cls.get("resolution_job_id"):
                    record["resolution_job_id"] = cls["resolution_job_id"]
                record["updated_at_utc"] = utc_now()
                _append_history(
                    record,
                    "RECONCILED_CLASSIFICATION",
                    details={
                        "classification": cls["classification"],
                        "executor_status": exec_status,
                        "exception_code": effective_exception_code,
                    },
                )
                save_handoff(record, state_root=qroot)
                reclassified_ids.append(hid)

            # 3. Identify requests without executor — NEVER leave them indefinitely in WAIT!
            if not has_exec and not _clean(record.get("resolution_job_id")):
                without_executor_ids.append(hid)
                if (
                    not technical_plan_required
                    and age_s >= float(no_executor_stall_seconds)
                    and _clean(record.get("lifecycle_state")).upper() in {"REGISTERED", "CLASSIFIED", "QUEUED_IN_TARGET_DOMAIN"}
                ):
                    _ensure_history(record)
                    record["lifecycle_state"] = "ESCALATED_HUMAN_REQUIRED"
                    record["requires_human_intervention"] = True
                    record["exception_code"] = record.get("exception_code") or "HANDOFF_NO_EXECUTOR_STALLED"
                    record["exception_reason"] = (
                        f"Solicitud sin ejecutor activo tras {int(age_s)}s ({exec_status}); "
                        "no debe permanecer indefinidamente en WAIT."
                    )
                    record["human_intervention_reason"] = record["exception_reason"]
                    record["exception_recorded_at_utc"] = utc_now()
                    record["next_allowed_action"] = (
                        "ACTIVATE_AUTHORIZED_AUTO_DISPATCH"
                        if _clean(record.get("requested_capability"))
                        else "ASSIGN_COMPATIBLE_CAPABILITY"
                    )
                    record["updated_at_utc"] = utc_now()
                    _append_history(
                        record,
                        "NO_EXECUTOR_STALL_EXCEPTION",
                        details={"age_seconds": int(age_s), "executor_status": exec_status},
                    )
                    save_handoff(record, state_root=qroot)
                    stalled_no_executor_ids.append(hid)
                    continue

            # 4. Dispatch eligible work within per-cycle budget (using canonical RBAC & auth revalidation)
            if (
                cls.get("dispatch_eligible") is True
                and record.get("auto_dispatch") is True
                and dispatches_left > 0
                and not _clean(record.get("resolution_job_id"))
            ):
                disp = dispatch_handoff_resolution(
                    record,
                    state_root=qroot,
                    repo_root=repo_root,
                    identity_resolver=identity_resolver,
                    submit_fn=submit_fn,
                    now_utc=now_dt,
                    now_epoch=now_epoch,
                )
                if disp.get("dispatched") is True:
                    dispatched_ids.append(hid)
                    dispatches_left -= 1
        except Exception as exc:
            errors.append({"handoff_id": hid, "error": type(exc).__name__})

    refreshed = list_handoffs(state_root=qroot)
    active_count = sum(1 for h in refreshed if _clean(h.get("lifecycle_state")).upper() in ACTIVE_HANDOFF_STATES)
    returned_count = sum(1 for h in refreshed if _clean(h.get("lifecycle_state")).upper() == "RETURNED_TO_SOURCE")
    human_req = sum(1 for h in refreshed if h.get("requires_human_intervention") is True)
    return {
        "schema": SCHEMA_HANDOFF_RECONCILE,
        "reconciled_at_utc": utc_now(),
        "total_handoffs": len(refreshed),
        "active_handoffs": active_count,
        "returned_to_source_total": returned_count,
        "human_intervention_required_count": human_req,
        "without_executor_count": len(without_executor_ids),
        "without_executor_this_cycle": without_executor_ids,
        "stalled_no_executor_this_cycle": stalled_no_executor_ids,
        "returned_this_cycle": returned_ids,
        "dispatched_this_cycle": dispatched_ids,
        "reclassified_this_cycle": reclassified_ids,
        "isolated_errors": errors,
        "production_touched": False,
    }


def _compact_handoff_view(h: Mapping[str, Any]) -> dict[str, Any]:
    res_jid = h.get("resolution_job_id")
    st = _clean(h.get("lifecycle_state")).upper()
    default_has_exec = bool(res_jid) or st == "RETURNED_TO_SOURCE"
    return {
        "handoff_id": h.get("handoff_id"),
        "source_domain": h.get("source_domain"),
        "target_domain": h.get("target_domain"),
        "owner_domain": h.get("owner_domain") or h.get("target_domain"),
        "source_objective": h.get("source_objective"),
        "source_job_id": h.get("source_job_id"),
        "incident_id": h.get("incident_id"),
        "dependency_id": h.get("dependency_id"),
        "request_key": h.get("request_key"),
        "authorization_ref": h.get("authorization_ref"),
        "requested_capability": h.get("requested_capability"),
        "auto_dispatch": bool(h.get("auto_dispatch", False)),
        "acceptance_criteria": list(h.get("acceptance_criteria") or []),
        "resolution_job_id": res_jid,
        "certification": h.get("certification"),
        "lifecycle_state": h.get("lifecycle_state"),
        "next_allowed_action": h.get("next_allowed_action"),
        "classification": h.get("classification"),
        "has_executor": bool(h.get("has_executor", default_has_exec)),
        "executor_status": h.get("executor_status") or ("RESOLVED" if st == "RETURNED_TO_SOURCE" else ("IN_FLIGHT_JOB" if res_jid else "UNASSIGNED_NO_EXECUTOR")),
        "compatible_capabilities": list(h.get("compatible_capabilities") or []),
        "exception_code": h.get("exception_code"),
        "exception_reason": h.get("exception_reason"),
        "history_count": len(h.get("history") or []) if isinstance(h.get("history"), list) else 0,
        "dependency_satisfied": bool(h.get("dependency_satisfied", False)),
        "evidence_link": h.get("evidence_link"),
        "source_resumed": bool(h.get("source_resumed", False)),
        "resumed_job_id": h.get("resumed_job_id"),
        "resolution_stage": h.get("resolution_stage"),
        "semantic_validation": h.get("semantic_validation"),
        "successor_status": h.get("successor_status"),
        "successor_certification": h.get("successor_certification"),
        "successor_evidence_link": h.get("successor_evidence_link"),
        "requires_human_intervention": bool(h.get("requires_human_intervention", False)),
        "human_intervention_reason": h.get("human_intervention_reason"),
        "grants_target_permissions": False,
        "updated_at_utc": h.get("updated_at_utc"),
        "production_touched": False,
    }


def summarize_handoffs_for_domain(
    domain: str,
    *,
    state_root: Path | None = None,
) -> dict[str, Any]:
    """Read-only cross-domain handoff summary exposed inside get_go_context (Fase 4)."""
    qroot = state_root or _default_state_root()
    dom = _clean(domain).upper()
    all_items = list_handoffs(state_root=qroot)

    outgoing: list[dict[str, Any]] = []
    incoming: list[dict[str, Any]] = []
    satisfied_resolutions: list[dict[str, Any]] = []
    unsatisfied_dependencies: list[dict[str, Any]] = []

    for item in all_items:
        src = _clean(item.get("source_domain")).upper()
        tgt = _clean(item.get("target_domain")).upper()
        state = _clean(item.get("lifecycle_state")).upper()
        view = _compact_handoff_view(item)

        if src == dom:
            outgoing.append(view)
            if state == "RETURNED_TO_SOURCE" and view["dependency_satisfied"] and view["certification"] in TERMINAL_CERTIFICATIONS:
                satisfied_resolutions.append({
                    "handoff_id": view["handoff_id"],
                    "dependency_id": view["dependency_id"],
                    "target_domain": tgt,
                    "resolution_job_id": view["resolution_job_id"],
                    "certification": view["certification"],
                    "evidence_link": view["evidence_link"],
                    "source_resumed": view["source_resumed"],
                    "resumed_job_id": view["resumed_job_id"],
                    "next_allowed_action": "CONTINUE_AUTONOMOUS",
                    "production_touched": False,
                })
            elif not view["dependency_satisfied"]:
                unsatisfied_dependencies.append({
                    "handoff_id": view["handoff_id"],
                    "dependency_id": view["dependency_id"],
                    "target_domain": tgt,
                    "lifecycle_state": state,
                    "resolution_job_id": view["resolution_job_id"],
                    "resolution_stage": view.get("resolution_stage"),
                    "exception_code": view.get("exception_code"),
                    "semantic_validation": view.get("semantic_validation"),
                    "evidence_link": view.get("evidence_link"),
                    "next_allowed_action": view["next_allowed_action"],
                    "requires_human_intervention": view["requires_human_intervention"],
                })
        elif tgt == dom:
            incoming.append(view)

    return {
        "schema": "edarsahub.worker-go-context-handoffs.v1",
        "domain": dom,
        "outgoing_handoffs": outgoing,
        "incoming_handoffs": incoming,
        "satisfied_resolutions": satisfied_resolutions,
        "unsatisfied_dependencies": unsatisfied_dependencies,
        "counts": {
            "outgoing": len(outgoing),
            "incoming": len(incoming),
            "satisfied_resolutions": len(satisfied_resolutions),
            "unsatisfied_dependencies": len(unsatisfied_dependencies),
        },
        "production_touched": False,
    }


def check_gate_handoff_dependencies(
    gate: Mapping[str, Any],
    *,
    state_root: Path | None = None,
) -> dict[str, Any]:
    """Read-only check used by Gate Chain Orchestrator to distinguish in-flight WAIT vs no-executor STOP."""
    req_ids = [
        _clean(x)
        for x in (gate.get("required_handoff_ids") or gate.get("handoff_dependency_ids") or ())
        if _clean(x)
    ]
    if not req_ids:
        return {
            "satisfied": True,
            "has_unexecutable_dependencies": False,
            "missing_or_pending": [],
            "unexecutable_handoffs": [],
            "satisfied_handoffs": [],
            "production_touched": False,
        }

    qroot = state_root or _default_state_root()
    all_items = list_handoffs(state_root=qroot)
    by_hid = {_clean(h.get("handoff_id")): h for h in all_items}
    by_dep = {_clean(h.get("dependency_id")): h for h in all_items}

    missing: list[dict[str, Any]] = []
    unexecutable: list[dict[str, Any]] = []
    satisfied: list[str] = []
    for ref in req_ids:
        doc = by_hid.get(ref) or by_dep.get(ref)
        if (
            isinstance(doc, dict)
            and _clean(doc.get("lifecycle_state")).upper() == "RETURNED_TO_SOURCE"
            and doc.get("dependency_satisfied") is True
            and _clean(doc.get("certification")).upper() in TERMINAL_CERTIFICATIONS
        ):
            satisfied.append(_clean(doc.get("handoff_id")))
        else:
            st = _clean(doc.get("lifecycle_state")).upper() if isinstance(doc, dict) else "NOT_FOUND"
            res_jid = _clean(doc.get("resolution_job_id")) if isinstance(doc, dict) else ""
            has_exec = (
                bool(res_jid)
                or (
                    isinstance(doc, dict)
                    and st == "CLASSIFIED"
                    and doc.get("auto_dispatch") is True
                    and doc.get("has_executor") is True
                )
            )
            entry = {
                "ref": ref,
                "lifecycle_state": st,
                "resolution_job_id": res_jid or None,
                "has_executor": has_exec,
                "executor_status": (
                    doc.get("executor_status")
                    if isinstance(doc, dict) and doc.get("executor_status")
                    else ("IN_FLIGHT_JOB" if res_jid else ("NOT_FOUND" if doc is None else "UNASSIGNED_NO_EXECUTOR"))
                ),
                "exception_code": doc.get("exception_code") if isinstance(doc, dict) else "HANDOFF_NOT_FOUND",
                "next_allowed_action": (
                    doc.get("next_allowed_action")
                    if isinstance(doc, dict)
                    else "REGISTER_HANDOFF"
                ),
            }
            missing.append(entry)
            if not has_exec or st in EXCEPTION_HANDOFF_STATES or st == "NOT_FOUND":
                unexecutable.append(entry)

    return {
        "satisfied": len(missing) == 0,
        "has_unexecutable_dependencies": len(unexecutable) > 0,
        "missing_or_pending": missing,
        "unexecutable_handoffs": unexecutable,
        "satisfied_handoffs": satisfied,
        "production_touched": False,
    }


def build_control_center_handoffs_summary(
    *,
    state_root: Path | None = None,
    domain: str | None = None,
    state: str | None = None,
    allowed_domains: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Fase 6: Read-only Control Center dossier of handoffs, dependencies, owners, resolutions, and exceptions."""
    qroot = state_root or _default_state_root()
    all_items = list_handoffs(state_root=qroot)

    dom_filter = _clean(domain).upper() or None
    state_filter = _clean(state).upper() or None
    allowed_set = (
        {_clean(d).upper() for d in allowed_domains if _clean(d)}
        if allowed_domains is not None
        else None
    )

    filtered: list[dict[str, Any]] = []
    for item in all_items:
        src = _clean(item.get("source_domain")).upper()
        tgt = _clean(item.get("target_domain")).upper()
        st = _clean(item.get("lifecycle_state")).upper()
        if allowed_set is not None and "*" not in allowed_set:
            if src not in allowed_set and tgt not in allowed_set:
                continue
        if dom_filter and src != dom_filter and tgt != dom_filter:
            continue
        if state_filter and st != state_filter:
            continue
        filtered.append(_compact_handoff_view(item))

    dependencies: list[dict[str, Any]] = []
    owners_by_domain: dict[str, dict[str, Any]] = {}
    resolutions: list[dict[str, Any]] = []
    exceptions: list[dict[str, Any]] = []
    human_required: list[dict[str, Any]] = []

    for view in filtered:
        tgt = str(view["target_domain"])
        st = str(view["lifecycle_state"])
        owner_bucket = owners_by_domain.setdefault(
            tgt,
            {"owner_domain": tgt, "active": 0, "resolved": 0, "exceptions": 0, "handoff_ids": []},
        )
        owner_bucket["handoff_ids"].append(view["handoff_id"])
        if st in ACTIVE_HANDOFF_STATES:
            owner_bucket["active"] += 1
        if st == "RETURNED_TO_SOURCE":
            owner_bucket["resolved"] += 1
            resolutions.append({
                "handoff_id": view["handoff_id"],
                "source_domain": view["source_domain"],
                "target_domain": tgt,
                "dependency_id": view["dependency_id"],
                "resolution_job_id": view["resolution_job_id"],
                "certification": view["certification"],
                "evidence_link": view["evidence_link"],
                "source_resumed": view["source_resumed"],
                "resumed_job_id": view["resumed_job_id"],
            })
        if st in EXCEPTION_HANDOFF_STATES:
            owner_bucket["exceptions"] += 1
            exceptions.append({
                "handoff_id": view["handoff_id"],
                "source_domain": view["source_domain"],
                "target_domain": tgt,
                "lifecycle_state": st,
                "classification": view["classification"],
                "executor_status": view["executor_status"],
                "exception_code": view["exception_code"],
                "exception_reason": view["exception_reason"],
                "requires_human_intervention": view["requires_human_intervention"],
                "human_intervention_reason": view["human_intervention_reason"],
            })
        if view["requires_human_intervention"] is True:
            human_required.append({
                "handoff_id": view["handoff_id"],
                "source_domain": view["source_domain"],
                "target_domain": tgt,
                "lifecycle_state": st,
                "reason": view["human_intervention_reason"] or view["classification"],
                "next_allowed_action": view["next_allowed_action"],
            })
        dependencies.append({
            "dependency_id": view["dependency_id"],
            "handoff_id": view["handoff_id"],
            "source_domain": view["source_domain"],
            "target_domain": tgt,
            "satisfied": view["dependency_satisfied"],
            "lifecycle_state": st,
            "resolution_job_id": view["resolution_job_id"],
        })

    return {
        "schema": SCHEMA_HANDOFF_OVERVIEW,
        "generated_at_utc": utc_now(),
        "total_handoffs": len(filtered),
        "counts": {
            "total": len(filtered),
            "active": sum(1 for v in filtered if v["lifecycle_state"] in ACTIVE_HANDOFF_STATES),
            "returned_certified": len(resolutions),
            "unsatisfied_dependencies": sum(1 for d in dependencies if not d["satisfied"]),
            "without_executor": sum(1 for v in filtered if v["lifecycle_state"] != "RETURNED_TO_SOURCE" and not v["has_executor"]),
            "exceptions": len(exceptions),
            "human_intervention_required": len(human_required),
        },
        "handoffs": filtered,
        "dependencies": dependencies,
        "owners_by_domain": [owners_by_domain[k] for k in sorted(owners_by_domain)],
        "resolutions": resolutions,
        "exceptions": exceptions,
        "human_intervention_required": human_required,
        "human_escalation_policy": "ONLY_WHEN_INDISPENSABLE",
        "production_touched": False,
    }
