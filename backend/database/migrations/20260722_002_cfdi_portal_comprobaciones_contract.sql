/*
EDARSAHUB V1.0 / CFDI, Portal Proveedores y Comprobaciones

Contrato:
- No MongoDB.
- No conexiones live para tableros, reportes ni portal.
- No conexion SAT en V1.0; SAT queda preparado para fases posteriores.
- Las carpetas del servidor son solo fuente de ingesta controlada inicial.
- El consumo funcional vive en EDARSAHUB SQL.
- No duplicar facturas por modulo: todo CFDI vive en Compras_DocumentosFiscales
  y Compras_DocumentosFiscalesDetalle.
- Caja, viaticos, fondos y comprobaciones agregan contexto financiero,
  no crean tablas paralelas de facturas.
- Portal proveedores V1.0 permite un usuario activo por proveedor; el modelo
  Proveedor_UsuariosPortal conserva capacidad multiusuario futura.

REVISION: script preparado para DBA. No ejecutar sin autorizacion explicita.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Unidades_Negocio', 'U') IS NULL
        THROW 52000, 'Falta tabla canonica dbo.Unidades_Negocio.', 1;

    IF OBJECT_ID('dbo.Proveedor_Catalogo', 'U') IS NULL
        THROW 52001, 'Falta tabla canonica dbo.Proveedor_Catalogo.', 1;

    IF OBJECT_ID('dbo.Proveedor_UsuariosPortal', 'U') IS NULL
        THROW 52002, 'Falta tabla canonica dbo.Proveedor_UsuariosPortal.', 1;

    IF OBJECT_ID('dbo.Compras_DocumentosFiscales', 'U') IS NULL
        THROW 52003, 'Falta tabla canonica dbo.Compras_DocumentosFiscales.', 1;

    IF OBJECT_ID('dbo.Compras_DocumentosFiscalesDetalle', 'U') IS NULL
        THROW 52004, 'Falta tabla canonica dbo.Compras_DocumentosFiscalesDetalle.', 1;

    IF OBJECT_ID('dbo.Compras_CFDI_RutasIngesta', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Compras_CFDI_RutasIngesta (
            RutaIngestaID INT IDENTITY(1,1) NOT NULL,
            UnidadNegocioID UNIQUEIDENTIFIER NULL,
            EmpresaCodigo NVARCHAR(50) NULL,
            TipoFuente NVARCHAR(40) NOT NULL,
            RutaOrigen NVARCHAR(1000) NOT NULL,
            RutaDestinoEdarsahub NVARCHAR(1000) NOT NULL,
            PatronXML NVARCHAR(120) NOT NULL
                CONSTRAINT DF_Compras_CFDI_RutasIngesta_PatronXML DEFAULT ('*.xml'),
            PatronPDF NVARCHAR(120) NOT NULL
                CONSTRAINT DF_Compras_CFDI_RutasIngesta_PatronPDF DEFAULT ('*.pdf'),
            ModoIngesta NVARCHAR(30) NOT NULL
                CONSTRAINT DF_Compras_CFDI_RutasIngesta_Modo DEFAULT ('SOLO_REGISTRAR'),
            Activo BIT NOT NULL
                CONSTRAINT DF_Compras_CFDI_RutasIngesta_Activo DEFAULT (1),
            FechaAlta DATETIME2(0) NOT NULL
                CONSTRAINT DF_Compras_CFDI_RutasIngesta_FechaAlta DEFAULT (SYSUTCDATETIME()),
            FechaModificacion DATETIME2(0) NULL,
            CreatedBy NVARCHAR(100) NULL,
            ModifiedBy NVARCHAR(100) NULL,

            CONSTRAINT PK_Compras_CFDI_RutasIngesta
                PRIMARY KEY CLUSTERED (RutaIngestaID),
            CONSTRAINT CK_Compras_CFDI_RutasIngesta_TipoFuente
                CHECK (TipoFuente IN ('CARPETA_SERVIDOR', 'PORTAL_PROVEEDOR', 'TAB_COMPROBACION')),
            CONSTRAINT CK_Compras_CFDI_RutasIngesta_Modo
                CHECK (ModoIngesta IN ('SOLO_REGISTRAR', 'COPIAR_A_EDARSAHUB', 'MOVER_A_EDARSAHUB')),
            CONSTRAINT FK_Compras_CFDI_RutasIngesta_UnidadNegocio
                FOREIGN KEY (UnidadNegocioID) REFERENCES dbo.Unidades_Negocio(id)
        );
    END;

    IF OBJECT_ID('dbo.Compras_DocumentosFiscalesRelaciones', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Compras_DocumentosFiscalesRelaciones (
            DocumentoFiscalRelacionID BIGINT IDENTITY(1,1) NOT NULL,
            DocumentoFiscalID BIGINT NOT NULL,
            TipoContexto NVARCHAR(40) NOT NULL,
            EntidadID NVARCHAR(80) NOT NULL,
            EntidadClave NVARCHAR(120) NULL,
            UnidadNegocioID UNIQUEIDENTIFIER NOT NULL,
            ProveedorID INT NULL,
            UsuarioResponsableID INT NULL,
            MontoAplicado DECIMAL(18,2) NOT NULL
                CONSTRAINT DF_Compras_DocFiscalRel_MontoAplicado DEFAULT (0),
            EstatusAplicacion NVARCHAR(30) NOT NULL
                CONSTRAINT DF_Compras_DocFiscalRel_Estatus DEFAULT ('PENDIENTE'),
            OrigenCarga NVARCHAR(30) NOT NULL,
            Activo BIT NOT NULL
                CONSTRAINT DF_Compras_DocFiscalRel_Activo DEFAULT (1),
            FechaAlta DATETIME2(0) NOT NULL
                CONSTRAINT DF_Compras_DocFiscalRel_FechaAlta DEFAULT (SYSUTCDATETIME()),
            FechaModificacion DATETIME2(0) NULL,
            CreatedBy NVARCHAR(100) NULL,
            ModifiedBy NVARCHAR(100) NULL,

            CONSTRAINT PK_Compras_DocumentosFiscalesRelaciones
                PRIMARY KEY CLUSTERED (DocumentoFiscalRelacionID),
            CONSTRAINT CK_Compras_DocFiscalRel_TipoContexto
                CHECK (TipoContexto IN (
                    'ORDEN_COMPRA', 'PEDIDO', 'REQUISITO', 'RECEPCION', 'CXP',
                    'COMPROBACION', 'FONDO_REVOLVENTE', 'VIATICO',
                    'GASTO_POR_COMPROBAR', 'REEMBOLSO'
                )),
            CONSTRAINT CK_Compras_DocFiscalRel_Estatus
                CHECK (EstatusAplicacion IN (
                    'PENDIENTE', 'CONCILIADO', 'OBSERVADO',
                    'RECHAZADO', 'CERRADO', 'CANCELADO'
                )),
            CONSTRAINT CK_Compras_DocFiscalRel_OrigenCarga
                CHECK (OrigenCarga IN (
                    'INGESTA_SERVIDOR', 'PORTAL_PROVEEDOR', 'TAB_COMPROBACION', 'SYNC_CXP'
                )),
            CONSTRAINT FK_Compras_DocFiscalRel_DocumentoFiscal
                FOREIGN KEY (DocumentoFiscalID) REFERENCES dbo.Compras_DocumentosFiscales(DocumentoFiscalID),
            CONSTRAINT FK_Compras_DocFiscalRel_UnidadNegocio
                FOREIGN KEY (UnidadNegocioID) REFERENCES dbo.Unidades_Negocio(id),
            CONSTRAINT FK_Compras_DocFiscalRel_Proveedor
                FOREIGN KEY (ProveedorID) REFERENCES dbo.Proveedor_Catalogo(ProveedorID)
        );
    END;

    IF OBJECT_ID('dbo.Finanzas_Comprobaciones', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Finanzas_Comprobaciones (
            ComprobacionID BIGINT IDENTITY(1,1) NOT NULL,
            UnidadNegocioID UNIQUEIDENTIFIER NOT NULL,
            UsuarioResponsableID INT NOT NULL,
            TipoComprobacion NVARCHAR(40) NOT NULL,
            ReferenciaOperacion NVARCHAR(120) NULL,
            MontoEntregado DECIMAL(18,2) NOT NULL
                CONSTRAINT DF_Finanzas_Comprobaciones_MontoEntregado DEFAULT (0),
            MontoComprobado DECIMAL(18,2) NOT NULL
                CONSTRAINT DF_Finanzas_Comprobaciones_MontoComprobado DEFAULT (0),
            MontoReembolsar DECIMAL(18,2) NOT NULL
                CONSTRAINT DF_Finanzas_Comprobaciones_MontoReembolsar DEFAULT (0),
            MontoReintegrar DECIMAL(18,2) NOT NULL
                CONSTRAINT DF_Finanzas_Comprobaciones_MontoReintegrar DEFAULT (0),
            EstadoComprobacion NVARCHAR(30) NOT NULL
                CONSTRAINT DF_Finanzas_Comprobaciones_Estado DEFAULT ('ABIERTA'),
            RequiereAutorizacion BIT NOT NULL
                CONSTRAINT DF_Finanzas_Comprobaciones_RequiereAut DEFAULT (1),
            AutorizadoPorUsuarioID INT NULL,
            FechaAutorizacion DATETIME2(0) NULL,
            CerradoPorUsuarioID INT NULL,
            FechaCierre DATETIME2(0) NULL,
            Observaciones NVARCHAR(1000) NULL,
            Activo BIT NOT NULL
                CONSTRAINT DF_Finanzas_Comprobaciones_Activo DEFAULT (1),
            FechaAlta DATETIME2(0) NOT NULL
                CONSTRAINT DF_Finanzas_Comprobaciones_FechaAlta DEFAULT (SYSUTCDATETIME()),
            FechaModificacion DATETIME2(0) NULL,
            CreatedBy NVARCHAR(100) NULL,
            ModifiedBy NVARCHAR(100) NULL,

            CONSTRAINT PK_Finanzas_Comprobaciones
                PRIMARY KEY CLUSTERED (ComprobacionID),
            CONSTRAINT CK_Finanzas_Comprobaciones_Tipo
                CHECK (TipoComprobacion IN (
                    'CAJA_CHICA', 'FONDO_REVOLVENTE', 'VIATICO',
                    'GASTO_POR_COMPROBAR', 'REEMBOLSO'
                )),
            CONSTRAINT CK_Finanzas_Comprobaciones_Estado
                CHECK (EstadoComprobacion IN (
                    'ABIERTA', 'PENDIENTE_AUTORIZACION', 'AUTORIZADA',
                    'OBSERVADA', 'RECHAZADA', 'CERRADA', 'CANCELADA'
                )),
            CONSTRAINT CK_Finanzas_Comprobaciones_Montos
                CHECK (
                    MontoEntregado >= 0 AND MontoComprobado >= 0
                    AND MontoReembolsar >= 0 AND MontoReintegrar >= 0
                ),
            CONSTRAINT FK_Finanzas_Comprobaciones_UnidadNegocio
                FOREIGN KEY (UnidadNegocioID) REFERENCES dbo.Unidades_Negocio(id)
        );
    END;

    IF OBJECT_ID('dbo.Finanzas_ComprobacionesDocumentos', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Finanzas_ComprobacionesDocumentos (
            ComprobacionDocumentoID BIGINT IDENTITY(1,1) NOT NULL,
            ComprobacionID BIGINT NOT NULL,
            DocumentoFiscalID BIGINT NOT NULL,
            MontoAplicado DECIMAL(18,2) NOT NULL,
            EstatusDocumento NVARCHAR(30) NOT NULL
                CONSTRAINT DF_Finanzas_ComprobacionesDocs_Estatus DEFAULT ('PENDIENTE'),
            Observaciones NVARCHAR(1000) NULL,
            Activo BIT NOT NULL
                CONSTRAINT DF_Finanzas_ComprobacionesDocs_Activo DEFAULT (1),
            FechaAlta DATETIME2(0) NOT NULL
                CONSTRAINT DF_Finanzas_ComprobacionesDocs_FechaAlta DEFAULT (SYSUTCDATETIME()),
            FechaModificacion DATETIME2(0) NULL,
            CreatedBy NVARCHAR(100) NULL,
            ModifiedBy NVARCHAR(100) NULL,

            CONSTRAINT PK_Finanzas_ComprobacionesDocumentos
                PRIMARY KEY CLUSTERED (ComprobacionDocumentoID),
            CONSTRAINT CK_Finanzas_ComprobacionesDocs_Monto CHECK (MontoAplicado > 0),
            CONSTRAINT CK_Finanzas_ComprobacionesDocs_Estatus
                CHECK (EstatusDocumento IN (
                    'PENDIENTE', 'VALIDADO', 'OBSERVADO', 'RECHAZADO', 'CANCELADO'
                )),
            CONSTRAINT FK_Finanzas_ComprobacionesDocs_Comprobacion
                FOREIGN KEY (ComprobacionID) REFERENCES dbo.Finanzas_Comprobaciones(ComprobacionID),
            CONSTRAINT FK_Finanzas_ComprobacionesDocs_DocumentoFiscal
                FOREIGN KEY (DocumentoFiscalID) REFERENCES dbo.Compras_DocumentosFiscales(DocumentoFiscalID)
        );
    END;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE name = 'UX_Proveedor_UsuariosPortal_UnActivo_V10'
          AND object_id = OBJECT_ID('dbo.Proveedor_UsuariosPortal')
    )
    BEGIN
        CREATE UNIQUE INDEX UX_Proveedor_UsuariosPortal_UnActivo_V10
        ON dbo.Proveedor_UsuariosPortal(ProveedorID)
        WHERE Activo = 1;
    END;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE name = 'UX_Compras_DocumentosFiscales_UUID_Activo'
          AND object_id = OBJECT_ID('dbo.Compras_DocumentosFiscales')
    )
    BEGIN
        CREATE UNIQUE INDEX UX_Compras_DocumentosFiscales_UUID_Activo
        ON dbo.Compras_DocumentosFiscales(UUID)
        WHERE Activo = 1;
    END;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE name = 'IX_Compras_CFDI_RutasIngesta_Activo'
          AND object_id = OBJECT_ID('dbo.Compras_CFDI_RutasIngesta')
    )
    BEGIN
        CREATE INDEX IX_Compras_CFDI_RutasIngesta_Activo
        ON dbo.Compras_CFDI_RutasIngesta(Activo, TipoFuente, UnidadNegocioID)
        INCLUDE (RutaOrigen, RutaDestinoEdarsahub, ModoIngesta);
    END;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE name = 'IX_Compras_DocFiscalRel_Contexto'
          AND object_id = OBJECT_ID('dbo.Compras_DocumentosFiscalesRelaciones')
    )
    BEGIN
        CREATE INDEX IX_Compras_DocFiscalRel_Contexto
        ON dbo.Compras_DocumentosFiscalesRelaciones(TipoContexto, EntidadID, Activo)
        INCLUDE (DocumentoFiscalID, UnidadNegocioID, MontoAplicado, EstatusAplicacion);
    END;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE name = 'UX_Compras_DocFiscalRel_Doc_Contexto_Activo'
          AND object_id = OBJECT_ID('dbo.Compras_DocumentosFiscalesRelaciones')
    )
    BEGIN
        CREATE UNIQUE INDEX UX_Compras_DocFiscalRel_Doc_Contexto_Activo
        ON dbo.Compras_DocumentosFiscalesRelaciones(DocumentoFiscalID, TipoContexto, EntidadID)
        WHERE Activo = 1;
    END;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE name = 'IX_Finanzas_Comprobaciones_Responsable_Abiertas'
          AND object_id = OBJECT_ID('dbo.Finanzas_Comprobaciones')
    )
    BEGIN
        CREATE INDEX IX_Finanzas_Comprobaciones_Responsable_Abiertas
        ON dbo.Finanzas_Comprobaciones(UsuarioResponsableID, UnidadNegocioID, EstadoComprobacion, Activo)
        INCLUDE (TipoComprobacion, MontoEntregado, MontoComprobado, MontoReembolsar, MontoReintegrar);
    END;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE name = 'UX_Finanzas_Comprobaciones_Bloqueo_Abierta'
          AND object_id = OBJECT_ID('dbo.Finanzas_Comprobaciones')
    )
    BEGIN
        CREATE UNIQUE INDEX UX_Finanzas_Comprobaciones_Bloqueo_Abierta
        ON dbo.Finanzas_Comprobaciones(UsuarioResponsableID, UnidadNegocioID, TipoComprobacion)
        WHERE Activo = 1
          AND EstadoComprobacion <> 'CERRADA'
          AND EstadoComprobacion <> 'CANCELADA'
          AND EstadoComprobacion <> 'RECHAZADA';
    END;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE name = 'UX_Finanzas_ComprobacionesDocs_Doc_Activo'
          AND object_id = OBJECT_ID('dbo.Finanzas_ComprobacionesDocumentos')
    )
    BEGIN
        CREATE UNIQUE INDEX UX_Finanzas_ComprobacionesDocs_Doc_Activo
        ON dbo.Finanzas_ComprobacionesDocumentos(ComprobacionID, DocumentoFiscalID)
        WHERE Activo = 1;
    END;

    COMMIT TRANSACTION;

    SELECT
        'OK' AS Estatus,
        OBJECT_ID('dbo.Compras_CFDI_RutasIngesta') AS ComprasCFDIRutasIngestaObjectID,
        OBJECT_ID('dbo.Compras_DocumentosFiscalesRelaciones') AS ComprasDocumentosFiscalesRelacionesObjectID,
        OBJECT_ID('dbo.Finanzas_Comprobaciones') AS FinanzasComprobacionesObjectID,
        OBJECT_ID('dbo.Finanzas_ComprobacionesDocumentos') AS FinanzasComprobacionesDocumentosObjectID;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
