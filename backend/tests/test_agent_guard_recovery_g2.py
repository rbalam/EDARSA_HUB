"""Gate G2 (P0 Root-Cause Fix) regression & concurrency tests.

Covers:
1. Canonical interprocess publication lock in gate_chain_publisher.py:
   - Concurrent multi-process / multi-thread serialization without collisions.
   - Bounded timeout & backoff classifying legitimate contention as CLAIM_BUSY (retryable=True).
   - Guaranteed lock release on exception and crash recovery (SIGKILL subprocess).
   - Idempotency on duplicate job_id under contention.
   - Real Agent Guard errors remain AGENT_GUARD_WORKTREE_FAILED (retryable=False, guards intact).
2. Cross-domain handoff recovery & anti-oscillation in worker_cross_domain_handoff.py:
   - Recognizes verified terminal certification of source_job_id (identity + domain + fingerprint + semantic criteria).
   - Fail-closed rejection on mismatched fingerprint, mismatched domain, failed check, or uncertified result.
   - Eliminates RECONCILED_CLASSIFICATION <-> NO_EXECUTOR_STALL_EXCEPTION oscillation and redundant disk writes.
"""
from __future__ import annotations

import json
import multiprocessing
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

from modules.worker_ingress import service as ingress_service
from tools.mirror_sync import gate_chain_publisher as gcp
from tools.mirror_sync import worker_cross_domain_handoff as handoff_mod
from tools.mirror_sync import worker_lifecycle_recovery as lifecycle_rec


def _hold_lock_child(lock_path_str: str, ready_file_str: str, hold_seconds: float) -> None:
    lock_path = Path(lock_path_str)
    ready_file = Path(ready_file_str)
    with gcp._queue_publication_lock(
        job_id="CHILD-HOLDER-JOB",
        timeout_seconds=5.0,
        backoff_initial=0.02,
        backoff_max=0.05,
        lock_path=lock_path,
    ):
        ready_file.write_text(str(os.getpid()), encoding="utf-8")
        time.sleep(hold_seconds)


def test_g2_publisher_lock_serializes_concurrent_threads_and_releases_on_error(tmp_path):
    lock_file = tmp_path / "publisher.lock"
    events: list[tuple[str, str]] = []
    active = 0
    max_active = 0
    guard_mu = threading.Lock()

    def worker(idx: int, fail: bool = False) -> None:
        nonlocal active, max_active
        try:
            with gcp._queue_publication_lock(
                job_id=f"CONCURRENT-JOB-{idx}",
                timeout_seconds=5.0,
                backoff_initial=0.01,
                backoff_max=0.03,
                lock_path=lock_file,
            ):
                with guard_mu:
                    active += 1
                    max_active = max(max_active, active)
                    events.append(("enter", str(idx)))
                time.sleep(0.06)
                if fail:
                    raise RuntimeError("SIMULATED_FAILURE")
                with guard_mu:
                    events.append(("exit", str(idx)))
                    active -= 1
        except RuntimeError:
            with guard_mu:
                active -= 1

    t1 = threading.Thread(target=worker, args=(1, True))
    t2 = threading.Thread(target=worker, args=(2, False))
    t3 = threading.Thread(target=worker, args=(3, False))
    t1.start()
    t2.start()
    t3.start()
    t1.join(timeout=5)
    t2.join(timeout=5)
    t3.join(timeout=5)

    assert max_active == 1, "Publication lock must enforce strict mutual exclusion"
    assert active == 0
    assert ("exit", "2") in events
    assert ("exit", "3") in events


