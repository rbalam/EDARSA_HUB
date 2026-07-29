/*
EDARSAHUB - Centro de Conexiones V1.0
Migracion aditiva e idempotente.

Objetivos:
- Mantener dbo.Servidores_Conexiones como registro compatible existente.
- Agregar metadatos canonicos sin duplicar conexiones ni secretos.
- Permitir organizacion por categoria, proveedor, empresa y unidad de negocio.
- Preparar versionado y rollback de configuracion.
- No ejecutar cutover ni eliminar contratos legacy.
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
        display_order       int             NOT NULL CONSTRAINT DF_Integration_Category_Order DEFAULT (100),
        enabled             bit             NOT NULL CONSTRAINT DF_Integration_Category_Enabled DEFAULT (1),
        created_at          datetime2(0)    NOT NULL CONSTRAINT DF_Integration_Category_Created DEFAULT (SYSDATETIME()),
        updated_at          datetime2(0)    NOT NULL CONSTRAINT DF_Integration_Category_Updated DEFAULT (SYSDATETIME()),
        CONSTRAINT PK_Integration_ConnectionCategory PRIMARY KEY (category_code),
        CONSTRAINT UQ_Integration_ConnectionCategory_Name UNIQUE (category_name)
    );
END;

IF OBJECT_ID('dbo.Integration_ProviderDefinition', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Integration_ProviderDefinition (
        provider_code       varchar(80)     NOT NULL,
        provider_name       nvarchar(160)   NOT NULL,
        category_code       varchar(50)     NOT NULL,
        adapter_code        varchar(80)     NOT NULL,
        auth_type_default   varchar(40)     NULL,
        config_schema_json  nvarchar(max)   NULL,
        supports_read       bit             NOT NULL CONSTRAINT DF_Integration_Provider_Read DEFAULT (1),
        supports_write      bit             NOT NULL CONSTRAINT DF_Integration_Provider_Write DEFAULT (0),
        enabled             bit             NOT NULL CONSTRAINT DF_Integration_Provider_Enabled DEFAULT (1),
        created_at          datetime2(0)    NOT NULL CONSTRAINT DF_Integration_Provider_Created DEFAULT (SYSDATETIME()),
        updated_at          datetime2(0)    NOT NULL CONSTRAINT DF_Integration_Provider_Updated DEFAULT (SYSDATETIME()),
        CONSTRAINT PK_Integration_ProviderDefinition PRIMARY KEY (provider_code),
        CONSTRAINT UQ_Integration_ProviderDefinition_Name UNIQUE (provider_name),
        CONSTRAINT FK_Integration_Provider_Category FOREIGN KEY (category_code)
            REFERENCES dbo.Integration_ConnectionCategory(category_code),
        CONSTRAINT CK_Integration_Provider_ConfigJson CHECK (config_schema_json IS NULL OR ISJSON(config_schema_json) = 1)
    );
END;

IF OBJECT_ID('dbo.Integration_ConnectionMetadata', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Integration_ConnectionMetadata (
        connection_id       uniqueidentifier NOT NULL,
        category_code       varchar(50)      NOT NULL,
        provider_code       varchar(80)      NOT NULL,
        environment_code    varchar(30)      NOT NULL CONSTRAINT DF_Integration_Metadata_Environment DEFAULT ('PRODUCTION'),
        status_code         varchar(30)      NOT NULL CONSTRAINT DF_Integration_Metadata_Status DEFAULT ('ACTIVE'),
        auth_type           varchar(40)      NULL,
        owner_user_id       nvarchar(120)    NULL,
        support_team        nvarchar(120)    NULL,
        criticality_code    varchar(20)      NOT NULL CONSTRAINT DF_Integration_Metadata_Criticality DEFAULT ('MEDIUM'),
        provider_config_json nvarchar(max)   NULL,
        current_version     int              NOT NULL CONSTRAINT DF_Integration_Metadata_Version DEFAULT (1),
        created_at          datetime2(0)     NOT NULL CONSTRAINT DF_Integration_Metadata_Created DEFAULT (SYSDATETIME()),
        updated_at          datetime2(0)     NOT NULL CONSTRAINT DF_Integration_Metadata_Updated DEFAULT (SYSDATETIME()),
        created_by          nvarchar(150)    NULL,
        updated_by          nvarchar(150)    NULL,
        row_version         rowversion       NOT NULL,
        CONSTRAINT PK_Integration_ConnectionMetadata PRIMARY KEY (connection_id),
        CONSTRAINT FK_Integration_Metadata_Connection FOREIGN KEY (connection_id)
            REFERENCES dbo.Servidores_Conexiones(id),
        CONSTRAINT FK_Integration_Metadata_Category FOREIGN KEY (category_code)
            REFERENCES dbo.Integration_ConnectionCategory(category_code),
        CONSTRAINT FK_Integration_Metadata_Provider FOREIGN KEY (provider_code)
            REFERENCES dbo.Integration_ProviderDefinition(provider_code),
        CONSTRAINT CK_Integration_Metadata_Environment CHECK (environment_code IN ('DEVELOPMENT','TEST','STAGING','PRODUCTION')),
        CONSTRAINT CK_Integration_Metadata_Status CHECK (status_code IN ('DRAFT','ACTIVE','SUSPENDED','ERROR','RETIRED')),
        CONSTRAINT CK_Integration_Metadata_Criticality CHECK (criticality_code IN ('LOW','MEDIUM','HIGH','CRITICAL')),
        CONSTRAINT CK_Integration_Metadata_ConfigJson CHECK (provider_config_json IS NULL OR ISJSON(provider_config_json) = 1),
        CONSTRAINT CK_Integration_Metadata_Version CHECK (current_version >= 1)
    );
END;

IF OBJECT_ID('dbo.Integration_ConnectionScope', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Integration_ConnectionScope (
        scope_id            bigint IDENTITY(1,1) NOT NULL,
        connection_id       uniqueidentifier NOT NULL,
        scope_type          varchar(30)      NOT NULL,
        company_id          nvarchar(100)    NULL,
        business_unit_id    nvarchar(100)    NULL,
        external_asset_id   nvarchar(180)    NULL,
        external_asset_name nvarchar(250)    NULL,
        is_primary          bit              NOT NULL CONSTRAINT DF_Integration_Scope_Primary DEFAULT (0),
        enabled             bit              NOT NULL CONSTRAINT DF_Integration_Scope_Enabled DEFAULT (1),
        valid_from          datetime2(0)     NULL,
        valid_to            datetime2(0)     NULL,
        created_at          datetime2(0)     NOT NULL CONSTRAINT DF_Integration_Scope_Created DEFAULT (SYSDATETIME()),
        created_by          nvarchar(150)    NULL,
        CONSTRAINT PK_Integration_ConnectionScope PRIMARY KEY (scope_id),
        CONSTRAINT FK_Integration_Scope_Connection FOREIGN KEY (connection_id)
            REFERENCES dbo.Servidores_Conexiones(id),
        CONSTRAINT CK_Integration_Scope_Type CHECK (scope_type IN ('UNIT','MULTI_UNIT','COMPANY','MULTI_COMPANY','GROUP','GLOBAL')),
        CONSTRAINT CK_Integration_Scope_Dates CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from)
    );

    CREATE UNIQUE INDEX UX_Integration_ConnectionScope_Natural
        ON dbo.Integration_ConnectionScope (
            connection_id,
            scope_type,
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

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.Integration_ConnectionMetadata') AND name = 'IX_Integration_Metadata_Filter')
BEGIN
    CREATE INDEX IX_Integration_Metadata_Filter
        ON dbo.Integration_ConnectionMetadata (category_code, provider_code, environment_code, status_code, criticality_code);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.Integration_ConnectionScope') AND name = 'IX_Integration_Scope_BusinessUnit')
BEGIN
    CREATE INDEX IX_Integration_Scope_BusinessUnit
        ON dbo.Integration_ConnectionScope (business_unit_id, enabled, connection_id)
        INCLUDE (company_id, scope_type, external_asset_id, external_asset_name);
END;

/* Catalogos iniciales: datos administrables, no logica hardcodeada en frontend. */
MERGE dbo.Integration_ConnectionCategory AS target
USING (VALUES
    ('POS',                    N'Punto de venta',            10),
    ('PAYMENT_PROCESSOR',      N'Procesadores de pago',      20),
    ('DATABASE',               N'Bases de datos',            30),
    ('SOCIAL_MEDIA',           N'Redes sociales',            40),
    ('RESERVATION_PLATFORM',   N'Reservaciones',             50),
    ('ONLINE_REPUTATION',      N'Reputacion en linea',       60),
    ('OTA',                    N'Agencias de viaje en linea',70),
    ('ADVERTISING_PLATFORM',   N'Publicidad',                80),
    ('CRM',                    N'CRM',                        90),
    ('OTHER',                  N'Otras conexiones',         999)
) AS source(category_code, category_name, display_order)
ON target.category_code = source.category_code
WHEN NOT MATCHED THEN
    INSERT (category_code, category_name, display_order)
    VALUES (source.category_code, source.category_name, source.display_order);

MERGE dbo.Integration_ProviderDefinition AS target
USING (VALUES
    ('LEGACY_API_LOCAL', N'API local heredada', 'OTHER',    'GENERIC_REST', 'API_KEY'),
    ('GENERIC_REST',     N'API REST generica',   'OTHER',    'GENERIC_REST', NULL),
    ('SQL_SERVER',       N'Microsoft SQL Server','DATABASE', 'SQL_SERVER',   'USERNAME_PASSWORD'),
    ('VTIGER',           N'Vtiger CRM',          'CRM',      'VTIGER',       'ACCESS_KEY'),
    ('TOAST',            N'Toast',               'POS',      'TOAST',        'OAUTH2_CLIENT_CREDENTIALS'),
    ('NETPAY',           N'NetPay',              'PAYMENT_PROCESSOR', 'NETPAY', NULL)
) AS source(provider_code, provider_name, category_code, adapter_code, auth_type_default)
ON target.provider_code = source.provider_code
WHEN NOT MATCHED THEN
    INSERT (provider_code, provider_name, category_code, adapter_code, auth_type_default)
    VALUES (source.provider_code, source.provider_name, source.category_code, source.adapter_code, source.auth_type_default);

COMMIT TRANSACTION;
