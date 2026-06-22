"""
EDARSA HUB - Base Job Class
===========================
Clase base para todos los jobs del scheduler.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging
import traceback

from ..locks import get_lock_manager
from ..job_logger import get_job_logger
from ..config import JobConfig

logger = logging.getLogger(__name__)


class BaseJob(ABC):
    """
    Clase base abstracta para jobs del scheduler.
    
    Proporciona:
    - Locking automático
    - Logging de ejecución
    - Manejo de errores
    - Métricas
    """
    
    def __init__(self, db, config: JobConfig):
        """
        Args:
            db: Dependencia técnica legacy opcional para locks/logs
            config: Configuración del job
        """
        self.db = db
        self.config = config
        self.job_name = config.job_id
        self.lock_manager = get_lock_manager(db)
        self.job_logger = get_job_logger(db)
    
    @abstractmethod
    async def execute(self) -> Dict[str, Any]:
        """
        Lógica principal del job.
        
        Debe implementarse en cada job concreto.
        
        Returns:
            Dict con resultados:
            - processed_count: int
            - success_count: int
            - failed_count: int
            - skipped_count: int
            - message: str (opcional)
            - details: Dict (opcional)
        """
        pass
    
    async def run(self) -> Dict[str, Any]:
        """
        Ejecuta el job con locking, logging y manejo de errores.
        
        NO sobrescribir este método. Implementar execute() en su lugar.
        
        Returns:
            Dict con resultado de ejecución
        """
        # Verificar si está habilitado
        if not self.config.enabled:
            await self.job_logger.log_skipped(self.job_name, "Job deshabilitado en configuración")
            return {"status": "skipped", "reason": "disabled"}
        
        # Intentar adquirir lock
        lock = self.lock_manager.get_lock(self.job_name)
        
        try:
            acquired = await lock.acquire(timeout_seconds=self.config.timeout_seconds)
            
            if not acquired:
                await self.job_logger.log_skipped(
                    self.job_name, 
                    "Lock no disponible - otra instancia en ejecución"
                )
                return {"status": "skipped", "reason": "locked"}
            
            # Iniciar heartbeat para jobs largos
            await lock.start_heartbeat_loop(
                interval_seconds=30,
                extend_seconds=self.config.timeout_seconds
            )
            
            # Registrar inicio
            log_entry = await self.job_logger.start_execution(
                job_name=self.job_name,
                metadata={"config": self.config.model_dump()}
            )
            
            try:
                # Ejecutar lógica del job
                result = await self.execute()
                
                # Registrar éxito
                await self.job_logger.finish_execution(
                    log_entry=log_entry,
                    status="success",
                    processed_count=result.get("processed_count", 0),
                    success_count=result.get("success_count", 0),
                    failed_count=result.get("failed_count", 0),
                    skipped_count=result.get("skipped_count", 0),
                    message=result.get("message"),
                    extra_metadata=result.get("details")
                )
                
                return {"status": "success", **result}
                
            except Exception as e:
                # Registrar error
                error_detail = traceback.format_exc()
                logger.error(f"Error en job {self.job_name}: {e}\n{error_detail}")
                
                await self.job_logger.finish_execution(
                    log_entry=log_entry,
                    status="failed",
                    message=str(e),
                    error_detail=error_detail[:2000]  # Limitar tamaño
                )
                
                return {"status": "failed", "error": str(e)}
                
        finally:
            # Siempre liberar lock
            await lock.release()
    
    def _safe_execute_item(self, item: Any, process_func) -> Dict:
        """
        Helper para ejecutar procesamiento de un item de forma segura.
        
        Captura errores individuales sin detener el batch completo.
        """
        try:
            result = process_func(item)
            return {"success": True, "result": result}
        except Exception as e:
            logger.warning(f"Error procesando item en {self.job_name}: {e}")
            return {"success": False, "error": str(e)}
