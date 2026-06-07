# Reporte de Respaldo MongoDB (Sunset - Fase NO destructiva)

- **Fecha del respaldo:** 2026-06-07 18:14:21
- **Ruta del dump:** `/app/backups/mongo_sunset_20260607_181350/dump`
- **Herramienta:** mongodump (BSON nativo)
- **Bases respaldadas:** edarsa_hub, test_database, cab003, edarsahub, stock_tracker

> ⚠️ FASE NO DESTRUCTIVA: No se borró ni desinstaló nada. Solo respaldo + inventario.


## Base: `edarsa_hub`  (28 colecciones)


## Resumen global

- **Total bases:** 5
- **Total colecciones:** 107
- **Total documentos:** 3066
- **Tamaño total dump (BSON en disco):** 2.4 MB
- **SHA256 global del dump (hash de hashes):** `bbb26d027ccba5a719c3e29972a878eaac10e39b9a8e2bf162add5f08f30d5e9`
| Colección | Docs | Tamaño datos | Tamaño almacen. | Archivo BSON | SHA256 (12) |
|---|---:|---:|---:|---|---|
| audit_password_reset | 3 | 806.0 B | 36.0 KB | `dump/edarsa_hub/audit_password_reset.bson` | 4e086763eb14 |
| consultas_custom | 6 | 6.9 KB | 36.0 KB | `dump/edarsa_hub/consultas_custom.bson` | fd09a3c7912d |
| inventarios_procesados_auto | 158 | 136.7 KB | 68.0 KB | `dump/edarsa_hub/inventarios_procesados_auto.bson` | 0582364d1aa5 |
| password_reset_tokens | 0 | 0.0 B | 36.0 KB | `dump/edarsa_hub/password_reset_tokens.bson` | e3b0c44298fc |
| pedidos_procesados_automatizacion | 2 | 412.0 B | 36.0 KB | `dump/edarsa_hub/pedidos_procesados_automatizacion.bson` | eca7d67c7ab3 |
| permisos_catalogos | 8 | 3.1 KB | 36.0 KB | `dump/edarsa_hub/permisos_catalogos.bson` | 1645d01df080 |
| portal_suppliers | 3 | 1.6 KB | 36.0 KB | `dump/edarsa_hub/portal_suppliers.bson` | 37c38ecaa508 |
| propinas_config | 1 | 562.0 B | 20.0 KB | `dump/edarsa_hub/propinas_config.bson` | 5da86644dc61 |
| rate_limit_password_reset | 0 | 0.0 B | 24.0 KB | `dump/edarsa_hub/rate_limit_password_reset.bson` | e3b0c44298fc |
| rbac_audit_log | 598 | 289.4 KB | 124.0 KB | `dump/edarsa_hub/rbac_audit_log.bson` | bebd213bb805 |
| rbac_permisos | 43 | 9.3 KB | 24.0 KB | `dump/edarsa_hub/rbac_permisos.bson` | 7d32509dd8d8 |
| rbac_roles | 6 | 4.6 KB | 20.0 KB | `dump/edarsa_hub/rbac_roles.bson` | ff3c9dc9f467 |
| rbac_usuarios_roles | 72 | 21.2 KB | 24.0 KB | `dump/edarsa_hub/rbac_usuarios_roles.bson` | 51539330f1f9 |
| roles | 4 | 1.7 KB | 36.0 KB | `dump/edarsa_hub/roles.bson` | 105dbeb83a9a |
| sec_bitacora_acceso | 27 | 7.7 KB | 36.0 KB | `dump/edarsa_hub/sec_bitacora_acceso.bson` | bae2a7c8e805 |
| sec_bitacora_admin | 61 | 41.6 KB | 48.0 KB | `dump/edarsa_hub/sec_bitacora_admin.bson` | 82b0a64da0db |
| sec_empresas | 1 | 404.0 B | 20.0 KB | `dump/edarsa_hub/sec_empresas.bson` | 56ca9fceedca |
| sec_mapeo_servidor_sucursal | 7 | 4.1 KB | 20.0 KB | `dump/edarsa_hub/sec_mapeo_servidor_sucursal.bson` | 714bfa5f79b7 |
| sec_metadata | 1 | 687.0 B | 20.0 KB | `dump/edarsa_hub/sec_metadata.bson` | b60859d3278b |
| sec_modulos_sistema | 10 | 2.5 KB | 20.0 KB | `dump/edarsa_hub/sec_modulos_sistema.bson` | 2d42fcb6e9f5 |
| sec_perfiles | 5 | 1.3 KB | 20.0 KB | `dump/edarsa_hub/sec_perfiles.bson` | a6665ec45b00 |
| sec_permisos_catalogo | 90 | 23.1 KB | 52.0 KB | `dump/edarsa_hub/sec_permisos_catalogo.bson` | ecf4886fc77e |
| sec_roles | 5 | 2.0 KB | 36.0 KB | `dump/edarsa_hub/sec_roles.bson` | 7e8c0bab5092 |
| sec_sucursales | 7 | 3.0 KB | 20.0 KB | `dump/edarsa_hub/sec_sucursales.bson` | d548630afa27 |
| sec_unidades_negocio | 7 | 4.0 KB | 20.0 KB | `dump/edarsa_hub/sec_unidades_negocio.bson` | 8ac4400fb416 |
| server_connection_status | 1 | 191.0 B | 36.0 KB | `dump/edarsa_hub/server_connection_status.bson` | 4d1d80b4d537 |
| server_status | 13 | 2.1 KB | 36.0 KB | `dump/edarsa_hub/server_status.bson` | e8aa7f50c3a7 |
| users | 17 | 13.6 KB | 44.0 KB | `dump/edarsa_hub/users.bson` | 72318e1ee141 |

