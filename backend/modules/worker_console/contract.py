"""
Contrato del Universal Worker Console + Repositorio SQL Canónico (SOLO LECTURA).

GATE-M2 (Cierre M-08):
- Fuente de verdad histórica y operativa: SQL Server EDARSAHUB (tablas certificadas GATE-M1
  dbo.Sys_Worker_Jobs, dbo.Sys_Worker_Incidents, dbo.Sys_Worker_RecoveryEvents,
  dbo.Sys_Worker_Capabilities) vía conexión read-only fail-closed (HRLectura).
- Intérprete canónico: delega a tools.mirror_sync.worker_result_status y
  tools.mirror_sync.worker_result_integrity (sin lógica heurística paralela).
- No escribe archivos, no ejecuta DDL/DML, no consulta MongoDB, no toca Producción.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from core.sql_first.db import fetch_all_dict_readonly, fetch_one_dict_readonly
from tools.mirror_sync.worker_result_integrity import validate_terminal_result_payload
from tools.mirror_sync.worker_result_reader import read_canonical_result
from tools.mirror_sync.worker_result_status import build_differentiated_evidence

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
REQUESTS_DIR = REPO_ROOT / "worker" / "requests"
QUEUE_ROOT = REPO_ROOT / ".git" / "universal-worker-queue"

LIFECYCLE_STATES: List[str] = [
    "pending",
    "processing",
    "results",
    "done",
    "published",
    "rejected",
]

SCHEMA_ID = "edarsahub.worker-job.v2"
VALID_MODES = {"READ_ONLY", "MUTATION", "FRONTEND_BUILD_CERTIFICATION", "OPERATIONAL"}

CANONICAL_LIFECYCLE_STAGES = frozenset(
    {
        "DRAFT",
        "SUBMITTED",
        "INTEGRATED",
        "CERTIFIED",
        "ACTIVE_IN_PREVIEW",
        "BLOCKED",
        "FAILED",
        "REJECTED",
        "INVALID",
    }
)

_CERTIFIED_VALUES = frozenset(
    {
        "CERTIFIED",
        "CERTIFIED_READ_ONLY",
        "CERTIFIED_OPERATIONAL",
        "CERTIFIED_FRONTEND_BUILD",
    }
)

_FAIL_STATUSES = frozenset({"FAILED", "BLOCKED", "REJECTED", "INVALID", "ERROR"})


class WorkerConsoleSqlError(RuntimeError):
    """Error fail-closed al consultar las tablas canónicas dbo.Sys_Worker_* en SQL Server."""


def state_dir(state: str) -> Optional[Path]:
    """Devuelve el Path de una carpeta de estado válida de la cola local, o None."""
    if state == "requests":
        return REQUESTS_DIR
    if state == "runtime":
        return QUEUE_ROOT / "runtime"
    if state in LIFECYCLE_STATES:
        return QUEUE_ROOT / state
    return None


def _safe_json(path: Path) -> Optional[Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _parse_marker(text: str) -> Optional[Dict[str, Any]]:
    """Los archivos de published/ son marcadores 'clave=valor' por línea."""
    out: Dict[str, Any] = {}
    for line in text.splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("{"):
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip()
    return out or None


def read_json_file(path: Path) -> Optional[Any]:
    doc = _safe_json(path)
    if doc is not None:
        return doc
    try:
        return _parse_marker(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def extract_job(doc: Any) -> Dict[str, Any]:
    """Un archivo puede ser el job directo o un envoltorio {'job': {...}}."""
    if isinstance(doc, dict) and isinstance(doc.get("job"), dict):
        return doc["job"]
    if isinstance(doc, dict):
        return doc
    return {}


def validate_job(doc: Any) -> Dict[str, Any]:
    """Valida el contrato edarsahub.worker-job.v2 en memoria SIN escribir nada."""
    errors: List[str] = []
    warnings: List[str] = []
    job = extract_job(doc)

    if job.get("schema") != SCHEMA_ID:
        errors.append(f"schema debe ser '{SCHEMA_ID}'")
    if not job.get("job_id"):
        errors.append("job_id es obligatorio")
    mode = job.get("mode")
    if mode not in VALID_MODES:
        errors.append(f"mode debe ser uno de {sorted(VALID_MODES)}")
    if not job.get("objective"):
        warnings.append("objective vacío")

    actions = job.get("actions", None)
    if mode == "READ_ONLY" and actions not in ([], None):
        errors.append("READ_ONLY debe tener actions=[] (sin mutaciones)")
    if job.get("production_allowed", False) is True:
        errors.append("production_allowed=true no está permitido (No tocar Producción)")

    tgt = job.get("target_branch")
    if tgt and str(tgt).lower() in {"main", "master", "produccion", "production", "prod", "edarsahub_produccion"}:
        errors.append(f"target_branch '{tgt}' apunta a Producción (prohibido)")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "job_id": job.get("job_id"),
        "mode": mode,
        "schema": job.get("schema"),
    }


def _parse_blockers(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item) for item in raw if item is not None and str(item).strip()]
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item) for item in parsed if item is not None and str(item).strip()]
        except Exception:
            pass
        return [text]
    return [str(raw)]


def interpret_result(doc: Any) -> Dict[str, Any]:
    """Interpreta un resultado delegando al contrato canónico worker_result_status.

    Elimina heurísticas paralelas y separa explícitamente SUBMITTED / INTEGRATED /
    CERTIFIED / ACTIVE_IN_PREVIEW sin inventar validación operativa en Preview.
    """
    root = doc if isinstance(doc, dict) else {}
    job_id = str(root.get("job_id") or extract_job(root).get("job_id") or "").strip() or None

    certification = root.get("certification")
    cert_upper = str(certification or "").strip().upper()
    quality_gate = root.get("quality_gate")
    qg_upper = str(quality_gate or "").strip().upper()
    status_upper = str(root.get("status") or "").strip().upper()
    blockers = _parse_blockers(root.get("blockers"))
    blocker_count = len(blockers)
    production_touched = root.get("production_touched")

    files_changed = root.get("files_changed")
    if isinstance(files_changed, list):
        files_count: Optional[int] = len(files_changed)
    elif isinstance(files_changed, int) and not isinstance(files_changed, bool):
        files_count = files_changed
    else:
        files_count = None

    commit_sha = (
        root.get("certified_source_sha")
        or root.get("development_sha")
        or root.get("candidate_sha")
        or root.get("commit_sha")
    )

    terminal_valid = False
    if root and job_id:
        try:
            validate_terminal_result_payload(root, expected_job_id=job_id)
            terminal_valid = True
        except ValueError:
            terminal_valid = False
    elif cert_upper in _CERTIFIED_VALUES and qg_upper == "PASS" and blocker_count == 0 and production_touched is not True:
        # Compatibilidad con resultados parciales o tests unitarios mínimos
        terminal_valid = True

    diff_ev = build_differentiated_evidence(
        root,
        job_id=job_id or "UNKNOWN",
        terminal_valid=terminal_valid,
        commit_sha=str(commit_sha) if commit_sha else None,
        preview_evidence=root.get("operational_validation") if isinstance(root.get("operational_validation"), dict) else None,
    )

    if (
        production_touched is True
        or blocker_count > 0
        or qg_upper in _FAIL_STATUSES
        or status_upper in _FAIL_STATUSES
        or cert_upper in {"NOT_CERTIFIED", "REJECTED", "INVALID"}
    ):
        verdict = "FAIL"
    elif cert_upper in _CERTIFIED_VALUES and (qg_upper in {"PASS", ""} or qg_upper == "PASS"):
        verdict = "PASS"
    elif cert_upper == "PENDING_AUDIT_EVIDENCE":
        verdict = "PENDING"
    else:
        verdict = "UNKNOWN"

    return {
        "verdict": verdict,
        "certification": certification,
        "quality_gate": quality_gate,
        "status": root.get("status"),
        "tests": root.get("tests"),
        "reconciliation_status": root.get("reconciliation_status"),
        "percent_complete": root.get("percent_complete"),
        "lifecycle_stage": diff_ev["lifecycle_stage"],
        "code_certified": diff_ev["code_certified"],
        "operational_validated": diff_ev["operational_validated"],
        "operational_validation_status": diff_ev["operational_validation_status"],
        "evidence_breakdown": diff_ev["evidence_breakdown"],
        "blockers": blockers,
        "blocker_count": blocker_count,
        "production_touched": production_touched,
        "files_changed": files_changed if isinstance(files_changed, list) else None,
        "files_changed_count": files_count,
        "development_commit_sha": commit_sha,
        "published_result_commit_sha": root.get("published_result_commit"),
        "result_sha256": root.get("published_result_sha256") or root.get("result_sha256"),
        "attestation_sha256": root.get("attestation_sha256"),
        "summary_es": root.get("summary_es"),
        "next_allowed_step": root.get("next_allowed_step"),
        "job_id": job_id,
    }


# =============================================================================
# REPOSITORIO SQL CANÓNICO SOLO LECTURA (dbo.Sys_Worker_* vía HRLectura)
# =============================================================================

def _json_safe_value(val: Any) -> Any:
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc).isoformat()
        return val.astimezone(timezone.utc).isoformat()
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")
    return val


def _serialize_job_row(row: Dict[str, Any]) -> Dict[str, Any]:
    clean = {k: _json_safe_value(v) for k, v in row.items()}
    blockers = _parse_blockers(clean.get("BlockersJson"))
    stage = str(clean.get("LifecycleStage") or "SUBMITTED").upper()
    cert = str(clean.get("CertificationStatus") or "NOT_CERTIFIED").upper()
    op_status = str(clean.get("OperationalValidationStatus") or "PENDING_PREVIEW_VALIDATION").upper()
    preview_activated = bool(clean.get("PreviewActivated"))
    code_certified = cert in _CERTIFIED_VALUES
    operational_validated = preview_activated and op_status in {"ACTIVE_IN_PREVIEW", "VALIDATED_IN_PREVIEW"}

    return {
        "job_id": clean.get("JobID"),
        "schema_version": clean.get("SchemaVersion"),
        "source_job_id": clean.get("SourceJobID"),
        "project_id": clean.get("ProjectID"),
        "bounded_context": clean.get("BoundedContext"),
        "capability_code": clean.get("CapabilityCode"),
        "mode": clean.get("Mode"),
        "objective": clean.get("Objective"),
        "priority_class": clean.get("PriorityClass"),
        "requester_usuario_id": clean.get("RequesterUsuarioID"),
        "requester_email": clean.get("RequesterEmail"),
        "requester_source": clean.get("RequesterSource"),
        "owner_agent_or_dev": clean.get("OwnerAgentOrDev"),
        "chain_id": clean.get("ChainID"),
        "gate_id": clean.get("GateID"),
        "depends_on_job_id": clean.get("DependsOnJobID"),
        "lifecycle_stage": stage,
        "execution_status": clean.get("ExecutionStatus"),
        "quality_gate": clean.get("QualityGate"),
        "tests_status": clean.get("TestsStatus"),
        "integration_status": clean.get("IntegrationStatus"),
        "git_sync_status": clean.get("GitSyncStatus"),
        "certification_status": cert,
        "code_certified": code_certified,
        "operational_validation_status": op_status,
        "preview_activated": preview_activated,
        "operational_validated": operational_validated,
        "operational_tests": clean.get("OperationalTests"),
        "functional_result": clean.get("FunctionalResult"),
        "terminal_result_valid": bool(clean.get("TerminalResultValid")),
        "percent_complete": int(clean.get("PercentComplete") or 0),
        "development_commit_sha": clean.get("DevelopmentCommitSHA"),
        "published_result_commit_sha": clean.get("PublishedResultCommitSHA"),
        "result_sha256": clean.get("ResultSHA256"),
        "attestation_sha256": clean.get("AttestationSHA256"),
        "production_touched": bool(clean.get("ProductionTouched")),
        "recovery_attempts": int(clean.get("RecoveryAttempts") or 0),
        "blockers": blockers,
        "blocker_count": len(blockers),
        "next_recommended_action": clean.get("NextRecommendedAction"),
        "reconciliation_status": clean.get("ReconciliationStatus"),
        "provenance_source": clean.get("ProvenanceSource"),
        "submitted_at_utc": clean.get("SubmittedAtUtc"),
        "started_at_utc": clean.get("StartedAtUtc"),
        "completed_at_utc": clean.get("CompletedAtUtc"),
        "published_at_utc": clean.get("PublishedAtUtc"),
        "updated_at_utc": clean.get("UpdatedAtUtc"),
        "evidence_breakdown": {
            "quality_gate": clean.get("QualityGate") or "UNKNOWN",
            "tests": clean.get("TestsStatus") or "UNKNOWN",
            "git_sync": clean.get("GitSyncStatus") or "UNVERIFIED",
            "code_certification": cert,
            "preview_activation": "ACTIVE_IN_PREVIEW" if operational_validated else op_status,
            "operational_tests": clean.get("OperationalTests") or "NOT_RUN",
            "functional_result": clean.get("FunctionalResult") or "UNVERIFIED",
        },
    }


def _serialize_incident_row(row: Dict[str, Any]) -> Dict[str, Any]:
    clean = {k: _json_safe_value(v) for k, v in row.items()}
    return {
        "incident_id": clean.get("IncidentID"),
        "incident_category": clean.get("IncidentCategory"),
        "error_class": clean.get("ErrorClass"),
        "severity": clean.get("Severity"),
        "incident_state": clean.get("IncidentState"),
        "source_job_id": clean.get("SourceJobID"),
        "repair_job_id": clean.get("RepairJobID"),
        "project_id": clean.get("ProjectID"),
        "bounded_context": clean.get("BoundedContext"),
        "problem_signature": clean.get("ProblemSignature"),
        "blocker_signature": clean.get("BlockerSignature"),
        "capability_code": clean.get("CapabilityCode"),
        "root_cause": clean.get("RootCause"),
        "impact_summary": clean.get("ImpactSummary"),
        "owner_email": clean.get("OwnerEmail"),
        "evidence_ref": clean.get("EvidenceRef"),
        "recommended_action": clean.get("RecommendedAction"),
        "recovery_attempts": int(clean.get("RecoveryAttempts") or 0),
        "cooldown_until_utc": clean.get("CooldownUntilUtc"),
        "alert_notified_at_utc": clean.get("AlertNotifiedAtUtc"),
        "production_touched": bool(clean.get("ProductionTouched")),
        "created_at_utc": clean.get("CreatedAtUtc"),
        "updated_at_utc": clean.get("UpdatedAtUtc"),
    }


def _serialize_recovery_row(row: Dict[str, Any]) -> Dict[str, Any]:
    clean = {k: _json_safe_value(v) for k, v in row.items()}
    detail_raw = clean.get("DetailJson")
    detail_parsed: Any = detail_raw
    if isinstance(detail_raw, str) and detail_raw.strip():
        try:
            detail_parsed = json.loads(detail_raw)
        except Exception:
            detail_parsed = detail_raw
    return {
        "recovery_event_id": clean.get("RecoveryEventID"),
        "incident_id": clean.get("IncidentID"),
        "job_id": clean.get("JobID"),
        "action_taken": clean.get("ActionTaken"),
        "outcome": clean.get("Outcome"),
        "policy_tier": clean.get("PolicyTier"),
        "detail": detail_parsed,
        "production_touched": bool(clean.get("ProductionTouched")),
        "occurred_at_utc": clean.get("OccurredAtUtc"),
    }


def _serialize_capability_row(row: Dict[str, Any]) -> Dict[str, Any]:
    clean = {k: _json_safe_value(v) for k, v in row.items()}
    return {
        "capability_code": clean.get("CapabilityCode"),
        "capability_kind": clean.get("CapabilityKind"),
        "problem_signature": clean.get("ProblemSignature"),
        "allowed_modes": clean.get("AllowedModes"),
        "bounded_context_rule": clean.get("BoundedContextRule"),
        "reusable": bool(clean.get("Reusable")),
        "source_job_id": clean.get("SourceJobID"),
        "certified_repair_job_id": clean.get("CertifiedRepairJobID"),
        "certified_commit_sha": clean.get("CertifiedCommitSHA"),
        "certification_status": clean.get("CertificationStatus"),
        "operational_validation_status": clean.get("OperationalValidationStatus"),
        "root_cause": clean.get("RootCause"),
        "prevention_rule": clean.get("PreventionRule"),
        "production_touched": bool(clean.get("ProductionTouched")),
        "updated_at_utc": clean.get("UpdatedAtUtc"),
    }


def _parse_iso_utc_filter(value: Optional[str], field_name: str) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        normalized = text.replace("Z", "+00:00")
        if len(normalized) == 10 and normalized[4] == "-" and normalized[7] == "-":
            dt = datetime.fromisoformat(f"{normalized}T00:00:00+00:00")
        else:
            dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    except ValueError as exc:
        raise ValueError(f"Fecha inválida en {field_name}: '{text}' (use ISO-8601 YYYY-MM-DD)") from exc


def _run_readonly_all(sql: str, params: Optional[Sequence[Any]] = None) -> List[Dict[str, Any]]:
    try:
        rows = fetch_all_dict_readonly(sql, list(params) if params else [])
        return list(rows or [])
    except Exception as exc:
        logger.error("[WORKER_CONSOLE_SQL] Error en consulta read-only: %s", exc)
        raise WorkerConsoleSqlError(f"SQL_READONLY_QUERY_FAILED:{type(exc).__name__}") from exc


def _run_readonly_one(sql: str, params: Optional[Sequence[Any]] = None) -> Optional[Dict[str, Any]]:
    try:
        return fetch_one_dict_readonly(sql, list(params) if params else [])
    except Exception as exc:
        logger.error("[WORKER_CONSOLE_SQL] Error en consulta puntual read-only: %s", exc)
        raise WorkerConsoleSqlError(f"SQL_READONLY_QUERY_FAILED:{type(exc).__name__}") from exc


def query_dashboard_summary(
    *,
    allowed_bounded_contexts: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Resumen ejecutivo y operativo desde las 4 tablas canónicas dbo.Sys_Worker_*."""
    where_sql = ""
    params: List[Any] = []
    if allowed_bounded_contexts:
        placeholders = ", ".join(["%s"] * len(allowed_bounded_contexts))
        where_sql = f" WHERE BoundedContext IN ({placeholders})"
        params = [str(c).strip() for c in allowed_bounded_contexts]

    totals_row = _run_readonly_one(
        f"""
        SELECT
            COUNT(*) AS total_jobs,
            SUM(CASE WHEN LifecycleStage = N'ACTIVE_IN_PREVIEW' THEN 1 ELSE 0 END) AS active_in_preview_count,
            SUM(CASE WHEN LifecycleStage = N'CERTIFIED' THEN 1 ELSE 0 END) AS certified_count,
            SUM(CASE WHEN LifecycleStage = N'INTEGRATED' THEN 1 ELSE 0 END) AS integrated_count,
            SUM(CASE WHEN LifecycleStage = N'SUBMITTED' THEN 1 ELSE 0 END) AS submitted_count,
            SUM(CASE WHEN LifecycleStage IN (N'BLOCKED', N'FAILED', N'REJECTED', N'INVALID') THEN 1 ELSE 0 END) AS error_or_blocked_count,
            SUM(CASE WHEN ProductionTouched = 1 THEN 1 ELSE 0 END) AS production_touched_count,
            SUM(CASE WHEN PreviewActivated = 1 AND OperationalValidationStatus IN (N'ACTIVE_IN_PREVIEW', N'VALIDATED_IN_PREVIEW') THEN 1 ELSE 0 END) AS preview_validated_count,
            MAX(UpdatedAtUtc) AS last_updated_utc
        FROM dbo.Sys_Worker_Jobs
        {where_sql}
        """,
        params,
    ) or {}

    by_stage_rows = _run_readonly_all(
        f"""
        SELECT LifecycleStage AS lifecycle_stage, COUNT(*) AS total
        FROM dbo.Sys_Worker_Jobs
        {where_sql}
        GROUP BY LifecycleStage
        ORDER BY COUNT(*) DESC
        """,
        params,
    )

    by_cert_rows = _run_readonly_all(
        f"""
        SELECT CertificationStatus AS certification_status, COUNT(*) AS total
        FROM dbo.Sys_Worker_Jobs
        {where_sql}
        GROUP BY CertificationStatus
        ORDER BY COUNT(*) DESC
        """,
        params,
    )

    by_domain_rows = _run_readonly_all(
        f"""
        SELECT TOP 20 BoundedContext AS bounded_context, COUNT(*) AS total
        FROM dbo.Sys_Worker_Jobs
        {where_sql}
        GROUP BY BoundedContext
        ORDER BY COUNT(*) DESC
        """,
        params,
    )

    inc_where = ""
    inc_params: List[Any] = []
    if allowed_bounded_contexts:
        placeholders = ", ".join(["%s"] * len(allowed_bounded_contexts))
        inc_where = f" WHERE BoundedContext IN ({placeholders})"
        inc_params = [str(c).strip() for c in allowed_bounded_contexts]

    inc_totals = _run_readonly_one(
        f"""
        SELECT
            COUNT(*) AS total_incidents,
            SUM(CASE WHEN UPPER(ISNULL(IncidentState, N'')) NOT IN (N'RESOLVED', N'CLOSED', N'CERTIFIED') THEN 1 ELSE 0 END) AS open_incidents,
            SUM(CASE WHEN UPPER(ISNULL(Severity, N'')) IN (N'CRITICAL', N'HIGH', N'P0', N'P1') THEN 1 ELSE 0 END) AS high_severity_incidents,
            MAX(UpdatedAtUtc) AS last_incident_utc
        FROM dbo.Sys_Worker_Incidents
        {inc_where}
        """,
        inc_params,
    ) or {}

    cap_totals = _run_readonly_one(
        """
        SELECT
            COUNT(*) AS total_capabilities,
            SUM(CASE WHEN CapabilityKind = N'LEARNED_REPAIR' THEN 1 ELSE 0 END) AS learned_repair_count,
            SUM(CASE WHEN CapabilityKind = N'KNOWLEDGE_LESSON' THEN 1 ELSE 0 END) AS knowledge_lesson_count,
            SUM(CASE WHEN Reusable = 1 THEN 1 ELSE 0 END) AS reusable_count
        FROM dbo.Sys_Worker_Capabilities
        """
    ) or {}

    rec_totals = _run_readonly_one(
        """
        SELECT COUNT(*) AS total_recovery_events
        FROM dbo.Sys_Worker_RecoveryEvents
        """
    ) or {}

    return {
        "source": "SQL_CANONICAL_EDARSAHUB_READONLY",
        "tables": [
            "dbo.Sys_Worker_Jobs",
            "dbo.Sys_Worker_Incidents",
            "dbo.Sys_Worker_RecoveryEvents",
            "dbo.Sys_Worker_Capabilities",
        ],
        "jobs": {
            "total": int(totals_row.get("total_jobs") or 0),
            "active_in_preview": int(totals_row.get("active_in_preview_count") or 0),
            "certified": int(totals_row.get("certified_count") or 0),
            "integrated": int(totals_row.get("integrated_count") or 0),
            "submitted": int(totals_row.get("submitted_count") or 0),
            "error_or_blocked": int(totals_row.get("error_or_blocked_count") or 0),
            "preview_validated": int(totals_row.get("preview_validated_count") or 0),
            "production_touched": int(totals_row.get("production_touched_count") or 0),
            "last_updated_utc": _json_safe_value(totals_row.get("last_updated_utc")),
            "by_lifecycle_stage": {
                str(r.get("lifecycle_stage") or "UNKNOWN"): int(r.get("total") or 0)
                for r in by_stage_rows
            },
            "by_certification_status": {
                str(r.get("certification_status") or "UNKNOWN"): int(r.get("total") or 0)
                for r in by_cert_rows
            },
            "by_bounded_context": [
                {
                    "bounded_context": str(r.get("bounded_context") or "UNSPECIFIED"),
                    "total": int(r.get("total") or 0),
                }
                for r in by_domain_rows
            ],
        },
        "incidents": {
            "total": int(inc_totals.get("total_incidents") or 0),
            "open": int(inc_totals.get("open_incidents") or 0),
            "high_severity": int(inc_totals.get("high_severity_incidents") or 0),
            "last_updated_utc": _json_safe_value(inc_totals.get("last_incident_utc")),
        },
        "capabilities": {
            "total": int(cap_totals.get("total_capabilities") or 0),
            "learned_repair": int(cap_totals.get("learned_repair_count") or 0),
            "knowledge_lesson": int(cap_totals.get("knowledge_lesson_count") or 0),
            "reusable": int(cap_totals.get("reusable_count") or 0),
        },
        "recovery_events": {
            "total": int(rec_totals.get("total_recovery_events") or 0),
        },
    }


