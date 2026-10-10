SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    /*
      EDARSAHUB Production Quality Foundation
      Gate5D1 artifact only.

      Invariants:
      - SQL Server canonical source of truth.
      - No MongoDB.
      - No LIVE dependency.
      - EmpresaID + UnidadNegocioID canonical tenant scope.
      - FechaOperacion persisted on operational facts.
      - Evidence stores metadata only; binaries remain in canonical object storage.
      - Rework / Override represented initially by Production_QualityAction.
    */

    IF OBJECT_ID('dbo.Production_Station', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Production_Station (
            ProductionStationID uniqueidentifier NOT NULL
                CONSTRAINT DF_Production_Station_ID DEFAULT NEWID(),
            EmpresaID int NOT NULL,
            UnidadNegocioID uniqueidentifier NOT NULL,
            ServerID int NULL,
            Codigo varchar(80) NOT NULL,
            Nombre nvarchar(160) NOT NULL,
            Tipo varchar(40) NOT NULL,
            Activo bit NOT NULL
                CONSTRAINT DF_Production_Station_Activo DEFAULT (1),
            CreatedAtUTC datetime2(7) NOT NULL
                CONSTRAINT DF_Production_Station_Created DEFAULT SYSUTCDATETIME(),
            UpdatedAtUTC datetime2(7) NULL,

            CONSTRAINT PK_Production_Station
                PRIMARY KEY (ProductionStationID),

            CONSTRAINT FK_Production_Station_Empresa
                FOREIGN KEY (EmpresaID)
                REFERENCES dbo.Sistema_Empresas(EmpresaID),

            CONSTRAINT FK_Production_Station_Unidad
                FOREIGN KEY (UnidadNegocioID)
                REFERENCES dbo.Unidades_Negocio(id),

            CONSTRAINT UQ_Production_Station_ScopeCode
                UNIQUE (EmpresaID, UnidadNegocioID, Codigo)
        );
    END;

    IF OBJECT_ID('dbo.Production_Item', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Production_Item (
            ProductionItemID uniqueidentifier NOT NULL
                CONSTRAINT DF_Production_Item_ID DEFAULT NEWID(),
            EmpresaID int NOT NULL,
            UnidadNegocioID uniqueidentifier NOT NULL,
            ServerID int NULL,
            FechaOperacion date NOT NULL,
            SourceSystem varchar(40) NOT NULL,
            SourceTransactionID nvarchar(120) NOT NULL,
            SourceLineID nvarchar(120) NOT NULL,
            KDSTicketLineID nvarchar(120) NULL,
            ProductoCodigo nvarchar(100) NULL,
            ProductionStationID uniqueidentifier NULL,
            EstadoProduccion varchar(30) NOT NULL,
            CreatedAtUTC datetime2(7) NOT NULL
                CONSTRAINT DF_Production_Item_Created DEFAULT SYSUTCDATETIME(),
            UpdatedAtUTC datetime2(7) NULL,

            CONSTRAINT PK_Production_Item
                PRIMARY KEY (ProductionItemID),

            CONSTRAINT FK_Production_Item_Empresa
                FOREIGN KEY (EmpresaID)
                REFERENCES dbo.Sistema_Empresas(EmpresaID),

            CONSTRAINT FK_Production_Item_Unidad
                FOREIGN KEY (UnidadNegocioID)
                REFERENCES dbo.Unidades_Negocio(id),

            CONSTRAINT FK_Production_Item_Station
                FOREIGN KEY (ProductionStationID)
                REFERENCES dbo.Production_Station(ProductionStationID),

            CONSTRAINT UQ_Production_Item_Source
                UNIQUE (
                    EmpresaID,
                    UnidadNegocioID,
                    SourceSystem,
                    SourceTransactionID,
                    SourceLineID
                )
        );

        CREATE INDEX IX_Production_Item_FechaOperacion
            ON dbo.Production_Item (
                EmpresaID,
                UnidadNegocioID,
                FechaOperacion
            );
    END;

    IF OBJECT_ID('dbo.Production_QualityStandard', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Production_QualityStandard (
            QualityStandardID uniqueidentifier NOT NULL
                CONSTRAINT DF_Production_QualityStandard_ID DEFAULT NEWID(),
            EmpresaID int NOT NULL,
            UnidadNegocioID uniqueidentifier NULL,
            ProductoCodigo nvarchar(100) NOT NULL,
            Nombre nvarchar(160) NOT NULL,
            Activo bit NOT NULL
                CONSTRAINT DF_Production_QualityStandard_Activo DEFAULT (1),
            CreatedAtUTC datetime2(7) NOT NULL
                CONSTRAINT DF_Production_QualityStandard_Created DEFAULT SYSUTCDATETIME(),
            CreatedByUserID int NULL,

            CONSTRAINT PK_Production_QualityStandard
                PRIMARY KEY (QualityStandardID),

            CONSTRAINT FK_Production_QualityStandard_Empresa
                FOREIGN KEY (EmpresaID)
                REFERENCES dbo.Sistema_Empresas(EmpresaID),

            CONSTRAINT FK_Production_QualityStandard_Unidad
                FOREIGN KEY (UnidadNegocioID)
                REFERENCES dbo.Unidades_Negocio(id),

            CONSTRAINT FK_Production_QualityStandard_User
                FOREIGN KEY (CreatedByUserID)
                REFERENCES dbo.Usuario_Catalogo(UsuarioID)
        );
    END;

    IF OBJECT_ID('dbo.Production_QualityStandardVersion', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Production_QualityStandardVersion (
            QualityStandardVersionID uniqueidentifier NOT NULL
                CONSTRAINT DF_Production_QSV_ID DEFAULT NEWID(),
            QualityStandardID uniqueidentifier NOT NULL,
            VersionNumber int NOT NULL,
            ValidFromUTC datetime2(7) NOT NULL,
            ValidToUTC datetime2(7) NULL,
            Estado varchar(20) NOT NULL,
            PesoObjetivo decimal(18,4) NULL,
            PesoMin decimal(18,4) NULL,
            PesoMax decimal(18,4) NULL,
            TemperaturaMin decimal(18,4) NULL,
            TemperaturaMax decimal(18,4) NULL,
            TiempoMinSegundos int NULL,
            TiempoMaxSegundos int NULL,
            CreatedAtUTC datetime2(7) NOT NULL
                CONSTRAINT DF_Production_QSV_Created DEFAULT SYSUTCDATETIME(),
            CreatedByUserID int NULL,

            CONSTRAINT PK_Production_QualityStandardVersion
                PRIMARY KEY (QualityStandardVersionID),

            CONSTRAINT FK_Production_QSV_Standard
                FOREIGN KEY (QualityStandardID)
                REFERENCES dbo.Production_QualityStandard(QualityStandardID),

            CONSTRAINT FK_Production_QSV_User
                FOREIGN KEY (CreatedByUserID)
                REFERENCES dbo.Usuario_Catalogo(UsuarioID),

            CONSTRAINT UQ_Production_QSV_Version
                UNIQUE (QualityStandardID, VersionNumber),

            CONSTRAINT CK_Production_QSV_Weight
                CHECK (
                    PesoMin IS NULL
                    OR PesoMax IS NULL
                    OR PesoMin <= PesoMax
                ),

            CONSTRAINT CK_Production_QSV_Temperature
                CHECK (
                    TemperaturaMin IS NULL
                    OR TemperaturaMax IS NULL
                    OR TemperaturaMin <= TemperaturaMax
                ),

            CONSTRAINT CK_Production_QSV_Time
                CHECK (
                    TiempoMinSegundos IS NULL
                    OR TiempoMaxSegundos IS NULL
                    OR TiempoMinSegundos <= TiempoMaxSegundos
                )
        );
    END;

    IF OBJECT_ID('dbo.Production_Device', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Production_Device (
            DeviceID uniqueidentifier NOT NULL
                CONSTRAINT DF_Production_Device_ID DEFAULT NEWID(),
            EmpresaID int NOT NULL,
            UnidadNegocioID uniqueidentifier NOT NULL,
            ServerID int NULL,
            ProductionStationID uniqueidentifier NULL,
            DeviceType varchar(30) NOT NULL,
            Codigo varchar(80) NOT NULL,
            Nombre nvarchar(160) NOT NULL,
            AdapterType varchar(60) NULL,
            ConnectionRef nvarchar(240) NULL,
            Estado varchar(30) NOT NULL,
            LastHeartbeatAtUTC datetime2(7) NULL,
            CalibrationRequired bit NOT NULL
                CONSTRAINT DF_Production_Device_CalibrationRequired DEFAULT (0),
            Activo bit NOT NULL
                CONSTRAINT DF_Production_Device_Activo DEFAULT (1),
            CreatedAtUTC datetime2(7) NOT NULL
                CONSTRAINT DF_Production_Device_Created DEFAULT SYSUTCDATETIME(),
            UpdatedAtUTC datetime2(7) NULL,

            CONSTRAINT PK_Production_Device
                PRIMARY KEY (DeviceID),

            CONSTRAINT FK_Production_Device_Empresa
                FOREIGN KEY (EmpresaID)
                REFERENCES dbo.Sistema_Empresas(EmpresaID),

            CONSTRAINT FK_Production_Device_Unidad
                FOREIGN KEY (UnidadNegocioID)
                REFERENCES dbo.Unidades_Negocio(id),

            CONSTRAINT FK_Production_Device_Station
                FOREIGN KEY (ProductionStationID)
                REFERENCES dbo.Production_Station(ProductionStationID),

            CONSTRAINT UQ_Production_Device_ScopeCode
                UNIQUE (EmpresaID, UnidadNegocioID, Codigo)
        );
    END;

    IF OBJECT_ID('dbo.Production_Measurement', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Production_Measurement (
            MeasurementID uniqueidentifier NOT NULL
                CONSTRAINT DF_Production_Measurement_ID DEFAULT NEWID(),
            ProductionItemID uniqueidentifier NOT NULL,
            ProductionStationID uniqueidentifier NULL,
            QualityStandardVersionID uniqueidentifier NULL,
            DeviceID uniqueidentifier NULL,
            EmpresaID int NOT NULL,
            UnidadNegocioID uniqueidentifier NOT NULL,
            FechaOperacion date NOT NULL,
            MeasurementType varchar(30) NOT NULL,
            NumericValue decimal(18,6) NOT NULL,
            UnitCode varchar(30) NOT NULL,
            CapturedAtUTC datetime2(7) NOT NULL,
            OperatorUserID int NULL,
            Source varchar(40) NOT NULL,
            IdempotencyKey varchar(160) NOT NULL,

            CONSTRAINT PK_Production_Measurement
                PRIMARY KEY (MeasurementID),

            CONSTRAINT FK_Production_Measurement_Item
                FOREIGN KEY (ProductionItemID)
                REFERENCES dbo.Production_Item(ProductionItemID),

            CONSTRAINT FK_Production_Measurement_Station
                FOREIGN KEY (ProductionStationID)
                REFERENCES dbo.Production_Station(ProductionStationID),

            CONSTRAINT FK_Production_Measurement_StandardVersion
                FOREIGN KEY (QualityStandardVersionID)
                REFERENCES dbo.Production_QualityStandardVersion(QualityStandardVersionID),

            CONSTRAINT FK_Production_Measurement_Device
                FOREIGN KEY (DeviceID)
                REFERENCES dbo.Production_Device(DeviceID),

            CONSTRAINT FK_Production_Measurement_User
                FOREIGN KEY (OperatorUserID)
                REFERENCES dbo.Usuario_Catalogo(UsuarioID),

            CONSTRAINT UQ_Production_Measurement_Idempotency
                UNIQUE (IdempotencyKey)
        );

        CREATE INDEX IX_Production_Measurement_ItemCaptured
            ON dbo.Production_Measurement (
                ProductionItemID,
                CapturedAtUTC
            );
    END;

    IF OBJECT_ID('dbo.Production_Evidence', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Production_Evidence (
            EvidenceID uniqueidentifier NOT NULL
                CONSTRAINT DF_Production_Evidence_ID DEFAULT NEWID(),
            ProductionItemID uniqueidentifier NOT NULL,
            ProductionStationID uniqueidentifier NULL,
            DeviceID uniqueidentifier NULL,
            EmpresaID int NOT NULL,
            UnidadNegocioID uniqueidentifier NOT NULL,
            FechaOperacion date NOT NULL,
            EvidenceType varchar(30) NOT NULL,
            StoragePath nvarchar(500) NOT NULL,
            ContentType varchar(120) NOT NULL,
            ByteSize bigint NULL,
            ContentHash varchar(128) NOT NULL,
            CapturedAtUTC datetime2(7) NOT NULL,
            OperatorUserID int NULL,
            IdempotencyKey varchar(160) NOT NULL,

            CONSTRAINT PK_Production_Evidence
                PRIMARY KEY (EvidenceID),

            CONSTRAINT FK_Production_Evidence_Item
                FOREIGN KEY (ProductionItemID)
                REFERENCES dbo.Production_Item(ProductionItemID),

            CONSTRAINT FK_Production_Evidence_Station
                FOREIGN KEY (ProductionStationID)
                REFERENCES dbo.Production_Station(ProductionStationID),

            CONSTRAINT FK_Production_Evidence_Device
                FOREIGN KEY (DeviceID)
                REFERENCES dbo.Production_Device(DeviceID),

            CONSTRAINT FK_Production_Evidence_User
                FOREIGN KEY (OperatorUserID)
                REFERENCES dbo.Usuario_Catalogo(UsuarioID),

            CONSTRAINT UQ_Production_Evidence_Idempotency
                UNIQUE (IdempotencyKey)
        );

        CREATE INDEX IX_Production_Evidence_Item
            ON dbo.Production_Evidence (
                ProductionItemID,
                CapturedAtUTC
            );
    END;

    IF OBJECT_ID('dbo.Production_QualityDecision', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Production_QualityDecision (
            QualityDecisionID uniqueidentifier NOT NULL
                CONSTRAINT DF_Production_QD_ID DEFAULT NEWID(),
            ProductionItemID uniqueidentifier NOT NULL,
            QualityStandardVersionID uniqueidentifier NULL,
            Decision varchar(20) NOT NULL,
            ReasonCode varchar(60) NULL,
            ReasonText nvarchar(1000) NULL,
            AttemptNumber int NOT NULL,
            PreviousDecisionID uniqueidentifier NULL,
            EvaluatedAtUTC datetime2(7) NOT NULL,
            EvaluatorUserID int NULL,
            ReleasedAtUTC datetime2(7) NULL,
            IdempotencyKey varchar(160) NOT NULL,

            CONSTRAINT PK_Production_QualityDecision
                PRIMARY KEY (QualityDecisionID),

            CONSTRAINT FK_Production_QD_Item
                FOREIGN KEY (ProductionItemID)
                REFERENCES dbo.Production_Item(ProductionItemID),

            CONSTRAINT FK_Production_QD_StandardVersion
                FOREIGN KEY (QualityStandardVersionID)
                REFERENCES dbo.Production_QualityStandardVersion(QualityStandardVersionID),

            CONSTRAINT FK_Production_QD_Previous
                FOREIGN KEY (PreviousDecisionID)
                REFERENCES dbo.Production_QualityDecision(QualityDecisionID),

            CONSTRAINT FK_Production_QD_User
                FOREIGN KEY (EvaluatorUserID)
                REFERENCES dbo.Usuario_Catalogo(UsuarioID),

            CONSTRAINT UQ_Production_QD_Attempt
                UNIQUE (ProductionItemID, AttemptNumber),

            CONSTRAINT UQ_Production_QD_Idempotency
                UNIQUE (IdempotencyKey),

            CONSTRAINT CK_Production_QD_Decision
                CHECK (Decision IN ('PASS', 'WARNING', 'FAIL'))
        );
    END;

    IF OBJECT_ID('dbo.Production_QualityAction', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Production_QualityAction (
            QualityActionID uniqueidentifier NOT NULL
                CONSTRAINT DF_Production_QA_ID DEFAULT NEWID(),
            ProductionItemID uniqueidentifier NOT NULL,
            QualityDecisionID uniqueidentifier NOT NULL,
            EvidenceID uniqueidentifier NULL,
            ActionType varchar(20) NOT NULL,
            Estado varchar(30) NOT NULL,
            ReasonCode varchar(60) NULL,
            ReasonText nvarchar(1000) NULL,
            RequestedByUserID int NULL,
            ApprovedByUserID int NULL,
            RequestedAtUTC datetime2(7) NOT NULL,
            ApprovedAtUTC datetime2(7) NULL,
            CompletedAtUTC datetime2(7) NULL,
            IdempotencyKey varchar(160) NOT NULL,

            CONSTRAINT PK_Production_QualityAction
                PRIMARY KEY (QualityActionID),

            CONSTRAINT FK_Production_QA_Item
                FOREIGN KEY (ProductionItemID)
                REFERENCES dbo.Production_Item(ProductionItemID),

            CONSTRAINT FK_Production_QA_Decision
                FOREIGN KEY (QualityDecisionID)
                REFERENCES dbo.Production_QualityDecision(QualityDecisionID),

            CONSTRAINT FK_Production_QA_Evidence
                FOREIGN KEY (EvidenceID)
                REFERENCES dbo.Production_Evidence(EvidenceID),

            CONSTRAINT FK_Production_QA_RequestedBy
                FOREIGN KEY (RequestedByUserID)
                REFERENCES dbo.Usuario_Catalogo(UsuarioID),

            CONSTRAINT FK_Production_QA_ApprovedBy
                FOREIGN KEY (ApprovedByUserID)
                REFERENCES dbo.Usuario_Catalogo(UsuarioID),

            CONSTRAINT UQ_Production_QA_Idempotency
                UNIQUE (IdempotencyKey),

            CONSTRAINT CK_Production_QA_Type
                CHECK (ActionType IN ('REWORK', 'OVERRIDE', 'REJECT', 'RELEASE'))
        );
    END;

    IF OBJECT_ID('dbo.Production_DeviceCalibration', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Production_DeviceCalibration (
            DeviceCalibrationID uniqueidentifier NOT NULL
                CONSTRAINT DF_Production_DeviceCalibration_ID DEFAULT NEWID(),
            DeviceID uniqueidentifier NOT NULL,
            EvidenceID uniqueidentifier NULL,
            CalibrationType varchar(40) NOT NULL,
            CalibrationValue decimal(18,6) NULL,
            UnitCode varchar(30) NULL,
            CalibratedAtUTC datetime2(7) NOT NULL,
            ValidUntilUTC datetime2(7) NULL,
            CalibratedByUserID int NULL,
            Notes nvarchar(1000) NULL,

            CONSTRAINT PK_Production_DeviceCalibration
                PRIMARY KEY (DeviceCalibrationID),

            CONSTRAINT FK_Production_DeviceCalibration_Device
                FOREIGN KEY (DeviceID)
                REFERENCES dbo.Production_Device(DeviceID),

            CONSTRAINT FK_Production_DeviceCalibration_Evidence
                FOREIGN KEY (EvidenceID)
                REFERENCES dbo.Production_Evidence(EvidenceID),

            CONSTRAINT FK_Production_DeviceCalibration_User
                FOREIGN KEY (CalibratedByUserID)
                REFERENCES dbo.Usuario_Catalogo(UsuarioID)
        );

        CREATE INDEX IX_Production_DeviceCalibration_DeviceDate
            ON dbo.Production_DeviceCalibration (
                DeviceID,
                CalibratedAtUTC
            );
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
