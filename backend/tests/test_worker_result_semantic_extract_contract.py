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


def test_canonical_compatibility_resolves_execution_base_sha_and_repository_evidence_with_provenance() -> None:
    sha = "dfc9e0f82cf94adf502d6376fd19d68baac13fe3"
    payload = {
        "schema": "edarsahub.worker-result.v2",
        "job_id": "EDARSAHUB-BOS-WORKER-REPAIR-KNOWLEDGE-GATE1-READONLY-R1-20261022",
        "status": "READ_ONLY_COMPLETE",
        "tests": "PASS",
        "quality_gate": "PASS",
        "certification": "CERTIFIED_READ_ONLY",
        "certification_basis": "READ_ONLY_REPOSITORY_PASS_PLUS_SANITIZED_EVIDENCE",
        "work_completion": "COMPLETE",
        "percent_complete": 100,
        "production_touched": False,
        "files_changed": [],
        "blockers": [],
        "base_sha": sha,
        "summary_es": "Resumen canonico de lectura.",
        "repository_contract_evidence": {
            "checks": [
                {
                    "status": "PASS",
                    "mode": "READ_ONLY_REPOSITORY",
                    "summary": {"matched_files": 1, "scanned_files": 1, "skipped_sensitive": 0},
                    "truncated": False,
                    "evidence": [
                        {
                            "path": "tools/mirror_sync/worker_repair_capability_registry.py",
                            "matched_terms": ["register_learned_capability"],
                            "candidate_ownership": "tools",
                            "symbols": ["register_learned_capability"],
                            "imports": [],
                            "routes": [],
                            "tables_referenced": [],
                            "helpers": [],
                            "connections": [],
                            "rbac_contracts": [],
                            "scheduler_contracts": [],
                            "integrations": [],
                            "secret_raw_leak": "must-be-dropped",
                        }
                    ],
                }
            ]
        },
    }
    report = build_report(
        payload,
        {
            "required_semantic_fields": [
                "repository_evidence",
                "certification_basis",
                "execution_base_sha",
                "summary_es",
            ]
        },
        {
            "source_result_read_status": "RESULT_READ_OK",
            "source_result_loader": "git_show:origin/worker/results:worker_queue/results/EDARSAHUB-BOS-WORKER-REPAIR-KNOWLEDGE-GATE1-READONLY-R1-20261022.json",
        },
    )

    assert report["status"] == "PASS"
    assert report["semantic_fields"]["execution_base_sha"] == sha
    assert report["semantic_fields"]["certification_basis"] == "READ_ONLY_REPOSITORY_PASS_PLUS_SANITIZED_EVIDENCE"
    assert report["semantic_fields"]["summary_es"] == "Resumen canonico de lectura."
    repo_ev = report["semantic_fields"]["repository_evidence"]
    assert isinstance(repo_ev, dict)
    assert repo_ev["checks"][0]["evidence"][0]["path"] == "tools/mirror_sync/worker_repair_capability_registry.py"
    assert "secret_raw_leak" not in repo_ev["checks"][0]["evidence"][0]

    assert report["semantic_field_provenance"]["execution_base_sha"] == {
        "status": "DERIVED_CANONICAL_COMPATIBILITY",
        "source_key": "base_sha",
        "derivation": "PUBLISHED_WORKER_RESULT_BASE_SHA_INVARIANT",
    }
    assert report["semantic_field_provenance"]["repository_evidence"] == {
        "status": "DERIVED_CANONICAL_COMPATIBILITY",
        "source_key": "repository_contract_evidence",
        "derivation": "PUBLISHED_SANITIZED_REPOSITORY_CONTRACT_EVIDENCE",
    }
    assert "execution_base_sha" not in report["source_missing_semantic_fields"]
    assert "repository_evidence" not in report["source_missing_semantic_fields"]
    assert "execution_base_sha" in report["source_explicit_missing_semantic_fields"]
    assert "repository_evidence" in report["source_explicit_missing_semantic_fields"]

    # Crucial contract invariant: compatibility of provenance/evidence fields never opens Gate 3
    assert report["source_semantic_fields_complete"] is False
    assert report["semantic_fields_complete"] is True
    assert report["missing_semantic_fields"] == []
    assert report["gate3_allowed"] is False
    assert report["bridge_verdict"] == "SOURCE_SEMANTIC_FIELDS_DERIVED_FAIL_CLOSED"
    assert report["next_allowed_step"] == "GATE3_HOLD_PENDING_EXPLICIT_SEMANTIC_FIELDS"
    assert report["semantic_fields"]["gate3_allowed"] is False
    assert report["semantic_fields"]["blocking_reason_if_any"] == "SOURCE_SEMANTIC_FIELDS_MISSING"
    assert report["semantic_fields"]["next_allowed_gate"] == "GATE3_HOLD_PENDING_EXPLICIT_SEMANTIC_FIELDS"