def test_g2_publisher_lock_interprocess_timeout_is_claim_busy_and_recovers_after_crash(tmp_path):
    lock_file = tmp_path / "publisher.lock"
    ready_file = tmp_path / "ready.pid"
    ctx = multiprocessing.get_context("spawn")
    proc = ctx.Process(target=_hold_lock_child, args=(str(lock_file), str(ready_file), 15.0))
    proc.start()
    try:
        deadline = time.monotonic() + 5.0
        while not ready_file.is_file() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert ready_file.is_file(), "Child failed to acquire lock in time"

        # 1. Bounded timeout raises QUEUE_PUBLISHER_CLAIM_BUSY -> CLAIM_BUSY (retryable=True)
        with pytest.raises(RuntimeError) as exc_info:
            with gcp._queue_publication_lock(
                job_id="BLOCKED-CALLER",
                timeout_seconds=0.18,
                backoff_initial=0.02,
                backoff_max=0.05,
                lock_path=lock_file,
            ):
                pass
        err_text = str(exc_info.value)
        assert "QUEUE_PUBLISHER_CLAIM_BUSY" in err_text
        assert gcp._submit_failure_status(exc_info.value) == "CLAIM_BUSY"

        diag = ingress_service.classify_publication_diagnostic(
            {"status": "CLAIM_BUSY", "reason": err_text, "job_id": "BLOCKED-CALLER"}
        )
        assert diag["error_code"] == "CLAIM_BUSY"
        assert diag["retryable"] is True
        assert diag["recovery_required"] is False

        # 2. Simulate abrupt crash (SIGKILL) -> OS releases flock immediately -> next publisher recovers
        os.kill(proc.pid, signal.SIGKILL)
        proc.join(timeout=5)

        with gcp._queue_publication_lock(
            job_id="RECOVERED-AFTER-CRASH",
            timeout_seconds=1.5,
            backoff_initial=0.02,
            backoff_max=0.05,
            lock_path=lock_file,
        ) as meta:
            assert meta["attempts"] >= 1
    finally:
        if proc.is_alive():
            proc.kill()
            proc.join(timeout=3)


def test_g2_contention_vs_real_agent_guard_error_classification():
    # Legitimate contention on worker_queue_publication -> CLAIM_BUSY (retryable)
    contention_out = (
        ".vscode/tasks.json:1:1: error: AGENT_GUARD: "
        "Dominio funcional duplicado con queue-publisher-SEM-REQUEST-123: worker_queue_publication"
    )
    assert gcp._is_agent_guard_contention_output(contention_out) is True

    diag_busy = ingress_service.classify_publication_diagnostic(
        {"status": "RECOVERY_REQUIRED", "reason": "RuntimeError:QUEUE_PUBLISHER_CLAIM_BUSY:" + contention_out}
    )
    assert diag_busy["error_code"] == "CLAIM_BUSY"
    assert diag_busy["retryable"] is True
    assert diag_busy["recovery_required"] is False

    # Real Agent Guard policy/security error -> NEVER misclassified as CLAIM_BUSY
    real_guard_errors = [
        "AGENT_STORAGE_POLICY_V1: /app esta al 92.0% y supera el umbral de bloqueo",
        "AGENT_GUARD: rama de Produccion prohibida",
        "AGENT_GUARD: worktree no registrado",
        "AGENT_GUARD: cambio fuera del scope de queue-publisher-X",
    ]
    for err_out in real_guard_errors:
        assert gcp._is_agent_guard_contention_output(err_out) is False
        diag_real = ingress_service.classify_publication_diagnostic(
            {"status": "RECOVERY_REQUIRED", "reason": "RuntimeError:AGENT_GUARD_WORKTREE_CREATE_FAILED:" + err_out}
        )
        assert diag_real["error_code"] == "AGENT_GUARD_WORKTREE_FAILED"
        assert diag_real["retryable"] is False
        assert diag_real["recovery_required"] is True


