"""
Endpoints de Auditorías Programadas
EDARSA HUB - Módulo Auditorías Programadas
PROTEGIDO CON RBAC

Permisos:
- AUDITORIA_VER: Ver programaciones, historial, KPIs, calendario
- AUDITORIAS_PROGRAMAR: Crear, editar, activar/desactivar
- AUDITORIAS_GESTIONAR: Ejecutar manualmente, eliminar
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
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
from ..access import (
    AUDITORIA_READ_PERMISSIONS,
    AUDITORIAS_GESTIONAR,
    AUDITORIAS_PROGRAMAR,
    resolve_operativo_unit_filter,
)

# RBAC
from core.rbac.middleware import require_any_permission, require_explicit_permission

router = APIRouter()


def get_db():
    """Obtiene conexión a la base de datos."""
    return get_database()


def _get_authenticated_actor_id(current_user: dict) -> str:
    usuario_id = str(
        current_user.get("id")
        or current_user.get("user_id")
        or current_user.get("sub")
        or current_user.get("email")
        or ""
    ).strip()
    if not usuario_id:
        raise HTTPException(
            status_code=403,
            detail="No fue posible resolver identidad RBAC del usuario autenticado"
        )
    return usuario_id


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
    unidad_negocio_pk: Optional[str] = Query(None, description="Filtrar por unidad de negocio canónica"),
    solo_activas: bool = Query(False, description="Solo auditorías activas"),
    current_user: dict = Depends(require_any_permission(list(AUDITORIA_READ_PERMISSIONS)))
):
    """Lista auditorías programadas."""
    db = get_db()
    service = AuditoriaProgramadaService(db)
    unidad_pk, unidades_permitidas = resolve_operativo_unit_filter(
        current_user,
        unidad_negocio_pk or sucursal_id,
        AUDITORIA_READ_PERMISSIONS,
    )
    
    auditorias = service.listar(
        sucursal_id=None if unidad_pk else sucursal_id,
        solo_activas=solo_activas,
        unidad_negocio_pk=unidad_pk,
        unidades_permitidas=unidades_permitidas,
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
    unidad_negocio_pk: Optional[str] = Query(None, description="Filtrar por unidad de negocio canónica"),
    current_user: dict = Depends(require_any_permission(list(AUDITORIA_READ_PERMISSIONS)))
):
    """Obtiene KPIs de auditorías."""
    db = get_db()
    service = AuditoriaProgramadaService(db)
    unidad_pk, unidades_permitidas = resolve_operativo_unit_filter(
        current_user,
        unidad_negocio_pk,
        AUDITORIA_READ_PERMISSIONS,
    )
    return service.obtener_kpis(
        unidad_negocio_pk=unidad_pk,
        unidades_permitidas=unidades_permitidas,
    )


@router.get(
    "/calendario",
    summary="Calendario de auditorías",
    description="Obtiene vista calendario de auditorías programadas. Requiere AUDITORIA_VER."
)
async def obtener_calendario(
    anio: int = Query(..., ge=2020, le=2100),
    mes: int = Query(..., ge=1, le=12),
    unidad_negocio_pk: Optional[str] = Query(None, description="Filtrar por unidad de negocio canónica"),
    current_user: dict = Depends(require_any_permission(list(AUDITORIA_READ_PERMISSIONS)))
):
    """Obtiene calendario de auditorías."""
    db = get_db()
    service = AuditoriaProgramadaService(db)
    unidad_pk, unidades_permitidas = resolve_operativo_unit_filter(
        current_user,
        unidad_negocio_pk,
        AUDITORIA_READ_PERMISSIONS,
    )
    return service.obtener_calendario(
        anio,
        mes,
        unidad_negocio_pk=unidad_pk,
        unidades_permitidas=unidades_permitidas,
    )


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
    unidad_negocio_pk: Optional[str] = Query(None, description="Filtrar por unidad de negocio canónica"),
    current_user: dict = Depends(require_any_permission(list(AUDITORIA_READ_PERMISSIONS)))
):
    """Obtiene historial de ejecuciones."""
    db = get_db()
    service = AuditoriaProgramadaService(db)
    unidad_pk, unidades_permitidas = resolve_operativo_unit_filter(
        current_user,
        unidad_negocio_pk,
        AUDITORIA_READ_PERMISSIONS,
    )
    
    logs = service.obtener_historial(
        auditoria_id=auditoria_id,
        estado=estado,
        dias=dias,
        limit=limit,
        unidad_negocio_pk=unidad_pk,
        unidades_permitidas=unidades_permitidas,
    )
    
    return {"items": logs, "total": len(logs)}


@router.get(
    "/{auditoria_id}",
    summary="Obtener auditoría",
    description="Obtiene una auditoría programada por ID. Requiere AUDITORIA_VER."
)
async def obtener_auditoria(
    auditoria_id: str,
    current_user: dict = Depends(require_any_permission(list(AUDITORIA_READ_PERMISSIONS)))
):
    """Obtiene una auditoría por ID."""
    try:
        db = get_db()
        service = AuditoriaProgramadaService(db)
        _, unidades_permitidas = resolve_operativo_unit_filter(
            current_user,
            None,
            AUDITORIA_READ_PERMISSIONS,
        )
        return service.obtener(auditoria_id, unidades_permitidas)
    except AuditoriaNoEncontradaError as e:
        raise HTTPException(status_code=404, detail="Error interno del servidor")


@router.post(
    "",
    response_model=OperacionResponse,
    status_code=201,
    summary="Crear auditoría programada",
    description="Crea una nueva auditoría programada. Requiere AUDITORIAS_PROGRAMAR."
)
async def crear_auditoria(
    request: AuditoriaProgramadaCreate,
    current_user: dict = Depends(require_explicit_permission(AUDITORIAS_PROGRAMAR))
):
    """Crea una nueva auditoría programada."""
    try:
        db = get_db()
        service = AuditoriaProgramadaService(db)
        unidad_pk, _ = resolve_operativo_unit_filter(
            current_user,
            request.unidad_negocio_pk or request.sucursal_id or request.server_id,
            (AUDITORIAS_PROGRAMAR,),
        )
        
        request_autenticado = request.model_copy(
            update={"created_by": _get_authenticated_actor_id(current_user)}
        )
        auditoria = service.crear(request_autenticado, unidad_negocio_pk=unidad_pk)
        
        return OperacionResponse(
            success=True,
            message=f"Auditoría programada creada: {auditoria['nombre']}",
            data=auditoria
        )
    except HTTPException:
        raise
    except ConfiguracionInvalidaError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.put(
    "/{auditoria_id}",
    response_model=OperacionResponse,
    summary="Actualizar auditoría",
    description="Actualiza una auditoría programada. Requiere AUDITORIAS_PROGRAMAR."
)
async def actualizar_auditoria(
    auditoria_id: str,
    request: AuditoriaProgramadaUpdate,
    current_user: dict = Depends(require_explicit_permission(AUDITORIAS_PROGRAMAR))
):
    """Actualiza una auditoría programada."""
    try:
        db = get_db()
        service = AuditoriaProgramadaService(db)
        unidad_ref = request.unidad_negocio_pk or request.sucursal_id or request.server_id
        if unidad_ref:
            resolve_operativo_unit_filter(
                current_user,
                unidad_ref,
                (AUDITORIAS_PROGRAMAR,),
            )
        _, unidades_permitidas = resolve_operativo_unit_filter(
            current_user,
            None,
            (AUDITORIAS_PROGRAMAR,),
        )
        
        auditoria = service.actualizar(
            auditoria_id,
            request,
            unidades_permitidas=unidades_permitidas,
        )
        
        return OperacionResponse(
            success=True,
            message="Auditoría actualizada",
            data=auditoria
        )
    except AuditoriaNoEncontradaError as e:
        raise HTTPException(status_code=404, detail="Error interno del servidor")
    except ConfiguracionInvalidaError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")


@router.delete(
    "/{auditoria_id}",
    response_model=OperacionResponse,
    summary="Eliminar auditoría",
    description="Elimina una auditoría programada. Requiere AUDITORIAS_GESTIONAR."
)
async def eliminar_auditoria(
    auditoria_id: str,
    current_user: dict = Depends(require_explicit_permission(AUDITORIAS_GESTIONAR))
):
    """Elimina una auditoría programada."""
    try:
        db = get_db()
        service = AuditoriaProgramadaService(db)
        _, unidades_permitidas = resolve_operativo_unit_filter(
            current_user,
            None,
            (AUDITORIAS_GESTIONAR,),
        )
        
        service.eliminar(auditoria_id, unidades_permitidas)
        
        return OperacionResponse(
            success=True,
            message="Auditoría eliminada"
        )
    except AuditoriaNoEncontradaError as e:
        raise HTTPException(status_code=404, detail="Error interno del servidor")


# =============================================================================
# ACCIONES
# =============================================================================

@router.post(
    "/{auditoria_id}/activar",
    response_model=OperacionResponse,
    summary="Activar auditoría",
    description="Activa una auditoría programada. Requiere AUDITORIAS_PROGRAMAR."
)
async def activar_auditoria(
    auditoria_id: str,
    current_user: dict = Depends(require_explicit_permission(AUDITORIAS_PROGRAMAR))
):
    """Activa una auditoría programada."""
    try:
        db = get_db()
        service = AuditoriaProgramadaService(db)
        _, unidades_permitidas = resolve_operativo_unit_filter(
            current_user,
            None,
            (AUDITORIAS_PROGRAMAR,),
        )
        
        auditoria = service.activar(auditoria_id, unidades_permitidas)
        
        return OperacionResponse(
            success=True,
            message="Auditoría activada",
            data=auditoria
        )
    except AuditoriaNoEncontradaError as e:
        raise HTTPException(status_code=404, detail="Error interno del servidor")


@router.post(
    "/{auditoria_id}/desactivar",
    response_model=OperacionResponse,
    summary="Desactivar auditoría",
    description="Desactiva una auditoría programada. Requiere AUDITORIAS_PROGRAMAR."
)
async def desactivar_auditoria(
    auditoria_id: str,
    current_user: dict = Depends(require_explicit_permission(AUDITORIAS_PROGRAMAR))
):
    """Desactiva una auditoría programada."""
    try:
        db = get_db()
        service = AuditoriaProgramadaService(db)
        _, unidades_permitidas = resolve_operativo_unit_filter(
            current_user,
            None,
            (AUDITORIAS_PROGRAMAR,),
        )
        
        auditoria = service.desactivar(auditoria_id, unidades_permitidas)
        
        return OperacionResponse(
            success=True,
            message="Auditoría desactivada",
            data=auditoria
        )
    except AuditoriaNoEncontradaError as e:
        raise HTTPException(status_code=404, detail="Error interno del servidor")


@router.post(
    "/{auditoria_id}/ejecutar",
    response_model=OperacionResponse,
    summary="Ejecutar auditoría manualmente",
    description="Ejecuta una auditoría de forma manual. Requiere AUDITORIAS_GESTIONAR."
)
async def ejecutar_auditoria(
    auditoria_id: str,
    current_user: dict = Depends(require_explicit_permission(AUDITORIAS_GESTIONAR))
):
    """Ejecuta una auditoría manualmente."""
    try:
        db = get_db()
        service = AuditoriaProgramadaService(db)
        _, unidades_permitidas = resolve_operativo_unit_filter(
            current_user,
            None,
            (AUDITORIAS_GESTIONAR,),
        )
        
        usuario_id = current_user.get("id") or current_user.get("user_id") or current_user.get("email") or "unknown"
        resultado = service.ejecutar_manual(auditoria_id, usuario_id, unidades_permitidas)
        
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
    except HTTPException:
        raise
    except AuditoriaNoEncontradaError as e:
        raise HTTPException(status_code=404, detail="Error interno del servidor")
    except EjecucionDuplicadaError as e:
        raise HTTPException(status_code=409, detail="Error interno del servidor")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")
