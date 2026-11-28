"""Certification Tests for EDARSAHUB BOS Multichat Autonomous Handoff P1 (Corrections 1-10).

Certifies positive and negative contracts for all 10 P1 transversal gaps without repeating P0:
1. Assign compatible capability to an existing pending handoff.
2. Authorized activation of auto_dispatch without duplicating the handoff.
3. Preserve identity, history, request_key, and dependency_id.
4. Identify requests without executor; never leave them indefinitely in WAIT.
5. Resolve compatible capabilities via Capability Registry.
6. Register concrete exception when no compatible capability exists.
7. Eliminate artificial role=SUPERADMIN / permissions=["*"] fallback in _build_dispatch_job_for_handoff();
   reuse canonical service identity, effective permissions & RBAC; fail closed without verifiable identity.
8. Revalidate authorizations on dispatch (fail closed if expired/revoked/deleted/tampered).
9. Link certified resolution with original handoff (fail closed on uncertified or wrong domain).
10. End-to-end continuity without manual prompt exchange on Acceptance Case:
    External Availability Monitor Gate0 (HO-WORKERCONTROLP-CONTINUIDADOPE-B2CB1DD561414218).
"""
from __future__ import annotations

import inspect
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
for p in (REPO_ROOT, BACKEND_ROOT, REPO_ROOT / "tools" / "mirror_sync"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from modules.worker_console import contract as console_contract
from modules.worker_ingress import semantic_capabilities as sem_caps
from modules.worker_ingress import service as wis
from tools.mirror_sync import gate_chain_orchestrator as orchestrator
from tools.mirror_sync import worker_cross_domain_handoff as handoff_mod
from tools.mirror_sync import worker_lifecycle_recovery as lr


GATE0_HANDOFF_ID = "HO-WORKERCONTROLP-CONTINUIDADOPE-B2CB1DD561414218"
GATE0_DEPENDENCY_ID = "DEP-HO-WORKERCONTROLP-CONTINUIDADOPE-B2CB1DD561414218"
GATE0_REQUEST_KEY = "EXTERNAL-AVAILABILITY-MONITOR-GATE0-READONLY-20261125"
GATE0_OBJECTIVE = (
    "Diagnosticar infraestructura externa independiente reutilizable para disponibilidad "
    "de Emergent, integracion con continuidad operativa y senales al Worker; sin despliegue, "
    "cambios de configuracion ni escrituras SQL."
)
GATE0_ACCEPTANCE_CRITERIA = [
    "Identificar infraestructura externa existente y ownership",
    "Verificar mecanismos autorizados de deteccion y reactivacion",
    "Definir contrato de señales al Worker sin duplicar infraestructura",
    "production_touched_false",
]
GATE0_AUDIT_CONSTRAINTS = {
    "paths": [
        "tools/mirror_sync/worker_control_plane.py",
        "tools/mirror_sync/worker_lifecycle_recovery.py",
        "tools/mirror_sync/worker_cross_domain_handoff.py",
        "backend/core/centro_control/routes.py",
        "backend/modules/worker_console/contract.py",
    ],
    "search_terms": [
        "heartbeat",
        "watchdog",
        "worker-salud",
        "converge_runtime",
        "reconcile_cross_domain_handoffs",
    ],
    "max_results": 40,
}


def _canonical_service_actor(email: str = "ricardo@edarsa.com.mx") -> dict:
    """Canonical SQL-resolved actor with explicit effective permissions (NO wildcard ['*']!)."""
    return {
        "id": "8",
        "usuario_id": 8,
        "email": email,
        "role": "SuperAdministrador",
        "role_code": "SUPERADMIN",
        "active": True,
        "permissions": ["RBAC_ADMIN", "CENTRO_CONTROL_VER", "worker:status", "worker:submit"],
        "scopes": ["worker:status", "worker:submit"],
        "auth_source": "SQL_CANONICAL_RBAC",
        "identity_verified": True,
    }


def _readonly_operator() -> dict:
    return {
        "id": "42",
        "email": "operador@edarsa.com.mx",
        "role": "OPERADOR",
        "active": True,
        "permissions": ["worker:status"],
        "scopes": ["worker:status"],
        "allowed_domains": ["WORKER_CONTROL_PLANE"],
    }


def _setup_queue(tmp_path: Path) -> Path:
    qroot = tmp_path / ".git" / "universal-worker-queue"
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
        "maintenance/handoffs",
    ):
        (qroot / sub).mkdir(parents=True, exist_ok=True)
    return qroot


