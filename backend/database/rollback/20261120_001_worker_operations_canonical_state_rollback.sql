/*
  EDARSAHUB BOS — GATE-M1: Rollback Controlado en Desarrollo (orden inverso)
  Requiere autorizacion explicita de reversion en EDARSAHUB Desarrollo.
*/
SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> N'EDARSAHUB'
    THROW 52900, 'Rollback GATE-M1 bloqueado: DB_NAME() debe ser exactamente EDARSAHUB.', 1;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(N'dbo.sp_Worker_UpsertCapability', N'P') IS NOT NULL
        DROP PROCEDURE dbo.sp_Worker_UpsertCapability;

    IF OBJECT_ID(N'dbo.sp_Worker_RecordRecoveryEvent', N'P') IS NOT NULL
        DROP PROCEDURE dbo.sp_Worker_RecordRecoveryEvent;

    IF OBJECT_ID(N'dbo.sp_Worker_UpsertIncident', N'P') IS NOT NULL
        DROP PROCEDURE dbo.sp_Worker_UpsertIncident;

    IF OBJECT_ID(N'dbo.sp_Worker_UpsertJobState', N'P') IS NOT NULL
        DROP PROCEDURE dbo.sp_Worker_UpsertJobState;

    IF OBJECT_ID(N'dbo.Sys_Worker_Capabilities', N'U') IS NOT NULL
        DROP TABLE dbo.Sys_Worker_Capabilities;

    IF OBJECT_ID(N'dbo.Sys_Worker_RecoveryEvents', N'U') IS NOT NULL
        DROP TABLE dbo.Sys_Worker_RecoveryEvents;

    IF OBJECT_ID(N'dbo.Sys_Worker_Incidents', N'U') IS NOT NULL
        DROP TABLE dbo.Sys_Worker_Incidents;

    IF OBJECT_ID(N'dbo.Sys_Worker_Jobs', N'U') IS NOT NULL
        DROP TABLE dbo.Sys_Worker_Jobs;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO
