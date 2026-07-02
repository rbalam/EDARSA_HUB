from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Endpoints de Auditorías Programadas
EDARSA HUB - Módulo Auditorías Programadas
PROTEGIDO CON RBAC

Permisos:
- AUDITORIA_VER: Ver programaciones, historial, KPIs, calendario
- AUDITORIA_PROGRAMAR: Crear, editar, activar/desactivar
- AUDITORIAS_GESTIONAR: Ejecutar manualmente, eliminar
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime, timezone

from ..services.auditoria_programada_service import (
    AuditoriaProgramadaService,
    AuditoriaNoEncontradaError,
    EjecucionDuplicadaError,
    ConfiguracionInvalidaError,
)
from ..schemas.auditoria_programada_schemas import (
    AuditoriaProgramadaCreate,
    AuditoriaProgramadaUpdate,
)
from ..api_schemas import OperacionResponse
from ..db_utils import get_database

# RBAC
from core.rbac.middleware import require_permission, require_explicit_permission

router = APIRouter()


def get_db():
    """Obtiene conexión a la base de datos."""
    return get_database()


# =============================================================================
# CRUD
# =============================================================================

@router.get(
    "",
    summary="Listar auditorías programadas",
    description="Lista todas las auditorías programadas con filtros opcionales. Requiere AUDITORIA_VER."
)
async def listar_auditorias(
    sucursal_id: Optional[str] = Query(None, description="Filtrar por sucursal"),
    solo_activas: bool = Query(False, description="Solo auditorías activas"),
    current_user: dict = Depends(require_permission("AUDITORIA_VER"))
):
    """Lista auditorías programadas."""
    db = get_db()
    service = AuditoriaProgramadaService(db)
    
    auditorias = service.listar(
        sucursal_id=sucursal_id,
        solo_activas=solo_activas
    )
    
    activas = sum(1 for a in auditorias if a.get("activo"))
    inactivas = len(auditorias) - activas
    
    return {
        "items": auditorias,
        "total": len(auditorias),
        "activas": activas,
        "inactivas": inactivas
    }


@router.get(
    "/kpis",
    summary="KPIs de auditorías",
    description="Obtiene métricas agregadas de auditorías programadas. Requiere AUDITORIA_VER."
)
async def obtener_kpis(
    current_user: dict = Depends(require_permission("AUDITORIA_VER"))
):
    """Obtiene KPIs de auditorías."""
    db = get_db()
    service = AuditoriaProgramadaService(db)
    return service.obtener_kpis()


@router.get(
    "/calendario",
    summary="Calendario de auditorías",
    description="Obtiene vista calendario de auditorías programadas. Requiere AUDITORIA_VER."
)
async def obtener_calendario(
    anio: int = Query(..., ge=2020, le=2100),
    mes: int = Query(..., ge=1, le=12),
    current_user: dict = Depends(require_permission("AUDITORIA_VER"))
):
    """Obtiene calendario de auditorías."""
    db = get_db()
    service = AuditoriaProgramadaService(db)
    return service.obtener_calendario(anio, mes)


@router.get(
    "/historial",
    summary="Historial de ejecuciones",
    description="Obtiene historial de ejecuciones de auditorías. Requiere AUDITORIA_VER."
)
async def obtener_historial(
    auditoria_id: Optional[str] = Query(None, description="Filtrar por auditoría"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    dias: int = Query(30, ge=1, le=365, description="Días hacia atrás"),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_permission("AUDITORIA_VER"))
):
    """Obtiene historial de ejecuciones."""
    db = get_db()
    service = AuditoriaProgramadaService(db)
    
    logs = service.obtener_historial(
        auditoria_id=auditoria_id,
        estado=estado,
        dias=dias,
        limit=limit
    )
    
    return {"items": logs, "total": len(logs)}


