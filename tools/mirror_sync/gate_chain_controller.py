#!/usr/bin/env python3
"""Deterministic, side-effect-free gate-chain state machine.

Foundation only: validates chain definitions and decides the next allowed
transition. It does not publish jobs, run Git commands or execute gates.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

TERMINAL_CERTIFICATIONS = {'CERTIFIED', 'CERTIFIED_READ_ONLY', 'CERTIFIED_OPERATIONAL'}
TERMINAL_STATUSES = {'INTEGRATED', 'READ_ONLY_COMPLETE', 'OPERATIONAL_COMPLETE'}
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

def decide_next(chain: dict[str, Any], *, completed_results: Iterable[dict[str, Any]], existing_job_ids: Iterable[str], hop_count: int, authorization_classes: Iterable[str] = ()) -> TransitionDecision:
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
        start_id = _text(chain['start_gate_id'])
        start_job = _text(gates[start_id].get('job_id'))
        if start_job in existing:
            return TransitionDecision('WAIT', chain_id, None, start_id, 'START_JOB_ALREADY_EXISTS')
        return TransitionDecision('READY', chain_id, None, start_id, 'START_GATE_DECLARED')
    next_ids = list(current_gate.get('next_gate_ids') or [])
    if not next_ids:
        return TransitionDecision('COMPLETE', chain_id, current_gate_id, None, 'CHAIN_TERMINAL_GATE')
    if len(next_ids) != 1:
        return TransitionDecision('STOP', chain_id, current_gate_id, None, 'AMBIGUOUS_NEXT_GATE')
    next_gate_id = next_ids[0]
    next_gate = gates[next_gate_id]
    next_job_id = _text(next_gate.get('job_id'))
    if next_job_id in existing or next_job_id in results_by_job:
        return TransitionDecision('WAIT', chain_id, current_gate_id, next_gate_id, 'NEXT_JOB_ALREADY_EXISTS')
    mutation = _text(next_gate.get('mutation_class') or 'READ_ONLY')
    required_auth = _text(next_gate.get('authorization_class'))
    if mutation == 'PRODUCTION':
        return TransitionDecision('STOP', chain_id, current_gate_id, next_gate_id, 'PRODUCTION_FORBIDDEN')
    if required_auth and required_auth not in authorized:
        return TransitionDecision('STOP', chain_id, current_gate_id, next_gate_id, 'AUTHORIZATION_REQUIRED')
    if next_gate.get('requires_human_decision') is True:
        return TransitionDecision('STOP', chain_id, current_gate_id, next_gate_id, 'HUMAN_DECISION_REQUIRED')
    return TransitionDecision('READY', chain_id, current_gate_id, next_gate_id, 'DECLARED_TRANSITION_READY')
