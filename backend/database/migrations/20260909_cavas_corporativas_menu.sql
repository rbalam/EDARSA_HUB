SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @ModuloID int;
    DECLARE @Orden int;

    SELECT @ModuloID = ModuloID
    FROM dbo.Sistema_Modulos WITH (UPDLOCK, HOLDLOCK)
    WHERE Codigo = N'CAVA_SOCIOS'
      AND ISNULL(Activo, 1) = 1;

    IF @ModuloID IS NULL
        THROW 51001, 'CAVA_SOCIOS_MODULE_NOT_FOUND', 1;

    IF EXISTS (
        SELECT 1
        FROM dbo.Sistema_ModulosMenus
        WHERE Codigo = N'cava.corporativas'
          AND (ModuloID <> @ModuloID
               OR ISNULL(Ruta, N'') <> N'/cavas-corporativas'
               OR ISNULL(RequierePermiso, N'') <> N'cava_socios')
    )
        THROW 51002, 'CAVAS_CORPORATIVAS_MENU_CODE_COLLISION', 1;

    IF EXISTS (
        SELECT 1
        FROM dbo.Sistema_ModulosMenus
        WHERE Ruta = N'/cavas-corporativas'
          AND Codigo <> N'cava.corporativas'
    )
        THROW 51003, 'CAVAS_CORPORATIVAS_MENU_ROUTE_COLLISION', 1;

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Sistema_ModulosMenus WITH (UPDLOCK, HOLDLOCK)
        WHERE Codigo = N'cava.corporativas'
    )
    BEGIN
        SELECT @Orden = ISNULL(MAX(Orden), 0) + 1
        FROM dbo.Sistema_ModulosMenus
        WHERE ModuloID = @ModuloID;

        INSERT INTO dbo.Sistema_ModulosMenus
            (ModuloID, MenuPadreID, Codigo, Nombre, Descripcion, Icono, Ruta, Orden, RequierePermiso, Activo, FechaCreacion)
        VALUES
            (@ModuloID, NULL, N'cava.corporativas', N'Cavas Corporativas',
             N'Beneficios y convenios corporativos', N'Wine', N'/cavas-corporativas',
             @Orden, N'cava_socios', 1, GETDATE());
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
