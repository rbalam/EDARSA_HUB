"""Phase 3 integral resilience tests for Autonomous Self-Healing & Global Lifecycle Recovery.

Covers all 15 controlled Development scenarios and mandatory invariants:
1. Persistent draft recovery (idempotent, exact job_id & payload, no invented request_key)
2. Transient draft protection (never touched within grace or active claim)
3. Duplicate draft prevention (local or remote inbox/result already exists)
4. Corrupt draft forensic preservation (untouched JSON, sanitized forensic dossier, zero reconstruction)
5. Git error classification & bounded handling
6. MCP timeout classification & backoff
7. Runtime failure degradation auto-suspension
8. Orphan claim detection & active claim preservation
9. Pending certification reconciliation (fail-closed without attestation)
10. Unknown incident governed diagnostic pipeline (never auto-mutates outside policy)
11. Recurring incident exponential backoff & circuit breaker opening (no infinite loop)
12. Revoked authorization / missing RBAC fail-closed rejection
13. Circuit breaker OPEN -> cooldown -> HALF_OPEN -> CERTIFIED CLOSED recovery
14. Repair self-failure recording & escalation (never self-certifies)
15. Restart mid-recovery idempotency (crash after enqueue reconciled cleanly without duplicate)
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
for p in (REPO_ROOT, REPO_ROOT / "tools" / "mirror_sync"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from tools.mirror_sync import worker_lifecycle_recovery as lr
from tools.mirror_sync import worker_maintenance_runtime as mr
from tools.mirror_sync import worker_repair_auto_loop as al


def _readonly_draft(job_id: str, *, domain: str = "COMERCIAL_POS", req_email: str = "ricardo@edarsa.com.mx") -> dict:
    return {
        "schema": "edarsahub.worker-job.v2",
        "job_id": job_id,
        "mode": "READ_ONLY",
        "target_repo": "rbalam/EDARSA_HUB",
        "target_branch": "Edarsahub_Desarrollo",
        "production_allowed": False,
        "human_summary_language": "es",
        "objective": f"Controlled READ_ONLY test audit for {domain}",
        "actions": [],
        "checks": [{"type": "git_diff_check"}],
        "requester": {
            "email": req_email,
            "source": "edarsahub-worker-ingress",
            "project": "EDARSAHUB",
            "chat": "self-healing-test",
        },
        "scheduling": {
            "project_id": "EDARSAHUB",
            "bounded_context": domain,
            "priority_class": "NORMAL",
            "fairness_weight": 1,
            "max_parallelism": 1,
            "resource_claims": [],
            "conflict_domains": [domain],
        },
    }


def _setup_queue(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    qroot = tmp_path / ".git" / "universal-worker-queue"
    for sub in ("drafts", "pending", "processing", "done", "rejected", "results", "published", "maintenance/incidents", "maintenance/circuit_breakers"):
        (qroot / sub).mkdir(parents=True, exist_ok=True)
    claims_dir = tmp_path / ".git" / "agent-guard" / "state" / "claims"
    claims_dir.mkdir(parents=True, exist_ok=True)
    attest_dir = tmp_path / ".git" / "mirror-sync" / "reporting" / "test_attestations"
    attest_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path, qroot, claims_dir, attest_dir


def _age_file(path: Path, seconds_ago: int, now_ts: float) -> None:
    ts = now_ts - seconds_ago
    os.utime(path, (ts, ts))


def test_01_persistent_vs_02_transient_vs_03_duplicate_vs_04_corrupt_drafts(tmp_path):
    root, qroot, claims_dir, attest_dir = _setup_queue(tmp_path)
    now_ts = time.time()

    # 1. Persistent draft (1000s old, no request_key -> never invented)
    p_id = "SEM-COMERCIAL_POS-PERSISTENT-001"
    p_path = qroot / "drafts" / f"{p_id}.json"
    p_payload = _readonly_draft(p_id)
    p_path.write_text(json.dumps(p_payload), encoding="utf-8")
    _age_file(p_path, 1000, now_ts)

    # 2. Transient draft (30s old -> must NOT be touched)
    t_id = "SEM-COMERCIAL_POS-TRANSIENT-001"
    t_path = qroot / "drafts" / f"{t_id}.json"
    t_path.write_text(json.dumps(_readonly_draft(t_id)), encoding="utf-8")
    _age_file(t_path, 30, now_ts)

    # 3. Duplicate draft (already in remote inbox)
    d_id = "SEM-COMERCIAL_POS-DUPLICATE-001"
    d_path = qroot / "drafts" / f"{d_id}.json"
    d_path.write_text(json.dumps(_readonly_draft(d_id)), encoding="utf-8")
    _age_file(d_path, 1000, now_ts)

    # 4. Corrupt draft (broken JSON -> preserved untouched, forensic generated)
    c_id = "SEM-COMERCIAL_POS-CORRUPT-001"
    c_path = qroot / "drafts" / f"{c_id}.json"
    corrupt_raw = '{"job_id":"broken"} TRAILING_GARBAGE'
    c_path.write_text(corrupt_raw, encoding="utf-8")
    _age_file(c_path, 1000, now_ts)

    det = lr.scan_global_lifecycle_blockers(
        repo_root=root,
        state_root=qroot,
        claims_dir=claims_dir,
        attestations_dir=attest_dir,
        now_epoch=now_ts,
        force_full=True,
        remote_inbox_ids={d_id},
        remote_result_ids=set(),
    )
    assert det["counts"]["persistent_drafts"] == 1
    assert det["persistent_drafts"][0]["job_id"] == p_id
    assert det["counts"]["transient_drafts"] == 2  # t_id (<grace) + d_id (in_remote_inbox)
    assert det["counts"]["corrupt_drafts"] == 1
    assert det["corrupt_drafts"][0]["preserved_untouched"] is True
    assert det["corrupt_drafts"][0]["reconstructed"] is False

    # Recover persistent draft via canonical submit stub -> preserves exact job_id, zero invented request_key
    submitted: list[dict] = []

    def fake_submit(job_spec, *, require_convergence=False):
        submitted.append(dict(job_spec))
        return {"status": "SUBMITTED", "job_id": job_spec["job_id"], "production_touched": False}

    rec = lr.advance_lifecycle_recovery(
        det,
        repo_root=root,
        state_root=qroot,
        claims_dir=claims_dir,
        automation_state={
            "valid": True,
            "enabled": True,
            "production_allowed": False,
            "enabled_at_utc": "2020-01-01T00:00:00Z",
            "adopted_job_ids": [],
        },
        submit_fn=fake_submit,
        now_epoch=now_ts,
        max_recoveries_per_cycle=1,
        remote_inbox_ids={d_id},
        remote_result_ids=set(),
    )
    assert rec["status"] == "ACTIVE"
    assert rec["recoveries_attempted"] == 1
    assert rec["recoveries_succeeded"] == 1
    assert len(submitted) == 1
    assert submitted[0]["job_id"] == p_id
    assert "request_key" not in submitted[0]  # Never invented for legacy drafts
    assert c_path.read_text(encoding="utf-8") == corrupt_raw  # Untouched
    assert (qroot / "maintenance" / "forensics" / f"{c_id}.json").is_file()

    # Duplicate draft rejected explicitly
    dup_out = lr.recover_persistent_readonly_draft(
        d_path,
        repo_root=root,
        state_root=qroot,
        claims_dir=claims_dir,
        circuit_state_dir=qroot / "maintenance" / "circuit_breakers",
        remote_inbox_ids={d_id},
        remote_result_ids=set(),
        submit_fn=fake_submit,
        now_epoch=now_ts,
    )
    assert dup_out["eligible"] is False
    assert dup_out["action"] == "DUPLICATE_PREVENTED"


def test_05_git_06_mcp_07_runtime_degradation_08_orphan_claim_09_pending_audit(tmp_path):
    root, qroot, claims_dir, attest_dir = _setup_queue(tmp_path)
    now_ts = time.time()

    # 5. Git error taxonomy & 6. MCP timeout taxonomy
    git_tax = al.classify_failure_taxonomy(status="GIT_DIVERGENCE_BLOCKED", causal_evidence={"x": 1})
    assert git_tax["failure_class"] == "GIT_MIRROR_DIVERGENCE"
    mcp_tax = al.classify_failure_taxonomy(error_code="504", blockers=["CONNECTIONRESET"], causal_evidence={"x": 1})
    assert mcp_tax["failure_class"] == "CONNECTION_LOSS"

    # 8. Active claim protects draft as transient
    p_id = "SEM-CLAIM-TEST-001"
    p_path = qroot / "drafts" / f"{p_id}.json"
    p_path.write_text(json.dumps(_readonly_draft(p_id)), encoding="utf-8")
    _age_file(p_path, 1200, now_ts)
    (claims_dir / f"queue-publisher-{p_id}.json").write_text(json.dumps({"status": "ACTIVE", "agent_id": f"queue-publisher-{p_id}"}))

    # 9. Pending audit evidence: one with attestation, one without
    sha_ok = "a" * 40
    sha_no = "b" * 40
    (attest_dir / f"{sha_ok}.json").write_text(json.dumps({"sha": sha_ok}))
    for jid, sha in (("JOB-PA-OK", sha_ok), ("JOB-PA-NO", sha_no)):
        (qroot / "results" / f"{jid}.json").write_text(json.dumps({"job_id": jid, "status": "INTEGRATED", "development_sha": sha}))
        mp = qroot / "published" / f"{jid}.json"
        mp.write_text("published=2026-11-20T00:00:00Z\ncommit=1234\ncertification=PENDING_AUDIT_EVIDENCE\n")
        _age_file(mp, 600, now_ts)

    # 7. Runtime failure triggers degraded mode -> automatic suspension of recovery
    det = lr.scan_global_lifecycle_blockers(
        repo_root=root,
        state_root=qroot,
        claims_dir=claims_dir,
        attestations_dir=attest_dir,
        ff={"ff": "ALREADY_ALIGNED"},
        runtime={"runtime_repair_needed": True},
        claims_summary={"quarantined": 2},
        now_epoch=now_ts,
        force_full=True,
        remote_inbox_ids=set(),
        remote_result_ids=set(),
    )
    assert det["system_degraded"] is True
    assert det["counts"]["runtime_failures"] >= 1
    assert det["counts"]["orphan_claims"] == 2
    assert det["counts"]["transient_drafts"] == 1  # Protected by active claim
    assert det["counts"]["pending_audit_stale"] == 2
    assert det["pending_audit_with_attestation_count"] == 1

    rec = lr.advance_lifecycle_recovery(
        det,
        repo_root=root,
        state_root=qroot,
        claims_dir=claims_dir,
        automation_state={"valid": True, "enabled": True, "production_allowed": False},
        now_epoch=now_ts,
        remote_inbox_ids=set(),
        remote_result_ids=set(),
    )
    assert rec["status"] == "SUSPENDED_DEGRADATION"
    assert rec["recoveries_attempted"] == 0


def test_10_unknown_incident_diagnostic_never_auto_mutates(tmp_path):
    root, qroot, _, _ = _setup_queue(tmp_path)
    src_id = "JOB-UNKNOWN-FAIL-001"
    (qroot / "results" / f"{src_id}.json").write_text(json.dumps({
        "schema": "edarsahub.worker-result.v2",
        "job_id": src_id,
        "status": "BLOCKED",
        "quality_gate": "FAIL",
        "tests": "FAIL",
        "certification": "NOT_CERTIFIED",
        "percent_complete": 0,
        "production_touched": False,
        "blockers": ["EXOTIC_UNSEEN_KERNEL_FAULT_XYZ"],
        "checks": [{
            "type": "pytest",
            "status": "FAIL",
            "returncode": 1,
            "output": "FAILED test_x.py::test_y\nE   AssertionError: unexpected exotic invariant\n",
        }],
    }))
    dossier = lr.diagnose_unknown_incident(
        incident_id="INC-UNKNOWN-001",
        source_job_id=src_id,
        blockers=["EXOTIC_UNSEEN_KERNEL_FAULT_XYZ"],
        state_root=qroot,
    )
    assert dossier["schema"] == lr.SCHEMA_DIAGNOSTIC
    assert dossier["auto_mutation_authorized"] is False
    assert dossier["independent_certification_required"] is True
    assert dossier["learning_allowed_only_if_certified"] is True
    assert dossier["risk_level"] == "HIGH"
    assert dossier["recommended_action"] == "ESCALATED_HUMAN_REQUIRED"
    assert dossier["causal_evidence"]["failed_check_count"] == 1
    assert (qroot / "maintenance" / "diagnostics" / "INC-UNKNOWN-001.json").is_file()


def test_11_recurring_12_revoked_auth_13_circuit_breaker_14_repair_failure_15_restart_idempotency(tmp_path):
    root, qroot, claims_dir, _ = _setup_queue(tmp_path)
    cb_dir = qroot / "maintenance" / "circuit_breakers"
    now_ts = 1_700_000_000.0

    # 11. Exponential backoff progression
    assert lr.compute_exponential_backoff(0) == 0
    assert lr.compute_exponential_backoff(1) == 60
    assert lr.compute_exponential_backoff(2) == 120
    assert lr.compute_exponential_backoff(3) == 240
    assert lr.compute_exponential_backoff(20) == 3600

    # 12. Revoked authorization fails closed before publish
    rev_id = "SEM-REVOKED-001"
    rev_path = qroot / "drafts" / f"{rev_id}.json"
    rev_path.write_text(json.dumps(_readonly_draft(rev_id)), encoding="utf-8")
    _age_file(rev_path, 1000, now_ts)
    rev_out = lr.recover_persistent_readonly_draft(
        rev_path,
        repo_root=root,
        state_root=qroot,
        claims_dir=claims_dir,
        circuit_state_dir=cb_dir,
        remote_inbox_ids=set(),
        remote_result_ids=set(),
        authorization_context={"revoked": True, "authorization_id": "AUTH-REV-1"},
        now_epoch=now_ts,
    )
    assert rev_out["eligible"] is False
    assert rev_out["action"] == "ESCALATE_POLICY"
    assert rev_out["reason"] == "AUTHORIZATION_REVOKED"

    # 13 & 14. Repair self-failure -> backoff -> circuit breaker OPEN -> HALF_OPEN -> CLOSED
    fail_id = "SEM-FAILING-RECOVERY-001"
    fail_path = qroot / "drafts" / f"{fail_id}.json"
    fail_path.write_text(json.dumps(_readonly_draft(fail_id)), encoding="utf-8")
    _age_file(fail_path, 1000, now_ts)

    def broken_submit(_job, *, require_convergence=False):
        raise RuntimeError("UPSTREAM_PUBLISH_FAILED")

    r1 = lr.recover_persistent_readonly_draft(
        fail_path, repo_root=root, state_root=qroot, claims_dir=claims_dir, circuit_state_dir=cb_dir,
        remote_inbox_ids=set(), remote_result_ids=set(), submit_fn=broken_submit, now_epoch=now_ts,
    )
    assert r1["action"] == "RECOVERY_FAILED_RECORDED"

    # Immediate retry blocked by exponential backoff (60s)
    r_bo = lr.recover_persistent_readonly_draft(
        fail_path, repo_root=root, state_root=qroot, claims_dir=claims_dir, circuit_state_dir=cb_dir,
        remote_inbox_ids=set(), remote_result_ids=set(), submit_fn=broken_submit, now_epoch=now_ts + 10,
    )
    assert r_bo["action"] == "BACKOFF_WAIT"

    # Failures 2 and 3 open the circuit breaker
    lr.recover_persistent_readonly_draft(
        fail_path, repo_root=root, state_root=qroot, claims_dir=claims_dir, circuit_state_dir=cb_dir,
        remote_inbox_ids=set(), remote_result_ids=set(), submit_fn=broken_submit, now_epoch=now_ts + 70,
    )
    lr.recover_persistent_readonly_draft(
        fail_path, repo_root=root, state_root=qroot, claims_dir=claims_dir, circuit_state_dir=cb_dir,
        remote_inbox_ids=set(), remote_result_ids=set(), submit_fn=broken_submit, now_epoch=now_ts + 250,
    )
    r_open = lr.recover_persistent_readonly_draft(
        fail_path, repo_root=root, state_root=qroot, claims_dir=claims_dir, circuit_state_dir=cb_dir,
        remote_inbox_ids=set(), remote_result_ids=set(), submit_fn=broken_submit, now_epoch=now_ts + 260,
    )
    assert r_open["action"] == "CIRCUIT_OPEN"

    # After cooldown expires (HALF_OPEN), healthy submit succeeds and resets circuit to CLOSED
    def healthy_submit(job_spec, *, require_convergence=False):
        return {"status": "SUBMITTED", "job_id": job_spec["job_id"], "production_touched": False}

    r_ok = lr.recover_persistent_readonly_draft(
        fail_path, repo_root=root, state_root=qroot, claims_dir=claims_dir, circuit_state_dir=cb_dir,
        remote_inbox_ids=set(), remote_result_ids=set(), submit_fn=healthy_submit, now_epoch=now_ts + 1000,
    )
    assert r_ok["recovered"] is True
    assert r_ok["independent_certification_pending"] is True

    # 15. Crash/restart mid-recovery: job was already pushed to remote inbox before restart -> zero duplicate!
    restart_out = lr.recover_persistent_readonly_draft(
        fail_path, repo_root=root, state_root=qroot, claims_dir=claims_dir, circuit_state_dir=cb_dir,
        remote_inbox_ids={fail_id}, remote_result_ids=set(), submit_fn=healthy_submit, now_epoch=now_ts + 1010,
    )
    assert restart_out["eligible"] is False
    assert restart_out["action"] == "DUPLICATE_PREVENTED"

    # Maintenance escalation preserves history and halts retries
    monkeypatch_dir = qroot / "maintenance" / "incidents"
    orig_dir = mr.INCIDENT_DIR
    try:
        mr.INCIDENT_DIR = monkeypatch_dir
        mr.declare_runtime_incident("INC-ESC-001", ["tools/mirror_sync/worker_control_plane.py"])
        esc = mr.escalate_runtime_incident("INC-ESC-001", reason="REPAIR_ATTEMPTS_EXHAUSTED")
        assert esc.state == "ESCALATED_HUMAN_REQUIRED"
        assert esc.escalation_reason == "REPAIR_ATTEMPTS_EXHAUSTED"
        assert (monkeypatch_dir / "INC-ESC-001.json").is_file()
    finally:
        mr.INCIDENT_DIR = orig_dir
