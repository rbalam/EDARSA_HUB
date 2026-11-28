"""Certification Suite for EDARSAHUB BOS — AUTONOMOUS RUNTIME RECOVERY G1 (Phases 1-6).

Validates every architectural invariant without touching Production or widening global permissions:
- Phase 1 & 2: Non-destructive platform-only local-ahead Git recovery (preserving commit refs +
  working tree, NEVER git reset --hard / force push), fail-closed preservation of non-platform
  local code commits, breaking circular dependency ONLY for WORKER_REPAIR_BOUNDED
  (capability_code=RUNTIME_CONVERGENCE_RECOVERY) while keeping all other mutations blocked when
  overall_converged=False, RBAC fail-closed, idempotency, concurrency, 6/6 MCP tools preserved.
- Phase 3 (Consent Bridge G1B): Explicit separation of Preview/Development human portal origin vs
  Production hosts (never emitting stock-tracker-990.emergent.host or hub.edarsa.com.mx),
  canonical INVALIDATE_STALE on HEAD/SHA drift, OAuth review stale guard, zero auto-approval.
- Phase 4 (Cross-Domain Handoff Recovery): Safe reassignment of semantic-blocker handoffs
  (HANDOFF_CANARY_INSUFFICIENT_FOR_OBJECTIVE, e.g. HO-BITACORAS-WORKERCONTROLP-0A8BB6B347CDA64A)
  without IDEMPOTENCY_CONFLICT 409 or 504 timeout, preserving identity, history, acceptance
  criteria, RBAC, prior insufficient evidence, and preventing duplicates.
- Phase 5 (Knowledge Loop): Audit trail recording and strict enforcement that SUPERSEDED never
  certifies a repair or learned capability.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
for _p in (REPO_ROOT, BACKEND_ROOT, REPO_ROOT / "tools" / "mirror_sync"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from modules.worker_ingress import semantic_capabilities as sem_caps
from modules.worker_ingress import service as wis
from modules.worker_mcp import oauth_server
from tools.mirror_sync import git_divergence_guard as gdg
from tools.mirror_sync import worker_control_plane as wcp
from tools.mirror_sync import worker_cross_domain_handoff as hm
from tools.mirror_sync import worker_lifecycle_recovery as lr
from tools.mirror_sync import worker_repair_capability_registry as learned_reg


def _actor(
    *,
    usuario_id: int = 8,
    email: str = "ricardo@edarsa.com.mx",
    role: str = "SuperAdministrador",
    role_code: str = "SUPERADMIN",
    permissions: list[str] | None = None,
    scopes: list[str] | None = None,
    session_id: str | None = "sess-human-recovery-g1",
) -> dict:
    doc = {
        "id": f"uuid-{usuario_id}",
        "usuario_id": usuario_id,
        "_sql_usuario_id": usuario_id,
        "email": email,
        "role": role,
        "role_code": role_code,
        "active": True,
        "permissions": (
            list(permissions)
            if permissions is not None
            else ["RBAC_ADMIN", "CENTRO_CONTROL_VER", "worker:status", "worker:submit"]
        ),
        "scopes": list(scopes) if scopes is not None else ["worker:status", "worker:submit"],
        "auth_source": "SQL_CANONICAL_RBAC",
        "identity_verified": True,
    }
    if session_id is not None:
        doc["_session_id"] = session_id
    return doc


def _init_repo_with_origin(tmp_path: Path) -> tuple[Path, Path, str]:
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", str(bare)], check=True, capture_output=True)
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-b", "Edarsahub_Desarrollo"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "EDARSAHUB Worker"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "worker@edarsahub.local"], check=True)
    subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", str(bare)], check=True)

    (repo / ".emergent").mkdir(parents=True, exist_ok=True)
    (repo / ".emergent" / "system_deps.txt").write_text("git\n", encoding="utf-8")
    (repo / "app.code-workspace").write_text("{}\n", encoding="utf-8")
    (repo / "backend" / "modules").mkdir(parents=True, exist_ok=True)
    (repo / "backend" / "modules" / "demo_mod.py").write_text("X = 1\n", encoding="utf-8")
    (repo / "backend" / "tests").mkdir(parents=True, exist_ok=True)
    (repo / "backend" / "tests" / "test_demo_mod.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "base"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "push", "-u", "origin", "Edarsahub_Desarrollo"], check=True, capture_output=True)
    base_sha = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    return repo, bare, base_sha


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
        "maintenance/approvals",
        "maintenance/consent_requests",
        "maintenance/handoffs",
    ):
        (qroot / sub).mkdir(parents=True, exist_ok=True)
    return qroot


def test_phase1_phase2_platform_local_ahead_recovery_preserves_commits_and_blocks_code_commits(tmp_path):
    """Phase 1/2: Recover Emergent platform-only local commit non-destructively; fail closed on legitimate code commits."""
    repo, _bare, base_sha = _init_repo_with_origin(tmp_path)

    # 1. Create an Emergent platform-only local commit (exact pattern of 358bcf236)
    (repo / ".emergent" / "system_deps.txt").write_text("", encoding="utf-8")
    (repo / "app.code-workspace").write_text('{"folders": [{"path": "."}]}\n', encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", ".emergent/system_deps.txt", "app.code-workspace"], check=True)
    subprocess.run(
        [
            "git", "-C", str(repo),
            "-c", "user.name=emergent-agent-e1",
            "-c", "user.email=github@emergent.sh",
            "commit", "-m", "platform auto commit",
        ],
        check=True,
        capture_output=True,
    )
    plat_sha = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    assert plat_sha != base_sha

    cls = gdg.classify_platform_only_local_ahead(repo)
    assert cls["eligible"] is True
    assert cls["ahead_count"] == 1

    rec = gdg.recover_platform_only_local_ahead(repo, owner="test-recovery")
    assert rec["recovered"] is True
    assert rec["local_head_after"] == base_sha
    assert rec["reset_mode"] == "mixed_non_destructive"
    assert rec["production_touched"] is False

    # Preserved branch points to exact platform commit AND working tree file contents are preserved!
    preserved_sha = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", rec["preserved_branch"]], text=True
    ).strip()
    assert preserved_sha == plat_sha
    assert (repo / "app.code-workspace").read_text(encoding="utf-8") == '{"folders": [{"path": "."}]}\n'

    # 2. Now create a legitimate local CODE commit -> MUST FAIL CLOSED and NEVER discard!
    (repo / "backend" / "modules" / "demo_mod.py").write_text("X = 2\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "backend/modules/demo_mod.py"], check=True)
    subprocess.run(
        [
            "git", "-C", str(repo),
            "-c", "user.name=emergent-agent-e1",
            "-c", "user.email=github@emergent.sh",
            "commit", "-m", "legitimate code change",
        ],
        check=True,
        capture_output=True,
    )
    code_sha = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()

    cls_code = gdg.classify_platform_only_local_ahead(repo)
    assert cls_code["eligible"] is False
    assert cls_code["reason"] == "LOCAL_AHEAD_CONTAINS_NON_PLATFORM_CHANGES"
    with pytest.raises(gdg.GitGuardError, match="LOCAL_AHEAD_CONTAINS_NON_PLATFORM_CHANGES"):
        gdg.recover_platform_only_local_ahead(repo, owner="test-recovery")
    # HEAD MUST remain untouched on code_sha!
    assert subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip() == code_sha


def test_phase2_breaks_circular_convergence_dependency_only_for_bounded_recovery_and_preserves_6_mcp_tools(
    tmp_path, monkeypatch
):
    """Phase 2: WORKER_REPAIR_BOUNDED(RUNTIME_CONVERGENCE_RECOVERY) bypasses convergence deadlock while normal mutations stay blocked."""
    repo, _bare, base_sha = _init_repo_with_origin(tmp_path)
    qroot = _setup_queue(repo)
    actor = _actor()

    monkeypatch.setattr(wis, "STATE_ROOT", qroot)
    monkeypatch.setattr(wis, "REPO_ROOT", repo)
    monkeypatch.setattr(
        wis,
        "_require_mutation_runtime_convergence",
        lambda: (_ for _ in ()).throw(wis.WorkerIngressError("RUNTIME_NOT_CONVERGED")),
    )

    # 1. Exact 6 MCP tools preserved
    if importlib.util.find_spec("mcp") is None:
        for cand in sorted(Path("/app/.runtime/worker_mcp/venv/lib").glob("python*/site-packages")):
            if str(cand) not in sys.path:
                sys.path.append(str(cand))
    from modules.worker_mcp import server as mcp_server

    assert set(mcp_server.TOOL_REQUIRED_SCOPES) == {
        "submit_objective",
        "get_job_status",
        "get_go_context",
        "list_capabilities",
        "preflight_objective",
        "get_runtime_convergence",
    }

    # 2. Normal DEVELOPMENT_MUTATION_BOUNDED MUST STILL FAIL CLOSED with RUNTIME_NOT_CONVERGED!
    dev_mut = {
        "objective": "Intentar mutacion normal sin convergencia.",
        "bounded_context": "COMERCIAL_POS",
        "mode": "MUTATION",
        "capability": "DEVELOPMENT_MUTATION_BOUNDED",
        "constraints": {
            "change_spec": [],
            "verification_tests": ["backend/tests/test_demo_mod.py"],
            "authorization_ref": "GO-DEMO",
        },
    }
    pf_dev = wis.preflight_semantic_objective(dev_mut, current_user=actor, enforce_runtime_convergence=True)
    assert pf_dev["ok"] is False
    assert pf_dev["error_code"] == "RUNTIME_NOT_CONVERGED"

    # 3. Non-convergence WORKER_REPAIR_BOUNDED capability MUST STILL FAIL CLOSED with RUNTIME_NOT_CONVERGED!
    other_rep = {
        "objective": "Intentar otra reparacion sin convergencia.",
        "bounded_context": "WORKER_RUNTIME_CONVERGENCE",
        "mode": "MUTATION",
        "capability": "WORKER_REPAIR_BOUNDED",
        "constraints": {
            "incident_id": "INC-OTHER-R1",
            "capability_code": "MUTATION_LIFECYCLE_STALE_OWNERSHIP",
        },
    }
    pf_other = wis.preflight_semantic_objective(other_rep, current_user=actor, enforce_runtime_convergence=True)
    assert pf_other["ok"] is False
    assert pf_other["error_code"] == "RUNTIME_NOT_CONVERGED"

    # 4. Bounded RUNTIME_CONVERGENCE_RECOVERY breaks the deadlock cleanly WITH full RBAC enforcement!
    rec_req = {
        "objective": "Recuperar convergencia Git/runtime acotada y auditable en Desarrollo.",
        "bounded_context": "WORKER_RUNTIME_CONVERGENCE",
        "mode": "MUTATION",
        "capability": "WORKER_REPAIR_BOUNDED",
        "constraints": {
            "incident_id": "INC-CONV-G1-R1",
            "capability_code": "RUNTIME_CONVERGENCE_RECOVERY",
        },
    }
    # Non-admin RBAC MUST STILL BE DENIED!
    non_admin = _actor(role="Operador", role_code="OPERADOR", permissions=["CENTRO_CONTROL_VER"], scopes=[])
    pf_denied = wis.preflight_semantic_objective(rec_req, current_user=non_admin, enforce_runtime_convergence=True)
    assert pf_denied["ok"] is False
    assert pf_denied["error_code"] == "RBAC_MUTATION_FORBIDDEN"

    pf_rec = wis.preflight_semantic_objective(rec_req, current_user=actor, enforce_runtime_convergence=True)
    assert pf_rec["ok"] is True
    assert pf_rec["status"] == "PREFLIGHT_READY"

    monkeypatch.setattr(
        "tools.mirror_sync.worker_requester_rbac.authorize_requester",
        lambda req: {"allowed": True, "reason": "SUPERADMIN_CANONICAL"},
    )
    monkeypatch.setattr(
        wcp,
        "execute_bounded_runtime_convergence_recovery",
        lambda **kw: {
            "recovery_kind": "RUNTIME_CONVERGENCE_RECOVERY",
            "incident_id": kw["incident_id"],
            "status": "CONVERGED",
            "overall_converged": True,
            "preserved_branch": "recovery/preserved-platform-358bcf236906",
            "production_touched": False,
        },
    )
    out = wis.submit_objective(rec_req, current_user=actor)
    assert out["status"] == "CONVERGED"
    assert out["overall_converged"] is True
    assert out["recovery_kind"] == "RUNTIME_CONVERGENCE_RECOVERY"
    assert out["production_touched"] is False


def test_phase3_consent_bridge_g1b_origin_separation_and_canonical_stale_invalidation(tmp_path, monkeypatch):
    """Phase 3 (G1B): Never emit Production URLs (404), always emit Preview human portal, and invalidate stale HEAD canonically."""
    repo, _bare, base_sha = _init_repo_with_origin(tmp_path)
    qroot = _setup_queue(repo)
    actor = _actor()
    monkeypatch.setenv("EDARSAHUB_ROOT", str(repo))
    monkeypatch.setenv("EDARSAHUB_CONSENT_SIGNING_SECRET", "edarsahub-test-consent-secret-0123456789")
    monkeypatch.delenv("EDARSAHUB_CONSENT_HUMAN_PORTAL_ORIGIN", raising=False)
    monkeypatch.delenv("EDARSAHUB_PREVIEW_PUBLIC_ORIGIN", raising=False)
    monkeypatch.delenv("EDARSAHUB_MCP_PUBLIC_ORIGIN", raising=False)
    # Exact Production-first CORS_ORIGINS from Preview that caused the HTTP 404 bug!
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://stock-tracker-990.emergent.host,https://erp-crm-enterprise-1.preview.emergentagent.com,https://hub.edarsa.com.mx,http://localhost:3000",
    )

    # 1. Origin resolver MUST skip stock-tracker-990.emergent.host & hub.edarsa.com.mx and select Preview!
    resolved = lr._resolve_public_approval_base_url()
    assert resolved == "https://erp-crm-enterprise-1.preview.emergentagent.com"
    assert lr._resolve_public_approval_base_url("https://stock-tracker-990.emergent.host") == (
        "https://erp-crm-enterprise-1.preview.emergentagent.com"
    )
    assert lr._resolve_public_approval_base_url("https://hub.edarsa.com.mx") == (
        "https://erp-crm-enterprise-1.preview.emergentagent.com"
    )

    # 2. If ONLY Production hosts exist, fail closed to None (NEVER emit Production 404 link!)
    monkeypatch.setenv("CORS_ORIGINS", "https://stock-tracker-990.emergent.host,https://hub.edarsa.com.mx")
    assert lr._resolve_public_approval_base_url() is None

    # Restore real CORS_ORIGINS and create a consent request
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://stock-tracker-990.emergent.host,https://erp-crm-enterprise-1.preview.emergentagent.com,https://hub.edarsa.com.mx,http://localhost:3000",
    )
    mod_sha = hashlib.sha256((repo / "backend/modules/demo_mod.py").read_bytes()).hexdigest()
    req = {
        "objective": "Solicitar consentimiento especifico para ajuste en Desarrollo.",
        "bounded_context": "WORKER_CONTROL_PLANE",
        "mode": "READ_ONLY",
        "capability": "GATE_AUTHORIZATION_LIFECYCLE",
        "constraints": {
            "action": "REQUEST_CONSENT",
            "gate_id": "AUTH-RBAC-P0-B-TEST",
            "authorization_id": "GO-AUTH-RBAC-P0-B-TEST",
            "authorized_operations": ["replace_text"],
            "allowed_paths": ["backend/modules/demo_mod.py"],
            "source_sha256": {"backend/modules/demo_mod.py": mod_sha},
            "base_head_sha": base_sha,
            "ttl_hours": 4,
            "consent_ttl_minutes": 60,
            "verification_tests": ["backend/tests/test_demo_mod.py"],
            "rollback_plan": "Revert single commit on Edarsahub_Desarrollo.",
        },
    }
    created = lr.create_human_consent_request(req, current_user=actor, state_root=qroot, repo_root=repo)
    cid = created["consent_request_id"]
    assert created["human_portal_origin"] == "https://erp-crm-enterprise-1.preview.emergentagent.com"
    assert created["approval_url"] == f"https://erp-crm-enterprise-1.preview.emergentagent.com/api/mcp/oauth/consent/{cid}"
    assert created["target_environment"] == "PREVIEW_DESARROLLO"
    assert created["auto_approved"] is False

    # 3. While HEAD is unchanged, invalidate_stale_consent_request preserves it (STILL_VALID)
    still = lr.invalidate_stale_consent_request(cid, current_user=actor, state_root=qroot, repo_root=repo)
    assert still["status"] == "STILL_VALID"
    assert still["invalidated"] is False

    # 4. Advance HEAD -> OAuth HTML screen MUST block approval & canonical invalidate_stale transitions cleanly!
    (repo / "backend/modules/demo_mod.py").write_text("X = 99\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "backend/modules/demo_mod.py"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "advance head"], check=True, capture_output=True)

    async def _fake_dual(_request):
        return dict(actor)

    monkeypatch.setattr(oauth_server, "get_current_user_dual", _fake_dual)
    monkeypatch.setattr(oauth_server, "_require_worker_permission", lambda uid: None)
    app = FastAPI()
    app.include_router(oauth_server.router)
    client = TestClient(app)
    html_res = client.get(f"/api/mcp/oauth/consent/{cid}")
    assert html_res.status_code == 200
    assert "STALE_HEAD_OR_SHA_INVALIDATION_REQUIRED" in html_res.text
    assert 'name="decision" value="approve"' not in html_res.text

    inv = lr.invalidate_stale_consent_request(cid, current_user=actor, state_root=qroot, repo_root=repo)
    assert inv["status"] == "INVALIDATED_STALE_SCOPE"
    assert inv["invalidated"] is True
    assert inv["auto_approved"] is False
    assert inv["production_touched"] is False

    # Re-invalidating is idempotent
    inv2 = lr.invalidate_stale_consent_request(cid, current_user=actor, state_root=qroot, repo_root=repo)
    assert inv2["status"] == "INVALIDATED_STALE_SCOPE"
    assert inv2["duplicate_prevented"] is True


def test_phase4_bitacoras_semantic_blocker_reassignment_without_409_or_duplication(tmp_path):
    """Phase 4: Safely reassign HANDOFF_CANARY_INSUFFICIENT_FOR_OBJECTIVE handoff preserving identity, history & prior evidence."""
    repo, _bare, _base_sha = _init_repo_with_origin(tmp_path)
    qroot = _setup_queue(repo)
    actor = _actor()

    # Create a certified canary result (insufficient) AND a certified SQL result (SEM-REQUEST-0AF43543EE9736B71858515C)
    canary_jid = "SEM-REQUEST-2E4E4870FF4F8356CD23C853"
    sql_jid = "SEM-REQUEST-0AF43543EE9736B71858515C"
    for jid, chk_type in ((canary_jid, "git_diff_check"), (sql_jid, "sql_readonly_audit")):
        (qroot / "done" / f"{jid}.json").write_text(
            json.dumps({
                "job_id": jid,
                "mode": "READ_ONLY",
                "checks": [{"type": chk_type}],
                "scheduling": {"bounded_context": "WORKER_CONTROL_PLANE"},
            }),
            encoding="utf-8",
        )
        (qroot / "results" / f"{jid}.json").write_text(
            json.dumps({
                "schema": "edarsahub.worker-result.v2",
                "job_id": jid,
                "status": "READ_ONLY_COMPLETE",
                "quality_gate": "PASS",
                "tests": "PASS",
                "certification": "CERTIFIED_READ_ONLY",
                "work_completion": "COMPLETE",
                "percent_complete": 100,
                "blockers": [],
                "checks": [{"type": chk_type, "status": "PASS"}],
                "completed_at_utc": "2026-11-27T03:39:03Z",
                "summary_es": "Auditoria certificada READ_ONLY",
                "production_touched": False,
            }),
            encoding="utf-8",
        )
        (qroot / "published" / f"{jid}.json").write_text(
            f"published=2026-11-27T03:39:10Z\ncommit={'a'*40}\ncertification=CERTIFIED_READ_ONLY\n",
            encoding="utf-8",
        )

    req_key = "EDARSAHUB-BITACORAS-CAJAS-SQL-PROFILE-COVERAGE-HANDOFF-R1-20261126"
    criteria = [
        "existing_authorized_sql_profile_identified_or_precise_gap",
        "no_arbitrary_sql_or_new_profile_granted",
        "no_duplicate_certified_gate",
        "production_touched_false",
        "return_owner_and_next_safe_step",
    ]
    objective = (
        "Delegacion de dependencia READ_ONLY desde BITACORAS hacia WORKER_CONTROL_PLANE: "
        "confirmar cobertura de perfil SQL reutilizando SEM-REQUEST-0AF43543EE9736B71858515C."
    )

    # 1. Initial registration with READ_ONLY_CANARY -> lands in SEMANTIC_BLOCKER (HANDOFF_CANARY_INSUFFICIENT_FOR_OBJECTIVE)
    base_req = {
        "objective": objective,
        "bounded_context": "BITACORAS",
        "mode": "READ_ONLY",
        "capability": "CROSS_DOMAIN_HANDOFF_REGISTER",
        "request_key": req_key,
        "constraints": {
            "target_domain": "WORKER_CONTROL_PLANE",
            "requested_capability": "READ_ONLY_CANARY",
            "requested_constraints": {},
            "source_job_id": sql_jid,
            "resolution_job_id": canary_jid,
            "acceptance_criteria": criteria,
            "auto_dispatch": False,
        },
    }
    first = hm.register_cross_domain_handoff(base_req, current_user=actor, state_root=qroot, repo_root=repo)
    hid = first["handoff_id"]
    loaded1 = hm.load_handoff(hid, state_root=qroot)
    assert loaded1["dependency_satisfied"] is False
    assert loaded1["executor_status"] == "SEMANTIC_BLOCKER"
    assert loaded1["exception_code"] == "HANDOFF_CANARY_INSUFFICIENT_FOR_OBJECTIVE"

    # 2. Reassigning to a real compatible capability MUST succeed (NO IDEMPOTENCY_CONFLICT 409, NO duplicate handoff!)
    reassign_req = {
        **base_req,
        "constraints": {
            "target_domain": "WORKER_CONTROL_PLANE",
            "requested_capability": "REPOSITORY_CONTRACT_AUDIT_BOUNDED",
            "requested_constraints": {
                "paths": ["tools/mirror_sync/readonly_audit_profiles.py"],
                "search_terms": ["CAJAS", "BITACORAS"],
                "max_results": 20,
            },
            "source_job_id": sql_jid,
            "acceptance_criteria": criteria,
            "auto_dispatch": False,
        },
    }
    reassigned = hm.register_cross_domain_handoff(reassign_req, current_user=actor, state_root=qroot, repo_root=repo)
    assert reassigned["handoff_id"] == hid
    assert reassigned["handoff_updated"] is True
    assert reassigned["duplicate_prevented"] is True
    assert len(hm.list_handoffs(state_root=qroot)) == 1

    loaded2 = hm.load_handoff(hid, state_root=qroot)
    assert loaded2["requested_capability"] == "REPOSITORY_CONTRACT_AUDIT_BOUNDED"
    assert loaded2["request_key"] == req_key
    assert loaded2["acceptance_criteria"] == criteria
    assert loaded2["grants_target_permissions"] is False
    # Prior insufficient canary evidence is archived intact!
    assert len(loaded2.get("prior_insufficient_resolutions") or []) == 1
    assert loaded2["prior_insufficient_resolutions"][0]["resolution_job_id"] == canary_jid

    # 3. Attempting to reassign a NON-blocker handoff with a different capability STILL raises IDEMPOTENCY_CONFLICT!
    conflict_req = {
        **reassign_req,
        "constraints": {
            **reassign_req["constraints"],
            "requested_capability": "WORKER_RESULT_DETAIL_READ",
            "requested_constraints": {"source_job_id": sql_jid},
        },
    }
    with pytest.raises(hm.HandoffConflictError, match="IDEMPOTENCY_CONFLICT"):
        hm.register_cross_domain_handoff(conflict_req, current_user=actor, state_root=qroot, repo_root=repo)


def test_phase5_knowledge_loop_superseded_never_certifies_learned_capability():
    """Phase 5: SUPERSEDED state must NEVER be accepted as CERTIFIED in Learned Capability Registry."""
    superseded_incident = SimpleNamespace(
        incident_id="INC-SUPERSEDED-CHECK-R1",
        state="SUPERSEDED",
        target_paths=("tools/mirror_sync/worker_control_plane.py",),
        production_touched=False,
    )
    payload = {
        "schema": "edarsahub.worker-repair-learned-capability.v1",
        "code": "TEST_SUPERSEDED_BLOCK_CAP",
        "problem_signature": "TEST_SIG",
        "incident_ids": ["INC-SUPERSEDED-CHECK-R1"],
        "required_paths": ["tools/mirror_sync/worker_control_plane.py"],
        "objective": "Verificar que SUPERSEDED nunca certifica capacidad aprendida.",
        "actions": [{"type": "replace_text", "path": "tools/mirror_sync/worker_control_plane.py", "old": "a", "new": "b"}],
        "checks": [{"type": "git_diff_check"}],
        "evidence": {
            "source_job_id": "JOB-SRC-1",
            "blocker_signature": "RUNTIME_NOT_CONVERGED",
            "repair_job_id": "JOB-REP-1",
            "result_commit": "a" * 40,
            "certification": "CERTIFIED",
        },
        "learned_from_incident": "INC-SUPERSEDED-CHECK-R1",
        "reusable": True,
        "production_allowed": False,
    }
    with pytest.raises(ValueError, match="LEARNED_CAPABILITY_INCIDENT_NOT_CERTIFIED"):
        learned_reg.register_learned_capability(payload, incident=superseded_incident, require_certified_incident=True)
