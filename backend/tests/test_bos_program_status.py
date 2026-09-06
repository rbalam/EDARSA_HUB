from core.bos_program_status import (
    FrontSpec,
    MilestoneSpec,
    evaluate_program,
)


def certified_result():
    return {
        'status': 'INTEGRATED',
        'certification': 'CERTIFIED',
        'work_completion': 'COMPLETE',
        'quality_gate': 'PASS',
        'percent_complete': 100,
        'production_touched': False,
        'blockers': [],
    }


def program_spec():
    return (
        FrontSpec(
            front_id='foundation',
            milestones=(
                MilestoneSpec('architecture', ('JOB-A',)),
                MilestoneSpec('canonical-data', ('JOB-B',)),
            ),
        ),
        FrontSpec(
            front_id='governance',
            milestones=(MilestoneSpec('policy', ('JOB-C',)),),
        ),
    )


def test_program_is_100_only_when_every_required_milestone_is_certified():
    evidence = {job: certified_result() for job in ('JOB-A', 'JOB-B', 'JOB-C')}
    status = evaluate_program(program_spec(), evidence)
    assert status.percent_complete == 100.0
    assert status.certified is True


def test_missing_evidence_prevents_100_and_reports_objective_progress():
    evidence = {'JOB-A': certified_result(), 'JOB-C': certified_result()}
    status = evaluate_program(program_spec(), evidence)
    assert status.percent_complete == 66.67
    assert status.certified is False
    foundation = status.fronts[0]
    assert foundation.percent_complete == 50.0
    assert foundation.certified is False


def test_pending_audit_evidence_does_not_count_as_certified():
    pending = certified_result()
    pending['certification'] = 'PENDING_AUDIT_EVIDENCE'
    evidence = {'JOB-A': pending, 'JOB-B': certified_result(), 'JOB-C': certified_result()}
    status = evaluate_program(program_spec(), evidence)
    assert status.percent_complete == 66.67
    assert status.certified is False


def test_production_touch_prevents_certification():
    touched = certified_result()
    touched['production_touched'] = True
    evidence = {'JOB-A': touched, 'JOB-B': certified_result(), 'JOB-C': certified_result()}
    status = evaluate_program(program_spec(), evidence)
    assert status.certified is False
    assert status.percent_complete == 66.67


def test_blockers_prevent_certification():
    blocked = certified_result()
    blocked['blockers'] = ['REAL_BLOCKER']
    evidence = {'JOB-A': blocked, 'JOB-B': certified_result(), 'JOB-C': certified_result()}
    status = evaluate_program(program_spec(), evidence)
    assert status.certified is False


def test_alternative_certified_evidence_can_satisfy_a_milestone():
    spec = (
        FrontSpec(
            front_id='runtime',
            milestones=(MilestoneSpec('runtime-cert', ('JOB-OLD', 'JOB-R2')),),
        ),
    )
    evidence = {'JOB-R2': certified_result()}
    status = evaluate_program(spec, evidence)
    assert status.certified is True
    assert status.fronts[0].milestones[0].matched_job_id == 'JOB-R2'


def test_empty_specs_never_claim_completion():
    status = evaluate_program((), {})
    assert status.percent_complete == 0.0
    assert status.certified is False