def test_g2_publish_idempotency_serialized_returns_exists_on_second_caller(monkeypatch, tmp_path):
    lock_file = tmp_path / "publisher.lock"
    calls = {"publish_serialized": 0}
    monkeypatch.setattr(gcp, "_publisher_lock_path", lambda: lock_file)
    monkeypatch.setattr(gcp, "validate_template", lambda t: dict(t))

    def fake_publish_serialized(*, job_id, template, remote, queue_branch):
        calls["publish_serialized"] += 1
        if calls["publish_serialized"] == 1:
            return {"status": "PUBLISHED", "job_id": job_id, "production_touched": False}
        return {"status": "EXISTS", "job_id": job_id, "publish": False, "result": "REMOTE_JOB=EXISTS"}

    monkeypatch.setattr(gcp, "_publish_serialized", fake_publish_serialized)

    plan = {
        "status": "READY_TO_PUBLISH",
        "job_id": "SEM-REQUEST-IDEMPOTENT-001",
        "template": {"schema": "edarsahub.worker-job.v2", "job_id": "SEM-REQUEST-IDEMPOTENT-001", "production_allowed": False},
    }
    r1 = gcp.publish(plan)
    r2 = gcp.publish(plan)
    assert r1["status"] == "PUBLISHED"
    assert r2["status"] == "EXISTS"
    assert "publication_lock" in r1 and "publication_lock" in r2


def _seed_certified_source_job(
    state_root: Path,
    *,
    job_id: str,
    domain: str,
    certification: str = "CERTIFIED_READ_ONLY",
    status: str = "READ_ONLY_COMPLETE",
    tests: str = "PASS",
    quality_gate: str = "PASS",
    mutate_done_payload: bool = False,
    check_status: str = "PASS",
) -> None:
    for sub in ("drafts", "done", "results", "published", "maintenance/handoffs"):
        (state_root / sub).mkdir(parents=True, exist_ok=True)
    draft = {
        "schema": "edarsahub.worker-job.v2",
        "job_id": job_id,
        "mode": "READ_ONLY",
        "target_repo": "rbalam/EDARSA_HUB",
        "target_branch": "Edarsahub_Desarrollo",
        "production_allowed": False,
        "objective": f"Auditoria READ_ONLY para {domain}",
        "actions": [],
        "checks": [{"type": "repository_contract_audit", "request": {"paths": ["backend/modules/"], "search_terms": ["audit"]}}],
        "scheduling": {"bounded_context": domain, "project_id": "EDARSAHUB"},
    }
    (state_root / "drafts" / f"{job_id}.json").write_text(json.dumps(draft, indent=2), encoding="utf-8")
    done_job = dict(draft)
    if mutate_done_payload:
        done_job["objective"] = "TAMPERED OBJECTIVE"
    (state_root / "done" / f"{job_id}.json").write_text(
        json.dumps({"job": done_job}, indent=2),
        encoding="utf-8",
    )
    res = {
        "schema": "edarsahub.worker-result.v2",
        "job_id": job_id,
        "status": status,
        "certification": certification,
        "tests": tests,
        "quality_gate": quality_gate,
        "blockers": [],
        "production_touched": False,
        "completed_at_utc": "2026-11-26T04:50:00Z",
        "summary_es": "Auditoria certificada.",
        "checks": [{"type": "repository_contract_audit", "status": check_status}],
    }
    (state_root / "results" / f"{job_id}.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    (state_root / "published" / f"{job_id}.json").write_text(
        json.dumps({"job_id": job_id, "certification": certification, "commit": "a" * 40}),
        encoding="utf-8",
    )


