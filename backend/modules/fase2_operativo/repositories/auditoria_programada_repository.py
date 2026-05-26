"""
Repository para Auditorías Programadas - VERSIÓN SQL
EDARSA HUB - Módulo Auditorías Programadas

FASE B-P1-E: Migrado a EDARSAHUB SQL Server
- CERO MongoDB productivo
- SQL explícito contra Operativo_AuditoriasProgramadas

Gestiona acceso a:
- auditorias_programadas (tabla principal)
- logs de ejecución (misma tabla con campos de log)
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import json
import logging

from .sql_base_repository import SQLBaseRepository

logger = logging.getLogger(__name__)


class AuditoriaProgramadaRepository(SQLBaseRepository):
    """
    Repository para auditorías programadas.
    Migrado de MongoDB a SQL Server EDARSAHUB.
    """
    
    def __init__(self, db=None):
        """
        Inicializa el repository SQL.
        Args:
            db: IGNORADO - Solo para compatibilidad. Todo va a SQL.
        """
        super().__init__("auditorias_programadas")
        logger.info(f"[AUDITORIA_PROG_REPO] Inicializado con SQL → {self.table_name}")
    
    # =========================================================================
    # CRUD AUDITORÍAS PROGRAMADAS (sync por compatibilidad)
    # =========================================================================
    
    def create(self, data: Dict) -> Dict:
        """Crea un nuevo documento (sync)."""
        now = datetime.now(timezone.utc)
        data["fecha_creacion"] = now
        data["fecha_ultima_actualizacion"] = now
        
        auditoria_id = data.get("id") or str(uuid.uuid4()).upper()
        
        sql_data = {
            "AuditoriaID": auditoria_id,
            "Nombre": data.get("nombre", ""),
            "Descripcion": data.get("descripcion", ""),
            "ServerID": data.get("server_id", ""),
            "SucursalID": data.get("sucursal_id", ""),
            "AlmacenID": data.get("almacen_id", ""),
            "Frecuencia": data.get("frecuencia", "MENSUAL"),
            "Activo": data.get("activo", True),
            "ProximaEjecucion": data.get("proxima_ejecucion"),
            "UltimaEjecucion": data.get("ultima_ejecucion"),
            "UltimaEjecucionStatus": data.get("ultima_ejecucion_status"),
        }
        
        columns = ", ".join(sql_data.keys())
        placeholders = ", ".join(["%s"] * len(sql_data))
        sql = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, list(sql_data.values()))
            conn.commit()
            cursor.close()
            conn.close()
            
            data["id"] = auditoria_id
            return data
            
        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error create: {e}")
            raise
    
    def get_by_id(self, id: str) -> Optional[Dict]:
        """Obtiene por ID usando campo AuditoriaID."""
        sql = f"SELECT * FROM {self.table_name} WHERE AuditoriaID = %s"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return self._row_to_auditoria_dict(row) if row else None
            
        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error get_by_id: {e}")
            return None
    
    def get_all(self) -> List[Dict]:
        """Obtiene todas las auditorías."""
        sql = f"SELECT * FROM {self.table_name} ORDER BY Nombre"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [self._row_to_auditoria_dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error get_all: {e}")
            return []
    
    def update(self, id: str, data: Dict) -> Dict:
        """Actualiza un documento (sync)."""
        data["fecha_ultima_actualizacion"] = datetime.now(timezone.utc)
        
        set_parts = []
        params = []
        
        field_mapping = {
            "nombre": "Nombre",
            "descripcion": "Descripcion",
            "server_id": "ServerID",
            "sucursal_id": "SucursalID",
            "almacen_id": "AlmacenID",
            "frecuencia": "Frecuencia",
            "activo": "Activo",
            "proxima_ejecucion": "ProximaEjecucion",
            "ultima_ejecucion": "UltimaEjecucion",
            "ultima_ejecucion_status": "UltimaEjecucionStatus",
        }
        
        for key, value in data.items():
            if key in field_mapping:
                set_parts.append(f"{field_mapping[key]} = %s")
                params.append(value)
        
        if not set_parts:
            return self.get_by_id(id)
        
        params.append(id)
        sql = f"UPDATE {self.table_name} SET {', '.join(set_parts)} WHERE AuditoriaID = %s"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            cursor.close()
            conn.close()
            
            return self.get_by_id(id)
            
        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error update: {e}")
            raise
    
    def delete(self, id: str) -> bool:
        """Elimina un documento (sync)."""
        sql = f"DELETE FROM {self.table_name} WHERE AuditoriaID = %s"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (id,))
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            return affected > 0
            
        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error delete: {e}")
            return False
    
    # =========================================================================
    # CONSULTAS ESPECÍFICAS
    # =========================================================================
    
    def get_activas(self) -> List[Dict]:
        """Obtiene todas las auditorías activas."""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE Activo = 1
            ORDER BY ProximaEjecucion
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [self._row_to_auditoria_dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error get_activas: {e}")
            return []
    
    def get_by_sucursal(self, sucursal_id: str) -> List[Dict]:
        """Obtiene auditorías de una sucursal."""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE SucursalID = %s
            ORDER BY Nombre
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (sucursal_id,))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [self._row_to_auditoria_dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error get_by_sucursal: {e}")
            return []
    
    def get_pendientes_ejecucion(self, hasta: datetime) -> List[Dict]:
        """
        Obtiene auditorías cuya próxima ejecución es <= hasta.
        Solo activas y con proxima_ejecucion definida.
        """
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE Activo = 1 AND ProximaEjecucion <= %s
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (hasta,))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [self._row_to_auditoria_dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error get_pendientes_ejecucion: {e}")
            return []
    
    def get_proximas_24h(self) -> List[Dict]:
        """Obtiene auditorías programadas para las próximas 24 horas."""
        ahora = datetime.now(timezone.utc)
        en_24h = ahora + timedelta(hours=24)
        
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE Activo = 1 
              AND ProximaEjecucion >= %s 
              AND ProximaEjecucion <= %s
            ORDER BY ProximaEjecucion
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (ahora, en_24h))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [self._row_to_auditoria_dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error get_proximas_24h: {e}")
            return []
    
    def actualizar_ejecucion(
        self,
        auditoria_id: str,
        estado: str,
        proxima: Optional[datetime] = None
    ) -> bool:
        """Actualiza estado de última ejecución y próxima."""
        now = datetime.now(timezone.utc)
        
        if proxima:
            sql = f"""
                UPDATE {self.table_name}
                SET UltimaEjecucion = %s, UltimaEjecucionStatus = %s, ProximaEjecucion = %s
                WHERE AuditoriaID = %s
            """
            params = (now, estado, proxima, auditoria_id)
        else:
            sql = f"""
                UPDATE {self.table_name}
                SET UltimaEjecucion = %s, UltimaEjecucionStatus = %s
                WHERE AuditoriaID = %s
            """
            params = (now, estado, auditoria_id)
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            return affected > 0
            
        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error actualizar_ejecucion: {e}")
            return False
    
    def activar(self, auditoria_id: str) -> bool:
        """Activa una auditoría programada."""
        sql = f"UPDATE {self.table_name} SET Activo = 1 WHERE AuditoriaID = %s"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (auditoria_id,))
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            return affected > 0
            
        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error activar: {e}")
            return False
    
    def desactivar(self, auditoria_id: str) -> bool:
        """Desactiva una auditoría programada."""
        sql = f"UPDATE {self.table_name} SET Activo = 0 WHERE AuditoriaID = %s"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (auditoria_id,))
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            return affected > 0
            
        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error desactivar: {e}")
            return False
    
    def contar_por_estado(self) -> Dict[str, int]:
        """Cuenta auditorías por estado activo/inactivo."""
        sql = f"""
            SELECT Activo, COUNT(*) as count
            FROM {self.table_name}
            GROUP BY Activo
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            result = {"activas": 0, "inactivas": 0}
            for row in rows:
                if row["Activo"]:
                    result["activas"] = row["count"]
                else:
                    result["inactivas"] = row["count"]
            return result
            
        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error contar_por_estado: {e}")
            return {"activas": 0, "inactivas": 0}
    
    def get_calendario(self, anio: int, mes: int) -> List[Dict]:
        """
        Obtiene auditorías para un mes específico (vista calendario).
        """
        inicio_mes = datetime(anio, mes, 1, tzinfo=timezone.utc)
        if mes == 12:
            fin_mes = datetime(anio + 1, 1, 1, tzinfo=timezone.utc)
        else:
            fin_mes = datetime(anio, mes + 1, 1, tzinfo=timezone.utc)
        
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE Activo = 1 
              AND ProximaEjecucion >= %s 
              AND ProximaEjecucion < %s
            ORDER BY ProximaEjecucion
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (inicio_mes, fin_mes))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [self._row_to_auditoria_dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error get_calendario: {e}")
            return []
    
    # =========================================================================
    # LOG DE EJECUCIONES (simplificado - usa campos de la tabla principal)
    # =========================================================================
    
    def crear_log(self, log_data: Dict) -> Dict:
        """
        Crea un registro de ejecución.
        NOTA: En SQL, los logs pueden ir en una tabla separada o como 
        actualizaciones de UltimaEjecucion/Status.
        """
        # Simplificado: actualizar campos de log en la auditoría
        auditoria_id = log_data.get("auditoria_programada_id")
        estado = log_data.get("estado", "EN_PROGRESO")
        
        if auditoria_id:
            self.actualizar_ejecucion(auditoria_id, estado)
        
        return log_data
    
    def get_logs(
        self,
        auditoria_id: Optional[str] = None,
        estado: Optional[str] = None,
        desde: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Obtiene logs de ejecución con filtros.
        NOTA: Simplificado - retorna info de últimas ejecuciones.
        """
        conditions = []
        params = []
        
        if auditoria_id:
            conditions.append("AuditoriaID = %s")
            params.append(auditoria_id)
        if estado:
            conditions.append("UltimaEjecucionStatus = %s")
            params.append(estado)
        if desde:
            conditions.append("UltimaEjecucion >= %s")
            params.append(desde)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        sql = f"""
            SELECT TOP {limit} * FROM {self.table_name}
            WHERE {where_clause} AND UltimaEjecucion IS NOT NULL
            ORDER BY UltimaEjecucion DESC
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Transformar a formato de log
            logs = []
            for row in rows:
                logs.append({
                    "auditoria_programada_id": row.get("AuditoriaID"),
                    "nombre": row.get("Nombre"),
                    "estado": row.get("UltimaEjecucionStatus"),
                    "fecha_ejecucion": row.get("UltimaEjecucion").isoformat() if row.get("UltimaEjecucion") else None,
                })
            return logs
            
        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error get_logs: {e}")
            return []
    
    def verificar_ejecucion_duplicada(
        self,
        auditoria_id: str,
        fecha_programada: datetime,
        ventana_minutos: int = 60
    ) -> bool:
        """
        Verifica si ya existe una ejecución para esta auditoría
        dentro de la ventana de tiempo (idempotencia).
        """
        inicio_ventana = fecha_programada - timedelta(minutes=ventana_minutos)
        fin_ventana = fecha_programada + timedelta(minutes=ventana_minutos)
        
        sql = f"""
            SELECT COUNT(*) as count FROM {self.table_name}
            WHERE AuditoriaID = %s
              AND UltimaEjecucion >= %s
              AND UltimaEjecucion <= %s
              AND UltimaEjecucionStatus IN ('COMPLETADA', 'EN_PROGRESO')
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (auditoria_id, inicio_ventana, fin_ventana))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return row["count"] > 0 if row else False
            
        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error verificar_ejecucion_duplicada: {e}")
            return False
    
    def contar_logs_mes(self, anio: int, mes: int) -> Dict[str, int]:
        """Cuenta ejecuciones por estado en un mes."""
        inicio_mes = datetime(anio, mes, 1, tzinfo=timezone.utc)
        if mes == 12:
            fin_mes = datetime(anio + 1, 1, 1, tzinfo=timezone.utc)
        else:
            fin_mes = datetime(anio, mes + 1, 1, tzinfo=timezone.utc)
        
        sql = f"""
            SELECT UltimaEjecucionStatus, COUNT(*) as count
            FROM {self.table_name}
            WHERE UltimaEjecucion >= %s AND UltimaEjecucion < %s
            GROUP BY UltimaEjecucionStatus
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (inicio_mes, fin_mes))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            result = {"COMPLETADA": 0, "FALLIDA": 0, "OMITIDA": 0, "EN_PROGRESO": 0}
            for row in rows:
                status = row.get("UltimaEjecucionStatus")
                if status in result:
                    result[status] = row["count"]
            return result
            
        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error contar_logs_mes: {e}")
            return {"COMPLETADA": 0, "FALLIDA": 0, "OMITIDA": 0, "EN_PROGRESO": 0}
    
    # =========================================================================
    # ÍNDICES (DEPRECATED - manejados por DDL)
    # =========================================================================
    
    def ensure_indexes(self):
        """DEPRECATED: Índices manejados por DDL de SQL Server."""
        pass
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _row_to_auditoria_dict(self, row: Dict) -> Optional[Dict]:
        """Convierte una fila SQL a formato compatible con la API."""
        if not row:
            return None
        
        return {
            "id": row.get("AuditoriaID"),
            "nombre": row.get("Nombre"),
            "descripcion": row.get("Descripcion"),
            "server_id": row.get("ServerID"),
            "sucursal_id": row.get("SucursalID"),
            "almacen_id": row.get("AlmacenID"),
            "frecuencia": row.get("Frecuencia"),
            "activo": bool(row.get("Activo")),
            "proxima_ejecucion": row.get("ProximaEjecucion").isoformat() if row.get("ProximaEjecucion") else None,
            "ultima_ejecucion": row.get("UltimaEjecucion").isoformat() if row.get("UltimaEjecucion") else None,
            "ultima_ejecucion_status": row.get("UltimaEjecucionStatus"),
        }
