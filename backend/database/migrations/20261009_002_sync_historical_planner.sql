SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Sync_Control_Ejecuciones','U') IS NULL
        THROW 51000, 'SYNC_HISTORICAL_PLANNER_MISSING_LEDGER', 1;

    /*
      Fase 3 - planner/orquestador historico.

      El ledger canonico existente se extiende para representar:
      - job padre persistente;
      - unidades atomicas hijas;
      - contexto canonico;
      - checkpoint/retry/control cooperativo.

      NO se crea otra tabla de runs.
    */

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','ParentSyncControlID') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD ParentSyncControlID int NULL;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','RunKind') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones
        ADD RunKind nvarchar(20) NOT NULL
            CONSTRAINT DF_Sync_Control_Ejecuciones_RunKind DEFAULT ('LEGACY');

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','CorrelationID') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD CorrelationID uniqueidentifier NULL;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','SistemaTipoID') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD SistemaTipoID int NULL;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','SistemaCapacidadID') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD SistemaCapacidadID int NULL;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','SistemaVersionID') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD SistemaVersionID uniqueidentifier NULL;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','SucursalID') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD SucursalID int NULL;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','SucursalOrigenID') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD SucursalOrigenID nvarchar(100) NULL;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','CategoriaCodigo') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD CategoriaCodigo nvarchar(100) NULL;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','EntidadCodigo') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD EntidadCodigo nvarchar(100) NULL;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','BlockOrdinal') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD BlockOrdinal int NULL;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','ExecutionOrder') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD ExecutionOrder int NULL;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','PlanJSON') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD PlanJSON nvarchar(max) NULL;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','CheckpointJSON') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD CheckpointJSON nvarchar(max) NULL;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','AttemptCount') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones
        ADD AttemptCount int NOT NULL
            CONSTRAINT DF_Sync_Control_Ejecuciones_AttemptCount DEFAULT (0);

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','MaxAttempts') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones
        ADD MaxAttempts int NOT NULL
            CONSTRAINT DF_Sync_Control_Ejecuciones_MaxAttempts DEFAULT (3);

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','NextRetryAtUTC') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD NextRetryAtUTC datetime2(3) NULL;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','PauseRequested') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones
        ADD PauseRequested bit NOT NULL
            CONSTRAINT DF_Sync_Control_Ejecuciones_PauseRequested DEFAULT (0);

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','CancelRequested') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones
        ADD CancelRequested bit NOT NULL
            CONSTRAINT DF_Sync_Control_Ejecuciones_CancelRequested DEFAULT (0);

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','LastHeartbeatUTC') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD LastHeartbeatUTC datetime2(3) NULL;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','DispatchCount') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones
        ADD DispatchCount int NOT NULL
            CONSTRAINT DF_Sync_Control_Ejecuciones_DispatchCount DEFAULT (0);

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','WorkerJobID') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD WorkerJobID nvarchar(121) NULL;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','RequestedBy') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD RequestedBy nvarchar(320) NULL;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','Reason') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD Reason nvarchar(1000) NULL;

    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','UpdatedAtUTC') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD UpdatedAtUTC datetime2(3) NULL;

    IF NOT EXISTS (
        SELECT 1 FROM sys.foreign_keys
        WHERE name='FK_Sync_Control_Ejecuciones_Parent'
    )
        EXEC(N'
            ALTER TABLE dbo.Sync_Control_Ejecuciones WITH CHECK
            ADD CONSTRAINT FK_Sync_Control_Ejecuciones_Parent
            FOREIGN KEY (ParentSyncControlID)
            REFERENCES dbo.Sync_Control_Ejecuciones(SyncControlID);
        ');

    IF NOT EXISTS (
        SELECT 1 FROM sys.foreign_keys
        WHERE name='FK_Sync_Control_Ejecuciones_SistemaTipo'
    )
        EXEC(N'
            ALTER TABLE dbo.Sync_Control_Ejecuciones WITH CHECK
            ADD CONSTRAINT FK_Sync_Control_Ejecuciones_SistemaTipo
            FOREIGN KEY (SistemaTipoID)
            REFERENCES dbo.Sistema_Tipos(SistemaTipoID);
        ');

    IF NOT EXISTS (
        SELECT 1 FROM sys.foreign_keys
        WHERE name='FK_Sync_Control_Ejecuciones_SistemaCapacidad'
    )
        EXEC(N'
            ALTER TABLE dbo.Sync_Control_Ejecuciones WITH CHECK
            ADD CONSTRAINT FK_Sync_Control_Ejecuciones_SistemaCapacidad
            FOREIGN KEY (SistemaCapacidadID)
            REFERENCES dbo.Sistema_Capacidades(SistemaCapacidadID);
        ');

    IF NOT EXISTS (
        SELECT 1 FROM sys.foreign_keys
        WHERE name='FK_Sync_Control_Ejecuciones_SistemaVersion'
    )
        EXEC(N'
            ALTER TABLE dbo.Sync_Control_Ejecuciones WITH CHECK
            ADD CONSTRAINT FK_Sync_Control_Ejecuciones_SistemaVersion
            FOREIGN KEY (SistemaVersionID)
            REFERENCES dbo.Sistema_VersionesSistemas(sistema_version_id);
        ');

    IF NOT EXISTS (
        SELECT 1 FROM sys.foreign_keys
        WHERE name='FK_Sync_Control_Ejecuciones_Sucursal'
    )
        EXEC(N'
            ALTER TABLE dbo.Sync_Control_Ejecuciones WITH CHECK
            ADD CONSTRAINT FK_Sync_Control_Ejecuciones_Sucursal
            FOREIGN KEY (SucursalID)
            REFERENCES dbo.Sistema_Sucursales(SucursalID);
        ');

    /*
      Los checks e indices referencian columnas agregadas en este mismo batch.
      Se difiere su compilacion hasta despues de materializar las columnas.
    */
    IF NOT EXISTS (
        SELECT 1 FROM sys.check_constraints
        WHERE name='CK_Sync_Control_Ejecuciones_RunKind'
    )
        EXEC(N'
            ALTER TABLE dbo.Sync_Control_Ejecuciones
            ADD CONSTRAINT CK_Sync_Control_Ejecuciones_RunKind
            CHECK (RunKind IN (''LEGACY'',''PARENT'',''ATOMIC''));
        ');

    IF NOT EXISTS (
        SELECT 1 FROM sys.check_constraints
        WHERE name='CK_Sync_Control_Ejecuciones_PlanJSON'
    )
        EXEC(N'
            ALTER TABLE dbo.Sync_Control_Ejecuciones
            ADD CONSTRAINT CK_Sync_Control_Ejecuciones_PlanJSON
            CHECK (PlanJSON IS NULL OR ISJSON(PlanJSON)=1);
        ');

    IF NOT EXISTS (
        SELECT 1 FROM sys.check_constraints
        WHERE name='CK_Sync_Control_Ejecuciones_CheckpointJSON'
    )
        EXEC(N'
            ALTER TABLE dbo.Sync_Control_Ejecuciones
            ADD CONSTRAINT CK_Sync_Control_Ejecuciones_CheckpointJSON
            CHECK (CheckpointJSON IS NULL OR ISJSON(CheckpointJSON)=1);
        ');

    IF NOT EXISTS (
        SELECT 1 FROM sys.check_constraints
        WHERE name='CK_Sync_Control_Ejecuciones_Attempts'
    )
        EXEC(N'
            ALTER TABLE dbo.Sync_Control_Ejecuciones
            ADD CONSTRAINT CK_Sync_Control_Ejecuciones_Attempts
            CHECK (
                AttemptCount >= 0
                AND MaxAttempts >= 1
                AND AttemptCount <= MaxAttempts
            );
        ');

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE object_id=OBJECT_ID('dbo.Sync_Control_Ejecuciones')
          AND name='IX_Sync_Control_Ejecuciones_Parent_Status'
    )
        EXEC(N'
            CREATE INDEX IX_Sync_Control_Ejecuciones_Parent_Status
            ON dbo.Sync_Control_Ejecuciones
                (ParentSyncControlID, Status, ExecutionOrder, BlockOrdinal, SyncControlID)
            INCLUDE (
                SyncRunID, CodigoSync, UnidadNegocioID, ConexionID,
                FechaInicio, FechaFin, AttemptCount, NextRetryAtUTC
            );
        ');

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE object_id=OBJECT_ID('dbo.Sync_Control_Ejecuciones')
          AND name='IX_Sync_Control_Ejecuciones_Correlation'
    )
        EXEC(N'
            CREATE INDEX IX_Sync_Control_Ejecuciones_Correlation
            ON dbo.Sync_Control_Ejecuciones
                (CorrelationID, RunKind, Status, SyncControlID);
        ');

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
