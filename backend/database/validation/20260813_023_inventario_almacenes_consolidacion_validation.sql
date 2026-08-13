SET NOCOUNT ON;

SELECT
    DB_NAME() AS DBName,
    SUSER_SNAME() AS LoginName,
    USER_NAME() AS DatabaseUser;

SELECT
    COUNT(*) AS Almacenes
FROM dbo.Inventario_Almacenes;

SELECT
    COUNT_BIG(*) AS Movimientos
FROM dbo.Inventario_Movimientos;

SELECT
    COUNT(*) AS LegacyWarehousesRemaining
FROM dbo.Inventario_Almacenes
WHERE AlmacenID BETWEEN 1 AND 39;

SELECT
    COUNT(*) AS LegacyRecepcionesRemaining
FROM dbo.Compras_Recepciones
WHERE AlmacenID BETWEEN 1 AND 39;

SELECT
    COUNT(*) AS LegacyMovimientosRemaining
FROM dbo.Inventario_Movimientos
WHERE AlmacenID BETWEEN 1 AND 39;

SELECT
    COUNT(*) AS SurvivorRecepciones01
FROM dbo.Compras_Recepciones
WHERE AlmacenID = 86;

SELECT
    COUNT(*) AS SurvivorMovimientos01
FROM dbo.Inventario_Movimientos
WHERE AlmacenID = 86;

SELECT
    COUNT(*) AS DuplicateCanonicalKeys
FROM (
    SELECT
        EmpresaID,
        SucursalID,
        CodigoAlmacen
    FROM dbo.Inventario_Almacenes
    GROUP BY
        EmpresaID,
        SucursalID,
        CodigoAlmacen
    HAVING COUNT(*) > 1
) x;
