SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY

    BEGIN TRANSACTION;

    DECLARE @ProveedorID INT;

    SELECT
        @ProveedorID = ProveedorEconomicoID
    FROM dbo.Economia_Proveedores
    WHERE Codigo = N'INEGI';


    IF @ProveedorID IS NULL
    BEGIN
        THROW 51000,
        'Proveedor INEGI no encontrado',
        1;
    END;


    IF (
        SELECT COUNT_BIG(*)
        FROM dbo.Economia_Proveedores
        WHERE Codigo = N'INEGI'
    ) <> 1
    BEGIN
        THROW 51000,
        'Proveedor INEGI no es unico',
        1;
    END;


    IF EXISTS (
        SELECT 1
        FROM dbo.Economia_Proveedores
        WHERE ProveedorEconomicoID = @ProveedorID
          AND RequiereAutenticacion = 1
    )
    BEGIN

        UPDATE dbo.Economia_Proveedores
        SET
            RequiereAutenticacion = 0,
            FechaModificacionUTC = SYSUTCDATETIME()
        WHERE ProveedorEconomicoID = @ProveedorID;

    END;


    IF EXISTS (
        SELECT 1
        FROM dbo.Economia_Proveedores
        WHERE ProveedorEconomicoID = @ProveedorID
          AND RequiereAutenticacion <> 0
    )
    BEGIN
        THROW 51000,
        'INEGI no quedo configurado como publico',
        1;
    END;


    COMMIT TRANSACTION;

END TRY
BEGIN CATCH

    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;

END CATCH;
