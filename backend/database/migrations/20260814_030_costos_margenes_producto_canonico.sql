SET XACT_ABORT ON;
SET NOCOUNT ON;

IF OBJECT_ID(
    'dbo.Comercial_AlertasMargenReglas',
    'U'
) IS NULL
    THROW 51000,
        'Comercial_AlertasMargenReglas no existe',
        1;

IF OBJECT_ID(
    'dbo.Producto_Catalogo',
    'U'
) IS NULL
    THROW 51001,
        'Producto_Catalogo no existe',
        1;

IF COL_LENGTH(
    'dbo.Comercial_AlertasMargenReglas',
    'ProductoID'
) IS NULL
BEGIN
    ALTER TABLE dbo.Comercial_AlertasMargenReglas
    ADD ProductoID int NULL;
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.foreign_keys
    WHERE
        parent_object_id =
            OBJECT_ID(
                'dbo.Comercial_AlertasMargenReglas'
            )
        AND name =
            'FK_Comercial_AlertasMargenReglas_Producto'
)
BEGIN
    ALTER TABLE dbo.Comercial_AlertasMargenReglas
    WITH CHECK
    ADD CONSTRAINT
        FK_Comercial_AlertasMargenReglas_Producto
    FOREIGN KEY (ProductoID)
    REFERENCES dbo.Producto_Catalogo (ProductoID);

    ALTER TABLE dbo.Comercial_AlertasMargenReglas
    CHECK CONSTRAINT
        FK_Comercial_AlertasMargenReglas_Producto;
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE
        object_id =
            OBJECT_ID(
                'dbo.Comercial_AlertasMargenReglas'
            )
        AND name =
            'IX_AlertasMargenReglas_ProductoID'
)
BEGIN
    CREATE INDEX
        IX_AlertasMargenReglas_ProductoID
    ON dbo.Comercial_AlertasMargenReglas (
        ProductoID
    )
    WHERE
        NivelAplicacion = 'PRODUCTO'
        AND ProductoID IS NOT NULL;
END;
GO
