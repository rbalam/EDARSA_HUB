SET NOCOUNT ON;

SELECT
    CASE
        WHEN OBJECT_ID(
            N'dbo.Sys_Scheduler_RuntimeState',
            N'U'
        ) IS NOT NULL
        THEN 1 ELSE 0
    END AS RuntimeStateTableExists,

    CASE
        WHEN OBJECT_ID(
            N'dbo.sp_Scheduler_SetAdministrativePause',
            N'P'
        ) IS NOT NULL
        THEN 1 ELSE 0
    END AS SetPauseProcedureExists,

    HAS_PERMS_BY_NAME(
        N'dbo.sp_Scheduler_SetAdministrativePause',
        N'OBJECT',
        N'EXECUTE'
    ) AS CurrentUserCanExecuteProcedure;

IF OBJECT_ID(
    N'dbo.Sys_Scheduler_RuntimeState',
    N'U'
) IS NOT NULL
BEGIN
    SELECT
        JobID,
        PausadoAdministrativo,
        FechaActualizacion
    FROM dbo.Sys_Scheduler_RuntimeState
    ORDER BY JobID;
END;
