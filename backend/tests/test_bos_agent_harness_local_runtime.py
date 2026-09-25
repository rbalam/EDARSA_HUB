from __future__ import annotations

import pytest

from core.agent_execution_gate import ExecutionGateDecision
from core.agent_runtime_activation import RuntimeActivationMode, RuntimeEnvironment
from modules.agent_harness.local_runtime import LocalRuntime, LocalRuntimeError


def allowed_gate():
    return ExecutionGateDecision(allowed=True, reasons=(), downstream=None)


def denied_gate():
    return ExecutionGateDecision(allowed=False, reasons=('REQUESTER_RBAC_DENIED',), downstream=None)


def test_dry_run_is_allowed_but_not_ready_for_executor():
    envelope = LocalRuntime().prepare(
        request_id='req-1', step_id='s1', execution_gate=allowed_gate(), payload={'x': 1}
    )
    assert envelope.environment == 'development'
    assert envelope.mode == 'dry_run'
    assert envelope.ready_for_executor is False


def test_local_execute_is_ready_only_after_execution_gate_allows():
    envelope = LocalRuntime().prepare(
        request_id='req-2', step_id='s2', execution_gate=allowed_gate(), payload={'x': 2},
        mode=RuntimeActivationMode.LOCAL_EXECUTE,
    )
    assert envelope.ready_for_executor is True
    assert envelope.executor == 'local-development-adapter'


def test_execution_gate_denied_fails_closed():
    with pytest.raises(LocalRuntimeError, match='EXECUTION_GATE_DENIED'):
        LocalRuntime().prepare(
            request_id='req-3', step_id='s3', execution_gate=denied_gate(), payload={}
        )


def test_production_fails_closed_before_activation():
    with pytest.raises(LocalRuntimeError, match='LOCAL_RUNTIME_DEVELOPMENT_ONLY'):
        LocalRuntime().prepare(
            request_id='req-4', step_id='s4', execution_gate=allowed_gate(), payload={},
            environment=RuntimeEnvironment.PRODUCTION,
        )


def test_staging_is_not_local_runtime():
    with pytest.raises(LocalRuntimeError, match='LOCAL_RUNTIME_DEVELOPMENT_ONLY'):
        LocalRuntime().prepare(
            request_id='req-5', step_id='s5', execution_gate=allowed_gate(), payload={},
            environment=RuntimeEnvironment.STAGING,
        )


def test_execute_mode_fails_closed():
    with pytest.raises(LocalRuntimeError, match='RUNTIME_EXECUTION_NOT_ENABLED'):
        LocalRuntime().prepare(
            request_id='req-6', step_id='s6', execution_gate=allowed_gate(), payload={},
            mode=RuntimeActivationMode.EXECUTE,
        )


def test_external_execution_fails_closed():
    with pytest.raises(LocalRuntimeError, match='RUNTIME_EXTERNAL_EXECUTION_DISABLED'):
        LocalRuntime().prepare(
            request_id='req-7', step_id='s7', execution_gate=allowed_gate(), payload={},
            external_execution_enabled=True,
        )


def test_identity_and_payload_validation():
    with pytest.raises(LocalRuntimeError, match='REQUEST_ID_REQUIRED'):
        LocalRuntime().prepare(request_id='', step_id='s8', execution_gate=allowed_gate(), payload={})
    with pytest.raises(LocalRuntimeError, match='STEP_ID_REQUIRED'):
        LocalRuntime().prepare(request_id='r', step_id='', execution_gate=allowed_gate(), payload={})
