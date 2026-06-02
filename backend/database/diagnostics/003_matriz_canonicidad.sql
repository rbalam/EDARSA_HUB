/* ============================================================
   MATRIZ DE CANONICIDAD EDARSAHUB
   Script: 003_matriz_canonicidad.sql
   Modo: diagnostic
   
   Identifica tablas activas, heredadas, sincronizadas y en revisión.
   No modifica datos.
   ============================================================ */

-- 1. MATRIZ DE CANONICIDAD
SELECT
    t.name AS tabla,
    s.name AS esquema,
    SUM(p.rows) AS registros_aproximados,
    CASE
        WHEN t.name LIKE 'Global_Cat_%' THEN 'CANONICA_GLOBAL'
        WHEN t.name LIKE 'RH_%' THEN 'CANONICA_RH'
        WHEN t.name LIKE 'Finanzas_%' THEN 'CANONICA_FINANZAS_PROPUESTA'
        WHEN t.name LIKE 'FIN_%' THEN 'LEGADO_FINANZAS_REVISION'
        WHEN t.name LIKE 'propinas_tpv_%' THEN 'CANONICA_PROPINAS_TPV'
        WHEN t.name LIKE 'Sync_%' THEN 'SINCRONIZADA'
        WHEN t.name LIKE 'Comercial_%' THEN 'CANONICA_COMERCIAL_DERIVADA'
        WHEN t.name LIKE 'Sistema_%' THEN 'CANONICA_SISTEMA'
        WHEN t.name LIKE 'Sys_%' THEN 'SISTEMA_REVISION'
        WHEN t.name IN ('Products', 'Fact_Ventas_Consolidadas', 'Config_Horarios') THEN 'LEGADO_REVISION_NO_USAR_NUEVO'
        ELSE 'SIN_CLASIFICAR'
    END AS clasificacion_sugerida
FROM sys.tables t
INNER JOIN sys.schemas s
    ON t.schema_id = s.schema_id
LEFT JOIN sys.partitions p
    ON t.object_id = p.object_id
    AND p.index_id IN (0, 1)
GROUP BY
    t.name,
    s.name
ORDER BY
    clasificacion_sugerida,
    t.name;
GO

-- 2. VALIDACIÓN FIN_* vs Finanzas_*
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE 
    TABLE_NAME LIKE 'FIN_%'
    OR TABLE_NAME LIKE 'Finanzas_%'
ORDER BY TABLE_NAME, ORDINAL_POSITION;
GO

-- 3. VALIDACIÓN COMERCIAL / SYNC / PRODUCTS
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME IN (
    'Comercial_KPIs_Diarios_v2',
    'Comercial_Ventas_Dia_Abiertas_v2',
    'Sync_Sales',
    'Sync_PAX_Detalle',
    'Sync_Productos',
    'Sync_Productos_Familias',
    'Sync_Productos_SubFamilias',
    'Products',
    'Fact_Ventas_Consolidadas',
    'Config_Horarios'
)
ORDER BY TABLE_NAME, ORDINAL_POSITION;
GO
