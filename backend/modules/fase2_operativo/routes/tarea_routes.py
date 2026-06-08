from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Endpoints de Tareas
CAB-003 | EDARSA HUB - Fase 2A
PROTEGIDO CON RBAC (Fase 3.1)

Expone la funcionalidad de tareas vía HTTP.

Permisos:
- Todos los endpoints requieren autenticación
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict, Any
from ..services.tarea_service import (
    TareaService,
    TareaNoEncontradaError,
    TareaYaCompletadaError
)
from ..api_schemas import (
    TareaCreateRequest,
    TareaAsignarRequest,
    TareaReasignarRequest,
    OperacionResponse
)
from ..schemas.enums import EstadoTarea
from ..db_utils import get_database

# RBAC - Fase 3.1
from core.security import get_current_user

router = APIRouter()


def get_db():
    """Obtiene conexión a la base de datos."""
    return get_database()


@router.post("", response_model=OperacionResponse, status_code=201)
async def crear_tarea(
    request: TareaCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Crea una nueva tarea para un workflow.
    PROTEGIDO: Requiere autenticación.
    
    - **workflow_id**: ID del workflow asociado
    - **tipo_tarea**: REVISAR, JUSTIFICAR, AUDITAR o ESCALAR
    - **usuario_asignado_id**: Usuario a asignar (opcional)
    """
    try:
        db = get_db()
        tarea_svc = TareaService(db)
        
        tarea = await tarea_svc.crear_tarea(
            workflow_id=request.workflow_id,
            tipo_tarea=request.tipo_tarea,
            usuario_asignado_id=request.usuario_asignado_id
        )
        
        return OperacionResponse(
            success=True,
            message="Tarea creada exitosamente",
            data=tarea
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tarea_id}")
async def obtener_tarea(
    tarea_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene una tarea por su ID.
    PROTEGIDO: Requiere autenticación.
    """
    try:
        db = get_db()
        tarea_svc = TareaService(db)
        
        tarea = await tarea_svc.obtener_tarea(tarea_id)
        if not tarea:
            raise HTTPException(status_code=404, detail=f"Tarea no encontrada: {tarea_id}")
        
        return tarea
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def listar_tareas(
    usuario_id: Optional[str] = Query(None, description="Filtrar por usuario asignado"),
    workflow_id: Optional[str] = Query(None, description="Filtrar por workflow"),
    estado: Optional[EstadoTarea] = Query(None, description="Filtrar por estado"),
    vencidas: bool = Query(False, description="Solo tareas vencidas"),
    pendientes: bool = Query(False, description="Solo tareas pendientes"),
    unidad: Optional[str] = Query(None, description="Unidad de negocio canónica (unidad_codigo o id). Contrato nuevo."),
    server_id: Optional[str] = Query(None, description="DEPRECATED: usar 'unidad'. Compatibilidad temporal."),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Lista tareas con filtros opcionales.
    PROTEGIDO: Requiere autenticación.
    Contrato canónico: el frontend envía **unidad**; el backend resuelve el scope
    a los workflows de esa unidad (Tareas_Inventario no tiene server_id directo).
    """
    try:
        db = get_db()
        tarea_svc = TareaService(db)
        
        # Resolver scope canónico → workflow uuids de la unidad (puerta única)
        from core.corporate_filters.request_resolver import resolve_unidad_scope
        from ..services.workflow_service import WorkflowService
        workflow_uuids = None
        if unidad or server_id:
            scope = await resolve_unidad_scope(current_user, unidad=unidad, server_id_legacy=server_id)
            workflow_uuids = await WorkflowService(db).get_uuids_by_servers(
                server_ids=scope.effective_server_ids,
                sucursal_ids=scope.sucursal_labels
            )
        
        if vencidas:
            tareas = await tarea_svc.obtener_tareas_vencidas(workflow_ids=workflow_uuids)
            return {"items": tareas, "total": len(tareas)}
        
        if usuario_id:
            tareas = await tarea_svc.obtener_tareas_por_usuario(usuario_id, solo_pendientes=pendientes)
            return {"items": tareas, "total": len(tareas)}
        
        if workflow_id:
            tareas = await tarea_svc.obtener_tareas_workflow(workflow_id)
            return {"items": tareas, "total": len(tareas)}
        
        if pendientes:
            tareas = await tarea_svc.obtener_tareas_pendientes(limit, workflow_ids=workflow_uuids)
            return {"items": tareas, "total": len(tareas)}
        
        # Sin filtros específicos, listar todas pendientes
        tareas = await tarea_svc.obtener_tareas_pendientes(limit, workflow_ids=workflow_uuids)
        return {"items": tareas, "total": len(tareas)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{tarea_id}/asignar", response_model=OperacionResponse)
async def asignar_tarea(
    tarea_id: str,
    request: TareaAsignarRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Asigna una tarea a un usuario.
    PROTEGIDO: Requiere autenticación.
    """
    try:
        db = get_db()
        tarea_svc = TareaService(db)
        
        tarea = await tarea_svc.asignar_tarea(
            tarea_id=tarea_id,
            usuario_asignado_id=request.usuario_asignado_id,
            asignado_por_id=request.asignado_por_id,
            fecha_limite=request.fecha_limite
        )
        
        return OperacionResponse(
            success=True,
            message="Tarea asignada exitosamente",
            data=tarea
        )
    except TareaNoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{tarea_id}/reasignar", response_model=OperacionResponse)
async def reasignar_tarea(
    tarea_id: str,
    request: TareaReasignarRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Reasigna una tarea a otro usuario con motivo obligatorio.
    PROTEGIDO: Requiere autenticación.
    """
    try:
        db = get_db()
        tarea_svc = TareaService(db)
        
        tarea = await tarea_svc.reasignar_tarea(
            tarea_id=tarea_id,
            usuario_nuevo_id=request.usuario_nuevo_id,
            motivo=request.motivo,
            cambiado_por_id=request.cambiado_por_id
        )
        
        return OperacionResponse(
            success=True,
            message="Tarea reasignada exitosamente",
            data=tarea
        )
    except TareaNoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TareaYaCompletadaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{tarea_id}/completar", response_model=OperacionResponse)
async def completar_tarea(
    tarea_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Marca una tarea como completada.
    PROTEGIDO: Requiere autenticación.
    """
    try:
        db = get_db()
        tarea_svc = TareaService(db)
        
        tarea = await tarea_svc.completar_tarea(tarea_id)
        
        return OperacionResponse(
            success=True,
            message="Tarea completada exitosamente",
            data=tarea
        )
    except TareaNoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TareaYaCompletadaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{tarea_id}/en-progreso", response_model=OperacionResponse)
async def marcar_en_progreso(
    tarea_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Marca una tarea como en progreso.
    PROTEGIDO: Requiere autenticación.
    """
    try:
        db = get_db()
        tarea_svc = TareaService(db)
        
        tarea = await tarea_svc.marcar_en_progreso(tarea_id)
        
        return OperacionResponse(
            success=True,
            message="Tarea marcada en progreso",
            data=tarea
        )
    except TareaNoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tarea_id}/historial")
async def obtener_historial_tarea(
    tarea_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene el historial de asignaciones de una tarea.
    PROTEGIDO: Requiere autenticación.
    """
    try:
        db = get_db()
        tarea_svc = TareaService(db)
        
        historial = await tarea_svc.obtener_historial_tarea(tarea_id)
        return {"historial": historial, "total": len(historial)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marcar-vencidas", response_model=OperacionResponse)
async def marcar_tareas_vencidas(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Marca como vencidas todas las tareas que excedieron su fecha límite.
    PROTEGIDO: Requiere autenticación (operación administrativa).
    """
    try:
        db = get_db()
        tarea_svc = TareaService(db)
        
        cantidad = await tarea_svc.marcar_vencidas()
        
        return OperacionResponse(
            success=True,
            message=f"{cantidad} tareas marcadas como vencidas",
            data={"tareas_marcadas": cantidad}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
