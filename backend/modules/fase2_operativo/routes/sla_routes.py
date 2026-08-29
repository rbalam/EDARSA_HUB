from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Rutas de SLA - API para monitoreo de tiempos y cumplimiento.
CAB-003 | EDARSA HUB - Fase 2B.4
PROTEGIDO CON RBAC (Fase 2D)

Endpoints para gestión de SLA de tareas operativas.

Permisos requeridos:
- GET /configuracion - SLA_VER
- PUT /configuracion - SLA_CONFIGURAR
- GET /metricas - SLA_VER
- GET /tareas/* - SLA_VER
- POST /actualizar-estados - SLA_VER (invocado por scheduler)
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any
import logging

from ..db_utils import get_database
from ..services.sla_service import get_sla_service, EstadoSLA

# RBAC - Fase 2D
from core.rbac.middleware import require_permission, require_explicit_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sla", tags=["SLA"])


@router.get("/configuracion")
async def obtener_configuracion_sla(
    current_user: dict = Depends(require_permission("SLA_VER"))
):
    """
    Obtiene la configuración actual de umbrales SLA.
    
    Returns:
        Configuración de umbrales y porcentajes
    """
    try:
        db = get_database()
        sla_service = get_sla_service(db)
        
        config = sla_service.obtener_configuracion()
        
        return {
            "success": True,
            "data": config
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo configuración SLA: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo configuración"
        )


@router.put("/configuracion")
async def actualizar_configuracion_sla(
    valores: Dict[str, int],
    current_user: dict = Depends(require_explicit_permission("SLA_CONFIGURAR"))
):
    """
    Actualiza la configuración de umbrales SLA.
    
    Args:
        valores: Dict con claves y valores a actualizar
        Ejemplo: {"justificacion_simple_horas": 24, "umbral_advertencia_porcentaje": 50}
        
    Returns:
        Configuración actualizada
    """
    try:
        db = get_database()
        sla_service = get_sla_service(db)
        
        config = await sla_service.actualizar_configuracion(valores)
        
        return {
            "success": True,
            "message": "Configuración actualizada",
            "data": config
        }
        
    except Exception as e:
        logger.error(f"Error actualizando configuración SLA: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando configuración"
        )


@router.get("/metricas")
async def obtener_metricas_sla(
    current_user: dict = Depends(require_permission("SLA_VER"))
):
    """
    Obtiene métricas globales de cumplimiento SLA.
    
    Returns:
        Métricas de cumplimiento, tiempos promedio y distribución
    """
    try:
        db = get_database()
        sla_service = get_sla_service(db)
        
        metricas = await sla_service.obtener_metricas_globales()
        
        return {
            "success": True,
            "data": metricas
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas SLA: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo métricas"
        )


@router.get("/tareas/proximas-vencer")
async def obtener_tareas_proximas_vencer(
    limite: int = Query(default=20, le=100),
    current_user: dict = Depends(require_permission("SLA_VER"))
):
    """
    Obtiene tareas próximas a vencer (ADVERTENCIA o URGENTE).
    
    Args:
        limite: Máximo de tareas a retornar
        
    Returns:
        Lista de tareas con cálculos SLA
    """
    try:
        db = get_database()
        sla_service = get_sla_service(db)
        
        tareas = await sla_service.obtener_tareas_proximas_vencer(limite)
        
        return {
            "success": True,
            "items": tareas,
            "total": len(tareas)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo tareas próximas a vencer: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo tareas"
        )


@router.get("/tareas/vencidas")
async def obtener_tareas_vencidas(
    limite: int = Query(default=50, le=200),
    current_user: dict = Depends(require_permission("SLA_VER"))
):
    """
    Obtiene tareas vencidas.
    
    Args:
        limite: Máximo de tareas a retornar
        
    Returns:
        Lista de tareas vencidas con cálculos SLA
    """
    try:
        db = get_database()
        sla_service = get_sla_service(db)
        
        tareas = await sla_service.obtener_tareas_vencidas(limite)
        
        return {
            "success": True,
            "items": tareas,
            "total": len(tareas)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo tareas vencidas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo tareas"
        )


@router.post("/actualizar-estados")
async def actualizar_estados_sla(
    current_user: dict = Depends(require_permission("SLA_VER"))
):
    """
    Actualiza los estados SLA de todas las tareas activas.
    
    Este endpoint debe ser invocado periódicamente (cada hora)
    por un cron externo o mecanismo equivalente.
    
    Returns:
        Resumen de actualizaciones realizadas
    """
    try:
        db = get_database()
        sla_service = get_sla_service(db)
        
        resultado = await sla_service.actualizar_estados_sla()
        
        logger.info(f"Estados SLA actualizados: {resultado}")
        
        return {
            "success": True,
            "message": "Estados SLA actualizados",
            "data": resultado
        }
        
    except Exception as e:
        logger.error(f"Error actualizando estados SLA: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando estados"
        )


@router.get("/tarea/{tarea_id}")
async def obtener_sla_tarea(
    tarea_id: str,
    current_user: dict = Depends(require_permission("SLA_VER"))
):
    """
    Obtiene el cálculo SLA de una tarea específica.
    
    Args:
        tarea_id: ID de la tarea
        
    Returns:
        Cálculo SLA de la tarea
    """
    try:
        db = get_database()
        sla_service = get_sla_service(db)
        
        # SQL-FIRST P2B: buscar tarea en dbo.Tareas_Inventario
        tarea = None
        try:
            from modules.compras.sync_service import get_edarsahub_connection
            conn = get_edarsahub_connection()
            cur = conn.cursor(as_dict=True)
            cur.execute("""
                SELECT TOP 1
                    TareaID AS id,
                    TareaID AS tarea_id,
                    WorkflowID AS workflow_id,
                    TipoTarea AS tipo_tarea,
                    Titulo AS titulo,
                    Descripcion AS descripcion,
                    EstadoTarea AS estado_tarea,
                    Prioridad AS prioridad,
                    UsuarioAsignadoID AS usuario_asignado_id,
                    UsuarioAsignadoNombre AS usuario_asignado_nombre,
                    FechaCreacion AS fecha_creacion,
                    FechaAsignacion AS fecha_asignacion,
                    FechaLimite AS fecha_limite,
                    FechaPrimeraAccion AS fecha_primera_accion,
                    FechaCompletada AS fecha_completada,
                    Ciclo AS ciclo,
                    EsReasignacion AS es_reasignacion,
                    Vencida AS vencida,
                    EstadoSLA AS estado_sla,
                    NotasJSON AS notas_json
                FROM dbo.Tareas_Inventario
                WHERE TareaID=%s
            """, (tarea_id,))
            tarea = cur.fetchone()
            conn.close()
        except Exception:
            tarea = None
        if not tarea:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        
        # Calcular SLA
        calculo = sla_service.calcular_estado_sla(tarea)
        
        return {
            "success": True,
            "data": {
                "tarea_id": tarea_id,
                "tipo_tarea": tarea.get("tipo_tarea"),
                "estado_tarea": tarea.get("estado_tarea"),
                "sla": calculo
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo SLA de tarea {tarea_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo SLA"
        )


@router.get("/estados")
async def obtener_definicion_estados():
    """
    Obtiene la definición de estados SLA.
    
    Returns:
        Lista de estados SLA con sus descripciones
    """
    return {
        "success": True,
        "data": {
            "estados": [
                {
                    "valor": EstadoSLA.EN_TIEMPO.value,
                    "descripcion": "Tarea activa, dentro del 50% del tiempo",
                    "tipo": "activa"
                },
                {
                    "valor": EstadoSLA.ADVERTENCIA.value,
                    "descripcion": "Tarea activa, 50-75% del tiempo consumido",
                    "tipo": "activa"
                },
                {
                    "valor": EstadoSLA.URGENTE.value,
                    "descripcion": "Tarea activa, 75-100% del tiempo consumido",
                    "tipo": "activa"
                },
                {
                    "valor": EstadoSLA.VENCIDA.value,
                    "descripcion": "Tarea activa, tiempo excedido",
                    "tipo": "activa"
                },
                {
                    "valor": EstadoSLA.CUMPLIDA_EN_TIEMPO.value,
                    "descripcion": "Tarea completada dentro del SLA",
                    "tipo": "completada"
                },
                {
                    "valor": EstadoSLA.CUMPLIDA_FUERA_DE_TIEMPO.value,
                    "descripcion": "Tarea completada fuera del SLA",
                    "tipo": "completada"
                }
            ]
        }
    }
