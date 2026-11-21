/*
  EDARSAHUB BOS — GATE-M1: Estado Operativo Canonico SQL del Universal Worker V4
  Archivo: backend/database/migrations/20261120_001_worker_operations_canonical_state.sql

  Reglas:
  - 100% aditivo e idempotente (sin DROP, TRUNCATE ni DELETE).
  - Unica fuente operativa consultable en SQL Server EDARSAHUB (sin colas paralelas).
  - Escritura estrecha exclusivamente via 4 Stored Procedures idempotentes (sp_Worker_*).
  - Reutiliza dbo.Usuario_Catalogo y dbo.Unidades_Negocio sin duplicar catalogos.
  - Produccion prohibida: exige DB_NAME() = 'EDARSAHUB' y ProductionTouched = 0.
*/
SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> N'EDARSAHUB'
    THROW 52000, 'GATE-M1 bloqueado: DB_NAME() debe ser exactamente EDARSAHUB (Desarrollo).', 1;

IF USER_ID(N'HRLectura') IS NULL
    THROW 52001, 'GATE-M1 bloqueado: no existe usuario HRLectura en EDARSAHUB.', 1;

BEGIN TRY
    BEGIN TRANSACTION;

    /* 1. dbo.Sys_Worker_Jobs */
    IF OBJECT_ID(N'dbo.Sys_Worker_Jobs', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Sys_Worker_Jobs (
            JobID varchar(128) NOT NULL,
            SchemaVersion varchar(40) NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_SchemaVersion DEFAULT ('edarsahub.worker-job.v2'),
            SourceJobID varchar(128) NULL,
            ProjectID varchar(100) NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_ProjectID DEFAULT ('UNSPECIFIED'),
            BoundedContext varchar(120) NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_BoundedContext DEFAULT ('UNSPECIFIED'),
            CapabilityCode varchar(120) NULL,
            Mode varchar(40) NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_Mode DEFAULT ('MUTATION'),
            Objective nvarchar(1000) NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_Objective DEFAULT (N''),
            PriorityClass varchar(20) NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_PriorityClass DEFAULT ('NORMAL'),
            RequesterUsuarioID int NULL,
            RequesterEmail varchar(255) NULL,
            RequesterSource varchar(120) NULL,
            OwnerAgentOrDev varchar(120) NULL,
            ChainID varchar(120) NULL,
            GateID varchar(120) NULL,
            DependsOnJobID varchar(128) NULL,
            LifecycleStage varchar(30) NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_LifecycleStage DEFAULT ('SUBMITTED'),
            ExecutionStatus varchar(60) NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_ExecutionStatus DEFAULT ('UNKNOWN'),
            QualityGate varchar(20) NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_QualityGate DEFAULT ('PENDING'),
            TestsStatus varchar(20) NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_TestsStatus DEFAULT ('PENDING'),
            IntegrationStatus varchar(60) NULL,
            GitSyncStatus varchar(60) NULL,
            CertificationStatus varchar(60) NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_CertificationStatus DEFAULT ('NOT_CERTIFIED'),
            OperationalValidationStatus varchar(60) NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_OpValStatus DEFAULT ('PENDING_PREVIEW_VALIDATION'),
            PreviewActivated bit NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_PreviewActivated DEFAULT (0),
            OperationalTests varchar(20) NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_OperationalTests DEFAULT ('NOT_RUN'),
            FunctionalResult varchar(20) NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_FunctionalResult DEFAULT ('UNVERIFIED'),
            TerminalResultValid bit NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_TerminalResultValid DEFAULT (0),
            PercentComplete tinyint NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_PercentComplete DEFAULT (0),
            DevelopmentCommitSHA char(40) NULL,
            PublishedResultCommitSHA char(40) NULL,
            ResultSHA256 char(64) NULL,
            AttestationSHA256 char(64) NULL,
            ProductionTouched bit NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_ProductionTouched DEFAULT (0),
            RecoveryAttempts int NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_RecoveryAttempts DEFAULT (0),
            BlockersJson nvarchar(max) NULL,
            NextRecommendedAction varchar(120) NULL,
            ReconciliationStatus varchar(60) NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_ReconciliationStatus DEFAULT ('PENDING_RECONCILIATION'),
            ProvenanceSource varchar(60) NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_ProvenanceSource DEFAULT ('WORKER_RUNTIME'),
            SubmittedAtUtc datetime2(7) NULL,
            StartedAtUtc datetime2(7) NULL,
            CompletedAtUtc datetime2(7) NULL,
            PublishedAtUtc datetime2(7) NULL,
            UpdatedAtUtc datetime2(7) NOT NULL
                CONSTRAINT DF_Sys_Worker_Jobs_UpdatedAtUtc DEFAULT (SYSUTCDATETIME()),

            CONSTRAINT PK_Sys_Worker_Jobs PRIMARY KEY (JobID),
            CONSTRAINT CK_Sys_Worker_Jobs_PercentComplete CHECK (PercentComplete BETWEEN 0 AND 100),
            CONSTRAINT CK_Sys_Worker_Jobs_ProductionTouched CHECK (ProductionTouched = 0),
            CONSTRAINT CK_Sys_Worker_Jobs_BlockersJson CHECK (BlockersJson IS NULL OR ISJSON(BlockersJson) = 1)
        );
    END;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE object_id = OBJECT_ID(N'dbo.Sys_Worker_Jobs')
          AND name = N'IX_Sys_Worker_Jobs_Project_Domain_Stage'
    )
    BEGIN
        CREATE INDEX IX_Sys_Worker_Jobs_Project_Domain_Stage
            ON dbo.Sys_Worker_Jobs (ProjectID, BoundedContext, LifecycleStage);
    END;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE object_id = OBJECT_ID(N'dbo.Sys_Worker_Jobs')
          AND name = N'IX_Sys_Worker_Jobs_Cert_Updated'
    )
    BEGIN
        CREATE INDEX IX_Sys_Worker_Jobs_Cert_Updated
            ON dbo.Sys_Worker_Jobs (CertificationStatus, UpdatedAtUtc DESC);
    END;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE object_id = OBJECT_ID(N'dbo.Sys_Worker_Jobs')
          AND name = N'IX_Sys_Worker_Jobs_Chain'
    )
    BEGIN
        CREATE INDEX IX_Sys_Worker_Jobs_Chain
            ON dbo.Sys_Worker_Jobs (ChainID, GateID);
    END;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE object_id = OBJECT_ID(N'dbo.Sys_Worker_Jobs')
          AND name = N'IX_Sys_Worker_Jobs_SourceJob'
    )
    BEGIN
        CREATE INDEX IX_Sys_Worker_Jobs_SourceJob
            ON dbo.Sys_Worker_Jobs (SourceJobID);
    END;

    /* 2. dbo.Sys_Worker_Incidents */
    IF OBJECT_ID(N'dbo.Sys_Worker_Incidents', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Sys_Worker_Incidents (
            IncidentID varchar(128) NOT NULL,
            IncidentCategory varchar(60) NOT NULL
                CONSTRAINT DF_Sys_Worker_Incidents_Category DEFAULT ('UNRECONCILED_HISTORICAL_RESULT'),
            ErrorClass varchar(30) NOT NULL
                CONSTRAINT DF_Sys_Worker_Incidents_ErrorClass DEFAULT ('CONTRACTUAL'),
            Severity varchar(20) NOT NULL
                CONSTRAINT DF_Sys_Worker_Incidents_Severity DEFAULT ('MEDIUM'),
            IncidentState varchar(40) NOT NULL
                CONSTRAINT DF_Sys_Worker_Incidents_State DEFAULT ('OPEN'),
            SourceJobID varchar(128) NULL,
            RepairJobID varchar(128) NULL,
            ProjectID varchar(100) NULL,
            BoundedContext varchar(120) NULL,
            ProblemSignature varchar(192) NULL,
            BlockerSignature varchar(255) NULL,
            CapabilityCode varchar(120) NULL,
            RootCause nvarchar(1000) NOT NULL
                CONSTRAINT DF_Sys_Worker_Incidents_RootCause DEFAULT (N'UNCLASSIFIED'),
            ImpactSummary nvarchar(500) NULL,
            OwnerEmail varchar(255) NULL,
            EvidenceRef nvarchar(500) NULL,
            RecommendedAction nvarchar(500) NOT NULL
                CONSTRAINT DF_Sys_Worker_Incidents_Action DEFAULT (N'REVIEW_EVIDENCE'),
            RecoveryAttempts int NOT NULL
                CONSTRAINT DF_Sys_Worker_Incidents_Attempts DEFAULT (0),
            CooldownUntilUtc datetime2(7) NULL,
            AlertNotifiedAtUtc datetime2(7) NULL,
            ProductionTouched bit NOT NULL
                CONSTRAINT DF_Sys_Worker_Incidents_ProductionTouched DEFAULT (0),
            CreatedAtUtc datetime2(7) NOT NULL
                CONSTRAINT DF_Sys_Worker_Incidents_CreatedAtUtc DEFAULT (SYSUTCDATETIME()),
            UpdatedAtUtc datetime2(7) NOT NULL
                CONSTRAINT DF_Sys_Worker_Incidents_UpdatedAtUtc DEFAULT (SYSUTCDATETIME()),

            CONSTRAINT PK_Sys_Worker_Incidents PRIMARY KEY (IncidentID),
            CONSTRAINT CK_Sys_Worker_Incidents_ProductionTouched CHECK (ProductionTouched = 0)
        );
    END;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE object_id = OBJECT_ID(N'dbo.Sys_Worker_Incidents')
          AND name = N'IX_Sys_Worker_Incidents_State_Severity'
    )
    BEGIN
        CREATE INDEX IX_Sys_Worker_Incidents_State_Severity
            ON dbo.Sys_Worker_Incidents (IncidentState, Severity, UpdatedAtUtc DESC);
    END;

    /* 3. dbo.Sys_Worker_RecoveryEvents */
    IF OBJECT_ID(N'dbo.Sys_Worker_RecoveryEvents', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Sys_Worker_RecoveryEvents (
            RecoveryEventID bigint IDENTITY(1,1) NOT NULL,
            IncidentID varchar(128) NOT NULL,
            JobID varchar(128) NULL,
            ActionTaken varchar(80) NOT NULL,
            Outcome varchar(40) NOT NULL,
            PolicyTier varchar(40) NOT NULL
                CONSTRAINT DF_Sys_Worker_RecoveryEvents_PolicyTier DEFAULT ('READ_ONLY'),
            DetailJson nvarchar(max) NULL,
            ProductionTouched bit NOT NULL
                CONSTRAINT DF_Sys_Worker_RecoveryEvents_ProductionTouched DEFAULT (0),
            OccurredAtUtc datetime2(7) NOT NULL
                CONSTRAINT DF_Sys_Worker_RecoveryEvents_OccurredAtUtc DEFAULT (SYSUTCDATETIME()),

            CONSTRAINT PK_Sys_Worker_RecoveryEvents PRIMARY KEY (RecoveryEventID),
            CONSTRAINT FK_Sys_Worker_RecoveryEvents_Incident
                FOREIGN KEY (IncidentID) REFERENCES dbo.Sys_Worker_Incidents (IncidentID),
            CONSTRAINT CK_Sys_Worker_RecoveryEvents_ProductionTouched CHECK (ProductionTouched = 0),
            CONSTRAINT CK_Sys_Worker_RecoveryEvents_DetailJson CHECK (DetailJson IS NULL OR ISJSON(DetailJson) = 1)
        );
    END;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE object_id = OBJECT_ID(N'dbo.Sys_Worker_RecoveryEvents')
          AND name = N'IX_Sys_Worker_RecoveryEvents_Incident_Occurred'
    )
    BEGIN
        CREATE INDEX IX_Sys_Worker_RecoveryEvents_Incident_Occurred
            ON dbo.Sys_Worker_RecoveryEvents (IncidentID, OccurredAtUtc DESC);
    END;

    /* 4. dbo.Sys_Worker_Capabilities */
    IF OBJECT_ID(N'dbo.Sys_Worker_Capabilities', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Sys_Worker_Capabilities (
            CapabilityCode varchar(120) NOT NULL,
            CapabilityKind varchar(40) NOT NULL,
            ProblemSignature varchar(192) NULL,
            AllowedModes varchar(120) NULL,
            BoundedContextRule varchar(120) NULL,
            Reusable bit NOT NULL
                CONSTRAINT DF_Sys_Worker_Capabilities_Reusable DEFAULT (1),
            SourceJobID varchar(128) NULL,
            CertifiedRepairJobID varchar(128) NULL,
            CertifiedCommitSHA char(40) NULL,
            CertificationStatus varchar(60) NOT NULL
                CONSTRAINT DF_Sys_Worker_Capabilities_CertStatus DEFAULT ('CERTIFIED'),
            OperationalValidationStatus varchar(60) NOT NULL
                CONSTRAINT DF_Sys_Worker_Capabilities_OpValStatus DEFAULT ('NOT_APPLICABLE'),
            RootCause nvarchar(1000) NULL,
            PreventionRule nvarchar(1000) NULL,
            ProductionTouched bit NOT NULL
                CONSTRAINT DF_Sys_Worker_Capabilities_ProductionTouched DEFAULT (0),
            UpdatedAtUtc datetime2(7) NOT NULL
                CONSTRAINT DF_Sys_Worker_Capabilities_UpdatedAtUtc DEFAULT (SYSUTCDATETIME()),

            CONSTRAINT PK_Sys_Worker_Capabilities PRIMARY KEY (CapabilityCode),
            CONSTRAINT CK_Sys_Worker_Capabilities_ProductionTouched CHECK (ProductionTouched = 0)
        );
    END;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE object_id = OBJECT_ID(N'dbo.Sys_Worker_Capabilities')
          AND name = N'IX_Sys_Worker_Capabilities_Kind_Cert'
    )
    BEGIN
        CREATE INDEX IX_Sys_Worker_Capabilities_Kind_Cert
            ON dbo.Sys_Worker_Capabilities (CapabilityKind, CertificationStatus);
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO

