"""
Servicio de Workflow de Inventarios
CAB-003 | EDARSA HUB - Fase 2A

Encapsula la lógica de negocio para gestión de workflows operativos.
"""
from typing import Optional, List, Dict, Any
from ..repositories.workflow_repository import WorkflowRepository
from ..repositories.detalle_diferencias_repository import DetalleDiferenciasRepository
from ..schemas.enums import EstadoWorkflow


class WorkflowServiceError(Exception):
    """Excepción base para errores del servicio de workflow."""
    pass


class WorkflowNoEncontradoError(WorkflowServiceError):
    """El workflow solicitado no existe."""
    pass


class TransicionInvalidaError(WorkflowServiceError):
    """La transición de estado no es válida."""
    pass


class WorkflowYaExisteError(WorkflowServiceError):
    """Ya existe un workflow para este procesado_id."""
    pass


class WorkflowService:
    """
    Servicio para gestión de workflows de inventario.
    
    Maneja la lógica de negocio relacionada con el ciclo de vida
    de los workflows operativos.
    """
    
    # Mapa de transiciones válidas entre estados
    TRANSICIONES_VALIDAS = {
        EstadoWorkflow.PENDIENTE_ASIGNACION: [
            EstadoWorkflow.EN_REVISION
        ],
        EstadoWorkflow.EN_REVISION: [
            EstadoWorkflow.PENDIENTE_JUSTIFICACION,
            EstadoWorkflow.ESCALADO
        ],
        EstadoWorkflow.PENDIENTE_JUSTIFICACION: [
            EstadoWorkflow.JUSTIFICADO,
            EstadoWorkflow.ESCALADO
        ],
        EstadoWorkflow.JUSTIFICADO: [
            EstadoWorkflow.EN_AUDITORIA
        ],
        EstadoWorkflow.EN_AUDITORIA: [
            EstadoWorkflow.CERRADO,
            EstadoWorkflow.PENDIENTE_JUSTIFICACION  # Devuelto para corrección
        ],
        EstadoWorkflow.ESCALADO: [
            EstadoWorkflow.CERRADO
        ],
        EstadoWorkflow.CERRADO: []  # Estado final
    }
    
    def __init__(self, db):
        """
        Inicializa el servicio con conexión a BD.
        
        Args:
            db: Instancia de la base de datos MongoDB
        """
        self.workflow_repo = WorkflowRepository(db)
        self.detalle_repo = DetalleDiferenciasRepository(db)
    
    async def obtener_workflow_por_id(self, workflow_id: str) -> Optional[Dict]:
        """
        Obtiene un workflow por su ID.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Workflow o None si no existe
        """
        return await self.workflow_repo.get_by_id(workflow_id)
    
    async def obtener_workflow_por_procesado_id(self, procesado_id: str) -> Optional[Dict]:
        """
        Obtiene un workflow por el ID del folio procesado (FK a Fase 1).
        
        Args:
            procesado_id: ID del folio procesado
            
        Returns:
            Workflow o None si no existe
        """
        return await self.workflow_repo.get_by_procesado_id(procesado_id)
    
    async def obtener_workflow_completo(self, workflow_id: str) -> Optional[Dict]:
        """
        Obtiene un workflow con sus diferencias asociadas.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Workflow con diferencias o None
        """
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            return None
        
        # Agregar diferencias asociadas
        workflow["diferencias"] = await self.detalle_repo.get_by_workflow(workflow_id)
        workflow["total_diferencias"] = len(workflow["diferencias"])
        workflow["valor_total_diferencia"] = await self.detalle_repo.calcular_total_diferencia(workflow_id)
        
        return workflow
    
    async def crear_workflow(
        self, 
        procesado_id: str,
        diferencias: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Crea un nuevo workflow para un folio procesado.
        
        Args:
            procesado_id: ID del folio procesado (de Fase 1)
            diferencias: Lista opcional de diferencias a asociar
            
        Returns:
            Workflow creado
            
        Raises:
            WorkflowYaExisteError: Si ya existe workflow para este procesado_id
        """
        # Verificar que no exista
        existente = await self.workflow_repo.get_by_procesado_id(procesado_id)
        if existente:
            raise WorkflowYaExisteError(
                f"Ya existe un workflow para procesado_id: {procesado_id}"
            )
        
        # Crear workflow
        workflow_data = {
            "procesado_id": procesado_id,
            "estado_workflow": EstadoWorkflow.PENDIENTE_ASIGNACION.value,
            "ciclo_actual": 1
        }
        
        workflow = await self.workflow_repo.create(workflow_data)
        
        # Crear diferencias asociadas si se proporcionan
        if diferencias:
            for dif in diferencias:
                dif["workflow_id"] = workflow["_id"]
                await self.detalle_repo.create(dif)
        
        return workflow
    
    async def crear_workflow_si_no_existe(
        self, 
        procesado_id: str,
        diferencias: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Crea un workflow solo si no existe. Si existe, lo retorna.
        
        Args:
            procesado_id: ID del folio procesado
            diferencias: Lista opcional de diferencias
            
        Returns:
            Workflow existente o nuevo
        """
        existente = await self.workflow_repo.get_by_procesado_id(procesado_id)
        if existente:
            return existente
        
        return await self.crear_workflow(procesado_id, diferencias)
    
    def _validar_transicion(
        self, 
        estado_actual: EstadoWorkflow, 
        nuevo_estado: EstadoWorkflow
    ) -> bool:
        """
        Valida si una transición de estado es permitida.
        
        Args:
            estado_actual: Estado actual del workflow
            nuevo_estado: Estado destino
            
        Returns:
            True si la transición es válida
        """
        estados_permitidos = self.TRANSICIONES_VALIDAS.get(estado_actual, [])
        return nuevo_estado in estados_permitidos
    
    async def cambiar_estado(
        self, 
        workflow_id: str, 
        nuevo_estado: EstadoWorkflow
    ) -> Dict:
        """
        Cambia el estado de un workflow validando la transición.
        
        Args:
            workflow_id: ID del workflow
            nuevo_estado: Nuevo estado
            
        Returns:
            Workflow actualizado
            
        Raises:
            WorkflowNoEncontradoError: Si el workflow no existe
            TransicionInvalidaError: Si la transición no es válida
        """
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise WorkflowNoEncontradoError(f"Workflow no encontrado: {workflow_id}")
        
        estado_actual = EstadoWorkflow(workflow["estado_workflow"])
        
        if not self._validar_transicion(estado_actual, nuevo_estado):
            raise TransicionInvalidaError(
                f"Transición no válida: {estado_actual.value} -> {nuevo_estado.value}"
            )
        
        return await self.workflow_repo.actualizar_estado(workflow_id, nuevo_estado.value)
    
    async def incrementar_ciclo(self, workflow_id: str) -> Dict:
        """
        Incrementa el ciclo de reasignación de un workflow.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Workflow actualizado
            
        Raises:
            WorkflowNoEncontradoError: Si el workflow no existe
        """
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise WorkflowNoEncontradoError(f"Workflow no encontrado: {workflow_id}")
        
        return await self.workflow_repo.incrementar_ciclo(workflow_id)
    
    async def listar_pendientes_asignacion(self, limit: int = 100) -> List[Dict]:
        """
        Lista workflows pendientes de asignación.
        
        Args:
            limit: Límite de resultados
            
        Returns:
            Lista de workflows
        """
        return await self.workflow_repo.get_pendientes_asignacion(limit)
    
    async def listar_en_revision(self, limit: int = 100) -> List[Dict]:
        """Lista workflows en revisión."""
        return await self.workflow_repo.get_en_revision(limit)
    
    async def listar_pendientes_justificacion(self, limit: int = 100) -> List[Dict]:
        """Lista workflows pendientes de justificación."""
        return await self.workflow_repo.get_pendientes_justificacion(limit)
    
    async def listar_en_auditoria(self, limit: int = 100) -> List[Dict]:
        """Lista workflows en auditoría."""
        return await self.workflow_repo.get_en_auditoria(limit)
    
    async def listar_escalados(self, limit: int = 100) -> List[Dict]:
        """Lista workflows escalados."""
        return await self.workflow_repo.get_escalados(limit)
    
    async def resumen_por_estado(self) -> Dict[str, int]:
        """
        Obtiene resumen de conteos por estado.
        
        Returns:
            Diccionario con conteos por estado
        """
        return await self.workflow_repo.contar_por_estado()
    
    async def listar_workflows(
        self,
        estado: Optional[EstadoWorkflow] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Lista workflows con filtros y paginación.
        
        Args:
            estado: Filtro por estado (opcional)
            skip: Paginación
            limit: Límite
            
        Returns:
            Dict con items y total
        """
        filters = {}
        if estado:
            filters["estado_workflow"] = estado.value
        
        items = await self.workflow_repo.get_all(filters, skip, limit)
        total = await self.workflow_repo.count(filters)
        
        return {"items": items, "total": total}
