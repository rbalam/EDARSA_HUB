SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> 'EDARSAHUB'
    THROW 54100, 'Base inesperada.', 1;

IF COL_LENGTH(
    'dbo.Sistema_Sucursales',
    'UnidadNegocioID'
) IS NOT NULL
    THROW 54101, 'La columna ya existe.', 1;

ALTER TABLE dbo.Sistema_Sucursales
ADD UnidadNegocioID int NULL;

SELECT
    'ROLLBACK_025_OK' AS Estado;
