SET NOCOUNT ON;

IF DB_NAME() <> 'EDARSAHUB'
    THROW 51000, 'SYNC_HISTORICAL_PLANNER_VALIDATION_WRONG_DATABASE', 1;

IF OBJECT_ID('dbo.Sync_Control_Ejecuciones','U') IS NULL
    THROW 51000, 'SYNC_HISTORICAL_PLANNER_VALIDATION_MISSING_LEDGER', 1;

DECLARE @required TABLE (ColumnName sysname NOT NULL);
INSERT INTO @required (ColumnName) VALUES
('ParentSyncControlID'),
('RunKind'),
('CorrelationID'),
('SistemaTipoID'),
('SistemaVersionID'),
('SucursalID'),
('SucursalOrigenID'),
('CategoriaCodigo'),
('EntidadCodigo'),
('BlockOrdinal'),
('ExecutionOrder'),
('PlanJSON'),
('CheckpointJSON'),
('AttemptCount'),
('MaxAttempts'),
('NextRetryAtUTC'),
('PauseRequested'),
('CancelRequested'),
('LastHeartbeatUTC'),
('DispatchCount'),
('WorkerJobID'),
('RequestedBy'),
('Reason'),
('UpdatedAtUTC');

IF EXISTS (
    SELECT 1
    FROM @required r
    WHERE COL_LENGTH('dbo.Sync_Control_Ejecuciones', r.ColumnName) IS NULL
)
    THROW 51000, 'SYNC_HISTORICAL_PLANNER_VALIDATION_COLUMNS_MISSING', 1;

IF EXISTS (
    SELECT 1
    FROM dbo.Sync_Control_Ejecuciones
    WHERE PlanJSON IS NOT NULL AND ISJSON(PlanJSON)<>1
)
    THROW 51000, 'SYNC_HISTORICAL_PLANNER_INVALID_PLAN_JSON', 1;

IF EXISTS (
    SELECT 1
    FROM dbo.Sync_Control_Ejecuciones
    WHERE CheckpointJSON IS NOT NULL AND ISJSON(CheckpointJSON)<>1
)
    THROW 51000, 'SYNC_HISTORICAL_PLANNER_INVALID_CHECKPOINT_JSON', 1;

IF EXISTS (
    SELECT 1
    FROM dbo.Sync_Control_Ejecuciones
    WHERE ParentSyncControlID IS NOT NULL
      AND ParentSyncControlID = SyncControlID
)
    THROW 51000, 'SYNC_HISTORICAL_PLANNER_SELF_PARENT', 1;

SELECT
    RunKind,
    Status,
    COUNT_BIG(*) AS Total
FROM dbo.Sync_Control_Ejecuciones
GROUP BY RunKind, Status
ORDER BY RunKind, Status;
