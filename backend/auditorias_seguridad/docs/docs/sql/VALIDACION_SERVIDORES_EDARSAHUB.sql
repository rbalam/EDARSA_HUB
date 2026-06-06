-- =============================================================================
-- SCRIPT DE VALIDACIÓN DE SERVIDORES EN EDARSAHUB
-- =============================================================================
-- Archivo: VALIDACION_SERVIDORES_EDARSAHUB.sql
-- Fecha: 2025-12-19
-- Propósito: Verificar estado del catálogo maestro de servidores
-- Uso: SOLO LECTURA - No modifica datos
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. RESUMEN GENERAL DEL CATÁLOGO
-- -----------------------------------------------------------------------------
PRINT '=== RESUMEN GENERAL DEL CATÁLOGO DE SERVIDORES ===';

SELECT 
    COUNT(*) AS total_servidores,
    SUM(CASE WHEN activo = 1 THEN 1 ELSE 0 END) AS activos,
    SUM(CASE WHEN activo = 0 OR activo IS NULL THEN 1 ELSE 0 END) AS inactivos,
    SUM(CASE WHEN password_encrypted IS NOT NULL AND password_encrypted != '' THEN 1 ELSE 0 END) AS con_password,
    SUM(CASE WHEN queries_configured = 1 THEN 1 ELSE 0 END) AS con_queries,
    SUM(CASE WHEN sucursales IS NOT NULL AND sucursales != '' AND sucursales != '[]' THEN 1 ELSE 0 END) AS con_sucursales
FROM Servidores_Conexiones;

-- -----------------------------------------------------------------------------
-- 2. DETALLE DE SERVIDORES ACTIVOS
-- -----------------------------------------------------------------------------
PRINT '';
PRINT '=== SERVIDORES ACTIVOS ===';

SELECT 
    id,
    nombre,
    system_type,
    tipo_conexion,
    host,
    port,
    database_name,
    username,
    CASE WHEN password_encrypted IS NOT NULL AND password_encrypted != '' THEN 'Sí' ELSE 'No' END AS tiene_password,
    visible_en_listado,
    visible_en_operaciones
FROM Servidores_Conexiones
WHERE activo = 1
ORDER BY nombre;

-- -----------------------------------------------------------------------------
-- 3. SERVIDORES INACTIVOS (incluyendo TEST)
-- -----------------------------------------------------------------------------
PRINT '';
PRINT '=== SERVIDORES INACTIVOS ===';

SELECT 
    id,
    nombre,
    system_type,
    CASE 
        WHEN nombre LIKE 'TEST%' THEN 'Servidor de pruebas'
        WHEN nombre = 'EDARSA HUB' AND system_type = 'Otro' THEN 'Duplicado legacy'
        ELSE 'Inactivo'
    END AS clasificacion
FROM Servidores_Conexiones
WHERE activo = 0 OR activo IS NULL
ORDER BY nombre;

-- -----------------------------------------------------------------------------
-- 4. IDENTIFICAR DUPLICADOS POR HOST + DATABASE
-- -----------------------------------------------------------------------------
PRINT '';
PRINT '=== POSIBLES DUPLICADOS (mismo host + database) ===';

SELECT 
    host,
    database_name,
    COUNT(*) AS cantidad,
    STRING_AGG(nombre, ', ') AS servidores
FROM Servidores_Conexiones
WHERE activo = 1
GROUP BY host, database_name
HAVING COUNT(*) > 1;

-- -----------------------------------------------------------------------------
-- 5. SERVIDORES CON CAMPOS CRÍTICOS FALTANTES
-- -----------------------------------------------------------------------------
PRINT '';
PRINT '=== SERVIDORES CON CAMPOS CRÍTICOS FALTANTES ===';

SELECT 
    id,
    nombre,
    CASE WHEN host IS NULL OR host = '' THEN 'FALTA' ELSE 'OK' END AS host_status,
    CASE WHEN database_name IS NULL OR database_name = '' THEN 'FALTA' ELSE 'OK' END AS database_status,
    CASE WHEN username IS NULL OR username = '' THEN 'FALTA' ELSE 'OK' END AS username_status,
    CASE WHEN password_encrypted IS NULL OR password_encrypted = '' THEN 'FALTA' ELSE 'OK' END AS password_status
