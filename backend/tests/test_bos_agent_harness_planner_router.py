from __future__ import annotations

import pytest

from modules.agent_harness.planner import PlanError, Planner, PlanStep
from modules.agent_harness.registry import AgentSpec, SkillSpec
from modules.agent_harness.router import RouteError, Router


def approved_skill(**overrides):
    values = dict(
        id='repo-change', version='1', source='BOS_NATIVE', origin='BOS',
        domain='engineering', description='deterministic repository change',
        entrypoint='worker', provenance='BOS_NATIVE',
        required_capabilities=('CODE_WRITE',), allowed_scopes=('repo:rbalam/EDARSA_HUB',),
        max_risk='R2', allowed_data_classifications=('PUBLIC', 'INTERNAL'),
        allowed_executors=('worker',), lifecycle='APPROVED', adoption='NATIVE',
    )
    values.update(overrides)
    return SkillSpec(**values)


def approved_agent(**overrides):
    values = dict(
        id='bos-backend', version='1', role='backend', domains=('engineering',),
        status='APPROVED', allowed_skills=('repo-change',),
        capability_ceiling=('CODE_WRITE',), scope_ceiling=('repo:rbalam/EDARSA_HUB',),
        max_risk='R2', allowed_data_classifications=('PUBLIC', 'INTERNAL'),
        provenance='BOS_NATIVE',
    )
    values.update(overrides)
    return AgentSpec(**values)


def step(**overrides):
    values = dict(
        id='s1', domain='engineering', procedure='repo-change',
        required_capabilities=('CODE_WRITE',), required_scopes=('repo:rbalam/EDARSA_HUB',),
        risk='R1', data_classification='INTERNAL', executor='worker',
    )
    values.update(overrides)
    return PlanStep(**values)


def test_planner_is_deterministic_and_topological():
    planner = Planner()
    plan = planner.build('req-1', [
        step(id='b', depends_on=('a',)),
        step(id='a'),
        step(id='c', depends_on=('a',)),
    ])
    assert [item.id for item in plan.topological_steps()] == ['a', 'b', 'c']
    assert [item.id for item in plan.topological_steps()] == ['a', 'b', 'c']


def test_planner_rejects_cycle():
    with pytest.raises(PlanError, match='PLAN_CYCLE_DETECTED'):
        Planner().build('req-1', [step(id='a', depends_on=('b',)), step(id='b', depends_on=('a',))])


def test_planner_rejects_missing_dependency():
    with pytest.raises(PlanError, match='PLAN_DEPENDENCY_NOT_FOUND'):
        Planner().build('req-1', [step(id='a', depends_on=('missing',))])


def test_router_selects_least_privileged_agent():
    broad = approved_agent(
        id='broad', max_risk='R4',
        capability_ceiling=('CODE_WRITE', 'SQL_WRITE', 'EXTERNAL_EGRESS'),
        scope_ceiling=('repo:rbalam/EDARSA_HUB', 'sql:all'),
    )
    narrow = approved_agent(id='narrow', max_risk='R1')
    decision = Router().route(step(), [broad, narrow], [approved_skill()])
    assert decision.agent_id == 'narrow'
    assert decision.skill_id == 'repo-change'
    assert decision.executor == 'worker'


def test_router_fails_closed_when_agent_capability_is_insufficient():
    agent = approved_agent(capability_ceiling=())
    with pytest.raises(RouteError, match='NO_ELIGIBLE_ROUTE'):
        Router().route(step(), [agent], [approved_skill()])


def test_router_fails_closed_when_scope_is_insufficient():
    agent = approved_agent(scope_ceiling=('repo:other',))
    with pytest.raises(RouteError, match='NO_ELIGIBLE_ROUTE'):
        Router().route(step(), [agent], [approved_skill()])


def test_router_fails_closed_on_excess_risk():
    with pytest.raises(RouteError, match='NO_ELIGIBLE_ROUTE'):
        Router().route(step(risk='R3'), [approved_agent()], [approved_skill()])


def test_router_rejects_unapproved_skill_or_agent():
    with pytest.raises(RouteError, match='NO_ELIGIBLE_ROUTE'):
        Router().route(step(), [approved_agent(status='DRAFT')], [approved_skill()])
    with pytest.raises(RouteError, match='NO_ELIGIBLE_ROUTE'):
        Router().route(step(), [approved_agent()], [approved_skill(lifecycle='DRAFT')])


def test_router_rejects_wrong_executor_and_data_classification():
    with pytest.raises(RouteError, match='NO_ELIGIBLE_ROUTE'):
        Router().route(step(executor='communications'), [approved_agent()], [approved_skill()])
    with pytest.raises(RouteError, match='NO_ELIGIBLE_ROUTE'):
        Router().route(step(data_classification='PII'), [approved_agent()], [approved_skill()])
