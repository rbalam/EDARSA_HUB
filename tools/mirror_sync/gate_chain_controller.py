#!/usr/bin/env python3
"""Deterministic, side-effect-free gate-chain state machine.

Foundation only: validates chain definitions and decides the next allowed
transition. It does not publish jobs, run Git commands or execute gates.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Iterable, Mapping

TERMINAL_CERTIFICATIONS = {'CERTIFIED', 'CERTIFIED_READ_ONLY', 'CERTIFIED_OPERATIONAL', 'CERTIFIED_FRONTEND_BUILD'}
TERMINAL_STATUSES = {'INTEGRATED', 'READ_ONLY_COMPLETE', 'OPERATIONAL_COMPLETE', 'FRONTEND_BUILD_CERTIFIED'}
MUTATION_CLASSES = {'READ_ONLY', 'CODE_MUTATION', 'SQL_DML', 'SQL_DDL', 'PRODUCTION'}

class GateChainContractError(ValueError):
    pass

@dataclass(frozen=True)
class TransitionDecision:
    action: str
    chain_id: str
    current_gate_id: str | None
    next_gate_id: str | None
    reason: str
    decision_digest: str = ''

def _text(value: Any) -> str:
    return str(value or '').strip()

def _gate_map(chain: dict[str, Any]) -> dict[str, dict[str, Any]]:
    gates = chain.get('gates')
    if not isinstance(gates, list) or not gates:
        raise GateChainContractError('GATES_REQUIRED')
    result: dict[str, dict[str, Any]] = {}
    for gate in gates:
        if not isinstance(gate, dict):
            raise GateChainContractError('GATE_NOT_OBJECT')
        gate_id = _text(gate.get('gate_id'))
        if not gate_id:
            raise GateChainContractError('GATE_ID_REQUIRED')
        if gate_id in result:
            raise GateChainContractError(f'DUPLICATE_GATE_ID:{gate_id}')
        mutation = _text(gate.get('mutation_class') or 'READ_ONLY')
        if mutation not in MUTATION_CLASSES:
            raise GateChainContractError(f'INVALID_MUTATION_CLASS:{gate_id}')
        result[gate_id] = gate
    return result

def validate_chain(chain: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(chain, dict):
        raise GateChainContractError('CHAIN_NOT_OBJECT')
    if _text(chain.get('schema')) != 'edarsahub.gate-chain.v1':
        raise GateChainContractError('INVALID_SCHEMA')
    if not _text(chain.get('chain_id')):
        raise GateChainContractError('CHAIN_ID_REQUIRED')
    max_hops = chain.get('max_hops')
    if not isinstance(max_hops, int) or max_hops < 1 or max_hops > 1000:
        raise GateChainContractError('INVALID_MAX_HOPS')
    gates = _gate_map(chain)
    start = _text(chain.get('start_gate_id'))
    if start not in gates:
        raise GateChainContractError('INVALID_START_GATE')
    for gate_id, gate in gates.items():
        next_ids = gate.get('next_gate_ids', [])
        if not isinstance(next_ids, list) or not all(isinstance(x, str) and x.strip() for x in next_ids):
            raise GateChainContractError(f'INVALID_NEXT_GATE_IDS:{gate_id}')
        for next_id in next_ids:
            if next_id not in gates:
                raise GateChainContractError(f'UNKNOWN_NEXT_GATE:{gate_id}:{next_id}')
        if len(next_ids) > 1 and not gate.get('transition_key'):
            raise GateChainContractError(f'AMBIGUOUS_TRANSITION_REQUIRES_KEY:{gate_id}')
    return chain

def _result_ok(result: dict[str, Any]) -> bool:
    return (_text(result.get('status')).upper() in TERMINAL_STATUSES and _text(result.get('certification')).upper() in TERMINAL_CERTIFICATIONS and _text(result.get('quality_gate')).upper() == 'PASS' and _text(result.get('tests')).upper() == 'PASS' and result.get('production_touched') is False and not (result.get('blockers') or []))

def _parse_utc(value: Any) -> datetime | None:
    raw = _text(value)
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _norm_set(value: Any) -> set[str]:
    if isinstance(value, (list, tuple, set, frozenset)):
        return {_text(x) for x in value if _text(x)}
    text = _text(value)
    return {text} if text else set()


def _decision_digest(
    *,
    chain_id: str,
    gate_id: str,
    gate: Mapping[str, Any],
    authorized: Iterable[str],
) -> str:
    payload = {
        'chain_id': _text(chain_id),
        'gate_id': _text(gate_id),
        'job_id': _text(gate.get('job_id')),
        'mutation_class': _text(gate.get('mutation_class') or 'READ_ONLY'),
        'authorization_class': _text(gate.get('authorization_class')),
        'requires_human_decision': bool(gate.get('requires_human_decision') is True),
        'production_allowed': bool(gate.get('production_allowed') is True),
        'authorized_classes': sorted({_text(x) for x in authorized if _text(x)}),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def evaluate_gate_authorization(
    gate: Mapping[str, Any],
    *,
    authorization_classes: Iterable[str] = (),
    authorization_context: Mapping[str, Any] | None = None,
    now_utc: datetime | None = None,
) -> tuple[bool, str]:
    """Shared fail-closed authorization check applied equally to start and subsequent gates."""
    mutation = _text(gate.get('mutation_class') or 'READ_ONLY').upper()
    if mutation not in MUTATION_CLASSES:
        return False, 'INVALID_MUTATION_CLASS'
    if mutation == 'PRODUCTION':
        return False, 'PRODUCTION_FORBIDDEN'
    if gate.get('production_allowed') is True:
        return False, 'PRODUCTION_FORBIDDEN'
    template = gate.get('job_template')
    if isinstance(template, Mapping) and template.get('production_allowed') is True:
        return False, 'PRODUCTION_FORBIDDEN'
    if gate.get('requires_human_decision') is True:
        return False, 'HUMAN_DECISION_REQUIRED'

    authorized = {_text(x) for x in authorization_classes if _text(x)}
    required_auth = _text(gate.get('authorization_class'))
    if required_auth and required_auth not in authorized:
        return False, 'AUTHORIZATION_REQUIRED'

    ctx = authorization_context if isinstance(authorization_context, Mapping) else None
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    # Traceable & time-bounded authorization checks (enforced when context is provided or gate requires traceability)
    require_trace = bool(gate.get('require_traceable_authorization') is True)
    if require_trace and ctx is None:
        return False, 'AUTHORIZATION_NOT_TRACEABLE'

    if ctx is not None:
        if ctx.get('revoked') is True:
            return False, 'AUTHORIZATION_REVOKED'
        if require_trace and not _text(ctx.get('authorization_id')):
            return False, 'AUTHORIZATION_NOT_TRACEABLE'
        expires_raw = ctx.get('expires_at_utc')
        if expires_raw is not None:
            expires_dt = _parse_utc(expires_raw)
            if expires_dt is None or expires_dt <= now:
                return False, 'AUTHORIZATION_EXPIRED'

    # Effective RBAC checks (enforced when gate declares required_rbac)
    required_rbac = gate.get('required_rbac')
    if isinstance(required_rbac, Mapping) and required_rbac:
        if ctx is None:
            return False, 'RBAC_AUTHORIZATION_DENIED'
        req_roles = {r.lower() for r in _norm_set(required_rbac.get('roles'))}
        req_perms = {p.lower() for p in _norm_set(required_rbac.get('permissions'))}
        actor_roles = {r.lower() for r in _norm_set(ctx.get('actor_roles') or ctx.get('actor_role'))}
        actor_perms = {p.lower() for p in _norm_set(ctx.get('actor_permissions'))}
        if req_roles and not (req_roles & actor_roles):
            return False, 'RBAC_AUTHORIZATION_DENIED'
        if req_perms and not req_perms.issubset(actor_perms):
            return False, 'RBAC_AUTHORIZATION_DENIED'

    # Scope checks: empresa, unidad_negocio_pk, domain (enforced when gate declares required_scope)
    required_scope = gate.get('required_scope')
    if isinstance(required_scope, Mapping) and required_scope:
        if ctx is None:
            return False, 'SCOPE_AUTHORIZATION_DENIED'
        granted_scope = ctx.get('scope') if isinstance(ctx.get('scope'), Mapping) else ctx
        for field in ('empresa_id', 'unidad_negocio_pk', 'domain'):
            req_vals = {v.lower() for v in _norm_set(required_scope.get(field))}
            if not req_vals:
                continue
            granted_vals = {v.lower() for v in _norm_set(granted_scope.get(field) or granted_scope.get(f'{field}s'))}
            if '*' in granted_vals:
                continue
            if not req_vals.issubset(granted_vals):
                return False, 'SCOPE_AUTHORIZATION_DENIED'

    return True, 'AUTHORIZED'


def decide_next(
    chain: dict[str, Any],
    *,
    completed_results: Iterable[dict[str, Any]],
    existing_job_ids: Iterable[str],
    hop_count: int,
    authorization_classes: Iterable[str] = (),
    authorization_context: Mapping[str, Any] | None = None,
    now_utc: datetime | None = None,
) -> TransitionDecision:
    validate_chain(chain)
    chain_id = _text(chain['chain_id'])
    gates = _gate_map(chain)
    if hop_count >= int(chain['max_hops']):
        return TransitionDecision('STOP', chain_id, None, None, 'MAX_HOPS_REACHED')
    results_by_job = {_text(item.get('job_id')): item for item in completed_results if isinstance(item, dict) and _text(item.get('job_id'))}
    existing = {_text(x) for x in existing_job_ids if _text(x)}
    authorized = {_text(x) for x in authorization_classes if _text(x)}
    current_gate_id = None
    current_gate = None
    for gate_id, gate in gates.items():
        job_id = _text(gate.get('job_id'))
        if job_id and job_id in results_by_job and _result_ok(results_by_job[job_id]):
            current_gate_id, current_gate = gate_id, gate

    if current_gate is None:
        target_gate_id = _text(chain['start_gate_id'])
        target_gate = gates[target_gate_id]
        target_job_id = _text(target_gate.get('job_id'))
        if target_job_id in existing or target_job_id in results_by_job:
            return TransitionDecision('WAIT', chain_id, None, target_gate_id, 'START_JOB_ALREADY_EXISTS')
        ready_reason = 'START_GATE_DECLARED'
    else:
        next_ids = list(current_gate.get('next_gate_ids') or [])
        if not next_ids:
            return TransitionDecision('COMPLETE', chain_id, current_gate_id, None, 'CHAIN_TERMINAL_GATE')
        if len(next_ids) != 1:
            return TransitionDecision('STOP', chain_id, current_gate_id, None, 'AMBIGUOUS_NEXT_GATE')
        target_gate_id = next_ids[0]
        target_gate = gates[target_gate_id]
        target_job_id = _text(target_gate.get('job_id'))
        if target_job_id in existing or target_job_id in results_by_job:
            return TransitionDecision('WAIT', chain_id, current_gate_id, target_gate_id, 'NEXT_JOB_ALREADY_EXISTS')
        ready_reason = 'DECLARED_TRANSITION_READY'

    ok, auth_reason = evaluate_gate_authorization(
        target_gate,
        authorization_classes=authorized,
        authorization_context=authorization_context,
        now_utc=now_utc,
    )
    if not ok:
        return TransitionDecision('STOP', chain_id, current_gate_id, target_gate_id, auth_reason)

    digest = _decision_digest(
        chain_id=chain_id,
        gate_id=target_gate_id,
        gate=target_gate,
        authorized=authorized,
    )
    return TransitionDecision('READY', chain_id, current_gate_id, target_gate_id, ready_reason, digest)


AUTONOMOUS_POLICY_SCHEMA = 'edarsahub.autonomous-execution-policy.v1'
POLICY_TIERS = ('READ_ONLY', 'DEVELOPMENT_MUTATION', 'HUMAN_APPROVAL_REQUIRED')
_HUMAN_APPROVAL_FLAGS = (
    'requires_human_decision',
    'touches_credentials',
    'destructive_operation',
    'irreversible_financial_operation',
    'personal_data_outside_scope',
    'unauthorized_business_change',
    'out_of_contract',
)


@dataclass(frozen=True)
class PolicyLimits:
    max_hops: int = 10
    max_retries_per_gate: int = 2
    max_parallelism: int = 1
    max_runtime_seconds: int = 600
    max_actions_per_job: int = 15
    max_files_per_job: int = 15
    circuit_breaker_threshold: int = 3

    def validated(self) -> 'PolicyLimits':
        if not 1 <= self.max_hops <= 100:
            raise GateChainContractError('POLICY_INVALID_MAX_HOPS')
        if not 0 <= self.max_retries_per_gate <= 3:
            raise GateChainContractError('POLICY_INVALID_MAX_RETRIES')
        if not 1 <= self.max_parallelism <= 4:
            raise GateChainContractError('POLICY_INVALID_MAX_PARALLELISM')
        if not 30 <= self.max_runtime_seconds <= 1800:
            raise GateChainContractError('POLICY_INVALID_MAX_RUNTIME')
        if not 1 <= self.max_actions_per_job <= 25:
            raise GateChainContractError('POLICY_INVALID_MAX_ACTIONS')
        if not 1 <= self.max_files_per_job <= 25:
            raise GateChainContractError('POLICY_INVALID_MAX_FILES')
        if not 1 <= self.circuit_breaker_threshold <= 5:
            raise GateChainContractError('POLICY_INVALID_CIRCUIT_BREAKER')
        return self


def classify_policy_tier(
    gate: Mapping[str, Any],
    *,
    template: Mapping[str, Any] | None = None,
) -> tuple[str, str]:
    """Classify a gate into READ_ONLY, DEVELOPMENT_MUTATION, or HUMAN_APPROVAL_REQUIRED."""
    mutation = _text(gate.get('mutation_class') or 'READ_ONLY').upper()
    if mutation == 'PRODUCTION' or gate.get('production_allowed') is True:
        return 'HUMAN_APPROVAL_REQUIRED', 'PRODUCTION_FORBIDDEN'
    if isinstance(template, Mapping) and template.get('production_allowed') is True:
        return 'HUMAN_APPROVAL_REQUIRED', 'PRODUCTION_FORBIDDEN'

    for flag in _HUMAN_APPROVAL_FLAGS:
        if gate.get(flag) is True:
            return 'HUMAN_APPROVAL_REQUIRED', flag.upper()

    if mutation in {'SQL_DML', 'SQL_DDL'}:
        return 'HUMAN_APPROVAL_REQUIRED', f'MUTATION_CLASS_REQUIRES_APPROVAL:{mutation}'

    effective_template = template if isinstance(template, Mapping) else gate.get('job_template')
    if isinstance(effective_template, Mapping):
        for action in effective_template.get('actions') or []:
            if isinstance(action, Mapping) and _text(action.get('type')).lower() == 'delete_file':
                return 'HUMAN_APPROVAL_REQUIRED', 'DESTRUCTIVE_ACTION_DELETE_FILE'

    if mutation == 'READ_ONLY':
        return 'READ_ONLY', 'TIER_READ_ONLY_ALLOWED'
    if mutation == 'CODE_MUTATION':
        return 'DEVELOPMENT_MUTATION', 'TIER_DEVELOPMENT_MUTATION_ALLOWED'
    return 'HUMAN_APPROVAL_REQUIRED', 'UNKNOWN_MUTATION_CLASS'


def evaluate_autonomous_policy(
    gate: Mapping[str, Any],
    *,
    limits: PolicyLimits | None = None,
    hop_count: int = 0,
    retry_count: int = 0,
    consecutive_failures: int = 0,
    elapsed_seconds: float = 0.0,
    cancel_requested: bool = False,
    authorization_classes: Iterable[str] = (),
    authorization_context: Mapping[str, Any] | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Evaluate edarsahub.autonomous-execution-policy.v1 fail-closed for one gate."""
    effective_limits = (limits or PolicyLimits()).validated()
    template = gate.get('job_template') if isinstance(gate.get('job_template'), Mapping) else None
    tier, tier_reason = classify_policy_tier(gate, template=template)

    allowed = False
    action = 'STOP'
    reason = tier_reason

    if cancel_requested:
        action, reason = 'CANCELLED_SAFELY', 'SAFE_CANCELLATION_REQUESTED'
    elif hop_count >= effective_limits.max_hops:
        action, reason = 'STOP', 'POLICY_MAX_HOPS_EXCEEDED'
    elif retry_count > effective_limits.max_retries_per_gate:
        action, reason = 'STOP', 'POLICY_RETRY_BUDGET_EXCEEDED'
    elif consecutive_failures >= effective_limits.circuit_breaker_threshold:
        action, reason = 'STOP', 'POLICY_CIRCUIT_BREAKER_OPEN'
    elif elapsed_seconds > effective_limits.max_runtime_seconds:
        action, reason = 'STOP', 'POLICY_TIMEOUT_EXCEEDED'
    elif tier == 'HUMAN_APPROVAL_REQUIRED':
        action, reason = 'STOP', f'HUMAN_APPROVAL_REQUIRED:{tier_reason}'
    else:
        auth_ok, auth_reason = evaluate_gate_authorization(
            gate,
            authorization_classes=authorization_classes,
            authorization_context=authorization_context,
            now_utc=now_utc,
        )
        if not auth_ok:
            action, reason = 'STOP', auth_reason
        else:
            if isinstance(template, Mapping):
                t_actions = list(template.get('actions') or [])
                touched_files = {
                    _text(a.get('path'))
                    for a in t_actions
                    if isinstance(a, Mapping) and _text(a.get('path'))
                }
                if len(t_actions) > effective_limits.max_actions_per_job:
                    action, reason = 'STOP', 'POLICY_MAX_ACTIONS_EXCEEDED'
                elif len(touched_files) > effective_limits.max_files_per_job:
                    action, reason = 'STOP', 'POLICY_MAX_FILES_EXCEEDED'
                else:
                    allowed, action, reason = True, 'ALLOW', tier_reason
            else:
                allowed, action, reason = True, 'ALLOW', tier_reason

    ts = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    return {
        'schema': AUTONOMOUS_POLICY_SCHEMA,
        'gate_id': _text(gate.get('gate_id')),
        'job_id': _text(gate.get('job_id')),
        'policy_tier': tier,
        'allowed': allowed,
        'action': action,
        'reason': reason,
        'retry_count': int(retry_count),
        'consecutive_failures': int(consecutive_failures),
        'rollback_eligible': tier == 'DEVELOPMENT_MUTATION',
        'safe_cancellation_supported': True,
        'limits': {
            'max_hops': effective_limits.max_hops,
            'max_retries_per_gate': effective_limits.max_retries_per_gate,
            'max_parallelism': effective_limits.max_parallelism,
            'max_runtime_seconds': effective_limits.max_runtime_seconds,
            'max_actions_per_job': effective_limits.max_actions_per_job,
            'max_files_per_job': effective_limits.max_files_per_job,
            'circuit_breaker_threshold': effective_limits.circuit_breaker_threshold,
        },
        'decided_at_utc': ts,
        'production_touched': False,
    }
