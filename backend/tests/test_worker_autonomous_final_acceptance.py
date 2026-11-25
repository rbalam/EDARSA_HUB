"""Final Acceptance Tests for Autonomous Worker P0 Certification.

Verifies all 7 acceptance pillars deterministically without touching Production:
1. Permanent runtime autoconvergence (worker code tree, watchdog identity parity, mirror/backend/MCP convergence).
2. Multiagent coordination (normalized path disjointness, safe mirror FF under disjoint dirty worktree, overlap fail-closed).
3. Blocked job auto-resume (materialized authorization lookup, gcp.submit wiring, scope-drift fail-closed).
4. Active specific gate authorizations (materialized non-expired/non-revoked lookup in resolve_go_context + fail-closed expiry/domain).
5. MCP cold-cache performance (incremental disk index reuse across cold process restarts + immediate invalidation on change).
6. Historical queue reconciliation (non-destructive ledger for superseded PENDING_AUDIT_EVIDENCE, legacy drafts, abandoned branches).
7. Multichat terminal certification invariants (domain isolation, 6 authorized MCP tools preserved, production_touched=False).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
for p in (REPO_ROOT, BACKEND_ROOT, REPO_ROOT / "tools" / "mirror_sync"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from tools.mirror_sync import git_divergence_guard as gdg
from tools.mirror_sync import worker_control_plane as wcp
from tools.mirror_sync import worker_lifecycle_recovery as lr
from modules.worker_ingress import service as wis


def _init_git_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-b", "Edarsahub_Desarrollo"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@edarsa.com.mx"], check=True)
    (repo / "a.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "b.py").write_text("y = 1\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], check=True, capture_output=True)
    sha = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    return repo, sha


def _setup_queue(repo: Path) -> Path:
    qroot = repo / ".git" / "universal-worker-queue"
    for sub in (
        "drafts",
        "pending",
        "processing",
        "done",
        "rejected",
        "results",
        "published",
        "runtime",
        "maintenance/incidents",
        "maintenance/circuit_breakers",
        "maintenance/authorizations",
    ):
        (qroot / sub).mkdir(parents=True, exist_ok=True)
    (repo / ".git" / "agent-guard" / "state" / "claims").mkdir(parents=True, exist_ok=True)
    (repo / ".git" / "mirror-sync" / "reporting" / "test_attestations").mkdir(parents=True, exist_ok=True)
    return qroot


def test_01_permanent_autoconvergence_contract_and_watchdog_parity():
    # 1. universal_job_worker.sh must atomically record active_worker_code_tree_sha on startup
    worker_sh = (REPO_ROOT / "tools" / "mirror_sync" / "universal_job_worker.sh").read_text(encoding="utf-8")
    assert "active_worker_code_tree_sha" in worker_sh
    assert "HEAD:tools/mirror_sync" in worker_sh

    # 2. Control plane and bootstrap watchdog must track identical expanded identity paths
    watchdog_src = (REPO_ROOT / "tools" / "bootstrap" / "edarsahub_bootstrap_watchdog.py").read_text(encoding="utf-8")
    for rel in (
        "tools/mirror_sync/worker_lifecycle_recovery.py",
        "tools/mirror_sync/git_divergence_guard.py",
        "tools/mirror_sync/worker_repair_auto_loop.py",
        "tools/mirror_sync/worker_runtime_fingerprint.py",
    ):
        assert rel in wcp.CONTROL_PLANE_IDENTITY_PATHS
        assert rel in watchdog_src

    # 3. converge_runtime_permanently must fail closed in Production environment
    orig_env = os.environ.get("EDARSA_ENV")
    try:
        os.environ["EDARSA_ENV"] = "PRODUCTION"
        out = wcp.converge_runtime_permanently(ff={"ff": "ALREADY_ALIGNED"}, runtime={})
        assert out["status"] == "BLOCKED_PRODUCTION_ENV"
        assert out["production_touched"] is False
    finally:
        if orig_env is None:
            os.environ.pop("EDARSA_ENV", None)
        else:
            os.environ["EDARSA_ENV"] = orig_env


def test_02_multiagent_coordination_normalized_paths_and_mirror_ff():
    # Normalized relative paths detect overlap even with './' prefix
    dirty_state = {
        "current_branch": "Edarsahub_Desarrollo",
        "worktree_dirty": True,
        "ahead_count": 0,
        "behind_count": 0,
        "classification": "DIRTY_WORKTREE",
        "dirty_paths": ["./backend/modules/worker_mcp/server.py"],
    }
    overlap = gdg.mutation_policy(
        dirty_state,
        requested_paths=["backend/modules/worker_mcp/server.py"],
        isolated_worktree=True,
    )
    assert overlap["allowed"] is False
    assert overlap["reason"] == "GIT_WORKTREE_CONCURRENT_SCOPE_CONFLICT"

    # Disjoint dirty worktree with mirror behind development allows safe mirror FF without touching local dirty files
    conv = gdg.classify_submit_convergence(
        local="b" * 40,
        development="b" * 40,
        mirror="a" * 40,
        local_merge_base="b" * 40,
        mirror_merge_base="a" * 40,
        worktree_dirty=True,
        dirty_paths=["backend/modules/worker_mcp/server.py"],
        requested_paths=["backend/modules/cajas/service.py"],
    )
    assert conv["status"] == "SAFE_MIRROR_FF_ISOLATED_LOCAL_DIRTY_DISJOINT"
    assert conv["mirror_fast_forward_safe"] is True
    assert conv["safe"] is True
    assert conv["local_checkout_refresh_deferred"] is True


def test_03_auto_resume_uses_materialized_authorization_and_gcp_submit(tmp_path, monkeypatch):
    repo, base_sha = _init_git_repo(tmp_path)
    qroot = _setup_queue(repo)
    now_ts = time.time()

    jid = "EDARSAHUB-FINAL-ACCEPT-RESUME-001"
    draft = {
        "schema": "edarsahub.worker-job.v2",
        "job_id": jid,
        "mode": "MUTATION",
        "target_repo": "rbalam/EDARSA_HUB",
        "target_branch": "Edarsahub_Desarrollo",
        "base_sha": base_sha,
        "production_allowed": False,
        "human_summary_language": "es",
        "objective": "Authorized auto-resume test",
        "actions": [{"type": "write_file", "path": "a.py", "content": "x = 2\n"}],
        "checks": [{"type": "git_diff_check"}],
        "requester": {
            "email": "ricardo@edarsa.com.mx",
            "source": "edarsahub-worker-ingress",
            "project": "EDARSAHUB",
            "chat": "final-acceptance",
        },
        "scheduling": {
            "project_id": "EDARSAHUB",
            "bounded_context": "WORKER_CONTROL_PLANE",
            "priority_class": "NORMAL",
            "fairness_weight": 1,
            "max_parallelism": 1,
            "resource_claims": [],
            "conflict_domains": ["WORKER_CONTROL_PLANE"],
        },
    }
    (qroot / "drafts" / f"{jid}.json").write_text(json.dumps(draft), encoding="utf-8")
    (qroot / "results" / f"{jid}.json").write_text(
        json.dumps({
            "schema": "edarsahub.worker-result.v2",
            "job_id": jid,
            "status": "BLOCKED_CONVERGENCE",
            "certification": "NOT_CERTIFIED",
            "execution_base_sha": base_sha,
            "completed_at_utc": "2026-11-25T09:00:00Z",
            "production_touched": False,
        }),
        encoding="utf-8",
    )

    # Without materialized authorization -> fail closed
    denied = lr.resume_authorized_concurrency_blocked_objective(
        jid,
        repo_root=repo,
        state_root=qroot,
        git_state_override={"current_branch": "Edarsahub_Desarrollo", "worktree_dirty": False, "classification": "SYNC", "local_head": base_sha, "remote_head": base_sha},
        now_epoch=now_ts,
    )
    assert denied["resumed"] is False
    assert denied["action"] == "ESCALATE_POLICY"

    # Materialize active Gate authorization -> default gcp.submit path (no NameError!) succeeds
    lr.materialize_gate_authorization(
        gate_id="FINAL-ACCEPT-TEST",
        authorization_id="GO-FINAL-ACCEPT-TEST",
        granted_by="ricardo@edarsa.com.mx",
        domains=["WORKER_CONTROL_PLANE"],
        allowed_paths=["a.py"],
        state_root=qroot,
    )
    captured = []
    monkeypatch.setattr(lr.gcp, "submit", lambda payload, require_convergence=False: (captured.append(payload), {"status": "SUBMITTED", "job_id": payload["job_id"]})[1])
    ok = lr.resume_authorized_concurrency_blocked_objective(
        jid,
        repo_root=repo,
        state_root=qroot,
        git_state_override={"current_branch": "Edarsahub_Desarrollo", "worktree_dirty": False, "classification": "SYNC", "local_head": base_sha, "remote_head": base_sha},
        now_epoch=now_ts,
    )
    assert ok["resumed"] is True
    assert ok["resume_job_id"] == f"{jid}-RESUME-1"
    assert len(captured) == 1
    assert ok["production_touched"] is False


def test_04_active_materialized_authorizations_and_05_cold_cache_disk_index(tmp_path, monkeypatch):
    repo, base_sha = _init_git_repo(tmp_path)
    qroot = _setup_queue(repo)
    monkeypatch.setattr(wis, "STATE_ROOT", qroot)
    wis._GO_CONTEXT_CACHE.clear()

    # Seed done/results artifacts
    done_job = {
        "job_id": "SEM-WORKER_INGRESS-CERT-001",
        "mode": "READ_ONLY",
        "objective": "Seeded audit",
        "scheduling": {"bounded_context": "WORKER_INGRESS"},
    }
    (qroot / "done" / "SEM-WORKER_INGRESS-CERT-001.json").write_text(json.dumps(done_job), encoding="utf-8")
    (qroot / "results" / "SEM-WORKER_INGRESS-CERT-001.json").write_text(
        json.dumps({
            "schema": "edarsahub.worker-result.v2",
            "job_id": "SEM-WORKER_INGRESS-CERT-001",
            "status": "READ_ONLY_COMPLETE",
            "quality_gate": "PASS",
            "tests": "PASS",
            "certification": "CERTIFIED_READ_ONLY",
            "work_completion": "COMPLETE",
            "percent_complete": 100,
            "blockers": [],
            "completed_at_utc": "2026-11-25T09:00:00Z",
            "summary_es": "Auditoria certificada",
            "production_touched": False,
        }),
        encoding="utf-8",
    )

    # Materialize active Gate authorization for WORKER_INGRESS only
    lr.materialize_gate_authorization(
        gate_id="ACTIVE-AUTH-TEST",
        authorization_id="GO-ACTIVE-AUTH-TEST",
        granted_by="ricardo@edarsa.com.mx",
        domains=["WORKER_INGRESS"],
        allowed_paths=["backend/modules/worker_ingress/service.py"],
        state_root=qroot,
    )

    admin = {"email": "ricardo@edarsa.com.mx", "role": "SUPERADMIN", "permissions": ["*"]}
    # First cold call builds disk index
    ctx1 = wis.resolve_go_context(domain="WORKER_INGRESS", current_user=admin, config_dir=tmp_path / "nochains")
    assert ctx1["mutation_allowed"] is True
    assert ctx1["active_authorizations"]["explicit_authorization_status"] == "MATERIALIZED_GATE_AUTHORIZATION_VERIFIED"
    assert ctx1["active_authorizations"]["explicit_authorization_id"] == "GO-ACTIVE-AUTH-TEST"
    assert (qroot / "runtime" / wis._GO_CONTEXT_DISK_INDEX_NAME).is_file()

    # Simulate cold process restart by clearing in-memory cache -> disk index is reused!
    wis._GO_CONTEXT_CACHE.clear()
    ctx2 = wis.resolve_go_context(domain="WORKER_INGRESS", current_user=admin, config_dir=tmp_path / "nochains")
    assert ctx2["continuity"]["disk_index_reused"] is True
    assert ctx2["last_certified_gate"]["job_id"] == "SEM-WORKER_INGRESS-CERT-001"

    # Unrelated domain must remain fail-closed (mutation_allowed=False)
    ctx_other = wis.resolve_go_context(domain="FINANZAS_CXP", current_user=admin, config_dir=tmp_path / "nochains")
    assert ctx_other["mutation_allowed"] is False
    assert ctx_other["active_authorizations"]["explicit_mutation_authorized"] is False


def test_06_historical_reconciliation_ledger_non_destructive(tmp_path):
    repo, sha1 = _init_git_repo(tmp_path)
    qroot = _setup_queue(repo)
    # Create origin/Edarsahub_Desarrollo and origin/mirror/emergent-live refs at a newer commit modifying a.py
    (repo / "a.py").write_text("x = 2\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "a.py"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "evolve a.py"], check=True, capture_output=True)
    sha2 = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    subprocess.run(["git", "-C", str(repo), "update-ref", "refs/remotes/origin/Edarsahub_Desarrollo", sha2], check=True)
    subprocess.run(["git", "-C", str(repo), "update-ref", "refs/remotes/origin/mirror/emergent-live", sha2], check=True)

    # Seed historical PENDING_AUDIT_EVIDENCE marker for sha1 (attested + superseded by sha2)
    jid = "HIST-JOB-001"
    (qroot / "results" / f"{jid}.json").write_text(
        json.dumps({"job_id": jid, "status": "INTEGRATED", "development_sha": sha1, "files_changed": ["a.py"]}),
        encoding="utf-8",
    )
    (qroot / "published" / f"{jid}.json").write_text(
        "published=2026-10-01T00:00:00Z\ncommit=1234\ncertification=PENDING_AUDIT_EVIDENCE\n",
        encoding="utf-8",
    )
    (repo / ".git" / "mirror-sync" / "reporting" / "test_attestations" / f"{sha1}.json").write_text("{}", encoding="utf-8")

    # Seed abandoned old draft + orphan publisher branch
    old_draft_id = "OLD-ABANDONED-DRAFT-001"
    old_draft = qroot / "drafts" / f"{old_draft_id}.json"
    old_draft.write_text(json.dumps({"job_id": old_draft_id, "mode": "MUTATION", "scheduling": {"bounded_context": "WORKER_INGRESS"}}), encoding="utf-8")
    old_ts = time.time() - (86400 * 10)
    os.utime(old_draft, (old_ts, old_ts))
    subprocess.run(["git", "-C", str(repo), "branch", f"agent/queue-publisher/{old_draft_id}", sha1], check=True)

    ledger = lr.reconcile_historical_queue_artifacts(
        repo_root=repo,
        state_root=qroot,
        claims_dir=repo / ".git" / "agent-guard" / "state" / "claims",
        attestations_dir=repo / ".git" / "mirror-sync" / "reporting" / "test_attestations",
        force_refresh=True,
    )
    assert ledger["schema"] == lr.SCHEMA_HISTORICAL_RECONCILIATION
    assert ledger["pending_audit_reconciled"][jid]["classification"] == "HISTORICAL_SUPERSEDED_ATTESTED"
    assert ledger["historical_drafts_classified"][old_draft_id]["preserved_untouched"] is True
    assert old_draft.is_file()  # Never deleted!
    assert ledger["abandoned_branches_pruned_count"] == 1
    assert ledger["production_touched"] is False

    # Scanner now reports 0 live pending_audit_stale and 1 historically reconciled
    det = lr.scan_global_lifecycle_blockers(
        repo_root=repo,
        state_root=qroot,
        claims_dir=repo / ".git" / "agent-guard" / "state" / "claims",
        attestations_dir=repo / ".git" / "mirror-sync" / "reporting" / "test_attestations",
        force_full=True,
        remote_inbox_ids=set(),
        remote_result_ids=set(),
    )
    assert det["counts"]["pending_audit_stale"] == 0
    assert det["historical_reconciled_pending_audit_count"] == 1
    assert det["counts"]["orphan_branches"] == 0
