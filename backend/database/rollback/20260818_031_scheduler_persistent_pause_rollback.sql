SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(
        N'dbo.sp_Scheduler_SetAdministrativePause',
        N'P'
    ) IS NOT NULL
    BEGIN
        DROP PROCEDURE
            dbo.sp_Scheduler_SetAdministrativePause;
    END;

    IF OBJECT_ID(
        N'dbo.Sys_Scheduler_RuntimeState',
        N'U'
    ) IS NOT NULL
    BEGIN
        DROP TABLE dbo.Sys_Scheduler_RuntimeState;
    END;

    COMMIT TRANSACTION;

END TRY
BEGIN CATCH

    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;

END CATCH;
