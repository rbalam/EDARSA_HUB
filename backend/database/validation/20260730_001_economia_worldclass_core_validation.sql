SET NOCOUNT ON;

DECLARE @Errors int = 0;

DECLARE @RequiredTables TABLE
(
    TableName sysname NOT NULL
);

INSERT INTO @RequiredTables(TableName)
VALUES
('Economia_Paises'),
('Economia_Proveedores'),
('Economia_CategoriasIndicador'),
('Economia_Series'),
('Economia_Valores'),
('Economia_ContextoOperativo');

SELECT
    rt.TableName,
    CASE
        WHEN OBJECT_ID('dbo.' + rt.TableName, 'U') IS NOT NULL
        THEN 'PASS'
        ELSE 'FAIL'
    END AS Estado
FROM @RequiredTables rt;

SELECT @Errors = @Errors + COUNT(*)
FROM @RequiredTables rt
WHERE OBJECT_ID('dbo.' + rt.TableName, 'U') IS NULL;

IF OBJECT_ID('dbo.Economia_Valores', 'U') IS NOT NULL
BEGIN
    IF NOT EXISTS
    (
        SELECT 1
        FROM sys.indexes
        WHERE object_id = OBJECT_ID('dbo.Economia_Valores')
          AND name = 'IX_Economia_Valores_Serie_Fecha'
    )
        SET @Errors += 1;
END;

IF OBJECT_ID('dbo.Economia_Series', 'U') IS NOT NULL
BEGIN
    IF NOT EXISTS
    (
        SELECT 1
        FROM sys.key_constraints
        WHERE parent_object_id = OBJECT_ID('dbo.Economia_Series')
          AND name = 'UQ_Economia_Series_CodigoCanonico'
    )
        SET @Errors += 1;
END;

SELECT
    @Errors AS ValidationErrors,
    CASE
        WHEN @Errors = 0 THEN 'PASS'
        ELSE 'FAIL'
    END AS Resultado;

IF @Errors <> 0
    THROW 51000, 'ECONOMIA_WORLDCLASS_VALIDATION_FAILED', 1;
