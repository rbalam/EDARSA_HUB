"""
EDARSA HUB - Job de Detección de Nuevos Registros (Polling Incremental)
=======================================================================

PROPÓSITO:
Detecta nuevos inventarios y requisiciones en tiempo casi-real usando
polling incremental con checkpoints. Genera eventos para disparar informes.

ARQUITECTURA:
- Usa checkpoints para consultar solo registros NUEVOS
- Genera eventos que luego pueden disparar informes automáticos
- Preparado para migrar a Service Broker (Opción C)

FRECUENCIA:
- Cada 2 minutos (configurable via COMPRAS_POLLING_INTERVAL)

DIFERENCIA CON sync_compras_job.py:
- sync_compras_job: Sincroniza TODOS los datos cada 30 min (backup completo)
- detect_nuevos_job: Detecta SOLO nuevos cada 2 min (tiempo real)

Autor: E1 Agent
Fecha: 2026-05-23
"""

import os
import uuid
import logging
import pymssql
from datetime import datetime
from typing import Dict, List, Any, Optional
from zoneinfo import ZoneInfo

from modules.integrations_runtime.sync_ledger import enrich_sync_start, mark_sync_finished
from modules.compras.eventos_compras import (
    get_detector,
    get_event_dispatcher,
    get_checkpoint_manager,
    EventoTipo,
)

logger = logging.getLogger(__name__)

# Configuración
JOB_NAME = "detect_nuevos_compras"
POLLING_INTERVAL_SECONDS = int(os.environ.get("COMPRAS_POLLING_INTERVAL", "120"))  # 2 min default
SYNC_TYPE = "DETECT_NUEVOS"
LOCK_TIMEOUT_MINUTES = 5

# P2-01: Config centralizado
from core.config.edarsahub_config import get_edarsahub_sql_config
from core.sql_first.connection_factory import get_external_sql_connection, get_edarsahub_connection
_edarsa_cfg = get_edarsahub_sql_config()
EDARSAHUB_CONFIG = {
    'host': _edarsa_cfg.host,
    'port': _edarsa_cfg.port,
    'database': _edarsa_cfg.database,
    'username': _edarsa_cfg.user,
    'password': _edarsa_cfg.password
}


# =============================================================================
# LOCK ANTI-CONCURRENCIA (Más ligero que sync_compras)
# =============================================================================

def _acquire_detect_lock(run_id: str) -> bool:
    """Adquiere lock para evitar ejecuciones concurrentes."""
    from datetime import timedelta
    
    try:
        conn = get_edarsahub_connection()
        cursor = conn.cursor(as_dict=True)
        now_mx = datetime.now(ZoneInfo("America/Mexico_City"))
        timeout_threshold = now_mx - timedelta(minutes=LOCK_TIMEOUT_MINUTES)
        
        cursor.execute("""
            SELECT SyncControlID, SyncRunID, StartedAtMexico
            FROM Sync_Control_Ejecuciones
            WHERE SyncType=%s AND Status='IN_PROGRESS' AND FinishedAtMexico IS NULL
        """, (SYNC_TYPE,))
        active = cursor.fetchone()
        
        if active:
            started = active['StartedAtMexico']
            if started.tzinfo is None:
                started = started.replace(tzinfo=ZoneInfo("America/Mexico_City"))
            if started < timeout_threshold:
                cursor.execute("""
                    UPDATE Sync_Control_Ejecuciones
                    SET Status='TIMEOUT', FinishedAtMexico=%s,
                        FinishedAtUTC=COALESCE(FinishedAtUTC,SYSUTCDATETIME())
                    WHERE SyncControlID=%s
                """, (now_mx.replace(tzinfo=None), active['SyncControlID']))
                conn.commit()
            else:
                conn.close()
                return False
        
        today = now_mx.date()
        cursor.execute("""
            INSERT INTO Sync_Control_Ejecuciones (
                SyncRunID, SyncType, FechaInicio, FechaFin, VentanaInicioHoraConfig,
                VentanaFinHoraConfig, IsDryRun, RegistrosProcesados, RegistrosInsertados,
                RegistrosActualizados, RegistrosError, Status, StartedAtMexico, CreatedAt
            ) VALUES (%s,%s,%s,%s,0,0,0,0,0,0,0,'IN_PROGRESS',%s,%s)
        """, (run_id, SYNC_TYPE, today, today, now_mx.replace(tzinfo=None), now_mx.replace(tzinfo=None)))
        enrich_sync_start(
            cursor,
            sync_run_id=run_id,
            sync_type=SYNC_TYPE,
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"[DETECT-LOCK] Error: {e}")
        return True


