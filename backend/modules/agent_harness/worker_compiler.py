from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from tools.mirror_sync.worker_job_factory import (
    CANONICAL_SUMMARY_LANGUAGE,
    CANONICAL_TARGET_BRANCH,
    CANONICAL_TARGET_REPO,
    WORKER_JOB_SCHEMA,
    _canonical_scheduling,
    canonicalize_job,
)

from .planner import PlanStep
from .router import RouteDecision

WORKER_SCHEMA = WORKER_JOB_SCHEMA
TARGET_REPO = CANONICAL_TARGET_REPO
TARGET_BRANCH = CANONICAL_TARGET_BRANCH
V2_ACTIONS = frozenset({'replace_text', 'insert_before', 'insert_after', 'append_once'})
ALLOWED_ACTIONS = frozenset({'replace_text', 'write_file', 'delete_file', 'insert_before', 'insert_after', 'append_once'})
ALLOWED_CHECKS = frozenset({'git_diff_check', 'py_compile', 'pytest', 'frontend_build'})
JOB_ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$')
SHA256_RE = re.compile(r'^[0-9a-f]{64}$')
GIT_SHA_RE = re.compile(r'^[0-9a-f]{40}$')
FORBIDDEN_KEYS = frozenset({
    'command',
    'commands',
    'shell',
    'script',
    'script_body',
    'production_allowed',
    'target_repo',
    'target_branch',
    'sql',
    'password',
    'passwd',
    'secret',
    'token',
    'credential',
})
V1_REPLACE_KEYS = frozenset({'old', 'new', 'expected_count'})
V2_MUTATION_KEYS = frozenset({'source_sha256', 'old_text', 'replacement', 'expected_occurrences', 'anchor'})


class WorkerCompileError(ValueError):
    pass


