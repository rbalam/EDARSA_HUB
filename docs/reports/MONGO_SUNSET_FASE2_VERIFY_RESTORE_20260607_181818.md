# Mongo Sunset Fase 2 — Verificación de Restauración

- **Fecha:** 2026-06-07 18:18:18
- **BACKUP_ROOT:** `/app/backups/mongo_sunset_20260607_181350`
- **Sufijo temporal:** `verify_20260607_181818` (bases restauradas y luego eliminadas)
- **Log mongorestore:** `/app/backups/mongo_sunset_20260607_181350/mongorestore_verify_20260607_181818.log`
- **Resultado global:** ❌ DISCREPANCIAS DETECTADAS (ver detalle)

> ⚠️ NO destructivo sobre originales. Las bases `*_verify_*` fueron creadas, verificadas y eliminadas. No se tocó SQL, runtime ni pymongo/motor.

## Resumen por base

| Base | Cols original | Cols restauradas | Cols match | ¿Todo coincide? |
|---|---:|---:|---:|---|
| `cab003` | 10 | 0 | 0/10 | ❌ |
| `edarsa_hub` | 28 | 0 | 0/28 | ❌ |
| `edarsahub` | 6 | 0 | 0/6 | ❌ |
| `stock_tracker` | 2 | 0 | 0/2 | ❌ |
| `test_database` | 61 | 0 | 0/61 | ❌ |

## ⚠️ Discrepancias (original ≠ restaurado)