def _release_detect_lock(run_id: str, status: str, detected: int, eventos: int):
    """Libera el lock de detección."""
    try:
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        now_mx = datetime.now(ZoneInfo("America/Mexico_City"))
        
        cursor.execute("SELECT StartedAtMexico FROM Sync_Control_Ejecuciones WHERE SyncRunID=%s", (run_id,))
        row = cursor.fetchone()
        duration = 0
        if row and row[0]:
            started = row[0]
            if started.tzinfo is None:
                started = started.replace(tzinfo=ZoneInfo("America/Mexico_City"))
            duration = int((now_mx - started).total_seconds())
        
        cursor.execute("""
            UPDATE Sync_Control_Ejecuciones
            SET Status=%s, FinishedAtMexico=%s, DurationSeconds=%s, 
                RegistrosProcesados=%s, RegistrosInsertados=%s
            WHERE SyncRunID=%s
        """, (status, now_mx.replace(tzinfo=None), duration, detected, eventos, run_id))
        mark_sync_finished(cursor, run_id)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"[DETECT-LOCK] Error liberando: {e}")


# =============================================================================
# OBTENER SERVIDORES
# =============================================================================

def _get_servers_for_detection() -> List[Dict]:
    """Obtiene servidores activos para detección."""
    from core.secret_manager import decrypt_secret
    
    try:
        conn = get_edarsahub_connection()
        cursor = conn.cursor(as_dict=True)
        
        cursor.execute("""
            SELECT 
                s.id, s.nombre as server_name, s.host, s.port, s.database_name,
                s.username, s.password_encrypted, s.system_type,
                u.id as unidad_id, u.codigo as unidad_codigo, u.nombre as unidad_nombre
            FROM Servidores_Conexiones s
            LEFT JOIN Unidades_Negocio u ON u.server_id = CAST(s.id AS NVARCHAR(36))
            WHERE s.activo = 1
              AND s.tipo_conexion IN ('SQL_SERVER', 'DATA_SOURCE')
              AND s.system_type IN ('SOFTRESTAURANT', 'MPRO', 'MANAGEMENTPRO', 'SOFTRESTAURANT_PRO')
              AND s.host IS NOT NULL AND s.host != ''
        """)
        rows = cursor.fetchall()
        conn.close()
        
        servers = []
        for row in rows:
            password = ''
            if row.get('password_encrypted'):
                try:
                    password = decrypt_secret(row['password_encrypted'])
                except Exception:
                    continue
            
            servers.append({
                'id': str(row.get('id', '')),
                'name': row.get('server_name', ''),
                'host': row.get('host', ''),
                'port': int(row.get('port', 1433)),
                'database': row.get('database_name', ''),
                'username': row.get('username', ''),
                'password': password,
                'system_type': row.get('system_type', ''),
                'unidad_id': str(row.get('unidad_id', '')),
                'unidad_codigo': row.get('unidad_codigo', ''),
                'unidad_nombre': row.get('unidad_nombre', ''),
            })
        
        return servers
        
    except Exception as e:
        logger.error(f"[DETECT] Error obteniendo servidores: {e}")
        return []


# =============================================================================
# FUNCIÓN DE QUERY CON TIMEOUT
# =============================================================================

