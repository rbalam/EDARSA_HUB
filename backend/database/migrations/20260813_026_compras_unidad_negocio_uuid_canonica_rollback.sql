SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE
            object_id=OBJECT_ID(
                'dbo.Compras_Recepciones'
            )
            AND name='IX_Compras_Recepciones_UnidadNegocio'
    )
        DROP INDEX IX_Compras_Recepciones_UnidadNegocio
        ON dbo.Compras_Recepciones;

    IF EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE
            object_id=OBJECT_ID(
                'dbo.Compras_Ordenes'
            )
            AND name='IX_Compras_Ordenes_UnidadNegocio'
    )
        DROP INDEX IX_Compras_Ordenes_UnidadNegocio
        ON dbo.Compras_Ordenes;

    IF EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE
            object_id=OBJECT_ID(
                'dbo.Compras_Pedidos'
            )
            AND name='IX_Compras_Pedidos_UnidadNegocio'
    )
        DROP INDEX IX_Compras_Pedidos_UnidadNegocio
        ON dbo.Compras_Pedidos;

    IF EXISTS (
        SELECT 1
        FROM sys.foreign_keys
        WHERE name='FK_Compras_Recepciones_UnidadNegocio'
    )
        ALTER TABLE dbo.Compras_Recepciones
        DROP CONSTRAINT FK_Compras_Recepciones_UnidadNegocio;

    IF EXISTS (
        SELECT 1
        FROM sys.foreign_keys
        WHERE name='FK_Compras_Ordenes_UnidadNegocio'
    )
        ALTER TABLE dbo.Compras_Ordenes
        DROP CONSTRAINT FK_Compras_Ordenes_UnidadNegocio;

    IF EXISTS (
        SELECT 1
        FROM sys.foreign_keys
        WHERE name='FK_Compras_Pedidos_UnidadNegocio'
    )
        ALTER TABLE dbo.Compras_Pedidos
        DROP CONSTRAINT FK_Compras_Pedidos_UnidadNegocio;

    IF COL_LENGTH(
        'dbo.Compras_Recepciones',
        'unidad_negocio_pk'
    ) IS NOT NULL
        ALTER TABLE dbo.Compras_Recepciones
        DROP COLUMN unidad_negocio_pk;

    IF COL_LENGTH(
        'dbo.Compras_Ordenes',
        'unidad_negocio_pk'
    ) IS NOT NULL
        ALTER TABLE dbo.Compras_Ordenes
        DROP COLUMN unidad_negocio_pk;

    IF COL_LENGTH(
        'dbo.Compras_Pedidos',
        'unidad_negocio_pk'
    ) IS NOT NULL
        ALTER TABLE dbo.Compras_Pedidos
        DROP COLUMN unidad_negocio_pk;

    COMMIT TRANSACTION;

    SELECT
        'ROLLBACK_026_OK' AS Estado;

END TRY
BEGIN CATCH

    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;

    THROW;

END CATCH;
