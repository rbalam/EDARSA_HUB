SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(N'dbo.Sistema_CatalogosConfig', N'U') IS NULL
        THROW 51370, 'Sistema_CatalogosConfig no existe.', 1;

    /*
      Solo elimina filas creadas inequívocamente por Slice 035.
      No toca workflow, permisos ni registros preexistentes.
    */
    DELETE FROM dbo.Sistema_CatalogosConfig
    WHERE CreatedBy = N'MIGRATION_20260819_035'
      AND UPPER(LTRIM(RTRIM(TipoConfiguracion))) = N'CATALOGO_FISICO';

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
