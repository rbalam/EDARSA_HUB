"""
EDARSA HUB - Notification Orchestrator Service
==============================================
Subfase 2B.5 - Servicio principal de orquestación de notificaciones.

Este es el punto de entrada para disparar notificaciones desde
cualquier módulo del sistema (inventarios, compras, CxP, etc.).

Responsabilidades:
- Recibir eventos de negocio
- Determinar si se debe notificar
- Resolver destinatarios
- Delegar a dispatcher
- NO contiene lógica de negocio de WhatsApp
"""

from typing import Optional, Dict, Any, List
import logging

from .schemas import (
    NotificationEvent,
    NotificationResult,
    EventType,
    SendMode,
)
from .repository import NotificationRepository
from .dedup import DeduplicationService
from ..templates.template_service import TemplateService
from ..dispatcher.dispatcher import NotificationDispatcher

logger = logging.getLogger(__name__)


class NotificationOrchestratorService:
    """
    Orquestador principal de notificaciones.
    
    Punto de entrada único para solicitar notificaciones.
    Decide si, cómo, y a quién notificar basado en:
    - Configuración del evento
    - Estado del destinatario
    - Reglas de deduplicación
    
    MIGRACIÓN SQL SERVER (Mayo 2026):
    - Operaciones de MongoDB pasan por StubDatabase
    """
    
    def __init__(self, db):
        self.db = db
        self._is_stub = self._check_is_stub(db)
        self.repository = NotificationRepository(db)
        self.dedup_service = DeduplicationService(db)
        self.template_service = TemplateService(db)
        self._dispatcher: Optional[NotificationDispatcher] = None
    
    def _check_is_stub(self, db) -> bool:
        """Verifica si estamos usando StubDatabase."""
        if db is None:
            return True
        try:
            from core.mongo_stub import StubDatabase
            return isinstance(db, StubDatabase)
        except ImportError:
            return False
    
    async def _get_dispatcher(self) -> NotificationDispatcher:
        """Obtiene o crea instancia del dispatcher."""
        if self._dispatcher is None:
            self._dispatcher = NotificationDispatcher(self.db)
            await self._dispatcher.initialize_providers()
        return self._dispatcher
    
    async def notify(self, event: NotificationEvent) -> NotificationResult:
        """
        Procesa un evento de notificación.
        
        Flujo:
        1. Verificar configuración activa
        2. Resolver destinatarios
        3. Validar teléfonos
        4. Encolar o enviar
        
        Args:
            event: Evento de notificación
            
        Returns:
            NotificationResult con resultado
        """
        result = NotificationResult(
            success=False,
            event_type=event.evento,
            channel=event.canal
        )
        
        try:
            # 1. Obtener configuración del evento
            config = await self.repository.get_config(
                canal=event.canal,
                modulo=event.modulo,
                evento=event.evento
            )
            
            if not config:
                logger.info(f"Sin configuración para evento {event.evento}, usando defaults")
                # Crear configuración default
                config = {
                    "activo": True,
                    "modo_envio": SendMode.MOCK.value,
                    "provider": "mock",
                    "enviar_a_responsable": True,
                    "enviar_a_supervisor": False,
                    "enviar_a_gerente": False,
                    "ventana_duplicidad_minutos": 60,
                    "template_codigo": f"{event.modulo}_{event.evento.lower()}"
                }
            
            if not config.get("activo", True):
                logger.info(f"Notificación desactivada para evento {event.evento}")
                result.errors.append("Evento desactivado en configuración")
                return result
            
            # 2. Resolver destinatarios
            destinatarios = await self._resolve_recipients(event, config)
            
            if not destinatarios:
                logger.warning(f"Sin destinatarios válidos para evento {event.evento}")
                result.errors.append("Sin destinatarios válidos")
                return result
            
            # 3. Determinar template
            template_codigo = config.get("template_codigo") or f"{event.modulo}_{event.evento.lower()}"
            
            # 4. Encolar para procesamiento
            dispatcher = await self._get_dispatcher()
            queue_id = await dispatcher.enqueue(event, destinatarios, template_codigo)
            
            # 5. Procesar cola (envío inmediato)
            process_result = await dispatcher.process_queue(limit=10)
            
            result.success = process_result.get("sent", 0) > 0
            result.destinatarios_enviados = process_result.get("sent", 0)
            result.destinatarios_fallidos = process_result.get("failed", 0)
            result.duplicados = process_result.get("duplicates", 0)
            result.log_ids = [queue_id]
            
            logger.info(
                f"Notificación procesada: evento={event.evento}, "
                f"enviados={result.destinatarios_enviados}, "
                f"fallidos={result.destinatarios_fallidos}"
            )
            
        except Exception as e:
            logger.error(f"Error en notificación {event.evento}: {e}")
            result.errors.append(str(e))
        
        return result
    
    async def _resolve_recipients(
        self,
        event: NotificationEvent,
        config: Dict
    ) -> List[Dict[str, Any]]:
        """
        Resuelve los destinatarios para una notificación.
        
        Busca usuarios por ID y obtiene sus teléfonos.
        
        Args:
            event: Evento con IDs de destinatarios
            config: Configuración con reglas de envío
            
        Returns:
            Lista de {user_id, telefono, nombre, tipo}
        """
        destinatarios = []
        
        # Responsable
        if config.get("enviar_a_responsable", True) and event.responsable_id:
            user = await self._get_user_contact(event.responsable_id)
            if user:
                destinatarios.append({
                    "user_id": event.responsable_id,
                    "telefono": user.get("telefono"),
                    "nombre": user.get("name"),
                    "email": user.get("email"),
                    "tipo": "responsable"
                })
        
        # Supervisor
        if config.get("enviar_a_supervisor", False) and event.supervisor_id:
            user = await self._get_user_contact(event.supervisor_id)
            if user:
                destinatarios.append({
                    "user_id": event.supervisor_id,
                    "telefono": user.get("telefono"),
                    "nombre": user.get("name"),
                    "email": user.get("email"),
                    "tipo": "supervisor"
                })
        
        # Gerente
        if config.get("enviar_a_gerente", False) and event.gerente_id:
            user = await self._get_user_contact(event.gerente_id)
            if user:
                destinatarios.append({
                    "user_id": event.gerente_id,
                    "telefono": user.get("telefono"),
                    "nombre": user.get("name"),
                    "email": user.get("email"),
                    "tipo": "gerente"
                })
        
        # Destinatarios adicionales
        for user_id in event.destinatarios_adicionales:
            user = await self._get_user_contact(user_id)
            if user:
                destinatarios.append({
                    "user_id": user_id,
                    "telefono": user.get("telefono"),
                    "nombre": user.get("name"),
                    "email": user.get("email"),
                    "tipo": "adicional"
                })
        
        # Filtrar destinatarios sin teléfono (pero registrar para auditoría)
        return destinatarios
    
    async def _get_user_contact(self, user_id: str) -> Optional[Dict]:
        """
        Obtiene datos de contacto de un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict con name, email, telefono o None
        """
        # En modo stub, intentar obtener desde SQL
        if self._is_stub:
            try:
                from modules.fase2_operativo.sql_repository import obtener_usuario_por_id
                user = await obtener_usuario_por_id(user_id)
                if user:
                    return user
            except Exception:
                pass
            return None
        
        user = await self.db.users.find_one(
            {"id": user_id, "active": True},
            {"_id": 0, "id": 1, "name": 1, "email": 1, "telefono": 1}
        )
        return user
    
    # =========================================================================
    # MÉTODOS DE CONVENIENCIA PARA EVENTOS ESPECÍFICOS
    # =========================================================================
    
    async def notify_task_assigned(
        self,
        tarea_id: str,
        workflow_id: str,
        responsable_id: str,
        folio: str,
        sucursal: str,
        fecha_limite: str,
        tipo_tarea: str = "Justificación"
    ) -> NotificationResult:
        """Notifica asignación de tarea."""
        event = NotificationEvent(
            evento=EventType.ASIGNACION_TAREA,
            modulo="inventarios",
            tarea_id=tarea_id,
            workflow_id=workflow_id,
            responsable_id=responsable_id,
            payload={
                "folio": folio,
                "sucursal": sucursal,
                "fecha_limite": fecha_limite,
                "tipo_tarea": tipo_tarea
            }
        )
        return await self.notify(event)
    
    async def notify_sla_warning(
        self,
        tarea_id: str,
        workflow_id: str,
        responsable_id: str,
        folio: str,
        sucursal: str,
        evento: str,
        fecha_limite: str,
        horas_restantes: float
    ) -> NotificationResult:
        """Notifica SLA por vencer (80%)."""
        event = NotificationEvent(
            evento=EventType.SLA_POR_VENCER,
            modulo="inventarios",
            tarea_id=tarea_id,
            workflow_id=workflow_id,
            responsable_id=responsable_id,
            prioridad=2,  # Alta prioridad
            payload={
                "folio": folio,
                "sucursal": sucursal,
                "evento": evento,
                "fecha_limite": fecha_limite,
                "horas_restantes": round(horas_restantes, 1)
            }
        )
        return await self.notify(event)
    
    async def notify_sla_expired(
        self,
        tarea_id: str,
        workflow_id: str,
        responsable_id: str,
        supervisor_id: Optional[str],
        folio: str,
        sucursal: str,
        evento: str
    ) -> NotificationResult:
        """Notifica SLA vencido (100%)."""
        event = NotificationEvent(
            evento=EventType.SLA_VENCIDO,
            modulo="inventarios",
            tarea_id=tarea_id,
            workflow_id=workflow_id,
            responsable_id=responsable_id,
            supervisor_id=supervisor_id,
            prioridad=1,  # Máxima prioridad
            payload={
                "folio": folio,
                "sucursal": sucursal,
                "evento": evento
            }
        )
        return await self.notify(event)
    
    async def notify_sla_escalated(
        self,
        tarea_id: str,
        workflow_id: str,
        supervisor_id: str,
        gerente_id: Optional[str],
        folio: str,
        sucursal: str,
        evento: str,
        porcentaje_excedido: float
    ) -> NotificationResult:
        """Notifica escalamiento SLA (150%)."""
        event = NotificationEvent(
            evento=EventType.SLA_ESCALADO,
            modulo="inventarios",
            tarea_id=tarea_id,
            workflow_id=workflow_id,
            supervisor_id=supervisor_id,
            gerente_id=gerente_id,
            prioridad=1,  # Máxima prioridad
            payload={
                "folio": folio,
                "sucursal": sucursal,
                "evento": evento,
                "porcentaje_excedido": round(porcentaje_excedido, 0)
            }
        )
        return await self.notify(event)
    
    async def notify_justification_rejected(
        self,
        tarea_id: str,
        workflow_id: str,
        responsable_id: str,
        folio: str,
        sucursal: str,
        motivo: str
    ) -> NotificationResult:
        """Notifica rechazo de justificación."""
        event = NotificationEvent(
            evento=EventType.JUSTIFICACION_RECHAZADA,
            modulo="inventarios",
            tarea_id=tarea_id,
            workflow_id=workflow_id,
            responsable_id=responsable_id,
            payload={
                "folio": folio,
                "sucursal": sucursal,
                "motivo": motivo
            }
        )
        return await self.notify(event)
    
    async def notify_audit_decision(
        self,
        workflow_id: str,
        responsable_id: str,
        folio: str,
        sucursal: str,
        decision: str,
        comentario: str = ""
    ) -> NotificationResult:
        """Notifica decisión de auditoría."""
        event = NotificationEvent(
            evento=EventType.DECISION_AUDITORIA,
            modulo="inventarios",
            workflow_id=workflow_id,
            responsable_id=responsable_id,
            payload={
                "folio": folio,
                "sucursal": sucursal,
                "decision": decision,
                "comentario": comentario or "Sin comentarios adicionales"
            }
        )
        return await self.notify(event)
    
    async def notify_workflow_closed(
        self,
        workflow_id: str,
        responsable_id: str,
        folio: str,
        sucursal: str,
        estado_final: str
    ) -> NotificationResult:
        """Notifica cierre de workflow."""
        event = NotificationEvent(
            evento=EventType.CIERRE_WORKFLOW,
            modulo="inventarios",
            workflow_id=workflow_id,
            responsable_id=responsable_id,
            payload={
                "folio": folio,
                "sucursal": sucursal,
                "estado_final": estado_final
            }
        )
        return await self.notify(event)


# =============================================================================
# SINGLETON
# =============================================================================

_orchestrator: Optional[NotificationOrchestratorService] = None


def get_notification_orchestrator(db) -> NotificationOrchestratorService:
    """Obtiene instancia del orquestador."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = NotificationOrchestratorService(db)
    return _orchestrator


def reset_notification_orchestrator():
    """Reset para testing."""
    global _orchestrator
    _orchestrator = None
