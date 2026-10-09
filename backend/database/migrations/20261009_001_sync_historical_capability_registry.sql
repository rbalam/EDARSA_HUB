SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Sistema_Sync_Catalogo','U') IS NULL
        THROW 51000, 'SYNC_HISTORICAL_MISSING_Sistema_Sync_Catalogo', 1;

    IF OBJECT_ID('dbo.Sistema_Sync_Capacidades','U') IS NULL
        THROW 51000, 'SYNC_HISTORICAL_MISSING_Sistema_Sync_Capacidades', 1;

    /*
      Fase 2 - Capability Registry historico.

      REUSE:
      - Codigo              -> capability/table key
      - Nombre              -> display_name
      - Grupo               -> category_name
      - Handler             -> handler
      - TablaDestino        -> destination table
      - PermiteResync       -> supports_historical
      - Dependencias        -> dependencies
      - Orden               -> execution_order
      - Activo              -> enabled

      EXTEND solo lo que no tenia equivalente canonico.
      Defaults fail-closed: ninguna capacidad adicional queda habilitada por inferencia.
    */

    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','CategoriaCodigo') IS NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo ADD CategoriaCodigo nvarchar(100) NULL;

    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','EntidadCodigo') IS NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo ADD EntidadCodigo nvarchar(100) NULL;

    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','CampoFecha') IS NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo ADD CampoFecha nvarchar(200) NULL;

    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','ClaveNegocio') IS NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo ADD ClaveNegocio nvarchar(max) NULL;

    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','SoportaIncremental') IS NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo
        ADD SoportaIncremental bit NOT NULL
            CONSTRAINT DF_Sistema_Sync_Catalogo_SoportaIncremental DEFAULT (0);

    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','SoportaFullSync') IS NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo
        ADD SoportaFullSync bit NOT NULL
            CONSTRAINT DF_Sistema_Sync_Catalogo_SoportaFullSync DEFAULT (0);

    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','SoportaResume') IS NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo
        ADD SoportaResume bit NOT NULL
            CONSTRAINT DF_Sistema_Sync_Catalogo_SoportaResume DEFAULT (0);

    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','SoportaSafeStop') IS NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo
        ADD SoportaSafeStop bit NOT NULL
            CONSTRAINT DF_Sistema_Sync_Catalogo_SoportaSafeStop DEFAULT (0);

    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','VersionContrato') IS NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo ADD VersionContrato nvarchar(50) NULL;

    IF COL_LENGTH('dbo.Sistema_Sync_Catalogo','MetadataJSON') IS NULL
        ALTER TABLE dbo.Sistema_Sync_Catalogo ADD MetadataJSON nvarchar(max) NULL;

    IF NOT EXISTS (
        SELECT 1 FROM sys.check_constraints
        WHERE name = 'CK_Sistema_Sync_Catalogo_ClaveNegocio_JSON'
    )
        ALTER TABLE dbo.Sistema_Sync_Catalogo
        ADD CONSTRAINT CK_Sistema_Sync_Catalogo_ClaveNegocio_JSON
        CHECK (ClaveNegocio IS NULL OR ISJSON(ClaveNegocio) = 1);

    IF NOT EXISTS (
        SELECT 1 FROM sys.check_constraints
        WHERE name = 'CK_Sistema_Sync_Catalogo_MetadataJSON_JSON'
    )
        ALTER TABLE dbo.Sistema_Sync_Catalogo
        ADD CONSTRAINT CK_Sistema_Sync_Catalogo_MetadataJSON_JSON
        CHECK (MetadataJSON IS NULL OR ISJSON(MetadataJSON) = 1);

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE object_id = OBJECT_ID('dbo.Sistema_Sync_Catalogo')
          AND name = 'IX_Sistema_Sync_Catalogo_HistoricalRegistry'
    )
        CREATE INDEX IX_Sistema_Sync_Catalogo_HistoricalRegistry
        ON dbo.Sistema_Sync_Catalogo (Activo, PermiteResync, CategoriaCodigo, Orden)
        INCLUDE (Codigo, Handler, HandlerImplementado, TablaDestino);

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