FROM Servidores_Conexiones
WHERE activo = 1
  AND (host IS NULL OR host = '' 
       OR database_name IS NULL OR database_name = ''
       OR username IS NULL OR username = ''
       OR password_encrypted IS NULL OR password_encrypted = '');

-- Si no hay resultados, mostrar mensaje
IF @@ROWCOUNT = 0
    PRINT 'Ningún servidor activo tiene campos críticos faltantes.';

-- -----------------------------------------------------------------------------
-- 6. DISTRIBUCIÓN POR SYSTEM_TYPE
-- -----------------------------------------------------------------------------
PRINT '';
PRINT '=== DISTRIBUCIÓN POR SYSTEM_TYPE ===';

SELECT 
    system_type,
    COUNT(*) AS cantidad,
    SUM(CASE WHEN activo = 1 THEN 1 ELSE 0 END) AS activos,
    SUM(CASE WHEN activo = 0 OR activo IS NULL THEN 1 ELSE 0 END) AS inactivos
FROM Servidores_Conexiones
GROUP BY system_type
ORDER BY cantidad DESC;

-- -----------------------------------------------------------------------------
-- 7. VERIFICAR CONSISTENCIA DE mongodb_id
-- -----------------------------------------------------------------------------
PRINT '';
PRINT '=== VERIFICACIÓN DE mongodb_id ===';

SELECT 
    COUNT(*) AS total,
    SUM(CASE WHEN mongodb_id IS NOT NULL AND mongodb_id = CAST(id AS VARCHAR(50)) THEN 1 ELSE 0 END) AS id_coincide_mongodb_id,
    SUM(CASE WHEN mongodb_id IS NULL OR mongodb_id = '' THEN 1 ELSE 0 END) AS sin_mongodb_id,
    SUM(CASE WHEN mongodb_id IS NOT NULL AND mongodb_id != CAST(id AS VARCHAR(50)) THEN 1 ELSE 0 END) AS id_diferente_mongodb_id
FROM Servidores_Conexiones;

-- -----------------------------------------------------------------------------
-- 8. SERVIDORES CREADOS/ACTUALIZADOS RECIENTEMENTE
-- -----------------------------------------------------------------------------
PRINT '';
PRINT '=== SERVIDORES ACTUALIZADOS EN ÚLTIMOS 30 DÍAS ===';

SELECT 
    id,
    nombre,
    created_at,
    updated_at
FROM Servidores_Conexiones
WHERE updated_at >= DATEADD(day, -30, GETDATE())
   OR created_at >= DATEADD(day, -30, GETDATE())
ORDER BY COALESCE(updated_at, created_at) DESC;

-- -----------------------------------------------------------------------------
-- 9. VERIFICAR SERVIDORES DEL LOTE 3 (MENCIONADOS EN DOCUMENTACIÓN)
-- -----------------------------------------------------------------------------
PRINT '';
PRINT '=== VERIFICACIÓN DE SERVIDORES MENCIONADOS EN LOTE 3 ===';

SELECT 
    id,
    nombre,
    system_type,
    host,
    port,
    database_name,
    username,
    CASE WHEN password_encrypted IS NOT NULL THEN 'CONFIGURADO' ELSE 'NO CONFIGURADO' END AS password_status,
    activo,
    'EXISTE EN EDARSAHUB' AS estado
FROM Servidores_Conexiones
WHERE id IN (
    'a5547321-1139-4d2b-9d53-182ca737b6b6',  -- 130° MERIDA
    'b5175237-5e57-41f3-ab6d-b5ae2f5e780b'   -- HR2020 ESCRITURA
);

-- -----------------------------------------------------------------------------
-- FIN DEL SCRIPT DE VALIDACIÓN
-- -----------------------------------------------------------------------------
PRINT '';
PRINT '=== VALIDACIÓN COMPLETADA ===';
