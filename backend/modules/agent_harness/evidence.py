from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Mapping

from .planner import Plan, PlanStep
from .registry import SkillSpec
from .router import RouteDecision
from .worker_compiler import TARGET_BRANCH, TARGET_REPO, WORKER_SCHEMA

EVIDENCE_SCHEMA = 'edarsahub.bos-evidence.v1'
TERMINAL_STATUSES = frozenset({'INTEGRATED', 'BLOCKED', 'REJECTED', 'FAILED'})


class EvidenceError(ValueError):
    pass


def _token(value: object, field: str) -> str:
    token = str(value or '').strip()
    if not token:
        raise EvidenceError(f'{field}_REQUIRED')
    return token


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=str).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class EvidenceRecord:
    request_id: str
    plan_sha256: str
    step_id: str
    agent_id: str
    agent_version: str
    skill_id: str
    skill_version: str
    skill_provenance: str
    skill_checksum: str
    worker_job_id: str
    worker_job_sha256: str
    worker_result_status: str
    worker_result_certification: str
    worker_result_quality_gate: str
    worker_result_tests: str
    worker_result_sha: str
    production_touched: bool
    schema: str = EVIDENCE_SCHEMA


class EvidenceBuilder:
    def build(
        self,
        *,
        plan: Plan,
        step: PlanStep,
        route: RouteDecision,
        skill: SkillSpec,
        compiled_job: Mapping[str, object],
        worker_result: Mapping[str, object],
    ) -> EvidenceRecord:
        if not isinstance(plan, Plan):
            raise EvidenceError('PLAN_REQUIRED')
        if not isinstance(step, PlanStep):
            raise EvidenceError('PLAN_STEP_REQUIRED')
        if not isinstance(route, RouteDecision):
            raise EvidenceError('ROUTE_DECISION_REQUIRED')
        if not isinstance(skill, SkillSpec):
            raise EvidenceError('SKILL_SPEC_REQUIRED')
        if step.id not in {item.id for item in plan.steps}:
            raise EvidenceError('STEP_NOT_IN_PLAN')
        if route.step_id != step.id:
            raise EvidenceError('ROUTE_STEP_MISMATCH')
        if route.skill_id != skill.id or route.skill_version != skill.version:
            raise EvidenceError('ROUTE_SKILL_MISMATCH')

        job = dict(compiled_job)
        result = dict(worker_result)
        if job.get('schema') != WORKER_SCHEMA:
            raise EvidenceError('WORKER_JOB_SCHEMA_INVALID')
        if job.get('target_repo') != TARGET_REPO or job.get('target_branch') != TARGET_BRANCH:
            raise EvidenceError('WORKER_JOB_TARGET_INVALID')
        if job.get('production_allowed') is not False:
            raise EvidenceError('WORKER_JOB_PRODUCTION_FORBIDDEN')

        context = job.get('harness_context')
        if not isinstance(context, Mapping):
            raise EvidenceError('HARNESS_CONTEXT_REQUIRED')
        expected_context = {
            'plan_step_id': step.id,
            'agent_id': route.agent_id,
            'agent_version': route.agent_version,
            'skill_id': route.skill_id,
            'skill_version': route.skill_version,
            'executor': route.executor,
        }
        for key, expected in expected_context.items():
            if context.get(key) != expected:
                raise EvidenceError(f'HARNESS_CONTEXT_{key.upper()}_MISMATCH')

        job_id = _token(job.get('job_id'), 'WORKER_JOB_ID')
        if result.get('job_id') != job_id:
            raise EvidenceError('WORKER_RESULT_JOB_MISMATCH')
        if result.get('source_repo') != TARGET_REPO or result.get('source_branch') != TARGET_BRANCH:
            raise EvidenceError('WORKER_RESULT_TARGET_MISMATCH')
        status = _token(result.get('status'), 'WORKER_RESULT_STATUS')
        if status not in TERMINAL_STATUSES:
            raise EvidenceError('WORKER_RESULT_NOT_TERMINAL')
        if result.get('production_touched') is not False:
            raise EvidenceError('WORKER_RESULT_PRODUCTION_TOUCHED')

        plan_payload = {
            'schema': plan.schema,
            'request_id': plan.request_id,
            'steps': [asdict(item) for item in plan.topological_steps()],
        }
        result_sha = canonical_sha256(result)
        return EvidenceRecord(
            request_id=plan.request_id,
            plan_sha256=canonical_sha256(plan_payload),
            step_id=step.id,
            agent_id=route.agent_id,
            agent_version=route.agent_version,
            skill_id=skill.id,
            skill_version=skill.version,
            skill_provenance=skill.provenance,
            skill_checksum=skill.checksum,
            worker_job_id=job_id,
            worker_job_sha256=canonical_sha256(job),
            worker_result_status=status,
            worker_result_certification=str(result.get('certification') or ''),
            worker_result_quality_gate=str(result.get('quality_gate') or ''),
            worker_result_tests=str(result.get('tests') or ''),
            worker_result_sha=result_sha,
            production_touched=False,
        )

    @staticmethod
    def is_certified_success(record: EvidenceRecord) -> bool:
        if not isinstance(record, EvidenceRecord):
            raise EvidenceError('EVIDENCE_RECORD_REQUIRED')
        return (
            record.worker_result_status == 'INTEGRATED'
            and record.worker_result_certification == 'CERTIFIED'
            and record.worker_result_quality_gate == 'PASS'
            and record.worker_result_tests == 'PASS'
            and record.production_touched is False
        )
