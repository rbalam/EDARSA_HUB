"""
Endpoints de Justificaciones
CAB-003 | EDARSA HUB - Fase 2A

Expone la funcionalidad de justificaciones vía HTTP.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..services.justificacion_service import (
    JustificacionService,
    JustificacionInvalidaError,
    EvidenciaRequeridaError,
    JustificacionYaExisteError
)
from ..services.operativo_service import OperativoService
from ..api_schemas import JustificacionCreateRequest, OperacionResponse
from ..schemas.enums import TipoJustificacion
from ..db_utils import get_database

router = APIRouter()


def get_db():
    """Obtiene conexión a la base de datos."""
    return get_database()


@router.post("", response_model=OperacionResponse, status_code=201)
async def registrar_justificacion(request: JustificacionCreateRequest):
    """
    Registra una justificación para una diferencia.
    
    Aplica el modelo híbrido:
    - **SIMPLE**: Solo texto (diferencia <= umbral configurado)
    - **COMPLETA**: Texto + evidencia obligatoria (diferencia > umbral)
    
    El umbral se obtiene de la configuración operativa (default: 500 MXN).
    """
    try:
        db = get_db()
        operativo_svc = OperativoService(db)
        
        resultado = await operativo_svc.registrar_justificacion_y_verificar(
            workflow_id=request.workflow_id,
            diferencia_id=request.diferencia_id,
            texto_justificacion=request.texto_justificacion,
            usuario_justificador_id=request.usuario_justificador_id,
            evidencia_documental=request.evidencia_documental
        )
        
        return OperacionResponse(
            success=True,
            message="Justificación registrada exitosamente",
            data=resultado
        )
    except JustificacionInvalidaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EvidenciaRequeridaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except JustificacionYaExisteError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{justificacion_id}")
async def obtener_justificacion(justificacion_id: str):
    """
    Obtiene una justificación por su ID.
    """
    try:
        db = get_db()
        just_svc = JustificacionService(db)
        
        justificacion = await just_svc.obtener_justificacion(justificacion_id)
        if not justificacion:
            raise HTTPException(status_code=404, detail=f"Justificación no encontrada: {justificacion_id}")
        
        return justificacion
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def listar_justificaciones(
    workflow_id: Optional[str] = Query(None, description="Filtrar por workflow"),
    diferencia_id: Optional[str] = Query(None, description="Filtrar por diferencia"),
    usuario_id: Optional[str] = Query(None, description="Filtrar por usuario"),
    tipo: Optional[TipoJustificacion] = Query(None, description="Filtrar por tipo"),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Lista justificaciones con filtros opcionales.
    """
    try:
        db = get_db()
        just_svc = JustificacionService(db)
        
        if workflow_id:
            justificaciones = await just_svc.obtener_justificaciones_workflow(workflow_id)
            return {"items": justificaciones, "total": len(justificaciones)}
        
        if diferencia_id:
            justificaciones = await just_svc.obtener_justificaciones_diferencia(diferencia_id)
            return {"items": justificaciones, "total": len(justificaciones)}
        
        if usuario_id:
            justificaciones = await just_svc.listar_por_usuario(usuario_id, limit)
            return {"items": justificaciones, "total": len(justificaciones)}
        
        if tipo:
            justificaciones = await just_svc.listar_por_tipo(tipo, limit)
            return {"items": justificaciones, "total": len(justificaciones)}
        
        # Sin filtros, retornar vacío (requiere al menos un filtro)
        return {"items": [], "total": 0, "message": "Proporcione al menos un filtro"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow/{workflow_id}")
async def obtener_justificaciones_workflow(workflow_id: str):
    """
    Obtiene todas las justificaciones de un workflow.
    """
    try:
        db = get_db()
        just_svc = JustificacionService(db)
        
        justificaciones = await just_svc.obtener_justificaciones_workflow(workflow_id)
        return {"items": justificaciones, "total": len(justificaciones)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflow/{workflow_id}/verificar")
async def verificar_justificaciones_workflow(workflow_id: str):
    """
    Verifica si todas las diferencias de un workflow tienen justificación.
    
    Retorna:
    - **completamente_justificado**: True si todas las diferencias tienen justificación
    - **total_diferencias**: Número total de diferencias
    - **justificadas**: Número de diferencias justificadas
    - **pendientes**: Número de diferencias sin justificar
    """
    try:
        db = get_db()
        just_svc = JustificacionService(db)
        
        resultado = await just_svc.verificar_workflow_completamente_justificado(workflow_id)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/umbral")
async def obtener_umbral_justificacion():
    """
    Obtiene el umbral actual para determinar tipo de justificación.
    
    - Si diferencia_valor <= umbral → SIMPLE (solo texto)
    - Si diferencia_valor > umbral → COMPLETA (texto + evidencia)
    """
    try:
        db = get_db()
        just_svc = JustificacionService(db)
        
        umbral = await just_svc.obtener_umbral_actual()
        return {"umbral_justificacion_simple": umbral, "moneda": "MXN"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/determinar-tipo")
async def determinar_tipo_justificacion(diferencia_valor: float):
    """
    Determina qué tipo de justificación se requiere para un monto dado.
    """
    try:
        db = get_db()
        just_svc = JustificacionService(db)
        
        tipo = await just_svc.determinar_tipo_justificacion(diferencia_valor)
        umbral = await just_svc.obtener_umbral_actual()
        
        return {
            "diferencia_valor": diferencia_valor,
            "tipo_requerido": tipo.value,
            "umbral_aplicado": umbral,
            "requiere_evidencia": tipo == TipoJustificacion.COMPLETA
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
