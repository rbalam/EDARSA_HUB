# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T16:16:33.783336
- Modo: `diagnostic`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/app/backend/database/diagnostics/014_diagnostico_tablas_rbac_usuario.sql`

## Resultado
ERROR

## Detalle
```text
Falta variable de entorno requerida: EDARSAHUB_SQL_SERVER
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