**Subtotal `edarsa_hub`:** 28 colecciones, 1156 documentos, 582.4 KB datos.


## Base: `test_database`  (61 colecciones)

| Colección | Docs | Tamaño datos | Tamaño almacen. | Archivo BSON | SHA256 (12) |
|---|---:|---:|---:|---|---|
| auditoria_financiera | 269 | 157.8 KB | 76.0 KB | `dump/test_database/auditoria_financiera.bson` | a5617ff694e4 |
| auditorias_programadas | 1 | 622.0 B | 20.0 KB | `dump/test_database/auditorias_programadas.bson` | 89bd7e01735d |
| automatizaciones_bitacora | 1 | 639.0 B | 20.0 KB | `dump/test_database/automatizaciones_bitacora.bson` | 874982ceddf5 |
| automatizaciones_operativas_compras | 2 | 2.4 KB | 36.0 KB | `dump/test_database/automatizaciones_operativas_compras.bson` | 4927cf885bb8 |
| cargos_economicos | 2 | 1.4 KB | 36.0 KB | `dump/test_database/cargos_economicos.bson` | 225455f3111d |
| cargos_economicos_log | 7 | 2.8 KB | 36.0 KB | `dump/test_database/cargos_economicos_log.bson` | 9dff2a5678d4 |
| config_catalogos | 1 | 78.0 B | 20.0 KB | `dump/test_database/config_catalogos.bson` | 180f68d37137 |
| configuracion_operativa | 9 | 1.7 KB | 36.0 KB | `dump/test_database/configuracion_operativa.bson` | 38d61389fbb0 |
| configuracion_operativo | 1 | 153.0 B | 36.0 KB | `dump/test_database/configuracion_operativo.bson` | df0530a94d24 |
| consultas_custom | 4 | 12.4 KB | 36.0 KB | `dump/test_database/consultas_custom.bson` | f9fcf754e201 |
| decisiones_auditoria | 0 | 0.0 B | 8.0 KB | `dump/test_database/decisiones_auditoria.bson` | e3b0c44298fc |
| detalle_diferencias | 48 | 29.6 KB | 40.0 KB | `dump/test_database/detalle_diferencias.bson` | 1a8d10e1970d |
| documentos_generados | 9 | 2.4 KB | 36.0 KB | `dump/test_database/documentos_generados.bson` | 963dfe02f1fb |
| historial_asignaciones | 0 | 0.0 B | 24.0 KB | `dump/test_database/historial_asignaciones.bson` | e3b0c44298fc |
| informes_auditoria | 3 | 5.1 KB | 36.0 KB | `dump/test_database/informes_auditoria.bson` | 4656d05746c2 |
| inventario_diferencias_cache | 1 | 643.0 B | 36.0 KB | `dump/test_database/inventario_diferencias_cache.bson` | 0769749ef808 |
| inventario_diferencias_detalle | 19 | 509.6 KB | 320.0 KB | `dump/test_database/inventario_diferencias_detalle.bson` | 9d898c4a8a51 |
| inventarios_fisicos_procesados | 1 | 188.0 B | 20.0 KB | `dump/test_database/inventarios_fisicos_procesados.bson` | d994111d72f8 |
| justificaciones_inventario | 0 | 0.0 B | 12.0 KB | `dump/test_database/justificaciones_inventario.bson` | e3b0c44298fc |
| kpis_cache | 46 | 32.7 KB | 52.0 KB | `dump/test_database/kpis_cache.bson` | 62e17c2b3346 |
| nomina_ciclos | 3 | 5.1 KB | 36.0 KB | `dump/test_database/nomina_ciclos.bson` | 1bfeb0c7730a |
| nomina_configuracion | 1 | 310.0 B | 36.0 KB | `dump/test_database/nomina_configuracion.bson` | 8cf3d1b383ae |
| nomina_kpis_puestos | 1 | 326.0 B | 36.0 KB | `dump/test_database/nomina_kpis_puestos.bson` | 9f143d86bbfa |
| nomina_movimientos | 3 | 1.3 KB | 36.0 KB | `dump/test_database/nomina_movimientos.bson` | 66aa07a960fd |
| notificaciones_log | 4 | 1.9 KB | 36.0 KB | `dump/test_database/notificaciones_log.bson` | 8e804519bc69 |
| notification_config | 6 | 2.6 KB | 36.0 KB | `dump/test_database/notification_config.bson` | 2379893a2970 |
| notification_log | 0 | 0.0 B | 4.0 KB | `dump/test_database/notification_log.bson` | e3b0c44298fc |
| notification_provider_config | 2 | 663.0 B | 36.0 KB | `dump/test_database/notification_provider_config.bson` | fd2751209c99 |
| notification_queue | 0 | 0.0 B | 4.0 KB | `dump/test_database/notification_queue.bson` | e3b0c44298fc |
| notification_templates | 9 | 3.9 KB | 36.0 KB | `dump/test_database/notification_templates.bson` | e7275e7074d9 |
| permisos_catalogos | 2 | 495.0 B | 36.0 KB | `dump/test_database/permisos_catalogos.bson` | 90172b45c8d7 |
| portal_suppliers | 1 | 700.0 B | 36.0 KB | `dump/test_database/portal_suppliers.bson` | 38b8c4f29f7c |
| propinas_cache_listado | 7 | 2.9 KB | 36.0 KB | `dump/test_database/propinas_cache_listado.bson` | 482c2fcab81c |
| queries | 4 | 9.5 KB | 20.0 KB | `dump/test_database/queries.bson` | c34011ecd568 |
| rbac_audit_log | 370 | 226.5 KB | 96.0 KB | `dump/test_database/rbac_audit_log.bson` | e3113d5cf5e8 |
| rbac_permisos | 43 | 9.3 KB | 40.0 KB | `dump/test_database/rbac_permisos.bson` | a3c6140a2247 |
| rbac_roles | 6 | 4.6 KB | 36.0 KB | `dump/test_database/rbac_roles.bson` | 804232b7bc21 |
| rbac_usuarios_roles | 0 | 0.0 B | 4.0 KB | `dump/test_database/rbac_usuarios_roles.bson` | e3b0c44298fc |
| responsabilidad_economica | 5 | 4.0 KB | 36.0 KB | `dump/test_database/responsabilidad_economica.bson` | 4916fad480f9 |
| responsabilidad_historial | 37 | 15.3 KB | 44.0 KB | `dump/test_database/responsabilidad_historial.bson` | 2860dc071c41 |
| roles | 4 | 1.7 KB | 36.0 KB | `dump/test_database/roles.bson` | 7f85939a6bac |
| scheduler_job_log | 586 | 511.5 KB | 156.0 KB | `dump/test_database/scheduler_job_log.bson` | eba67043f219 |
| scheduler_locks | 0 | 0.0 B | 12.0 KB | `dump/test_database/scheduler_locks.bson` | e3b0c44298fc |
| script_logs | 19 | 109.5 KB | 60.0 KB | `dump/test_database/script_logs.bson` | 529e98251b00 |
| scripts_pendientes | 57 | 117.3 KB | 96.0 KB | `dump/test_database/scripts_pendientes.bson` | ab99c6af1e90 |
| sec_bitacora_acceso | 0 | 0.0 B | 4.0 KB | `dump/test_database/sec_bitacora_acceso.bson` | e3b0c44298fc |
| sec_empresas | 1 | 404.0 B | 36.0 KB | `dump/test_database/sec_empresas.bson` | 56ca9fceedca |
| sec_mapeo_servidor_sucursal | 7 | 4.1 KB | 36.0 KB | `dump/test_database/sec_mapeo_servidor_sucursal.bson` | 714bfa5f79b7 |
| sec_metadata | 1 | 687.0 B | 20.0 KB | `dump/test_database/sec_metadata.bson` | b60859d3278b |
| sec_modulos_sistema | 10 | 2.5 KB | 20.0 KB | `dump/test_database/sec_modulos_sistema.bson` | 2d42fcb6e9f5 |
| sec_permisos_catalogo | 89 | 22.8 KB | 28.0 KB | `dump/test_database/sec_permisos_catalogo.bson` | bdd73e67d483 |
| sec_sucursales | 7 | 3.0 KB | 36.0 KB | `dump/test_database/sec_sucursales.bson` | d548630afa27 |
| sec_unidades_negocio | 7 | 4.0 KB | 36.0 KB | `dump/test_database/sec_unidades_negocio.bson` | 8ac4400fb416 |
| server_status | 9 | 1.4 KB | 36.0 KB | `dump/test_database/server_status.bson` | 57adb0c80650 |
| server_sucursales_config | 7 | 3.4 KB | 36.0 KB | `dump/test_database/server_sucursales_config.bson` | a97d6e6851b2 |
| servers | 11 | 12.7 KB | 44.0 KB | `dump/test_database/servers.bson` | 6cb6634fe96d |
| solicitudes_catalogos | 10 | 12.4 KB | 36.0 KB | `dump/test_database/solicitudes_catalogos.bson` | c3ef1a74b9b9 |
| tareas_inventario | 26 | 6.3 KB | 36.0 KB | `dump/test_database/tareas_inventario.bson` | 35e31d653766 |
| tareas_sistema | 22 | 11.8 KB | 36.0 KB | `dump/test_database/tareas_sistema.bson` | b70a7cea7ec1 |
| users | 16 | 7.2 KB | 36.0 KB | `dump/test_database/users.bson` | f69148ddee6c |
| workflow_inventarios | 28 | 7.2 KB | 36.0 KB | `dump/test_database/workflow_inventarios.bson` | 6b3444028ede |

