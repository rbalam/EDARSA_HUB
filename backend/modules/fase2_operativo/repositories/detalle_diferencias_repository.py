"""
Repositorio para detalle_diferencias
CAB-003 | EDARSA HUB - Fase 2A

Gestiona el acceso a datos de detalles de diferencias de inventario.
"""
from typing import Optional, List, Dict
from .base_repository import BaseRepository


class DetalleDiferenciasRepository(BaseRepository):
    """Repository para la colección detalle_diferencias."""
    
    def __init__(self, db):
        super().__init__(db, "detalle_diferencias")
    
    async def get_by_workflow(self, workflow_id: str) -> List[Dict]:
        """
        Obtiene todos los detalles de diferencia de un workflow.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Lista de detalles de diferencia
        """
        cursor = self.collection.find({"workflow_id": workflow_id})
        return self._serialize_list(list(cursor))
    
    async def get_by_producto(self, producto_id: str) -> List[Dict]:
        """
        Obtiene detalles de diferencia por producto.
        
        Args:
            producto_id: ID del producto
            
        Returns:
            Lista de detalles
        """
        cursor = self.collection.find({"producto_id": producto_id})
        return self._serialize_list(list(cursor))
    
    async def get_pendientes_justificacion(self, workflow_id: str) -> List[Dict]:
        """
        Obtiene diferencias que requieren justificación completa.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Lista de diferencias que requieren justificación completa
        """
        cursor = self.collection.find({
            "workflow_id": workflow_id,
            "requiere_justificacion_completa": True
        })
        return self._serialize_list(list(cursor))
    
    async def calcular_total_diferencia(self, workflow_id: str) -> float:
        """
        Calcula el total de diferencia de valor de un workflow.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Suma total de diferencia_valor
        """
        pipeline = [
            {"$match": {"workflow_id": workflow_id}},
            {"$group": {"_id": None, "total": {"$sum": "$diferencia_valor"}}}
        ]
        
        result = list(self.collection.aggregate(pipeline))
        return result[0]["total"] if result else 0.0
    
    async def contar_por_workflow(self, workflow_id: str) -> int:
        """
        Cuenta el número de diferencias en un workflow.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Número de diferencias
        """
        return await self.count({"workflow_id": workflow_id})
