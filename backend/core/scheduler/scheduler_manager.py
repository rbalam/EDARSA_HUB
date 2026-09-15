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

import asyncio
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED

from .config import get_scheduler_config
from .locks import get_lock_manager
from .job_logger import get_job_logger
from .jobs.sla_job import create_sla_job
from .jobs.notifications_job import create_notifications_job
from .jobs.catalogo_ampliado_alertas_job import execute_catalogo_ampliado_alertas
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
from .jobs.sync_comercial_abiertas_v2_job import run_sync_comercial_abiertas_v2_manual
# Cava de Socios: Job de envío mensual de estados de cuenta
from .jobs.cava_socios_monthly_job import execute_cava_socios_monthly
# CRM: Jobs de sincronización y seguimiento
from .jobs.crm_sync_job import execute_crm_sync, execute_crm_sla_check, execute_crm_actividades_vencidas
# Vtiger: Job de sincronización bidireccional
from .jobs.vtiger_sync_job import execute_vtiger_sync
# Inteligencia Comercial: Sincronización de ventas desde POS
from .jobs.inteligencia_comercial_sync_job import job_inteligencia_comercial_sync
# NetPay: Sincronización diaria de reportes conciliables
from .jobs.netpay_sync_job import execute_netpay_sync_diario
from .jobs.sync_compras_job import (
    get_job_config as get_sync_compras_job_config,
    run_sync_compras_job,
)
# Notificador de Excepciones Críticas (WhatsApp Twilio + Email SMTP)
from .jobs.alertas_excepciones_job import execute_alertas_excepciones_notifier
# Resumen Diario Ejecutivo de Excepciones (correo matutino)
from .jobs.resumen_diario_excepciones_job import execute_resumen_diario_excepciones
from .jobs.bos_direction_status_job import execute_bos_direction_status

from .persistent_state_repository import SchedulerPersistentStateRepository
logger = logging.getLogger(__name__)



