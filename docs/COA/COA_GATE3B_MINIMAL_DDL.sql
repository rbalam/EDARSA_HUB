/*
COA Gate 3B - DDL MINIMO DE DISENO
DESIGN ONLY - NO EJECUTAR EN ESTE GATE
Fuente: Gate 2 dossier + Gate 3A CERTIFIED_READ_ONLY.
No contiene porcentajes de comision por defecto. 6.5% NO es constante del sistema.
No altera tablas canonicas existentes.
*/

CREATE TABLE dbo.COA_Expedientes (
    ExpedienteID bigint IDENTITY(1,1) NOT NULL,
    PublicUUID uniqueidentifier NOT NULL CONSTRAINT DF_COA_Expedientes_PublicUUID DEFAULT (newid()),
    EmpresaID int NOT NULL,
    UnidadNegocioID uniqueidentifier NULL,
    TipoOperacionCodigo varchar(40) NOT NULL,
    EstadoCodigo varchar(30) NOT NULL,
    OrigenCodigo varchar(30) NULL,
    ReferenciaOperacion nvarchar(200) NULL,
    ResponsableUsuarioID int NULL,
    FechaOperacion datetime2(3) NULL,
    FechaAlta datetime2(3) NOT NULL CONSTRAINT DF_COA_Expedientes_FechaAlta DEFAULT (sysutcdatetime()),
    FechaModificacion datetime2(3) NULL,
    CreadoPorUsuarioID int NULL,
    ModificadoPorUsuarioID int NULL,
    Activo bit NOT NULL CONSTRAINT DF_COA_Expedientes_Activo DEFAULT ((1)),
    CONSTRAINT PK_COA_Expedientes PRIMARY KEY (ExpedienteID),
    CONSTRAINT UQ_COA_Expedientes_PublicUUID UNIQUE (PublicUUID),
    CONSTRAINT FK_COA_Expedientes_Empresa FOREIGN KEY (EmpresaID) REFERENCES dbo.Sistema_Empresas(EmpresaID),
    CONSTRAINT FK_COA_Expedientes_Unidad FOREIGN KEY (UnidadNegocioID) REFERENCES dbo.Unidades_Negocio(id),
    CONSTRAINT FK_COA_Expedientes_Responsable FOREIGN KEY (ResponsableUsuarioID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
    CONSTRAINT FK_COA_Expedientes_CreadoPor FOREIGN KEY (CreadoPorUsuarioID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
    CONSTRAINT FK_COA_Expedientes_ModificadoPor FOREIGN KEY (ModificadoPorUsuarioID) REFERENCES dbo.Usuario_Catalogo(UsuarioID)
);

CREATE INDEX IX_COA_Expedientes_Empresa_Estado ON dbo.COA_Expedientes(EmpresaID, EstadoCodigo, Activo);
CREATE INDEX IX_COA_Expedientes_Unidad ON dbo.COA_Expedientes(UnidadNegocioID) WHERE UnidadNegocioID IS NOT NULL;

CREATE TABLE dbo.COA_ExpedienteEventos (
    ExpedienteEventoID bigint IDENTITY(1,1) NOT NULL,
    ExpedienteID bigint NOT NULL,
    TipoEventoCodigo varchar(40) NOT NULL,
    EstadoAnteriorCodigo varchar(30) NULL,
    EstadoNuevoCodigo varchar(30) NULL,
    CanalCodigo varchar(30) NULL,
    Detalle nvarchar(1000) NULL,
    ReferenciaExterna nvarchar(200) NULL,
    UsuarioID int NULL,
    FechaEvento datetime2(3) NOT NULL CONSTRAINT DF_COA_ExpedienteEventos_Fecha DEFAULT (sysutcdatetime()),
    CONSTRAINT PK_COA_ExpedienteEventos PRIMARY KEY (ExpedienteEventoID),
    CONSTRAINT FK_COA_ExpedienteEventos_Expediente FOREIGN KEY (ExpedienteID) REFERENCES dbo.COA_Expedientes(ExpedienteID),
    CONSTRAINT FK_COA_ExpedienteEventos_Usuario FOREIGN KEY (UsuarioID) REFERENCES dbo.Usuario_Catalogo(UsuarioID)
);

CREATE INDEX IX_COA_ExpedienteEventos_Expediente_Fecha ON dbo.COA_ExpedienteEventos(ExpedienteID, FechaEvento);

CREATE TABLE dbo.COA_ExpedienteReferencias (
    ExpedienteReferenciaID bigint IDENTITY(1,1) NOT NULL,
    ExpedienteID bigint NOT NULL,
    TipoRelacionCodigo varchar(40) NOT NULL,
    ClienteID int NULL,
    ProveedorID int NULL,
    DocumentoFiscalID bigint NULL,
    PagoID bigint NULL,
    DecisionPagoID bigint NULL,
    NominaID int NULL,
    DispersionNominaID int NULL,
    NominaReciboID int NULL,
    ColaboradorID int NULL,
    ContratoID uniqueidentifier NULL,
    UsuarioAltaID int NULL,
    FechaAlta datetime2(3) NOT NULL CONSTRAINT DF_COA_ExpedienteReferencias_Fecha DEFAULT (sysutcdatetime()),
    CONSTRAINT PK_COA_ExpedienteReferencias PRIMARY KEY (ExpedienteReferenciaID),
    CONSTRAINT FK_COA_ExpedienteReferencias_Expediente FOREIGN KEY (ExpedienteID) REFERENCES dbo.COA_Expedientes(ExpedienteID),
    CONSTRAINT FK_COA_ExpedienteReferencias_Cliente FOREIGN KEY (ClienteID) REFERENCES dbo.Cliente_Catalogo(ClienteID),
    CONSTRAINT FK_COA_ExpedienteReferencias_Proveedor FOREIGN KEY (ProveedorID) REFERENCES dbo.Proveedor_Catalogo(ProveedorID),
    CONSTRAINT FK_COA_ExpedienteReferencias_DocumentoFiscal FOREIGN KEY (DocumentoFiscalID) REFERENCES dbo.Compras_DocumentosFiscales(DocumentoFiscalID),
    CONSTRAINT FK_COA_ExpedienteReferencias_Pago FOREIGN KEY (PagoID) REFERENCES dbo.Finanzas_Pagos(PagoID),
    CONSTRAINT FK_COA_ExpedienteReferencias_DecisionPago FOREIGN KEY (DecisionPagoID) REFERENCES dbo.Finanzas_CxP_DecisionesPago(DecisionPagoID),
    CONSTRAINT FK_COA_ExpedienteReferencias_Nomina FOREIGN KEY (NominaID) REFERENCES dbo.RH_Nomina(NominaID),
    CONSTRAINT FK_COA_ExpedienteReferencias_Dispersion FOREIGN KEY (DispersionNominaID) REFERENCES dbo.RH_Nomina_Dispersion(DispersionNominaID),
    CONSTRAINT FK_COA_ExpedienteReferencias_ReciboNomina FOREIGN KEY (NominaReciboID) REFERENCES dbo.RH_Nomina_Recibos(NominaReciboID),
    CONSTRAINT FK_COA_ExpedienteReferencias_Colaborador FOREIGN KEY (ColaboradorID) REFERENCES dbo.RH_Colaboradores_Expediente(ColaboradorID),
    CONSTRAINT FK_COA_ExpedienteReferencias_Contrato FOREIGN KEY (ContratoID) REFERENCES dbo.CRM_Contratos(ContratoID),
    CONSTRAINT FK_COA_ExpedienteReferencias_UsuarioAlta FOREIGN KEY (UsuarioAltaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
    CONSTRAINT CK_COA_ExpedienteReferencias_UnSoloDestino CHECK (
        (CASE WHEN ClienteID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN ProveedorID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN DocumentoFiscalID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN PagoID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN DecisionPagoID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN NominaID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN DispersionNominaID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN NominaReciboID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN ColaboradorID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN ContratoID IS NULL THEN 0 ELSE 1 END) = 1
    )
);

CREATE INDEX IX_COA_ExpedienteReferencias_Expediente ON dbo.COA_ExpedienteReferencias(ExpedienteID);
CREATE INDEX IX_COA_ExpedienteReferencias_Proveedor ON dbo.COA_ExpedienteReferencias(ProveedorID) WHERE ProveedorID IS NOT NULL;
CREATE INDEX IX_COA_ExpedienteReferencias_Cliente ON dbo.COA_ExpedienteReferencias(ClienteID) WHERE ClienteID IS NOT NULL;
CREATE INDEX IX_COA_ExpedienteReferencias_DocumentoFiscal ON dbo.COA_ExpedienteReferencias(DocumentoFiscalID) WHERE DocumentoFiscalID IS NOT NULL;
CREATE INDEX IX_COA_ExpedienteReferencias_Nomina ON dbo.COA_ExpedienteReferencias(NominaID) WHERE NominaID IS NOT NULL;

CREATE TABLE dbo.COA_ReglasComision (
    ReglaComisionID uniqueidentifier NOT NULL CONSTRAINT DF_COA_ReglasComision_ID DEFAULT (newid()),
    Codigo varchar(50) NOT NULL,
    Nombre nvarchar(200) NOT NULL,
    Descripcion nvarchar(1000) NULL,
    VersionRegla int NOT NULL CONSTRAINT DF_COA_ReglasComision_Version DEFAULT ((1)),
    Prioridad int NOT NULL,
    BaseCalculoCodigo varchar(40) NOT NULL,
    Porcentaje decimal(9,6) NULL,
    ImporteFijo decimal(19,4) NULL,
    MonedaID smallint NULL,
    VigenciaDesde datetime2(3) NOT NULL,
    VigenciaHasta datetime2(3) NULL,
    Activo bit NOT NULL CONSTRAINT DF_COA_ReglasComision_Activo DEFAULT ((1)),
    FechaAlta datetime2(3) NOT NULL CONSTRAINT DF_COA_ReglasComision_FechaAlta DEFAULT (sysutcdatetime()),
    FechaModificacion datetime2(3) NULL,
    CreadoPorUsuarioID int NULL,
    ModificadoPorUsuarioID int NULL,
    CONSTRAINT PK_COA_ReglasComision PRIMARY KEY (ReglaComisionID),
    CONSTRAINT UQ_COA_ReglasComision_Codigo_Version UNIQUE (Codigo, VersionRegla),
    CONSTRAINT FK_COA_ReglasComision_CreadoPor FOREIGN KEY (CreadoPorUsuarioID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
    CONSTRAINT FK_COA_ReglasComision_ModificadoPor FOREIGN KEY (ModificadoPorUsuarioID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
    CONSTRAINT FK_COA_ReglasComision_Moneda FOREIGN KEY (MonedaID) REFERENCES dbo.Proveedor_Monedas(MonedaID),
    CONSTRAINT CK_COA_ReglasComision_Valor CHECK (Porcentaje IS NOT NULL OR ImporteFijo IS NOT NULL),
    CONSTRAINT CK_COA_ReglasComision_Porcentaje CHECK (Porcentaje IS NULL OR Porcentaje >= 0),
    CONSTRAINT CK_COA_ReglasComision_ImporteFijo CHECK (ImporteFijo IS NULL OR ImporteFijo >= 0),
    CONSTRAINT CK_COA_ReglasComision_Vigencia CHECK (VigenciaHasta IS NULL OR VigenciaHasta >= VigenciaDesde)
);

CREATE INDEX IX_COA_ReglasComision_Resolucion ON dbo.COA_ReglasComision(Activo, VigenciaDesde, VigenciaHasta, Prioridad);

CREATE TABLE dbo.COA_ReglasComisionCondiciones (
    ReglaComisionCondicionID bigint IDENTITY(1,1) NOT NULL,
    ReglaComisionID uniqueidentifier NOT NULL,
    DimensionCodigo varchar(40) NOT NULL,
    OperadorCodigo varchar(20) NOT NULL,
    EmpresaID int NULL,
    UnidadNegocioID uniqueidentifier NULL,
    ClienteID int NULL,
    ProveedorID int NULL,
    ContratoID uniqueidentifier NULL,
    ValorTexto nvarchar(200) NULL,
    ValorDecimalDesde decimal(19,4) NULL,
    ValorDecimalHasta decimal(19,4) NULL,
    ValorFechaDesde datetime2(3) NULL,
    ValorFechaHasta datetime2(3) NULL,
    Activo bit NOT NULL CONSTRAINT DF_COA_ReglasComisionCondiciones_Activo DEFAULT ((1)),
    FechaAlta datetime2(3) NOT NULL CONSTRAINT DF_COA_ReglasComisionCondiciones_FechaAlta DEFAULT (sysutcdatetime()),
    UsuarioAltaID int NULL,
    CONSTRAINT PK_COA_ReglasComisionCondiciones PRIMARY KEY (ReglaComisionCondicionID),
    CONSTRAINT FK_COA_ReglasComisionCondiciones_Regla FOREIGN KEY (ReglaComisionID) REFERENCES dbo.COA_ReglasComision(ReglaComisionID),
    CONSTRAINT FK_COA_ReglasComisionCondiciones_Empresa FOREIGN KEY (EmpresaID) REFERENCES dbo.Sistema_Empresas(EmpresaID),
    CONSTRAINT FK_COA_ReglasComisionCondiciones_Unidad FOREIGN KEY (UnidadNegocioID) REFERENCES dbo.Unidades_Negocio(id),
    CONSTRAINT FK_COA_ReglasComisionCondiciones_Cliente FOREIGN KEY (ClienteID) REFERENCES dbo.Cliente_Catalogo(ClienteID),
    CONSTRAINT FK_COA_ReglasComisionCondiciones_Proveedor FOREIGN KEY (ProveedorID) REFERENCES dbo.Proveedor_Catalogo(ProveedorID),
    CONSTRAINT FK_COA_ReglasComisionCondiciones_Contrato FOREIGN KEY (ContratoID) REFERENCES dbo.CRM_Contratos(ContratoID),
    CONSTRAINT FK_COA_ReglasComisionCondiciones_UsuarioAlta FOREIGN KEY (UsuarioAltaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
    CONSTRAINT CK_COA_ReglasComisionCondiciones_RangoDecimal CHECK (ValorDecimalHasta IS NULL OR ValorDecimalDesde IS NULL OR ValorDecimalHasta >= ValorDecimalDesde),
    CONSTRAINT CK_COA_ReglasComisionCondiciones_RangoFecha CHECK (ValorFechaHasta IS NULL OR ValorFechaDesde IS NULL OR ValorFechaHasta >= ValorFechaDesde)
);

CREATE INDEX IX_COA_ReglasComisionCondiciones_Regla_Dimension ON dbo.COA_ReglasComisionCondiciones(ReglaComisionID, DimensionCodigo, Activo);

CREATE TABLE dbo.COA_ExcepcionesRegla (
    ExcepcionReglaID bigint IDENTITY(1,1) NOT NULL,
    ExpedienteID bigint NOT NULL,
    ReglaComisionID uniqueidentifier NULL,
    TipoExcepcionCodigo varchar(40) NOT NULL,
    Motivo nvarchar(1000) NOT NULL,
    BaseCalculoCodigoOverride varchar(40) NULL,
    PorcentajeOverride decimal(9,6) NULL,
    ImporteFijoOverride decimal(19,4) NULL,
    EstadoAutorizacionCodigo varchar(30) NOT NULL,
    SolicitadoPorUsuarioID int NULL,
    AutorizadoPorUsuarioID int NULL,
    FechaSolicitud datetime2(3) NOT NULL CONSTRAINT DF_COA_ExcepcionesRegla_FechaSolicitud DEFAULT (sysutcdatetime()),
    FechaAutorizacion datetime2(3) NULL,
    VigenciaDesde datetime2(3) NULL,
    VigenciaHasta datetime2(3) NULL,
    Activo bit NOT NULL CONSTRAINT DF_COA_ExcepcionesRegla_Activo DEFAULT ((1)),
    CONSTRAINT PK_COA_ExcepcionesRegla PRIMARY KEY (ExcepcionReglaID),
    CONSTRAINT FK_COA_ExcepcionesRegla_Expediente FOREIGN KEY (ExpedienteID) REFERENCES dbo.COA_Expedientes(ExpedienteID),
    CONSTRAINT FK_COA_ExcepcionesRegla_Regla FOREIGN KEY (ReglaComisionID) REFERENCES dbo.COA_ReglasComision(ReglaComisionID),
    CONSTRAINT FK_COA_ExcepcionesRegla_SolicitadoPor FOREIGN KEY (SolicitadoPorUsuarioID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
    CONSTRAINT FK_COA_ExcepcionesRegla_AutorizadoPor FOREIGN KEY (AutorizadoPorUsuarioID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
    CONSTRAINT CK_COA_ExcepcionesRegla_Porcentaje CHECK (PorcentajeOverride IS NULL OR PorcentajeOverride >= 0),
    CONSTRAINT CK_COA_ExcepcionesRegla_Importe CHECK (ImporteFijoOverride IS NULL OR ImporteFijoOverride >= 0),
    CONSTRAINT CK_COA_ExcepcionesRegla_Vigencia CHECK (VigenciaHasta IS NULL OR VigenciaDesde IS NULL OR VigenciaHasta >= VigenciaDesde)
);

CREATE INDEX IX_COA_ExcepcionesRegla_Expediente ON dbo.COA_ExcepcionesRegla(ExpedienteID, Activo);

CREATE TABLE dbo.COA_ComisionAplicada (
    ComisionAplicadaID bigint IDENTITY(1,1) NOT NULL,
    ExpedienteID bigint NOT NULL,
    ReglaComisionID uniqueidentifier NULL,
    ExcepcionReglaID bigint NULL,
    VersionCalculo int NOT NULL,
    ReglaVersionAplicada int NULL,
    PrioridadAplicada int NULL,
    BaseCalculoCodigo varchar(40) NOT NULL,
    MontoBase decimal(19,4) NOT NULL,
    PorcentajeAplicado decimal(9,6) NULL,
    ImporteFijoAplicado decimal(19,4) NULL,
    ImporteComision decimal(19,4) NOT NULL,
    MonedaID smallint NULL,
    SnapshotResolucion nvarchar(max) NULL,
    CalculadoPorUsuarioID int NULL,
    FechaCalculo datetime2(3) NOT NULL CONSTRAINT DF_COA_ComisionAplicada_FechaCalculo DEFAULT (sysutcdatetime()),
    CONSTRAINT PK_COA_ComisionAplicada PRIMARY KEY (ComisionAplicadaID),
    CONSTRAINT UQ_COA_ComisionAplicada_Expediente_Version UNIQUE (ExpedienteID, VersionCalculo),
    CONSTRAINT FK_COA_ComisionAplicada_Expediente FOREIGN KEY (ExpedienteID) REFERENCES dbo.COA_Expedientes(ExpedienteID),
    CONSTRAINT FK_COA_ComisionAplicada_Regla FOREIGN KEY (ReglaComisionID) REFERENCES dbo.COA_ReglasComision(ReglaComisionID),
    CONSTRAINT FK_COA_ComisionAplicada_Excepcion FOREIGN KEY (ExcepcionReglaID) REFERENCES dbo.COA_ExcepcionesRegla(ExcepcionReglaID),
    CONSTRAINT FK_COA_ComisionAplicada_Moneda FOREIGN KEY (MonedaID) REFERENCES dbo.Proveedor_Monedas(MonedaID),
    CONSTRAINT FK_COA_ComisionAplicada_CalculadoPor FOREIGN KEY (CalculadoPorUsuarioID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
    CONSTRAINT CK_COA_ComisionAplicada_MontoBase CHECK (MontoBase >= 0),
    CONSTRAINT CK_COA_ComisionAplicada_Porcentaje CHECK (PorcentajeAplicado IS NULL OR PorcentajeAplicado >= 0),
    CONSTRAINT CK_COA_ComisionAplicada_ImporteFijo CHECK (ImporteFijoAplicado IS NULL OR ImporteFijoAplicado >= 0),
    CONSTRAINT CK_COA_ComisionAplicada_ImporteComision CHECK (ImporteComision >= 0)
);

CREATE INDEX IX_COA_ComisionAplicada_Regla ON dbo.COA_ComisionAplicada(ReglaComisionID) WHERE ReglaComisionID IS NOT NULL;

/* FIN DDL DE DISENO. NO EJECUTADO EN GATE 3B. */
