from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Notification Dispatcher
====================================
Subfase 2B.5 - Cola y despacho de notificaciones.

Responsabilidades:
- Encolar solicitudes de notificación
- Procesar cola pendiente
- Reintentos automáticos
- Registro de resultados
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
import logging
import uuid

from ..notifications.schemas import (
    NotificationQueue,
    NotificationLog,
    NotificationStatus,
    NotificationEvent,
    NotificationResult,
)
from ..notifications.repository import NotificationRepository
from ..notifications.dedup import DeduplicationService
from ..templates.template_service import TemplateService
from ..providers.base import BaseProvider, ProviderFactory
from ..providers.mock_provider import MockProvider
from ..providers.twilio_provider import TwilioWhatsAppProvider
from ..providers.email_smtp_provider import EmailSMTPProvider

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    """
    Despachador de notificaciones.
    
    Flujo:
    1. Encolar solicitud
    2. Procesar cola
    3. Enviar via provider
    4. Registrar resultado
    
    MIGRACIÓN SQL SERVER (Mayo 2026):
    - Operaciones de MongoDB pasan por StubDatabase
    """
    
    def __init__(self, db):
        self.db = db
        self._is_stub = self._check_is_stub(db)
        self.repository = NotificationRepository(db)
        self.dedup_service = DeduplicationService(db)
        self.template_service = TemplateService(db)
        self._providers: Dict[str, BaseProvider] = {}
        self._worker_id = f"dispatcher_{uuid.uuid4().hex[:8]}"
    
    def _check_is_stub(self, db) -> bool:
        """Verifica si estamos usando StubDatabase."""
        if db is None:
            return True
        try:
            from core.mongo_stub import StubDatabase
            return isinstance(db, StubDatabase)
        except ImportError:
            return False
    
    async def initialize_providers(self):
        """
        Inicializa los providers configurados en BD.
        
        Orden de carga:
        1. Mock provider (siempre disponible)
        2. Twilio provider (si credenciales disponibles)
        3. Otros providers de BD
        """
        # 1. Siempre tener mock disponible
        mock_provider = MockProvider({})
        await mock_provider.initialize()
        self._providers["mock"] = mock_provider
        logger.info("Provider inicializado: mock")
        
        # 2. Intentar inicializar Twilio (credenciales desde env vars)
        try:
            twilio_config = await self.repository.get_provider_config("whatsapp", "twilio") or {
                "provider_type": "twilio",
                "token_ref": "TWILIO_AUTH_TOKEN"
            }
            twilio_provider = TwilioWhatsAppProvider(twilio_config)
            await twilio_provider.initialize()
            
            if twilio_provider.is_available():
                self._providers["twilio"] = twilio_provider
                self._providers["twilio_whatsapp"] = twilio_provider
                self._providers["twilio_sdk"] = twilio_provider
                logger.info("Provider inicializado: twilio_whatsapp (SDK)")
            else:
                logger.info("Provider Twilio no disponible (credenciales no configuradas)")
        except Exception as e:
            logger.warning(f"No se pudo inicializar Twilio provider: {e}")
        
        # 3. Gate 5D: providers adicionales desde SQL canonico.
        try:
            providers = await self.repository.get_all_provider_configs(activo=True)
            
            for config in providers:
                provider_name = config.get("provider")
                # Saltar mock y twilio (ya inicializados)
                if provider_name and provider_name not in ["mock", "twilio", "twilio_whatsapp", "twilio_sdk"]:
                    try:
                        provider = ProviderFactory.create(provider_name, config)
                        if provider:
                            await provider.initialize()
                            self._providers[provider_name] = provider
                            logger.info(f"Provider inicializado desde BD: {provider_name}")
                    except Exception as e:
                        logger.error(f"Error inicializando provider {provider_name}: {e}")
        except Exception as e:
            logger.warning(f"Error cargando providers de BD: {e}")
    
    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """Obtiene un provider por nombre."""
        return self._providers.get(name)
    
    def get_providers_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado de todos los providers.
        
        Returns:
            Dict con estado de cada provider
        """
        status = {
            "providers": {},
            "count": len(self._providers),
            "available_for_real_send": []
        }
        
        for name, provider in self._providers.items():
            provider_status = {
                "name": name,
                "initialized": provider.is_initialized(),
                "type": provider.__class__.__name__
            }
            
            # Para Twilio, incluir disponibilidad
            if hasattr(provider, 'is_available'):
                provider_status["available"] = provider.is_available()
                if provider.is_available():
                    status["available_for_real_send"].append(name)
            
            # Para Twilio, incluir info adicional
            if hasattr(provider, 'get_status'):
                provider_status["details"] = provider.get_status()
            
            status["providers"][name] = provider_status
        
        return status
    
    async def enqueue(
        self,
        event: NotificationEvent,
        destinatarios: List[Dict[str, Any]],
        template_codigo: str
    ) -> str:
        """
        Encola una solicitud de notificación.
        
        Args:
            event: Evento de negocio
            destinatarios: Lista de {user_id, telefono, nombre, tipo}
            template_codigo: Código del template a usar
            
        Returns:
            ID del item en cola
        """
        queue_item = NotificationQueue(
            canal=event.canal,
            modulo=event.modulo,
            evento_negocio=event.evento,
            referencia_id=event.referencia_id,
            workflow_id=event.workflow_id,
            tarea_id=event.tarea_id,
            prioridad=event.prioridad,
            destinatarios=destinatarios,
            template_codigo=template_codigo,
            payload=event.payload,
            estado=NotificationStatus.PENDIENTE
        )
        
        result = await self.repository.enqueue(queue_item)
        logger.info(f"Notificación encolada: {result['id']} (evento={event.evento})")
        return result["id"]
    
    async def process_queue(self, limit: int = 50) -> Dict[str, Any]:
        """
        Procesa items pendientes de la cola.
        
        Args:
            limit: Máximo de items a procesar
            
        Returns:
            Resumen de procesamiento
        """
        logger.info(f"Iniciando procesamiento de cola (limit={limit})")
        
        results = {
            "processed": 0,
            "sent": 0,
            "failed": 0,
            "duplicates": 0,
            "errors": []
        }
        
        pending_items = await self.repository.get_pending_items(limit)
        
        for item in pending_items:
            try:
                # Intentar bloquear
                locked = await self.repository.lock_item(item["id"], self._worker_id)
                if not locked:
                    continue  # Otro worker lo tomó
                
                # Procesar item
                item_result = await self._process_item(item)
                results["processed"] += 1
                
                if item_result.get("all_sent"):
                    results["sent"] += 1
                    await self.repository.mark_sent(item["id"])
                else:
                    results["failed"] += 1
                    if item_result.get("should_retry"):
                        # Programar reintento
                        await self._schedule_retry(item)
                    else:
                        await self.repository.mark_failed(item["id"], "Max reintentos alcanzados")
                
                results["duplicates"] += item_result.get("duplicates", 0)
                
            except Exception as e:
                logger.error(f"Error procesando item {item.get('id')}: {e}")
                results["errors"].append(str(e))
                await self.repository.mark_failed(item["id"], str(e))
        
        logger.info(f"Procesamiento completado: {results}")
        return results
    
    async def _process_item(self, item: Dict) -> Dict:
        """
        Procesa un item individual de la cola.
        """
        evento = item.get("evento_negocio")
        canal = item.get("canal", "whatsapp")
        template_codigo = item.get("template_codigo")
        payload = item.get("payload", {})
        destinatarios = item.get("destinatarios", [])
        
        # Obtener configuración del evento
        config = await self.repository.get_config(canal, item.get("modulo", "inventarios"), evento)
        
        # Determinar provider y modo
        provider_name = config.get("provider", "mock") if config else "mock"
        modo_envio = config.get("modo_envio", "mock") if config else "mock"
        ventana_dedup = config.get("ventana_duplicidad_minutos", 60) if config else 60
        
        # Si modo es mock, usar mock provider
        if modo_envio == "mock":
            provider_name = "mock"
        
        provider = self.get_provider(provider_name)
        if not provider:
            if str(modo_envio).lower() == "real":
                logger.error("Provider real no disponible para canal=%s provider=%s", canal, provider_name)
                return {"all_sent": False, "should_retry": True, "error_code": "REAL_PROVIDER_UNAVAILABLE"}
            provider = self._providers.get("mock")
        
        # Renderizar template
        template = await self.template_service.get_template(template_codigo, canal)
        if not template:
            logger.error(f"Template no encontrado: {template_codigo}")
            return {"all_sent": False, "should_retry": False}
        
        mensaje = self.template_service.render(template["template_texto"], payload)
        
        # Enviar a cada destinatario
        sent_count = 0
        failed_count = 0
        duplicates = 0
        
        for dest in destinatarios:
            telefono = dest.get("email") if str(canal).lower() == "email" else dest.get("telefono")
            user_id = dest.get("user_id")
            
            if not telefono:
                logger.warning(f"Destinatario sin teléfono: {user_id}")
                await self._log_notification(
                    item=item,
                    destinatario="N/A",
                    usuario_destino_id=user_id,
                    mensaje=mensaje,
                    provider=provider_name,
                    estado=NotificationStatus.OMITIDO,
                    error_codigo="NO_PHONE",
                    error_detalle="Destinatario sin número de teléfono"
                )
                continue
            
            # Verificar duplicado
            should_send = await self.dedup_service.should_send(
                evento=evento,
                referencia_id=item.get("referencia_id"),
                workflow_id=item.get("workflow_id"),
                destinatario=telefono,
                template_codigo=template_codigo,
                ventana_minutos=ventana_dedup
            )
            
            if not should_send["should_send"]:
                duplicates += 1
                await self._log_notification(
                    item=item,
                    destinatario=telefono,
                    usuario_destino_id=user_id,
                    mensaje=mensaje,
                    provider=provider_name,
                    estado=NotificationStatus.DUPLICADO,
                    error_codigo="DUPLICATE",
                    error_detalle=f"Duplicado de log {should_send['existing_log_id']}"
                )
                continue
            
            # Enviar
            try:
                response = await provider.send_message(
                    recipient=telefono,
                    message=mensaje,
                    metadata={"queue_id": item["id"], "event": evento}
                )
                
                if response.success:
                    sent_count += 1
                    await self._log_notification(
                        item=item,
                        destinatario=telefono,
                        usuario_destino_id=user_id,
                        usuario_destino_nombre=dest.get("nombre"),
                        tipo_destinatario=dest.get("tipo"),
                        mensaje=mensaje,
                        provider=provider_name,
                        estado=NotificationStatus.ENVIADO,
                        provider_message_id=response.message_id
                    )
                else:
                    failed_count += 1
                    await self._log_notification(
                        item=item,
                        destinatario=telefono,
                        usuario_destino_id=user_id,
                        mensaje=mensaje,
                        provider=provider_name,
                        estado=NotificationStatus.FALLIDO,
                        error_codigo=response.error_code,
                        error_detalle=response.error_message
                    )
            except Exception as e:
                failed_count += 1
                await self._log_notification(
                    item=item,
                    destinatario=telefono,
                    usuario_destino_id=user_id,
                    mensaje=mensaje,
                    provider=provider_name,
                    estado=NotificationStatus.FALLIDO,
                    error_codigo="EXCEPTION",
                    error_detalle=str(e)
                )
        
        total = len(destinatarios)
        all_sent = (sent_count + duplicates) == total and failed_count == 0
        
        # Determinar si debe reintentar
        max_reintentos = config.get("max_reintentos", 3) if config else 3
        intentos_actuales = item.get("intentos", 0) + 1
        should_retry = failed_count > 0 and intentos_actuales < max_reintentos
        
        return {
            "all_sent": all_sent,
            "sent": sent_count,
            "failed": failed_count,
            "duplicates": duplicates,
            "should_retry": should_retry
        }
    
    async def _log_notification(
        self,
        item: Dict,
        destinatario: str,
        mensaje: str,
        provider: str,
        estado: NotificationStatus,
        usuario_destino_id: Optional[str] = None,
        usuario_destino_nombre: Optional[str] = None,
        tipo_destinatario: Optional[str] = None,
        provider_message_id: Optional[str] = None,
        error_codigo: Optional[str] = None,
        error_detalle: Optional[str] = None
    ):
        """Registra el resultado en notification_log."""
        log_entry = NotificationLog(
            canal=item.get("canal", "whatsapp"),
            modulo=item.get("modulo", "inventarios"),
            evento_negocio=item.get("evento_negocio"),
            referencia_id=item.get("referencia_id"),
            workflow_id=item.get("workflow_id"),
            tarea_id=item.get("tarea_id"),
            queue_id=item.get("id"),
            destinatario=destinatario,
            usuario_destino_id=usuario_destino_id,
            usuario_destino_nombre=usuario_destino_nombre,
            tipo_destinatario=tipo_destinatario,
            template_codigo=item.get("template_codigo"),
            payload_renderizado=mensaje,
            provider=provider,
            provider_message_id=provider_message_id,
            estado_envio=estado,
            intentos=item.get("intentos", 0) + 1,
            error_codigo=error_codigo,
            error_detalle=error_detalle,
            fecha_envio=datetime.now(timezone.utc).isoformat() if estado == NotificationStatus.ENVIADO else None
        )
        
        await self.repository.create_log(log_entry)
    
    async def _schedule_retry(self, item: Dict):
        """Programa un reintento para el item."""
        intentos = item.get("intentos", 0)
        # Backoff exponencial: 5min, 15min, 45min
        delay_minutes = 5 * (3 ** intentos)
        proximo_intento = (datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)).isoformat()
        
        await self.repository.update_queue_item(item["id"], {
            "proximo_intento": proximo_intento,
            "estado": NotificationStatus.PENDIENTE.value,
            "locked_at": None,
            "locked_by": None
        })
        
        logger.info(f"Reintento programado para {item['id']} en {delay_minutes} minutos")
    
    async def send_immediate(
        self,
        event: NotificationEvent,
        destinatarios: List[Dict[str, Any]],
        template_codigo: str
    ) -> NotificationResult:
        """
        Envía notificación inmediatamente (sin encolar).
        
        Útil para mensajes de prueba o críticos.
        """
        result = NotificationResult(
            success=False,
            event_type=event.evento,
            channel=event.canal
        )
        
        # Obtener config
        config = await self.repository.get_config(
            event.canal, event.modulo, event.evento
        )
        
        provider_name = config.get("provider", "mock") if config else "mock"
        modo_envio = config.get("modo_envio", "mock") if config else "mock"
        
        if modo_envio == "mock":
            provider_name = "mock"
        
        provider = self.get_provider(provider_name)
        if not provider:
            if str(modo_envio).lower() == "real":
                result.errors.append("REAL_PROVIDER_UNAVAILABLE")
                return result
            provider = self._providers.get("mock")
        
        # Renderizar
        mensaje = await self.template_service.render_template(
            template_codigo, event.payload, event.canal
        )
        
        if not mensaje:
            result.errors.append(f"Template no encontrado: {template_codigo}")
            return result
        
        # Enviar
        for dest in destinatarios:
            telefono = dest.get("email") if str(event.canal).lower() == "email" else dest.get("telefono")
            if not telefono:
                result.destinatarios_omitidos += 1
                continue
            
            try:
                response = await provider.send_message(telefono, mensaje)
                if response.success:
                    result.destinatarios_enviados += 1
                    result.log_ids.append(response.message_id or "unknown")
                else:
                    result.destinatarios_fallidos += 1
                    result.errors.append(response.error_message or "Unknown error")
            except Exception as e:
                result.destinatarios_fallidos += 1
                result.errors.append(str(e))
        
        result.success = result.destinatarios_enviados > 0
        return result


# =============================================================================
# SINGLETON
# =============================================================================

_dispatcher: Optional[NotificationDispatcher] = None


async def get_dispatcher(db) -> NotificationDispatcher:
    """Obtiene instancia del dispatcher."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = NotificationDispatcher(db)
        await _dispatcher.initialize_providers()
    return _dispatcher


def reset_dispatcher():
    """Reset para testing."""
    global _dispatcher
    _dispatcher = None
