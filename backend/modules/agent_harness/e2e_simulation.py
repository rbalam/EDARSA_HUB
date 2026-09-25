from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .control_plane import BudgetEnvelope, ControlPlane, EvidenceSummary, GateState
from .evidence import EvidenceBuilder
from .planner import Planner, PlanStep
from .registry import AgentRegistry, AgentSpec, SkillRegistry, SkillSpec
from .router import Router
from .worker_compiler import WorkerCompileRequest, WorkerCompiler

SIMULATION_SCHEMA = 'edarsahub.bos-agent-harness-e2e-simulation.v1'


class SimulationError(ValueError):
    pass


@dataclass(frozen=True)
class SimulationResult:
    request_id: str
    step_id: str
    worker_job_id: str
    evidence_success: bool
    control_plane_healthy: bool
    schema: str = SIMULATION_SCHEMA


class AgentHarnessSimulation:
    def run(
        self,
        *,
        request_id: str,
        step: PlanStep,
        agent: AgentSpec,
        skill: SkillSpec,
        worker_result: Mapping[str, object],
        budget_limit: float = 100.0,
        budget_consumed: float = 0.0,
    ) -> SimulationResult:
        agents = AgentRegistry()
        skills = SkillRegistry()
        agents.register(agent)
        skills.register(skill)

        plan = Planner().build(request_id, [step])
        route = Router().route(step, [agent], [skill])
        compiled_job = WorkerCompiler().compile(
            WorkerCompileRequest(
                job_id=str(worker_result.get('job_id') or ''),
                objective='e2e-simulation',
                step=step,
                route=route,
                actions=({'type': 'write_file', 'path': 'backend/modules/example/e2e.py', 'content': 'x=1\n'},),
                checks=({'type': 'git_diff_check'},),
            )
        )
        evidence = EvidenceBuilder().build(
            plan=plan,
            step=step,
            route=route,
            skill=skill,
            compiled_job=compiled_job,
            worker_result=worker_result,
        )
        evidence_success = EvidenceBuilder.is_certified_success(evidence)
        snapshot = ControlPlane().snapshot(
            gates=[
                GateState(
                    gate_id='AH10-SIM',
                    status='CERTIFIED' if evidence_success else 'BLOCKED',
                    percent_complete=100 if evidence_success else 80,
                    blockers=() if evidence_success else ('evidence-not-certified',),
                    production_touched=False,
                )
            ],
            budgets=[BudgetEnvelope('simulation', budget_limit, budget_consumed)],
            evidence=[EvidenceSummary(request_id, compiled_job['job_id'], evidence_success, False)],
        )
        return SimulationResult(
            request_id=request_id,
            step_id=step.id,
            worker_job_id=compiled_job['job_id'],
            evidence_success=evidence_success,
            control_plane_healthy=snapshot.healthy,
        )