def _normalize_comercial_sync_status(value) -> str:
    """Traduce estados del job Comercial V2 al contrato de JobLogger."""
    normalized = str(value or "").strip().upper()

    return {
        "COMPLETADO": "success",
        "COMPLETED": "success",
        "SUCCESS": "success",
        "PARCIAL": "partial",
        "PARTIAL": "partial",
        "FALLIDO": "failed",
        "FAILED": "failed",
        "ERROR": "failed",
    }.get(normalized, "failed")


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
            db: Dependencia legacy opcional; en modo SQL-only usa StubDatabase
        """
        # Si no se pasa db, usar StubDatabase para compatibilidad legacy
        if db is None:
            from core.mongo_stub import get_stub_database
            db = get_stub_database()
            logger.info("[SCHEDULER] __init__ Usando StubDatabase (auto)")
        
        logger.debug(f"[SCHEDULER] __init__ llamado con db tipo: {type(db).__name__}")
        
        # Evitar re-inicialización completa pero actualizar db si es mejor
        if SchedulerManager._initialized and hasattr(self, '_scheduler') and self._scheduler is not None:
            # Siempre actualizar db si self.db es None
            if not hasattr(self, 'db') or self.db is None:
                self.db = db
                logger.info(f"[SCHEDULER] Actualizado db reference a: {type(db).__name__}")
            return
        
        # Detectar si es StubDatabase
        is_stub = hasattr(db, '_collections') and db.__class__.__name__ == 'StubDatabase'
        
        # Scheduler SQL-only: StubDatabase conserva compatibilidad con firmas legacy
        if is_stub and not SchedulerManager._initialized:
            logger.info("[SCHEDULER] Inicializando con StubDatabase - MongoDB ELIMINADO")
        
        if not SchedulerManager._initialized:
            self.db = db  # StubDatabase
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

    async def _run_catalogo_ampliado_alertas_job(self):
        job_config = self.config.jobs.get("catalogo_ampliado_alertas")
        if not job_config or not job_config.enabled:
            return
        lock_manager = get_lock_manager(self.db)
        lock = lock_manager.get_lock("catalogo_ampliado_alertas")
        if not await lock.acquire(timeout_seconds=job_config.timeout_seconds):
            logger.warning("[CATALOGO_AMPLIADO_ALERTAS] ejecucion omitida por lock activo")
            return
        job_logger = get_job_logger()
        log_entry = await job_logger.start_execution("catalogo_ampliado_alertas")
        try:
            result = await execute_catalogo_ampliado_alertas(job_config.batch_size)
            await job_logger.finish_execution(
                log_entry=log_entry,
                status="success",
                processed_count=result.get("processed", 0),
                success_count=result.get("processed", 0),
                message=f"planned={result.get('planned', 0)} processed={result.get('processed', 0)}",
                extra_metadata={"external_delivery_authorized": False},
            )
            return result
        except Exception:
            await job_logger.finish_execution(log_entry=log_entry, status="failed", error_detail="Error interno del servidor")
            raise
        finally:
            await lock.release()
    
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

    async def retry_inventario_error_by_id(self, record_id: int) -> Dict[str, Any]:
        """Recuperación administrativa de un único ERROR usando el job canónico."""
        import os

        if os.environ.get("SCHEDULER_INVENTARIOS_EMAIL_ENABLED", "false").lower() == "true":
            return {
                "status": "error",
                "message": "Desactive SCHEDULER_INVENTARIOS_EMAIL_ENABLED antes del canario de recuperación",
            }

        job_config = self.config.jobs.get("inventarios_detector")
        if not job_config or not job_config.enabled:
            return {"status": "error", "message": "inventarios_detector está deshabilitado"}

        job = create_inventarios_detector_job(self.db, job_config)
        return await job.retry_error_by_id(record_id)
    
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
        
        job_logger = get_job_logger()
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
                error_detail="Error interno del servidor"
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
        
        job_logger = get_job_logger()
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
                error_detail="Error interno del servidor"
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
        
        job_logger = get_job_logger()
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
                error_detail="Error interno del servidor"
            )
        finally:
            await lock.release()
    
    async def _run_sync_compras_job(self):
        """Wrapper async para sincronización canónica de Compras."""
        logger.warning("[SYNC_COMPRAS] Ejecución solicitada por scheduler")
        job_config = self.config.jobs.get("sync_compras")
        if not job_config or not job_config.enabled:
            logger.debug("[SYNC_COMPRAS] Deshabilitado por configuración")
            return

        try:
            import asyncio
            result = await run_sync_compras_job()
            logger.warning(
                "[SYNC_COMPRAS] Finalizado: status=%s procesados=%s errores=%s",
                result.get("status"),
                result.get("total_processed"),
                result.get("total_errors"),
            )
        except Exception as e:
            logger.error(f"[SYNC_COMPRAS] Error: {e}")

    async def _run_sync_cxp_facturas_job(self):
        """Wrapper async: sincroniza Cuentas por Pagar hacia dbo.Finanzas_CxP_Sync (canónico)."""
        job_config = self.config.jobs.get("sync_cxp_facturas")
        if not job_config or not job_config.enabled:
            return
        lock_manager = get_lock_manager(self.db)
        lock = lock_manager.get_lock("sync_cxp_facturas")
        if not await lock.acquire(timeout_seconds=600):
            logger.warning("[SYNC_CXP] Lock ocupado - ejecución en progreso")
            return
        job_logger = get_job_logger()
        log_entry = await job_logger.start_execution("sync_cxp_facturas")
        try:
            from .jobs.cxp_sync_job import run_cxp_sync_async
            result = await run_cxp_sync_async(dry_run=False)
            await job_logger.finish_execution(
                log_entry=log_entry,
                status="failed" if result.get("errores") else "success",
                processed_count=result.get("facturas_persistidas", 0),
                success_count=result.get("facturas_persistidas", 0),
                message=f"CxP SR={result.get('softrestaurant')} MPRO={result.get('mpro')} "
                        f"persistidas={result.get('facturas_persistidas')}",
                extra_metadata={"result_summary": result},
            )
            logger.info(f"[SYNC_CXP] Completado: {result.get('facturas_persistidas')} facturas")
        except Exception as e:
            logger.error(f"[SYNC_CXP] Error: {e}")
            await job_logger.finish_execution(log_entry=log_entry, status="failed", error_detail="Error interno del servidor")
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
        
        job_logger = get_job_logger()
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
                error_detail="Error interno del servidor"
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
        
        job_logger = get_job_logger()
        log_entry = await job_logger.start_execution("sync_comercial_v2")
        
        try:
            logger.info("[SYNC_COMERCIAL_V2] Iniciando sincronización incremental de KPIs comerciales V2")
            result = await execute_sync_comercial_v2(self.db)
            
            # Finalizar log con éxito
            await job_logger.finish_execution(
                log_entry=log_entry,
                status=_normalize_comercial_sync_status(
                    result.get("estatus_general")
                ),
                processed_count=result.get("total_insertados", 0) + result.get("total_actualizados", 0) + result.get("total_omitidos", 0),
                success_count=result.get("unidades_exitosas", 0),
                failed_count=(
                    int(result.get("unidades_fallidas", 0) or 0)
                    + int(result.get("detalle_producto_fallidos", 0) or 0)
                ),
                skipped_count=result.get("total_omitidos", 0),
                message=f"Unidades: {result.get('unidades_exitosas', 0)}/{result.get('unidades_procesadas', 0)}, "
                        f"Insertados: {result.get('total_insertados', 0)}, "
                        f"Actualizados: {result.get('total_actualizados', 0)}, "
                        f"Omitidos: {result.get('total_omitidos', 0)}, "
                        f"Detalle OK: {result.get('detalle_producto_exitosos', 0)}, "
                        f"Detalle fallido: {result.get('detalle_producto_fallidos', 0)}, "
                        f"Detalle omitido: {result.get('detalle_producto_omitidos', 0)}",
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
                error_detail="Error interno del servidor"
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
        
        job_logger = get_job_logger()
        log_entry = await job_logger.start_execution("sync_comercial_abiertas_v2")
        
        try:
            logger.info("[SYNC_ABIERTAS_V2] Iniciando sincronización de ventas abiertas del día")
            result = await asyncio.to_thread(
                run_sync_comercial_abiertas_v2_manual
            )
            
            processed_count = int(
                result.get("unidades_procesadas") or 0
            )
            success_count = int(
                result.get("unidades_exitosas") or 0
            )
            failed_count = int(
                result.get("unidades_fallidas") or 0
            )
            result_status = str(
                result.get("status") or ""
            ).upper()

            if result_status == "SKIPPED_LOCKED":
                final_status = "skipped"
                skipped_count = 1
            elif processed_count > 0 and failed_count == 0:
                final_status = "success"
                skipped_count = 0
            elif success_count > 0:
                final_status = "partial"
                skipped_count = 0
            else:
                final_status = "failed"
                skipped_count = 0

            duracion_segundos = float(
                result.get("duracion_segundos") or 0
            )

            await job_logger.finish_execution(
                log_entry=log_entry,
                status=final_status,
                processed_count=processed_count,
                success_count=success_count,
                failed_count=failed_count,
                skipped_count=skipped_count,
                message=(
                    f"Unidades: {success_count}/{processed_count}, "
                    f"Abiertas: ${result.get('total_ventas_abiertas', 0):,.2f}, "
                    f"Total día: ${result.get('total_estimado_dia', 0):,.2f}"
                ),
                extra_metadata={"result_summary": result},
            )

            logger.info(
                "[SYNC_ABIERTAS_V2] Completado: "
                f"status={final_status}, "
                f"{success_count}/{processed_count} unidades, "
                f"abiertas=${result.get('total_ventas_abiertas', 0):,.2f}, "
                f"total_dia=${result.get('total_estimado_dia', 0):,.2f}, "
                f"duracion={duracion_segundos:.3f}s"
            )
        except Exception as e:
            logger.error(f"[SYNC_ABIERTAS_V2] Error: {e}")
            await job_logger.finish_execution(
                log_entry=log_entry,
                status="failed",
                error_detail="Error interno del servidor"
            )
        finally:
            await lock.release()
    
    async def _run_cava_socios_monthly_job(self):
        """
        Wrapper async para ejecutar envío mensual de estados de cuenta de Cava de Socios.
        Programado: 9:00 AM del día 1 de cada mes.
        """
        job_config = self.config.jobs.get("cava_socios_monthly")
        if not job_config or not job_config.enabled:
            logger.debug("[CAVA_MONTHLY] Deshabilitado por configuración")
            return
        
        # Obtener lock para evitar ejecución concurrente
        lock_manager = get_lock_manager(self.db)
        lock = lock_manager.get_lock("cava_socios_monthly")
        lock_acquired = await lock.acquire(timeout_seconds=1800)  # 30 min para envío masivo
        
        if not lock_acquired:
            logger.warning("[CAVA_MONTHLY] No se pudo obtener lock - ya hay una ejecución en progreso")
            return
        
        job_logger = get_job_logger()
        log_entry = await job_logger.start_execution("cava_socios_monthly")
        
        try:
            logger.info("[CAVA_MONTHLY] Iniciando envío mensual de estados de cuenta")
            result = await execute_cava_socios_monthly(self.db)
            
            # Finalizar log con éxito
            await job_logger.finish_execution(
                log_entry=log_entry,
                status=result.get("estatus_general", "unknown").lower(),
                processed_count=result.get("total_enviados", 0) + result.get("total_fallidos", 0),
                success_count=result.get("total_enviados", 0),
                failed_count=result.get("total_fallidos", 0),
                skipped_count=result.get("total_sin_email", 0),
                message=f"Enviados: {result.get('total_enviados', 0)}, "
                        f"Fallidos: {result.get('total_fallidos', 0)}, "
                        f"Sin email: {result.get('total_sin_email', 0)}",
                extra_metadata={"result_summary": result}
            )
            
            logger.info(
                f"[CAVA_MONTHLY] Completado: {result.get('total_enviados', 0)} enviados, "
                f"{result.get('total_fallidos', 0)} fallidos, "
                f"{result.get('total_sin_email', 0)} sin email, "
                f"{result.get('duracion_ms', 0)}ms"
            )
        except Exception as e:
            logger.error(f"[CAVA_MONTHLY] Error: {e}")
            await job_logger.finish_execution(
                log_entry=log_entry,
                status="failed",
                error_detail="Error interno del servidor"
            )
        finally:
            await lock.release()
    
    async def _run_crm_sync_job(self):
        """
        Wrapper async para sincronización con CRMs externos.
        Programado: Cada 30 minutos.
        """
        job_config = self.config.jobs.get("crm_sync")
        if not job_config or not job_config.enabled:
            logger.debug("[CRM_SYNC] Deshabilitado por configuración")
            return
        
        lock_manager = get_lock_manager(self.db)
        lock = lock_manager.get_lock("crm_sync")
        lock_acquired = await lock.acquire(timeout_seconds=600)
        
        if not lock_acquired:
            logger.warning("[CRM_SYNC] No se pudo obtener lock - ya hay una ejecución en progreso")
            return
        
        job_logger = get_job_logger()
        log_entry = await job_logger.start_execution("crm_sync")
        
        try:
            logger.info("[CRM_SYNC] Iniciando sincronización con CRMs externos")
            result = await execute_crm_sync(self.db)
            
            await job_logger.finish_execution(
                log_entry=log_entry,
                status=result.get("estatus_general", "unknown").lower(),
                processed_count=result.get("total_conectores", 0),
                success_count=result.get("conectores_exitosos", 0),
                message=f"Conectores: {result.get('conectores_exitosos', 0)}/{result.get('total_conectores', 0)}, "
                        f"Creados: {result.get('registros_creados', 0)}, "
                        f"Actualizados: {result.get('registros_actualizados', 0)}",
                extra_metadata={"result_summary": result}
            )
            
            logger.info(f"[CRM_SYNC] Completado en {result.get('duracion_ms', 0)}ms")
        except Exception as e:
            logger.error(f"[CRM_SYNC] Error: {e}")
            await job_logger.finish_execution(log_entry=log_entry, status="failed", error_detail="Error interno del servidor")
        finally:
            await lock.release()
    
    async def _run_crm_sla_check_job(self):
        """
        Wrapper async para verificación de SLAs de oportunidades.
        Programado: Cada hora.
        """
        job_config = self.config.jobs.get("crm_sla_check")
        if not job_config or not job_config.enabled:
            logger.debug("[CRM_SLA] Deshabilitado por configuración")
            return
        
        lock_manager = get_lock_manager(self.db)
        lock = lock_manager.get_lock("crm_sla_check")
        lock_acquired = await lock.acquire(timeout_seconds=300)
        
        if not lock_acquired:
            logger.warning("[CRM_SLA] No se pudo obtener lock")
            return
        
        job_logger = get_job_logger()
        log_entry = await job_logger.start_execution("crm_sla_check")
        
        try:
            logger.info("[CRM_SLA] Verificando SLAs de oportunidades")
            result = await execute_crm_sla_check(self.db)
            
            await job_logger.finish_execution(
                log_entry=log_entry,
                status=result.get("estatus_general", "unknown").lower(),
                processed_count=result.get("total_vencidas", 0) + result.get("total_proximas", 0),
                success_count=result.get("triggers_ejecutados", 0),
                message=f"Vencidas: {result.get('total_vencidas', 0)}, "
                        f"Próximas: {result.get('total_proximas', 0)}, "
                        f"Triggers: {result.get('triggers_ejecutados', 0)}",
                extra_metadata={"result_summary": result}
            )
            
            logger.info(f"[CRM_SLA] Completado en {result.get('duracion_ms', 0)}ms")
        except Exception as e:
            logger.error(f"[CRM_SLA] Error: {e}")
            await job_logger.finish_execution(log_entry=log_entry, status="failed", error_detail="Error interno del servidor")
        finally:
            await lock.release()
    
    async def _run_crm_actividades_vencidas_job(self):
        """
        Wrapper async para verificación de actividades vencidas.
        Programado: Cada 15 minutos.
        """
        job_config = self.config.jobs.get("crm_actividades_vencidas")
        if not job_config or not job_config.enabled:
            logger.debug("[CRM_ACT] Deshabilitado por configuración")
            return
        
        lock_manager = get_lock_manager(self.db)
        lock = lock_manager.get_lock("crm_actividades_vencidas")
        lock_acquired = await lock.acquire(timeout_seconds=180)
        
        if not lock_acquired:
            logger.warning("[CRM_ACT] No se pudo obtener lock")
            return
        
        job_logger = get_job_logger()
        log_entry = await job_logger.start_execution("crm_actividades_vencidas")
        
        try:
            logger.info("[CRM_ACT] Verificando actividades vencidas")
            result = await execute_crm_actividades_vencidas(self.db)
            
            await job_logger.finish_execution(
                log_entry=log_entry,
                status=result.get("estatus_general", "unknown").lower(),
                processed_count=result.get("total_vencidas", 0),
                success_count=result.get("notificaciones_creadas", 0),
                message=f"Vencidas: {result.get('total_vencidas', 0)}, "
                        f"Notificaciones: {result.get('notificaciones_creadas', 0)}",
                extra_metadata={"result_summary": result}
            )
            
            logger.info(f"[CRM_ACT] Completado en {result.get('duracion_ms', 0)}ms")
        except Exception as e:
            logger.error(f"[CRM_ACT] Error: {e}")
            await job_logger.finish_execution(log_entry=log_entry, status="failed", error_detail="Error interno del servidor")
        finally:
            await lock.release()
    
    async def _run_vtiger_sync_job(self):
        """
        Wrapper async para sincronización con Vtiger CRM.
        Programado: Cada 15 minutos.
        """
        job_config = self.config.jobs.get("vtiger_sync")
        if not job_config or not job_config.enabled:
            logger.debug("[VTIGER_SYNC] Deshabilitado por configuración")
            return
        
        lock_manager = get_lock_manager(self.db)
        lock = lock_manager.get_lock("vtiger_sync")
        lock_acquired = await lock.acquire(timeout_seconds=300)
        
        if not lock_acquired:
            logger.warning("[VTIGER_SYNC] No se pudo obtener lock - ya hay una ejecución en progreso")
            return
        
        job_logger = get_job_logger()
        log_entry = await job_logger.start_execution("vtiger_sync")
        
        try:
            logger.info("[VTIGER_SYNC] Iniciando sincronización con Vtiger CRM")
            result = await execute_vtiger_sync(self.db)
            
            status = "completed" if result.get("success") else "failed"
            
            await job_logger.finish_execution(
                log_entry=log_entry,
                status=status,
                processed_count=result.get("total_fetched", 0),
                success_count=result.get("total_inserted", 0) + result.get("total_updated", 0),
                message=f"Obtenidos: {result.get('total_fetched', 0)}, "
                        f"Insertados: {result.get('total_inserted', 0)}, "
                        f"Actualizados: {result.get('total_updated', 0)}",
                extra_metadata={"result_summary": result}
            )
            
            logger.info(f"[VTIGER_SYNC] Completado en {result.get('duracion_ms', 0)}ms")
        except Exception as e:
            logger.error(f"[VTIGER_SYNC] Error: {e}")
            await job_logger.finish_execution(log_entry=log_entry, status="failed", error_detail="Error interno del servidor")
        finally:
            await lock.release()
    
    async def _run_economia_sync_job(self):
        """Sincroniza las series económicas activas."""
        job_config = self.config.jobs.get("economia_sync")
        if not job_config or not job_config.enabled:
            logger.debug("[ECONOMIA_SYNC] Deshabilitado por configuración")
            return

        from modules.economia.service import EconomiaService

        lock_manager = get_lock_manager(self.db)
        lock = lock_manager.get_lock("economia_sync")
        lock_acquired = await lock.acquire(
            timeout_seconds=job_config.timeout_seconds
        )

        if not lock_acquired:
            logger.warning(
                "[ECONOMIA_SYNC] No se pudo obtener lock"
            )
            return

        job_logger = get_job_logger()
        log_entry = await job_logger.start_execution(
            "economia_sync"
        )

        procesadas = 0
        exitosas = 0
        errores = []

        try:
            series = EconomiaService.listar_series(
                activo=True,
                limite=job_config.batch_size,
            )

            for serie in series:
                procesadas += 1
                serie_id = serie["id"]

                try:
                    await EconomiaService.sincronizar_serie(
                        serie_id
                    )
                    exitosas += 1
                except Exception as exc:
                    errores.append({
                        "serie_id": serie_id,
                        "error": str(exc),
                    })
                    logger.error(
                        "[ECONOMIA_SYNC] Error serie %s: %s",
                        serie_id,
                        exc,
                    )

            status = (
                "completed"
                if not errores
                else "partial"
            )

            await job_logger.finish_execution(
                log_entry=log_entry,
                status=status,
                processed_count=procesadas,
                success_count=exitosas,
                message=(
                    f"Series procesadas: {procesadas}, "
                    f"exitosas: {exitosas}, "
                    f"errores: {len(errores)}"
                ),
                extra_metadata={
                    "errores_count": len(errores)
                },
            )

        except Exception as exc:
            logger.error("[ECONOMIA_SYNC] Error: %s", exc)
            await job_logger.finish_execution(
                log_entry=log_entry,
                status="failed",
                error_detail=str(exc),
            )
        finally:
            await lock.release()

    async def _run_inteligencia_comercial_sync_job(self):
        """
        Wrapper async para sincronización de Inteligencia Comercial.
        Extrae ventas de SoftRestaurant/MPRO y las consolida en EDARSAHUB.
        Programado: Cada hora (cron: 0 * * * *)
        """
        job_config = self.config.jobs.get("inteligencia_comercial_sync")
        if not job_config or not job_config.enabled:
            logger.debug("[INTELIGENCIA_SYNC] Deshabilitado por configuración")
            return
        
        lock_manager = get_lock_manager(self.db)
        lock = lock_manager.get_lock("inteligencia_comercial_sync")
        lock_acquired = await lock.acquire(timeout_seconds=600)
        
        if not lock_acquired:
            logger.warning("[INTELIGENCIA_SYNC] No se pudo obtener lock - ya hay una ejecución en progreso")
            return
        
        job_logger = get_job_logger()
        log_entry = await job_logger.start_execution("inteligencia_comercial_sync")
        
        try:
            logger.info("[INTELIGENCIA_SYNC] Iniciando sincronización de ventas desde POS")
            
            # Ejecutar el job de sincronización
            result = job_inteligencia_comercial_sync(dias_atras=1)
            
            status = "completed" if not result.get("errores") else "partial"
            
            await job_logger.finish_execution(
                log_entry=log_entry,
                status=status,
                processed_count=result.get("registros_extraidos", 0),
                success_count=result.get("registros_insertados", 0),
                message=f"Unidades: {result.get('unidades_procesadas', 0)}, "
                        f"Extraídos: {result.get('registros_extraidos', 0)}, "
                        f"Insertados: {result.get('registros_insertados', 0)}, "
                        f"KPIs: {result.get('kpis_actualizados', 0)}",
                extra_metadata={"result_summary": result}
            )
            
            logger.info(f"[INTELIGENCIA_SYNC] Completado - {result.get('registros_insertados', 0)} registros insertados")
        except Exception as e:
            logger.error(f"[INTELIGENCIA_SYNC] Error: {e}")
            await job_logger.finish_execution(log_entry=log_entry, status="failed", error_detail="Error interno del servidor")
        finally:
            await lock.release()
    
    async def _run_netpay_sync_diario_job(self):
        """Wrapper async para sincronización diaria NetPay."""
        job_config = self.config.jobs.get("netpay_sync_diario")
        if not job_config or not job_config.enabled:
            logger.debug("[NETPAY_SYNC] Deshabilitado por configuración")
            return

        lock_manager = get_lock_manager(self.db)
        lock = lock_manager.get_lock("netpay_sync_diario")
        lock_acquired = await lock.acquire(timeout_seconds=job_config.timeout_seconds)

        if not lock_acquired:
            logger.warning("[NETPAY_SYNC] No se pudo obtener lock - ya hay una ejecución en progreso")
            return

        job_logger = get_job_logger()
        log_entry = await job_logger.start_execution("netpay_sync_diario")

        try:
            result = await execute_netpay_sync_diario()
            reports = result.get("reports", [])
            success_count = sum(1 for item in reports if item.get("success"))

            await job_logger.finish_execution(
                log_entry=log_entry,
                status="completed" if result.get("success") else "failed",
                processed_count=len(reports),
                success_count=success_count,
                message=result.get("message", "NetPay sync diario finalizado"),
                extra_metadata={"result_summary": result}
            )
        except Exception as e:
            logger.error(f"[NETPAY_SYNC] Error: {e}")
            await job_logger.finish_execution(log_entry=log_entry, status="failed", error_detail="Error interno del servidor")
        finally:
            await lock.release()

    async def _run_alertas_excepciones_notifier_job(self):
        """Wrapper async: notifica excepciones críticas nuevas por WhatsApp + Email."""
        job_config = self.config.jobs.get("alertas_excepciones_notifier")
        if not job_config or not job_config.enabled:
            logger.debug("[ALERTAS_EXC] Deshabilitado por configuración")
            return

        lock_manager = get_lock_manager(self.db)
        lock = lock_manager.get_lock("alertas_excepciones_notifier")
        if not await lock.acquire(timeout_seconds=job_config.timeout_seconds):
            logger.warning("[ALERTAS_EXC] Lock ocupado - ejecución en progreso")
            return

        job_logger = get_job_logger()
        log_entry = await job_logger.start_execution("alertas_excepciones_notifier")
        try:
            result = await execute_alertas_excepciones_notifier()
            await job_logger.finish_execution(
                log_entry=log_entry,
                status="success" if not result.get("errores") else "partial",
                processed_count=result.get("total_evaluadas", 0),
                success_count=result.get("notificadas", 0),
                message=f"Nuevas: {result.get('nuevas', 0)}, Notificadas: {result.get('notificadas', 0)}, "
                        f"Email: {result.get('email_enviado')}, WhatsApp: {result.get('whatsapp_enviado')}",
                extra_metadata={"result_summary": result},
            )
            logger.info(f"[ALERTAS_EXC] Completado: {result.get('notificadas', 0)} notificadas")
        except Exception as e:
            logger.error(f"[ALERTAS_EXC] Error: {e}")
            await job_logger.finish_execution(log_entry=log_entry, status="failed", error_detail="Error interno del servidor")
        finally:
            await lock.release()

    async def _run_resumen_diario_excepciones_job(self):
        """Wrapper async: envía el resumen diario ejecutivo de excepciones por correo."""
        job_config = self.config.jobs.get("resumen_diario_excepciones")
        if not job_config or not job_config.enabled:
            logger.debug("[RESUMEN_DIARIO_EXC] Deshabilitado por configuración")
            return

        lock_manager = get_lock_manager(self.db)
        lock = lock_manager.get_lock("resumen_diario_excepciones")
        if not await lock.acquire(timeout_seconds=job_config.timeout_seconds):
            logger.warning("[RESUMEN_DIARIO_EXC] Lock ocupado - ejecución en progreso")
            return

        job_logger = get_job_logger()
        log_entry = await job_logger.start_execution("resumen_diario_excepciones")
        try:
            result = await execute_resumen_diario_excepciones()
            await job_logger.finish_execution(
                log_entry=log_entry,
                status="success" if not result.get("errores") else "partial",
                processed_count=result.get("total", 0),
                success_count=result.get("unidades", 0),
                message=f"Total: {result.get('total', 0)}, Unidades: {result.get('unidades', 0)}, "
                        f"Email: {result.get('email_enviado')}",
                extra_metadata={"result_summary": result},
            )
            logger.info(f"[RESUMEN_DIARIO_EXC] Completado: {result.get('total', 0)} excepciones")
        except Exception as e:
            logger.error(f"[RESUMEN_DIARIO_EXC] Error: {e}")
            await job_logger.finish_execution(log_entry=log_entry, status="failed", error_detail="Error interno del servidor")
        finally:
            await lock.release()

    async def _run_bos_direction_status_job(self):
        """Publica el status vivo BOS de Direccion mediante el ciclo certificado."""
        job_config = self.config.jobs.get("bos_direction_status")
        if not job_config or not job_config.enabled:
            logger.debug("[BOS_DIRECTION_STATUS] Deshabilitado por configuración")
            return

        lock_manager = get_lock_manager(self.db)
        lock = lock_manager.get_lock("bos_direction_status")
        if not await lock.acquire(timeout_seconds=job_config.timeout_seconds):
            logger.warning("[BOS_DIRECTION_STATUS] Lock ocupado - ejecución en progreso")
            return

        job_logger = get_job_logger()
        log_entry = await job_logger.start_execution("bos_direction_status")
        try:
            result = await asyncio.to_thread(execute_bos_direction_status)
            snapshot = result["snapshot"]
            await job_logger.finish_execution(
                log_entry=log_entry,
                status="success",
                processed_count=int(snapshot.get("total_gates") or 0),
                success_count=int(snapshot.get("certified_gates") or 0),
                message=(
                    f"Avance BOS: {snapshot.get('percent_complete', 0)}%, "
                    f"certified={snapshot.get('certified', False)}"
                ),
                extra_metadata={
                    "generated_at_utc": snapshot.get("generated_at_utc"),
                    "history_file": result.get("history_file"),
                    "latest_file": result.get("latest_file"),
                },
            )
            logger.info("[BOS_DIRECTION_STATUS] Snapshot publicado: %s", result.get("latest_file"))
        except Exception as e:
            logger.error("[BOS_DIRECTION_STATUS] Error: %s", e)
            await job_logger.finish_execution(
                log_entry=log_entry,
                status="failed",
                error_detail="Error interno del servidor",
            )
            raise
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

        catalogo_alertas_config = self.config.jobs.get("catalogo_ampliado_alertas")
        if catalogo_alertas_config and catalogo_alertas_config.enabled:
            trigger = IntervalTrigger(seconds=catalogo_alertas_config.interval_seconds)
            self._scheduler.add_job(
                self._run_catalogo_ampliado_alertas_job,
                trigger=trigger,
                id="catalogo_ampliado_alertas",
                name="Catalogo Ampliado - Alertas",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )
            self._jobs["catalogo_ampliado_alertas"] = catalogo_alertas_config
            logger.info(f"Job Catalogo Ampliado Alertas registrado: intervalo={catalogo_alertas_config.interval_seconds}s")
        
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
        # Compras: Job Sincronización Integral
        # ========================================
        sync_compras_config = self.config.jobs.get("sync_compras")
        sync_compras_job_definition = get_sync_compras_job_config()
        if (
            sync_compras_config
            and sync_compras_config.enabled
            and sync_compras_job_definition.get("enabled", False)
        ):
            if sync_compras_config.cron_expression:
                trigger = CronTrigger.from_crontab(sync_compras_config.cron_expression)
            else:
                trigger = IntervalTrigger(seconds=sync_compras_config.interval_seconds)

            self._scheduler.add_job(
                self._run_sync_compras_job,
                trigger=trigger,
                id="sync_compras",
                name="SYNC Compras Integral",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )
            self._jobs["sync_compras"] = sync_compras_config
            logger.warning(
                "[SYNC_COMPRAS] Job registrado: intervalo=%ss run_inicial=none",
                sync_compras_config.interval_seconds,
            )

        # ========================================
        # CxP: Job Sincronización Cuentas por Pagar (canónico)
        # ========================================
        sync_cxp_config = self.config.jobs.get("sync_cxp_facturas")
        if sync_cxp_config and sync_cxp_config.enabled:
            if sync_cxp_config.cron_expression:
                trigger = CronTrigger.from_crontab(sync_cxp_config.cron_expression)
            else:
                trigger = IntervalTrigger(seconds=sync_cxp_config.interval_seconds)
            self._scheduler.add_job(
                self._run_sync_cxp_facturas_job,
                trigger=trigger,
                id="sync_cxp_facturas",
                name="SYNC Cuentas por Pagar",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["sync_cxp_facturas"] = sync_cxp_config
            logger.info(f"Job SYNC_CXP registrado: cron={sync_cxp_config.cron_expression}")

        
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
            
            # Usar la configuración canónica del job.
            self._scheduler.add_job(
                self._run_sync_comercial_abiertas_v2_job,
                trigger=trigger,
                id="sync_comercial_abiertas_v2",
                name="SYNC Ventas Abiertas V2",
                replace_existing=True,
                max_instances=sync_comercial_abiertas_v2_config.max_instances,
                coalesce=sync_comercial_abiertas_v2_config.coalesce,
                misfire_grace_time=sync_comercial_abiertas_v2_config.misfire_grace_time
            )
            self._jobs["sync_comercial_abiertas_v2"] = sync_comercial_abiertas_v2_config
            logger.info(
                "Job SYNC_ABIERTAS_V2 registrado: "
                f"intervalo={sync_comercial_abiertas_v2_config.interval_seconds}s, "
                f"max_instances={sync_comercial_abiertas_v2_config.max_instances}, "
                f"coalesce={sync_comercial_abiertas_v2_config.coalesce}, "
                f"misfire_grace_time={sync_comercial_abiertas_v2_config.misfire_grace_time}s"
            )
        
        # ========================================
        # Cava de Socios: Envío mensual de estados de cuenta
        # ========================================
        
        cava_monthly_config = self.config.jobs.get("cava_socios_monthly")
        if cava_monthly_config and cava_monthly_config.enabled:
            if cava_monthly_config.cron_expression:
                trigger = CronTrigger.from_crontab(cava_monthly_config.cron_expression)
            else:
                trigger = IntervalTrigger(seconds=cava_monthly_config.interval_seconds)
            
            self._scheduler.add_job(
                self._run_cava_socios_monthly_job,
                trigger=trigger,
                id="cava_socios_monthly",
                name="Cava Socios - Estado Cuenta Mensual",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["cava_socios_monthly"] = cava_monthly_config
            logger.info(f"Job CAVA_MONTHLY registrado: cron={cava_monthly_config.cron_expression}")
        
        # ========================================
        # CRM: Sincronización con CRMs externos (cada 30 min)
        # ========================================
        
        crm_sync_config = self.config.jobs.get("crm_sync")
        if crm_sync_config and crm_sync_config.enabled:
            trigger = IntervalTrigger(seconds=crm_sync_config.interval_seconds)
            
            self._scheduler.add_job(
                self._run_crm_sync_job,
                trigger=trigger,
                id="crm_sync",
                name="CRM - Sincronización Externa",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["crm_sync"] = crm_sync_config
            logger.info(f"Job CRM_SYNC registrado: intervalo={crm_sync_config.interval_seconds}s")
        
        # ========================================
        # CRM: Verificación de SLAs (cada hora)
        # ========================================
        
        crm_sla_config = self.config.jobs.get("crm_sla_check")
        if crm_sla_config and crm_sla_config.enabled:
            trigger = IntervalTrigger(seconds=crm_sla_config.interval_seconds)
            
            self._scheduler.add_job(
                self._run_crm_sla_check_job,
                trigger=trigger,
                id="crm_sla_check",
                name="CRM - Verificación SLA",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["crm_sla_check"] = crm_sla_config
            logger.info(f"Job CRM_SLA_CHECK registrado: intervalo={crm_sla_config.interval_seconds}s")
        
        # ========================================
        # CRM: Actividades vencidas (cada 15 min)
        # ========================================
        
        crm_act_config = self.config.jobs.get("crm_actividades_vencidas")
        if crm_act_config and crm_act_config.enabled:
            trigger = IntervalTrigger(seconds=crm_act_config.interval_seconds)
            
            self._scheduler.add_job(
                self._run_crm_actividades_vencidas_job,
                trigger=trigger,
                id="crm_actividades_vencidas",
                name="CRM - Actividades Vencidas",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["crm_actividades_vencidas"] = crm_act_config
            logger.info(f"Job CRM_ACTIVIDADES registrado: intervalo={crm_act_config.interval_seconds}s")
        
        # ========================================
        # Vtiger: Sincronización Bidireccional
        # ========================================
        
        vtiger_sync_config = self.config.jobs.get("vtiger_sync")
        if vtiger_sync_config and vtiger_sync_config.enabled:
            trigger = IntervalTrigger(seconds=vtiger_sync_config.interval_seconds)
            
            self._scheduler.add_job(
                self._run_vtiger_sync_job,
                trigger=trigger,
                id="vtiger_sync",
                name="Vtiger CRM - Sincronización",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["vtiger_sync"] = vtiger_sync_config
            logger.info(f"Job VTIGER_SYNC registrado: intervalo={vtiger_sync_config.interval_seconds}s")
        
        # ========================================
        # Inteligencia Comercial: Sincronización POS
        # ========================================
        
        inteligencia_sync_config = self.config.jobs.get("inteligencia_comercial_sync")
        if inteligencia_sync_config and inteligencia_sync_config.enabled:
            # Usar CronTrigger si está definido, sino IntervalTrigger
            if inteligencia_sync_config.cron_expression:
                trigger = CronTrigger.from_crontab(inteligencia_sync_config.cron_expression)
            else:
                trigger = IntervalTrigger(seconds=inteligencia_sync_config.interval_seconds)
            
            self._scheduler.add_job(
                self._run_inteligencia_comercial_sync_job,
                trigger=trigger,
                id="inteligencia_comercial_sync",
                name="Inteligencia Comercial - Sync Sales",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["inteligencia_comercial_sync"] = inteligencia_sync_config
            logger.info(f"Job INTELIGENCIA_COMERCIAL_SYNC registrado: cron={inteligencia_sync_config.cron_expression or 'interval'}")

        
        # ========================================
        # Economía WorldClass
        # ========================================
        economia_config = self.config.jobs.get("economia_sync")
        if economia_config and economia_config.enabled:
            if economia_config.cron_expression:
                trigger = CronTrigger.from_crontab(
                    economia_config.cron_expression
                )
            else:
                trigger = IntervalTrigger(
                    seconds=economia_config.interval_seconds
                )

            self._scheduler.add_job(
                self._run_economia_sync_job,
                trigger=trigger,
                id="economia_sync",
                name="Economía - Sync Indicadores",
                replace_existing=True,
                max_instances=economia_config.max_instances,
                coalesce=economia_config.coalesce,
            )
            self._jobs["economia_sync"] = economia_config
            logger.info(
                "Job ECONOMIA_SYNC registrado"
            )

        # ========================================
        # NetPay: Sincronización diaria conciliable
        # ========================================
        netpay_sync_config = self.config.jobs.get("netpay_sync_diario")
        if netpay_sync_config and netpay_sync_config.enabled:
            if netpay_sync_config.cron_expression:
                trigger = CronTrigger.from_crontab(netpay_sync_config.cron_expression)
            else:
                trigger = IntervalTrigger(seconds=netpay_sync_config.interval_seconds)

            self._scheduler.add_job(
                self._run_netpay_sync_diario_job,
                trigger=trigger,
                id="netpay_sync_diario",
                name="NetPay - Sync Diario",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["netpay_sync_diario"] = netpay_sync_config
            logger.info(f"Job NETPAY_SYNC registrado: cron={netpay_sync_config.cron_expression or 'interval'}")

        # ========================================
        # Notificador de Excepciones Críticas (WhatsApp + Email)
        # ========================================
        alertas_exc_config = self.config.jobs.get("alertas_excepciones_notifier")
        if alertas_exc_config and alertas_exc_config.enabled:
            if alertas_exc_config.cron_expression:
                trigger = CronTrigger.from_crontab(alertas_exc_config.cron_expression)
            else:
                trigger = IntervalTrigger(seconds=alertas_exc_config.interval_seconds)

            self._scheduler.add_job(
                self._run_alertas_excepciones_notifier_job,
                trigger=trigger,
                id="alertas_excepciones_notifier",
                name="Notificador Excepciones Críticas",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["alertas_excepciones_notifier"] = alertas_exc_config
            logger.info(f"Job ALERTAS_EXC registrado: intervalo={alertas_exc_config.interval_seconds}s")

        # ========================================
        # Resumen Diario Ejecutivo de Excepciones (correo matutino)
        # ========================================
        resumen_diario_config = self.config.jobs.get("resumen_diario_excepciones")
        if resumen_diario_config and resumen_diario_config.enabled:
            if resumen_diario_config.cron_expression:
                trigger = CronTrigger.from_crontab(resumen_diario_config.cron_expression)
            else:
                trigger = IntervalTrigger(seconds=resumen_diario_config.interval_seconds)

            self._scheduler.add_job(
                self._run_resumen_diario_excepciones_job,
                trigger=trigger,
                id="resumen_diario_excepciones",
                name="Resumen Diario de Excepciones",
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            self._jobs["resumen_diario_excepciones"] = resumen_diario_config
            logger.info(f"Job RESUMEN_DIARIO_EXC registrado: cron={resumen_diario_config.cron_expression}")

        # ========================================
        # BOS Direccion: Status vivo recurrente
        # ========================================
        bos_direction_config = self.config.jobs.get("bos_direction_status")
        if bos_direction_config and bos_direction_config.enabled:
            trigger = IntervalTrigger(seconds=bos_direction_config.interval_seconds)
            self._scheduler.add_job(
                self._run_bos_direction_status_job,
                trigger=trigger,
                id="bos_direction_status",
                name="BOS Direccion - Status Vivo",
                replace_existing=True,
                max_instances=bos_direction_config.max_instances,
                coalesce=bos_direction_config.coalesce,
                misfire_grace_time=bos_direction_config.misfire_grace_time,
            )
            self._jobs["bos_direction_status"] = bos_direction_config
            logger.info(
                "Job BOS_DIRECTION_STATUS registrado: intervalo=%ss",
                bos_direction_config.interval_seconds,
            )
    
    async def start(self):
        """Inicia el scheduler."""
        if not self.config.enabled:
            logger.warning("Scheduler deshabilitado por configuración")
            return
        
        if self._running:
            logger.warning("Scheduler ya está corriendo")
            return
        
        # Asegurar índices
        lock_manager = get_lock_manager(self.db)
        await lock_manager.ensure_indexes()
        
        job_logger = get_job_logger()
        await job_logger.ensure_indexes()
        
        # Limpiar locks expirados
        await lock_manager.cleanup_expired()
        
        # Registrar jobs
        self.register_jobs()

        # Restaurar pausas administrativas persistentes antes de iniciar.
        # Fail-closed: si SQL no puede entregar el estado persistente,
        # el scheduler no debe arrancar ignorando decisiones administrativas.
        paused_job_ids = (
            SchedulerPersistentStateRepository.get_paused_job_ids()
        )

        registered_job_ids = {
            job.id
            for job in self._scheduler.get_jobs()
        }

        unknown_paused_job_ids = sorted(
            set(paused_job_ids) - registered_job_ids
        )

        if unknown_paused_job_ids:
            logger.warning(
                "Estados de pausa persistentes sin job runtime registrado: %s",
                unknown_paused_job_ids,
            )

        for job_id in paused_job_ids:
            if job_id not in registered_job_ids:
                continue

            self._scheduler.pause_job(job_id)

            logger.info(
                "Pausa administrativa restaurada al iniciar: %s",
                job_id,
            )

        # Iniciar scheduler
        self._scheduler.start()
        self._running = True

        logger.warning("Scheduler iniciado con %s jobs", len(self._jobs))
    
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
        elif job_id == "catalogo_ampliado_alertas":
            await self._run_catalogo_ampliado_alertas_job()
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
        elif job_id == "sync_compras":
            await self._run_sync_compras_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "sync_cxp_facturas":
            await self._run_sync_cxp_facturas_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "sync_comercial_v2":
            await self._run_sync_comercial_v2_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "sync_comercial_abiertas_v2":
            await self._run_sync_comercial_abiertas_v2_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "cava_socios_monthly":
            await self._run_cava_socios_monthly_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "crm_sync":
            await self._run_crm_sync_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "crm_sla_check":
            await self._run_crm_sla_check_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "crm_actividades_vencidas":
            await self._run_crm_actividades_vencidas_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "vtiger_sync":
            await self._run_vtiger_sync_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "inteligencia_comercial_sync":
            await self._run_inteligencia_comercial_sync_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "economia_sync":
            await self._run_economia_sync_job()
            return {"status": "executed", "job_id": job_id}
        elif job_id == "netpay_sync_diario":
            await self._run_netpay_sync_diario_job()
            return {"status": "executed", "job_id": job_id}
        else:
            return {"status": "error", "message": f"Job desconocido: {job_id}"}
    
    def pause_job(self, job_id: str) -> bool:
        """Pausa un job y persiste la decisión administrativa."""
        if self._scheduler is None:
            return False

        try:
            self._scheduler.pause_job(job_id)

            try:
                persisted = SchedulerPersistentStateRepository.set_paused(
                    job_id,
                    True,
                )
            except Exception:
                try:
                    self._scheduler.resume_job(job_id)
                except Exception:
                    logger.exception(
                        "No fue posible revertir pausa runtime de %s",
                        job_id,
                    )
                raise

            if not persisted:
                try:
                    self._scheduler.resume_job(job_id)
                except Exception:
                    logger.exception(
                        "No fue posible revertir pausa runtime de %s",
                        job_id,
                    )

                logger.error(
                    "No existe registro persistente para job %s",
                    job_id,
                )
                return False

            logger.info("Job pausado administrativamente: %s", job_id)
            return True

        except Exception as e:
            logger.error("Error pausando job %s: %s", job_id, e)
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """Reanuda un job y elimina la pausa administrativa persistente."""
        if self._scheduler is None:
            return False

        try:
            self._scheduler.resume_job(job_id)

            try:
                persisted = SchedulerPersistentStateRepository.set_paused(
                    job_id,
                    False,
                )
            except Exception:
                try:
                    self._scheduler.pause_job(job_id)
                except Exception:
                    logger.exception(
                        "No fue posible revertir reanudación runtime de %s",
                        job_id,
                    )
                raise

            if not persisted:
                try:
                    self._scheduler.pause_job(job_id)
                except Exception:
                    logger.exception(
                        "No fue posible revertir reanudación runtime de %s",
                        job_id,
                    )

                logger.error(
                    "No existe registro persistente para job %s",
                    job_id,
                )
                return False

            logger.info("Job reanudado administrativamente: %s", job_id)
            return True

        except Exception as e:
            logger.error("Error reanudando job %s: %s", job_id, e)
            return False


# =============================================================================
# FUNCIONES DE CONVENIENCIA
# =============================================================================

_scheduler_manager: Optional[SchedulerManager] = None


def get_scheduler_manager(db=None) -> SchedulerManager:
    """
    Obtiene instancia del scheduler manager.
    
    Scheduler SQL-only: si no recibe dependencia, usa StubDatabase para compatibilidad legacy.
    """
    global _scheduler_manager
    
    # Si no se pasa db, usar StubDatabase para compatibilidad legacy
    if db is None:
        from core.mongo_stub import get_stub_database
        db = get_stub_database()
    
    if _scheduler_manager is None:
        logger.info("[SCHEDULER] Creando SchedulerManager")
        _scheduler_manager = SchedulerManager(db)
    elif _scheduler_manager.db is None:
        # Si ya existe pero con db=None, actualizar
        _scheduler_manager.db = db
        logger.info("[SCHEDULER] Actualizado db reference en SchedulerManager existente")
    return _scheduler_manager


async def start_scheduler(db) -> SchedulerManager:
    """
    Inicia el scheduler.
    
    Acepta db=None para modo SQL-only.
    """
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
