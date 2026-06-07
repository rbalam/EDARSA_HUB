# Mongo Sunset Fase 6-ter — Validación por muestreo de llaves (solo lectura)

Fecha: 2026-06-07T19:14:39

## Estado

✅ Solo lectura. No se borró nada, no se modificó Mongo ni SQL.

## Parámetros

- Muestra por colección: **10**
- Solo fuertes: **False**
- Fuente: `/app/docs/reports/mongo_cobertura_canonica_20260607_190519/MONGO_COBERTURA_CANONICA.json`

## Resumen por dictamen de muestra

- CUBIERTA_CONFIRMADA: **6**
- NO_CUBIERTA: **18**
- SIN_LLAVE_COMPARABLE: **3**

## Resumen por colección

| Base | Colección | Docs | Tabla SQL | Muestra | Enc | Amb | NoEnc | SinLlave | Dictamen | Acción | Confianza |
|---|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| edarsa_hub | rbac_roles | 6 | dbo.Sistema_RBAC_Roles | 6 | 0 | 0 | 6 | 0 | NO_CUBIERTA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | sec_unidades_negocio | 7 | dbo.Unidades_Negocio | 7 | 3 | 0 | 4 | 0 | NO_CUBIERTA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | portal_suppliers | 3 | dbo.Portal_Proveedores | 3 | 3 | 0 | 0 | 0 | CUBIERTA_CONFIRMADA | CANDIDATA_A_BORRADO_POSTERIOR_CON_RESPALDO | ALTA |
| edarsa_hub | inventarios_procesados_auto | 158 | dbo.Inventarios_ProcesadosAuto | 10 | 10 | 0 | 0 | 0 | CUBIERTA_CONFIRMADA | CANDIDATA_A_BORRADO_POSTERIOR_CON_RESPALDO | ALTA |
| edarsa_hub | consultas_custom | 6 | dbo.Sistema_ConsultasCustom | 6 | 6 | 0 | 0 | 0 | CUBIERTA_CONFIRMADA | CANDIDATA_A_BORRADO_POSTERIOR_CON_RESPALDO | ALTA |
| edarsa_hub | users | 17 | dbo.Usuario_Catalogo | 10 | 10 | 0 | 0 | 0 | CUBIERTA_CONFIRMADA | CANDIDATA_A_BORRADO_POSTERIOR_CON_RESPALDO | ALTA |
| edarsa_hub | rbac_permisos | 43 | dbo.RBAC_Permisos | 10 | 0 | 2 | 8 | 0 | NO_CUBIERTA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | sec_roles | 5 | dbo.Sistema_RBAC_Roles | 5 | 0 | 0 | 5 | 0 | NO_CUBIERTA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | sec_modulos_sistema | 10 | dbo.Sistema_Modulos | 10 | 10 | 0 | 0 | 0 | CUBIERTA_CONFIRMADA | CANDIDATA_A_BORRADO_POSTERIOR_CON_RESPALDO | ALTA |
| edarsa_hub | roles | 4 | dbo.Sistema_RBAC_Roles | 4 | 0 | 0 | 4 | 0 | NO_CUBIERTA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | sec_sucursales | 7 | dbo.Sistema_Sucursales | 7 | 0 | 0 | 7 | 0 | NO_CUBIERTA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | rbac_usuarios_roles | 72 | dbo.Sistema_RBAC_Roles | 10 | 0 | 0 | 10 | 0 | NO_CUBIERTA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | sec_permisos_catalogo | 90 | dbo.RBAC_Permisos | 10 | 2 | 8 | 0 | 0 | NO_CUBIERTA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | permisos_catalogos | 8 | dbo.RBAC_Permisos | 8 | 0 | 0 | 0 | 8 | SIN_LLAVE_COMPARABLE | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | pedidos_procesados_automatizacion | 2 | dbo.automatizacion_inventarios_folios_procesados | 2 | 0 | 0 | 2 | 0 | NO_CUBIERTA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | sec_empresas | 1 | dbo.Sistema_Empresas | 1 | 0 | 0 | 1 | 0 | NO_CUBIERTA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | sec_mapeo_servidor_sucursal | 7 | dbo.Sistema_ServidoresSucursalesConfig | 7 | 0 | 0 | 7 | 0 | NO_CUBIERTA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | server_status | 13 | dbo.Sistema_ServidoresEstado | 10 | 10 | 0 | 0 | 0 | CUBIERTA_CONFIRMADA | CANDIDATA_A_BORRADO_POSTERIOR_CON_RESPALDO | ALTA |
| cab003 | detalle_diferencias | 18 | dbo.Inventarios_DiferenciasDetalle | 10 | 0 | 0 | 10 | 0 | NO_CUBIERTA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| cab003 | cargos_economicos | 5 | dbo.CavaSocios_Cargos | 5 | 0 | 0 | 0 | 5 | SIN_LLAVE_COMPARABLE | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsahub | users_legacy_backup_auth_rbac_20260604 | 1 | dbo.Backup_P5_RBAC_Permisos | 1 | 0 | 0 | 1 | 0 | NO_CUBIERTA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| cab003 | responsabilidad_economica | 5 | dbo.CavaSocios_Movimientos | 5 | 0 | 0 | 0 | 5 | SIN_LLAVE_COMPARABLE | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | sec_perfiles | 5 | dbo.Usuario_Roles | 5 | 0 | 0 | 5 | 0 | NO_CUBIERTA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | sec_metadata | 1 | dbo.Sistema_DeudaTecnica_TablasDuplicadas | 1 | 0 | 0 | 1 | 0 | NO_CUBIERTA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsa_hub | server_connection_status | 1 | dbo.Sistema_ServidoresEstado | 1 | 0 | 0 | 1 | 0 | NO_CUBIERTA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsahub | notification_templates | 11 | dbo.Sistema_NotificacionesConfig | 10 | 0 | 0 | 10 | 0 | NO_CUBIERTA | REQUIERE_MIGRACION_SEMANTICA | BAJA |
| edarsahub | notification_config | 11 | dbo.Sistema_NotificacionesConfig | 10 | 0 | 0 | 10 | 0 | NO_CUBIERTA | REQUIERE_MIGRACION_SEMANTICA | BAJA |

## Criterio

```text
CUBIERTA_CONFIRMADA: toda la muestra encontrada unívocamente en SQL → candidata a borrado (con respaldo), no automático.
CUBIERTA_PARCIAL_NO_CONCLUYENTE: muestra ampliada / revisión manual.
NO_CUBIERTA / SIN_LLAVE_COMPARABLE: no borrar; migración semántica o conservación.
```
