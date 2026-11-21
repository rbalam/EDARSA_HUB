SET NOCOUNT ON;

SELECT
    COL_LENGTH('dbo.Sync_Logs','SyncControlID') AS SyncControlIDLength,
    COL_LENGTH('dbo.Sync_Logs','CorrelationID') AS CorrelationIDLength,
    COL_LENGTH('dbo.Sync_Logs','EventCode') AS EventCodeLength,
    COL_LENGTH('dbo.Sync_Logs','PayloadJSON') AS PayloadJSONLength;

SELECT TOP 20
    id, SyncControlID, CorrelationID, EventCode,
    type, timestamp, operador
FROM dbo.Sync_Logs
WHERE SyncControlID IS NOT NULL
ORDER BY id DESC;
