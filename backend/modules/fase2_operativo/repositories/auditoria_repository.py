"""
Repositorio para decisiones_auditoria
CAB-003 | EDARSA HUB - Fase 2A

Gestiona el acceso a datos de decisiones de auditoría.
"""
from typing import Optional, List, Dict
from pymongo import DESCENDING
from .base_repository import BaseRepository


class AuditoriaRepository(BaseRepository):
    """Repository para la colección decisiones_auditoria."""
    
    def __init__(self, db):
        super().__init__(db, "decisiones_auditoria")
    
    async def get_by_workflow(self, workflow_id: str) -> List[Dict]:
        """
        Obtiene todas las decisiones de auditoría de un workflow.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Lista de decisiones ordenadas por fecha
        """
        cursor = self.collection.find(
            {"workflow_id": workflow_id}
        ).sort("fecha_decision", DESCENDING)
        
        return self._serialize_list(list(cursor))
    
    async def get_ultima_decision(self, workflow_id: str) -> Optional[Dict]:
        """
        Obtiene la última decisión de auditoría de un workflow.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Última decisión o None
        """
        doc = self.collection.find_one(
            {"workflow_id": workflow_id},
            sort=[("fecha_decision", DESCENDING)]
        )
        return self._serialize_id(doc)
    
    async def get_by_auditor(self, auditor_id: str, limit: int = 100) -> List[Dict]:
        """
        Obtiene decisiones tomadas por un auditor.
        
        Args:
            auditor_id: ID del auditor
            limit: Límite de resultados
            
        Returns:
            Lista de decisiones
        """
        cursor = self.collection.find(
            {"usuario_auditor_id": auditor_id}
        ).sort("fecha_decision", DESCENDING).limit(limit)
        
        return self._serialize_list(list(cursor))
    
    async def get_por_decision(self, decision: str, limit: int = 100) -> List[Dict]:
        """
        Obtiene registros por tipo de decisión.
        
        Args:
            decision: Tipo de decisión (APROBADO, RECHAZADO, DEVUELTO_PARA_CORRECCION)
            limit: Límite de resultados
            
        Returns:
            Lista de decisiones
        """
        cursor = self.collection.find(
            {"decision": decision}
        ).sort("fecha_decision", DESCENDING).limit(limit)
        
        return self._serialize_list(list(cursor))
    
    async def contar_por_decision(self) -> Dict[str, int]:
        """
        Cuenta decisiones agrupadas por tipo.
        
        Returns:
            Diccionario con conteos por tipo de decisión
        """
        pipeline = [
            {"$group": {"_id": "$decision", "count": {"$sum": 1}}}
        ]
        
        result = list(self.collection.aggregate(pipeline))
        return {item["_id"]: item["count"] for item in result}
    
    async def workflow_tiene_decision(self, workflow_id: str) -> bool:
        """
        Verifica si un workflow tiene al menos una decisión de auditoría.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            True si tiene decisión, False si no
        """
        return await self.exists({"workflow_id": workflow_id})
