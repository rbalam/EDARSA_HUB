"""
EDARSAHUB Universal Worker Console — API Canónica SQL-First + RBAC Fail-Closed (GATE-M2).

Contrato de seguridad:
- TODOS los endpoints requieren JWT válido + sesión activa no revocada (P1-2 vía
  core.security.get_current_user_dual) + autorización explícita (SUPERADMIN en SQL o
  permiso SQL explícito RBAC_ADMIN / WORKER_CONSOLE_VER).
- Deniega por defecto (401 si no autenticado / JWT inválido / sesión revocada;
  403 si no autorizado o intento de cruce de empresa/dominio).
- Solo lectura sobre SQL Server EDARSAHUB (HRLectura read-only) y evidencia del Worker.
- Nunca escribe archivos, nunca ejecuta DDL/DML, nunca toca Producción.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from core.security import get_current_user_dual
from core.sql_first.db import fetch_one_dict_readonly
from modules.worker_console import contract as C

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/worker/console", tags=["worker-console"])

_ALLOWED_EXPLICIT_PERMISSIONS = ("RBAC_ADMIN", "WORKER_CONSOLE_VER")
_SUPERADMIN_ROLE_CODES = frozenset({"SUPERADMIN", "SUPERADMINISTRADOR"})


def _audit_access(
    request: Request,
    *,
    outcome: str,
    user: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
    detail: Optional[str] = None,
) -> None:
    """Registra auditoría de acceso sin exponer secretos, tokens ni credenciales."""
    client_ip = request.client.host if request.client else "unknown"
    email = (user or {}).get("email") or "anonymous"
    usuario_id = (user or {}).get("usuario_id") or (user or {}).get("id") or "unknown"
    role = (user or {}).get("role") or "unknown"
    logger.info(
        "[WORKER_CONSOLE_AUDIT] outcome=%s method=%s path=%s email=%s usuario_id=%s role=%s ip=%s reason=%s detail=%s",
        outcome,
        request.method,
        request.url.path,
        email,
        usuario_id,
        role,
        client_ip,
        reason or "OK",
        (detail or "")[:160],
    )


def _check_sql_worker_console_authority(email: str) -> Dict[str, Any]:
    """Verifica en SQL canónico (HRLectura read-only, fail-closed) si el usuario es
    SUPERADMIN (NivelJerarquia >= 100 / CodigoRol = SUPERADMIN) o posee permiso
    SQL explícito RBAC_ADMIN / WORKER_CONSOLE_VER.
    """
    clean_email = str(email or "").strip()
    if not clean_email:
        return {"authorized": False, "is_superadmin": False, "reason": "MISSING_EMAIL"}

    try:
        role_row = fetch_one_dict_readonly(
            """
            SELECT TOP 1
                u.UsuarioID AS usuario_id,
                r.CodigoRol AS codigo_rol,
                r.NivelJerarquia AS nivel_jerarquia
            FROM dbo.Usuario_Catalogo u
            INNER JOIN dbo.Usuario_RolesAsignacion ura
                ON ura.UsuarioID = u.UsuarioID
                AND ura.Activo = 1
            INNER JOIN dbo.Usuario_Roles r
                ON r.RolID = ura.RolID
                AND r.Activo = 1
            WHERE u.Activo = 1
              AND LOWER(u.Email) = LOWER(%s)
              AND (
                    UPPER(r.CodigoRol) IN (N'SUPERADMIN', N'SUPERADMINISTRADOR')
                 OR ISNULL(r.NivelJerarquia, 0) >= 100
              )
            ORDER BY ISNULL(r.NivelJerarquia, 0) DESC
            """,
            [clean_email],
        )
        if role_row:
            return {
                "authorized": True,
                "is_superadmin": True,
                "reason": f"SQL_SUPERADMIN:{role_row.get('codigo_rol')}",
            }

        perm_row = fetch_one_dict_readonly(
            """
            SELECT TOP 1
                UPPER(CONCAT(m.CodigoModulo, '_', a.CodigoAccion)) AS permiso_efectivo
            FROM dbo.Usuario_Catalogo u
            INNER JOIN dbo.Usuario_RolesAsignacion ura
                ON ura.UsuarioID = u.UsuarioID
                AND ura.Activo = 1
            INNER JOIN dbo.Usuario_Roles r
                ON r.RolID = ura.RolID
                AND r.Activo = 1
            INNER JOIN dbo.Usuario_PermisosRolModulo prm
                ON prm.RolID = r.RolID
                AND prm.Activo = 1
                AND prm.Permitido = 1
            INNER JOIN dbo.Usuario_Modulos m
                ON m.ModuloID = prm.ModuloID
                AND m.Activo = 1
            INNER JOIN dbo.Usuario_Acciones a
                ON a.AccionID = prm.AccionID
                AND a.Activo = 1
            WHERE u.Activo = 1
              AND LOWER(u.Email) = LOWER(%s)
              AND (
                    UPPER(CONCAT(m.CodigoModulo, '_', a.CodigoAccion)) IN (N'RBAC_ADMIN', N'WORKER_CONSOLE_VER')
                 OR LOWER(CONCAT(m.CodigoModulo, '.', a.CodigoAccion)) IN (N'rbac.admin', N'worker_console.ver')
              )
            """,
            [clean_email],
        )
        if perm_row:
            return {
                "authorized": True,
                "is_superadmin": False,
                "reason": f"SQL_EXPLICIT_PERMISSION:{perm_row.get('permiso_efectivo')}",
            }

        return {"authorized": False, "is_superadmin": False, "reason": "NO_RBAC_AUTHORITY"}
    except Exception as exc:
        logger.error("[WORKER_CONSOLE_RBAC] Error verificando autoridad SQL (fail-closed): %s", exc)
        return {"authorized": False, "is_superadmin": False, "reason": f"SQL_RBAC_ERROR:{type(exc).__name__}"}


async def require_worker_console_access(request: Request) -> Dict[str, Any]:
    """Dependencia obligatoria fail-closed para TODOS los endpoints de Worker Console."""
    try:
        user = await get_current_user_dual(request)
    except HTTPException as exc:
        _audit_access(request, outcome="DENIED_AUTH", reason=f"HTTP_{exc.status_code}", detail=str(exc.detail))
        raise

    email = str(user.get("email") or "").strip()
    authority = _check_sql_worker_console_authority(email)

    if not authority.get("authorized"):
        _audit_access(
            request,
            outcome="DENIED_RBAC",
            user=user,
            reason=str(authority.get("reason") or "FORBIDDEN"),
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "WORKER_CONSOLE_FORBIDDEN",
                "mensaje": "Acceso denegado: se requiere rol SUPERADMIN o permiso SQL explícito RBAC_ADMIN.",
                "permiso_requerido": "RBAC_ADMIN",
            },
        )

    enriched = dict(user)
    enriched["_worker_console_is_superadmin"] = bool(authority.get("is_superadmin"))
    enriched["_worker_console_auth_reason"] = str(authority.get("reason") or "AUTHORIZED")
    _audit_access(request, outcome="ALLOWED", user=enriched, reason=enriched["_worker_console_auth_reason"])
    return enriched


def _enforce_tenant_and_domain_scope(
    request: Request,
    current_user: Dict[str, Any],
    *,
    requested_empresa_id: Optional[str] = None,
    requested_bounded_context: Optional[str] = None,
) -> Optional[List[str]]:
    """Impide acceso cruzado de empresa o dominio para usuarios no SUPERADMIN."""
    is_superadmin = bool(current_user.get("_worker_console_is_superadmin"))
    if is_superadmin:
        return None

    # 1. Protección cross-empresa (fail-closed si se solicita otra empresa)
    if requested_empresa_id is not None and str(requested_empresa_id).strip():
        req_emp = str(requested_empresa_id).strip()
        user_empresas = set()
        for key in ("empresa_id", "EmpresaID"):
            if current_user.get(key) is not None:
                user_empresas.add(str(current_user.get(key)).strip())
        raw_list = current_user.get("empresas_permitidas") or current_user.get("allowed_empresas")
        if isinstance(raw_list, (list, tuple, set)):
            user_empresas.update(str(e).strip() for e in raw_list if e is not None and str(e).strip())
        if not user_empresas or req_emp not in user_empresas:
            _audit_access(
                request,
                outcome="DENIED_CROSS_EMPRESA",
                user=current_user,
                reason="CROSS_EMPRESA_FORBIDDEN",
                detail=f"requested_empresa_id={req_emp}",
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "CROSS_EMPRESA_FORBIDDEN",
                    "mensaje": "No tiene autorización para consultar información de otra empresa.",
                },
            )

    # 2. Protección cross-dominio (si el usuario tiene dominios acotados)
    raw_domains = current_user.get("allowed_bounded_contexts") or current_user.get("dominios_permitidos")
    allowed_domains: Optional[List[str]] = None
    if isinstance(raw_domains, (list, tuple, set)) and len(raw_domains) > 0:
        allowed_domains = [str(d).strip() for d in raw_domains if str(d).strip()]
        allowed_upper = {d.upper() for d in allowed_domains}
        if requested_bounded_context and requested_bounded_context.strip().upper() not in allowed_upper:
            _audit_access(
                request,
                outcome="DENIED_CROSS_DOMAIN",
                user=current_user,
                reason="CROSS_DOMAIN_FORBIDDEN",
                detail=f"requested_bounded_context={requested_bounded_context}",
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "CROSS_DOMAIN_FORBIDDEN",
                    "mensaje": "No tiene autorización para consultar este dominio operativo.",
                },
            )
    return allowed_domains


def _raise_sql_unavailable(exc: C.WorkerConsoleSqlError) -> None:
    raise HTTPException(
        status_code=503,
        detail={
            "error": "WORKER_CONSOLE_SQL_UNAVAILABLE",
            "mensaje": "No se pudo consultar el estado canónico en SQL Server EDARSAHUB (fail-closed).",
            "codigo": str(exc),
        },
    )


def _list_state(directory: Path) -> List[Path]:
    if not directory.exists():
        return []
    return [p for p in directory.iterdir() if p.is_file()]


def _job_id_from_name(name: str) -> str:
    return re.sub(r"\.(json)(\..*)?$", "", name, flags=re.IGNORECASE)


def _read_reconciled_result_doc(job_id: str, path: Path, state: str) -> Optional[Any]:
    """Lee resultados reconciliados vía worker_result_reader + preview_validations (sin inventar estado)."""
    if state == "results":
        try:
            read_res = C.read_canonical_result(path, expected_job_id=job_id)
            if getattr(read_res, "terminal_result_valid", False) and isinstance(getattr(read_res, "payload", None), dict):
                payload = dict(read_res.payload)
                preview_path = C.QUEUE_ROOT / "preview_validations" / f"{job_id}.json"
                if preview_path.is_file() and "operational_validation" not in payload:
                    preview_doc = C.read_json_file(preview_path)
                    if isinstance(preview_doc, dict):
                        payload["operational_validation"] = preview_doc
                return payload
        except Exception:
            pass
    return C.read_json_file(path)


def _find_in_state(state: str, job_id: str) -> Optional[Path]:
    d = C.state_dir(state)
    if d is None or not d.exists():
        return None
    for p in _list_state(d):
        if _job_id_from_name(p.name) == job_id:
            return p
    return None


@router.get("/dashboard")
async def dashboard(
    request: Request,
    empresa_id: Optional[str] = Query(None, description="Filtro de alcance de empresa (validado RBAC)"),
    current_user: dict = Depends(require_worker_console_access),
):
    """Resumen SQL canónico (dbo.Sys_Worker_*) + telemetría del runtime del Worker."""
    allowed_domains = _enforce_tenant_and_domain_scope(
        request,
        current_user,
        requested_empresa_id=empresa_id,
    )
    try:
        sql_summary = C.query_dashboard_summary(allowed_bounded_contexts=allowed_domains)
    except C.WorkerConsoleSqlError as exc:
        _raise_sql_unavailable(exc)

    states: Dict[str, int] = {}
    for st in ["requests"] + C.LIFECYCLE_STATES:
        d = C.state_dir(st)
        states[st] = len(_list_state(d)) if d else 0

    runtime_dir = C.QUEUE_ROOT / "runtime"

    def _read_txt(name: str) -> Optional[str]:
        p = runtime_dir / name
        try:
            return p.read_text(encoding="utf-8", errors="replace").strip() if p.exists() else None
        except Exception:
            return None

    preferred_doc = C.read_json_file(runtime_dir / "preferred_job.json")
    preferred_job_orphaned = False
    if isinstance(preferred_doc, dict):
        pref_jid = str(preferred_doc.get("job_id") or "").strip()
        exp_epoch = preferred_doc.get("expires_at_epoch")
        expired = isinstance(exp_epoch, (int, float)) and datetime.now(timezone.utc).timestamp() > float(exp_epoch)
        in_flight = bool(pref_jid and (_find_in_state("pending", pref_jid) or _find_in_state("processing", pref_jid)))
        preferred_job_orphaned = bool(not pref_jid or not in_flight or expired)

    orphaned_archive_dir = runtime_dir / "orphaned-preferred"
    orphaned_archive_count = (
        sum(1 for entry in orphaned_archive_dir.iterdir())
        if orphaned_archive_dir.is_dir()
        else 0
    )

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": sql_summary["source"],
        "sql_summary": sql_summary,
        "states": states,
        "runtime": {
            "current_job_id": _read_txt("current_job_id"),
            "generation": _read_txt("generation"),
            "last_cycle_utc": _read_txt("last_cycle_utc"),
            "last_receive_utc": _read_txt("last_receive_utc"),
            "last_terminal_utc": _read_txt("last_terminal_utc"),
            "control_plane_status": C.read_json_file(runtime_dir / "control_plane_status.json"),
            "reconciler": C.read_json_file(runtime_dir / "reconciler.json"),
            "preferred_job": preferred_doc,
            "preferred_job_orphaned": preferred_job_orphaned,
            "orphaned_preferred_archive_count": orphaned_archive_count,
            "sql_projection_pending": C.read_json_file(runtime_dir / "sql_projection_pending.json"),
        },
        "viewer": {
            "email": current_user.get("email"),
            "is_superadmin": bool(current_user.get("_worker_console_is_superadmin")),
            "auth_basis": current_user.get("_worker_console_auth_reason"),
        },
    }


@router.get("/jobs")
async def list_canonical_jobs(
    request: Request,
    q: Optional[str] = Query(None, description="Búsqueda por job_id, source_job_id, objetivo o capacidad"),
    job_id: Optional[str] = Query(None, description="Filtro por JobID"),
    source_job_id: Optional[str] = Query(None, description="Filtro por SourceJobID"),
    project_id: Optional[str] = Query(None, description="Filtro por ProjectID"),
    bounded_context: Optional[str] = Query(None, description="Filtro por dominio / BoundedContext"),
    lifecycle_stage: Optional[str] = Query(None, description="SUBMITTED, INTEGRATED, CERTIFIED, ACTIVE_IN_PREVIEW, BLOCKED, FAILED, REJECTED, INVALID"),
    certification_status: Optional[str] = Query(None, description="Estado de certificación"),
    operational_validation_status: Optional[str] = Query(None, description="Estado de validación operativa en Preview"),
    reconciliation_status: Optional[str] = Query(None, description="Estado de reconciliación"),
    has_blockers: Optional[bool] = Query(None, description="Filtrar jobs con o sin bloqueos"),
    date_from: Optional[str] = Query(None, description="Fecha inicio UTC (YYYY-MM-DD o ISO-8601)"),
    date_to: Optional[str] = Query(None, description="Fecha fin UTC (YYYY-MM-DD o ISO-8601)"),
    empresa_id: Optional[str] = Query(None, description="Alcance de empresa (validado RBAC)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_worker_console_access),
):
    """Lista paginada y filtrable de trabajos desde SQL canónico dbo.Sys_Worker_Jobs."""
    allowed_domains = _enforce_tenant_and_domain_scope(
        request,
        current_user,
        requested_empresa_id=empresa_id,
        requested_bounded_context=bounded_context,
    )
    try:
        return C.query_jobs(
            q=q,
            job_id=job_id,
            source_job_id=source_job_id,
            project_id=project_id,
            bounded_context=bounded_context,
            lifecycle_stage=lifecycle_stage,
            certification_status=certification_status,
            operational_validation_status=operational_validation_status,
            reconciliation_status=reconciliation_status,
            has_blockers=has_blockers,
            date_from=date_from,
            date_to=date_to,
            allowed_bounded_contexts=allowed_domains,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except C.WorkerConsoleSqlError as exc:
        _raise_sql_unavailable(exc)


@router.get("/job/{job_id}")
async def get_canonical_job_detail(
    job_id: str,
    request: Request,
    current_user: dict = Depends(require_worker_console_access),
):
    """Detalle completo de un trabajo: SQL canónico + resultado + incidentes + recovery."""
    allowed_domains = _enforce_tenant_and_domain_scope(request, current_user)
    try:
        detail = C.query_job_detail(job_id, allowed_bounded_contexts=allowed_domains)
    except PermissionError:
        _audit_access(request, outcome="DENIED_CROSS_DOMAIN", user=current_user, reason="CROSS_DOMAIN_JOB_FORBIDDEN", detail=job_id)
        raise HTTPException(
            status_code=403,
            detail={
                "error": "CROSS_DOMAIN_FORBIDDEN",
                "mensaje": "No tiene autorización para consultar este trabajo fuera de su dominio.",
            },
        )
    except C.WorkerConsoleSqlError as exc:
        _raise_sql_unavailable(exc)

    if detail is None:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado en SQL canónico ni en resultados")
    return detail


@router.get("/incidents")
async def list_incidents(
    request: Request,
    incident_state: Optional[str] = Query(None, description="Estado del incidente"),
    severity: Optional[str] = Query(None, description="Severidad"),
    incident_category: Optional[str] = Query(None, description="Categoría"),
    source_job_id: Optional[str] = Query(None, description="Job origen o reparación"),
    bounded_context: Optional[str] = Query(None, description="Dominio / BoundedContext"),
    q: Optional[str] = Query(None, description="Búsqueda libre"),
    empresa_id: Optional[str] = Query(None, description="Alcance de empresa (validado RBAC)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_worker_console_access),
):
    """Consulta incidentes (dbo.Sys_Worker_Incidents) y eventos de recuperación."""
    allowed_domains = _enforce_tenant_and_domain_scope(
        request,
        current_user,
        requested_empresa_id=empresa_id,
        requested_bounded_context=bounded_context,
    )
    try:
        return C.query_incidents(
            incident_state=incident_state,
            severity=severity,
            incident_category=incident_category,
            source_job_id=source_job_id,
            bounded_context=bounded_context,
            q=q,
            allowed_bounded_contexts=allowed_domains,
            limit=limit,
            offset=offset,
        )
    except C.WorkerConsoleSqlError as exc:
        _raise_sql_unavailable(exc)


@router.get("/capabilities")
async def list_capabilities(
    request: Request,
    capability_kind: Optional[str] = Query(None, description="LEARNED_REPAIR o KNOWLEDGE_LESSON"),
    certification_status: Optional[str] = Query(None, description="Estado de certificación"),
    reusable: Optional[bool] = Query(None, description="Solo reutilizables"),
    q: Optional[str] = Query(None, description="Búsqueda por código, firma o prevención"),
    empresa_id: Optional[str] = Query(None, description="Alcance de empresa (validado RBAC)"),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_worker_console_access),
):
    """Consulta capacidades aprendidas y lecciones del Knowledge Loop (dbo.Sys_Worker_Capabilities)."""
    _enforce_tenant_and_domain_scope(request, current_user, requested_empresa_id=empresa_id)
    try:
        return C.query_capabilities(
            capability_kind=capability_kind,
            certification_status=certification_status,
            reusable=reusable,
            q=q,
            limit=limit,
            offset=offset,
        )
    except C.WorkerConsoleSqlError as exc:
        _raise_sql_unavailable(exc)


@router.get("/jobs/{state}")
async def list_jobs_by_queue_state(
    state: str,
    q: Optional[str] = Query(None, description="filtro por job_id"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_worker_console_access),
):
    """Lista artefactos de una carpeta de estado de la cola local (protegido RBAC)."""
    d = C.state_dir(state)
    if d is None:
        raise HTTPException(status_code=400, detail="Estado no válido")
    files = _list_state(d)
    items = []
    for p in files:
        jid = _job_id_from_name(p.name)
        if q and q.lower() not in jid.lower():
            continue
        try:
            stt = p.stat()
            items.append({
                "job_id": jid,
                "file": p.name,
                "size": stt.st_size,
                "modified_utc": datetime.fromtimestamp(stt.st_mtime, timezone.utc).isoformat(),
            })
        except Exception:
            continue
    items.sort(key=lambda x: x["modified_utc"], reverse=True)
    return {
        "state": state,
        "total": len(items),
        "limit": limit,
        "offset": offset,
        "items": items[offset:offset + limit],
    }


@router.get("/lifecycle/{job_id}")
async def lifecycle(
    job_id: str,
    request: Request,
    current_user: dict = Depends(require_worker_console_access),
):
    """Traza un job_id combinando SQL canónico, cola local e intérprete canónico."""
    allowed_domains = _enforce_tenant_and_domain_scope(request, current_user)
    presence: Dict[str, bool] = {}
    job_doc = None
    for st in ["requests"] + C.LIFECYCLE_STATES:
        p = _find_in_state(st, job_id)
        present = p is not None
        presence[st] = present
        if present and job_doc is None and st in ("requests", "pending", "processing"):
            doc = C.read_json_file(p)
            if doc is not None:
                job_doc = C.extract_job(doc)

    result_interp = None
    for st in ("results", "done", "published"):
        rp = _find_in_state(st, job_id)
        if rp is None:
            continue
        doc = _read_reconciled_result_doc(job_id, rp, st)
        if doc is not None:
            result_interp = C.interpret_result(doc)
            break

    sql_detail = None
    try:
        sql_detail = C.query_job_detail(job_id, allowed_bounded_contexts=allowed_domains)
    except PermissionError:
        raise HTTPException(
            status_code=403,
            detail={"error": "CROSS_DOMAIN_FORBIDDEN", "mensaje": "Trabajo fuera del dominio autorizado."},
        )
    except C.WorkerConsoleSqlError as exc:
        _raise_sql_unavailable(exc)

    if sql_detail and result_interp is None:
        result_interp = sql_detail.get("canonical_result")

    if not any(presence.values()) and sql_detail is None:
        raise HTTPException(status_code=404, detail="job_id no encontrado en SQL canónico ni en cola")

    presence_list = [{"state": st, "present": bool(presence[st])} for st in ["requests"] + C.LIFECYCLE_STATES]

    return {
        "job_id": job_id,
        "presence": presence,
        "presence_list": presence_list,
        "job": job_doc or (sql_detail.get("sql_job") if sql_detail else None),
        "sql_job": sql_detail.get("sql_job") if sql_detail else None,
        "incidents": sql_detail.get("incidents", []) if sql_detail else [],
        "recovery_events": sql_detail.get("recovery_events", []) if sql_detail else [],
        "result": result_interp,
        "interpretation": result_interp,
    }


@router.get("/result/{job_id}")
async def result(
    job_id: str,
    request: Request,
    current_user: dict = Depends(require_worker_console_access),
):
    """Intérprete canónico de resultado de un job (cola + SQL canónico)."""
    allowed_domains = _enforce_tenant_and_domain_scope(request, current_user)
    sql_detail = None
    if allowed_domains:
        try:
            sql_detail = C.query_job_detail(job_id, allowed_bounded_contexts=allowed_domains)
        except PermissionError:
            _audit_access(request, outcome="DENIED_CROSS_DOMAIN", user=current_user, reason="CROSS_DOMAIN_RESULT_FORBIDDEN", detail=job_id)
            raise HTTPException(
                status_code=403,
                detail={"error": "CROSS_DOMAIN_FORBIDDEN", "mensaje": "Trabajo fuera del dominio autorizado."},
            )
        except C.WorkerConsoleSqlError as exc:
            _raise_sql_unavailable(exc)

    for st in ("results", "done", "published", "rejected"):
        p = _find_in_state(st, job_id)
        if p is not None:
            doc = _read_reconciled_result_doc(job_id, p, st)
            return {
                "job_id": job_id,
                "found_in": st,
                "interpretation": C.interpret_result(doc) if doc is not None else None,
                "raw": doc,
            }

    if sql_detail is None:
        try:
            sql_detail = C.query_job_detail(job_id, allowed_bounded_contexts=allowed_domains)
        except PermissionError:
            raise HTTPException(
                status_code=403,
                detail={"error": "CROSS_DOMAIN_FORBIDDEN", "mensaje": "Trabajo fuera del dominio autorizado."},
            )
        except C.WorkerConsoleSqlError as exc:
            _raise_sql_unavailable(exc)

    if sql_detail and (sql_detail.get("canonical_result") or sql_detail.get("sql_job")):
        sql_job = sql_detail.get("sql_job")
        interp = sql_detail.get("canonical_result")
        if interp is None and sql_job is not None:
            interp = C.interpret_result(
                {
                    "job_id": sql_job.get("job_id"),
                    "status": sql_job.get("execution_status"),
                    "certification": sql_job.get("certification_status"),
                    "quality_gate": sql_job.get("quality_gate"),
                    "tests": sql_job.get("tests_status"),
                    "blockers": sql_job.get("blockers"),
                    "production_touched": sql_job.get("production_touched"),
                    "development_sha": sql_job.get("development_commit_sha"),
                    "published_result_commit": sql_job.get("published_result_commit_sha"),
                    "published_result_sha256": sql_job.get("result_sha256"),
                    "attestation_sha256": sql_job.get("attestation_sha256"),
                    "reconciliation_status": sql_job.get("reconciliation_status"),
                    "percent_complete": sql_job.get("percent_complete"),
                }
            )
        return {
            "job_id": job_id,
            "found_in": "sql_canonical",
            "interpretation": interp,
            "raw": sql_job,
        }

    raise HTTPException(status_code=404, detail="Sin resultado para ese job_id")


@router.post("/validate")
async def validate(
    payload: dict,
    current_user: dict = Depends(require_worker_console_access),
):
    """Valida un job contra el contrato edarsahub.worker-job.v2 SIN escribir nada."""
    return C.validate_job(payload)


TABLAJERIAS_PATTERNS = [
    ("R24E certificado", r"TABLAJERIA.*R24E"),
    ("R24F certificado", r"TABLAJERIA.*R24F"),
    ("R24E+R24F compatibility", r"TABLAJERIA.*R24E.*R24F.*COMPAT|TABLAJERIA.*COMPAT.*R24"),
    ("Release Package Manifest R1B", r"TABLAJERIA.*(PACKAGE|MANIFEST).*R1B"),
    ("Release Patch Plan R1B", r"TABLAJERIA.*PATCH.*PLAN.*R1B"),
    ("Release Dry Run R1B", r"TABLAJERIA.*DRY.?RUN.*R1B"),
    ("Release Go/No-Go R1B", r"TABLAJERIA.*(GO.?NO.?GO|GO_NO_GO).*R1B"),
]


@router.get("/tablajerias/checklist")
async def tablajerias_checklist(current_user: dict = Depends(require_worker_console_access)):
    """Checklist ejecutivo de cierre de Tablajerías (protegido RBAC, solo lectura)."""
    index: Dict[str, Path] = {}
    for st in ("results", "done", "published"):
        d = C.state_dir(st)
        if d and d.exists():
            for p in _list_state(d):
                jid = _job_id_from_name(p.name)
                index.setdefault(jid.upper(), p)

    items = []
    all_pass = True
    prod_touched_any = False
    for label, pat in TABLAJERIAS_PATTERNS:
        rx = re.compile(pat, re.IGNORECASE)
        candidates = [jid for jid in index if rx.search(jid)]
        best = None
        for jid in candidates:
            doc = C.read_json_file(index[jid])
            interp = C.interpret_result(doc) if doc is not None else None
            if not interp:
                continue
            rank = {"PASS": 3, "FAIL": 2}.get(interp.get("verdict"), 1)
            if best is None or rank > best[0]:
                best = (rank, jid, interp)
        if best:
            match_jid, interp = best[1], best[2]
            verdict = interp["verdict"]
            pt = interp.get("production_touched")
            if pt is True:
                prod_touched_any = True
            if verdict != "PASS":
                all_pass = False
            items.append({
                "check": label,
                "job_id": match_jid,
                "verdict": verdict,
                "production_touched": pt,
                "blocker_count": interp.get("blocker_count"),
            })
        else:
            all_pass = False
            items.append({
                "check": label,
                "job_id": None,
                "verdict": "NOT_FOUND",
                "production_touched": None,
                "blocker_count": None,
            })

    return {
        "case": "Tablajerías",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "items": items,
        "all_pass": all_pass,
        "production_touched": prod_touched_any,
        "technical_status": "GO técnico READ_ONLY" if (all_pass and not prod_touched_any) else "PENDIENTE",
        "next_decision": "Autorización humana explícita antes de Producción",
        "note": "GO técnico READ_ONLY. NO es autorización automática para Producción. "
                "Requiere autorización humana explícita.",
    }


@router.get("/audit")
async def audit(
    tail: int = Query(80, ge=1, le=500),
    current_user: dict = Depends(require_worker_console_access),
):
    """Visor de evidencia/auditoría del runtime (solo lectura, protegido RBAC)."""
    runtime_dir = C.QUEUE_ROOT / "runtime"

    def _tail(name: str) -> List[str]:
        p = runtime_dir / name
        if not p.exists():
            return []
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            return lines[-tail:]
        except Exception:
            return []

    cert_log = _tail("universal-worker-cert.log")
    launch_log = _tail("universal-worker-launch.log")
    control_plane_status = C.read_json_file(runtime_dir / "control_plane_status.json")
    reconciler = C.read_json_file(runtime_dir / "reconciler.json")
    sql_projection_pending = C.read_json_file(runtime_dir / "sql_projection_pending.json")

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "cert_log": cert_log,
        "launch_log": launch_log,
        "control_plane_status": control_plane_status,
        "reconciler": reconciler,
        "sql_projection_pending": sql_projection_pending,
        "logs": {
            "universal-worker-cert.log": cert_log,
            "universal-worker-launch.log": launch_log,
            "control_plane_status.json": control_plane_status,
            "reconciler.json": reconciler,
            "sql_projection_pending.json": sql_projection_pending,
        },
    }
