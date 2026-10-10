from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .planner import PlanStep, VALID_RISK
from .registry import AgentSpec, RegistryError, SkillSpec

RISK_RANK = {risk: index for index, risk in enumerate(VALID_RISK)}


class RouteError(ValueError):
    pass


@dataclass(frozen=True)
class RouteDecision:
    step_id: str
    agent_id: str
    agent_version: str
    skill_id: str
    skill_version: str
    executor: str


def _eligible_skill(step: PlanStep, skill: SkillSpec) -> bool:
    return (
        skill.lifecycle == 'APPROVED'
        and skill.adoption != 'BLOCKED'
        and skill.domain == step.domain
        and skill.id == step.procedure
        and set(step.required_capabilities).issubset(skill.required_capabilities)
        and set(step.required_scopes).issubset(skill.allowed_scopes)
        and RISK_RANK[step.risk] <= RISK_RANK[skill.max_risk]
        and step.data_classification in skill.allowed_data_classifications
        and step.executor in skill.allowed_executors
    )


def _eligible_agent(step: PlanStep, skill: SkillSpec, agent: AgentSpec) -> bool:
    return (
        agent.status == 'APPROVED'
        and step.domain in agent.domains
        and skill.id in agent.allowed_skills
        and set(step.required_capabilities).issubset(agent.capability_ceiling)
        and set(step.required_scopes).issubset(agent.scope_ceiling)
        and RISK_RANK[step.risk] <= RISK_RANK[agent.max_risk]
        and step.data_classification in agent.allowed_data_classifications
    )


def _privilege_score(step: PlanStep, skill: SkillSpec, agent: AgentSpec) -> tuple[int, int, int, int, int, str, str, str, str]:
    return (
        RISK_RANK[agent.max_risk],
        len(agent.capability_ceiling),
        len(agent.scope_ceiling),
        RISK_RANK[skill.max_risk],
        len(skill.allowed_scopes) + len(skill.required_capabilities),
        agent.id,
        agent.version,
        skill.id,
        skill.version,
    )


class Router:
    def route(
        self,
        step: PlanStep,
        agents: Iterable[AgentSpec],
        skills: Iterable[SkillSpec],
    ) -> RouteDecision:
        if not isinstance(step, PlanStep):
            raise RouteError('PLAN_STEP_REQUIRED')
        agents = tuple(agents)
        skills = tuple(skills)
        if not all(isinstance(agent, AgentSpec) for agent in agents):
            raise RouteError('AGENT_SPEC_REQUIRED')
        if not all(isinstance(skill, SkillSpec) for skill in skills):
            raise RouteError('SKILL_SPEC_REQUIRED')

        candidates: list[tuple[tuple[int, int, int, int, int, str, str, str, str], AgentSpec, SkillSpec]] = []
        for skill in skills:
            if not _eligible_skill(step, skill):
                continue
            for agent in agents:
                if _eligible_agent(step, skill, agent):
                    candidates.append((_privilege_score(step, skill, agent), agent, skill))

        if not candidates:
            raise RouteError('NO_ELIGIBLE_ROUTE')

        _, agent, skill = min(candidates, key=lambda candidate: candidate[0])
        return RouteDecision(
            step_id=step.id,
            agent_id=agent.id,
            agent_version=agent.version,
            skill_id=skill.id,
            skill_version=skill.version,
            executor=step.executor,
        )
