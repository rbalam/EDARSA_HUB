"""
EDARSA HUB - SLA Processor Job
==============================
Job para procesamiento automático del motor SLA.

Funcionalidades:
- Recalcula estados SLA de tareas activas
- Dispara notificaciones al 80% (warning)
- Dispara notificaciones al 100% (vencido)
- Dispara notificaciones al 150% (escalado)
- Registra todas las transiciones
"""

from typing import Dict, Any
from datetime import datetime, timezone
import logging

from .base_job import BaseJob
from ..config import JobConfig

logger = logging.getLogger(__name__)


class SLAProcessorJob(BaseJob):
    """
    Job de procesamiento de SLA.
    
    Ejecuta el método actualizar_estados_sla() del SLAService
    que ya incluye la lógica de notificaciones automáticas.
    """
    
    async def execute(self) -> Dict[str, Any]:
        """
        Ejecuta procesamiento de SLA.
        
        Returns:
            Dict con métricas de procesamiento
        """
        logger.info(f"Iniciando procesamiento SLA (batch_size={self.config.batch_size})")
        
        # Obtener servicio SLA
        from modules.fase2_operativo.services.sla_service import get_sla_service
        sla_service = get_sla_service(self.db)
        
        # El método actualizar_estados_sla ya hace todo el trabajo:
        # - Recalcula estados
        # - Dispara notificaciones automáticas (warning/expired/escalated)
        # - Registra actualizaciones
        resultado = await sla_service.actualizar_estados_sla()
        
        # Mapear resultado al formato esperado
        processed = resultado.get("total_procesadas", 0)
        updated = resultado.get("actualizadas", 0)
        errors = resultado.get("errores", 0)
        
        notificaciones = resultado.get("notificaciones", {})
        warnings_sent = notificaciones.get("warning_enviadas", 0)
        expired_sent = notificaciones.get("vencido_enviadas", 0)
        escalated_sent = notificaciones.get("escalado_enviadas", 0)
        
        total_notifications = warnings_sent + expired_sent + escalated_sent
        
        message = (
            f"SLA procesado: {processed} tareas, {updated} actualizadas, "
            f"{total_notifications} notificaciones ({warnings_sent} warning, "
            f"{expired_sent} vencido, {escalated_sent} escalado)"
        )
        
        return {
            "processed_count": processed,
            "success_count": updated + total_notifications,
            "failed_count": errors,
            "skipped_count": processed - updated,
            "message": message,
            "details": {
                "por_estado": resultado.get("por_estado", {}),
                "notificaciones": notificaciones,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }


def create_sla_job(db, config: JobConfig = None) -> SLAProcessorJob:
    """Factory para crear instancia del job."""
    if config is None:
        from ..config import get_scheduler_config
        scheduler_config = get_scheduler_config()
        config = scheduler_config.jobs.get("sla_processor")
    return SLAProcessorJob(db, config)
