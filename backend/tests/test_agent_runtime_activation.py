from core.agent_execution_gate import ExecutionGateDecision
from core.agent_runtime_activation import (
    RuntimeActivationMode, RuntimeActivationRequest, RuntimeEnvironment,
    authorize_runtime_activation,
)


def gate(allowed=True, reasons=()):
    return ExecutionGateDecision(allowed=allowed, reasons=tuple(reasons), downstream=None)


def test_development_dry_run_is_allowed_but_never_executor_ready():
    decision = authorize_runtime_activation(
        gate(),
        RuntimeActivationRequest(environment=RuntimeEnvironment.DEVELOPMENT),
    )
    assert decision.allowed is True
    assert decision.ready_for_executor is False
    assert decision.reasons == ()


def test_staging_dry_run_is_allowed_but_never_executor_ready():
    decision = authorize_runtime_activation(
        gate(),
        RuntimeActivationRequest(environment=RuntimeEnvironment.STAGING),
    )
    assert decision.allowed is True
    assert decision.ready_for_executor is False


def test_production_is_fail_closed():
    decision = authorize_runtime_activation(
        gate(),
        RuntimeActivationRequest(environment=RuntimeEnvironment.PRODUCTION),
    )
    assert decision.allowed is False
    assert 'RUNTIME_PRODUCTION_FORBIDDEN' in decision.reasons


def test_execute_mode_is_not_enabled_in_gate5a():
    decision = authorize_runtime_activation(
        gate(),
        RuntimeActivationRequest(
            environment=RuntimeEnvironment.DEVELOPMENT,
            mode=RuntimeActivationMode.EXECUTE,
        ),
    )
    assert decision.allowed is False
    assert 'RUNTIME_EXECUTION_NOT_ENABLED' in decision.reasons


def test_external_execution_switch_is_not_enabled_in_gate5a():
    decision = authorize_runtime_activation(
        gate(),
        RuntimeActivationRequest(
            environment=RuntimeEnvironment.DEVELOPMENT,
            external_execution_enabled=True,
        ),
    )
    assert decision.allowed is False
    assert 'RUNTIME_EXTERNAL_EXECUTION_DISABLED' in decision.reasons


def test_execution_gate_denial_is_propagated():
    decision = authorize_runtime_activation(
        gate(False, ('REQUESTER_RBAC_DENIED',)),
        RuntimeActivationRequest(environment=RuntimeEnvironment.DEVELOPMENT),
    )
    assert decision.allowed is False
    assert decision.reasons[0] == 'EXECUTION_GATE_DENIED'
    assert 'REQUESTER_RBAC_DENIED' in decision.reasons
    assert decision.ready_for_executor is False
