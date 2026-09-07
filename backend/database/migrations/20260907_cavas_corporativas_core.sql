/*
EDARSAHUB - CAVAS CORPORATIVAS CORE
Migracion idempotente SQL Server
Fuente: docs/CAVAS/CAVAS_CORPORATIVAS_MINIMAL_DDL_PROPOSAL.sql
Evidencia: docs/CAVAS/CAVAS_CORPORATIVAS_DDL_KEYS_EVIDENCE_DOSSIER.md

IMPORTANTE:
- Este archivo es una migracion ejecutable, pero este commit NO la ejecuta.
- Production permanece prohibida.
- No duplica unidades, clientes/CRM, productos, tickets, reservas ni ventas.
- Las FKs fisicas son exclusivamente internas al dominio Cavas Corporativas.
- Referencias externas permanecen desacopladas hasta certificar contrato fisico visible.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.CavasCorporativas_OrganizacionesRef', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.CavasCorporativas_OrganizacionesRef
        (
            OrganizacionCorporativaID uniqueidentifier NOT NULL CONSTRAINT DF_CC_Organizacion_ID DEFAULT NEWID(),
            FuenteCanonica varchar(50) NOT NULL,
            ReferenciaCanonica varchar(150) NOT NULL,
            CodigoCorporativo varchar(50) NULL,
            Activa bit NOT NULL CONSTRAINT DF_CC_Organizacion_Activa DEFAULT (1),
            CreatedAt datetime2(3) NOT NULL CONSTRAINT DF_CC_Organizacion_CreatedAt DEFAULT SYSUTCDATETIME(),
            UpdatedAt datetime2(3) NOT NULL CONSTRAINT DF_CC_Organizacion_UpdatedAt DEFAULT SYSUTCDATETIME(),
            CONSTRAINT PK_CavasCorporativas_OrganizacionesRef PRIMARY KEY (OrganizacionCorporativaID),
            CONSTRAINT UQ_CC_Organizacion_FuenteRef UNIQUE (FuenteCanonica, ReferenciaCanonica)
        );
    END;

    IF OBJECT_ID('dbo.CavasCorporativas_Convenios', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.CavasCorporativas_Convenios
        (
            ConvenioID uniqueidentifier NOT NULL CONSTRAINT DF_CC_Convenio_ID DEFAULT NEWID(),
            OrganizacionCorporativaID uniqueidentifier NOT NULL,
            CodigoConvenio varchar(50) NOT NULL,
            NombreConvenio nvarchar(150) NOT NULL,
            VigenciaDesde datetime2(0) NOT NULL,
            VigenciaHasta datetime2(0) NULL,
            Estado varchar(30) NOT NULL CONSTRAINT DF_CC_Convenio_Estado DEFAULT ('BORRADOR'),
            UsoNegocioRequerido bit NOT NULL CONSTRAINT DF_CC_Convenio_UsoNegocio DEFAULT (1),
            Activo bit NOT NULL CONSTRAINT DF_CC_Convenio_Activo DEFAULT (1),
            CreatedAt datetime2(3) NOT NULL CONSTRAINT DF_CC_Convenio_CreatedAt DEFAULT SYSUTCDATETIME(),
            UpdatedAt datetime2(3) NOT NULL CONSTRAINT DF_CC_Convenio_UpdatedAt DEFAULT SYSUTCDATETIME(),
            CONSTRAINT PK_CavasCorporativas_Convenios PRIMARY KEY (ConvenioID),
            CONSTRAINT UQ_CC_Convenio_Codigo UNIQUE (CodigoConvenio),
            CONSTRAINT FK_CC_Convenio_Organizacion FOREIGN KEY (OrganizacionCorporativaID) REFERENCES dbo.CavasCorporativas_OrganizacionesRef(OrganizacionCorporativaID),
            CONSTRAINT CK_CC_Convenio_Vigencia CHECK (VigenciaHasta IS NULL OR VigenciaHasta >= VigenciaDesde)
        );
    END;

    IF OBJECT_ID('dbo.CavasCorporativas_ConvenioUnidades', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.CavasCorporativas_ConvenioUnidades
        (
            ConvenioUnidadID uniqueidentifier NOT NULL CONSTRAINT DF_CC_ConvenioUnidad_ID DEFAULT NEWID(),
            ConvenioID uniqueidentifier NOT NULL,
            UnidadReferencia varchar(100) NOT NULL,
            Activa bit NOT NULL CONSTRAINT DF_CC_ConvenioUnidad_Activa DEFAULT (1),
            CreatedAt datetime2(3) NOT NULL CONSTRAINT DF_CC_ConvenioUnidad_CreatedAt DEFAULT SYSUTCDATETIME(),
            CONSTRAINT PK_CavasCorporativas_ConvenioUnidades PRIMARY KEY (ConvenioUnidadID),
            CONSTRAINT UQ_CC_ConvenioUnidad UNIQUE (ConvenioID, UnidadReferencia),
            CONSTRAINT FK_CC_ConvenioUnidad_Convenio FOREIGN KEY (ConvenioID) REFERENCES dbo.CavasCorporativas_Convenios(ConvenioID)
        );
    END;

    IF OBJECT_ID('dbo.CavasCorporativas_Autorizados', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.CavasCorporativas_Autorizados
        (
            AutorizadoID uniqueidentifier NOT NULL CONSTRAINT DF_CC_Autorizado_ID DEFAULT NEWID(),
            ConvenioID uniqueidentifier NOT NULL,
            IdentidadFuente varchar(50) NOT NULL,
            IdentidadReferencia varchar(150) NOT NULL,
            TipoAutorizacion varchar(30) NOT NULL CONSTRAINT DF_CC_Autorizado_Tipo DEFAULT ('CONSUMO'),
            VigenciaDesde datetime2(0) NULL,
            VigenciaHasta datetime2(0) NULL,
            Activo bit NOT NULL CONSTRAINT DF_CC_Autorizado_Activo DEFAULT (1),
            CreatedAt datetime2(3) NOT NULL CONSTRAINT DF_CC_Autorizado_CreatedAt DEFAULT SYSUTCDATETIME(),
            CONSTRAINT PK_CavasCorporativas_Autorizados PRIMARY KEY (AutorizadoID),
            CONSTRAINT UQ_CC_Autorizado UNIQUE (ConvenioID, IdentidadFuente, IdentidadReferencia, TipoAutorizacion),
            CONSTRAINT FK_CC_Autorizado_Convenio FOREIGN KEY (ConvenioID) REFERENCES dbo.CavasCorporativas_Convenios(ConvenioID),
            CONSTRAINT CK_CC_Autorizado_Vigencia CHECK (VigenciaHasta IS NULL OR VigenciaDesde IS NULL OR VigenciaHasta >= VigenciaDesde)
        );
    END;

    IF OBJECT_ID('dbo.CavasCorporativas_Beneficios', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.CavasCorporativas_Beneficios
        (
            BeneficioID uniqueidentifier NOT NULL CONSTRAINT DF_CC_Beneficio_ID DEFAULT NEWID(),
            ConvenioID uniqueidentifier NOT NULL,
            CodigoBeneficio varchar(50) NOT NULL,
            TipoBeneficio varchar(40) NOT NULL,
            ValorDecimal decimal(18,6) NULL,
            ValorMonetario decimal(18,2) NULL,
            MonedaCodigo char(3) NULL,
            ConfiguracionJson nvarchar(max) NULL,
            Prioridad int NOT NULL CONSTRAINT DF_CC_Beneficio_Prioridad DEFAULT (100),
            Activo bit NOT NULL CONSTRAINT DF_CC_Beneficio_Activo DEFAULT (1),
            VigenciaDesde datetime2(0) NULL,
            VigenciaHasta datetime2(0) NULL,
            CreatedAt datetime2(3) NOT NULL CONSTRAINT DF_CC_Beneficio_CreatedAt DEFAULT SYSUTCDATETIME(),
            UpdatedAt datetime2(3) NOT NULL CONSTRAINT DF_CC_Beneficio_UpdatedAt DEFAULT SYSUTCDATETIME(),
            CONSTRAINT PK_CavasCorporativas_Beneficios PRIMARY KEY (BeneficioID),
            CONSTRAINT UQ_CC_Beneficio UNIQUE (ConvenioID, CodigoBeneficio),
            CONSTRAINT FK_CC_Beneficio_Convenio FOREIGN KEY (ConvenioID) REFERENCES dbo.CavasCorporativas_Convenios(ConvenioID),
            CONSTRAINT CK_CC_Beneficio_Vigencia CHECK (VigenciaHasta IS NULL OR VigenciaDesde IS NULL OR VigenciaHasta >= VigenciaDesde),
            CONSTRAINT CK_CC_Beneficio_ConfigJson CHECK (ConfiguracionJson IS NULL OR ISJSON(ConfiguracionJson)=1)
        );
    END;

    IF OBJECT_ID('dbo.CavasCorporativas_BeneficioAlcances', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.CavasCorporativas_BeneficioAlcances
        (
            AlcanceID uniqueidentifier NOT NULL CONSTRAINT DF_CC_Alcance_ID DEFAULT NEWID(),
            BeneficioID uniqueidentifier NOT NULL,
            UnidadReferencia varchar(100) NULL,
            LineaComercialCodigo varchar(80) NOT NULL,
            NivelDetalle varchar(20) NOT NULL CONSTRAINT DF_CC_Alcance_Nivel DEFAULT ('LINEA'),
            ReferenciaDetalle varchar(150) NULL,
            Incluido bit NOT NULL CONSTRAINT DF_CC_Alcance_Incluido DEFAULT (1),
            CreatedAt datetime2(3) NOT NULL CONSTRAINT DF_CC_Alcance_CreatedAt DEFAULT SYSUTCDATETIME(),
            CONSTRAINT PK_CavasCorporativas_BeneficioAlcances PRIMARY KEY (AlcanceID),
            CONSTRAINT FK_CC_Alcance_Beneficio FOREIGN KEY (BeneficioID) REFERENCES dbo.CavasCorporativas_Beneficios(BeneficioID),
            CONSTRAINT CK_CC_Alcance_Nivel CHECK (NivelDetalle IN ('LINEA','CATEGORIA','FAMILIA','SKU'))
        );
    END;

    IF OBJECT_ID('dbo.CavasCorporativas_Politicas', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.CavasCorporativas_Politicas
        (
            PoliticaID uniqueidentifier NOT NULL CONSTRAINT DF_CC_Politica_ID DEFAULT NEWID(),
            ConvenioID uniqueidentifier NOT NULL,
            BeneficioID uniqueidentifier NULL,
            TipoPolitica varchar(50) NOT NULL,
            ConfiguracionJson nvarchar(max) NOT NULL,
            Prioridad int NOT NULL CONSTRAINT DF_CC_Politica_Prioridad DEFAULT (100),
            Activa bit NOT NULL CONSTRAINT DF_CC_Politica_Activa DEFAULT (1),
            CreatedAt datetime2(3) NOT NULL CONSTRAINT DF_CC_Politica_CreatedAt DEFAULT SYSUTCDATETIME(),
            UpdatedAt datetime2(3) NOT NULL CONSTRAINT DF_CC_Politica_UpdatedAt DEFAULT SYSUTCDATETIME(),
            CONSTRAINT PK_CavasCorporativas_Politicas PRIMARY KEY (PoliticaID),
            CONSTRAINT FK_CC_Politica_Convenio FOREIGN KEY (ConvenioID) REFERENCES dbo.CavasCorporativas_Convenios(ConvenioID),
            CONSTRAINT FK_CC_Politica_Beneficio FOREIGN KEY (BeneficioID) REFERENCES dbo.CavasCorporativas_Beneficios(BeneficioID),
            CONSTRAINT CK_CC_Politica_ConfigJson CHECK (ISJSON(ConfiguracionJson)=1)
        );
    END;

    IF OBJECT_ID('dbo.CavasCorporativas_AplicacionesBeneficio', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.CavasCorporativas_AplicacionesBeneficio
        (
            AplicacionID uniqueidentifier NOT NULL CONSTRAINT DF_CC_Aplicacion_ID DEFAULT NEWID(),
            ConvenioID uniqueidentifier NOT NULL,
            BeneficioID uniqueidentifier NOT NULL,
            AutorizadoID uniqueidentifier NULL,
            UnidadReferencia varchar(100) NOT NULL,
            OperacionTipo varchar(30) NOT NULL,
            OperacionReferencia varchar(150) NOT NULL,
            EventoTemporalTipo varchar(30) NULL,
            EventoTemporalUtc datetime2(3) NULL,
            ImporteBase decimal(18,2) NULL,
            ImporteBeneficio decimal(18,2) NULL,
            MonedaCodigo char(3) NULL,
            EvaluacionJson nvarchar(max) NULL,
            AppliedAt datetime2(3) NOT NULL CONSTRAINT DF_CC_Aplicacion_AppliedAt DEFAULT SYSUTCDATETIME(),
            AppliedByReferencia varchar(150) NULL,
            CONSTRAINT PK_CavasCorporativas_AplicacionesBeneficio PRIMARY KEY (AplicacionID),
            CONSTRAINT FK_CC_Aplicacion_Convenio FOREIGN KEY (ConvenioID) REFERENCES dbo.CavasCorporativas_Convenios(ConvenioID),
            CONSTRAINT FK_CC_Aplicacion_Beneficio FOREIGN KEY (BeneficioID) REFERENCES dbo.CavasCorporativas_Beneficios(BeneficioID),
            CONSTRAINT FK_CC_Aplicacion_Autorizado FOREIGN KEY (AutorizadoID) REFERENCES dbo.CavasCorporativas_Autorizados(AutorizadoID),
            CONSTRAINT UQ_CC_Aplicacion_Idempotencia UNIQUE (BeneficioID, UnidadReferencia, OperacionTipo, OperacionReferencia),
            CONSTRAINT CK_CC_Aplicacion_EvaluacionJson CHECK (EvaluacionJson IS NULL OR ISJSON(EvaluacionJson)=1)
        );
    END;

    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.CavasCorporativas_BeneficioAlcances') AND name='UX_CC_Alcance')
        CREATE UNIQUE INDEX UX_CC_Alcance ON dbo.CavasCorporativas_BeneficioAlcances(BeneficioID, UnidadReferencia, LineaComercialCodigo, NivelDetalle, ReferenciaDetalle);

    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.CavasCorporativas_Convenios') AND name='IX_CC_Convenios_OrganizacionEstado')
        CREATE INDEX IX_CC_Convenios_OrganizacionEstado ON dbo.CavasCorporativas_Convenios(OrganizacionCorporativaID, Estado, Activo);

    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.CavasCorporativas_Autorizados') AND name='IX_CC_Autorizados_Identidad')
        CREATE INDEX IX_CC_Autorizados_Identidad ON dbo.CavasCorporativas_Autorizados(IdentidadFuente, IdentidadReferencia, Activo);

    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.CavasCorporativas_AplicacionesBeneficio') AND name='IX_CC_Aplicaciones_Operacion')
        CREATE INDEX IX_CC_Aplicaciones_Operacion ON dbo.CavasCorporativas_AplicacionesBeneficio(UnidadReferencia, OperacionTipo, OperacionReferencia);

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;

/*
POSTCONDICION ESPERADA AL EJECUTARSE POR EL RUNNER AUTORIZADO:
- 8 tablas propias creadas si no existian.
- Indices minimos creados idempotentemente.
- Ninguna FK externa inventada.
- Ningun dato semilla comercial hardcodeado.
- Ningun cambio a Production desde este artefacto por si solo.
*/
