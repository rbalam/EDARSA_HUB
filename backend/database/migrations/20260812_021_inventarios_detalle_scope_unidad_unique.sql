SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(
        'dbo.Compras_Inventarios_Fisicos_Detalle_Sync',
        'U'
    ) IS NULL
    BEGIN
        THROW 51000,
            'No existe dbo.Compras_Inventarios_Fisicos_Detalle_Sync',
            1;
    END;

    IF EXISTS (
        SELECT 1
        FROM dbo.Compras_Inventarios_Fisicos_Detalle_Sync
        WHERE server_id IS NULL
           OR LTRIM(RTRIM(server_id)) = ''
           OR unidad_negocio_id IS NULL
           OR LTRIM(RTRIM(unidad_negocio_id)) = ''
           OR folio IS NULL
           OR LTRIM(RTRIM(folio)) = ''
           OR almacen_id IS NULL
           OR LTRIM(RTRIM(almacen_id)) = ''
           OR codigo_producto IS NULL
           OR LTRIM(RTRIM(codigo_producto)) = ''
    )
    BEGIN
        THROW 51001,
            'Existen valores nulos/vacios en la nueva llave de detalle',
            1;
    END;

    IF EXISTS (
        SELECT 1
        FROM dbo.Compras_Inventarios_Fisicos_Detalle_Sync
        GROUP BY
            server_id,
            unidad_negocio_id,
            folio,
            almacen_id,
            codigo_producto
        HAVING COUNT_BIG(*) > 1
    )
    BEGIN
        THROW 51002,
            'Existen duplicados para la nueva llave de detalle',
            1;
    END;

    IF EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE object_id =
              OBJECT_ID(
                  'dbo.Compras_Inventarios_Fisicos_Detalle_Sync'
              )
          AND name =
              'UX_CIFDS_ServerFolioAlmacenProducto'
    )
    BEGIN
        DROP INDEX
            UX_CIFDS_ServerFolioAlmacenProducto
        ON dbo.Compras_Inventarios_Fisicos_Detalle_Sync;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE object_id =
              OBJECT_ID(
                  'dbo.Compras_Inventarios_Fisicos_Detalle_Sync'
              )
          AND name =
              'UX_CIFDS_ServerUnidadFolioAlmacenProducto'
    )
    BEGIN
        CREATE UNIQUE NONCLUSTERED INDEX
            UX_CIFDS_ServerUnidadFolioAlmacenProducto
        ON dbo.Compras_Inventarios_Fisicos_Detalle_Sync
        (
            server_id,
            unidad_negocio_id,
            folio,
            almacen_id,
            codigo_producto
        );
    END;

    DECLARE @columnas nvarchar(max);

    SELECT
        @columnas =
            STUFF((
                SELECT
                    ',' + c.name
                FROM sys.indexes i
                INNER JOIN sys.index_columns ic
                    ON ic.object_id = i.object_id
                   AND ic.index_id = i.index_id
                INNER JOIN sys.columns c
                    ON c.object_id = ic.object_id
                   AND c.column_id = ic.column_id
                WHERE i.object_id =
                      OBJECT_ID(
                          'dbo.Compras_Inventarios_Fisicos_Detalle_Sync'
                      )
                  AND i.name =
                      'UX_CIFDS_ServerUnidadFolioAlmacenProducto'
                  AND ic.is_included_column = 0
                ORDER BY ic.key_ordinal
                FOR XML PATH(''), TYPE
            ).value('.', 'nvarchar(max)'), 1, 1, '');

    IF ISNULL(@columnas, '') <>
       'server_id,unidad_negocio_id,folio,almacen_id,codigo_producto'
    BEGIN
        THROW 51003,
            'La llave UNIQUE nueva no tiene las columnas esperadas',
            1;
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
