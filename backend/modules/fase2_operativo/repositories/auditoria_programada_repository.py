from core.unidades_service import UnidadesService
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
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
import uuid
import json
import logging

from .sql_base_repository import SQLBaseRepository

logger = logging.getLogger(__name__)



def _clean(value: Any) -> str:
    return str(value or "").strip()


def _key(value: Any) -> str:
    return _clean(value).casefold()


def _unique(values: List[str]) -> List[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = _clean(value)
        marker = cleaned.casefold()
        if cleaned and marker not in seen:
            result.append(cleaned)
            seen.add(marker)
    return result


def _unit_pk(unit: Dict[str, Any]) -> str:
    return _clean(unit.get("unidad_negocio_pk") or unit.get("id"))


def _unit_identifiers(unit: Dict[str, Any]) -> List[str]:
    return _unique([
        _unit_pk(unit),
        unit.get("codigo"),
        unit.get("unidad_negocio_codigo"),
        unit.get("nombre"),
        unit.get("unidad_negocio_nombre"),
        unit.get("sucursal_origen_id"),
    ])


def _active_units_by_server() -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for unit in UnidadesService.get_all():
        server_id = _key(unit.get("server_id"))
        if server_id:
            counts[server_id] = counts.get(server_id, 0) + 1
    return counts


def _find_unit(unidad_pk: str) -> Optional[Dict[str, Any]]:
    target = _key(unidad_pk)
    for unit in UnidadesService.get_all():
        if _key(_unit_pk(unit)) == target:
            return unit
    return None


def _resolve_unit_from_row(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    row_server = _key(row.get("ServerID"))
    row_branch = _key(row.get("SucursalID"))
    counts = _active_units_by_server()

    for unit in UnidadesService.get_all():
        server_id = _key(unit.get("server_id"))
        branch = _key(unit.get("sucursal_origen_id"))
        identifiers = {_key(value) for value in _unit_identifiers(unit)}

        if row_server and server_id == row_server:
            if branch and row_branch == branch:
                return unit
            if not branch and counts.get(server_id, 0) == 1:
                return unit
        if row_branch and row_branch in identifiers:
            return unit

    return None


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

    def _scope_where(
        self,
        unidad_negocio_pks: Optional[List[str]] = None,
    ) -> Tuple[str, List[Any]]:
        if unidad_negocio_pks is None:
            return "", []

        pks = _unique([_clean(pk) for pk in unidad_negocio_pks])
        if not pks:
            return " AND 1 = 0", []

        counts = _active_units_by_server()
        or_parts: list[str] = []
        params: list[Any] = []

        for pk in pks:
            unit = _find_unit(pk)
            if not unit:
                continue

            server_id = _clean(unit.get("server_id"))
            branch = _clean(unit.get("sucursal_origen_id"))
            identifiers = _unit_identifiers(unit)

            if server_id and branch and identifiers:
                placeholders = ", ".join(["%s"] * len(identifiers))
                or_parts.append(
                    f"(ServerID = %s AND SucursalID IN ({placeholders}))"
                )
                params.append(server_id)
                params.extend(identifiers)
                or_parts.append(
                    "((ServerID IS NULL OR LTRIM(RTRIM(ServerID)) = '') "
                    f"AND SucursalID IN ({placeholders}))"
                )
                params.extend(identifiers)
                continue

            if server_id and counts.get(_key(server_id), 0) == 1:
                or_parts.append("ServerID = %s")
                params.append(server_id)
                continue

            if identifiers:
                placeholders = ", ".join(["%s"] * len(identifiers))
                or_parts.append(f"SucursalID IN ({placeholders})")
                params.extend(identifiers)

        if not or_parts:
            return " AND 1 = 0", []

        return f" AND ({' OR '.join(or_parts)})", params
    
    # =========================================================================
    # CRUD AUDITORÍAS PROGRAMADAS (sync por compatibilidad)
    # =========================================================================
    
    def create(self, data: Dict) -> Dict:
        """Crea una auditoria programada en SQL Server."""
        now = datetime.now(timezone.utc)
        data["fecha_creacion"] = now
        data["fecha_ultima_actualizacion"] = now

        auditoria_id = data.get("id") or str(uuid.uuid4()).upper()
        config = {
            "unidad_negocio_pk": data.get("unidad_negocio_pk"),
            "unidad_negocio_codigo": data.get("unidad_negocio_codigo"),
            "unidad_negocio_nombre": data.get("unidad_negocio_nombre"),
            "sucursal_nombre": data.get("sucursal_nombre"),
            "tipo_auditoria": data.get("tipo_auditoria"),
            "almacenes": data.get("almacenes", []),
            "usuario_responsable_id": data.get("usuario_responsable_id"),
            "rol_responsable": data.get("rol_responsable"),
            "observaciones": data.get("observaciones"),
            "created_by": data.get("created_by"),
        }

        sql_data = {
            "AuditoriaID": auditoria_id,
            "Nombre": data.get("nombre", ""),
            "Descripcion": data.get("descripcion", ""),
            "ServerID": data.get("server_id", ""),
            "SucursalID": data.get("sucursal_id", ""),
            "AlmacenID": data.get("almacen_id", ""),
            "Frecuencia": data.get("frecuencia", "MENSUAL"),
            "DiaSemana": data.get("dia_semana"),
            "DiaMes": data.get("dia_mes"),
            "HoraEjecucion": data.get("hora_ejecucion"),
            "Timezone": data.get("timezone"),
            "Estado": "ACTIVA" if data.get("activo", True) else "INACTIVA",
            "ProximaEjecucion": data.get("proxima_ejecucion"),
            "UltimaEjecucion": data.get("ultima_ejecucion"),
            "UsuarioCreadorID": data.get("created_by"),
            "FechaCreacion": now,
            "FechaActualizacion": now,
            "ConfiguracionJSON": json.dumps(config, ensure_ascii=False),
        }

        existing = {col.upper() for col in self._get_table_columns()}
        if existing:
            sql_data = {k: v for k, v in sql_data.items() if k.upper() in existing}

        columns = ", ".join(sql_data.keys())
        placeholders = ", ".join(["%s"] * len(sql_data))
        sql = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"

        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            cursor.execute(sql, list(sql_data.values()))
            conn.commit()
            cursor.close()
            conn.close()

            data["id"] = auditoria_id
            return data

        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error create: {e}")
            raise

    def get_by_id(
        self,
        id: str,
        unidad_negocio_pks: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        """Obtiene por ID usando campo AuditoriaID y alcance canonico."""
        scope_where, scope_params = self._scope_where(unidad_negocio_pks)
        sql = f"SELECT * FROM {self.table_name} WHERE AuditoriaID = %s{scope_where}"
        params = [id, *scope_params]

        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            cursor.execute(sql, params)
            row = cursor.fetchone()
            cursor.close()
            conn.close()

            return self._row_to_auditoria_dict(row) if row else None

        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error get_by_id: {e}")
            return None

    def get_all(
        self,
        unidad_negocio_pks: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Obtiene auditorias respetando alcance por unidad."""
        scope_where, scope_params = self._scope_where(unidad_negocio_pks)
        sql = f"SELECT * FROM {self.table_name} WHERE 1 = 1{scope_where} ORDER BY Nombre"

        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            cursor.execute(sql, scope_params)
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
            "dia_semana": "DiaSemana",
            "dia_mes": "DiaMes",
            "hora_ejecucion": "HoraEjecucion",
            "timezone": "Timezone",
            "activo": "Estado",
            "proxima_ejecucion": "ProximaEjecucion",
            "ultima_ejecucion": "UltimaEjecucion",
            "fecha_creacion": "FechaCreacion",
            "fecha_ultima_actualizacion": "FechaActualizacion",
            "updated_at": "FechaActualizacion",
            "created_by": "UsuarioCreadorID",
        }

        existing = {col.upper() for col in self._get_table_columns()}
        for key, value in data.items():
            if key in field_mapping and field_mapping[key].upper() in existing:
                if key == "activo":
                    value = "ACTIVA" if value else "INACTIVA"
                set_parts.append(f"{field_mapping[key]} = %s")
                params.append(value)

        config_keys = {
            "unidad_negocio_pk",
            "unidad_negocio_codigo",
            "unidad_negocio_nombre",
            "sucursal_nombre",
            "tipo_auditoria",
            "almacenes",
            "usuario_responsable_id",
            "rol_responsable",
            "observaciones",
            "created_by",
        }
        if "CONFIGURACIONJSON" in existing and any(k in data for k in config_keys):
            current = self.get_by_id(id) or {}
            config = {key: current.get(key) for key in config_keys}
            config.update({key: data.get(key) for key in config_keys if key in data})
            set_parts.append("ConfiguracionJSON = %s")
            params.append(json.dumps(config, ensure_ascii=False))

        if not set_parts:
            return self.get_by_id(id)
        
        params.append(id)
        sql = f"UPDATE {self.table_name} SET {', '.join(set_parts)} WHERE AuditoriaID = %s"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
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
            cursor = conn.cursor(as_dict=True)
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
    
    def get_activas(
        self,
        unidad_negocio_pks: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Obtiene auditorias activas respetando alcance."""
        scope_where, scope_params = self._scope_where(unidad_negocio_pks)
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE ISNULL(Estado, 'ACTIVA') = 'ACTIVA'{scope_where}
            ORDER BY ProximaEjecucion
        """

        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            cursor.execute(sql, scope_params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            return [self._row_to_auditoria_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error get_activas: {e}")
            return []

    def get_by_sucursal(
        self,
        sucursal_id: str,
        unidad_negocio_pks: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Obtiene auditorias por sucursal legacy, respetando alcance."""
        scope_where, scope_params = self._scope_where(unidad_negocio_pks)
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE SucursalID = %s{scope_where}
            ORDER BY Nombre
        """
        params = [sucursal_id, *scope_params]

        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            return [self._row_to_auditoria_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error get_by_sucursal: {e}")
            return []

    def get_by_unidad(self, unidad_negocio_pk: str) -> List[Dict]:
        """Obtiene auditorias de una unidad canonica."""
        return self.get_all([unidad_negocio_pk])

    def get_pendientes_ejecucion(
        self,
        hasta: datetime,
        unidad_negocio_pks: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Obtiene auditorias cuya proxima ejecucion es <= hasta."""
        scope_where, scope_params = self._scope_where(unidad_negocio_pks)
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE ISNULL(Estado, 'ACTIVA') = 'ACTIVA'
              AND ProximaEjecucion <= %s{scope_where}
        """
        params = [hasta, *scope_params]

        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            return [self._row_to_auditoria_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error get_pendientes_ejecucion: {e}")
            return []

    def get_proximas_24h(
        self,
        unidad_negocio_pks: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Obtiene auditorias programadas para las proximas 24 horas."""
        ahora = datetime.now(timezone.utc)
        en_24h = ahora + timedelta(hours=24)
        scope_where, scope_params = self._scope_where(unidad_negocio_pks)

        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE ISNULL(Estado, 'ACTIVA') = 'ACTIVA'
              AND ProximaEjecucion >= %s
              AND ProximaEjecucion <= %s{scope_where}
            ORDER BY ProximaEjecucion
        """
        params = [ahora, en_24h, *scope_params]

        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            cursor.execute(sql, params)
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
                SET UltimaEjecucion = %s, Estado = %s, ProximaEjecucion = %s, FechaActualizacion = SYSUTCDATETIME()
                WHERE AuditoriaID = %s
            """
            params = (now, estado, proxima, auditoria_id)
        else:
            sql = f"""
                UPDATE {self.table_name}
                SET UltimaEjecucion = %s, Estado = %s, FechaActualizacion = SYSUTCDATETIME()
                WHERE AuditoriaID = %s
            """
            params = (now, estado, auditoria_id)
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
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
        sql = f"UPDATE {self.table_name} SET Estado = 'ACTIVA', FechaActualizacion = SYSUTCDATETIME() WHERE AuditoriaID = %s"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
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
        sql = f"UPDATE {self.table_name} SET Estado = 'INACTIVA', FechaActualizacion = SYSUTCDATETIME() WHERE AuditoriaID = %s"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            cursor.execute(sql, (auditoria_id,))
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            return affected > 0
            
        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error desactivar: {e}")
            return False
    
    def contar_por_estado(
        self,
        unidad_negocio_pks: Optional[List[str]] = None,
    ) -> Dict[str, int]:
        """Cuenta auditorias por estado activo/inactivo y alcance."""
        scope_where, scope_params = self._scope_where(unidad_negocio_pks)
        sql = f"""
            SELECT ISNULL(Estado, 'ACTIVA') AS Estado, COUNT(*) as count
            FROM {self.table_name}
            WHERE 1 = 1{scope_where}
            GROUP BY ISNULL(Estado, 'ACTIVA')
        """

        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            cursor.execute(sql, scope_params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            result = {"activas": 0, "inactivas": 0}
            for row in rows:
                if str(row.get("Estado") or "").upper() == "ACTIVA":
                    result["activas"] = row["count"]
                else:
                    result["inactivas"] = row["count"]
            return result

        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error contar_por_estado: {e}")
            return {"activas": 0, "inactivas": 0}

    def get_calendario(
        self,
        anio: int,
        mes: int,
        unidad_negocio_pks: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Obtiene auditorias para un mes especifico."""
        inicio_mes = datetime(anio, mes, 1, tzinfo=timezone.utc)
        if mes == 12:
            fin_mes = datetime(anio + 1, 1, 1, tzinfo=timezone.utc)
        else:
            fin_mes = datetime(anio, mes + 1, 1, tzinfo=timezone.utc)

        scope_where, scope_params = self._scope_where(unidad_negocio_pks)
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE ISNULL(Estado, 'ACTIVA') = 'ACTIVA'
              AND ProximaEjecucion >= %s
              AND ProximaEjecucion < %s{scope_where}
            ORDER BY ProximaEjecucion
        """
        params = [inicio_mes, fin_mes, *scope_params]

        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            cursor.execute(sql, params)
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
        limit: int = 100,
        unidad_negocio_pks: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Obtiene logs de ejecucion con filtros y alcance."""
        conditions = []
        params = []

        if auditoria_id:
            conditions.append("AuditoriaID = %s")
            params.append(auditoria_id)
        if estado:
            conditions.append("Estado = %s")
            params.append(estado)
        if desde:
            conditions.append("UltimaEjecucion >= %s")
            params.append(desde)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        scope_where, scope_params = self._scope_where(unidad_negocio_pks)
        top_limit = max(1, min(int(limit or 100), 500))

        sql = f"""
            SELECT TOP {top_limit} * FROM {self.table_name}
            WHERE {where_clause}
              AND UltimaEjecucion IS NOT NULL{scope_where}
            ORDER BY UltimaEjecucion DESC
        """
        params = [*params, *scope_params]

        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            logs = []
            for row in rows:
                logs.append({
                    "id": row.get("AuditoriaID"),
                    "auditoria_programada_id": row.get("AuditoriaID"),
                    "nombre": row.get("Nombre"),
                    "estado": row.get("Estado"),
                    "disparado_por": row.get("UsuarioCreadorID") or "SCHEDULER",
                    "workflow_id": None,
                    "mensaje": row.get("Nombre"),
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
              AND Estado IN ('COMPLETADA', 'EN_PROGRESO')
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            cursor.execute(sql, (auditoria_id, inicio_ventana, fin_ventana))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return row["count"] > 0 if row else False
            
        except Exception as e:
            logger.error(f"[AUDITORIA_PROG_REPO] Error verificar_ejecucion_duplicada: {e}")
            return False
    
    def contar_logs_mes(
        self,
        anio: int,
        mes: int,
        unidad_negocio_pks: Optional[List[str]] = None,
    ) -> Dict[str, int]:
        """Cuenta ejecuciones por estado en un mes y alcance."""
        inicio_mes = datetime(anio, mes, 1, tzinfo=timezone.utc)
        if mes == 12:
            fin_mes = datetime(anio + 1, 1, 1, tzinfo=timezone.utc)
        else:
            fin_mes = datetime(anio, mes + 1, 1, tzinfo=timezone.utc)

        scope_where, scope_params = self._scope_where(unidad_negocio_pks)
        sql = f"""
            SELECT Estado, COUNT(*) as count
            FROM {self.table_name}
            WHERE UltimaEjecucion >= %s
              AND UltimaEjecucion < %s{scope_where}
            GROUP BY Estado
        """
        params = [inicio_mes, fin_mes, *scope_params]

        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            result = {"COMPLETADA": 0, "FALLIDA": 0, "OMITIDA": 0, "EN_PROGRESO": 0}
            for row in rows:
                status = row.get("Estado")
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

        config = {}
        raw_config = row.get("ConfiguracionJSON")
        if raw_config:
            try:
                config = json.loads(raw_config)
            except (TypeError, ValueError):
                config = {}

        unit = _resolve_unit_from_row(row) or {}
        unidad_pk = config.get("unidad_negocio_pk") or _unit_pk(unit) or None
        unidad_codigo = (
            config.get("unidad_negocio_codigo")
            or unit.get("codigo")
            or unit.get("unidad_negocio_codigo")
        )
        unidad_nombre = (
            config.get("unidad_negocio_nombre")
            or unit.get("nombre")
            or unit.get("unidad_negocio_nombre")
        )

        return {
            "id": row.get("AuditoriaID"),
            "nombre": row.get("Nombre"),
            "descripcion": row.get("Descripcion"),
            "unidad_negocio_pk": unidad_pk,
            "unidad_negocio_codigo": unidad_codigo,
            "unidad_negocio_nombre": unidad_nombre,
            "server_id": row.get("ServerID"),
            "sucursal_id": row.get("SucursalID"),
            "sucursal_nombre": config.get("sucursal_nombre") or unidad_nombre,
            "almacen_id": row.get("AlmacenID"),
            "almacenes": config.get("almacenes") or [],
            "tipo_auditoria": config.get("tipo_auditoria") or "INVENTARIO_COMPLETO",
            "frecuencia": row.get("Frecuencia"),
            "dia_semana": row.get("DiaSemana"),
            "dia_mes": row.get("DiaMes"),
            "hora_ejecucion": row.get("HoraEjecucion") or "08:00",
            "timezone": row.get("Timezone") or "America/Mexico_City",
            "activo": str(row.get("Estado") or "ACTIVA").upper() != "INACTIVA",
            "proxima_ejecucion": row.get("ProximaEjecucion").isoformat() if row.get("ProximaEjecucion") else None,
            "ultima_ejecucion": row.get("UltimaEjecucion").isoformat() if row.get("UltimaEjecucion") else None,
            "ultima_ejecucion_status": row.get("Estado"),
            "usuario_responsable_id": config.get("usuario_responsable_id"),
            "rol_responsable": config.get("rol_responsable"),
            "observaciones": config.get("observaciones"),
            "created_by": config.get("created_by") or row.get("UsuarioCreadorID"),
        }
