from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from modules.agent_harness.planner import PlanStep
from modules.agent_harness.router import RouteDecision
from modules.agent_harness.worker_compiler import (
    TARGET_BRANCH, TARGET_REPO, WorkerCompileError, WorkerCompileRequest, WorkerCompiler,
)
from tools.mirror_sync.universal_job_bridge import validate


def step(**overrides):
    values = dict(
        id='s1', domain='engineering', procedure='repo-change',
        required_capabilities=('CODE_WRITE',), required_scopes=('repo:rbalam/EDARSA_HUB',),
        risk='R1', data_classification='INTERNAL', executor='worker',
    )
    values.update(overrides)
    return PlanStep(**values)


def route(**overrides):
    values = dict(
        step_id='s1', agent_id='bos-backend', agent_version='1',
        skill_id='repo-change', skill_version='1', executor='worker',
    )
    values.update(overrides)
    return RouteDecision(**values)


def request(**overrides):
    values = dict(
        job_id='AH4-test-job', objective='deterministic mutation test',
        step=step(), route=route(),
        actions=({'type': 'write_file', 'path': 'backend/modules/example/generated.py', 'content': 'x = 1\n'},),
        checks=({'type': 'git_diff_check'},),
    )
    values.update(overrides)
    return WorkerCompileRequest(**values)


def test_compiler_generates_worker_v2_job_accepted_by_canonical_bridge(tmp_path, monkeypatch):
    import tools.mirror_sync.universal_job_bridge as bridge
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    job = WorkerCompiler().compile(request())
    assert job['schema'] == 'edarsahub.worker-job.v2'
    assert job['target_repo'] == TARGET_REPO
    assert job['target_branch'] == TARGET_BRANCH
    assert job['production_allowed'] is False
    assert validate(job) == []


def test_compiler_carries_non_authoritative_harness_evidence():
    job = WorkerCompiler().compile(request())
    context = job['harness_context']
    assert context['plan_step_id'] == 's1'
    assert context['agent_id'] == 'bos-backend'
    assert context['skill_id'] == 'repo-change'
    assert context['executor'] == 'worker'


def test_compile_fails_on_route_step_mismatch():
    with pytest.raises(WorkerCompileError, match='ROUTE_STEP_MISMATCH'):
        request(route=route(step_id='other'))


def test_compile_fails_for_non_worker_executor():
    with pytest.raises(WorkerCompileError, match='WORKER_EXECUTOR_REQUIRED'):
        request(step=step(executor='ai_gateway'), route=route(executor='ai_gateway'))


def test_compile_rejects_shell_or_command_keys():
    with pytest.raises(WorkerCompileError, match='ACTION_FORBIDDEN_KEY'):
        WorkerCompiler().compile(request(actions=({'type': 'write_file', 'path': 'x.py', 'content': 'x', 'command': 'rm -rf /'},)))
    with pytest.raises(WorkerCompileError, match='ACTION_TYPE_FORBIDDEN'):
        WorkerCompiler().compile(request(actions=({'type': 'shell', 'path': 'x', 'content': 'echo x'},)))


def test_compile_rejects_sql_readonly_check_in_mutation_adapter():
    with pytest.raises(WorkerCompileError, match='CHECK_TYPE_FORBIDDEN'):
        WorkerCompiler().compile(request(checks=({'type': 'sql_readonly_audit'},)))


def test_compile_rejects_attempt_to_override_production_or_branch():
    with pytest.raises(WorkerCompileError, match='ACTION_FORBIDDEN_KEY'):
        WorkerCompiler().compile(request(actions=({'type': 'write_file', 'path': 'x.py', 'content': 'x', 'production_allowed': True},)))
    with pytest.raises(WorkerCompileError, match='ACTION_FORBIDDEN_KEY'):
        WorkerCompiler().compile(request(actions=({'type': 'write_file', 'path': 'x.py', 'content': 'x', 'target_branch': 'main'},)))


def test_compile_rejects_empty_actions_and_invalid_job_id():
    with pytest.raises(WorkerCompileError, match='ACTIONS_REQUIRED'):
        request(actions=())
    with pytest.raises(WorkerCompileError, match='JOB_ID_INVALID'):
        request(job_id='x')


def test_compile_preserves_core_growth_guard(tmp_path, monkeypatch):
    import tools.mirror_sync.universal_job_bridge as bridge
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    (tmp_path / 'backend' / 'core').mkdir(parents=True)
    with pytest.raises(WorkerCompileError, match='CORE_GROWTH_FORBIDDEN'):
        WorkerCompiler().compile(request(actions=({'type': 'write_file', 'path': 'backend/core/new_feature.py', 'content': 'x = 1\n'},)))
