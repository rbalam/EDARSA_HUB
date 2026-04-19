"""
Servicio Orquestador Operativo
CAB-003 | EDARSA HUB - Fase 2A

Coordina el flujo completo de operaciones sobre workflows, tareas,
justificaciones y auditoría. Actúa como fachada para operaciones
que involucran múltiples servicios.
"""
from typing import Optional, List, Dict, Any
from .workflow_service import (
    WorkflowService, 
    WorkflowNoEncontradoError,
    TransicionInvalidaError
)
from .tarea_service import TareaService, TareaNoEncontradaError
from .justificacion_service import JustificacionService
from .auditoria_service import AuditoriaService, WorkflowNoEnAuditoriaError
from .configuracion_service import ConfiguracionService
from ..schemas.enums import (
    EstadoWorkflow, 
    TipoTarea, 
    DecisionAuditoria,
    TipoJustificacion
)


class OperativoServiceError(Exception):
    """Excepción base para errores del servicio operativo."""
    pass


class FlujoInvalidoError(OperativoServiceError):
    """El flujo solicitado no es válido en el estado actual."""
    pass


class OperativoService:
    """
    Servicio orquestador para el módulo operativo.
    
    Coordina operaciones que involucran múltiples servicios,
    manteniendo la consistencia del flujo de trabajo.
    """
    
    def __init__(self, db):
        """
        Inicializa el servicio con todos los sub-servicios.
        
        Args:
            db: Instancia de la base de datos MongoDB
        """
        self.db = db
        self.workflow_service = WorkflowService(db)
        self.tarea_service = TareaService(db)
        self.justificacion_service = JustificacionService(db)
        self.auditoria_service = AuditoriaService(db)
        self.config_service = ConfiguracionService(db)
    
    # === OPERACIONES DE INICIO DE WORKFLOW ===
    
    async def iniciar_workflow_completo(
        self,
        procesado_id: str,
        diferencias: List[Dict],
        usuario_asignador_id: Optional[str] = None,
        usuario_revisor_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Inicia un workflow completo con diferencias y tarea inicial.
        
        Args:
            procesado_id: ID del folio procesado (de Fase 1)
            diferencias: Lista de diferencias detectadas
            usuario_asignador_id: Usuario que inicia el workflow
            usuario_revisor_id: Usuario a asignar para revisión (opcional)
            
        Returns:
            Dict con workflow y tarea creados
        """
        # Crear workflow con diferencias
        workflow = await self.workflow_service.crear_workflow(
            procesado_id, 
            diferencias
        )
        
        # Crear tarea inicial de revisión
        tarea = await self.tarea_service.crear_tarea(
            workflow_id=workflow["_id"],
            tipo_tarea=TipoTarea.REVISAR
        )
        
        # Si se proporciona revisor, asignar la tarea
        if usuario_revisor_id and usuario_asignador_id:
            tarea = await self.tarea_service.asignar_tarea(
                tarea_id=tarea["_id"],
                usuario_asignado_id=usuario_revisor_id,
                asignado_por_id=usuario_asignador_id
            )
            
            # Transicionar a EN_REVISION
            workflow = await self.workflow_service.cambiar_estado(
                workflow["_id"],
                EstadoWorkflow.EN_REVISION
            )
        
        return {
            "workflow": workflow,
            "tarea": tarea,
            "diferencias_count": len(diferencias)
        }
    
    # === OPERACIONES DE REVISIÓN ===
    
    async def completar_revision(
        self,
        workflow_id: str,
        tarea_id: str,
        usuario_id: str
    ) -> Dict[str, Any]:
        """
        Completa la revisión y prepara el workflow para justificación.
        
        Args:
            workflow_id: ID del workflow
            tarea_id: ID de la tarea de revisión
            usuario_id: Usuario que completa la revisión
            
        Returns:
            Dict con workflow y nueva tarea
        """
        # Completar tarea de revisión
        await self.tarea_service.completar_tarea(tarea_id)
        
        # Cambiar estado a PENDIENTE_JUSTIFICACION
        workflow = await self.workflow_service.cambiar_estado(
            workflow_id,
            EstadoWorkflow.PENDIENTE_JUSTIFICACION
        )
        
        # Crear tarea de justificación
        tarea_justificacion = await self.tarea_service.crear_tarea(
            workflow_id=workflow_id,
            tipo_tarea=TipoTarea.JUSTIFICAR
        )
        
        return {
            "workflow": workflow,
            "tarea_justificacion": tarea_justificacion
        }
    
    # === OPERACIONES DE JUSTIFICACIÓN ===
    
    async def registrar_justificacion_y_verificar(
        self,
        workflow_id: str,
        diferencia_id: str,
        texto_justificacion: str,
        usuario_justificador_id: str,
        evidencia_documental: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Registra una justificación y verifica si el workflow está completo.
        
        Args:
            workflow_id: ID del workflow
            diferencia_id: ID de la diferencia
            texto_justificacion: Texto de justificación
            usuario_justificador_id: Usuario que justifica
            evidencia_documental: Evidencia opcional
            
        Returns:
            Dict con justificación y estado de completitud
        """
        # Registrar justificación
        justificacion = await self.justificacion_service.registrar_justificacion(
            workflow_id=workflow_id,
            diferencia_id=diferencia_id,
            texto_justificacion=texto_justificacion,
            usuario_justificador_id=usuario_justificador_id,
            evidencia_documental=evidencia_documental
        )
        
        # Verificar si está completamente justificado
        estado_justificacion = await self.justificacion_service.verificar_workflow_completamente_justificado(
            workflow_id
        )
        
        return {
            "justificacion": justificacion,
            "estado_justificacion": estado_justificacion
        }
    
    async def completar_justificacion_y_enviar_auditoria(
        self,
        workflow_id: str,
        tarea_id: str
    ) -> Dict[str, Any]:
        """
        Completa la fase de justificación y envía a auditoría.
        
        Args:
            workflow_id: ID del workflow
            tarea_id: ID de la tarea de justificación
            
        Returns:
            Dict con workflow y nueva tarea de auditoría
            
        Raises:
            FlujoInvalidoError: Si no está completamente justificado
        """
        # Verificar que está completamente justificado
        estado = await self.justificacion_service.verificar_workflow_completamente_justificado(
            workflow_id
        )
        
        if not estado["completamente_justificado"]:
            raise FlujoInvalidoError(
                f"El workflow tiene {estado['pendientes']} diferencias sin justificar"
            )
        
        # Completar tarea de justificación
        await self.tarea_service.completar_tarea(tarea_id)
        
        # Cambiar estado a JUSTIFICADO
        await self.workflow_service.cambiar_estado(
            workflow_id,
            EstadoWorkflow.JUSTIFICADO
        )
        
        # Cambiar a EN_AUDITORIA
        workflow = await self.workflow_service.cambiar_estado(
            workflow_id,
            EstadoWorkflow.EN_AUDITORIA
        )
        
        # Crear tarea de auditoría
        tarea_auditoria = await self.tarea_service.crear_tarea(
            workflow_id=workflow_id,
            tipo_tarea=TipoTarea.AUDITAR
        )
        
        return {
            "workflow": workflow,
            "tarea_auditoria": tarea_auditoria
        }
    
    # === OPERACIONES DE AUDITORÍA ===
    
    async def procesar_decision_auditoria(
        self,
        workflow_id: str,
        tarea_id: str,
        decision: DecisionAuditoria,
        comentarios: str,
        auditor_id: str,
        requiere_accion: bool = False
    ) -> Dict[str, Any]:
        """
        Procesa una decisión de auditoría y actualiza el workflow.
        
        Args:
            workflow_id: ID del workflow
            tarea_id: ID de la tarea de auditoría
            decision: Decisión del auditor
            comentarios: Comentarios del auditor
            auditor_id: ID del auditor
            requiere_accion: Si requiere seguimiento
            
        Returns:
            Dict con decisión, workflow actualizado y posible nueva tarea
        """
        # Registrar decisión
        decision_doc = await self.auditoria_service.registrar_decision(
            workflow_id=workflow_id,
            decision=decision,
            comentarios_auditor=comentarios,
            usuario_auditor_id=auditor_id,
            requiere_accion_adicional=requiere_accion
        )
        
        # Completar tarea de auditoría
        await self.tarea_service.completar_tarea(tarea_id)
        
        resultado = {
            "decision": decision_doc,
            "workflow": None,
            "nueva_tarea": None
        }
        
        # Actualizar estado según decisión
        if decision == DecisionAuditoria.APROBADO:
            resultado["workflow"] = await self.workflow_service.cambiar_estado(
                workflow_id,
                EstadoWorkflow.CERRADO
            )
            
        elif decision == DecisionAuditoria.RECHAZADO:
            resultado["workflow"] = await self.workflow_service.cambiar_estado(
                workflow_id,
                EstadoWorkflow.CERRADO
            )
            
        elif decision == DecisionAuditoria.DEVUELTO_PARA_CORRECCION:
            # Incrementar ciclo
            await self.workflow_service.incrementar_ciclo(workflow_id)
            
            # Volver a PENDIENTE_JUSTIFICACION
            resultado["workflow"] = await self.workflow_service.cambiar_estado(
                workflow_id,
                EstadoWorkflow.PENDIENTE_JUSTIFICACION
            )
            
            # Crear nueva tarea de justificación
            resultado["nueva_tarea"] = await self.tarea_service.crear_tarea(
                workflow_id=workflow_id,
                tipo_tarea=TipoTarea.JUSTIFICAR
            )
        
        return resultado
    
    # === OPERACIONES DE ESCALAMIENTO ===
    
    async def escalar_workflow(
        self,
        workflow_id: str,
        motivo: str,
        usuario_id: str
    ) -> Dict[str, Any]:
        """
        Escala un workflow para atención especial.
        
        Args:
            workflow_id: ID del workflow
            motivo: Motivo del escalamiento
            usuario_id: Usuario que escala
            
        Returns:
            Dict con workflow escalado y tarea
        """
        # Cambiar estado a ESCALADO
        workflow = await self.workflow_service.cambiar_estado(
            workflow_id,
            EstadoWorkflow.ESCALADO
        )
        
        # Crear tarea de escalamiento
        tarea = await self.tarea_service.crear_tarea(
            workflow_id=workflow_id,
            tipo_tarea=TipoTarea.ESCALAR
        )
        
        return {
            "workflow": workflow,
            "tarea": tarea,
            "motivo": motivo
        }
    
    # === OPERACIONES DE DASHBOARD ===
    
    async def obtener_resumen_dashboard(self, server_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Obtiene un resumen completo para el dashboard.
        FASE 3.1: Soporta filtrado por server_ids para RBAC.
        
        Args:
            server_ids: Lista opcional de server_ids permitidos para filtrar
        
        Returns:
            Dict con resúmenes de workflows, tareas y alertas
        """
        # Resumen de workflows
        workflows_por_estado = await self.workflow_service.resumen_por_estado(server_ids=server_ids)
        
        # Resumen de tareas
        tareas_por_estado = await self.tarea_service.resumen_por_estado(server_ids=server_ids)
        
        # Tareas vencidas
        tareas_vencidas = await self.tarea_service.obtener_tareas_vencidas(server_ids=server_ids)
        
        # Workflows escalados
        workflows_escalados = await self.workflow_service.listar_escalados(server_ids=server_ids)
        
        # Parámetros operativos
        parametros = await self.config_service.obtener_parametros_operativos()
        
        return {
            "workflows": {
                "por_estado": workflows_por_estado,
                "total": sum(workflows_por_estado.values()) if workflows_por_estado else 0
            },
            "tareas": {
                "por_estado": tareas_por_estado,
                "vencidas": len(tareas_vencidas)
            },
            "alertas": {
                "tareas_vencidas": len(tareas_vencidas),
                "workflows_escalados": len(workflows_escalados)
            },
            "parametros": parametros
        }
    
    async def obtener_alertas_activas(self, server_ids: Optional[List[str]] = None) -> List[Dict]:
        """
        Obtiene las alertas activas del sistema.
        FASE 3.1: Soporta filtrado por server_ids para RBAC.
        
        Args:
            server_ids: Lista opcional de server_ids permitidos para filtrar
        
        Returns:
            Lista de alertas
        """
        alertas = []
        
        # Tareas vencidas
        tareas_vencidas = await self.tarea_service.obtener_tareas_vencidas(server_ids=server_ids)
        for tarea in tareas_vencidas:
            alertas.append({
                "tipo": "TAREA_VENCIDA",
                "severidad": "ALTA",
                "mensaje": f"Tarea {tarea['tipo_tarea']} ha excedido su fecha límite",
                "tarea_id": tarea["_id"],
                "workflow_id": tarea["workflow_id"]
            })
        
        # Workflows escalados
        workflows_escalados = await self.workflow_service.listar_escalados(server_ids=server_ids)
        for wf in workflows_escalados:
            alertas.append({
                "tipo": "WORKFLOW_ESCALADO",
                "severidad": "ALTA",
                "mensaje": f"Workflow requiere atención de supervisión",
                "workflow_id": wf["_id"]
            })
        
        return alertas
