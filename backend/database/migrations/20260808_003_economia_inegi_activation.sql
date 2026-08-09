SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY

    BEGIN TRANSACTION;

    DECLARE @ProveedorID INT;
    DECLARE @SerieID INT;


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


    IF EXISTS (
        SELECT 1
        FROM dbo.Economia_Proveedores
        WHERE ProveedorEconomicoID=@ProveedorID
          AND RequiereAutenticacion<>0
    )
    BEGIN
        THROW 51000,
        'INEGI requiere autenticacion incorrecta',
        1;
    END;


    IF EXISTS (
        SELECT 1
        FROM dbo.Servidores_Conexiones sc
        INNER JOIN dbo.Economia_Proveedores p
            ON p.ServerConexionID=sc.id
        WHERE p.ProveedorEconomicoID=@ProveedorID
          AND (
              sc.tipo_conexion<>N'DATA_SOURCE'
              OR sc.activo<>0
          )
    )
    BEGIN
        THROW 51000,
        'Conexion INEGI no cumple contrato DATA_SOURCE',
        1;
    END;


    SELECT
        @SerieID = SerieEconomicaID
    FROM dbo.Economia_Series
    WHERE CodigoCanonico=N'MX.INPC.INFLACION_ANUAL'
      AND ProveedorEconomicoID=@ProveedorID;


    IF @SerieID IS NULL
    BEGIN
        THROW 51000,
        'Serie INEGI no encontrada',
        1;
    END;


    IF EXISTS (
        SELECT 1
        FROM dbo.Economia_Valores v
        WHERE v.SerieEconomicaID=@SerieID
    )
    BEGIN
        THROW 51000,
        'Serie INEGI ya contiene valores',
        1;
    END;


    UPDATE dbo.Economia_Proveedores
    SET
        Activo=1,
        FechaModificacionUTC=SYSUTCDATETIME()
    WHERE ProveedorEconomicoID=@ProveedorID;


    UPDATE dbo.Economia_Series
    SET
        Activo=1,
        FechaModificacionUTC=SYSUTCDATETIME()
    WHERE SerieEconomicaID=@SerieID;


    COMMIT TRANSACTION;

END TRY
BEGIN CATCH

    IF @@TRANCOUNT>0
        ROLLBACK TRANSACTION;

    THROW;

END CATCH;
