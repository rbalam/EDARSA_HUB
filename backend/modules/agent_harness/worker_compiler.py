from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Mapping

from .planner import PlanStep
from .router import RouteDecision

WORKER_SCHEMA = 'edarsahub.worker-job.v2'
TARGET_REPO = 'rbalam/EDARSA_HUB'
TARGET_BRANCH = 'Edarsahub_Desarrollo'
ALLOWED_ACTIONS = frozenset({'replace_text', 'write_file', 'delete_file'})
ALLOWED_CHECKS = frozenset({'git_diff_check', 'py_compile', 'pytest', 'frontend_build'})
JOB_ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$')
FORBIDDEN_KEYS = frozenset({'command', 'commands', 'shell', 'script', 'script_body', 'production_allowed', 'target_repo', 'target_branch'})


class WorkerCompileError(ValueError):
    pass


def _plain_mapping(value: Mapping[str, object], field: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise WorkerCompileError(f'{field}_MUST_BE_OBJECT')
    result = dict(value)
    if any(str(key) in FORBIDDEN_KEYS for key in result):
        raise WorkerCompileError(f'{field}_FORBIDDEN_KEY')
    return result


def _validate_action(action: Mapping[str, object]) -> dict[str, object]:
    result = _plain_mapping(action, 'ACTION')
    kind = str(result.get('type') or '')
    if kind not in ALLOWED_ACTIONS:
        raise WorkerCompileError('ACTION_TYPE_FORBIDDEN')
    path = str(result.get('path') or '').strip()
    if not path:
        raise WorkerCompileError('ACTION_PATH_REQUIRED')
    if kind == 'replace_text':
        if not isinstance(result.get('old'), str) or not result.get('old'):
            raise WorkerCompileError('ACTION_OLD_REQUIRED')
        if not isinstance(result.get('new'), str):
            raise WorkerCompileError('ACTION_NEW_REQUIRED')
    elif kind == 'write_file':
        if not isinstance(result.get('content'), str):
            raise WorkerCompileError('ACTION_CONTENT_REQUIRED')
    elif kind == 'delete_file':
        if not isinstance(result.get('expected_sha256'), str):
            raise WorkerCompileError('ACTION_EXPECTED_SHA256_REQUIRED')
    return result


def _validate_check(check: Mapping[str, object]) -> dict[str, object]:
    result = _plain_mapping(check, 'CHECK')
    kind = str(result.get('type') or '')
    if kind not in ALLOWED_CHECKS:
        raise WorkerCompileError('CHECK_TYPE_FORBIDDEN')
    return result


@dataclass(frozen=True)
class WorkerCompileRequest:
    job_id: str
    objective: str
    step: PlanStep
    route: RouteDecision
    actions: tuple[Mapping[str, object], ...]
    checks: tuple[Mapping[str, object], ...] = ({'type': 'git_diff_check'},)
    human_summary_language: str = 'es'
    human_summary_level: str = '13yo-non-programmer'

    def __post_init__(self) -> None:
        if not JOB_ID_RE.fullmatch(str(self.job_id or '')):
            raise WorkerCompileError('JOB_ID_INVALID')
        if not str(self.objective or '').strip():
            raise WorkerCompileError('OBJECTIVE_REQUIRED')
        if not isinstance(self.step, PlanStep):
            raise WorkerCompileError('PLAN_STEP_REQUIRED')
        if not isinstance(self.route, RouteDecision):
            raise WorkerCompileError('ROUTE_DECISION_REQUIRED')
        if self.step.id != self.route.step_id:
            raise WorkerCompileError('ROUTE_STEP_MISMATCH')
        if self.step.executor != 'worker' or self.route.executor != 'worker':
            raise WorkerCompileError('WORKER_EXECUTOR_REQUIRED')
        if not self.actions:
            raise WorkerCompileError('ACTIONS_REQUIRED')
        if self.human_summary_language != 'es':
            raise WorkerCompileError('SUMMARY_LANGUAGE_MUST_BE_ES')


class WorkerCompiler:
    def compile(self, request: WorkerCompileRequest) -> dict[str, object]:
        if not isinstance(request, WorkerCompileRequest):
            raise WorkerCompileError('WORKER_COMPILE_REQUEST_REQUIRED')
        actions = [_validate_action(action) for action in request.actions]
        checks = [_validate_check(check) for check in request.checks]
        if not checks:
            raise WorkerCompileError('CHECKS_REQUIRED')
        job: dict[str, object] = {
            'schema': WORKER_SCHEMA,
            'job_id': request.job_id,
            'target_repo': TARGET_REPO,
            'target_branch': TARGET_BRANCH,
            'production_allowed': False,
            'objective': str(request.objective).strip(),
            'actions': actions,
            'checks': checks,
            'human_summary_language': request.human_summary_language,
            'human_summary_level': request.human_summary_level,
            'harness_context': {
                'plan_step_id': request.step.id,
                'domain': request.step.domain,
                'procedure': request.step.procedure,
                'risk': request.step.risk,
                'data_classification': request.step.data_classification,
                'agent_id': request.route.agent_id,
                'agent_version': request.route.agent_version,
                'skill_id': request.route.skill_id,
                'skill_version': request.route.skill_version,
                'executor': request.route.executor,
            },
        }
        self._validate_with_worker_bridge(job)
        return job

    @staticmethod
    def _validate_with_worker_bridge(job: dict[str, object]) -> None:
        try:
            from tools.mirror_sync.universal_job_bridge import validate
        except ImportError as exc:
            raise WorkerCompileError('WORKER_BRIDGE_UNAVAILABLE') from exc
        errors = validate(job)
        if errors:
            raise WorkerCompileError('WORKER_JOB_INVALID:' + ','.join(errors))
