SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Sync_Logs','U') IS NULL
        THROW 51000, 'SYNC_HISTORICAL_LOG_MISSING_Sync_Logs', 1;
    IF OBJECT_ID('dbo.Sync_Control_Ejecuciones','U') IS NULL
        THROW 51000, 'SYNC_HISTORICAL_LOG_MISSING_LEDGER', 1;

    IF COL_LENGTH('dbo.Sync_Logs','SyncControlID') IS NULL
        ALTER TABLE dbo.Sync_Logs ADD SyncControlID int NULL;

    IF COL_LENGTH('dbo.Sync_Logs','CorrelationID') IS NULL
        ALTER TABLE dbo.Sync_Logs ADD CorrelationID uniqueidentifier NULL;

    IF COL_LENGTH('dbo.Sync_Logs','EventCode') IS NULL
        ALTER TABLE dbo.Sync_Logs ADD EventCode nvarchar(80) NULL;

    IF COL_LENGTH('dbo.Sync_Logs','PayloadJSON') IS NULL
        ALTER TABLE dbo.Sync_Logs ADD PayloadJSON nvarchar(max) NULL;

    IF NOT EXISTS (
        SELECT 1 FROM sys.foreign_keys
        WHERE name='FK_Sync_Logs_SyncControl'
    )
        EXEC(N'
            ALTER TABLE dbo.Sync_Logs WITH CHECK
            ADD CONSTRAINT FK_Sync_Logs_SyncControl
            FOREIGN KEY (SyncControlID)
            REFERENCES dbo.Sync_Control_Ejecuciones(SyncControlID);
        ');

    /*
      PayloadJSON/SyncControlID/CorrelationID/EventCode nacen en este batch.
      Diferir checks e indice evita resolucion temprana de columnas nuevas.
    */
    IF NOT EXISTS (
        SELECT 1 FROM sys.check_constraints
        WHERE name='CK_Sync_Logs_PayloadJSON'
    )
        EXEC(N'
            ALTER TABLE dbo.Sync_Logs
            ADD CONSTRAINT CK_Sync_Logs_PayloadJSON
            CHECK (PayloadJSON IS NULL OR ISJSON(PayloadJSON)=1);
        ');

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE object_id=OBJECT_ID('dbo.Sync_Logs')
          AND name='IX_Sync_Logs_Control_Time'
    )
        EXEC(N'
            CREATE INDEX IX_Sync_Logs_Control_Time
            ON dbo.Sync_Logs (SyncControlID, timestamp DESC, id DESC)
            INCLUDE (CorrelationID, EventCode, type);
        ');

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