CREATE OR ALTER PROCEDURE dbo.sp_Worker_UpsertJobState
    @JobID varchar(128),
    @SchemaVersion varchar(40) = 'edarsahub.worker-job.v2',
    @SourceJobID varchar(128) = NULL,
    @ProjectID varchar(100) = 'UNSPECIFIED',
    @BoundedContext varchar(120) = 'UNSPECIFIED',
    @CapabilityCode varchar(120) = NULL,
    @Mode varchar(40) = 'MUTATION',
    @Objective nvarchar(1000) = N'',
    @PriorityClass varchar(20) = 'NORMAL',
    @RequesterUsuarioID int = NULL,
    @RequesterEmail varchar(255) = NULL,
    @RequesterSource varchar(120) = NULL,
    @OwnerAgentOrDev varchar(120) = NULL,
    @ChainID varchar(120) = NULL,
    @GateID varchar(120) = NULL,
    @DependsOnJobID varchar(128) = NULL,
    @LifecycleStage varchar(30) = 'SUBMITTED',
    @ExecutionStatus varchar(60) = 'UNKNOWN',
    @QualityGate varchar(20) = 'PENDING',
    @TestsStatus varchar(20) = 'PENDING',
    @IntegrationStatus varchar(60) = NULL,
    @GitSyncStatus varchar(60) = NULL,
    @CertificationStatus varchar(60) = 'NOT_CERTIFIED',
    @OperationalValidationStatus varchar(60) = 'PENDING_PREVIEW_VALIDATION',
    @PreviewActivated bit = 0,
    @OperationalTests varchar(20) = 'NOT_RUN',
    @FunctionalResult varchar(20) = 'UNVERIFIED',
    @TerminalResultValid bit = 0,
    @PercentComplete tinyint = 0,
    @DevelopmentCommitSHA char(40) = NULL,
    @PublishedResultCommitSHA char(40) = NULL,
    @ResultSHA256 char(64) = NULL,
    @AttestationSHA256 char(64) = NULL,
    @ProductionTouched bit = 0,
    @RecoveryAttempts int = 0,
    @BlockersJson nvarchar(max) = NULL,
    @NextRecommendedAction varchar(120) = NULL,
    @ReconciliationStatus varchar(60) = 'PENDING_RECONCILIATION',
    @ProvenanceSource varchar(60) = 'WORKER_RUNTIME',
    @SubmittedAtUtc datetime2(7) = NULL,
    @StartedAtUtc datetime2(7) = NULL,
    @CompletedAtUtc datetime2(7) = NULL,
    @PublishedAtUtc datetime2(7) = NULL,
    @AllowDowngrade bit = 0
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    SET @JobID = LTRIM(RTRIM(@JobID));
    IF @JobID IS NULL OR @JobID = ''
        THROW 52010, 'JobID requerido en sp_Worker_UpsertJobState.', 1;

    IF @ProductionTouched <> 0
        THROW 52011, 'ProductionTouched=1 prohibido en dbo.Sys_Worker_Jobs.', 1;

    IF @BlockersJson IS NOT NULL AND ISJSON(@BlockersJson) <> 1
        THROW 52012, 'BlockersJson invalido en sp_Worker_UpsertJobState.', 1;

    DECLARE @ExistingCert varchar(60);
    DECLARE @ExistingStage varchar(30);

    SELECT
        @ExistingCert = CertificationStatus,
        @ExistingStage = LifecycleStage
    FROM dbo.Sys_Worker_Jobs
    WHERE JobID = @JobID;

    IF @ExistingCert IS NOT NULL
    BEGIN
        /* Monotonicidad fail-closed: nunca degradar un job ya CERTIFIED salvo @AllowDowngrade = 1 */
        IF @AllowDowngrade = 0
           AND @ExistingCert IN ('CERTIFIED', 'CERTIFIED_READ_ONLY', 'CERTIFIED_OPERATIONAL', 'CERTIFIED_FRONTEND_BUILD')
           AND @CertificationStatus NOT IN ('CERTIFIED', 'CERTIFIED_READ_ONLY', 'CERTIFIED_OPERATIONAL', 'CERTIFIED_FRONTEND_BUILD')
        BEGIN
            RETURN;
        END;

        IF @AllowDowngrade = 0
           AND @ExistingStage = 'ACTIVE_IN_PREVIEW'
           AND @LifecycleStage <> 'ACTIVE_IN_PREVIEW'
        BEGIN
            SET @LifecycleStage = 'ACTIVE_IN_PREVIEW';
            SET @OperationalValidationStatus = 'ACTIVE_IN_PREVIEW';
            SET @PreviewActivated = 1;
        END;

        UPDATE dbo.Sys_Worker_Jobs
        SET
            SchemaVersion = COALESCE(NULLIF(@SchemaVersion, ''), SchemaVersion),
            SourceJobID = COALESCE(@SourceJobID, SourceJobID),
            ProjectID = CASE WHEN NULLIF(@ProjectID, '') IS NOT NULL AND @ProjectID <> 'UNSPECIFIED' THEN @ProjectID ELSE ProjectID END,
            BoundedContext = CASE WHEN NULLIF(@BoundedContext, '') IS NOT NULL AND @BoundedContext <> 'UNSPECIFIED' THEN @BoundedContext ELSE BoundedContext END,
            CapabilityCode = COALESCE(@CapabilityCode, CapabilityCode),
            Mode = COALESCE(NULLIF(@Mode, ''), Mode),
            Objective = CASE WHEN NULLIF(@Objective, N'') IS NOT NULL THEN @Objective ELSE Objective END,
            PriorityClass = COALESCE(NULLIF(@PriorityClass, ''), PriorityClass),
            RequesterUsuarioID = COALESCE(@RequesterUsuarioID, RequesterUsuarioID),
            RequesterEmail = COALESCE(@RequesterEmail, RequesterEmail),
            RequesterSource = COALESCE(@RequesterSource, RequesterSource),
            OwnerAgentOrDev = COALESCE(@OwnerAgentOrDev, OwnerAgentOrDev),
            ChainID = COALESCE(@ChainID, ChainID),
            GateID = COALESCE(@GateID, GateID),
            DependsOnJobID = COALESCE(@DependsOnJobID, DependsOnJobID),
            LifecycleStage = @LifecycleStage,
            ExecutionStatus = @ExecutionStatus,
            QualityGate = @QualityGate,
            TestsStatus = @TestsStatus,
            IntegrationStatus = COALESCE(@IntegrationStatus, IntegrationStatus),
            GitSyncStatus = COALESCE(@GitSyncStatus, GitSyncStatus),
            CertificationStatus = @CertificationStatus,
            OperationalValidationStatus = @OperationalValidationStatus,
            PreviewActivated = @PreviewActivated,
            OperationalTests = @OperationalTests,
            FunctionalResult = @FunctionalResult,
            TerminalResultValid = @TerminalResultValid,
            PercentComplete = @PercentComplete,
            DevelopmentCommitSHA = COALESCE(@DevelopmentCommitSHA, DevelopmentCommitSHA),
            PublishedResultCommitSHA = COALESCE(@PublishedResultCommitSHA, PublishedResultCommitSHA),
            ResultSHA256 = COALESCE(@ResultSHA256, ResultSHA256),
            AttestationSHA256 = COALESCE(@AttestationSHA256, AttestationSHA256),
            RecoveryAttempts = CASE WHEN @RecoveryAttempts > RecoveryAttempts THEN @RecoveryAttempts ELSE RecoveryAttempts END,
            BlockersJson = COALESCE(@BlockersJson, BlockersJson),
            NextRecommendedAction = COALESCE(@NextRecommendedAction, NextRecommendedAction),
            ReconciliationStatus = @ReconciliationStatus,
            ProvenanceSource = @ProvenanceSource,
            SubmittedAtUtc = COALESCE(@SubmittedAtUtc, SubmittedAtUtc),
            StartedAtUtc = COALESCE(@StartedAtUtc, StartedAtUtc),
            CompletedAtUtc = COALESCE(@CompletedAtUtc, CompletedAtUtc),
            PublishedAtUtc = COALESCE(@PublishedAtUtc, PublishedAtUtc),
            UpdatedAtUtc = SYSUTCDATETIME()
        WHERE JobID = @JobID;
    END
    ELSE
    BEGIN
        INSERT INTO dbo.Sys_Worker_Jobs (
            JobID, SchemaVersion, SourceJobID, ProjectID, BoundedContext, CapabilityCode,
            Mode, Objective, PriorityClass, RequesterUsuarioID, RequesterEmail, RequesterSource,
            OwnerAgentOrDev, ChainID, GateID, DependsOnJobID, LifecycleStage, ExecutionStatus,
            QualityGate, TestsStatus, IntegrationStatus, GitSyncStatus, CertificationStatus,
            OperationalValidationStatus, PreviewActivated, OperationalTests, FunctionalResult,
            TerminalResultValid, PercentComplete, DevelopmentCommitSHA, PublishedResultCommitSHA,
            ResultSHA256, AttestationSHA256, ProductionTouched, RecoveryAttempts, BlockersJson,
            NextRecommendedAction, ReconciliationStatus, ProvenanceSource,
            SubmittedAtUtc, StartedAtUtc, CompletedAtUtc, PublishedAtUtc, UpdatedAtUtc
        )
        VALUES (
            @JobID, ISNULL(NULLIF(@SchemaVersion, ''), 'edarsahub.worker-job.v2'), @SourceJobID,
            ISNULL(NULLIF(@ProjectID, ''), 'UNSPECIFIED'), ISNULL(NULLIF(@BoundedContext, ''), 'UNSPECIFIED'),
            @CapabilityCode, ISNULL(NULLIF(@Mode, ''), 'MUTATION'), ISNULL(@Objective, N''),
            ISNULL(NULLIF(@PriorityClass, ''), 'NORMAL'), @RequesterUsuarioID, @RequesterEmail,
            @RequesterSource, @OwnerAgentOrDev, @ChainID, @GateID, @DependsOnJobID,
            @LifecycleStage, @ExecutionStatus, @QualityGate, @TestsStatus, @IntegrationStatus,
            @GitSyncStatus, @CertificationStatus, @OperationalValidationStatus, @PreviewActivated,
            @OperationalTests, @FunctionalResult, @TerminalResultValid, @PercentComplete,
            @DevelopmentCommitSHA, @PublishedResultCommitSHA, @ResultSHA256, @AttestationSHA256,
            0, ISNULL(@RecoveryAttempts, 0), @BlockersJson, @NextRecommendedAction,
            @ReconciliationStatus, @ProvenanceSource,
            @SubmittedAtUtc, @StartedAtUtc, @CompletedAtUtc, @PublishedAtUtc, SYSUTCDATETIME()
        );
    END;
