/*
EDARSAHUB BOS V1.0
Gate 4B - Infraestructura universal Servidores/Integraciones

GENERADO DESPUES DE:
- Gate 2 CERTIFIED 100%
- Gate 3A CERTIFIED_READ_ONLY 100%
- Gate 3B CERTIFIED 100%
- Gate 4A CERTIFIED_READ_ONLY 100%

REGLAS:
- SQL-first
- idempotente
- no duplica empresas/unidades/sistemas/versiones/conexiones/sync/capacidades/RBAC/FX
- no crea Toast_* ni ToastRobot
- no secretos en nuevas tablas
- este archivo NO implica ejecucion automatica
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    /* ------------------------------------------------------------
       0. Precondiciones canonicas
       ------------------------------------------------------------ */
    IF OBJECT_ID('dbo.Unidades_Negocio','U') IS NULL
        THROW 51000, 'GATE4B_MISSING_Unidades_Negocio', 1;
    IF OBJECT_ID('dbo.Servidores_Conexiones','U') IS NULL
        THROW 51000, 'GATE4B_MISSING_Servidores_Conexiones', 1;
    IF OBJECT_ID('dbo.Servidores_ConexionEstado','U') IS NULL
        THROW 51000, 'GATE4B_MISSING_Servidores_ConexionEstado', 1;
    IF OBJECT_ID('dbo.Sistema_Tipos','U') IS NULL
        THROW 51000, 'GATE4B_MISSING_Sistema_Tipos', 1;
    IF OBJECT_ID('dbo.Sistema_VersionesSistemas','U') IS NULL
        THROW 51000, 'GATE4B_MISSING_Sistema_VersionesSistemas', 1;
    IF OBJECT_ID('dbo.Sistema_Capacidades','U') IS NULL
        THROW 51000, 'GATE4B_MISSING_Sistema_Capacidades', 1;
    IF OBJECT_ID('dbo.Sistema_Sync_Catalogo','U') IS NULL
        THROW 51000, 'GATE4B_MISSING_Sistema_Sync_Catalogo', 1;
    IF OBJECT_ID('dbo.Sync_Control_Ejecuciones','U') IS NULL
        THROW 51000, 'GATE4B_MISSING_Sync_Control_Ejecuciones', 1;

    /* ------------------------------------------------------------
       1. Unidad canonica: timezone IANA + locale
       ------------------------------------------------------------ */
    IF COL_LENGTH('dbo.Unidades_Negocio','timezone_iana') IS NULL
        ALTER TABLE dbo.Unidades_Negocio ADD timezone_iana nvarchar(100) NULL;

    IF COL_LENGTH('dbo.Unidades_Negocio','locale_operativo') IS NULL
        ALTER TABLE dbo.Unidades_Negocio ADD locale_operativo nvarchar(20) NULL;

    /* ------------------------------------------------------------
       2. Puente sync <-> capacidades
       Sistema_Sync_Catalogo.Codigo = NVARCHAR(100)
       Sistema_Capacidades.SistemaCapacidadID = INT
       ------------------------------------------------------------ */
    IF OBJECT_ID('dbo.Sistema_Sync_Capacidades','U') IS NULL
    BEGIN
        CREATE TABLE dbo.Sistema_Sync_Capacidades
        (
            SyncCapacidadID bigint IDENTITY(1,1) NOT NULL,
            CodigoSync nvarchar(100) NOT NULL,
            SistemaCapacidadID int NOT NULL,
            Obligatoria bit NOT NULL CONSTRAINT DF_Sistema_Sync_Capacidades_Obligatoria DEFAULT (1),
            Activo bit NOT NULL CONSTRAINT DF_Sistema_Sync_Capacidades_Activo DEFAULT (1),
            FechaAlta datetime2(3) NOT NULL CONSTRAINT DF_Sistema_Sync_Capacidades_FechaAlta DEFAULT (SYSUTCDATETIME()),
            FechaModificacion datetime2(3) NULL,
            CONSTRAINT PK_Sistema_Sync_Capacidades PRIMARY KEY CLUSTERED (SyncCapacidadID),
            CONSTRAINT UQ_Sistema_Sync_Capacidades_SyncCapacidad UNIQUE (CodigoSync, SistemaCapacidadID),
            CONSTRAINT FK_Sistema_Sync_Capacidades_Sync FOREIGN KEY (CodigoSync) REFERENCES dbo.Sistema_Sync_Catalogo(Codigo),
            CONSTRAINT FK_Sistema_Sync_Capacidades_Capacidad FOREIGN KEY (SistemaCapacidadID) REFERENCES dbo.Sistema_Capacidades(SistemaCapacidadID)
        );
    END;

    /* ------------------------------------------------------------
       3. Ledger canonico de ejecuciones: contexto universal
       ------------------------------------------------------------ */
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','ConexionID') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD ConexionID uniqueidentifier NULL;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','UnidadNegocioID') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD UnidadNegocioID uniqueidentifier NULL;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','CodigoSync') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD CodigoSync nvarchar(100) NULL;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','StartedAtUTC') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD StartedAtUTC datetime2(3) NULL;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','FinishedAtUTC') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD FinishedAtUTC datetime2(3) NULL;
    IF COL_LENGTH('dbo.Sync_Control_Ejecuciones','IdempotencyKey') IS NULL
        ALTER TABLE dbo.Sync_Control_Ejecuciones ADD IdempotencyKey nvarchar(200) NULL;

    /* DDL dinamico: evita binding anticipado de columnas agregadas en este batch. */
    IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name='FK_Sync_Control_Ejecuciones_Conexion')
        EXEC(N'ALTER TABLE dbo.Sync_Control_Ejecuciones WITH CHECK ADD CONSTRAINT FK_Sync_Control_Ejecuciones_Conexion FOREIGN KEY (ConexionID) REFERENCES dbo.Servidores_Conexiones(id);');
    IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name='FK_Sync_Control_Ejecuciones_Unidad')
        EXEC(N'ALTER TABLE dbo.Sync_Control_Ejecuciones WITH CHECK ADD CONSTRAINT FK_Sync_Control_Ejecuciones_Unidad FOREIGN KEY (UnidadNegocioID) REFERENCES dbo.Unidades_Negocio(id);');
    IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name='FK_Sync_Control_Ejecuciones_CodigoSync')
        EXEC(N'ALTER TABLE dbo.Sync_Control_Ejecuciones WITH CHECK ADD CONSTRAINT FK_Sync_Control_Ejecuciones_CodigoSync FOREIGN KEY (CodigoSync) REFERENCES dbo.Sistema_Sync_Catalogo(Codigo);');

    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.Sync_Control_Ejecuciones') AND name='UX_Sync_Control_Ejecuciones_IdempotencyKey')
        EXEC(N'CREATE UNIQUE INDEX UX_Sync_Control_Ejecuciones_IdempotencyKey ON dbo.Sync_Control_Ejecuciones(IdempotencyKey) WHERE IdempotencyKey IS NOT NULL;');

    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.Sync_Control_Ejecuciones') AND name='IX_Sync_Control_Ejecuciones_Conexion_CodigoSync')
        EXEC(N'CREATE INDEX IX_Sync_Control_Ejecuciones_Conexion_CodigoSync ON dbo.Sync_Control_Ejecuciones(ConexionID, CodigoSync, StartedAtUTC DESC);');

    /* ------------------------------------------------------------
       4. Evidencia por ejecucion
       ------------------------------------------------------------ */
    IF OBJECT_ID('dbo.Sync_Control_Evidencias','U') IS NULL
    BEGIN
        CREATE TABLE dbo.Sync_Control_Evidencias
        (
            EvidenciaID bigint IDENTITY(1,1) NOT NULL,
            SyncControlID int NOT NULL,
            TipoEvidencia nvarchar(50) NOT NULL,
            HashSHA256 char(64) NOT NULL,
            Referencia nvarchar(1000) NULL,
            NombreOriginal nvarchar(500) NULL,
            MimeType nvarchar(150) NULL,
            Bytes bigint NULL,
            FechaCapturaUTC datetime2(3) NOT NULL CONSTRAINT DF_Sync_Control_Evidencias_FechaCapturaUTC DEFAULT (SYSUTCDATETIME()),
            CONSTRAINT PK_Sync_Control_Evidencias PRIMARY KEY CLUSTERED (EvidenciaID),
            CONSTRAINT FK_Sync_Control_Evidencias_Ejecucion FOREIGN KEY (SyncControlID) REFERENCES dbo.Sync_Control_Ejecuciones(SyncControlID),
            CONSTRAINT UQ_Sync_Control_Evidencias_RunHash UNIQUE (SyncControlID, HashSHA256),
            CONSTRAINT CK_Sync_Control_Evidencias_Bytes CHECK (Bytes IS NULL OR Bytes >= 0)
        );
    END;

    /* ------------------------------------------------------------
       5. Identificadores externos universales
       No columnas ToastLocationId/NetPayId dispersas.
       ------------------------------------------------------------ */
    IF OBJECT_ID('dbo.Sistema_IdentificadoresExternos','U') IS NULL
    BEGIN
        CREATE TABLE dbo.Sistema_IdentificadoresExternos
        (
            IdentificadorExternoID bigint IDENTITY(1,1) NOT NULL,
            UnidadNegocioID uniqueidentifier NULL,
            SistemaTipoID int NOT NULL,
            SistemaVersionID uniqueidentifier NULL,
            ConexionID uniqueidentifier NULL,
            TipoIdentificador nvarchar(80) NOT NULL,
            ValorExterno nvarchar(300) NOT NULL,
            Activo bit NOT NULL CONSTRAINT DF_Sistema_IdentificadoresExternos_Activo DEFAULT (1),
            FechaAlta datetime2(3) NOT NULL CONSTRAINT DF_Sistema_IdentificadoresExternos_FechaAlta DEFAULT (SYSUTCDATETIME()),
            FechaModificacion datetime2(3) NULL,
            CONSTRAINT PK_Sistema_IdentificadoresExternos PRIMARY KEY CLUSTERED (IdentificadorExternoID),
            CONSTRAINT FK_Sistema_IdentificadoresExternos_Unidad FOREIGN KEY (UnidadNegocioID) REFERENCES dbo.Unidades_Negocio(id),
            CONSTRAINT FK_Sistema_IdentificadoresExternos_Sistema FOREIGN KEY (SistemaTipoID) REFERENCES dbo.Sistema_Tipos(SistemaTipoID),
            CONSTRAINT FK_Sistema_IdentificadoresExternos_Version FOREIGN KEY (SistemaVersionID) REFERENCES dbo.Sistema_VersionesSistemas(sistema_version_id),
            CONSTRAINT FK_Sistema_IdentificadoresExternos_Conexion FOREIGN KEY (ConexionID) REFERENCES dbo.Servidores_Conexiones(id),
            CONSTRAINT CK_Sistema_IdentificadoresExternos_Contexto CHECK (UnidadNegocioID IS NOT NULL OR ConexionID IS NOT NULL),
            CONSTRAINT UQ_Sistema_IdentificadoresExternos_Valor UNIQUE (SistemaTipoID, TipoIdentificador, ValorExterno)
        );
    END;

    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.Sistema_IdentificadoresExternos') AND name='IX_Sistema_IdentificadoresExternos_UnidadSistema')
        EXEC(N'CREATE INDEX IX_Sistema_IdentificadoresExternos_UnidadSistema ON dbo.Sistema_IdentificadoresExternos(UnidadNegocioID, SistemaTipoID, Activo);');

    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.Sistema_IdentificadoresExternos') AND name='IX_Sistema_IdentificadoresExternos_Conexion')
        EXEC(N'CREATE INDEX IX_Sistema_IdentificadoresExternos_Conexion ON dbo.Sistema_IdentificadoresExternos(ConexionID, SistemaTipoID, Activo);');

    /* ------------------------------------------------------------
       6. Health real de conexion
       Se preservan UltimoCheck/ResponseTimeMs legacy.
       ------------------------------------------------------------ */
    IF COL_LENGTH('dbo.Servidores_ConexionEstado','UltimaPruebaUTC') IS NULL
        ALTER TABLE dbo.Servidores_ConexionEstado ADD UltimaPruebaUTC datetime2(3) NULL;
    IF COL_LENGTH('dbo.Servidores_ConexionEstado','UltimoExitoUTC') IS NULL
        ALTER TABLE dbo.Servidores_ConexionEstado ADD UltimoExitoUTC datetime2(3) NULL;
    IF COL_LENGTH('dbo.Servidores_ConexionEstado','UltimoErrorUTC') IS NULL
        ALTER TABLE dbo.Servidores_ConexionEstado ADD UltimoErrorUTC datetime2(3) NULL;
    IF COL_LENGTH('dbo.Servidores_ConexionEstado','UltimoErrorCodigo') IS NULL
        ALTER TABLE dbo.Servidores_ConexionEstado ADD UltimoErrorCodigo nvarchar(80) NULL;
    IF COL_LENGTH('dbo.Servidores_ConexionEstado','UltimoErrorMensaje') IS NULL
        ALTER TABLE dbo.Servidores_ConexionEstado ADD UltimoErrorMensaje nvarchar(1000) NULL;
    IF COL_LENGTH('dbo.Servidores_ConexionEstado','LatenciaMs') IS NULL
        ALTER TABLE dbo.Servidores_ConexionEstado ADD LatenciaMs int NULL;
    IF COL_LENGTH('dbo.Servidores_ConexionEstado','UltimoSyncUTC') IS NULL
        ALTER TABLE dbo.Servidores_ConexionEstado ADD UltimoSyncUTC datetime2(3) NULL;
    IF COL_LENGTH('dbo.Servidores_ConexionEstado','UltimoSyncExitosoUTC') IS NULL
        ALTER TABLE dbo.Servidores_ConexionEstado ADD UltimoSyncExitosoUTC datetime2(3) NULL;
    IF COL_LENGTH('dbo.Servidores_ConexionEstado','FechaActualizacionUTC') IS NULL
        ALTER TABLE dbo.Servidores_ConexionEstado ADD FechaActualizacionUTC datetime2(3) NULL;

    /* ------------------------------------------------------------
       7. Guardas de contrato
       ------------------------------------------------------------ */
    IF COL_LENGTH('dbo.Unidades_Negocio','timezone_iana') IS NULL OR COL_LENGTH('dbo.Unidades_Negocio','locale_operativo') IS NULL
        THROW 51000, 'GATE4B_UNIT_METADATA_NOT_CREATED', 1;
    IF OBJECT_ID('dbo.Sistema_Sync_Capacidades','U') IS NULL
        THROW 51000, 'GATE4B_SYNC_CAPABILITIES_NOT_CREATED', 1;
    IF OBJECT_ID('dbo.Sync_Control_Evidencias','U') IS NULL
        THROW 51000, 'GATE4B_EVIDENCE_NOT_CREATED', 1;
    IF OBJECT_ID('dbo.Sistema_IdentificadoresExternos','U') IS NULL
        THROW 51000, 'GATE4B_EXTERNAL_IDS_NOT_CREATED', 1;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