def _seed_legacy_gate0_handoff(qroot: Path, *, created_at_utc: str = "2026-11-26T03:00:23Z") -> dict:
    """Seed exact legacy P0 state of HO-WORKERCONTROLP-CONTINUIDADOPE-B2CB1DD561414218."""
    doc = {
        "acceptance_criteria": list(GATE0_ACCEPTANCE_CRITERIA),
        "authorization_ref": None,
        "authorization_verification": {
            "authorization_id": None,
            "source_domain_covered": False,
            "status": "NO_AUTHORIZATION_REF_SUPPLIED",
            "supplied": False,
            "target_authorization_id": None,
            "target_domain_independently_authorized": False,
            "verified": False,
        },
        "auto_dispatch": False,
        "certification": "NOT_CERTIFIED",
        "classification": "TARGET_BOUNDED_CONTEXT_REQUIRED",
        "classification_reason": "BOUNDED_CONTEXT_OWNER_REQUIRED:CONTINUIDAD_OPERATIVA",
        "created_at_utc": created_at_utc,
        "delegation_chain": ["WORKER_CONTROL_PLANE", "CONTINUIDAD_OPERATIVA"],
        "delegation_depth": 1,
        "dependency_id": GATE0_DEPENDENCY_ID,
        "dependency_satisfied": False,
        "dispatch_attempts": 0,
        "evidence_link": None,
        "grants_target_permissions": False,
        "handoff_id": GATE0_HANDOFF_ID,
        "handoff_mode": "READ_ONLY",
        "human_intervention_reason": None,
        "incident_id": None,
        "lifecycle_state": "QUEUED_IN_TARGET_DOMAIN",
        "next_allowed_action": "WAIT_FOR_IN_FLIGHT_JOB",
        "owner_domain": "CONTINUIDAD_OPERATIVA",
        "payload_fingerprint": "a16ba78bef5fdd1fa15d2d9c3da2af200eb93d5d146d6b99d36792bfb59d254d",
        "priority_class": "NORMAL",
        "production_allowed": False,
        "production_touched": False,
        "request_key": GATE0_REQUEST_KEY,
        "requested_capability": None,
        "requested_constraints": {},
        "requester_email": "ricardo@edarsa.com.mx",
        "requires_human_intervention": False,
        "resolution_job_id": None,
        "resumed_job_id": None,
        "risk_level": "LOW",
        "schema": handoff_mod.SCHEMA_HANDOFF,
        "source_domain": "WORKER_CONTROL_PLANE",
        "source_job_id": None,
        "source_objective": GATE0_OBJECTIVE,
        "source_resumed": False,
        "target_domain": "CONTINUIDAD_OPERATIVA",
        "updated_at_utc": created_at_utc,
    }
    handoff_mod.save_handoff(doc, state_root=qroot)
    return doc


def _write_certified_result(
    qroot: Path,
    job_id: str,
    *,
    domain: str,
    certification: str = "CERTIFIED_READ_ONLY",
    status: str = "READ_ONLY_COMPLETE",
    tests: str = "PASS",
    quality_gate: str = "PASS",
    production_touched: bool = False,
    checks: list[dict] | None = None,
) -> None:
    (qroot / "done" / f"{job_id}.json").write_text(
        json.dumps({
            "job_id": job_id,
            "mode": "READ_ONLY",
            "objective": f"Certified work for {domain}",
            "checks": checks or [{"type": "git_diff_check"}],
            "scheduling": {"bounded_context": domain},
        }),
        encoding="utf-8",
    )
    (qroot / "results" / f"{job_id}.json").write_text(
        json.dumps({
            "schema": "edarsahub.worker-result.v2",
            "job_id": job_id,
            "status": status,
            "quality_gate": quality_gate,
            "tests": tests,
            "certification": certification,
            "work_completion": "COMPLETE",
            "percent_complete": 100,
            "blockers": [],
            "checks": checks or [{"type": "git_diff_check", "status": "PASS"}],
            "completed_at_utc": "2026-11-26T03:20:00Z",
            "certified_source_sha": "b" * 40,
            "summary_es": f"Resolucion certificada para {domain}",
            "production_touched": production_touched,
        }),
        encoding="utf-8",
    )


