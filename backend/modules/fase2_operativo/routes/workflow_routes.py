from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Endpoints de Workflows
CAB-003 | EDARSA HUB - Fase 2A
PROTEGIDO CON RBAC (Fase 3.1)

Expone la funcionalidad de workflows vía HTTP.

Permisos:
- Todos los endpoints requieren autenticación
- Los datos se filtran por empresas_permitidas del usuario
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from ..services.workflow_service import (
    WorkflowService,
    WorkflowNoEncontradoError,
    TransicionInvalidaError,
    WorkflowYaExisteError
)
from ..services.operativo_service import OperativoService
from ..api_schemas import (
    WorkflowCreateRequest,
    WorkflowEstadoRequest,
    WorkflowEscalarRequest,
    OperacionResponse
)
from ..schemas.enums import EstadoWorkflow
from ..db_utils import get_database

# RBAC - Fase 3.1
from core.security import get_current_user, get_user_empresas_permitidas, get_servers_for_empresas

router = APIRouter()


def get_db():
    """Obtiene conexión a la base de datos."""
    return get_database()


async def get_user_server_ids(current_user: Dict[str, Any]) -> list:
    """Obtiene los server_ids permitidos para el usuario."""
    empresas_permitidas = await get_user_empresas_permitidas(current_user)
    if not empresas_permitidas:
        return []
    return await get_servers_for_empresas(empresas_permitidas)


@router.post("", response_model=OperacionResponse, status_code=201)
async def crear_workflow(
    request: WorkflowCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Crea un nuevo workflow para un folio procesado.
    PROTEGIDO: Requiere autenticación.
    
    - **procesado_id**: ID del folio procesado (de Fase 1)
    - **diferencias**: Lista opcional de diferencias a asociar
    - **usuario_revisor_id**: Usuario a asignar para revisión inicial (opcional)
    """
    try:
        db = get_db()
        operativo_svc = OperativoService(db)
        
        resultado = await operativo_svc.iniciar_workflow_completo(
            procesado_id=request.procesado_id,
            diferencias=request.diferencias or [],
            usuario_asignador_id=request.usuario_revisor_id,
            usuario_revisor_id=request.usuario_revisor_id
        )
        
        return OperacionResponse(
            success=True,
            message="Workflow creado exitosamente",
            data=resultado
        )
    except WorkflowYaExisteError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}")
async def obtener_workflow(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene un workflow por su ID con sus diferencias asociadas.
    PROTEGIDO: Requiere autenticación.
    """
    try:
        db = get_db()
        workflow_svc = WorkflowService(db)
        
        workflow = await workflow_svc.obtener_workflow_completo(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow no encontrado: {workflow_id}")
        
        # Verificar acceso por server_id
        server_ids = await get_user_server_ids(current_user)
        workflow_server = workflow.get("server_id")
        if workflow_server and server_ids and workflow_server not in server_ids:
            raise HTTPException(status_code=403, detail="No tiene acceso a este workflow")
        
        return workflow
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def listar_workflows(
    estado: Optional[EstadoWorkflow] = Query(None, description="Filtrar por estado"),
    procesado_id: Optional[str] = Query(None, description="Filtrar por procesado_id"),
    unidad: Optional[str] = Query(None, description="Unidad de negocio canónica (unidad_codigo o id). Contrato nuevo."),
    server_id: Optional[str] = Query(None, description="DEPRECATED: usar 'unidad'. Compatibilidad temporal."),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(50, ge=1, le=100, description="Límite de registros"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Lista workflows con filtros opcionales.
    PROTEGIDO: Requiere autenticación y filtra por empresas_permitidas.
    Contrato canónico: el frontend envía **unidad**; el backend resuelve server_id/sucursal.
    """
    try:
        from core.corporate_filters.request_resolver import resolve_unidad_scope
        db = get_db()
        workflow_svc = WorkflowService(db)
        
        if procesado_id:
            workflow = await workflow_svc.obtener_workflow_por_procesado_id(procesado_id)
            if workflow:
                return {"items": [workflow], "total": 1}
            return {"items": [], "total": 0}
        
        resultado = await workflow_svc.listar_workflows(estado, skip, limit)
        
        # Filtro por unidad de negocio canónica (post-filtro: el item ya trae
        # servidor_id y sucursal_id). El backend resuelve el scope, no el frontend.
        if (unidad or server_id) and isinstance(resultado, dict) and isinstance(resultado.get("items"), list):
            scope = await resolve_unidad_scope(current_user, unidad=unidad, server_id_legacy=server_id)
            target_server = scope.server_id
            labels = set(l.lower() for l in (scope.sucursal_labels or []))
            
            def _match(w):
                if scope.access_denied:
                    return False
                if str(w.get("servidor_id") or "") != str(target_server or ""):
                    return False
                # Desambiguar por sucursal solo si el server aloja >1 unidad (MPRO)
                if labels:
                    return str(w.get("sucursal_id") or "").lower() in labels
                return True
            
            items = [w for w in resultado["items"] if _match(w)]
            resultado = {"items": items, "total": len(items)}
        
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{workflow_id}/estado", response_model=OperacionResponse)
async def cambiar_estado_workflow(
    workflow_id: str,
    request: WorkflowEstadoRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Cambia el estado de un workflow.
    PROTEGIDO: Requiere autenticación.
    
    Las transiciones válidas son:
    - PENDIENTE_ASIGNACION → EN_REVISION
    - EN_REVISION → PENDIENTE_JUSTIFICACION, ESCALADO
    - PENDIENTE_JUSTIFICACION → JUSTIFICADO, ESCALADO
    - JUSTIFICADO → EN_AUDITORIA
    - EN_AUDITORIA → CERRADO, PENDIENTE_JUSTIFICACION
    - ESCALADO → CERRADO
    """
    try:
        db = get_db()
        workflow_svc = WorkflowService(db)
        
        workflow = await workflow_svc.cambiar_estado(workflow_id, request.nuevo_estado)
        
        return OperacionResponse(
            success=True,
            message=f"Estado cambiado a {request.nuevo_estado.value}",
            data=workflow
        )
    except WorkflowNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TransicionInvalidaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/escalar", response_model=OperacionResponse)
async def escalar_workflow(
    workflow_id: str,
    request: WorkflowEscalarRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Escala un workflow para atención especial.
    PROTEGIDO: Requiere autenticación.
    """
    try:
        db = get_db()
        operativo_svc = OperativoService(db)
        
        resultado = await operativo_svc.escalar_workflow(
            workflow_id=workflow_id,
            motivo=request.motivo,
            usuario_id=request.usuario_id
        )
        
        return OperacionResponse(
            success=True,
            message="Workflow escalado exitosamente",
            data=resultado
        )
    except WorkflowNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TransicionInvalidaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/resumen")
async def obtener_resumen_workflow(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene un resumen del estado del workflow incluyendo
    conteo de justificaciones y estado de completitud.
    PROTEGIDO: Requiere autenticación.
    """
    try:
        db = get_db()
        workflow_svc = WorkflowService(db)
        from ..services.justificacion_service import JustificacionService
        
        workflow = await workflow_svc.obtener_workflow_completo(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow no encontrado: {workflow_id}")
        
        just_svc = JustificacionService(db)
        estado_justificacion = await just_svc.verificar_workflow_completamente_justificado(workflow_id)
        
        return {
            "workflow": workflow,
            "estado_justificacion": estado_justificacion
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
