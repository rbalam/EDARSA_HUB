# AUDITORÍA CREDENCIALES HARDCODED EDARSAHUB

**Fecha:** 2026-06-04  
**Estado:** DOCUMENTADO (Sin modificaciones)

---

## Resumen

| Tipo | Cantidad |
|------|----------|
| Archivos .py con credenciales | 93 |
| Archivos .md (documentación) | 41 |
| Total ocurrencias | 445 |

---

## Archivos Python con Credenciales (Requieren Limpieza)

```text
/app/backend/api/admin_data_quality.py
/app/backend/api/admin_scheduler_resync.py
/app/backend/api/configuracion_operativa_unidades.py
/app/backend/core/alcance_helper.py
/app/backend/core/auth/user_repository_sql.py
/app/backend/core/context_resolver.py
/app/backend/core/empresa_resolver.py
/app/backend/core/pool.py
/app/backend/core/rbac/repository_sql.py
/app/backend/core/rbac_helper_sql.py
/app/backend/core/scheduler/jobs/crm_sync_job.py
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py
/app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py
/app/backend/core/scheduler/jobs/sync_compras_job.py
/app/backend/core/scheduler/jobs/vtiger_sync_job.py
/app/backend/core/scheduler/sql_repository.py
/app/backend/core/security.py
/app/backend/core/server_registry.py
/app/backend/core/system_capability_resolver.py
/app/backend/core/unidades_registry.py
/app/backend/core/user_access_context.py
/app/backend/core/utils/operational_window.py
/app/backend/modules/api_connections/repository.py
/app/backend/modules/api_connections/universal_test_routes.py
/app/backend/modules/auth/context_service.py
/app/backend/modules/auth/password_reset.py
/app/backend/modules/auth/repository.py
/app/backend/modules/auth/service.py
/app/backend/modules/catalogos/routes.py
/app/backend/modules/cava_socios/service.py
/app/backend/modules/comercial/inteligencia_comercial_routes.py
/app/backend/modules/comercial/repository.py
/app/backend/modules/comercial/routes.py
/app/backend/modules/comercial/service.py
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py
/app/backend/modules/comercial_v2/repository_readonly.py
/app/backend/modules/compras/eventos_compras.py
/app/backend/modules/compras/repository_compras_sql.py
/app/backend/modules/compras/repository_pedidos_sql.py
/app/backend/modules/compras/sync_service.py
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py
/app/backend/modules/crm/automation_service.py
/app/backend/modules/crm/comercial_routes.py
/app/backend/modules/crm/integration_routes.py
/app/backend/modules/crm/native_routes.py
/app/backend/modules/crm/repository.py
/app/backend/modules/crm/sql/execute_crm_migration.py
/app/backend/modules/crm/trigger_service.py
/app/backend/modules/fase2_operativo/repositories/sql_base_repository.py
/app/backend/modules/fase2_operativo/sql_repository.py
/app/backend/modules/finanzas/propinas_tpv/repository_edarsahub.py
/app/backend/modules/finanzas/repository_cuadres_z_edarsahub.py
/app/backend/modules/finanzas/repository_ingresos_edarsahub.py
/app/backend/modules/finanzas/repository_softrestaurant.py
/app/backend/modules/finanzas/sync_cortes_mpro.py
/app/backend/modules/finanzas/sync_cortes_softrestaurant.py
/app/backend/modules/finanzas/sync_propinas_mpro.py
/app/backend/modules/finanzas/sync_propinas_softrestaurant.py
/app/backend/modules/finanzas/test_conn_cienfuegos.py
/app/backend/modules/inteligencia_comercial/routes.py
/app/backend/modules/rh/repository.py
/app/backend/modules/sistema/menu_service.py
/app/backend/modules/tablajeria/dashboard_service.py
/app/backend/modules/tablajeria/fase6_service.py
/app/backend/modules/tablajeria/routes.py
/app/backend/scripts/actualizacion_kpi_proyeccion_comercial.py
/app/backend/scripts/audit_fecha_operativa_0600.py
/app/backend/scripts/backfill_cienfuegos_mayo_2026.py
/app/backend/scripts/consolidado_general_sistema_comercial.py
/app/backend/scripts/consolidado_general_sistema_comercial_v2.py
/app/backend/scripts/consultar_cache_finops.py
/app/backend/scripts/correccion_proyeccion_y_moneda_final.py
/app/backend/scripts/correccion_sistema_menus_y_fallbacks.py
/app/backend/scripts/create_cava_socios_rbac.py
/app/backend/scripts/create_cava_socios_tables.py
/app/backend/scripts/create_crm_automation_tables.py
/app/backend/scripts/create_scheduler_tables.py
/app/backend/scripts/create_sesiones_tables.py
/app/backend/scripts/create_tablajeria_rbac.py
/app/backend/scripts/create_unidades_negocio_table.py
/app/backend/scripts/create_workflow_tables.py
/app/backend/scripts/seed_inteligencia_demo.py
/app/backend/scripts/seed_ventas_consolidadas.py
/app/backend/scripts/sync_response_cache_finops.py
/app/backend/scripts/update_proyeccion_con_funcion.py
/app/backend/server.py
/app/backend/tests/test_migracion_servidores_sql.py
/app/backend/tests/test_simulacion_controlada.py
/app/backend/tools/sync_sales_dry_run.py
/app/backend/tools/test_sql_connection_from_servidores.py
/app/backend/tools/validate_server_secret_key.py
```

