-- Rollback reversible GATE-M2 R3: retirar exclusivamente sistema.worker_console (/worker-console)
SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    IF DB_NAME() <> N'EDARSAHUB'
        THROW 51200, 'UNEXPECTED_DATABASE_FORBIDDEN', 1;

    BEGIN TRANSACTION;

    DELETE FROM dbo.Sistema_ModulosMenus
    WHERE Codigo = N'sistema.worker_console'
      AND Ruta = N'/worker-console';

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
