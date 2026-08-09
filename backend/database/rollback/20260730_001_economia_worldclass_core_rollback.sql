SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Economia_ContextoOperativo', 'U') IS NOT NULL
        DROP TABLE dbo.Economia_ContextoOperativo;

    IF OBJECT_ID('dbo.Economia_Valores', 'U') IS NOT NULL
        DROP TABLE dbo.Economia_Valores;

    IF OBJECT_ID('dbo.Economia_Series', 'U') IS NOT NULL
        DROP TABLE dbo.Economia_Series;

    IF OBJECT_ID('dbo.Economia_CategoriasIndicador', 'U') IS NOT NULL
        DROP TABLE dbo.Economia_CategoriasIndicador;

    IF OBJECT_ID('dbo.Economia_Proveedores', 'U') IS NOT NULL
        DROP TABLE dbo.Economia_Proveedores;

    IF OBJECT_ID('dbo.Economia_Paises', 'U') IS NOT NULL
        DROP TABLE dbo.Economia_Paises;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
