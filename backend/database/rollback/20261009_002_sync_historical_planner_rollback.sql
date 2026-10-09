SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Sync_Control_Ejecuciones','U') IS NULL
        THROW 51000, 'SYNC_HISTORICAL_PLANNER_ROLLBACK_MISSING_LEDGER', 1;

    IF EXISTS (
        SELECT 1
        FROM dbo.Sync_Control_Ejecuciones
        WHERE RunKind IN ('PARENT','ATOMIC')
           OR ParentSyncControlID IS NOT NULL
           OR CorrelationID IS NOT NULL
           OR PlanJSON IS NOT NULL
           OR CheckpointJSON IS NOT NULL
    )
        THROW 51000, 'SYNC_HISTORICAL_PLANNER_ROLLBACK_REFUSES_RUNTIME_DATA', 1;

    IF EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.Sync_Control_Ejecuciones') AND name='IX_Sync_Control_Ejecuciones_Parent_Status')
        DROP INDEX IX_Sync_Control_Ejecuciones_Parent_Status ON dbo.Sync_Control_Ejecuciones;
    IF EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.Sync_Control_Ejecuciones') AND name='IX_Sync_Control_Ejecuciones_Correlation')
        DROP INDEX IX_Sync_Control_Ejecuciones_Correlation ON dbo.Sync_Control_Ejecuciones;

    IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name='FK_Sync_Control_Ejecuciones_Parent')
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP CONSTRAINT FK_Sync_Control_Ejecuciones_Parent;
    IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name='FK_Sync_Control_Ejecuciones_SistemaTipo')
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP CONSTRAINT FK_Sync_Control_Ejecuciones_SistemaTipo;
    IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name='FK_Sync_Control_Ejecuciones_SistemaCapacidad')
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP CONSTRAINT FK_Sync_Control_Ejecuciones_SistemaCapacidad;
    IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name='FK_Sync_Control_Ejecuciones_SistemaVersion')
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP CONSTRAINT FK_Sync_Control_Ejecuciones_SistemaVersion;
    IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name='FK_Sync_Control_Ejecuciones_Sucursal')
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP CONSTRAINT FK_Sync_Control_Ejecuciones_Sucursal;

    IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name='CK_Sync_Control_Ejecuciones_RunKind')
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP CONSTRAINT CK_Sync_Control_Ejecuciones_RunKind;
    IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name='CK_Sync_Control_Ejecuciones_PlanJSON')
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP CONSTRAINT CK_Sync_Control_Ejecuciones_PlanJSON;
    IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name='CK_Sync_Control_Ejecuciones_CheckpointJSON')
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP CONSTRAINT CK_Sync_Control_Ejecuciones_CheckpointJSON;
    IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name='CK_Sync_Control_Ejecuciones_Attempts')
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP CONSTRAINT CK_Sync_Control_Ejecuciones_Attempts;

    IF EXISTS (SELECT 1 FROM sys.default_constraints WHERE name='DF_Sync_Control_Ejecuciones_RunKind')
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP CONSTRAINT DF_Sync_Control_Ejecuciones_RunKind;
    IF EXISTS (SELECT 1 FROM sys.default_constraints WHERE name='DF_Sync_Control_Ejecuciones_AttemptCount')
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP CONSTRAINT DF_Sync_Control_Ejecuciones_AttemptCount;
    IF EXISTS (SELECT 1 FROM sys.default_constraints WHERE name='DF_Sync_Control_Ejecuciones_MaxAttempts')
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP CONSTRAINT DF_Sync_Control_Ejecuciones_MaxAttempts;
    IF EXISTS (SELECT 1 FROM sys.default_constraints WHERE name='DF_Sync_Control_Ejecuciones_PauseRequested')
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP CONSTRAINT DF_Sync_Control_Ejecuciones_PauseRequested;
    IF EXISTS (SELECT 1 FROM sys.default_constraints WHERE name='DF_Sync_Control_Ejecuciones_CancelRequested')
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP CONSTRAINT DF_Sync_Control_Ejecuciones_CancelRequested;
    IF EXISTS (SELECT 1 FROM sys.default_constraints WHERE name='DF_Sync_Control_Ejecuciones_DispatchCount')
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP CONSTRAINT DF_Sync_Control_Ejecuciones_DispatchCount;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','UpdatedAtUTC') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN UpdatedAtUTC;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','Reason') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN Reason;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','RequestedBy') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN RequestedBy;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','WorkerJobID') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN WorkerJobID;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','DispatchCount') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN DispatchCount;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','LastHeartbeatUTC') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN LastHeartbeatUTC;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','CancelRequested') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN CancelRequested;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','PauseRequested') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN PauseRequested;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','NextRetryAtUTC') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN NextRetryAtUTC;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','MaxAttempts') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN MaxAttempts;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','AttemptCount') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN AttemptCount;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','CheckpointJSON') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN CheckpointJSON;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','PlanJSON') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN PlanJSON;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','ExecutionOrder') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN ExecutionOrder;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','BlockOrdinal') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN BlockOrdinal;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','EntidadCodigo') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN EntidadCodigo;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','CategoriaCodigo') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN CategoriaCodigo;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','SucursalOrigenID') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN SucursalOrigenID;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','SucursalID') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN SucursalID;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','SistemaVersionID') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN SistemaVersionID;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','SistemaCapacidadID') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN SistemaCapacidadID;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','SistemaTipoID') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN SistemaTipoID;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','CorrelationID') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN CorrelationID;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','RunKind') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN RunKind;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','ParentSyncControlID') IS NOT NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones DROP COLUMN ParentSyncControlID;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
