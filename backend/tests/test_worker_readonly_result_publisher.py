from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def _publisher():
    spec = importlib.util.spec_from_file_location("worker_result_publisher_readonly", ROOT / "tools/mirror_sync/universal_job_result_publisher.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def _result():
    return {
        "status": "READ_ONLY_COMPLETE",
        "tests": "PASS",
        "quality_gate": "PASS",
        "production_touched": False,
        "blockers": [],
        "percent_complete": 100,
        "checks": [{
            "type": "sql_readonly_audit",
            "status": "PASS",
            "sql_evidence": {
                "status": "PASS",
                "mode": "READ_ONLY_SQL",
                "connection": "readonly_sql_connection:default",
                "evidence": [{
                    "name": "metadata",
                    "columns": ["table_name", "password_hash"],
                    "rows": [["Cliente_Catalogo", "must-not-publish"]],
                    "row_count_returned": 1,
                    "truncated": False
                }]
            }
        }]
    }

def test_readonly_complete_certifies_with_structured_evidence():
    publisher = _publisher()
    evidence = publisher.certification_evidence(_result())
    assert evidence["certification"] == "CERTIFIED_READ_ONLY"
    assert evidence["percent_complete"] == 100

def test_sensitive_sql_values_are_redacted():
    publisher = _publisher()
    public = publisher.sanitize(_result())
    assert public["certification"] == "CERTIFIED_READ_ONLY"
    row = public["sql_readonly_evidence"]["checks"][0]["evidence"][0]["rows"][0]
    assert row == ["Cliente_Catalogo", "[REDACTED]"]
    assert "must-not-publish" not in json.dumps(public)

def test_readonly_without_evidence_is_not_certified():
    publisher = _publisher()
    result = _result()
    result["checks"] = []
    assert publisher.certification_evidence(result)["certification"] == "NOT_CERTIFIED"


def _generic_result():
    return {
        "status": "READ_ONLY_COMPLETE",
        "tests": "PASS",
        "quality_gate": "PASS",
        "production_touched": False,
        "blockers": [],
        "files_changed": [],
        "percent_complete": 100,
        "checks": [
            {"type": "py_compile", "status": "PASS"},
            {"type": "pytest", "status": "PASS"},
            {"type": "git_diff_check", "status": "PASS"},
        ],
    }


def test_generic_readonly_certifies_only_non_mutating_pass_checks():
    publisher = _publisher()
    evidence = publisher.certification_evidence(_generic_result())
    assert evidence["certification"] == "CERTIFIED_READ_ONLY"
    assert evidence["work_completion"] == "COMPLETE"
    assert evidence["percent_complete"] == 100
    assert evidence["certification_basis"] == "GENERIC_READ_ONLY_NON_MUTATING_CHECKS_PASS"


def test_generic_readonly_rejects_disallowed_or_failed_checks():
    publisher = _publisher()
    for check in (
        {"type": "frontend_build", "status": "PASS"},
        {"type": "sql_readonly_audit", "status": "PASS"},
        {"type": "unknown", "status": "PASS"},
        {"type": "pytest", "status": "FAIL"},
    ):
        result = _generic_result()
        result["checks"] = [check]
        assert publisher.certification_evidence(result)["certification"] == "NOT_CERTIFIED"


def test_generic_readonly_rejects_changed_files_production_or_blockers():
    publisher = _publisher()
    changed = _generic_result()
    changed["files_changed"] = ["backend/x.py"]
    assert publisher.certification_evidence(changed)["certification"] == "NOT_CERTIFIED"

    production = _generic_result()
    production["production_touched"] = True
    assert publisher.certification_evidence(production)["certification"] == "NOT_CERTIFIED"

    blocked = _generic_result()
    blocked["blockers"] = ["x"]
    assert publisher.certification_evidence(blocked)["certification"] == "NOT_CERTIFIED"
