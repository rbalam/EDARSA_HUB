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
