from pathlib import Path
from types import SimpleNamespace
import inspect
import pytest

from core.agent_capability_policy import BudgetRequest, DataClassification, PolicyContext, PolicyRequest, RiskLevel
from core.agent_execution_gate import ExecutionGateDecision
from core.agent_reach_egress_canary import execute_agent_reach_egress_canary
from core.agent_reach_policy_adapter import authorize_agent_reach
from core.agent_runtime_activation import RuntimeActivationMode, RuntimeActivationRequest, RuntimeEnvironment, authorize_runtime_activation

def execution_gate(allowed=True, reasons=()):
    return ExecutionGateDecision(allowed=allowed, reasons=tuple(reasons), downstream=None)

def activation(environment=RuntimeEnvironment.DEVELOPMENT):
    return authorize_runtime_activation(execution_gate(), RuntimeActivationRequest(environment=environment, mode=RuntimeActivationMode.LOCAL_EXECUTE, external_execution_enabled=False))

def policy_context():
    caps = frozenset({'EXTERNAL_RESEARCH'})
    scopes = frozenset({'external:web'})
    return PolicyContext(
        user_allowed_capabilities=caps,
        agent_allowed_capabilities=caps,
        environment_allowed_capabilities=caps,
        policy_allowed_capabilities=caps,
        user_allowed_scopes=scopes,
        agent_allowed_scopes=scopes,
        environment_allowed_scopes=scopes,
        policy_allowed_scopes=scopes,
        budget_limits={
            'runtime_seconds': 60,
            'files_changed': 0,
            'lines_changed': 0,
            'external_calls': 1,
            'sql_rows': 0,
            'inference_cost_usd': 0.0,
        },
    )

def reach_decision(calls=1):
    request = PolicyRequest(
        capabilities=frozenset({'EXTERNAL_RESEARCH'}),
        scopes=frozenset({'external:web'}),
        risk=RiskLevel.R1,
        data_classification=DataClassification.PUBLIC,
        budgets=BudgetRequest(external_calls=calls),
        external_egress=True,
        production_allowed=False,
        privilege_expansion=False,
        procedure='agent-reach-external-research',
    )
    return authorize_agent_reach('public connectivity canary', request, policy_context())

def write_lock(tmp_path: Path):
    path = tmp_path / 'versions.lock'
    path.write_text('IMAGE_REPOSITORY=edarsa/agent-reach-runtime\nIMAGE_TAG=test-tag\n', encoding='utf-8')
    return path

def test_canary_uses_fixed_https_target_and_hardened_argv(monkeypatch, tmp_path):
    captured = {}
    def fake_run(argv, **kwargs):
        captured['argv'] = tuple(argv)
        captured['kwargs'] = kwargs
        return SimpleNamespace(returncode=0, stdout='ok', stderr='')
    monkeypatch.setattr('core.agent_reach_egress_canary.subprocess.run', fake_run)
    result = execute_agent_reach_egress_canary(activation(), reach_decision(), write_lock(tmp_path), docker_binary='/usr/bin/docker')
    assert result.success is True
    assert result.argv[-1] == 'https://example.com/'
    assert result.argv[result.argv.index('--network') + 1] == 'bridge'
    assert result.argv[result.argv.index('--cap-drop') + 1] == 'ALL'
    assert '--mount' not in result.argv and '-v' not in result.argv
    assert result.argv[result.argv.index('--max-redirs') + 1] == '0'
    assert captured['kwargs']['shell'] is False

def test_no_user_url_or_arbitrary_command_surface():
    signature = inspect.signature(execute_agent_reach_egress_canary)
    assert 'url' not in signature.parameters
    assert 'command' not in signature.parameters
    assert 'headers' not in signature.parameters

def test_canary_requires_policy_and_exactly_one_call(tmp_path):
    denied = reach_decision(calls=0)
    with pytest.raises(RuntimeError, match='AGENT_REACH_POLICY_DENIED'):
        execute_agent_reach_egress_canary(activation(), denied, write_lock(tmp_path), docker_binary='/usr/bin/docker')

def test_canary_fails_closed_on_runtime_and_timeout(tmp_path):
    dry = authorize_runtime_activation(execution_gate(), RuntimeActivationRequest(environment=RuntimeEnvironment.DEVELOPMENT))
    with pytest.raises(RuntimeError, match='RUNTIME_NOT_READY_FOR_EXECUTOR'):
        execute_agent_reach_egress_canary(dry, reach_decision(), write_lock(tmp_path), docker_binary='/usr/bin/docker')
    with pytest.raises(RuntimeError, match='AGENT_REACH_CANARY_TIMEOUT_INVALID'):
        execute_agent_reach_egress_canary(activation(), reach_decision(), write_lock(tmp_path), timeout_seconds=31, docker_binary='/usr/bin/docker')

def test_production_remains_denied(tmp_path):
    prod = activation(RuntimeEnvironment.PRODUCTION)
    assert prod.allowed is False
    with pytest.raises(RuntimeError, match='RUNTIME_NOT_READY_FOR_EXECUTOR'):
        execute_agent_reach_egress_canary(prod, reach_decision(), write_lock(tmp_path), docker_binary='/usr/bin/docker')
