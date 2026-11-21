SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> 'EDARSAHUB'
    THROW 51000, 'ABORT_WRONG_DATABASE', 1;

IF OBJECT_ID('dbo.Services_Credentials','U') IS NOT NULL
AND EXISTS (SELECT 1 FROM dbo.Services_Credentials)
    THROW 51031, 'ABORT_ROLLBACK_DATA_PRESENT_SERVICES_CREDENTIALS', 1;

IF OBJECT_ID('dbo.Services_ProviderSpecialties','U') IS NOT NULL
AND EXISTS (SELECT 1 FROM dbo.Services_ProviderSpecialties)
    THROW 51032, 'ABORT_ROLLBACK_DATA_PRESENT_PROVIDER_SPECIALTIES', 1;

IF OBJECT_ID('dbo.Services_Providers','U') IS NOT NULL
AND EXISTS (SELECT 1 FROM dbo.Services_Providers)
    THROW 51033, 'ABORT_ROLLBACK_DATA_PRESENT_SERVICES_PROVIDERS', 1;

BEGIN TRY
    BEGIN TRANSACTION;
    IF OBJECT_ID('dbo.Services_Credentials','U') IS NOT NULL DROP TABLE dbo.Services_Credentials;
    IF OBJECT_ID('dbo.Services_ProviderSpecialties','U') IS NOT NULL DROP TABLE dbo.Services_ProviderSpecialties;
    IF OBJECT_ID('dbo.Services_Providers','U') IS NOT NULL DROP TABLE dbo.Services_Providers;
    COMMIT;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK;
    THROW;
END CATCH;