def test_invalid_base_sha_or_failed_repository_contract_evidence_fails_closed() -> None:
    payload = {
        "schema": "edarsahub.worker-result.v2",
        "job_id": "SOURCE-INVALID",
        "status": "READ_ONLY_COMPLETE",
        "tests": "PASS",
        "quality_gate": "PASS",
        "production_touched": False,
        "files_changed": [],
        "blockers": [],
        "base_sha": "not-a-valid-40-hex-sha",
        "repository_contract_evidence": {
            "checks": [
                {
                    "status": "FAIL",
                    "mode": "READ_ONLY_REPOSITORY",
                    "evidence": [],
                }
            ]
        },
    }
    report = build_report(
        payload,
        {
            "required_semantic_fields": [
                "execution_base_sha",
                "repository_evidence",
            ]
        },
        {
            "source_result_read_status": "RESULT_READ_OK",
            "source_result_loader": "git_show:x",
        },
    )

    assert report["semantic_fields"]["execution_base_sha"] is None
    assert report["semantic_fields"]["repository_evidence"] is None
    assert "execution_base_sha" in report["source_missing_semantic_fields"]
    assert "repository_evidence" in report["source_missing_semantic_fields"]
    assert report["semantic_field_provenance"]["execution_base_sha"]["status"] == "MISSING_OR_UNVERIFIED"
    assert report["semantic_field_provenance"]["repository_evidence"]["status"] == "MISSING_OR_UNVERIFIED"
    assert report["source_semantic_fields_complete"] is False
    assert report["gate3_allowed"] is False
    assert report["next_allowed_step"] == "GATE3_HOLD_PENDING_EXPLICIT_SEMANTIC_FIELDS"


def test_publisher_preserves_execution_base_sha_and_sanitized_semantic_provenance_fields() -> None:
    from tools.mirror_sync.universal_job_result_publisher import sanitize

    sha = "43d28b3196516eb3fc4e44392806c658df577da2"
    source_sha = "dfc9e0f82cf94adf502d6376fd19d68baac13fe3"
    semantic_report = build_report(
        {
            "schema": "edarsahub.worker-result.v2",
            "job_id": "EDARSAHUB-BOS-WORKER-REPAIR-KNOWLEDGE-GATE1-READONLY-R1-20261022",
            "status": "READ_ONLY_COMPLETE",
            "tests": "PASS",
            "quality_gate": "PASS",
            "certification": "CERTIFIED_READ_ONLY",
            "certification_basis": "READ_ONLY_REPOSITORY_PASS_PLUS_SANITIZED_EVIDENCE",
            "work_completion": "COMPLETE",
            "percent_complete": 100,
            "production_touched": False,
            "files_changed": [],
            "blockers": [],
            "base_sha": source_sha,
            "summary_es": "Resumen.",
            "repository_contract_evidence": {
                "checks": [
                    {
                        "status": "PASS",
                        "mode": "READ_ONLY_REPOSITORY",
                        "summary": {"matched_files": 1},
                        "truncated": False,
                        "evidence": [{"path": "tools/mirror_sync/worker_repair_planner.py", "matched_terms": ["x"]}],
                    }
                ]
            },
        },
        {
            "required_semantic_fields": [
                "repository_evidence",
                "certification_basis",
                "execution_base_sha",
                "summary_es",
            ]
        },
        {
            "source_result_read_status": "RESULT_READ_OK",
            "source_result_loader": "git_show:origin/worker/results:worker_queue/results/EDARSAHUB-BOS-WORKER-REPAIR-KNOWLEDGE-GATE1-READONLY-R1-20261022.json",
        },
    )

    result = {
        "schema": "edarsahub.worker-result.v2",
        "job_id": "SEMANTIC-EXTRACT-JOB-TEST",
        "status": "READ_ONLY_COMPLETE",
        "tests": "PASS",
        "quality_gate": "PASS",
        "production_touched": False,
        "files_changed": [],
        "blockers": [],
        "base_sha": sha,
        "execution_base_sha": sha,
        "requested_base_sha": "invalid-sha-must-be-dropped",
        "checks": [
            {
                "type": "worker_result_semantic_extract",
                "status": "PASS",
                "returncode": 0,
                "semantic_evidence": semantic_report,
            }
        ],
    }

    public = sanitize(result)
    assert public["base_sha"] == sha
    assert public["execution_base_sha"] == sha
    assert "requested_base_sha" not in public
    assert public["source_semantic_fields_complete"] is False
    assert public["semantic_fields_complete"] is True
    assert public["gate3_allowed"] is False
    assert public["next_allowed_step"] == "GATE3_HOLD_PENDING_EXPLICIT_SEMANTIC_FIELDS"
    assert "execution_base_sha" not in public["source_missing_semantic_fields"]
    assert "repository_evidence" not in public["source_missing_semantic_fields"]
    assert "execution_base_sha" in public["source_explicit_missing_semantic_fields"]
    assert "repository_evidence" in public["source_explicit_missing_semantic_fields"]
    assert public["semantic_fields"]["execution_base_sha"] == source_sha
    assert public["semantic_fields"]["repository_evidence"]["checks"][0]["evidence"][0]["path"] == "tools/mirror_sync/worker_repair_planner.py"
    assert public["semantic_field_provenance"]["execution_base_sha"]["source_key"] == "base_sha"
    assert public["semantic_field_provenance"]["repository_evidence"]["source_key"] == "repository_contract_evidence"
