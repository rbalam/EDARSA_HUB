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
from .jobs.pedidos_detector_job import create_pedidos_detector_job
from .jobs.inventarios_detector_job import create_inventarios_detector_job
# MACROFASE 2: Jobs de sincronización KPIs
from .jobs.sync_short_comercial_job import execute_sync_short_comercial
from .jobs.sync_nightly_comercial_job import execute_sync_nightly_comercial
# FASE 2.6: Job de sincronización Control de Ingresos
from .jobs.sync_ingresos_job import execute_sync_ingresos_incremental
# FASE 3.6: Job de sincronización Propinas TPV
from .jobs.sync_propinas_tpv_job import execute_sync_propinas_tpv_incremental
# SUBFASE 4: Job de sincronización Comercial V2 (Tablero Ejecutivo Blindado)
from .jobs.sync_comercial_v2_job import execute_sync_comercial_v2
# P0: Job de sincronización Ventas Abiertas V2 (cada 5 minutos)
from .jobs.sync_comercial_abiertas_v2_job import execute_sync_comercial_abiertas_v2

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
    
    async def _run_pedidos_detector_job(self):
        """Wrapper async para ejecutar job de detección de pedidos."""
        job_config = self.config.jobs.get("pedidos_detector")
        if not job_config or not job_config.enabled:
            return
        
        job = create_pedidos_detector_job(self.db, job_config)
        await job.run()
    
    async def _run_inventarios_detector_job(self):
        """Wrapper async para ejecutar job de detección de inventarios."""
        job_config = self.config.jobs.get("inventarios_detector")
        if not job_config or not job_config.enabled:
            return
        
        job = create_inventarios_detector_job(self.db, job_config)
        await job.run()
    
    async def _run_sync_short_comercial_job(self):
        """
        Wrapper async para ejecutar SYNC-S de KPIs comerciales.
        MACROFASE 2: Sincronización cada 15 min, ventana 48h.
        """
        job_config = self.config.jobs.get("sync_short_comercial")
        if not job_config or not job_config.enabled:
            logger.debug("SYNC-S deshabilitado por configuración")
            return
        
        # Obtener lock para evitar ejecución concurrente
        lock_manager = get_lock_manager(self.db)
        lock = lock_manager.get_lock("sync_short_comercial")
        lock_acquired = await lock.acquire(timeout_seconds=600)
        
        if not lock_acquired:
            logger.warning("[SYNC-S] No se pudo obtener lock - ya hay una ejecución en progreso")
            return
        
        job_logger = get_job_logger(self.db)
        log_entry = await job_logger.start_execution("sync_short_comercial")
        
        try:
            logger.info("[SYNC-S] Iniciando sincronización corta de KPIs")
            result = await execute_sync_short_comercial(self.db)
            
            # Finalizar log con éxito
            await job_logger.finish_execution(
                log_entry=log_entry,
                status="success" if not result.get("errors") else "partial",
                processed_count=result.get("inserts", 0) + result.get("updates", 0),
                success_count=result.get("inserts", 0) + result.get("updates", 0),
                skipped_count=result.get("skips", 0),
                message=f"Servers: {result.get('servers_procesados', 0)}, Errores: {len(result.get('errors', []))}",
                extra_metadata={"result_summary": {
                    "inserts": result.get("inserts", 0),
                    "updates": result.get("updates", 0),
                    "skips": result.get("skips", 0),
                    "errors": len(result.get("errors", []))
                }}
            )
            
            logger.info(
                f"[SYNC-S] Completado: {result.get('inserts', 0)} inserts, "
                f"{result.get('updates', 0)} updates, {result.get('skips', 0)} skips"
            )
        except Exception as e:
            logger.error(f"[SYNC-S] Error: {e}")
            await job_logger.finish_execution(
                log_entry=log_entry,
                status="failed",
                error_detail=str(e)
            )
        finally:
            await lock.release()
    
    async def _run_sync_nightly_comercial_job(self):
        """
        Wrapper async para ejecutar SYNC-N de KPIs comerciales.
        MACROFASE 2: Sincronización nocturna 03:00, ventana 7 días.
        """
        job_config = self.config.jobs.get("sync_nightly_comercial")
        if not job_config or not job_config.enabled:
            logger.debug("SYNC-N deshabilitado por configuración")
            return
        
        # Obtener lock para evitar ejecución concurrente
        lock_manager = get_lock_manager(self.db)
        lock = lock_manager.get_lock("sync_nightly_comercial")
        lock_acquired = await lock.acquire(timeout_seconds=1800)
        
        if not lock_acquired:
            logger.warning("[SYNC-N] No se pudo obtener lock - ya hay una ejecución en progreso")
            return
        
        job_logger = get_job_logger(self.db)
        log_entry = await job_logger.start_execution("sync_nightly_comercial")
        
        try:
            logger.info("[SYNC-N] Iniciando sincronización nocturna de KPIs")
            result = await execute_sync_nightly_comercial(self.db)
            
            # Finalizar log con éxito
            await job_logger.finish_execution(
                log_entry=log_entry,
                status="success" if not result.get("errors") else "partial",
                processed_count=result.get("inserts", 0) + result.get("updates", 0),
                success_count=result.get("inserts", 0) + result.get("updates", 0),
                skipped_count=result.get("skips", 0),
                message=f"Servers: {result.get('servers_procesados', 0)}, Cerrados: {result.get('periodos_cerrados', 0)}",
                extra_metadata={"result_summary": {
                    "inserts": result.get("inserts", 0),
                    "updates": result.get("updates", 0),
                    "skips": result.get("skips", 0),
                    "periodos_cerrados": result.get("periodos_cerrados", 0),
                    "errors": len(result.get("errors", []))
                }}
            )
            
            logger.info(
                f"[SYNC-N] Completado: {result.get('inserts', 0)} inserts, "
                f"{result.get('updates', 0)} updates, {result.get('skips', 0)} skips, "
                f"{result.get('periodos_cerrados', 0)} períodos cerrados"
            )
        except Exception as e:
            logger.error(f"[SYNC-N] Error: {e}")
            await job_logger.finish_execution(
                log_entry=log_entry,
                status="failed",
                error_detail=str(e)
            )
        finally:
            await lock.release()
    
    async def _run_sync_ingresos_incremental_job(self):
        """
        Wrapper async para ejecutar sincronización incremental de Control de Ingresos.
        FASE 2.6: Sincronización cada 15 minutos hacia EDARSAHUB.
        
        - SoftRestaurant: 130° MÉRIDA, CIENFUEGOS, LA ESTELAR
        - MPRO: 130° QRO, ORIGEN
        """
        job_config = self.config.jobs.get("sync_ingresos_incremental")
        if not job_config or not job_config.enabled:
            logger.debug("[SYNC_INGRESOS] Deshabilitado por configuración")
            return
        
        # Obtener lock para evitar ejecución concurrente
        lock_manager = get_lock_manager(self.db)
        lock = lock_manager.get_lock("sync_ingresos_incremental")
        lock_acquired = await lock.acquire(timeout_seconds=600)
        
        if not lock_acquired:
            logger.warning("[SYNC_INGRESOS] No se pudo obtener lock - ya hay una ejecución en progreso")
            return
        
        job_logger = get_job_logger(self.db)
        log_entry = await job_logger.start_execution("sync_ingresos_incremental")
        
        try:
            logger.info("[SYNC_INGRESOS] Iniciando sincronización incremental de Control de Ingresos")
            result = await execute_sync_ingresos_incremental(self.db)
            
            # Finalizar log con éxito
            await job_logger.finish_execution(
                log_entry=log_entry,
                status=result.get("estatus_general", "unknown").lower(),
                processed_count=result.get("total_insertados", 0) + result.get("total_actualizados", 0),
                success_count=result.get("unidades_exitosas", 0),
                skipped_count=result.get("total_omitidos", 0),
                message=f"Unidades: {result.get('unidades_exitosas', 0)}/{result.get('unidades_procesadas', 0)}, "
                        f"Insertados: {result.get('total_insertados', 0)}, "
                        f"Omitidos: {result.get('total_omitidos', 0)}",
                extra_metadata={"result_summary": result}
            )
            
            logger.info(
                f"[SYNC_INGRESOS] Completado: {result.get('unidades_exitosas', 0)}/{result.get('unidades_procesadas', 0)} unidades, "
                f"{result.get('total_insertados', 0)} insertados, "
                f"{result.get('total_omitidos', 0)} omitidos, "
                f"{result.get('duracion_ms', 0)}ms"
            )
        except Exception as e:
            logger.error(f"[SYNC_INGRESOS] Error: {e}")
            await job_logger.finish_execution(
                log_entry=log_entry,
                status="failed",
                error_detail=str(e)
            )
        finally:
            await lock.release()
    
    async def _run_sync_propinas_tpv_incremental_job(self):
        """
        Wrapper async para ejecutar sincronización incremental de Propinas TPV.
        FASE 3.6: Sincronización cada 15 minutos hacia EDARSAHUB.
        
        - SoftRestaurant: 130° MÉRIDA, CIENFUEGOS, LA ESTELAR
        - MPRO: 130° QRO, ORIGEN
        """
        job_config = self.config.jobs.get("sync_propinas_tpv_incremental")
        if not job_config or not job_config.enabled:
            logger.debug("[SYNC_PROPINAS_TPV] Deshabilitado por configuración")
            return
        
        # Obtener lock para evitar ejecución concurrente
        lock_manager = get_lock_manager(self.db)
        lock = lock_manager.get_lock("sync_propinas_tpv_incremental")
        lock_acquired = await lock.acquire(timeout_seconds=600)
        
        if not lock_acquired:
            logger.warning("[SYNC_PROPINAS_TPV] No se pudo obtener lock - ya hay una ejecución en progreso")
            return
        
        job_logger = get_job_logger(self.db)
        log_entry = await job_logger.start_execution("sync_propinas_tpv_incremental")
        
        try:
            logger.info("[SYNC_PROPINAS_TPV] Iniciando sincronización incremental de Propinas TPV")
            result = await execute_sync_propinas_tpv_incremental(self.db)
            
            # Finalizar log con éxito
            await job_logger.finish_execution(
                log_entry=log_entry,
                status=result.get("estatus_general", "unknown").lower(),
                processed_count=result.get("total_insertados", 0) + result.get("total_omitidos", 0),
                success_count=result.get("unidades_exitosas", 0),
                skipped_count=result.get("total_omitidos", 0),
                message=f"Unidades: {result.get('unidades_exitosas', 0)}/{result.get('unidades_procesadas', 0)}, "
                        f"Insertados: {result.get('total_insertados', 0)}, "
                        f"Omitidos: {result.get('total_omitidos', 0)}, "
                        f"Propinas: ${result.get('suma_propinas_tpv', 0):,.2f}",
                extra_metadata={"result_summary": result}
            )
            
            logger.info(
                f"[SYNC_PROPINAS_TPV] Completado: {result.get('unidades_exitosas', 0)}/{result.get('unidades_procesadas', 0)} unidades, "
                f"{result.get('total_insertados', 0)} insertados, "
                f"{result.get('total_omitidos', 0)} omitidos, "
                f"${result.get('suma_propinas_tpv', 0):,.2f} propinas, "
                f"{result.get('duracion_ms', 0)}ms"
            )
        except Exception as e:
            logger.error(f"[SYNC_PROPINAS_TPV] Error: {e}")
            await job_logger.finish_execution(
                log_entry=log_entry,
                status="failed",
                error_detail=str(e)
            )
        finally:
            await lock.release()
    
    async def _run_sync_comercial_v2_job(self):
        """
        Wrapper async para ejecutar sincronización incremental de Comercial V2.
        SUBFASE 4: Sincronización cada 15 minutos hacia EDARSAHUB.
        
        Unidades:
        - SoftRestaurant: 130° MÉRIDA, CIENFUEGOS, LA ESTELAR
        - MPRO: 130° QRO, ORIGEN
        """
        job_config = self.config.jobs.get("sync_comercial_v2")
        if not job_config or not job_config.enabled:
            logger.debug("[SYNC_COMERCIAL_V2] Deshabilitado por configuración")
            return
        
        # Obtener lock para evitar ejecución concurrente
        lock_manager = get_lock_manager(self.db)
        lock = lock_manager.get_lock("sync_comercial_v2")
        lock_acquired = await lock.acquire(timeout_seconds=600)
        
        if not lock_acquired:
            logger.warning("[SYNC_COMERCIAL_V2] No se pudo obtener lock - ya hay una ejecución en progreso")
            return
        
        job_logger = get_job_logger(self.db)
        log_entry = await job_logger.start_execution("sync_comercial_v2")
        
        try:
            logger.info("[SYNC_COMERCIAL_V2] Iniciando sincronización incremental de KPIs comerciales V2")
            result = await execute_sync_comercial_v2(self.db)
            
            # Finalizar log con éxito
            await job_logger.finish_execution(
                log_entry=log_entry,
                status=result.get("estatus_general", "unknown").lower(),
                processed_count=result.get("total_insertados", 0) + result.get("total_actualizados", 0) + result.get("total_omitidos", 0),
                success_count=result.get("unidades_exitosas", 0),
                skipped_count=result.get("total_omitidos", 0),
                message=f"Unidades: {result.get('unidades_exitosas', 0)}/{result.get('unidades_procesadas', 0)}, "
                        f"Insertados: {result.get('total_insertados', 0)}, "
                        f"Actualizados: {result.get('total_actualizados', 0)}, "
                        f"Omitidos: {result.get('total_omitidos', 0)}",
                extra_metadata={"result_summary": result}
            )
            
            logger.info(
                f"[SYNC_COMERCIAL_V2] Completado: {result.get('unidades_exitosas', 0)}/{result.get('unidades_procesadas', 0)} unidades, "
                f"{result.get('total_insertados', 0)} insertados, "
                f"{result.get('total_actualizados', 0)} actualizados, "
                f"{result.get('total_omitidos', 0)} omitidos, "
                f"{result.get('duracion_ms', 0)}ms"
            )
        except Exception as e:
            logger.error(f"[SYNC_COMERCIAL_V2] Error: {e}")
            await job_logger.finish_execution(
                log_entry=log_entry,
                status="failed",
                error_detail=str(e)
            )
        finally:
            await lock.release()
    
    async def _run_sync_comercial_abiertas_v2_job(self):
        """
        Wrapper async para ejecutar sincronización de ventas abiertas Comercial V2.
        P0: Sincronización cada 5 minutos hacia EDARSAHUB.
        
        Unidades:
        - SoftRestaurant: 130° MÉRIDA, CIENFUEGOS, LA ESTELAR
        - MPRO: 130° QRO, ORIGEN
        """
        job_config = self.config.jobs.get("sync_comercial_abiertas_v2")
        if not job_config or not job_config.enabled:
            logger.debug("[SYNC_ABIERTAS_V2] Deshabilitado por configuración")
            return
        
        # Obtener lock para evitar ejecución concurrente
        lock_manager = get_lock_manager(self.db)
        lock = lock_manager.get_lock("sync_comercial_abiertas_v2")
        lock_acquired = await lock.acquire(timeout_seconds=300)
        
        if not lock_acquired:
            logger.warning("[SYNC_ABIERTAS_V2] No se pudo obtener lock - ya hay una ejecución en progreso")
            return
        
        job_logger = get_job_logger(self.db)
        log_entry = await job_logger.start_execution("sync_comercial_abiertas_v2")
        
        try:
            logger.info("[SYNC_ABIERTAS_V2] Iniciando sincronización de ventas abiertas del día")
            result = await execute_sync_comercial_abiertas_v2(self.db)
            
            # Finalizar log con éxito
            await job_logger.finish_execution(
                log_entry=log_entry,
                status=result.get("estatus_general", "unknown").lower(),
                processed_count=result.get("unidades_procesadas", 0),
                success_count=result.get("unidades_exitosas", 0),
                skipped_count=0,
                message=f"Unidades: {result.get('unidades_exitosas', 0)}/{result.get('unidades_procesadas', 0)}, "
                        f"Abiertas: ${result.get('total_ventas_abiertas', 0):,.2f}, "
                        f"Total día: ${result.get('total_estimado_dia', 0):,.2f}",
                extra_metadata={"result_summary": result}
            )
            
            logger.info(
                f"[SYNC_ABIERTAS_V2] Completado: {result.get('unidades_exitosas', 0)}/{result.get('unidades_procesadas', 0)} unidades, "
                f"abiertas=${result.get('total_ventas_abiertas', 0):,.2f}, "
                f"total_dia=${result.get('total_estimado_dia', 0):,.2f}, "
                f"{result.get('duracion_ms', 0)}ms"
            )
        except Exception as e:
            logger.error(f"[SYNC_ABIERTAS_V2] Error: {e}")
            await job_logger.finish_execution(
                log_entry=log_entry,
                status="failed",
                error_detail=str(e)
            )
        finally:
            await lock.release()
    
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
        
        # Job Detector de Pedidos (Automatización Operativa)
        pedidos_config = self.config.jobs.get("pedidos_detector")
        if pedidos_config and pedidos_config.enabled:
            if pedidos_config.cron_expression:
                trigger = CronTrigger.from_crontab(pedidos_config.cron_expression)
            else:
                trigger = IntervalTrigger(seconds=pedidos_config.interval_seconds)
            
            self._scheduler.add_job(
                self._run_pedidos_detector_job,
                trigger=trigger,
                id="pedidos_detector",
                name="Pedidos Detector",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["pedidos_detector"] = pedidos_config
            logger.info(f"Job Pedidos Detector registrado: intervalo={pedidos_config.interval_seconds}s")
        
        # Job Detector de Inventarios (Automatización de Análisis)
        inventarios_config = self.config.jobs.get("inventarios_detector")
        if inventarios_config and inventarios_config.enabled:
            if inventarios_config.cron_expression:
                trigger = CronTrigger.from_crontab(inventarios_config.cron_expression)
            else:
                trigger = IntervalTrigger(seconds=inventarios_config.interval_seconds)
            
            self._scheduler.add_job(
                self._run_inventarios_detector_job,
                trigger=trigger,
                id="inventarios_detector",
                name="Inventarios Detector",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["inventarios_detector"] = inventarios_config
            logger.info(f"Job Inventarios Detector registrado: intervalo={inventarios_config.interval_seconds}s")
        
        # ========================================
        # MACROFASE 2: Jobs de Sincronización KPIs
        # ========================================
        
        # Job SYNC-S (cada 15 minutos)
        sync_s_config = self.config.jobs.get("sync_short_comercial")
        if sync_s_config and sync_s_config.enabled:
            if sync_s_config.cron_expression:
                trigger = CronTrigger.from_crontab(sync_s_config.cron_expression)
            else:
                trigger = IntervalTrigger(seconds=sync_s_config.interval_seconds)
            
            self._scheduler.add_job(
                self._run_sync_short_comercial_job,
                trigger=trigger,
                id="sync_short_comercial",
                name="SYNC-S KPIs Comerciales",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["sync_short_comercial"] = sync_s_config
            logger.info(f"Job SYNC-S registrado: intervalo={sync_s_config.interval_seconds}s")
        
        # Job SYNC-N (nocturno 03:00)
        sync_n_config = self.config.jobs.get("sync_nightly_comercial")
        if sync_n_config and sync_n_config.enabled:
            if sync_n_config.cron_expression:
                trigger = CronTrigger.from_crontab(sync_n_config.cron_expression)
            else:
                trigger = IntervalTrigger(seconds=sync_n_config.interval_seconds)
            
            self._scheduler.add_job(
                self._run_sync_nightly_comercial_job,
                trigger=trigger,
                id="sync_nightly_comercial",
                name="SYNC-N KPIs Comerciales",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["sync_nightly_comercial"] = sync_n_config
            logger.info(f"Job SYNC-N registrado: cron={sync_n_config.cron_expression}")
        
        # ========================================
        # FASE 2.6: Job Sincronización Control de Ingresos
        # ========================================
        
        sync_ingresos_config = self.config.jobs.get("sync_ingresos_incremental")
        if sync_ingresos_config and sync_ingresos_config.enabled:
            if sync_ingresos_config.cron_expression:
                trigger = CronTrigger.from_crontab(sync_ingresos_config.cron_expression)
            else:
                trigger = IntervalTrigger(seconds=sync_ingresos_config.interval_seconds)
            
            self._scheduler.add_job(
                self._run_sync_ingresos_incremental_job,
                trigger=trigger,
                id="sync_ingresos_incremental",
                name="SYNC Control de Ingresos",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["sync_ingresos_incremental"] = sync_ingresos_config
            logger.info(f"Job SYNC_INGRESOS registrado: intervalo={sync_ingresos_config.interval_seconds}s")
        
        # ========================================
        # FASE 3.6: Job Sincronización Propinas TPV
        # ========================================
        
        sync_propinas_config = self.config.jobs.get("sync_propinas_tpv_incremental")
        if sync_propinas_config and sync_propinas_config.enabled:
            if sync_propinas_config.cron_expression:
                trigger = CronTrigger.from_crontab(sync_propinas_config.cron_expression)
            else:
                trigger = IntervalTrigger(seconds=sync_propinas_config.interval_seconds)
            
            self._scheduler.add_job(
                self._run_sync_propinas_tpv_incremental_job,
                trigger=trigger,
                id="sync_propinas_tpv_incremental",
                name="SYNC Propinas TPV",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["sync_propinas_tpv_incremental"] = sync_propinas_config
            logger.info(f"Job SYNC_PROPINAS_TPV registrado: intervalo={sync_propinas_config.interval_seconds}s")
        
        # ========================================
        # SUBFASE 4: Job Sincronización Comercial V2
        # ========================================
        
        sync_comercial_v2_config = self.config.jobs.get("sync_comercial_v2")
        if sync_comercial_v2_config and sync_comercial_v2_config.enabled:
            if sync_comercial_v2_config.cron_expression:
                trigger = CronTrigger.from_crontab(sync_comercial_v2_config.cron_expression)
            else:
                trigger = IntervalTrigger(seconds=sync_comercial_v2_config.interval_seconds)
            
            self._scheduler.add_job(
                self._run_sync_comercial_v2_job,
                trigger=trigger,
                id="sync_comercial_v2",
                name="SYNC Comercial V2",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["sync_comercial_v2"] = sync_comercial_v2_config
            logger.info(f"Job SYNC_COMERCIAL_V2 registrado: intervalo={sync_comercial_v2_config.interval_seconds}s")
        
        # ========================================
        # P0: Job Sincronización Ventas Abiertas V2 (cada 5 min)
        # ========================================
        
        sync_comercial_abiertas_v2_config = self.config.jobs.get("sync_comercial_abiertas_v2")
        if sync_comercial_abiertas_v2_config and sync_comercial_abiertas_v2_config.enabled:
            if sync_comercial_abiertas_v2_config.cron_expression:
                trigger = CronTrigger.from_crontab(sync_comercial_abiertas_v2_config.cron_expression)
            else:
                trigger = IntervalTrigger(seconds=sync_comercial_abiertas_v2_config.interval_seconds)
            
            self._scheduler.add_job(
                self._run_sync_comercial_abiertas_v2_job,
                trigger=trigger,
                id="sync_comercial_abiertas_v2",
                name="SYNC Ventas Abiertas V2",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["sync_comercial_abiertas_v2"] = sync_comercial_abiertas_v2_config
            logger.info(f"Job SYNC_ABIERTAS_V2 registrado: intervalo={sync_comercial_abiertas_v2_config.interval_seconds}s")
    
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
        elif job_id == "auditorias_scheduler":
            await self._run_auditorias_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "pedidos_detector":
            await self._run_pedidos_detector_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "inventarios_detector":
            await self._run_inventarios_detector_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "sync_short_comercial":
            await self._run_sync_short_comercial_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "sync_nightly_comercial":
            await self._run_sync_nightly_comercial_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "sync_ingresos_incremental":
            await self._run_sync_ingresos_incremental_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "sync_propinas_tpv_incremental":
            await self._run_sync_propinas_tpv_incremental_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "sync_comercial_v2":
            await self._run_sync_comercial_v2_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "sync_comercial_abiertas_v2":
            await self._run_sync_comercial_abiertas_v2_job()
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
