SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    /*
      Estado administrativo persistente del Scheduler runtime.

      Esta tabla NO define jobs, cron, intervalos ni estados
      de ejecución. Solo persiste pausa administrativa.
    */
    IF OBJECT_ID(
        N'dbo.Sys_Scheduler_RuntimeState',
        N'U'
    ) IS NULL
    BEGIN
        CREATE TABLE dbo.Sys_Scheduler_RuntimeState (
            JobID varchar(100) NOT NULL,

            PausadoAdministrativo bit NOT NULL
                CONSTRAINT DF_Sys_Scheduler_RuntimeState_Pausado
                DEFAULT (0),

            FechaActualizacion datetime2(7) NOT NULL
                CONSTRAINT DF_Sys_Scheduler_RuntimeState_FechaActualizacion
                DEFAULT SYSUTCDATETIME(),

            CONSTRAINT PK_Sys_Scheduler_RuntimeState
                PRIMARY KEY (JobID)
        );
    END;

    IF COL_LENGTH(
        N'dbo.Sys_Scheduler_RuntimeState',
        N'JobID'
    ) IS NULL
        THROW 51001,
            'Falta JobID en Sys_Scheduler_RuntimeState.',
            1;

    IF COL_LENGTH(
        N'dbo.Sys_Scheduler_RuntimeState',
        N'PausadoAdministrativo'
    ) IS NULL
        THROW 51002,
            'Falta PausadoAdministrativo en Sys_Scheduler_RuntimeState.',
            1;

    IF COL_LENGTH(
        N'dbo.Sys_Scheduler_RuntimeState',
        N'FechaActualizacion'
    ) IS NULL
        THROW 51003,
            'Falta FechaActualizacion en Sys_Scheduler_RuntimeState.',
            1;

    COMMIT TRANSACTION;

END TRY
BEGIN CATCH

    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;

END CATCH;
GO

/*
  Interfaz de escritura estrecha del Scheduler.

  El backend no debe ejecutar INSERT/UPDATE directo sobre la tabla.
*/
CREATE OR ALTER PROCEDURE dbo.sp_Scheduler_SetAdministrativePause
    @JobID varchar(100),
    @PausadoAdministrativo bit
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    SET @JobID = LTRIM(RTRIM(@JobID));

    IF @JobID IS NULL OR @JobID = ''
        THROW 51010, 'JobID requerido.', 1;

    IF LEN(@JobID) > 100
        THROW 51011, 'JobID excede 100 caracteres.', 1;

    BEGIN TRY
        BEGIN TRANSACTION;

        UPDATE dbo.Sys_Scheduler_RuntimeState
        SET
            PausadoAdministrativo =
                @PausadoAdministrativo,
            FechaActualizacion =
                SYSUTCDATETIME()
        WHERE JobID = @JobID;

        IF @@ROWCOUNT = 0
        BEGIN
            INSERT INTO dbo.Sys_Scheduler_RuntimeState (
                JobID,
                PausadoAdministrativo,
                FechaActualizacion
            )
            VALUES (
                @JobID,
                @PausadoAdministrativo,
                SYSUTCDATETIME()
            );
        END;

        COMMIT TRANSACTION;

    END TRY
    BEGIN CATCH

        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        THROW;

    END CATCH;
END;
GO

/*
  Contrato explícito para la única identidad runtime autorizada
  actualmente por EDARSAHUB.

  Este GRANT permite conservar el Scheduler cuando HRLectura sea
  posteriormente reducido a privilegios realmente mínimos.
*/
IF USER_ID(N'HRLectura') IS NULL
    THROW 51020, 'No existe usuario HRLectura en EDARSAHUB.', 1;
GO

GRANT EXECUTE
ON OBJECT::dbo.sp_Scheduler_SetAdministrativePause
TO HRLectura;
GO
