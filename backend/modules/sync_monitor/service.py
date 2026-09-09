"""
P3-02 Sync Monitor Service - SQL-First
Monitor de sincronizaciones usando SOLO tablas existentes en EDARSAHUB SQL.

Tablas consumidas (NO crea nuevas):
- Compras_Sync_Log
- Comercial_SyncLog_v2
- Sync_Logs
- Servidores_Conexiones

NO usa MongoDB.
NO usa conexiones LIVE.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)

# P3A-R3 certificó que no existe una configuración SQL explícita de SLA/threshold
# aplicable al Sync Monitor. No se permiten umbrales operativos inventados.
SYNC_SLA_EVIDENCE = "P3A_R3_NO_CANONICAL_SYNC_SLA_CONFIG_CERTIFIED"


def _get_stale_threshold(sync_type: str) -> Optional[int]:
    """Devuelve None mientras no exista un SLA canónico certificado para el proceso."""
    return None


def _calculate_status(
    last_sync: Optional[datetime],
    original_status: str,
    sync_type: str,
    error_message: Optional[str] = None
) -> str:
    """Calcula estado sin fabricar STALE cuando no hay SLA canónico."""
    if error_message or (original_status and "ERROR" in original_status.upper()):
        return "ERROR"
    if original_status and "WARNING" in original_status.upper():
        return "WARNING"
    if not last_sync:
        return "SIN_TELEMETRIA"
    threshold_minutes = _get_stale_threshold(sync_type)
    if threshold_minutes is None:
        return "SIN_SLA_THRESHOLD_CONFIGURADO"
    cutoff = datetime.now() - timedelta(minutes=threshold_minutes)
    if last_sync < cutoff:
        return "STALE"
    return "SUCCESS"


def _safe_float(val) -> float:
    """Convierte valor a float de forma segura."""
    if val is None:
        return 0.0
    if isinstance(val, Decimal):
        return float(val)
    try:
        return float(val)
    except Exception:
        return 0.0



def _safe_datetime(val):
    """Convierte fechas SQL/strings ISO a datetime naive para comparaciones seguras."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.replace(tzinfo=None)
    if isinstance(val, str):
        raw = val.strip()
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            try:
                return datetime.strptime(raw[:19], "%Y-%m-%d %H:%M:%S")
            except Exception:
                return None
    return None


def _norm_server_id(val) -> str:
    """Normaliza server_id canónico para cruces contra Servidores_Conexiones."""
    return _safe_str(val).lower()


def _safe_str(val) -> str:
    """Convierte valor a string de forma segura."""
    if val is None:
        return ""
    return str(val)


