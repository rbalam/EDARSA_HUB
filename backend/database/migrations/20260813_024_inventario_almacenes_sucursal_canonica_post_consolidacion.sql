SET NOCOUNT ON;
SET XACT_ABORT ON;

DECLARE @ExpectedWarehouses int = 67;
DECLARE @ExpectedUpdates int = 0;
DECLARE @ExpectedMovements bigint = 15224;

IF DB_NAME() <> 'EDARSAHUB'
    THROW 53000, 'Base inesperada.', 1;

IF SUSER_SNAME() <> 'HRLectura'
    THROW 53001, 'Login inesperado.', 1;

IF USER_NAME() <> 'HRLectura'
    THROW 53002, 'Usuario inesperado.', 1;

IF (
    SELECT COUNT(*)
    FROM dbo.Inventario_Almacenes
) <> @ExpectedWarehouses
    THROW 53003, 'Cantidad de almacenes inesperada.', 1;

IF (
    SELECT COUNT(*)
    FROM dbo.Inventario_Almacenes a
    JOIN dbo.Sistema_Sucursales s
      ON s.EmpresaID=a.EmpresaID
     AND ISNULL(s.Activo,0)=1
    WHERE a.SucursalID<>s.SucursalID
) <> @ExpectedUpdates
    THROW 53004, 'Scope de actualización cambió.', 1;

IF EXISTS (
    SELECT 1
    FROM dbo.Inventario_Movimientos m
    JOIN dbo.Inventario_Almacenes a
      ON a.AlmacenID=m.AlmacenID
    JOIN dbo.Sistema_Sucursales s
      ON s.EmpresaID=a.EmpresaID
     AND ISNULL(s.Activo,0)=1
    WHERE m.SucursalID<>s.SucursalID
)
    THROW 53005, 'Movimientos no reconciliados.', 1;

IF (
    SELECT COUNT_BIG(*)
    FROM dbo.Inventario_Movimientos
) <> @ExpectedMovements
    THROW 53006, 'Cantidad de movimientos inesperada.', 1;

BEGIN TRY
    BEGIN TRANSACTION;

    UPDATE a
       SET a.SucursalID=s.SucursalID
    FROM dbo.Inventario_Almacenes a
    JOIN dbo.Sistema_Sucursales s
      ON s.EmpresaID=a.EmpresaID
     AND ISNULL(s.Activo,0)=1
    WHERE a.SucursalID<>s.SucursalID;

    IF @@ROWCOUNT <> @ExpectedUpdates
        THROW 53007, 'Cantidad actualizada inesperada.', 1;

    IF OBJECT_ID(
        'dbo.FK_Inventario_Almacenes_Sucursal',
        'F'
    ) IS NOT NULL
    BEGIN
        ALTER TABLE dbo.Inventario_Almacenes
            DROP CONSTRAINT FK_Inventario_Almacenes_Sucursal;
    END;

    ALTER TABLE dbo.Inventario_Almacenes
        WITH CHECK
        ADD CONSTRAINT FK_Inventario_Almacenes_Sucursal
        FOREIGN KEY (SucursalID)
        REFERENCES dbo.Sistema_Sucursales (SucursalID);

    ALTER TABLE dbo.Inventario_Almacenes
        CHECK CONSTRAINT FK_Inventario_Almacenes_Sucursal;

    IF EXISTS (
        SELECT 1
        FROM dbo.Inventario_Almacenes a
        LEFT JOIN dbo.Sistema_Sucursales s
          ON s.SucursalID=a.SucursalID
        WHERE s.SucursalID IS NULL
    )
        THROW 53008, 'Almacén sin sucursal canónica.', 1;

    IF EXISTS (
        SELECT 1
        FROM dbo.Inventario_Movimientos m
        JOIN dbo.Inventario_Almacenes a
          ON a.AlmacenID=m.AlmacenID
        WHERE m.SucursalID<>a.SucursalID
    )
        THROW 53009, 'Movimientos inconsistentes.', 1;

    COMMIT TRANSACTION;

    SELECT
        'MIGRATION_024_OK' AS Estado,
        @ExpectedUpdates AS Actualizados,
        @ExpectedWarehouses AS Almacenes,
        @ExpectedMovements AS Movimientos;

END TRY
BEGIN CATCH

    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;

    THROW;

END CATCH;
