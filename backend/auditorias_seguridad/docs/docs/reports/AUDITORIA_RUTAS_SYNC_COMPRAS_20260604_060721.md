# AUDITORÍA RUTAS SYNC COMPRAS
Fecha: Thu Jun  4 06:07:21 UTC 2026

## 1. Rutas actuales en server.py relacionadas con sync/compras
```text
741:@api_router.post("/admin/sync/compras")
775:@api_router.post("/admin/sync/compras/force-unlock")
```

## 2. Referencias a rutas legacy en todo el código
```text
/app/backend/server.py:742:async def admin_sync_compras_manual(
/app/backend/server.py:764:    from core.scheduler.jobs.sync_compras_job import execute_sync_compras
/app/backend/server.py:770:    result = await loop.run_in_executor(None, execute_sync_compras, dry_run)
/app/backend/server.py:776:async def admin_sync_compras_force_unlock(
/app/backend/core/scheduler/jobs/sync_compras_job.py:46:JOB_NAME = "sync_compras"
/app/backend/core/scheduler/jobs/sync_compras_job.py:47:SYNC_INTERVAL_SECONDS = int(os.environ.get("SCHEDULER_SYNC_COMPRAS_INTERVAL_SECONDS", "1800"))  # 30 min default
/app/backend/core/scheduler/jobs/sync_compras_job.py:99:                logger.warning(f"[SYNC-COMPRAS-LOCK] Timeout detectado: {active['SyncRunID']}")
/app/backend/core/scheduler/jobs/sync_compras_job.py:107:                logger.info(f"[SYNC-COMPRAS-LOCK] Lock activo: {active['SyncRunID']} - Abortando")
/app/backend/core/scheduler/jobs/sync_compras_job.py:122:        logger.info(f"[SYNC-COMPRAS-LOCK] 🔒 Lock adquirido: {run_id}")
/app/backend/core/scheduler/jobs/sync_compras_job.py:125:        logger.error(f"[SYNC-COMPRAS-LOCK] Error adquiriendo lock: {e}")
/app/backend/core/scheduler/jobs/sync_compras_job.py:160:        logger.info(f"[SYNC-COMPRAS-LOCK] 🔓 Lock liberado: {run_id} (status={status}, duration={duration}s)")
/app/backend/core/scheduler/jobs/sync_compras_job.py:162:        logger.error(f"[SYNC-COMPRAS-LOCK] Error liberando lock: {e}")
/app/backend/core/scheduler/jobs/sync_compras_job.py:185:            logger.warning(f"[SYNC-COMPRAS] Error de conexión/timeout a {host}: {str(e)[:100]}")
/app/backend/core/scheduler/jobs/sync_compras_job.py:187:        logger.error(f"[SYNC-COMPRAS] Error inesperado en query a {host}: {str(e)[:200]}")
/app/backend/core/scheduler/jobs/sync_compras_job.py:226:                    logger.warning(f"[SYNC-COMPRAS] No se pudo desencriptar password de {row['server_name']}: {e}")
/app/backend/core/scheduler/jobs/sync_compras_job.py:243:        logger.info(f"[SYNC-COMPRAS] Servidores encontrados: {len(servers)}")
/app/backend/core/scheduler/jobs/sync_compras_job.py:247:        logger.error(f"[SYNC-COMPRAS] Error obteniendo servidores: {e}")
/app/backend/core/scheduler/jobs/sync_compras_job.py:255:def execute_sync_compras(dry_run: bool = False) -> Dict[str, Any]:
/app/backend/core/scheduler/jobs/sync_compras_job.py:266:    logger.info(f"[SYNC-COMPRAS] ========== INICIO SINCRONIZACIÓN {run_id} ==========")
/app/backend/core/scheduler/jobs/sync_compras_job.py:290:            logger.warning("[SYNC-COMPRAS] No hay servidores configurados para sincronizar")
/app/backend/core/scheduler/jobs/sync_compras_job.py:303:            logger.info(f"[SYNC-COMPRAS] Procesando: {server_name} ({unidad_codigo})")
/app/backend/core/scheduler/jobs/sync_compras_job.py:306:                logger.warning(f"[SYNC-COMPRAS] Servidor {server_name} sin host/password - Saltando")
/app/backend/core/scheduler/jobs/sync_compras_job.py:349:                    logger.info(f"[SYNC-COMPRAS] ✅ Inventarios {server_name}: {inv_result.get('records_synced', 0)} registros")
/app/backend/core/scheduler/jobs/sync_compras_job.py:353:                    logger.warning(f"[SYNC-COMPRAS] ❌ Inventarios {server_name}: {inv_result.get('error')}")
/app/backend/core/scheduler/jobs/sync_compras_job.py:369:                logger.error(f"[SYNC-COMPRAS] Error sincronizando inventarios {server_name}: {e}")
/app/backend/core/scheduler/jobs/sync_compras_job.py:396:                    logger.info(f"[SYNC-COMPRAS] ✅ Requisiciones {server_name}: {req_result.get('records_synced', 0)} registros")
/app/backend/core/scheduler/jobs/sync_compras_job.py:400:                    logger.warning(f"[SYNC-COMPRAS] ❌ Requisiciones {server_name}: {req_result.get('error')}")
/app/backend/core/scheduler/jobs/sync_compras_job.py:416:                logger.error(f"[SYNC-COMPRAS] Error sincronizando requisiciones {server_name}: {e}")
/app/backend/core/scheduler/jobs/sync_compras_job.py:431:        logger.info("[SYNC-COMPRAS] ========== FIN SINCRONIZACIÓN ==========")
/app/backend/core/scheduler/jobs/sync_compras_job.py:432:        logger.info(f"[SYNC-COMPRAS] Status: {final_status}, Procesados: {total_processed}, Errores: {total_errors}, Duración: {duration}s")
/app/backend/core/scheduler/jobs/sync_compras_job.py:450:        logger.error(f"[SYNC-COMPRAS] Error crítico: {e}")
/app/backend/core/scheduler/jobs/sync_compras_job.py:465:async def run_sync_compras_job():
/app/backend/core/scheduler/jobs/sync_compras_job.py:469:    logger.info("[SYNC-COMPRAS-JOB] Iniciando job programado")
/app/backend/core/scheduler/jobs/sync_compras_job.py:473:    result = await loop.run_in_executor(None, execute_sync_compras, False)
/app/backend/core/scheduler/jobs/sync_compras_job.py:475:    logger.info(f"[SYNC-COMPRAS-JOB] Completado: {result.get('status')}")
/app/backend/core/scheduler/jobs/sync_compras_job.py:484:        "func": run_sync_compras_job,
/app/backend/core/scheduler/jobs/sync_compras_job.py:488:        "enabled": os.environ.get("SCHEDULER_SYNC_COMPRAS_ENABLED", "true").lower() == "true"
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:17:DIFERENCIA CON sync_compras_job.py:
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:18:- sync_compras_job: Sincroniza TODOS los datos cada 30 min (backup completo)
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py:58:# LOCK ANTI-CONCURRENCIA (Más ligero que sync_compras)
```

## 3. Rutas oficiales confirmadas
```text
741:@api_router.post("/admin/sync/compras")
775:@api_router.post("/admin/sync/compras/force-unlock")
```
