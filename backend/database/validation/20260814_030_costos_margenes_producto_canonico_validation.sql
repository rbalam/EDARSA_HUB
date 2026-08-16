SET NOCOUNT ON;

IF OBJECT_ID(
    'dbo.Comercial_AlertasMargenReglas',
    'U'
) IS NULL
    THROW 51010,
        'Comercial_AlertasMargenReglas no existe',
        1;

IF COL_LENGTH(
    'dbo.Comercial_AlertasMargenReglas',
    'ProductoID'
) IS NULL
    THROW 51011,
        'ProductoID canonico no existe',
        1;

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns c
    WHERE
        c.object_id =
            OBJECT_ID(
                'dbo.Comercial_AlertasMargenReglas'
            )
        AND c.name = 'ProductoID'
        AND TYPE_NAME(c.user_type_id) = 'int'
        AND c.is_nullable = 1
)
    THROW 51012,
        'ProductoID no cumple contrato int NULL',
        1;

IF NOT EXISTS (
    SELECT 1
    FROM sys.foreign_keys fk
    JOIN sys.foreign_key_columns fkc
        ON fkc.constraint_object_id = fk.object_id
    JOIN sys.columns pc
        ON pc.object_id = fkc.parent_object_id
       AND pc.column_id = fkc.parent_column_id
    JOIN sys.columns rc
        ON rc.object_id = fkc.referenced_object_id
       AND rc.column_id = fkc.referenced_column_id
    WHERE
        fk.parent_object_id =
            OBJECT_ID(
                'dbo.Comercial_AlertasMargenReglas'
            )
        AND fk.referenced_object_id =
            OBJECT_ID(
                'dbo.Producto_Catalogo'
            )
        AND pc.name = 'ProductoID'
        AND rc.name = 'ProductoID'
        AND fk.is_disabled = 0
        AND fk.is_not_trusted = 0
)
    THROW 51013,
        'FK ProductoID -> Producto_Catalogo no valida',
        1;

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
        AND has_filter = 1
)
    THROW 51014,
        'Indice ProductoID no existe',
        1;

SELECT
    c.name AS columna,
    TYPE_NAME(c.user_type_id) AS tipo,
    c.is_nullable
FROM sys.columns c
WHERE
    c.object_id =
        OBJECT_ID(
            'dbo.Comercial_AlertasMargenReglas'
        )
    AND c.name IN (
        'ProductoID',
        'ProductoClave'
    )
ORDER BY c.column_id;
