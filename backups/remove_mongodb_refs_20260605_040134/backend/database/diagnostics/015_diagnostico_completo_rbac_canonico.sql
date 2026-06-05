/* ============================================================
   DIAGNÓSTICO COMPLETO TABLAS RBAC CANONICO (Usuario_*)
   Verifica existencia de tablas, estructura y datos existentes.
   No modifica datos.
   ============================================================ */

-- 1. Verificar qué tablas Usuario_* existen
SELECT 
    'TABLAS_EXISTENTES' AS diagnostico,
    TABLE_SCHEMA AS esquema,
    TABLE_NAME AS tabla,
    TABLE_TYPE AS tipo
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME LIKE 'Usuario_%'
ORDER BY TABLE_NAME;

-- 2. Verificar qué tablas Sistema_RBAC_* existen (transicionales)
SELECT 
    'TABLAS_TRANSICIONALES' AS diagnostico,
    TABLE_SCHEMA AS esquema,
    TABLE_NAME AS tabla,
    TABLE_TYPE AS tipo
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME LIKE 'Sistema_RBAC_%'
ORDER BY TABLE_NAME;

-- 3. Estructura detallada de Usuario_Modulos (si existe)
SELECT
    'Usuario_Modulos' AS tabla,
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Usuario_Modulos'
ORDER BY ORDINAL_POSITION;

-- 4. Estructura detallada de Usuario_Roles (si existe)
SELECT
    'Usuario_Roles' AS tabla,
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Usuario_Roles'
ORDER BY ORDINAL_POSITION;

-- 5. Estructura detallada de Usuario_Acciones (si existe)
SELECT
    'Usuario_Acciones' AS tabla,
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Usuario_Acciones'
ORDER BY ORDINAL_POSITION;

-- 6. Datos existentes en Usuario_Modulos
SELECT TOP 50 * FROM Usuario_Modulos;

-- 7. Datos existentes en Usuario_Roles
SELECT TOP 50 * FROM Usuario_Roles;

-- 8. Datos existentes en Usuario_Acciones
SELECT TOP 50 * FROM Usuario_Acciones;

-- 9. Datos existentes en Usuario_PermisosRolModulo
SELECT TOP 50 * FROM Usuario_PermisosRolModulo;
