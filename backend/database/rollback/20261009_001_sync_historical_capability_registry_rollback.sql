SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Sistema_Sync_Catalogo','U') IS NULL
        THROW 51000, 'SYNC_HISTORICAL_ROLLBACK_MISSING_CATALOG', 1;

    /*
      Rollback conservador:
      si ya existe metadata historica configurada, se niega a borrar columnas.
    */
    IF EXISTS (
        SELECT 1
        FROM dbo.Sistema_Sync_Catalogo
        WHERE CategoriaCodigo IS NOT NULL
           OR EntidadCodigo IS NOT NULL
           OR CampoFecha IS NOT NULL
           OR ClaveNegocio IS NOT NULL
           OR ISNULL(SoportaIncremental,0) <> 0
           OR ISNULL(SoportaFullSync,0) <> 0
           OR ISNULL(SoportaResume,0) <> 0
           OR ISNULL(SoportaSafeStop,0) <> 0
           OR VersionContrato IS NOT NULL
           OR MetadataJSON IS NOT NULL
    )
        THROW 51000, 'SYNC_HISTORICAL_ROLLBACK_REFUSES_CONFIGURED_METADATA', 1;

    IF EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE object_id = OBJECT_ID('dbo.Sistema_Sync_Catalogo')
          AND name = 'IX_Sistema_Sync_Catalogo_HistoricalRegistry'
    )
        DROP INDEX IX_Sistema_Sync_Catalogo_HistoricalRegistry
        ON dbo.Sistema_Sync_Catalogo;

    IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name='CK_Sistema_Sync_Catalogo_ClaveNegocio_JSON')
        ALTER TABLE dbo.Sistema_Sync_Catalogo DROP CONSTRAINT CK_Sistema_Sync_Catalogo_ClaveNegocio_JSON;

    IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name='CK_Sistema_Sync_Catalogo_MetadataJSON_JSON')
        ALTER TABLE dbo.Sistema_Sync_Catalogo DROP CONSTRAINT CK_Sistema_Sync_Catalogo_MetadataJSON_JSON;

    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','MetadataJSON') IS NOT NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo DROP COLUMN MetadataJSON;
    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','VersionContrato') IS NOT NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo DROP COLUMN VersionContrato;
    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','SoportaSafeStop') IS NOT NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo DROP COLUMN SoportaSafeStop;
    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','SoportaResume') IS NOT NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo DROP COLUMN SoportaResume;
    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','SoportaFullSync') IS NOT NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo DROP COLUMN SoportaFullSync;
    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','SoportaIncremental') IS NOT NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo DROP COLUMN SoportaIncremental;
    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','ClaveNegocio') IS NOT NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo DROP COLUMN ClaveNegocio;
    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','CampoFecha') IS NOT NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo DROP COLUMN CampoFecha;
    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','EntidadCodigo') IS NOT NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo DROP COLUMN EntidadCodigo;
    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','CategoriaCodigo') IS NOT NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo DROP COLUMN CategoriaCodigo;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
