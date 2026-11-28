from __future__ import annotations

import pytest

from modules.agent_harness.evidence import EvidenceBuilder, EvidenceError, canonical_sha256
from modules.agent_harness.planner import Planner, PlanStep
from modules.agent_harness.registry import SkillSpec
from modules.agent_harness.router import RouteDecision


def step():
    return PlanStep(
        id='s1', domain='engineering', procedure='repo-change',
        required_capabilities=('CODE_WRITE',), required_scopes=('repo:rbalam/EDARSA_HUB',),
        risk='R1', data_classification='INTERNAL', executor='worker',
    )


def route():
    return RouteDecision(
        step_id='s1', agent_id='bos-backend', agent_version='1',
        skill_id='repo-change', skill_version='1', executor='worker',
    )


def skill():
    return SkillSpec(
        id='repo-change', version='1', source='BOS_NATIVE', origin='BOS',
        domain='engineering', description='repository change', entrypoint='worker',
        provenance='BOS_NATIVE', checksum='abc123',
        required_capabilities=('CODE_WRITE',), allowed_scopes=('repo:rbalam/EDARSA_HUB',),
        max_risk='R2', allowed_data_classifications=('PUBLIC', 'INTERNAL'),
        allowed_executors=('worker',), lifecycle='APPROVED', adoption='NATIVE',
    )


def job():
    return {
        'schema': 'edarsahub.worker-job.v2',
        'job_id': 'evidence-test-job',
        'target_repo': 'rbalam/EDARSA_HUB',
        'target_branch': 'Edarsahub_Desarrollo',
        'production_allowed': False,
        'objective': 'test',
        'actions': [{'type': 'write_file', 'path': 'backend/modules/example/x.py', 'content': 'x=1\n'}],
        'checks': [{'type': 'git_diff_check'}],
        'human_summary_language': 'es',
        'human_summary_level': '13yo-non-programmer',
        'harness_context': {
            'plan_step_id': 's1', 'domain': 'engineering', 'procedure': 'repo-change',
            'risk': 'R1', 'data_classification': 'INTERNAL',
            'agent_id': 'bos-backend', 'agent_version': '1',
            'skill_id': 'repo-change', 'skill_version': '1', 'executor': 'worker',
        },
    }


def result(**overrides):
    values = dict(
        job_id='evidence-test-job', source_repo='rbalam/EDARSA_HUB',
        source_branch='Edarsahub_Desarrollo', status='INTEGRATED',
        certification='CERTIFIED', quality_gate='PASS', tests='PASS',
        production_touched=False, blockers=[], percent_complete=100,
    )
    values.update(overrides)
    return values


def build(worker_result=None):
    item = step()
    plan = Planner().build('req-1', [item])
    return EvidenceBuilder().build(
        plan=plan, step=item, route=route(), skill=skill(),
        compiled_job=job(), worker_result=worker_result or result(),
    )


def test_evidence_is_deterministic_and_certifies_success():
    first = build()
    second = build()
    assert first == second
    assert first.plan_sha256 == second.plan_sha256
    assert first.worker_job_sha256 == second.worker_job_sha256
    assert EvidenceBuilder.is_certified_success(first) is True


def test_canonical_hash_ignores_mapping_order():
    assert canonical_sha256({'a': 1, 'b': 2}) == canonical_sha256({'b': 2, 'a': 1})


def test_evidence_carries_skill_provenance_and_checksum():
    record = build()
    assert record.skill_provenance == 'BOS_NATIVE'
    assert record.skill_checksum == 'abc123'


def test_evidence_rejects_wrong_worker_job_id():
    with pytest.raises(EvidenceError, match='WORKER_RESULT_JOB_MISMATCH'):
        build(result(job_id='other'))


def test_evidence_rejects_nonterminal_result():
    with pytest.raises(EvidenceError, match='WORKER_RESULT_NOT_TERMINAL'):
        build(result(status='PROCESSING'))


def test_evidence_rejects_production_touched():
    with pytest.raises(EvidenceError, match='WORKER_RESULT_PRODUCTION_TOUCHED'):
        build(result(production_touched=True))


def test_evidence_rejects_wrong_target():
    with pytest.raises(EvidenceError, match='WORKER_RESULT_TARGET_MISMATCH'):
        build(result(source_branch='main'))


def test_evidence_rejects_harness_context_tampering():
    item = step()
    plan = Planner().build('req-1', [item])
    tampered = job()
    tampered['harness_context'] = dict(tampered['harness_context'])
    tampered['harness_context']['agent_id'] = 'other-agent'
    with pytest.raises(EvidenceError, match='HARNESS_CONTEXT_AGENT_ID_MISMATCH'):
        EvidenceBuilder().build(
            plan=plan, step=item, route=route(), skill=skill(),
            compiled_job=tampered, worker_result=result(),
        )


def test_blocked_result_is_evidence_but_not_certified_success():
    record = build(result(status='BLOCKED', certification='NOT_CERTIFIED', quality_gate='FAIL', tests='PASS'))
    assert EvidenceBuilder.is_certified_success(record) is False
