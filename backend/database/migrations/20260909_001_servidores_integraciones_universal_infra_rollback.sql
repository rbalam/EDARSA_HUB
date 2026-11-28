SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Sync_Control_Evidencias','U') IS NOT NULL
    BEGIN
        IF EXISTS (SELECT 1 FROM dbo.Sync_Control_Evidencias) THROW 51000, 'ROLLBACK_REFUSES_NONEMPTY_Sync_Control_Evidencias', 1;
        DROP TABLE dbo.Sync_Control_Evidencias;
    END;

    IF OBJECT_ID('dbo.Sistema_IdentificadoresExternos','U') IS NOT NULL
    BEGIN
        IF EXISTS (SELECT 1 FROM dbo.Sistema_IdentificadoresExternos) THROW 51000, 'ROLLBACK_REFUSES_NONEMPTY_Sistema_IdentificadoresExternos', 1;
        DROP TABLE dbo.Sistema_IdentificadoresExternos;
    END;

    IF OBJECT_ID('dbo.Sistema_Sync_Capacidades','U') IS NOT NULL
    BEGIN
        IF EXISTS (SELECT 1 FROM dbo.Sistema_Sync_Capacidades) THROW 51000, 'ROLLBACK_REFUSES_NONEMPTY_Sistema_Sync_Capacidades', 1;
        DROP TABLE dbo.Sistema_Sync_Capacidades;
    END;

    IF EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.Sync_Control_Ejecuciones') AND name='UX_Sync_Control_Ejecuciones_IdempotencyKey') DROP INDEX UX_Sync_Control_Ejecuciones_IdempotencyKey ON dbo.Sync_Control_Ejecuciones;
    IF EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.Sync_Control_Ejecuciones') AND name='IX_Sync_Control_Ejecuciones_Conexion_CodigoSync') DROP INDEX IX_Sync_Control_Ejecuciones_Conexion_CodigoSync ON dbo.Sync_Control_Ejecuciones;

    IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name='FK_Sync_Control_Ejecuciones_Conexion') ALTER TABLE dbo.Sync_Control_Ejecuciones DROP CONSTRAINT FK_Sync_Control_Ejecuciones_Conexion;
    IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name='FK_Sync_Control_Ejecuciones_Unidad') ALTER TABLE dbo.Sync_Control_Ejecuciones DROP CONSTRAINT FK_Sync_Control_Ejecuciones_Unidad;
    IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name='FK_Sync_Control_Ejecuciones_CodigoSync') ALTER TABLE dbo.Sync_Control_Ejecuciones DROP CONSTRAINT FK_Sync_Control_Ejecuciones_CodigoSync;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','IdempotencyKey') IS NOT NULL ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN IdempotencyKey;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','FinishedAtUTC') IS NOT NULL ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN FinishedAtUTC;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','StartedAtUTC') IS NOT NULL ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN StartedAtUTC;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','CodigoSync') IS NOT NULL ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN CodigoSync;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','UnidadNegocioID') IS NOT NULL ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN UnidadNegocioID;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','ConexionID') IS NOT NULL ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN ConexionID;

    IF COL_LENGTH('dbo.Servidores_ConexionEstado','FechaActualizacionUTC') IS NOT NULL ALTER TABLE dbo.Servidores_ConexionEstado DROP COLUMN FechaActualizacionUTC;
    IF COL_LENGTH('dbo.Servidores_ConexionEstado','UltimoSyncExitosoUTC') IS NOT NULL ALTER TABLE dbo.Servidores_ConexionEstado DROP COLUMN UltimoSyncExitosoUTC;
    IF COL_LENGTH('dbo.Servidores_ConexionEstado','UltimoSyncUTC') IS NOT NULL ALTER TABLE dbo.Servidores_ConexionEstado DROP COLUMN UltimoSyncUTC;
    IF COL_LENGTH('dbo.Servidores_ConexionEstado','LatenciaMs') IS NOT NULL ALTER TABLE dbo.Servidores_ConexionEstado DROP COLUMN LatenciaMs;
    IF COL_LENGTH('dbo.Servidores_ConexionEstado','UltimoErrorMensaje') IS NOT NULL ALTER TABLE dbo.Servidores_ConexionEstado DROP COLUMN UltimoErrorMensaje;
    IF COL_LENGTH('dbo.Servidores_ConexionEstado','UltimoErrorCodigo') IS NOT NULL ALTER TABLE dbo.Servidores_ConexionEstado DROP COLUMN UltimoErrorCodigo;
    IF COL_LENGTH('dbo.Servidores_ConexionEstado','UltimoErrorUTC') IS NOT NULL ALTER TABLE dbo.Servidores_ConexionEstado DROP COLUMN UltimoErrorUTC;
    IF COL_LENGTH('dbo.Servidores_ConexionEstado','UltimoExitoUTC') IS NOT NULL ALTER TABLE dbo.Servidores_ConexionEstado DROP COLUMN UltimoExitoUTC;
    IF COL_LENGTH('dbo.Servidores_ConexionEstado','UltimaPruebaUTC') IS NOT NULL ALTER TABLE dbo.Servidores_ConexionEstado DROP COLUMN UltimaPruebaUTC;

    IF COL_LENGTH('dbo.Unidades_Negocio','locale_operativo') IS NOT NULL ALTER TABLE dbo.Unidades_Negocio DROP COLUMN locale_operativo;
    IF COL_LENGTH('dbo.Unidades_Negocio','timezone_iana') IS NOT NULL ALTER TABLE dbo.Unidades_Negocio DROP COLUMN timezone_iana;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
