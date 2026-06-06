-- ============================================================================
-- DDL: VISTAS ALIAS PARA TABLAS SYNC LEGACY
-- Fecha: 2026-06-04
-- Propósito: Crear vistas que encapsulan tablas legacy para facilitar migración
-- ============================================================================

-- 1. Consultar estructura actual de tablas Sync legacy
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'dbo'
AND TABLE_NAME IN ('Sync_Inventory', 'Sync_Purchases')
ORDER BY TABLE_NAME, ORDINAL_POSITION;
GO

-- 2. Crear vista alias para Sync_Inventory
CREATE OR ALTER VIEW dbo.Inventario_Sync
AS
SELECT *
FROM dbo.Sync_Inventory;
GO

-- 3. Crear vista alias para Sync_Purchases
CREATE OR ALTER VIEW dbo.Compras_Sync
AS
SELECT *
FROM dbo.Sync_Purchases;
GO

-- 4. Marcar tabla Sync_Inventory como legacy (no eliminar)
IF NOT EXISTS (
    SELECT 1 
    FROM sys.extended_properties ep
    INNER JOIN sys.tables t ON ep.major_id = t.object_id
    WHERE t.name = 'Sync_Inventory'
      AND ep.name = 'EDARSAHUB_Estatus'
)
BEGIN
    EXEC sp_addextendedproperty 
        @name = N'EDARSAHUB_Estatus',
        @value = N'LEGACY_NO_ELIMINAR_USAR_VISTA_dbo.Inventario_Sync',
        @level0type = N'SCHEMA', @level0name = 'dbo',
        @level1type = N'TABLE',  @level1name = 'Sync_Inventory';
END;
GO

-- 5. Marcar tabla Sync_Purchases como legacy (no eliminar)
IF NOT EXISTS (
    SELECT 1 
    FROM sys.extended_properties ep
    INNER JOIN sys.tables t ON ep.major_id = t.object_id
    WHERE t.name = 'Sync_Purchases'
      AND ep.name = 'EDARSAHUB_Estatus'
)
BEGIN
    EXEC sp_addextendedproperty 
        @name = N'EDARSAHUB_Estatus',
        @value = N'LEGACY_NO_ELIMINAR_USAR_VISTA_dbo.Compras_Sync',
        @level0type = N'SCHEMA', @level0name = 'dbo',
        @level1type = N'TABLE',  @level1name = 'Sync_Purchases';
END;
GO

-- 6. Verificar extended properties creadas
SELECT 
    t.name AS TablaLegacy,
    ep.name AS Propiedad,
    ep.value AS Valor
FROM sys.extended_properties ep
INNER JOIN sys.tables t ON ep.major_id = t.object_id
WHERE t.name IN ('Sync_Inventory', 'Sync_Purchases')
  AND ep.name = 'EDARSAHUB_Estatus';
GO

PRINT 'DDL Vistas Sync Legacy ejecutado correctamente';
