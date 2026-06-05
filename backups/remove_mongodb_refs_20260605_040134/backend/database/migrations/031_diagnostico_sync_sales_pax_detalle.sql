/* ============================================================
   EDARSAHUB - DIAGNÓSTICO Sync_Sales / Sync_PAX_Detalle
   Archivo: 031_diagnostico_sync_sales_pax_detalle.sql

   OBJETIVO:
   - Diagnosticar por qué Sync_Sales y Sync_PAX_Detalle están en 0
   - Validar tablas, columnas, índices
   - Validar unidades, servidores, jobs y logs
   - No insertar ventas
   - No sincronizar
   - No conectar live
   ============================================================ */

SET NOCOUNT ON;

PRINT '============================================================';
PRINT 'DIAGNÓSTICO Sync_Sales / Sync_PAX_Detalle';
PRINT '============================================================';


/* ============================================================
   1. Existencia de tablas
   ============================================================ */

SELECT
    t.TABLE_SCHEMA,
    t.TABLE_NAME,
    t.TABLE_TYPE
FROM INFORMATION_SCHEMA.TABLES t
WHERE t.TABLE_NAME IN (
    'Sync_Sales',
    'Sync_PAX_Detalle',
    'Comercial_KPIs_Diarios_v2',
    'Comercial_Ventas_Dia_Abiertas_v2',
    'Unidades_Negocio',
    'Servidores_Conexiones'
)
ORDER BY t.TABLE_NAME;


/* ============================================================
   2. Columnas de tablas Sync
   ============================================================ */

SELECT
    c.TABLE_NAME,
    c.COLUMN_NAME,
    c.DATA_TYPE,
    c.CHARACTER_MAXIMUM_LENGTH,
    c.IS_NULLABLE,
    c.ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS c
WHERE c.TABLE_NAME IN (
    'Sync_Sales',
    'Sync_PAX_Detalle',
    'Comercial_KPIs_Diarios_v2',
    'Comercial_Ventas_Dia_Abiertas_v2'
)
ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION;


/* ============================================================
   3. Conteos y frescura
   ============================================================ */

SELECT
    'Sync_Sales' AS fuente,
    COUNT(*) AS registros,
    MIN(CAST(FechaHora AS DATE)) AS fecha_minima,
    MAX(CAST(FechaHora AS DATE)) AS fecha_maxima,
    MAX(last_modified) AS ultima_modificacion
FROM dbo.Sync_Sales;

SELECT
    'Sync_PAX_Detalle' AS fuente,
    COUNT(*) AS registros,
    MIN(FechaOperacion) AS fecha_minima,
    MAX(FechaOperacion) AS fecha_maxima,
    MAX(FechaSync) AS ultima_sincronizacion
FROM dbo.Sync_PAX_Detalle;

SELECT
    'Comercial_KPIs_Diarios_v2' AS fuente,
    COUNT(*) AS registros,
    MIN(fecha_operacion) AS fecha_minima,
    MAX(fecha_operacion) AS fecha_maxima,
    MAX(fecha_sincronizacion) AS ultima_sincronizacion
FROM dbo.Comercial_KPIs_Diarios_v2;

SELECT
    'Comercial_Ventas_Dia_Abiertas_v2' AS fuente,
    COUNT(*) AS registros,
    MIN(fecha_operacion) AS fecha_minima,
    MAX(fecha_operacion) AS fecha_maxima,
    MAX(fecha_ultima_actualizacion) AS ultima_actualizacion
FROM dbo.Comercial_Ventas_Dia_Abiertas_v2;


/* ============================================================
   4. Unidades activas y mapeo a servidores
   ============================================================ */

SELECT
    id,
    nombre,
    codigo,
    server_id,
    sucursal_origen_id,
    system_type,
    activo,
    orden,
    created_at,
    updated_at
FROM dbo.Unidades_Negocio
ORDER BY orden, nombre;

SELECT
    id,
    nombre,
    system_type,
    tipo_conexion,
    host,
    port,
    database_name,
    activo,
    visible_en_operaciones,
    visible_en_listado,
    empresa_id,
    EmpresaID,
    fecha_ultima_sincronizacion,
    source_status,
    ultimo_error_sync
FROM dbo.Sistema_VW_Servidores_Conexiones_Publico
ORDER BY nombre;


/* ============================================================
   5. Servidores con posible falta de configuración
   ============================================================ */

