"""
EDARSA HUB - Scheduler API Routes
=================================
Endpoints de administración del scheduler.
PROTEGIDO CON RBAC (Fase 2D)

Permisos requeridos:
- GET /status, /jobs/{id}, /logs, /logs/stats, /locks, /config - SCHEDULER_VER
- POST /jobs/{id}/pause, /jobs/{id}/resume - SCHEDULER_GESTIONAR
- POST /jobs/{id}/run, DELETE /locks/{job_name} - SCHEDULER_ADMIN
"""

from typing import Optional
from datetime import date, datetime, timezone, timedelta
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
import logging

from core.rbac.middleware import require_permission, require_explicit_permission_dual

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/scheduler", tags=["Scheduler"])


class NetPayManualRunRequest(BaseModel):
    fecha_desde: date = Field(..., description="Fecha inicial ISO YYYY-MM-DD")
    fecha_hasta: date = Field(..., description="Fecha final ISO YYYY-MM-DD")


# Inyección de dependencia
_db = None


def init_scheduler_routes(database) -> None:
    """
    Inicializa las rutas con la dependencia técnica del scheduler.
    
    NOTA: MongoDB ELIMINADO del sistema. Este módulo ahora opera con StubDatabase
    que retorna valores vacíos sin fallar.
    """
    global _db
    _db = database
    # Detectar si es StubDatabase
    is_stub = hasattr(database, '_collections') and database.__class__.__name__ == 'StubDatabase'
    if is_stub:
        logger.info("[SCHEDULER_ROUTES] Inicializado con StubDatabase - MongoDB ELIMINADO")
    else:
        logger.info("Scheduler routes initialized")


def get_db():
    """
    Obtiene la dependencia técnica del scheduler.
    
    NOTA: Puede retornar StubDatabase que opera sin persistencia.
    """
    return _db


def is_mongo_available() -> bool:
    """
    Verifica si existe dependencia legacy real no StubDatabase.
    
    NOTA: StubDatabase se considera como NO disponible.
    """
    if _db is None:
        return False
    return not (hasattr(_db, '_collections') and _db.__class__.__name__ == 'StubDatabase')


# =============================================================================
# STATUS
# =============================================================================

@router.get("/status")
async def get_scheduler_status(
    current_user: dict = Depends(require_permission("SCHEDULER_VER"))
):
    """
    Obtiene estado actual del scheduler.
    
    Incluye:
    - Estado running/stopped
    - Lista de jobs registrados
    - Próximas ejecuciones
    """
    from .scheduler_manager import get_scheduler_manager
    
    try:
        manager = get_scheduler_manager()
        return manager.get_status()
    except Exception as e:
        return {
            "running": False,
            "error": str(e),
            "message": "Scheduler no disponible"
        }


@router.get("/jobs/{job_id}")
async def get_job_info(
    job_id: str,
    current_user: dict = Depends(require_permission("SCHEDULER_VER"))
):
    """Obtiene información detallada de un job."""
    from .scheduler_manager import get_scheduler_manager
    
    manager = get_scheduler_manager()
    info = manager.get_job_info(job_id)
    
    if not info:
        raise HTTPException(status_code=404, detail=f"Job no encontrado: {job_id}")
    
    return info


# =============================================================================
# CONTROL
# =============================================================================

@router.post("/jobs/{job_id}/run")
async def run_job_now(
    job_id: str,
    current_user: dict = Depends(require_explicit_permission_dual("SCHEDULER_ADMIN"))
):
    """
    Ejecuta un job inmediatamente (manual).
    
    Útil para pruebas o forzar procesamiento.
    """
    from .scheduler_manager import get_scheduler_manager
    
    manager = get_scheduler_manager()
    result = await manager.run_job_now(job_id)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return result


