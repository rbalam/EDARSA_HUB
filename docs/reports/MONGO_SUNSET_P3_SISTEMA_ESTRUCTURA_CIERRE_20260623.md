# EDARSAHUB – Mongo Sunset / SQL-First
## Cierre P3 Sistema Estructura – 23-Jun-2026

## Estado validado

- `backend/modules/sistema/estructura_service.py` quedó sin runtime Mongo operativo.
- Validación:
  - `python3 -m py_compile backend/modules/sistema/estructura_service.py` = OK.
  - Runtime Mongo en archivo = 0.

## Migraciones realizadas

- `sec_empresas` → `dbo.Sistema_Empresas`
- `sec_unidades_negocio` → `dbo.Unidades_Negocio`
- `sec_sucursales` → `dbo.Sistema_Sucursales`
- `sec_mapeo_servidor_sucursal` → `dbo.Sistema_SucursalServidorMapeo`
- `sec_permisos_catalogo` → `dbo.Usuario_PermisosRolModulo` + `dbo.Usuario_Modulos` + `dbo.Usuario_Acciones` + `dbo.Usuario_Roles`
- `sec_bitacora_acceso` → `dbo.Usuario_LogAccesos`

## Pendiente técnico

- Revisar si la relación Empresa → Unidad debe refinarse con tabla canónica específica. Actualmente se conserva respuesta compatible y se evita Mongo.

## Reglas conservadas

- Sin tablas nuevas.
- SQL Server como fuente operativa.
- Cambios quirúrgicos.
- Backup local fuera de Git.