def _contains_forbidden_key(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in FORBIDDEN_KEYS or str(key).lower() in FORBIDDEN_KEYS:
                return True
            if _contains_forbidden_key(item):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def _plain_mapping(value: Mapping[str, object], field: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise WorkerCompileError(f'{field}_MUST_BE_OBJECT')
    result = dict(value)
    if _contains_forbidden_key(result):
        raise WorkerCompileError(f'{field}_FORBIDDEN_KEY')
    return result


def _safe_repo_path(value: object) -> str:
    if not isinstance(value, str):
        raise WorkerCompileError('ACTION_PATH_REQUIRED')
    raw = value.strip()
    if not raw:
        raise WorkerCompileError('ACTION_PATH_REQUIRED')
    if '\x00' in raw:
        raise WorkerCompileError('ACTION_PATH_INVALID')
    path = Path(raw)
    if path.is_absolute() or '..' in path.parts or (path.parts and path.parts[0] == '.git'):
        raise WorkerCompileError('ACTION_PATH_INVALID')
    return raw


def _validate_action(action: Mapping[str, object], *, require_v2: bool = False) -> dict[str, object]:
    result = _plain_mapping(action, 'ACTION')
    kind = str(result.get('type') or '')
    if kind not in ALLOWED_ACTIONS:
        raise WorkerCompileError('ACTION_TYPE_FORBIDDEN')
    result['path'] = _safe_repo_path(result.get('path'))

    has_v1 = any(key in result for key in V1_REPLACE_KEYS)
    has_v2 = kind in {'insert_before', 'insert_after', 'append_once'} or any(
        key in result for key in V2_MUTATION_KEYS
    )
    if has_v1 and has_v2:
        raise WorkerCompileError('ACTION_MIXED_V1_V2_KEYS')

    if has_v2 or (kind == 'replace_text' and require_v2 and not has_v1):
        if 'source_sha256' not in result or result.get('source_sha256') is None or result.get('source_sha256') == '':
            raise WorkerCompileError('ACTION_SOURCE_SHA256_REQUIRED')
        source_sha = result.get('source_sha256')
        if not isinstance(source_sha, str) or not SHA256_RE.fullmatch(source_sha):
            raise WorkerCompileError('ACTION_SOURCE_SHA256_INVALID')

        if 'expected_occurrences' not in result or result.get('expected_occurrences') is None:
            raise WorkerCompileError('ACTION_EXPECTED_OCCURRENCES_REQUIRED')
        expected_occurrences = result.get('expected_occurrences')
        if (
            not isinstance(expected_occurrences, int)
            or isinstance(expected_occurrences, bool)
            or expected_occurrences < 1
            or expected_occurrences > 1000
        ):
            raise WorkerCompileError('ACTION_EXPECTED_OCCURRENCES_INVALID')

        if not isinstance(result.get('replacement'), str):
            raise WorkerCompileError('ACTION_REPLACEMENT_REQUIRED')

        if kind == 'replace_text':
            if not isinstance(result.get('old_text'), str) or not result.get('old_text'):
                raise WorkerCompileError('ACTION_OLD_TEXT_REQUIRED')
            if 'anchor' in result:
                raise WorkerCompileError('ACTION_ANCHOR_FORBIDDEN')
        elif kind in {'insert_before', 'insert_after'}:
            if not isinstance(result.get('anchor'), str) or not result.get('anchor'):
                raise WorkerCompileError('ACTION_ANCHOR_REQUIRED')
            if 'old_text' in result:
                raise WorkerCompileError('ACTION_OLD_TEXT_FORBIDDEN')
        elif kind == 'append_once':
            if 'anchor' in result or 'old_text' in result:
                raise WorkerCompileError('ACTION_ANCHOR_OR_OLD_TEXT_FORBIDDEN')
        return result

    if kind == 'replace_text':
        if require_v2:
            raise WorkerCompileError('ACTION_V2_REQUIRED')
        if not isinstance(result.get('old'), str) or not result.get('old'):
            raise WorkerCompileError('ACTION_OLD_REQUIRED')
        if not isinstance(result.get('new'), str):
            raise WorkerCompileError('ACTION_NEW_REQUIRED')
        if 'expected_count' in result:
            count = result.get('expected_count')
            if not isinstance(count, int) or isinstance(count, bool) or count < 1 or count > 1000:
                raise WorkerCompileError('ACTION_EXPECTED_COUNT_INVALID')
    elif kind == 'write_file':
        if not isinstance(result.get('content'), str):
            raise WorkerCompileError('ACTION_CONTENT_REQUIRED')
        if 'expected_sha256' in result and result.get('expected_sha256') is not None:
            expected_sha = result.get('expected_sha256')
            if not isinstance(expected_sha, str) or not SHA256_RE.fullmatch(expected_sha):
                raise WorkerCompileError('ACTION_EXPECTED_SHA256_INVALID')
    elif kind == 'delete_file':
        expected_sha = result.get('expected_sha256')
        if not isinstance(expected_sha, str) or not expected_sha:
            raise WorkerCompileError('ACTION_EXPECTED_SHA256_REQUIRED')
        if not SHA256_RE.fullmatch(expected_sha):
            raise WorkerCompileError('ACTION_EXPECTED_SHA256_INVALID')
    return result


def _validate_check(check: Mapping[str, object]) -> dict[str, object]:
    result = _plain_mapping(check, 'CHECK')
    kind = str(result.get('type') or '')
    if kind not in ALLOWED_CHECKS:
        raise WorkerCompileError('CHECK_TYPE_FORBIDDEN')
    return result


def _default_rbac_authorizer(requester: dict[str, Any]) -> Mapping[str, Any]:
    try:
        from tools.mirror_sync.worker_requester_rbac import authorize_requester
    except ImportError as exc:
        raise WorkerCompileError('WORKER_REQUESTER_RBAC_UNAVAILABLE') from exc
    return authorize_requester(requester)


def derive_authorized_requester(
    authorized_identity: Mapping[str, object] | None,
    *,
    requester: Mapping[str, object] | None = None,
    source: str = '',
    project: str = '',
    chat: str = '',
    rbac_authorizer: Callable[[dict[str, Any]], Mapping[str, Any]] | None = None,
) -> dict[str, object]:
    if authorized_identity is None and requester is None:
        raise WorkerCompileError('AUTHORIZED_IDENTITY_REQUIRED:REQUESTER_REQUIRED')

    identity_map: dict[str, object] = {}
    identity_email = ''
    if authorized_identity is not None:
        identity_map = _plain_mapping(authorized_identity, 'AUTHORIZED_IDENTITY')
        if identity_map.get('active') is False or identity_map.get('Activo') is False:
            raise WorkerCompileError('REQUESTER_RBAC_DENIED:REQUESTER_INACTIVE')
        identity_email = str(
            identity_map.get('email')
            or identity_map.get('Email')
            or identity_map.get('user_email')
            or ''
        ).strip().lower()
        if not identity_email or '@' not in identity_email:
            raise WorkerCompileError('AUTHORIZED_IDENTITY_EMAIL_INVALID')

    requester_map: dict[str, object] = {}
    requester_email = ''
    if requester is not None:
        requester_map = _plain_mapping(requester, 'REQUESTER')
        requester_email = str(requester_map.get('email') or '').strip().lower()
        if authorized_identity is not None and requester_email and requester_email != identity_email:
            raise WorkerCompileError('REQUESTER_IDENTITY_MISMATCH')

    resolved_email = identity_email if authorized_identity is not None else requester_email
    if not resolved_email or '@' not in resolved_email:
        raise WorkerCompileError('REQUESTER_EMAIL_INVALID')

    resolved_source = str(
        source
        or requester_map.get('source')
        or identity_map.get('source')
        or identity_map.get('request_source')
        or ''
    ).strip()
    if not resolved_source:
        raise WorkerCompileError('REQUESTER_SOURCE_REQUIRED')

    resolved_project = str(
        project
        or requester_map.get('project')
        or identity_map.get('project')
        or ''
    ).strip()
    resolved_chat = str(
        chat
        or requester_map.get('chat')
        or identity_map.get('chat')
        or ''
    ).strip()

    candidate: dict[str, Any] = {
        'email': resolved_email,
        'source': resolved_source,
        'project': resolved_project,
        'chat': resolved_chat,
    }
    authorizer = rbac_authorizer or _default_rbac_authorizer
    decision = dict(authorizer(candidate))
    if not bool(decision.get('allowed')):
        reason = str(decision.get('reason') or 'REQUESTER_DENIED').strip()
        raise WorkerCompileError(f'REQUESTER_RBAC_DENIED:{reason}')

    canonical_email = str(decision.get('email') or resolved_email).strip().lower()
    if not canonical_email or '@' not in canonical_email:
        raise WorkerCompileError('REQUESTER_EMAIL_INVALID')

    return {
        'email': canonical_email,
        'source': resolved_source,
        'project': resolved_project,
        'chat': resolved_chat,
    }


@dataclass(frozen=True)
class WorkerCompileRequest:
    job_id: str
    objective: str
    step: PlanStep
    route: RouteDecision
    actions: tuple[Mapping[str, object], ...]
    checks: tuple[Mapping[str, object], ...] = ({'type': 'git_diff_check'},)
    human_summary_language: str = CANONICAL_SUMMARY_LANGUAGE
    human_summary_level: str = '13yo-non-programmer'
    requester: Mapping[str, object] | None = None
    authorized_identity: Mapping[str, object] | None = None
    base_sha: str | None = None
    scheduling: Mapping[str, object] | None = None
    mode: str = 'MUTATION'
    for_publication: bool = False

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
        if self.human_summary_language != CANONICAL_SUMMARY_LANGUAGE:
            raise WorkerCompileError('SUMMARY_LANGUAGE_MUST_BE_ES')
        if str(self.mode or '') != 'MUTATION':
            raise WorkerCompileError('WORKER_MODE_INVALID')
        if self.base_sha is not None:
            if not isinstance(self.base_sha, str) or not GIT_SHA_RE.fullmatch(self.base_sha):
                raise WorkerCompileError('BASE_SHA_INVALID')
        if self.requester is not None:
            _plain_mapping(self.requester, 'REQUESTER')
        if self.authorized_identity is not None:
            _plain_mapping(self.authorized_identity, 'AUTHORIZED_IDENTITY')
        if self.scheduling is not None:
            _plain_mapping(self.scheduling, 'SCHEDULING')


class WorkerCompiler:
    def __init__(
        self,
        *,
        rbac_authorizer: Callable[[dict[str, Any]], Mapping[str, Any]] | None = None,
    ) -> None:
        self._rbac_authorizer = rbac_authorizer

    def compile(
        self,
        request: WorkerCompileRequest,
        *,
        for_publication: bool = False,
    ) -> dict[str, object]:
        if not isinstance(request, WorkerCompileRequest):
            raise WorkerCompileError('WORKER_COMPILE_REQUEST_REQUIRED')
        must_publish = bool(for_publication or request.for_publication)
        has_identity = must_publish or request.requester is not None or request.authorized_identity is not None

        actions = [_validate_action(action, require_v2=must_publish) for action in request.actions]
        checks = [_validate_check(check) for check in request.checks]
        if not checks:
            raise WorkerCompileError('CHECKS_REQUIRED')

        job: dict[str, object] = {
            'schema': WORKER_SCHEMA,
            'job_id': request.job_id,
            'target_repo': TARGET_REPO,
            'target_branch': TARGET_BRANCH,
            'production_allowed': False,
            'mode': request.mode,
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
        if request.base_sha is not None:
            job['base_sha'] = request.base_sha
        if request.scheduling is not None:
            job['scheduling'] = _plain_mapping(request.scheduling, 'SCHEDULING')

        if has_identity:
            resolved_requester = derive_authorized_requester(
                request.authorized_identity,
                requester=request.requester,
                rbac_authorizer=self._rbac_authorizer,
            )
            job['requester'] = resolved_requester
            job = self._canonicalize_with_factory(job)
        elif request.scheduling is not None:
            job['scheduling'] = _canonical_scheduling(job, {})

        self._validate_with_worker_bridge(job)
        return job

    def compile_for_publication(self, request: WorkerCompileRequest) -> dict[str, object]:
        return self.compile(request, for_publication=True)

    @staticmethod
    def _canonicalize_with_factory(job: dict[str, object]) -> dict[str, object]:
        try:
            return canonicalize_job(job)
        except ValueError as exc:
            raise WorkerCompileError(str(exc)) from exc

    @staticmethod
    def _validate_with_worker_bridge(job: dict[str, object]) -> None:
        try:
            from tools.mirror_sync.universal_job_bridge import validate
        except ImportError as exc:
            raise WorkerCompileError('WORKER_BRIDGE_UNAVAILABLE') from exc
        errors = validate(job)
        if errors:
            raise WorkerCompileError('WORKER_JOB_INVALID:' + ','.join(errors))
