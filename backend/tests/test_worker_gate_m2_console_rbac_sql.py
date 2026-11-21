"""Pruebas integrales GATE-M2: Worker Console RBAC Fail-Closed + SQL Canónico + Proyección Incremental."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock

# Configurar variables dummy antes de importar core.* en worktree aislado sin .env
os.environ.setdefault("JWT_SECRET", "test-gate-m2-jwt-secret-only-unit-tests-1234567890")
os.environ.setdefault("EDARSAHUB_SQL_HOST", "127.0.0.1")
os.environ.setdefault("EDARSAHUB_SQL_PORT", "1433")
os.environ.setdefault("EDARSAHUB_SQL_DATABASE", "EDARSAHUB")
os.environ.setdefault("EDARSAHUB_SQL_USER", "HRLectura")
os.environ.setdefault("EDARSAHUB_SQL_PASSWORD", "test-placeholder")

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
TOOLS = ROOT / "tools" / "mirror_sync"
for p in (str(ROOT), str(BACKEND), str(TOOLS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
import pytest  # noqa: E402

from core.security import create_access_token  # noqa: E402
from modules.worker_console import contract as C  # noqa: E402
from modules.worker_console import routes as R  # noqa: E402
from tools.mirror_sync import worker_sql_projection as proj  # noqa: E402


def _make_client() -> TestClient:
    app = FastAPI()
    app.include_router(R.router, prefix="/api")
    return TestClient(app)


SAMPLE_JOB_ROWS: List[Dict[str, Any]] = [
    {
        "JobID": "EDARSAHUB-BOS-TEST-ACTIVE-PREVIEW-1",
        "SchemaVersion": "edarsahub.worker-job.v2",
        "SourceJobID": None,
        "ProjectID": "EDARSAHUB",
        "BoundedContext": "WORKER_OPERATIONS",
        "CapabilityCode": "GATE_M1",
        "Mode": "MUTATION",
        "Objective": "SQL Canónico M1 validado en Preview",
        "PriorityClass": "HIGH",
        "RequesterUsuarioID": 1,
        "RequesterEmail": "superadmin@edarsa.com",
        "RequesterSource": "ANTIGRAVITY",
        "OwnerAgentOrDev": "universal-worker-v4",
        "ChainID": "CHAIN-1",
        "GateID": "GATE-M1",
        "DependsOnJobID": None,
        "LifecycleStage": "ACTIVE_IN_PREVIEW",
        "ExecutionStatus": "INTEGRATED",
        "QualityGate": "PASS",
        "TestsStatus": "PASS",
        "IntegrationStatus": "INTEGRATED",
        "GitSyncStatus": "SYNCED_0_0",
        "CertificationStatus": "CERTIFIED",
        "OperationalValidationStatus": "VALIDATED_IN_PREVIEW",
        "PreviewActivated": 1,
        "OperationalTests": "PASS",
        "FunctionalResult": "PASS",
        "TerminalResultValid": 1,
        "PercentComplete": 100,
        "DevelopmentCommitSHA": "a" * 40,
        "PublishedResultCommitSHA": "b" * 40,
        "ResultSHA256": "c" * 64,
        "AttestationSHA256": "d" * 64,
        "ProductionTouched": 0,
        "RecoveryAttempts": 0,
        "BlockersJson": "[]",
        "NextRecommendedAction": None,
        "ReconciliationStatus": "RECONCILED_CERTIFIED",
        "ProvenanceSource": "GIT_RESULTS_BACKFILL",
        "SubmittedAtUtc": "2026-11-20T16:00:00",
        "StartedAtUtc": "2026-11-20T16:00:05",
        "CompletedAtUtc": "2026-11-20T16:01:00",
        "PublishedAtUtc": "2026-11-20T16:01:10",
        "UpdatedAtUtc": "2026-11-20T16:01:15",
    },
    {
        "JobID": "EDARSAHUB-BOS-TEST-CERTIFIED-ONLY-2",
        "SchemaVersion": "edarsahub.worker-job.v2",
        "SourceJobID": "SRC-JOB-99",
        "ProjectID": "EDARSAHUB",
        "BoundedContext": "COMERCIAL",
        "CapabilityCode": None,
        "Mode": "MUTATION",
        "Objective": "Código certificado pendiente validación Preview",
        "PriorityClass": "NORMAL",
        "RequesterUsuarioID": 2,
        "RequesterEmail": "admin@edarsa.com",
        "RequesterSource": "ANTIGRAVITY",
        "OwnerAgentOrDev": "universal-worker-v4",
        "ChainID": None,
        "GateID": None,
        "DependsOnJobID": None,
        "LifecycleStage": "CERTIFIED",
        "ExecutionStatus": "INTEGRATED",
        "QualityGate": "PASS",
        "TestsStatus": "PASS",
        "IntegrationStatus": "INTEGRATED",
        "GitSyncStatus": "SYNCED_0_0",
        "CertificationStatus": "CERTIFIED",
        "OperationalValidationStatus": "PENDING_PREVIEW_VALIDATION",
        "PreviewActivated": 0,
        "OperationalTests": "NOT_RUN",
        "FunctionalResult": "UNVERIFIED",
        "TerminalResultValid": 1,
        "PercentComplete": 100,
        "DevelopmentCommitSHA": "e" * 40,
        "PublishedResultCommitSHA": "f" * 40,
        "ResultSHA256": "1" * 64,
        "AttestationSHA256": "2" * 64,
        "ProductionTouched": 0,
        "RecoveryAttempts": 0,
        "BlockersJson": "[]",
        "NextRecommendedAction": "VALIDATE_IN_PREVIEW",
        "ReconciliationStatus": "RECONCILED_CERTIFIED",
        "ProvenanceSource": "GIT_RESULTS_BACKFILL",
        "SubmittedAtUtc": "2026-11-20T15:00:00",
        "StartedAtUtc": "2026-11-20T15:00:05",
        "CompletedAtUtc": "2026-11-20T15:01:00",
        "PublishedAtUtc": "2026-11-20T15:01:10",
        "UpdatedAtUtc": "2026-11-20T15:01:15",
    },
]

SAMPLE_INCIDENT_ROWS: List[Dict[str, Any]] = [
    {
        "IncidentID": "INC-TEST-001",
        "IncidentCategory": "WORKER_FAILURE",
        "ErrorClass": "CONTRACT_DRIFT",
        "Severity": "HIGH",
        "IncidentState": "RESOLVED",
        "SourceJobID": "EDARSAHUB-BOS-TEST-CERTIFIED-ONLY-2",
        "RepairJobID": "EDARSAHUB-BOS-TEST-ACTIVE-PREVIEW-1",
        "ProjectID": "EDARSAHUB",
        "BoundedContext": "WORKER_OPERATIONS",
        "ProblemSignature": "SIG_CONTRACT",
        "BlockerSignature": "BLK_01",
        "CapabilityCode": "GATE_M1",
        "RootCause": "Alias SQL faltante",
        "ImpactSummary": "Fallo en lectura as_dict",
        "OwnerEmail": "superadmin@edarsa.com",
        "EvidenceRef": "ev://1",
        "RecommendedAction": "Usar alias explícito",
        "RecoveryAttempts": 1,
        "CooldownUntilUtc": None,
        "AlertNotifiedAtUtc": None,
        "ProductionTouched": 0,
        "CreatedAtUtc": "2026-11-20T14:00:00",
        "UpdatedAtUtc": "2026-11-20T14:30:00",
    }
]

SAMPLE_CAPABILITY_ROWS: List[Dict[str, Any]] = [
    {
        "CapabilityCode": "CAP_KNOWLEDGE_P1_2",
        "CapabilityKind": "KNOWLEDGE_LESSON",
        "ProblemSignature": "PYMSSQL_AS_DICT_UNNAMED",
        "AllowedModes": "MUTATION",
        "BoundedContextRule": "WORKER_OPERATIONS",
        "Reusable": 1,
        "SourceJobID": "P1-2-R3",
        "CertifiedRepairJobID": "P1-2-R4",
        "CertifiedCommitSHA": "a" * 40,
        "CertificationStatus": "CERTIFIED",
        "OperationalValidationStatus": "VALIDATED_IN_PREVIEW",
        "RootCause": "Expresión SQL sin alias con cursor as_dict=True",
        "PreventionRule": "Siempre asignar alias explícito AS ...",
        "ProductionTouched": 0,
        "UpdatedAtUtc": "2026-11-20T16:00:00",
    }
]


def _mock_sql_reads(monkeypatch, *, captured_sql: Optional[List[tuple]] = None):
    def fake_all(sql: str, params=None, profile: str = "default"):
        if captured_sql is not None:
            captured_sql.append((sql, list(params or [])))
        if "GROUP BY LifecycleStage" in sql:
            return [
                {"lifecycle_stage": "CERTIFIED", "total": 2500},
                {"lifecycle_stage": "ACTIVE_IN_PREVIEW", "total": 12},
                {"lifecycle_stage": "SUBMITTED", "total": 812},
            ]
        if "GROUP BY CertificationStatus" in sql:
            return [
                {"certification_status": "CERTIFIED", "total": 2512},
                {"certification_status": "NOT_CERTIFIED", "total": 812},
            ]
        if "GROUP BY BoundedContext" in sql:
            return [{"bounded_context": "WORKER_OPERATIONS", "total": 3324}]
        if "FROM dbo.Sys_Worker_Jobs" in sql:
            return list(SAMPLE_JOB_ROWS)
        if "FROM dbo.Sys_Worker_Incidents" in sql:
            return list(SAMPLE_INCIDENT_ROWS)
        if "FROM dbo.Sys_Worker_Capabilities" in sql:
            return list(SAMPLE_CAPABILITY_ROWS)
        if "FROM dbo.Sys_Worker_RecoveryEvents" in sql:
            return []
        return []

    def fake_one(sql: str, params=None, profile: str = "default"):
        if captured_sql is not None:
            captured_sql.append((sql, list(params or [])))
        if "AS total_jobs" in sql:
            return {
                "total_jobs": 3324,
                "active_in_preview_count": 12,
                "certified_count": 2500,
                "integrated_count": 0,
                "submitted_count": 812,
                "error_or_blocked_count": 0,
                "production_touched_count": 0,
                "preview_validated_count": 12,
                "last_updated_utc": "2026-11-20T17:00:00",
            }
        if "AS total_incidents" in sql:
            return {
                "total_incidents": 107,
                "open_incidents": 3,
                "high_severity_incidents": 5,
                "last_incident_utc": "2026-11-20T16:30:00",
            }
        if "AS total_capabilities" in sql:
            return {
                "total_capabilities": 11,
                "learned_repair_count": 4,
                "knowledge_lesson_count": 7,
                "reusable_count": 11,
            }
        if "AS total_recovery_events" in sql:
            return {"total_recovery_events": 0}
        if "SELECT COUNT(*) AS total FROM dbo.Sys_Worker_Jobs" in sql:
            return {"total": 3324}
        if "SELECT COUNT(*) AS total FROM dbo.Sys_Worker_Incidents" in sql:
            return {"total": 107}
        if "SELECT COUNT(*) AS total FROM dbo.Sys_Worker_Capabilities" in sql:
            return {"total": 11}
        if "FROM dbo.Sys_Worker_Jobs" in sql and "WHERE JobID = %s" in sql:
            target = params[0] if params else ""
            for row in SAMPLE_JOB_ROWS:
                if row["JobID"] == target:
                    return dict(row)
            return None
        return None

    monkeypatch.setattr(C, "fetch_all_dict_readonly", fake_all)
    monkeypatch.setattr(C, "fetch_one_dict_readonly", fake_one)


# -----------------------------------------------------------------------------
# 1. PRUEBAS DE SEGURIDAD Y RBAC FAIL-CLOSED (401 / 403 / P1-2 / CROSS-SCOPE)
# -----------------------------------------------------------------------------

PROTECTED_GET_ENDPOINTS = [
    "/api/worker/console/dashboard",
    "/api/worker/console/jobs",
    "/api/worker/console/job/EDARSAHUB-BOS-TEST-ACTIVE-PREVIEW-1",
    "/api/worker/console/incidents",
    "/api/worker/console/capabilities",
    "/api/worker/console/jobs/results",
    "/api/worker/console/lifecycle/EDARSAHUB-BOS-TEST-ACTIVE-PREVIEW-1",
    "/api/worker/console/result/EDARSAHUB-BOS-TEST-ACTIVE-PREVIEW-1",
    "/api/worker/console/tablajerias/checklist",
    "/api/worker/console/audit",
]


def test_all_endpoints_reject_unauthenticated_401():
    client = _make_client()
    for ep in PROTECTED_GET_ENDPOINTS:
        resp = client.get(ep)
        assert resp.status_code == 401, f"{ep} debía retornar 401 sin token, retornó {resp.status_code}"
    resp_val = client.post("/api/worker/console/validate", json={})
    assert resp_val.status_code == 401


def test_invalid_jwt_rejected_401():
    client = _make_client()
    resp = client.get(
        "/api/worker/console/dashboard",
        headers={"Authorization": "Bearer not.a.valid.jwt.token"},
    )
    assert resp.status_code == 401


def test_revoked_session_p1_2_rejected_401(monkeypatch):
    import core.security as sec

    token = create_access_token(
        user_id="uuid-superadmin",
        email="superadmin@edarsa.com",
        role="SUPERADMIN",
        session_id="revoked-session-123",
    )
    monkeypatch.setattr(sec, "verify_token_session_active", AsyncMock(return_value=False))
    client = _make_client()
    resp = client.get(
        "/api/worker/console/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401
    assert "revocada" in str(resp.json().get("detail", "")).lower()


def test_non_admin_user_denied_403_on_all_endpoints(monkeypatch):
    monkeypatch.setattr(
        R,
        "get_current_user_dual",
        AsyncMock(return_value={"id": "u-basic", "email": "operador@edarsa.com", "role": "USUARIO"}),
    )
    monkeypatch.setattr(
        R,
        "_check_sql_worker_console_authority",
        lambda email: {"authorized": False, "is_superadmin": False, "reason": "NO_RBAC_AUTHORITY"},
    )
    client = _make_client()
    for ep in PROTECTED_GET_ENDPOINTS:
        resp = client.get(ep)
        assert resp.status_code == 403, f"{ep} debía denegar 403 a usuario sin RBAC_ADMIN"
    resp_val = client.post("/api/worker/console/validate", json={})
    assert resp_val.status_code == 403


def test_sql_rbac_error_fails_closed_403(monkeypatch):
    monkeypatch.setattr(
        R,
        "get_current_user_dual",
        AsyncMock(return_value={"id": "u-1", "email": "admin@edarsa.com", "role": "ADMIN"}),
    )

    def boom(*args, **kwargs):
        raise RuntimeError("SQL_DOWN")

    monkeypatch.setattr(R, "fetch_one_dict_readonly", boom)
    client = _make_client()
    resp = client.get("/api/worker/console/dashboard")
    assert resp.status_code == 403


def test_cross_empresa_and_cross_domain_denied_403(monkeypatch):
    _mock_sql_reads(monkeypatch)
    monkeypatch.setattr(
        R,
        "get_current_user_dual",
        AsyncMock(
            return_value={
                "id": "u-scoped",
                "email": "rbac_ops@edarsa.com",
                "role": "OPERADOR_RBAC",
                "empresa_id": "EMP_1",
                "allowed_bounded_contexts": ["WORKER_OPERATIONS"],
            }
        ),
    )
    monkeypatch.setattr(
        R,
        "_check_sql_worker_console_authority",
        lambda email: {"authorized": True, "is_superadmin": False, "reason": "SQL_EXPLICIT_PERMISSION:RBAC_ADMIN"},
    )
    client = _make_client()

    # Cross-empresa bloqueado
    r_emp = client.get("/api/worker/console/jobs?empresa_id=EMP_OTRA")
    assert r_emp.status_code == 403
    assert r_emp.json()["detail"]["error"] == "CROSS_EMPRESA_FORBIDDEN"

    # Cross-domain bloqueado en filtro
    r_dom = client.get("/api/worker/console/jobs?bounded_context=FINANZAS")
    assert r_dom.status_code == 403
    assert r_dom.json()["detail"]["error"] == "CROSS_DOMAIN_FORBIDDEN"

    # Cross-domain bloqueado en detalle de job (COMERCIAL != WORKER_OPERATIONS)
    r_job = client.get("/api/worker/console/job/EDARSAHUB-BOS-TEST-CERTIFIED-ONLY-2")
    assert r_job.status_code == 403

    # Cross-domain bloqueado en /result/{job_id} incluso si hubiera archivo en cola local
    r_res = client.get("/api/worker/console/result/EDARSAHUB-BOS-TEST-CERTIFIED-ONLY-2")
    assert r_res.status_code == 403
    assert r_res.json()["detail"]["error"] == "CROSS_DOMAIN_FORBIDDEN"

    # Mismo dominio y empresa permitido
    r_ok = client.get("/api/worker/console/jobs?empresa_id=EMP_1&bounded_context=WORKER_OPERATIONS")
    assert r_ok.status_code == 200


def test_operational_status_active_in_preview_and_canonical_reader_signature(monkeypatch, tmp_path):
    row_active = dict(SAMPLE_JOB_ROWS[0], OperationalValidationStatus="ACTIVE_IN_PREVIEW", PreviewActivated=1)
    serialized = C._serialize_job_row(row_active)
    assert serialized["operational_validated"] is True
    assert serialized["code_certified"] is True

    fake_results = tmp_path / "results"
    fake_results.mkdir(parents=True)
    result_file = fake_results / "EDARSAHUB-BOS-TEST-ACTIVE-PREVIEW-1.json"
    result_file.write_text('{"job_id": "EDARSAHUB-BOS-TEST-ACTIVE-PREVIEW-1"}', encoding="utf-8")

    seen_calls: List[tuple] = []

    class _FakeRead:
        terminal_result_valid = True
        payload = {
            "job_id": "EDARSAHUB-BOS-TEST-ACTIVE-PREVIEW-1",
            "status": "INTEGRATED",
            "certification": "CERTIFIED",
            "quality_gate": "PASS",
            "tests": "PASS",
            "blockers": [],
            "production_touched": False,
            "development_sha": "a" * 40,
        }

    def fake_reader(path, *, expected_job_id):
        seen_calls.append((Path(path), expected_job_id))
        return _FakeRead()

    _mock_sql_reads(monkeypatch)
    monkeypatch.setattr(C, "QUEUE_ROOT", tmp_path)
    monkeypatch.setattr(C, "read_canonical_result", fake_reader)
    detail = C.query_job_detail("EDARSAHUB-BOS-TEST-ACTIVE-PREVIEW-1")
    assert detail is not None
    assert len(seen_calls) == 1
    assert seen_calls[0][0] == result_file
    assert seen_calls[0][1] == "EDARSAHUB-BOS-TEST-ACTIVE-PREVIEW-1"
    assert detail["canonical_result"]["verdict"] == "PASS"


# -----------------------------------------------------------------------------
# 2. PRUEBAS SQL CANÓNICO, FILTROS, PAGINACIÓN, M1 Y SEPARACIÓN DE ETAPAS
# -----------------------------------------------------------------------------

def test_superadmin_dashboard_and_m1_history_reconciled(monkeypatch):
    captured: List[tuple] = []
    _mock_sql_reads(monkeypatch, captured_sql=captured)
    monkeypatch.setattr(
        R,
        "get_current_user_dual",
        AsyncMock(return_value={"id": "u-sa", "email": "superadmin@edarsa.com", "role": "SUPERADMIN"}),
    )
    monkeypatch.setattr(
        R,
        "_check_sql_worker_console_authority",
        lambda email: {"authorized": True, "is_superadmin": True, "reason": "SQL_SUPERADMIN:SUPERADMIN"},
    )
    client = _make_client()
    resp = client.get("/api/worker/console/dashboard")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "SQL_CANONICAL_EDARSAHUB_READONLY"
    assert body["sql_summary"]["jobs"]["total"] == 3324
    assert body["sql_summary"]["incidents"]["total"] == 107
    assert body["sql_summary"]["capabilities"]["total"] == 11
    assert body["sql_summary"]["jobs"]["production_touched"] == 0
    assert body["viewer"]["is_superadmin"] is True
    # Verificar que todas las queries son solo SELECT (cero DDL/DML)
    for sql, _ in captured:
        upper = sql.upper()
        for forbidden in ("INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER ", "TRUNCATE "):
            assert forbidden not in upper


def test_jobs_filters_pagination_and_stage_differentiation(monkeypatch):
    captured: List[tuple] = []
    _mock_sql_reads(monkeypatch, captured_sql=captured)
    monkeypatch.setattr(
        R,
        "get_current_user_dual",
        AsyncMock(return_value={"id": "u-sa", "email": "superadmin@edarsa.com", "role": "SUPERADMIN"}),
    )
    monkeypatch.setattr(
        R,
        "_check_sql_worker_console_authority",
        lambda email: {"authorized": True, "is_superadmin": True, "reason": "SQL_SUPERADMIN:SUPERADMIN"},
    )
    client = _make_client()
    resp = client.get(
        "/api/worker/console/jobs"
        "?q=TEST&source_job_id=SRC-JOB&project_id=EDARSAHUB&bounded_context=WORKER_OPERATIONS"
        "&lifecycle_stage=CERTIFIED&certification_status=CERTIFIED"
        "&operational_validation_status=PENDING_PREVIEW_VALIDATION"
        "&date_from=2026-11-01&date_to=2026-11-30&has_blockers=false&limit=25&offset=50"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3324
    assert data["limit"] == 25
    assert data["offset"] == 50
    assert len(data["items"]) == 2

    # Verificar diferenciación explícita CERTIFIED vs ACTIVE_IN_PREVIEW
    active_item = data["items"][0]
    cert_only_item = data["items"][1]
    assert active_item["lifecycle_stage"] == "ACTIVE_IN_PREVIEW"
    assert active_item["code_certified"] is True
    assert active_item["operational_validated"] is True
    assert cert_only_item["lifecycle_stage"] == "CERTIFIED"
    assert cert_only_item["code_certified"] is True
    assert cert_only_item["operational_validated"] is False

    # Verificar parametrización SQL (cero interpolación directa)
    assert any("OFFSET %s ROWS FETCH NEXT %s ROWS ONLY" in sql for sql, _ in captured)
    assert any(50 in params and 25 in params for _, params in captured)


def test_invalid_date_filter_returns_400(monkeypatch):
    _mock_sql_reads(monkeypatch)
    monkeypatch.setattr(
        R,
        "get_current_user_dual",
        AsyncMock(return_value={"id": "u-sa", "email": "superadmin@edarsa.com", "role": "SUPERADMIN"}),
    )
    monkeypatch.setattr(
        R,
        "_check_sql_worker_console_authority",
        lambda email: {"authorized": True, "is_superadmin": True, "reason": "SQL_SUPERADMIN:SUPERADMIN"},
    )
    client = _make_client()
    resp = client.get("/api/worker/console/jobs?date_from=NOT-A-DATE")
    assert resp.status_code == 400


def test_sql_outage_fails_closed_503(monkeypatch):
    def sql_down(*args, **kwargs):
        raise ConnectionError("SQL Server unreachable")

    monkeypatch.setattr(C, "fetch_one_dict_readonly", sql_down)
    monkeypatch.setattr(C, "fetch_all_dict_readonly", sql_down)
    monkeypatch.setattr(
        R,
        "get_current_user_dual",
        AsyncMock(return_value={"id": "u-sa", "email": "superadmin@edarsa.com", "role": "SUPERADMIN"}),
    )
    monkeypatch.setattr(
        R,
        "_check_sql_worker_console_authority",
        lambda email: {"authorized": True, "is_superadmin": True, "reason": "SQL_SUPERADMIN:SUPERADMIN"},
    )
    client = _make_client()
    for ep in ("/api/worker/console/dashboard", "/api/worker/console/jobs", "/api/worker/console/incidents", "/api/worker/console/capabilities"):
        resp = client.get(ep)
        assert resp.status_code == 503, f"{ep} debía fallar cerrado con 503 ante caída SQL"


def test_incidents_capabilities_and_audit_endpoints(monkeypatch):
    _mock_sql_reads(monkeypatch)
    monkeypatch.setattr(
        R,
        "get_current_user_dual",
        AsyncMock(return_value={"id": "u-sa", "email": "superadmin@edarsa.com", "role": "SUPERADMIN"}),
    )
    monkeypatch.setattr(
        R,
        "_check_sql_worker_console_authority",
        lambda email: {"authorized": True, "is_superadmin": True, "reason": "SQL_SUPERADMIN:SUPERADMIN"},
    )
    client = _make_client()

    r_inc = client.get("/api/worker/console/incidents?severity=HIGH")
    assert r_inc.status_code == 200
    assert r_inc.json()["total"] == 107
    assert r_inc.json()["items"][0]["incident_id"] == "INC-TEST-001"

    r_cap = client.get("/api/worker/console/capabilities?capability_kind=KNOWLEDGE_LESSON")
    assert r_cap.status_code == 200
    assert r_cap.json()["total"] == 11
    assert r_cap.json()["items"][0]["capability_code"] == "CAP_KNOWLEDGE_P1_2"

    r_aud = client.get("/api/worker/console/audit?tail=20")
    assert r_aud.status_code == 200
    assert "logs" in r_aud.json()
    assert "universal-worker-cert.log" in r_aud.json()["logs"]


def test_lifecycle_returns_presence_dict_and_list_plus_interpretation(monkeypatch):
    _mock_sql_reads(monkeypatch)
    monkeypatch.setattr(
        R,
        "get_current_user_dual",
        AsyncMock(return_value={"id": "u-sa", "email": "superadmin@edarsa.com", "role": "SUPERADMIN"}),
    )
    monkeypatch.setattr(
        R,
        "_check_sql_worker_console_authority",
        lambda email: {"authorized": True, "is_superadmin": True, "reason": "SQL_SUPERADMIN:SUPERADMIN"},
    )
    client = _make_client()
    resp = client.get("/api/worker/console/lifecycle/EDARSAHUB-BOS-TEST-ACTIVE-PREVIEW-1")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["presence"], dict)
    assert isinstance(body["presence_list"], list)
    assert body["sql_job"]["lifecycle_stage"] == "ACTIVE_IN_PREVIEW"


# -----------------------------------------------------------------------------
# 3. PROYECCIÓN INCREMENTAL SEGURA, IDEMPOTENTE Y NO BLOQUEANTE (FASE 5)
# -----------------------------------------------------------------------------

class _FakeCursor:
    def __init__(self, db_name: str = "EDARSAHUB", executed: Optional[List[tuple]] = None):
        self.db_name = db_name
        self.executed = executed if executed is not None else []
        self._last_sql = ""

    def execute(self, sql: str, params=None):
        self._last_sql = sql
        self.executed.append((sql, params))

    def fetchone(self):
        if "DB_NAME()" in self._last_sql:
            return {
                "server_name": "ns559627",
                "db_name": self.db_name,
                "login_name": "HRLectura",
                "db_user": "HRLectura",
            }
        return None


class _FakeConn:
    def __init__(self, db_name: str = "EDARSAHUB", executed: Optional[List[tuple]] = None):
        self.db_name = db_name
        self.executed = executed if executed is not None else []
        self.committed = 0
        self.rolled_back = 0
        self.closed = False

    def cursor(self, as_dict=False):
        return _FakeCursor(self.db_name, self.executed)

    def commit(self):
        self.committed += 1

    def rollback(self):
        self.rolled_back += 1

    def close(self):
        self.closed = True


def test_incremental_projection_idempotent_and_non_blocking(tmp_path):
    executed: List[tuple] = []
    result_payload = {
        "schema": "edarsahub.worker-job.v2",
        "job_id": "EDARSAHUB-BOS-INC-PROJ-1",
        "status": "INTEGRATED",
        "certification": "CERTIFIED",
        "quality_gate": "PASS",
        "tests": "PASS",
        "blockers": [],
        "production_touched": False,
        "percent_complete": 100,
        "development_sha": "a" * 40,
        "reconciliation_status": "RECONCILED_CERTIFIED",
    }

    # Ejecución idempotente 2 veces
    for _ in range(2):
        out = proj.project_single_job_best_effort(
            job_id="EDARSAHUB-BOS-INC-PROJ-1",
            result_payload=result_payload,
            published_commit="b" * 40,
            queue_root=tmp_path,
            connection_factory=lambda: _FakeConn("EDARSAHUB", executed),
        )
        assert out["projected"] is True
        assert out["database"] == "EDARSAHUB"
        assert out["production_touched"] is False

    sp_calls = [sql for sql, _ in executed if "sp_Worker_UpsertJobState" in sql]
    assert len(sp_calls) == 2

    # Base inesperada -> fail-closed sin lanzar excepción, registra pending
    bad_db_out = proj.project_single_job_best_effort(
        job_id="EDARSAHUB-BOS-INC-PROJ-BAD-DB",
        result_payload=result_payload,
        queue_root=tmp_path,
        connection_factory=lambda: _FakeConn("EDARSAHUB_PRODUCCION"),
    )
    assert bad_db_out["projected"] is False
    assert bad_db_out["pending_recorded"] is True
    assert "UNEXPECTED_DATABASE_FORBIDDEN" in bad_db_out["reason"]
    pending_file = tmp_path / "runtime" / "sql_projection_pending.json"
    assert pending_file.is_file()

    # production_touched=True -> rechazado fail-closed
    prod_payload = dict(result_payload, production_touched=True)
    prod_out = proj.project_single_job_best_effort(
        job_id="EDARSAHUB-BOS-INC-PROJ-PROD",
        result_payload=prod_payload,
        queue_root=tmp_path,
        connection_factory=lambda: _FakeConn("EDARSAHUB"),
    )
    assert prod_out["projected"] is False
    assert prod_out["reason"] == "PRODUCTION_POLICY_VIOLATION"


def test_publisher_incremental_projection_hook_uses_canonical_state_dir(monkeypatch, tmp_path):
    from tools.mirror_sync import universal_job_result_publisher as pub

    fake_env = tmp_path / "backend" / ".env"
    fake_env.parent.mkdir(parents=True)
    fake_env.write_text("# test marker only\n", encoding="utf-8")

    captured = {}

    def fake_project(**kwargs):
        captured.update(kwargs)
        return {"projected": True, "job_id": kwargs["job_id"], "production_touched": False}

    monkeypatch.setattr(pub, "ROOT", tmp_path)
    monkeypatch.setattr(pub, "STATE", tmp_path / ".git" / "universal-worker-queue")
    monkeypatch.setattr(proj, "project_single_job_best_effort", fake_project)

    pub._project_published_result_to_sql_best_effort(
        job_id="EDARSAHUB-BOS-INC-HOOK-R2",
        public_result={"job_id": "EDARSAHUB-BOS-INC-HOOK-R2", "certification": "CERTIFIED"},
        published_commit="a" * 40,
    )
    assert captured["job_id"] == "EDARSAHUB-BOS-INC-HOOK-R2"
    assert captured["published_commit"] == "a" * 40
    assert captured["queue_root"] == tmp_path / ".git" / "universal-worker-queue"


def test_dashboard_preferred_job_orphaned_ignores_historical_archive_and_detects_active_orphan(monkeypatch, tmp_path):
    _mock_sql_reads(monkeypatch)
    monkeypatch.setattr(C, "QUEUE_ROOT", tmp_path)
    monkeypatch.setattr(
        R,
        "get_current_user_dual",
        AsyncMock(return_value={"id": "u-sa", "email": "superadmin@edarsa.com", "role": "SUPERADMIN"}),
    )
    monkeypatch.setattr(
        R,
        "_check_sql_worker_console_authority",
        lambda email: {"authorized": True, "is_superadmin": True, "reason": "SQL_SUPERADMIN:SUPERADMIN"},
    )
    archive = tmp_path / "runtime" / "orphaned-preferred"
    (archive / "20260920T191607Z").mkdir(parents=True)
    (archive / "20260920T192100Z").mkdir(parents=True)

    client = _make_client()
    r1 = client.get("/api/worker/console/dashboard")
    assert r1.status_code == 200
    rt1 = r1.json()["runtime"]
    assert rt1["preferred_job"] is None
    assert rt1["preferred_job_orphaned"] is False
    assert rt1["orphaned_preferred_archive_count"] == 2

    # Si existe un preferred_job.json activo cuyo job_id no está en pending/processing -> True
    (tmp_path / "runtime" / "preferred_job.json").write_text(
        '{"job_id": "ORPHAN-ACTIVE-JOB-1", "expires_at_epoch": 9999999999}',
        encoding="utf-8",
    )
    r2 = client.get("/api/worker/console/dashboard")
    assert r2.status_code == 200
    assert r2.json()["runtime"]["preferred_job_orphaned"] is True


def test_lifecycle_and_result_reconcile_canonical_result_and_preview_validation(monkeypatch, tmp_path):
    _mock_sql_reads(monkeypatch)
    monkeypatch.setattr(C, "QUEUE_ROOT", tmp_path)
    monkeypatch.setattr(
        R,
        "get_current_user_dual",
        AsyncMock(return_value={"id": "u-sa", "email": "superadmin@edarsa.com", "role": "SUPERADMIN"}),
    )
    monkeypatch.setattr(
        R,
        "_check_sql_worker_console_authority",
        lambda email: {"authorized": True, "is_superadmin": True, "reason": "SQL_SUPERADMIN:SUPERADMIN"},
    )

    jid = "EDARSAHUB-BOS-TEST-ACTIVE-PREVIEW-1"
    (tmp_path / "results").mkdir(parents=True)
    (tmp_path / "results" / f"{jid}.json").write_text(
        '{"job_id": "EDARSAHUB-BOS-TEST-ACTIVE-PREVIEW-1", "status": "INTEGRATED", "certification": "PENDING_AUDIT_EVIDENCE"}',
        encoding="utf-8",
    )
    (tmp_path / "preview_validations").mkdir(parents=True)
    (tmp_path / "preview_validations" / f"{jid}.json").write_text(
        '{"schema": "edarsahub.preview-operational-validation.v1", "job_id": "EDARSAHUB-BOS-TEST-ACTIVE-PREVIEW-1", "commit_sha": "'
        + ("a" * 40)
        + '", "preview_activated": true, "operational_tests": "PASS", "functional_result": "PASS", "validated_at_utc": "2026-11-21T02:30:00Z", "production_touched": false}',
        encoding="utf-8",
    )

    class _FakeRead:
        terminal_result_valid = True
        payload = {
            "schema": "edarsahub.worker-result.v1",
            "completed_at_utc": "2026-11-21T02:25:00Z",
            "job_id": jid,
            "percent_complete": 100,
            "work_completion": "COMPLETE",
            "status": "INTEGRATED",
            "certification": "CERTIFIED",
            "quality_gate": "PASS",
            "tests": "PASS",
            "blockers": [],
            "production_touched": False,
            "development_sha": "a" * 40,
            "git_sync_status": "CERTIFIED_GIT_SYNC",
        }

    monkeypatch.setattr(C, "read_canonical_result", lambda p, *, expected_job_id: _FakeRead())

    client = _make_client()
    r_lc = client.get(f"/api/worker/console/lifecycle/{jid}")
    assert r_lc.status_code == 200
    assert r_lc.json()["interpretation"]["verdict"] == "PASS"
    assert r_lc.json()["interpretation"]["lifecycle_stage"] == "ACTIVE_IN_PREVIEW"

    r_res = client.get(f"/api/worker/console/result/{jid}")
    assert r_res.status_code == 200
    assert r_res.json()["interpretation"]["verdict"] == "PASS"
    assert r_res.json()["interpretation"]["lifecycle_stage"] == "ACTIVE_IN_PREVIEW"


# -----------------------------------------------------------------------------
# 4. CONTRATO ESTÁTICO DEL FRONTEND WorkerConsole.jsx
# -----------------------------------------------------------------------------

def test_frontend_worker_console_contract_and_bugfixes():
    jsx = (ROOT / "frontend" / "src" / "pages" / "WorkerConsole.jsx").read_text(encoding="utf-8")
    # Bug histórico eliminado: no hacer (data.presence || []).map directo sobre dict
    assert "(data.presence || []).map" not in jsx
    # Soporta presencia como lista o dict
    assert "data?.presence_list" in jsx
    # Soporta data.interpretation || data.result
    assert "data?.interpretation || data?.result" in jsx
    # Soporta vistas SQL canónicas y separación CERTIFIED vs ACTIVE_IN_PREVIEW
    for token in (
        "ACTIVE_IN_PREVIEW",
        "CERTIFIED",
        "/api/worker/console",
        "/incidents",
        "/capabilities",
        "dbo.Sys_Worker_Jobs",
        "HTTP 401",
        "HTTP 403",
        "getToken",
    ):
        assert token in jsx, f"Token esperado faltante en WorkerConsole.jsx: {token}"
