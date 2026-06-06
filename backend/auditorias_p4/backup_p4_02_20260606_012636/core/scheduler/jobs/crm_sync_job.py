"""
EDARSA HUB - CRM Sync Job
==========================
Job programado para tareas automáticas del CRM Enterprise (SQL-First).

NOTA: Sincronización con CRMs externos (vTiger) ha sido eliminada.
Este job ahora solo ejecuta tareas internas de SLA y actividades.

Ejecución: Cada 30 minutos por defecto
Acción: Verifica SLAs y actividades vencidas
"""

import logging
from typing import Dict, Any
from datetime import datetime, timedelta
import os
import pymssql
from core.config.edarsahub_config import get_edarsahub_sql_config
_edarsa_cfg = get_edarsahub_sql_config()


logger = logging.getLogger(__name__)


def _get_connection():
    """Obtiene conexión a EDARSAHUB SQL Server."""
    return pymssql.connect(
        server=_edarsa_cfg.host,
        user=_edarsa_cfg.user,
        password=_edarsa_cfg.password,
        database=_edarsa_cfg.database,
        port=_edarsa_cfg.port
    )


async def execute_crm_sync(db) -> Dict[str, Any]:
    """
    Job de sincronización CRM.
    
    NOTA: Sincronización con CRMs externos (vTiger) ha sido eliminada.
    Este job retorna inmediatamente indicando que no hay conectores externos.
    
    Args:
        db: StubDatabase (no usado, SQL Server directo)
    
    Returns:
        Dict con mensaje indicando que no hay sincronización externa
    """
    logger.info("[CRM-SYNC] Sincronización externa deshabilitada (vTiger eliminado)")
    
    return {
        "estatus_general": "OK",
        "mensaje": "Sincronización con CRMs externos deshabilitada. El CRM opera en modo SQL-First.",
        "total_conectores": 0,
        "conectores_exitosos": 0,
        "registros_creados": 0,
        "registros_actualizados": 0,
        "registros_error": 0,
        "duracion_ms": 0,
        "fecha_ejecucion": datetime.now().isoformat(),
        "errores": []
    }


async def execute_crm_sla_check(db) -> Dict[str, Any]:
    """
    Verifica SLAs de oportunidades y genera alertas.
    
    Args:
        db: StubDatabase (no usado)
    
    Returns:
        Dict con resumen de verificación SLA
    """
    from modules.crm.automation_service import get_pipeline_automation_service
    from modules.crm.trigger_service import get_crm_trigger_service, TriggerEvent
    
    inicio = datetime.now()
    
    automation_service = get_pipeline_automation_service()
    trigger_service = get_crm_trigger_service()
    
    total_vencidas = 0
    total_proximas = 0
    triggers_ejecutados = 0
    
    conn = _get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        
        # Obtener empresas activas con CRM
        cursor.execute("""
            SELECT DISTINCT EmpresaID FROM CRM_Oportunidades WHERE Activo = 1
        """)
        empresas = cursor.fetchall() or []
        
        for emp in empresas:
            empresa_id = emp['EmpresaID']
            
            # Verificar SLAs
            resultado_sla = automation_service.verificar_sla_oportunidades(empresa_id)
            
            total_vencidas += resultado_sla.get('vencidas', 0)
            total_proximas += resultado_sla.get('proximas_a_vencer', 0)
            
            # Disparar triggers para oportunidades con SLA vencido
            for opp in resultado_sla.get('detalle_vencidas', []):
                try:
                    trigger_service.dispatch_event(
                        evento=TriggerEvent.SLA_VENCIDO,
                        empresa_id=empresa_id,
                        entidad_id=opp['OportunidadID'],
                        datos_evento={
                            'nombre_oportunidad': opp['Nombre'],
                            'dias_en_etapa': opp['DiasEnEtapa'],
                            'etapa_nombre': opp['EtapaNombre'],
                            'monto_estimado': float(opp.get('MontoEstimado') or 0)
                        }
                    )
                    triggers_ejecutados += 1
                except Exception as e:
                    logger.warning(f"[CRM-SLA] Error disparando trigger: {e}")
    
    except Exception as e:
        logger.error(f"[CRM-SLA] Error verificando SLAs: {e}")
    finally:
        conn.close()
    
    duracion_ms = int((datetime.now() - inicio).total_seconds() * 1000)
    
    return {
        "estatus_general": "OK",
        "total_vencidas": total_vencidas,
        "total_proximas": total_proximas,
        "triggers_ejecutados": triggers_ejecutados,
        "duracion_ms": duracion_ms,
        "fecha_ejecucion": inicio.isoformat()
    }


async def execute_crm_actividades_vencidas(db) -> Dict[str, Any]:
    """
    Verifica actividades vencidas y genera recordatorios.
    
    Args:
        db: StubDatabase (no usado)
    
    Returns:
        Dict con resumen de actividades procesadas
    """
    from modules.crm.trigger_service import get_crm_trigger_service, TriggerEvent
    
    inicio = datetime.now()
    
    trigger_service = get_crm_trigger_service()
    
    total_vencidas = 0
    notificaciones_creadas = 0
    
    conn = _get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        
        # Actividades vencidas no procesadas
        cursor.execute("""
            SELECT 
                a.ActividadID, a.EmpresaID, a.OportunidadID, a.ResponsableID,
                a.Titulo, a.FechaProgramada, a.NotificacionEnviada,
                o.NombreOportunidad as NombreOportunidad,
                DATEDIFF(day, a.FechaProgramada, GETDATE()) as DiasVencida
            FROM CRM_Actividades a
            INNER JOIN CRM_Oportunidades o ON a.OportunidadID = o.OportunidadID
            WHERE a.EstatusID = 1  -- Pendiente
            AND a.FechaProgramada < GETDATE()
            AND ISNULL(a.NotificacionEnviada, 0) = 0
            ORDER BY a.FechaProgramada ASC
        """)
        
        actividades = cursor.fetchall() or []
        total_vencidas = len(actividades)
        
        for act in actividades:
            try:
                # Disparar trigger
                resultados = trigger_service.dispatch_event(
                    evento=TriggerEvent.ACTIVIDAD_VENCIDA,
                    empresa_id=act['EmpresaID'],
                    entidad_id=act['OportunidadID'],
                    datos_evento={
                        'actividad_id': act['ActividadID'],
                        'titulo_actividad': act['Titulo'],
                        'nombre_oportunidad': act['NombreOportunidad'],
                        'dias_vencida': act['DiasVencida'],
                        'responsable_id': act['ResponsableID']
                    }
                )
                
                if resultados:
                    notificaciones_creadas += 1
                
                # Marcar como notificada
                cursor.execute("""
                    UPDATE CRM_Actividades
                    SET NotificacionEnviada = 1, FechaNotificacion = GETDATE()
                    WHERE ActividadID = %s
                """, (act['ActividadID'],))
                conn.commit()
                
            except Exception as e:
                logger.warning(f"[CRM-ACT] Error procesando actividad {act['ActividadID']}: {e}")
    
    except Exception as e:
        logger.error(f"[CRM-ACT] Error general: {e}")
    finally:
        conn.close()
    
    duracion_ms = int((datetime.now() - inicio).total_seconds() * 1000)
    
    return {
        "estatus_general": "OK",
        "total_vencidas": total_vencidas,
        "notificaciones_creadas": notificaciones_creadas,
        "duracion_ms": duracion_ms,
        "fecha_ejecucion": inicio.isoformat()
    }
