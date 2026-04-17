"""
Servicio de Auditoría de Inventario
CAB-003 | EDARSA HUB - Fase 2A

Encapsula la lógica de negocio para gestión de decisiones de auditoría.
"""
from typing import Optional, List, Dict
from datetime import datetime, timezone
from ..repositories.auditoria_repository import AuditoriaRepository
from ..repositories.workflow_repository import WorkflowRepository
from ..schemas.enums import DecisionAuditoria, EstadoWorkflow


class AuditoriaServiceError(Exception):
    """Excepción base para errores del servicio de auditoría."""
    pass


class WorkflowNoEnAuditoriaError(AuditoriaServiceError):
    """El workflow no está en estado de auditoría."""
    pass


class DecisionInvalidaError(AuditoriaServiceError):
    """La decisión de auditoría no es válida."""
    pass


class AuditoriaService:
    """
    Servicio para gestión de decisiones de auditoría.
    
    Maneja el registro de decisiones y la actualización correspondiente
    del estado del workflow.
    """
    
    MIN_LONGITUD_COMENTARIOS = 10  # Mínimo de caracteres para comentarios
    
    def __init__(self, db):
        """
        Inicializa el servicio con conexión a BD.
        
        Args:
            db: Instancia de la base de datos MongoDB
        """
        self.auditoria_repo = AuditoriaRepository(db)
        self.workflow_repo = WorkflowRepository(db)
    
    async def registrar_decision(
        self,
        workflow_id: str,
        decision: DecisionAuditoria,
        comentarios_auditor: str,
        usuario_auditor_id: str,
        requiere_accion_adicional: bool = False
    ) -> Dict:
        """
        Registra una decisión de auditoría.
        
        Args:
            workflow_id: ID del workflow
            decision: Decisión del auditor
            comentarios_auditor: Comentarios obligatorios
            usuario_auditor_id: ID del auditor
            requiere_accion_adicional: Si requiere seguimiento
            
        Returns:
            Decisión registrada
            
        Raises:
            WorkflowNoEnAuditoriaError: Si el workflow no está en auditoría
            DecisionInvalidaError: Si los comentarios son muy cortos
        """
        # Validar longitud de comentarios
        if len(comentarios_auditor.strip()) < self.MIN_LONGITUD_COMENTARIOS:
            raise DecisionInvalidaError(
                f"Los comentarios deben tener al menos {self.MIN_LONGITUD_COMENTARIOS} caracteres"
            )
        
        # Verificar que el workflow está en auditoría
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise WorkflowNoEnAuditoriaError(f"Workflow no encontrado: {workflow_id}")
        
        if workflow["estado_workflow"] != EstadoWorkflow.EN_AUDITORIA.value:
            raise WorkflowNoEnAuditoriaError(
                f"El workflow no está en auditoría. Estado actual: {workflow['estado_workflow']}"
            )
        
        # Crear registro de decisión
        decision_data = {
            "workflow_id": workflow_id,
            "decision": decision.value,
            "comentarios_auditor": comentarios_auditor.strip(),
            "usuario_auditor_id": usuario_auditor_id,
            "fecha_decision": datetime.now(timezone.utc),
            "requiere_accion_adicional": requiere_accion_adicional
        }
        
        decision_doc = await self.auditoria_repo.create(decision_data)
        
        # Actualizar estado del workflow según la decisión
        # NOTA: No se hace aquí para mantener separación de responsabilidades
        # El OperativoService coordinará esta actualización
        
        return decision_doc
    
    async def obtener_decision(self, decision_id: str) -> Optional[Dict]:
        """
        Obtiene una decisión por su ID.
        
        Args:
            decision_id: ID de la decisión
            
        Returns:
            Decisión o None
        """
        return await self.auditoria_repo.get_by_id(decision_id)
    
    async def obtener_decisiones_workflow(self, workflow_id: str) -> List[Dict]:
        """
        Obtiene todas las decisiones de un workflow.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Lista de decisiones ordenadas por fecha
        """
        return await self.auditoria_repo.get_by_workflow(workflow_id)
    
    async def obtener_ultima_decision(self, workflow_id: str) -> Optional[Dict]:
        """
        Obtiene la última decisión de auditoría de un workflow.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Última decisión o None
        """
        return await self.auditoria_repo.get_ultima_decision(workflow_id)
    
    async def validar_si_workflow_tiene_decision(self, workflow_id: str) -> bool:
        """
        Verifica si un workflow tiene al menos una decisión de auditoría.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            True si tiene decisión, False si no
        """
        return await self.auditoria_repo.workflow_tiene_decision(workflow_id)
    
    async def listar_por_decision(
        self, 
        decision: DecisionAuditoria, 
        limit: int = 100
    ) -> List[Dict]:
        """
        Lista decisiones por tipo.
        
        Args:
            decision: Tipo de decisión
            limit: Límite de resultados
            
        Returns:
            Lista de decisiones
        """
        return await self.auditoria_repo.get_por_decision(decision.value, limit)
    
    async def listar_por_auditor(
        self, 
        auditor_id: str, 
        limit: int = 100
    ) -> List[Dict]:
        """
        Lista decisiones tomadas por un auditor.
        
        Args:
            auditor_id: ID del auditor
            limit: Límite de resultados
            
        Returns:
            Lista de decisiones
        """
        return await self.auditoria_repo.get_by_auditor(auditor_id, limit)
    
    async def obtener_workflows_pendientes_auditoria(self, limit: int = 100) -> List[Dict]:
        """
        Obtiene workflows que están pendientes de auditoría.
        
        Args:
            limit: Límite de resultados
            
        Returns:
            Lista de workflows en estado EN_AUDITORIA
        """
        return await self.workflow_repo.get_en_auditoria(limit)
    
    async def resumen_por_decision(self) -> Dict[str, int]:
        """
        Obtiene resumen de decisiones por tipo.
        
        Returns:
            Diccionario con conteos por tipo de decisión
        """
        return await self.auditoria_repo.contar_por_decision()