@router.post("/inventarios/retry-error/{record_id}")
async def retry_inventario_error(
    record_id: int,
    current_user: dict = Depends(require_explicit_permission_dual("SCHEDULER_ADMIN"))
):
    """Reintenta exactamente un inventario en ERROR sin resetear el resto de la cola."""
    from .scheduler_manager import get_scheduler_manager

    manager = get_scheduler_manager()
    result = await manager.retry_inventario_error_by_id(record_id)

    if result.get("status") == "error":
        raise HTTPException(status_code=409, detail=result.get("message"))
    if result.get("status") == "NOT_ELIGIBLE":
        raise HTTPException(status_code=404, detail=result.get("message"))

    return result


async def _run_netpay_manual_background(fecha_desde: date, fecha_hasta: date) -> None:
    """Ejecuta NetPay fuera del request HTTP para evitar timeouts de navegador/proxy."""
    from .jobs.netpay_sync_job import execute_netpay_sync_diario

    try:
        result = await execute_netpay_sync_diario(
            date_from=fecha_desde,
            date_to=fecha_hasta,
            max_days=31,
        )
        logger.info(
            "[NETPAY_MANUAL_RUN_BG] Finalizado status=%s fecha_desde=%s fecha_hasta=%s",
            "completed" if result.get("success") else "failed",
            fecha_desde.isoformat(),
            fecha_hasta.isoformat(),
        )
    except Exception as e:
        logger.error(f"[NETPAY_MANUAL_RUN_BG] Error ejecutando NetPay manual: {e}")


@router.post("/netpay/run")
async def run_netpay_manual(
    payload: NetPayManualRunRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_explicit_permission_dual("SCHEDULER_ADMIN"))
):
    """
    Inicia manualmente NetPay por rango controlado.
    Máximo permitido: 31 días calendario.
    """
    if payload.fecha_hasta < payload.fecha_desde:
        raise HTTPException(status_code=400, detail="Fecha hasta no puede ser menor que fecha desde.")

    diff_days = (payload.fecha_hasta - payload.fecha_desde).days + 1
    if diff_days > 31:
        raise HTTPException(status_code=400, detail=f"El rango máximo permitido es de 31 días. Rango actual: {diff_days} días.")

    background_tasks.add_task(
        _run_netpay_manual_background,
        payload.fecha_desde,
        payload.fecha_hasta,
    )

    return {
        "status": "accepted",
        "job_id": "netpay_sync_diario",
        "manual": True,
        "fecha_desde": payload.fecha_desde.isoformat(),
        "fecha_hasta": payload.fecha_hasta.isoformat(),
        "message": "Ejecución NetPay iniciada en segundo plano",
    }


@router.post("/jobs/{job_id}/pause")
async def pause_job(
    job_id: str,
    current_user: dict = Depends(require_explicit_permission_dual("SCHEDULER_GESTIONAR"))
):
    """Pausa un job."""
    from .scheduler_manager import get_scheduler_manager
    
    manager = get_scheduler_manager()
    success = manager.pause_job(job_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=f"No se pudo pausar job: {job_id}")
    
    return {"status": "paused", "job_id": job_id}


@router.post("/jobs/{job_id}/resume")
async def resume_job(
    job_id: str,
    current_user: dict = Depends(require_explicit_permission_dual("SCHEDULER_GESTIONAR"))
):
    """Reanuda un job pausado."""
    from .scheduler_manager import get_scheduler_manager
    
    manager = get_scheduler_manager()
    success = manager.resume_job(job_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=f"No se pudo reanudar job: {job_id}")
    
    return {"status": "resumed", "job_id": job_id}


# =============================================================================
# LOGS
# =============================================================================

@router.get("/logs")
async def get_job_logs(
    job_name: Optional[str] = None,
    status: Optional[str] = None,
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_permission("SCHEDULER_VER"))
):
    """
    Consulta historial de ejecuciones de jobs.
    
    Args:
        job_name: Filtrar por nombre de job
        status: Filtrar por estado (success, failed, skipped)
        hours: Horas hacia atrás (default 24, max 168)
        limit: Máximo de registros
    """
    db = get_db()
    from .job_logger import get_job_logger
    
    job_logger = get_job_logger()
    
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    logs = await job_logger.get_logs(
        job_name=job_name,
        status=status,
        since=since,
        limit=limit
    )
    
    return {
        "items": logs,
        "total": len(logs),
        "filters": {
            "job_name": job_name,
            "status": status,
            "hours": hours
        }
    }


