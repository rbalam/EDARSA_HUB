SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    /*
      Development rollback for an unactivated foundation.
      Gate5D1 does not execute this file.
      Never run against a database containing operational Production Quality data.
    */

    IF OBJECT_ID('dbo.Production_DeviceCalibration', 'U') IS NOT NULL
        DROP TABLE dbo.Production_DeviceCalibration;

    IF OBJECT_ID('dbo.Production_QualityAction', 'U') IS NOT NULL
        DROP TABLE dbo.Production_QualityAction;

    IF OBJECT_ID('dbo.Production_QualityDecision', 'U') IS NOT NULL
        DROP TABLE dbo.Production_QualityDecision;

    IF OBJECT_ID('dbo.Production_Evidence', 'U') IS NOT NULL
        DROP TABLE dbo.Production_Evidence;

    IF OBJECT_ID('dbo.Production_Measurement', 'U') IS NOT NULL
        DROP TABLE dbo.Production_Measurement;

    IF OBJECT_ID('dbo.Production_Device', 'U') IS NOT NULL
        DROP TABLE dbo.Production_Device;

    IF OBJECT_ID('dbo.Production_QualityStandardVersion', 'U') IS NOT NULL
        DROP TABLE dbo.Production_QualityStandardVersion;

    IF OBJECT_ID('dbo.Production_QualityStandard', 'U') IS NOT NULL
        DROP TABLE dbo.Production_QualityStandard;

    IF OBJECT_ID('dbo.Production_Item', 'U') IS NOT NULL
        DROP TABLE dbo.Production_Item;

    IF OBJECT_ID('dbo.Production_Station', 'U') IS NOT NULL
        DROP TABLE dbo.Production_Station;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
