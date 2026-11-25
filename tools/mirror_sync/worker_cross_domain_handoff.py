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
    is_admin = bool(roles & _ADMIN_ROLES) or bool(perms & {"rbac_admin", "*"})
    return roles, perms, is_admin


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

    # 3. Direct scan of certified results in target_domain matching profile_code / pytest suite
    if requested_capability in {"SQL_READONLY_PROFILE_AUDIT", "WORKER_PYTEST_CERTIFICATION_READONLY"}:
        results_dir = state_root / "results"
        if results_dir.is_dir():
            target_profile = _clean(requested_constraints.get("profile_code")).upper()
            for res_path in sorted(results_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
                jid = res_path.stem
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


def _is_reusable_capability_available(
    *,
    target_domain: str,
    requested_capability: str | None,
    requested_constraints: Mapping[str, Any],
    incident_id: str | None,
) -> tuple[bool, str | None]:
    """Check existing Capability Registry & Knowledge Loop for reusable resolution capabilities."""
    cap_code = _clean(requested_capability).upper()
    if cap_code and cap_code in SAFE_REUSABLE_READONLY_CAPABILITIES:
        try:
            from modules.worker_ingress import semantic_capabilities as sem_caps

            cap = sem_caps.resolve_capability(cap_code)
            if cap.builder is not None:
                mode = "READ_ONLY_SQL" if "READ_ONLY_SQL" in cap.modes else "READ_ONLY"
                # Dry-run capability builder to confirm target_domain + constraints satisfy contract
                cap.builder({
                    "objective": "Dry-run reusable capability check",
                    "bounded_context": target_domain,
                    "mode": mode,
                    "capability": cap_code,
                    "constraints": dict(requested_constraints),
                })
                return True, cap_code
        except Exception:
            return False, None

    if target_domain in WORKER_INFRA_DOMAINS and incident_id:
        try:
            learned = learned_registry.resolve_learned_capability(incident_id=incident_id)
            if learned is not None and learned.reusable:
                return True, learned.code
        except Exception:
            pass
    return False, None


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
            "production_touched": False,
        }

    # 3. Reusable capability available (takes precedence when caller explicitly names a safe READ_ONLY capability)
    reusable_ok, reusable_code = _is_reusable_capability_available(
        target_domain=target_domain,
        requested_capability=requested_capability,
        requested_constraints=requested_constraints,
        incident_id=incident_id,
    )
    if reusable_ok and requested_capability in SAFE_REUSABLE_READONLY_CAPABILITIES:
        return {
            "schema": SCHEMA_HANDOFF_CLASSIFICATION,
            "classification": "REUSABLE_CAPABILITY_AVAILABLE",
            "reason": f"REUSABLE_CAPABILITY_MATCHED:{reusable_code}",
            "reusable_capability": reusable_code,
            "resolution_job_id": None,
            "lifecycle_state": "CLASSIFIED",
            "next_allowed_action": "SUBMIT_TARGET_RESOLUTION",
            "requires_human_intervention": False,
            "dispatch_eligible": True,
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
            "next_allowed_action": "RECOVER_EXISTING_CAPABILITY",
            "requires_human_intervention": False,
            "dispatch_eligible": True,
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
            "next_allowed_action": "SUBMIT_TARGET_RESOLUTION",
            "requires_human_intervention": False,
            "dispatch_eligible": True,
            "production_touched": False,
        }

    # 5. Mutation / privileged request requires explicit independent target_domain authorization & policy
    if handoff_mode == "MUTATION" or requested_capability in {"DEVELOPMENT_MUTATION_BOUNDED", "COA_FISCAL_STATUS_SEED_DEVELOPMENT"}:
        # Never shift functional business development into Worker infrastructure domains!
        if target_domain in WORKER_INFRA_DOMAINS and requested_capability == "DEVELOPMENT_MUTATION_BOUNDED":
            # Ensure target_domain independently holds valid materialized authorization
            pass
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
                "production_touched": False,
            }
        return {
            "schema": SCHEMA_HANDOFF_CLASSIFICATION,
            "classification": "TARGET_BOUNDED_CONTEXT_REQUIRED",
            "reason": "TARGET_BOUNDED_CONTEXT_OWNED_MUTATION",
            "policy_decision": policy_decision,
            "resolution_job_id": None,
            "lifecycle_state": "QUEUED_IN_TARGET_DOMAIN",
            "next_allowed_action": "WAIT_FOR_IN_FLIGHT_JOB",
            "requires_human_intervention": False,
            "dispatch_eligible": False,
            "production_touched": False,
        }

    # 6. Functional/domain work owned by another bounded context (never moved to Worker)
    return {
        "schema": SCHEMA_HANDOFF_CLASSIFICATION,
        "classification": "TARGET_BOUNDED_CONTEXT_REQUIRED",
        "reason": f"BOUNDED_CONTEXT_OWNER_REQUIRED:{target_domain}",
        "resolution_job_id": None,
        "lifecycle_state": "QUEUED_IN_TARGET_DOMAIN",
        "next_allowed_action": "WAIT_FOR_IN_FLIGHT_JOB",
        "requires_human_intervention": False,
        "dispatch_eligible": False,
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
    dependency_id = (
        _validate_optional_token(constraints.get("dependency_id"), field_name="dependency_id", job_id_style=False)
        or f"DEP-{handoff_id}"
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

    existing = load_handoff(handoff_id, state_root=qroot)
    if existing is not None:
        if _clean(existing.get("payload_fingerprint")) != fingerprint:
            raise HandoffConflictError("IDEMPOTENCY_CONFLICT")
        return {
            "duplicate": True,
            "existing_handoff": existing,
            "handoff_id": handoff_id,
            "dependency_id": dependency_id,
            "source_domain": source_domain,
            "target_domain": target_domain,
            "request_key": request_key,
            "payload_fingerprint": fingerprint,
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

    auto_dispatch = bool(constraints.get("auto_dispatch", True))
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
        "payload_fingerprint": fingerprint,
        "dependency_satisfied": False,
        "evidence_link": None,
        "source_resumed": False,
        "resumed_job_id": None,
        "requires_human_intervention": False,
        "human_intervention_reason": None,
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
) -> dict[str, Any] | None:
    """Build one canonical edarsahub.worker-job.v2 envelope for reusable READ_ONLY capability dispatch."""
    cap_code = _clean(handoff.get("requested_capability")).upper()
    if cap_code not in SAFE_REUSABLE_READONLY_CAPABILITIES:
        return None
    from modules.worker_ingress import semantic_capabilities as sem_caps
    from modules.worker_ingress import service as ingress_service

    cap = sem_caps.resolve_capability(cap_code)
    if cap.builder is None:
        return None
    mode = "READ_ONLY_SQL" if "READ_ONLY_SQL" in cap.modes else "READ_ONLY"
    actor = dict(current_user) if isinstance(current_user, Mapping) else {
        "email": _clean(handoff.get("requester_email")) or "worker@edarsahub.local",
        "role": "SUPERADMIN",
        "permissions": ["*"],
    }
    if not _clean(actor.get("email")):
        actor["email"] = _clean(handoff.get("requester_email")) or "worker@edarsahub.local"

    req = {
        "objective": (
            f"[HANDOFF {handoff['handoff_id']} {handoff['source_domain']}->{handoff['target_domain']}] "
            f"{handoff['source_objective']}"
        )[:3900],
        "bounded_context": _clean(handoff.get("target_domain")).upper(),
        "mode": mode,
        "capability": cap_code,
        "request_key": f"handoff-{handoff['handoff_id']}",
        "constraints": dict(handoff.get("requested_constraints") or {}),
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
    submit_fn: Any = None,
    now_epoch: float | None = None,
) -> dict[str, Any]:
    """Publish resolution work exclusively via gate_chain_publisher.submit() with backoff & circuit breaker."""
    qroot = state_root or _default_state_root()
    hid = _clean(handoff.get("handoff_id"))
    now_ts = float(now_epoch if now_epoch is not None else time.time())
    cb_dir = qroot / "maintenance" / "circuit_breakers"
    cb_key = f"handoff_dispatch:{hid[:64]}"

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
        handoff["updated_at_utc"] = utc_now()
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
                    save_handoff(handoff, state_root=qroot)
                    return {"dispatched": False, "status": "RECOVERY_DEFERRED_CONNECTIVITY", "handoff": handoff, "production_touched": False}
                if rec.get("resumed") is True:
                    auto_loop.record_circuit_outcome(cb_key, certified_success=True, now_epoch=now_ts, state_dir=cb_dir)
                    handoff["resolution_job_id"] = rec.get("resume_job_id")
                    handoff["lifecycle_state"] = "IN_PROGRESS"
                    handoff["next_allowed_action"] = "WAIT_FOR_IN_FLIGHT_JOB"
                    handoff["dispatch_attempts"] = int(handoff.get("dispatch_attempts") or 0) + 1
                    handoff["updated_at_utc"] = utc_now()
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
                handoff["next_allowed_action"] = "HUMAN_APPROVAL_REQUIRED" if handoff["lifecycle_state"] == "WAITING_AUTHORIZATION" else "WAIT_FOR_IN_FLIGHT_JOB"
                handoff["requires_human_intervention"] = handoff["lifecycle_state"] == "WAITING_AUTHORIZATION"
                handoff["human_intervention_reason"] = str(rec.get("reason") or "") if handoff["requires_human_intervention"] else None
                handoff["updated_at_utc"] = utc_now()
                save_handoff(handoff, state_root=qroot)
                return {"dispatched": False, "status": str(rec.get("action") or "DEFERRED"), "handoff": handoff, "production_touched": False}

    # Path B: Reusable certified READ_ONLY / READ_ONLY_SQL capability
    canonical_job = _build_dispatch_job_for_handoff(handoff, current_user=current_user)
    if canonical_job is None:
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
        save_handoff(handoff, state_root=qroot)
        return {"dispatched": False, "status": "DISPATCH_ERROR_BACKOFF", "handoff": handoff, "production_touched": False}

    pub_status = _clean((pub_out or {}).get("status")).upper()
    pub_job_id = _clean((pub_out or {}).get("job_id")) or canonical_job["job_id"]
    if pub_status in {"SUBMITTED", "ALREADY_SUBMITTED", "PUBLISHED", "EXISTS", "ALREADY_PROCESSING", "ALREADY_COMPLETED"}:
        auto_loop.record_circuit_outcome(cb_key, certified_success=True, now_epoch=now_ts, state_dir=cb_dir)
        handoff["resolution_job_id"] = pub_job_id
        handoff["dispatch_attempts"] = int(handoff.get("dispatch_attempts") or 0) + 1
        handoff["publication_channel"] = "gate_chain_publisher.submit"
        handoff["lifecycle_state"] = "IN_PROGRESS"
        handoff["next_allowed_action"] = "WAIT_FOR_IN_FLIGHT_JOB"
        handoff["updated_at_utc"] = utc_now()
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
    save_handoff(handoff, state_root=qroot)
    return {"dispatched": False, "status": pub_status or "DISPATCH_REJECTED", "handoff": handoff, "production_touched": False}


def return_certified_handoff_to_source(
    handoff: dict[str, Any],
    *,
    certified_evidence: Mapping[str, Any],
    state_root: Path | None = None,
    repo_root: Path | None = None,
    submit_fn: Any = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Fase 4: Link certified terminal evidence, satisfy dependency, and auto-resume authorized work."""
    qroot = state_root or _default_state_root()
    cert = _clean(certified_evidence.get("certification")).upper()
    if cert not in TERMINAL_CERTIFICATIONS or certified_evidence.get("production_touched") is not False:
        raise HandoffSecurityError("HANDOFF_TERMINAL_CERTIFICATION_INVALID")

    now_str = utc_now()
    handoff["resolution_job_id"] = _clean(certified_evidence.get("job_id")) or handoff.get("resolution_job_id")
    handoff["certification"] = cert
    handoff["dependency_satisfied"] = True
    handoff["lifecycle_state"] = "RETURNED_TO_SOURCE"
    handoff["next_allowed_action"] = "CONTINUE_AUTONOMOUS"
    handoff["requires_human_intervention"] = False
    handoff["human_intervention_reason"] = None
    handoff["resolved_at_utc"] = handoff.get("resolved_at_utc") or now_str
    handoff["returned_at_utc"] = now_str
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
        "acceptance_criteria_verified": True,
        "production_touched": False,
    }

    # Auto-resume previously authorized source_job_id once without asking for another GO
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
                    handoff["second_go_required"] = False

    save_handoff(handoff, state_root=qroot)
    return handoff


def register_cross_domain_handoff(
    request: Mapping[str, Any],
    *,
    current_user: Mapping[str, Any] | None = None,
    requester: Mapping[str, Any] | None = None,
    state_root: Path | None = None,
    repo_root: Path | None = None,
    submit_fn: Any = None,
    now_utc: datetime | None = None,
    now_epoch: float | None = None,
) -> dict[str, Any]:
    """Fase 2 & 3 entry point: validate, persist atomically, classify, and optionally dispatch/return."""
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

    if validated.get("duplicate") is True:
        existing = dict(validated["existing_handoff"])
        return {
            "status": "EXISTS",
            "duplicate_prevented": True,
            "handoff_id": existing["handoff_id"],
            "job_id": existing.get("resolution_job_id") or existing["handoff_id"],
            "dependency_id": existing["dependency_id"],
            "source_domain": existing["source_domain"],
            "target_domain": existing["target_domain"],
            "classification": existing.get("classification"),
            "lifecycle_state": existing.get("lifecycle_state"),
            "certification": existing.get("certification"),
            "next_allowed_action": existing.get("next_allowed_action"),
            "production_touched": False,
            "handoff": existing,
        }

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
    if cls.get("resolution_job_id"):
        handoff["resolution_job_id"] = cls["resolution_job_id"]

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
            submit_fn=submit_fn,
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
        "handoff_id": handoff["handoff_id"],
        "job_id": handoff.get("resolution_job_id") or handoff["handoff_id"],
        "dependency_id": handoff["dependency_id"],
        "source_domain": handoff["source_domain"],
        "target_domain": handoff["target_domain"],
        "classification": handoff["classification"],
        "lifecycle_state": handoff["lifecycle_state"],
        "certification": handoff["certification"],
        "next_allowed_action": handoff["next_allowed_action"],
        "production_touched": False,
        "handoff": handoff,
    }


def reconcile_cross_domain_handoffs(
    *,
    state_root: Path | None = None,
    repo_root: Path | None = None,
    max_dispatches: int = MAX_HANDOFF_DISPATCHES_PER_CYCLE,
    submit_fn: Any = None,
    now_utc: datetime | None = None,
    now_epoch: float | None = None,
) -> dict[str, Any]:
    """Periodic Control Plane reconciliation: certify returns, unblock dependencies, dispatch eligible work."""
    qroot = state_root or _default_state_root()
    handoffs = list_handoffs(state_root=qroot)
    returned_ids: list[str] = []
    dispatched_ids: list[str] = []
    reclassified_ids: list[str] = []
    errors: list[dict[str, str]] = []
    dispatches_left = max(0, int(max_dispatches))

    for record in handoffs:
        hid = _clean(record.get("handoff_id"))
        state = _clean(record.get("lifecycle_state")).upper()
        if state in {"RETURNED_TO_SOURCE", "BLOCKED_CYCLE", "BLOCKED_POLICY"}:
            continue
        try:
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
                        now_utc=now_utc,
                    )
                    returned_ids.append(hid)
                    continue

            # 2. Re-classify open handoffs to detect newly certified results or newly materialized auth
            cls = classify_handoff_request(
                record,
                state_root=qroot,
                existing_handoffs=handoffs,
                now_utc=now_utc,
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
                    now_utc=now_utc,
                )
                returned_ids.append(hid)
                continue

            if cls["classification"] != record.get("classification") or cls["lifecycle_state"] != state:
                record["classification"] = cls["classification"]
                record["classification_reason"] = cls["reason"]
                record["lifecycle_state"] = cls["lifecycle_state"]
                record["next_allowed_action"] = cls["next_allowed_action"]
                record["requires_human_intervention"] = bool(cls.get("requires_human_intervention", False))
                record["human_intervention_reason"] = cls.get("human_intervention_reason")
                if cls.get("resolution_job_id"):
                    record["resolution_job_id"] = cls["resolution_job_id"]
                record["updated_at_utc"] = utc_now()
                save_handoff(record, state_root=qroot)
                reclassified_ids.append(hid)

            # 3. Dispatch eligible work within per-cycle budget
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
                    submit_fn=submit_fn,
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
        "returned_this_cycle": returned_ids,
        "dispatched_this_cycle": dispatched_ids,
        "reclassified_this_cycle": reclassified_ids,
        "isolated_errors": errors,
        "production_touched": False,
    }


def _compact_handoff_view(h: Mapping[str, Any]) -> dict[str, Any]:
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
        "acceptance_criteria": list(h.get("acceptance_criteria") or []),
        "resolution_job_id": h.get("resolution_job_id"),
        "certification": h.get("certification"),
        "lifecycle_state": h.get("lifecycle_state"),
        "next_allowed_action": h.get("next_allowed_action"),
        "classification": h.get("classification"),
        "dependency_satisfied": bool(h.get("dependency_satisfied", False)),
        "evidence_link": h.get("evidence_link"),
        "source_resumed": bool(h.get("source_resumed", False)),
        "resumed_job_id": h.get("resumed_job_id"),
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
    """Read-only check used by Gate Chain Orchestrator to block transitions with unsatisfied handoffs."""
    req_ids = [
        _clean(x)
        for x in (gate.get("required_handoff_ids") or gate.get("handoff_dependency_ids") or ())
        if _clean(x)
    ]
    if not req_ids:
        return {"satisfied": True, "missing_or_pending": [], "satisfied_handoffs": [], "production_touched": False}

    qroot = state_root or _default_state_root()
    all_items = list_handoffs(state_root=qroot)
    by_hid = {_clean(h.get("handoff_id")): h for h in all_items}
    by_dep = {_clean(h.get("dependency_id")): h for h in all_items}

    missing: list[dict[str, Any]] = []
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
            missing.append({
                "ref": ref,
                "lifecycle_state": _clean(doc.get("lifecycle_state")).upper() if isinstance(doc, dict) else "NOT_FOUND",
                "resolution_job_id": doc.get("resolution_job_id") if isinstance(doc, dict) else None,
            })

    return {
        "satisfied": len(missing) == 0,
        "missing_or_pending": missing,
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
