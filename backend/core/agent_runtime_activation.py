from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.agent_execution_gate import ExecutionGateDecision


class RuntimeEnvironment(str, Enum):
    DEVELOPMENT = 'development'
    STAGING = 'staging'
    PRODUCTION = 'production'


class RuntimeActivationMode(str, Enum):
    DRY_RUN = 'dry_run'
    LOCAL_EXECUTE = 'local_execute'
    EXECUTE = 'execute'


@dataclass(frozen=True)
class RuntimeActivationRequest:
    environment: RuntimeEnvironment
    mode: RuntimeActivationMode = RuntimeActivationMode.DRY_RUN
    external_execution_enabled: bool = False


@dataclass(frozen=True)
class RuntimeActivationDecision:
    allowed: bool
    reasons: tuple[str, ...]
    execution_gate: ExecutionGateDecision
    ready_for_executor: bool


def authorize_runtime_activation(
    execution_gate: ExecutionGateDecision,
    activation: RuntimeActivationRequest,
) -> RuntimeActivationDecision:
    reasons: list[str] = []

    if not execution_gate.allowed:
        reasons.append('EXECUTION_GATE_DENIED')
        reasons.extend(execution_gate.reasons)
    if activation.environment is RuntimeEnvironment.PRODUCTION:
        reasons.append('RUNTIME_PRODUCTION_FORBIDDEN')
    if activation.mode is RuntimeActivationMode.EXECUTE:
        reasons.append('RUNTIME_EXECUTION_NOT_ENABLED')
    if activation.external_execution_enabled:
        reasons.append('RUNTIME_EXTERNAL_EXECUTION_DISABLED')

    unique_reasons = tuple(dict.fromkeys(reasons))
    if unique_reasons:
        return RuntimeActivationDecision(
            allowed=False,
            reasons=unique_reasons,
            execution_gate=execution_gate,
            ready_for_executor=False,
        )

    return RuntimeActivationDecision(
        allowed=True,
        reasons=(),
        execution_gate=execution_gate,
        ready_for_executor=(activation.mode is RuntimeActivationMode.LOCAL_EXECUTE),
    )