| Base | Colección | Original | Restaurado |
|---|---|---:|---:|
| `cab003` | auditorias_programadas | 0 | None |
| `cab003` | auditorias_programadas_log | 0 | None |
| `cab003` | cargos_economicos | 5 | None |
| `cab003` | cargos_economicos_log | 0 | None |
| `cab003` | detalle_diferencias | 18 | None |
| `cab003` | notificaciones_log | 4 | None |
| `cab003` | responsabilidad_economica | 5 | None |
| `cab003` | responsabilidad_historial | 10 | None |
| `cab003` | users | 0 | None |
| `cab003` | workflow_inventarios | 0 | None |
| `edarsa_hub` | audit_password_reset | 3 | None |
| `edarsa_hub` | consultas_custom | 6 | None |
| `edarsa_hub` | inventarios_procesados_auto | 158 | None |
| `edarsa_hub` | password_reset_tokens | 0 | None |
| `edarsa_hub` | pedidos_procesados_automatizacion | 2 | None |
| `edarsa_hub` | permisos_catalogos | 8 | None |
| `edarsa_hub` | portal_suppliers | 3 | None |
| `edarsa_hub` | propinas_config | 1 | None |
| `edarsa_hub` | rate_limit_password_reset | 0 | None |
| `edarsa_hub` | rbac_audit_log | 598 | None |
| `edarsa_hub` | rbac_permisos | 43 | None |
| `edarsa_hub` | rbac_roles | 6 | None |
| `edarsa_hub` | rbac_usuarios_roles | 72 | None |
| `edarsa_hub` | roles | 4 | None |
| `edarsa_hub` | sec_bitacora_acceso | 27 | None |
| `edarsa_hub` | sec_bitacora_admin | 61 | None |
| `edarsa_hub` | sec_empresas | 1 | None |
| `edarsa_hub` | sec_mapeo_servidor_sucursal | 7 | None |
| `edarsa_hub` | sec_metadata | 1 | None |
| `edarsa_hub` | sec_modulos_sistema | 10 | None |
| `edarsa_hub` | sec_perfiles | 5 | None |
| `edarsa_hub` | sec_permisos_catalogo | 90 | None |
| `edarsa_hub` | sec_roles | 5 | None |
| `edarsa_hub` | sec_sucursales | 7 | None |
| `edarsa_hub` | sec_unidades_negocio | 7 | None |
| `edarsa_hub` | server_connection_status | 1 | None |
| `edarsa_hub` | server_status | 13 | None |
| `edarsa_hub` | users | 17 | None |
| `edarsahub` | notification_config | 11 | None |
| `edarsahub` | notification_log | 0 | None |
| `edarsahub` | notification_queue | 0 | None |
| `edarsahub` | notification_templates | 11 | None |
| `edarsahub` | users_legacy_backup_auth_rbac_20260603 | 0 | None |
| `edarsahub` | users_legacy_backup_auth_rbac_20260604 | 1 | None |
| `stock_tracker` | rbac_permisos | 0 | None |
| `stock_tracker` | rbac_roles | 0 | None |
| `test_database` | auditoria_financiera | 274 | None |
| `test_database` | auditorias_programadas | 1 | None |
| `test_database` | automatizaciones_bitacora | 1 | None |
| `test_database` | automatizaciones_operativas_compras | 2 | None |
| `test_database` | cargos_economicos | 2 | None |
| `test_database` | cargos_economicos_log | 7 | None |
| `test_database` | config_catalogos | 1 | None |
| `test_database` | configuracion_operativa | 9 | None |
| `test_database` | configuracion_operativo | 1 | None |
| `test_database` | consultas_custom | 4 | None |
| `test_database` | decisiones_auditoria | 0 | None |
| `test_database` | detalle_diferencias | 48 | None |
| `test_database` | documentos_generados | 9 | None |
| `test_database` | historial_asignaciones | 0 | None |
| `test_database` | informes_auditoria | 3 | None |
| `test_database` | inventario_diferencias_cache | 1 | None |
| `test_database` | inventario_diferencias_detalle | 19 | None |
| `test_database` | inventarios_fisicos_procesados | 1 | None |
| `test_database` | justificaciones_inventario | 0 | None |
| `test_database` | kpis_cache | 46 | None |
| `test_database` | nomina_ciclos | 3 | None |
| `test_database` | nomina_configuracion | 1 | None |
| `test_database` | nomina_kpis_puestos | 1 | None |
| `test_database` | nomina_movimientos | 3 | None |
| `test_database` | notificaciones_log | 4 | None |
| `test_database` | notification_config | 6 | None |
| `test_database` | notification_log | 0 | None |
| `test_database` | notification_provider_config | 2 | None |
| `test_database` | notification_queue | 0 | None |
| `test_database` | notification_templates | 9 | None |
| `test_database` | permisos_catalogos | 2 | None |
| `test_database` | portal_suppliers | 1 | None |
| `test_database` | propinas_cache_listado | 7 | None |
| `test_database` | queries | 4 | None |
| `test_database` | rbac_audit_log | 370 | None |
| `test_database` | rbac_permisos | 43 | None |
| `test_database` | rbac_roles | 6 | None |
| `test_database` | rbac_usuarios_roles | 0 | None |
| `test_database` | responsabilidad_economica | 5 | None |
| `test_database` | responsabilidad_historial | 37 | None |
| `test_database` | roles | 4 | None |
| `test_database` | scheduler_job_log | 590 | None |
| `test_database` | scheduler_locks | 0 | None |
| `test_database` | script_logs | 19 | None |
| `test_database` | scripts_pendientes | 58 | None |
| `test_database` | sec_bitacora_acceso | 0 | None |
| `test_database` | sec_empresas | 1 | None |
| `test_database` | sec_mapeo_servidor_sucursal | 7 | None |
| `test_database` | sec_metadata | 1 | None |
| `test_database` | sec_modulos_sistema | 10 | None |
| `test_database` | sec_permisos_catalogo | 89 | None |
| `test_database` | sec_sucursales | 7 | None |
| `test_database` | sec_unidades_negocio | 7 | None |
| `test_database` | server_status | 9 | None |
| `test_database` | server_sucursales_config | 7 | None |
| `test_database` | servers | 11 | None |
| `test_database` | solicitudes_catalogos | 10 | None |
| `test_database` | tareas_inventario | 26 | None |
| `test_database` | tareas_sistema | 22 | None |
| `test_database` | users | 16 | None |
| `test_database` | workflow_inventarios | 28 | None |

## Limpieza

Bases temporales eliminadas (5): `cab003_verify_20260607_181818`, `edarsa_hub_verify_20260607_181818`, `edarsahub_verify_20260607_181818`, `stock_tracker_verify_20260607_181818`, `test_database_verify_20260607_181818`

