"""
Repositorio para justificaciones_inventario
CAB-003 | EDARSA HUB - Fase 2A

Gestiona el acceso a datos de justificaciones de inventario.
"""
from typing import List, Dict
from pymongo import DESCENDING
from .base_repository import BaseRepository


class JustificacionRepository(BaseRepository):
    """Repository para la colección justificaciones_inventario."""
    
    def __init__(self, db):
        super().__init__(db, "justificaciones_inventario")
    
    async def get_by_workflow(self, workflow_id: str) -> List[Dict]:
        """
        Obtiene todas las justificaciones de un workflow.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Lista de justificaciones
        """
        cursor = self.collection.find(
            {"workflow_id": workflow_id}
        ).sort("fecha_justificacion", DESCENDING)
        
        return self._serialize_list(list(cursor))
    
    async def get_by_diferencia(self, diferencia_id: str) -> List[Dict]:
        """
        Obtiene justificaciones de una diferencia específica.
        
        Args:
            diferencia_id: ID del detalle de diferencia
            
        Returns:
            Lista de justificaciones
        """
        cursor = self.collection.find(
            {"diferencia_id": diferencia_id}
        ).sort("fecha_justificacion", DESCENDING)
        
        return self._serialize_list(list(cursor))
    
    async def get_by_usuario(self, usuario_id: str, limit: int = 100) -> List[Dict]:
        """
        Obtiene justificaciones creadas por un usuario.
        
        Args:
            usuario_id: ID del usuario
            limit: Límite de resultados
            
        Returns:
            Lista de justificaciones
        """
        cursor = self.collection.find(
            {"usuario_justificador_id": usuario_id}
        ).sort("fecha_justificacion", DESCENDING).limit(limit)
        
        return self._serialize_list(list(cursor))
    
    async def get_por_tipo(self, tipo: str, limit: int = 100) -> List[Dict]:
        """
        Obtiene justificaciones por tipo (SIMPLE o COMPLETA).
        
        Args:
            tipo: Tipo de justificación
            limit: Límite de resultados
            
        Returns:
            Lista de justificaciones
        """
        cursor = self.collection.find(
            {"tipo_justificacion": tipo}
        ).sort("fecha_justificacion", DESCENDING).limit(limit)
        
        return self._serialize_list(list(cursor))
    
    async def contar_por_workflow(self, workflow_id: str) -> int:
        """
        Cuenta justificaciones de un workflow.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Número de justificaciones
        """
        return await self.count({"workflow_id": workflow_id})
    
    async def existe_justificacion(self, workflow_id: str, diferencia_id: str) -> bool:
        """
        Verifica si existe una justificación para una diferencia.
        
        Args:
            workflow_id: ID del workflow
            diferencia_id: ID de la diferencia
            
        Returns:
            True si existe, False si no
        """
        return await self.exists({
            "workflow_id": workflow_id,
            "diferencia_id": diferencia_id
        })
