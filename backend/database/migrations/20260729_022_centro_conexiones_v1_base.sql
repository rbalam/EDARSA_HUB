/*
EDARSAHUB - Centro de Conexiones V1.0
Migracion aditiva e idempotente.

Principios:
- dbo.Servidores_Conexiones permanece como registro compatible existente.
- Los proveedores, categorias, adaptadores y clasificaciones son catalogos administrables.
- No se insertan proveedores ni valores funcionales hardcodeados.
- El frontend y los servicios deben consumir los catalogos SQL.
- No se ejecuta cutover ni se eliminan contratos legacy.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRANSACTION;

IF OBJECT_ID('dbo.Integration_ConnectionCategory', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Integration_ConnectionCategory (
        category_code       varchar(50)     NOT NULL,
        category_name       nvarchar(120)   NOT NULL,
        description         nvarchar(500)   NULL,
        display_order       int             NOT NULL,
        enabled             bit             NOT NULL,
        created_at          datetime2(0)    NOT NULL CONSTRAINT DF_Integration_Category_Created DEFAULT (SYSDATETIME()),
        updated_at          datetime2(0)    NOT NULL CONSTRAINT DF_Integration_Category_Updated DEFAULT (SYSDATETIME()),
        created_by          nvarchar(150)   NULL,
        updated_by          nvarchar(150)   NULL,
        row_version         rowversion      NOT NULL,
        CONSTRAINT PK_Integration_ConnectionCategory PRIMARY KEY (category_code),
        CONSTRAINT UQ_Integration_ConnectionCategory_Name UNIQUE (category_name)
    );
END;

IF OBJECT_ID('dbo.Integration_AdapterDefinition', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Integration_AdapterDefinition (
        adapter_code        varchar(80)     NOT NULL,
        adapter_name        nvarchar(160)   NOT NULL,
        implementation_key  nvarchar(250)   NOT NULL,
        description         nvarchar(500)   NULL,
        capability_json     nvarchar(max)   NULL,
        enabled             bit             NOT NULL,
        created_at          datetime2(0)    NOT NULL CONSTRAINT DF_Integration_Adapter_Created DEFAULT (SYSDATETIME()),
        updated_at          datetime2(0)    NOT NULL CONSTRAINT DF_Integration_Adapter_Updated DEFAULT (SYSDATETIME()),
        created_by          nvarchar(150)   NULL,
        updated_by          nvarchar(150)   NULL,
        row_version         rowversion      NOT NULL,
        CONSTRAINT PK_Integration_AdapterDefinition PRIMARY KEY (adapter_code),
        CONSTRAINT UQ_Integration_AdapterDefinition_Name UNIQUE (adapter_name),
        CONSTRAINT UQ_Integration_AdapterDefinition_Implementation UNIQUE (implementation_key),
        CONSTRAINT CK_Integration_Adapter_CapabilityJson CHECK (capability_json IS NULL OR ISJSON(capability_json) = 1)
    );
END;

IF OBJECT_ID('dbo.Integration_AuthType', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Integration_AuthType (
        auth_type_code      varchar(50)     NOT NULL,
        auth_type_name      nvarchar(120)   NOT NULL,
        field_schema_json   nvarchar(max)   NULL,
        enabled             bit             NOT NULL,
        display_order       int             NOT NULL,
        created_at          datetime2(0)    NOT NULL CONSTRAINT DF_Integration_AuthType_Created DEFAULT (SYSDATETIME()),
        updated_at          datetime2(0)    NOT NULL CONSTRAINT DF_Integration_AuthType_Updated DEFAULT (SYSDATETIME()),
        CONSTRAINT PK_Integration_AuthType PRIMARY KEY (auth_type_code),
        CONSTRAINT UQ_Integration_AuthType_Name UNIQUE (auth_type_name),
        CONSTRAINT CK_Integration_AuthType_FieldsJson CHECK (field_schema_json IS NULL OR ISJSON(field_schema_json) = 1)
    );
END;

IF OBJECT_ID('dbo.Integration_Environment', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Integration_Environment (
        environment_code    varchar(30)     NOT NULL,
        environment_name    nvarchar(100)   NOT NULL,
        display_order       int             NOT NULL,
        enabled             bit             NOT NULL,
        CONSTRAINT PK_Integration_Environment PRIMARY KEY (environment_code),
        CONSTRAINT UQ_Integration_Environment_Name UNIQUE (environment_name)
    );
END;

IF OBJECT_ID('dbo.Integration_ConnectionStatus', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Integration_ConnectionStatus (
        status_code         varchar(30)     NOT NULL,
        status_name         nvarchar(100)   NOT NULL,
        is_operational      bit             NOT NULL,
        display_order       int             NOT NULL,
        enabled             bit             NOT NULL,
        CONSTRAINT PK_Integration_ConnectionStatus PRIMARY KEY (status_code),
        CONSTRAINT UQ_Integration_ConnectionStatus_Name UNIQUE (status_name)
    );
END;

IF OBJECT_ID('dbo.Integration_Criticality', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Integration_Criticality (
        criticality_code    varchar(30)     NOT NULL,
        criticality_name    nvarchar(100)   NOT NULL,
        display_order       int             NOT NULL,
        enabled             bit             NOT NULL,
        CONSTRAINT PK_Integration_Criticality PRIMARY KEY (criticality_code),
        CONSTRAINT UQ_Integration_Criticality_Name UNIQUE (criticality_name)
    );
END;

IF OBJECT_ID('dbo.Integration_ScopeType', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Integration_ScopeType (
        scope_type_code     varchar(30)     NOT NULL,
        scope_type_name     nvarchar(100)   NOT NULL,
        allows_company      bit             NOT NULL,
        allows_business_unit bit            NOT NULL,
        allows_external_asset bit           NOT NULL,
        display_order       int             NOT NULL,
        enabled             bit             NOT NULL,
        CONSTRAINT PK_Integration_ScopeType PRIMARY KEY (scope_type_code),
        CONSTRAINT UQ_Integration_ScopeType_Name UNIQUE (scope_type_name)
    );
END;

IF OBJECT_ID('dbo.Integration_ProviderDefinition', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Integration_ProviderDefinition (
        provider_code       varchar(80)     NOT NULL,
        provider_name       nvarchar(160)   NOT NULL,
        category_code       varchar(50)     NOT NULL,
        adapter_code        varchar(80)     NOT NULL,
        auth_type_code      varchar(50)     NULL,
        config_schema_json  nvarchar(max)   NULL,
        supports_read       bit             NOT NULL,
        supports_write      bit             NOT NULL,
        supports_discovery  bit             NOT NULL,
        supports_sync       bit             NOT NULL,
        enabled             bit             NOT NULL,
        display_order       int             NOT NULL,
        created_at          datetime2(0)    NOT NULL CONSTRAINT DF_Integration_Provider_Created DEFAULT (SYSDATETIME()),
        updated_at          datetime2(0)    NOT NULL CONSTRAINT DF_Integration_Provider_Updated DEFAULT (SYSDATETIME()),
        created_by          nvarchar(150)   NULL,
        updated_by          nvarchar(150)   NULL,
        row_version         rowversion      NOT NULL,
        CONSTRAINT PK_Integration_ProviderDefinition PRIMARY KEY (provider_code),
        CONSTRAINT UQ_Integration_ProviderDefinition_Name UNIQUE (provider_name),
        CONSTRAINT FK_Integration_Provider_Category FOREIGN KEY (category_code)
            REFERENCES dbo.Integration_ConnectionCategory(category_code),
        CONSTRAINT FK_Integration_Provider_Adapter FOREIGN KEY (adapter_code)
            REFERENCES dbo.Integration_AdapterDefinition(adapter_code),
        CONSTRAINT FK_Integration_Provider_AuthType FOREIGN KEY (auth_type_code)
            REFERENCES dbo.Integration_AuthType(auth_type_code),
        CONSTRAINT CK_Integration_Provider_ConfigJson CHECK (config_schema_json IS NULL OR ISJSON(config_schema_json) = 1)
    );
END;

IF OBJECT_ID('dbo.Integration_ConnectionMetadata', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Integration_ConnectionMetadata (
        connection_id        uniqueidentifier NOT NULL,
        provider_code        varchar(80)      NOT NULL,
        environment_code     varchar(30)      NOT NULL,
        status_code          varchar(30)      NOT NULL,
        auth_type_code       varchar(50)      NULL,
        owner_user_id        nvarchar(120)    NULL,
        support_team         nvarchar(120)    NULL,
        criticality_code     varchar(30)      NOT NULL,
        provider_config_json nvarchar(max)    NULL,
        current_version      int              NOT NULL,
        created_at           datetime2(0)     NOT NULL CONSTRAINT DF_Integration_Metadata_Created DEFAULT (SYSDATETIME()),
        updated_at           datetime2(0)     NOT NULL CONSTRAINT DF_Integration_Metadata_Updated DEFAULT (SYSDATETIME()),
        created_by           nvarchar(150)    NULL,
        updated_by           nvarchar(150)    NULL,
        row_version          rowversion       NOT NULL,
        CONSTRAINT PK_Integration_ConnectionMetadata PRIMARY KEY (connection_id),
        CONSTRAINT FK_Integration_Metadata_Connection FOREIGN KEY (connection_id)
            REFERENCES dbo.Servidores_Conexiones(id),
        CONSTRAINT FK_Integration_Metadata_Provider FOREIGN KEY (provider_code)
            REFERENCES dbo.Integration_ProviderDefinition(provider_code),
        CONSTRAINT FK_Integration_Metadata_Environment FOREIGN KEY (environment_code)
            REFERENCES dbo.Integration_Environment(environment_code),
        CONSTRAINT FK_Integration_Metadata_Status FOREIGN KEY (status_code)
            REFERENCES dbo.Integration_ConnectionStatus(status_code),
        CONSTRAINT FK_Integration_Metadata_AuthType FOREIGN KEY (auth_type_code)
            REFERENCES dbo.Integration_AuthType(auth_type_code),
        CONSTRAINT FK_Integration_Metadata_Criticality FOREIGN KEY (criticality_code)
            REFERENCES dbo.Integration_Criticality(criticality_code),
        CONSTRAINT CK_Integration_Metadata_ConfigJson CHECK (provider_config_json IS NULL OR ISJSON(provider_config_json) = 1),
        CONSTRAINT CK_Integration_Metadata_Version CHECK (current_version >= 1)
    );
END;

IF OBJECT_ID('dbo.Integration_ConnectionScope', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Integration_ConnectionScope (
        scope_id            bigint IDENTITY(1,1) NOT NULL,
        connection_id       uniqueidentifier NOT NULL,
        scope_type_code     varchar(30)      NOT NULL,
        company_id          nvarchar(100)    NULL,
        business_unit_id    nvarchar(100)    NULL,
        external_asset_id   nvarchar(180)    NULL,
        external_asset_name nvarchar(250)    NULL,
        is_primary          bit              NOT NULL,
        enabled             bit              NOT NULL,
        valid_from          datetime2(0)     NULL,
        valid_to            datetime2(0)     NULL,
        created_at          datetime2(0)     NOT NULL CONSTRAINT DF_Integration_Scope_Created DEFAULT (SYSDATETIME()),
        created_by          nvarchar(150)    NULL,
        CONSTRAINT PK_Integration_ConnectionScope PRIMARY KEY (scope_id),
        CONSTRAINT FK_Integration_Scope_Connection FOREIGN KEY (connection_id)
            REFERENCES dbo.Servidores_Conexiones(id),
        CONSTRAINT FK_Integration_Scope_Type FOREIGN KEY (scope_type_code)
            REFERENCES dbo.Integration_ScopeType(scope_type_code),
        CONSTRAINT CK_Integration_Scope_Dates CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from)
    );

    CREATE UNIQUE INDEX UX_Integration_ConnectionScope_Natural
        ON dbo.Integration_ConnectionScope (
            connection_id,
            scope_type_code,
            company_id,
            business_unit_id,
            external_asset_id
        )
        WHERE enabled = 1;
END;

IF OBJECT_ID('dbo.Integration_ConnectionVersion', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Integration_ConnectionVersion (
        version_id          bigint IDENTITY(1,1) NOT NULL,
        connection_id       uniqueidentifier NOT NULL,
        version_number      int              NOT NULL,
        snapshot_json       nvarchar(max)    NOT NULL,
        change_reason       nvarchar(500)    NULL,
        created_at          datetime2(0)     NOT NULL CONSTRAINT DF_Integration_Version_Created DEFAULT (SYSDATETIME()),
        created_by          nvarchar(150)    NULL,
        CONSTRAINT PK_Integration_ConnectionVersion PRIMARY KEY (version_id),
        CONSTRAINT FK_Integration_Version_Connection FOREIGN KEY (connection_id)
            REFERENCES dbo.Servidores_Conexiones(id),
        CONSTRAINT UQ_Integration_Version UNIQUE (connection_id, version_number),
        CONSTRAINT CK_Integration_Version_Number CHECK (version_number >= 1),
        CONSTRAINT CK_Integration_Version_Json CHECK (ISJSON(snapshot_json) = 1)
    );
END;

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID('dbo.Integration_ConnectionMetadata')
      AND name = 'IX_Integration_Metadata_Filter'
)
BEGIN
    CREATE INDEX IX_Integration_Metadata_Filter
        ON dbo.Integration_ConnectionMetadata (
            provider_code,
            environment_code,
            status_code,
            criticality_code
        );
END;

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID('dbo.Integration_ConnectionScope')
      AND name = 'IX_Integration_Scope_BusinessUnit'
)
BEGIN
    CREATE INDEX IX_Integration_Scope_BusinessUnit
        ON dbo.Integration_ConnectionScope (business_unit_id, enabled, connection_id)
        INCLUDE (company_id, scope_type_code, external_asset_id, external_asset_name);
END;

/*
IMPORTANTE:
Esta migracion no carga proveedores, categorias, adaptadores, ambientes,
estados, criticidades, tipos de autenticacion ni tipos de alcance.
Esos valores deben administrarse mediante catalogos, permisos RBAC y auditoria.
*/

COMMIT TRANSACTION;
