"""Integral Certification Tests for Universal Autonomous Worker Master Plan A-I.

Covers every pillar end-to-end with strict fail-closed assertions and zero Production impact:
A. Global domain unblocking & per-domain failure isolation (orphan queue-publisher claims,
   round-robin recovery, settled orphan branch pruning).
B. Runtime self-healing & MCP Connector Internal Error incident family (504 timeout,
   502/503 unavailable, JSON-RPC -32603 internal error, protocol errors, secret-free telemetry,
   converged runtime incident reconciliation).
C. Extensible universal capabilities & hermetic pytest certification suites.
D. Reusable HRLectura READ_ONLY_SQL profiles (SQL_READONLY_PROFILE_AUDIT, fail-closed DML/DDL
   & arbitrary SQL rejection, domain scope enforcement).
E. Active Knowledge Loop (canonical + certified dynamic lessons, uncertified rejection).
F. Automatic objective continuity across chats (continuity dossier, non-blocking gate-chain isolation).
G. Time & cost optimization (directory-signature-invalidated queue snapshot cache in resolve_go_context).
H. Centro de Control & Worker Console self-healing telemetry integration (RBAC fail-closed).
I. Integral multichat certification invariants (production_touched=False, zero duplicate runs).
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
for p in (REPO_ROOT, BACKEND_ROOT, REPO_ROOT / "tools" / "mirror_sync"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from tools.mirror_sync import gate_chain_orchestrator as orchestrator
from tools.mirror_sync import worker_control_plane as control_plane
from tools.mirror_sync import worker_lifecycle_recovery as lifecycle
from tools.mirror_sync import worker_repair_auto_loop as auto_loop
from modules.worker_ingress import semantic_capabilities as sem_caps
from modules.worker_ingress import service as ingress_service
from modules.worker_mcp import client as mcp_server
from modules.worker_console import contract as console_contract


def _readonly_draft(job_id: str, *, domain: str) -> dict:
    return {
        "schema": "edarsahub.worker-job.v2",
        "job_id": job_id,
        "mode": "READ_ONLY",
        "target_repo": "rbalam/EDARSA_HUB",
        "target_branch": "Edarsahub_Desarrollo",
        "production_allowed": False,
        "human_summary_language": "es",
        "objective": f"Controlled READ_ONLY audit for {domain}",
        "actions": [],
        "checks": [{"type": "git_diff_check"}],
        "requester": {
            "email": "ricardo@edarsa.com.mx",
            "source": "edarsahub-worker-ingress",
            "project": "EDARSAHUB",
            "chat": "master-plan-ai-cert",
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
    for sub in (
        "drafts",
        "pending",
        "processing",
        "done",
        "rejected",
        "results",
        "published",
        "maintenance/incidents",
        "maintenance/circuit_breakers",
        "maintenance/knowledge_lessons",
        "runtime",
    ):
        (qroot / sub).mkdir(parents=True, exist_ok=True)
    claims_dir = tmp_path / ".git" / "agent-guard" / "state" / "claims"
    claims_dir.mkdir(parents=True, exist_ok=True)
    attest_dir = tmp_path / ".git" / "mirror-sync" / "reporting" / "test_attestations"
    attest_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path, qroot, claims_dir, attest_dir


def test_pillar_a_orphan_queue_publisher_claim_matching_and_domain_isolation(tmp_path):
    # 1. Control plane regex must recognize BOTH worker-* AND queue-publisher-* orphan claims
    assert control_plane.WORKER_TOKEN_RE.search(
        "queue-publisher-SEM-COMERCIAL_CONVENIOS_MARCAS-REPOSITORY_CONTRACT_AUDIT_BOUNDE-B21EBDD502F17EAE4F77.json"
    )
    assert control_plane.WORKER_TOKEN_RE.search("worker-SEM-REQUEST-123456.json")

    # 2. Per-domain isolation in lifecycle recovery: failure in Domain A must NOT block Domain B
    root, qroot, claims_dir, attest_dir = _setup_queue(tmp_path)
    now_ts = time.time()

    drafts = [
        ("SEM-ALPHA-AUDIT-001", "DOMAIN_ALPHA"),
        ("SEM-ALPHA-AUDIT-002", "DOMAIN_ALPHA"),
        ("SEM-BETA-AUDIT-001", "DOMAIN_BETA"),
    ]
    for jid, dom in drafts:
        p = qroot / "drafts" / f"{jid}.json"
        p.write_text(json.dumps(_readonly_draft(jid, domain=dom)), encoding="utf-8")
        os.utime(p, (now_ts - 1000, now_ts - 1000))

    det = lifecycle.scan_global_lifecycle_blockers(
        repo_root=root,
        state_root=qroot,
        claims_dir=claims_dir,
        attestations_dir=attest_dir,
        now_epoch=now_ts,
        force_full=True,
        remote_inbox_ids=set(),
        remote_result_ids=set(),
    )
    assert det["domain_isolation_active"] is True
    assert det["counts"]["persistent_drafts"] == 3

    attempted_jobs: list[str] = []

    def selective_submit(job_spec, *, require_convergence=False):
        jid = job_spec["job_id"]
        attempted_jobs.append(jid)
        if "ALPHA" in jid:
            return {"status": "RECOVERY_REQUIRED", "job_id": jid, "reason": "AGENT_GUARD_WORKTREE_CREATE_FAILED", "production_touched": False}
        return {"status": "SUBMITTED", "job_id": jid, "production_touched": False}

    rec = lifecycle.advance_lifecycle_recovery(
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
        submit_fn=selective_submit,
        now_epoch=now_ts,
        max_recoveries_per_cycle=3,
        remote_inbox_ids=set(),
        remote_result_ids=set(),
    )
    assert rec["domain_isolation_active"] is True
    assert "DOMAIN_ALPHA" in rec["isolated_failed_domains"]
    assert "DOMAIN_BETA" not in rec["isolated_failed_domains"]
    # ALPHA-001 fails -> ALPHA is isolated (ALPHA-002 skipped), BETA-001 succeeds!
    assert "SEM-BETA-AUDIT-001" in attempted_jobs
    assert "SEM-ALPHA-AUDIT-002" not in attempted_jobs
    assert rec["recoveries_succeeded"] == 1
    rejected_action = next(a for a in rec["actions"] if a["job_id"] == "SEM-ALPHA-AUDIT-001")
    assert rejected_action["publication_reason"] == "AGENT_GUARD_WORKTREE_CREATE_FAILED"
    assert rec["production_touched"] is False


def test_pillar_b_mcp_connector_incident_family_and_converged_runtime_reconciliation(tmp_path):
    root, qroot, claims_dir, attest_dir = _setup_queue(tmp_path)
    now_ts = time.time()

    # 1. Taxonomy classifies all 4 MCP connector internal error classes + orphan publisher deadlock
    mcp_cases = [
        ("JSONRPC_INTERNAL_ERROR", "MCP_CONNECTOR_INTERNAL_ERROR", "INTEGRATION", True),
        ("UPSTREAM_TIMEOUT", "MCP_CONNECTOR_UPSTREAM_TIMEOUT", "INTEGRATION", True),
        ("BACKEND_UNREACHABLE", "MCP_CONNECTOR_UPSTREAM_UNAVAILABLE", "INTEGRATION", True),
        ("SESSION_ID_MISSING", "MCP_CONNECTOR_PROTOCOL_ERROR", "CONTRACT", False),
        ("AGENT_GUARD_WORKTREE_CREATE_FAILED", "ORPHAN_PUBLISHER_CLAIM_DEADLOCK", "INFRASTRUCTURE", True),
    ]
    for code, expected_cls, expected_cat, expected_auto in mcp_cases:
        tax = auto_loop.classify_failure_taxonomy(
            error_code=code,
            causal_evidence={"tool": "get_go_context"},
        )
        assert tax["failure_class"] == expected_cls, f"{code} -> {tax}"
        assert tax["category"] == expected_cat
        assert tax["auto_repair_allowed"] is expected_auto
        assert tax["production_touched"] is False

    # 2. Record secret-free MCP connector incidents & verify normal 401/403/422 are NOT recorded
    log_path = qroot / "maintenance" / lifecycle.MCP_INCIDENTS_FILENAME
    assert mcp_server.record_mcp_connector_incident(
        tool_name="submit_objective",
        http_status=403,
        error_code="INSUFFICIENT_SCOPE",
        log_path=log_path,
    ) is None
    assert mcp_server.record_mcp_connector_incident(
        tool_name="submit_objective",
        http_status=422,
        error_code="SEMANTIC_CONSTRAINTS_UNSUPPORTED",
        log_path=log_path,
    ) is None

    rec1 = mcp_server.record_mcp_connector_incident(
        tool_name="get_go_context",
        http_status=504,
        error_code="UPSTREAM_TIMEOUT",
        correlation_id="RH",
        log_path=log_path,
    )
    rec2 = mcp_server.record_mcp_connector_incident(
        tool_name="gateway:tools/call",
        http_status=500,
        error_code="JSONRPC_INTERNAL_ERROR",
        log_path=log_path,
    )
    assert rec1 is not None and rec1["incident_family"] == "MCP_CONNECTOR_UPSTREAM_TIMEOUT"
    assert rec2 is not None and rec2["incident_family"] == "MCP_CONNECTOR_INTERNAL_ERROR"

    # Scanner ingests MCP connector incidents without globally halting other domains
    det = lifecycle.scan_global_lifecycle_blockers(
        repo_root=root,
        state_root=qroot,
        claims_dir=claims_dir,
        attestations_dir=attest_dir,
        now_epoch=now_ts,
        force_full=True,
        remote_inbox_ids=set(),
        remote_result_ids=set(),
    )
    assert det["counts"]["mcp_connector_recent_incidents"] == 2
    assert det["counts"]["mcp_failures"] >= 2
    assert det["mcp_connector_incidents"]["non_blocking_isolation"] is True
    assert det["system_degraded"] is False  # Isolated MCP errors must NOT halt entire project

    # 3. Stale RUNTIME_NOT_CONVERGED incident supersedes cleanly once convergence is verified True
    inc_path = qroot / "maintenance" / "incidents" / "INC-DRIFT-001.json"
    inc_path.write_text(
        json.dumps({
            "incident_id": "INC-DRIFT-001",
            "source_status": "RUNTIME_NOT_CONVERGED",
            "problem_signature": "WORKER_CODE_TREE_DRIFT_PREVIEW_RUNTIME",
            "state": "REPAIR_REQUIRED",
            "production_touched": False,
        }),
        encoding="utf-8",
    )
    rec_conv = lifecycle.reconcile_converged_runtime_incidents(
        state_root=qroot,
        convergence_report={"overall_converged": True, "local_head": "a" * 40},
    )
    assert rec_conv["superseded"] == ["INC-DRIFT-001"]
    updated = json.loads(inc_path.read_text(encoding="utf-8"))
    assert updated["state"] == "SUPERSEDED"
    assert updated["production_touched"] is False


def test_pillars_c_and_d_extensible_capabilities_and_reusable_sql_readonly_profiles():
    # Pillar C: New audited hermetic pytest suites registered
    suites = sem_caps.pytest_certification_suites()
    for domain in ("WORKER_SELF_HEALING", "WORKER_CONSOLE", "WORKER_INGRESS", "CENTRO_CONTROL_SECURITY"):
        assert domain in suites
        assert suites[domain].isolation == "HERMETIC_READONLY"
        assert suites[domain].requires_sql is False
        assert suites[domain].requires_network is False

    # Pillar D: Reusable HRLectura READ_ONLY_SQL profiles registered & fail-closed
    profiles = sem_caps.sql_readonly_profiles()
    expected_profiles = {
        "SEC_RBAC_PERMISSION_MATRIX",
        "UNIDADES_NEGOCIO_CANONICAL_CATALOG",
        "WORKER_OPERATIONS_STATE_SUMMARY",
        "CENTRO_CONTROL_ALERTS_SUMMARY",
        "AUTH_ACTIVE_SESSIONS_SUMMARY",
    }
    assert expected_profiles.issubset(set(profiles))
    for prof in profiles.values():
        assert prof.source == "EDARSAHUB"
        assert prof.login_policy == "HRLectura"
        assert prof.read_only is True

    # Valid profile expansion succeeds
    cap = sem_caps.resolve_capability("SQL_READONLY_PROFILE_AUDIT")
    expanded = cap.builder({
        "bounded_context": "COMERCIAL_POS",
        "mode": "READ_ONLY_SQL",
        "capability": "SQL_READONLY_PROFILE_AUDIT",
        "constraints": {"profile_code": "UNIDADES_NEGOCIO_CANONICAL_CATALOG"},
    })
    assert expanded["actions"] == []
    assert expanded["checks"][0]["type"] == "sql_readonly_audit"
    assert expanded["checks"][0]["source"] == "EDARSAHUB"
    assert expanded["checks"][0]["profile_code"] == "UNIDADES_NEGOCIO_CANONICAL_CATALOG"

    # Domain restriction enforced fail-closed
    with pytest.raises(sem_caps.SemanticCapabilityError, match="SEMANTIC_SQL_PROFILE_DOMAIN_FORBIDDEN"):
        cap.builder({
            "bounded_context": "MARKETING",
            "mode": "READ_ONLY_SQL",
            "capability": "SQL_READONLY_PROFILE_AUDIT",
            "constraints": {"profile_code": "SEC_RBAC_PERMISSION_MATRIX"},
        })

    # Arbitrary SQL constraint rejected fail-closed
    with pytest.raises(sem_caps.SemanticCapabilityError, match="SEMANTIC_CONSTRAINTS_UNSUPPORTED"):
        cap.builder({
            "bounded_context": "SEC_RBAC",
            "mode": "READ_ONLY_SQL",
            "capability": "SQL_READONLY_PROFILE_AUDIT",
            "constraints": {"profile_code": "SEC_RBAC_PERMISSION_MATRIX", "sql": "SELECT 1"},
        })

    # Validator rejects DML/DDL/multi-statement/unnamed SELECT 1 at registration time
    for unsafe_sql in (
        "DELETE FROM dbo.Unidades_Negocio",
        "SELECT 1; DROP TABLE dbo.Sesiones",
        "SELECT 1 FROM dbo.Unidades_Negocio",
        "EXEC dbo.sp_help",
    ):
        with pytest.raises(sem_caps.SemanticCapabilityError):
            sem_caps._validate_readonly_sql_query({"name": "bad_q", "sql": unsafe_sql})

    # Dynamic catalog exposes SQL_READONLY_PROFILE_AUDIT and registered profiles
    catalog = {item["code"]: item for item in sem_caps.capability_catalog()}
    assert "SQL_READONLY_PROFILE_AUDIT" in catalog
    assert "UNIDADES_NEGOCIO_CANONICAL_CATALOG" in catalog["SQL_READONLY_PROFILE_AUDIT"]["ownership"]["registered_sql_readonly_profiles"]


def test_pillar_e_active_knowledge_loop_dynamic_lessons_fail_closed(tmp_path):
    lessons_dir = tmp_path / "knowledge_lessons"

    # Built-in new root-cause lessons are immediately discoverable
    assert auto_loop.lookup_canonical_lesson(
        failure_class="ORPHAN_PUBLISHER_CLAIM_DEADLOCK",
        lessons_dir=lessons_dir,
    )["lesson_id"] == "LESSON-ORPHAN-QUEUE-PUBLISHER-CLAIM-DEADLOCK"
    assert auto_loop.lookup_canonical_lesson(
        problem_signature="GO_CONTEXT_UNINDEXED_FULL_SCAN_TIMEOUT_504",
        lessons_dir=lessons_dir,
    )["lesson_id"] == "LESSON-GO-CONTEXT-UNINDEXED-FULL-SCAN-504"

    # Uncertified or production-touched lessons MUST fail closed
    with pytest.raises(ValueError, match="KNOWLEDGE_LESSON_NOT_CERTIFIED"):
        auto_loop.record_dynamic_knowledge_lesson(
            lesson_id="LESSON-UNSAFE-01",
            failure_class="TEST_FAILURE",
            problem_signature="SIG_1",
            root_cause="rc",
            source_job_id="JOB-1",
            certified_repair_job_id="JOB-2",
            reusable_guardrail="guard",
            prevention_rule="rule",
            certification="PENDING_CERTIFICATION",
            lessons_dir=lessons_dir,
        )
    with pytest.raises(ValueError, match="KNOWLEDGE_LESSON_PRODUCTION_FORBIDDEN"):
        auto_loop.record_dynamic_knowledge_lesson(
            lesson_id="LESSON-UNSAFE-02",
            failure_class="TEST_FAILURE",
            problem_signature="SIG_2",
            root_cause="rc",
            source_job_id="JOB-1",
            certified_repair_job_id="JOB-2",
            reusable_guardrail="guard",
            prevention_rule="rule",
            production_touched=True,
            lessons_dir=lessons_dir,
        )

    # Certified dynamic lesson persists and is discoverable via lookup_canonical_lesson
    saved = auto_loop.record_dynamic_knowledge_lesson(
        lesson_id="LESSON-DYNAMIC-CERTIFIED-01",
        failure_class="MCP_CONNECTOR_PROTOCOL_ERROR",
        problem_signature="DYNAMIC_SIG_CERT_01",
        root_cause="Handshake header mismatch",
        source_job_id="JOB-SRC-01",
        certified_repair_job_id="JOB-REP-01",
        reusable_guardrail="gateway_router._build_upstream_headers",
        prevention_rule="Validate handshake protocol version before forwarding",
        certified_commit_sha="b" * 40,
        lessons_dir=lessons_dir,
    )
    assert saved["production_touched"] is False
    found = auto_loop.lookup_canonical_lesson(
        problem_signature="DYNAMIC_SIG_CERT_01",
        lessons_dir=lessons_dir,
    )
    assert found is not None and found["lesson_id"] == "LESSON-DYNAMIC-CERTIFIED-01"


def test_pillars_f_and_g_go_context_cache_invalidation_and_chain_isolation(tmp_path, monkeypatch):
    root, qroot, _, _ = _setup_queue(tmp_path)
    monkeypatch.setattr(ingress_service, "STATE_ROOT", qroot)
    ingress_service._GO_CONTEXT_CACHE.clear()

    user = {"email": "ricardo@edarsa.com.mx", "role": "SUPERADMIN"}
    # Cold call populates cache
    ctx1 = ingress_service.resolve_go_context(domain="FINANZAS", current_user=user, objective_hint="Audit")
    assert ctx1["continuity"]["cache_hit"] is False
    assert ctx1["continuity"]["isolated_from_other_domains"] is True
    assert ctx1["production_touched"] is False

    # Warm call hits cache immediately
    ctx2 = ingress_service.resolve_go_context(domain="FINANZAS", current_user=user, objective_hint="Audit")
    assert ctx2["continuity"]["cache_hit"] is True

    # Adding a new draft MUST invalidate cache immediately (zero stale reads!)
    draft_path = qroot / "drafts" / "SEM-FINANZAS-NEW-001.json"
    draft_path.write_text(json.dumps(_readonly_draft("SEM-FINANZAS-NEW-001", domain="FINANZAS")), encoding="utf-8")
    ctx3 = ingress_service.resolve_go_context(domain="FINANZAS", current_user=user, objective_hint="Audit")
    assert ctx3["continuity"]["cache_hit"] is False
    assert ctx3["next_allowed_action"] == "RECOVER_PENDING_DRAFT"
    assert ctx3["continuity"]["resume_from_job_id"] == "SEM-FINANZAS-NEW-001"

    # Unrelated domain RH is completely unaffected by FINANZAS draft!
    ctx_rh = ingress_service.resolve_go_context(domain="RH", current_user=user, objective_hint="Audit RH")
    assert ctx_rh["next_allowed_action"] == "CONTINUE_AUTONOMOUS"
    assert ctx_rh["pending_drafts"] == []

    # Pillar F: Gate-chain orchestrator isolates broken chain JSON without stopping valid chains
    cfg_dir = tmp_path / "gate_chains"
    persist_dir = tmp_path / "orchestrator"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "01_broken.json").write_text("{BROKEN_JSON", encoding="utf-8")
    (cfg_dir / "02_valid_disabled.json").write_text(
        json.dumps({"chain_id": "VALID-02", "enabled": False, "gates": []}),
        encoding="utf-8",
    )
    cycle_out = orchestrator.run_cycle(cfg_dir, qroot, persist_dir, publish_enabled=False)
    assert cycle_out["chain_isolation_active"] is True
    assert cycle_out["isolated_error_chains"] == ["01_broken"]
    assert cycle_out["chains"][0]["action"] == "CHAIN_ISOLATED_ERROR"
    assert cycle_out["production_touched"] is False


def test_pillar_h_centro_control_and_worker_console_self_healing_snapshot(tmp_path):
    _, qroot, _, _ = _setup_queue(tmp_path)
    (qroot / "runtime" / "control_plane_status.json").write_text(
        json.dumps({
            "at_utc": "2026-11-25T09:10:00Z",
            "runtime": {"pid_alive": True, "runtime_repair_needed": False, "expected_generation": "v4", "actual_generation": "v4"},
            "ff": {"ff": "ALREADY_ALIGNED", "local": "c" * 40},
            "lifecycle_detection": {
                "system_degraded": False,
                "counts": {"persistent_drafts": 2, "corrupt_drafts": 0, "orphan_claims": 0, "orphan_branches": 0},
                "persistent_drafts_by_domain": {"RH": 2},
            },
            "lifecycle_recovery": {"status": "ACTIVE", "isolated_failed_domains": []},
        }),
        encoding="utf-8",
    )
    mcp_server.record_mcp_connector_incident(
        tool_name="get_go_context",
        http_status=504,
        error_code="UPSTREAM_TIMEOUT",
        log_path=qroot / "maintenance" / lifecycle.MCP_INCIDENTS_FILENAME,
    )

    snap = console_contract.get_worker_self_healing_snapshot(queue_root=qroot)
    assert snap["schema"] == "edarsahub.worker-self-healing-snapshot.v1"
    assert snap["overall_status"] == "HEALTHY"
    assert snap["domain_isolation_active"] is True
    assert snap["mcp_connector"]["total_recent_incidents"] == 1
    assert snap["mcp_connector"]["by_family"]["MCP_CONNECTOR_UPSTREAM_TIMEOUT"] == 1
    assert snap["knowledge_loop"]["certified_lessons_count"] >= 10
    assert snap["extensible_capabilities"]["sql_readonly_profiles_count"] >= 5
    assert snap["production_touched"] is False
