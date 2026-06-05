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
