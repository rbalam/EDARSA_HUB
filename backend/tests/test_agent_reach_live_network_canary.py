from __future__ import annotations

import json
import shutil
from pathlib import Path

from core.agent_capability_policy import BudgetRequest, DataClassification, PolicyContext, PolicyRequest, RiskLevel
from core.agent_external_research_service import execute_external_research

EVIDENCE = Path(__file__).with_name('agent_reach_live_network_canary_evidence.json')
LOCK = Path(__file__).resolve().parents[2] / 'infra' / 'agent-reach' / 'versions.lock'
QUERY = 'OpenAI official website'

def _context() -> PolicyContext:
    caps = frozenset({'EXTERNAL_RESEARCH'})
    scopes = frozenset({'external:web'})
    return PolicyContext(
        user_allowed_capabilities=caps, agent_allowed_capabilities=caps,
        environment_allowed_capabilities=caps, policy_allowed_capabilities=caps,
        user_allowed_scopes=scopes, agent_allowed_scopes=scopes,
        environment_allowed_scopes=scopes, policy_allowed_scopes=scopes,
        budget_limits={'runtime_seconds': 60, 'files_changed': 0, 'lines_changed': 0, 'external_calls': 1, 'sql_rows': 0, 'inference_cost_usd': 0.0},
    )

def _request() -> PolicyRequest:
    return PolicyRequest(
        capabilities=frozenset({'EXTERNAL_RESEARCH'}), scopes=frozenset({'external:web'}),
        risk=RiskLevel.R1, data_classification=DataClassification.PUBLIC,
        budgets=BudgetRequest(external_calls=1), external_egress=True,
        production_allowed=False, privilege_expansion=False,
        procedure='agent-reach-external-research',
    )

def test_agent_reach_live_network_canary() -> None:
    docker = shutil.which('docker')
    evidence = {
        'schema': 'edarsahub.agent-reach-live-canary.v1',
        'canary_live': True, 'production_touched': False,
        'docker_available': bool(docker), 'external_calls_budget': 1,
        'timeout_seconds': 30, 'output_limit_bytes': 65536,
    }
    if not docker:
        evidence['success'] = False
        evidence['reason'] = 'DOCKER_COMMAND_NOT_AVAILABLE'
        EVIDENCE.write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        raise AssertionError('DOCKER_COMMAND_NOT_AVAILABLE')
    execution = execute_external_research(
        {'allowed': True}, QUERY, _request(), _context(), LOCK,
        timeout_seconds=30, docker_binary=docker,
    )
    ev = execution.evidence
    evidence.update({
        'allowed': ev.allowed, 'success': ev.success, 'reason': ev.reason,
        'procedure': ev.procedure, 'effective_scopes': list(ev.effective_scopes),
        'external_calls_budget': ev.external_calls_budget, 'duration_ms': ev.duration_ms,
        'stdout_bytes': ev.stdout_bytes, 'stderr_bytes': ev.stderr_bytes,
        'returncode': ev.returncode, 'production_touched': ev.production_touched,
    })
    EVIDENCE.write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    assert ev.allowed is True
    assert ev.success is True
    assert ev.reason == 'OK'
    assert ev.procedure == 'agent-reach-external-research'
    assert ev.effective_scopes == ('external:web',)
    assert ev.external_calls_budget == 1
    assert ev.stdout_bytes > 0 and ev.stdout_bytes <= 65536
    assert ev.returncode == 0
    assert ev.production_touched is False
