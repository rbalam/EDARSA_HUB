"""Objective certification regression tests."""
import ast
import textwrap
from pathlib import Path

from tools.mirror_sync.universal_job_bridge import validate


def job():
    return {
        "schema": "edarsahub.worker-job.v2",
        "job_id": "BOS-OBJECTIVE-R2-TEST",
        "target_repo": "rbalam/EDARSA_HUB",
        "target_branch": "Edarsahub_Desarrollo",
        "production_allowed": False,
        "objective": "Verify acceptance contract",
        "human_summary_language": "es",
        "mode": "READ_ONLY",
        "actions": [],
        "checks": [{"type": "git_diff_check"}],
    }


def criterion():
    return {
        "id": "proof",
        "check_index": 0,
        "evidence_key": "proof",
        "expected_value": "verified",
    }


def evaluator():
    source = (
        Path(__file__).resolve().parents[2]
        / "tools/mirror_sync/universal_job_dispatcher.py"
    ).read_text(encoding="utf-8")

    tree = ast.parse(source)

    matches = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "evaluate_objective_criteria"
    ]

    assert len(matches) == 1

    node = matches[0]
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)

    namespace = {}
    exec(compile(module, "<objective-evaluator>", "exec"), namespace)
    return namespace["evaluate_objective_criteria"]


def test_legacy_compatibility():
    assert not any(
        "ACCEPTANCE" in error for error in validate(job())
    )


def test_valid_contract():
    request = job()
    request["acceptance_criteria"] = [criterion()]
    assert not any(
        "ACCEPTANCE" in error for error in validate(request)
    )


def test_missing_evidence_is_pending():
    evaluate = evaluator()
    status, evidence = evaluate(
        [criterion()],
        [{"status": "PASS"}],
        [],
    )
    assert status == "OBJECTIVE_PENDING"
    assert not evidence[0]["satisfied"]


def test_matching_evidence_is_certified():
    evaluate = evaluator()
    status, evidence = evaluate(
        [criterion()],
        [{"status": "PASS", "proof": "verified"}],
        [],
    )
    assert status == "OBJECTIVE_CERTIFIED"
    assert evidence[0]["satisfied"]


def test_failed_check_is_pending():
    evaluate = evaluator()
    status, _ = evaluate(
        [criterion()],
        [{"status": "FAIL", "proof": "verified"}],
        [],
    )
    assert status == "OBJECTIVE_PENDING"


def test_blockers_prevent_certification():
    evaluate = evaluator()
    status, _ = evaluate(
        [criterion()],
        [{"status": "PASS", "proof": "verified"}],
        ["blocking_error"],
    )
    assert status == "OBJECTIVE_PENDING"


def test_invalid_check_index_rejected():
    request = job()
    item = criterion()
    item["check_index"] = 99
    request["acceptance_criteria"] = [item]
    assert "ACCEPTANCE_1_CHECK_INDEX_INVALID" in validate(request)


def test_empty_criteria_rejected():
    request = job()
    request["acceptance_criteria"] = []
    assert "ACCEPTANCE_CRITERIA_INVALID" in validate(request)
