"""
EDARSA HUB - Scheduler Manager
==============================
Manager central para el scheduler de jobs.

Responsabilidades:
- Registrar jobs
- Iniciar/detener scheduler
- Controlar ciclo de vida con FastAPI
- Evitar registros duplicados
"""

from typing import Optional, Dict, Any
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED

from .config import get_scheduler_config
from .locks import get_lock_manager
from .job_logger import get_job_logger
from .jobs.sla_job import create_sla_job
from .jobs.notifications_job import create_notifications_job
from .jobs.auditorias_job import create_auditorias_job

logger = logging.getLogger(__name__)


class SchedulerManager:
    """
    Manager central del scheduler.
    
    Características:
    - Singleton seguro
    - Integración con FastAPI lifecycle
    - Jobs configurables
    - Listeners para eventos
    """
    
    _instance: Optional["SchedulerManager"] = None
    _initialized: bool = False
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db=None):
        """
        Args:
            db: Conexión MongoDB (requerido en primera inicialización)
        """
        # Evitar re-inicialización
        if SchedulerManager._initialized and self._scheduler is not None:
            return
        
        if db is None and not SchedulerManager._initialized:
            raise ValueError("db requerido en primera inicialización")
        
        if not SchedulerManager._initialized:
            self.db = db
            self.config = get_scheduler_config()
            self._scheduler: Optional[AsyncIOScheduler] = None
            self._jobs: Dict[str, Any] = {}
            self._running = False
            SchedulerManager._initialized = True
            logger.info("SchedulerManager inicializado")
    
    def _create_scheduler(self) -> AsyncIOScheduler:
        """Crea instancia del scheduler APScheduler."""
        scheduler = AsyncIOScheduler(
            timezone=self.config.timezone,
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 60
            }
        )
        
        # Agregar listeners
        scheduler.add_listener(
            self._on_job_executed,
            EVENT_JOB_EXECUTED
        )
        scheduler.add_listener(
            self._on_job_error,
            EVENT_JOB_ERROR
        )
        scheduler.add_listener(
            self._on_job_missed,
            EVENT_JOB_MISSED
        )
        
        return scheduler
    
    def _on_job_executed(self, event):
        """Callback cuando un job termina exitosamente."""
        logger.debug(f"Job ejecutado: {event.job_id}")
    
    def _on_job_error(self, event):
        """Callback cuando un job falla."""
        logger.error(f"Job error: {event.job_id} - {event.exception}")
    
    def _on_job_missed(self, event):
        """Callback cuando un job se pierde."""
        logger.warning(f"Job perdido: {event.job_id}")
    
    async def _run_sla_job(self):
        """Wrapper async para ejecutar job SLA."""
        job_config = self.config.jobs.get("sla_processor")
        if not job_config or not job_config.enabled:
            return
        
        job = create_sla_job(self.db, job_config)
        await job.run()
    
    async def _run_notifications_job(self):
        """Wrapper async para ejecutar job de notificaciones."""
        job_config = self.config.jobs.get("notifications_dispatcher")
        if not job_config or not job_config.enabled:
            return
        
        job = create_notifications_job(self.db, job_config)
        await job.run()
    
    async def _run_auditorias_job(self):
        """Wrapper async para ejecutar job de auditorías programadas."""
        job_config = self.config.jobs.get("auditorias_scheduler")
        if not job_config or not job_config.enabled:
            return
        
        job = create_auditorias_job(self.db, job_config)
        await job.run()
    
    def register_jobs(self):
        """Registra todos los jobs configurados."""
        if self._scheduler is None:
            self._scheduler = self._create_scheduler()
        
        # Job SLA
        sla_config = self.config.jobs.get("sla_processor")
        if sla_config and sla_config.enabled:
            if sla_config.cron_expression:
                trigger = CronTrigger.from_crontab(sla_config.cron_expression)
            else:
                trigger = IntervalTrigger(seconds=sla_config.interval_seconds)
            
            self._scheduler.add_job(
                self._run_sla_job,
                trigger=trigger,
                id="sla_processor",
                name="SLA Processor",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["sla_processor"] = sla_config
            logger.info(f"Job SLA registrado: intervalo={sla_config.interval_seconds}s")
        
        # Job Notificaciones
        notif_config = self.config.jobs.get("notifications_dispatcher")
        if notif_config and notif_config.enabled:
            if notif_config.cron_expression:
                trigger = CronTrigger.from_crontab(notif_config.cron_expression)
            else:
                trigger = IntervalTrigger(seconds=notif_config.interval_seconds)
            
            self._scheduler.add_job(
                self._run_notifications_job,
                trigger=trigger,
                id="notifications_dispatcher",
                name="Notifications Dispatcher",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["notifications_dispatcher"] = notif_config
            logger.info(f"Job Notificaciones registrado: intervalo={notif_config.interval_seconds}s")
        
        # Job Auditorías Programadas
        audit_config = self.config.jobs.get("auditorias_scheduler")
        if audit_config and audit_config.enabled:
            if audit_config.cron_expression:
                trigger = CronTrigger.from_crontab(audit_config.cron_expression)
            else:
                trigger = IntervalTrigger(seconds=audit_config.interval_seconds)
            
            self._scheduler.add_job(
                self._run_auditorias_job,
                trigger=trigger,
                id="auditorias_scheduler",
                name="Auditorias Scheduler",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["auditorias_scheduler"] = audit_config
            logger.info(f"Job Auditorías registrado: intervalo={audit_config.interval_seconds}s")
    
    async def start(self):
        """Inicia el scheduler."""
        if not self.config.enabled:
            logger.info("Scheduler deshabilitado por configuración")
            return
        
        if self._running:
            logger.warning("Scheduler ya está corriendo")
            return
        
        # Asegurar índices
        lock_manager = get_lock_manager(self.db)
        await lock_manager.ensure_indexes()
        
        job_logger = get_job_logger(self.db)
        await job_logger.ensure_indexes()
        
        # Limpiar locks expirados
        await lock_manager.cleanup_expired()
        
        # Registrar jobs
        self.register_jobs()
        
        # Iniciar scheduler
        self._scheduler.start()
        self._running = True
        
        logger.info(f"Scheduler iniciado con {len(self._jobs)} jobs")
    
    async def stop(self):
        """Detiene el scheduler limpiamente."""
        if not self._running or self._scheduler is None:
            return
        
        logger.info("Deteniendo scheduler...")
        
        self._scheduler.shutdown(wait=True)
        self._running = False
        
        # Limpiar locks del proceso actual
        lock_manager = get_lock_manager(self.db)
        await lock_manager.cleanup_expired()
        
        logger.info("Scheduler detenido")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado actual del scheduler."""
        if self._scheduler is None:
            return {
                "running": False,
                "jobs": [],
                "message": "Scheduler no inicializado"
            }
        
        jobs_status = []
        for job in self._scheduler.get_jobs():
            job_info = {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            jobs_status.append(job_info)
        
        return {
            "running": self._running,
            "enabled": self.config.enabled,
            "timezone": self.config.timezone,
            "jobs": jobs_status,
            "jobs_count": len(jobs_status)
        }
    
    def get_job_info(self, job_id: str) -> Optional[Dict]:
        """Obtiene información de un job específico."""
        if self._scheduler is None:
            return None
        
        job = self._scheduler.get_job(job_id)
        if not job:
            return None
        
        config = self._jobs.get(job_id)
        
        return {
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
            "config": config.model_dump() if config else None
        }
    
    async def run_job_now(self, job_id: str) -> Dict[str, Any]:
        """Ejecuta un job inmediatamente."""
        if job_id == "sla_processor":
            await self._run_sla_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "notifications_dispatcher":
            await self._run_notifications_job()
            return {"status": "executed", "job_id": job_id}
        else:
            return {"status": "error", "message": f"Job desconocido: {job_id}"}
    
    def pause_job(self, job_id: str) -> bool:
        """Pausa un job."""
        if self._scheduler is None:
            return False
        try:
            self._scheduler.pause_job(job_id)
            logger.info(f"Job pausado: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error pausando job {job_id}: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """Reanuda un job pausado."""
        if self._scheduler is None:
            return False
        try:
            self._scheduler.resume_job(job_id)
            logger.info(f"Job reanudado: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error reanudando job {job_id}: {e}")
            return False


# =============================================================================
# FUNCIONES DE CONVENIENCIA
# =============================================================================

_scheduler_manager: Optional[SchedulerManager] = None


def get_scheduler_manager(db=None) -> SchedulerManager:
    """Obtiene instancia del scheduler manager."""
    global _scheduler_manager
    if _scheduler_manager is None:
        if db is None:
            raise ValueError("db requerido para inicializar SchedulerManager")
        _scheduler_manager = SchedulerManager(db)
    return _scheduler_manager


async def start_scheduler(db) -> SchedulerManager:
    """Inicia el scheduler."""
    manager = get_scheduler_manager(db)
    await manager.start()
    return manager


async def stop_scheduler():
    """Detiene el scheduler."""
    global _scheduler_manager
    if _scheduler_manager:
        await _scheduler_manager.stop()


def reset_scheduler_manager():
    """Reset para testing."""
    global _scheduler_manager
    if _scheduler_manager and _scheduler_manager._scheduler:
        _scheduler_manager._scheduler.shutdown(wait=False)
    _scheduler_manager = None
    SchedulerManager._instance = None
    SchedulerManager._initialized = False
