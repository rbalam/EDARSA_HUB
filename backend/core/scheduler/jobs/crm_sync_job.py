"""
EDARSA HUB - CRM Sync Job
==========================
Job programado para sincronización automática con CRMs externos (VTiger, etc.)

Ejecución: Cada 30 minutos por defecto
Acción: Sincroniza leads, oportunidades y cuentas desde CRMs externos
"""

import logging
from typing import Dict, Any
from datetime import datetime, timedelta
import os
import pymssql

logger = logging.getLogger(__name__)


def _get_connection():
    """Obtiene conexión a EDARSAHUB SQL Server."""
    return pymssql.connect(
        server=os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
        user=os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
        password=os.environ.get('EDARSAHUB_PASSWORD', 'National09$'),
        database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
        port=int(os.environ.get('EDARSAHUB_PORT', 1433))
    )


async def execute_crm_sync(db) -> Dict[str, Any]:
    """
    Ejecuta sincronización con CRMs externos configurados.
    
    Args:
        db: StubDatabase (no usado, SQL Server directo)
    
    Returns:
        Dict con resultados de la sincronización
    """
    from modules.crm.integration.sync_engine import SyncEngine, SyncJob
    
    inicio = datetime.now()
    
    # Resultados globales
    total_conectores = 0
    conectores_exitosos = 0
    registros_creados = 0
    registros_actualizados = 0
    registros_error = 0
    errores = []
    
    conn = _get_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        
        # Obtener conectores activos
        cursor.execute("""
            SELECT 
                c.ConectorID, c.EmpresaID, c.TipoConector,
                c.URLBase, c.Usuario, c.APIKey, c.SecretKey,
                c.ConfigJSON, c.UltimaSincronizacion
            FROM CRM_Integration_Conectores c
            WHERE c.Activo = 1
            AND c.SyncAutomatico = 1
            ORDER BY c.UltimaSincronizacion ASC
        """)
        
        conectores = cursor.fetchall() or []
        total_conectores = len(conectores)
        
        if not conectores:
            logger.info("[CRM-SYNC] No hay conectores activos para sincronizar")
            return {
                "estatus_general": "OK",
                "mensaje": "Sin conectores activos",
                "total_conectores": 0,
                "duracion_ms": 0
            }
        
        # Inicializar motor de sincronización
        db_config = {
            'host': os.environ.get('EDARSAHUB_HOST'),
            'user': os.environ.get('EDARSAHUB_USERNAME'),
            'password': os.environ.get('EDARSAHUB_PASSWORD'),
            'database': os.environ.get('EDARSAHUB_DATABASE'),
            'port': int(os.environ.get('EDARSAHUB_PORT', 1433))
        }
        sync_engine = SyncEngine(db_config)
        
        for conector in conectores:
            try:
                conector_id = conector['ConectorID']
                empresa_id = conector['EmpresaID']
                
                logger.info(f"[CRM-SYNC] Sincronizando conector {conector_id} ({conector['TipoConector']})")
                
                # Configurar job
                job = SyncJob(
                    conector_id=conector_id,
                    empresa_id=empresa_id,
                    tipo_conector=conector['TipoConector'],
                    entidades=['leads', 'oportunidades', 'cuentas'],
                    desde_fecha=conector.get('UltimaSincronizacion')
                )
                
                # Configurar conector
                config = {
                    'url_base': conector['URLBase'],
                    'usuario': conector['Usuario'],
                    'api_key': conector['APIKey'],
                    'secret_key': conector['SecretKey']
                }
                
                # Ejecutar sincronización
                result = sync_engine.run_sync(job, config)
                
                if result.success:
                    conectores_exitosos += 1
                    registros_creados += result.registros_creados
                    registros_actualizados += result.registros_actualizados
                    
                    # Actualizar timestamp de última sincronización
                    cursor.execute("""
                        UPDATE CRM_Integration_Conectores
                        SET UltimaSincronizacion = GETDATE()
                        WHERE ConectorID = %s
                    """, (conector_id,))
                    conn.commit()
                else:
                    registros_error += result.registros_error
                    errores.extend(result.errores[:5])  # Max 5 errores por conector
                
            except Exception as e:
                logger.error(f"[CRM-SYNC] Error con conector {conector.get('ConectorID')}: {e}")
                errores.append(f"Conector {conector.get('ConectorID')}: {str(e)}")
        
    except Exception as e:
        logger.error(f"[CRM-SYNC] Error general: {e}")
        errores.append(str(e))
    finally:
        conn.close()
    
    duracion_ms = int((datetime.now() - inicio).total_seconds() * 1000)
    
    resultado = {
        "estatus_general": "OK" if conectores_exitosos == total_conectores else "PARCIAL",
        "total_conectores": total_conectores,
        "conectores_exitosos": conectores_exitosos,
        "registros_creados": registros_creados,
        "registros_actualizados": registros_actualizados,
        "registros_error": registros_error,
        "duracion_ms": duracion_ms,
        "fecha_ejecucion": inicio.isoformat(),
        "errores": errores[:10]
    }
    
    logger.info(
        f"[CRM-SYNC] Completado: {conectores_exitosos}/{total_conectores} conectores, "
        f"{registros_creados} creados, {registros_actualizados} actualizados, "
        f"{registros_error} errores, {duracion_ms}ms"
    )
    
    return resultado


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