END;
GO

CREATE OR ALTER PROCEDURE dbo.sp_Worker_UpsertIncident
    @IncidentID varchar(128),
    @IncidentCategory varchar(60) = 'UNRECONCILED_HISTORICAL_RESULT',
    @ErrorClass varchar(30) = 'CONTRACTUAL',
    @Severity varchar(20) = 'MEDIUM',
    @IncidentState varchar(40) = 'OPEN',
    @SourceJobID varchar(128) = NULL,
    @RepairJobID varchar(128) = NULL,
    @ProjectID varchar(100) = NULL,
    @BoundedContext varchar(120) = NULL,
    @ProblemSignature varchar(192) = NULL,
    @BlockerSignature varchar(255) = NULL,
    @CapabilityCode varchar(120) = NULL,
    @RootCause nvarchar(1000) = N'UNCLASSIFIED',
    @ImpactSummary nvarchar(500) = NULL,
    @OwnerEmail varchar(255) = NULL,
    @EvidenceRef nvarchar(500) = NULL,
    @RecommendedAction nvarchar(500) = N'REVIEW_EVIDENCE',
    @RecoveryAttempts int = 0,
    @CooldownUntilUtc datetime2(7) = NULL,
    @ProductionTouched bit = 0
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    SET @IncidentID = LTRIM(RTRIM(@IncidentID));
    IF @IncidentID IS NULL OR @IncidentID = ''
        THROW 52020, 'IncidentID requerido en sp_Worker_UpsertIncident.', 1;

    IF @ProductionTouched <> 0
        THROW 52021, 'ProductionTouched=1 prohibido en dbo.Sys_Worker_Incidents.', 1;

    IF EXISTS (SELECT 1 FROM dbo.Sys_Worker_Incidents WHERE IncidentID = @IncidentID)
    BEGIN
        UPDATE dbo.Sys_Worker_Incidents
        SET
            IncidentCategory = @IncidentCategory,
            ErrorClass = @ErrorClass,
            Severity = @Severity,
            IncidentState = @IncidentState,
            SourceJobID = COALESCE(@SourceJobID, SourceJobID),
            RepairJobID = COALESCE(@RepairJobID, RepairJobID),
            ProjectID = COALESCE(@ProjectID, ProjectID),
            BoundedContext = COALESCE(@BoundedContext, BoundedContext),
            ProblemSignature = COALESCE(@ProblemSignature, ProblemSignature),
            BlockerSignature = COALESCE(@BlockerSignature, BlockerSignature),
            CapabilityCode = COALESCE(@CapabilityCode, CapabilityCode),
            RootCause = COALESCE(NULLIF(@RootCause, N''), RootCause),
            ImpactSummary = COALESCE(@ImpactSummary, ImpactSummary),
            OwnerEmail = COALESCE(@OwnerEmail, OwnerEmail),
            EvidenceRef = COALESCE(@EvidenceRef, EvidenceRef),
            RecommendedAction = COALESCE(NULLIF(@RecommendedAction, N''), RecommendedAction),
            RecoveryAttempts = CASE WHEN @RecoveryAttempts > RecoveryAttempts THEN @RecoveryAttempts ELSE RecoveryAttempts END,
            CooldownUntilUtc = COALESCE(@CooldownUntilUtc, CooldownUntilUtc),
            UpdatedAtUtc = SYSUTCDATETIME()
        WHERE IncidentID = @IncidentID;
    END
    ELSE
    BEGIN
        INSERT INTO dbo.Sys_Worker_Incidents (
            IncidentID, IncidentCategory, ErrorClass, Severity, IncidentState,
            SourceJobID, RepairJobID, ProjectID, BoundedContext,
            ProblemSignature, BlockerSignature, CapabilityCode,
            RootCause, ImpactSummary, OwnerEmail, EvidenceRef, RecommendedAction,
            RecoveryAttempts, CooldownUntilUtc, ProductionTouched, CreatedAtUtc, UpdatedAtUtc
        )
        VALUES (
            @IncidentID, @IncidentCategory, @ErrorClass, @Severity, @IncidentState,
            @SourceJobID, @RepairJobID, @ProjectID, @BoundedContext,
            @ProblemSignature, @BlockerSignature, @CapabilityCode,
            ISNULL(NULLIF(@RootCause, N''), N'UNCLASSIFIED'), @ImpactSummary, @OwnerEmail,
            @EvidenceRef, ISNULL(NULLIF(@RecommendedAction, N''), N'REVIEW_EVIDENCE'),
            ISNULL(@RecoveryAttempts, 0), @CooldownUntilUtc, 0, SYSUTCDATETIME(), SYSUTCDATETIME()
        );
    END;
