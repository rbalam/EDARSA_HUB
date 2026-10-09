SET NOCOUNT ON;

IF DB_NAME() <> 'EDARSAHUB'
    THROW 51000, 'SYNC_HISTORICAL_VALIDATION_WRONG_DATABASE', 1;

IF OBJECT_ID('dbo.Sistema_Sync_Catalogo','U') IS NULL
    THROW 51000, 'SYNC_HISTORICAL_VALIDATION_MISSING_CATALOG', 1;

IF OBJECT_ID('dbo.Sistema_Sync_Capacidades','U') IS NULL
    THROW 51000, 'SYNC_HISTORICAL_VALIDATION_MISSING_BRIDGE', 1;

DECLARE @required TABLE (ColumnName sysname NOT NULL);
INSERT INTO @required (ColumnName) VALUES
('CategoriaCodigo'),
('EntidadCodigo'),
('CampoFecha'),
('ClaveNegocio'),
('SoportaIncremental'),
('SoportaFullSync'),
('SoportaResume'),
('SoportaSafeStop'),
('VersionContrato'),
('MetadataJSON');

IF EXISTS (
    SELECT 1
    FROM @required r
    WHERE COL_LENGTH('dbo.Sistema_Sync_Catalogo', r.ColumnName) IS NULL
)
    THROW 51000, 'SYNC_HISTORICAL_VALIDATION_COLUMNS_MISSING', 1;

IF EXISTS (
    SELECT 1
    FROM dbo.Sistema_Sync_Catalogo
    WHERE ClaveNegocio IS NOT NULL
      AND ISJSON(ClaveNegocio) <> 1
)
    THROW 51000, 'SYNC_HISTORICAL_VALIDATION_INVALID_BUSINESS_KEY_JSON', 1;

IF EXISTS (
    SELECT 1
    FROM dbo.Sistema_Sync_Catalogo
    WHERE MetadataJSON IS NOT NULL
      AND ISJSON(MetadataJSON) <> 1
)
    THROW 51000, 'SYNC_HISTORICAL_VALIDATION_INVALID_METADATA_JSON', 1;

SELECT
    COUNT_BIG(*) AS CatalogRows,
    SUM(CASE WHEN ISNULL(Activo,0)=1 THEN 1 ELSE 0 END) AS ActiveRows,
    SUM(CASE WHEN ISNULL(PermiteResync,0)=1 THEN 1 ELSE 0 END) AS HistoricalRows,
    SUM(CASE WHEN CategoriaCodigo IS NOT NULL THEN 1 ELSE 0 END) AS RowsWithCategoryKey,
    SUM(CASE WHEN EntidadCodigo IS NOT NULL THEN 1 ELSE 0 END) AS RowsWithEntityKey,
    SUM(CASE WHEN ClaveNegocio IS NOT NULL THEN 1 ELSE 0 END) AS RowsWithBusinessKey
FROM dbo.Sistema_Sync_Catalogo;

SELECT
    COUNT_BIG(*) AS ExplicitSystemCapabilityLinks
FROM dbo.Sistema_Sync_Capacidades;
