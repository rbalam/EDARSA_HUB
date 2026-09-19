"""
EDARSA HUB - Job de Sincronización de Compras (Inventarios y Requisiciones)
============================================================================

PROPÓSITO:
Sincroniza datos de inventarios físicos y requisiciones desde los servidores
físicos (SoftRestaurant, MPRO) hacia las tablas intermedias en EDARSAHUB SQL.

POLÍTICA P0 SQL-ONLY:
- Los endpoints de compras NUNCA consultan servidores físicos directamente
- Este job es el ÚNICO autorizado para conectarse a los servidores origen
- Los datos se guardan en tablas intermedias que luego los endpoints consultan

TABLAS DESTINO:
- Compras_Inventarios_Fisicos_Sync
- Compras_Inventarios_Fisicos_Detalle_Sync
- Compras_Requisiciones_Sync
- Compras_Sync_Log

FRECUENCIA RECOMENDADA:
- Cada 30 minutos (configurable via ENV)
- Ejecutar fuera de horario pico para evitar saturar conexiones

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

from core.sql_first.connection_factory import (
    get_edarsahub_pymssql_connection,
    get_external_sql_connection,
)
from modules.integrations_runtime.sync_ledger import enrich_sync_start, mark_sync_finished
from modules.compras.sync_service import (
    sync_inventarios_fisicos_from_server,
    sync_requisiciones_from_server,
    sync_almacenes_from_server,
    sync_existencias_from_server,
    sync_movimientos_from_server,
    sync_pedidos_from_server,
    sync_ordenes_from_server,
    sync_recepciones_from_server,
    log_sync_operation,
    get_edarsahub_connection,
)

logger = logging.getLogger(__name__)

# Configuración
JOB_NAME = "sync_compras"
SYNC_INTERVAL_SECONDS = int(os.environ.get("SCHEDULER_SYNC_COMPRAS_INTERVAL_SECONDS", "1800"))  # 30 min default
SYNC_TYPE = "COMPRAS_SYNC"
LOCK_TIMEOUT_MINUTES = int(
    os.environ.get("SCHEDULER_SYNC_COMPRAS_LOCK_TIMEOUT_MINUTES", "5")
)

# P2-01: Config centralizado
from core.config.edarsahub_config import get_edarsahub_sql_config
from core.sql_first.db import get_sql_connection
_edarsa_cfg = get_edarsahub_sql_config()
EDARSAHUB_CONFIG = {
    'host': _edarsa_cfg.host,
    'port': _edarsa_cfg.port,
    'database': _edarsa_cfg.database,
    'username': _edarsa_cfg.user,
    'password': _edarsa_cfg.password
}


def _coerce_mx_datetime(value):
    """Normaliza datetime de SQL; algunos cursores devuelven texto."""
    if not value:
        return None
    if isinstance(value, str):
        text = value.strip()
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                value = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue
        else:
            try:
                value = datetime.fromisoformat(text)
            except ValueError:
                return None
    if value.tzinfo is None:
        return value.replace(tzinfo=ZoneInfo("America/Mexico_City"))
    return value.astimezone(ZoneInfo("America/Mexico_City"))


# =============================================================================
# LOCK ANTI-CONCURRENCIA SQL
# =============================================================================

def _acquire_sync_lock(run_id: str) -> bool:
    """
    Adquiere lock para evitar ejecuciones concurrentes.
    Retorna True si OK, False si hay lock activo.
    """
    from datetime import timedelta

    conn = None
    cursor = None

    try:
        conn = get_edarsahub_pymssql_connection(
            timeout=15,
            login_timeout=10,
        )
        cursor = conn.cursor(as_dict=True)
        now_mx = datetime.now(ZoneInfo("America/Mexico_City"))
        now_sql = now_mx.replace(tzinfo=None)
        timeout_threshold = (
            now_mx - timedelta(minutes=LOCK_TIMEOUT_MINUTES)
        ).replace(tzinfo=None)

        cursor.execute("SET XACT_ABORT ON")
        cursor.execute("SET LOCK_TIMEOUT 10000")
        cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
        cursor.execute("BEGIN TRANSACTION")

        # Liberar locks vencidos sin depender del tipo devuelto por el driver.
        cursor.execute("""
            UPDATE dbo.Sync_Control_Ejecuciones
               WITH (UPDLOCK, HOLDLOCK)
            SET
                Status = 'TIMEOUT',
                FinishedAtMexico = %s,
                FinishedAtUTC = COALESCE(FinishedAtUTC, SYSUTCDATETIME()),
                ErrorMessage = COALESCE(
                    ErrorMessage,
                    'Lock vencido antes de nueva ejecución'
                )
            WHERE SyncType = %s
              AND Status = 'IN_PROGRESS'
              AND FinishedAtMexico IS NULL
              AND (
                    StartedAtMexico IS NULL
                    OR StartedAtMexico < %s
              )
        """, (now_sql, SYNC_TYPE, timeout_threshold))

        stale_count = cursor.rowcount
        if stale_count and stale_count > 0:
            logger.warning(
                "[SYNC-COMPRAS-LOCK] Locks vencidos marcados TIMEOUT: %s",
                stale_count,
            )

        # La lectura y el INSERT quedan serializados en la misma transacción.
        cursor.execute("""
            SELECT TOP (1)
                SyncControlID,
                SyncRunID,
                StartedAtMexico
            FROM dbo.Sync_Control_Ejecuciones
                 WITH (UPDLOCK, HOLDLOCK)
            WHERE SyncType = %s
              AND Status = 'IN_PROGRESS'
              AND FinishedAtMexico IS NULL
            ORDER BY StartedAtMexico
        """, (SYNC_TYPE,))
        active = cursor.fetchone()

        if active:
            conn.commit()
            logger.warning(
                "[SYNC-COMPRAS-LOCK] Lock activo: %s iniciado=%s - Abortando",
                active.get("SyncRunID"),
                active.get("StartedAtMexico"),
            )
            return False

        # Crear nuevo lock
        today = now_mx.date()
        cursor.execute("""
            INSERT INTO Sync_Control_Ejecuciones (
                SyncRunID, SyncType, FechaInicio, FechaFin, VentanaInicioHoraConfig,
                VentanaFinHoraConfig, IsDryRun, RegistrosProcesados, RegistrosInsertados,
                RegistrosActualizados, RegistrosError, Status, StartedAtMexico, CreatedAt
            ) VALUES (%s,%s,%s,%s,0,0,0,0,0,0,0,'IN_PROGRESS',%s,%s)
        """, (run_id, SYNC_TYPE, today, today, now_sql, now_sql))
        enrich_sync_start(
            cursor,
            sync_run_id=run_id,
            sync_type=SYNC_TYPE,
        )
        conn.commit()
        logger.info(f"[SYNC-COMPRAS-LOCK] 🔒 Lock adquirido: {run_id}")
        return True
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        logger.error(f"[SYNC-COMPRAS-LOCK] Error adquiriendo lock; ejecución bloqueada: {e}")
        return False
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _release_sync_lock(run_id: str, status: str, processed: int, errors: int, error_msg: str = None):
    """Libera el lock de sincronización."""
    conn = None
    cursor = None

    try:
        conn = get_edarsahub_pymssql_connection(
            timeout=15,
            login_timeout=10,
        )
        cursor = conn.cursor()
        now_mx = datetime.now(ZoneInfo("America/Mexico_City"))
        now_sql = now_mx.replace(tzinfo=None)
        
        # Calcular duración
        cursor.execute("SELECT StartedAtMexico FROM Sync_Control_Ejecuciones WHERE SyncRunID=%s", (run_id,))
        row = cursor.fetchone()
        duration = 0
        if row and row[0]:
            started = _coerce_mx_datetime(row[0])
            if started:
                duration = int((now_mx - started).total_seconds())
        
        cursor.execute("""
            UPDATE Sync_Control_Ejecuciones
            SET Status=%s, FinishedAtMexico=%s, DurationSeconds=%s, RegistrosProcesados=%s, RegistrosError=%s, ErrorMessage=%s
            WHERE SyncRunID=%s
        """, (status, now_sql, duration, processed, errors, error_msg[:500] if error_msg else None, run_id))
        mark_sync_finished(cursor, run_id)
        conn.commit()
        logger.info(f"[SYNC-COMPRAS-LOCK] 🔓 Lock liberado: {run_id} (status={status}, duration={duration}s)")
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        logger.error(f"[SYNC-COMPRAS-LOCK] Error liberando lock: {e}")
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


# =============================================================================
# OBTENER SERVIDORES PARA SINCRONIZAR
# =============================================================================

def _execute_sql_with_timeout(host, port, database, username, password, query, timeout_seconds=45):
    """
    Ejecuta query SQL con timeout usando el parámetro nativo de execute_sql_query.
    NOTA: Se eliminó signal.alarm() porque no funciona en threads secundarios (FastAPI async).
    El timeout se maneja directamente en la conexión SQL.
    """
    conn = None
    cursor = None

    try:
        conn = get_external_sql_connection({
            "host": host,
            "port": port,
            "database": database,
            "username": username,
            "password": password,
            "timeout": timeout_seconds,
            "login_timeout": min(10, max(1, int(timeout_seconds))),
            "as_dict": True,
        })
        try:
            cursor = conn.cursor(as_dict=True)
        except TypeError:
            cursor = conn.cursor()

        cursor.execute(query)
        rows = cursor.fetchall()
        if not rows:
            return []
        if isinstance(rows[0], dict):
            return [dict(row) for row in rows]

        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        error_str = str(e).lower()
        if 'timeout' in error_str or 'connection' in error_str or 'timed out' in error_str:
            logger.warning(f"[SYNC-COMPRAS] Error de conexión/timeout a {host}: {str(e)[:100]}")
            return None
        logger.error(f"[SYNC-COMPRAS] Error inesperado en query a {host}: {str(e)[:200]}")
        raise
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _get_servers_to_sync() -> List[Dict]:
    """
    Obtiene la lista de servidores activos configurados para sincronización.
    Lee desde Servidores_Conexiones y Unidades_Negocio en EDARSAHUB.
    """
    from core.secret_manager import decrypt_secret
    
    try:
        conn = get_edarsahub_connection()
        cursor = conn.cursor(as_dict=True)
        
        # Obtener servidores SQL activos con su unidad asociada
        cursor.execute("""
            SELECT 
                s.id, s.nombre as server_name, s.host, s.port, s.database_name,
                s.username, s.password_encrypted, s.system_type, s.activo,
                u.id as unidad_id, u.codigo as unidad_codigo, u.nombre as unidad_nombre,
                u.sucursal_origen_id as sucursal_origen_id
            FROM Servidores_Conexiones s
            LEFT JOIN Unidades_Negocio u ON u.server_id = CAST(s.id AS NVARCHAR(36))
            WHERE s.activo = 1
              AND s.tipo_conexion IN ('SQL_SERVER', 'DATA_SOURCE')
              AND UPPER(LTRIM(RTRIM(s.system_type))) IN (
                  'SOFTRESTAURANT', 'SOFTRESTAURANT_PRO', 'SOFTRESTAURANTPRO', 'SR',
                  'MPRO', 'MANAGEMENTPRO', 'MANAGMENTPRO'
              )
              AND u.id IS NOT NULL
              AND s.host IS NOT NULL AND s.host != ''
            ORDER BY u.codigo, u.nombre, s.nombre
        """)
        rows = cursor.fetchall()
        conn.close()
        
        servers = []
        for row in rows:
            # Desencriptar contraseña si está encriptada
            password = ''
            if row.get('password_encrypted'):
                try:
                    password = decrypt_secret(row['password_encrypted'])
                except Exception as e:
                    logger.warning(f"[SYNC-COMPRAS] No se pudo desencriptar password de {row['server_name']}: {e}")
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
                'sucursal_origen_id': row.get('sucursal_origen_id'),
            })
        
        logger.info(f"[SYNC-COMPRAS] Servidores encontrados: {len(servers)}")
        return servers
        
    except Exception as e:
        logger.error(f"[SYNC-COMPRAS] Error obteniendo servidores: {e}")
        return []


# =============================================================================
# FUNCIÓN PRINCIPAL DE EJECUCIÓN
# =============================================================================

def execute_sync_compras(dry_run: bool = False) -> Dict[str, Any]:
    """
    Ejecuta la sincronización completa de Compras.
    
    Args:
        dry_run: Si True, no guarda cambios en la base de datos
    
    Returns:
        Dict con resultados de la sincronización
    """
    run_id = f"COMPRAS-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"
    logger.info(f"[SYNC-COMPRAS] ========== INICIO SINCRONIZACIÓN {run_id} ==========")
    
    # Adquirir lock
    if not _acquire_sync_lock(run_id):
        return {
            "status": "SKIPPED",
            "reason": "Lock activo - otra sincronización en curso",
            "run_id": run_id
        }
    
    start_time = datetime.now(ZoneInfo("America/Mexico_City"))
    total_processed = 0
    total_errors = 0
    results = {
        "inventarios": [],
        "requisiciones": [],
        "almacenes": [],
        "existencias": [],
        "movimientos": [],
        "pedidos": [],
        "ordenes": [],
        "recepciones": []
    }
    error_messages = []
    
    try:
        # Obtener servidores
        servers = _get_servers_to_sync()
        
        if not servers:
            logger.warning("[SYNC-COMPRAS] No hay servidores configurados para sincronizar")
            _release_sync_lock(run_id, "WARNING", 0, 0, "Sin servidores configurados")
            return {
                "status": "WARNING",
                "message": "No hay servidores configurados",
                "run_id": run_id
            }
        
        # Sincronizar cada servidor
        for server in servers:
            server_name = server.get('name', 'UNKNOWN')
            unidad_codigo = server.get('unidad_codigo', '')
            
            logger.warning(f"[SYNC-COMPRAS] Procesando: {server_name} ({unidad_codigo})")
            
            if not server.get('host') or not server.get('password'):
                logger.warning(f"[SYNC-COMPRAS] Servidor {server_name} sin host/password - Saltando")
                error_messages.append(f"{server_name}: Sin credenciales")
                total_errors += 1
                continue
            
            server_info = {
                'id': server['id'],
                'host': server['host'],
                'port': server['port'],
                'database': server['database'],
                'username': server['username'],
                'password': server['password'],
                'system_type': server['system_type'],
            }
            unidad_info = {
                'id': server['unidad_id'],
                'codigo': unidad_codigo,
                'nombre': server['unidad_nombre'],
                'sucursal_origen_id': server.get('sucursal_origen_id'),
            }
            
            # Sincronizar Inventarios Físicos
            try:
                sync_start = datetime.now(ZoneInfo("America/Mexico_City"))
                
                if not dry_run:
                    inv_result = sync_inventarios_fisicos_from_server(
                        server_info, unidad_info, _execute_sql_with_timeout
                    )
                else:
                    inv_result = {"status": "DRY_RUN", "records_synced": 0, "error": None}
                
                sync_end = datetime.now(ZoneInfo("America/Mexico_City"))
                
                results["inventarios"].append({
                    "server": server_name,
                    "unidad": unidad_codigo,
                    "status": inv_result.get("status"),
                    "records": inv_result.get("records_synced", 0),
                    "details_synced": inv_result.get("details_synced", 0),
                    "details_updated": inv_result.get("details_updated", 0),
                    "detail_errors": inv_result.get("detail_errors", 0),
                    "error": inv_result.get("error")
                })
                
                if inv_result.get("status") == "OK" or inv_result.get("status") == "DRY_RUN":
                    total_processed += inv_result.get("records_synced", 0)
                    total_processed += inv_result.get("details_synced", 0)
                    total_processed += inv_result.get("details_updated", 0)
                    logger.warning(
                        "[SYNC-COMPRAS] ✅ Inventarios %s: headers=%s detalles_insertados=%s detalles_actualizados=%s",
                        server_name,
                        inv_result.get("records_synced", 0),
                        inv_result.get("details_synced", 0),
                        inv_result.get("details_updated", 0),
                    )
                else:
                    total_errors += 1
                    error_messages.append(f"{server_name} INV: {inv_result.get('error', 'Error desconocido')}")
                    logger.warning(f"[SYNC-COMPRAS] ❌ Inventarios {server_name}: {inv_result.get('error')}")
                
                # Log en tabla de sync
                if not dry_run:
                    log_sync_operation(
                        unidad_negocio_id=unidad_info['id'],
                        server_id=server_info['id'],
                        sync_type="INVENTARIOS",
                        sync_start=sync_start,
                        sync_end=sync_end,
                        records_synced=inv_result.get("records_synced", 0),
                        status=inv_result.get("status", "ERROR"),
                        error_message=inv_result.get("error")
                    )
                    
            except Exception as e:
                logger.error(f"[SYNC-COMPRAS] Error sincronizando inventarios {server_name}: {e}")
                total_errors += 1
                error_messages.append(f"{server_name} INV: {str(e)[:100]}")
            
            # Sincronizar Requisiciones
            try:
                sync_start = datetime.now(ZoneInfo("America/Mexico_City"))
                
                if not dry_run:
                    req_result = sync_requisiciones_from_server(
                        server_info, unidad_info, _execute_sql_with_timeout
                    )
                else:
                    req_result = {"status": "DRY_RUN", "records_synced": 0, "error": None}
                
                sync_end = datetime.now(ZoneInfo("America/Mexico_City"))
                
                results["requisiciones"].append({
                    "server": server_name,
                    "unidad": unidad_codigo,
                    "status": req_result.get("status"),
                    "records": req_result.get("records_synced", 0),
                    "error": req_result.get("error")
                })
                
                if req_result.get("status") == "OK" or req_result.get("status") == "DRY_RUN":
                    total_processed += req_result.get("records_synced", 0)
                    logger.info(f"[SYNC-COMPRAS] ✅ Requisiciones {server_name}: {req_result.get('records_synced', 0)} registros")
                else:
                    total_errors += 1
                    error_messages.append(f"{server_name} REQ: {req_result.get('error', 'Error desconocido')}")
                    logger.warning(f"[SYNC-COMPRAS] ❌ Requisiciones {server_name}: {req_result.get('error')}")
                
                # Log en tabla de sync
                if not dry_run:
                    log_sync_operation(
                        unidad_negocio_id=unidad_info['id'],
                        server_id=server_info['id'],
                        sync_type="REQUISICIONES",
                        sync_start=sync_start,
                        sync_end=sync_end,
                        records_synced=req_result.get("records_synced", 0),
                        status=req_result.get("status", "ERROR"),
                        error_message=req_result.get("error")
                    )
                    
            except Exception as e:
                logger.error(f"[SYNC-COMPRAS] Error sincronizando requisiciones {server_name}: {e}")
                total_errors += 1
                error_messages.append(f"{server_name} REQ: {str(e)[:100]}")
            
            # =================================================================
            # SQL-FIRST FASE 2: Sincronizaciones adicionales Compras/Inventarios
            # =================================================================
            sync_steps = [
                ("almacenes", sync_almacenes_from_server, "ALMACENES"),
                ("existencias", sync_existencias_from_server, "EXISTENCIAS"),
                ("movimientos", sync_movimientos_from_server, "MOVIMIENTOS"),
                ("pedidos", sync_pedidos_from_server, "PEDIDOS"),
                ("ordenes", sync_ordenes_from_server, "ORDENES"),
                ("recepciones", sync_recepciones_from_server, "RECEPCIONES"),
            ]
            
            for step_name, step_func, sync_type_label in sync_steps:
                try:
                    sync_start = datetime.now(ZoneInfo("America/Mexico_City"))
                    logger.info(f"[SYNC-COMPRAS] Ejecutando {step_name} para {server_name}")
                    
                    if not dry_run:
                        step_result = step_func(
                            server_info, unidad_info, _execute_sql_with_timeout
                        )
                    else:
                        step_result = {"status": "DRY_RUN", "records_synced": 0, "error": None}
                    
                    sync_end = datetime.now(ZoneInfo("America/Mexico_City"))
                    
                    results[step_name].append({
                        "server": server_name,
                        "unidad": unidad_codigo,
                        "status": step_result.get("status"),
                        "records": step_result.get("records_synced", 0),
                        "encabezados": step_result.get("encabezados_synced", 0),
                        "detalles": step_result.get("detalles_synced", 0),
                        "error": step_result.get("error")
                    })
                    
                    if step_result.get("status") in ("OK", "DRY_RUN"):
                        synced = step_result.get("records_synced", 0) + step_result.get("encabezados_synced", 0)
                        total_processed += synced
                        logger.info(f"[SYNC-COMPRAS] ✅ {step_name} {server_name}: {synced} registros")
                    else:
                        total_errors += 1
                        error_messages.append(f"{server_name} {step_name.upper()}: {step_result.get('error', 'Error desconocido')}")
                        logger.warning(f"[SYNC-COMPRAS] ❌ {step_name} {server_name}: {step_result.get('error')}")
                    
                    if not dry_run:
                        log_sync_operation(
                            unidad_negocio_id=unidad_info['id'],
                            server_id=server_info['id'],
                            sync_type=sync_type_label,
                            sync_start=sync_start,
                            sync_end=sync_end,
                            records_synced=step_result.get("records_synced", 0) + step_result.get("encabezados_synced", 0),
                            status=step_result.get("status", "ERROR"),
                            error_message=step_result.get("error")
                        )
                        
                except Exception as e:
                    logger.error(f"[SYNC-COMPRAS] Error en {step_name} {server_name}: {e}")
                    total_errors += 1
                    error_messages.append(f"{server_name} {step_name.upper()}: {str(e)[:100]}")
        
        # Determinar status final
        if total_errors == 0:
            final_status = "SUCCESS"
        elif total_processed > 0:
            final_status = "PARTIAL"
        else:
            final_status = "FAILED"
        
        end_time = datetime.now(ZoneInfo("America/Mexico_City"))
        duration = int((end_time - start_time).total_seconds())
        
        logger.info("[SYNC-COMPRAS] ========== FIN SINCRONIZACIÓN ==========")
        logger.info(f"[SYNC-COMPRAS] Status: {final_status}, Procesados: {total_processed}, Errores: {total_errors}, Duración: {duration}s")
        
        # Liberar lock
        error_summary = "; ".join(error_messages[:5]) if error_messages else None
        _release_sync_lock(run_id, final_status, total_processed, total_errors, error_summary)
        
        return {
            "status": final_status,
            "run_id": run_id,
            "duration_seconds": duration,
            "total_processed": total_processed,
            "total_errors": total_errors,
            "servers_processed": len(servers),
            "results": results,
            "errors": error_messages[:10]
        }
        
    except Exception as e:
        logger.error(f"[SYNC-COMPRAS] Error crítico: {e}")
        _release_sync_lock(run_id, "FAILED", total_processed, total_errors + 1, str(e)[:500])
        return {
            "status": "FAILED",
            "run_id": run_id,
            "error": str(e),
            "total_processed": total_processed,
            "total_errors": total_errors + 1
        }


# =============================================================================
# FUNCIONES PARA SCHEDULER
# =============================================================================

def _is_sync_compras_execution_enabled() -> bool:
    """
    Guardrail P0.

    La ejecución de SYNC_COMPRAS es fail-closed: requiere
    SCHEDULER_SYNC_COMPRAS_EXECUTION_ENABLED=true de forma explícita.
    El flag histórico SCHEDULER_SYNC_COMPRAS_ENABLED sigue aplicando,
    pero no autoriza ejecución por sí solo.
    """
    scheduler_enabled = (
        os.environ.get(
            "SCHEDULER_SYNC_COMPRAS_ENABLED",
            "true",
        ).strip().lower()
        == "true"
    )
    raw_execution_enabled = os.environ.get(
        "SCHEDULER_SYNC_COMPRAS_EXECUTION_ENABLED",
        "",
    ).strip().lower()
    execution_enabled = raw_execution_enabled == "true"
    return scheduler_enabled and execution_enabled


async def run_sync_compras_job(dry_run: bool = False):
    """Función async para el scheduler APScheduler."""
    import asyncio

    if not _is_sync_compras_execution_enabled():
        logger.warning(
            "[SYNC-COMPRAS-JOB] Ejecución omitida por guardrail "
            "SCHEDULER_SYNC_COMPRAS_EXECUTION_ENABLED"
        )
        return {
            "status": "DISABLED",
            "reason": "execution_guard",
        }

    logger.info("[SYNC-COMPRAS-JOB] Iniciando job programado")

    # Ejecutar en thread separado para no bloquear el event loop
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, execute_sync_compras, dry_run)
    
    logger.info(f"[SYNC-COMPRAS-JOB] Completado: {result.get('status')}")
    return result


def get_job_config() -> Dict:
    """Retorna la configuración del job para el scheduler."""
    return {
        "job_id": JOB_NAME,
        "job_name": "Sincronización Compras (Inventarios/Requisiciones)",
        "func": run_sync_compras_job,
        "trigger": "interval",
        "seconds": SYNC_INTERVAL_SECONDS,
        "description": "Sincroniza inventarios físicos y requisiciones desde servidores origen hacia EDARSAHUB SQL",
        "enabled": _is_sync_compras_execution_enabled()
    }