END;
GO

CREATE OR ALTER PROCEDURE dbo.sp_Worker_RecordRecoveryEvent
    @IncidentID varchar(128),
    @JobID varchar(128) = NULL,
    @ActionTaken varchar(80),
    @Outcome varchar(40),
    @PolicyTier varchar(40) = 'READ_ONLY',
    @DetailJson nvarchar(max) = NULL,
    @ProductionTouched bit = 0
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    SET @IncidentID = LTRIM(RTRIM(@IncidentID));
    IF @IncidentID IS NULL OR @IncidentID = ''
        THROW 52030, 'IncidentID requerido en sp_Worker_RecordRecoveryEvent.', 1;

    IF @ProductionTouched <> 0
        THROW 52031, 'ProductionTouched=1 prohibido en dbo.Sys_Worker_RecoveryEvents.', 1;

    IF @DetailJson IS NOT NULL AND ISJSON(@DetailJson) <> 1
        THROW 52032, 'DetailJson invalido en sp_Worker_RecordRecoveryEvent.', 1;

    IF NOT EXISTS (SELECT 1 FROM dbo.Sys_Worker_Incidents WHERE IncidentID = @IncidentID)
        THROW 52033, 'IncidentID inexistente en dbo.Sys_Worker_Incidents.', 1;

    INSERT INTO dbo.Sys_Worker_RecoveryEvents (
        IncidentID, JobID, ActionTaken, Outcome, PolicyTier,
        DetailJson, ProductionTouched, OccurredAtUtc
    )
    VALUES (
        @IncidentID, @JobID, @ActionTaken, @Outcome, @PolicyTier,
        @DetailJson, 0, SYSUTCDATETIME()
    );