SELECT
    id,
    nombre,
    system_type,
    tipo_conexion,
    activo,
    visible_en_operaciones,
    visible_en_listado,
    fecha_ultima_sincronizacion,
    source_status,
    ultimo_error_sync,
    CASE
        WHEN activo = 0 THEN 'INACTIVO'
        WHEN visible_en_operaciones = 0 THEN 'NO_VISIBLE_OPERACIONES'
        WHEN source_status IS NULL THEN 'SIN_STATUS'
        WHEN source_status NOT IN ('OK', 'ACTIVE', 'ACTIVO') THEN 'REVISAR_STATUS'
        ELSE 'OK'
    END AS diagnostico
FROM dbo.Sistema_VW_Servidores_Conexiones_Publico
ORDER BY diagnostico, nombre;


/* ============================================================
   6. Scheduler / Jobs relacionados
   ============================================================ */

SELECT
    TABLE_SCHEMA,
    TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME LIKE '%Scheduler%'
   OR TABLE_NAME LIKE '%Job%'
   OR TABLE_NAME LIKE '%Sync%'
ORDER BY TABLE_NAME;

IF OBJECT_ID('dbo.Sys_Scheduler_Jobs', 'U') IS NOT NULL
BEGIN
    SELECT *
    FROM dbo.Sys_Scheduler_Jobs
    WHERE JobID LIKE '%inteligencia%'
       OR JobName LIKE '%inteligencia%'
       OR JobID LIKE '%sync%'
       OR JobName LIKE '%sync%'
    ORDER BY JobName;
END;

IF OBJECT_ID('dbo.Sistema_Scheduler_Jobs', 'U') IS NOT NULL
BEGIN
    SELECT *
    FROM dbo.Sistema_Scheduler_Jobs
    WHERE JobID LIKE '%inteligencia%'
       OR JobName LIKE '%inteligencia%'
       OR JobID LIKE '%sync%'
       OR JobName LIKE '%sync%'
    ORDER BY JobName;
END;


/* ============================================================
   7. Logs o ejecuciones relacionadas
   ============================================================ */

DECLARE @LogTables TABLE (table_name SYSNAME);

INSERT INTO @LogTables (table_name)
SELECT t.name
FROM sys.tables t
WHERE t.name LIKE '%Log%'
   OR t.name LIKE '%Ejecucion%'
   OR t.name LIKE '%Execution%'
   OR t.name LIKE '%Scheduler%'
   OR t.name LIKE '%Sync%';

SELECT *
FROM @LogTables
ORDER BY table_name;


/* ============================================================
   8. Comparar unidades con datos KPI vs Sync vacío
   ============================================================ */

SELECT
    unidad_negocio_nombre,
    sistema_origen,
    COUNT(*) AS registros_kpi,
    MIN(fecha_operacion) AS fecha_minima,
    MAX(fecha_operacion) AS fecha_maxima,
    MAX(fecha_sincronizacion) AS ultima_sync
FROM dbo.Comercial_KPIs_Diarios_v2
GROUP BY unidad_negocio_nombre, sistema_origen
ORDER BY unidad_negocio_nombre;


/* ============================================================
   9. Validar si Sync_Sales tiene registros por unidad
   ============================================================ */

SELECT
    UnidadNegocio,
    COUNT(*) AS registros,
    MIN(CAST(FechaHora AS DATE)) AS fecha_minima,
    MAX(CAST(FechaHora AS DATE)) AS fecha_maxima,
    MAX(last_modified) AS ultima_modificacion
FROM dbo.Sync_Sales
GROUP BY UnidadNegocio
ORDER BY UnidadNegocio;


/* ============================================================
   10. Validar si Sync_PAX_Detalle tiene registros por sucursal
   ============================================================ */

SELECT
    SucursalNombre,
    COUNT(*) AS registros,
    MIN(FechaOperacion) AS fecha_minima,
    MAX(FechaOperacion) AS fecha_maxima,
    MAX(FechaSync) AS ultima_sync
FROM dbo.Sync_PAX_Detalle
GROUP BY SucursalNombre
ORDER BY SucursalNombre;


/* ============================================================
   11. Diagnóstico ejecutivo
   ============================================================ */

SELECT
    'DIAGNOSTICO_SYNC_SALES_PAX_DETALLE_COMPLETADO' AS resultado,
    SYSDATETIME() AS fecha_ejecucion,
    'Si Sync_Sales o Sync_PAX_Detalle siguen en 0, revisar job, credenciales, logs y mapeo de unidades.' AS siguiente_accion;