def _seed_recovery_handoff(
    state_root: Path,
    *,
    handoff_id: str,
    source_domain: str,
    source_job_id: str,
    created_at_utc: str = "2026-11-26T23:50:00Z",
    lifecycle_state: str = "ESCALATED_HUMAN_REQUIRED",
    exception_code: str | None = "HANDOFF_NO_EXECUTOR_STALLED",
    tamper_fp: bool = False,
) -> Path:
    hdir = state_root / "maintenance" / "handoffs"
    hdir.mkdir(parents=True, exist_ok=True)
    record = {
        "schema": "edarsahub.cross-domain-handoff.v1",
        "handoff_id": handoff_id,
        "request_key": f"recover-{source_job_id.lower()}",
        "source_domain": source_domain,
        "target_domain": "WORKER_CONTROL_PLANE",
        "owner_domain": "WORKER_CONTROL_PLANE",
        "source_job_id": source_job_id,
        "source_objective": f"Recuperar el DRAFT existente {source_job_id} bloqueado por AGENT_GUARD_WORKTREE_FAILED.",
        "acceptance_criteria": [
            "existing_draft_reconciled",
            "no_duplicate_job",
            "terminal_certification_valid",
            "production_touched_false",
        ],
        "handoff_mode": "READ_ONLY",
        "requested_capability": None,
        "requested_constraints": {},
        "auto_dispatch": False,
        "classification": "TARGET_BOUNDED_CONTEXT_REQUIRED",
        "classification_reason": "BOUNDED_CONTEXT_OWNER_REQUIRED:WORKER_CONTROL_PLANE",
        "lifecycle_state": lifecycle_state,
        "next_allowed_action": "ASSIGN_COMPATIBLE_CAPABILITY",
        "requires_human_intervention": True,
        "has_executor": False,
        "executor_status": "UNASSIGNED_NO_EXECUTOR",
        "exception_code": exception_code,
        "exception_reason": "Solicitud sin ejecutor activo.",
        "dependency_satisfied": False,
        "certification": "NOT_CERTIFIED",
        "resolution_job_id": None,
        "payload_fingerprint": "b" * 64 if tamper_fp else "a" * 64,
        "initial_payload_fingerprint": "a" * 64,
        "created_at_utc": created_at_utc,
        "updated_at_utc": created_at_utc,
        "production_allowed": False,
        "production_touched": False,
        "history": [
            {
                "at_utc": created_at_utc,
                "event": "REGISTERED_INITIAL",
                "lifecycle_state": "QUEUED_IN_TARGET_DOMAIN",
            }
        ],
    }
    path = hdir / f"{handoff_id}.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_g2_handoff_reconciles_already_certified_source_job_with_fingerprint_and_identity(tmp_path):
    job_id = "SEM-REQUEST-031D4113B222D9351791C548"
    hid = "HO-FABRICCOMERCIA-WORKERCONTROLP-CA40F8D825FA1505"
    _seed_certified_source_job(tmp_path, job_id=job_id, domain="FABRIC_COMERCIAL")
    _seed_recovery_handoff(tmp_path, handoff_id=hid, source_domain="FABRIC_COMERCIAL", source_job_id=job_id)

    out = handoff_mod.reconcile_cross_domain_handoffs(state_root=tmp_path, max_dispatches=0)
    assert hid in out["returned_this_cycle"]

    updated = handoff_mod.load_handoff(hid, state_root=tmp_path)
    assert updated["lifecycle_state"] == "RETURNED_TO_SOURCE"
    assert updated["dependency_satisfied"] is True
    assert updated["resolution_job_id"] == job_id
    assert updated["certification"] == "CERTIFIED_READ_ONLY"
    assert updated["evidence_link"]["source_job_recovery_verified"] is True
    assert updated["evidence_link"]["recovery_verification"]["fingerprint_matched"] is True
    assert len(updated["history"]) >= 2


