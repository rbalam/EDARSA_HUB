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


def test_deliverable_specs_valid_generic_contract():
    from tools.mirror_sync.worker_deliverable_contract import (
        normalize_deliverable_specs,
    )

    value = normalize_deliverable_specs(
        {
            "EXAMPLE_OUTPUT": {
                "source": {
                    "check_type":
                        "repository_contract_audit",
                    "occurrence": 1,
                },
                "selector": {
                    "type": "json_path",
                    "path": [
                        "repository_evidence",
                    ],
                },
            }
        },
        ["EXAMPLE_OUTPUT"],
    )

    assert value["EXAMPLE_OUTPUT"]["source"][
        "occurrence"
    ] == 1


def test_deliverable_specs_must_reference_required_name():
    from tools.mirror_sync.worker_deliverable_contract import (
        normalize_deliverable_specs,
    )

    try:
        normalize_deliverable_specs(
            {
                "OTHER_OUTPUT": {
                    "source": {
                        "check_type":
                            "repository_contract_audit",
                        "occurrence": 1,
                    },
                    "selector": {
                        "type": "json_path",
                        "path": ["output"],
                    },
                }
            },
            ["EXAMPLE_OUTPUT"],
        )
    except ValueError as exc:
        assert (
            str(exc)
            == "DELIVERABLE_SPEC_NOT_REQUIRED"
        )
    else:
        raise AssertionError(
            "spec outside required deliverables must fail"
        )


def test_deliverable_source_requires_explicit_occurrence():
    from tools.mirror_sync.worker_deliverable_contract import (
        normalize_deliverable_specs,
    )

    try:
        normalize_deliverable_specs(
            {
                "EXAMPLE_OUTPUT": {
                    "source": {
                        "check_type":
                            "repository_contract_audit",
                    },
                    "selector": {
                        "type": "json_path",
                        "path": ["output"],
                    },
                }
            },
            ["EXAMPLE_OUTPUT"],
        )
    except ValueError as exc:
        assert (
            str(exc)
            == "DELIVERABLE_SOURCE_OCCURRENCE_INVALID"
        )
    else:
        raise AssertionError(
            "occurrence must be explicit"
        )


def test_generic_materializer_selects_nested_json():
    from tools.mirror_sync.worker_deliverable_contract import (
        materialize_deliverables,
    )

    checks = [
        {
            "type": "repository_contract_audit",
            "status": "PASS",
            "repository_evidence": {
                "summary": {
                    "matched_files": 12,
                }
            },
        }
    ]

    value = materialize_deliverables(
        ["EXAMPLE_OUTPUT"],
        {
            "EXAMPLE_OUTPUT": {
                "source": {
                    "check_type":
                        "repository_contract_audit",
                    "occurrence": 1,
                },
                "selector": {
                    "type": "json_path",
                    "path": [
                        "repository_evidence",
                        "summary",
                    ],
                },
            }
        },
        checks,
    )

    assert value == {
        "EXAMPLE_OUTPUT": {
            "matched_files": 12,
        }
    }


def test_generic_materializer_occurrence_is_deterministic():
    from tools.mirror_sync.worker_deliverable_contract import (
        materialize_deliverables,
    )

    checks = [
        {
            "type": "repository_contract_audit",
            "output": {"value": "first"},
        },
        {
            "type": "repository_contract_audit",
            "output": {"value": "second"},
        },
    ]

    value = materialize_deliverables(
        ["EXAMPLE_OUTPUT"],
        {
            "EXAMPLE_OUTPUT": {
                "source": {
                    "check_type":
                        "repository_contract_audit",
                    "occurrence": 2,
                },
                "selector": {
                    "type": "json_path",
                    "path": ["output"],
                },
            }
        },
        checks,
    )

    assert value == {
        "EXAMPLE_OUTPUT": {
            "value": "second",
        }
    }


