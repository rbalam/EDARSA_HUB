SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Sync_Logs','U') IS NULL
        THROW 51000, 'SYNC_HISTORICAL_LOG_ROLLBACK_MISSING_Sync_Logs', 1;

    IF EXISTS (
        SELECT 1
        FROM dbo.Sync_Logs
        WHERE SyncControlID IS NOT NULL
           OR CorrelationID IS NOT NULL
           OR EventCode IS NOT NULL
           OR PayloadJSON IS NOT NULL
    )
        THROW 51000, 'SYNC_HISTORICAL_LOG_ROLLBACK_REFUSES_RUNTIME_DATA', 1;

    IF EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE object_id=OBJECT_ID('dbo.Sync_Logs')
          AND name='IX_Sync_Logs_Control_Time'
    )
        DROP INDEX IX_Sync_Logs_Control_Time ON dbo.Sync_Logs;

    IF EXISTS (
        SELECT 1 FROM sys.foreign_keys
        WHERE name='FK_Sync_Logs_SyncControl'
    )
        ALTER TABLE dbo.Sync_Logs
        DROP CONSTRAINT FK_Sync_Logs_SyncControl;

    IF EXISTS (
        SELECT 1 FROM sys.check_constraints
        WHERE name='CK_Sync_Logs_PayloadJSON'
    )
        ALTER TABLE dbo.Sync_Logs
        DROP CONSTRAINT CK_Sync_Logs_PayloadJSON;

    IF COL_LENGTH('dbo.Sync_Logs','PayloadJSON') IS NOT NULL
        ALTER TABLE dbo.Sync_Logs DROP COLUMN PayloadJSON;
    IF COL_LENGTH('dbo.Sync_Logs','EventCode') IS NOT NULL
        ALTER TABLE dbo.Sync_Logs DROP COLUMN EventCode;
    IF COL_LENGTH('dbo.Sync_Logs','CorrelationID') IS NOT NULL
        ALTER TABLE dbo.Sync_Logs DROP COLUMN CorrelationID;
    IF COL_LENGTH('dbo.Sync_Logs','SyncControlID') IS NOT NULL
        ALTER TABLE dbo.Sync_Logs DROP COLUMN SyncControlID;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