def test_g2_handoff_refuses_to_close_on_fingerprint_mismatch_domain_mismatch_or_failed_evidence(tmp_path):
    # Case 1: Fingerprint mismatch between draft and done -> fail-closed
    _seed_certified_source_job(
        tmp_path,
        job_id="SEM-REQUEST-FPMISMATCH000000000001",
        domain="FABRIC_STUDIO",
        mutate_done_payload=True,
    )
    _seed_recovery_handoff(
        tmp_path,
        handoff_id="HO-FABRICSTUDIO-WORKERCONTROLP-FPMISMATCH01",
        source_domain="FABRIC_STUDIO",
        source_job_id="SEM-REQUEST-FPMISMATCH000000000001",
    )

    # Case 2: Domain mismatch -> fail-closed
    _seed_certified_source_job(
        tmp_path,
        job_id="SEM-REQUEST-DOMMISMATCH00000000002",
        domain="OTRO_DOMINIO",
    )
    _seed_recovery_handoff(
        tmp_path,
        handoff_id="HO-INVENTARIOS-WORKERCONTROLP-DOMMISMATCH02",
        source_domain="INVENTARIOS",
        source_job_id="SEM-REQUEST-DOMMISMATCH00000000002",
    )

    # Case 3: Failed check inside result -> fail-closed
    _seed_certified_source_job(
        tmp_path,
        job_id="SEM-REQUEST-CHECKFAIL0000000000003",
        domain="RH",
        check_status="FAIL",
    )
    _seed_recovery_handoff(
        tmp_path,
        handoff_id="HO-RH-WORKERCONTROLP-CHECKFAIL03",
        source_domain="RH",
        source_job_id="SEM-REQUEST-CHECKFAIL0000000000003",
    )

    out = handoff_mod.reconcile_cross_domain_handoffs(state_root=tmp_path, max_dispatches=0)
    assert out["returned_this_cycle"] == []
    for hid in (
        "HO-FABRICSTUDIO-WORKERCONTROLP-FPMISMATCH01",
        "HO-INVENTARIOS-WORKERCONTROLP-DOMMISMATCH02",
        "HO-RH-WORKERCONTROLP-CHECKFAIL03",
    ):
        rec = handoff_mod.load_handoff(hid, state_root=tmp_path)
        assert rec["dependency_satisfied"] is False
        assert rec["lifecycle_state"] != "RETURNED_TO_SOURCE"


def test_g2_handoff_reconcile_eliminates_oscillation_and_avoids_redundant_writes(tmp_path):
    job_id = "SEM-REQUEST-STILL-DRAFT-000000000001"
    hid = "HO-WORKERCONSOLE-WORKERCONTROLP-NOOSCILLATION01"
    (tmp_path / "drafts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "drafts" / f"{job_id}.json").write_text(
        json.dumps({"schema": "edarsahub.worker-job.v2", "job_id": job_id, "mode": "READ_ONLY_SQL", "production_allowed": False}),
        encoding="utf-8",
    )
    old_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    hpath = _seed_recovery_handoff(
        tmp_path,
        handoff_id=hid,
        source_domain="WORKER_CONSOLE",
        source_job_id=job_id,
        created_at_utc=old_ts,
        lifecycle_state="CLASSIFIED",
        exception_code=None,
    )

    # First reconcile escalates once to ESCALATED_HUMAN_REQUIRED
    out1 = handoff_mod.reconcile_cross_domain_handoffs(state_root=tmp_path, max_dispatches=0)
    assert hid in out1["stalled_no_executor_this_cycle"]
    rec1 = handoff_mod.load_handoff(hid, state_root=tmp_path)
    assert rec1["lifecycle_state"] == "ESCALATED_HUMAN_REQUIRED"
    assert rec1["exception_code"] == "HANDOFF_NO_EXECUTOR_STALLED"
    mtime1 = hpath.stat().st_mtime_ns
    hist_len1 = len(rec1["history"])
    raw1 = hpath.read_text(encoding="utf-8")

    # Second and third reconciles MUST NOT oscillate, MUST NOT append history, MUST NOT rewrite file
    time.sleep(0.02)
    out2 = handoff_mod.reconcile_cross_domain_handoffs(state_root=tmp_path, max_dispatches=0)
    out3 = handoff_mod.reconcile_cross_domain_handoffs(state_root=tmp_path, max_dispatches=0)

    assert hid not in out2["reclassified_this_cycle"]
    assert hid not in out2["stalled_no_executor_this_cycle"]
    assert hid not in out3["reclassified_this_cycle"]
    assert hid not in out3["stalled_no_executor_this_cycle"]
    assert hpath.stat().st_mtime_ns == mtime1, "No disk write allowed when handoff state did not change"
    assert hpath.read_text(encoding="utf-8") == raw1
    rec3 = handoff_mod.load_handoff(hid, state_root=tmp_path)
    assert len(rec3["history"]) == hist_len1