def query_jobs(
    *,
    q: Optional[str] = None,
    job_id: Optional[str] = None,
    source_job_id: Optional[str] = None,
    project_id: Optional[str] = None,
    bounded_context: Optional[str] = None,
    lifecycle_stage: Optional[str] = None,
    certification_status: Optional[str] = None,
    operational_validation_status: Optional[str] = None,
    reconciliation_status: Optional[str] = None,
    has_blockers: Optional[bool] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    allowed_bounded_contexts: Optional[Sequence[str]] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """Consulta paginada y filtrable sobre dbo.Sys_Worker_Jobs (100% parametrizada)."""
    clauses: List[str] = []
    params: List[Any] = []

    if allowed_bounded_contexts:
        placeholders = ", ".join(["%s"] * len(allowed_bounded_contexts))
        clauses.append(f"BoundedContext IN ({placeholders})")
        params.extend(str(c).strip() for c in allowed_bounded_contexts)

    if job_id and job_id.strip():
        clauses.append("JobID LIKE %s")
        params.append(f"%{job_id.strip()}%")

    if q and q.strip():
        term = f"%{q.strip()}%"
        clauses.append("(JobID LIKE %s OR ISNULL(SourceJobID, N'') LIKE %s OR ISNULL(Objective, N'') LIKE %s OR ISNULL(CapabilityCode, N'') LIKE %s)")
        params.extend([term, term, term, term])

    if source_job_id and source_job_id.strip():
        clauses.append("ISNULL(SourceJobID, N'') LIKE %s")
        params.append(f"%{source_job_id.strip()}%")

    if project_id and project_id.strip():
        clauses.append("UPPER(ISNULL(ProjectID, N'')) = UPPER(%s)")
        params.append(project_id.strip())

    if bounded_context and bounded_context.strip():
        clauses.append("UPPER(ISNULL(BoundedContext, N'')) = UPPER(%s)")
        params.append(bounded_context.strip())

    if lifecycle_stage and lifecycle_stage.strip():
        clauses.append("UPPER(ISNULL(LifecycleStage, N'')) = UPPER(%s)")
        params.append(lifecycle_stage.strip())

    if certification_status and certification_status.strip():
        clauses.append("UPPER(ISNULL(CertificationStatus, N'')) = UPPER(%s)")
        params.append(certification_status.strip())

    if operational_validation_status and operational_validation_status.strip():
        clauses.append("UPPER(ISNULL(OperationalValidationStatus, N'')) = UPPER(%s)")
        params.append(operational_validation_status.strip())

    if reconciliation_status and reconciliation_status.strip():
        clauses.append("UPPER(ISNULL(ReconciliationStatus, N'')) = UPPER(%s)")
        params.append(reconciliation_status.strip())

    if has_blockers is True:
        clauses.append("BlockersJson IS NOT NULL AND LTRIM(RTRIM(BlockersJson)) NOT IN (N'', N'[]')")
    elif has_blockers is False:
        clauses.append("(BlockersJson IS NULL OR LTRIM(RTRIM(BlockersJson)) IN (N'', N'[]'))")

    parsed_from = _parse_iso_utc_filter(date_from, "date_from")
    parsed_to = _parse_iso_utc_filter(date_to, "date_to")
    if parsed_from:
        clauses.append("COALESCE(PublishedAtUtc, CompletedAtUtc, SubmittedAtUtc, UpdatedAtUtc) >= TRY_CONVERT(DATETIME2(3), %s)")
        params.append(parsed_from)
    if parsed_to:
        clauses.append("COALESCE(PublishedAtUtc, CompletedAtUtc, SubmittedAtUtc, UpdatedAtUtc) <= TRY_CONVERT(DATETIME2(3), %s)")
        params.append(parsed_to)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    count_row = _run_readonly_one(
        f"SELECT COUNT(*) AS total FROM dbo.Sys_Worker_Jobs {where_sql}",
        params,
    ) or {}
    total = int(count_row.get("total") or 0)

    safe_limit = max(1, min(int(limit), 200))
    safe_offset = max(0, int(offset))

    rows = _run_readonly_all(
        f"""
        SELECT
            JobID, SchemaVersion, SourceJobID, ProjectID, BoundedContext,
            CapabilityCode, Mode, Objective, PriorityClass,
            RequesterUsuarioID, RequesterEmail, RequesterSource,
            OwnerAgentOrDev, ChainID, GateID, DependsOnJobID,
            LifecycleStage, ExecutionStatus, QualityGate, TestsStatus,
            IntegrationStatus, GitSyncStatus, CertificationStatus,
            OperationalValidationStatus, PreviewActivated, OperationalTests,
            FunctionalResult, TerminalResultValid, PercentComplete,
            DevelopmentCommitSHA, PublishedResultCommitSHA, ResultSHA256,
            AttestationSHA256, ProductionTouched, RecoveryAttempts,
            BlockersJson, NextRecommendedAction, ReconciliationStatus,
            ProvenanceSource, SubmittedAtUtc, StartedAtUtc, CompletedAtUtc,
            PublishedAtUtc, UpdatedAtUtc
        FROM dbo.Sys_Worker_Jobs
        {where_sql}
        ORDER BY COALESCE(PublishedAtUtc, CompletedAtUtc, SubmittedAtUtc, UpdatedAtUtc) DESC, JobID DESC
        OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
        """,
        [*params, safe_offset, safe_limit],
    )

    return {
        "source": "SQL_CANONICAL_EDARSAHUB_READONLY",
        "total": total,
        "limit": safe_limit,
        "offset": safe_offset,
        "items": [_serialize_job_row(r) for r in rows],
    }


def query_job_detail(
    job_id: str,
    *,
    allowed_bounded_contexts: Optional[Sequence[str]] = None,
) -> Optional[Dict[str, Any]]:
    """Detalle completo de un job combinando SQL canónico + incidentes + recovery + resultado."""
    clean_id = str(job_id or "").strip()
    if not clean_id:
        return None

    row = _run_readonly_one(
        """
        SELECT
            JobID, SchemaVersion, SourceJobID, ProjectID, BoundedContext,
            CapabilityCode, Mode, Objective, PriorityClass,
            RequesterUsuarioID, RequesterEmail, RequesterSource,
            OwnerAgentOrDev, ChainID, GateID, DependsOnJobID,
            LifecycleStage, ExecutionStatus, QualityGate, TestsStatus,
            IntegrationStatus, GitSyncStatus, CertificationStatus,
            OperationalValidationStatus, PreviewActivated, OperationalTests,
            FunctionalResult, TerminalResultValid, PercentComplete,
            DevelopmentCommitSHA, PublishedResultCommitSHA, ResultSHA256,
            AttestationSHA256, ProductionTouched, RecoveryAttempts,
            BlockersJson, NextRecommendedAction, ReconciliationStatus,
            ProvenanceSource, SubmittedAtUtc, StartedAtUtc, CompletedAtUtc,
            PublishedAtUtc, UpdatedAtUtc
        FROM dbo.Sys_Worker_Jobs
        WHERE JobID = %s
        """,
        [clean_id],
    )

    sql_job = _serialize_job_row(row) if row else None
    if sql_job and allowed_bounded_contexts:
        allowed_upper = {str(c).strip().upper() for c in allowed_bounded_contexts}
        if str(sql_job.get("bounded_context") or "").upper() not in allowed_upper:
            raise PermissionError("CROSS_DOMAIN_JOB_FORBIDDEN")

    incidents_rows = _run_readonly_all(
        """
        SELECT
            IncidentID, IncidentCategory, ErrorClass, Severity, IncidentState,
            SourceJobID, RepairJobID, ProjectID, BoundedContext,
            ProblemSignature, BlockerSignature, CapabilityCode, RootCause,
            ImpactSummary, OwnerEmail, EvidenceRef, RecommendedAction,
            RecoveryAttempts, CooldownUntilUtc, AlertNotifiedAtUtc,
            ProductionTouched, CreatedAtUtc, UpdatedAtUtc
        FROM dbo.Sys_Worker_Incidents
        WHERE SourceJobID = %s OR RepairJobID = %s
        ORDER BY UpdatedAtUtc DESC
        """,
        [clean_id, clean_id],
    )

    recovery_rows = _run_readonly_all(
        """
        SELECT
            RecoveryEventID, IncidentID, JobID, ActionTaken, Outcome,
            PolicyTier, DetailJson, ProductionTouched, OccurredAtUtc
        FROM dbo.Sys_Worker_RecoveryEvents
        WHERE JobID = %s
        ORDER BY OccurredAtUtc DESC
        """,
        [clean_id],
    )

    canonical_result: Optional[Dict[str, Any]] = None
    try:
        result_path = QUEUE_ROOT / "results" / f"{clean_id}.json"
        if result_path.is_file():
            read_res = read_canonical_result(result_path, expected_job_id=clean_id)
            if getattr(read_res, "terminal_result_valid", False) and isinstance(getattr(read_res, "payload", None), dict):
                payload_copy = dict(read_res.payload)
                preview_path = QUEUE_ROOT / "preview_validations" / f"{clean_id}.json"
                if preview_path.is_file() and "operational_validation" not in payload_copy:
                    preview_doc = _safe_json(preview_path)
                    if isinstance(preview_doc, dict):
                        payload_copy["operational_validation"] = preview_doc
                canonical_result = interpret_result(payload_copy)
    except Exception as exc:
        logger.debug("[WORKER_CONSOLE] read_canonical_result no disponible para %s: %s", clean_id, exc)

    if sql_job is None and canonical_result is None and not incidents_rows:
        return None

    return {
        "source": "SQL_CANONICAL_EDARSAHUB_READONLY",
        "job_id": clean_id,
        "sql_job": sql_job,
        "canonical_result": canonical_result,
        "incidents": [_serialize_incident_row(r) for r in incidents_rows],
        "recovery_events": [_serialize_recovery_row(r) for r in recovery_rows],
    }


def query_incidents(
    *,
    incident_state: Optional[str] = None,
    severity: Optional[str] = None,
    incident_category: Optional[str] = None,
    source_job_id: Optional[str] = None,
    bounded_context: Optional[str] = None,
    q: Optional[str] = None,
    allowed_bounded_contexts: Optional[Sequence[str]] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """Consulta paginada de dbo.Sys_Worker_Incidents + eventos recientes de recuperación."""
    clauses: List[str] = []
    params: List[Any] = []

    if allowed_bounded_contexts:
        placeholders = ", ".join(["%s"] * len(allowed_bounded_contexts))
        clauses.append(f"BoundedContext IN ({placeholders})")
        params.extend(str(c).strip() for c in allowed_bounded_contexts)

    if incident_state and incident_state.strip():
        clauses.append("UPPER(ISNULL(IncidentState, N'')) = UPPER(%s)")
        params.append(incident_state.strip())

    if severity and severity.strip():
        clauses.append("UPPER(ISNULL(Severity, N'')) = UPPER(%s)")
        params.append(severity.strip())

    if incident_category and incident_category.strip():
        clauses.append("UPPER(ISNULL(IncidentCategory, N'')) = UPPER(%s)")
        params.append(incident_category.strip())

    if source_job_id and source_job_id.strip():
        clauses.append("(ISNULL(SourceJobID, N'') LIKE %s OR ISNULL(RepairJobID, N'') LIKE %s)")
        term = f"%{source_job_id.strip()}%"
        params.extend([term, term])

    if bounded_context and bounded_context.strip():
        clauses.append("UPPER(ISNULL(BoundedContext, N'')) = UPPER(%s)")
        params.append(bounded_context.strip())

    if q and q.strip():
        term = f"%{q.strip()}%"
        clauses.append(
            "(IncidentID LIKE %s OR ISNULL(ProblemSignature, N'') LIKE %s OR ISNULL(RootCause, N'') LIKE %s OR ISNULL(SourceJobID, N'') LIKE %s)"
        )
        params.extend([term, term, term, term])

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    count_row = _run_readonly_one(
        f"SELECT COUNT(*) AS total FROM dbo.Sys_Worker_Incidents {where_sql}",
        params,
    ) or {}
    total = int(count_row.get("total") or 0)

    safe_limit = max(1, min(int(limit), 200))
    safe_offset = max(0, int(offset))

    rows = _run_readonly_all(
        f"""
        SELECT
            IncidentID, IncidentCategory, ErrorClass, Severity, IncidentState,
            SourceJobID, RepairJobID, ProjectID, BoundedContext,
            ProblemSignature, BlockerSignature, CapabilityCode, RootCause,
            ImpactSummary, OwnerEmail, EvidenceRef, RecommendedAction,
            RecoveryAttempts, CooldownUntilUtc, AlertNotifiedAtUtc,
            ProductionTouched, CreatedAtUtc, UpdatedAtUtc
        FROM dbo.Sys_Worker_Incidents
        {where_sql}
        ORDER BY UpdatedAtUtc DESC, IncidentID DESC
        OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
        """,
        [*params, safe_offset, safe_limit],
    )

    recovery_rows = _run_readonly_all(
        """
        SELECT TOP 50
            RecoveryEventID, IncidentID, JobID, ActionTaken, Outcome,
            PolicyTier, DetailJson, ProductionTouched, OccurredAtUtc
        FROM dbo.Sys_Worker_RecoveryEvents
        ORDER BY OccurredAtUtc DESC
        """
    )

    return {
        "source": "SQL_CANONICAL_EDARSAHUB_READONLY",
        "total": total,
        "limit": safe_limit,
        "offset": safe_offset,
        "items": [_serialize_incident_row(r) for r in rows],
        "recent_recovery_events": [_serialize_recovery_row(r) for r in recovery_rows],
    }


def query_capabilities(
    *,
    capability_kind: Optional[str] = None,
    certification_status: Optional[str] = None,
    reusable: Optional[bool] = None,
    q: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    """Consulta el catálogo unificado dbo.Sys_Worker_Capabilities (Learned Repair + Knowledge Loop)."""
    clauses: List[str] = []
    params: List[Any] = []

    if capability_kind and capability_kind.strip():
        clauses.append("UPPER(ISNULL(CapabilityKind, N'')) = UPPER(%s)")
        params.append(capability_kind.strip())

    if certification_status and certification_status.strip():
        clauses.append("UPPER(ISNULL(CertificationStatus, N'')) = UPPER(%s)")
        params.append(certification_status.strip())

    if reusable is True:
        clauses.append("Reusable = 1")
    elif reusable is False:
        clauses.append("Reusable = 0")

    if q and q.strip():
        term = f"%{q.strip()}%"
        clauses.append(
            "(CapabilityCode LIKE %s OR ISNULL(ProblemSignature, N'') LIKE %s OR ISNULL(RootCause, N'') LIKE %s OR ISNULL(PreventionRule, N'') LIKE %s)"
        )
        params.extend([term, term, term, term])

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    count_row = _run_readonly_one(
        f"SELECT COUNT(*) AS total FROM dbo.Sys_Worker_Capabilities {where_sql}",
        params,
    ) or {}
    total = int(count_row.get("total") or 0)

    safe_limit = max(1, min(int(limit), 200))
    safe_offset = max(0, int(offset))

    rows = _run_readonly_all(
        f"""
        SELECT
            CapabilityCode, CapabilityKind, ProblemSignature, AllowedModes,
            BoundedContextRule, Reusable, SourceJobID, CertifiedRepairJobID,
            CertifiedCommitSHA, CertificationStatus, OperationalValidationStatus,
            RootCause, PreventionRule, ProductionTouched, UpdatedAtUtc
        FROM dbo.Sys_Worker_Capabilities
        {where_sql}
        ORDER BY UpdatedAtUtc DESC, CapabilityCode ASC
        OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
        """,
        [*params, safe_offset, safe_limit],
    )

    return {
        "source": "SQL_CANONICAL_EDARSAHUB_READONLY",
        "total": total,
        "limit": safe_limit,
        "offset": safe_offset,
        "items": [_serialize_capability_row(r) for r in rows],
    }
