import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mirror_sync.worker_deliverable_contract import (
    evaluate_deliverables,
    normalize_required_deliverables,
)


def test_legacy_job_without_required_deliverables_is_compatible():
    assert normalize_required_deliverables(None) == ()


def test_required_deliverables_normalize_to_uppercase():
    assert normalize_required_deliverables(
        ["executive_finding", "REUSE_MATRIX"]
    ) == (
        "EXECUTIVE_FINDING",
        "REUSE_MATRIX",
    )


def test_required_deliverables_duplicate_fails_closed():
    try:
        normalize_required_deliverables(
            ["EXECUTIVE_FINDING", "executive_finding"]
        )
    except ValueError as exc:
        assert str(exc) == "REQUIRED_DELIVERABLE_DUPLICATED"
    else:
        raise AssertionError("duplicate must fail")


def test_required_deliverables_invalid_name_fails_closed():
    try:
        normalize_required_deliverables(["free form"])
    except ValueError as exc:
        assert str(exc) == "REQUIRED_DELIVERABLE_INVALID"
    else:
        raise AssertionError("invalid name must fail")


def test_missing_deliverable_is_detected():
    evaluation = evaluate_deliverables(
        ["EXECUTIVE_FINDING", "REUSE_MATRIX"],
        {
            "EXECUTIVE_FINDING": {
                "finding": "present",
            },
        },
    )

    assert evaluation.complete is False
    assert evaluation.completed == ("EXECUTIVE_FINDING",)
    assert evaluation.missing == ("REUSE_MATRIX",)


def test_empty_deliverable_payload_is_not_complete():
    evaluation = evaluate_deliverables(
        ["EXECUTIVE_FINDING"],
        {
            "EXECUTIVE_FINDING": {},
        },
    )

    assert evaluation.complete is False


def test_complete_deliverables_are_complete():
    evaluation = evaluate_deliverables(
        ["EXECUTIVE_FINDING", "REUSE_MATRIX"],
        {
            "EXECUTIVE_FINDING": {
                "finding": "present",
            },
            "REUSE_MATRIX": {
                "rows": ["canonical"],
            },
        },
    )

    assert evaluation.complete is True
    assert evaluation.missing == ()


def load_module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def base_readonly_job():
    return {
        "schema": "edarsahub.worker-job.v2",
        "job_id": "DELIVERABLE-CONTRACT-TEST",
        "target_repo": "rbalam/EDARSA_HUB",
        "target_branch": "Edarsahub_Desarrollo",
        "production_allowed": False,
        "objective": "test",
        "human_summary_language": "es",
        "mode": "READ_ONLY",
        "actions": [],
        "checks": [
            {
                "type": "git_diff_check",
            }
        ],
    }


def test_bridge_accepts_valid_required_deliverables():
    bridge = load_module(
        "deliverable_bridge_valid",
        "tools/mirror_sync/universal_job_bridge.py",
    )

    job = base_readonly_job()
    job["required_deliverables"] = [
        "EXECUTIVE_FINDING",
        "REUSE_MATRIX",
    ]

    errors = bridge.validate(job)

    assert "REQUIRED_DELIVERABLE_INVALID" not in errors
    assert "REQUIRED_DELIVERABLE_DUPLICATED" not in errors


def test_bridge_rejects_duplicate_required_deliverables():
    bridge = load_module(
        "deliverable_bridge_duplicate",
        "tools/mirror_sync/universal_job_bridge.py",
    )

    job = base_readonly_job()
    job["required_deliverables"] = [
        "EXECUTIVE_FINDING",
        "executive_finding",
    ]

    errors = bridge.validate(job)

    assert "REQUIRED_DELIVERABLE_DUPLICATED" in errors


def generic_result():
    return {
        "schema": "edarsahub.worker-result.v2",
        "job_id": "DELIVERABLE-PUBLISHER-TEST",
        "status": "READ_ONLY_COMPLETE",
        "tests": "PASS",
        "quality_gate": "PASS",
        "production_touched": False,
        "blockers": [],
        "files_changed": [],
        "percent_complete": 100,
        "certification": "CERTIFIED_READ_ONLY",
        "checks": [
            {
                "type": "git_diff_check",
                "status": "PASS",
                "returncode": 0,
                "output": "",
            }
        ],
    }


def test_publisher_blocks_complete_when_required_deliverable_missing():
    publisher = load_module(
        "deliverable_publisher_missing",
        "tools/mirror_sync/universal_job_result_publisher.py",
    )

    result = generic_result()

    result["required_deliverables"] = [
        "EXECUTIVE_FINDING",
        "REUSE_MATRIX",
    ]

    result["deliverables"] = {
        "EXECUTIVE_FINDING": {
            "finding": "present",
        },
    }

    evidence = publisher.certification_evidence(result)

    assert evidence["certified"] is False
    assert evidence["certification"] == "PENDING_DELIVERABLES"
    assert evidence["work_completion"] == "PENDING_DELIVERABLES"
    assert evidence["percent_complete"] <= 95
    assert evidence["missing_deliverables"] == ["REUSE_MATRIX"]


def test_publisher_legacy_readonly_still_certifies():
    publisher = load_module(
        "deliverable_publisher_legacy",
        "tools/mirror_sync/universal_job_result_publisher.py",
    )

    result = generic_result()

    evidence = publisher.certification_evidence(result)

    assert evidence["certified"] is True
    assert evidence["certification"] == "CERTIFIED_READ_ONLY"
    assert evidence["work_completion"] == "COMPLETE"
    assert evidence["percent_complete"] == 100


def test_publisher_certifies_when_required_deliverables_complete():
    publisher = load_module(
        "deliverable_publisher_complete",
        "tools/mirror_sync/universal_job_result_publisher.py",
    )

    result = generic_result()

    result["required_deliverables"] = [
        "EXECUTIVE_FINDING",
    ]

    result["deliverables"] = {
        "EXECUTIVE_FINDING": {
            "finding": "present",
        },
    }

    evidence = publisher.certification_evidence(result)

    assert evidence["certified"] is True
    assert evidence["certification"] == "CERTIFIED_READ_ONLY"
    assert evidence["work_completion"] == "COMPLETE"
    assert evidence["percent_complete"] == 100
