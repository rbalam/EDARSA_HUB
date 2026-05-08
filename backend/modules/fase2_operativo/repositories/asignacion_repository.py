"""
Repositorio para matriz de asignación automática.
CAB-003 | Fase 2A - Subfase 2A.9

Gestiona la relación sucursal + almacén → usuario responsable.
"""

from typing import Optional, Dict, List
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class AsignacionRepository:
    """Repository para gestionar asignaciones automáticas por sucursal+almacén."""
    
    def __init__(self, db):
        self.db = db
        self.collection = db.server_sucursales_config
    
    async def get_usuario_responsable(
        self,
        server_id: str,
        sucursal_id: str,
        almacen_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Obtiene el usuario responsable para una combinación sucursal+almacén.
        
        Prioridad de búsqueda:
        1. Buscar por server_id + sucursal_id + almacen_id (si se proporciona)
        2. Buscar por server_id + sucursal_id (sin almacén)
        3. Retornar None si no hay configuración
        
        Args:
            server_id: ID del servidor
            sucursal_id: ID de la sucursal origen
            almacen_id: ID del almacén (opcional)
        
        Returns:
            ID del usuario responsable o None
        """
        try:
            # Intento 1: Buscar configuración específica de almacén
            if almacen_id:
                config = await self.collection.find_one({
                    "server_id": server_id,
                    "sucursal_origen_id": sucursal_id,
                    "almacen_id": almacen_id,
                    "activa": True
                }, {"_id": 0, "usuario_responsable_id": 1})
                
                if config and config.get("usuario_responsable_id"):
                    return config["usuario_responsable_id"]
            
            # Intento 2: Buscar configuración general de sucursal
            config = await self.collection.find_one({
                "server_id": server_id,
                "sucursal_origen_id": sucursal_id,
                "activa": True
            }, {"_id": 0, "usuario_responsable_id": 1})
            
            if config and config.get("usuario_responsable_id"):
                return config["usuario_responsable_id"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error buscando usuario responsable: {e}")
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
        Establece el usuario responsable para una sucursal (y opcionalmente almacén).
        
        Args:
            server_id: ID del servidor
            sucursal_id: ID de la sucursal
            usuario_id: ID del usuario responsable
            almacen_id: ID del almacén (opcional)
            modificado_por: Usuario que hace la modificación
        
        Returns:
            True si se actualizó correctamente
        """
        try:
            filtro = {
                "server_id": server_id,
                "sucursal_origen_id": sucursal_id
            }
            if almacen_id:
                filtro["almacen_id"] = almacen_id
            
            result = await self.collection.update_one(
                filtro,
                {
                    "$set": {
                        "usuario_responsable_id": usuario_id,
                        "fecha_modificacion": datetime.now(timezone.utc).isoformat(),
                        "usuario_modificacion": modificado_por
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error estableciendo usuario responsable: {e}")
            return False
    
    async def get_todas_asignaciones(self, server_id: Optional[str] = None) -> List[Dict]:
        """
        Obtiene todas las configuraciones de asignación.
        
        Args:
            server_id: Filtrar por servidor (opcional)
        
        Returns:
            Lista de configuraciones con usuario_responsable_id
        """
        try:
            filtro = {"activa": True}
            if server_id:
                filtro["server_id"] = server_id
            
            cursor = self.collection.find(
                filtro,
                {"_id": 0}
            ).sort("sucursal_nombre", 1)
            
            return await cursor.to_list(length=500)
            
        except Exception as e:
            logger.error(f"Error obteniendo asignaciones: {e}")
            return []
