# P0 — AUDITORÍA MONGO RESIDUAL (síntesis)  — 2026-06-06

## HALLAZGO CLAVE
NO hay MongoDB vivo. `db = core/mongo_stub.StubDatabase` → todas las ops retornan vacío/no-op,
no persisten ni conectan. `MONGO_URL` no se usa en runtime. Clientes reales bloqueados (no_mongo.py).
El "residual" = CÓDIGO que aún referencia el stub (devuelve vacío).

## CLASIFICACIÓN
A = ya puede morir (sin consumidor real / ya servido por SQL)
B = migrar a SQL (feature aún necesaria; hoy opera sobre vacío)
C = aislar temporalmente (infra: locks/cache/estado; neutralizar hasta impl SQL)

| Colección Mongo (stub) | Archivo | Módulo | Endpoint/Job | Clase |
|---|---|---|---|---|
| kpis_comercial | modules/comercial/kpis_repository.py, historical_kpis_repository.py, cache_service.py | Comercial / Inteligencia | escrito por SYNC-S/N (DESACTIVADOS); tableros leen de EDARSAHUB | **A** |
| inventarios_procesados_auto | core/scheduler/jobs/inventarios_detector_job.py | Inventarios | inventarios_detector (DESACTIVADO) | **A** |
| servers / server_status / server_connection_status | core/server_registry.py | Core / Servidores | registry; tablero ya lee servidores de EDARSAHUB (_get_servers_for_tablero_sql) | **A** (legacy duplicado) |
| pedidos_procesados_automatizacion | modules/compras/repository_pedidos_sql.py | Compras / fase2_operativo | automatizacion_compras_routes/service; pedidos_detector (DESACTIVADO) | **B** (idempotencia de automatización) |
| tareas_operativas_compras | modules/compras/repository_pedidos_sql.py | Compras / fase2_operativo | automatizacion_compras_service | **B** |
| auditoria_compras_bitacora | modules/compras/repository_pedidos_sql.py | Compras | bitácora de auditoría | **B** (auditoría → SQL) |
| manuales_operativos | modules/manuales_operativos/service.py, triggers.py | Manuales Operativos | manuales routes | **B** |
| notifications (+ config) | core/communications/notifications/repository.py, routes.py | Comunicaciones | endpoints de notificaciones | **B** |
| alert_recipients | core/centro_control/recipients_manager.py | Centro de Control | recipients de alertas | **B** |
| propinas_control / propinas_config | modules/finanzas/propinas_tpv/repository.py | Finanzas / Propinas TPV | propinas routes | **B** |
| propinas_cache_resumen/listado/detalle/config | modules/finanzas/propinas_tpv/cache_manager.py | Finanzas / Propinas TPV | cache de propinas | **C** (cache → aislar) |
| scheduler_locks | core/scheduler/locks/distributed_lock.py | Scheduler infra | lock distribuido de jobs | **C** (single-instance: no-op OK; multi-instance → migrar) |
| scheduler_job_log | core/scheduler/job_log (COLLECTION_NAME) | Scheduler infra | log de ejecuciones de jobs | **C** |
| cuadres_z (repository_cuadres_z) | modules/finanzas/repository_cuadres_z.py | Finanzas | cuadres Z | **B** |
| tareas (aggregate) | modules/fase2_operativo/repositories/tarea_repository.py | fase2_operativo | tareas operativas | **B** |
| responsabilidad | modules/fase2_operativo/services/responsabilidad_service.py | fase2_operativo | responsabilidades | **B** |
| documentos | modules/fase2_operativo/routes/documentos_routes.py | fase2_operativo | documentos | **B** |
| config_asignaciones | modules/configuracion/routes/config_asignaciones_routes.py | Configuración | asignaciones | **B** |
| almacenes_sync | modules/configuracion/services/almacenes_sync_service.py | Configuración | sync almacenes | **B/C** |

## NOTA
server.py concentra el mayor volumen (81 find_one / 28 update_one / 13 insert_one) — endpoints legacy
que operan sobre el stub (vacío). Migrar por módulo, no en bloque, validando cada endpoint contra EDARSAHUB.
