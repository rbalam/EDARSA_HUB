SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> 'EDARSAHUB'
    THROW 51000, 'ABORT_WRONG_DATABASE', 1;

IF SUSER_SNAME() = 'HRLectura'
    THROW 51001, 'ABORT_READONLY_LOGIN_NOT_WRITER', 1;

IF OBJECT_ID('dbo.Logistica_ViajeLegs','U') IS NOT NULL
AND EXISTS (SELECT 1 FROM dbo.Logistica_ViajeLegs)
    THROW 51010, 'ABORT_ROLLBACK_DATA_PRESENT_LOGISTICA_VIAJELEGS', 1;

IF OBJECT_ID('dbo.Logistica_Viajes','U') IS NOT NULL
AND EXISTS (SELECT 1 FROM dbo.Logistica_Viajes)
    THROW 51011, 'ABORT_ROLLBACK_DATA_PRESENT_LOGISTICA_VIAJES', 1;

IF OBJECT_ID('dbo.Logistica_MediosTransportePerfilOperativo','U') IS NOT NULL
AND EXISTS (SELECT 1 FROM dbo.Logistica_MediosTransportePerfilOperativo)
    THROW 51012, 'ABORT_ROLLBACK_DATA_PRESENT_LOGISTICA_MEDIOS', 1;

IF OBJECT_ID('dbo.Logistica_Ordenes','U') IS NOT NULL
AND EXISTS (SELECT 1 FROM dbo.Logistica_Ordenes)
    THROW 51013, 'ABORT_ROLLBACK_DATA_PRESENT_LOGISTICA_ORDENES', 1;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Logistica_ViajeLegs','U') IS NOT NULL
        DROP TABLE dbo.Logistica_ViajeLegs;

    IF OBJECT_ID('dbo.Logistica_Viajes','U') IS NOT NULL
        DROP TABLE dbo.Logistica_Viajes;

    IF OBJECT_ID('dbo.Logistica_MediosTransportePerfilOperativo','U') IS NOT NULL
        DROP TABLE dbo.Logistica_MediosTransportePerfilOperativo;

    IF OBJECT_ID('dbo.Logistica_Ordenes','U') IS NOT NULL
        DROP TABLE dbo.Logistica_Ordenes;

    IF OBJECT_ID('dbo.Logistica_Cat_PropositosServicio','U') IS NOT NULL
        DROP TABLE dbo.Logistica_Cat_PropositosServicio;

    IF OBJECT_ID('dbo.Logistica_Cat_ModosTransporte','U') IS NOT NULL
        DROP TABLE dbo.Logistica_Cat_ModosTransporte;

    COMMIT;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK;
    THROW;
END CATCH;
