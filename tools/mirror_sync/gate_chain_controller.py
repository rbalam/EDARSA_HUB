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