END;
GO

CREATE OR ALTER PROCEDURE dbo.sp_Worker_UpsertCapability
    @CapabilityCode varchar(120),
    @CapabilityKind varchar(40),
    @ProblemSignature varchar(192) = NULL,
    @AllowedModes varchar(120) = NULL,
    @BoundedContextRule varchar(120) = NULL,
    @Reusable bit = 1,
    @SourceJobID varchar(128) = NULL,
    @CertifiedRepairJobID varchar(128) = NULL,
    @CertifiedCommitSHA char(40) = NULL,
    @CertificationStatus varchar(60) = 'CERTIFIED',
    @OperationalValidationStatus varchar(60) = 'NOT_APPLICABLE',
    @RootCause nvarchar(1000) = NULL,
    @PreventionRule nvarchar(1000) = NULL,
    @ProductionTouched bit = 0
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    SET @CapabilityCode = LTRIM(RTRIM(@CapabilityCode));
    IF @CapabilityCode IS NULL OR @CapabilityCode = ''
        THROW 52040, 'CapabilityCode requerido en sp_Worker_UpsertCapability.', 1;

    IF @ProductionTouched <> 0
        THROW 52041, 'ProductionTouched=1 prohibido en dbo.Sys_Worker_Capabilities.', 1;

    IF EXISTS (SELECT 1 FROM dbo.Sys_Worker_Capabilities WHERE CapabilityCode = @CapabilityCode)
    BEGIN
        UPDATE dbo.Sys_Worker_Capabilities
        SET
            CapabilityKind = @CapabilityKind,
            ProblemSignature = COALESCE(@ProblemSignature, ProblemSignature),
            AllowedModes = COALESCE(@AllowedModes, AllowedModes),
            BoundedContextRule = COALESCE(@BoundedContextRule, BoundedContextRule),
            Reusable = @Reusable,
            SourceJobID = COALESCE(@SourceJobID, SourceJobID),
            CertifiedRepairJobID = COALESCE(@CertifiedRepairJobID, CertifiedRepairJobID),
            CertifiedCommitSHA = COALESCE(@CertifiedCommitSHA, CertifiedCommitSHA),
            CertificationStatus = @CertificationStatus,
            OperationalValidationStatus = @OperationalValidationStatus,
            RootCause = COALESCE(@RootCause, RootCause),
            PreventionRule = COALESCE(@PreventionRule, PreventionRule),
            UpdatedAtUtc = SYSUTCDATETIME()
        WHERE CapabilityCode = @CapabilityCode;
    END
    ELSE
    BEGIN
        INSERT INTO dbo.Sys_Worker_Capabilities (
            CapabilityCode, CapabilityKind, ProblemSignature, AllowedModes,
            BoundedContextRule, Reusable, SourceJobID, CertifiedRepairJobID,
            CertifiedCommitSHA, CertificationStatus, OperationalValidationStatus,
            RootCause, PreventionRule, ProductionTouched, UpdatedAtUtc
        )
        VALUES (
            @CapabilityCode, @CapabilityKind, @ProblemSignature, @AllowedModes,
            @BoundedContextRule, @Reusable, @SourceJobID, @CertifiedRepairJobID,
            @CertifiedCommitSHA, @CertificationStatus, @OperationalValidationStatus,
            @RootCause, @PreventionRule, 0, SYSUTCDATETIME()
        );
    END;
END;
GO

GRANT SELECT ON OBJECT::dbo.Sys_Worker_Jobs TO HRLectura;
GRANT SELECT ON OBJECT::dbo.Sys_Worker_Incidents TO HRLectura;
GRANT SELECT ON OBJECT::dbo.Sys_Worker_RecoveryEvents TO HRLectura;
GRANT SELECT ON OBJECT::dbo.Sys_Worker_Capabilities TO HRLectura;

GRANT EXECUTE ON OBJECT::dbo.sp_Worker_UpsertJobState TO HRLectura;
GRANT EXECUTE ON OBJECT::dbo.sp_Worker_UpsertIncident TO HRLectura;
GRANT EXECUTE ON OBJECT::dbo.sp_Worker_RecordRecoveryEvent TO HRLectura;
GRANT EXECUTE ON OBJECT::dbo.sp_Worker_UpsertCapability TO HRLectura;
GO
