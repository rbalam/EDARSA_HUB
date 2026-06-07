# Mongo Sunset Fase 4 — Lista blanca editable

Fecha: 2026-06-07T18:30:30

## Estado

✅ Generada en modo NO destructivo. No se borró nada, no se modificó Mongo ni SQL.

## Fuente

`/app/docs/reports/mongo_sql_compare_20260607_182308/MONGO_SQL_COVERAGE_182308.json`

## Regla principal

Todas salen con `aprobar_borrado = NO`. Cambiar a `SI` SOLO las autorizadas.

## Resumen

- Filas evaluadas (Fase 3): **107**
- En lista blanca editable: **31**
- Excluidas por seguridad: **76**

### Lista blanca por base

- edarsa_hub: **2**
- edarsahub: **1**
- test_database: **28**

### Lista blanca por recomendación

- BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO: **24**
- CANDIDATA_A_BORRADO_POSTERIOR: **7**

## Colecciones incluidas (editables)

| Aprobar | Base | Colección | Docs | Clasificación | Recomendación | Riesgo |
|---|---|---|---:|---|---|---|
| NO | edarsa_hub | password_reset_tokens | 0 | Vacía / Sin datos | CANDIDATA_A_BORRADO_POSTERIOR | BAJO |
| NO | edarsa_hub | rate_limit_password_reset | 0 | Vacía / Sin datos | CANDIDATA_A_BORRADO_POSTERIOR | BAJO |
| NO | edarsahub | notification_queue | 0 | Vacía / Sin datos | CANDIDATA_A_BORRADO_POSTERIOR | BAJO |
| NO | test_database | automatizaciones_bitacora | 1 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | automatizaciones_operativas_compras | 2 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | cargos_economicos | 2 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | consultas_custom | 4 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | detalle_diferencias | 48 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | documentos_generados | 9 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | kpis_cache | 46 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | nomina_ciclos | 3 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | nomina_kpis_puestos | 1 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | nomina_movimientos | 3 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | notification_templates | 9 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | portal_suppliers | 1 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | propinas_cache_listado | 7 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | queries | 4 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | responsabilidad_economica | 5 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | responsabilidad_historial | 37 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | scripts_pendientes | 58 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | sec_empresas | 1 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | sec_mapeo_servidor_sucursal | 7 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | sec_metadata | 1 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | sec_modulos_sistema | 10 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | sec_sucursales | 7 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | sec_unidades_negocio | 7 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | tareas_sistema | 22 | Pruebas / Test | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | MEDIO |
| NO | test_database | historial_asignaciones | 0 | Pruebas / Test | CANDIDATA_A_BORRADO_POSTERIOR | BAJO |
| NO | test_database | notification_queue | 0 | Pruebas / Test | CANDIDATA_A_BORRADO_POSTERIOR | BAJO |
| NO | test_database | scheduler_locks | 0 | Pruebas / Test | CANDIDATA_A_BORRADO_POSTERIOR | BAJO |
| NO | test_database | sec_bitacora_acceso | 0 | Pruebas / Test | CANDIDATA_A_BORRADO_POSTERIOR | BAJO |

## Excluidas por seguridad

