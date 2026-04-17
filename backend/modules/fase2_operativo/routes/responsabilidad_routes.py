"""
Endpoints de Responsabilidad Económica
CAB-003 | EDARSA HUB - Fase 2C.1

Expone la funcionalidad de cálculo de impacto económico vía HTTP.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..services.responsabilidad_service import (
    ResponsabilidadService,
    WorkflowNoEncontradoError,
    CalculoYaExisteError,
    ModuloDesactivadoError,
    SinDiferenciasError,
)
from ..schemas.responsabilidad_schemas import (
    ResponsabilidadResumenCalculo,
    ResponsabilidadResponse,
    ResponsabilidadListResponse,
    ConfiguracionResponsabilidadResponse,
    ConfiguracionResponsabilidadUpdate,
)
from ..api_schemas import OperacionResponse
from ..db_utils import get_database

router = APIRouter()


def get_db():
    """Obtiene conexión a la base de datos."""
    return get_database()


# ==================== CÁLCULO ====================

@router.post(
    "/calcular/{workflow_id}",
    response_model=ResponsabilidadResumenCalculo,
    summary="Calcular impacto económico",
    description="""
    Ejecuta el cálculo de responsabilidad económica para un workflow.
    
    Flujo:
    1. Lee las diferencias del workflow
    2. Clasifica faltantes y sobrantes
    3. Aplica tolerancias configurables
    4. Calcula monto propuesto (solo faltantes fuera de tolerancia)
    5. Persiste con estado CALCULADO
    6. Actualiza workflow a EN_REVISION_FINANCIERA
    
    **Nota:** Los sobrantes se registran pero NO compensan faltantes.
    """
)
async def calcular_responsabilidad(
    workflow_id: str,
    usuario_id: str = Query(..., description="ID del usuario que ejecuta el cálculo"),
    forzar_recalculo: bool = Query(False, description="Forzar recálculo si ya existe")
):
    """Calcula el impacto económico de un workflow."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        resultado = await service.calcular_responsabilidad(
            workflow_id=workflow_id,
            usuario_id=usuario_id,
            forzar_recalculo=forzar_recalculo
        )
        
        return resultado
        
    except ModuloDesactivadoError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except WorkflowNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CalculoYaExisteError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except SinDiferenciasError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ==================== CONSULTAS ====================

@router.get(
    "/workflow/{workflow_id}",
    response_model=ResponsabilidadResponse,
    summary="Obtener cálculo por workflow",
    description="Obtiene el cálculo de responsabilidad económica de un workflow específico."
)
async def obtener_por_workflow(workflow_id: str):
    """Obtiene el cálculo de responsabilidad de un workflow."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        resultado = await service.obtener_por_workflow(workflow_id)
        
        if not resultado:
            raise HTTPException(
                status_code=404,
                detail=f"No existe cálculo de responsabilidad para el workflow {workflow_id}"
            )
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "",
    response_model=ResponsabilidadListResponse,
    summary="Listar cálculos de responsabilidad",
    description="Lista todos los cálculos de responsabilidad económica con filtros opcionales."
)
async def listar_responsabilidades(
    sucursal_id: Optional[str] = Query(None, description="Filtrar por sucursal"),
    estado: Optional[str] = Query(None, description="Filtrar por estado (CALCULADO)"),
    excede_minimo: Optional[bool] = Query(None, description="Filtrar por si excede mínimo"),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(50, ge=1, le=200, description="Límite de registros")
):
    """Lista cálculos de responsabilidad con filtros."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        resultado = await service.listar(
            sucursal_id=sucursal_id,
            estado=estado,
            excede_minimo=excede_minimo,
            skip=skip,
            limit=limit
        )
        
        return ResponsabilidadListResponse(
            items=resultado["items"],
            total=resultado["total"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ==================== CONFIGURACIÓN ====================

@router.get(
    "/configuracion",
    response_model=ConfiguracionResponsabilidadResponse,
    summary="Obtener configuración de responsabilidad",
    description="""
    Obtiene la configuración actual del módulo de responsabilidad económica.
    
    Incluye:
    - cargo_minimo_mxn: Monto mínimo para generar cargo
    - tolerancia_unidades: Tolerancia absoluta en unidades
    - tolerancia_porcentaje_diferencia: Tolerancia relativa (%)
    - precio_faltante_default: Precio unitario por defecto
    - modulo_responsabilidad_activo: Si el módulo está habilitado
    - permitir_compensacion_faltantes_sobrantes: Si se permite compensación (default: false)
    """
)
async def obtener_configuracion():
    """Obtiene la configuración de responsabilidad."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        return await service.obtener_configuracion()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.put(
    "/configuracion",
    response_model=ConfiguracionResponsabilidadResponse,
    summary="Actualizar configuración de responsabilidad",
    description="Actualiza los parámetros de configuración del módulo de responsabilidad económica."
)
async def actualizar_configuracion(request: ConfiguracionResponsabilidadUpdate):
    """Actualiza la configuración de responsabilidad."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        return await service.actualizar_configuracion(
            cargo_minimo_mxn=request.cargo_minimo_mxn,
            tolerancia_unidades=request.tolerancia_unidades,
            tolerancia_porcentaje_diferencia=request.tolerancia_porcentaje_diferencia,
            precio_faltante_default=request.precio_faltante_default,
            modulo_responsabilidad_activo=request.modulo_responsabilidad_activo,
            permitir_compensacion_faltantes_sobrantes=request.permitir_compensacion_faltantes_sobrantes
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ==================== INICIALIZACIÓN ====================

@router.post(
    "/inicializar-configuracion",
    response_model=OperacionResponse,
    summary="Inicializar configuración",
    description="Inicializa las claves de configuración del módulo si no existen. Seguro de ejecutar múltiples veces."
)
async def inicializar_configuracion():
    """Inicializa la configuración del módulo."""
    try:
        db = get_db()
        service = ResponsabilidadService(db)
        
        resultado = await service.inicializar_configuracion()
        
        return OperacionResponse(
            success=True,
            message=resultado["mensaje"],
            data=resultado
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
