SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(
        'dbo.Compras_Inventarios_Fisicos_Detalle_Stage',
        'U'
    ) IS NOT NULL
    BEGIN
        DROP TABLE dbo.Compras_Inventarios_Fisicos_Detalle_Stage;
    END;

    IF OBJECT_ID(
        'dbo.Compras_Inventarios_Fisicos_Stage',
        'U'
    ) IS NOT NULL
    BEGIN
        DROP TABLE dbo.Compras_Inventarios_Fisicos_Stage;
    END;

    IF OBJECT_ID(
        'dbo.Compras_Inventarios_Fisicos_SyncRuns',
        'U'
    ) IS NOT NULL
    BEGIN
        DROP TABLE dbo.Compras_Inventarios_Fisicos_SyncRuns;
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
