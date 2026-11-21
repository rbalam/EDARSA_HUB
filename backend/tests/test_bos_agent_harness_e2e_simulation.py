from __future__ import annotations

import pytest

from modules.agent_harness.control_plane import ControlPlaneError
from modules.agent_harness.e2e_simulation import AgentHarnessSimulation
from modules.agent_harness.evidence import EvidenceError
from modules.agent_harness.planner import PlanStep
from modules.agent_harness.registry import AgentSpec, SkillSpec
from modules.agent_harness.router import RouteError


def agent(**overrides):
    values = dict(
        id='sim-agent', version='1', role='backend', domains=('engineering',), status='APPROVED',
        allowed_skills=('repo-change',), capability_ceiling=('CODE_WRITE',),
        scope_ceiling=('repo:rbalam/EDARSA_HUB',), max_risk='R1',
        allowed_data_classifications=('INTERNAL',), model_requirements={}, budgets={},
        max_concurrency=1, red_team_required=True, human_approval_thresholds=(), provenance='BOS_NATIVE',
    )
    values.update(overrides)
    return AgentSpec(**values)


def skill(**overrides):
    values = dict(
        id='repo-change', version='1', source='BOS_NATIVE', origin='BOS', domain='engineering',
        description='repo mutation', entrypoint='worker', provenance='BOS_NATIVE', checksum='abc123', license='',
        required_capabilities=('CODE_WRITE',), allowed_scopes=('repo:rbalam/EDARSA_HUB',),
        max_risk='R1', allowed_data_classifications=('INTERNAL',), external_egress=False,
        allowed_executors=('worker',), allowed_tools=(), dependencies=(), conflicts=(), validations=(),
        lifecycle='APPROVED', adoption='NATIVE',
    )
    values.update(overrides)
    return SkillSpec(**values)


def step(**overrides):
    values = dict(
        id='s1', domain='engineering', procedure='repo-change', required_capabilities=('CODE_WRITE',),
        required_scopes=('repo:rbalam/EDARSA_HUB',), risk='R1', data_classification='INTERNAL', executor='worker',
    )
    values.update(overrides)
    return PlanStep(**values)


def worker_result(**overrides):
    values = dict(
        job_id='sim-job-1', source_repo='rbalam/EDARSA_HUB', source_branch='Edarsahub_Desarrollo',
        status='INTEGRATED', certification='CERTIFIED', quality_gate='PASS', tests='PASS',
        production_touched=False, blockers=[], percent_complete=100,
    )
    values.update(overrides)
    return values


def test_e2e_happy_path_is_certified_and_healthy():
    result = AgentHarnessSimulation().run(
        request_id='req-1', step=step(), agent=agent(), skill=skill(), worker_result=worker_result()
    )
    assert result.evidence_success is True
    assert result.control_plane_healthy is True
    assert result.worker_job_id == 'sim-job-1'


def test_route_failure_is_fail_closed():
    with pytest.raises(RouteError, match='NO_ELIGIBLE_ROUTE'):
        AgentHarnessSimulation().run(
            request_id='req-2', step=step(required_scopes=('repo:other/repo',)),
            agent=agent(), skill=skill(), worker_result=worker_result(job_id='sim-job-2'),
        )


def test_nonterminal_worker_result_is_rejected():
    with pytest.raises(EvidenceError, match='WORKER_RESULT_NOT_TERMINAL'):
        AgentHarnessSimulation().run(
            request_id='req-3', step=step(), agent=agent(), skill=skill(),
            worker_result=worker_result(job_id='sim-job-3', status='PROCESSING'),
        )


def test_production_touched_is_rejected():
    with pytest.raises(EvidenceError, match='WORKER_RESULT_PRODUCTION_TOUCHED'):
        AgentHarnessSimulation().run(
            request_id='req-5', step=step(), agent=agent(), skill=skill(),
            worker_result=worker_result(job_id='sim-job-5', production_touched=True),
        )


def test_budget_overrun_is_rejected_by_control_plane():
    with pytest.raises(ControlPlaneError, match='BUDGET_EXCEEDED'):
        AgentHarnessSimulation().run(
            request_id='req-6', step=step(), agent=agent(), skill=skill(),
            worker_result=worker_result(job_id='sim-job-6'), budget_limit=10, budget_consumed=11,
        )
