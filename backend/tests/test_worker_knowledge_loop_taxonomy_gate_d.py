"""Gate D tests: Failure taxonomy (22+ classes), persistent circuit breaker, and Knowledge Loop."""
from __future__ import annotations

import pytest

from tools.mirror_sync import worker_repair_auto_loop as loop


def test_taxonomy_covers_all_required_failure_classes_and_never_auto_repairs_security():
    cases = [
        ("INVALID_JOB_TEMPLATE_SCHEMA", "INVALID_CONTRACT", "CONTRACT", False),
        ("SEMANTIC_CAPABILITY_UNKNOWN", "UNKNOWN_MCP_CAPABILITY", "CONTRACT", False),
        ("RBAC_MUTATION_FORBIDDEN", "INSUFFICIENT_PERMISSIONS", "SECURITY", False),
        ("START_JOB_ALREADY_EXISTS", "DUPLICATE_JOB", "CONTRACT", False),
        ("PUBLISHED_RESULT_COMMIT_BLOB_MISSING", "CONTRADICTORY_NOT_FOUND", "INFRASTRUCTURE", True),
        ("SEMANTIC_SOURCE_SHA256_MISMATCH", "STALE_SOURCE_SHA256", "CONTRACT", True),
        ("GIT_DIVERGENCE_BLOCKED", "GIT_MIRROR_DIVERGENCE", "INFRASTRUCTURE", True),
        ("GIT_WORKTREE_NOT_CLEAN", "DIRTY_WORKTREE", "INFRASTRUCTURE", False),
        ("CONCURRENT_SCOPE_CONFLICT", "CONCURRENCY_CONFLICT", "TRANSIENT", True),
        ("MODULENOTFOUNDERROR", "MISSING_DEPENDENCY", "INFRASTRUCTURE", False),
        ("GIT_TESTS_FAILED", "TEST_FAILURE", "CONTRACT", False),
        ("GIT_PUSH_FAILED", "INCOMPLETE_PUBLICATION", "TRANSIENT", True),
        ("EVIDENCE_TRUNCATED", "ABSENT_OR_TRUNCATED_EVIDENCE", "CONTRACT", False),
        ("CONTRADICTORY_RESULT_ARTIFACT", "CONTRADICTORY_RESULT", "INFRASTRUCTURE", False),
        ("PENDING_AUDIT_EVIDENCE", "PENDING_ATTESTATION", "TRANSIENT", True),
        ("RUNTIME_RESTART_TRANSIENT", "RUNTIME_RESTART_OR_TRANSIENT", "TRANSIENT", True),
        ("SLOT_EXPIRED", "STUCK_OR_EXPIRED_JOB", "TRANSIENT", True),
        ("CONNECTIONREFUSED", "CONNECTION_LOSS", "INTEGRATION", True),
        ("ENOSPC", "STORAGE_OR_RESOURCE_LIMIT", "INFRASTRUCTURE", False),
        ("NAIVE_DATETIME", "DATE_OR_TIMEZONE_ERROR", "BUSINESS", False),
        ("SCOPE_AUTHORIZATION_DENIED", "EMPRESA_OR_SUCURSAL_AUTH_FAILURE", "SECURITY", False),
        ("REJECTED_UNSAFE_OR_OVERSIZED", "SENSITIVE_DATA_EXPOSURE_RISK", "SECURITY", False),
        ("PRODUCTION_FORBIDDEN", "PRODUCTION_POLICY_VIOLATION", "SECURITY", False),
    ]
    for code, expected_cls, expected_cat, expected_auto in cases:
        res = loop.classify_failure_taxonomy(
            error_code=code,
            causal_evidence={"source_job_id": "JOB-1", "verified": True},
        )
        assert res["failure_class"] == expected_cls, f"{code} -> {res}"
        assert res["category"] == expected_cat
        assert res["auto_repair_allowed"] is expected_auto
        assert res["production_touched"] is False

    # Superficial string match WITHOUT causal evidence MUST NOT authorize auto repair
    no_ev = loop.classify_failure_taxonomy(
        error_code="GIT_DIVERGENCE_BLOCKED",
        causal_evidence=None,
    )
    assert no_ev["auto_repair_allowed"] is False


def test_persistent_circuit_breaker_opens_after_threshold_and_resets_only_on_certified(tmp_path):
    cb_dir = tmp_path / "cb"
    key = "INC-TEST-CIRCUIT-001"
    t0 = 1_700_000_000.0

    assert loop.evaluate_circuit_breaker(key, now_epoch=t0, state_dir=cb_dir)["state"] == "CLOSED"

    for idx in range(3):
        loop.record_circuit_outcome(
            key,
            certified_success=False,
            failure_class="GIT_PUSH_FAILED",
            now_epoch=t0 + idx,
            state_dir=cb_dir,
        )

    opened = loop.evaluate_circuit_breaker(key, now_epoch=t0 + 10, state_dir=cb_dir)
    assert opened["state"] == "OPEN"
    assert opened["allow_attempt"] is False
    assert opened["reason"] == "CIRCUIT_OPEN_MAX_FAILURES"

    # Knowledge loop blocks repair while circuit is open
    assessment = loop.assess_knowledge_loop_cycle(
        incident_id=key,
        error_code="GIT_PUSH_FAILED",
        causal_evidence={"source_job_id": "JOB-1"},
        now_epoch=t0 + 10,
        state_dir=cb_dir,
    )
    assert assessment["next_step"] == "CIRCUIT_OPEN_STOP"

    # After cooldown -> HALF_OPEN probe allowed
    half_open = loop.evaluate_circuit_breaker(key, now_epoch=t0 + 950, state_dir=cb_dir)
    assert half_open["state"] == "HALF_OPEN"
    assert half_open["allow_attempt"] is True

    # Certified recovery resets circuit back to CLOSED
    loop.record_circuit_outcome(key, certified_success=True, now_epoch=t0 + 960, state_dir=cb_dir)
    closed = loop.evaluate_circuit_breaker(key, now_epoch=t0 + 965, state_dir=cb_dir)
    assert closed["state"] == "CLOSED"
    assert closed["consecutive_failures"] == 0