| Base | Colección | Docs | Recomendación | Motivo exclusión |
|---|---|---:|---|---|
| cab003 | auditorias_programadas | 0 | CANDIDATA_A_BORRADO_POSTERIOR | coleccion_sensible_bloqueada |
| cab003 | auditorias_programadas_log | 0 | CANDIDATA_A_BORRADO_POSTERIOR | coleccion_sensible_bloqueada |
| cab003 | cargos_economicos_log | 0 | CANDIDATA_A_BORRADO_POSTERIOR | coleccion_sensible_bloqueada |
| cab003 | users | 0 | CANDIDATA_A_BORRADO_POSTERIOR | coleccion_sensible_bloqueada |
| cab003 | workflow_inventarios | 0 | CANDIDATA_A_BORRADO_POSTERIOR | coleccion_sensible_bloqueada |
| cab003 | notificaciones_log | 4 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| cab003 | responsabilidad_economica | 5 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| cab003 | responsabilidad_historial | 10 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| cab003 | cargos_economicos | 5 | VALIDAR_MANUALMENTE | recomendacion_no_permitida |
| cab003 | detalle_diferencias | 18 | VALIDAR_MANUALMENTE | recomendacion_no_permitida |
| edarsa_hub | audit_password_reset | 3 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsa_hub | consultas_custom | 6 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsa_hub | inventarios_procesados_auto | 158 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsa_hub | pedidos_procesados_automatizacion | 2 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida |
| edarsa_hub | permisos_catalogos | 8 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsa_hub | portal_suppliers | 3 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida |
| edarsa_hub | propinas_config | 1 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsa_hub | rbac_audit_log | 598 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsa_hub | rbac_permisos | 43 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsa_hub | rbac_roles | 6 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsa_hub | rbac_usuarios_roles | 72 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsa_hub | roles | 4 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsa_hub | sec_bitacora_acceso | 27 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsa_hub | sec_bitacora_admin | 61 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsa_hub | sec_modulos_sistema | 10 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida |
| edarsa_hub | sec_perfiles | 5 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsa_hub | sec_permisos_catalogo | 90 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsa_hub | sec_roles | 5 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsa_hub | sec_unidades_negocio | 7 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsa_hub | users | 17 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsa_hub | sec_empresas | 1 | VALIDAR_MANUALMENTE | recomendacion_no_permitida |
| edarsa_hub | sec_mapeo_servidor_sucursal | 7 | VALIDAR_MANUALMENTE | recomendacion_no_permitida |
| edarsa_hub | sec_metadata | 1 | VALIDAR_MANUALMENTE | recomendacion_no_permitida |
| edarsa_hub | sec_sucursales | 7 | VALIDAR_MANUALMENTE | recomendacion_no_permitida |
| edarsa_hub | server_connection_status | 1 | VALIDAR_MANUALMENTE | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsa_hub | server_status | 13 | VALIDAR_MANUALMENTE | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsahub | notification_log | 0 | CANDIDATA_A_BORRADO_POSTERIOR | coleccion_sensible_bloqueada |
| edarsahub | users_legacy_backup_auth_rbac_20260603 | 0 | CANDIDATA_A_BORRADO_POSTERIOR | coleccion_sensible_bloqueada |
| edarsahub | notification_config | 11 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsahub | users_legacy_backup_auth_rbac_20260604 | 1 | MIGRAR_ANTES_DE_BORRAR | recomendacion_no_permitida,coleccion_sensible_bloqueada |
| edarsahub | notification_templates | 11 | VALIDAR_MANUALMENTE | recomendacion_no_permitida |
| stock_tracker | rbac_permisos | 0 | CANDIDATA_A_BORRADO_POSTERIOR | coleccion_sensible_bloqueada |
| stock_tracker | rbac_roles | 0 | CANDIDATA_A_BORRADO_POSTERIOR | coleccion_sensible_bloqueada |
| test_database | auditoria_financiera | 274 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | auditorias_programadas | 1 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | cargos_economicos_log | 7 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | config_catalogos | 1 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | configuracion_operativa | 9 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | configuracion_operativo | 1 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | informes_auditoria | 3 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | inventario_diferencias_cache | 1 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | inventario_diferencias_detalle | 19 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | inventarios_fisicos_procesados | 1 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | nomina_configuracion | 1 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | notificaciones_log | 4 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | notification_config | 6 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | notification_provider_config | 2 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | permisos_catalogos | 2 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | rbac_audit_log | 370 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | rbac_permisos | 43 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | rbac_roles | 6 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | roles | 4 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | scheduler_job_log | 590 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | script_logs | 19 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | sec_permisos_catalogo | 89 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | server_status | 9 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | server_sucursales_config | 7 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | servers | 11 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | solicitudes_catalogos | 10 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | tareas_inventario | 26 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | users | 16 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | workflow_inventarios | 28 | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | coleccion_sensible_bloqueada |
| test_database | decisiones_auditoria | 0 | CANDIDATA_A_BORRADO_POSTERIOR | coleccion_sensible_bloqueada |
| test_database | justificaciones_inventario | 0 | CANDIDATA_A_BORRADO_POSTERIOR | coleccion_sensible_bloqueada |
| test_database | notification_log | 0 | CANDIDATA_A_BORRADO_POSTERIOR | coleccion_sensible_bloqueada |
| test_database | rbac_usuarios_roles | 0 | CANDIDATA_A_BORRADO_POSTERIOR | coleccion_sensible_bloqueada |

## Siguiente paso

Revisar el CSV y cambiar `aprobar_borrado` de `NO` a `SI` solo donde se autorice. El script de borrado futuro leerá SOLO ese CSV y borrará únicamente filas con `aprobar_borrado = SI` (con re-respaldo previo).
