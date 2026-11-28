from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from core.agent_execution_gate import ExecutionGateDecision
from core.agent_runtime_activation import (
    RuntimeActivationMode,
    RuntimeActivationRequest,
    RuntimeEnvironment,
    authorize_runtime_activation,
)

LOCAL_RUNTIME_SCHEMA = 'edarsahub.bos-local-runtime-envelope.v1'


class LocalRuntimeError(ValueError):
    pass


@dataclass(frozen=True)
class LocalRuntimeEnvelope:
    request_id: str
    step_id: str
    mode: str
    environment: str
    ready_for_executor: bool
    executor: str
    payload: Mapping[str, object]
    schema: str = LOCAL_RUNTIME_SCHEMA


class LocalRuntime:
    def prepare(
        self,
        *,
        request_id: str,
        step_id: str,
        execution_gate: ExecutionGateDecision,
        payload: Mapping[str, object],
        mode: RuntimeActivationMode = RuntimeActivationMode.DRY_RUN,
        environment: RuntimeEnvironment = RuntimeEnvironment.DEVELOPMENT,
        external_execution_enabled: bool = False,
    ) -> LocalRuntimeEnvelope:
        if not str(request_id).strip():
            raise LocalRuntimeError('REQUEST_ID_REQUIRED')
        if not str(step_id).strip():
            raise LocalRuntimeError('STEP_ID_REQUIRED')
        if not isinstance(payload, Mapping):
            raise LocalRuntimeError('PAYLOAD_MAPPING_REQUIRED')
        if environment is not RuntimeEnvironment.DEVELOPMENT:
            raise LocalRuntimeError('LOCAL_RUNTIME_DEVELOPMENT_ONLY')

        activation = RuntimeActivationRequest(
            environment=environment,
            mode=mode,
            external_execution_enabled=external_execution_enabled,
        )
        decision = authorize_runtime_activation(execution_gate, activation)
        if not decision.allowed:
            raise LocalRuntimeError('|'.join(decision.reasons) or 'RUNTIME_ACTIVATION_DENIED')

        return LocalRuntimeEnvelope(
            request_id=str(request_id).strip(),
            step_id=str(step_id).strip(),
            mode=mode.value,
            environment=environment.value,
            ready_for_executor=decision.ready_for_executor,
            executor='local-development-adapter',
            payload=dict(payload),
        )
