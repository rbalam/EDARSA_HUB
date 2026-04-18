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
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
import logging

from core.rbac.middleware import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/scheduler", tags=["Scheduler"])

# Inyección de dependencia
_db = None


def init_scheduler_routes(database) -> None:
    """Inicializa las rutas con la conexión a MongoDB."""
    global _db
    _db = database
    logger.info("Scheduler routes initialized")


def get_db():
    """Obtiene la conexión a MongoDB."""
    if _db is None:
        raise RuntimeError("Scheduler routes not initialized")
    return _db


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
    current_user: dict = Depends(require_permission("SCHEDULER_ADMIN"))
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


@router.post("/jobs/{job_id}/pause")
async def pause_job(
    job_id: str,
    current_user: dict = Depends(require_permission("SCHEDULER_GESTIONAR"))
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
    current_user: dict = Depends(require_permission("SCHEDULER_GESTIONAR"))
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
    
    job_logger = get_job_logger(db)
    
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
    
    job_logger = get_job_logger(db)
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
    current_user: dict = Depends(require_permission("SCHEDULER_ADMIN"))
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
    return {
        "enabled": config.enabled,
        "timezone": config.timezone,
        "jobs": {k: v.model_dump() for k, v in config.jobs.items()},
        "lock_timeout_seconds": config.lock_timeout_seconds
    }
