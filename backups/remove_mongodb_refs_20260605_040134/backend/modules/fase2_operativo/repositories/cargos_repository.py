"""
Repository para Cargos Económicos - VERSIÓN SQL EXPLÍCITO
CAB-003 | EDARSA HUB - Fase 2C.3

FASE B-P1-D: Migración completa a EDARSAHUB SQL Server
- CERO MongoDB productivo
- CERO conexiones LIVE
- SQL explícito contra tablas:
  - Operativo_CargosResponsabilidad
  - Operativo_HistorialCargos
"""
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid
import logging

from .sql_base_repository import SQLBaseRepository

logger = logging.getLogger(__name__)


class CargosEconomicosRepository(SQLBaseRepository):
    """
    Repository para la tabla Operativo_CargosResponsabilidad.
    Reemplaza acceso MongoDB por SQL Server EDARSAHUB.
    """
    
    def __init__(self, db=None):
        """
        Inicializa el repository SQL.
        
        Args:
            db: IGNORADO - Solo para compatibilidad. Todo va a SQL.
        """
        super().__init__("cargos_economicos")
        logger.info(f"[CARGOS_REPO] Inicializado con SQL → {self.table_name}")
    
    def _ensure_indexes(self):
        """
        DEPRECATED: Índices manejados por DDL de SQL Server.
        Método vacío para compatibilidad.
        """
        pass
    
    async def crear_cargo(self, datos: Dict) -> str:
        """
        Crea un nuevo registro de cargo económico en SQL.
        
        Args:
            datos: Dict con los datos del cargo
            
        Returns:
            ID del cargo creado (CargoID)
        """
        now = datetime.now(timezone.utc)
        cargo_id = datos.get("id") or str(uuid.uuid4()).upper()
        
        # Mapeo de datos MongoDB → SQL
        sql_data = {
            "CargoID": cargo_id,
            "ResponsabilidadID": datos.get("responsabilidad_id", ""),
            "WorkflowID": datos.get("workflow_id", ""),
            "SucursalID": datos.get("sucursal_id", ""),
            "ResponsableID": datos.get("responsable_id", ""),
            "ResponsableNombre": datos.get("responsable_nombre", ""),
            "MontoPropuesto": datos.get("monto_responsabilidad", 0.0),
            "MontoFinal": datos.get("monto_aplicado", 0.0),
            "EstatusCargo": datos.get("estatus_cargo", "PENDIENTE"),
            "FechaPropuesta": datos.get("fecha_propuesta", now),
            "FechaAprobacion": datos.get("fecha_autorizacion"),
            "AprobadoPorID": datos.get("autorizado_por", ""),
            "Comentarios": datos.get("comentarios", ""),
        }
        
        # Construir INSERT
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
            
            logger.info(f"[CARGOS_REPO] Cargo creado: {cargo_id} para responsabilidad {datos.get('responsabilidad_id')}")
            return cargo_id
            
        except Exception as e:
            logger.error(f"[CARGOS_REPO] Error crear_cargo: {e}")
            raise
    
    async def get_by_id(self, cargo_id: str) -> Optional[Dict]:
        """Obtiene un cargo por su CargoID."""
        sql = f"SELECT * FROM {self.table_name} WHERE CargoID = %s"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (cargo_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return self._row_to_cargo_dict(row) if row else None
            
        except Exception as e:
            logger.error(f"[CARGOS_REPO] Error get_by_id: {e}")
            raise
    
    async def get_by_responsabilidad(self, responsabilidad_id: str) -> Optional[Dict]:
        """
        Obtiene el cargo asociado a una responsabilidad.
        Retorna el más reciente si hay varios.
        """
        sql = f"""
            SELECT TOP 1 * FROM {self.table_name}
            WHERE ResponsabilidadID = %s
            ORDER BY FechaPropuesta DESC
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (responsabilidad_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return self._row_to_cargo_dict(row) if row else None
            
        except Exception as e:
            logger.error(f"[CARGOS_REPO] Error get_by_responsabilidad: {e}")
            raise
    
    async def get_cargo_activo_por_responsabilidad(self, responsabilidad_id: str) -> Optional[Dict]:
        """
        Obtiene un cargo activo (no terminal) para una responsabilidad.
        Estados activos: PENDIENTE, AUTORIZADO, APLICADO
        """
        sql = f"""
            SELECT TOP 1 * FROM {self.table_name}
            WHERE ResponsabilidadID = %s
              AND EstatusCargo IN ('PENDIENTE', 'AUTORIZADO', 'APLICADO')
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (responsabilidad_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return self._row_to_cargo_dict(row) if row else None
            
        except Exception as e:
            logger.error(f"[CARGOS_REPO] Error get_cargo_activo_por_responsabilidad: {e}")
            raise
    
    async def actualizar_cargo(self, cargo_id: str, datos: Dict) -> Optional[Dict]:
        """Actualiza un cargo existente."""
        # Mapear campos MongoDB → SQL
        sql_updates = []
        params = []
        
        field_mapping = {
            "estatus_cargo": "EstatusCargo",
            "monto_aplicado": "MontoFinal",
            "monto_responsabilidad": "MontoPropuesto",
            "fecha_autorizacion": "FechaAprobacion",
            "autorizado_por": "AprobadoPorID",
            "fecha_aplicacion": "FechaAprobacion",  # Alias
            "aplicado_por": "AprobadoPorID",  # Alias
            "fecha_reversa": "FechaRechazo",
            "revertido_por": "RechazadoPorID",
            "comentarios": "Comentarios",
            "motivo_rechazo": "MotivoRechazo",
            "fecha_rechazo": "FechaRechazo",
            "rechazado_por_id": "RechazadoPorID",
            "fecha_disputa": "FechaDisputa",
            "disputado_por_id": "DisputadoPorID",
            "motivo_disputa": "MotivoDisputa",
            "fecha_resolucion": "FechaResolucion",
            "resuelto_por_id": "ResueltoPorID",
        }
        
        for key, value in datos.items():
            if key in field_mapping:
                sql_updates.append(f"{field_mapping[key]} = %s")
                params.append(value)
            elif key == "fecha_actualizacion":
                # Ignorar - SQL no tiene este campo
                continue
        
        if not sql_updates:
            return await self.get_by_id(cargo_id)
        
        params.append(cargo_id)
        sql = f"UPDATE {self.table_name} SET {', '.join(sql_updates)} WHERE CargoID = %s"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            cursor.close()
            conn.close()
            
            return await self.get_by_id(cargo_id)
            
        except Exception as e:
            logger.error(f"[CARGOS_REPO] Error actualizar_cargo: {e}")
            raise
    
    async def listar_con_filtros(
        self,
        estatus: Optional[str] = None,
        sucursal_id: Optional[str] = None,
        responsable_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict:
        """Lista cargos con filtros opcionales."""
        conditions = []
        params = []
        
        if estatus:
            conditions.append("EstatusCargo = %s")
            params.append(estatus)
        if sucursal_id:
            conditions.append("SucursalID = %s")
            params.append(sucursal_id)
        if responsable_id:
            conditions.append("ResponsableID = %s")
            params.append(responsable_id)
        if workflow_id:
            conditions.append("WorkflowID = %s")
            params.append(workflow_id)
        if fecha_desde:
            conditions.append("FechaPropuesta >= %s")
            params.append(fecha_desde)
        if fecha_hasta:
            conditions.append("FechaPropuesta <= %s")
            params.append(fecha_hasta)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Count query
        count_sql = f"SELECT COUNT(*) as total FROM {self.table_name} WHERE {where_clause}"
        
        # Data query con paginación
        data_sql = f"""
            SELECT * FROM {self.table_name}
            WHERE {where_clause}
            ORDER BY FechaPropuesta DESC
            OFFSET {skip} ROWS FETCH NEXT {limit} ROWS ONLY
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Obtener total
            cursor.execute(count_sql, params)
            total = cursor.fetchone()["total"]
            
            # Obtener datos
            cursor.execute(data_sql, params)
            rows = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            items = [self._row_to_cargo_dict(row) for row in rows]
            return {"total": total, "items": items}
            
        except Exception as e:
            logger.error(f"[CARGOS_REPO] Error listar_con_filtros: {e}")
            raise
    
    async def contar_por_estatus(self) -> Dict[str, int]:
        """Cuenta cargos agrupados por estatus."""
        sql = f"""
            SELECT EstatusCargo, COUNT(*) as count
            FROM {self.table_name}
            WHERE EstatusCargo IS NOT NULL
            GROUP BY EstatusCargo
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return {row["EstatusCargo"]: row["count"] for row in rows if row["EstatusCargo"]}
            
        except Exception as e:
            logger.error(f"[CARGOS_REPO] Error contar_por_estatus: {e}")
            return {}
    
    async def obtener_metricas(self) -> Dict:
        """Obtiene métricas agregadas de cargos."""
        sql = f"""
            SELECT 
                COUNT(*) as total_cargos,
                ISNULL(SUM(MontoPropuesto), 0) as monto_total_propuesto,
                ISNULL(SUM(MontoFinal), 0) as monto_total_aplicado,
                ISNULL(SUM(CASE WHEN EstatusCargo = 'REVERTIDO' THEN MontoFinal ELSE 0 END), 0) as monto_total_revertido
            FROM {self.table_name}
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if row:
                return {
                    "total_cargos": row["total_cargos"] or 0,
                    "monto_total_propuesto": float(row["monto_total_propuesto"] or 0),
                    "monto_total_aplicado": float(row["monto_total_aplicado"] or 0),
                    "monto_total_revertido": float(row["monto_total_revertido"] or 0),
                }
            return {
                "total_cargos": 0,
                "monto_total_propuesto": 0,
                "monto_total_aplicado": 0,
                "monto_total_revertido": 0,
            }
            
        except Exception as e:
            logger.error(f"[CARGOS_REPO] Error obtener_metricas: {e}")
            return {
                "total_cargos": 0,
                "monto_total_propuesto": 0,
                "monto_total_aplicado": 0,
                "monto_total_revertido": 0,
            }
    
    async def obtener_monto_autorizado_total(self) -> float:
        """Suma de montos de cargos en estado AUTORIZADO."""
        sql = f"""
            SELECT ISNULL(SUM(MontoPropuesto), 0) as total
            FROM {self.table_name}
            WHERE EstatusCargo = 'AUTORIZADO'
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return float(row["total"]) if row else 0.0
            
        except Exception as e:
            logger.error(f"[CARGOS_REPO] Error obtener_monto_autorizado_total: {e}")
            return 0.0
    
    def _row_to_cargo_dict(self, row: Dict) -> Optional[Dict]:
        """
        Convierte una fila SQL a formato compatible con la API.
        Mapea campos SQL → formato MongoDB/API legacy.
        """
        if not row:
            return None
        
        return {
            "id": row.get("CargoID"),
            "responsabilidad_id": row.get("ResponsabilidadID"),
            "workflow_id": row.get("WorkflowID"),
            "sucursal_id": row.get("SucursalID"),
            "responsable_id": row.get("ResponsableID"),
            "responsable_nombre": row.get("ResponsableNombre"),
            "monto_responsabilidad": float(row.get("MontoPropuesto") or 0),
            "monto_aplicado": float(row.get("MontoFinal") or 0),
            "monto_revertido": 0.0,  # Calculado por lógica de negocio
            "estatus_cargo": row.get("EstatusCargo"),
            "origen": "RESPONSABILIDAD_ECONOMICA",
            "fecha_propuesta": row.get("FechaPropuesta").isoformat() if row.get("FechaPropuesta") else None,
            "fecha_autorizacion": row.get("FechaAprobacion").isoformat() if row.get("FechaAprobacion") else None,
            "fecha_aplicacion": row.get("FechaAprobacion").isoformat() if row.get("FechaAprobacion") else None,
            "fecha_reversa": row.get("FechaRechazo").isoformat() if row.get("FechaRechazo") else None,
            "propuesto_por": None,  # No existe en SQL
            "autorizado_por": row.get("AprobadoPorID"),
            "aplicado_por": row.get("AprobadoPorID"),
            "revertido_por": row.get("RechazadoPorID"),
            "comentarios": row.get("Comentarios"),
            "motivo_rechazo": row.get("MotivoRechazo"),
            "fecha_creacion": row.get("FechaPropuesta").isoformat() if row.get("FechaPropuesta") else None,
            "fecha_actualizacion": row.get("FechaPropuesta").isoformat() if row.get("FechaPropuesta") else None,
        }
    
    # Métodos de compatibilidad para código legacy
    def _serialize_id(self, doc: Optional[Dict]) -> Optional[Dict]:
        """Compatibilidad - No necesario en SQL."""
        return doc


class CargosLogRepository(SQLBaseRepository):
    """
    Repository para la tabla Operativo_HistorialCargos (auditoría).
    Reemplaza acceso MongoDB por SQL Server EDARSAHUB.
    """
    
    def __init__(self, db=None):
        """
        Inicializa el repository SQL.
        
        Args:
            db: IGNORADO - Solo para compatibilidad. Todo va a SQL.
        """
        super().__init__("cargos_economicos_log")
        logger.info(f"[CARGOS_LOG_REPO] Inicializado con SQL → {self.table_name}")
    
    def _ensure_indexes(self):
        """
        DEPRECATED: Índices manejados por DDL de SQL Server.
        Método vacío para compatibilidad.
        """
        pass
    
    async def registrar_log(
        self,
        cargo_id: str,
        accion: str,
        estatus_anterior: str,
        estatus_nuevo: str,
        usuario_id: str,
        comentario: str,
        monto_al_momento: float,
        usuario_rol: Optional[str] = None,
        motivo_codigo: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Registra una entrada en el log de auditoría.
        
        Returns:
            ID del registro de log (HistorialID)
        """
        log_id = str(uuid.uuid4()).upper()
        now = datetime.now(timezone.utc)
        
        # Construir detalle JSON con info adicional
        detalle_info = {
            "monto_al_momento": monto_al_momento,
            "usuario_rol": usuario_rol,
            "motivo_codigo": motivo_codigo,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "comentario": comentario,
        }
        import json
        detalle_str = json.dumps(detalle_info, ensure_ascii=False)
        
        sql = f"""
            INSERT INTO {self.table_name} 
            (HistorialID, CargoID, Accion, UsuarioID, UsuarioNombre, Detalle, EstadoAnterior, EstadoNuevo, Fecha)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            log_id,
            cargo_id,
            accion,
            usuario_id,
            usuario_rol or "",
            detalle_str,
            estatus_anterior,
            estatus_nuevo,
            now,
        )
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"[CARGOS_LOG_REPO] Log registrado: {accion} sobre cargo {cargo_id}")
            return log_id
            
        except Exception as e:
            logger.error(f"[CARGOS_LOG_REPO] Error registrar_log: {e}")
            raise
    
    async def get_by_cargo(self, cargo_id: str, limit: int = 100) -> List[Dict]:
        """Obtiene el historial de logs de un cargo."""
        sql = f"""
            SELECT TOP {limit} * FROM {self.table_name}
            WHERE CargoID = %s
            ORDER BY Fecha DESC
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (cargo_id,))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [self._row_to_log_dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"[CARGOS_LOG_REPO] Error get_by_cargo: {e}")
            return []
    
    async def get_ultimos_logs(self, limit: int = 50) -> List[Dict]:
        """Obtiene los últimos logs del sistema."""
        sql = f"""
            SELECT TOP {limit} * FROM {self.table_name}
            ORDER BY Fecha DESC
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [self._row_to_log_dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"[CARGOS_LOG_REPO] Error get_ultimos_logs: {e}")
            return []
    
    async def contar_acciones_por_usuario(self, usuario_id: str) -> Dict[str, int]:
        """Cuenta las acciones realizadas por un usuario."""
        sql = f"""
            SELECT Accion, COUNT(*) as count
            FROM {self.table_name}
            WHERE UsuarioID = %s
            GROUP BY Accion
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (usuario_id,))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return {row["Accion"]: row["count"] for row in rows if row["Accion"]}
            
        except Exception as e:
            logger.error(f"[CARGOS_LOG_REPO] Error contar_acciones_por_usuario: {e}")
            return {}
    
    def _row_to_log_dict(self, row: Dict) -> Optional[Dict]:
        """
        Convierte una fila SQL a formato compatible con la API.
        """
        if not row:
            return None
        
        # Parsear detalle JSON si existe
        detalle = row.get("Detalle", "{}")
        import json
        try:
            detalle_dict = json.loads(detalle) if detalle else {}
        except:
            detalle_dict = {"raw": detalle}
        
        return {
            "id": row.get("HistorialID"),
            "cargo_id": row.get("CargoID"),
            "accion": row.get("Accion"),
            "estatus_anterior": row.get("EstadoAnterior"),
            "estatus_nuevo": row.get("EstadoNuevo"),
            "usuario_id": row.get("UsuarioID"),
            "usuario_rol": row.get("UsuarioNombre"),
            "comentario": detalle_dict.get("comentario", ""),
            "motivo_codigo": detalle_dict.get("motivo_codigo"),
            "monto_al_momento": detalle_dict.get("monto_al_momento", 0),
            "fecha": row.get("Fecha").isoformat() if row.get("Fecha") else None,
            "ip_address": detalle_dict.get("ip_address"),
            "user_agent": detalle_dict.get("user_agent"),
        }
    
    # Métodos de compatibilidad para código legacy
    def _serialize_id(self, doc: Optional[Dict]) -> Optional[Dict]:
        """Compatibilidad - No necesario en SQL."""
        return doc
