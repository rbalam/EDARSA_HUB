"""
Repositorio para historial_asignaciones
CAB-003 | EDARSA HUB - Fase 2A

Gestiona el acceso a datos del historial de asignaciones de tareas.
"""
from typing import List, Dict
from pymongo import DESCENDING
from .base_repository import BaseRepository


class HistorialAsignacionRepository(BaseRepository):
    """Repository para la colección historial_asignaciones."""
    
    def __init__(self, db):
        super().__init__(db, "historial_asignaciones")
    
    async def get_by_tarea(self, tarea_id: str) -> List[Dict]:
        """
        Obtiene el historial de asignaciones de una tarea.
        
        Args:
            tarea_id: ID de la tarea
            
        Returns:
            Lista de registros de historial ordenados por fecha
        """
        cursor = self.collection.find(
            {"tarea_id": tarea_id}
        ).sort("fecha_cambio", DESCENDING)
        
        return self._serialize_list(list(cursor))
    
    async def get_by_usuario_anterior(self, usuario_id: str) -> List[Dict]:
        """
        Obtiene reasignaciones donde el usuario fue el anterior asignado.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Lista de registros
        """
        cursor = self.collection.find(
            {"usuario_anterior_id": usuario_id}
        ).sort("fecha_cambio", DESCENDING)
        
        return self._serialize_list(list(cursor))
    
    async def get_by_usuario_nuevo(self, usuario_id: str) -> List[Dict]:
        """
        Obtiene asignaciones donde el usuario fue el nuevo asignado.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Lista de registros
        """
        cursor = self.collection.find(
            {"usuario_nuevo_id": usuario_id}
        ).sort("fecha_cambio", DESCENDING)
        
        return self._serialize_list(list(cursor))
    
    async def contar_reasignaciones_tarea(self, tarea_id: str) -> int:
        """
        Cuenta el número de reasignaciones de una tarea.
        
        Args:
            tarea_id: ID de la tarea
            
        Returns:
            Número de reasignaciones
        """
        return await self.count({"tarea_id": tarea_id})
    
    async def create(self, data: Dict) -> Dict:
        """
        Crea un registro de historial con timestamp de cambio.
        
        Args:
            data: Datos del registro
            
        Returns:
            Registro creado
        """
        data["fecha_cambio"] = self._get_timestamp()
        return await super().create(data)
