from pathlib import Path
from types import SimpleNamespace
import inspect
import pytest

from core.agent_capability_policy import BudgetRequest, DataClassification, PolicyContext, PolicyRequest, RiskLevel
from core.agent_execution_gate import ExecutionGateDecision
from core.agent_reach_policy_adapter import authorize_agent_reach
from core.agent_reach_public_search_executor import execute_agent_reach_public_search
from core.agent_runtime_activation import RuntimeActivationMode, RuntimeActivationRequest, RuntimeEnvironment, authorize_runtime_activation

def execution_gate(allowed=True, reasons=()):
    return ExecutionGateDecision(allowed=allowed, reasons=tuple(reasons), downstream=None)

def activation(environment=RuntimeEnvironment.DEVELOPMENT):
    return authorize_runtime_activation(execution_gate(), RuntimeActivationRequest(environment=environment, mode=RuntimeActivationMode.LOCAL_EXECUTE, external_execution_enabled=False))

def policy_context(scopes=frozenset({'external:web'})):
    caps = frozenset({'EXTERNAL_RESEARCH'})
    return PolicyContext(
        user_allowed_capabilities=caps, agent_allowed_capabilities=caps,
        environment_allowed_capabilities=caps, policy_allowed_capabilities=caps,
        user_allowed_scopes=scopes, agent_allowed_scopes=scopes,
        environment_allowed_scopes=scopes, policy_allowed_scopes=scopes,
        budget_limits={'runtime_seconds': 60, 'files_changed': 0, 'lines_changed': 0, 'external_calls': 1, 'sql_rows': 0, 'inference_cost_usd': 0.0},
    )

def reach_decision(query='public restaurant technology trends', calls=1, scopes=frozenset({'external:web'})):
    request = PolicyRequest(
        capabilities=frozenset({'EXTERNAL_RESEARCH'}), scopes=scopes,
        risk=RiskLevel.R1, data_classification=DataClassification.PUBLIC,
        budgets=BudgetRequest(external_calls=calls), external_egress=True,
        production_allowed=False, privilege_expansion=False,
        procedure='agent-reach-external-research',
    )
    return authorize_agent_reach(query, request, policy_context(scopes))

def write_lock(tmp_path: Path):
    path = tmp_path / 'versions.lock'
    path.write_text('IMAGE_REPOSITORY=edarsa/agent-reach-runtime\nIMAGE_TAG=test-tag\n', encoding='utf-8')
    return path

def test_query_drives_only_fixed_search_target(monkeypatch, tmp_path):
    captured = {}
    def fake_run(argv, **kwargs):
        captured['argv'] = tuple(argv); captured['kwargs'] = kwargs
        return SimpleNamespace(returncode=0, stdout='result', stderr='')
    monkeypatch.setattr('core.agent_reach_public_search_executor.subprocess.run', fake_run)
    result = execute_agent_reach_public_search(activation(), reach_decision('menu trends mexico 2026'), write_lock(tmp_path), docker_binary='/usr/bin/docker')
    assert result.success is True
    assert result.argv[-1].startswith('https://r.jina.ai/http://www.google.com/search?q=')
    assert result.argv[-1].endswith('menu+trends+mexico+2026')
    assert result.argv[result.argv.index('--network') + 1] == 'bridge'
    assert result.argv[result.argv.index('--cap-drop') + 1] == 'ALL'
    assert result.argv[result.argv.index('--max-filesize') + 1] == '65536'
    assert '--mount' not in result.argv and '-v' not in result.argv
    assert captured['kwargs']['shell'] is False

def test_executor_has_no_arbitrary_surface():
    signature = inspect.signature(execute_agent_reach_public_search)
    for name in ('url', 'command', 'headers', 'cookies', 'token', 'env', 'mounts', 'args'):
        assert name not in signature.parameters

def test_policy_rejects_over_budget_before_executor(tmp_path):
    denied = reach_decision(calls=2)
    assert denied.allowed is False
    assert 'BUDGET_EXCEEDED:external_calls' in denied.reasons
    with pytest.raises(RuntimeError, match='AGENT_REACH_POLICY_DENIED'):
        execute_agent_reach_public_search(activation(), denied, write_lock(tmp_path), docker_binary='/usr/bin/docker')

def test_requires_canonical_scope(tmp_path):
    bad_scope = reach_decision(scopes=frozenset({'external:other'}))
    with pytest.raises(RuntimeError, match='AGENT_REACH_SCOPE_INVALID'):
        execute_agent_reach_public_search(activation(), bad_scope, write_lock(tmp_path), docker_binary='/usr/bin/docker')

def test_policy_denial_and_runtime_denial_fail_closed(tmp_path):
    denied = reach_decision(query='password=abc')
    with pytest.raises(RuntimeError, match='AGENT_REACH_POLICY_DENIED'):
        execute_agent_reach_public_search(activation(), denied, write_lock(tmp_path), docker_binary='/usr/bin/docker')
    dry = authorize_runtime_activation(execution_gate(), RuntimeActivationRequest(environment=RuntimeEnvironment.DEVELOPMENT))
    with pytest.raises(RuntimeError, match='RUNTIME_NOT_READY_FOR_EXECUTOR'):
        execute_agent_reach_public_search(dry, reach_decision(), write_lock(tmp_path), docker_binary='/usr/bin/docker')

def test_production_and_timeout_remain_fail_closed(tmp_path):
    prod = activation(RuntimeEnvironment.PRODUCTION)
    assert prod.allowed is False
    with pytest.raises(RuntimeError, match='RUNTIME_NOT_READY_FOR_EXECUTOR'):
        execute_agent_reach_public_search(prod, reach_decision(), write_lock(tmp_path), docker_binary='/usr/bin/docker')
    with pytest.raises(RuntimeError, match='AGENT_REACH_SEARCH_TIMEOUT_INVALID'):
        execute_agent_reach_public_search(activation(), reach_decision(), write_lock(tmp_path), timeout_seconds=31, docker_binary='/usr/bin/docker')
