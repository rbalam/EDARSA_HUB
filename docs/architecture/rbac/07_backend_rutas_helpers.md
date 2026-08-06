# Backend, rutas y helpers

| Archivo | Función | Método | Ruta | Auth | Guard | Permisos | Alcances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| backend/api/admin_cache.py | clear_preview_cache | POST | /clear-preview | Sí | No |  |  |
| backend/api/admin_cache.py | get_cache_status | GET | /status | Sí | No |  |  |
| backend/api/admin_core_connections.py | get_core_audit_log | GET | /audit-log | Sí | No |  |  |
| backend/api/admin_core_connections.py | get_core_connection_detail | GET | /{server_id} | Sí | No |  |  |
| backend/api/admin_core_connections.py | test_core_connection | POST | /{server_id}/test | Sí | No |  |  |
| backend/api/admin_data_quality.py | audit_merida_duplicates | GET | /audit/merida-duplicates | Sí | No |  | unidad_negocio_id |
| backend/api/admin_data_quality.py | audit_generic_duplicates | GET | /audit/generic-duplicates | Sí | No |  | unidad_negocio_id |
| backend/api/admin_data_quality.py | verify_merida_consolidation | GET | /verify/merida-consolidation | Sí | No |  | unidad_negocio_id |
| backend/api/admin_scheduler_resync.py | validar_resync | POST | /resync/validate | Sí | No |  | unidad_negocio_id |
| backend/api/admin_scheduler_resync.py | ejecutar_resync | POST | /resync/execute | Sí | No |  | unidad_negocio_id |
| backend/api/admin_scheduler_resync.py | obtener_historial_resync | GET | /resync/history | Sí | Sí | SCHEDULER_VER | unidad_negocio_id |
| backend/api/admin_scheduler_resync.py | obtener_opciones_resync | GET | /resync/options | Sí | Sí | SCHEDULER_VER |  |
| backend/api/admin_scheduler_resync.py | listar_catalogo_sync | GET | /resync/catalogo | Sí | Sí | SCHEDULER_VER |  |
| backend/api/admin_scheduler_resync.py | crear_tipo_sync | POST | /resync/catalogo | Sí | No |  |  |
| backend/api/admin_scheduler_resync.py | actualizar_tipo_sync | PUT | /resync/catalogo/{codigo} | Sí | No |  |  |
| backend/api/admin_scheduler_resync.py | toggle_tipo_sync | PATCH | /resync/catalogo/{codigo}/toggle | Sí | No |  |  |
| backend/api/admin_scheduler_resync.py | resolver_dependencias_sync | POST | /resync/resolve | Sí | Sí | SCHEDULER_VER |  |
| backend/api/catalogos_sistemas.py | listar_sistemas_explorables | GET | /explorables | Sí | No |  |  |
| backend/api/catalogos_sistemas.py | listar_sistemas_explorables_dinamico | GET | /explorables-dinamico | Sí | No |  |  |
| backend/api/catalogos_sistemas.py | listar_sistemas_sync_ventas | GET | /sync-ventas | Sí | No |  |  |
| backend/api/catalogos_sistemas.py | listar_capacidades_disponibles | GET | /meta/capacidades-disponibles | Sí | No |  |  |
| backend/api/catalogos_sistemas.py | listar_modulos_disponibles | GET | /meta/modulos-disponibles | Sí | No |  |  |
| backend/api/catalogos_sistemas.py | normalizar_system_type | GET | /normalizar/{system_type} | Sí | No |  |  |
| backend/api/catalogos_sistemas.py | diagnostico_sistema | GET | /diagnostico/{system_type} | Sí | No |  |  |
| backend/api/catalogos_sistemas.py | listar_sistemas_por_capacidad | GET | /capacidades/{capacidad} | Sí | No |  |  |
| backend/api/catalogos_sistemas.py | listar_capacidades_sistema | GET | /{codigo_sistema}/capacidades | Sí | No |  |  |
| backend/api/catalogos_sistemas.py | obtener_sistema | GET | /{codigo_sistema} | Sí | No |  |  |
| backend/api/dba_credential_p0d.py | get_dba_credential_status | GET | /status | Sí | No |  |  |
| backend/api/dba_credential_p0d.py | register_dba_credential | POST | /register | Sí | No |  |  |
| backend/api/dba_credential_p0d.py | clear_dba_credential | DELETE | /clear | Sí | No |  |  |
| backend/api/dba_credential_p0d.py | test_dba_connection | GET | /test-connection | Sí | No |  |  |
| backend/api/dba_credential_p0d.py | execute_dba_diagnostic | POST | /execute-diagnostic | Sí | No |  |  |
| backend/api/sync_receiver.py | sync_kpis | POST | /sync/kpis | No | No |  | empresa_id, sucursal_id |
| backend/api/sync_receiver.py | sync_heartbeat | POST | /sync/heartbeat | No | No |  |  |
| backend/api/sync_receiver.py | test_agent_auth | GET | /sync/test-auth | No | No |  |  |
| backend/api/sync_receiver.py | generate_agent_token_endpoint | POST | /admin/agents/generate-token | Sí | No | SYNC_AGENT_GENERAR |  |
| backend/core/centro_control/routes.py | obtener_salud_sistema | GET | /salud | Sí | No |  |  |
| backend/core/centro_control/routes.py | obtener_resumen_ejecutivo | GET | /salud/resumen | Sí | No |  |  |
| backend/core/centro_control/routes.py | ejecutar_checks_regresion | POST | /regresiones | Sí | No |  |  |
| backend/core/centro_control/routes.py | obtener_regresiones_modulo | GET | /regresiones/{modulo} | Sí | No |  |  |
| backend/core/centro_control/routes.py | obtener_estado_fuentes | GET | /fuentes | Sí | No |  |  |
| backend/core/centro_control/routes.py | obtener_alertas | GET | /alertas | Sí | No |  |  |
| backend/core/centro_control/routes.py | reconocer_alerta | POST | /alertas/acknowledge | Sí | No |  |  |
| backend/core/centro_control/routes.py | obtener_historial | GET | /historial | Sí | No |  |  |
| backend/core/centro_control/routes.py | obtener_matriz_resolucion | GET | /matriz-resolucion | Sí | No |  |  |
| backend/core/centro_control/routes.py | ping_centro_control | GET | /ping | No | No |  |  |
| backend/core/centro_control/routes.py | obtener_estado_general | GET | /estado | Sí | No |  |  |
| backend/core/centro_control/routes.py | obtener_estado_jobs | GET | /jobs | Sí | No |  |  |
| backend/core/centro_control/routes.py | crear_scheduler_job | POST | /jobs | Sí | No |  |  |
| backend/core/centro_control/routes.py | ejecutar_scheduler_job_manual | POST | /jobs/{job_id}/run | Sí | No |  |  |
| backend/core/centro_control/routes.py | obtener_bitacora | GET | /bitacora | Sí | No |  |  |
| backend/core/centro_control/routes.py | registrar_cambio_bitacora | POST | /bitacora | Sí | No |  |  |
| backend/core/centro_control/routes.py | obtener_metricas_estabilidad | GET | /metricas | Sí | No |  |  |
| backend/core/centro_control/routes.py | websocket_status | GET | /ws/status | Sí | No |  |  |
| backend/core/centro_control/routes.py | notificar_alerta_critica | POST | /notificar/alerta-critica | Sí | No |  |  |
| backend/core/centro_control/routes.py | notificar_test | POST | /notificar/test | Sí | No |  |  |
| backend/core/centro_control/routes.py | obtener_config_email | GET | /email/config | Sí | No |  |  |
| backend/core/centro_control/routes.py | enviar_email_prueba | POST | /email/test | Sí | No |  |  |
| backend/core/centro_control/routes.py | enviar_alerta_critica_email | POST | /email/alerta-critica | Sí | No |  |  |
| backend/core/centro_control/routes.py | obtener_config_whatsapp | GET | /whatsapp/config | Sí | No |  |  |
| backend/core/centro_control/routes.py | enviar_whatsapp_prueba | POST | /whatsapp/test | Sí | No |  |  |
| backend/core/centro_control/routes.py | enviar_alerta_critica_whatsapp | POST | /whatsapp/alerta-critica | Sí | No |  |  |
| backend/core/centro_control/routes.py | obtener_config_notificaciones | GET | /notificaciones/config | Sí | No |  |  |
| backend/core/centro_control/routes.py | listar_destinatarios | GET | /destinatarios | Sí | No |  |  |
| backend/core/centro_control/routes.py | resumen_destinatarios | GET | /destinatarios/resumen | Sí | No |  |  |
| backend/core/centro_control/routes.py | crear_destinatario | POST | /destinatarios | Sí | No |  |  |
| backend/core/centro_control/routes.py | actualizar_destinatario | PUT | /destinatarios/{recipient_id} | Sí | No |  |  |
| backend/core/centro_control/routes.py | eliminar_destinatario | DELETE | /destinatarios/{recipient_id} | Sí | No |  |  |
| backend/core/communications/routes.py | list_configs | GET | /config | Sí | Sí | NOTIFICACIONES_VER |  |
| backend/core/communications/routes.py | get_config | GET | /config/{config_id} | Sí | Sí | NOTIFICACIONES_VER |  |
| backend/core/communications/routes.py | create_config | POST | /config | Sí | No | NOTIFICACIONES_CONFIGURAR |  |
| backend/core/communications/routes.py | update_config | PUT | /config/{config_id} | Sí | No | NOTIFICACIONES_CONFIGURAR |  |
| backend/core/communications/routes.py | list_templates | GET | /templates | Sí | Sí | NOTIFICACIONES_VER |  |
| backend/core/communications/routes.py | get_template | GET | /templates/{template_id} | Sí | Sí | NOTIFICACIONES_VER |  |
| backend/core/communications/routes.py | create_template | POST | /templates | Sí | No | NOTIFICACIONES_CONFIGURAR |  |
| backend/core/communications/routes.py | update_template | PUT | /templates/{template_id} | Sí | No | NOTIFICACIONES_CONFIGURAR |  |
| backend/core/communications/routes.py | get_notification_logs | GET | /log | Sí | Sí | NOTIFICACIONES_VER |  |
| backend/core/communications/routes.py | get_notification_stats | GET | /stats | Sí | Sí | NOTIFICACIONES_VER |  |
| backend/core/communications/routes.py | get_queue_status | GET | /queue-status | Sí | Sí | NOTIFICACIONES_VER |  |
| backend/core/communications/routes.py | test_notification | POST | /test | Sí | Sí |  |  |
| backend/core/communications/routes.py | reprocess_queue | POST | /reprocesar | Sí | No | NOTIFICACIONES_CONFIGURAR |  |
| backend/core/communications/routes.py | initialize_notification_system | POST | /inicializar | Sí | No | NOTIFICACIONES_CONFIGURAR |  |
| backend/core/communications/routes.py | list_providers | GET | /providers | Sí | Sí | NOTIFICACIONES_VER |  |
| backend/core/communications/routes.py | get_provider | GET | /providers/{provider_id} | Sí | Sí | NOTIFICACIONES_VER |  |
| backend/core/communications/routes.py | get_provider_runtime_status | GET | /provider-status | Sí | Sí | NOTIFICACIONES_VER |  |
| backend/core/communications/routes.py | test_real_notification | POST | /test-real | Sí | Sí |  |  |
| backend/core/communications/routes.py | configure_twilio_provider | POST | /config/set-twilio | Sí | No | NOTIFICACIONES_CONFIGURAR |  |
| backend/core/communications/routes.py | update_event_provider | PUT | /config/{config_id}/set-provider | Sí | No | NOTIFICACIONES_CONFIGURAR |  |
| backend/core/rbac/routes.py | listar_roles | GET | /roles | Sí | No | RBAC_VER |  |
| backend/core/rbac/routes.py | crear_rol | POST | /roles | Sí | No |  |  |
| backend/core/rbac/routes.py | obtener_rol | GET | /roles/{rol_id} | Sí | No | RBAC_VER |  |
| backend/core/rbac/routes.py | actualizar_rol | PUT | /roles/{rol_id} | Sí | No |  |  |
| backend/core/rbac/routes.py | eliminar_rol | DELETE | /roles/{rol_id} | Sí | No |  |  |
| backend/core/rbac/routes.py | listar_permisos | GET | /permisos | Sí | No | RBAC_VER |  |
| backend/core/rbac/routes.py | asignar_rol | POST | /asignar | Sí | No |  | sucursal_id |
| backend/core/rbac/routes.py | revocar_rol | POST | /revocar | Sí | No |  | sucursal_id |
| backend/core/rbac/routes.py | obtener_permisos_usuario | GET | /usuario/{user_id}/permisos | Sí | No |  |  |
| backend/core/rbac/routes.py | obtener_mis_permisos | GET | /mis-permisos | Sí | No |  |  |
| backend/core/rbac/routes.py | obtener_audit_logs | GET | /audit | Sí | No |  |  |
| backend/core/rbac/routes.py | verificar_permiso | POST | /verificar | Sí | Sí |  |  |
| backend/core/scheduler/routes.py | get_scheduler_status | GET | /status | Sí | Sí | SCHEDULER_VER |  |
| backend/core/scheduler/routes.py | get_job_info | GET | /jobs/{job_id} | Sí | Sí | SCHEDULER_VER |  |
| backend/core/scheduler/routes.py | run_job_now | POST | /jobs/{job_id}/run | Sí | No |  |  |
| backend/core/scheduler/routes.py | run_netpay_manual | POST | /netpay/run | Sí | No |  |  |
| backend/core/scheduler/routes.py | pause_job | POST | /jobs/{job_id}/pause | Sí | No | SCHEDULER_GESTIONAR |  |
| backend/core/scheduler/routes.py | resume_job | POST | /jobs/{job_id}/resume | Sí | No | SCHEDULER_GESTIONAR |  |
| backend/core/scheduler/routes.py | get_job_logs | GET | /logs | Sí | Sí | SCHEDULER_VER |  |
| backend/core/scheduler/routes.py | get_job_stats | GET | /logs/stats | Sí | Sí | SCHEDULER_VER |  |
| backend/core/scheduler/routes.py | get_active_locks | GET | /locks | Sí | Sí | SCHEDULER_VER |  |
| backend/core/scheduler/routes.py | force_release_lock | DELETE | /locks/{job_name} | Sí | No |  |  |
| backend/core/scheduler/routes.py | get_scheduler_config | GET | /config | Sí | Sí | SCHEDULER_VER |  |
| backend/modules/admin_sql/rbac_audit_routes.py | execute_all_users_rbac_audit | POST | /users/execute | Sí | No |  |  |
| backend/modules/admin_sql/rbac_audit_routes.py | execute_schema_convergence_audit | POST | /schema/execute | Sí | No |  |  |
| backend/modules/admin_sql/rbac_audit_routes.py | execute_schema_section_audit | POST | /schema/sections/{section_number}/execute | Sí | No |  |  |
| backend/modules/admin_sql/routes.py | get_users | GET | /users | Sí | No |  |  |
| backend/modules/admin_sql/routes.py | toggle_user_activo | PATCH | /users/{user_id}/toggle-activo | Sí | No |  |  |
| backend/modules/admin_sql/routes.py | get_roles | GET | /roles | Sí | No |  |  |
| backend/modules/admin_sql/routes.py | get_modulos | GET | /roles/modulos | Sí | No |  |  |
| backend/modules/admin_sql/routes.py | get_servers | GET | /servers | Sí | No |  |  |
| backend/modules/admin_sql/routes.py | get_usuarios_asignables | GET | /usuarios-asignables | Sí | No |  |  |
| backend/modules/admin_sql/routes.py | get_catalogos_disponibles | GET | /catalogos-disponibles | Sí | No |  |  |
| backend/modules/admin_sql/routes.py | save_permisos_catalogos | POST | /permisos-catalogos | Sí | No | puede_autorizar, puede_solicitar |  |
| backend/modules/admin_sql/routes.py | update_role_sql | PUT | /roles/{role_id} | Sí | No |  |  |
| backend/modules/admin_sql/routes.py | create_role_sql | POST | /roles | Sí | No |  |  |
| backend/modules/admin_sql/routes.py | delete_role_sql | DELETE | /roles/{role_id} | Sí | No |  |  |
| backend/modules/alertas_estrategicas/routes.py | resumen_alertas | GET | /resumen | Sí | No |  |  |
| backend/modules/api_connections/universal_test_routes.py | execute_api_connection_test | POST | /api-connections/{connection_id}/universal-query-test | Sí | No |  |  |
| backend/modules/api_connections/universal_test_routes.py | test_api_connection_secure | POST | /api-connections/{connection_id}/test-connection | Sí | No |  |  |
| backend/modules/api_connections/universal_test_routes.py | test_api_connectivity_simple | POST | /api-connections/{connection_id}/test-connectivity | Sí | No |  |  |
| backend/modules/auth/routes.py | register | POST | /auth/register | No | No |  |  |
| backend/modules/auth/routes.py | login | POST | /auth/login | No | No |  |  |
| backend/modules/auth/routes.py | logout | POST | /auth/logout | No | No |  |  |
| backend/modules/auth/routes.py | refresh_tokens | POST | /auth/refresh | Sí | No |  |  |
| backend/modules/auth/routes.py | logout_all_sessions | POST | /auth/logout-all | Sí | No |  |  |
| backend/modules/auth/routes.py | get_me | GET | /auth/me | Sí | No |  |  |
| backend/modules/auth/routes.py | get_my_context | GET | /auth/me/context | Sí | No |  |  |
| backend/modules/auth/routes.py | change_context | POST | /auth/context | Sí | No |  | empresa_id, sucursal_id |
| backend/modules/auth/routes.py | get_my_empresas | GET | /auth/empresas | Sí | No |  |  |
| backend/modules/auth/routes.py | get_my_access_context | GET | /auth/me/access-context | Sí | No |  |  |
| backend/modules/auth/routes.py | get_my_effective_permissions | GET | /auth/me/effective-permissions | Sí | No |  |  |
| backend/modules/auth/routes.py | get_my_menu_permissions | GET | /auth/me/menu-permissions | Sí | No |  | scope |
| backend/modules/auth/routes.py | create_user_admin | POST | /users | Sí | No |  |  |
| backend/modules/auth/routes.py | get_users | GET | /users | Sí | No |  |  |
| backend/modules/auth/routes.py | update_user | PUT | /users/{user_id} | Sí | No |  |  |
| backend/modules/auth/routes.py | delete_user | DELETE | /users/{user_id} | Sí | No |  |  |
| backend/modules/auth/routes.py | update_user_permissions | PUT | /users/{user_id}/permissions | Sí | No |  |  |
| backend/modules/auth/routes.py | get_modulos_disponibles | GET | /roles/modulos | Sí | No |  |  |
| backend/modules/auth/routes.py | get_roles | GET | /roles | Sí | No |  |  |
| backend/modules/auth/routes.py | create_role | POST | /roles | Sí | No |  |  |
| backend/modules/auth/routes.py | update_role | PUT | /roles/{role_id} | Sí | No |  |  |
| backend/modules/auth/routes.py | delete_role | DELETE | /roles/{role_id} | Sí | No |  |  |
| backend/modules/auth/routes.py | forgot_password | POST | /auth/forgot-password | No | No |  |  |
| backend/modules/auth/routes.py | reset_password_endpoint | POST | /auth/reset-password | No | No |  |  |
| backend/modules/backfill_corporativo/routes.py | get_backfill_modulos | GET | /modulos | Sí | No |  |  |
| backend/modules/catalogo/routes.py | obtener_clasificacion | GET | /clasificacion | Sí | No |  | scope |
| backend/modules/catalogos/routes.py | listar_sistemas | GET | /sistemas | Sí | No |  |  |
| backend/modules/catalogos/routes.py | listar_sistemas_activos | GET | /sistemas/activos | Sí | No | puede_crear, puede_solicitar |  |
| backend/modules/catalogos/routes.py | solicitar_sistema | POST | /sistemas/solicitar | Sí | No |  |  |
| backend/modules/catalogos/routes.py | crear_sistema | POST | /sistemas | Sí | No |  |  |
| backend/modules/catalogos/routes.py | actualizar_sistema | PUT | /sistemas/{sistema_id} | Sí | No |  |  |
| backend/modules/catalogos/routes.py | toggle_sistema_activo | PATCH | /sistemas/{sistema_id}/toggle-activo | Sí | No |  |  |
| backend/modules/catalogos/routes.py | autorizar_sistema | PATCH | /sistemas/{sistema_id}/autorizar | Sí | No |  |  |
| backend/modules/catalogos/routes.py | rechazar_sistema | PATCH | /sistemas/{sistema_id}/rechazar | Sí | No |  |  |
| backend/modules/catalogos/routes.py | listar_dominios | GET | /dominios | Sí | No |  |  |
| backend/modules/catalogos/routes.py | listar_catalogo | GET | /tabla/{tabla} | Sí | No |  |  |
| backend/modules/catalogos/routes.py | obtener_registro | GET | /tabla/{tabla}/{id} | Sí | No |  |  |
| backend/modules/catalogos/routes.py | obtener_estructura | GET | /estructura/{tabla} | Sí | No |  |  |
| backend/modules/catalogos/routes.py | crear_registro | POST | /tabla/{tabla} | Sí | No |  |  |
| backend/modules/catalogos/routes.py | actualizar_registro | PUT | /tabla/{tabla}/{id} | Sí | No |  |  |
| backend/modules/catalogos/routes.py | desactivar_registro | PUT | /tabla/{tabla}/{id}/desactivar | Sí | No |  |  |
| backend/modules/catalogos/routes.py | activar_registro | PUT | /tabla/{tabla}/{id}/activar | Sí | No |  |  |
| backend/modules/catalogos/routes.py | crear_tablas_nuevas | POST | /admin/crear-tablas | Sí | No |  |  |
| backend/modules/catalogos/routes.py | verificar_tablas_nuevas | GET | /admin/verificar-tablas | Sí | No |  |  |
| backend/modules/catalogos/routes.py | obtener_script_ddl | GET | /admin/script-ddl | Sí | No |  |  |
| backend/modules/catalogos_workflow_compat/routes.py | compat_get_catalogos_disponibles | GET | /sistema/catalogos-disponibles | Sí | No |  |  |
| backend/modules/catalogos_workflow_compat/routes.py | compat_put_catalogo_niveles | PUT | /sistema/catalogos/{catalogo_id}/niveles | Sí | No |  |  |
| backend/modules/catalogos_workflow_compat/routes.py | compat_get_permisos_catalogo | GET | /sistema/catalogos/permisos/{user_id} | Sí | No |  |  |
| backend/modules/catalogos_workflow_compat/routes.py | compat_get_mis_permisos_catalogos | GET | /sistema/mis-permisos-catalogos | Sí | No |  |  |
| backend/modules/catalogos_workflow_compat/routes.py | compat_post_permisos_catalogo | POST | /sistema/permisos-catalogos | Sí | No |  |  |
| backend/modules/catalogos_workflow_compat/routes.py | compat_get_usuarios_asignables | GET | /sistema/usuarios-asignables | Sí | No |  |  |
| backend/modules/catalogos_workflow_compat/routes.py | compat_get_solicitudes_catalogo | GET | /sistema/catalogos/solicitudes | Sí | No |  |  |
| backend/modules/catalogos_workflow_compat/routes.py | compat_get_solicitud | GET | /sistema/solicitudes/{solicitud_id} | Sí | No |  |  |
| backend/modules/catalogos_workflow_compat/routes.py | compat_get_historial_solicitud | GET | /sistema/solicitudes/{solicitud_id}/historial | Sí | No |  |  |
| backend/modules/catalogos_workflow_compat/routes.py | compat_post_solicitud_catalogo | POST | /sistema/solicitudes | Sí | No |  |  |
| backend/modules/catalogos_workflow_compat/routes.py | compat_aprobar_solicitud | POST | /sistema/solicitudes/{solicitud_id}/aprobar | Sí | No |  |  |
| backend/modules/catalogos_workflow_compat/routes.py | compat_rechazar_solicitud | POST | /sistema/solicitudes/{solicitud_id}/rechazar | Sí | No |  |  |
| backend/modules/catalogos_workflow_compat/routes.py | compat_liberar_solicitud | POST | /sistema/solicitudes/{solicitud_id}/liberar | Sí | No |  |  |
| backend/modules/catalogos_workflow_compat/routes.py | compat_corregir_solicitud | PUT | /sistema/solicitudes/{solicitud_id}/corregir | Sí | No |  |  |
| backend/modules/catalogos_workflow_compat/routes.py | compat_get_mis_tareas | GET | /sistema/mis-tareas | Sí | No |  |  |
| backend/modules/catalogos_workflow_compat/routes.py | compat_get_tareas | GET | /sistema/tareas | Sí | No |  |  |
| backend/modules/catalogos_workflow_compat/routes.py | compat_post_tarea | POST | /sistema/tareas | Sí | No |  |  |
| backend/modules/catalogos_workflow_sql/routes.py | get_catalogos_disponibles | GET | /config | Sí | No |  |  |
| backend/modules/catalogos_workflow_sql/routes.py | put_catalogo_niveles | PUT | /config/{catalogo_id}/niveles | Sí | No |  |  |
| backend/modules/catalogos_workflow_sql/routes.py | get_permisos_catalogo | GET | /permisos/usuario/{user_id} | Sí | No |  |  |
| backend/modules/catalogos_workflow_sql/routes.py | post_permisos_catalogo | POST | /permisos | Sí | No |  |  |
| backend/modules/catalogos_workflow_sql/routes.py | get_solicitudes_catalogo | GET | /solicitudes | Sí | No |  |  |
| backend/modules/catalogos_workflow_sql/routes.py | post_solicitud_catalogo | POST | /solicitudes | Sí | No |  |  |
| backend/modules/catalogos_workflow_sql/routes.py | put_estado_solicitud_catalogo | PUT | /solicitudes/{solicitud_id}/estado | Sí | No |  |  |
| backend/modules/catalogos_workflow_sql/routes.py | get_tareas | GET | /tareas | Sí | No |  |  |
| backend/modules/catalogos_workflow_sql/routes.py | post_tarea | POST | /tareas | Sí | No |  |  |
| backend/modules/cava_socios/routes.py | get_dashboard | GET | /dashboard | Sí | No |  | empresa_id |
| backend/modules/cava_socios/routes.py | listar_socios | GET | /socios | Sí | No |  | empresa_id |
| backend/modules/cava_socios/routes.py | obtener_socio | GET | /socios/{socio_id} | Sí | No |  |  |
| backend/modules/cava_socios/routes.py | crear_socio | POST | /socios | Sí | No |  | empresa_id |
| backend/modules/cava_socios/routes.py | registrar_botella | POST | /socios/{socio_id}/botellas | Sí | No |  | empresa_id |
| backend/modules/cava_socios/routes.py | registrar_consumo | POST | /botellas/{botella_id}/consumo | Sí | No |  |  |
| backend/modules/cava_socios/routes.py | descargar_ficha_socio | GET | /reportes/socio/{socio_id}/ficha | Sí | No |  |  |
| backend/modules/cava_socios/routes.py | descargar_historial_consumos | GET | /reportes/socio/{socio_id}/consumos | Sí | No |  |  |
| backend/modules/cava_socios/routes.py | descargar_estado_cuenta | GET | /reportes/socio/{socio_id}/estado-cuenta | Sí | No |  |  |
| backend/modules/cava_socios/routes.py | enviar_reporte_socio | POST | /socios/{socio_id}/enviar-reporte | Sí | No |  |  |
| backend/modules/cava_socios/routes.py | enviar_todos_reportes_socio | POST | /socios/{socio_id}/enviar-todos-reportes | Sí | No |  |  |
| backend/modules/comercial/canonical_detail_routes.py | comercial_detalle_movimientos_canonical | GET | /comercial/detalle-movimientos/{server_id} | Sí | No |  | unidad_negocio_id |
| backend/modules/comercial/inteligencia_comercial_routes.py | get_inteligencia_kpis | GET | /kpis | Sí | No |  |  |
| backend/modules/comercial/inteligencia_comercial_routes.py | get_ventas_comparativo | GET | /ventas-comparativo | Sí | No |  |  |
| backend/modules/comercial/inteligencia_comercial_routes.py | get_pax_inteligencia | GET | /pax | Sí | No |  |  |
| backend/modules/comercial/inteligencia_comercial_routes.py | get_unidades_inteligencia | GET | /unidades | Sí | No |  |  |
| backend/modules/comercial/inteligencia_comercial_routes.py | get_sync_status_inteligencia | GET | /sync-status | Sí | No |  |  |
| backend/modules/comercial/inteligencia_comercial_routes.py | get_tendencia_diaria | GET | /tendencia | Sí | No |  |  |
| backend/modules/comercial/inteligencia_comercial_routes.py | get_kpis_por_unidad | GET | /kpis-por-unidad | Sí | No |  | unidad_negocio_id |
| backend/modules/comercial/routes.py | tablero_ejecutivo | GET | /comercial/tablero-ejecutivo | Sí | No |  |  |
| backend/modules/comercial/routes.py | obtener_sucursales | GET | /comercial/sucursales/{server_id} | Sí | No |  | empresa_id |
| backend/modules/comercial/routes.py | comercial_metas | GET | /comercial/metas/{server_id} | Sí | No |  | sucursal_id |
| backend/modules/comercial/routes.py | comercial_ticket_perfecto | GET | /comercial/ticket-perfecto/{server_id} | Sí | No |  | sucursal_id |
| backend/modules/comercial/routes.py | comercial_ventas_tiempo | GET | /comercial/ventas-tiempo/{server_id} | Sí | No |  |  |
| backend/modules/comercial/routes.py | comercial_mesas | GET | /comercial/mesas/{server_id} | Sí | No |  | sucursal_id |
| backend/modules/comercial/routes.py | comercial_detalle_movimientos | GET | /comercial/detalle-movimientos/{server_id} | Sí | No |  |  |
| backend/modules/comercial/routes.py | ventas_precios_constantes | GET | /comercial/precios-constantes/{server_id} | Sí | No |  | sucursal_id |
| backend/modules/comercial/routes.py | comercial_reporte_pax | GET | /comercial/reporte-pax/{server_id} | Sí | No |  | sucursal_id |
| backend/modules/comercial/routes.py | comercial_dashboard | GET | /comercial/dashboard/{server_id} | Sí | No |  | sucursal_id |
| backend/modules/comercial/routes_alertas_margen.py | listar_reglas_endpoint | GET | /reglas | Sí | No |  | empresa_id, sucursal_id |
| backend/modules/comercial/routes_alertas_margen.py | crear_regla_endpoint | POST | /reglas | Sí | No |  | empresa_id, sucursal_id |
| backend/modules/comercial/routes_alertas_margen.py | obtener_regla_endpoint | GET | /reglas/{regla_id} | Sí | No |  |  |
| backend/modules/comercial/routes_alertas_margen.py | actualizar_regla_endpoint | PUT | /reglas/{regla_id} | Sí | No |  |  |
| backend/modules/comercial/routes_alertas_margen.py | desactivar_regla_endpoint | DELETE | /reglas/{regla_id} | Sí | No |  |  |
| backend/modules/comercial/routes_alertas_margen.py | resolver_regla_endpoint | GET | /resolver-regla | Sí | No |  | empresa_id, sucursal_id |
| backend/modules/comercial/routes_alertas_margen.py | evaluar_margen_endpoint | POST | /evaluar | Sí | No |  | empresa_id, sucursal_id |
| backend/modules/comercial/routes_alertas_margen.py | obtener_umbrales_endpoint | GET | /umbrales | Sí | No |  |  |
| backend/modules/comercial/routes_alertas_margen.py | obtener_estadisticas_endpoint | GET | /estadisticas | Sí | No |  |  |
| backend/modules/comercial/routes_benchmark_sectorial.py | get_sectores | GET | /sectores | Sí | Sí |  | empresa_id |
| backend/modules/comercial/routes_benchmark_sectorial.py | get_vs_sector | GET | /vs-sector | Sí | Sí |  | empresa_id |
| backend/modules/comercial/routes_benchmark_sectorial.py | get_interno | GET | /interno | Sí | Sí |  |  |
| backend/modules/comercial/routes_benchmark_sectorial.py | get_por_segmento | GET | /por-segmento | Sí | Sí |  | empresa_id |
| backend/modules/comercial/routes_competidores_enterprise.py | crear_competidor_catalogo_endpoint | POST | /competidores-catalogo | Sí | No |  |  |
| backend/modules/comercial/routes_competidores_enterprise.py | buscar_competidores_catalogo_endpoint | GET | /competidores-catalogo | Sí | No |  |  |
| backend/modules/comercial/routes_competidores_enterprise.py | relacionar_competidor_endpoint | POST | /competidores-unidad/relacionar | Sí | No |  | empresa_id |
| backend/modules/comercial/routes_competidores_enterprise.py | desrelacionar_competidor_endpoint | POST | /competidores-unidad/desrelacionar | Sí | No |  |  |
| backend/modules/comercial/routes_competidores_enterprise.py | obtener_unidades_competidor_endpoint | GET | /competidores-unidad/{competidor_catalogo_id}/unidades | Sí | No |  |  |
| backend/modules/comercial/routes_competidores_enterprise.py | listar_competidores_unidad_endpoint | GET | /competidores | Sí | No |  | empresa_id |
| backend/modules/comercial/routes_competidores_enterprise.py | obtener_competidor_unidad_endpoint | GET | /competidores/{competidor_catalogo_id} | Sí | No |  |  |
| backend/modules/comercial/routes_competidores_enterprise.py | estadisticas_competidores_endpoint | GET | /competidores-estadisticas | Sí | No |  |  |
| backend/modules/comercial/routes_ingesta_competencia.py | descargar_plantilla | GET | /plantilla | Sí | Sí |  |  |
| backend/modules/comercial/routes_ingesta_competencia.py | detalle | GET | /{ingesta_id} | Sí | Sí |  |  |
| backend/modules/comercial/routes_ingesta_competencia.py | descargar_archivo | GET | /{ingesta_id}/archivo | Sí | Sí |  |  |
| backend/modules/comercial/routes_ingesta_competencia.py | upload | POST | /upload | Sí | Sí |  | empresa_id |
| backend/modules/comercial/routes_ingesta_competencia.py | desde_link | POST | /link | Sí | Sí |  | empresa_id |
| backend/modules/comercial/routes_ingesta_competencia.py | editar_filas | PUT | /{ingesta_id}/filas | Sí | Sí |  |  |
| backend/modules/comercial/routes_ingesta_competencia.py | confirmar | POST | /{ingesta_id}/confirmar | Sí | Sí |  |  |
| backend/modules/comercial/routes_ingesta_competencia.py | rechazar | POST | /{ingesta_id}/rechazar | Sí | Sí |  |  |
| backend/modules/comercial/routes_listas_competidores.py | endpoint_obtener_lista | GET | /{lista_id} | Sí | Sí |  |  |
| backend/modules/comercial/routes_listas_competidores.py | endpoint_actualizar_lista | PUT | /{lista_id} | Sí | Sí |  |  |
| backend/modules/comercial/routes_listas_competidores.py | endpoint_desactivar_lista | DELETE | /{lista_id} | Sí | Sí |  |  |
| backend/modules/comercial/routes_listas_competidores.py | endpoint_listar_competidores_lista | GET | /{lista_id}/competidores | Sí | Sí |  |  |
| backend/modules/comercial/routes_listas_competidores.py | endpoint_agregar_competidor | POST | /{lista_id}/competidores | Sí | Sí |  |  |
| backend/modules/comercial/routes_listas_competidores.py | endpoint_quitar_competidor | DELETE | /{lista_id}/competidores/{competidor_id} | Sí | Sí |  |  |
| backend/modules/comercial/routes_listas_competidores.py | endpoint_listas_de_competidor | GET | /competidor/{competidor_id}/listas | Sí | Sí |  |  |
| backend/modules/comercial/routes_precios_sugeridos.py | get_precios_sugeridos | GET | /precios-sugeridos | Sí | Sí |  |  |
| backend/modules/comercial/routes_precios_sugeridos.py | get_rangos_vinos | GET | /reglas/vinos/rangos | Sí | Sí |  |  |
| backend/modules/comercial/routes_precios_sugeridos.py | post_crear_rango_vino | POST | /reglas/vinos/rangos | Sí | Sí |  |  |
| backend/modules/comercial/routes_precios_sugeridos.py | put_actualizar_rango_vino | PUT | /reglas/vinos/rangos/{rango_id} | Sí | Sí |  |  |
| backend/modules/comercial/routes_precios_sugeridos.py | patch_desactivar_rango_vino | PATCH | /reglas/vinos/rangos/{rango_id}/desactivar | Sí | Sí |  |  |
| backend/modules/comercial/routes_precios_sugeridos.py | patch_activar_rango_vino | PATCH | /reglas/vinos/rangos/{rango_id}/activar | Sí | Sí |  |  |
| backend/modules/comercial/routes_pricing_ai.py | endpoint_analizar_producto | POST | /analizar-producto | Sí | Sí |  | empresa_id |
| backend/modules/comercial/routes_pricing_ai.py | endpoint_sugerir_comparables | POST | /sugerir-comparables | Sí | Sí |  | empresa_id |
| backend/modules/comercial/routes_pricing_ai.py | endpoint_generar_justificacion | POST | /generar-justificacion | Sí | Sí |  | empresa_id |
| backend/modules/comercial/routes_pricing_ai.py | endpoint_analizar_benchmark | POST | /analizar-benchmark | Sí | Sí |  | empresa_id |
| backend/modules/comercial/routes_pricing_ai.py | endpoint_obtener_analisis | GET | /analisis/{analisis_id} | Sí | Sí |  |  |
| backend/modules/comercial/routes_pricing_ai.py | health_check_ia | GET | /health | No | No | sin_configurar |  |
| backend/modules/comercial/routes_pricing_ai.py | endpoint_dashboard_metricas | GET | /dashboard/metricas | Sí | Sí |  | empresa_id |
| backend/modules/comercial/routes_pricing_ai.py | endpoint_estadisticas_competidores | GET | /dashboard/estadisticas-competidores | Sí | Sí |  | empresa_id |
| backend/modules/comercial/routes_pricing_ia.py | listar_perfiles | GET | /perfil-unidad | Sí | Sí |  | empresa_id |
| backend/modules/comercial/routes_pricing_ia.py | obtener_perfil | GET | /perfil-unidad/{unidad_negocio_pk} | Sí | Sí |  |  |
| backend/modules/comercial/routes_pricing_ia.py | crear_perfil | POST | /perfil-unidad | Sí | Sí |  |  |
| backend/modules/comercial/routes_pricing_ia.py | actualizar_perfil | PUT | /perfil-unidad/{perfil_id} | Sí | Sí |  |  |
| backend/modules/comercial/routes_pricing_ia.py | listar_todos_competidores | GET | /competidores | Sí | Sí |  | empresa_id |
| backend/modules/comercial/routes_pricing_ia.py | obtener_competidor | GET | /competidores/{competidor_id} | Sí | Sí |  |  |
| backend/modules/comercial/routes_pricing_ia.py | crear_nuevo_competidor | POST | /competidores | Sí | Sí |  |  |
| backend/modules/comercial/routes_pricing_ia.py | actualizar_competidor_existente | PUT | /competidores/{competidor_id} | Sí | Sí |  |  |
| backend/modules/comercial/routes_pricing_ia.py | eliminar_competidor | DELETE | /competidores/{competidor_id} | Sí | Sí |  |  |
| backend/modules/comercial/routes_pricing_ia.py | listar_items_competidor | GET | /competidores/{competidor_id}/menu-items | Sí | Sí |  |  |
| backend/modules/comercial/routes_pricing_ia.py | crear_item_menu | POST | /competidores/{competidor_id}/menu-items | Sí | Sí |  |  |
| backend/modules/comercial/routes_pricing_ia.py | actualizar_item_menu | PUT | /competidores/menu-items/{menu_item_id} | Sí | Sí |  |  |
| backend/modules/comercial/routes_pricing_ia.py | eliminar_item_menu | DELETE | /competidores/menu-items/{menu_item_id} | Sí | Sí |  |  |
| backend/modules/comercial/routes_pricing_ia.py | listar_benchmarks_productos | GET | /benchmark/productos | Sí | Sí |  | empresa_id |
| backend/modules/comercial/routes_pricing_ia.py | obtener_benchmark_producto | GET | /benchmark/productos/{producto_id} | Sí | Sí |  |  |
| backend/modules/comercial/routes_pricing_ia.py | crear_benchmark_producto | POST | /benchmark/productos | Sí | Sí |  |  |
| backend/modules/comercial/routes_pricing_ia.py | actualizar_benchmark_producto | PUT | /benchmark/productos/{benchmark_id} | Sí | Sí |  |  |
| backend/modules/comercial/routes_pricing_ia.py | validar_benchmark_producto | POST | /benchmark/productos/{benchmark_id}/validar | Sí | Sí |  |  |
| backend/modules/comercial/routes_pricing_ia.py | eliminar_benchmark_producto | DELETE | /benchmark/productos/{benchmark_id} | Sí | Sí |  |  |
| backend/modules/comercial/routes_pricing_ia.py | obtener_resumen | GET | /benchmark/resumen/{unidad_negocio_pk} | Sí | Sí |  | empresa_id |
| backend/modules/comercial/routes_pricing_ia.py | obtener_estado_preparacion | GET | /benchmark/estado-preparacion/{unidad_negocio_pk} | Sí | Sí |  | empresa_id |
| backend/modules/comercial/routes_pricing_ia.py | calcular_precio_base | POST | /precios-sugeridos/calcular-base | Sí | Sí |  |  |
| backend/modules/comercial/routes_pricing_ia.py | health_check | GET | /pricing-ia/health | No | No |  |  |
| backend/modules/comercial_analytics/routes.py | commercial_drilldown | POST | /drilldown | Sí | No |  | allowed_units |
| backend/modules/comercial_analytics/routes.py | commercial_tickets | GET | /tickets | Sí | No |  | allowed_units, unidad_negocio_id |
| backend/modules/comercial_analytics/routes.py | commercial_ticket_detail | GET | /tickets/{ticket_pk} | Sí | No |  | allowed_units |
| backend/modules/comercial_analytics/routes.py | commercial_current_operation | GET | /operacion-en-curso | Sí | No |  | allowed_units |
| backend/modules/comercial_analytics/routes.py | commercial_temporal_resolve | POST | /temporal/resolve | Sí | No |  | allowed_units |
| backend/modules/comercial_benchmark/routes.py | benchmark_unidades | GET | /interno/unidades | Sí | No |  | scope |
| backend/modules/comercial_benchmark/routes.py | benchmark_productos | GET | /interno/productos | Sí | No |  | scope |
| backend/modules/comercial_benchmark/routes.py | mis_unidades | GET | /mis-unidades | Sí | No |  | scope |
| backend/modules/comercial_benchmark/routes.py | metricas | GET | /metricas | Sí | No |  |  |
| backend/modules/comercial_benchmark/routes.py | cobertura | GET | /cobertura | Sí | No |  |  |
| backend/modules/comercial_enriquecido/routes.py | catalogos_filtros | GET | /catalogos/filtros | Sí | No |  |  |
| backend/modules/comercial_enriquecido/routes.py | obtener_producto_enriquecido | GET | /{id} | Sí | No |  |  |
| backend/modules/comercial_enriquecido/routes.py | actualizar_producto_enriquecido | PUT | /{id} | Sí | No |  |  |
| backend/modules/comercial_enriquecido/routes.py | activar_producto | PATCH | /{id}/activar | Sí | No |  |  |
| backend/modules/comercial_enriquecido/routes.py | desactivar_producto | PATCH | /{id}/desactivar | Sí | No |  |  |
| backend/modules/comercial_enriquecido/routes.py | importar_productos | POST | /importar | Sí | No |  |  |
| backend/modules/comercial_v2/periodos_routes.py | obtener_periodos_disponibles | GET | /periodos/disponibles | Sí | No |  |  |
| backend/modules/comercial_v2/periodos_routes.py | obtener_periodos_agregados | POST | /periodos/agregado | Sí | No |  |  |
| backend/modules/comercial_v2/periodos_routes.py | obtener_contrato_periodo | GET | /periodos/contrato | Sí | No |  |  |
| backend/modules/comercial_v2/routes.py | comercial_v2_health | GET | /health | No | No |  |  |
| backend/modules/comercial_v2/routes.py | comercial_v2_dashboard | GET | /dashboard | Sí | No |  | unidad_negocio_id, unidades_permitidas |
| backend/modules/comercial_v2/routes.py | comercial_v2_kpis_diarios | GET | /kpis-diarios | Sí | No |  | unidades_permitidas |
| backend/modules/comercial_v2/routes.py | comercial_v2_kpis_diarios_unidad | GET | /kpis-diarios/{unidad_negocio_pk} | Sí | No |  | unidades_permitidas |
| backend/modules/comercial_v2/routes.py | comercial_v2_kpis_mensuales | GET | /kpis-mensuales | Sí | No |  | unidades_permitidas |
| backend/modules/comercial_v2/routes.py | comercial_v2_ventas_dia | GET | /ventas-dia | Sí | No |  | unidad_negocio_id, unidades_permitidas |
| backend/modules/comercial_v2/routes.py | comercial_v2_unidades | GET | /unidades | Sí | No |  | unidades_permitidas |
| backend/modules/comercial_v2/routes.py | comercial_v2_sync_status | GET | /sync-status | Sí | No |  | unidades_permitidas |
| backend/modules/configuracion/routes/config_asignaciones_routes.py | listar_unidades_negocio | GET | /unidades-negocio | Sí | No |  |  |
| backend/modules/configuracion/routes/config_asignaciones_routes.py | listar_almacenes | GET | /almacenes/{unidad_negocio_pk} | Sí | No |  |  |
| backend/modules/configuracion/routes/config_asignaciones_routes.py | info_sincronizacion_almacenes | GET | /almacenes/{unidad_negocio_pk}/sync-info | Sí | No |  |  |
| backend/modules/configuracion/routes/config_asignaciones_routes.py | obtener_asignacion | GET | /{config_id} | Sí | No |  |  |
| backend/modules/configuracion/routes/config_asignaciones_routes.py | actualizar_asignacion | PUT | /{config_id} | Sí | No |  |  |
| backend/modules/configuracion/routes/config_asignaciones_routes.py | eliminar_asignacion | DELETE | /{config_id} | Sí | No |  |  |
| backend/modules/configuracion/routes/config_asignaciones_routes.py | resolver_responsable_test | GET | /resolver/test | Sí | No |  |  |
| backend/modules/configuracion/routes/config_asignaciones_routes.py | sincronizar_almacenes | POST | /almacenes/sincronizar/{unidad_negocio_pk} | Sí | No |  |  |
| backend/modules/consultas_sql/routes.py | listar_consultas_sql | GET | /consultas | Sí | No |  |  |
| backend/modules/consultas_sql/routes.py | obtener_consulta_sql | GET | /consultas/{consulta_id} | Sí | No |  |  |
| backend/modules/consultas_sql/routes.py | crear_consulta_sql | POST | /consultas | Sí | No |  |  |
| backend/modules/consultas_sql/routes.py | actualizar_consulta_sql | PUT | /consultas/{consulta_id} | Sí | No |  |  |
| backend/modules/consultas_sql/routes.py | eliminar_consulta_sql | DELETE | /consultas/{consulta_id} | Sí | No |  |  |
| backend/modules/corporate_filters/router.py | health | GET | /health | No | No |  |  |
| backend/modules/corporate_filters/router.py | bootstrap | GET | /bootstrap | No | No |  | scope |
| backend/modules/corporate_filters/router.py | resolve | POST | /resolve | No | No |  | scope |
| backend/modules/corporate_filters/router.py | listar_versiones_sistemas | GET | /admin/versiones-sistemas | No | No |  |  |
| backend/modules/corporate_filters/router.py | listar_servidores_con_versiones | GET | /admin/servidores-versiones | No | No |  |  |
| backend/modules/corporate_filters/router.py | crear_version_sistema | POST | /admin/versiones-sistemas | No | No |  |  |
| backend/modules/corporate_filters/router.py | actualizar_version_sistema | PUT | /admin/versiones-sistemas/{sistema_version_id} | No | No |  |  |
| backend/modules/corporate_filters/router.py | asignar_version_a_servidor | PUT | /admin/servidores/{servidor_conexion_id}/version | No | No |  |  |
| backend/modules/costos_margenes/routes.py | obtener_resumen | GET | /resumen | Sí | No |  |  |
| backend/modules/costos_margenes/routes.py | listar_productos | GET | /productos | Sí | No |  | empresa_id |
| backend/modules/costos_margenes/routes.py | obtener_receta_producto | GET | /productos/{producto_id}/receta | Sí | No |  |  |
| backend/modules/costos_margenes/routes.py | obtener_insumos_producto | GET | /productos/{producto_id}/insumos | Sí | No |  |  |
| backend/modules/costos_margenes/routes.py | obtener_sync_status | GET | /sync-status | Sí | No |  |  |
| backend/modules/costos_margenes/routes.py | listar_familias | GET | /familias | Sí | No |  |  |
| backend/modules/costos_margenes/routes.py | listar_subfamilias | GET | /subfamilias | Sí | No |  |  |
| backend/modules/costos_margenes/routes.py | exportar_productos_csv | GET | /exportar | Sí | No |  |  |
| backend/modules/costos_margenes/routes_precios.py | simular_precio | POST | /simulacion | Sí | No |  |  |
| backend/modules/costos_margenes/routes_precios.py | crear_solicitud | POST | /solicitudes-precio | Sí | No |  |  |
| backend/modules/costos_margenes/routes_precios.py | listar_solicitudes_precio | GET | /solicitudes-precio | Sí | No |  |  |
| backend/modules/costos_margenes/routes_precios.py | obtener_solicitud_precio | GET | /solicitudes-precio/{solicitud_id} | Sí | No |  |  |
| backend/modules/costos_margenes/routes_precios.py | enviar_solicitud | POST | /solicitudes-precio/{solicitud_id}/enviar | Sí | No |  |  |
| backend/modules/costos_margenes/routes_precios.py | aprobar_solicitud | POST | /solicitudes-precio/{solicitud_id}/aprobar | Sí | No |  |  |
| backend/modules/costos_margenes/routes_precios.py | rechazar_solicitud | POST | /solicitudes-precio/{solicitud_id}/rechazar | Sí | No |  |  |
| backend/modules/costos_margenes/routes_precios.py | aplicar_solicitud | POST | /solicitudes-precio/{solicitud_id}/aplicar | Sí | No |  |  |
| backend/modules/costos_margenes/routes_precios.py | cancelar_solicitud | POST | /solicitudes-precio/{solicitud_id}/cancelar | Sí | No |  |  |
| backend/modules/costos_margenes/routes_precios.py | obtener_historial | GET | /solicitudes-precio/{solicitud_id}/historial | Sí | No |  |  |
| backend/modules/crm/automation_routes.py | listar_reglas | GET | /reglas | Sí | No |  | empresa_id |
| backend/modules/crm/automation_routes.py | crear_regla | POST | /reglas | Sí | No |  | empresa_id |
| backend/modules/crm/automation_routes.py | verificar_sla | GET | /sla/verificar | Sí | No |  | empresa_id |
| backend/modules/crm/automation_routes.py | obtener_estadisticas | GET | /estadisticas | Sí | No |  | empresa_id |
| backend/modules/crm/automation_routes.py | ejecutar_trigger_cambio_etapa | POST | /ejecutar/cambio-etapa | Sí | No |  | empresa_id |
| backend/modules/crm/comercial_routes.py | listar_cuentas | GET | /cuentas | Sí | No |  | empresa_id |
| backend/modules/crm/comercial_routes.py | crear_cuenta | POST | /cuentas | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | obtener_cuenta | GET | /cuentas/{cuenta_id} | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | ligar_cliente | POST | /cuentas/{cuenta_id}/ligar-cliente | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | listar_clientes | GET | /clientes | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | listar_solicitudes_alta | GET | /clientes/solicitudes | Sí | No |  | empresa_id |
| backend/modules/crm/comercial_routes.py | crear_solicitud_alta | POST | /clientes/solicitudes | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | enviar_solicitud | POST | /clientes/solicitudes/{solicitud_id}/enviar | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | autorizar_solicitud | POST | /clientes/solicitudes/{solicitud_id}/autorizar | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | rechazar_solicitud | POST | /clientes/solicitudes/{solicitud_id}/rechazar | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | listar_actividades | GET | /actividades | Sí | No |  | empresa_id |
| backend/modules/crm/comercial_routes.py | crear_actividad | POST | /actividades | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | cerrar_actividad | POST | /actividades/{actividad_id}/cerrar | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | listar_tipos_actividad | GET | /catalogos/tipos-actividad | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | listar_estatus_actividad | GET | /catalogos/estatus-actividad | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | listar_estatus_remision | GET | /catalogos/estatus-remision | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | listar_cotizaciones | GET | /cotizaciones | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | obtener_cotizacion | GET | /cotizaciones/{cotizacion_id} | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | crear_cotizacion | POST | /cotizaciones | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | enviar_cotizacion | POST | /cotizaciones/{cotizacion_id}/enviar | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | aprobar_cotizacion | POST | /cotizaciones/{cotizacion_id}/aprobar | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | listar_pedidos | GET | /pedidos-venta | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | obtener_pedido | GET | /pedidos-venta/{pedido_id} | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | crear_pedido | POST | /pedidos-venta | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | confirmar_pedido | POST | /pedidos-venta/{pedido_id}/confirmar | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | listar_remisiones | GET | /remisiones-venta | Sí | No |  | empresa_id |
| backend/modules/crm/comercial_routes.py | obtener_remision | GET | /remisiones-venta/{remision_id} | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | crear_remision | POST | /remisiones-venta | Sí | No |  |  |
| backend/modules/crm/comercial_routes.py | registrar_entrega | POST | /remisiones-venta/{remision_id}/entregar | Sí | No |  |  |
| backend/modules/crm/native_routes.py | crear_lead | POST | /leads | Sí | No |  |  |
| backend/modules/crm/native_routes.py | listar_leads | GET | /leads | Sí | No |  | empresa_id |
| backend/modules/crm/native_routes.py | obtener_lead | GET | /leads/{lead_id} | Sí | No |  |  |
| backend/modules/crm/native_routes.py | actualizar_lead | PUT | /leads/{lead_id} | Sí | No |  |  |
| backend/modules/crm/native_routes.py | eliminar_lead | DELETE | /leads/{lead_id} | Sí | No |  |  |
| backend/modules/crm/native_routes.py | descalificar_lead | POST | /leads/{lead_id}/descalificar | Sí | No |  |  |
| backend/modules/crm/native_routes.py | convertir_lead | POST | /leads/{lead_id}/convertir | Sí | No |  |  |
| backend/modules/crm/native_routes.py | crear_oportunidad | POST | /oportunidades | Sí | No |  |  |
| backend/modules/crm/native_routes.py | listar_oportunidades | GET | /oportunidades | Sí | No |  | empresa_id |
| backend/modules/crm/native_routes.py | listar_contactos | GET | /contactos | Sí | No |  | empresa_id |
| backend/modules/crm/native_routes.py | obtener_oportunidad | GET | /oportunidades/{oportunidad_id} | Sí | No |  |  |
| backend/modules/crm/native_routes.py | cambiar_etapa_oportunidad | POST | /oportunidades/{oportunidad_id}/cambiar-etapa | Sí | No |  |  |
| backend/modules/crm/native_routes.py | cerrar_oportunidad | POST | /oportunidades/{oportunidad_id}/cerrar | Sí | No |  |  |
| backend/modules/crm/native_routes.py | listar_pipelines | GET | /pipelines | Sí | No |  | empresa_id |
| backend/modules/crm/native_routes.py | obtener_kanban | GET | /pipelines/{pipeline_id}/kanban | Sí | No |  | empresa_id |
| backend/modules/crm/native_routes.py | obtener_catalogos | GET | /catalogos | Sí | No |  |  |
| backend/modules/crm/native_routes.py | obtener_catalogo | GET | /catalogos/{nombre} | Sí | No |  |  |
| backend/modules/crm/native_routes.py | obtener_dashboard | GET | /dashboard | Sí | No |  | empresa_id |
| backend/modules/crm/trigger_routes.py | listar_triggers | GET | / | Sí | No |  | empresa_id |
| backend/modules/crm/trigger_routes.py | crear_trigger | POST | / | Sí | No |  | empresa_id |
| backend/modules/crm/trigger_routes.py | toggle_trigger | PATCH | /{trigger_id}/toggle | Sí | No |  |  |
| backend/modules/crm/trigger_routes.py | dispatch_event | POST | /dispatch | Sí | No |  | empresa_id |
| backend/modules/crm/trigger_routes.py | listar_tipos_evento | GET | /eventos | No | No |  |  |
| backend/modules/crm/trigger_routes.py | listar_tipos_accion | GET | /acciones | No | No |  |  |
| backend/modules/dashboard_ejecutivo/routes.py | resumen | GET | /resumen | Sí | No |  | scope |
| backend/modules/dashboard_ejecutivo/routes.py | rentabilidad_base | GET | /rentabilidad-base | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/auditoria_programada_routes.py | obtener_kpis | GET | /kpis | Sí | No |  | unidades_permitidas |
| backend/modules/fase2_operativo/routes/auditoria_programada_routes.py | obtener_calendario | GET | /calendario | Sí | No |  | unidades_permitidas |
| backend/modules/fase2_operativo/routes/auditoria_programada_routes.py | obtener_historial | GET | /historial | Sí | No |  | unidades_permitidas |
| backend/modules/fase2_operativo/routes/auditoria_programada_routes.py | obtener_auditoria | GET | /{auditoria_id} | Sí | No |  | unidades_permitidas |
| backend/modules/fase2_operativo/routes/auditoria_programada_routes.py | actualizar_auditoria | PUT | /{auditoria_id} | Sí | No |  | sucursal_id, unidades_permitidas |
| backend/modules/fase2_operativo/routes/auditoria_programada_routes.py | eliminar_auditoria | DELETE | /{auditoria_id} | Sí | No |  | unidades_permitidas |
| backend/modules/fase2_operativo/routes/auditoria_programada_routes.py | activar_auditoria | POST | /{auditoria_id}/activar | Sí | No |  | unidades_permitidas |
| backend/modules/fase2_operativo/routes/auditoria_programada_routes.py | desactivar_auditoria | POST | /{auditoria_id}/desactivar | Sí | No |  | unidades_permitidas |
| backend/modules/fase2_operativo/routes/auditoria_programada_routes.py | ejecutar_auditoria | POST | /{auditoria_id}/ejecutar | Sí | No |  | unidades_permitidas |
| backend/modules/fase2_operativo/routes/auditoria_routes.py | registrar_decision | POST | /decisiones | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/auditoria_routes.py | procesar_decision_completa | POST | /decisiones/procesar | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/auditoria_routes.py | obtener_decision | GET | /decisiones/{decision_id} | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/auditoria_routes.py | obtener_decisiones_workflow | GET | /workflow/{workflow_id}/decisiones | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/auditoria_routes.py | obtener_ultima_decision | GET | /workflow/{workflow_id}/ultima-decision | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/auditoria_routes.py | obtener_pendientes_auditoria | GET | /pendientes | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/auditoria_routes.py | obtener_resumen_auditoria | GET | /resumen | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py | ejecutar_detector_manual | POST | /compras/detector/ejecutar | Sí | No | COMPRAS_FACT_EJECUTAR | empresa_id |
| backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py | obtener_estado_detector | GET | /compras/detector/estado | Sí | Sí | COMPRAS_FACT_VER |  |
| backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py | listar_tareas_operativas | GET | /compras/tareas | Sí | Sí | COMPRAS_FACT_VER | empresa_id |
| backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py | obtener_tarea_operativa | GET | /compras/tareas/{tarea_id} | Sí | Sí | COMPRAS_FACT_VER |  |
| backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py | completar_tarea_operativa | POST | /compras/tareas/{tarea_id}/completar | Sí | No | COMPRAS_FACT_EJECUTAR |  |
| backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py | asignar_tarea_operativa | POST | /compras/tareas/{tarea_id}/asignar | Sí | No | COMPRAS_FACT_GESTIONAR |  |
| backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py | obtener_kpis | GET | /compras/kpis | Sí | Sí | COMPRAS_FACT_VER | unidades_permitidas |
| backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py | listar_automatizaciones | GET | /compras | Sí | Sí | COMPRAS_FACT_VER | sucursal_id, unidades_permitidas |
| backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py | obtener_bitacora_detector | GET | /compras/detector/bitacora | Sí | Sí | COMPRAS_FACT_VER |  |
| backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py | listar_pedidos_procesados | GET | /compras/pedidos-procesados | Sí | Sí | COMPRAS_FACT_VER | empresa_id |
| backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py | obtener_automatizacion | GET | /compras/{automatizacion_id} | Sí | Sí | COMPRAS_FACT_VER | unidades_permitidas |
| backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py | procesar_pedido | POST | /compras/procesar | Sí | No | COMPRAS_FACT_EJECUTAR | sucursal_id |
| backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py | autorizar_gerencia | POST | /compras/{automatizacion_id}/gerencia | Sí | No | COMPRAS_FACT_AUTORIZAR |  |
| backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py | autorizar_tesoreria | POST | /compras/{automatizacion_id}/tesoreria | Sí | No | COMPRAS_FACT_APROBAR |  |
| backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py | modificar_dias_objetivo | POST | /compras/{automatizacion_id}/dias-objetivo | Sí | No | COMPRAS_FACT_CONFIGURAR |  |
| backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py | modificar_parametros_consumo | POST | /compras/{automatizacion_id}/parametros-consumo | Sí | No | COMPRAS_FACT_CONFIGURAR |  |
| backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py | obtener_bitacora | GET | /compras/{automatizacion_id}/bitacora | Sí | Sí | COMPRAS_FACT_VER | unidades_permitidas |
| backend/modules/fase2_operativo/routes/cargos_routes.py | obtener_pendientes | GET | /pendientes | Sí | Sí | CARGOS_VER |  |
| backend/modules/fase2_operativo/routes/cargos_routes.py | obtener_aplicados | GET | /aplicados | Sí | Sí | CARGOS_VER |  |
| backend/modules/fase2_operativo/routes/cargos_routes.py | obtener_metricas | GET | /metricas | Sí | Sí | CARGOS_VER |  |
| backend/modules/fase2_operativo/routes/cargos_routes.py | evaluar_elegibilidad | GET | /elegibilidad/{responsabilidad_id} | Sí | Sí | CARGOS_VER |  |
| backend/modules/fase2_operativo/routes/cargos_routes.py | obtener_cargo | GET | /{cargo_id} | Sí | Sí | CARGOS_VER |  |
| backend/modules/fase2_operativo/routes/cargos_routes.py | obtener_log_cargo | GET | /{cargo_id}/log | Sí | Sí | CARGOS_VER |  |
| backend/modules/fase2_operativo/routes/cargos_routes.py | autorizar_cargo | POST | /{cargo_id}/autorizar | Sí | No | CARGOS_AUTORIZAR |  |
| backend/modules/fase2_operativo/routes/cargos_routes.py | aplicar_cargo | POST | /{cargo_id}/aplicar | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/cargos_routes.py | rechazar_cargo | POST | /{cargo_id}/rechazar | Sí | No | CARGOS_RECHAZAR |  |
| backend/modules/fase2_operativo/routes/cargos_routes.py | revertir_cargo | POST | /{cargo_id}/revertir | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/cargos_routes.py | cancelar_cargo | POST | /{cargo_id}/cancelar | Sí | No | CARGOS_CANCELAR |  |
| backend/modules/fase2_operativo/routes/configuracion_routes.py | listar_todas_configuraciones | GET | /todas | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/configuracion_routes.py | obtener_configuracion | GET | /{clave} | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/configuracion_routes.py | actualizar_configuracion | PATCH | /{clave} | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/configuracion_routes.py | obtener_umbral_justificacion | GET | /umbral-justificacion/valor | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/configuracion_routes.py | actualizar_umbral_justificacion | PATCH | /umbral-justificacion/valor | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/configuracion_routes.py | obtener_dias_limite_tarea | GET | /dias-limite-tarea/valor | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/configuracion_routes.py | actualizar_dias_limite_tarea | PATCH | /dias-limite-tarea/valor | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/configuracion_routes.py | obtener_max_ciclos_reasignacion | GET | /max-ciclos-reasignacion/valor | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/configuracion_routes.py | actualizar_max_ciclos_reasignacion | PATCH | /max-ciclos-reasignacion/valor | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/dashboard_routes.py | obtener_resumen_dashboard | GET | /resumen | Sí | No |  | scope |
| backend/modules/fase2_operativo/routes/dashboard_routes.py | obtener_alertas | GET | /alertas | Sí | No |  | scope |
| backend/modules/fase2_operativo/routes/dashboard_routes.py | obtener_workflows_por_estado | GET | /workflows/por-estado | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/dashboard_routes.py | obtener_tareas_por_estado | GET | /tareas/por-estado | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/dashboard_routes.py | obtener_conteo_tareas_vencidas | GET | /tareas/vencidas/conteo | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/dashboard_routes.py | obtener_kpis | GET | /kpis | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/documentos_routes.py | descargar_excel_workflow | GET | /workflow/{workflow_id}/excel | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/documentos_routes.py | descargar_pdf_workflow | GET | /workflow/{workflow_id}/pdf | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/documentos_routes.py | obtener_datos_workflow | GET | /workflow/{workflow_id}/datos | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/documentos_routes.py | obtener_resumen_workflow | GET | /workflow/{workflow_id}/resumen | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/documentos_routes.py | obtener_historial_documentos | GET | /historial | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/justificacion_routes.py | obtener_justificacion | GET | /{justificacion_id} | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/justificacion_routes.py | obtener_justificaciones_workflow | GET | /workflow/{workflow_id} | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/justificacion_routes.py | verificar_justificaciones_workflow | POST | /workflow/{workflow_id}/verificar | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/justificacion_routes.py | obtener_umbral_justificacion | GET | /umbral | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/justificacion_routes.py | determinar_tipo_justificacion | POST | /determinar-tipo | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/notificaciones_routes.py | get_notification_status | GET | /status | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/notificaciones_routes.py | get_notification_log | GET | /log | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/notificaciones_routes.py | verificar_tareas_vencidas | POST | /verificar-vencidas | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/notificaciones_routes.py | test_email | POST | /test-email | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/responsabilidad_routes.py | calcular_responsabilidad | POST | /calcular/{workflow_id} | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/responsabilidad_routes.py | obtener_por_workflow | GET | /workflow/{workflow_id} | Sí | Sí | RESPONSABILIDAD_VER |  |
| backend/modules/fase2_operativo/routes/responsabilidad_routes.py | obtener_configuracion | GET | /configuracion | Sí | Sí | RESPONSABILIDAD_VER |  |
| backend/modules/fase2_operativo/routes/responsabilidad_routes.py | actualizar_configuracion | PUT | /configuracion | Sí | No | RESPONSABILIDAD_GESTIONAR |  |
| backend/modules/fase2_operativo/routes/responsabilidad_routes.py | inicializar_configuracion | POST | /inicializar-configuracion | Sí | No | RESPONSABILIDAD_GESTIONAR |  |
| backend/modules/fase2_operativo/routes/responsabilidad_routes.py | obtener_metricas | GET | /metricas | Sí | Sí | RESPONSABILIDAD_VER |  |
| backend/modules/fase2_operativo/routes/responsabilidad_routes.py | proponer | POST | /{responsabilidad_id}/proponer | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/responsabilidad_routes.py | aprobar | POST | /{responsabilidad_id}/aprobar | Sí | No | RESPONSABILIDAD_APROBAR |  |
| backend/modules/fase2_operativo/routes/responsabilidad_routes.py | rechazar | POST | /{responsabilidad_id}/rechazar | Sí | No | RESPONSABILIDAD_RECHAZAR |  |
| backend/modules/fase2_operativo/routes/responsabilidad_routes.py | exonerar | POST | /{responsabilidad_id}/exonerar | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/responsabilidad_routes.py | disputar | POST | /{responsabilidad_id}/disputar | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/responsabilidad_routes.py | resolver_disputa | POST | /{responsabilidad_id}/resolver-disputa | Sí | No | RESPONSABILIDAD_GESTIONAR |  |
| backend/modules/fase2_operativo/routes/responsabilidad_routes.py | listar_pendientes_aprobacion | GET | /pendientes-aprobacion | Sí | Sí | RESPONSABILIDAD_VER |  |
| backend/modules/fase2_operativo/routes/responsabilidad_routes.py | listar_en_disputa | GET | /en-disputa | Sí | Sí | RESPONSABILIDAD_VER |  |
| backend/modules/fase2_operativo/routes/responsabilidad_routes.py | obtener_historial | GET | /{responsabilidad_id}/historial | Sí | Sí | RESPONSABILIDAD_VER |  |
| backend/modules/fase2_operativo/routes/sla_routes.py | obtener_configuracion_sla | GET | /configuracion | Sí | Sí | SLA_VER |  |
| backend/modules/fase2_operativo/routes/sla_routes.py | actualizar_configuracion_sla | PUT | /configuracion | Sí | No | SLA_CONFIGURAR |  |
| backend/modules/fase2_operativo/routes/sla_routes.py | obtener_metricas_sla | GET | /metricas | Sí | Sí | SLA_VER |  |
| backend/modules/fase2_operativo/routes/sla_routes.py | obtener_tareas_proximas_vencer | GET | /tareas/proximas-vencer | Sí | Sí | SLA_VER |  |
| backend/modules/fase2_operativo/routes/sla_routes.py | obtener_tareas_vencidas | GET | /tareas/vencidas | Sí | Sí | SLA_VER |  |
| backend/modules/fase2_operativo/routes/sla_routes.py | actualizar_estados_sla | POST | /actualizar-estados | Sí | Sí | SLA_VER |  |
| backend/modules/fase2_operativo/routes/sla_routes.py | obtener_sla_tarea | GET | /tarea/{tarea_id} | Sí | Sí | SLA_VER |  |
| backend/modules/fase2_operativo/routes/sla_routes.py | obtener_definicion_estados | GET | /estados | No | No |  |  |
| backend/modules/fase2_operativo/routes/tarea_routes.py | obtener_tarea | GET | /{tarea_id} | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/tarea_routes.py | asignar_tarea | PATCH | /{tarea_id}/asignar | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/tarea_routes.py | reasignar_tarea | PATCH | /{tarea_id}/reasignar | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/tarea_routes.py | completar_tarea | PATCH | /{tarea_id}/completar | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/tarea_routes.py | marcar_en_progreso | PATCH | /{tarea_id}/en-progreso | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/tarea_routes.py | obtener_historial_tarea | GET | /{tarea_id}/historial | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/tarea_routes.py | marcar_tareas_vencidas | POST | /marcar-vencidas | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/workflow_routes.py | obtener_workflow | GET | /{workflow_id} | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/workflow_routes.py | cambiar_estado_workflow | PATCH | /{workflow_id}/estado | Sí | No |  |  |
| backend/modules/fase2_operativo/routes/workflow_routes.py | escalar_workflow | POST | /{workflow_id}/escalar | Sí | No | WORKFLOW_GESTIONAR |  |
| backend/modules/fase2_operativo/routes/workflow_routes.py | obtener_resumen_workflow | GET | /{workflow_id}/resumen | Sí | No |  |  |
| backend/modules/finanzas/comprobaciones.py | get_comprobaciones_status | GET | /status | Sí | No |  |  |
| backend/modules/finanzas/cuentas_bancarias.py | listar_bancos | GET | /bancos | Sí | No |  |  |
| backend/modules/finanzas/cuentas_bancarias.py | listar_cuentas_bancarias | GET | /cuentas-bancarias | Sí | No |  | unidades_permitidas |
| backend/modules/finanzas/cuentas_bancarias.py | obtener_cuenta_bancaria | GET | /cuentas-bancarias/{cuenta_id} | Sí | No |  |  |
| backend/modules/finanzas/cuentas_bancarias.py | crear_cuenta | POST | /cuentas-bancarias | Sí | No |  | empresa_id |
| backend/modules/finanzas/cuentas_bancarias.py | actualizar_cuenta | PUT | /cuentas-bancarias/{cuenta_id} | Sí | No |  | empresa_id |
| backend/modules/finanzas/cuentas_bancarias.py | desactivar_cuenta | POST | /cuentas-bancarias/{cuenta_id}/desactivar | Sí | No |  |  |
| backend/modules/finanzas/cuentas_por_pagar.py | get_resumen_cuentas_por_pagar | GET | /resumen | Sí | No |  | sucursal_id, unidades_permitidas |
| backend/modules/finanzas/cuentas_por_pagar.py | listar_proveedores_con_saldo | GET | /proveedores | Sí | No |  | sucursal_id, unidades_permitidas |
| backend/modules/finanzas/cuentas_por_pagar.py | listar_sucursales_cxp | GET | /sucursales | Sí | No |  | unidades_permitidas |
| backend/modules/finanzas/cuentas_por_pagar.py | actualizar_decision_pago | PUT | /{factura_id}/decision-pago | Sí | No |  | sucursal_id, unidades_permitidas |
| backend/modules/finanzas/cuentas_por_pagar.py | autorizar_decision_pago | POST | /{factura_id}/decision-pago/autorizacion | Sí | No |  | sucursal_id, unidades_permitidas |
| backend/modules/finanzas/cuentas_por_pagar.py | actualizar_decision_pago_masivo | PUT | /decision-pago-masivo | Sí | No |  | unidades_permitidas |
| backend/modules/finanzas/cuentas_por_pagar.py | get_factura_detalle | GET | /{factura_id} | Sí | No |  | unidades_permitidas |
| backend/modules/finanzas/health.py | get_finanzas_health_quick | GET | /quick | Sí | No |  |  |
| backend/modules/finanzas/health.py | get_tables_status | GET | /tables | Sí | No |  |  |
| backend/modules/finanzas/health.py | get_server_health | GET | /servers/{server_id} | Sí | No |  |  |
| backend/modules/finanzas/ingresos.py | listar_cortes_caja | GET | /cortes-caja | Sí | No |  | sucursal_id, unidades_permitidas |
| backend/modules/finanzas/ingresos.py | get_saldos_por_depositar | GET | /saldos-por-depositar | Sí | No |  | unidades_permitidas |
| backend/modules/finanzas/ingresos.py | get_resumen_comisiones | GET | /resumen-comisiones | Sí | No |  | unidades_permitidas |
| backend/modules/finanzas/ingresos.py | registrar_deposito_efectivo | PUT | /cortes-caja/{corte_id}/deposito-efectivo | Sí | No |  |  |
| backend/modules/finanzas/ingresos.py | registrar_deposito_tarjetas | PUT | /cortes-caja/{corte_id}/deposito-tarjetas | Sí | No |  |  |
| backend/modules/finanzas/ingresos.py | cargar_estado_cuenta | POST | /cargar-estado-cuenta | Sí | No |  |  |
| backend/modules/finanzas/ingresos.py | listar_movimientos_banco | GET | /movimientos-banco | Sí | No |  |  |
| backend/modules/finanzas/ingresos.py | get_config_comisiones | GET | /config-comisiones | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes.py | health_check | GET | /health | No | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes.py | sincronizar_propinas | POST | /sincronizar | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes.py | inicializar_modulo | POST | /inicializar | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes.py | detectar_esquema | GET | /detectar-esquema/{server_id} | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes.py | detectar_esquema_todos | GET | /detectar-esquema-todos | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes.py | preview_propinas | GET | /preview | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes.py | resumen_propinas | GET | /resumen | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes.py | listar_configs | GET | /config/all | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes.py | obtener_config | GET | /config | Sí | No |  | sucursal_id |
| backend/modules/finanzas/propinas_tpv/routes.py | crear_config | POST | /config | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes.py | actualizar_config | PUT | /config/{config_id} | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes.py | obtener_propina | GET | /{propina_id} | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes.py | registrar_pago | PUT | /{propina_id}/pago | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_edarsahub.py | resumen_propinas_edarsahub | GET | /resumen | Sí | No |  | unidad_negocio_id, unidades_permitidas |
| backend/modules/finanzas/propinas_tpv/routes_edarsahub.py | detalle_propinas_edarsahub | GET | /detalle | Sí | No |  | unidad_negocio_id, unidades_permitidas |
| backend/modules/finanzas/propinas_tpv/routes_edarsahub.py | listado_propinas_edarsahub | GET | /listado | Sí | No |  | unidad_negocio_id, unidades_permitidas |
| backend/modules/finanzas/propinas_tpv/routes_edarsahub.py | unidades_disponibles | GET | /unidades | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_edarsahub.py | obtener_config_v2 | GET | /config | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_edarsahub.py | listar_configs_v2 | GET | /config/all | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_edarsahub.py | crear_config_v2 | POST | /config | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_edarsahub.py | actualizar_config_v2 | PUT | /config/{config_id} | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_edarsahub.py | formas_pago_disponibles | GET | /formas-pago | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_edarsahub.py | status_sincronizacion | GET | /status | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_edarsahub.py | health_check | GET | /health | No | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_edarsahub.py | obtener_propina_por_id | GET | /{propina_id} | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_sql.py | health_check_sql | GET | /health | No | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_sql.py | inicializar_modulo_sql | POST | /inicializar-sql | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_sql.py | sincronizar_propinas_sql | POST | /sincronizar | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_sql.py | resumen_propinas_sql | GET | /resumen | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_sql.py | obtener_config_sql | GET | /config | Sí | No |  | sucursal_id |
| backend/modules/finanzas/propinas_tpv/routes_sql.py | listar_configs_sql | GET | /config/all | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_sql.py | crear_config_sql | POST | /config | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_sql.py | actualizar_config_sql | PUT | /config/{config_id} | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_sql.py | cache_stats | GET | /cache/stats | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_sql.py | invalidar_cache | POST | /cache/invalidar | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_sql.py | detectar_esquema | GET | /detectar-esquema/{server_id} | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_sql.py | detectar_esquema_todos | GET | /detectar-esquema-todos | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_sql.py | preview_propinas | GET | /preview | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_sql.py | obtener_propina_sql | GET | /{propina_id} | Sí | No |  |  |
| backend/modules/finanzas/propinas_tpv/routes_sql.py | registrar_pago_sql | PUT | /{propina_id}/pago | Sí | No |  |  |
| backend/modules/finanzas/saldos_bancarios.py | listar_saldos_cuenta | GET | /cuentas-bancarias/{cuenta_id}/saldos | Sí | No |  |  |
| backend/modules/finanzas/saldos_bancarios.py | obtener_saldo_actual | GET | /cuentas-bancarias/{cuenta_id}/saldo-actual | Sí | No |  |  |
| backend/modules/finanzas/saldos_bancarios.py | capturar_saldo | POST | /saldos-bancarios | Sí | No |  |  |
| backend/modules/finanzas/saldos_bancarios.py | corregir_saldo | POST | /saldos-bancarios/{saldo_id}/corregir | Sí | No |  |  |
| backend/modules/finanzas/saldos_bancarios.py | cancelar_saldo | POST | /saldos-bancarios/{saldo_id}/cancelar | Sí | No |  |  |
| backend/modules/finanzas/saldos_bancarios.py | obtener_historial_saldo | GET | /saldos-bancarios/{saldo_id}/historial | Sí | No |  |  |
| backend/modules/finanzas/saldos_bancarios.py | obtener_saldo_total | GET | /saldos-bancarios/total | Sí | No |  | unidades_permitidas |
| backend/modules/finanzas/tesoreria.py | listar_cortes_z | GET | /cortes-z | Sí | No |  | scope, sucursal_id |
| backend/modules/finanzas/tesoreria.py | obtener_corte_z | GET | /cortes-z/{sucursal}/{folio} | Sí | No |  | scope |
| backend/modules/finanzas/tesoreria.py | listar_cuadres | GET | /cuadres | Sí | No |  | scope, sucursal_id, unidades_permitidas |
| backend/modules/finanzas/tesoreria.py | obtener_resumen_cuadres | GET | /cuadres/resumen | Sí | No |  | scope, unidades_permitidas |
| backend/modules/finanzas/tesoreria.py | obtener_cuadre | GET | /cuadres/{cuadre_id} | Sí | No |  | scope |
| backend/modules/finanzas/tesoreria.py | crear_cuadre | POST | /cuadres | Sí | No |  | empresa_id, scope, sucursal_id |
| backend/modules/finanzas/tesoreria.py | actualizar_cuadre | PUT | /cuadres/{cuadre_id} | Sí | No |  | scope |
| backend/modules/finanzas/tesoreria.py | eliminar_cuadre | DELETE | /cuadres/{cuadre_id} | Sí | No |  | scope |
| backend/modules/finanzas/tesoreria.py | subir_ficha_deposito | POST | /cuadres/{cuadre_id}/ficha-deposito | Sí | No |  | scope |
| backend/modules/finanzas/tesoreria.py | validar_ficha_deposito | POST | /cuadres/{cuadre_id}/validar-ficha | Sí | No |  | scope |
| backend/modules/finanzas/tesoreria.py | listar_sucursales | GET | /sucursales | Sí | No |  | scope |
| backend/modules/ia_assistant/routes.py | health | GET | /health | Sí | No |  |  |
| backend/modules/ia_assistant/routes.py | listar_sesiones | GET | /sesiones | Sí | No |  |  |
| backend/modules/ia_assistant/routes.py | crear_sesion | POST | /sesiones | Sí | No |  |  |
| backend/modules/ia_assistant/routes.py | obtener_mensajes | GET | /sesiones/{sesion_id}/mensajes | Sí | No |  |  |
| backend/modules/ia_assistant/routes.py | eliminar_sesion | DELETE | /sesiones/{sesion_id} | Sí | No |  |  |
| backend/modules/ia_assistant/routes.py | chat | POST | /chat | Sí | No |  |  |
| backend/modules/informes_auditoria/routes.py | listar_informes_auditoria_sql | GET | /informes-auditoria | Sí | No |  | empresa_id |
| backend/modules/informes_auditoria/routes.py | obtener_informe_auditoria_sql | GET | /informes-auditoria/{informe_id} | Sí | No |  |  |
| backend/modules/informes_auditoria/routes.py | crear_informe_auditoria_sql | POST | /informes-auditoria | Sí | No |  |  |
| backend/modules/informes_auditoria/routes.py | actualizar_informe_auditoria_sql | PUT | /informes-auditoria/{informe_id} | Sí | No |  |  |
| backend/modules/informes_auditoria/routes.py | eliminar_informe_auditoria_sql | DELETE | /informes-auditoria/{informe_id} | Sí | No |  |  |
| backend/modules/inteligencia_comercial/routes.py | get_dashboard_data | GET | /dashboard | No | No |  |  |
| backend/modules/inteligencia_comercial/routes.py | get_tendencia_diaria | GET | /dashboard/tendencia | No | No |  |  |
| backend/modules/inteligencia_comercial/routes.py | get_ventas_horario | GET | /dashboard/horarios | No | No |  |  |
| backend/modules/inteligencia_comercial/routes.py | get_analisis_pax | GET | /dashboard/pax | No | No |  |  |
| backend/modules/inteligencia_comercial/routes.py | get_top_productos | GET | /productos | No | No |  |  |
| backend/modules/inteligencia_comercial/routes.py | get_ventas_familia | GET | /familias | No | No |  |  |
| backend/modules/inteligencia_comercial/routes.py | get_reporte_alcohol | GET | /alcohol | No | No |  |  |
| backend/modules/inteligencia_comercial/routes.py | get_ventas_casas | GET | /casas | No | No |  |  |
| backend/modules/inteligencia_comercial/routes.py | get_tickets | GET | /tickets | No | No |  |  |
| backend/modules/inteligencia_comercial/routes.py | get_ticket_detalle | GET | /ticket-detalle | No | No |  |  |
| backend/modules/inteligencia_comercial/routes.py | get_productos_subfamilia | GET | /productos-subfamilia | No | No |  |  |
| backend/modules/inteligencia_comercial/routes.py | get_unidades_negocio | GET | /unidades | No | No |  |  |
| backend/modules/inteligencia_comercial/routes.py | health_check | GET | /health | No | No |  |  |
| backend/modules/inteligencia_comercial/routes.py | get_catalogo_clasificaciones | GET | /clasificaciones | No | No |  |  |
| backend/modules/inteligencia_comercial/routes.py | admin_listar_productos | GET | /admin/productos-clasificacion | No | No |  |  |
| backend/modules/inteligencia_comercial/routes.py | admin_familias_pendientes | GET | /admin/familias-pendientes | No | No |  |  |
| backend/modules/inteligencia_comercial/routes.py | admin_clasificar | POST | /admin/clasificar | No | No |  |  |
| backend/modules/manuales_operativos/routes.py | obtener_manual | GET | /{manual_id} | Sí | No |  |  |
| backend/modules/manuales_operativos/routes.py | obtener_manual_por_proceso | GET | /proceso/{proceso_id} | Sí | No |  |  |
| backend/modules/manuales_operativos/routes.py | exportar_manual_texto | GET | /{manual_id}/exportar | Sí | No |  |  |
| backend/modules/manuales_operativos/routes.py | generar_manual_manual | POST | /generar/{proceso_id} | Sí | No |  |  |
| backend/modules/pricing_ai/routes.py | get_pricing_resumen | GET | /resumen | Sí | No |  |  |
| backend/modules/rbac_context_sql/context_routes.py | get_access_context | GET | /auth/access-context | Sí | No |  | unidad_negocio_id |
| backend/modules/rbac_context_sql/context_routes.py | select_access_unit | POST | /auth/access-context/select-unit | Sí | No |  | unidad_negocio_id |
| backend/modules/rbac_context_sql/routes.py | listar_roles_contexto_usuario | GET | /rbac-context/usuarios/{usuario_id}/roles-contexto | Sí | No |  |  |
| backend/modules/rbac_context_sql/routes.py | crear_rol_contexto_usuario | POST | /rbac-context/usuarios/{usuario_id}/roles-contexto | Sí | No |  | empresa_id, sucursal_id, unidad_negocio_id |
| backend/modules/rbac_context_sql/routes.py | actualizar_rol_contexto | PUT | /rbac-context/roles-contexto/{usuario_rol_contexto_id} | Sí | No |  | empresa_id, sucursal_id, unidad_negocio_id |
| backend/modules/rbac_context_sql/routes.py | obtener_permisos_efectivos_usuario | GET | /rbac-context/usuarios/{usuario_id}/permisos-efectivos | Sí | No |  | empresa_id, sucursal_id, unidad_negocio_id |
| backend/modules/rentabilidad/routes.py | rentabilidad_productos | GET | /productos | Sí | No |  |  |
| backend/modules/rentabilidad/routes.py | rentabilidad_resumen | GET | /resumen | Sí | No |  |  |
| backend/modules/reporteador_bi/routes.py | listar_paginas | GET | /paginas | No | No |  |  |
| backend/modules/reporteador_bi/routes.py | analisis_ventas | GET | /analisis-ventas | No | No |  |  |
| backend/modules/reporteador_bi/routes.py | ventas_semana | GET | /ventas-semana | No | No |  |  |
| backend/modules/reporteador_bi/routes.py | ventas_mes | GET | /ventas-mes | No | No |  |  |
| backend/modules/reporteador_bi/routes.py | ambientacion | GET | /ambientacion | No | No |  | unidad_negocio_id |
| backend/modules/reporteador_bi/routes.py | gastos | GET | /gastos | No | No |  |  |
| backend/modules/reporteador_bi/routes.py | revision_tickets | GET | /revision-tickets | No | No |  |  |
| backend/modules/reporteador_bi/routes.py | rotacion_mesas | GET | /rotacion-mesas | No | No |  |  |
| backend/modules/reporteador_bi/routes.py | analisis_documentos | GET | /analisis-documentos | No | No |  |  |
| backend/modules/reporteador_bi/routes.py | kpis_mes | GET | /kpis-mes | No | No |  |  |
| backend/modules/rh/importador/routes.py | crear_tablas_apoyo | POST | /tablas/crear | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | obtener_script_tablas | GET | /tablas/script | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | preview_importacion_excel | POST | /excel/preview | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | cargar_excel_a_staging | POST | /excel/staging | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | listar_registros_staging | GET | /staging | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | actualizar_registro_staging | PUT | /staging/{staging_id} | Sí | No |  | sucursal_id |
| backend/modules/rh/importador/routes.py | aprobar_y_cargar_maestro | POST | /staging/aprobar | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | ver_bitacora | GET | /bitacora | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | get_estadisticas_staging | GET | /staging/estadisticas | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | get_pendientes_aprobacion | GET | /staging/pendientes | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | get_incompletos | GET | /staging/incompletos | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | get_excluidos | GET | /staging/excluidos | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | get_registro_detalle | GET | /staging/{staging_id} | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | post_aprobar_registro | POST | /staging/aprobar/{staging_id} | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | post_rechazar_registro | POST | /staging/rechazar/{staging_id} | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | post_observar_registro | POST | /staging/observar/{staging_id} | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | post_aprobar_lote | POST | /staging/aprobar-lote | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | post_ejecutar_homologacion | POST | /homologacion/ejecutar | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | get_estadisticas_homologacion | GET | /homologacion/estadisticas | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | get_equivalencias | GET | /homologacion/equivalencias | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | get_verificar_homologacion | GET | /homologacion/verificar | Sí | No |  |  |
| backend/modules/rh/importador/routes.py | post_actualizar_staging_ids | POST | /homologacion/actualizar-staging | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_listar_puestos | GET | /catalogos/puestos | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_crear_puesto | POST | /catalogos/puestos | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_actualizar_puesto | PUT | /catalogos/puestos/{puesto_id} | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_eliminar_puesto | DELETE | /catalogos/puestos/{puesto_id} | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_listar_sucursales | GET | /catalogos/sucursales | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_listar_tipos_incidencias | GET | /catalogos/tipos-incidencias | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_crear_tipo_incidencia | POST | /catalogos/tipos-incidencias | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_actualizar_tipo_incidencia | PUT | /catalogos/tipos-incidencias/{tipo_id} | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_eliminar_tipo_incidencia | DELETE | /catalogos/tipos-incidencias/{tipo_id} | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_catalogos_script | GET | /catalogos/script-inicializacion | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_listar_colaboradores | GET | /colaboradores | Sí | No |  | sucursal_id |
| backend/modules/rh/routes.py | rrhh_obtener_colaborador | GET | /colaboradores/{colaborador_id} | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_crear_colaborador | POST | /colaboradores | Sí | No |  | sucursal_id |
| backend/modules/rh/routes.py | rrhh_actualizar_colaborador | PUT | /colaboradores/{colaborador_id} | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_dar_baja_colaborador | DELETE | /colaboradores/{colaborador_id} | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_listar_incidencias | GET | /incidencias | Sí | No |  | sucursal_id |
| backend/modules/rh/routes.py | rrhh_crear_incidencia | POST | /incidencias | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_importar_incidencias_excel | POST | /incidencias/importar-excel | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_plantilla_incidencias_excel | GET | /incidencias/plantilla-excel | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_listar_asistencias | GET | /asistencia | Sí | No |  | sucursal_id |
| backend/modules/rh/routes.py | rrhh_registrar_asistencia | POST | /asistencia | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_validar_asistencia | PUT | /asistencia/{check_id}/validar | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_listar_flujos_nomina | GET | /nominas/flujo | Sí | No |  | sucursal_id |
| backend/modules/rh/routes.py | rrhh_crear_flujo_nomina | POST | /nominas/flujo | Sí | No |  | sucursal_id |
| backend/modules/rh/routes.py | rrhh_enviar_nomina_rh | PUT | /nominas/flujo/{flujo_id}/enviar-rh | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_validar_nomina_gerente | PUT | /nominas/flujo/{flujo_id}/validar-gerente | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_autorizar_nomina_dg | PUT | /nominas/flujo/{flujo_id}/autorizar-dg | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_enviar_nomina_tesoreria | PUT | /nominas/flujo/{flujo_id}/enviar-tesoreria | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_marcar_nomina_pagada | PUT | /nominas/flujo/{flujo_id}/marcar-pagado | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_listar_auditoria_fiscal | GET | /auditoria-fiscal | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_dashboard | GET | /dashboard | Sí | No |  | sucursal_id |
| backend/modules/rh/routes.py | rrhh_listar_vacantes | GET | /vacantes | Sí | No |  | sucursal_id |
| backend/modules/rh/routes.py | rrhh_crear_vacante | POST | /vacantes | Sí | No |  | sucursal_id |
| backend/modules/rh/routes.py | rrhh_actualizar_vacante | PUT | /vacantes/{vacante_id} | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_eliminar_vacante | DELETE | /vacantes/{vacante_id} | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_listar_candidatos | GET | /candidatos | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_crear_candidato | POST | /candidatos | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_actualizar_candidato | PUT | /candidatos/{candidato_id} | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_eliminar_candidato | DELETE | /candidatos/{candidato_id} | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_reclutamiento_dashboard | GET | /reclutamiento/dashboard | Sí | No |  |  |
| backend/modules/rh/routes.py | rrhh_reclutamiento_script | GET | /reclutamiento/script-inicializacion | Sí | No |  |  |
| backend/modules/rh/solicitudes_catalogo.py | get_catalogos_disponibles | GET | /catalogos-disponibles | No | No |  |  |
| backend/modules/rh/solicitudes_catalogo.py | get_pendientes_notificacion | GET | /pendientes-notificacion | Sí | No |  |  |
| backend/modules/rh/solicitudes_catalogo.py | actualizar_solicitud | PUT | /{solicitud_id} | Sí | No |  |  |
| backend/modules/rh/solicitudes_catalogo.py | get_solicitud | GET | /{solicitud_id} | Sí | No |  |  |
| backend/modules/scripts_pendientes/routes.py | listar_scripts_pendientes_sql | GET | /scripts-pendientes | Sí | No |  |  |
| backend/modules/scripts_pendientes/routes.py | obtener_script_pendiente_sql | GET | /scripts-pendientes/{script_id} | Sí | No |  |  |
| backend/modules/scripts_pendientes/routes.py | crear_script_pendiente_sql | POST | /scripts-pendientes | Sí | No |  |  |
| backend/modules/scripts_pendientes/routes.py | actualizar_script_pendiente_sql | PUT | /scripts-pendientes/{script_id} | Sí | No |  |  |
| backend/modules/scripts_pendientes/routes.py | eliminar_script_pendiente_sql | DELETE | /scripts-pendientes/{script_id} | Sí | No |  |  |
| backend/modules/sistema/menu_routes.py | obtener_menus_usuario | GET | /usuario | Sí | No |  | unidad_negocio_id |
| backend/modules/sistema/menu_routes.py | obtener_menu_favoritos | GET | /favoritos | Sí | No |  |  |
| backend/modules/sistema/menu_routes.py | actualizar_menu_favoritos | PUT | /favoritos | Sí | No |  |  |
| backend/modules/sistema_users_sql/routes.py | listar_usuarios | GET | /sistema/usuarios | Sí | No |  |  |
| backend/modules/sistema_users_sql/routes.py | obtener_usuario | GET | /sistema/usuarios/{usuario_id} | Sí | No |  |  |
| backend/modules/sistema_users_sql/routes.py | obtener_usuario_por_email | GET | /sistema/usuarios/email/{email} | Sí | No |  |  |
| backend/modules/sistema_users_sql/routes.py | obtener_mi_usuario | GET | /sistema/mi-usuario | Sí | No |  |  |
| backend/modules/sql_compat_bridge/routes.py | compat_listar_consultas_custom | GET | /catalogo/consultas-custom | Sí | No |  |  |
| backend/modules/sql_compat_bridge/routes.py | compat_crear_consulta_custom | POST | /catalogo/consultas-custom | Sí | No |  |  |
| backend/modules/sql_compat_bridge/routes.py | compat_actualizar_consulta_custom | PUT | /catalogo/consultas-custom/{consulta_id} | Sí | No |  |  |
| backend/modules/sql_compat_bridge/routes.py | compat_eliminar_consulta_custom | DELETE | /catalogo/consultas-custom/{consulta_id} | Sí | No |  |  |
| backend/modules/sql_compat_bridge/routes.py | compat_listar_scripts_pendientes | GET | /explorador/scripts-pendientes/{server_id} | Sí | No |  |  |
| backend/modules/sql_compat_bridge/routes.py | compat_guardar_script | POST | /explorador/guardar-script/{server_id} | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | listar_plantillas | GET | /plantillas | No | No |  | empresa_id |
| backend/modules/tablajeria/routes.py | obtener_plantilla | GET | /plantillas/{plantilla_id} | No | No |  |  |
| backend/modules/tablajeria/routes.py | publicar_plantilla | PUT | /plantillas/{plantilla_id}/publicar | No | No |  |  |
| backend/modules/tablajeria/routes.py | listar_servidores_tablajeria | GET | /sync/servidores | No | No |  |  |
| backend/modules/tablajeria/routes.py | ejecutar_sincronizacion | POST | /sync/ejecutar | No | No |  |  |
| backend/modules/tablajeria/routes.py | obtener_sync_log | GET | /sync/log | No | No |  |  |
| backend/modules/tablajeria/routes.py | obtener_estadisticas | GET | /stats | No | No |  | empresa_id |
| backend/modules/tablajeria/routes.py | listar_ordenes | GET | /ordenes | Sí | No |  | empresa_id |
| backend/modules/tablajeria/routes.py | obtener_orden | GET | /ordenes/{orden_id} | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | crear_orden | POST | /ordenes | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | crear_orden_captura_directa | POST | /ordenes/captura-directa | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | iniciar_ejecucion_orden | PUT | /ordenes/{orden_id}/iniciar | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | registrar_resultados_orden | PUT | /ordenes/{orden_id}/resultados | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | cerrar_orden | PUT | /ordenes/{orden_id}/cerrar | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | cancelar_orden | PUT | /ordenes/{orden_id}/cancelar | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | autorizar_orden | PUT | /ordenes/{orden_id}/autorizar | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | obtener_estadisticas_ordenes | GET | /ordenes-stats | Sí | No |  | empresa_id |
| backend/modules/tablajeria/routes.py | procesar_cierre_fase6 | POST | /ordenes/{orden_id}/fase6/procesar-cierre | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | afectar_inventario | POST | /ordenes/{orden_id}/fase6/afectar-inventario | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | calcular_costeo | POST | /ordenes/{orden_id}/fase6/calcular-costeo | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | generar_poliza | POST | /ordenes/{orden_id}/fase6/generar-poliza | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | obtener_config_contable | GET | /fase6/config-contable/{empresa_id} | Sí | No |  | empresa_id |
| backend/modules/tablajeria/routes.py | guardar_config_contable | PUT | /fase6/config-contable/{empresa_id} | Sí | No |  | empresa_id |
| backend/modules/tablajeria/routes.py | get_dashboard_kpis | GET | /dashboard/kpis | Sí | No |  | empresa_id |
| backend/modules/tablajeria/routes.py | get_rendimientos_por_plantilla | GET | /dashboard/rendimientos-plantilla | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | get_tendencia_rendimientos | GET | /dashboard/tendencia | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | get_top_mermas | GET | /dashboard/top-mermas | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | get_alertas_rendimiento | GET | /dashboard/alertas | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | get_resumen_costeo | GET | /dashboard/resumen-costeo | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | exportar_ordenes | GET | /reportes/ordenes | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | exportar_mermas | GET | /reportes/mermas | Sí | No |  |  |
| backend/modules/tablajeria/routes.py | exportar_costeo | GET | /reportes/costeo | Sí | No |  |  |
| backend/modules/universal_query/routes.py | execute_universal_query_test | POST | /servers/{server_id}/universal-query-test | Sí | No |  |  |
| backend/routes/portal_inteligencia.py | login_intel | POST | /auth/login | No | No |  |  |
| backend/routes/portal_inteligencia.py | logout_intel | POST | /auth/logout | No | No |  |  |
| backend/routes/portal_inteligencia.py | me_intel | GET | /auth/me | No | No |  |  |
| backend/routes/portal_inteligencia.py | admin_listar_usuarios | GET | /admin/usuarios | No | No |  |  |
| backend/routes/portal_inteligencia.py | admin_crear_usuario | POST | /admin/usuarios | No | No |  |  |
| backend/routes/portal_inteligencia.py | admin_actualizar_usuario | PUT | /admin/usuarios/{uid} | No | No |  |  |
| backend/routes/portal_inteligencia.py | admin_eliminar_usuario | DELETE | /admin/usuarios/{uid} | No | No |  |  |
| backend/routes/portal_proveedores.py | register_supplier | POST | /auth/register | No | No |  |  |
| backend/routes/portal_proveedores.py | login_supplier | POST | /auth/login | No | No |  |  |
| backend/routes/portal_proveedores.py | logout_supplier | POST | /auth/logout | No | No |  |  |
| backend/routes/portal_proveedores.py | get_supplier_profile | GET | /auth/me | No | No |  |  |
| backend/routes/portal_proveedores.py | get_supplier_invoices | GET | /invoices | No | No |  |  |
| backend/routes/portal_proveedores.py | upload_invoice | POST | /invoices/upload | No | No |  |  |
| backend/routes/portal_proveedores.py | get_invoice_detail | GET | /invoices/{invoice_id} | No | No |  |  |
| backend/routes/portal_proveedores.py | get_purchase_orders | GET | /purchase-orders | No | No |  |  |
| backend/routes/portal_proveedores.py | get_account_status | GET | /account-status | No | No |  |  |
| backend/routes/portal_proveedores.py | get_saldos_proveedor | GET | /saldos | No | No |  |  |
| backend/routes/portal_proveedores.py | get_pending_suppliers | GET | /admin/pending-suppliers | Sí | No |  |  |
| backend/routes/portal_proveedores.py | get_all_suppliers | GET | /admin/all-suppliers | Sí | No |  |  |
| backend/routes/portal_proveedores.py | approve_supplier | POST | /admin/approve-supplier | Sí | No |  |  |
| backend/routes/portal_proveedores.py | admin_reset_supplier_password | POST | /admin/reset-password | Sí | No |  |  |
| backend/routes/portal_proveedores.py | admin_get_supplier_details | GET | /admin/supplier/{identifier} | Sí | No |  |  |
| backend/routes/portal_proveedores.py | admin_get_all_invoices | GET | /admin/invoices | Sí | No |  |  |
| backend/routes/portal_proveedores.py | get_available_servers | GET | /servers | Sí | No |  |  |
| backend/routes/portal_proveedores.py | delete_supplier | DELETE | /admin/supplier/{supplier_id} | Sí | No |  |  |
| backend/server.py | health_check | GET | /api/health | No | No |  |  |
| backend/server.py | tablero_ejecutivo_fallback | GET | /api/comercial/tablero-ejecutivo-fallback | No | No |  |  |
| backend/server.py | dashboard_comercial_v2_fallback | GET | /api/v2/comercial/dashboard-fallback | No | No |  |  |
| backend/server.py | admin_cache_stats | GET | /admin/cache/stats | Sí | No |  |  |
| backend/server.py | admin_cache_cleanup | POST | /admin/cache/cleanup | Sí | No |  |  |
| backend/server.py | admin_sync_compras_manual | POST | /admin/sync/compras | Sí | No |  |  |
| backend/server.py | admin_sync_compras_force_unlock | POST | /admin/sync/compras/force-unlock | Sí | No |  |  |
| backend/server.py | admin_sync_compras_table_counts | GET | /admin/sync/compras/table-counts | Sí | No |  |  |
| backend/server.py | admin_sync_compras_validate_columns | GET | /admin/sync/compras/validate-columns | Sí | No |  |  |
| backend/server.py | admin_detect_nuevos_manual | POST | /admin/detect/compras | Sí | No |  |  |
| backend/server.py | get_checkpoints_compras | GET | /admin/compras/checkpoints | Sí | No |  |  |
| backend/server.py | get_eventos_pendientes_compras | GET | /admin/compras/eventos-pendientes | Sí | No |  |  |
| backend/server.py | procesar_eventos_pendientes | POST | /admin/compras/procesar-eventos | Sí | No |  |  |
| backend/server.py | test_api_connection | POST | /test-api-connection | No | No |  |  |
| backend/server.py | create_server | POST | /servers | Sí | No |  |  |
| backend/server.py | get_servers | GET | /servers | Sí | No |  |  |
| backend/server.py | get_server | GET | /servers/{server_id} | Sí | No |  |  |
| backend/server.py | update_server | PUT | /servers/{server_id} | Sí | No |  |  |
| backend/server.py | delete_server | DELETE | /servers/{server_id} | Sí | No |  |  |
| backend/server.py | ping_server | GET | /servers/{server_id}/ping | No | No |  |  |
| backend/server.py | validate_server_query | POST | /servers/{server_id}/queries/validate | Sí | No |  |  |
| backend/server.py | save_server_query | PUT | /servers/{server_id}/queries/{query_type} | Sí | No |  |  |
| backend/server.py | get_server_queries | GET | /servers/{server_id}/queries | Sí | No |  |  |
| backend/server.py | delete_server_query | DELETE | /servers/{server_id}/queries/{query_type} | Sí | No |  |  |
| backend/server.py | get_tipos_movimiento | GET | /servers/{server_id}/tipos-movimiento | Sí | No |  |  |
| backend/server.py | get_categorias | GET | /servers/{server_id}/categorias | Sí | No |  |  |
| backend/server.py | get_departamentos | GET | /servers/{server_id}/departamentos | Sí | No |  |  |
| backend/server.py | get_sucursales | GET | /servers/{server_id}/sucursales | Sí | No |  |  |
| backend/server.py | get_almacenes | GET | /servers/{server_id}/almacenes | Sí | No |  | sucursal_id |
| backend/server.py | get_sucursales_config | GET | /servers/{server_id}/sucursales-config | Sí | No |  |  |
| backend/server.py | sync_sucursales_config | POST | /servers/{server_id}/sucursales-config/sync | Sí | No |  |  |
| backend/server.py | update_sucursal_config | PUT | /servers/{server_id}/sucursales-config/{sucursal_origen_id} | Sí | No |  |  |
| backend/server.py | update_sucursales_config_bulk | PUT | /servers/{server_id}/sucursales-config/bulk | Sí | No |  |  |
| backend/server.py | get_all_sucursales | GET | /sucursales | Sí | No |  |  |
| backend/server.py | get_unidades_negocio | GET | /unidades-negocio | Sí | No |  |  |
| backend/server.py | get_almacenes_softrestaurant | GET | /servers/{server_id}/almacenes-softrestaurant | Sí | No |  |  |
| backend/server.py | get_inventarios_list | GET | /servers/{server_id}/inventarios | Sí | No |  | sucursal_id |
| backend/server.py | get_insumos_pendientes | GET | /inventarios/pendientes/{server_id} | Sí | No |  |  |
| backend/server.py | get_report_filters | GET | /servers/{server_id}/report-filters | Sí | No |  |  |
| backend/server.py | generate_inventory_analysis | POST | /reports/inventory-analysis | Sí | No |  | sucursal_id |
| backend/server.py | get_movement_details | POST | /reports/movement-details | Sí | No |  |  |
| backend/server.py | get_sales_details | POST | /reports/sales-details | Sí | No |  |  |
| backend/server.py | export_excel | POST | /reports/export/excel | Sí | No |  |  |
| backend/server.py | export_pdf | POST | /reports/export/pdf | Sí | No |  |  |
| backend/server.py | export_comparativo_inventarios | POST | /reports/export/comparativo-inventarios | Sí | No |  | sucursal_id |
| backend/server.py | email_report | POST | /reports/email | Sí | No |  |  |
| backend/server.py | create_alert | POST | /alerts | Sí | No |  |  |
| backend/server.py | get_alerts | GET | /alerts | Sí | No |  |  |
| backend/server.py | update_alert | PUT | /alerts/{alert_id} | Sí | No |  |  |
| backend/server.py | delete_alert | DELETE | /alerts/{alert_id} | Sí | No |  |  |
| backend/server.py | get_catalogo_consultas | GET | /catalogo/consultas | Sí | No |  |  |
| backend/server.py | get_estructura_tablas | GET | /catalogo/estructura-tablas | Sí | No |  |  |
| backend/server.py | ejecutar_consulta_catalogo | POST | /catalogo/ejecutar-consulta | Sí | No |  |  |
| backend/server.py | ejecutar_consulta_personalizada | POST | /catalogo/consulta-personalizada | Sí | No |  |  |
| backend/server.py | debug_test_connection | POST | /debug/test-connection | Sí | No |  |  |
| backend/server.py | debug_tipos_movimiento_live | GET | /debug/tipos-movimiento-live/{server_id} | Sí | No |  |  |
| backend/server.py | debug_test_queries | POST | /debug/test-queries | Sí | No |  |  |
| backend/server.py | get_dashboard_inventory_summary | GET | /dashboard/inventory-summary | Sí | No |  |  |
| backend/server.py | get_dashboard_servers | GET | /dashboard/servers-configured | Sí | No |  |  |
| backend/server.py | get_dashboard_metrics | GET | /dashboard/metrics | Sí | No |  |  |
| backend/server.py | obtener_inventarios_fisicos | GET | /compras/inventarios-fisicos/{server_id} | No | No |  | scope, sucursal_id, unidad_negocio_id |
| backend/server.py | obtener_inventarios_fisicos_sql_first | GET | /compras/inventarios-fisicos-sql-first/{server_id} | Sí | No |  | sucursal_id |
| backend/server.py | obtener_pedidos_vigentes | GET | /compras/pedidos-vigentes/{server_id} | No | No |  | scope, unidad_negocio_id |
| backend/server.py | obtener_detalle_pedido_manual | GET | /compras/detalle-pedido-manual/{server_id} | No | No |  | empresa_id, scope, sucursal_id |
| backend/server.py | obtener_pedidos_vigentes_sql_first | GET | /compras/pedidos-vigentes-sql-first/{server_id} | Sí | No |  |  |
| backend/server.py | obtener_detalle_movimientos | GET | /compras/detalle-movimientos/{server_id} | No | No |  |  |
| backend/server.py | obtener_detalle_consumos | GET | /compras/detalle-consumos/{server_id} | No | No |  |  |
| backend/server.py | obtener_detalle_pedido | GET | /compras/detalle-pedido/{server_id}/{folio} | No | No |  | empresa_id, scope, sucursal_id |
| backend/server.py | calcular_pedido_sugerido | POST | /compras/calculo-pedido | No | No |  | empresa_id, scope, sucursal_id |
| backend/server.py | obtener_parametros_compra | GET | /compras/parametros/{server_id} | No | No |  | sucursal_id |
| backend/server.py | guardar_parametros_compra | POST | /compras/parametros | No | No |  | sucursal_id |
| backend/server.py | obtener_productos_para_captura | POST | /compras/productos-para-captura | No | No |  | empresa_id, scope, sucursal_id |
| backend/server.py | obtener_productos_para_captura_sql_first | POST | /compras/productos-para-captura-sql-first | Sí | No |  |  |
| backend/server.py | realizar_auditoria_operativa | POST | /compras/auditoria-operativa | No | No |  | empresa_id, scope, sucursal_id |
| backend/server.py | obtener_uso_inverso_receta_reportes | POST | /reports/inverse-recipe-usage | Sí | No |  |  |
| backend/server.py | guardar_inventario_provisional | POST | /compras/inventarios-provisionales | Sí | No |  | unidad_negocio_id |
| backend/server.py | obtener_inventarios_provisionales | GET | /compras/inventarios-provisionales/{unidad_negocio_id} | Sí | No |  | unidad_negocio_id |
| backend/server.py | eliminar_inventario_provisional | DELETE | /compras/inventarios-provisionales/{item_id} | Sí | No |  |  |
| backend/server.py | limpiar_inventarios_provisionales | DELETE | /compras/inventarios-provisionales/limpiar/{unidad_negocio_id} | Sí | No |  | unidad_negocio_id |
| backend/server.py | obtener_detalle_movimientos_post | POST | /compras/detalle-movimientos | Sí | No |  |  |
| backend/server.py | obtener_detalle_movimientos_sql_first | POST | /compras/detalle-movimientos-sql-first | Sí | No |  |  |
| backend/server.py | obtener_detalle_consumos_post | POST | /compras/detalle-consumos | Sí | No |  |  |
| backend/server.py | obtener_dashboard_compras | GET | /compras/dashboard/{server_id} | No | No |  | empresa_id, scope, sucursal_id |
| backend/server.py | obtener_analisis_compras | POST | /compras/analisis | No | No |  | empresa_id, scope, sucursal_id |
| backend/server.py | obtener_facturas_proveedor | GET | /compras/facturas-proveedor/{server_id} | No | No |  | empresa_id, scope, sucursal_id |
| backend/server.py | obtener_detalle_factura | GET | /compras/detalle-factura/{server_id}/{folio} | No | No |  | empresa_id, scope, sucursal_id |
| backend/server.py | obtener_facturas_proveedor_sql_first | GET | /compras/facturas-proveedor-sql-first/{server_id} | Sí | No |  |  |
| backend/server.py | obtener_detalle_factura_sql_first | GET | /compras/detalle-factura-sql-first/{server_id}/{folio} | Sí | No |  |  |
| backend/server.py | obtener_detalle_consumos_sql_first | POST | /compras/detalle-consumos-sql-first | Sí | No |  |  |
| backend/server.py | obtener_dashboard_compras_sql_first | GET | /compras/dashboard-sql-first/{server_id} | Sí | No |  |  |
| backend/server.py | listar_conexiones_explorables | GET | /explorador/conexiones-explorables | Sí | No |  |  |
| backend/server.py | listar_tablas | GET | /explorador/tablas/{server_id} | Sí | No |  |  |
| backend/server.py | listar_columnas | GET | /explorador/columnas/{server_id}/{tabla} | Sí | No |  |  |
| backend/server.py | listar_relaciones | GET | /explorador/relaciones/{server_id}/{tabla} | Sí | No |  |  |
| backend/server.py | preview_tabla | GET | /explorador/preview/{server_id}/{tabla} | Sí | No |  |  |
| backend/server.py | ejecutar_query_libre | POST | /explorador/query/{server_id} | Sí | No |  |  |
| backend/server.py | ejecutar_script_sql | POST | /explorador/ejecutar-script/{server_id} | Sí | No |  |  |
| backend/server.py | ejecutar_script_con_credenciales | GET | /rrhh/catalogos/puestos | Sí | No |  |  |
| backend/server.py | finanzas_dashboard | GET | /finanzas/dashboard | Sí | No |  | sucursal_id, unidad_negocio_id, unidades_permitidas |
| backend/server.py | finanzas_listar_presupuestos | GET | /finanzas/presupuestos | Sí | No |  | sucursal_id, unidad_negocio_id, unidades_permitidas |
| backend/server.py | finanzas_crear_presupuesto | POST | /finanzas/presupuestos | Sí | No |  |  |
| backend/server.py | finanzas_actualizar_presupuesto | PUT | /finanzas/presupuestos/{presupuesto_id} | Sí | No |  |  |
| backend/server.py | finanzas_eliminar_presupuesto | DELETE | /finanzas/presupuestos/{presupuesto_id} | Sí | No |  |  |
| backend/server.py | finanzas_listar_categorias | GET | /finanzas/categorias | Sí | No |  | unidades_permitidas |
| backend/server.py | finanzas_registrar_movimiento | POST | /finanzas/registrar-movimiento | Sí | No |  |  |
| backend/server.py | finanzas_obtener_script_inicializacion | GET | /finanzas/script-inicializacion | Sí | No |  |  |
| backend/server.py | buscar_en_bd | GET | /explorador/buscar/{server_id} | Sí | No |  |  |
| backend/server.py | listar_consultas_rich | GET | /catalogo/consultas-rich | Sí | No |  |  |
| backend/server.py | ejecutar_consulta_catalogo | POST | /catalogo/ejecutar-rich/{consulta_id} | Sí | No |  |  |
| backend/server.py | actualizar_consulta_sql | PUT | /catalogo/consultas/{consulta_id} | Sí | No |  |  |
| backend/server.py | ejecutar_consulta_custom | POST | /catalogo/ejecutar-custom/{consulta_id} | Sí | No |  |  |
| backend/server.py | get_pool_statistics | GET | /sistema/pool-stats | Sí | No |  |  |
| backend/server.py | reset_pool_connections | POST | /sistema/pool-reset | Sí | No |  |  |
| backend/server.py | sql_server_health_check | GET | /sistema/sql-health | Sí | No |  |  |
| backend/server.py | sql_server_test_query | POST | /sistema/sql-health/test-query | Sí | No |  |  |
| backend/server.py | obtener_pendientes_unificados | GET | /sistema/pendientes-unificados | Sí | No |  |  |
| backend/server.py | obtener_script_tareas | GET | /sistema/script-tareas | Sí | No |  |  |
| backend/server.py | listar_ciclos_nomina | GET | /nomina/ciclos | Sí | No |  | sucursal_id |
| backend/server.py | obtener_ciclo_nomina | GET | /nomina/ciclos/{ciclo_id} | Sí | No |  |  |
| backend/server.py | crear_ciclo_nomina | POST | /nomina/ciclos | Sí | No |  | sucursal_id |
| backend/server.py | avanzar_etapa_nomina | POST | /nomina/ciclos/{ciclo_id}/avanzar | Sí | No |  |  |
| backend/server.py | rechazar_ciclo_nomina | POST | /nomina/ciclos/{ciclo_id}/rechazar | Sí | No |  |  |
| backend/server.py | listar_movimientos_nomina | GET | /nomina/ciclos/{ciclo_id}/movimientos | Sí | No |  |  |
| backend/server.py | agregar_movimiento_nomina | POST | /nomina/ciclos/{ciclo_id}/movimientos | Sí | No |  |  |
| backend/server.py | eliminar_movimiento_nomina | DELETE | /nomina/movimientos/{movimiento_id} | Sí | No |  |  |
| backend/server.py | obtener_configuracion_nomina | GET | /nomina/configuracion | Sí | No |  |  |
| backend/server.py | guardar_configuracion_nomina | POST | /nomina/configuracion | Sí | No |  |  |
| backend/server.py | listar_kpis_nomina | GET | /nomina/kpis | Sí | No |  |  |
| backend/server.py | crear_kpi_nomina | POST | /nomina/kpis | Sí | No |  |  |
| backend/server.py | obtener_script_tablas_nomina | GET | /nomina/script-tablas | Sí | No |  |  |
| backend/server.py | get_estructura_organizacional | GET | /sistema/estructura-organizacional | Sí | No | SISTEMA_ESTRUCTURA_VER |  |
| backend/server.py | get_mapeo_servidores | GET | /sistema/mapeo-servidores | Sí | No |  |  |
| backend/server.py | get_permisos_catalogo_v2 | GET | /sistema/permisos-catalogo-v2 | Sí | No |  |  |
| backend/server.py | admin_asignar_permiso | POST | /admin/permisos/asignar | Sí | No |  |  |
| backend/server.py | admin_asignar_rol | POST | /admin/roles/asignar | Sí | No |  |  |
| backend/server.py | get_bitacora_rbac | GET | /admin/bitacora | Sí | No |  |  |
| backend/server.py | get_bitacora_evento_detalle | GET | /admin/bitacora/{evento_id} | Sí | No |  |  |
| backend/server.py | get_perfiles_disponibles | GET | /admin/perfiles | Sí | No |  |  |
| backend/server.py | asignar_perfil_usuario | POST | /admin/perfiles/asignar | Sí | No |  |  |
| backend/server.py | retirar_perfil_usuario | POST | /admin/perfiles/retirar | Sí | No |  |  |
| backend/server.py | download_schema_zip | GET | /api/download/schema | No | No |  |  |
| backend/server.py | download_schema_sql | GET | /api/download/schema-sql | No | No |  |  |
| backend/server.py | download_backup_full | GET | /api/download/backup-full | No | No |  |  |
| backend/server.py | download_manual_desarrollo | GET | /api/download/manual-desarrollo | No | No |  |  |
| backend/server.py | download_backup_db_completo | GET | /api/download/backup-db-completo | No | No |  |  |
| backend/server.py | download_backup_codigo_fuente | GET | /api/download/backup-codigo-fuente | No | No |  |  |
| backend/server.py | descargar_codigo_simple | GET | /api/descargar/codigo | No | No |  |  |
