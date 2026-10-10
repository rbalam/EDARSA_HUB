SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> 'EDARSAHUB'
    THROW 51000, 'ABORT_WRONG_DATABASE', 1;

IF SUSER_SNAME() = 'HRLectura'
    THROW 51001, 'ABORT_READONLY_LOGIN_NOT_WRITER', 1;

IF OBJECT_ID('dbo.Services_Professions','U') IS NULL
    THROW 51020, 'ABORT_SERVICES_PROFESSIONS_MISSING', 1;

IF OBJECT_ID('dbo.Services_Specialties','U') IS NULL
    THROW 51021, 'ABORT_SERVICES_SPECIALTIES_MISSING', 1;

IF OBJECT_ID('dbo.Gobierno_Persona','U') IS NULL
    THROW 51022, 'ABORT_GOBIERNO_PERSONA_MISSING', 1;

IF OBJECT_ID('dbo.Proveedor_Catalogo','U') IS NULL
    THROW 51023, 'ABORT_PROVEEDOR_CATALOGO_MISSING', 1;

IF OBJECT_ID('dbo.Sistema_Empresas','U') IS NULL
    THROW 51024, 'ABORT_SISTEMA_EMPRESAS_MISSING', 1;

IF OBJECT_ID('dbo.Gobierno_Documento','U') IS NULL
    THROW 51025, 'ABORT_GOBIERNO_DOCUMENTO_MISSING', 1;

