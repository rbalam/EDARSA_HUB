# Seeds y migraciones

## Seeds

- `backend/database/validation/phase1_rbac_menu_seed_audit.sql`
- `backend/modules/crm/sql/02_seed_crm_catalogs.sql`
- `backend/scripts/create_cava_socios_rbac.py`
- `backend/scripts/create_comercial_pricing_rbac.py`
- `backend/scripts/create_tablajeria_rbac.py`

## Migraciones

- `backend/database/migrations/007_crear_tabla_migracion_mongosql_mapeo.sql`
- `backend/database/migrations/008_crear_sistema_rbac_tablas.sql`
- `backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql`
- `backend/database/migrations/017_registrar_inteligencia_comercial_y_transicionales.sql`
- `backend/database/migrations/019_clasificacion_masiva_por_familia.sql`
- `backend/database/migrations/020_marcar_sistema_rbac_transicion.sql`
- `backend/database/migrations/023_rbac_inteligencia_comercial_matriz_ideal.sql`
- `backend/database/migrations/023a_crear_roles_comerciales.sql`
- `backend/database/migrations/030_diagnostico_mapeo_rbac_mongo_a_sql.sql`
- `backend/database/migrations/032_validacion_inteligencia_comercial_fase1.sql`
- `backend/database/migrations/033_reactivar_superadmin_inteligencia_gestionar.sql`
- `backend/database/migrations/20260630_010_reasignar_usuario_a_operador_rbac.sql`
- `backend/database/migrations/20260630_011_desactivar_roles_vacios_sin_usuarios_rbac.sql`
- `backend/database/migrations/20260630_012_rbac_bitacora_permiso.sql`
- `backend/database/migrations/20260702_013_rbac_superadmin_scheduler_admin_permissions.sql`
- `backend/database/migrations/20260702_014_rbac_superadmin_sensitive_phase2_permissions.sql`
- `backend/database/migrations/20260702_015_rbac_deactivate_non_superadmin_admin_config_permissions.sql`
- `backend/database/migrations/20260702_016_rbac_superadmin_cargos_remaining_actions.sql`
- `backend/database/migrations/20260702_019_rbac_workflow_gestionar_superadmin_explicit.sql`
- `backend/database/migrations/20260702_020_rbac_compras_tesoreria_role_explicit.sql`
- `backend/database/migrations/20260702_021_rbac_compras_operativo_explicit.sql`
- `backend/database/migrations/20260702_022_rbac_compras_gestionar_operativo_explicit.sql`
- `backend/database/migrations/20260702_023_rbac_catalogos_sistemas_ver.sql`
- `backend/database/migrations/20260708_002_fix_runtime_overlay_ticket_promedio.sql`
- `backend/database/migrations/20260718_001_ia_assistant_schema_rbac.sql`
- `backend/database/migrations/20260719_001_rbac_compras_rol_compras_explicit.sql`
- `backend/database/migrations/20260722_001_finanzas_cxp_decisiones_pago.sql`
- `backend/database/migrations/20260722_002_cfdi_portal_comprobaciones_contract.sql`
- `backend/migrations/PROPUESTA_puente_producto_mapeoorigen.sql`
- `backend/migrations/_splice_bitacora_alcance.py`
- `backend/migrations/_splice_rbac_endpoints.py`
- `backend/migrations/auditar_hardcodes_rbac.py`
- `backend/migrations/ejecutar_dml_canonizacion_insumos.py`
- `backend/migrations/rbac_bitacora_sql_20260607.py`
- `backend/migrations/rbac_pilot_sql_20260607.py`

## Validaciones

- `backend/database/diagnostics/015_diagnostico_completo_rbac_canonico.sql`
- `backend/database/diagnostics/016_verificar_datos_rbac.sql`
- `backend/database/diagnostics/018_validacion_rbac_inteligencia_comercial.sql`
- `backend/database/migrations/030_diagnostico_mapeo_rbac_mongo_a_sql.sql`
- `backend/database/validation/20260713_018_rbac_schema_convergence_audit.sql`
- `backend/database/validation/20260714_019_rbac_schema_convergence_sectioned_audit.sql`
- `backend/database/validation/20260718_001_ia_assistant_schema_rbac_validation.sql`
- `backend/database/validation/phase1_rbac_menu_seed_audit.sql`
- `backend/database/validation/phase2_rbac_empty_roles_impact_audit.sql`
- `backend/database/validation/phase2c_rbac_menu_multiuser_candidates.sql`
- `backend/database/validation/phase2c_rbac_usuario_operador_post_validation.sql`
- `backend/database/validation/phase2d_rbac_empty_roles_inactive_post_validation.sql`
- `backend/database/validation/phase2e_rbac_bitacora_permiso_validation.sql`
- `backend/database/validation/phase2f_rbac_superadmin_scheduler_admin_permissions_validation.sql`

## Obligaciones

Toda migración RBAC debe ser idempotente, reversible, auditable, preservar SUPERADMIN y actualizar esta documentación.
