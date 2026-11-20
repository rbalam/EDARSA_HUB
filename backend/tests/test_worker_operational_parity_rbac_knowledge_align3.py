"""Pruebas GATE-ALIGN-3: RBAC temprano (M-05), Certificacion Operativa Preview (M-07) y Knowledge Loop."""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

os.environ.setdefault("JWT_SECRET", "unit-test-only-signing-material-align3-0001")
os.environ.setdefault("EDARSAHUB_SQL_HOST", "127.0.0.1")
os.environ.setdefault("EDARSAHUB_SQL_PORT", "1433")
os.environ.setdefault("EDARSAHUB_SQL_DATABASE", "EDARSAHUB")
os.environ.setdefault("EDARSAHUB_SQL_USER", "HRLectura")
os.environ.setdefault("EDARSAHUB_SQL_PASSWORD", "unit-test-only-placeholder")
os.environ.setdefault("CORS_ORIGINS", "https://app.edarsa.test,http://localhost:3000")

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "backend"), str(ROOT / "tools" / "mirror_sync")):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest

from modules.worker_ingress import service as ingress_service
from tools.mirror_sync import universal_job_result_publisher as result_publisher
from tools.mirror_sync import worker_maintenance_runtime as maintenance
from tools.mirror_sync import worker_repair_auto_loop as auto_loop
from tools.mirror_sync import worker_repair_execution as execution
from tools.mirror_sync.worker_result_reader import read_canonical_result
from tools.mirror_sync.worker_result_status import (
    PREVIEW_VALIDATION_SCHEMA,
    build_job_status,
    validate_operational_preview_evidence,
)

COMMIT_SHA = "709bba11d09a18c5e7fe3285a466d3bb2e5564f2"


