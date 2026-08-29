from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Endpoints de Auditoría
CAB-003 | EDARSA HUB - Fase 2A
PROTEGIDO CON RBAC (Fase 3.1)

Expone la funcionalidad de auditoría vía HTTP.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict, Any
from ..services.auditoria_service import (
    AuditoriaService,
    WorkflowNoEnAuditoriaError,
    DecisionInvalidaError
)
from ..services.operativo_service import OperativoService
from ..api_schemas import DecisionAuditoriaRequest, OperacionResponse
from ..schemas.enums import DecisionAuditoria
from ..db_utils import get_database

# RBAC - Fase 3.1
from core.security import get_current_user

router = APIRouter()


def get_db():
    """Obtiene conexión a la base de datos."""
    return get_database()


@router.post("/decisiones", response_model=OperacionResponse, status_code=201)
async def registrar_decision(
    request: DecisionAuditoriaRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Registra una decisión de auditoría.
    
    Decisiones posibles:
    - **APROBADO**: Cierra el workflow
    - **RECHAZADO**: Cierra el workflow
    - **DEVUELTO_PARA_CORRECCION**: Vuelve a PENDIENTE_JUSTIFICACION
    """
    try:
        db = get_db()
        audit_svc = AuditoriaService(db)
        
        decision = await audit_svc.registrar_decision(
            workflow_id=request.workflow_id,
            decision=request.decision,
            comentarios_auditor=request.comentarios_auditor,
            usuario_auditor_id=request.usuario_auditor_id,
            requiere_accion_adicional=request.requiere_accion_adicional
        )
        
        return OperacionResponse(
            success=True,
            message=f"Decisión {request.decision.value} registrada exitosamente",
            data=decision
        )
    except WorkflowNoEnAuditoriaError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except DecisionInvalidaError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/decisiones/procesar", response_model=OperacionResponse)
async def procesar_decision_completa(
    request: DecisionAuditoriaRequest,
    tarea_id: str = Query(..., description="ID de la tarea de auditoría a completar"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Procesa una decisión de auditoría y actualiza el workflow completo.
    
    Esta operación:
    1. Registra la decisión
    2. Completa la tarea de auditoría
    3. Actualiza el estado del workflow
    4. Si es DEVUELTO_PARA_CORRECCION, crea nueva tarea de justificación
    """
    try:
        db = get_db()
        operativo_svc = OperativoService(db)
        
        resultado = await operativo_svc.procesar_decision_auditoria(
            workflow_id=request.workflow_id,
            tarea_id=tarea_id,
            decision=request.decision,
            comentarios=request.comentarios_auditor,
            auditor_id=request.usuario_auditor_id,
            requiere_accion=request.requiere_accion_adicional
        )
        
        return OperacionResponse(
            success=True,
            message=f"Decisión procesada: {request.decision.value}",
            data=resultado
        )
    except WorkflowNoEnAuditoriaError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except DecisionInvalidaError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/decisiones/{decision_id}")
async def obtener_decision(
    decision_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene una decisión de auditoría por su ID.
    """
    try:
        db = get_db()
        audit_svc = AuditoriaService(db)
        
        decision = await audit_svc.obtener_decision(decision_id)
        if not decision:
            raise HTTPException(status_code=404, detail=f"Decisión no encontrada: {decision_id}")
        
        return decision
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/workflow/{workflow_id}/decisiones")
async def obtener_decisiones_workflow(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene todas las decisiones de auditoría de un workflow.
    """
    try:
        db = get_db()
        audit_svc = AuditoriaService(db)
        
        decisiones = await audit_svc.obtener_decisiones_workflow(workflow_id)
        return {"items": decisiones, "total": len(decisiones)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/workflow/{workflow_id}/ultima-decision")
async def obtener_ultima_decision(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene la última decisión de auditoría de un workflow.
    """
    try:
        db = get_db()
        audit_svc = AuditoriaService(db)
        
        decision = await audit_svc.obtener_ultima_decision(workflow_id)
        if not decision:
            return {"decision": None, "message": "No hay decisiones para este workflow"}
        
        return decision
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/pendientes")
async def obtener_pendientes_auditoria(
    limit: int = Query(50, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene workflows que están pendientes de auditoría.
    """
    try:
        db = get_db()
        audit_svc = AuditoriaService(db)
        
        workflows = await audit_svc.obtener_workflows_pendientes_auditoria(limit)
        return {"items": workflows, "total": len(workflows)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/resumen")
async def obtener_resumen_auditoria(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene resumen de decisiones de auditoría por tipo.
    """
    try:
        db = get_db()
        audit_svc = AuditoriaService(db)
        
        resumen = await audit_svc.resumen_por_decision()
        pendientes = await audit_svc.obtener_workflows_pendientes_auditoria()
        
        return {
            "decisiones_por_tipo": resumen,
            "workflows_pendientes_auditoria": len(pendientes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("")
async def listar_decisiones(
    workflow_id: Optional[str] = Query(None, description="Filtrar por workflow"),
    auditor_id: Optional[str] = Query(None, description="Filtrar por auditor"),
    decision: Optional[DecisionAuditoria] = Query(None, description="Filtrar por tipo de decisión"),
    limit: int = Query(50, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Lista decisiones de auditoría con filtros opcionales.
    """
    try:
        db = get_db()
        audit_svc = AuditoriaService(db)
        
        if workflow_id:
            decisiones = await audit_svc.obtener_decisiones_workflow(workflow_id)
            return {"items": decisiones, "total": len(decisiones)}
        
        if auditor_id:
            decisiones = await audit_svc.listar_por_auditor(auditor_id, limit)
            return {"items": decisiones, "total": len(decisiones)}
        
        if decision:
            decisiones = await audit_svc.listar_por_decision(decision, limit)
            return {"items": decisiones, "total": len(decisiones)}
        
        return {"items": [], "total": 0, "message": "Proporcione al menos un filtro"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")
