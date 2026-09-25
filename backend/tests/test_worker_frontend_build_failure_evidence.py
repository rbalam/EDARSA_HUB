import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PUBLISHER = ROOT / "tools" / "mirror_sync" / "universal_job_result_publisher.py"


def _load():
    spec = importlib.util.spec_from_file_location("worker_result_publisher_frontend_evidence", PUBLISHER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_frontend_build_failure_evidence_is_published_and_redacted():
    m = _load()
    result = {
        "schema": "edarsahub.worker-result.v2",
        "job_id": "TEST",
        "status": "GIT_TESTS_FAILED",
        "certification": "NOT_CERTIFIED",
        "percent_complete": 80,
        "production_touched": False,
        "checks": [
            {
                "type": "frontend_build",
                "status": "FAIL",
                "returncode": 1,
                "started_at_utc": "2026-09-20T00:00:00Z",
                "completed_at_utc": "2026-09-20T00:00:01Z",
                "output": "Failed to compile.\nModule not found: Error: Can't resolve './Missing'\nTOKEN=should-not-leak",
            }
        ],
    }
    public = m.sanitize(result)
    evidence = public["frontend_build_evidence"]["checks"][0]
    assert evidence["status"] == "FAIL"
    assert evidence["returncode"] == 1
    assert "Failed to compile" in evidence["output_tail"]
    assert "Missing" in evidence["output_tail"]
    assert "should-not-leak" not in evidence["output_tail"]
    assert "[REDACTED_SENSITIVE_LINE]" in evidence["output_tail"]
