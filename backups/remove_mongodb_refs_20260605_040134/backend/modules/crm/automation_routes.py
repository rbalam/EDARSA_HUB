"""
EDARSA HUB - CRM Automation Routes
===================================
Endpoints para gestión de automatizaciones del pipeline CRM.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import date
import logging

from core.security import get_current_user
from .automation_service import get_pipeline_automation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crm/automation", tags=["CRM - Automatización"])


# ==================== SCHEMAS ====================

class ReglaCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    pipeline_id: Optional[int] = None
    tipo_trigger: str  # CAMBIO_ETAPA, TIEMPO_EN_ETAPA, CAMPO_MODIFICADO
    condicion_json: Optional[str] = "{}"
    accion_json: str
    prioridad: Optional[int] = 100

class ReglaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    condicion_json: Optional[str] = None
    accion_json: Optional[str] = None
    prioridad: Optional[int] = None
    activa: Optional[bool] = None


# ==================== ENDPOINTS REGLAS ====================

@router.get("/reglas", summary="Listar Reglas de Automatización")
async def listar_reglas(
    empresa_id: str = Query(..., description="ID de empresa"),
    pipeline_id: Optional[int] = Query(None, description="Filtrar por pipeline"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene las reglas de automatización activas.
    
    Permisos: CRM_ADMIN
    """
    try:
        service = get_pipeline_automation_service()
        reglas = service.obtener_reglas_activas(empresa_id, pipeline_id)
        return {
            "total": len(reglas),
            "reglas": reglas
        }
    except Exception as e:
        logger.error(f"[CRM-Automation] Error listando reglas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reglas", summary="Crear Regla de Automatización")
async def crear_regla(
    data: ReglaCreate,
    empresa_id: str = Query(..., description="ID de empresa"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Crea una nueva regla de automatización.
    
    Tipos de trigger soportados:
    - CAMBIO_ETAPA: Se ejecuta cuando una oportunidad cambia de etapa
    - TIEMPO_EN_ETAPA: Se ejecuta cuando una oportunidad lleva X días en una etapa
    - CAMPO_MODIFICADO: Se ejecuta cuando se modifica un campo específico
    
    Tipos de acción soportados:
    - CREAR_ACTIVIDAD: Crea una actividad de seguimiento
    - ACTUALIZAR_CAMPO: Actualiza un campo de la oportunidad
    - ENVIAR_NOTIFICACION: Envía una notificación al responsable
    - ASIGNAR_RESPONSABLE: Asigna un responsable específico
    
    Permisos: CRM_ADMIN
    """
    try:
        service = get_pipeline_automation_service()
        result = service.crear_regla(empresa_id, data.dict(), current_user['id'])
        return result
    except Exception as e:
        logger.error(f"[CRM-Automation] Error creando regla: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINTS SLA ====================

@router.get("/sla/verificar", summary="Verificar SLA de Oportunidades")
async def verificar_sla(
    empresa_id: str = Query(..., description="ID de empresa"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Verifica el SLA de oportunidades y retorna alertas.
    
    Identifica:
    - Oportunidades con SLA vencido (más días de los permitidos en la etapa)
    - Oportunidades próximas a vencer (>80% del SLA)
    
    Permisos: CRM_VER
    """
    try:
        service = get_pipeline_automation_service()
        result = service.verificar_sla_oportunidades(empresa_id)
        return result
    except Exception as e:
        logger.error(f"[CRM-Automation] Error verificando SLA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINTS ESTADÍSTICAS ====================

@router.get("/estadisticas", summary="Estadísticas de Automatizaciones")
async def obtener_estadisticas(
    empresa_id: str = Query(..., description="ID de empresa"),
    fecha_desde: Optional[date] = Query(None, description="Fecha inicio (default: últimos 30 días)"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene estadísticas de ejecución de automatizaciones.
    
    Permisos: CRM_ADMIN
    """
    try:
        service = get_pipeline_automation_service()
        result = service.obtener_estadisticas_automatizaciones(empresa_id, fecha_desde)
        return result
    except Exception as e:
        logger.error(f"[CRM-Automation] Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINT TRIGGER MANUAL ====================

@router.post("/ejecutar/cambio-etapa", summary="Ejecutar Trigger de Cambio de Etapa (Manual)")
async def ejecutar_trigger_cambio_etapa(
    oportunidad_id: str = Query(..., description="ID de oportunidad"),
    etapa_anterior_id: int = Query(..., description="ID etapa anterior"),
    etapa_nueva_id: int = Query(..., description="ID etapa nueva"),
    empresa_id: str = Query(..., description="ID de empresa"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Ejecuta manualmente las automatizaciones de cambio de etapa.
    Útil para testing o re-ejecución.
    
    Permisos: CRM_ADMIN
    """
    try:
        service = get_pipeline_automation_service()
        result = service.ejecutar_trigger_cambio_etapa(
            oportunidad_id, etapa_anterior_id, etapa_nueva_id, empresa_id
        )
        return {
            "oportunidad_id": oportunidad_id,
            "etapa_anterior": etapa_anterior_id,
            "etapa_nueva": etapa_nueva_id,
            "acciones_ejecutadas": result
        }
    except Exception as e:
        logger.error(f"[CRM-Automation] Error ejecutando trigger: {e}")
        raise HTTPException(status_code=500, detail=str(e))
