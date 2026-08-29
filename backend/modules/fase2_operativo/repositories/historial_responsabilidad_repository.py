from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Repositorio para responsabilidad_historial - VERSIÓN SQL
CAB-003 | EDARSA HUB - Fase 2C.2

FASE B-P1-E: Migrado a EDARSAHUB SQL Server
- CERO MongoDB productivo
- SQL explícito contra Operativo_HistorialCargos
"""
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid
import json
import logging

from .sql_base_repository import SQLBaseRepository

logger = logging.getLogger(__name__)


class HistorialResponsabilidadRepository(SQLBaseRepository):
    """
    Repository para la tabla Operativo_HistorialCargos.
    Gestiona el historial de transiciones de responsabilidad económica.
    Migrado de MongoDB a SQL Server EDARSAHUB.
    """
    
    def __init__(self, db=None):
        """
        Inicializa el repository SQL.
        Args:
            db: IGNORADO - Solo para compatibilidad. Todo va a SQL.
        """
        super().__init__("responsabilidad_historial")
        logger.info(f"[HISTORIAL_RESP_REPO] Inicializado con SQL → {self.table_name}")
    
    def _crear_indices(self):
        """DEPRECATED: Índices manejados por DDL de SQL Server."""
        pass
    
    async def registrar_transicion(
        self,
        transicion_id: str,
        responsabilidad_id: str,
        accion: str,
        estado_anterior: str,
        estado_nuevo: str,
        usuario_id: str,
        usuario_rol: Optional[str],
        comentario: str,
        monto_al_momento: float,
        motivo_codigo: Optional[str] = None
    ) -> Dict:
        """
        Registra una transición de estado en el historial.
        """
        now = datetime.now(timezone.utc)
        historial_id = transicion_id or str(uuid.uuid4()).upper()
        
        # Construir detalle JSON
        detalle_info = {
            "responsabilidad_id": responsabilidad_id,
            "monto_al_momento": monto_al_momento,
            "motivo_codigo": motivo_codigo,
            "comentario": comentario,
        }
        detalle_str = json.dumps(detalle_info, ensure_ascii=False)
        
        sql = f"""
            INSERT INTO {self.table_name} 
            (HistorialID, CargoID, Accion, UsuarioID, UsuarioNombre, Detalle, EstadoAnterior, EstadoNuevo, Fecha)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            historial_id,
            responsabilidad_id,  # Usamos CargoID para ResponsabilidadID
            accion,
            usuario_id,
            usuario_rol or "",
            detalle_str,
            estado_anterior,
            estado_nuevo,
            now,
        )
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"[HISTORIAL_RESP_REPO] Transición registrada: {accion} sobre {responsabilidad_id}")
            
            return {
                "id": historial_id,
                "responsabilidad_id": responsabilidad_id,
                "accion": accion,
                "estado_anterior": estado_anterior,
                "estado_nuevo": estado_nuevo,
                "usuario_id": usuario_id,
                "usuario_rol": usuario_rol,
                "comentario": comentario,
                "motivo_codigo": motivo_codigo,
                "monto_al_momento": monto_al_momento,
                "fecha": now.isoformat(),
            }
            
        except Exception as e:
            logger.error(f"[HISTORIAL_RESP_REPO] Error registrar_transicion: {e}")
            raise
    
    async def get_by_responsabilidad(
        self,
        responsabilidad_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Obtiene el historial de transiciones de una responsabilidad.
        """
        sql = f"""
            SELECT TOP {limit} * FROM {self.table_name}
            WHERE CargoID = %s
            ORDER BY Fecha DESC
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (responsabilidad_id,))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [self._row_to_historial_dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"[HISTORIAL_RESP_REPO] Error get_by_responsabilidad: {e}")
            return []
    
    async def get_ultima_transicion(self, responsabilidad_id: str) -> Optional[Dict]:
        """
        Obtiene la última transición de una responsabilidad.
        """
        sql = f"""
            SELECT TOP 1 * FROM {self.table_name}
            WHERE CargoID = %s
            ORDER BY Fecha DESC
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (responsabilidad_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return self._row_to_historial_dict(row) if row else None
            
        except Exception as e:
            logger.error(f"[HISTORIAL_RESP_REPO] Error get_ultima_transicion: {e}")
            return None
    
    async def contar_transiciones(self, responsabilidad_id: str) -> int:
        """Cuenta las transiciones de una responsabilidad."""
        return self.count_documents({"cargo_id": responsabilidad_id})
    
    async def get_transiciones_por_usuario(
        self,
        usuario_id: str,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Obtiene transiciones realizadas por un usuario.
        """
        conditions = ["UsuarioID = %s"]
        params = [usuario_id]
        
        if fecha_desde:
            conditions.append("Fecha >= %s")
            params.append(fecha_desde)
        if fecha_hasta:
            conditions.append("Fecha <= %s")
            params.append(fecha_hasta)
        
        where_clause = " AND ".join(conditions)
        
        sql = f"""
            SELECT TOP {limit} * FROM {self.table_name}
            WHERE {where_clause}
            ORDER BY Fecha DESC
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [self._row_to_historial_dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"[HISTORIAL_RESP_REPO] Error get_transiciones_por_usuario: {e}")
            return []
    
    async def get_estadisticas_acciones(self) -> Dict:
        """
        Obtiene estadísticas de acciones realizadas.
        """
        sql = f"""
            SELECT Accion, COUNT(*) as count
            FROM {self.table_name}
            WHERE Accion IS NOT NULL
            GROUP BY Accion
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return {row["Accion"]: row["count"] for row in rows if row["Accion"]}
            
        except Exception as e:
            logger.error(f"[HISTORIAL_RESP_REPO] Error get_estadisticas_acciones: {e}")
            return {}
    
    def _row_to_historial_dict(self, row: Dict) -> Optional[Dict]:
        """
        Convierte una fila SQL a formato compatible con la API.
        """
        if not row:
            return None
        
        # Parsear detalle JSON
        detalle = row.get("Detalle", "{}")
        try:
            detalle_dict = json.loads(detalle) if detalle else {}
        except Exception:
            detalle_dict = {"raw": detalle}
        
        return {
            "id": row.get("HistorialID"),
            "responsabilidad_id": detalle_dict.get("responsabilidad_id") or row.get("CargoID"),
            "accion": row.get("Accion"),
            "estado_anterior": row.get("EstadoAnterior"),
            "estado_nuevo": row.get("EstadoNuevo"),
            "usuario_id": row.get("UsuarioID"),
            "usuario_rol": row.get("UsuarioNombre"),
            "comentario": detalle_dict.get("comentario", ""),
            "motivo_codigo": detalle_dict.get("motivo_codigo"),
            "monto_al_momento": detalle_dict.get("monto_al_momento", 0),
            "fecha": row.get("Fecha").isoformat() if row.get("Fecha") else None,
        }
    
    # Métodos de compatibilidad
    def _serialize_id(self, doc: Optional[Dict]) -> Optional[Dict]:
        """Compatibilidad - No necesario en SQL."""
        return doc