def test_p1_req1_2_3_assign_capability_and_activate_auto_dispatch_preserving_identity_and_history(tmp_path, monkeypatch):
    """Corrections 1, 2, 3: enrich existing pending handoff via MCP ingress without duplication or identity loss."""
    qroot = _setup_queue(tmp_path)
    monkeypatch.setattr(wis, "STATE_ROOT", qroot)
    wis._GO_CONTEXT_CACHE.clear()
    _seed_legacy_gate0_handoff(qroot)

    published: list[dict] = []
    monkeypatch.setattr(
        wis.gate_chain_publisher,
        "submit",
        lambda job, **kw: (
            published.append(job),
            {"status": "SUBMITTED", "job_id": job["job_id"], "production_touched": False},
        )[1],
    )

    enrich_req = {
        "objective": GATE0_OBJECTIVE,
        "bounded_context": "WORKER_CONTROL_PLANE",
        "mode": "READ_ONLY",
        "capability": "CROSS_DOMAIN_HANDOFF_REGISTER",
        "request_key": GATE0_REQUEST_KEY,
        "constraints": {
            "target_domain": "CONTINUIDAD_OPERATIVA",
            "dependency_id": GATE0_DEPENDENCY_ID,
            "acceptance_criteria": list(GATE0_ACCEPTANCE_CRITERIA),
            "requested_capability": "REPOSITORY_CONTRACT_AUDIT_BOUNDED",
            "requested_constraints": dict(GATE0_AUDIT_CONSTRAINTS),
            "auto_dispatch": True,
        },
    }

    # Preflight recognizes pending update without duplicating or mutating disk
    pf = wis.preflight_semantic_objective(enrich_req, current_user=_canonical_service_actor())
    assert pf["ok"] is True
    assert pf["status"] == "PREFLIGHT_READY"
    assert pf["handoff_update"] is True
    assert pf["handoff_id"] == GATE0_HANDOFF_ID
    assert pf["dependency_id"] == GATE0_DEPENDENCY_ID
    assert pf["classification"] == "REUSABLE_CAPABILITY_AVAILABLE"
    assert pf["has_executor"] is True
    assert published == []

    # Submit enriches existing handoff & dispatches ONCE without creating a duplicate handoff!
    res = wis.submit_objective(enrich_req, current_user=_canonical_service_actor())
    assert res["handoff_id"] == GATE0_HANDOFF_ID
    assert res["dependency_id"] == GATE0_DEPENDENCY_ID
    assert res["handoff_updated"] is True
    assert res["duplicate_prevented"] is True
    assert res["lifecycle_state"] == "IN_PROGRESS"
    assert res["production_touched"] is False
    assert len(published) == 1
    assert len(handoff_mod.list_handoffs(state_root=qroot)) == 1  # Zero duplicates!

    saved = handoff_mod.load_handoff(GATE0_HANDOFF_ID, state_root=qroot)
    assert saved is not None
    assert saved["handoff_id"] == GATE0_HANDOFF_ID
    assert saved["request_key"] == GATE0_REQUEST_KEY
    assert saved["dependency_id"] == GATE0_DEPENDENCY_ID
    assert saved["created_at_utc"] == "2026-11-26T03:00:23Z"
    assert saved["initial_payload_fingerprint"] == "a16ba78bef5fdd1fa15d2d9c3da2af200eb93d5d146d6b99d36792bfb59d254d"
    assert saved["requested_capability"] == "REPOSITORY_CONTRACT_AUDIT_BOUNDED"
    assert saved["auto_dispatch"] is True
    assert saved["auto_dispatch_authorized_by"] == "ricardo@edarsa.com.mx"
    assert saved["resolution_job_id"] == published[0]["job_id"]
    events = [entry["event"] for entry in saved["history"]]
    assert "REGISTERED_INITIAL" in events
    assert "PENDING_HANDOFF_UPDATED" in events
    assert "DISPATCHED" in events

    # Negative: core objective drift still raises IDEMPOTENCY_CONFLICT!
    drifted = dict(enrich_req)
    drifted["objective"] = "Objetivo alterado ilegalmente sobre misma clave."
    with pytest.raises(handoff_mod.HandoffConflictError, match="IDEMPOTENCY_CONFLICT"):
        handoff_mod.register_cross_domain_handoff(
            drifted,
            current_user=_canonical_service_actor(),
            state_root=qroot,
        )

    # Negative: updating an already IN_PROGRESS handoff fails closed
    with pytest.raises(handoff_mod.HandoffConflictError, match="HANDOFF_UPDATE_NOT_ALLOWED_IN_STATE"):
        handoff_mod.update_pending_handoff(
            GATE0_HANDOFF_ID,
            requested_capability="READ_ONLY_CANARY",
            requested_constraints={},
            allow_reassign_capability=True,
            current_user=_canonical_service_actor(),
            state_root=qroot,
        )


