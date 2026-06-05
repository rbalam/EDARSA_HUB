"""
Repositorio para decisiones_auditoria - VERSIÓN SQL
CAB-003 | EDARSA HUB - Fase 2A

FASE B-P1-E: Migrado a EDARSAHUB SQL Server
- CERO MongoDB productivo
- SQL explícito contra Workflow_DecisionesAuditoria
"""
from typing import Optional, List, Dict

from .sql_base_repository import SQLBaseRepository


class AuditoriaRepository(SQLBaseRepository):
    """
    Repository para la tabla Workflow_DecisionesAuditoria.
    Migrado de MongoDB a SQL Server EDARSAHUB.
    """
    
    def __init__(self, db=None):
        """
        Inicializa el repository SQL.
        Args:
            db: IGNORADO - Solo para compatibilidad. Todo va a SQL.
        """
        super().__init__("decisiones_auditoria")
    
    async def get_by_workflow(self, workflow_id: str) -> List[Dict]:
        """
        Obtiene todas las decisiones de auditoría de un workflow.
        """
        cursor = self.find(
            {"workflow_id": workflow_id}
        ).sort("fecha_decision", -1)
        
        return list(cursor)
    
    async def get_ultima_decision(self, workflow_id: str) -> Optional[Dict]:
        """
        Obtiene la última decisión de auditoría de un workflow.
        """
        cursor = self.find(
            {"workflow_id": workflow_id}
        ).sort("fecha_decision", -1).limit(1)
        
        results = list(cursor)
        return results[0] if results else None
    
    async def get_by_auditor(self, auditor_id: str, limit: int = 100) -> List[Dict]:
        """
        Obtiene decisiones tomadas por un auditor.
        """
        cursor = self.find(
            {"usuario_auditor_id": auditor_id}
        ).sort("fecha_decision", -1).limit(limit)
        
        return list(cursor)
    
    async def get_por_decision(self, decision: str, limit: int = 100) -> List[Dict]:
        """
        Obtiene registros por tipo de decisión.
        """
        cursor = self.find(
            {"decision": decision}
        ).sort("fecha_decision", -1).limit(limit)
        
        return list(cursor)
    
    async def contar_por_decision(self) -> Dict[str, int]:
        """
        Cuenta decisiones agrupadas por tipo.
        """
        pipeline = [
            {"$group": {"_id": "$decision", "count": {"$sum": 1}}}
        ]
        
        result = list(self.aggregate(pipeline))
        return {item.get("_id", "UNKNOWN"): item.get("count", 0) for item in result if item.get("_id")}
    
    async def workflow_tiene_decision(self, workflow_id: str) -> bool:
        """
        Verifica si un workflow tiene al menos una decisión de auditoría.
        """
        return await self.exists({"workflow_id": workflow_id})
    
    # Métodos de compatibilidad
    def _serialize_id(self, doc: Optional[Dict]) -> Optional[Dict]:
        """Compatibilidad - No necesario en SQL."""
        return doc
    
    def _serialize_list(self, docs: List[Dict]) -> List[Dict]:
        """Compatibilidad - No necesario en SQL."""
        return docs
