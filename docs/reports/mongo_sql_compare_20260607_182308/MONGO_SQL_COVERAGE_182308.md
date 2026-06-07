# Mongo Sunset Fase 3 — Comparativo SQL ↔ Mongo (NO destructivo)

Fecha: 2026-06-07T18:24:11

## Reglas

- No se borró nada. No se modificó Mongo ni SQL. No se crearon tablas/vistas. No se desinstaló pymongo/motor.

## Resumen

- Colecciones Mongo analizadas: **107**
- Documentos Mongo analizados: **3076**
- Tablas SQL consideradas: **478**

### Recomendaciones

- BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO: **53**
- CANDIDATA_A_BORRADO_POSTERIOR: **20**
- MIGRAR_ANTES_DE_BORRAR: **25**
- VALIDAR_MANUALMENTE: **9**

### Clasificaciones

- Auditoría / Logs: **12**
- Compras / Proveedores: **3**
- Configuración: **4**
- Inventarios: **2**
- Legacy sin uso detectado: **9**
- Pruebas / Test: **61**
- Usuarios / Auth / RBAC: **13**
- Vacía / Sin datos: **3**

## Matriz de cobertura

| Base Mongo | Colección | Docs | Clasificación | SQL candidata | Score | Riesgo | Recomendación | Motivo |
|---|---|---:|---|---|---:|---|---|---|
| edarsa_hub | audit_password_reset | 3 | Auditoría / Logs | dbo.Sync_Logs | 0.2167 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsa_hub | consultas_custom | 6 | Configuración | dbo.Sistema_RBAC_Roles | 0.1944 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsa_hub | inventarios_procesados_auto | 158 | Inventarios | dbo.Inventarios_ProcesadosAuto | 0.241 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsa_hub | password_reset_tokens | 0 | Vacía / Sin datos | - | 0 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |
| edarsa_hub | pedidos_procesados_automatizacion | 2 | Compras / Proveedores | dbo.automatizacion_inventarios_folios_procesados | 0.2384 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsa_hub | permisos_catalogos | 8 | Auditoría / Logs | dbo.RBAC_Permisos | 0.2233 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsa_hub | portal_suppliers | 3 | Compras / Proveedores | dbo.Portal_Proveedores | 0.2567 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsa_hub | propinas_config | 1 | Configuración | dbo.propinas_tpv_config | 0.2657 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsa_hub | rate_limit_password_reset | 0 | Vacía / Sin datos | - | 0 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |
| edarsa_hub | rbac_audit_log | 598 | Auditoría / Logs | dbo.Compras_Sync_Log | 0.1824 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsa_hub | rbac_permisos | 43 | Usuarios / Auth / RBAC | dbo.RBAC_Permisos | 0.4018 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsa_hub | rbac_roles | 6 | Usuarios / Auth / RBAC | dbo.Sistema_RBAC_Roles | 0.4531 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsa_hub | rbac_usuarios_roles | 72 | Usuarios / Auth / RBAC | dbo.Sistema_RBAC_Roles | 0.2196 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsa_hub | roles | 4 | Usuarios / Auth / RBAC | dbo.Sistema_RBAC_Roles | 0.2991 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsa_hub | sec_bitacora_acceso | 27 | Auditoría / Logs | dbo.Inventarios_DiferenciasDetalle | 0.1569 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsa_hub | sec_bitacora_admin | 61 | Auditoría / Logs | dbo.RH_Homologacion_Equivalencias | 0.1568 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsa_hub | sec_empresas | 1 | Legacy sin uso detectado | dbo.CRM_Config_Pipelines | 0.21 | MEDIO | VALIDAR_MANUALMENTE | Sin equivalente SQL claro. |
| edarsa_hub | sec_mapeo_servidor_sucursal | 7 | Legacy sin uso detectado | dbo.Finanzas_ConfiguracionTPV_Sucursal | 0.1993 | MEDIO | VALIDAR_MANUALMENTE | Sin equivalente SQL claro. |
| edarsa_hub | sec_metadata | 1 | Legacy sin uso detectado | dbo.Finanzas_PropinasConfig | 0.1767 | MEDIO | VALIDAR_MANUALMENTE | Sin equivalente SQL claro. |
| edarsa_hub | sec_modulos_sistema | 10 | Compras / Proveedores | dbo.Sistema_Modulos | 0.405 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsa_hub | sec_perfiles | 5 | Usuarios / Auth / RBAC | dbo.Unidades_Negocio | 0.3038 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsa_hub | sec_permisos_catalogo | 90 | Auditoría / Logs | dbo.RBAC_Permisos | 0.2505 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsa_hub | sec_roles | 5 | Usuarios / Auth / RBAC | dbo.Sistema_RBAC_Roles | 0.3538 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsa_hub | sec_sucursales | 7 | Legacy sin uso detectado | dbo.Unidades_Negocio | 0.2321 | MEDIO | VALIDAR_MANUALMENTE | Sin equivalente SQL claro. |
| edarsa_hub | sec_unidades_negocio | 7 | Usuarios / Auth / RBAC | dbo.Unidades_Negocio | 0.3871 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsa_hub | server_connection_status | 1 | Legacy sin uso detectado | dbo.Finanzas_PropinasConfig | 0.1808 | MEDIO | VALIDAR_MANUALMENTE | Sin equivalente SQL claro. |
| edarsa_hub | server_status | 13 | Legacy sin uso detectado | dbo.Sistema_ServidoresEstado | 0.1808 | MEDIO | VALIDAR_MANUALMENTE | Sin equivalente SQL claro. |
| edarsa_hub | users | 17 | Auditoría / Logs | dbo.Usuario_LogRecuperacion | 0.1654 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| test_database | auditoria_financiera | 274 | Pruebas / Test | dbo.Sync_Productos_SubFamilias | 0.1445 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | auditorias_programadas | 1 | Pruebas / Test | dbo.automatizacion_inventarios_folios_procesados | 0.191 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | automatizaciones_bitacora | 1 | Pruebas / Test | dbo.Finanzas_PropinasConfig | 0.169 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | automatizaciones_operativas_compras | 2 | Pruebas / Test | dbo.Compras_PedidosProcesadosAutomatizacion | 0.2398 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | cargos_economicos | 2 | Pruebas / Test | dbo.CavaSocios_Cargos | 0.165 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | cargos_economicos_log | 7 | Pruebas / Test | dbo.Sistema_ServidoresSucursalesConfig | 0.169 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | config_catalogos | 1 | Pruebas / Test | dbo.CRM_Config_Pipelines | 0.225 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | configuracion_operativa | 9 | Pruebas / Test | dbo.Configuracion_Operativa | 0.5083 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | configuracion_operativo | 1 | Pruebas / Test | dbo.Configuracion_Operativa | 0.24 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | consultas_custom | 4 | Pruebas / Test | dbo.CRM_Cat_TiposPipeline | 0.2 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | decisiones_auditoria | 0 | Pruebas / Test | dbo.Auditoria_Informes | 0.09 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |
| test_database | detalle_diferencias | 48 | Pruebas / Test | dbo.Products | 0.1585 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | documentos_generados | 9 | Pruebas / Test | dbo.Sistema_DeudaTecnica_TablasDuplicadas | 0.1833 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | historial_asignaciones | 0 | Pruebas / Test | dbo.Config_Asignaciones | 0.09 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |
| test_database | informes_auditoria | 3 | Pruebas / Test | dbo.Auditoria_Informes | 0.225 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | inventario_diferencias_cache | 1 | Pruebas / Test | dbo.automatizacion_inventarios_folios_procesados | 0.2115 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | inventario_diferencias_detalle | 19 | Pruebas / Test | dbo.Tareas_Inventario | 0.2292 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | inventarios_fisicos_procesados | 1 | Pruebas / Test | dbo.automatizacion_inventarios_folios_procesados | 0.3513 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | justificaciones_inventario | 0 | Pruebas / Test | dbo.Inventario_Almacenes | 0.09 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |
| test_database | kpis_cache | 46 | Pruebas / Test | dbo.Comercial_KPIs_Cache | 0.2164 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | nomina_ciclos | 3 | Pruebas / Test | dbo.Comercial_Ventas_Dia_Abiertas_v2_backup_migracion_codigos_20260513_0558 | 0.1985 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | nomina_configuracion | 1 | Pruebas / Test | dbo.Finanzas_PropinasConfig | 0.1711 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | nomina_kpis_puestos | 1 | Pruebas / Test | dbo.Finanzas_PropinasConfig | 0.1786 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | nomina_movimientos | 3 | Pruebas / Test | dbo.CavaSocios_Movimientos | 0.24 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | notificaciones_log | 4 | Pruebas / Test | dbo.Operativo_Notificaciones_Log | 0.2527 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | notification_config | 6 | Pruebas / Test | dbo.CRM_Config_PipelineEtapas | 0.2161 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | notification_log | 0 | Pruebas / Test | dbo.Compras_Sync_Log | 0.075 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |
| test_database | notification_provider_config | 2 | Pruebas / Test | dbo.Config_Asignaciones | 0.2404 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | notification_queue | 0 | Pruebas / Test | - | 0 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |
| test_database | notification_templates | 9 | Pruebas / Test | dbo.Unidades_Negocio | 0.2433 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | permisos_catalogos | 2 | Pruebas / Test | dbo.Compras_PedidosProcesadosAutomatizacion | 0.1786 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | portal_suppliers | 1 | Pruebas / Test | dbo.Sync_Vtiger_Contactos | 0.1695 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | propinas_cache_listado | 7 | Pruebas / Test | dbo.Sistema_ServidoresSucursalesConfig | 0.1808 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | queries | 4 | Pruebas / Test | dbo.Sistema_Queries | 0.2892 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | rbac_audit_log | 370 | Pruebas / Test | dbo.Compras_Sync_Log | 0.2287 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | rbac_permisos | 43 | Pruebas / Test | dbo.RBAC_Permisos | 0.4018 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | rbac_roles | 6 | Pruebas / Test | dbo.Sistema_RBAC_Roles | 0.4531 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | rbac_usuarios_roles | 0 | Pruebas / Test | dbo.Sistema_RBAC_Roles | 0.15 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |
| test_database | responsabilidad_economica | 5 | Pruebas / Test | dbo.Comercial_Ventas_Dia_Abiertas_v2_Backup_FechaOperacion_20260521 | 0.1786 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | responsabilidad_historial | 37 | Pruebas / Test | dbo.propinas_tpv_historial | 0.2013 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | roles | 4 | Pruebas / Test | dbo.Sistema_RBAC_Roles | 0.2991 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | scheduler_job_log | 590 | Pruebas / Test | dbo.Compras_Sync_Log | 0.199 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | scheduler_locks | 0 | Pruebas / Test | dbo.Scheduler_BitacoraJobs | 0.09 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |
| test_database | script_logs | 19 | Pruebas / Test | dbo.Tareas_Inventario | 0.1663 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | scripts_pendientes | 58 | Pruebas / Test | dbo.RH_Homologacion_Equivalencias | 0.163 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | sec_bitacora_acceso | 0 | Pruebas / Test | dbo.RH_Importacion_Bitacora | 0.0643 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |
| test_database | sec_empresas | 1 | Pruebas / Test | dbo.CRM_Config_Pipelines | 0.21 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | sec_mapeo_servidor_sucursal | 7 | Pruebas / Test | dbo.Finanzas_ConfiguracionTPV_Sucursal | 0.1993 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | sec_metadata | 1 | Pruebas / Test | dbo.Finanzas_PropinasConfig | 0.1767 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | sec_modulos_sistema | 10 | Pruebas / Test | dbo.Sistema_Modulos | 0.405 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | sec_permisos_catalogo | 89 | Pruebas / Test | dbo.RBAC_Permisos | 0.2506 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | sec_sucursales | 7 | Pruebas / Test | dbo.Unidades_Negocio | 0.2321 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | sec_unidades_negocio | 7 | Pruebas / Test | dbo.Unidades_Negocio | 0.3871 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | server_status | 9 | Pruebas / Test | dbo.Sistema_DeudaTecnica_TablasDuplicadas | 0.1864 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | server_sucursales_config | 7 | Pruebas / Test | dbo.RH_Cat_Sucursales | 0.2298 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | servers | 11 | Pruebas / Test | dbo.Servidores_Conexiones | 0.2717 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | solicitudes_catalogos | 10 | Pruebas / Test | dbo.Auditoria_Inventario_Provisional | 0.1585 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | tareas_inventario | 26 | Pruebas / Test | dbo.Tareas_Inventario | 0.392 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | tareas_sistema | 22 | Pruebas / Test | dbo.Sistema_TurnosOperativosUnidad | 0.2744 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | users | 16 | Pruebas / Test | dbo.Sistema_MigracionMongoColecciones | 0.1722 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| test_database | workflow_inventarios | 28 | Pruebas / Test | dbo.Workflow_Inventarios | 0.3392 | MEDIO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | Base de pruebas; respaldo certificado. Requiere autorización final. |
| cab003 | auditorias_programadas | 0 | Auditoría / Logs | - | 0 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |
| cab003 | auditorias_programadas_log | 0 | Auditoría / Logs | dbo.Compras_Sync_Log | 0.075 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |
| cab003 | cargos_economicos | 5 | Legacy sin uso detectado | dbo.Comercial_Ventas_Dia_Abiertas_v2_Backup_FechaOperacion_20260521 | 0.1705 | MEDIO | VALIDAR_MANUALMENTE | Sin equivalente SQL claro. |
| cab003 | cargos_economicos_log | 0 | Auditoría / Logs | dbo.CavaSocios_Cargos | 0.09 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |
| cab003 | detalle_diferencias | 18 | Legacy sin uso detectado | dbo.Sistema_TurnosOperativosUnidad | 0.1731 | MEDIO | VALIDAR_MANUALMENTE | Sin equivalente SQL claro. |
| cab003 | notificaciones_log | 4 | Auditoría / Logs | dbo.Operativo_Notificaciones_Log | 0.2977 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| cab003 | responsabilidad_economica | 5 | Configuración | dbo.Comercial_Ventas_Dia_Abiertas_v2_Backup_FechaOperacion_20260521 | 0.1786 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| cab003 | responsabilidad_historial | 10 | Usuarios / Auth / RBAC | dbo.propinas_tpv_historial | 0.2163 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| cab003 | users | 0 | Usuarios / Auth / RBAC | - | 0 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |
| cab003 | workflow_inventarios | 0 | Inventarios | dbo.Workflow_Inventarios | 0.3 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |
| edarsahub | notification_config | 11 | Configuración | dbo.Compras_ConciliacionSATEstatus | 0.2167 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| edarsahub | notification_log | 0 | Auditoría / Logs | dbo.Compras_Sync_Log | 0.09 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |
| edarsahub | notification_queue | 0 | Vacía / Sin datos | - | 0 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |
| edarsahub | notification_templates | 11 | Legacy sin uso detectado | dbo.CRM_Cat_OrigenLead | 0.23 | MEDIO | VALIDAR_MANUALMENTE | Sin equivalente SQL claro. |
| edarsahub | users_legacy_backup_auth_rbac_20260603 | 0 | Usuarios / Auth / RBAC | dbo.Backup_P5_RBAC_Permisos | 0.1 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |
| edarsahub | users_legacy_backup_auth_rbac_20260604 | 1 | Usuarios / Auth / RBAC | dbo.Finanzas_PropinasConfig | 0.19 | ALTO | MIGRAR_ANTES_DE_BORRAR | Sensible sin match SQL claro. |
| stock_tracker | rbac_permisos | 0 | Usuarios / Auth / RBAC | dbo.RBAC_Permisos | 0.225 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |
| stock_tracker | rbac_roles | 0 | Usuarios / Auth / RBAC | dbo.Sistema_RBAC_Roles | 0.18 | BAJO | CANDIDATA_A_BORRADO_POSTERIOR | Colección vacía; respaldo certificado. |

## Criterio de uso

Este reporte NO autoriza borrado. Sirve para decidir el siguiente script quirúrgico.

```text
CONSERVAR / MIGRAR_ANTES_DE_BORRAR = no borrar.
VALIDAR_MANUALMENTE = revisar antes de borrar.
CANDIDATA_A_BORRADO_POSTERIOR = puede entrar a script futuro, con autorización explícita.
BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO = candidata fuerte si se confirma que no es productiva.
```
