# AUDITORÍA MONGO — RUTAS ACTIVAS

Fecha: 2026-06-05 00:02:31

Objetivo: identificar si archivos con MongoDB son consumidos por rutas/endpoints activos.

## Archivos con MongoDB detectados

Total: 45

- `backend/core/auditoria.py`
- `backend/core/auth/user_repository_sql.py`
- `backend/core/centro_control/recipients_manager.py`
- `backend/core/communications/scripts/__init__.py`
- `backend/core/connection_resolver.py`
- `backend/core/db.py`
- `backend/core/health_checker.py`
- `backend/core/rbac/middleware.py`
- `backend/core/rbac/routes.py`
- `backend/core/rbac_helper.py`
- `backend/init_queries.py`
- `backend/modules/catalogos/__init__.py`
- `backend/modules/comercial/historical_kpis_repository.py`
- `backend/modules/configuracion/routes/config_asignaciones_routes.py`
- `backend/modules/fase2_operativo/db_utils.py`
- `backend/modules/fase2_operativo/scripts/init_collections_fase2a.py`
- `backend/modules/fase2_operativo/scripts/init_notificaciones.py`
- `backend/modules/finanzas/propinas_tpv/cache_manager.py`
- `backend/modules/finanzas/propinas_tpv/repository.py`
- `backend/modules/finanzas/propinas_tpv/routes.py`
- `backend/modules/finanzas/propinas_tpv/routes_sql.py`
- `backend/modules/finanzas/propinas_tpv/service.py`
- `backend/modules/finanzas/propinas_tpv/service_sql.py`
- `backend/modules/finanzas/repository_cuadres_z.py`
- `backend/modules/manuales_operativos/service.py`
- `backend/modules/manuales_operativos/triggers.py`
- `backend/scripts/audit_mongo_active_routes.py`
- `backend/scripts/audit_mongo_legacy.py`
- `backend/scripts/carga_historica_fase23.py`
- `backend/scripts/encrypt_core_server_secrets.py`
- `backend/scripts/encrypt_existing_server_secrets.py`
- `backend/scripts/precheck_conectividad.py`
- `backend/scripts/reconcile_servers_sql_mongo.py`
- `backend/scripts/run_historical_load_24_months.py`
- `backend/scripts/run_historical_load_compras.py`
- `backend/scripts/run_historical_load_finanzas.py`
- `backend/scripts/setup_kpis_indexes.py`
- `backend/scripts/validar_post_carga.py`
- `backend/tests/test_bloque2_paridad.py`
- `backend/tests/test_bloque3_paridad_mpro.py`
- `backend/tests/test_comercial_adapters.py`
- `backend/tests/test_e2e_flujo_completo.py`
- `backend/tests/test_macrofase2_kpis.py`
- `backend/tests/test_migracion_servidores_sql.py`
- `backend/tests/test_simulacion_controlada.py`

## Archivos con rutas activas

Total: 73


## Cruce: Rutas que importan archivos Mongo

