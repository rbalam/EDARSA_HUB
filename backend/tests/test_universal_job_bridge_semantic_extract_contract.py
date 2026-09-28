from tools.mirror_sync.universal_job_bridge import validate_check


def valid_semantic_extract_check():
    return {
        "type": "worker_result_semantic_extract",
        "request": {
            "source_result": {
                "path": "worker_queue/results/EDARSAHUB-TABLAJERIA-RECOVERY-AUDIT-WORKER-JOB-V2-R2.json",
                "branch": "worker/results",
                "commit": "f67100bb74287ea86c66607400f6136bb37b51e2",
                "blob_sha": "1d04c48286bb0457e15e89d2370d501e53d1e505",
            },
            "required_semantic_fields": [
                "gate3_allowed",
                "last_gate_executed",
                "last_gate_certified",
                "real_implementation_percent",
                "next_allowed_gate",
                "blocking_reason_if_any",
            ],
        },
    }


def test_semantic_extract_check_is_valid_for_bridge() -> None:
    assert validate_check(valid_semantic_extract_check(), 1) == []


def test_semantic_extract_requires_source_result() -> None:
    check = {"type": "worker_result_semantic_extract", "request": {}}
    assert validate_check(check, 1) == ["CHECK_1_SOURCE_RESULT_REQUIRED"]


def test_semantic_extract_rejects_non_results_branch() -> None:
    check = valid_semantic_extract_check()
    check["request"]["source_result"]["branch"] = "Edarsahub_Desarrollo"
    assert validate_check(check, 1) == ["CHECK_1_INVALID_SOURCE_RESULT_BRANCH"]
