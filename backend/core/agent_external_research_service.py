from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from time import monotonic

from core.agent_capability_policy import PolicyContext, PolicyRequest
from core.agent_execution_gate import authorize_external_research_execution
from core.agent_reach_public_search_executor import AgentReachPublicSearchResult, execute_agent_reach_public_search
from core.agent_runtime_activation import RuntimeActivationMode, RuntimeActivationRequest, RuntimeEnvironment, authorize_runtime_activation

_MAX_OUTPUT_BYTES = 65536

@dataclass(frozen=True)
class ExternalResearchEvidence:
    allowed: bool
    success: bool
    reason: str
    procedure: str | None
    effective_scopes: tuple[str, ...]
    query_sha256: str
    external_calls_budget: int
    duration_ms: int
    stdout_bytes: int
    stderr_bytes: int
    returncode: int | None
    production_touched: bool = False

@dataclass(frozen=True)
class ExternalResearchExecution:
    result: AgentReachPublicSearchResult | None
    evidence: ExternalResearchEvidence

def execute_external_research(requester_authorization: object, query: str, request: PolicyRequest, context: PolicyContext, versions_lock_path: str | Path, *, environment: RuntimeEnvironment = RuntimeEnvironment.DEVELOPMENT, timeout_seconds: int = 20, docker_binary: str | None = None) -> ExternalResearchExecution:
    started = monotonic()
    query_hash = sha256(str(query).encode('utf-8')).hexdigest()
    gate = authorize_external_research_execution(requester_authorization, query, request, context)
    if not gate.allowed or gate.downstream is None:
        reason = gate.reasons[0] if gate.reasons else 'EXECUTION_GATE_DENIED'
        return ExternalResearchExecution(None, ExternalResearchEvidence(False, False, reason, None, (), query_hash, request.budgets.external_calls, int((monotonic()-started)*1000), 0, 0, None, False))
    activation = authorize_runtime_activation(gate, RuntimeActivationRequest(environment=environment, mode=RuntimeActivationMode.LOCAL_EXECUTE, external_execution_enabled=False))
    if not activation.allowed or not activation.ready_for_executor:
        reason = activation.reasons[0] if activation.reasons else 'RUNTIME_NOT_READY_FOR_EXECUTOR'
        prepared = gate.downstream.prepared
        return ExternalResearchExecution(None, ExternalResearchEvidence(False, False, reason, prepared.procedure if prepared else None, tuple(sorted(prepared.effective_scopes)) if prepared else (), query_hash, request.budgets.external_calls, int((monotonic()-started)*1000), 0, 0, None, False))
    try:
        result = execute_agent_reach_public_search(activation, gate.downstream, versions_lock_path, timeout_seconds=timeout_seconds, docker_binary=docker_binary)
    except Exception as exc:
        prepared = gate.downstream.prepared
        return ExternalResearchExecution(None, ExternalResearchEvidence(True, False, type(exc).__name__, prepared.procedure if prepared else None, tuple(sorted(prepared.effective_scopes)) if prepared else (), query_hash, request.budgets.external_calls, int((monotonic()-started)*1000), 0, 0, None, False))
    stdout_bytes = len(result.stdout.encode('utf-8'))
    stderr_bytes = len(result.stderr.encode('utf-8'))
    if stdout_bytes > _MAX_OUTPUT_BYTES:
        return ExternalResearchExecution(None, ExternalResearchEvidence(True, False, 'AGENT_REACH_OUTPUT_LIMIT_EXCEEDED', gate.downstream.prepared.procedure, tuple(sorted(gate.downstream.prepared.effective_scopes)), query_hash, request.budgets.external_calls, int((monotonic()-started)*1000), stdout_bytes, stderr_bytes, result.returncode, False))
    return ExternalResearchExecution(result, ExternalResearchEvidence(True, result.success, 'OK' if result.success else 'EXTERNAL_EXECUTION_FAILED', gate.downstream.prepared.procedure, tuple(sorted(gate.downstream.prepared.effective_scopes)), query_hash, request.budgets.external_calls, int((monotonic()-started)*1000), stdout_bytes, stderr_bytes, result.returncode, False))