def test_p1_req4_no_executor_detection_never_indefinite_wait_in_reconcile_and_orchestrator(tmp_path):
    """Correction 4: requests without executor are explicitly flagged and NEVER left indefinitely in WAIT."""
    qroot = _setup_queue(tmp_path)
    _seed_legacy_gate0_handoff(qroot, created_at_utc="2026-11-26T03:00:23Z")

    # 1. Fresh reconcile (within stall window) immediately clears stale WAIT_FOR_IN_FLIGHT_JOB
    t_fresh = datetime(2026, 11, 26, 3, 5, 0, tzinfo=timezone.utc)
    rec_fresh = handoff_mod.reconcile_cross_domain_handoffs(
        state_root=qroot,
        no_executor_stall_seconds=900,
        now_utc=t_fresh,
    )
    assert GATE0_HANDOFF_ID in rec_fresh["without_executor_this_cycle"]
    assert rec_fresh["without_executor_count"] == 1
    assert rec_fresh["stalled_no_executor_this_cycle"] == []

    after_fresh = handoff_mod.load_handoff(GATE0_HANDOFF_ID, state_root=qroot)
    assert after_fresh["has_executor"] is False
    assert after_fresh["executor_status"] == "UNASSIGNED_NO_EXECUTOR"
    assert after_fresh["next_allowed_action"] == "ASSIGN_COMPATIBLE_CAPABILITY"
    assert after_fresh["next_allowed_action"] != "WAIT_FOR_IN_FLIGHT_JOB"
    assert any(c["code"] == "REPOSITORY_CONTRACT_AUDIT_BOUNDED" for c in after_fresh["compatible_capabilities"])

    # 2. Gate Chain Orchestrator returns STOP (HANDOFF_DEPENDENCY_NO_EXECUTOR) instead of indefinite WAIT!
    chain = {
        "schema": "edarsahub.gate-chain.v1",
        "chain_id": "CHAIN-AVAILABILITY-GATE0",
        "domain": "WORKER_CONTROL_PLANE",
        "enabled": True,
        "max_hops": 5,
        "start_gate_id": "G0",
        "gates": [
            {
                "gate_id": "G0",
                "job_id": "JOB-G0-GATE",
                "mutation_class": "READ_ONLY",
                "next_gate_ids": [],
                "required_handoff_ids": [GATE0_HANDOFF_ID],
                "job_template": {
                    "schema": "edarsahub.worker-job.v2",
                    "job_id": "JOB-G0-GATE",
                    "objective": "Continuar tras Gate0",
                    "mode": "READ_ONLY",
                    "actions": [],
                    "checks": [{"type": "git_diff_check"}],
                    "requester": {"email": "ricardo@edarsa.com.mx", "source": "edarsahub-worker-ingress"},
                    "production_allowed": False,
                },
            }
        ],
    }
    orch_out = orchestrator.cycle_chain(chain, qroot, tmp_path / "orch", publish_enabled=False)
    assert orch_out["action"] == "STOP"
    assert orch_out["reason"] == "HANDOFF_DEPENDENCY_NO_EXECUTOR"
    assert orch_out["handoff_dependencies"]["has_unexecutable_dependencies"] is True

    # 3. After stall timeout, reconcile transitions handoff to concrete HANDOFF_NO_EXECUTOR_STALLED exception
    t_stalled = datetime(2026, 11, 26, 3, 25, 0, tzinfo=timezone.utc)
    rec_stalled = handoff_mod.reconcile_cross_domain_handoffs(
        state_root=qroot,
        no_executor_stall_seconds=900,
        now_utc=t_stalled,
    )
    assert GATE0_HANDOFF_ID in rec_stalled["stalled_no_executor_this_cycle"]
    after_stall = handoff_mod.load_handoff(GATE0_HANDOFF_ID, state_root=qroot)
    assert after_stall["lifecycle_state"] == "ESCALATED_HUMAN_REQUIRED"
    assert after_stall["requires_human_intervention"] is True
    assert after_stall["exception_code"] == "HANDOFF_NO_EXECUTOR_STALLED"
    assert after_stall["next_allowed_action"] == "ASSIGN_COMPATIBLE_CAPABILITY"

    # Control Center surfaces without_executor and concrete exception
    overview = console_contract.get_cross_domain_handoffs_overview(queue_root=qroot)
    assert overview["counts"]["without_executor"] == 1
    assert overview["counts"]["exceptions"] == 1
    assert overview["exceptions"][0]["exception_code"] == "HANDOFF_NO_EXECUTOR_STALLED"


