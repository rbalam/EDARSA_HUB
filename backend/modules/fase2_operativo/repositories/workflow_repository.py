"""
Repositorio para workflow_inventarios
CAB-003 | EDARSA HUB - Fase 2A

Gestiona el acceso a datos de workflows de inventario.
"""
from typing import Optional, List, Dict
from pymongo import DESCENDING
from .base_repository import BaseRepository


class WorkflowRepository(BaseRepository):
    """Repository para la colección workflow_inventarios."""
    
    def __init__(self, db):
        super().__init__(db, "workflow_inventarios")
    
    async def get_by_procesado_id(self, procesado_id: str) -> Optional[Dict]:
        """
        Obtiene un workflow por su procesado_id (FK a Fase 1).
        
        Args:
            procesado_id: ID del folio procesado
            
        Returns:
            Workflow o None si no existe
        """
        doc = self.collection.find_one({"procesado_id": procesado_id})
        return self._serialize_id(doc)
    
    async def get_by_estado(
        self, 
        estado: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Dict]:
        """
        Obtiene workflows por estado.
        
        Args:
            estado: Estado del workflow
            skip: Paginación
            limit: Límite
            
        Returns:
            Lista de workflows
        """
        cursor = self.collection.find(
            {"estado_workflow": estado}
        ).skip(skip).limit(limit).sort("fecha_creacion", DESCENDING)
        
        return self._serialize_list(list(cursor))
    
    async def get_pendientes_asignacion(self, limit: int = 100) -> List[Dict]:
        """Obtiene workflows pendientes de asignación."""
        return await self.get_by_estado("PENDIENTE_ASIGNACION", limit=limit)
    
    async def get_en_revision(self, limit: int = 100) -> List[Dict]:
        """Obtiene workflows en revisión."""
        return await self.get_by_estado("EN_REVISION", limit=limit)
    
    async def get_pendientes_justificacion(self, limit: int = 100) -> List[Dict]:
        """Obtiene workflows pendientes de justificación."""
        return await self.get_by_estado("PENDIENTE_JUSTIFICACION", limit=limit)
    
    async def get_en_auditoria(self, limit: int = 100) -> List[Dict]:
        """Obtiene workflows en auditoría."""
        return await self.get_by_estado("EN_AUDITORIA", limit=limit)
    
    async def get_escalados(self, limit: int = 100) -> List[Dict]:
        """Obtiene workflows escalados."""
        return await self.get_by_estado("ESCALADO", limit=limit)
    
    async def actualizar_estado(self, id: str, nuevo_estado: str) -> Optional[Dict]:
        """
        Actualiza el estado de un workflow.
        
        Args:
            id: ID del workflow
            nuevo_estado: Nuevo estado
            
        Returns:
            Workflow actualizado
        """
        return await self.update(id, {"estado_workflow": nuevo_estado})
    
    async def incrementar_ciclo(self, id: str) -> Optional[Dict]:
        """
        Incrementa el ciclo de reasignación de un workflow.
        
        Args:
            id: ID del workflow
            
        Returns:
            Workflow actualizado
        """
        object_id = self._to_object_id(id)
        if object_id is None:
            return None
        
        result = self.collection.find_one_and_update(
            {"_id": object_id},
            {
                "$inc": {"ciclo_actual": 1},
                "$set": {"fecha_ultima_actualizacion": self._get_timestamp()}
            },
            return_document=True
        )
        
        return self._serialize_id(result)
    
    async def contar_por_estado(self) -> Dict[str, int]:
        """
        Cuenta workflows agrupados por estado.
        
        Returns:
            Diccionario con conteos por estado
        """
        pipeline = [
            {"$group": {"_id": "$estado_workflow", "count": {"$sum": 1}}}
        ]
        
        result = list(self.collection.aggregate(pipeline))
        return {item["_id"]: item["count"] for item in result}