@router.get(
    "/{auditoria_id}",
    summary="Obtener auditoría",
    description="Obtiene una auditoría programada por ID. Requiere AUDITORIA_VER."
)
async def obtener_auditoria(
    auditoria_id: str,
    current_user: dict = Depends(require_permission("AUDITORIA_VER"))
):
    """Obtiene una auditoría por ID."""
    try:
        db = get_db()
        service = AuditoriaProgramadaService(db)
        return service.obtener(auditoria_id)
    except AuditoriaNoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "",
    response_model=OperacionResponse,
    status_code=201,
    summary="Crear auditoría programada",
    description="Crea una nueva auditoría programada. Requiere AUDITORIA_PROGRAMAR."
)
async def crear_auditoria(
    request: AuditoriaProgramadaCreate,
    current_user: dict = Depends(require_permission("AUDITORIA_PROGRAMAR"))
):
    """Crea una nueva auditoría programada."""
    try:
        db = get_db()
        service = AuditoriaProgramadaService(db)
        
        auditoria = service.crear(request)
        
        return OperacionResponse(
            success=True,
            message=f"Auditoría programada creada: {auditoria['nombre']}",
            data=auditoria
        )
    except ConfiguracionInvalidaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/{auditoria_id}",
    response_model=OperacionResponse,
    summary="Actualizar auditoría",
    description="Actualiza una auditoría programada. Requiere AUDITORIA_PROGRAMAR."
)
async def actualizar_auditoria(
    auditoria_id: str,
    request: AuditoriaProgramadaUpdate,
    current_user: dict = Depends(require_permission("AUDITORIA_PROGRAMAR"))
):
    """Actualiza una auditoría programada."""
    try:
        db = get_db()
        service = AuditoriaProgramadaService(db)
        
        auditoria = service.actualizar(auditoria_id, request)
        
        return OperacionResponse(
            success=True,
            message="Auditoría actualizada",
            data=auditoria
        )
    except AuditoriaNoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConfiguracionInvalidaError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{auditoria_id}",
    response_model=OperacionResponse,
    summary="Eliminar auditoría",
    description="Elimina una auditoría programada. Requiere AUDITORIAS_GESTIONAR."
)
async def eliminar_auditoria(
    auditoria_id: str,
    current_user: dict = Depends(require_explicit_permission("AUDITORIAS_GESTIONAR"))
):
    """Elimina una auditoría programada."""
    try:
        db = get_db()
        service = AuditoriaProgramadaService(db)
        
        service.eliminar(auditoria_id)
        
        return OperacionResponse(
            success=True,
            message="Auditoría eliminada"
        )
    except AuditoriaNoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# ACCIONES
# =============================================================================

@router.post(
    "/{auditoria_id}/activar",
    response_model=OperacionResponse,
    summary="Activar auditoría",
    description="Activa una auditoría programada. Requiere AUDITORIA_PROGRAMAR."
)
async def activar_auditoria(
    auditoria_id: str,
    current_user: dict = Depends(require_permission("AUDITORIA_PROGRAMAR"))
):
    """Activa una auditoría programada."""
    try:
        db = get_db()
        service = AuditoriaProgramadaService(db)
        
        auditoria = service.activar(auditoria_id)
        
        return OperacionResponse(
            success=True,
            message="Auditoría activada",
            data=auditoria
        )
    except AuditoriaNoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{auditoria_id}/desactivar",
    response_model=OperacionResponse,
    summary="Desactivar auditoría",
    description="Desactiva una auditoría programada. Requiere AUDITORIA_PROGRAMAR."
)
async def desactivar_auditoria(
    auditoria_id: str,
    current_user: dict = Depends(require_permission("AUDITORIA_PROGRAMAR"))
):
    """Desactiva una auditoría programada."""
    try:
        db = get_db()
        service = AuditoriaProgramadaService(db)
        
        auditoria = service.desactivar(auditoria_id)
        
        return OperacionResponse(
            success=True,
            message="Auditoría desactivada",
            data=auditoria
        )
    except AuditoriaNoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{auditoria_id}/ejecutar",
    response_model=OperacionResponse,
    summary="Ejecutar auditoría manualmente",
    description="Ejecuta una auditoría de forma manual. Requiere AUDITORIAS_GESTIONAR."
)
async def ejecutar_auditoria(
    auditoria_id: str,
    current_user: dict = Depends(require_explicit_permission("AUDITORIAS_GESTIONAR"))
):
    """Ejecuta una auditoría manualmente."""
    try:
        db = get_db()
        service = AuditoriaProgramadaService(db)
        
        usuario_id = current_user.get("user_id", "unknown")
        resultado = service.ejecutar_manual(auditoria_id, usuario_id)
        
        if resultado.get("estado") == "COMPLETADA":
            return OperacionResponse(
                success=True,
                message=f"Auditoría ejecutada. Workflow: {resultado.get('workflow_id')}",
                data=resultado
            )
        else:
            return OperacionResponse(
                success=False,
                message=f"Error en ejecución: {resultado.get('error_detalle')}",
                data=resultado
            )
    except AuditoriaNoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EjecucionDuplicadaError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
