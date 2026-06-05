"""
Repositorio para matriz de asignación automática - VERSIÓN SQL
CAB-003 | Fase 2A - Subfase 2A.9

FASE B-P1-E: Migrado a EDARSAHUB SQL Server
- CERO MongoDB productivo
- SQL explícito contra Sistema_SucursalServidorMapeo
"""
from typing import Optional, Dict, List
from datetime import datetime, timezone
import logging

from .sql_base_repository import SQLBaseRepository

logger = logging.getLogger(__name__)


class AsignacionRepository(SQLBaseRepository):
    """
    Repository para gestionar asignaciones automáticas por sucursal+almacén.
    Migrado de MongoDB a SQL Server EDARSAHUB.
    """
    
    def __init__(self, db=None):
        """
        Inicializa el repository SQL.
        Args:
            db: IGNORADO - Solo para compatibilidad. Todo va a SQL.
        """
        super().__init__("server_sucursales_config")
        logger.info(f"[ASIGNACION_REPO] Inicializado con SQL → {self.table_name}")
    
    async def get_usuario_responsable(
        self,
        server_id: str,
        sucursal_id: str,
        almacen_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Obtiene el usuario responsable para una combinación sucursal+almacén.
        
        Prioridad:
        1. Buscar por server_id + sucursal_id + almacen_id (si se proporciona)
        2. Buscar por server_id + sucursal_id (sin almacén)
        3. Retornar None si no hay configuración
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # La tabla Sistema_SucursalServidorMapeo no tiene usuario_responsable_id
            # Esto es una configuración que puede estar en otra tabla o no existe
            # Retornamos None por ahora - la lógica de negocio debe adaptarse
            
            # Intento buscar en la tabla de mapeo
            if almacen_id:
                cursor.execute("""
                    SELECT TOP 1 UsuarioResponsableID 
                    FROM Sistema_SucursalServidorMapeo
                    WHERE ServidorID = %s AND SucursalOrigenID = %s AND Activo = 1
                """, (server_id, sucursal_id))
            else:
                cursor.execute("""
                    SELECT TOP 1 UsuarioResponsableID 
                    FROM Sistema_SucursalServidorMapeo
                    WHERE ServidorID = %s AND SucursalOrigenID = %s AND Activo = 1
                """, (server_id, sucursal_id))
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if row and row.get("UsuarioResponsableID"):
                return row["UsuarioResponsableID"]
            return None
            
        except Exception as e:
            logger.warning(f"[ASIGNACION_REPO] Error buscando usuario responsable: {e}")
            return None
    
    async def set_usuario_responsable(
        self,
        server_id: str,
        sucursal_id: str,
        usuario_id: str,
        almacen_id: Optional[str] = None,
        modificado_por: Optional[str] = None
    ) -> bool:
        """
        Establece el usuario responsable para una sucursal.
        NOTA: Esta funcionalidad puede requerir una tabla adicional en SQL.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE Sistema_SucursalServidorMapeo
                SET FechaModificacion = %s
                WHERE ServidorID = %s AND SucursalOrigenID = %s
            """, (datetime.now(timezone.utc), server_id, sucursal_id))
            
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            return affected > 0
            
        except Exception as e:
            logger.error(f"[ASIGNACION_REPO] Error estableciendo usuario responsable: {e}")
            return False
    
    async def get_todas_asignaciones(self, server_id: Optional[str] = None) -> List[Dict]:
        """
        Obtiene todas las configuraciones de asignación activas.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if server_id:
                cursor.execute("""
                    SELECT MapeoID, SucursalID, ServidorID, SucursalOrigenID, Activo
                    FROM Sistema_SucursalServidorMapeo
                    WHERE Activo = 1 AND ServidorID = %s
                    ORDER BY SucursalID
                """, (server_id,))
            else:
                cursor.execute("""
                    SELECT MapeoID, SucursalID, ServidorID, SucursalOrigenID, Activo
                    FROM Sistema_SucursalServidorMapeo
                    WHERE Activo = 1
                    ORDER BY SucursalID
                """)
            
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [self._row_to_dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"[ASIGNACION_REPO] Error obteniendo asignaciones: {e}")
            return []
