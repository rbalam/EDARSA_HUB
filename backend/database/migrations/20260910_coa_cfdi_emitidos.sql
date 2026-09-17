/*
COA Gate 5E - MIGRACION CFDI EMITIDOS
DESIGN ONLY - NO EJECUTAR EN ESTE GATE
Base: Gates 5C + 5D.
*/
SET XACT_ABORT ON;

BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Fiscal_DocumentosEmitidosEstatus','U') IS NOT NULL
        THROW 51000, 'COLLISION: dbo.Fiscal_DocumentosEmitidosEstatus ya existe', 1;

    IF OBJECT_ID('dbo.Fiscal_DocumentosEmitidos','U') IS NOT NULL
        THROW 51000, 'COLLISION: dbo.Fiscal_DocumentosEmitidos ya existe', 1;

    IF COL_LENGTH('dbo.COA_ExpedienteReferencias','VentaID') IS NOT NULL
        THROW 51000, 'COLLISION: COA_ExpedienteReferencias.VentaID ya existe', 1;

    IF COL_LENGTH('dbo.COA_ExpedienteReferencias','DocumentoFiscalEmitidoID') IS NOT NULL
        THROW 51000, 'COLLISION: COA_ExpedienteReferencias.DocumentoFiscalEmitidoID ya existe', 1;

    IF OBJECT_ID('dbo.CK_COA_ExpedienteReferencias_UnSoloDestino','C') IS NULL
        THROW 51000, 'PRECONDITION: falta CK_COA_ExpedienteReferencias_UnSoloDestino', 1;

    CREATE TABLE dbo.Fiscal_DocumentosEmitidosEstatus (
        EstatusDocumentoFiscalEmitidoID tinyint NOT NULL,
        Codigo varchar(30) NOT NULL,
        Nombre nvarchar(100) NOT NULL,
        Descripcion nvarchar(500) NULL,
        EsFinal bit NOT NULL CONSTRAINT DF_Fiscal_DocumentosEmitidosEstatus_EsFinal DEFAULT ((0)),
        Activo bit NOT NULL CONSTRAINT DF_Fiscal_DocumentosEmitidosEstatus_Activo DEFAULT ((1)),
        CONSTRAINT PK_Fiscal_DocumentosEmitidosEstatus PRIMARY KEY (EstatusDocumentoFiscalEmitidoID),
        CONSTRAINT UQ_Fiscal_DocumentosEmitidosEstatus_Codigo UNIQUE (Codigo)
    );

    CREATE TABLE dbo.Fiscal_DocumentosEmitidos (
        DocumentoFiscalEmitidoID bigint IDENTITY(1,1) NOT NULL,
        EmpresaID int NOT NULL,
        UnidadNegocioID uniqueidentifier NULL,
        ClienteID int NOT NULL,
        VentaID bigint NULL,
        EstatusDocumentoFiscalEmitidoID tinyint NOT NULL,
        UUID varchar(36) NULL,
        TipoComprobante varchar(5) NULL,
        Serie varchar(25) NULL,
        Folio varchar(40) NULL,
        FechaEmision datetime2(3) NULL,
        FechaTimbrado datetime2(3) NULL,
        FechaCancelacion datetime2(3) NULL,
        RFCEmisor varchar(13) NULL,
        RFCReceptor varchar(13) NULL,
        MonedaID smallint NULL,
        TipoCambio decimal(19,6) NULL,
        Subtotal decimal(19,4) NULL,
        Descuento decimal(19,4) NULL,
        ImpuestoTrasladado decimal(19,4) NULL,
        ImpuestoRetenido decimal(19,4) NULL,
        Total decimal(19,4) NULL,
        MetodoPago varchar(10) NULL,
        FormaPago varchar(10) NULL,
        UsoCFDI varchar(10) NULL,
        VersionCFDI varchar(10) NULL,
        EstatusSAT varchar(30) NULL,
        RutaXML varchar(500) NULL,
        RutaPDF varchar(500) NULL,
        NombreArchivoXML varchar(255) NULL,
        NombreArchivoPDF varchar(255) NULL,
        HashXML varchar(128) NULL,
        HashPDF varchar(128) NULL,
        OrigenDocumento varchar(30) NULL,
        Observaciones nvarchar(1000) NULL,
        FechaAlta datetime2(3) NOT NULL CONSTRAINT DF_Fiscal_DocumentosEmitidos_FechaAlta DEFAULT (sysutcdatetime()),
        FechaModificacion datetime2(3) NULL,
        CreadoPorUsuarioID int NULL,
        ModificadoPorUsuarioID int NULL,
        Activo bit NOT NULL CONSTRAINT DF_Fiscal_DocumentosEmitidos_Activo DEFAULT ((1)),
        CONSTRAINT PK_Fiscal_DocumentosEmitidos PRIMARY KEY (DocumentoFiscalEmitidoID),
        CONSTRAINT FK_Fiscal_DocumentosEmitidos_Empresa FOREIGN KEY (EmpresaID) REFERENCES dbo.Sistema_Empresas(EmpresaID),
        CONSTRAINT FK_Fiscal_DocumentosEmitidos_Unidad FOREIGN KEY (UnidadNegocioID) REFERENCES dbo.Unidades_Negocio(id),
        CONSTRAINT FK_Fiscal_DocumentosEmitidos_Cliente FOREIGN KEY (ClienteID) REFERENCES dbo.Cliente_Catalogo(ClienteID),
        CONSTRAINT FK_Fiscal_DocumentosEmitidos_Venta FOREIGN KEY (VentaID) REFERENCES dbo.Venta_Encabezado(VentaID),
        CONSTRAINT FK_Fiscal_DocumentosEmitidos_Estatus FOREIGN KEY (EstatusDocumentoFiscalEmitidoID) REFERENCES dbo.Fiscal_DocumentosEmitidosEstatus(EstatusDocumentoFiscalEmitidoID),
        CONSTRAINT FK_Fiscal_DocumentosEmitidos_Moneda FOREIGN KEY (MonedaID) REFERENCES dbo.Proveedor_Monedas(MonedaID),
        CONSTRAINT FK_Fiscal_DocumentosEmitidos_CreadoPor FOREIGN KEY (CreadoPorUsuarioID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
        CONSTRAINT FK_Fiscal_DocumentosEmitidos_ModificadoPor FOREIGN KEY (ModificadoPorUsuarioID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
        CONSTRAINT CK_Fiscal_DocumentosEmitidos_Fechas CHECK (FechaCancelacion IS NULL OR FechaEmision IS NULL OR FechaCancelacion >= FechaEmision),
        CONSTRAINT CK_Fiscal_DocumentosEmitidos_Total CHECK (Total IS NULL OR Total >= 0)
    );

    CREATE UNIQUE INDEX UX_Fiscal_DocumentosEmitidos_UUID ON dbo.Fiscal_DocumentosEmitidos(UUID) WHERE UUID IS NOT NULL;
    CREATE INDEX IX_Fiscal_DocumentosEmitidos_Cliente_Fecha ON dbo.Fiscal_DocumentosEmitidos(ClienteID, FechaEmision);
    CREATE INDEX IX_Fiscal_DocumentosEmitidos_Empresa_Estatus ON dbo.Fiscal_DocumentosEmitidos(EmpresaID, EstatusDocumentoFiscalEmitidoID, Activo);
    CREATE INDEX IX_Fiscal_DocumentosEmitidos_Unidad ON dbo.Fiscal_DocumentosEmitidos(UnidadNegocioID) WHERE UnidadNegocioID IS NOT NULL;
    CREATE INDEX IX_Fiscal_DocumentosEmitidos_Venta ON dbo.Fiscal_DocumentosEmitidos(VentaID) WHERE VentaID IS NOT NULL;

    ALTER TABLE dbo.COA_ExpedienteReferencias ADD
        VentaID bigint NULL,
        DocumentoFiscalEmitidoID bigint NULL;

GO

    ALTER TABLE dbo.COA_ExpedienteReferencias ADD
        CONSTRAINT FK_COA_ExpedienteReferencias_Venta FOREIGN KEY (VentaID) REFERENCES dbo.Venta_Encabezado(VentaID),
        CONSTRAINT FK_COA_ExpedienteReferencias_DocumentoFiscalEmitido FOREIGN KEY (DocumentoFiscalEmitidoID) REFERENCES dbo.Fiscal_DocumentosEmitidos(DocumentoFiscalEmitidoID);

    CREATE INDEX IX_COA_ExpedienteReferencias_Venta ON dbo.COA_ExpedienteReferencias(VentaID) WHERE VentaID IS NOT NULL;
    CREATE INDEX IX_COA_ExpedienteReferencias_DocumentoFiscalEmitido ON dbo.COA_ExpedienteReferencias(DocumentoFiscalEmitidoID) WHERE DocumentoFiscalEmitidoID IS NOT NULL;

    ALTER TABLE dbo.COA_ExpedienteReferencias DROP CONSTRAINT CK_COA_ExpedienteReferencias_UnSoloDestino;

    ALTER TABLE dbo.COA_ExpedienteReferencias ADD CONSTRAINT CK_COA_ExpedienteReferencias_UnSoloDestino CHECK (
        (CASE WHEN ClienteID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN ProveedorID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN DocumentoFiscalID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN PagoID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN DecisionPagoID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN NominaID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN DispersionNominaID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN NominaReciboID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN ColaboradorID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN ContratoID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN VentaID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN DocumentoFiscalEmitidoID IS NULL THEN 0 ELSE 1 END) = 1
    );

    COMMIT TRANSACTION;
