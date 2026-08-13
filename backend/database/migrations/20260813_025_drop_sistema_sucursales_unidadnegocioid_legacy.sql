SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> 'EDARSAHUB'
    THROW 54000, 'Base inesperada.', 1;

IF SUSER_SNAME() <> 'HRLectura'
    THROW 54001, 'Login inesperado.', 1;

IF USER_NAME() <> 'HRLectura'
    THROW 54002, 'Usuario inesperado.', 1;

IF COL_LENGTH(
    'dbo.Sistema_Sucursales',
    'UnidadNegocioID'
) IS NULL
    THROW 54003, 'Columna legacy no existe.', 1;

IF (
    SELECT COUNT(*)
    FROM dbo.Sistema_Sucursales
) <> 5
    THROW 54004, 'Cantidad de sucursales inesperada.', 1;

IF EXISTS (
    SELECT 1
    FROM dbo.Sistema_Sucursales
    WHERE UnidadNegocioID IS NOT NULL
)
    THROW 54005, 'La columna legacy ya contiene datos.', 1;

DECLARE @ColumnId int;

SELECT
    @ColumnId=column_id
FROM sys.columns
WHERE
    object_id=
        OBJECT_ID(
            'dbo.Sistema_Sucursales'
        )
    AND name='UnidadNegocioID';

IF EXISTS (
    SELECT 1
    FROM sys.sql_expression_dependencies
    WHERE
        referenced_id=
            OBJECT_ID(
                'dbo.Sistema_Sucursales'
            )
        AND referenced_minor_id=@ColumnId
)
    THROW 54006, 'Existen dependencias SQL reales sobre la columna legacy.', 1;

IF EXISTS (
    SELECT 1
    FROM sys.foreign_key_columns
    WHERE
        parent_object_id=
            OBJECT_ID(
                'dbo.Sistema_Sucursales'
            )
        AND parent_column_id=@ColumnId
)
    THROW 54007, 'Existe FK sobre columna legacy.', 1;

IF EXISTS (
    SELECT 1
    FROM sys.index_columns
    WHERE
        object_id=
            OBJECT_ID(
                'dbo.Sistema_Sucursales'
            )
        AND column_id=@ColumnId
)
    THROW 54008, 'Existe indice sobre columna legacy.', 1;

BEGIN TRY

    BEGIN TRANSACTION;

    ALTER TABLE dbo.Sistema_Sucursales
        DROP COLUMN UnidadNegocioID;

    IF COL_LENGTH(
        'dbo.Sistema_Sucursales',
        'UnidadNegocioID'
    ) IS NOT NULL
        THROW 54009, 'La columna legacy no fue eliminada.', 1;

    COMMIT TRANSACTION;

    SELECT
        'MIGRATION_025_OK' AS Estado;

END TRY
BEGIN CATCH

    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;

    THROW;

END CATCH;
