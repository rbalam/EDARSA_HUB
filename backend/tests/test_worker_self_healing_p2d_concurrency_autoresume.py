"""Gate P2D tests: Canonical Gate Authorization, Multiagent Worktree Isolation & Authorized Auto-Resume."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
for p in (REPO_ROOT, REPO_ROOT / "tools" / "mirror_sync"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from tools.mirror_sync import git_divergence_guard as gdg
from tools.mirror_sync import worker_lifecycle_recovery as lr


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


def _make_mutation_draft(job_id: str, path: str, base_sha: str, domain: str = "WORKER_CONTROL_PLANE") -> dict:
    return {
        "schema": "edarsahub.worker-job.v2",
        "job_id": job_id,
        "mode": "MUTATION",
        "target_repo": "rbalam/EDARSA_HUB",
        "target_branch": "Edarsahub_Desarrollo",
        "base_sha": base_sha,
        "production_allowed": False,
        "human_summary_language": "es",
        "objective": f"Controlled mutation test for {job_id}",
        "actions": [{"type": "write_file", "path": path, "content": "updated = True\n"}],
        "checks": [{"type": "git_diff_check"}],
        "requester": {
            "email": "ricardo@edarsa.com.mx",
            "source": "edarsahub-worker-ingress",
            "project": "EDARSAHUB",
            "chat": "p2d-test",
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


def _setup_queue(repo: Path) -> Path:
    qroot = repo / ".git" / "universal-worker-queue"
    for sub in ("drafts", "pending", "processing", "done", "rejected", "results", "published", "maintenance/circuit_breakers", "maintenance/authorizations"):
        (qroot / sub).mkdir(parents=True, exist_ok=True)
    return qroot


def test_01_canonical_gate_p2d_authorization_materialization_and_fail_closed(tmp_path: Path) -> None:
    qroot = _setup_queue(tmp_path)
    mat = lr.materialize_gate_authorization(
        gate_id="SELF-HEALING-P2D",
        authorization_id="GO-P2D-TEST-001",
        granted_by="ricardo@edarsa.com.mx",
        domains=["WORKER_CONTROL_PLANE"],
        allowed_paths=["tools/mirror_sync/git_divergence_guard.py"],
        state_root=qroot,
    )
    assert mat["production_allowed"] is False
    assert Path(mat["authorization_path"]).is_file()

    # Positive verification in allowed domain
    ok = lr.verify_gate_authorization("SELF-HEALING-P2D", domain="WORKER_CONTROL_PLANE", state_root=qroot)
    assert ok["authorized"] is True
    assert ok["reason"] == "AUTHORIZED"

    # Negative: wrong domain fails closed
    wrong_dom = lr.verify_gate_authorization("SELF-HEALING-P2D", domain="FINANZAS_CXP", state_root=qroot)
    assert wrong_dom["authorized"] is False
    assert wrong_dom["reason"] == "SCOPE_AUTHORIZATION_DENIED"

    # Negative: expired authorization fails closed
    future = datetime.now(timezone.utc) + timedelta(hours=48)
    expired = lr.verify_gate_authorization("SELF-HEALING-P2D", domain="WORKER_CONTROL_PLANE", state_root=qroot, now_utc=future)
    assert expired["authorized"] is False
    assert expired["reason"] == "AUTHORIZATION_EXPIRED"

    # Negative: production_allowed=True always rejected
    with pytest.raises(ValueError, match="PRODUCTION_AUTHORIZATION_FORBIDDEN"):
        lr.materialize_gate_authorization(
            gate_id="BAD-PROD",
            authorization_id="GO-BAD",
            granted_by="ricardo@edarsa.com.mx",
            domains=["WORKER_CONTROL_PLANE"],
            state_root=qroot,
            production_allowed=True,
        )


def test_02_multiagent_dirty_worktree_disjoint_vs_overlap_and_backward_compat() -> None:
    dirty_state = {
        "current_branch": "Edarsahub_Desarrollo",
        "worktree_dirty": True,
        "ahead_count": 0,
        "behind_count": 0,
        "classification": "DIRTY_WORKTREE",
        "dirty_paths": ["backend/modules/worker_mcp/server.py"],
    }

    # Backward compatibility: without isolated_worktree=True, ALWAYS fails closed
    legacy = gdg.mutation_policy(dirty_state)
    assert legacy["allowed"] is False
    assert legacy["terminal_status"] == "GIT_WORKTREE_NOT_CLEAN"

    # Disjoint scope in isolated worktree -> ALLOWED, preserves concurrent dirty files untouched
    disjoint = gdg.mutation_policy(
        dirty_state,
        requested_paths=["backend/modules/cajas/service.py"],
        isolated_worktree=True,
    )
    assert disjoint["allowed"] is True
    assert disjoint["terminal_status"] == "ISOLATED_WORKTREE_DISJOINT_DIRTY"
    assert disjoint["local_checkout_refresh_deferred"] is True
    assert disjoint["dirty_paths_preserved"] == ["backend/modules/worker_mcp/server.py"]

    # Overlapping scope -> FAIL CLOSED with explicit scope conflict
    overlap = gdg.mutation_policy(
        dirty_state,
        requested_paths=["backend/modules/worker_mcp/server.py", "backend/modules/cajas/service.py"],
        isolated_worktree=True,
    )
    assert overlap["allowed"] is False
    assert overlap["terminal_status"] == "GIT_WORKTREE_NOT_CLEAN"
    assert overlap["reason"] == "GIT_WORKTREE_CONCURRENT_SCOPE_CONFLICT"
    assert overlap["scope_conflicts"] == ["backend/modules/worker_mcp/server.py"]

    # Submit convergence: disjoint allowed when development == mirror, overlap blocked
    conv_ok = gdg.classify_submit_convergence(
        local="a" * 40,
        development="a" * 40,
        mirror="a" * 40,
        local_merge_base="a" * 40,
        mirror_merge_base="a" * 40,
        worktree_dirty=True,
        dirty_paths=["backend/modules/worker_mcp/server.py"],
        requested_paths=["backend/modules/cajas/service.py"],
    )
    assert conv_ok["converged"] is True
    assert conv_ok["status"] == "CONVERGED_ISOLATED_LOCAL_DIRTY_DISJOINT"

    conv_block = gdg.classify_submit_convergence(
        local="a" * 40,
        development="a" * 40,
        mirror="a" * 40,
        local_merge_base="a" * 40,
        mirror_merge_base="a" * 40,
        worktree_dirty=True,
        dirty_paths=["backend/modules/worker_mcp/server.py"],
        requested_paths=["backend/modules/worker_mcp/server.py"],
    )
    assert conv_block["converged"] is False
    assert conv_block["status"] == "BLOCKED_LOCAL_DIRTY"
    assert conv_block["scope_conflicts"] == ["backend/modules/worker_mcp/server.py"]


def test_03_authorized_concurrency_auto_resume_positive_and_fail_closed(tmp_path: Path) -> None:
    repo, base_sha = _init_git_repo(tmp_path)
    qroot = _setup_queue(repo)
    cb_dir = qroot / "maintenance" / "circuit_breakers"
    now_ts = 1_795_600_000.0

    jid = "EDARSAHUB-P2D-CONC-BLOCKED-001"
    draft = _make_mutation_draft(jid, "a.py", base_sha, domain="WORKER_CONTROL_PLANE")
    (qroot / "drafts" / f"{jid}.json").write_text(json.dumps(draft), encoding="utf-8")
    (qroot / "results" / f"{jid}.json").write_text(
        json.dumps({
            "job_id": jid,
            "status": "GIT_WORKTREE_NOT_CLEAN",
            "certification": "NOT_CERTIFIED",
            "execution_base_sha": base_sha,
            "production_touched": False,
        }),
        encoding="utf-8",
    )

    clean_git = {
        "current_branch": "Edarsahub_Desarrollo",
        "local_head": base_sha,
        "remote_head": base_sha,
        "ahead_count": 0,
        "behind_count": 0,
        "worktree_dirty": False,
        "dirty_paths": [],
        "classification": "SYNC",
    }

    # 1. Without explicit mutation authorization -> FAIL CLOSED (never auto-resumes unauthorized mutation)
    unauth = lr.resume_authorized_concurrency_blocked_objective(
        jid, repo_root=repo, state_root=qroot, circuit_state_dir=cb_dir, git_state_override=clean_git, now_epoch=now_ts,
    )
    assert unauth["resumed"] is False
    assert unauth["action"] == "ESCALATE_POLICY"

    # 2. With revoked authorization -> FAIL CLOSED
    revoked = lr.resume_authorized_concurrency_blocked_objective(
        jid,
        repo_root=repo,
        state_root=qroot,
        circuit_state_dir=cb_dir,
        authorization_context={"revoked": True, "authorization_id": "GO-REV"},
        git_state_override=clean_git,
        now_epoch=now_ts,
    )
    assert revoked["resumed"] is False
    assert revoked["reason"] == "AUTHORIZATION_REVOKED"

    # 3. With valid materialized authorization -> RESUMES ONCE with deterministic idempotent resume_job_id
    auth = lr.materialize_gate_authorization(
        gate_id="P2D-RESUME-TEST",
        authorization_id="GO-P2D-RESUME-001",
        granted_by="ricardo@edarsa.com.mx",
        domains=["WORKER_CONTROL_PLANE"],
        state_root=qroot,
    )
    submitted: list[dict] = []

    def fake_submit(job_spec, *, require_convergence=False):
        submitted.append(dict(job_spec))
        (qroot / "pending" / f"{job_spec['job_id']}.json").write_text(json.dumps(job_spec), encoding="utf-8")
        return {"status": "SUBMITTED", "job_id": job_spec["job_id"], "production_touched": False}

    ok = lr.resume_authorized_concurrency_blocked_objective(
        jid,
        repo_root=repo,
        state_root=qroot,
        circuit_state_dir=cb_dir,
        authorization_context=auth,
        git_state_override=clean_git,
        submit_fn=fake_submit,
        now_epoch=now_ts,
    )
    assert ok["resumed"] is True
    assert ok["action"] == "RESUMED_VIA_CANONICAL_PUBLISHER"
    assert ok["resume_job_id"] == f"{jid}-RESUME-1"
    assert len(submitted) == 1
    assert submitted[0]["metadata"]["resumed_from_job_id"] == jid
    assert submitted[0]["production_allowed"] is False

    # 4. Idempotency: second call while resume is in-flight skips without duplicating
    dup = lr.resume_authorized_concurrency_blocked_objective(
        jid,
        repo_root=repo,
        state_root=qroot,
        circuit_state_dir=cb_dir,
        authorization_context=auth,
        git_state_override=clean_git,
        submit_fn=fake_submit,
        now_epoch=now_ts + 5,
    )
    assert dup["resumed"] is False
    assert dup["action"] == "SKIP_RESUME_IN_FLIGHT"
    assert len(submitted) == 1


def test_04_auto_resume_fails_closed_on_head_scope_drift(tmp_path: Path) -> None:
    repo, base_sha = _init_git_repo(tmp_path)
    qroot = _setup_queue(repo)
    cb_dir = qroot / "maintenance" / "circuit_breakers"

    # Advance HEAD modifying a.py -> causes scope drift for job targeting a.py
    (repo / "a.py").write_text("x = 2  # concurrent commit\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "a.py"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "concurrent change on a.py"], check=True, capture_output=True)
    new_head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()

    jid = "EDARSAHUB-P2D-DRIFT-001"
    draft = _make_mutation_draft(jid, "a.py", base_sha, domain="WORKER_CONTROL_PLANE")
    (qroot / "drafts" / f"{jid}.json").write_text(json.dumps(draft), encoding="utf-8")
    (qroot / "results" / f"{jid}.json").write_text(
        json.dumps({
            "job_id": jid,
            "status": "GIT_WORKTREE_NOT_CLEAN",
            "certification": "NOT_CERTIFIED",
            "execution_base_sha": base_sha,
            "production_touched": False,
        }),
        encoding="utf-8",
    )
    auth = lr.materialize_gate_authorization(
        gate_id="P2D-DRIFT-TEST",
        authorization_id="GO-P2D-DRIFT-001",
        granted_by="ricardo@edarsa.com.mx",
        domains=["WORKER_CONTROL_PLANE"],
        state_root=qroot,
    )
    drift_out = lr.resume_authorized_concurrency_blocked_objective(
        jid,
        repo_root=repo,
        state_root=qroot,
        circuit_state_dir=cb_dir,
        authorization_context=auth,
        git_state_override={
            "current_branch": "Edarsahub_Desarrollo",
            "local_head": new_head,
            "remote_head": new_head,
            "ahead_count": 0,
            "behind_count": 0,
            "worktree_dirty": False,
            "dirty_paths": [],
            "classification": "SYNC",
        },
    )
    assert drift_out["resumed"] is False
    assert drift_out["action"] == "ESCALATE_SCOPE_DRIFT"
    assert drift_out["reason"] == "RESUME_BLOCKED_SCOPE_DRIFT"
    assert drift_out["drifted_paths"] == ["a.py"]
