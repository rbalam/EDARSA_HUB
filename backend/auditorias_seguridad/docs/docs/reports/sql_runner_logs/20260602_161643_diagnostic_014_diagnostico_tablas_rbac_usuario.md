# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T16:16:43.700985
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/diagnostics/014_diagnostico_tablas_rbac_usuario.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecución completada.

### Batch 1
- Tipo: SELECT
- Columnas: tabla, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, ORDINAL_POSITION
- Filas: 14
- Preview (primeras 20 filas):
```
  {'tabla': 'Usuario_PermisosRolModulo', 'COLUMN_NAME': 'PermisoRolModuloID', 'DATA_TYPE': 'bigint', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 1}
  {'tabla': 'Usuario_PermisosRolModulo', 'COLUMN_NAME': 'RolID', 'DATA_TYPE': 'int', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 2}
  {'tabla': 'Usuario_PermisosRolModulo', 'COLUMN_NAME': 'ModuloID', 'DATA_TYPE': 'int', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 3}
  {'tabla': 'Usuario_PermisosRolModulo', 'COLUMN_NAME': 'AccionID', 'DATA_TYPE': 'smallint', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 4}
  {'tabla': 'Usuario_PermisosRolModulo', 'COLUMN_NAME': 'Permitido', 'DATA_TYPE': 'bit', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 5}
  {'tabla': 'Usuario_PermisosRolModulo', 'COLUMN_NAME': 'RestriccionPropietario', 'DATA_TYPE': 'bit', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 6}
  {'tabla': 'Usuario_PermisosRolModulo', 'COLUMN_NAME': 'RestriccionSucursal', 'DATA_TYPE': 'bit', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 7}
  {'tabla': 'Usuario_PermisosRolModulo', 'COLUMN_NAME': 'RequiereAutorizacion', 'DATA_TYPE': 'bit', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 8}
  {'tabla': 'Usuario_PermisosRolModulo', 'COLUMN_NAME': 'NivelAutorizacionRequerido', 'DATA_TYPE': 'smallint', 'IS_NULLABLE': 'YES', 'ORDINAL_POSITION': 9}
  {'tabla': 'Usuario_PermisosRolModulo', 'COLUMN_NAME': 'Activo', 'DATA_TYPE': 'bit', 'IS_NULLABLE': 'NO', 'ORDINAL_POSITION': 10}
```


## SQL ejecutado / revisado
```sql
/* ============================================================
   DIAGNÓSTICO PARA ASIGNAR PERMISOS EN Usuario_PermisosRolModulo
   No modifica datos.
   ============================================================ */

SELECT
    'Usuario_PermisosRolModulo' AS tabla,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Usuario_PermisosRolModulo'
ORDER BY ORDINAL_POSITION;

SELECT
    'Usuario_Roles' AS tabla,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Usuario_Roles'
ORDER BY ORDINAL_POSITION;

SELECT
    'Usuario_Acciones' AS tabla,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Usuario_Acciones'
ORDER BY ORDINAL_POSITION;

SELECT
    'Usuario_Modulos' AS tabla,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Usuario_Modulos'
ORDER BY ORDINAL_POSITION;

```