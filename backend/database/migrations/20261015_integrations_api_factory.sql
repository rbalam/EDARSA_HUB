SET NOCOUNT ON;

IF OBJECT_ID('dbo.Sistema_ApiFactoryApi', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sistema_ApiFactoryApi (
        ApiID UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
        ApiCode NVARCHAR(160) NOT NULL,
        Nombre NVARCHAR(200) NOT NULL,
        Estado NVARCHAR(30) NOT NULL DEFAULT 'DRAFT',
        AuthMode NVARCHAR(30) NOT NULL,
        Activo BIT NOT NULL DEFAULT 1,
        FechaCreacionUTC DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
        FechaActualizacionUTC DATETIME2(0) NULL,
        CONSTRAINT UQ_ApiFactoryApi_Code UNIQUE (ApiCode),
        CONSTRAINT CK_ApiFactoryApi_Estado CHECK (
            Estado IN ('DRAFT','REVIEW','APPROVED','PUBLISHED','SUSPENDED','RETIRED')
        ),
        CONSTRAINT CK_ApiFactoryApi_Auth CHECK (
            AuthMode IN ('OAUTH2','API_KEY','SERVICE_TOKEN')
        )
    );
END;

IF OBJECT_ID('dbo.Sistema_ApiFactoryVersion', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sistema_ApiFactoryVersion (
        ApiVersionID UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
        ApiID UNIQUEIDENTIFIER NOT NULL,
        VersionCode NVARCHAR(50) NOT NULL,
        Route NVARCHAR(300) NOT NULL,
        HttpMethod NVARCHAR(10) NOT NULL,
        ContractFingerprint CHAR(64) NOT NULL,
        InputSchemaVersion NVARCHAR(100) NULL,
        OutputSchemaVersion NVARCHAR(100) NULL,
        RateLimitPerMinute INT NULL,
        Immutable BIT NOT NULL DEFAULT 1,
        Activo BIT NOT NULL DEFAULT 1,
        FechaCreacionUTC DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_ApiFactoryVersion_Api FOREIGN KEY (ApiID)
            REFERENCES dbo.Sistema_ApiFactoryApi(ApiID),
        CONSTRAINT UQ_ApiFactoryVersion UNIQUE (ApiID, VersionCode),
        CONSTRAINT CK_ApiFactoryVersion_Method CHECK (
            HttpMethod IN ('GET','POST','PUT','PATCH','DELETE')
        ),
        CONSTRAINT CK_ApiFactoryVersion_Immutable CHECK (Immutable = 1),
        CONSTRAINT CK_ApiFactoryVersion_Rate CHECK (
            RateLimitPerMinute IS NULL OR RateLimitPerMinute > 0
        )
    );
END;

IF OBJECT_ID('dbo.Sistema_ApiFactoryConsumer', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sistema_ApiFactoryConsumer (
        ConsumerID UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
        ConsumerCode NVARCHAR(160) NOT NULL,
        Nombre NVARCHAR(200) NOT NULL,
        Estado NVARCHAR(30) NOT NULL DEFAULT 'PENDING',
        CredentialReference NVARCHAR(300) NULL,
        Activo BIT NOT NULL DEFAULT 1,
        FechaCreacionUTC DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
        FechaActualizacionUTC DATETIME2(0) NULL,
        CONSTRAINT UQ_ApiFactoryConsumer_Code UNIQUE (ConsumerCode),
        CONSTRAINT CK_ApiFactoryConsumer_Estado CHECK (
            Estado IN ('PENDING','ACTIVE','SUSPENDED','REVOKED')
        )
    );
END;

IF OBJECT_ID('dbo.Sistema_ApiFactoryConsumerGrant', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sistema_ApiFactoryConsumerGrant (
        ConsumerGrantID BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        ConsumerID UNIQUEIDENTIFIER NOT NULL,
        ApiVersionID UNIQUEIDENTIFIER NOT NULL,
        RateLimitPerMinute INT NULL,
        Activo BIT NOT NULL DEFAULT 1,
        FechaCreacionUTC DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_ApiFactoryGrant_Consumer FOREIGN KEY (ConsumerID)
            REFERENCES dbo.Sistema_ApiFactoryConsumer(ConsumerID),
        CONSTRAINT FK_ApiFactoryGrant_Version FOREIGN KEY (ApiVersionID)
            REFERENCES dbo.Sistema_ApiFactoryVersion(ApiVersionID),
        CONSTRAINT UQ_ApiFactoryGrant UNIQUE (ConsumerID, ApiVersionID),
        CONSTRAINT CK_ApiFactoryGrant_Rate CHECK (
            RateLimitPerMinute IS NULL OR RateLimitPerMinute > 0
        )
    );
END;

IF OBJECT_ID('dbo.Sistema_ApiFactoryConsumerEmpresa', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sistema_ApiFactoryConsumerEmpresa (
        ConsumerGrantID BIGINT NOT NULL,
        EmpresaID INT NOT NULL,
        Activo BIT NOT NULL DEFAULT 1,
        FechaCreacionUTC DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_ApiFactoryConsumerEmpresa PRIMARY KEY
            (ConsumerGrantID, EmpresaID),
        CONSTRAINT FK_ApiFactoryConsumerEmpresa_Grant FOREIGN KEY (ConsumerGrantID)
            REFERENCES dbo.Sistema_ApiFactoryConsumerGrant(ConsumerGrantID),
        CONSTRAINT FK_ApiFactoryConsumerEmpresa_Empresa FOREIGN KEY (EmpresaID)
            REFERENCES dbo.Sistema_Empresas(EmpresaID)
    );
END;

IF OBJECT_ID('dbo.Sistema_ApiFactoryConsumerUnidad', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sistema_ApiFactoryConsumerUnidad (
        ConsumerGrantID BIGINT NOT NULL,
        UnidadNegocioID UNIQUEIDENTIFIER NOT NULL,
        Activo BIT NOT NULL DEFAULT 1,
        FechaCreacionUTC DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_ApiFactoryConsumerUnidad PRIMARY KEY
            (ConsumerGrantID, UnidadNegocioID),
        CONSTRAINT FK_ApiFactoryConsumerUnidad_Grant FOREIGN KEY (ConsumerGrantID)
            REFERENCES dbo.Sistema_ApiFactoryConsumerGrant(ConsumerGrantID),
        CONSTRAINT FK_ApiFactoryConsumerUnidad_Unidad FOREIGN KEY (UnidadNegocioID)
            REFERENCES dbo.Unidades_Negocio(id)
    );
END;
