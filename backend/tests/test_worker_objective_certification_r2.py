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


# G3 - Semantic capability tests.
import importlib.util as _g3_importlib
import sys as _g3_sys
import pytest as _g3_pytest

def _g3_module():
    source = (
        Path(__file__).resolve().parents[1]
        / "modules/worker_ingress/semantic_capabilities.py"
    )
    spec = _g3_importlib.spec_from_file_location(
        "_g3_semantic_capabilities", source
    )
    module = _g3_importlib.module_from_spec(spec)
    _g3_sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def _g3_build(code, constraints, context="WORKER_INGRESS"):
    module = _g3_module()
    return module.resolve_capability(code).builder({
        "bounded_context": context,
        "constraints": constraints,
    })

def test_g3_registration():
    module = _g3_module()
    names = module.registered_capabilities()
    assert "REPOSITORY_CONTRACT_AUDIT" in names
    assert "REPOSITORY_CONTRACT_AUDIT_BOUNDED" in names
    assert "WORKER_RESULT_SEMANTIC_EXTRACT" in names

def test_g3_rh_compatibility():
    result = _g3_build("REPOSITORY_CONTRACT_AUDIT", {}, "RH")
    assert result["actions"] == []
    assert result["checks"][0]["request"]["max_results"] == 200

def test_g3_repository_valid():
    result = _g3_build("REPOSITORY_CONTRACT_AUDIT_BOUNDED", {
        "paths": ["backend/modules/worker_ingress/"],
        "search_terms": ["semantic"],
        "max_results": 10,
    })
    assert result["actions"] == []
    assert result["checks"][0]["type"] == "repository_contract_audit"

@_g3_pytest.mark.parametrize("path", [
    "../secret",
    "/etc/passwd",
    ".git/config",
    "backend/modules/../../secret",
    "backend/modules/.env",
    "backend/modules/node_modules/file",
    "backend/modules/auth/passwords.py",
])
def test_g3_repository_rejects_paths(path):
    with _g3_pytest.raises(ValueError):
        _g3_build("REPOSITORY_CONTRACT_AUDIT_BOUNDED", {
            "paths": [path],
            "search_terms": ["semantic"],
        })

def test_g3_result_valid():
    result = _g3_build("WORKER_RESULT_SEMANTIC_EXTRACT", {
        "source_job_id": "BOS-GATE1-TEST",
    })
    assert result["actions"] == []
    assert result["checks"][0]["request"]["source_result"] == {
        "branch": "worker/results",
        "path": "worker_queue/results/BOS-GATE1-TEST.json",
    }

@_g3_pytest.mark.parametrize("job_id", [
    "../secret", "bad/name", "", "x",
])
def test_g3_result_rejects_job_id(job_id):
    with _g3_pytest.raises(ValueError):
        _g3_build("WORKER_RESULT_SEMANTIC_EXTRACT", {
            "source_job_id": job_id,
        })

def test_g3_result_rejects_arbitrary_refs():
    with _g3_pytest.raises(ValueError):
        _g3_build("WORKER_RESULT_SEMANTIC_EXTRACT", {
            "source_job_id": "BOS-GATE1-TEST",
            "branch": "other",
        })
