SET NOCOUNT ON;

SELECT
    DB_NAME() AS DBName,
    SUSER_SNAME() AS LoginName,
    USER_NAME() AS DatabaseUser;

SELECT COUNT(*) AS Almacenes
FROM dbo.Inventario_Almacenes;

SELECT COUNT_BIG(*) AS Movimientos
FROM dbo.Inventario_Movimientos;

SELECT COUNT(*) AS AlmacenesSinSucursalCanonica
FROM dbo.Inventario_Almacenes a
LEFT JOIN dbo.Sistema_Sucursales s
  ON s.SucursalID=a.SucursalID
WHERE s.SucursalID IS NULL;

SELECT COUNT_BIG(*) AS MovimientosInconsistentes
FROM dbo.Inventario_Movimientos m
JOIN dbo.Inventario_Almacenes a
  ON a.AlmacenID=m.AlmacenID
WHERE m.SucursalID<>a.SucursalID;

SELECT
    fk.name AS FKName,
    OBJECT_NAME(fk.referenced_object_id) AS TablaReferenciada
FROM sys.foreign_keys fk
WHERE fk.parent_object_id=
      OBJECT_ID('dbo.Inventario_Almacenes')
  AND fk.name='FK_Inventario_Almacenes_Sucursal';

SELECT
    SucursalID,
    COUNT(*) AS Almacenes
FROM dbo.Inventario_Almacenes
GROUP BY SucursalID
ORDER BY SucursalID;