def test_generic_materializer_unknown_source_fails_closed():
    from tools.mirror_sync.worker_deliverable_contract import (
        materialize_deliverables,
    )

    try:
        materialize_deliverables(
            ["EXAMPLE_OUTPUT"],
            {
                "EXAMPLE_OUTPUT": {
                    "source": {
                        "check_type":
                            "repository_contract_audit",
                        "occurrence": 1,
                    },
                    "selector": {
                        "type": "json_path",
                        "path": ["output"],
                    },
                }
            },
            [],
        )
    except ValueError as exc:
        assert (
            str(exc)
            == "DELIVERABLE_SOURCE_CHECK_NOT_FOUND"
        )
    else:
        raise AssertionError(
            "missing source must fail closed"
        )


def test_generic_materializer_invalid_path_fails_closed():
    from tools.mirror_sync.worker_deliverable_contract import (
        materialize_deliverables,
    )

    try:
        materialize_deliverables(
            ["EXAMPLE_OUTPUT"],
            {
                "EXAMPLE_OUTPUT": {
                    "source": {
                        "check_type": "git_diff_check",
                        "occurrence": 1,
                    },
                    "selector": {
                        "type": "json_path",
                        "path": ["does_not_exist"],
                    },
                }
            },
            [
                {
                    "type": "git_diff_check",
                    "status": "PASS",
                }
            ],
        )
    except ValueError as exc:
        assert (
            str(exc)
            == "DELIVERABLE_SELECTOR_PATH_NOT_FOUND"
        )
    else:
        raise AssertionError(
            "missing path must fail closed"
        )


def test_generic_materializer_empty_payload_remains_missing():
    from tools.mirror_sync.worker_deliverable_contract import (
        evaluate_deliverables,
        materialize_deliverables,
    )

    checks = [
        {
            "type": "repository_contract_audit",
            "payload": {},
        }
    ]

    materialized = materialize_deliverables(
        ["EXAMPLE_OUTPUT"],
        {
            "EXAMPLE_OUTPUT": {
                "source": {
                    "check_type":
                        "repository_contract_audit",
                    "occurrence": 1,
                },
                "selector": {
                    "type": "json_path",
                    "path": ["payload"],
                },
            }
        },
        checks,
    )

    assert materialized == {}

    evaluation = evaluate_deliverables(
        ["EXAMPLE_OUTPUT"],
        materialized,
    )

    assert evaluation.complete is False
    assert evaluation.missing == (
        "EXAMPLE_OUTPUT",
    )


def test_generic_materializer_has_no_domain_hardcode():
    source = (
        ROOT
        / "tools/mirror_sync/"
        "worker_deliverable_contract.py"
    ).read_text(encoding="utf-8")

    for token in (
        "TECHNICAL_MAP_V1",
        "COSTING_CONTRACT",
        "PURCHASING_REVERSE_EXPLOSION_CONTRACT",
        "GATE3_ALLOWED_DECISION",
    ):
        assert token not in source


def test_bridge_accepts_generic_deliverable_specs():
    bridge = load_module(
        "deliverable_bridge_specs",
        "tools/mirror_sync/universal_job_bridge.py",
    )

    job = base_readonly_job()

    job["required_deliverables"] = [
        "EXAMPLE_OUTPUT",
    ]

    job["deliverable_specs"] = {
        "EXAMPLE_OUTPUT": {
            "source": {
                "check_type":
                    "repository_contract_audit",
                "occurrence": 1,
            },
            "selector": {
                "type": "json_path",
                "path": ["output"],
            },
        }
    }

    errors = bridge.validate(job)

    assert not [
        value
        for value in errors
        if value.startswith("DELIVERABLE_")
    ]


def test_bridge_rejects_invalid_deliverable_specs():
    bridge = load_module(
        "deliverable_bridge_specs_invalid",
        "tools/mirror_sync/universal_job_bridge.py",
    )

    job = base_readonly_job()

    job["required_deliverables"] = [
        "EXAMPLE_OUTPUT",
    ]

    job["deliverable_specs"] = {
        "EXAMPLE_OUTPUT": {
            "source": {
                "check_type":
                    "repository_contract_audit",
            },
            "selector": {
                "type": "json_path",
                "path": ["output"],
            },
        }
    }

    errors = bridge.validate(job)

    assert (
        "DELIVERABLE_SOURCE_OCCURRENCE_INVALID"
        in errors
    )