@router.get("/logs/stats")
async def get_job_stats(
    job_name: Optional[str] = None,
    hours: int = Query(24, ge=1, le=168),
    current_user: dict = Depends(require_permission("SCHEDULER_VER"))
):
    """Obtiene estadísticas de ejecuciones."""
    db = get_db()
    from .job_logger import get_job_logger
    
    job_logger = get_job_logger()
    stats = await job_logger.get_stats(job_name=job_name, hours=hours)
    
    return {
        "stats": stats,
        "period_hours": hours,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# =============================================================================
# LOCKS
# =============================================================================

@router.get("/locks")
async def get_active_locks(
    current_user: dict = Depends(require_permission("SCHEDULER_VER"))
):
    """Obtiene locks activos."""
    db = get_db()
    from .locks import get_lock_manager
    
    lock_manager = get_lock_manager(db)
    locks = await lock_manager.get_all_locks()
    
    return {
        "items": locks,
        "total": len(locks)
    }


@router.delete("/locks/{job_name}")
async def force_release_lock(
    job_name: str,
    current_user: dict = Depends(require_explicit_permission_dual("SCHEDULER_ADMIN"))
):
    """
    Fuerza liberación de un lock (admin/emergencia).
    
    ADVERTENCIA: Usar solo cuando sea absolutamente necesario.
    """
    db = get_db()
    from .locks import DistributedLock
    
    lock = DistributedLock(db, job_name)
    released = await lock.force_release()
    
    if not released:
        raise HTTPException(status_code=404, detail=f"Lock no encontrado: {job_name}")
    
    return {"status": "released", "job_name": job_name}


# =============================================================================
# CONFIGURATION
# =============================================================================

@router.get("/config")
async def get_scheduler_config(
    current_user: dict = Depends(require_permission("SCHEDULER_VER"))
):
    """Obtiene configuración actual del scheduler."""
    from .config import get_scheduler_config
    
    config = get_scheduler_config()
    jobs = {k: v.model_dump() for k, v in config.jobs.items()}

    # Complemento SQL-first: metadatos operativos editables/visibles desde Centro de Control.
    # No ejecuta comandos arbitrarios; solo expone instrucción, preview, parámetros y dependencias.
    try:
        from core.centro_control.routes import _cc_fetchall
        rows = _cc_fetchall("""
            SELECT
                JobID,
                Handler,
                ParametrosJSON,
                InstruccionEjecucion,
                ComandoPreview,
                ParametrosEditablesJSON,
                GrupoEjecucion,
                DependenciasJSON,
                AdvertenciaManual,
                PermiteEjecucionManual
            FROM dbo.Sys_Scheduler_JobConfig
        """)
        for row in rows:
            job_id = row.get("JobID")
            if not job_id:
                continue
            jobs.setdefault(job_id, {"job_id": job_id})
            jobs[job_id].update({
                "handler": row.get("Handler"),
                "parametros_json": row.get("ParametrosJSON"),
                "instruccion_ejecucion": row.get("InstruccionEjecucion"),
                "comando_preview": row.get("ComandoPreview"),
                "parametros_editables_json": row.get("ParametrosEditablesJSON"),
                "grupo_ejecucion": row.get("GrupoEjecucion"),
                "dependencias_json": row.get("DependenciasJSON"),
                "advertencia_manual": row.get("AdvertenciaManual"),
                "permite_ejecucion_manual": bool(row.get("PermiteEjecucionManual", True)),
            })
    except Exception as e:
        logger.warning(f"[SCHEDULER_CONFIG] No se pudieron cargar metadatos SQL de jobs: {e}")

    return {
        "enabled": config.enabled,
        "timezone": config.timezone,
        "jobs": jobs,
        "lock_timeout_seconds": config.lock_timeout_seconds
    }
