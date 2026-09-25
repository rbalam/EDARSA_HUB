from __future__ import annotations

import pytest

from modules.agent_harness.evidence import EvidenceBuilder, EvidenceError
from modules.agent_harness.planner import Planner, PlanStep
from modules.agent_harness.redteam import RedTeamFinding, RedTeamRecorder
from modules.agent_harness.registry import AgentSpec, SkillSpec
from modules.agent_harness.router import RouteDecision, RouteError, Router
from modules.agent_harness.worker_compiler import WorkerCompileError, WorkerCompileRequest, WorkerCompiler


def agent(**overrides):
    values = dict(
        id='a1', version='1', role='backend', domains=('engineering',), status='APPROVED',
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
        id='s1', domain='engineering', procedure='repo-change',
        required_capabilities=('CODE_WRITE',), required_scopes=('repo:rbalam/EDARSA_HUB',),
        risk='R1', data_classification='INTERNAL', executor='worker',
    )
    values.update(overrides)
    return PlanStep(**values)


def route_for(item=None):
    item = item or step()
    return Router().route(item, [agent()], [skill()])


def compile_request(item=None, route=None, actions=None):
    item = item or step()
    route = route or route_for(item)
    return WorkerCompileRequest(
        job_id='ah6-redteam-job', objective='redteam', step=item, route=route,
        actions=actions or ({'type': 'write_file', 'path': 'backend/modules/example/x.py', 'content': 'x=1\n'},),
        checks=({'type': 'git_diff_check'},),
    )


def test_cross_scope_is_denied():
    with pytest.raises(RouteError, match='NO_ELIGIBLE_ROUTE'):
        Router().route(step(required_scopes=('repo:other/repo',)), [agent()], [skill()])


def test_capability_escalation_is_denied():
    with pytest.raises(RouteError, match='NO_ELIGIBLE_ROUTE'):
        Router().route(step(required_capabilities=('CODE_WRITE', 'SQL_DDL')), [agent()], [skill()])


def test_risk_escalation_is_denied():
    with pytest.raises(RouteError, match='NO_ELIGIBLE_ROUTE'):
        Router().route(step(risk='R4'), [agent()], [skill()])


def test_data_classification_mismatch_is_denied():
    with pytest.raises(RouteError, match='NO_ELIGIBLE_ROUTE'):
        Router().route(step(data_classification='PII'), [agent()], [skill()])


def test_executor_mismatch_is_denied():
    with pytest.raises(RouteError, match='NO_ELIGIBLE_ROUTE'):
        Router().route(step(executor='ai_gateway'), [agent()], [skill()])


def test_draft_or_blocked_supply_chain_is_denied():
    with pytest.raises(RouteError, match='NO_ELIGIBLE_ROUTE'):
        Router().route(step(), [agent(status='DRAFT')], [skill()])
    with pytest.raises(RouteError, match='NO_ELIGIBLE_ROUTE'):
        Router().route(step(), [agent()], [skill(adoption='BLOCKED')])


def test_shell_and_command_injection_is_denied():
    item = step()
    route = route_for(item)
    with pytest.raises(WorkerCompileError):
        WorkerCompiler().compile(compile_request(item, route, ({'type': 'shell', 'path': 'x', 'content': 'id'},)))
    with pytest.raises(WorkerCompileError):
        WorkerCompiler().compile(compile_request(item, route, ({'type': 'write_file', 'path': 'x.py', 'content': 'x', 'command': 'id'},)))


def test_production_and_branch_override_is_denied():
    item = step()
    route = route_for(item)
    for forbidden in ({'production_allowed': True}, {'target_branch': 'main'}, {'target_repo': 'other/repo'}):
        action = {'type': 'write_file', 'path': 'x.py', 'content': 'x', **forbidden}
        with pytest.raises(WorkerCompileError, match='ACTION_FORBIDDEN_KEY'):
            WorkerCompiler().compile(compile_request(item, route, (action,)))


def test_evidence_rejects_context_tampering_and_replay():
    item = step()
    plan = Planner().build('req-ah6', [item])
    route = route_for(item)
    job = WorkerCompiler().compile(compile_request(item, route))
    result = {
        'job_id': job['job_id'], 'source_repo': 'rbalam/EDARSA_HUB',
        'source_branch': 'Edarsahub_Desarrollo', 'status': 'INTEGRATED',
        'certification': 'CERTIFIED', 'quality_gate': 'PASS', 'tests': 'PASS',
        'production_touched': False, 'blockers': [], 'percent_complete': 100,
    }
    tampered = dict(job)
    tampered['harness_context'] = dict(job['harness_context'])
    tampered['harness_context']['skill_version'] = '999'
    with pytest.raises(EvidenceError, match='HARNESS_CONTEXT_SKILL_VERSION_MISMATCH'):
        EvidenceBuilder().build(plan=plan, step=item, route=route, skill=skill(), compiled_job=tampered, worker_result=result)
    replay = dict(result)
    replay['job_id'] = 'different-job'
    with pytest.raises(EvidenceError, match='WORKER_RESULT_JOB_MISMATCH'):
        EvidenceBuilder().build(plan=plan, step=item, route=route, skill=skill(), compiled_job=job, worker_result=replay)


def test_nonterminal_and_production_touched_results_are_denied():
    item = step()
    plan = Planner().build('req-ah6', [item])
    route = route_for(item)
    job = WorkerCompiler().compile(compile_request(item, route))
    base = {
        'job_id': job['job_id'], 'source_repo': 'rbalam/EDARSA_HUB', 'source_branch': 'Edarsahub_Desarrollo',
        'certification': 'CERTIFIED', 'quality_gate': 'PASS', 'tests': 'PASS', 'blockers': [], 'percent_complete': 100,
    }
    with pytest.raises(EvidenceError, match='WORKER_RESULT_NOT_TERMINAL'):
        EvidenceBuilder().build(plan=plan, step=item, route=route, skill=skill(), compiled_job=job, worker_result={**base, 'status': 'PROCESSING', 'production_touched': False})
    with pytest.raises(EvidenceError, match='WORKER_RESULT_PRODUCTION_TOUCHED'):
        EvidenceBuilder().build(plan=plan, step=item, route=route, skill=skill(), compiled_job=job, worker_result={**base, 'status': 'INTEGRATED', 'production_touched': True})


def test_redteam_report_is_deterministic_and_fail_closed():
    report = RedTeamRecorder().build([
        RedTeamFinding('B', 'scope', 'PASS', 'NO_ELIGIBLE_ROUTE', 'NO_ELIGIBLE_ROUTE'),
        RedTeamFinding('A', 'shell', 'PASS', 'ACTION_TYPE_FORBIDDEN', 'ACTION_TYPE_FORBIDDEN'),
    ])
    assert report.passed is True
    assert tuple(x.case_id for x in report.findings) == ('A', 'B')
    failed = RedTeamRecorder().build([RedTeamFinding('C', 'tamper', 'FAIL', 'DENY', 'ALLOW')])
    assert failed.passed is False
    assert failed.failed_cases == ('C',)