def _redirect_maintenance(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(maintenance, "STATE_DIR", tmp_path)
    monkeypatch.setattr(maintenance, "INCIDENT_DIR", tmp_path / "incidents")


def _repair_job(
    incident_id: str,
    *,
    mode: str = "MUTATION",
    path: str = "tools/mirror_sync/worker_control_plane.py",
    email: str = "ricardo@edarsa.com.mx",
    production_allowed: bool = False,
    target_branch: str = "Edarsahub_Desarrollo",
    include_actions: bool = True,
) -> dict:
    actions = (
        [
            {
                "type": "replace_text",
                "path": path,
                "old": "OLD",
                "new": "NEW",
                "expected_count": 1,
            }
        ]
        if include_actions
        else []
    )
    return {
        "schema": "edarsahub.worker-job.v2",
        "job_id": execution.deterministic_repair_job_id(incident_id, 1),
        "target_repo": "rbalam/EDARSA_HUB",
        "target_branch": target_branch,
        "production_allowed": production_allowed,
        "objective": "Reparacion acotada de infraestructura Worker.",
        "human_summary_language": "es",
        "requester": {
            "email": email,
            "source": "edarsahub-worker-ingress",
            "project": "EDARSAHUB-BOS",
            "chat": "ALIGN-3-TEST",
        },
        "mode": mode,
        "actions": actions,
        "checks": [{"type": "git_diff_check"}],
    }


def _certified_result_payload(job_id: str, *, commit_sha: str = COMMIT_SHA) -> dict:
    return {
        "schema": "edarsahub.worker-result.v2",
        "job_id": job_id,
        "status": "INTEGRATED",
        "slot_class": "MUTATION",
        "quality_gate": "PASS",
        "tests": "PASS",
        "certification": "CERTIFIED",
        "work_completion": "COMPLETE",
        "percent_complete": 100,
        "blockers": [],
        "production_touched": False,
        "git_sync_status": "CERTIFIED_GIT_SYNC",
        "development_sha": commit_sha,
        "certified_source_sha": commit_sha,
        "converged_head": commit_sha,
        "certification_basis": "SHA_BOUND_ATTESTATION_PLUS_ARTIFACT_CONVERGENCE",
        "attestation_sha256": "a" * 64,
        "files_changed": ["tools/mirror_sync/worker_result_status.py"],
        "completed_at_utc": "2026-11-20T16:00:00Z",
        "summary_es": "Codigo certificado.",
    }


def _valid_preview_evidence(job_id: str, *, commit_sha: str = COMMIT_SHA) -> dict:
    return {
        "schema": PREVIEW_VALIDATION_SCHEMA,
        "job_id": job_id,
        "commit_sha": commit_sha,
        "preview_activated": True,
        "operational_tests": "PASS",
        "functional_result": "PASS",
        "checks_passed": 12,
        "checks_total": 12,
        "evidence_sha256": "b" * 64,
        "validated_at_utc": "2026-11-20T16:10:00Z",
        "production_touched": False,
    }


# =============================================================================
# FASE 2 (M-05) — RBAC temprano, separacion READ_ONLY/MUTATION y bounded context
# =============================================================================


def test_m05_rbac_authorized_and_unauthorized_fail_closed_before_publish(tmp_path, monkeypatch):
    _redirect_maintenance(tmp_path, monkeypatch)
    incident_id = "WORKER-ALIGN3-RBAC-1"
    maintenance.declare_runtime_incident(
        incident_id,
        ["tools/mirror_sync/worker_control_plane.py"],
    )

    publish_calls = []

    def _fake_publish(plan, **kwargs):
        publish_calls.append(plan["job_id"])
        return {"status": "PUBLISHED", "job_id": plan["job_id"], "commit_sha": "c" * 40, "production_touched": False}

    monkeypatch.setattr(execution.gate_chain_publisher, "publish", _fake_publish)

    # 1. No autorizado (no SUPERADMIN) -> bloqueado antes de publicar
    with pytest.raises(ValueError, match="REPAIR_RBAC_DENIED:REQUESTER_NOT_SUPERADMIN"):
        execution.publish_repair_job(
            incident_id,
            _repair_job(incident_id, email="operador@edarsa.com.mx"),
            enforce_rbac=True,
            rbac_authorizer=lambda _req: {"allowed": False, "reason": "REQUESTER_NOT_SUPERADMIN"},
        )
    assert publish_calls == []

    # 2. Usuario inactivo -> bloqueado
    with pytest.raises(ValueError, match="REPAIR_RBAC_DENIED:REQUESTER_INACTIVE"):
        execution.publish_repair_job(
            incident_id,
            _repair_job(incident_id, email="inactivo@edarsa.com.mx"),
            enforce_rbac=True,
            rbac_authorizer=lambda _req: {"allowed": False, "reason": "REQUESTER_INACTIVE"},
        )
    assert publish_calls == []

    # 3. Fallo SQL en lookup RBAC -> fail-closed REQUESTER_RBAC_RUNTIME_ERROR
    def _sql_down(_req):
        raise RuntimeError("SQL Server unreachable")

    with pytest.raises(ValueError, match="REPAIR_RBAC_DENIED:REQUESTER_RBAC_RUNTIME_ERROR"):
        execution.publish_repair_job(
            incident_id,
            _repair_job(incident_id),
            enforce_rbac=True,
            rbac_authorizer=_sql_down,
        )
    assert publish_calls == []

    # 4. SUPERADMIN activo autorizado -> permite publicacion exactamente una vez
    res = execution.publish_repair_job(
        incident_id,
        _repair_job(incident_id),
        enforce_rbac=True,
        rbac_authorizer=lambda req: {
            "allowed": True,
            "reason": "SUPERADMIN_CANONICAL",
            "email": req["email"],
            "role_code": "SUPERADMIN",
        },
    )
    assert res["production_touched"] is False
    assert len(publish_calls) == 1


def test_m05_readonly_mutation_separation_and_cross_bounded_context_denied():
    # READ_ONLY sin acciones -> permitido como lectura
    ro_ok = execution.authorize_repair_execution(
        _repair_job("WORKER-RO-1", mode="READ_ONLY", include_actions=False),
    )
    assert ro_ok["allowed"] is True
    assert ro_ok["mode"] == "READ_ONLY"

    # READ_ONLY con acciones de mutacion -> rechazado fail-closed
    with pytest.raises(ValueError, match="REPAIR_READ_ONLY_MUTATION_FORBIDDEN"):
        execution.authorize_repair_execution(
            _repair_job("WORKER-RO-2", mode="READ_ONLY", include_actions=True),
        )

    # Acceso entre bounded contexts (modulo comercial o frontend) -> rechazado fail-closed
    for forbidden_path in ("backend/modules/comercial/repository.py", "frontend/src/App.jsx"):
        with pytest.raises(ValueError, match="REPAIR_BOUNDED_CONTEXT_FORBIDDEN"):
            execution.authorize_repair_execution(
                _repair_job("WORKER-CTX-1", path=forbidden_path),
                authorizer=lambda _r: {"allowed": True, "reason": "SUPERADMIN_CANONICAL"},
            )

    # Produccion prohibida
    with pytest.raises(ValueError, match="REPAIR_PRODUCTION_FORBIDDEN"):
        execution.authorize_repair_execution(
            _repair_job("WORKER-PROD-1", production_allowed=True),
            authorizer=lambda _r: {"allowed": True, "reason": "SUPERADMIN_CANONICAL"},
        )


def test_m05_auto_loop_blocks_unauthorized_repair_before_planner(tmp_path, monkeypatch):
    _redirect_maintenance(tmp_path, monkeypatch)
    monkeypatch.setenv("EDARSAHUB_WORKER_REPAIR_ENFORCE_RBAC", "1")
    monkeypatch.setattr(auto_loop, "QUEUE_ROOT", tmp_path / "queue")

    incident_id = "WORKER-AUTO-RBAC-DENY"
    maintenance.declare_runtime_incident(
        incident_id,
        ["tools/mirror_sync/worker_control_plane.py"],
        source_job_id="SRC-JOB-RBAC-1",
        requester={
            "email": "no-admin@edarsa.com.mx",
            "source": "edarsahub-worker-ingress",
            "project": "EDARSAHUB-BOS",
            "chat": "TEST",
        },
    )

    monkeypatch.setattr(
        execution,
        "_default_rbac_authorizer",
        lambda _req: {"allowed": False, "reason": "REQUESTER_NOT_SUPERADMIN"},
    )
    called_planner = []
    monkeypatch.setattr(
        auto_loop.planner,
        "publish_planned_repair",
        lambda *a, **kw: called_planner.append(a),
    )

    out = auto_loop.advance_repair_automation({"incidents": []})
    assert called_planner == []
    assert any(
        row["incident_id"] == incident_id
        and row["action"] == "BLOCKED_RBAC"
        and "REQUESTER_NOT_SUPERADMIN" in row["reason"]
        for row in out["incidents"]
    )


# =============================================================================
# FASE 3 (M-07) — Separacion SUBMITTED / INTEGRATED / CERTIFIED / ACTIVE_IN_PREVIEW
# =============================================================================


def test_m07_four_lifecycle_stages_and_differentiated_evidence(tmp_path, monkeypatch):
    state = tmp_path / "queue"
    for d in ("pending", "results", "preview_validations"):
        (state / d).mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(ingress_service, "STATE_ROOT", state)

    # 1. SUBMITTED (pendiente en cola)
    jid_sub = "JOB-STAGE-SUBMITTED"
    (state / "pending" / f"{jid_sub}.json").write_text(json.dumps({"job_id": jid_sub}), encoding="utf-8")
    st_sub = ingress_service.get_job_status(jid_sub)
    assert st_sub["lifecycle_stage"] == "SUBMITTED"
    assert st_sub["code_certified"] is False
    assert st_sub["operational_validated"] is False

    # 2. INTEGRATED (95%, PENDING_AUDIT_EVIDENCE)
    jid_int = "JOB-STAGE-INTEGRATED"
    int_payload = _certified_result_payload(jid_int)
    int_payload.update(
        {
            "certification": "PENDING_AUDIT_EVIDENCE",
            "work_completion": "PENDING_CERTIFICATION",
            "percent_complete": 95,
        }
    )
    int_payload.pop("attestation_sha256", None)
    int_payload.pop("certification_basis", None)
    (state / "results" / f"{jid_int}.json").write_text(json.dumps(int_payload), encoding="utf-8")
    st_int = ingress_service.get_job_status(jid_int)
    assert st_int["lifecycle_stage"] == "INTEGRATED"
    assert st_int["code_certified"] is False
    assert st_int["operational_validated"] is False
    assert st_int["evidence_breakdown"]["quality_gate"] == "PASS"
    assert st_int["evidence_breakdown"]["attestation"] == "PENDING"
    assert st_int["evidence_breakdown"]["preview_activation"] == "UNVERIFIED"

    # 3. CERTIFIED sin evidencia Preview -> NO auto-promueve a ACTIVE_IN_PREVIEW
    jid_cert = "JOB-STAGE-CERTIFIED"
    cert_path = state / "results" / f"{jid_cert}.json"
    cert_raw = json.dumps(_certified_result_payload(jid_cert))
    cert_path.write_text(cert_raw, encoding="utf-8")
    st_cert = ingress_service.get_job_status(jid_cert)
    assert st_cert["certification"] == "CERTIFIED"
    assert st_cert["lifecycle_stage"] == "CERTIFIED"
    assert st_cert["code_certified"] is True
    assert st_cert["operational_validated"] is False
    assert st_cert["operational_validation_status"] == "PENDING_PREVIEW_VALIDATION"
    assert st_cert["evidence_breakdown"]["attestation"] == "VERIFIED"
    assert st_cert["evidence_breakdown"]["preview_activation"] == "UNVERIFIED"
    assert st_cert["evidence_breakdown"]["operational_tests"] == "NOT_RUN"
    assert st_cert["evidence_breakdown"]["functional_result"] == "UNVERIFIED"
    # Archivo historico certificado permanece intacto
    assert cert_path.read_text(encoding="utf-8") == cert_raw

    # 4. ACTIVE_IN_PREVIEW solo con evidencia Preview valida SHA-bound
    (state / "preview_validations" / f"{jid_cert}.json").write_text(
        json.dumps(_valid_preview_evidence(jid_cert)),
        encoding="utf-8",
    )
    st_prev = ingress_service.get_job_status(jid_cert)
    assert st_prev["lifecycle_stage"] == "ACTIVE_IN_PREVIEW"
    assert st_prev["code_certified"] is True
    assert st_prev["operational_validated"] is True
    assert st_prev["operational_validation_status"] == "ACTIVE_IN_PREVIEW"
    assert st_prev["evidence_breakdown"]["preview_activation"] == "ACTIVE"
    assert st_prev["evidence_breakdown"]["operational_tests"] == "PASS"
    assert st_prev["evidence_breakdown"]["functional_result"] == "PASS"


def test_m07_invalid_mismatched_or_sensitive_preview_evidence_fails_closed(tmp_path):
    jid = "JOB-PREVIEW-FAIL"
    res_path = tmp_path / f"{jid}.json"
    res_path.write_text(json.dumps(_certified_result_payload(jid)), encoding="utf-8")
    read = read_canonical_result(res_path, expected_job_id=jid)

    # SHA de commit distinto -> PREVIEW_VALIDATION_FAILED (no ACTIVE_IN_PREVIEW)
    bad_sha = _valid_preview_evidence(jid, commit_sha="1" * 40)
    st_bad_sha = build_job_status(result_read=read, preview_evidence=bad_sha)
    assert st_bad_sha["lifecycle_stage"] == "CERTIFIED"
    assert st_bad_sha["operational_validated"] is False
    assert st_bad_sha["operational_validation_status"] == "PREVIEW_VALIDATION_FAILED"

    # Clave sensible en evidencia Preview -> rechazada fail-closed
    leaky = {**_valid_preview_evidence(jid), "api_token": "secret-should-fail"}
    ev_leaky = validate_operational_preview_evidence(leaky, expected_job_id=jid, expected_commit_sha=COMMIT_SHA)
    assert ev_leaky["valid"] is False
    assert ev_leaky["reason"] == "PREVIEW_EVIDENCE_SENSITIVE_FIELD_FORBIDDEN"

    # Pruebas operativas en FAIL -> PREVIEW_VALIDATION_FAILED
    failed_ops = {**_valid_preview_evidence(jid), "operational_tests": "FAIL"}
    st_fail = build_job_status(result_read=read, preview_evidence=failed_ops)
    assert st_fail["operational_validated"] is False
    assert st_fail["operational_validation_status"] == "PREVIEW_VALIDATION_FAILED"

    # Result Publisher sanitiza evidencia Preview valida y descarta la invalida sin romper historicos
    pub_in = {**_certified_result_payload(jid), "operational_validation": leaky}
    sanitized_bad = result_publisher.sanitize(pub_in)
    assert "operational_validation" not in sanitized_bad

    pub_ok = {**_certified_result_payload(jid), "operational_validation": _valid_preview_evidence(jid)}
    sanitized_ok = result_publisher.sanitize(pub_ok)
    assert sanitized_ok["operational_validation"]["preview_activated"] is True
    assert sanitized_ok["operational_validation"]["commit_sha"] == COMMIT_SHA


# =============================================================================
# FASE 4 — Knowledge Loop: 7 lecciones historicas, prevencion de duplicados y concurrencia
# =============================================================================


def test_knowledge_loop_contains_all_seven_historical_lessons_and_taxonomy():
    expected_classes = {
        "MISSING_EXPECTED_SHA256",
        "EXECUTABLE_MODE_STRIP",
        "GIT_MIRROR_DIVERGENCE",
        "MIRROR_SYNC_STOPPED",
        "SQL_AS_DICT_UNNAMED_COLUMN",
        "REVOKED_SESSION_ACCEPTED",
        "CODE_CERTIFIED_WITHOUT_OPERATIONAL_VALIDATION",
    }
    present_classes = {lesson["failure_class"] for lesson in auto_loop.CANONICAL_KNOWLEDGE_LESSONS}
    assert expected_classes.issubset(present_classes)
    for lesson in auto_loop.CANONICAL_KNOWLEDGE_LESSONS:
        assert lesson["production_touched"] is False
        assert lesson["source_job_id"]
        assert lesson["root_cause"]
        assert lesson["certified_repair_job_id"]

    # Taxonomia clasifica todos los patrones clave
    assert auto_loop.classify_failure_taxonomy(blockers=["WRITE_EXISTING_REQUIRES_EXPECTED_SHA256"])["failure_class"] == "MISSING_EXPECTED_SHA256"
    assert auto_loop.classify_failure_taxonomy(blockers=["ATOMIC_WRITE_MODE_STRIP"])["failure_class"] == "EXECUTABLE_MODE_STRIP"
    assert auto_loop.classify_failure_taxonomy(blockers=["MIRROR_POST_DISCONNECT_STOPPED"])["failure_class"] == "MIRROR_SYNC_STOPPED"
    assert auto_loop.classify_failure_taxonomy(blockers=["PYMSSQL_AS_DICT_UNNAMED_COLUMN"])["failure_class"] == "SQL_AS_DICT_UNNAMED_COLUMN"
    assert auto_loop.classify_failure_taxonomy(blockers=["REVOKED_SESSION_ACCEPTED"])["human_approval_required"] is True
    assert auto_loop.classify_failure_taxonomy(blockers=["CERTIFIED_WITHOUT_PREVIEW_EVIDENCE"])["failure_class"] == "CODE_CERTIFIED_WITHOUT_OPERATIONAL_VALIDATION"
    assert auto_loop.classify_failure_taxonomy(blockers=["MODULENOTFOUNDERROR:pymssql"])["failure_class"] == "MISSING_DEPENDENCY"


def test_knowledge_loop_prevents_duplicate_historical_repairs(tmp_path, monkeypatch):
    _redirect_maintenance(tmp_path, monkeypatch)
    monkeypatch.setattr(auto_loop, "QUEUE_ROOT", tmp_path / "queue")

    # 1. Assess cycle detecta leccion historica ya certificada y detiene reparacion duplicada
    assessment = auto_loop.assess_knowledge_loop_cycle(
        incident_id="INC-DUP-SHA-1",
        blockers=["WRITE_EXISTING_REQUIRES_EXPECTED_SHA256"],
        error_code="WRITE_EXISTING_REQUIRES_EXPECTED_SHA256",
        source_job_id="EDARSAHUB-BOS-SEC-P1-SESSION-REVOCATION-R3-20261120",
        causal_evidence={"file": "backend/core/refresh_tokens.py"},
        state_dir=tmp_path / "cb",
    )
    assert assessment["duplicate_repair_check"]["duplicate_prevented"] is True
    assert assessment["next_step"] == "DUPLICATE_HISTORICAL_REPAIR_PREVENTED"
    assert assessment["matched_lesson"]["lesson_id"] == "LESSON-MISSING-EXPECTED-SHA256"
    assert assessment["production_touched"] is False

    # 2. Auto-loop suprime publicacion cuando un incidente repite causa historica certificada
    incident_id = "WORKER-DUP-HIST-1"
    maintenance.declare_runtime_incident(
        incident_id,
        ["tools/mirror_sync/worker_mutation_materializer.py"],
        source_job_id="EDARSAHUB-BOS-WORKER-OPS-GUARD-LOCK-FINALIZE-PARITY-R1-20261120",
        problem_signature="ATOMIC_WRITE_MODE_STRIP",
        requester={
            "email": "ricardo@edarsa.com.mx",
            "source": "edarsahub-worker-ingress",
            "project": "EDARSAHUB-BOS",
            "chat": "TEST",
        },
    )
    called = []
    monkeypatch.setattr(auto_loop.planner, "publish_planned_repair", lambda *a, **kw: called.append(a))

    out = auto_loop.advance_repair_automation({"incidents": []})
    assert called == []
    assert any(
        r["incident_id"] == incident_id
        and r["action"] == "PREVENTED_DUPLICATE_HISTORICAL_REPAIR"
        and r["matched_lesson_id"] == "LESSON-EXECUTABLE-MODE-STRIP"
        for r in out["incidents"]
    )


def test_concurrency_safe_rbac_status_and_knowledge_loop(tmp_path):
    res_path = tmp_path / "JOB-CONC-1.json"
    res_path.write_text(json.dumps(_certified_result_payload("JOB-CONC-1")), encoding="utf-8")

    def _worker(idx: int):
        auth = execution.authorize_repair_execution(
            _repair_job(f"WORKER-CONC-{idx}"),
            authorizer=lambda req: {"allowed": True, "reason": "SUPERADMIN_CANONICAL", "email": req["email"]},
        )
        read = read_canonical_result(res_path, expected_job_id="JOB-CONC-1")
        st = build_job_status(result_read=read, preview_evidence=_valid_preview_evidence("JOB-CONC-1"))
        kl = auto_loop.assess_knowledge_loop_cycle(
            incident_id=f"INC-CONC-{idx}",
            blockers=["PYMSSQL_AS_DICT_UNNAMED_COLUMN"],
            error_code="PYMSSQL_AS_DICT_UNNAMED_COLUMN",
            causal_evidence={"idx": idx},
            state_dir=tmp_path / f"cb_{idx}",
        )
        return auth["allowed"], st["lifecycle_stage"], kl["next_step"]

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(_worker, range(12)))

    assert all(
        r == (True, "ACTIVE_IN_PREVIEW", "DUPLICATE_HISTORICAL_REPAIR_PREVENTED")
        for r in results
    )