**Subtotal `test_database`:** 61 colecciones, 1845 documentos, 1.8 MB datos.


## Base: `cab003`  (10 colecciones)

| Colección | Docs | Tamaño datos | Tamaño almacen. | Archivo BSON | SHA256 (12) |
|---|---:|---:|---:|---|---|
| auditorias_programadas | 0 | 0.0 B | 12.0 KB | `dump/cab003/auditorias_programadas.bson` | e3b0c44298fc |
| auditorias_programadas_log | 0 | 0.0 B | 12.0 KB | `dump/cab003/auditorias_programadas_log.bson` | e3b0c44298fc |
| cargos_economicos | 5 | 3.4 KB | 36.0 KB | `dump/cab003/cargos_economicos.bson` | 61b0f97c0814 |
| cargos_economicos_log | 0 | 0.0 B | 12.0 KB | `dump/cab003/cargos_economicos_log.bson` | e3b0c44298fc |
| detalle_diferencias | 18 | 5.3 KB | 36.0 KB | `dump/cab003/detalle_diferencias.bson` | 853f055da4de |
| notificaciones_log | 4 | 2.2 KB | 36.0 KB | `dump/cab003/notificaciones_log.bson` | ab07a8b6f3d5 |
| responsabilidad_economica | 5 | 3.9 KB | 36.0 KB | `dump/cab003/responsabilidad_economica.bson` | c008b9a08071 |
| responsabilidad_historial | 10 | 3.8 KB | 36.0 KB | `dump/cab003/responsabilidad_historial.bson` | 2534514cb325 |
| users | 0 | 0.0 B | 12.0 KB | `dump/cab003/users.bson` | e3b0c44298fc |
| workflow_inventarios | 0 | 0.0 B | 12.0 KB | `dump/cab003/workflow_inventarios.bson` | e3b0c44298fc |

