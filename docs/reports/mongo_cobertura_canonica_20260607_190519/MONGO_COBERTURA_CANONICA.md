# Mongo Sunset Fase 6-bis — Verificación de cobertura canónica (solo lectura)

Fecha: 2026-06-07T19:05:21

## Estado

✅ Solo lectura. No se borró nada, no se modificó Mongo ni SQL.

## Fuente

- Fase 3: `/app/docs/reports/mongo_sql_compare_20260607_182308/MONGO_SQL_COVERAGE_182308.json`

## Resumen

- Colecciones sensibles revisadas: **34**

### Por dictamen

- CUBIERTA_PARCIALMENTE: **27**
- SIN_COBERTURA: **7**

### Por acción recomendada

- REQUIERE_MIGRACION_SEMANTICA: **7**
- VALIDAR_MANUALMENTE: **6**
- VALIDAR_MUESTRA_ANTES_DE_BORRAR: **21**

### Por confianza

- BAJA: **7**
- MEDIA: **21**
- MEDIA_BAJA: **6**

## Matriz

| Base | Colección | Docs | Clasificación | SQL candidata | SQL rows | Score | Dictamen | Acción | Confianza |
|---|---|---:|---|---|---:|---:|---|---|---|
| cab003 | cargos_economicos | 5 | Legacy sin uso detectado | dbo.CavaSocios_Cargos | 1 | 0.5367 | CUBIERTA_PARCIALMENTE | VALIDAR_MANUALMENTE | MEDIA_BAJA |
| cab003 | detalle_diferencias | 18 | Legacy sin uso detectado | dbo.Inventarios_DiferenciasDetalle | 24 | 0.5406 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| cab003 | notificaciones_log | 4 | Auditoría / Logs | dbo.Operativo_Notificaciones_Log | 0 | 0.6288 | SIN_COBERTURA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| cab003 | responsabilidad_economica | 5 | Configuración | dbo.CavaSocios_Movimientos | 3 | 0.51 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| cab003 | responsabilidad_historial | 10 | Usuarios / Auth / RBAC | dbo.propinas_tpv_historial | 0 | 0.5789 | SIN_COBERTURA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | audit_password_reset | 3 | Auditoría / Logs | dbo.Sync_Logs | 3 | 0.1417 | SIN_COBERTURA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | consultas_custom | 6 | Configuración | dbo.Sistema_ConsultasCustom | 6 | 0.5625 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| edarsa_hub | inventarios_procesados_auto | 158 | Inventarios | dbo.Inventarios_ProcesadosAuto | 158 | 0.61 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| edarsa_hub | pedidos_procesados_automatizacion | 2 | Compras / Proveedores | dbo.automatizacion_inventarios_folios_procesados | 1 | 0.6008 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| edarsa_hub | permisos_catalogos | 8 | Auditoría / Logs | dbo.RBAC_Permisos | 9 | 0.6056 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| edarsa_hub | portal_suppliers | 3 | Compras / Proveedores | dbo.Portal_Proveedores | 3 | 0.6271 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| edarsa_hub | propinas_config | 1 | Configuración | dbo.propinas_tpv_config | 0 | 0.6369 | SIN_COBERTURA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | rbac_audit_log | 598 | Auditoría / Logs | dbo.Compras_Sync_Log | 387 | 0.1179 | SIN_COBERTURA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | rbac_permisos | 43 | Usuarios / Auth / RBAC | dbo.RBAC_Permisos | 9 | 0.7618 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| edarsa_hub | rbac_roles | 6 | Usuarios / Auth / RBAC | dbo.Sistema_RBAC_Roles | 6 | 0.8269 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| edarsa_hub | rbac_usuarios_roles | 72 | Usuarios / Auth / RBAC | dbo.Sistema_RBAC_Roles | 6 | 0.6274 | CUBIERTA_PARCIALMENTE | VALIDAR_MANUALMENTE | MEDIA_BAJA |
| edarsa_hub | roles | 4 | Usuarios / Auth / RBAC | dbo.Sistema_RBAC_Roles | 6 | 0.6848 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| edarsa_hub | sec_bitacora_acceso | 27 | Auditoría / Logs | dbo.Inventarios_DiferenciasDetalle | 24 | 0.1036 | SIN_COBERTURA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | sec_bitacora_admin | 61 | Auditoría / Logs | dbo.RH_Homologacion_Equivalencias | 56 | 0.1018 | SIN_COBERTURA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | sec_empresas | 1 | Legacy sin uso detectado | dbo.Sistema_Empresas | 5 | 0.595 | CUBIERTA_PARCIALMENTE | VALIDAR_MANUALMENTE | MEDIA_BAJA |
| edarsa_hub | sec_mapeo_servidor_sucursal | 7 | Legacy sin uso detectado | dbo.Sistema_ServidoresSucursalesConfig | 7 | 0.5738 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| edarsa_hub | sec_metadata | 1 | Legacy sin uso detectado | dbo.Sistema_DeudaTecnica_TablasDuplicadas | 9 | 0.5028 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| edarsa_hub | sec_modulos_sistema | 10 | Compras / Proveedores | dbo.Sistema_Modulos | 28 | 0.6929 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| edarsa_hub | sec_perfiles | 5 | Usuarios / Auth / RBAC | dbo.Usuario_Roles | 22 | 0.5061 | CUBIERTA_PARCIALMENTE | VALIDAR_MANUALMENTE | MEDIA_BAJA |
| edarsa_hub | sec_permisos_catalogo | 90 | Auditoría / Logs | dbo.RBAC_Permisos | 9 | 0.6176 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| edarsa_hub | sec_roles | 5 | Usuarios / Auth / RBAC | dbo.Sistema_RBAC_Roles | 6 | 0.6962 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| edarsa_hub | sec_sucursales | 7 | Legacy sin uso detectado | dbo.Sistema_Sucursales | 5 | 0.6318 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| edarsa_hub | sec_unidades_negocio | 7 | Usuarios / Auth / RBAC | dbo.Unidades_Negocio | 5 | 0.7173 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| edarsa_hub | server_connection_status | 1 | Legacy sin uso detectado | dbo.Sistema_ServidoresEstado | 13 | 0.4769 | CUBIERTA_PARCIALMENTE | VALIDAR_MANUALMENTE | MEDIA_BAJA |
| edarsa_hub | server_status | 13 | Legacy sin uso detectado | dbo.Sistema_ServidoresEstado | 13 | 0.5692 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| edarsa_hub | users | 17 | Auditoría / Logs | dbo.Usuario_Catalogo | 20 | 0.5511 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| edarsahub | notification_config | 11 | Configuración | dbo.Sistema_NotificacionesConfig | 6 | 0.4648 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| edarsahub | notification_templates | 11 | Legacy sin uso detectado | dbo.Sistema_NotificacionesConfig | 6 | 0.4665 | CUBIERTA_PARCIALMENTE | VALIDAR_MUESTRA_ANTES_DE_BORRAR | MEDIA |
| edarsahub | users_legacy_backup_auth_rbac_20260604 | 1 | Usuarios / Auth / RBAC | dbo.Backup_P5_RBAC_Permisos | 9 | 0.5243 | CUBIERTA_PARCIALMENTE | VALIDAR_MANUALMENTE | MEDIA_BAJA |

## Criterio

```text
CUBIERTA_TOTALMENTE no autoriza borrado automático.
CUBIERTA_PARCIALMENTE requiere validación de muestra.
SIN_COBERTURA / REQUIERE_MIGRACION_SEMANTICA no debe borrarse aún.
```