def get_sync_monitor_data() -> Dict[str, Any]:
    """
    Obtiene datos consolidados del monitor de sincronización.
    
    Returns:
        {
            "servidores": [...],
            "procesos": [...],
            "errores": [...],
            "ultimos_syncs": [],
            "kpis": {...}
        }
    """
    from core.config.edarsahub_sql import get_edarsahub_connection
    
    try:
        conn = get_edarsahub_connection(timeout=30)
        cursor = conn.cursor(as_dict=True)
        
        now = datetime.now()
        hace_24h = now - timedelta(hours=24)
        
        # 1. Obtener servidores activos
        cursor.execute("""
            SELECT 
                CAST(id AS VARCHAR(100)) AS server_id,
                nombre,
                system_type,
                tipo_conexion,
                activo,
                fecha_ultima_sincronizacion,
                source_status,
                ultimo_error_sync
            FROM Servidores_Conexiones
            WHERE ISNULL(activo, 1) = 1
            ORDER BY nombre
        """)
        servidores_raw = cursor.fetchall()
        
        # 2. Obtener últimos syncs de Compras_Sync_Log
        cursor.execute("""
            SELECT 
                server_id,
                sync_type,
                MAX(sync_end) AS last_sync,
                MAX(CASE WHEN status = 'OK' THEN sync_end END) AS last_success,
                SUM(records_synced) AS total_records,
                COUNT(*) AS total_runs,
                SUM(CASE WHEN status != 'OK' THEN 1 ELSE 0 END) AS error_count,
                AVG(DATEDIFF(SECOND, sync_start, sync_end)) AS avg_duration_sec
            FROM Compras_Sync_Log
            WHERE sync_start >= %s
            GROUP BY server_id, sync_type
        """, (hace_24h,))
        compras_syncs = cursor.fetchall()
        
        # 3. Obtener últimos syncs de Comercial_SyncLog_v2
        cursor.execute("""
            SELECT 
                server_id,
                run_type AS sync_type,
                MAX(run_timestamp) AS last_sync,
                MAX(CASE WHEN status = 'SUCCESS' THEN run_timestamp END) AS last_success,
                SUM(ISNULL(records_processed, 0)) AS total_records,
                COUNT(*) AS total_runs,
                SUM(CASE WHEN status != 'SUCCESS' THEN 1 ELSE 0 END) AS error_count,
                AVG(ISNULL(duration_seconds, 0)) AS avg_duration_sec
            FROM Comercial_SyncLog_v2
            WHERE run_timestamp >= %s
            GROUP BY server_id, run_type
        """, (hace_24h,))
        # cursor as_dict ya retorna dicts
        comercial_syncs = cursor.fetchall()

        # KPI exacto de errores 24h: los listados posteriores usan TOP N solo para UI.
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM Compras_Sync_Log
            WHERE status != 'OK'
              AND sync_start >= %s
        """, (hace_24h,))
        row = cursor.fetchone() or {}
        total_errores_compras_24h = int(row.get("total") or 0)

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM Comercial_SyncLog_v2
            WHERE status != 'SUCCESS'
              AND run_timestamp >= %s
        """, (hace_24h,))
        row = cursor.fetchone() or {}
        total_errores_comercial_24h = int(row.get("total") or 0)

        # 4. Obtener errores últimas 24h
        cursor.execute("""
            SELECT TOP 50
                server_id,
                sync_type,
                sync_start,
                sync_end,
                status,
                error_message,
                records_synced
            FROM Compras_Sync_Log
            WHERE status != 'OK'
              AND sync_start >= %s
            ORDER BY sync_start DESC
        """, (hace_24h,))
        # cursor as_dict ya retorna dicts
        errores_compras = cursor.fetchall()
        
        cursor.execute("""
            SELECT TOP 50
                server_id,
                run_type AS sync_type,
                run_timestamp AS sync_start,
                run_timestamp AS sync_end,
                status,
                error_message,
                records_processed AS records_synced
            FROM Comercial_SyncLog_v2
            WHERE status != 'SUCCESS'
              AND run_timestamp >= %s
            ORDER BY run_timestamp DESC
        """, (hace_24h,))
        # cursor as_dict ya retorna dicts
        errores_comercial = cursor.fetchall()
        
        # 5. Telemetría genérica Sync_Logs. P3A-R3 certificó que existe, pero
        # no tiene server_id ni columnas de resultado cuantitativo; por ello se expone
        # como actividad global NO asignable a procesos/servidores.
        cursor.execute("""
            SELECT TOP 20 id, service, type, message, timestamp, operador
            FROM Sync_Logs
            ORDER BY timestamp DESC, id DESC
        """)
        sync_logs_genericos = cursor.fetchall()

        # 6. Últimos syncs generales (últimos 20)
        cursor.execute("""
            SELECT TOP 20
                server_id,
                sync_type,
                sync_start,
                sync_end,
                status,
                records_synced,
                error_message
            FROM Compras_Sync_Log
            ORDER BY sync_start DESC
        """)
        # cursor as_dict ya retorna dicts
        ultimos_compras = cursor.fetchall()
        
        cursor.execute("""
            SELECT TOP 20
                server_id,
                run_type AS sync_type,
                run_timestamp AS sync_start,
                run_timestamp AS sync_end,
                status,
                records_processed AS records_synced,
                error_message
            FROM Comercial_SyncLog_v2
            ORDER BY run_timestamp DESC
        """)
        # cursor as_dict ya retorna dicts
        ultimos_comercial = cursor.fetchall()
        
        conn.close()
        
        # Procesar servidores con estado calculado
        server_map = {_norm_server_id(s["server_id"]): s for s in servidores_raw}
        
        # Consolidar procesos por servidor
        procesos = []
        all_syncs = compras_syncs + comercial_syncs
        
        for sync in all_syncs:
            server_id = _norm_server_id(sync.get("server_id"))
            sync_type = _safe_str(sync.get("sync_type"))
            last_sync = _safe_datetime(sync.get("last_sync"))
            last_success = _safe_datetime(sync.get("last_success"))
            total_records = int(sync.get("total_records") or 0)
            total_runs = int(sync.get("total_runs") or 0)
            error_count = int(sync.get("error_count") or 0)
            avg_duration = _safe_float(sync.get("avg_duration_sec"))
            
            # Determinar status original
            original_status = "OK" if error_count == 0 else "ERROR"
            
            # Calcular estado final
            status = _calculate_status(last_sync, original_status, sync_type)
            
            # Nombre del servidor
            server_info = server_map.get(server_id, {})
            server_name = server_info.get("nombre", server_id[:20] if server_id else "DESCONOCIDO")
            
            procesos.append({
                "server_id": server_id,
                "server_name": server_name,
                "sync_type": sync_type,
                "last_sync": last_sync.isoformat() if last_sync else None,
                "last_success": last_success.isoformat() if last_success else None,
                "total_records_24h": total_records,
                "total_runs_24h": total_runs,
                "error_count_24h": error_count,
                "avg_duration_sec": round(avg_duration, 2),
                "status": status,
            })
        
        # Consolidar errores
        errores = []
        for err in errores_compras + errores_comercial:
            server_id = _norm_server_id(err.get("server_id"))
            server_info = server_map.get(server_id, {})
            server_name = server_info.get("nombre", server_id[:20] if server_id else "DESCONOCIDO")
            
            sync_start = _safe_datetime(err.get("sync_start"))
            sync_end = _safe_datetime(err.get("sync_end"))
            
            errores.append({
                "server_id": server_id,
                "server_name": server_name,
                "sync_type": _safe_str(err.get("sync_type")),
                "timestamp": sync_start.isoformat() if sync_start else None,
                "status": _safe_str(err.get("status")),
                "error_message": _safe_str(err.get("error_message")),
                "records": int(err.get("records_synced") or 0),
            })
        
        # Consolidar últimos syncs
        ultimos_syncs = []
        for ult in ultimos_compras + ultimos_comercial:
            server_id = _norm_server_id(ult.get("server_id"))
            server_info = server_map.get(server_id, {})
            server_name = server_info.get("nombre", server_id[:20] if server_id else "DESCONOCIDO")
            
            sync_start = _safe_datetime(ult.get("sync_start"))
            sync_end = _safe_datetime(ult.get("sync_end"))
            sync_type = _safe_str(ult.get("sync_type"))
            original_status = _safe_str(ult.get("status"))
            
            # Calcular duración
            duration = 0
            if sync_start and sync_end:
                try:
                    duration = (sync_end - sync_start).total_seconds()
                except Exception:
                    pass
            
            status = _calculate_status(sync_start, original_status, sync_type, ult.get("error_message"))
            
            ultimos_syncs.append({
                "server_id": server_id,
                "server_name": server_name,
                "sync_type": sync_type,
                "timestamp": sync_start.isoformat() if sync_start else None,
                "duration_sec": round(duration, 2),
                "records": int(ult.get("records_synced") or 0),
                "status": status,
                "error_message": _safe_str(ult.get("error_message")) if ult.get("error_message") else None,
            })
        
        # Ordenar por timestamp desc
        ultimos_syncs.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
        ultimos_syncs = ultimos_syncs[:30]
        
        # Servidores con estado consolidado
        servidores = []
        for srv in servidores_raw:
            server_id = _norm_server_id(srv.get("server_id"))
            
            # Buscar último sync de este servidor
            srv_procesos = [p for p in procesos if p["server_id"] == server_id]
            
            if srv_procesos:
                # Estado = peor estado de sus procesos
                statuses = [p["status"] for p in srv_procesos]
                if "ERROR" in statuses:
                    srv_status = "ERROR"
                elif "STALE" in statuses:
                    srv_status = "STALE"
                elif "WARNING" in statuses:
                    srv_status = "WARNING"
                else:
                    srv_status = "SUCCESS"
                
                last_sync_values = [
                    _safe_datetime(p.get("last_sync"))
                    for p in srv_procesos
                    if p.get("last_sync")
                ]
                last_sync_dt = max(last_sync_values) if last_sync_values else None
                last_sync_all = last_sync_dt.isoformat() if last_sync_dt else None
                total_records = sum(p["total_records_24h"] for p in srv_procesos)
                total_errors = sum(p["error_count_24h"] for p in srv_procesos)
            else:
                # Servidor activo sin proceso correlacionable en las fuentes canónicas.
                srv_status = "SIN_TELEMETRIA"
                last_sync_all = None
                total_records = 0
                total_errors = 0
            
            servidores.append({
                "server_id": server_id,
                "nombre": srv.get("nombre"),
                "system_type": srv.get("system_type"),
                "tipo_conexion": srv.get("tipo_conexion"),
                "activo": srv.get("activo"),
                "last_sync": last_sync_all,
                "total_records_24h": total_records,
                "error_count_24h": total_errors,
                "status": srv_status,
            })
        
        # KPIs globales
        total_servidores = len(servidores)
        servidores_ok = len([s for s in servidores if s["status"] == "SUCCESS"])
        servidores_warning = len([s for s in servidores if s["status"] == "WARNING"])
        servidores_error = len([s for s in servidores if s["status"] == "ERROR"])
        servidores_stale = len([s for s in servidores if s["status"] == "STALE"])
        servidores_sin_sla = len([s for s in servidores if s["status"] == "SIN_SLA_THRESHOLD_CONFIGURADO"])
        servidores_sin_telemetria = len([s for s in servidores if s["status"] == "SIN_TELEMETRIA"])
        
        total_errores_24h = total_errores_compras_24h + total_errores_comercial_24h
        total_records_24h = sum(p["total_records_24h"] for p in procesos)
        total_runs_24h = sum(p["total_runs_24h"] for p in procesos)
        
        return {
            "success": True,
            "source": "EDARSAHUB_SQL",
            "generated_at": now.isoformat(),
            "servidores": servidores,
            "procesos": procesos,
            "errores": errores[:20],
            "ultimos_syncs": ultimos_syncs,
            "sync_logs_genericos": [
                {
                    "id": row.get("id"),
                    "service": _safe_str(row.get("service")),
                    "type": _safe_str(row.get("type")),
                    "message": _safe_str(row.get("message")),
                    "timestamp": _safe_datetime(row.get("timestamp")).isoformat() if _safe_datetime(row.get("timestamp")) else None,
                    "operador": _safe_str(row.get("operador")),
                }
                for row in sync_logs_genericos
            ],
            "universo": {
                "server_catalog": "dbo.Servidores_Conexiones",
                "process_sources": ["dbo.Compras_Sync_Log", "dbo.Comercial_SyncLog_v2"],
                "generic_telemetry_source": "dbo.Sync_Logs",
                "generic_telemetry_scope": "GLOBAL_UNSCOPED_NO_SERVER_ID",
                "sla_config_status": "SIN_SLA_THRESHOLD_CONFIGURADO",
                "sla_evidence": SYNC_SLA_EVIDENCE,
            },
            "kpis": {
                "total_servidores": total_servidores,
                "servidores_ok": servidores_ok,
                "servidores_warning": servidores_warning,
                "servidores_error": servidores_error,
                "servidores_stale": servidores_stale,
                "servidores_sin_sla": servidores_sin_sla,
                "servidores_sin_telemetria": servidores_sin_telemetria,
                "total_errores_24h": total_errores_24h,
                "total_records_24h": total_records_24h,
                "total_runs_24h": total_runs_24h,
            },
        }
        
    except Exception as e:
        logger.error(f"[SYNC_MONITOR] Error obteniendo datos: {e}")
        return {
            "success": False,
            "source": "EDARSAHUB_SQL",
            "error": str(e),
            "servidores": [],
            "procesos": [],
            "errores": [],
            "ultimos_syncs": [],
            "sync_logs_genericos": [],
            "universo": {
                "server_catalog": "dbo.Servidores_Conexiones",
                "process_sources": ["dbo.Compras_Sync_Log", "dbo.Comercial_SyncLog_v2"],
                "generic_telemetry_source": "dbo.Sync_Logs",
                "generic_telemetry_scope": "GLOBAL_UNSCOPED_NO_SERVER_ID",
                "sla_config_status": "SIN_SLA_THRESHOLD_CONFIGURADO",
                "sla_evidence": SYNC_SLA_EVIDENCE,
            },
            "kpis": {},
        }
