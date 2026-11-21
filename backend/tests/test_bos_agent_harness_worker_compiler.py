from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from modules.agent_harness.evidence import EvidenceBuilder
from modules.agent_harness.planner import Planner, PlanStep
from modules.agent_harness.registry import SkillSpec
from modules.agent_harness.router import RouteDecision
from modules.agent_harness.worker_compiler import (
    TARGET_BRANCH,
    TARGET_REPO,
    WorkerCompileError,
    WorkerCompileRequest,
    WorkerCompiler,
    derive_authorized_requester,
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


def skill(**overrides):
    values = dict(
        id='repo-change', version='1', source='BOS_NATIVE', origin='BOS',
        domain='engineering', description='repository change', entrypoint='worker',
        provenance='BOS_NATIVE', checksum='abc123',
        required_capabilities=('CODE_WRITE',), allowed_scopes=('repo:rbalam/EDARSA_HUB',),
        max_risk='R2', allowed_data_classifications=('PUBLIC', 'INTERNAL'),
        allowed_executors=('worker',), lifecycle='APPROVED', adoption='NATIVE',
    )
    values.update(overrides)
    return SkillSpec(**values)


def v2_replace_action(**overrides):
    values = dict(
        type='replace_text',
        path='backend/modules/example/generated.py',
        source_sha256='a' * 64,
        old_text='x = 1\n',
        replacement='x = 2\n',
        expected_occurrences=1,
    )
    values.update(overrides)
    return values


def superadmin_rbac(requester):
    return {
        'allowed': True,
        'reason': 'SUPERADMIN_CANONICAL',
        'usuario_id': 8,
        'email': str(requester.get('email') or '').strip().lower(),
        'role_code': 'SUPERADMIN',
        'role': 'SUPERADMINISTRADOR',
        'auth_source': 'SQL_USUARIO_CATALOGO',
    }


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
    assert job['mode'] == 'MUTATION'
    assert 'requester' not in job
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


def test_compile_for_publication_reuses_canonical_factory_and_rbac():
    compiler = WorkerCompiler(rbac_authorizer=superadmin_rbac)
    req = request(
        actions=(v2_replace_action(),),
        authorized_identity={
            'email': 'Ricardo@Edarsa.com.mx',
            'source': 'COPILOT',
            'project': 'EDARSAHUB-BOS',
            'chat': 'G1B-COMPILER',
        },
        base_sha='b' * 40,
    )
    job = compiler.compile_for_publication(req)
    assert job['schema'] == 'edarsahub.worker-job.v2'
    assert job['requester'] == {
        'email': 'ricardo@edarsa.com.mx',
        'source': 'COPILOT',
        'project': 'EDARSAHUB-BOS',
        'chat': 'G1B-COMPILER',
    }
    assert job['scheduling']['project_id'] == 'EDARSAHUB-BOS'
    assert job['scheduling']['bounded_context'] == 'EDARSAHUB-BOS'
    assert job['scheduling']['conflict_domains'] == ['GLOBAL_GIT_WRITER']
    assert job['base_sha'] == 'b' * 40
    assert validate(job) == []


def test_compile_for_publication_never_fabricates_requester_and_enforces_rbac():
    compiler = WorkerCompiler(rbac_authorizer=superadmin_rbac)
    with pytest.raises(WorkerCompileError, match='REQUESTER_REQUIRED'):
        compiler.compile_for_publication(request(actions=(v2_replace_action(),)))

    with pytest.raises(WorkerCompileError, match='REQUESTER_IDENTITY_MISMATCH'):
        compiler.compile_for_publication(
            request(
                actions=(v2_replace_action(),),
                authorized_identity={'email': 'ricardo@edarsa.com.mx', 'source': 'COPILOT'},
                requester={'email': 'otro@edarsa.com.mx', 'source': 'COPILOT'},
            )
        )

    denied_compiler = WorkerCompiler(
        rbac_authorizer=lambda _: {'allowed': False, 'reason': 'REQUESTER_NOT_SUPERADMIN'}
    )
    with pytest.raises(WorkerCompileError, match='REQUESTER_RBAC_DENIED:REQUESTER_NOT_SUPERADMIN'):
        denied_compiler.compile_for_publication(
            request(
                actions=(v2_replace_action(),),
                authorized_identity={'email': 'visor@edarsa.com.mx', 'source': 'COPILOT'},
            )
        )

    with pytest.raises(WorkerCompileError, match='REQUESTER_RBAC_DENIED:REQUESTER_INACTIVE'):
        derive_authorized_requester(
            {'email': 'ricardo@edarsa.com.mx', 'active': False, 'source': 'COPILOT'},
            rbac_authorizer=superadmin_rbac,
        )


def test_compile_never_fabricates_v2_source_sha256_or_expected_occurrences():
    compiler = WorkerCompiler(rbac_authorizer=superadmin_rbac)
    missing_sha = v2_replace_action()
    del missing_sha['source_sha256']
    with pytest.raises(WorkerCompileError, match='ACTION_SOURCE_SHA256_REQUIRED'):
        compiler.compile(request(actions=(missing_sha,)))

    missing_occ = v2_replace_action()
    del missing_occ['expected_occurrences']
    with pytest.raises(WorkerCompileError, match='ACTION_EXPECTED_OCCURRENCES_REQUIRED'):
        compiler.compile(request(actions=(missing_occ,)))

    with pytest.raises(WorkerCompileError, match='ACTION_MIXED_V1_V2_KEYS'):
        compiler.compile(
            request(actions=({**v2_replace_action(), 'old': 'x = 1\n', 'new': 'x = 2\n'},))
        )

    with pytest.raises(WorkerCompileError, match='ACTION_V2_REQUIRED'):
        compiler.compile_for_publication(
            request(
                actions=({'type': 'replace_text', 'path': 'backend/modules/example/x.py', 'old': 'a', 'new': 'b'},),
                authorized_identity={'email': 'ricardo@edarsa.com.mx', 'source': 'COPILOT'},
            )
        )


def test_compile_supports_v2_insert_and_append_actions_and_evidence_builder():
    compiler = WorkerCompiler(rbac_authorizer=superadmin_rbac)
    actions = (
        v2_replace_action(),
        {
            'type': 'insert_before',
            'path': 'backend/modules/example/generated.py',
            'source_sha256': 'c' * 64,
            'anchor': 'x = 2\n',
            'replacement': '# header\n',
            'expected_occurrences': 1,
        },
        {
            'type': 'append_once',
            'path': 'backend/modules/example/generated.py',
            'source_sha256': 'd' * 64,
            'replacement': '# footer\n',
            'expected_occurrences': 1,
        },
    )
    item = step()
    rt = route()
    plan = Planner().build('req-g1b', [item])
    job = compiler.compile_for_publication(
        request(
            job_id='AH4-g1b-v2-job',
            step=item,
            route=rt,
            actions=actions,
            authorized_identity={
                'email': 'ricardo@edarsa.com.mx',
                'source': 'COPILOT',
                'project': 'EDARSAHUB-BOS',
                'chat': 'G1B-COMPILER',
            },
        )
    )
    record = EvidenceBuilder().build(
        plan=plan,
        step=item,
        route=rt,
        skill=skill(),
        compiled_job=job,
        worker_result={
            'job_id': 'AH4-g1b-v2-job',
            'source_repo': TARGET_REPO,
            'source_branch': TARGET_BRANCH,
            'status': 'INTEGRATED',
            'certification': 'CERTIFIED',
            'quality_gate': 'PASS',
            'tests': 'PASS',
            'production_touched': False,
            'blockers': [],
            'percent_complete': 100,
        },
    )
    assert EvidenceBuilder.is_certified_success(record) is True
