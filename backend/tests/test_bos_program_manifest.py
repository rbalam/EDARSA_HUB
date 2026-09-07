from core.bos_program_manifest import BOS_V1_FRONTS, bos_v1_fronts
from core.bos_program_status import evaluate_program


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


def all_job_ids():
    return tuple(
        job_id
        for front in BOS_V1_FRONTS
        for milestone in front.milestones
        for job_id in milestone.evidence_job_ids
    )


def test_manifest_contains_exactly_five_director_fronts():
    assert len(BOS_V1_FRONTS) == 5
    assert bos_v1_fronts() == BOS_V1_FRONTS


def test_manifest_maps_all_seven_program_gates_once():
    milestone_ids = [
        milestone.milestone_id
        for front in BOS_V1_FRONTS
        for milestone in front.milestones
    ]
    assert len(milestone_ids) == 7
    assert len(set(milestone_ids)) == 7
    assert {value.split('_')[1] for value in milestone_ids} == {'a', 'b', 'c', 'd', 'e', 'f', 'g'}


def test_missing_formal_gate_evidence_never_claims_progress():
    status = evaluate_program(BOS_V1_FRONTS, {})
    assert status.percent_complete == 0.0
    assert status.certified is False
    assert all(front.certified is False for front in status.fronts)


def test_only_formally_certified_gates_count():
    ids = all_job_ids()
    evidence = {ids[0]: certified_result(), ids[1]: certified_result()}
    status = evaluate_program(BOS_V1_FRONTS, evidence)
    assert status.percent_complete == 28.57
    assert status.certified is False


def test_all_seven_formal_gate_certifications_are_required_for_100():
    evidence = {job_id: certified_result() for job_id in all_job_ids()}
    status = evaluate_program(BOS_V1_FRONTS, evidence)
    assert status.percent_complete == 100.0
    assert status.certified is True


def test_partial_or_uncertified_gate_does_not_count():
    ids = all_job_ids()
    evidence = {job_id: certified_result() for job_id in ids}
    evidence[ids[-1]] = {**certified_result(), 'certification': 'PENDING_AUDIT_EVIDENCE'}
    status = evaluate_program(BOS_V1_FRONTS, evidence)
    assert status.percent_complete == 85.71
    assert status.certified is False
