"""
EDARSA HUB - Job de Auditorías Programadas
==========================================
Job del scheduler para ejecutar auditorías programadas automáticamente.

Características:
- Idempotente (no duplica ejecuciones)
- Valida configuración antes de ejecutar
- Registra cada ejecución en log
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from ..job_logger import get_job_logger

logger = logging.getLogger(__name__)


class AuditoriasSchedulerJob:
    """
    Job para disparar auditorías programadas.
    
    Se ejecuta cada hora y procesa auditorías cuya
    próxima ejecución <= ahora.
    """
    
    def __init__(self, db, config: Optional[dict] = None):
        self.db = db
        self.config = config or {}
        self.job_logger = get_job_logger(db)
    
    async def run(self):
        """
        Ejecuta el job de auditorías programadas.
        
        1. Obtiene auditorías pendientes
        2. Para cada una, verifica idempotencia
        3. Ejecuta si corresponde
        4. Registra resultado
        """
        inicio = datetime.now(timezone.utc)
        procesados = 0
        exitosos = 0
        fallidos = 0
        
        try:
            # Importar servicio
            from modules.fase2_operativo.services.auditoria_programada_service import (
                AuditoriaProgramadaService
            )
            from modules.fase2_operativo.repositories.auditoria_programada_repository import (
                AuditoriaProgramadaRepository
            )
            
            service = AuditoriaProgramadaService(self.db)
            repo = AuditoriaProgramadaRepository(self.db)
            
            # Obtener auditorías pendientes de ejecución
            ahora = datetime.now(timezone.utc)
            pendientes = await repo.get_pendientes_ejecucion(ahora)
            
            logger.info(f"Auditorías pendientes encontradas: {len(pendientes)}")
            
            for auditoria in pendientes:
                procesados += 1
                auditoria_id = auditoria["id"]
                
                try:
                    # La idempotencia se verifica dentro del servicio
                    fecha_programada = datetime.fromisoformat(
                        auditoria["proxima_ejecucion"].replace("Z", "+00:00")
                    )
                    
                    resultado = await service.ejecutar_programada(
                        auditoria_id=auditoria_id,
                        fecha_programada=fecha_programada
                    )
                    
                    if resultado.get("status") == "duplicada":
                        logger.debug(f"Auditoría {auditoria_id} ya procesada, ignorando")
                    elif resultado.get("estado") == "COMPLETADA":
                        exitosos += 1
                        logger.info(
                            f"Auditoría {auditoria_id} ejecutada - "
                            f"Workflow: {resultado.get('workflow_id')}"
                        )
                    else:
                        fallidos += 1
                        logger.warning(
                            f"Auditoría {auditoria_id} falló: "
                            f"{resultado.get('error_detalle', 'Error desconocido')}"
                        )
                
                except Exception as e:
                    fallidos += 1
                    logger.error(f"Error ejecutando auditoría {auditoria_id}: {e}")
            
            # Registrar ejecución del job
            duracion = int((datetime.now(timezone.utc) - inicio).total_seconds() * 1000)
            
            await self.job_logger.log_execution(
                job_name="auditorias_scheduler",
                status="success" if fallidos == 0 else "partial",
                duration_ms=duracion,
                processed_count=procesados,
                success_count=exitosos,
                failed_count=fallidos,
                message=f"Procesadas {procesados} auditorías: {exitosos} exitosas, {fallidos} fallidas"
            )
            
            logger.info(
                f"Job auditorias_scheduler completado: "
                f"{procesados} procesadas, {exitosos} exitosas, {fallidos} fallidas"
            )
            
        except Exception as e:
            duracion = int((datetime.now(timezone.utc) - inicio).total_seconds() * 1000)
            
            await self.job_logger.log_execution(
                job_name="auditorias_scheduler",
                status="failed",
                duration_ms=duracion,
                processed_count=procesados,
                success_count=exitosos,
                failed_count=fallidos,
                error_detail=str(e),
                message=f"Error en job: {str(e)}"
            )
            
            logger.error(f"Error en job auditorias_scheduler: {e}")
            raise


def create_auditorias_job(db, config: Optional[dict] = None) -> AuditoriasSchedulerJob:
    """Factory para crear el job de auditorías."""
    return AuditoriasSchedulerJob(db, config)
