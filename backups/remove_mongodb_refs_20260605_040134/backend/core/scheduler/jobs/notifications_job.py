"""
EDARSA HUB - Notifications Dispatcher Job
=========================================
Job para despacho automático de notificaciones pendientes.

Funcionalidades:
- Procesa cola de notificaciones pendientes
- Aplica deduplicación
- Maneja reintentos con backoff
- Respeta horarios permitidos
- Registra resultados
"""

from typing import Dict, Any
from datetime import datetime, timezone
import logging
import pytz

from .base_job import BaseJob
from ..config import JobConfig

logger = logging.getLogger(__name__)


class NotificationsDispatcherJob(BaseJob):
    """
    Job de despacho de notificaciones.
    
    Procesa la cola de notificaciones pendientes usando
    el dispatcher del sistema de comunicaciones.
    """
    
    async def execute(self) -> Dict[str, Any]:
        """
        Ejecuta despacho de notificaciones.
        
        Returns:
            Dict con métricas de procesamiento
        """
        logger.info(f"Iniciando despacho de notificaciones (batch_size={self.config.batch_size})")
        
        # Verificar horario permitido
        if not self._is_within_allowed_hours():
            return {
                "processed_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
                "message": "Fuera de horario permitido de notificaciones",
                "details": {"reason": "outside_allowed_hours"}
            }
        
        # Obtener dispatcher
        from core.communications.dispatcher.dispatcher import NotificationDispatcher
        dispatcher = NotificationDispatcher(self.db)
        await dispatcher.initialize_providers()
        
        # Procesar cola
        resultado = await dispatcher.process_queue(limit=self.config.batch_size)
        
        processed = resultado.get("processed", 0)
        sent = resultado.get("sent", 0)
        failed = resultado.get("failed", 0)
        duplicates = resultado.get("duplicates", 0)
        errors = resultado.get("errors", [])
        
        message = (
            f"Notificaciones procesadas: {processed} total, "
            f"{sent} enviadas, {failed} fallidas, {duplicates} duplicados"
        )
        
        if errors:
            message += f" ({len(errors)} errores)"
        
        return {
            "processed_count": processed,
            "success_count": sent,
            "failed_count": failed,
            "skipped_count": duplicates,
            "message": message,
            "details": {
                "duplicates": duplicates,
                "errors": errors[:10] if errors else [],  # Limitar errores en log
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    
    def _is_within_allowed_hours(self) -> bool:
        """
        Verifica si estamos dentro del horario permitido para notificaciones.
        
        Default: 08:00 - 20:00 hora de México
        """
        try:
            # Obtener configuración de horarios
            # Por ahora usar defaults, en futuro leer de BD
            start_hour = 8
            end_hour = 20
            tz_name = "America/Mexico_City"
            
            tz = pytz.timezone(tz_name)
            now_local = datetime.now(tz)
            current_hour = now_local.hour
            
            if current_hour < start_hour or current_hour >= end_hour:
                logger.info(
                    f"Fuera de horario permitido: {current_hour}:00 "
                    f"(permitido {start_hour}:00 - {end_hour}:00)"
                )
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error verificando horario: {e}, permitiendo ejecución")
            return True  # En caso de error, permitir ejecución
    
    async def _get_pending_count(self) -> int:
        """Obtiene cantidad de notificaciones pendientes."""
        from core.communications.notifications.schemas import NotificationStatus
        count = await self.db.notification_queue.count_documents({
            "estado": NotificationStatus.PENDIENTE.value
        })
        return count


def create_notifications_job(db, config: JobConfig = None) -> NotificationsDispatcherJob:
    """Factory para crear instancia del job."""
    if config is None:
        from ..config import get_scheduler_config
        scheduler_config = get_scheduler_config()
        config = scheduler_config.jobs.get("notifications_dispatcher")
    return NotificationsDispatcherJob(db, config)