def test_p1_req5_and_6_capability_registry_resolution_and_concrete_exceptions(tmp_path, monkeypatch):
    """Corrections 5 & 6: resolve compatible capabilities via Capability Registry; concrete exceptions when incompatible."""
    qroot = _setup_queue(tmp_path)

    # Positive: Capability Registry discovery prioritizes domain-specific capabilities
    res_console = handoff_mod.resolve_compatible_capabilities(
        target_domain="WORKER_CONSOLE",
        handoff_mode="READ_ONLY",
    )
    assert res_console["has_compatible_capabilities"] is True
    codes_console = [c["code"] for c in res_console["compatible_capabilities"]]
    assert "WORKER_PYTEST_CERTIFICATION_READONLY" in codes_console
    assert codes_console[0] == "WORKER_PYTEST_CERTIFICATION_READONLY"  # domain-specific prioritized first

    # Positive: Explicit compatible capability + valid constraints
    res_audit = handoff_mod.resolve_compatible_capabilities(
        target_domain="CONTINUIDAD_OPERATIVA",
        handoff_mode="READ_ONLY",
        requested_capability="REPOSITORY_CONTRACT_AUDIT_BOUNDED",
        requested_constraints=GATE0_AUDIT_CONSTRAINTS,
    )
    assert res_audit["compatible"] is True
    assert res_audit["executable"] is True
    assert res_audit["selected_capability"] == "REPOSITORY_CONTRACT_AUDIT_BOUNDED"
    assert res_audit["exception_code"] is None

    # Negative 1: Unknown capability -> concrete exception persisted on handoff
    unknown_reg = handoff_mod.register_cross_domain_handoff(
        {
            "objective": "Solicitar capacidad inexistente en Capability Registry.",
            "bounded_context": "WORKER_CONTROL_PLANE",
            "mode": "READ_ONLY",
            "request_key": "p1-cap-unknown-1",
            "constraints": {
                "target_domain": "CONTINUIDAD_OPERATIVA",
                "requested_capability": "CAPACIDAD_NO_EXISTE_XYZ",
                "auto_dispatch": False,
            },
        },
        current_user=_canonical_service_actor(),
        state_root=qroot,
    )
    assert unknown_reg["classification"] == "NO_COMPATIBLE_CAPABILITY"
    assert unknown_reg["lifecycle_state"] == "ESCALATED_HUMAN_REQUIRED"
    assert unknown_reg["exception_code"] == "NO_COMPATIBLE_CAPABILITY_UNKNOWN"
    assert unknown_reg["handoff"]["requires_human_intervention"] is True

    # Negative 2: Mode mismatch (READ_ONLY requesting MUTATION capability)
    mode_mismatch = handoff_mod.resolve_compatible_capabilities(
        target_domain="CONTINUIDAD_OPERATIVA",
        handoff_mode="READ_ONLY",
        requested_capability="DEVELOPMENT_MUTATION_BOUNDED",
    )
    assert mode_mismatch["compatible"] is False
    assert mode_mismatch["exception_code"] == "NO_COMPATIBLE_CAPABILITY_MODE_MISMATCH"

    # Negative 3: Domain mismatch (SEC_RBAC capability on CONTINUIDAD_OPERATIVA)
    dom_mismatch = handoff_mod.resolve_compatible_capabilities(
        target_domain="CONTINUIDAD_OPERATIVA",
        handoff_mode="READ_ONLY",
        requested_capability="SEC_RBAC_SQL_PERMISSION_MATRIX_READONLY",
    )
    assert dom_mismatch["compatible"] is False
    assert dom_mismatch["exception_code"] == "NO_COMPATIBLE_CAPABILITY_DOMAIN_MISMATCH"

    # Negative 4: Assigning incompatible capability to an existing pending handoff fails closed & records exception
    _seed_legacy_gate0_handoff(qroot)
    with pytest.raises(handoff_mod.HandoffError, match="HANDOFF_CAPABILITY_INCOMPATIBLE:NO_COMPATIBLE_CAPABILITY_CONTRACT_INVALID"):
        handoff_mod.update_pending_handoff(
            GATE0_HANDOFF_ID,
            requested_capability="REPOSITORY_CONTRACT_AUDIT_BOUNDED",
            requested_constraints={},  # missing required paths & search_terms!
            current_user=_canonical_service_actor(),
            state_root=qroot,
        )
    after_reject = handoff_mod.load_handoff(GATE0_HANDOFF_ID, state_root=qroot)
    assert after_reject["requested_capability"] is None  # not corrupted
    assert after_reject["exception_code"] == "NO_COMPATIBLE_CAPABILITY_CONTRACT_INVALID"

    # Negative 5: Empty catalog for a mode/domain records NO_COMPATIBLE_CAPABILITY_AVAILABLE
    monkeypatch.setattr(sem_caps, "capability_catalog", lambda: [])
    no_cap = handoff_mod.classify_handoff_request(
        {
            "handoff_id": "HO-TEST-EMPTY-CATALOG",
            "source_domain": "WORKER_CONTROL_PLANE",
            "target_domain": "CONTINUIDAD_OPERATIVA",
            "handoff_mode": "READ_ONLY",
        },
        state_root=qroot,
    )
    assert no_cap["classification"] == "NO_COMPATIBLE_CAPABILITY"
    assert no_cap["lifecycle_state"] == "ESCALATED_HUMAN_REQUIRED"
    assert no_cap["exception_code"] == "NO_COMPATIBLE_CAPABILITY_AVAILABLE"