**Subtotal `cab003`:** 10 colecciones, 42 documentos, 18.7 KB datos.


## Base: `edarsahub`  (6 colecciones)

| Colección | Docs | Tamaño datos | Tamaño almacen. | Archivo BSON | SHA256 (12) |
|---|---:|---:|---:|---|---|
| notification_config | 11 | 4.3 KB | 20.0 KB | `dump/edarsahub/notification_config.bson` | 9dff6c172ae6 |
| notification_log | 0 | 0.0 B | 4.0 KB | `dump/edarsahub/notification_log.bson` | e3b0c44298fc |
| notification_queue | 0 | 0.0 B | 4.0 KB | `dump/edarsahub/notification_queue.bson` | e3b0c44298fc |
| notification_templates | 11 | 4.8 KB | 20.0 KB | `dump/edarsahub/notification_templates.bson` | af09e56176f0 |
| users_legacy_backup_auth_rbac_20260603 | 0 | 0.0 B | 4.0 KB | `dump/edarsahub/users_legacy_backup_auth_rbac_20260603.bson` | e3b0c44298fc |
| users_legacy_backup_auth_rbac_20260604 | 1 | 529.0 B | 20.0 KB | `dump/edarsahub/users_legacy_backup_auth_rbac_20260604.bson` | fbdf3f0aee1c |

**Subtotal `edarsahub`:** 6 colecciones, 23 documentos, 9.6 KB datos.


## Base: `stock_tracker`  (2 colecciones)

| Colección | Docs | Tamaño datos | Tamaño almacen. | Archivo BSON | SHA256 (12) |
|---|---:|---:|---:|---|---|
| rbac_permisos | 0 | 0.0 B | 36.0 KB | `dump/stock_tracker/rbac_permisos.bson` | e3b0c44298fc |
| rbac_roles | 0 | 0.0 B | 24.0 KB | `dump/stock_tracker/rbac_roles.bson` | e3b0c44298fc |

**Subtotal `stock_tracker`:** 2 colecciones, 0 documentos, 0.0 B datos.