| Archivo Mongo | Ruta activa consumidora | Riesgo |
|---|---|---|
| `backend/modules/fase2_operativo/db_utils.py` | `backend/modules/fase2_operativo/routes/sla_routes.py` | ALTO |
| `backend/modules/fase2_operativo/db_utils.py` | `backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py` | ALTO |
| `backend/modules/fase2_operativo/db_utils.py` | `backend/modules/fase2_operativo/routes/tarea_routes.py` | ALTO |
| `backend/modules/fase2_operativo/db_utils.py` | `backend/modules/fase2_operativo/routes/configuracion_routes.py` | ALTO |
| `backend/modules/fase2_operativo/db_utils.py` | `backend/modules/fase2_operativo/routes/cargos_routes.py` | ALTO |
| `backend/modules/fase2_operativo/db_utils.py` | `backend/modules/fase2_operativo/routes/responsabilidad_routes.py` | ALTO |
| `backend/modules/fase2_operativo/db_utils.py` | `backend/modules/fase2_operativo/routes/notificaciones_routes.py` | ALTO |
| `backend/modules/fase2_operativo/db_utils.py` | `backend/modules/fase2_operativo/routes/justificacion_routes.py` | ALTO |
| `backend/modules/fase2_operativo/db_utils.py` | `backend/modules/fase2_operativo/routes/workflow_routes.py` | ALTO |
| `backend/modules/fase2_operativo/db_utils.py` | `backend/modules/fase2_operativo/routes/auditoria_programada_routes.py` | ALTO |
| `backend/modules/fase2_operativo/db_utils.py` | `backend/modules/fase2_operativo/routes/documentos_routes.py` | ALTO |
| `backend/modules/fase2_operativo/db_utils.py` | `backend/modules/fase2_operativo/routes/auditoria_routes.py` | ALTO |
| `backend/modules/fase2_operativo/db_utils.py` | `backend/modules/fase2_operativo/routes/dashboard_routes.py` | ALTO |
| `backend/modules/configuracion/routes/config_asignaciones_routes.py` | `backend/server.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/service.py` | `backend/server.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/service.py` | `backend/modules/comercial/routes.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/service.py` | `backend/modules/rh/routes.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/service.py` | `backend/modules/rh/importador/routes.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/service.py` | `backend/modules/consultas_sql/routes.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/service.py` | `backend/modules/catalogos/routes.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/service.py` | `backend/modules/auth/routes.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/service.py` | `backend/modules/crm/routes.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/service.py` | `backend/modules/finanzas/propinas_tpv/routes.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/service.py` | `backend/modules/cava_socios/routes.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/service.py` | `backend/modules/manuales_operativos/routes.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/service.py` | `backend/core/rbac/routes.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/service.py` | `backend/core/rbac/middleware.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/repository.py` | `backend/server.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/repository.py` | `backend/modules/comercial/routes.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/repository.py` | `backend/modules/api_connections/routes.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/repository.py` | `backend/modules/costos_margenes/routes.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/repository.py` | `backend/modules/rh/importador/routes.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/repository.py` | `backend/modules/consultas_sql/routes.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/repository.py` | `backend/modules/finanzas/cuentas_por_pagar.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/repository.py` | `backend/api/catalogos_sistemas.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/repository.py` | `backend/core/communications/routes.py` | ALTO |
| `backend/modules/finanzas/propinas_tpv/routes.py` | `backend/server.py` | ALTO |
| `backend/modules/manuales_operativos/service.py` | `backend/server.py` | ALTO |
| `backend/modules/manuales_operativos/service.py` | `backend/modules/comercial/routes.py` | ALTO |
| `backend/modules/manuales_operativos/service.py` | `backend/modules/rh/routes.py` | ALTO |
| `backend/modules/manuales_operativos/service.py` | `backend/modules/rh/importador/routes.py` | ALTO |
| `backend/modules/manuales_operativos/service.py` | `backend/modules/consultas_sql/routes.py` | ALTO |
| `backend/modules/manuales_operativos/service.py` | `backend/modules/catalogos/routes.py` | ALTO |
| `backend/modules/manuales_operativos/service.py` | `backend/modules/auth/routes.py` | ALTO |
| `backend/modules/manuales_operativos/service.py` | `backend/modules/crm/routes.py` | ALTO |
| `backend/modules/manuales_operativos/service.py` | `backend/modules/finanzas/propinas_tpv/routes.py` | ALTO |
| `backend/modules/manuales_operativos/service.py` | `backend/modules/cava_socios/routes.py` | ALTO |
| `backend/modules/manuales_operativos/service.py` | `backend/modules/manuales_operativos/routes.py` | ALTO |
| `backend/modules/manuales_operativos/service.py` | `backend/core/rbac/routes.py` | ALTO |
| `backend/modules/manuales_operativos/service.py` | `backend/core/rbac/middleware.py` | ALTO |
| `backend/modules/manuales_operativos/triggers.py` | `backend/server.py` | ALTO |
| `backend/core/connection_resolver.py` | `backend/core/centro_control/routes.py` | ALTO |
| `backend/core/auditoria.py` | `backend/modules/configuracion/routes/config_asignaciones_routes.py` | ALTO |
| `backend/core/health_checker.py` | `backend/core/centro_control/routes.py` | ALTO |
| `backend/core/db.py` | `backend/server.py` | ALTO |
| `backend/core/db.py` | `backend/modules/comercial/routes.py` | ALTO |
| `backend/core/db.py` | `backend/modules/corporate_filters/router.py` | ALTO |
| `backend/core/db.py` | `backend/modules/costos_margenes/routes.py` | ALTO |
| `backend/core/db.py` | `backend/modules/consultas_sql/routes.py` | ALTO |
| `backend/core/db.py` | `backend/modules/catalogos/routes.py` | ALTO |
| `backend/core/db.py` | `backend/modules/finanzas/tesoreria.py` | ALTO |
| `backend/core/db.py` | `backend/modules/finanzas/health.py` | ALTO |
| `backend/core/db.py` | `backend/api/admin_cache.py` | ALTO |
| `backend/core/db.py` | `backend/api/catalogos_sistemas.py` | ALTO |
| `backend/core/db.py` | `backend/api/admin_data_quality.py` | ALTO |
| `backend/core/db.py` | `backend/api/admin_core_connections.py` | ALTO |
| `backend/core/db.py` | `backend/api/dba_credential_p0d.py` | ALTO |
| `backend/core/centro_control/recipients_manager.py` | `backend/core/centro_control/routes.py` | ALTO |
| `backend/core/auth/user_repository_sql.py` | `backend/core/security.py` | ALTO |
| `backend/core/rbac/routes.py` | `backend/server.py` | ALTO |
| `backend/core/rbac/middleware.py` | `backend/modules/comercial/routes_pricing_ai.py` | ALTO |
| `backend/core/rbac/middleware.py` | `backend/modules/comercial/routes_pricing_ia.py` | ALTO |
| `backend/core/rbac/middleware.py` | `backend/modules/comercial/routes_listas_competidores.py` | ALTO |
| `backend/core/rbac/middleware.py` | `backend/modules/fase2_operativo/routes/sla_routes.py` | ALTO |
| `backend/core/rbac/middleware.py` | `backend/modules/fase2_operativo/routes/cargos_routes.py` | ALTO |
| `backend/core/rbac/middleware.py` | `backend/modules/fase2_operativo/routes/responsabilidad_routes.py` | ALTO |
| `backend/core/rbac/middleware.py` | `backend/modules/fase2_operativo/routes/auditoria_programada_routes.py` | ALTO |
| `backend/core/rbac/middleware.py` | `backend/api/admin_cache.py` | ALTO |
| `backend/core/rbac/middleware.py` | `backend/api/admin_scheduler_resync.py` | ALTO |
| `backend/core/rbac/middleware.py` | `backend/core/scheduler/routes.py` | ALTO |
| `backend/core/rbac/middleware.py` | `backend/core/communications/routes.py` | ALTO |
| `backend/core/rbac/middleware.py` | `backend/core/rbac/routes.py` | ALTO |

## Clasificación

- Todo riesgo ALTO debe auditarse manualmente por función.
- Si participa en endpoint visual/productivo, migrar a EDARSAHUB SQL.
- Si es solo migración/cache/test, documentar como permitido temporal.