def test_p1_req7_no_artificial_superadmin_fallback_and_fail_closed_identity(tmp_path):
    """Correction 7: artificial SUPERADMIN/['*'] fallback eliminated; canonical RBAC required, fail closed otherwise."""
    # Static check: _build_dispatch_job_for_handoff must NOT contain synthetic SUPERADMIN / ["*"] / worker@edarsahub.local
    fn_src = inspect.getsource(handoff_mod._build_dispatch_job_for_handoff)
    assert "SUPERADMIN" not in fn_src
    assert '["*"]' not in fn_src
    assert "worker@edarsahub.local" not in fn_src

    qroot = _setup_queue(tmp_path)
    handoff = {
        "schema": handoff_mod.SCHEMA_HANDOFF,
        "handoff_id": GATE0_HANDOFF_ID,
        "source_domain": "WORKER_CONTROL_PLANE",
        "target_domain": "CONTINUIDAD_OPERATIVA",
        "source_objective": GATE0_OBJECTIVE,
        "handoff_mode": "READ_ONLY",
        "requested_capability": "READ_ONLY_CANARY",
        "requested_constraints": {},
        "requester_email": "worker@edarsahub.local",  # synthetic email!
        "classification": "REUSABLE_CAPABILITY_AVAILABLE",
        "lifecycle_state": "CLASSIFIED",
        "auto_dispatch": True,
        "priority_class": "NORMAL",
        "production_allowed": False,
        "production_touched": False,
    }

    # Negative 1: synthetic requester email without current_user -> FAIL CLOSED
    with pytest.raises(handoff_mod.HandoffSecurityError, match="HANDOFF_DISPATCH_IDENTITY_UNVERIFIABLE"):
        handoff_mod._build_dispatch_job_for_handoff(handoff, current_user=None)

    # Negative 2: unverified empty / inactive / read-only operator identity -> FAIL CLOSED
    with pytest.raises(handoff_mod.HandoffSecurityError, match="HANDOFF_DISPATCH_IDENTITY_UNVERIFIABLE"):
        handoff_mod._build_dispatch_job_for_handoff(handoff, current_user={"email": "ricardo@edarsa.com.mx"})
    with pytest.raises(handoff_mod.HandoffSecurityError, match="HANDOFF_DISPATCH_IDENTITY_UNVERIFIABLE"):
        handoff_mod._build_dispatch_job_for_handoff(
            handoff,
            current_user={**_canonical_service_actor(), "active": False},
        )
    with pytest.raises(handoff_mod.HandoffSecurityError, match="HANDOFF_DISPATCH_RBAC_DENIED"):
        handoff_mod._build_dispatch_job_for_handoff(handoff, current_user=_readonly_operator())

    # Negative 3: dispatch_handoff_resolution fails closed when canonical SQL lookup fails
    handoff_real_email = {**handoff, "requester_email": "ricardo@edarsa.com.mx"}
    handoff_mod.save_handoff(handoff_real_email, state_root=qroot)
    dispatched_calls: list[dict] = []

    def failing_resolver(_email: str):
        raise handoff_mod.HandoffSecurityError("HANDOFF_DISPATCH_IDENTITY_UNVERIFIABLE:SQL_UNAVAILABLE")

    blocked = handoff_mod.dispatch_handoff_resolution(
        dict(handoff_real_email),
        state_root=qroot,
        current_user=None,
        identity_resolver=failing_resolver,
        submit_fn=lambda job, **kw: (dispatched_calls.append(job), {"status": "SUBMITTED", "job_id": job["job_id"]})[1],
    )
    assert blocked["dispatched"] is False
    assert blocked["status"] == "DISPATCH_BLOCKED_SECURITY"
    assert "HANDOFF_DISPATCH_IDENTITY_UNVERIFIABLE" in blocked["error_code"]
    assert dispatched_calls == []

    # Positive: canonical identity_resolver returning real user & effective permissions (NO '*') succeeds!
    job = handoff_mod._build_dispatch_job_for_handoff(
        handoff_real_email,
        current_user=None,
        identity_resolver=lambda email: _canonical_service_actor(email),
    )
    assert job is not None
    assert job["schema"] == "edarsahub.worker-job.v2"
    assert job["requester"]["email"] == "ricardo@edarsa.com.mx"
    assert job["production_allowed"] is False