IF OBJECT_ID('dbo.Usuario_Catalogo','U') IS NULL
    THROW 51026, 'ABORT_USUARIO_CATALOGO_MISSING', 1;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Services_Providers','U') IS NULL
    BEGIN
        CREATE TABLE dbo.Services_Providers(
            ProviderID bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_Services_Providers PRIMARY KEY,
            ProviderType varchar(20) NOT NULL,
            PersonaID bigint NULL,
            ProveedorID int NULL,
            EmpresaID int NULL,
            Estatus varchar(20) NOT NULL CONSTRAINT DF_Services_Providers_Estatus DEFAULT('ACTIVO'),
            FechaAlta datetime2(0) NOT NULL CONSTRAINT DF_Services_Providers_FechaAlta DEFAULT(SYSUTCDATETIME()),
            FechaActualizacion datetime2(0) NULL,
            UsuarioActualizacionID int NULL,
            CONSTRAINT CK_Services_Providers_Type CHECK (ProviderType IN ('INDIVIDUAL','ORGANIZATION','FACILITY')),
            CONSTRAINT CK_Services_Providers_Source CHECK (
                (ProviderType='INDIVIDUAL' AND PersonaID IS NOT NULL AND ProveedorID IS NULL AND EmpresaID IS NULL)
                OR
                (ProviderType='ORGANIZATION' AND PersonaID IS NULL AND ProveedorID IS NOT NULL AND EmpresaID IS NULL)
                OR
                (ProviderType='FACILITY' AND PersonaID IS NULL AND (
                    (ProveedorID IS NOT NULL AND EmpresaID IS NULL)
                    OR
                    (ProveedorID IS NULL AND EmpresaID IS NOT NULL)
                ))
            ),
            CONSTRAINT FK_Services_Providers_Persona FOREIGN KEY(PersonaID) REFERENCES dbo.Gobierno_Persona(PersonaID),
            CONSTRAINT FK_Services_Providers_Proveedor FOREIGN KEY(ProveedorID) REFERENCES dbo.Proveedor_Catalogo(ProveedorID),
            CONSTRAINT FK_Services_Providers_Empresa FOREIGN KEY(EmpresaID) REFERENCES dbo.Sistema_Empresas(EmpresaID),
            CONSTRAINT FK_Services_Providers_UsuarioActualizacion FOREIGN KEY(UsuarioActualizacionID) REFERENCES dbo.Usuario_Catalogo(UsuarioID)
        );
        CREATE UNIQUE INDEX UX_Services_Providers_Persona
            ON dbo.Services_Providers(PersonaID)
            WHERE PersonaID IS NOT NULL;
        CREATE UNIQUE INDEX UX_Services_Providers_Proveedor
            ON dbo.Services_Providers(ProveedorID)
            WHERE ProveedorID IS NOT NULL;
        CREATE UNIQUE INDEX UX_Services_Providers_Empresa
            ON dbo.Services_Providers(EmpresaID)
            WHERE EmpresaID IS NOT NULL;
        CREATE INDEX IX_Services_Providers_Estatus ON dbo.Services_Providers(Estatus);
    END;

    IF OBJECT_ID('dbo.Services_ProviderSpecialties','U') IS NULL
    BEGIN
        CREATE TABLE dbo.Services_ProviderSpecialties(
            ProviderSpecialtyID bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_Services_ProviderSpecialties PRIMARY KEY,
            ProviderID bigint NOT NULL,
            SpecialtyID bigint NOT NULL,
            EsPrincipal bit NOT NULL CONSTRAINT DF_Services_ProviderSpecialties_EsPrincipal DEFAULT(0),
            FechaAlta datetime2(0) NOT NULL CONSTRAINT DF_Services_ProviderSpecialties_FechaAlta DEFAULT(SYSUTCDATETIME()),
            UsuarioActualizacionID int NULL,
            CONSTRAINT FK_Services_ProviderSpecialties_Provider FOREIGN KEY(ProviderID) REFERENCES dbo.Services_Providers(ProviderID),
            CONSTRAINT FK_Services_ProviderSpecialties_Specialty FOREIGN KEY(SpecialtyID) REFERENCES dbo.Services_Specialties(SpecialtyID),
            CONSTRAINT FK_Services_ProviderSpecialties_Usuario FOREIGN KEY(UsuarioActualizacionID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
            CONSTRAINT UQ_Services_ProviderSpecialties UNIQUE(ProviderID,SpecialtyID)
        );
        CREATE INDEX IX_Services_ProviderSpecialties_Specialty ON dbo.Services_ProviderSpecialties(SpecialtyID);
    END;

    IF OBJECT_ID('dbo.Services_Credentials','U') IS NULL
    BEGIN
        CREATE TABLE dbo.Services_Credentials(
            CredentialID bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_Services_Credentials PRIMARY KEY,
            ProviderID bigint NOT NULL,
            CredentialTypeCode varchar(50) NOT NULL,
            IssuerName nvarchar(200) NULL,
            CredentialNumber nvarchar(120) NULL,
            ValidFrom date NULL,
            ValidTo date NULL,
            DocumentoID bigint NULL,
            Estatus varchar(20) NOT NULL CONSTRAINT DF_Services_Credentials_Estatus DEFAULT('ACTIVA'),
            FechaAlta datetime2(0) NOT NULL CONSTRAINT DF_Services_Credentials_FechaAlta DEFAULT(SYSUTCDATETIME()),
            FechaActualizacion datetime2(0) NULL,
            UsuarioActualizacionID int NULL,
            CONSTRAINT CK_Services_Credentials_Dates CHECK (ValidTo IS NULL OR ValidFrom IS NULL OR ValidTo >= ValidFrom),
            CONSTRAINT FK_Services_Credentials_Provider FOREIGN KEY(ProviderID) REFERENCES dbo.Services_Providers(ProviderID),
            CONSTRAINT FK_Services_Credentials_Documento FOREIGN KEY(DocumentoID) REFERENCES dbo.Gobierno_Documento(DocumentoID),
            CONSTRAINT FK_Services_Credentials_Usuario FOREIGN KEY(UsuarioActualizacionID) REFERENCES dbo.Usuario_Catalogo(UsuarioID)
        );
        CREATE INDEX IX_Services_Credentials_Provider ON dbo.Services_Credentials(ProviderID);
        CREATE INDEX IX_Services_Credentials_Vigencia ON dbo.Services_Credentials(ValidTo,Estatus);
        CREATE UNIQUE INDEX UX_Services_Credentials_Natural
            ON dbo.Services_Credentials(ProviderID,CredentialTypeCode,IssuerName,CredentialNumber,ValidFrom)
            WHERE CredentialNumber IS NOT NULL;
    END;

    COMMIT;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK;
    THROW;
END CATCH;
