/*
EDARSAHUB Finanzas / CxP
Tabla canonica de decisiones de pago.
Incluye contrato de autorizacion y cola de salida para carga posterior
a sistemas origen sin conexiones live desde el tablero.

Reglas:
- No MongoDB.
- No conexiones live.
- No datos demo.
- La lectura de facturas viene de dbo.Finanzas_CxP_Sync.
- Las decisiones NO se guardan en Finanzas_CxP_Sync porque el job la refresca.
- La llave estable es HashOrigen; CxpSyncID solo queda como ultimo id visto.
- FK canonica de unidad: dbo.Unidades_Negocio(id).
- La carga a origen se prepara en queue; un proceso autorizado posterior debe
  consumirla con guardrails, RBAC y auditoria. Esta migracion no ejecuta envios.

REVISION: ejecutar solo con autorizacion DBA/produccion correspondiente.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Finanzas_CxP_Sync', 'U') IS NULL
    BEGIN
        THROW 51000, 'Falta tabla canonica dbo.Finanzas_CxP_Sync.', 1;
    END;

    IF OBJECT_ID('dbo.Unidades_Negocio', 'U') IS NULL
    BEGIN
        THROW 51001, 'Falta tabla canonica dbo.Unidades_Negocio.', 1;
    END;

    IF OBJECT_ID('dbo.Finanzas_CxP_DecisionesPago', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Finanzas_CxP_DecisionesPago (
            DecisionPagoID BIGINT IDENTITY(1,1) NOT NULL,
            HashOrigen NVARCHAR(64) NOT NULL,
            CxpSyncID BIGINT NULL,
            UnidadNegocioID UNIQUEIDENTIFIER NOT NULL,
            DecisionPago BIT NOT NULL
                CONSTRAINT DF_Finanzas_CxP_DecisionesPago_DecisionPago DEFAULT (0),
            ImporteAPagar DECIMAL(18,2) NOT NULL
                CONSTRAINT DF_Finanzas_CxP_DecisionesPago_ImporteAPagar DEFAULT (0),
            UsuarioID INT NULL,
            EstadoAutorizacion NVARCHAR(30) NOT NULL
                CONSTRAINT DF_Finanzas_CxP_DecisionesPago_EstadoAutorizacion DEFAULT ('PENDIENTE_AUTORIZACION'),
            AutorizadoPorUsuarioID INT NULL,
            FechaAutorizacion DATETIME2(0) NULL,
            RechazadoPorUsuarioID INT NULL,
            FechaRechazo DATETIME2(0) NULL,
            ComentarioAutorizacion NVARCHAR(500) NULL,
            Activo BIT NOT NULL
                CONSTRAINT DF_Finanzas_CxP_DecisionesPago_Activo DEFAULT (1),
            FechaDecision DATETIME2(0) NOT NULL
                CONSTRAINT DF_Finanzas_CxP_DecisionesPago_FechaDecision DEFAULT (SYSUTCDATETIME()),
            FechaAlta DATETIME2(0) NOT NULL
                CONSTRAINT DF_Finanzas_CxP_DecisionesPago_FechaAlta DEFAULT (SYSUTCDATETIME()),
            FechaModificacion DATETIME2(0) NULL,

            CONSTRAINT PK_Finanzas_CxP_DecisionesPago
                PRIMARY KEY CLUSTERED (DecisionPagoID),

            CONSTRAINT CK_Finanzas_CxP_DecisionesPago_Importe
                CHECK (ImporteAPagar >= 0),

            CONSTRAINT CK_Finanzas_CxP_DecisionesPago_EstadoAutorizacion
                CHECK (EstadoAutorizacion IN (
                    'PENDIENTE_AUTORIZACION',
                    'AUTORIZADO',
                    'RECHAZADO',
                    'CANCELADO'
                )),

            CONSTRAINT FK_Finanzas_CxP_DecisionesPago_UnidadNegocio
                FOREIGN KEY (UnidadNegocioID)
                REFERENCES dbo.Unidades_Negocio(id)
        );
    END;

    IF COL_LENGTH('dbo.Finanzas_CxP_DecisionesPago', 'EstadoAutorizacion') IS NULL
    BEGIN
        ALTER TABLE dbo.Finanzas_CxP_DecisionesPago
        ADD EstadoAutorizacion NVARCHAR(30) NOT NULL
            CONSTRAINT DF_Finanzas_CxP_DecisionesPago_EstadoAutorizacion DEFAULT ('PENDIENTE_AUTORIZACION');
    END;

    IF COL_LENGTH('dbo.Finanzas_CxP_DecisionesPago', 'AutorizadoPorUsuarioID') IS NULL
    BEGIN
        ALTER TABLE dbo.Finanzas_CxP_DecisionesPago
        ADD AutorizadoPorUsuarioID INT NULL;
    END;

    IF COL_LENGTH('dbo.Finanzas_CxP_DecisionesPago', 'FechaAutorizacion') IS NULL
    BEGIN
        ALTER TABLE dbo.Finanzas_CxP_DecisionesPago
        ADD FechaAutorizacion DATETIME2(0) NULL;
    END;

    IF COL_LENGTH('dbo.Finanzas_CxP_DecisionesPago', 'RechazadoPorUsuarioID') IS NULL
    BEGIN
        ALTER TABLE dbo.Finanzas_CxP_DecisionesPago
        ADD RechazadoPorUsuarioID INT NULL;
    END;

    IF COL_LENGTH('dbo.Finanzas_CxP_DecisionesPago', 'FechaRechazo') IS NULL
    BEGIN
        ALTER TABLE dbo.Finanzas_CxP_DecisionesPago
        ADD FechaRechazo DATETIME2(0) NULL;
    END;

    IF COL_LENGTH('dbo.Finanzas_CxP_DecisionesPago', 'ComentarioAutorizacion') IS NULL
    BEGIN
        ALTER TABLE dbo.Finanzas_CxP_DecisionesPago
        ADD ComentarioAutorizacion NVARCHAR(500) NULL;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.check_constraints
        WHERE name = 'CK_Finanzas_CxP_DecisionesPago_EstadoAutorizacion'
          AND parent_object_id = OBJECT_ID('dbo.Finanzas_CxP_DecisionesPago')
    )
    BEGIN
        ALTER TABLE dbo.Finanzas_CxP_DecisionesPago
        ADD CONSTRAINT CK_Finanzas_CxP_DecisionesPago_EstadoAutorizacion
            CHECK (EstadoAutorizacion IN (
                'PENDIENTE_AUTORIZACION',
                'AUTORIZADO',
                'RECHAZADO',
                'CANCELADO'
            ));
    END;

    IF COL_LENGTH('dbo.Finanzas_CxP_DecisionesPago', 'HashOrigen') IS NULL
       OR COL_LENGTH('dbo.Finanzas_CxP_DecisionesPago', 'DecisionPago') IS NULL
       OR COL_LENGTH('dbo.Finanzas_CxP_DecisionesPago', 'ImporteAPagar') IS NULL
       OR COL_LENGTH('dbo.Finanzas_CxP_DecisionesPago', 'UnidadNegocioID') IS NULL
       OR COL_LENGTH('dbo.Finanzas_CxP_DecisionesPago', 'EstadoAutorizacion') IS NULL
    BEGIN
        THROW 51002, 'dbo.Finanzas_CxP_DecisionesPago existe pero no cumple el contrato canonico.', 1;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE name = 'UX_Finanzas_CxP_DecisionesPago_HashOrigen_Activo'
          AND object_id = OBJECT_ID('dbo.Finanzas_CxP_DecisionesPago')
    )
    BEGIN
        CREATE UNIQUE INDEX UX_Finanzas_CxP_DecisionesPago_HashOrigen_Activo
        ON dbo.Finanzas_CxP_DecisionesPago(HashOrigen)
        WHERE Activo = 1;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE name = 'IX_Finanzas_CxP_DecisionesPago_Unidad'
          AND object_id = OBJECT_ID('dbo.Finanzas_CxP_DecisionesPago')
    )
    BEGIN
        CREATE INDEX IX_Finanzas_CxP_DecisionesPago_Unidad
        ON dbo.Finanzas_CxP_DecisionesPago(UnidadNegocioID, Activo)
        INCLUDE (DecisionPago, ImporteAPagar, FechaDecision);
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE name = 'IX_Finanzas_CxP_DecisionesPago_CxpSyncID'
          AND object_id = OBJECT_ID('dbo.Finanzas_CxP_DecisionesPago')
    )
    BEGIN
        CREATE INDEX IX_Finanzas_CxP_DecisionesPago_CxpSyncID
        ON dbo.Finanzas_CxP_DecisionesPago(CxpSyncID)
        WHERE CxpSyncID IS NOT NULL;
    END;

    IF OBJECT_ID('dbo.Finanzas_CxP_PagosOrigenQueue', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Finanzas_CxP_PagosOrigenQueue (
            PagoOrigenQueueID BIGINT IDENTITY(1,1) NOT NULL,
            DecisionPagoID BIGINT NOT NULL,
            HashOrigen NVARCHAR(64) NOT NULL,
            UnidadNegocioID UNIQUEIDENTIFIER NOT NULL,
            CxpSyncID BIGINT NULL,
            ImporteAPagar DECIMAL(18,2) NOT NULL,
            EstadoEnvio NVARCHAR(30) NOT NULL
                CONSTRAINT DF_Finanzas_CxP_PagosOrigenQueue_EstadoEnvio DEFAULT ('PENDIENTE'),
            Intentos INT NOT NULL
                CONSTRAINT DF_Finanzas_CxP_PagosOrigenQueue_Intentos DEFAULT (0),
            UltimoError NVARCHAR(1000) NULL,
            FechaProgramada DATETIME2(0) NULL,
            FechaUltimoIntento DATETIME2(0) NULL,
            FechaEnviado DATETIME2(0) NULL,
            UsuarioAutorizacionID INT NULL,
            Activo BIT NOT NULL
                CONSTRAINT DF_Finanzas_CxP_PagosOrigenQueue_Activo DEFAULT (1),
            FechaAlta DATETIME2(0) NOT NULL
                CONSTRAINT DF_Finanzas_CxP_PagosOrigenQueue_FechaAlta DEFAULT (SYSUTCDATETIME()),
            FechaModificacion DATETIME2(0) NULL,

            CONSTRAINT PK_Finanzas_CxP_PagosOrigenQueue
                PRIMARY KEY CLUSTERED (PagoOrigenQueueID),

            CONSTRAINT CK_Finanzas_CxP_PagosOrigenQueue_Importe
                CHECK (ImporteAPagar > 0),

            CONSTRAINT CK_Finanzas_CxP_PagosOrigenQueue_EstadoEnvio
                CHECK (EstadoEnvio IN (
                    'PENDIENTE',
                    'EN_PROCESO',
                    'ENVIADO',
                    'ERROR',
                    'CANCELADO'
                )),

            CONSTRAINT FK_Finanzas_CxP_PagosOrigenQueue_Decision
                FOREIGN KEY (DecisionPagoID)
                REFERENCES dbo.Finanzas_CxP_DecisionesPago(DecisionPagoID),

            CONSTRAINT FK_Finanzas_CxP_PagosOrigenQueue_UnidadNegocio
                FOREIGN KEY (UnidadNegocioID)
                REFERENCES dbo.Unidades_Negocio(id)
        );
    END;

    IF COL_LENGTH('dbo.Finanzas_CxP_PagosOrigenQueue', 'DecisionPagoID') IS NULL
       OR COL_LENGTH('dbo.Finanzas_CxP_PagosOrigenQueue', 'HashOrigen') IS NULL
       OR COL_LENGTH('dbo.Finanzas_CxP_PagosOrigenQueue', 'ImporteAPagar') IS NULL
       OR COL_LENGTH('dbo.Finanzas_CxP_PagosOrigenQueue', 'EstadoEnvio') IS NULL
    BEGIN
        THROW 51003, 'dbo.Finanzas_CxP_PagosOrigenQueue existe pero no cumple el contrato canonico.', 1;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE name = 'IX_Finanzas_CxP_PagosOrigenQueue_Estado'
          AND object_id = OBJECT_ID('dbo.Finanzas_CxP_PagosOrigenQueue')
    )
    BEGIN
        CREATE INDEX IX_Finanzas_CxP_PagosOrigenQueue_Estado
        ON dbo.Finanzas_CxP_PagosOrigenQueue(EstadoEnvio, Activo, FechaProgramada)
        INCLUDE (DecisionPagoID, UnidadNegocioID, ImporteAPagar);
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE name = 'IX_Finanzas_CxP_PagosOrigenQueue_Decision'
          AND object_id = OBJECT_ID('dbo.Finanzas_CxP_PagosOrigenQueue')
    )
    BEGIN
        CREATE INDEX IX_Finanzas_CxP_PagosOrigenQueue_Decision
        ON dbo.Finanzas_CxP_PagosOrigenQueue(DecisionPagoID, Activo);
    END;

    COMMIT TRANSACTION;

    SELECT
        'OK' AS Estatus,
        OBJECT_ID('dbo.Finanzas_CxP_DecisionesPago') AS FinanzasCxPDecisionesPagoObjectID,
        OBJECT_ID('dbo.Finanzas_CxP_PagosOrigenQueue') AS FinanzasCxPPagosOrigenQueueObjectID;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
