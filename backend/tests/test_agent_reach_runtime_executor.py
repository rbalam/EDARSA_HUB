from pathlib import Path
from types import SimpleNamespace
import pytest
from core.agent_execution_gate import ExecutionGateDecision
from core.agent_reach_runtime_executor import execute_agent_reach_healthcheck, load_agent_reach_image
from core.agent_runtime_activation import RuntimeActivationMode, RuntimeActivationRequest, RuntimeEnvironment, authorize_runtime_activation

def gate(allowed=True, reasons=()):
    return ExecutionGateDecision(allowed=allowed, reasons=tuple(reasons), downstream=None)

def local_activation():
    return authorize_runtime_activation(gate(), RuntimeActivationRequest(environment=RuntimeEnvironment.DEVELOPMENT, mode=RuntimeActivationMode.LOCAL_EXECUTE, external_execution_enabled=False))

def write_lock(tmp_path: Path):
    path = tmp_path / 'versions.lock'
    path.write_text('IMAGE_REPOSITORY=edarsa/agent-reach-runtime\nIMAGE_TAG=test-tag\n', encoding='utf-8')
    return path

def test_local_execute_is_ready_and_execute_contract_stays_denied():
    local = local_activation()
    assert local.allowed is True
    assert local.ready_for_executor is True
    external = authorize_runtime_activation(gate(), RuntimeActivationRequest(environment=RuntimeEnvironment.DEVELOPMENT, mode=RuntimeActivationMode.EXECUTE, external_execution_enabled=True))
    assert external.allowed is False
    assert external.ready_for_executor is False
    assert 'RUNTIME_EXECUTION_NOT_ENABLED' in external.reasons
    assert 'RUNTIME_EXTERNAL_EXECUTION_DISABLED' in external.reasons

def test_production_local_execute_is_denied():
    decision = authorize_runtime_activation(gate(), RuntimeActivationRequest(environment=RuntimeEnvironment.PRODUCTION, mode=RuntimeActivationMode.LOCAL_EXECUTE))
    assert decision.allowed is False
    assert decision.ready_for_executor is False
    assert 'RUNTIME_PRODUCTION_FORBIDDEN' in decision.reasons

def test_image_loaded_from_lock(tmp_path):
    assert load_agent_reach_image(write_lock(tmp_path)) == 'edarsa/agent-reach-runtime:test-tag'

def test_executor_uses_fixed_networkless_argv(monkeypatch, tmp_path):
    captured = {}
    def fake_run(argv, **kwargs):
        captured['argv'] = tuple(argv)
        captured['kwargs'] = kwargs
        return SimpleNamespace(returncode=0, stdout='AGENT_REACH_HEALTHCHECK=PASS\n', stderr='')
    monkeypatch.setattr('core.agent_reach_runtime_executor.subprocess.run', fake_run)
    result = execute_agent_reach_healthcheck(local_activation(), write_lock(tmp_path), docker_binary='/usr/bin/docker')
    assert result.success is True
    assert '--network' in result.argv and 'none' in result.argv
    assert '--cap-drop' in result.argv and 'ALL' in result.argv
    assert '--mount' not in result.argv and '-v' not in result.argv
    assert captured['kwargs']['shell'] is False

def test_executor_fail_closed(tmp_path):
    dry = authorize_runtime_activation(gate(), RuntimeActivationRequest(environment=RuntimeEnvironment.DEVELOPMENT))
    with pytest.raises(RuntimeError, match='RUNTIME_NOT_READY_FOR_EXECUTOR'):
        execute_agent_reach_healthcheck(dry, write_lock(tmp_path), docker_binary='/usr/bin/docker')
    bad = tmp_path / 'bad.lock'
    bad.write_text('IMAGE_REPOSITORY=edarsa/runtime;rm -rf /\nIMAGE_TAG=x\n', encoding='utf-8')
    with pytest.raises(RuntimeError, match='AGENT_REACH_IMAGE_LOCK_INVALID'):
        load_agent_reach_image(bad)
    with pytest.raises(RuntimeError, match='AGENT_REACH_EXECUTOR_TIMEOUT_INVALID'):
        execute_agent_reach_healthcheck(local_activation(), write_lock(tmp_path), timeout_seconds=121, docker_binary='/usr/bin/docker')
