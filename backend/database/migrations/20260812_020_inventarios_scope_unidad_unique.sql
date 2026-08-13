SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(
        'dbo.Compras_Inventarios_Fisicos_Sync',
        'U'
    ) IS NULL
    BEGIN
        THROW 51000,
            'Tabla dbo.Compras_Inventarios_Fisicos_Sync no existe',
            1;
    END;

    IF EXISTS (
        SELECT 1
        FROM dbo.Compras_Inventarios_Fisicos_Sync
        WHERE server_id IS NULL
           OR LTRIM(RTRIM(server_id)) = ''
           OR unidad_negocio_id IS NULL
           OR LTRIM(RTRIM(unidad_negocio_id)) = ''
           OR folio IS NULL
           OR LTRIM(RTRIM(folio)) = ''
    )
    BEGIN
        THROW 51001,
            'Existen llaves nulas o vacias en inventarios fisicos',
            1;
    END;

    IF EXISTS (
        SELECT 1
        FROM dbo.Compras_Inventarios_Fisicos_Sync
        GROUP BY
            server_id,
            unidad_negocio_id,
            folio
        HAVING COUNT(*) > 1
    )
    BEGIN
        THROW 51002,
            'Existen duplicados para server_id + unidad_negocio_id + folio',
            1;
    END;

    IF EXISTS (
        SELECT 1
        FROM sys.key_constraints
        WHERE parent_object_id =
              OBJECT_ID('dbo.Compras_Inventarios_Fisicos_Sync')
          AND name = 'UQ_InvFisico_Folio_Server'
    )
    BEGIN
        ALTER TABLE dbo.Compras_Inventarios_Fisicos_Sync
        DROP CONSTRAINT UQ_InvFisico_Folio_Server;
    END
    ELSE IF EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE object_id =
              OBJECT_ID('dbo.Compras_Inventarios_Fisicos_Sync')
          AND name = 'UQ_InvFisico_Folio_Server'
    )
    BEGIN
        DROP INDEX UQ_InvFisico_Folio_Server
        ON dbo.Compras_Inventarios_Fisicos_Sync;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE object_id =
              OBJECT_ID('dbo.Compras_Inventarios_Fisicos_Sync')
          AND name = 'UQ_InvFisico_ServerUnidadFolio'
    )
    BEGIN
        CREATE UNIQUE NONCLUSTERED INDEX
            UQ_InvFisico_ServerUnidadFolio
        ON dbo.Compras_Inventarios_Fisicos_Sync
        (
            server_id,
            unidad_negocio_id,
            folio
        );
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes i
        INNER JOIN sys.index_columns ic
            ON ic.object_id = i.object_id
           AND ic.index_id = i.index_id
        INNER JOIN sys.columns c
            ON c.object_id = ic.object_id
           AND c.column_id = ic.column_id
        WHERE i.object_id =
              OBJECT_ID('dbo.Compras_Inventarios_Fisicos_Sync')
          AND i.name = 'UQ_InvFisico_ServerUnidadFolio'
          AND i.is_unique = 1
        GROUP BY
            i.object_id,
            i.index_id
        HAVING
            COUNT(*) = 3
            AND MAX(
                CASE
                    WHEN ic.key_ordinal = 1
                     AND c.name = 'server_id'
                    THEN 1 ELSE 0
                END
            ) = 1
            AND MAX(
                CASE
                    WHEN ic.key_ordinal = 2
                     AND c.name = 'unidad_negocio_id'
                    THEN 1 ELSE 0
                END
            ) = 1
            AND MAX(
                CASE
                    WHEN ic.key_ordinal = 3
                     AND c.name = 'folio'
                    THEN 1 ELSE 0
                END
            ) = 1
    )
    BEGIN
        THROW 51003,
            'Indice nuevo no coincide con contrato esperado',
            1;
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