def _execute_with_timeout(host, port, database, username, password, query, timeout_seconds=15):
    """Ejecuta query con timeout corto para detección rápida."""
    from core.db import execute_sql_query
    import signal
    import platform
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Timeout {timeout_seconds}s")
    
    if platform.system() != 'Windows':
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
    
    try:
        result = execute_sql_query(
            host,
            port,
            database,
            username,
            password,
            query,
            timeout_seconds=timeout_seconds,
            context="jobs",
        )
        return result
    except Exception as e:
        if 'timeout' in str(e).lower() or 'connection' in str(e).lower():
            return None
        raise
    finally:
        if platform.system() != 'Windows':
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def execute_detect_nuevos(dry_run: bool = False) -> Dict[str, Any]:
    """
    Ejecuta la detección de nuevos registros.
    
    Args:
        dry_run: Si True, no genera eventos ni actualiza checkpoints
    
    Returns:
        Dict con resultados de la detección
    """
    run_id = f"DETECT-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"
    logger.info(f"[DETECT] ========== INICIO DETECCIÓN {run_id} ==========")
    
    if not _acquire_detect_lock(run_id):
        return {"status": "SKIPPED", "reason": "Lock activo", "run_id": run_id}
    
    start_time = datetime.now(ZoneInfo("America/Mexico_City"))
    total_detected = 0
    total_eventos = 0
    results = {"inventarios": [], "requisiciones": []}
    
    try:
        detector = get_detector()
        servers = _get_servers_for_detection()
        
        if not servers:
            _release_detect_lock(run_id, "WARNING", 0, 0)
            return {"status": "WARNING", "message": "Sin servidores", "run_id": run_id}
        
        for server in servers:
            server_name = server.get('name', 'UNKNOWN')
            
            if not server.get('host') or not server.get('password'):
                continue
            
            server_info = {
                'id': server['id'],
                'name': server_name,
                'host': server['host'],
                'port': server['port'],
                'database': server['database'],
                'username': server['username'],
                'password': server['password'],
                'system_type': server['system_type'],
            }
            unidad_info = {
                'id': server['unidad_id'],
                'codigo': server['unidad_codigo'],
                'nombre': server['unidad_nombre'],
            }
            
            # Detectar nuevos inventarios
            if not dry_run:
                inv_result = detector.detectar_nuevos_inventarios(
                    server_info, unidad_info, _execute_with_timeout
                )
            else:
                inv_result = {"nuevos_encontrados": 0, "eventos_generados": 0, "error": None}
            
            results["inventarios"].append({
                "server": server_name,
                "nuevos": inv_result.get("nuevos_encontrados", 0),
                "eventos": inv_result.get("eventos_generados", 0),
                "error": inv_result.get("error")
            })
            total_detected += inv_result.get("nuevos_encontrados", 0)
            total_eventos += inv_result.get("eventos_generados", 0)
            
            # Detectar nuevas requisiciones
            if not dry_run:
                req_result = detector.detectar_nuevas_requisiciones(
                    server_info, unidad_info, _execute_with_timeout
                )
            else:
                req_result = {"nuevos_encontrados": 0, "eventos_generados": 0, "error": None}
            
            results["requisiciones"].append({
                "server": server_name,
                "nuevos": req_result.get("nuevos_encontrados", 0),
                "eventos": req_result.get("eventos_generados", 0),
                "error": req_result.get("error")
            })
            total_detected += req_result.get("nuevos_encontrados", 0)
            total_eventos += req_result.get("eventos_generados", 0)
        
        # Procesar eventos pendientes (disparar informes)
        if not dry_run and total_eventos > 0:
            dispatcher = get_event_dispatcher()
            process_result = dispatcher.process_pending_events()
            logger.info(f"[DETECT] Eventos procesados: {process_result}")
        
        end_time = datetime.now(ZoneInfo("America/Mexico_City"))
        duration = int((end_time - start_time).total_seconds())
        
        status = "SUCCESS" if total_detected > 0 or not dry_run else "NO_CHANGES"
        _release_detect_lock(run_id, status, total_detected, total_eventos)
        
        logger.info(f"[DETECT] ========== FIN: {total_detected} detectados, {total_eventos} eventos ==========")
        
        return {
            "status": status,
            "run_id": run_id,
            "duration_seconds": duration,
            "total_detected": total_detected,
            "total_eventos": total_eventos,
            "servers_checked": len(servers),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"[DETECT] Error crítico: {e}")
        _release_detect_lock(run_id, "FAILED", total_detected, total_eventos)
        return {"status": "FAILED", "run_id": run_id, "error": str(e)}


# =============================================================================
# FUNCIONES PARA SCHEDULER
# =============================================================================

async def run_detect_nuevos_job():
    """Función async para el scheduler APScheduler."""
    import asyncio
    
    logger.info("[DETECT-JOB] Iniciando detección programada")
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, execute_detect_nuevos, False)
    logger.info(f"[DETECT-JOB] Completado: {result.get('status')}")
    return result


def get_job_config() -> Dict:
    """Retorna la configuración del job para el scheduler."""
    return {
        "job_id": JOB_NAME,
        "job_name": "Detección de Nuevos Inventarios/Requisiciones",
        "func": run_detect_nuevos_job,
        "trigger": "interval",
        "seconds": POLLING_INTERVAL_SECONDS,
        "description": "Detecta nuevos registros cada 2 min y genera eventos para informes",
        "enabled": os.environ.get("COMPRAS_DETECT_ENABLED", "true").lower() == "true"
    }