def test_p1_req8_revalidate_authorization_at_dispatch_time(tmp_path):
    """Correction 8: dispatch revalidates authorizations live and fails closed on revocation or expiration."""
    qroot = _setup_queue(tmp_path)

    # Materialize initially valid authorization
    auth = lr.materialize_gate_authorization(
        gate_id="P1-REVALIDATE-TEST",
        authorization_id="GO-P1-REVALIDATE-TEST",
        granted_by="ricardo@edarsa.com.mx",
        domains=["WORKER_CONTROL_PLANE"],
        state_root=qroot,
    )
    auth_path = Path(auth["authorization_path"])

    # Register handoff with auto_dispatch=False while authorization is valid
    reg = handoff_mod.register_cross_domain_handoff(
        {
            "objective": GATE0_OBJECTIVE,
            "bounded_context": "WORKER_CONTROL_PLANE",
            "mode": "READ_ONLY",
            "request_key": "p1-auth-revalidate-r1",
            "constraints": {
                "target_domain": "CONTINUIDAD_OPERATIVA",
                "authorization_ref": "GO-P1-REVALIDATE-TEST",
                "requested_capability": "READ_ONLY_CANARY",
                "requested_constraints": {},
                "auto_dispatch": False,
            },
        },
        current_user=_canonical_service_actor(),
        state_root=qroot,
    )
    hid = reg["handoff_id"]
    assert reg["handoff"]["authorization_verification"]["verified"] is True

    # Revoke the authorization BEFORE dispatch!
    auth_doc = json.loads(auth_path.read_text(encoding="utf-8"))
    auth_doc["revoked"] = True
    auth_path.write_text(json.dumps(auth_doc), encoding="utf-8")

    # Negative 1: Activating auto_dispatch fails closed because authorization was revoked
    with pytest.raises(handoff_mod.HandoffSecurityError, match="HANDOFF_AUTHORIZATION_REVOKED"):
        handoff_mod.update_pending_handoff(
            hid,
            auto_dispatch=True,
            current_user=_canonical_service_actor(),
            state_root=qroot,
        )

    # Negative 2: Direct dispatch_handoff_resolution also revalidates and blocks fail-closed!
    submitted: list[dict] = []
    loaded = handoff_mod.load_handoff(hid, state_root=qroot)
    blocked_revoked = handoff_mod.dispatch_handoff_resolution(
        loaded,
        state_root=qroot,
        current_user=_canonical_service_actor(),
        submit_fn=lambda job, **kw: (submitted.append(job), {"status": "SUBMITTED", "job_id": job["job_id"]})[1],
    )
    assert blocked_revoked["dispatched"] is False
    assert blocked_revoked["status"] == "DISPATCH_BLOCKED_SECURITY"
    assert "HANDOFF_AUTHORIZATION_REVOKED" in blocked_revoked["error_code"]
    assert blocked_revoked["handoff"]["lifecycle_state"] == "WAITING_AUTHORIZATION"
    assert submitted == []

    # Negative 3: Un-revoke but EXPIRE authorization -> still blocked on dispatch!
    auth_doc["revoked"] = False
    auth_doc["expires_at_utc"] = (datetime.now(timezone.utc) - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    auth_path.write_text(json.dumps(auth_doc), encoding="utf-8")
    blocked_expired = handoff_mod.dispatch_handoff_resolution(
        handoff_mod.load_handoff(hid, state_root=qroot),
        state_root=qroot,
        current_user=_canonical_service_actor(),
        submit_fn=lambda job, **kw: (submitted.append(job), {"status": "SUBMITTED", "job_id": job["job_id"]})[1],
    )
    assert blocked_expired["dispatched"] is False
    assert "HANDOFF_AUTHORIZATION_EXPIRED" in blocked_expired["error_code"]
    assert submitted == []

    # Positive: Renew valid authorization -> dispatch succeeds after revalidation!
    auth_doc["expires_at_utc"] = (datetime.now(timezone.utc) + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
    auth_path.write_text(json.dumps(auth_doc), encoding="utf-8")
    ok_disp = handoff_mod.dispatch_handoff_resolution(
        handoff_mod.load_handoff(hid, state_root=qroot),
        state_root=qroot,
        current_user=_canonical_service_actor(),
        submit_fn=lambda job, **kw: (submitted.append(job), {"status": "SUBMITTED", "job_id": job["job_id"]})[1],
    )
    assert ok_disp["dispatched"] is True
    assert len(submitted) == 1
    assert ok_disp["handoff"]["last_authorization_revalidated_at_utc"] is not None


def test_p1_req9_and_10_link_certified_resolution_and_gate0_end_to_end_continuity(tmp_path, monkeypatch):
    """Corrections 9 & 10: link certified resolution fail-closed & demonstrate Gate0 continuity without manual prompts."""
    qroot = _setup_queue(tmp_path)
    monkeypatch.setattr(wis, "STATE_ROOT", qroot)
    wis._GO_CONTEXT_CACHE.clear()
    _seed_legacy_gate0_handoff(qroot)

    # Negative 1: cannot link uncertified / failed / production-touched / wrong-domain result
    _write_certified_result(
        qroot,
        "SEM-UNCERTIFIED-001",
        domain="CONTINUIDAD_OPERATIVA",
        certification="NOT_CERTIFIED",
        tests="FAIL",
    )
    with pytest.raises(handoff_mod.HandoffSecurityError, match="HANDOFF_TERMINAL_CERTIFICATION_INVALID"):
        handoff_mod.link_certified_resolution_to_handoff(
            GATE0_HANDOFF_ID,
            "SEM-UNCERTIFIED-001",
            current_user=_canonical_service_actor(),
            state_root=qroot,
        )

    _write_certified_result(
        qroot,
        "SEM-WRONG-DOMAIN-001",
        domain="FINANZAS_CXP",
        certification="CERTIFIED_READ_ONLY",
    )
    with pytest.raises(handoff_mod.HandoffSecurityError, match="HANDOFF_RESOLUTION_DOMAIN_MISMATCH"):
        handoff_mod.link_certified_resolution_to_handoff(
            GATE0_HANDOFF_ID,
            "SEM-WRONG-DOMAIN-001",
            current_user=_canonical_service_actor(),
            state_root=qroot,
        )

    # Positive end-to-end Gate0 continuity WITHOUT manual prompt exchange:
    # Step A: Assign compatible capability & authorize auto_dispatch on the existing Gate0 handoff
    dispatched: list[dict] = []
    upd = handoff_mod.update_pending_handoff(
        GATE0_HANDOFF_ID,
        requested_capability="REPOSITORY_CONTRACT_AUDIT_BOUNDED",
        requested_constraints=GATE0_AUDIT_CONSTRAINTS,
        auto_dispatch=True,
        current_user=_canonical_service_actor(),
        state_root=qroot,
        submit_fn=lambda job, **kw: (
            dispatched.append(job),
            {"status": "SUBMITTED", "job_id": job["job_id"], "production_touched": False},
        )[1],
    )
    assert upd["handoff_id"] == GATE0_HANDOFF_ID
    assert upd["dependency_id"] == GATE0_DEPENDENCY_ID
    assert upd["request_key"] == GATE0_REQUEST_KEY
    assert upd["dispatched"] is True
    assert upd["lifecycle_state"] == "IN_PROGRESS"
    assert len(dispatched) == 1
    resolution_job_id = upd["job_id"]
    assert dispatched[0]["scheduling"]["bounded_context"] == "CONTINUIDAD_OPERATIVA"
    assert dispatched[0]["production_allowed"] is False

    # Step B: Worker executes & produces certified terminal result for CONTINUIDAD_OPERATIVA
    _write_certified_result(
        qroot,
        resolution_job_id,
        domain="CONTINUIDAD_OPERATIVA",
        certification="CERTIFIED_READ_ONLY",
        checks=[{"type": "repository_contract_audit", "status": "PASS", "request": GATE0_AUDIT_CONSTRAINTS}],
    )

    # Step C: Control Plane reconciles & automatically links certified resolution back to original Gate0 handoff
    rec = handoff_mod.reconcile_cross_domain_handoffs(state_root=qroot)
    assert GATE0_HANDOFF_ID in rec["returned_this_cycle"]

    final_doc = handoff_mod.load_handoff(GATE0_HANDOFF_ID, state_root=qroot)
    assert final_doc["handoff_id"] == GATE0_HANDOFF_ID
    assert final_doc["request_key"] == GATE0_REQUEST_KEY
    assert final_doc["dependency_id"] == GATE0_DEPENDENCY_ID
    assert final_doc["resolution_job_id"] == resolution_job_id
    assert final_doc["lifecycle_state"] == "RETURNED_TO_SOURCE"
    assert final_doc["certification"] == "CERTIFIED_READ_ONLY"
    assert final_doc["dependency_satisfied"] is True
    assert final_doc["evidence_link"]["resolution_job_id"] == resolution_job_id
    assert final_doc["evidence_link"]["tests"] == "PASS"
    assert final_doc["evidence_link"]["quality_gate"] == "PASS"
    assert final_doc["production_touched"] is False
    assert len(handoff_mod.list_handoffs(state_root=qroot)) == 1  # Never duplicated!

    # Step D: Source domain WORKER_CONTROL_PLANE automatically receives certified resolution via get_go_context!
    ctx_source = wis.resolve_go_context(
        domain="WORKER_CONTROL_PLANE",
        current_user=_canonical_service_actor(),
        config_dir=tmp_path / "nochains",
    )
    assert ctx_source["next_allowed_action"] == "CONTINUE_AUTONOMOUS"
    assert ctx_source["cross_domain_handoffs"]["counts"]["satisfied_resolutions"] == 1
    sat = ctx_source["cross_domain_handoffs"]["satisfied_resolutions"][0]
    assert sat["handoff_id"] == GATE0_HANDOFF_ID
    assert sat["dependency_id"] == GATE0_DEPENDENCY_ID
    assert sat["resolution_job_id"] == resolution_job_id
    assert sat["certification"] == "CERTIFIED_READ_ONLY"
    assert sat["production_touched"] is False
