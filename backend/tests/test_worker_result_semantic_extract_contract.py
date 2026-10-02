from tools.mirror_sync.worker_result_semantic_extract import build_report, failure_report


def test_build_report_derives_fail_closed_when_required_fields_are_missing() -> None:
    payload = {
        "job_id": "SOURCE-R2",
        "status": "READ_ONLY_COMPLETE",
        "tests": "PASS",
        "quality_gate": "PASS",
        "certification": "CERTIFIED_READ_ONLY",
        "work_completion": "COMPLETE",
        "percent_complete": 100,
        "production_touched": False,
        "files_changed": [],
        "blockers": [],
    }
    report = build_report(
        payload,
        {"required_semantic_fields": ["gate3_allowed"]},
        {
            "source_result_read_status": "RESULT_READ_OK",
            "source_result_loader": "git_show:x",
        },
    )

    assert report["status"] == "PASS"
    assert report["runtime_gap_confirmed"] is False
    assert report["gate3_allowed"] is False
    assert report["bridge_verdict"] == "SOURCE_SEMANTIC_FIELDS_DERIVED_FAIL_CLOSED"
    assert report["source_semantic_fields_complete"] is False
    assert "gate3_allowed" in report["source_missing_semantic_fields"]
    assert report["semantic_fields_complete"] is True
    assert report["missing_semantic_fields"] == []
    assert report["semantic_fields"]["gate3_allowed"] is False
    assert report["semantic_fields"]["last_gate_executed"] == "SOURCE-R2"
    assert report["semantic_fields"]["last_gate_certified"] is False
    assert report["semantic_fields"]["blocking_reason_if_any"] == "SOURCE_SEMANTIC_FIELDS_MISSING"
    assert report["next_allowed_step"] == "GATE3_HOLD_PENDING_EXPLICIT_SEMANTIC_FIELDS"


def test_build_report_allows_only_explicit_complete_gate3() -> None:
    payload = {
        "status": "READ_ONLY_COMPLETE",
        "tests": "PASS",
        "quality_gate": "PASS",
        "certification": "CERTIFIED_READ_ONLY",
        "work_completion": "COMPLETE",
        "percent_complete": 100,
        "production_touched": False,
        "files_changed": [],
        "blockers": [],
        "decision": {
            "gate3_allowed": True,
            "last_gate_executed": "Gate2",
            "last_gate_certified": "Gate2",
            "real_implementation_percent": 95,
            "next_allowed_gate": "Gate3",
            "blocking_reason_if_any": "",
        },
    }
    report = build_report(
        payload,
        {},
        {
            "source_result_read_status": "RESULT_READ_OK",
            "source_result_loader": "git_show:x",
        },
    )
    assert report["source_semantic_fields_complete"] is True
    assert report["semantic_fields_complete"] is True
    assert report["gate3_allowed"] is True
    assert report["bridge_verdict"] == "SOURCE_SEMANTIC_FIELDS_COMPLETE_GATE3_ALLOWED"


def test_failure_report_is_fail_closed() -> None:
    report = failure_report(
        {"required_semantic_fields": ["gate3_allowed"]},
        {"source_result_read_status": "RESULT_READ_FAILED"},
    )
    assert report["status"] == "FAIL"
    assert report["runtime_gap_confirmed"] is True
    assert report["gate3_allowed"] is False