---

## Detalle por Módulo

### Módulos Críticos (Auth/Core)
```text
/app/backend/core/alcance_helper.py
/app/backend/core/auth/user_repository_sql.py
/app/backend/core/context_resolver.py
/app/backend/core/empresa_resolver.py
/app/backend/core/pool.py
/app/backend/core/rbac/repository_sql.py
/app/backend/core/rbac_helper_sql.py
/app/backend/core/scheduler/jobs/crm_sync_job.py
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py
/app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py
/app/backend/core/scheduler/jobs/sync_compras_job.py
/app/backend/core/scheduler/jobs/vtiger_sync_job.py
/app/backend/core/scheduler/sql_repository.py
/app/backend/core/security.py
/app/backend/core/server_registry.py
/app/backend/core/system_capability_resolver.py
/app/backend/core/unidades_registry.py
/app/backend/core/user_access_context.py
/app/backend/core/utils/operational_window.py
/app/backend/modules/auth/context_service.py
/app/backend/modules/auth/password_reset.py
/app/backend/modules/auth/repository.py
/app/backend/modules/auth/service.py
```

### Módulos Comerciales
```text
/app/backend/modules/comercial/inteligencia_comercial_routes.py
/app/backend/modules/comercial/repository.py
/app/backend/modules/comercial/routes.py
/app/backend/modules/comercial/service.py
/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py
/app/backend/modules/comercial_v2/repository_readonly.py
```

### Módulos Sistema/Config
```text
/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py
/app/backend/modules/sistema/menu_service.py
```

### Jobs/Scheduler
```text
/app/backend/core/scheduler/jobs/crm_sync_job.py
/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py
/app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py
/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py
/app/backend/core/scheduler/jobs/sync_compras_job.py
/app/backend/core/scheduler/jobs/vtiger_sync_job.py
/app/backend/core/scheduler/sql_repository.py
```

---

## Recomendación

### Opción A: Centralizar Configuración
Crear `/app/backend/core/config/edarsahub.py`:
```python
import os

EDARSAHUB_CONFIG = {
    'host': os.environ.get('EDARSAHUB_HOST'),
    'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
    'database': os.environ.get('EDARSAHUB_DATABASE'),
    'username': os.environ.get('EDARSAHUB_USERNAME'),
    'password': os.environ.get('EDARSAHUB_PASSWORD')
}

def get_edarsahub_connection():
    import pymssql
    if not all([EDARSAHUB_CONFIG['host'], EDARSAHUB_CONFIG['username'], EDARSAHUB_CONFIG['password']]):
        raise RuntimeError("EDARSAHUB_* variables de entorno no configuradas")
    return pymssql.connect(
        server=EDARSAHUB_CONFIG['host'],
        user=EDARSAHUB_CONFIG['username'],
        password=EDARSAHUB_CONFIG['password'],
        database=EDARSAHUB_CONFIG['database'],
        port=EDARSAHUB_CONFIG['port'],
        timeout=30
    )
```

### Opción B: Eliminar Fallbacks
Cambiar todos los:
```python
os.environ.get('EDARSAHUB_HOST', '54.39.104.176')
```
Por:
```python
os.environ.get('EDARSAHUB_HOST')  # Sin fallback - falla si no está configurado
```

---

## Archivos Ya Corregidos (Esta Sesión)

| Archivo | Estado |
|---------|--------|
| `/app/backend/modules/compras/sync_service.py` | ✅ Usa ENV |
| `/app/backend/server.py` | ✅ Corregido fallback |

---

*Reporte de auditoría - E1 Agent*
