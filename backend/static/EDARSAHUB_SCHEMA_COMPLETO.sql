-- ============================================================
-- EDARSAHUB - SCHEMA COMPLETO
-- Generado: 2026-06-02T08:07:45.254177
-- Servidor: 54.39.104.176
-- Base de datos: EDARSAHUB
-- ============================================================

-- Total de tablas: 417

-- ============================================================
-- TABLA: [Comercial].[TableroEjecutivoCache]
-- ============================================================
CREATE TABLE [Comercial].[TableroEjecutivoCache] (
    [UnidadID] VARCHAR(32) NOT NULL,
    [UnidadNombre] NVARCHAR(100) NOT NULL,
    [VentasConsolidadas] NUMERIC(18,2) NULL DEFAULT ((0.00)),
    [PaxTotal] INT NULL DEFAULT ((0)),
    [ChequesEmitidos] INT NULL DEFAULT ((0)),
    [PorcentajeMeta] NUMERIC(5,2) NULL DEFAULT ((0.00)),
    [UltimaSincronizacion] DATETIME NULL DEFAULT (getdate()),
    [StatusConexion] VARCHAR(20) NULL DEFAULT ('ACTIVE'),
    CONSTRAINT [PK_TableroEjecutivoCache] PRIMARY KEY ([UnidadID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_ActivoMedidores]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_ActivoMedidores] (
    [ActivoMedidorID] BIGINT NOT NULL,
    [ActivoID] BIGINT NOT NULL,
    [MedidorID] INT NOT NULL,
    [ValorActual] DECIMAL(18,4) NULL,
    [FechaUltimaLectura] DATETIME2 NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ActivoFijo_ActivoMedidores] PRIMARY KEY ([ActivoMedidorID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_Activos]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_Activos] (
    [ActivoID] BIGINT NOT NULL,
    [CodigoActivo] VARCHAR(30) NOT NULL,
    [EtiquetaID] VARCHAR(50) NULL,
    [NumeroSerie] VARCHAR(100) NULL,
    [NumeroPlaca] VARCHAR(50) NULL,
    [CodigoBarras] VARCHAR(100) NULL,
    [QRCode] VARCHAR(200) NULL,
    [NombreActivo] VARCHAR(200) NOT NULL,
    [Descripcion] VARCHAR(1000) NULL,
    [ClaseActivoID] SMALLINT NOT NULL,
    [TipoActivoID] SMALLINT NULL,
    [Marca] VARCHAR(100) NULL,
    [Modelo] VARCHAR(100) NULL,
    [VersionModelo] VARCHAR(100) NULL,
    [Capacidad] VARCHAR(100) NULL,
    [AnioFabricacion] SMALLINT NULL,
    [EstatusActivoID] TINYINT NOT NULL,
    [EstadoUsoActivoID] TINYINT NOT NULL DEFAULT ((1)),
    [EsComponente] BIT NOT NULL DEFAULT ((0)),
    [ActivoPadreID] BIGINT NULL,
    [UbicacionActualID] INT NULL,
    [AreaRestaurante] VARCHAR(120) NULL,
    [Sucursal] VARCHAR(120) NULL,
    [UbicacionEspecifica] VARCHAR(250) NULL,
    [ResponsableNombre] VARCHAR(150) NULL,
    [CentroCosto] VARCHAR(50) NULL,
    [Departamento] VARCHAR(100) NULL,
    [FechaCompra] DATE NULL,
    [FechaRecepcion] DATE NULL,
    [FechaAltaOperacion] DATE NULL,
    [FechaPuestaServicio] DATE NULL,
    [FechaGarantiaInicio] DATE NULL,
    [FechaGarantiaFin] DATE NULL,
    [ProveedorID] INT NULL,
    [FacturaNumero] VARCHAR(50) NULL,
    [FacturaUUID] VARCHAR(50) NULL,
    [OrdenCompraReferencia] VARCHAR(50) NULL,
    [MonedaCompraID] SMALLINT NULL,
    [CostoCompra] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [CostoInstalacion] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [CostoInicialCapitalizado] DECIMAL(19,2) NULL,
    [VidaUtilMesesManual] SMALLINT NULL,
    [ValorResidualManual] DECIMAL(18,2) NULL,
    [RequiereMantenimiento] BIT NOT NULL DEFAULT ((0)),
    [Criticidad] TINYINT NOT NULL DEFAULT ((2)),
    [FotoPrincipalURL] VARCHAR(500) NULL,
    [Notas] VARCHAR(2000) NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedAt] DATETIME2 NULL,
    [ModifiedBy] VARCHAR(100) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ActivoFijo_Activos] PRIMARY KEY ([ActivoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_ActivosLibros]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_ActivosLibros] (
    [ActivoLibroID] BIGINT NOT NULL,
    [ActivoID] BIGINT NOT NULL,
    [LibroDepreciacionID] SMALLINT NOT NULL,
    [MetodoDepreciacionID] SMALLINT NOT NULL,
    [FechaInicioDepreciacion] DATE NOT NULL,
    [VidaUtilMeses] SMALLINT NOT NULL,
    [ValorOriginal] DECIMAL(18,2) NOT NULL,
    [ValorResidual] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [DepreciacionAcumulada] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ValorLibroActual] DECIMAL(18,2) NOT NULL,
    [UltimoPeriodoDepreciado] CHAR(7) NULL,
    [Suspendida] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ActivoFijo_ActivosLibros] PRIMARY KEY ([ActivoLibroID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_Alertas]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_Alertas] (
    [AlertaID] BIGINT NOT NULL,
    [ActivoID] BIGINT NULL,
    [OrdenTrabajoID] BIGINT NULL,
    [PlanMantenimientoID] BIGINT NULL,
    [TipoAlerta] VARCHAR(30) NOT NULL,
    [Titulo] VARCHAR(200) NOT NULL,
    [Mensaje] VARCHAR(2000) NOT NULL,
    [Prioridad] VARCHAR(10) NOT NULL DEFAULT ('MEDIA'),
    [Leida] BIT NOT NULL DEFAULT ((0)),
    [EnviadaEmail] BIT NOT NULL DEFAULT ((0)),
    [EnviadaWhatsApp] BIT NOT NULL DEFAULT ((0)),
    [FechaCierre] DATETIME2 NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_ActivoFijo_Alertas] PRIMARY KEY ([AlertaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_Archivos]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_Archivos] (
    [ArchivoID] BIGINT NOT NULL,
    [EntidadTipo] VARCHAR(30) NOT NULL,
    [EntidadID] BIGINT NOT NULL,
    [TipoArchivo] VARCHAR(30) NOT NULL,
    [NombreArchivo] VARCHAR(255) NOT NULL,
    [NombreOriginal] VARCHAR(255) NULL,
    [ExtensionArchivo] VARCHAR(10) NULL,
    [MIMEType] VARCHAR(100) NULL,
    [RutaArchivo] VARCHAR(500) NOT NULL,
    [TamanoBytes] BIGINT NULL,
    [HashArchivo] VARCHAR(128) NULL,
    [EsPrincipal] BIT NOT NULL DEFAULT ((0)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ActivoFijo_Archivos] PRIMARY KEY ([ArchivoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_Autorizaciones]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_Autorizaciones] (
    [AutorizacionID] BIGINT NOT NULL,
    [FolioAutorizacion] VARCHAR(30) NOT NULL,
    [TipoAutorizacion] VARCHAR(30) NOT NULL,
    [ActivoID] BIGINT NULL,
    [OrdenTrabajoID] BIGINT NULL,
    [CotizacionID] BIGINT NULL,
    [Monto] DECIMAL(18,2) NULL,
    [MonedaID] SMALLINT NULL,
    [SolicitanteNombre] VARCHAR(150) NOT NULL,
    [AprobadorNombre] VARCHAR(150) NULL,
    [Justificacion] VARCHAR(2000) NOT NULL,
    [EstadoAutorizacion] VARCHAR(20) NOT NULL DEFAULT ('PENDIENTE'),
    [FechaSolicitud] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaResolucion] DATETIME2 NULL,
    [ComentariosResolucion] VARCHAR(2000) NULL,
    [NotificarEmail] BIT NOT NULL DEFAULT ((0)),
    [NotificarWhatsApp] BIT NOT NULL DEFAULT ((0)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_ActivoFijo_Autorizaciones] PRIMARY KEY ([AutorizacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_BajasActivos]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_BajasActivos] (
    [BajaActivoID] BIGINT NOT NULL,
    [ActivoID] BIGINT NOT NULL,
    [TipoBajaID] TINYINT NOT NULL,
    [FechaBaja] DATE NOT NULL,
    [Motivo] VARCHAR(1000) NOT NULL,
    [ValorVenta] DECIMAL(18,2) NULL,
    [CostoRetiro] DECIMAL(18,2) NULL,
    [Observaciones] VARCHAR(2000) NULL,
    [AutorizacionID] BIGINT NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_ActivoFijo_BajasActivos] PRIMARY KEY ([BajaActivoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_ClaseActivo]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_ClaseActivo] (
    [ClaseActivoID] SMALLINT NOT NULL,
    [Nombre] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [TipoActivoID] SMALLINT NULL,
    [Capitalizable] BIT NOT NULL DEFAULT ((1)),
    [RequiereSerie] BIT NOT NULL DEFAULT ((0)),
    [RequiereEtiqueta] BIT NOT NULL DEFAULT ((0)),
    [RequiereMantenimiento] BIT NOT NULL DEFAULT ((0)),
    [RequiereDepreciacion] BIT NOT NULL DEFAULT ((1)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ActivoFijo_ClaseActivo] PRIMARY KEY ([ClaseActivoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_Cotizaciones]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_Cotizaciones] (
    [CotizacionID] BIGINT NOT NULL,
    [FolioCotizacion] VARCHAR(30) NOT NULL,
    [ActivoID] BIGINT NOT NULL,
    [OrdenTrabajoID] BIGINT NULL,
    [ProveedorID] INT NOT NULL,
    [TipoCotizacion] VARCHAR(20) NOT NULL DEFAULT ('MANTENIMIENTO'),
    [Concepto] VARCHAR(500) NOT NULL,
    [Monto] DECIMAL(18,2) NOT NULL,
    [MonedaID] SMALLINT NOT NULL DEFAULT ((1)),
    [FechaCotizacion] DATE NOT NULL,
    [ValidaHasta] DATE NULL,
    [Incluye] VARCHAR(1000) NULL,
    [ArchivoURL] VARCHAR(500) NULL,
    [EstadoCotizacion] VARCHAR(20) NOT NULL DEFAULT ('PENDIENTE'),
    [SistemaExterno] VARCHAR(20) NULL,
    [PedidoExternoID] VARCHAR(50) NULL,
    [SucursalSistema] VARCHAR(120) NULL,
    [EsSeleccionada] BIT NOT NULL DEFAULT ((0)),
    [Observaciones] VARCHAR(1000) NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_ActivoFijo_Cotizaciones] PRIMARY KEY ([CotizacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_DepreciacionMovimientos]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_DepreciacionMovimientos] (
    [DepreciacionMovimientoID] BIGINT NOT NULL,
    [ActivoLibroID] BIGINT NOT NULL,
    [Periodo] CHAR(7) NOT NULL,
    [FechaContable] DATE NOT NULL,
    [ImporteDepreciacion] DECIMAL(18,2) NOT NULL,
    [DepreciacionAcumulada] DECIMAL(18,2) NOT NULL,
    [ValorLibroDespues] DECIMAL(18,2) NOT NULL,
    [TipoMovimiento] VARCHAR(20) NOT NULL DEFAULT ('NORMAL'),
    [Referencia] VARCHAR(100) NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_ActivoFijo_DepreciacionMovimientos] PRIMARY KEY ([DepreciacionMovimientoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_EstadoUsoActivo]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_EstadoUsoActivo] (
    [EstadoUsoActivoID] TINYINT NOT NULL,
    [Nombre] VARCHAR(40) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ActivoFijo_EstadoUsoActivo] PRIMARY KEY ([EstadoUsoActivoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_EstatusActivo]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_EstatusActivo] (
    [EstatusActivoID] TINYINT NOT NULL,
    [Nombre] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ActivoFijo_EstatusActivo] PRIMARY KEY ([EstatusActivoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_EstatusOT]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_EstatusOT] (
    [EstatusOTID] TINYINT NOT NULL,
    [Nombre] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ActivoFijo_EstatusOT] PRIMARY KEY ([EstatusOTID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_HistorialAsignaciones]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_HistorialAsignaciones] (
    [HistorialAsignacionID] BIGINT NOT NULL,
    [ActivoID] BIGINT NOT NULL,
    [UbicacionID] INT NULL,
    [ResponsableNombre] VARCHAR(150) NULL,
    [CentroCosto] VARCHAR(50) NULL,
    [Departamento] VARCHAR(100) NULL,
    [FechaInicio] DATETIME2 NOT NULL,
    [FechaFin] DATETIME2 NULL,
    [Motivo] VARCHAR(200) NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_ActivoFijo_HistorialAsignaciones] PRIMARY KEY ([HistorialAsignacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_LecturasMedidor]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_LecturasMedidor] (
    [LecturaMedidorID] BIGINT NOT NULL,
    [ActivoMedidorID] BIGINT NOT NULL,
    [FechaLectura] DATETIME2 NOT NULL,
    [ValorLectura] DECIMAL(18,4) NOT NULL,
    [OrigenLectura] VARCHAR(20) NOT NULL DEFAULT ('MANUAL'),
    [Observaciones] VARCHAR(500) NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_ActivoFijo_LecturasMedidor] PRIMARY KEY ([LecturaMedidorID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_LibrosDepreciacion]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_LibrosDepreciacion] (
    [LibroDepreciacionID] SMALLINT NOT NULL,
    [CodigoLibro] VARCHAR(20) NOT NULL,
    [NombreLibro] VARCHAR(100) NOT NULL,
    [TipoLibro] VARCHAR(20) NOT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ActivoFijo_LibrosDepreciacion] PRIMARY KEY ([LibroDepreciacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_Medidores]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_Medidores] (
    [MedidorID] INT NOT NULL,
    [CodigoMedidor] VARCHAR(30) NOT NULL,
    [NombreMedidor] VARCHAR(100) NOT NULL,
    [TipoMedidorID] TINYINT NOT NULL,
    [UnidadMedida] VARCHAR(30) NULL,
    [TieneLimiteAdvertencia] BIT NOT NULL DEFAULT ((0)),
    [LimiteAdvertencia] DECIMAL(18,4) NULL,
    [TieneLimiteCritico] BIT NOT NULL DEFAULT ((0)),
    [LimiteCritico] DECIMAL(18,4) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ActivoFijo_Medidores] PRIMARY KEY ([MedidorID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_MetodosDepreciacion]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_MetodosDepreciacion] (
    [MetodoDepreciacionID] SMALLINT NOT NULL,
    [CodigoMetodo] VARCHAR(20) NOT NULL,
    [NombreMetodo] VARCHAR(100) NOT NULL,
    [TipoCalculo] VARCHAR(30) NOT NULL,
    [PermiteValorResidual] BIT NOT NULL DEFAULT ((1)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ActivoFijo_MetodosDepreciacion] PRIMARY KEY ([MetodoDepreciacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_MovimientosActivo]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_MovimientosActivo] (
    [MovimientoActivoID] BIGINT NOT NULL,
    [ActivoID] BIGINT NOT NULL,
    [TipoMovimiento] VARCHAR(30) NOT NULL,
    [FechaMovimiento] DATETIME2 NOT NULL,
    [UbicacionOrigenID] INT NULL,
    [UbicacionDestinoID] INT NULL,
    [ProveedorID] INT NULL,
    [ImporteAjuste] DECIMAL(18,2) NULL,
    [ReferenciaDocumento] VARCHAR(100) NULL,
    [Observaciones] VARCHAR(1000) NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_ActivoFijo_MovimientosActivo] PRIMARY KEY ([MovimientoActivoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_OrdenesTrabajo]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_OrdenesTrabajo] (
    [OrdenTrabajoID] BIGINT NOT NULL,
    [FolioOT] VARCHAR(30) NOT NULL,
    [ActivoID] BIGINT NOT NULL,
    [PlanMantenimientoID] BIGINT NULL,
    [TipoOTID] TINYINT NOT NULL,
    [EstatusOTID] TINYINT NOT NULL,
    [PrioridadOTID] TINYINT NOT NULL,
    [UbicacionID] INT NULL,
    [FechaSolicitud] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaProgramada] DATETIME2 NULL,
    [FechaInicio] DATETIME2 NULL,
    [FechaFin] DATETIME2 NULL,
    [SolicitanteNombre] VARCHAR(150) NULL,
    [TecnicoAsignadoNombre] VARCHAR(150) NULL,
    [ProveedorID] INT NULL,
    [DescripcionFalla] VARCHAR(1000) NULL,
    [Diagnostico] VARCHAR(1000) NULL,
    [TrabajoRealizado] VARCHAR(2000) NULL,
    [TiempoParoMinutos] INT NULL,
    [CostoManoObra] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [CostoMateriales] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [CostoServicios] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [CostoTotal] DECIMAL(20,2) NULL,
    [RequiereAutorizacion] BIT NOT NULL DEFAULT ((0)),
    [Autorizada] BIT NOT NULL DEFAULT ((0)),
    [NumeroFacturaProveedor] VARCHAR(50) NULL,
    [UUIDFacturaProveedor] VARCHAR(50) NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedAt] DATETIME2 NULL,
    [ModifiedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_ActivoFijo_OrdenesTrabajo] PRIMARY KEY ([OrdenTrabajoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_OrdenTrabajoCostos]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_OrdenTrabajoCostos] (
    [OrdenTrabajoCostoID] BIGINT NOT NULL,
    [OrdenTrabajoID] BIGINT NOT NULL,
    [TipoCosto] VARCHAR(20) NOT NULL,
    [ProveedorID] INT NULL,
    [Descripcion] VARCHAR(500) NOT NULL,
    [Cantidad] DECIMAL(18,4) NOT NULL DEFAULT ((1)),
    [CostoUnitario] DECIMAL(18,4) NOT NULL DEFAULT ((0)),
    [Importe] DECIMAL(37,8) NULL,
    [FechaCosto] DATE NOT NULL,
    [FacturaNumero] VARCHAR(50) NULL,
    [UUIDFactura] VARCHAR(50) NULL,
    [Observaciones] VARCHAR(500) NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_ActivoFijo_OrdenTrabajoCostos] PRIMARY KEY ([OrdenTrabajoCostoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_PlanesMantenimiento]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_PlanesMantenimiento] (
    [PlanMantenimientoID] BIGINT NOT NULL,
    [CodigoPlan] VARCHAR(30) NOT NULL,
    [NombrePlan] VARCHAR(150) NOT NULL,
    [Descripcion] VARCHAR(500) NULL,
    [TipoOTID] TINYINT NOT NULL,
    [ActivoID] BIGINT NULL,
    [ClaseActivoID] SMALLINT NULL,
    [UbicacionID] INT NULL,
    [FrecuenciaDias] INT NULL,
    [MedidorID] INT NULL,
    [FrecuenciaValorMedidor] DECIMAL(18,4) NULL,
    [ProximoVencimiento] DATE NULL,
    [NotificarDiasAntes] INT NOT NULL DEFAULT ((7)),
    [RequiereOTAutomatica] BIT NOT NULL DEFAULT ((1)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [Notas] VARCHAR(1000) NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedAt] DATETIME2 NULL,
    [ModifiedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_ActivoFijo_PlanesMantenimiento] PRIMARY KEY ([PlanMantenimientoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_PrioridadOT]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_PrioridadOT] (
    [PrioridadOTID] TINYINT NOT NULL,
    [Nombre] VARCHAR(20) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ActivoFijo_PrioridadOT] PRIMARY KEY ([PrioridadOTID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_ReemplazosActivos]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_ReemplazosActivos] (
    [ReemplazoActivoID] BIGINT NOT NULL,
    [ActivoAnteriorID] BIGINT NOT NULL,
    [ActivoNuevoID] BIGINT NOT NULL,
    [FechaReemplazo] DATE NOT NULL,
    [Motivo] VARCHAR(1000) NOT NULL,
    [CostoTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [AutorizacionID] BIGINT NULL,
    [Notas] VARCHAR(2000) NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_ActivoFijo_ReemplazosActivos] PRIMARY KEY ([ReemplazoActivoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_ReglasClaseLibro]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_ReglasClaseLibro] (
    [ReglaClaseLibroID] INT NOT NULL,
    [ClaseActivoID] SMALLINT NOT NULL,
    [LibroDepreciacionID] SMALLINT NOT NULL,
    [MetodoDepreciacionID] SMALLINT NOT NULL,
    [VidaUtilMeses] SMALLINT NOT NULL,
    [PorcentajeResidual] DECIMAL(9,4) NOT NULL DEFAULT ((0)),
    [Capitalizable] BIT NOT NULL DEFAULT ((1)),
    [Deprecia] BIT NOT NULL DEFAULT ((1)),
    [CuentaActivo] VARCHAR(50) NULL,
    [CuentaDepreciacionAcum] VARCHAR(50) NULL,
    [CuentaGastoDepreciacion] VARCHAR(50) NULL,
    [CuentaBaja] VARCHAR(50) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ActivoFijo_ReglasClaseLibro] PRIMARY KEY ([ReglaClaseLibroID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_TipoActivo]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_TipoActivo] (
    [TipoActivoID] SMALLINT NOT NULL,
    [Nombre] VARCHAR(80) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ActivoFijo_TipoActivo] PRIMARY KEY ([TipoActivoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_TipoBaja]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_TipoBaja] (
    [TipoBajaID] TINYINT NOT NULL,
    [Nombre] VARCHAR(40) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ActivoFijo_TipoBaja] PRIMARY KEY ([TipoBajaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_TipoMedidor]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_TipoMedidor] (
    [TipoMedidorID] TINYINT NOT NULL,
    [Nombre] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ActivoFijo_TipoMedidor] PRIMARY KEY ([TipoMedidorID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_TipoOT]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_TipoOT] (
    [TipoOTID] TINYINT NOT NULL,
    [Nombre] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ActivoFijo_TipoOT] PRIMARY KEY ([TipoOTID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_TipoUbicacion]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_TipoUbicacion] (
    [TipoUbicacionID] SMALLINT NOT NULL,
    [Nombre] VARCHAR(60) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ActivoFijo_TipoUbicacion] PRIMARY KEY ([TipoUbicacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ActivoFijo_Ubicaciones]
-- ============================================================
CREATE TABLE [dbo].[ActivoFijo_Ubicaciones] (
    [UbicacionID] INT NOT NULL,
    [CodigoUbicacion] VARCHAR(30) NOT NULL,
    [NombreUbicacion] VARCHAR(150) NOT NULL,
    [UbicacionPadreID] INT NULL,
    [TipoUbicacionID] SMALLINT NULL,
    [Sucursal] VARCHAR(120) NULL,
    [Area] VARCHAR(120) NULL,
    [Edificio] VARCHAR(120) NULL,
    [Piso] VARCHAR(50) NULL,
    [Zona] VARCHAR(80) NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Pais] VARCHAR(60) NULL,
    [Estado] VARCHAR(100) NULL,
    [Ciudad] VARCHAR(100) NULL,
    [Direccion] VARCHAR(250) NULL,
    [Activa] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ActivoFijo_Ubicaciones] PRIMARY KEY ([UbicacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Alertas_Sistema]
-- ============================================================
CREATE TABLE [dbo].[Alertas_Sistema] (
    [ID] INT NOT NULL,
    [AlertaID] VARCHAR(50) NOT NULL,
    [Tipo] VARCHAR(100) NULL,
    [Severidad] VARCHAR(20) NULL DEFAULT ('info'),
    [Titulo] VARCHAR(200) NULL,
    [Mensaje] NVARCHAR(MAX) NULL,
    [Modulo] VARCHAR(50) NULL,
    [FechaCreacion] DATETIME2 NULL DEFAULT (getutcdate()),
    [DatosJSON] NVARCHAR(MAX) NULL,
    [AccionSugerida] VARCHAR(500) NULL,
    [Acknowledged] BIT NULL DEFAULT ((0)),
    [AcknowledgedBy] VARCHAR(50) NULL,
    [AcknowledgedAt] DATETIME2 NULL,
    CONSTRAINT [PK_Alertas_Sistema] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Auditoria_Inventario_Provisional]
-- ============================================================
CREATE TABLE [dbo].[Auditoria_Inventario_Provisional] (
    [id] INT NOT NULL,
    [unidad_negocio_id] VARCHAR(50) NOT NULL,
    [unidad_negocio_nombre] VARCHAR(100) NULL,
    [server_id] VARCHAR(50) NOT NULL,
    [sucursal] VARCHAR(100) NULL,
    [fecha_captura] DATETIME NULL DEFAULT (getdate()),
    [fecha_auditoria] DATE NULL,
    [usuario_id] INT NULL,
    [usuario_email] VARCHAR(100) NULL,
    [codigo_producto] VARCHAR(50) NOT NULL,
    [nombre_producto] VARCHAR(200) NULL,
    [cantidad] DECIMAL(18,4) NOT NULL,
    [costo_unitario] DECIMAL(18,4) NULL DEFAULT ((0)),
    [total] DECIMAL(18,4) NULL DEFAULT ((0)),
    [almacen] VARCHAR(100) NULL,
    [notas] TEXT(2147483647) NULL,
    [estado] VARCHAR(20) NULL DEFAULT ('PROVISIONAL'),
    [auditoria_ejecutada] BIT NULL DEFAULT ((0)),
    [fecha_auditoria_ejecutada] DATETIME NULL,
    [creado_en] DATETIME NULL DEFAULT (getdate()),
    [actualizado_en] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Auditoria_Inventario_Provisional] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[automatizacion_inventarios_config]
-- ============================================================
CREATE TABLE [dbo].[automatizacion_inventarios_config] (
    [config_id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [server_id] NVARCHAR(50) NOT NULL,
    [sucursal_id] NVARCHAR(20) NULL,
    [almacen_id] NVARCHAR(20) NULL,
    [intervalo_minutos] INT NOT NULL DEFAULT ((15)),
    [hora_inicio] TIME NULL,
    [hora_fin] TIME NULL,
    [activo] BIT NOT NULL DEFAULT ((0)),
    [created_at] DATETIME NOT NULL DEFAULT (getutcdate()),
    [updated_at] DATETIME NULL,
    [created_by] NVARCHAR(100) NULL,
    [updated_by] NVARCHAR(100) NULL,
    CONSTRAINT [PK_automatizacion_inventarios_config] PRIMARY KEY ([config_id])
);
GO

-- ============================================================
-- TABLA: [dbo].[automatizacion_inventarios_destinatarios]
-- ============================================================
CREATE TABLE [dbo].[automatizacion_inventarios_destinatarios] (
    [destinatario_id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [server_id] NVARCHAR(50) NOT NULL,
    [sucursal_id] NVARCHAR(20) NULL,
    [almacen_id] NVARCHAR(20) NULL,
    [nivel_origen] NVARCHAR(20) NOT NULL,
    [canal] NVARCHAR(20) NOT NULL DEFAULT ('EMAIL'),
    [tipo_destinatario] NVARCHAR(10) NOT NULL DEFAULT ('TO'),
    [email] NVARCHAR(255) NULL,
    [telefono] NVARCHAR(20) NULL,
    [nombre_contacto] NVARCHAR(100) NULL,
    [activo] BIT NOT NULL DEFAULT ((1)),
    [created_at] DATETIME NOT NULL DEFAULT (getutcdate()),
    [updated_at] DATETIME NULL,
    [created_by] NVARCHAR(100) NULL,
    [updated_by] NVARCHAR(100) NULL,
    CONSTRAINT [PK_automatizacion_inventarios_destinatarios] PRIMARY KEY ([destinatario_id])
);
GO

-- ============================================================
-- TABLA: [dbo].[automatizacion_inventarios_ejecuciones]
-- ============================================================
CREATE TABLE [dbo].[automatizacion_inventarios_ejecuciones] (
    [ejecucion_id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [fecha_inicio] DATETIME NOT NULL,
    [fecha_fin] DATETIME NULL,
    [estado] NVARCHAR(20) NOT NULL DEFAULT ('INICIADO'),
    [servidores_escaneados] INT NULL,
    [folios_detectados] INT NULL,
    [folios_procesados] INT NULL,
    [folios_error] INT NULL,
    [detalle_errores] NVARCHAR(MAX) NULL,
    [created_at] DATETIME NOT NULL DEFAULT (getutcdate()),
    [updated_at] DATETIME NULL,
    CONSTRAINT [PK_automatizacion_inventarios_ejecuciones] PRIMARY KEY ([ejecucion_id])
);
GO

-- ============================================================
-- TABLA: [dbo].[automatizacion_inventarios_envios]
-- ============================================================
CREATE TABLE [dbo].[automatizacion_inventarios_envios] (
    [envio_id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [procesado_id] UNIQUEIDENTIFIER NOT NULL,
    [destinatario_email] NVARCHAR(255) NOT NULL,
    [canal] NVARCHAR(20) NOT NULL DEFAULT ('EMAIL'),
    [tipo_destinatario] NVARCHAR(10) NOT NULL,
    [fecha_envio] DATETIME NULL,
    [estado] NVARCHAR(20) NOT NULL DEFAULT ('PENDIENTE'),
    [intentos] INT NOT NULL DEFAULT ((0)),
    [error_detalle] NVARCHAR(MAX) NULL,
    [created_at] DATETIME NOT NULL DEFAULT (getutcdate()),
    [updated_at] DATETIME NULL,
    CONSTRAINT [PK_automatizacion_inventarios_envios] PRIMARY KEY ([envio_id])
);
GO

-- ============================================================
-- TABLA: [dbo].[automatizacion_inventarios_folios_procesados]
-- ============================================================
CREATE TABLE [dbo].[automatizacion_inventarios_folios_procesados] (
    [procesado_id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [sistema_origen] NVARCHAR(20) NOT NULL,
    [server_id] NVARCHAR(50) NOT NULL,
    [sucursal_id] NVARCHAR(20) NOT NULL,
    [almacen_id] NVARCHAR(20) NOT NULL,
    [folio_inventario] NVARCHAR(50) NOT NULL,
    [fecha_inventario] DATE NOT NULL,
    [hash_verificacion] NVARCHAR(64) NOT NULL,
    [estado] NVARCHAR(20) NOT NULL DEFAULT ('EN_PROCESO'),
    [heartbeat_at] DATETIME NULL,
    [fecha_procesado] DATETIME NULL,
    [error_detalle] NVARCHAR(MAX) NULL,
    [ruta_archivo_excel] NVARCHAR(500) NULL,
    [created_at] DATETIME NOT NULL DEFAULT (getutcdate()),
    [updated_at] DATETIME NULL,
    [created_by] NVARCHAR(100) NULL,
    [updated_by] NVARCHAR(100) NULL,
    [comentario] NVARCHAR(100) NULL,
    [estado_inventario_origen] NVARCHAR(10) NULL,
    CONSTRAINT [PK_automatizacion_inventarios_folios_procesados] PRIMARY KEY ([procesado_id])
);
GO

-- ============================================================
-- TABLA: [dbo].[automatizacion_inventarios_ultimo_folio_conocido]
-- ============================================================
CREATE TABLE [dbo].[automatizacion_inventarios_ultimo_folio_conocido] (
    [id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [sistema_origen] NVARCHAR(20) NOT NULL,
    [server_id] NVARCHAR(50) NOT NULL,
    [sucursal_id] NVARCHAR(20) NOT NULL,
    [almacen_id] NVARCHAR(20) NOT NULL,
    [ultimo_folio] NVARCHAR(50) NOT NULL,
    [fecha_ultimo_folio] DATE NOT NULL,
    [fecha_actualizacion] DATETIME NOT NULL,
    [created_at] DATETIME NOT NULL DEFAULT (getutcdate()),
    [updated_at] DATETIME NULL,
    [created_by] NVARCHAR(100) NULL,
    [updated_by] NVARCHAR(100) NULL,
    CONSTRAINT [PK_automatizacion_inventarios_ultimo_folio_conocido] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[CavaSocios_Botellas]
-- ============================================================
CREATE TABLE [dbo].[CavaSocios_Botellas] (
    [BotellaID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [SocioID] UNIQUEIDENTIFIER NOT NULL,
    [ProductoCodigo] VARCHAR(50) NULL,
    [ProductoNombre] NVARCHAR(200) NOT NULL,
    [Marca] NVARCHAR(100) NULL,
    [TipoBebida] VARCHAR(50) NULL,
    [Añada] VARCHAR(10) NULL,
    [Capacidad] DECIMAL(10,2) NULL,
    [UbicacionCava] NVARCHAR(50) NULL,
    [ValorDeclarado] DECIMAL(18,2) NULL DEFAULT ((0)),
    [EstatusBotella] VARCHAR(30) NULL DEFAULT ('EN_CAVA'),
    [FechaIngreso] DATETIME2 NULL DEFAULT (getutcdate()),
    [FechaConsumo] DATETIME2 NULL,
    [FechaRetiro] DATETIME2 NULL,
    [NivelActual] DECIMAL(5,2) NULL DEFAULT ((100)),
    [FotoIngresoURL] NVARCHAR(500) NULL,
    [FechaCreacion] DATETIME2 NULL DEFAULT (getutcdate()),
    [UsuarioCreacionID] UNIQUEIDENTIFIER NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacionID] UNIQUEIDENTIFIER NULL,
    [Observaciones] NVARCHAR(500) NULL,
    CONSTRAINT [PK_CavaSocios_Botellas] PRIMARY KEY ([BotellaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CavaSocios_Cargos]
-- ============================================================
CREATE TABLE [dbo].[CavaSocios_Cargos] (
    [CargoID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [SocioID] UNIQUEIDENTIFIER NOT NULL,
    [TipoCargo] VARCHAR(50) NOT NULL,
    [ConceptoCargo] NVARCHAR(200) NOT NULL,
    [Monto] DECIMAL(18,2) NOT NULL,
    [Impuesto] DECIMAL(18,2) NULL DEFAULT ((0)),
    [Total] DECIMAL(18,2) NOT NULL,
    [EstatusCargo] VARCHAR(30) NULL DEFAULT ('PENDIENTE'),
    [BotellaID] UNIQUEIDENTIFIER NULL,
    [MovimientoID] UNIQUEIDENTIFIER NULL,
    [ReservacionID] UNIQUEIDENTIFIER NULL,
    [FacturaID] UNIQUEIDENTIFIER NULL,
    [FechaCargo] DATETIME2 NULL DEFAULT (getutcdate()),
    [FechaPago] DATETIME2 NULL,
    [FechaCreacion] DATETIME2 NULL DEFAULT (getutcdate()),
    [UsuarioCreacionID] UNIQUEIDENTIFIER NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacionID] UNIQUEIDENTIFIER NULL,
    [Observaciones] NVARCHAR(500) NULL,
    CONSTRAINT [PK_CavaSocios_Cargos] PRIMARY KEY ([CargoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CavaSocios_Configuracion]
-- ============================================================
CREATE TABLE [dbo].[CavaSocios_Configuracion] (
    [ConfigID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [CapacidadTotalBotellas] INT NULL DEFAULT ((500)),
    [TarifaDescorche] DECIMAL(18,2) NULL DEFAULT ((350)),
    [TarifaAlmacenajeMensual] DECIMAL(18,2) NULL DEFAULT ((150)),
    [DiasGraciaVencimiento] INT NULL DEFAULT ((30)),
    [MaximoBotellasEstandar] INT NULL DEFAULT ((12)),
    [MaximoBotellasVIP] INT NULL DEFAULT ((24)),
    [DiasAnticipacionVencimiento] INT NULL DEFAULT ((15)),
    [FechaCreacion] DATETIME2 NULL DEFAULT (getutcdate()),
    [UsuarioCreacionID] UNIQUEIDENTIFIER NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacionID] UNIQUEIDENTIFIER NULL,
    CONSTRAINT [PK_CavaSocios_Configuracion] PRIMARY KEY ([ConfigID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CavaSocios_Movimientos]
-- ============================================================
CREATE TABLE [dbo].[CavaSocios_Movimientos] (
    [MovimientoID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [BotellaID] UNIQUEIDENTIFIER NOT NULL,
    [SocioID] UNIQUEIDENTIFIER NOT NULL,
    [TipoMovimiento] VARCHAR(30) NOT NULL,
    [NivelAnterior] DECIMAL(5,2) NULL,
    [NivelNuevo] DECIMAL(5,2) NULL,
    [CantidadConsumida] DECIMAL(10,2) NULL,
    [MotivoMovimiento] NVARCHAR(200) NULL,
    [ReservacionID] UNIQUEIDENTIFIER NULL,
    [EventoID] UNIQUEIDENTIFIER NULL,
    [CuentaPOSID] UNIQUEIDENTIFIER NULL,
    [GeneroCargo] BIT NULL DEFAULT ((0)),
    [MontoCargo] DECIMAL(18,2) NULL DEFAULT ((0)),
    [CargoConceptoID] UNIQUEIDENTIFIER NULL,
    [MeseroID] UNIQUEIDENTIFIER NULL,
    [AutorizadoPor] UNIQUEIDENTIFIER NULL,
    [SucursalID] UNIQUEIDENTIFIER NULL,
    [FotoEvidenciaURL] NVARCHAR(500) NULL,
    [FechaMovimiento] DATETIME2 NULL DEFAULT (getutcdate()),
    [FechaCreacion] DATETIME2 NULL DEFAULT (getutcdate()),
    [UsuarioCreacionID] UNIQUEIDENTIFIER NULL,
    [Observaciones] NVARCHAR(500) NULL,
    CONSTRAINT [PK_CavaSocios_Movimientos] PRIMARY KEY ([MovimientoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CavaSocios_Socios]
-- ============================================================
CREATE TABLE [dbo].[CavaSocios_Socios] (
    [SocioID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [NumeroSocio] VARCHAR(50) NOT NULL,
    [NombreCompleto] NVARCHAR(200) NOT NULL,
    [Email] VARCHAR(150) NULL,
    [Telefono] VARCHAR(50) NULL,
    [ClienteCRMID] UNIQUEIDENTIFIER NULL,
    [TipoMembresia] VARCHAR(50) NULL DEFAULT ('ESTANDAR'),
    [FechaAltaMembresia] DATE NULL,
    [FechaVencimientoMembresia] DATE NULL,
    [MaximoBotellas] INT NULL DEFAULT ((12)),
    [Estatus] VARCHAR(30) NULL DEFAULT ('ACTIVO'),
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NULL DEFAULT (getutcdate()),
    [UsuarioCreacionID] UNIQUEIDENTIFIER NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacionID] UNIQUEIDENTIFIER NULL,
    [Observaciones] NVARCHAR(500) NULL,
    CONSTRAINT [PK_CavaSocios_Socios] PRIMARY KEY ([SocioID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Cliente_Catalogo]
-- ============================================================
CREATE TABLE [dbo].[Cliente_Catalogo] (
    [ClienteID] INT NOT NULL,
    [CodigoCliente] VARCHAR(20) NOT NULL,
    [RFC] VARCHAR(13) NOT NULL,
    [CURP] VARCHAR(18) NULL,
    [RazonSocial] VARCHAR(200) NOT NULL,
    [NombreComercial] VARCHAR(200) NULL,
    [TipoPersona] CHAR(1) NOT NULL DEFAULT ('M'),
    [ClienteMaestroID] INT NULL,
    [GrupoClienteID] INT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [LimiteCredito] DECIMAL(18,2) NULL,
    [DiasCredito] SMALLINT NOT NULL DEFAULT ((0)),
    [DescuentoMaximoPorcentaje] DECIMAL(9,4) NOT NULL DEFAULT ((0)),
    [PortalHabilitado] BIT NOT NULL DEFAULT ((0)),
    [BloqueadoVenta] BIT NOT NULL DEFAULT ((0)),
    [EmailPrincipal] VARCHAR(150) NULL,
    [TelefonoPrincipal] VARCHAR(25) NULL,
    [SitioWeb] VARCHAR(200) NULL,
    [CodigoPostalFiscal] VARCHAR(10) NULL,
    [Ciudad] VARCHAR(100) NULL,
    [Estado] VARCHAR(100) NULL,
    [Pais] VARCHAR(60) NOT NULL DEFAULT ('MEXICO'),
    [Observaciones] VARCHAR(1000) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedBy] VARCHAR(100) NULL,
    [ListaPrecioID] INT NULL,
    [CondicionPagoID] SMALLINT NULL,
    [EjecutivoPrincipalUserID] UNIQUEIDENTIFIER NULL,
    [GerenteComercialUserID] UNIQUEIDENTIFIER NULL,
    [CustomerSuccessUserID] UNIQUEIDENTIFIER NULL,
    [SectorID] INT NULL,
    [SubsectorID] INT NULL,
    [TamanoClienteID] INT NULL,
    [RiesgoCuentaID] INT NULL,
    [EsProspecto] BIT NULL DEFAULT ((0)),
    [EsPartner] BIT NULL DEFAULT ((0)),
    [EsCuentaEstrategica] BIT NULL DEFAULT ((0)),
    [FechaUltimaInteraccion] DATETIME NULL,
    [ScoreCuenta] INT NULL,
    [OrigenCuentaID] INT NULL,
    [PublicUUID] UNIQUEIDENTIFIER NULL DEFAULT (newid()),
    CONSTRAINT [PK_Cliente_Catalogo] PRIMARY KEY ([ClienteID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Cliente_Contactos]
-- ============================================================
CREATE TABLE [dbo].[Cliente_Contactos] (
    [ContactoClienteID] INT NOT NULL,
    [ClienteID] INT NOT NULL,
    [Nombre] VARCHAR(150) NOT NULL,
    [Apellidos] VARCHAR(150) NULL,
    [Puesto] VARCHAR(100) NULL,
    [Email] VARCHAR(150) NULL,
    [Telefono] VARCHAR(25) NULL,
    [Celular] VARCHAR(25) NULL,
    [EsPrincipal] BIT NOT NULL DEFAULT ((0)),
    [RecibeCotizaciones] BIT NOT NULL DEFAULT ((0)),
    [RecibeFacturacion] BIT NOT NULL DEFAULT ((0)),
    [RecibeCobranza] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Cliente_Contactos] PRIMARY KEY ([ContactoClienteID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Cliente_Direcciones]
-- ============================================================
CREATE TABLE [dbo].[Cliente_Direcciones] (
    [DireccionClienteID] INT NOT NULL,
    [ClienteID] INT NOT NULL,
    [TipoDireccion] VARCHAR(20) NOT NULL DEFAULT ('FISCAL'),
    [Calle] VARCHAR(150) NULL,
    [NumeroExterior] VARCHAR(20) NULL,
    [NumeroInterior] VARCHAR(20) NULL,
    [Colonia] VARCHAR(100) NULL,
    [Municipio] VARCHAR(100) NULL,
    [Ciudad] VARCHAR(100) NULL,
    [Estado] VARCHAR(100) NULL,
    [Pais] VARCHAR(60) NOT NULL DEFAULT ('MEXICO'),
    [CodigoPostal] VARCHAR(10) NULL,
    [Referencias] VARCHAR(250) NULL,
    [EsPrincipal] BIT NOT NULL DEFAULT ((0)),
    [Activa] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Cliente_Direcciones] PRIMARY KEY ([DireccionClienteID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Cliente_Grupos]
-- ============================================================
CREATE TABLE [dbo].[Cliente_Grupos] (
    [GrupoClienteID] INT NOT NULL,
    [CodigoGrupoCliente] VARCHAR(20) NOT NULL,
    [NombreGrupoCliente] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Cliente_Grupos] PRIMARY KEY ([GrupoClienteID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Cliente_RolUsuarioPortal]
-- ============================================================
CREATE TABLE [dbo].[Cliente_RolUsuarioPortal] (
    [RolPortalClienteID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Cliente_RolUsuarioPortal] PRIMARY KEY ([RolPortalClienteID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Cliente_UsuariosPortal]
-- ============================================================
CREATE TABLE [dbo].[Cliente_UsuariosPortal] (
    [UsuarioPortalClienteID] INT NOT NULL,
    [ClienteID] INT NOT NULL,
    [RolPortalClienteID] TINYINT NOT NULL,
    [NombreUsuario] VARCHAR(150) NOT NULL,
    [Email] VARCHAR(150) NOT NULL,
    [PasswordHash] VARCHAR(255) NULL,
    [ContactoClienteID] INT NULL,
    [UltimoAcceso] DATETIME2 NULL,
    [Bloqueado] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Cliente_UsuariosPortal] PRIMARY KEY ([UsuarioPortalClienteID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_AlertasMargenDestinatarios]
-- ============================================================
CREATE TABLE [dbo].[Comercial_AlertasMargenDestinatarios] (
    [DestinatarioID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [Nombre] NVARCHAR(200) NOT NULL,
    [Email] VARCHAR(200) NULL,
    [TelefonoWhatsApp] VARCHAR(20) NULL,
    [CanalEmail] BIT NULL DEFAULT ((1)),
    [CanalWhatsApp] BIT NULL DEFAULT ((0)),
    [EmpresaID] INT NULL,
    [SucursalID] INT NULL,
    [ServerID] UNIQUEIDENTIFIER NULL,
    [FamiliaCodigo] VARCHAR(100) NULL,
    [SeveridadMinima] VARCHAR(20) NULL DEFAULT ('ALTA'),
    [RecibeResumen] BIT NULL DEFAULT ((1)),
    [RecibeDetalle] BIT NULL DEFAULT ((1)),
    [FrecuenciaMaximaDiaria] INT NULL DEFAULT ((10)),
    [HoraPreferida] VARCHAR(5) NULL DEFAULT ('08:00'),
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME NULL,
    [CreadoPor] VARCHAR(100) NULL,
    [ModificadoPor] VARCHAR(100) NULL,
    CONSTRAINT [PK_Comercial_AlertasMargenDestinatarios] PRIMARY KEY ([DestinatarioID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_AlertasMargenEnvios]
-- ============================================================
CREATE TABLE [dbo].[Comercial_AlertasMargenEnvios] (
    [EnvioID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [AlertaMargenEventoID] UNIQUEIDENTIFIER NOT NULL,
    [DestinatarioID] UNIQUEIDENTIFIER NOT NULL,
    [Canal] VARCHAR(20) NOT NULL,
    [EstadoEnvio] VARCHAR(30) NULL DEFAULT ('PENDIENTE'),
    [FechaIntento] DATETIME NULL,
    [FechaEnvio] DATETIME NULL,
    [NumeroIntentos] INT NULL DEFAULT ((0)),
    [ProviderMessageID] VARCHAR(200) NULL,
    [ErrorMensajeSeguro] NVARCHAR(500) NULL,
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Comercial_AlertasMargenEnvios] PRIMARY KEY ([EnvioID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_AlertasMargenEventos]
-- ============================================================
CREATE TABLE [dbo].[Comercial_AlertasMargenEventos] (
    [AlertaMargenEventoID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [FechaEvaluacion] DATETIME NULL DEFAULT (getdate()),
    [ServerID] UNIQUEIDENTIFIER NULL,
    [EmpresaID] INT NULL,
    [SucursalID] INT NULL,
    [UnidadNegocioID] INT NULL,
    [ProductoClave] VARCHAR(100) NOT NULL,
    [ProductoNombre] NVARCHAR(500) NULL,
    [GrupoCodigo] VARCHAR(100) NULL,
    [FamiliaCodigo] VARCHAR(100) NULL,
    [SubfamiliaCodigo] VARCHAR(100) NULL,
    [PrecioVentaActual] DECIMAL(18,4) NULL,
    [CostoRecetaActual] DECIMAL(18,4) NULL,
    [MargenActualPorcentaje] DECIMAL(5,2) NULL,
    [MargenActualMonto] DECIMAL(18,4) NULL,
    [MargenEsperadoPorcentaje] DECIMAL(5,2) NULL,
    [DiferenciaPuntos] DECIMAL(5,2) NULL,
    [UtilidadActual] DECIMAL(18,4) NULL,
    [UtilidadEsperada] DECIMAL(18,4) NULL,
    [PerdidaPorUnidad] DECIMAL(18,4) NULL,
    [ReglaMargenID] UNIQUEIDENTIFIER NULL,
    [FuenteRegla] VARCHAR(20) NULL,
    [Severidad] VARCHAR(20) NOT NULL,
    [Estado] VARCHAR(30) NULL DEFAULT ('NUEVA'),
    [SnapshotID] UNIQUEIDENTIFIER NULL,
    [VariacionCostoAnterior] DECIMAL(18,4) NULL,
    [VariacionCostoAcumulada] DECIMAL(18,4) NULL,
    [Recomendacion] NVARCHAR(500) NULL,
    [ErrorDatos] BIT NULL DEFAULT ((0)),
    [NotasInternas] NVARCHAR(MAX) NULL,
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME NULL,
    [FechaResolucion] DATETIME NULL,
    [ResueltoPor] VARCHAR(100) NULL,
    CONSTRAINT [PK_Comercial_AlertasMargenEventos] PRIMARY KEY ([AlertaMargenEventoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_AlertasMargenReglas]
-- ============================================================
CREATE TABLE [dbo].[Comercial_AlertasMargenReglas] (
    [ReglaMargenID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [NivelAplicacion] VARCHAR(20) NOT NULL,
    [GrupoCodigo] VARCHAR(100) NULL,
    [FamiliaCodigo] VARCHAR(100) NULL,
    [SubfamiliaCodigo] VARCHAR(100) NULL,
    [ProductoClave] VARCHAR(100) NULL,
    [EmpresaID] INT NULL,
    [SucursalID] INT NULL,
    [ServerID] UNIQUEIDENTIFIER NULL,
    [MargenPorcentajeEsperado] DECIMAL(5,2) NULL,
    [CostoMaximoPorcentaje] DECIMAL(5,2) NULL,
    [UtilidadMinimaPorcentaje] DECIMAL(5,2) NULL,
    [SeveridadBase] VARCHAR(20) NULL DEFAULT ('MEDIA'),
    [Descripcion] NVARCHAR(500) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaInicioVigencia] DATETIME NULL DEFAULT (getdate()),
    [FechaFinVigencia] DATETIME NULL,
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME NULL,
    [CreadoPor] VARCHAR(100) NULL,
    [ModificadoPor] VARCHAR(100) NULL,
    CONSTRAINT [PK_Comercial_AlertasMargenReglas] PRIMARY KEY ([ReglaMargenID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_AlertasUmbralesSeveridad]
-- ============================================================
CREATE TABLE [dbo].[Comercial_AlertasUmbralesSeveridad] (
    [UmbralID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [Severidad] VARCHAR(20) NOT NULL,
    [PuntosDesde] DECIMAL(5,2) NOT NULL,
    [PuntosHasta] DECIMAL(5,2) NOT NULL,
    [IncluirUtilidadNegativa] BIT NULL DEFAULT ((0)),
    [IncluirCostoMayorPrecio] BIT NULL DEFAULT ((0)),
    [Descripcion] NVARCHAR(200) NULL,
    [ColorHex] VARCHAR(7) NULL DEFAULT ('#FFA500'),
    [Activo] BIT NULL DEFAULT ((1)),
    [Orden] INT NULL DEFAULT ((0)),
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME NULL,
    CONSTRAINT [PK_Comercial_AlertasUmbralesSeveridad] PRIMARY KEY ([UmbralID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_Competidores]
-- ============================================================
CREATE TABLE [dbo].[Comercial_Competidores] (
    [CompetidorID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] INT NOT NULL,
    [UnidadNegocioID] INT NULL,
    [NombreCompetidor] NVARCHAR(200) NOT NULL,
    [TipoRestaurante] VARCHAR(50) NULL,
    [SegmentoPrecio] VARCHAR(30) NULL,
    [Ciudad] NVARCHAR(100) NULL,
    [Estado] NVARCHAR(100) NULL,
    [Pais] VARCHAR(50) NULL DEFAULT ('México'),
    [ZonaComercial] NVARCHAR(200) NULL,
    [SitioWeb] NVARCHAR(500) NULL,
    [UrlMenu] NVARCHAR(500) NULL,
    [UrlGoogleMaps] NVARCHAR(500) NULL,
    [UrlInstagram] NVARCHAR(500) NULL,
    [UrlTripAdvisor] NVARCHAR(500) NULL,
    [UrlOpenTable] NVARCHAR(500) NULL,
    [EsCompetenciaDirecta] BIT NULL DEFAULT ((1)),
    [EsBenchmarkAspiracional] BIT NULL DEFAULT ((0)),
    [DistanciaKm] DECIMAL(10,2) NULL,
    [Prioridad] INT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NULL DEFAULT (getdate()),
    [UsuarioCreacion] NVARCHAR(100) NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacion] NVARCHAR(100) NULL,
    [UrlFacebook] NVARCHAR(500) NULL,
    [Notas] NVARCHAR(1000) NULL,
    CONSTRAINT [PK_Comercial_Competidores] PRIMARY KEY ([CompetidorID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_CompetidoresCatalogo]
-- ============================================================
CREATE TABLE [dbo].[Comercial_CompetidoresCatalogo] (
    [CompetidorCatalogoID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [NombreCompetidor] NVARCHAR(200) NOT NULL,
    [TipoRestaurante] VARCHAR(50) NULL,
    [SegmentoPrecio] VARCHAR(30) NULL,
    [Ciudad] NVARCHAR(100) NULL,
    [Estado] NVARCHAR(100) NULL,
    [Pais] VARCHAR(50) NULL DEFAULT ('México'),
    [ZonaComercial] NVARCHAR(200) NULL,
    [DireccionCompleta] NVARCHAR(500) NULL,
    [Latitud] DECIMAL(10,7) NULL,
    [Longitud] DECIMAL(10,7) NULL,
    [SitioWeb] NVARCHAR(500) NULL,
    [UrlMenu] NVARCHAR(500) NULL,
    [UrlGoogleMaps] NVARCHAR(500) NULL,
    [UrlInstagram] NVARCHAR(500) NULL,
    [UrlFacebook] NVARCHAR(500) NULL,
    [UrlTripAdvisor] NVARCHAR(500) NULL,
    [UrlOpenTable] NVARCHAR(500) NULL,
    [Notas] NVARCHAR(1000) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NULL DEFAULT (getdate()),
    [UsuarioCreacion] NVARCHAR(100) NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacion] NVARCHAR(100) NULL,
    CONSTRAINT [PK_Comercial_CompetidoresCatalogo] PRIMARY KEY ([CompetidorCatalogoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_CompetidoresListas]
-- ============================================================
CREATE TABLE [dbo].[Comercial_CompetidoresListas] (
    [ListaCompetidoresID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [NombreLista] NVARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [EmpresaID] INT NULL,
    [UnidadNegocioID] INT NULL,
    [Segmento] NVARCHAR(100) NULL,
    [Categoria] NVARCHAR(100) NULL,
    [ColorIdentificador] NVARCHAR(20) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME2 NULL,
    [CreadoPor] NVARCHAR(100) NOT NULL,
    [ModificadoPor] NVARCHAR(100) NULL,
    CONSTRAINT [PK_Comercial_CompetidoresListas] PRIMARY KEY ([ListaCompetidoresID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_CompetidoresListasDetalle]
-- ============================================================
CREATE TABLE [dbo].[Comercial_CompetidoresListasDetalle] (
    [ListaDetalleID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [ListaCompetidoresID] UNIQUEIDENTIFIER NOT NULL,
    [CompetidorID] UNIQUEIDENTIFIER NOT NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [Notas] NVARCHAR(500) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME2 NULL,
    [CreadoPor] NVARCHAR(100) NOT NULL,
    [ModificadoPor] NVARCHAR(100) NULL,
    CONSTRAINT [PK_Comercial_CompetidoresListasDetalle] PRIMARY KEY ([ListaDetalleID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_CompetidoresMenuItems]
-- ============================================================
CREATE TABLE [dbo].[Comercial_CompetidoresMenuItems] (
    [CompetidorMenuItemID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [CompetidorID] UNIQUEIDENTIFIER NOT NULL,
    [NombreProductoCompetidor] NVARCHAR(300) NOT NULL,
    [CategoriaCompetidor] NVARCHAR(100) NULL,
    [Descripcion] NVARCHAR(1000) NULL,
    [Precio] DECIMAL(18,2) NULL,
    [Moneda] VARCHAR(10) NULL DEFAULT ('MXN'),
    [FuenteUrl] NVARCHAR(500) NULL,
    [FechaConsulta] DATE NULL,
    [MetodoObtencion] VARCHAR(30) NOT NULL,
    [ConfianzaDato] VARCHAR(20) NULL DEFAULT ('MEDIA'),
    [EsDatoManual] BIT NULL DEFAULT ((0)),
    [EsDatoIA] BIT NULL DEFAULT ((0)),
    [PayloadJSON] NVARCHAR(MAX) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NULL DEFAULT (getdate()),
    [UsuarioCreacion] NVARCHAR(100) NULL,
    CONSTRAINT [PK_Comercial_CompetidoresMenuItems] PRIMARY KEY ([CompetidorMenuItemID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_CompetidoresUnidad]
-- ============================================================
CREATE TABLE [dbo].[Comercial_CompetidoresUnidad] (
    [CompetidorUnidadID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [CompetidorCatalogoID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] INT NOT NULL,
    [UnidadNegocioID] INT NOT NULL,
    [EsCompetenciaDirecta] BIT NULL DEFAULT ((1)),
    [EsBenchmarkAspiracional] BIT NULL DEFAULT ((0)),
    [TipoRelacion] VARCHAR(50) NULL DEFAULT ('COMPETENCIA_DIRECTA'),
    [Prioridad] INT NULL DEFAULT ((0)),
    [DistanciaKm] DECIMAL(10,2) NULL,
    [Comentarios] NVARCHAR(500) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NULL DEFAULT (getdate()),
    [UsuarioCreacion] NVARCHAR(100) NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacion] NVARCHAR(100) NULL,
    CONSTRAINT [PK_Comercial_CompetidoresUnidad] PRIMARY KEY ([CompetidorUnidadID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_Dashboard_Cache]
-- ============================================================
CREATE TABLE [dbo].[Comercial_Dashboard_Cache] (
    [CacheID] INT NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [PeriodoKey] VARCHAR(100) NOT NULL,
    [DataJSON] NVARCHAR(MAX) NULL,
    [UpdatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Comercial_Dashboard_Cache] PRIMARY KEY ([CacheID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_ImpuestosCatalogo]
-- ============================================================
CREATE TABLE [dbo].[Comercial_ImpuestosCatalogo] (
    [ImpuestoID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [Codigo] VARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [TipoImpuesto] VARCHAR(20) NOT NULL,
    [PaisISO] VARCHAR(3) NULL DEFAULT ('MEX'),
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [CreadoPor] NVARCHAR(100) NULL,
    [ModificadoPor] NVARCHAR(100) NULL,
    CONSTRAINT [PK_Comercial_ImpuestosCatalogo] PRIMARY KEY ([ImpuestoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_ImpuestosMapeo]
-- ============================================================
CREATE TABLE [dbo].[Comercial_ImpuestosMapeo] (
    [MapeoProductoID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [ServerID] UNIQUEIDENTIFIER NOT NULL,
    [SystemType] VARCHAR(50) NOT NULL,
    [CodigoProducto] VARCHAR(100) NOT NULL,
    [NombreProducto] NVARCHAR(500) NULL,
    [ImpuestoCanonicoID] UNIQUEIDENTIFIER NULL,
    [TasaCanonicoID] UNIQUEIDENTIFIER NULL,
    [TasaEfectiva] DECIMAL(10,4) NULL,
    [EstadoFiscal] VARCHAR(30) NOT NULL,
    [FuenteOrigen] VARCHAR(20) NULL,
    [Observaciones] NVARCHAR(500) NULL,
    [SyncRunID] VARCHAR(100) NULL,
    [FechaSincronizacion] DATETIME2 NULL,
    [FechaCreacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Comercial_ImpuestosMapeo] PRIMARY KEY ([MapeoProductoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_ImpuestosOverrides]
-- ============================================================
CREATE TABLE [dbo].[Comercial_ImpuestosOverrides] (
    [OverrideID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [TipoOverride] VARCHAR(30) NOT NULL,
    [ServerID] UNIQUEIDENTIFIER NULL,
    [CodigoProducto] VARCHAR(100) NULL,
    [FamiliaCodigoFuente] VARCHAR(50) NULL,
    [UnidadNegocioID] UNIQUEIDENTIFIER NULL,
    [SucursalID] UNIQUEIDENTIFIER NULL,
    [RegionCodigo] VARCHAR(10) NULL,
    [PaisCodigo] VARCHAR(3) NULL,
    [ImpuestoCanonicoID] UNIQUEIDENTIFIER NOT NULL,
    [TasaCanonicoID] UNIQUEIDENTIFIER NOT NULL,
    [TasaOverride] DECIMAL(10,4) NOT NULL,
    [Motivo] NVARCHAR(500) NOT NULL,
    [AutorizadoPor] NVARCHAR(200) NOT NULL,
    [FechaAutorizacion] DATETIME2 NOT NULL,
    [VigenciaDesde] DATE NOT NULL,
    [VigenciaHasta] DATE NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Comercial_ImpuestosOverrides] PRIMARY KEY ([OverrideID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_ImpuestosTasas]
-- ============================================================
CREATE TABLE [dbo].[Comercial_ImpuestosTasas] (
    [TasaID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [ImpuestoID] UNIQUEIDENTIFIER NOT NULL,
    [Tasa] DECIMAL(10,4) NOT NULL,
    [TipoFactor] VARCHAR(20) NOT NULL,
    [VigenciaDesde] DATE NOT NULL,
    [VigenciaHasta] DATE NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Comercial_ImpuestosTasas] PRIMARY KEY ([TasaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_KPIs_Cache]
-- ============================================================
CREATE TABLE [dbo].[Comercial_KPIs_Cache] (
    [CacheID] INT NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [PeriodoKey] VARCHAR(100) NOT NULL,
    [KPIsJSON] NVARCHAR(MAX) NULL,
    [UpdatedAt] DATETIME NULL DEFAULT (getdate()),
    [Status] VARCHAR(20) NULL DEFAULT ('online'),
    CONSTRAINT [PK_Comercial_KPIs_Cache] PRIMARY KEY ([CacheID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_KPIs_Diarios_v2]
-- ============================================================
CREATE TABLE [dbo].[Comercial_KPIs_Diarios_v2] (
    [id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [unidad_negocio_id] NVARCHAR(50) NOT NULL,
    [unidad_negocio_nombre] NVARCHAR(100) NOT NULL,
    [server_id] NVARCHAR(50) NOT NULL,
    [sucursal_id] NVARCHAR(50) NOT NULL DEFAULT ('DEFAULT'),
    [sucursal_nombre] NVARCHAR(100) NULL,
    [sistema_origen] NVARCHAR(20) NOT NULL,
    [fecha_operacion] DATE NOT NULL,
    [anio] INT NOT NULL,
    [mes] INT NOT NULL,
    [dia] INT NOT NULL,
    [ventas_total] DECIMAL(18,2) NULL DEFAULT ((0)),
    [ventas_sin_propina] DECIMAL(18,2) NULL DEFAULT ((0)),
    [propinas_total] DECIMAL(18,2) NULL DEFAULT ((0)),
    [tickets_total] INT NULL DEFAULT ((0)),
    [pax_total] INT NULL DEFAULT ((0)),
    [ticket_promedio] DECIMAL(18,2) NULL DEFAULT ((0)),
    [pax_promedio] DECIMAL(18,2) NULL DEFAULT ((0)),
    [ventas_cerradas] DECIMAL(18,2) NULL DEFAULT ((0)),
    [ventas_abiertas] DECIMAL(18,2) NULL DEFAULT ((0)),
    [total_estimado_dia] DECIMAL(18,2) NULL DEFAULT ((0)),
    [es_venta_abierta] BIT NULL DEFAULT ((0)),
    [es_corte_cerrado] BIT NULL DEFAULT ((0)),
    [es_demo] BIT NULL DEFAULT ((0)),
    [activo] BIT NULL DEFAULT ((1)),
    [fuente_original] NVARCHAR(50) NOT NULL,
    [id_origen] NVARCHAR(100) NULL,
    [hash_origen] NVARCHAR(64) NULL,
    [sync_run_id] NVARCHAR(50) NULL,
    [fecha_sincronizacion] DATETIME2 NULL DEFAULT (sysutcdatetime()),
    [fecha_alta] DATETIME2 NULL DEFAULT (sysutcdatetime()),
    [fecha_ultima_actualizacion] DATETIME2 NULL DEFAULT (sysutcdatetime()),
    [version] INT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Comercial_KPIs_Diarios_v2] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_KPIs_Diarios_v2_backup_migracion_codigos_20260513_0558]
-- ============================================================
CREATE TABLE [dbo].[Comercial_KPIs_Diarios_v2_backup_migracion_codigos_20260513_0558] (
    [id] UNIQUEIDENTIFIER NOT NULL,
    [unidad_negocio_id] NVARCHAR(50) NOT NULL,
    [unidad_negocio_nombre] NVARCHAR(100) NOT NULL,
    [server_id] NVARCHAR(50) NOT NULL,
    [sucursal_id] NVARCHAR(50) NOT NULL,
    [sucursal_nombre] NVARCHAR(100) NULL,
    [sistema_origen] NVARCHAR(20) NOT NULL,
    [fecha_operacion] DATE NOT NULL,
    [anio] INT NOT NULL,
    [mes] INT NOT NULL,
    [dia] INT NOT NULL,
    [ventas_total] DECIMAL(18,2) NULL,
    [ventas_sin_propina] DECIMAL(18,2) NULL,
    [propinas_total] DECIMAL(18,2) NULL,
    [tickets_total] INT NULL,
    [pax_total] INT NULL,
    [ticket_promedio] DECIMAL(18,2) NULL,
    [pax_promedio] DECIMAL(18,2) NULL,
    [ventas_cerradas] DECIMAL(18,2) NULL,
    [ventas_abiertas] DECIMAL(18,2) NULL,
    [total_estimado_dia] DECIMAL(18,2) NULL,
    [es_venta_abierta] BIT NULL,
    [es_corte_cerrado] BIT NULL,
    [es_demo] BIT NULL,
    [activo] BIT NULL,
    [fuente_original] NVARCHAR(50) NOT NULL,
    [id_origen] NVARCHAR(100) NULL,
    [hash_origen] NVARCHAR(64) NULL,
    [sync_run_id] NVARCHAR(50) NULL,
    [fecha_sincronizacion] DATETIME2 NULL,
    [fecha_alta] DATETIME2 NULL,
    [fecha_ultima_actualizacion] DATETIME2 NULL,
    [version] INT NULL,
    [fecha_backup] DATETIME NOT NULL,
    [fase_migracion] VARCHAR(25) NOT NULL,
    [criterio_backup] NVARCHAR(50) NOT NULL
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_KPIs_Historico]
-- ============================================================
CREATE TABLE [dbo].[Comercial_KPIs_Historico] (
    [id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [run_id] NVARCHAR(100) NOT NULL,
    [server_id] NVARCHAR(100) NOT NULL,
    [sucursal_id] NVARCHAR(100) NOT NULL,
    [sucursal_nombre] NVARCHAR(255) NULL,
    [empresa_id] NVARCHAR(100) NULL,
    [unidad_negocio_id] NVARCHAR(100) NULL,
    [system_type_normalized] NVARCHAR(50) NOT NULL,
    [fecha] DATE NOT NULL,
    [kpi_tipo] NVARCHAR(50) NOT NULL DEFAULT ('DIARIO'),
    [ventas_total] DECIMAL(18,2) NULL DEFAULT ((0)),
    [tickets_total] INT NULL DEFAULT ((0)),
    [pax_total] INT NULL DEFAULT ((0)),
    [ticket_promedio] DECIMAL(18,2) NULL DEFAULT ((0)),
    [propinas_total] DECIMAL(18,2) NULL DEFAULT ((0)),
    [source_hash] NVARCHAR(128) NULL,
    [source_batch_start] DATE NULL,
    [source_batch_end] DATE NULL,
    [metadata_json] NVARCHAR(MAX) NULL,
    [version] INT NOT NULL DEFAULT ((1)),
    [created_at] DATETIME2 NOT NULL DEFAULT (sysutcdatetime()),
    [updated_at] DATETIME2 NOT NULL DEFAULT (sysutcdatetime()),
    CONSTRAINT [PK_Comercial_KPIs_Historico] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_KPIs_Mensuales_v2]
-- ============================================================
CREATE TABLE [dbo].[Comercial_KPIs_Mensuales_v2] (
    [id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [unidad_negocio_id] NVARCHAR(50) NOT NULL,
    [unidad_negocio_nombre] NVARCHAR(100) NOT NULL,
    [server_id] NVARCHAR(50) NOT NULL,
    [sucursal_id] NVARCHAR(50) NOT NULL DEFAULT ('DEFAULT'),
    [sucursal_nombre] NVARCHAR(100) NULL,
    [sistema_origen] NVARCHAR(20) NOT NULL,
    [anio] INT NOT NULL,
    [mes] INT NOT NULL,
    [dias_con_datos] INT NULL DEFAULT ((0)),
    [dias_mes_total] INT NOT NULL,
    [ventas_total] DECIMAL(18,2) NULL DEFAULT ((0)),
    [ventas_sin_propina] DECIMAL(18,2) NULL DEFAULT ((0)),
    [propinas_total] DECIMAL(18,2) NULL DEFAULT ((0)),
    [tickets_total] INT NULL DEFAULT ((0)),
    [pax_total] INT NULL DEFAULT ((0)),
    [ticket_promedio] DECIMAL(18,2) NULL DEFAULT ((0)),
    [pax_promedio] DECIMAL(18,2) NULL DEFAULT ((0)),
    [proyeccion_mes] DECIMAL(18,2) NULL DEFAULT ((0)),
    [ventas_mes_anterior] DECIMAL(18,2) NULL DEFAULT ((0)),
    [var_vs_mes_anterior] DECIMAL(8,2) NULL DEFAULT ((0)),
    [ventas_anio_anterior] DECIMAL(18,2) NULL DEFAULT ((0)),
    [var_vs_anio_anterior] DECIMAL(8,2) NULL DEFAULT ((0)),
    [es_mes_completo] BIT NULL DEFAULT ((0)),
    [es_demo] BIT NULL DEFAULT ((0)),
    [activo] BIT NULL DEFAULT ((1)),
    [sync_run_id] NVARCHAR(50) NULL,
    [fecha_calculo] DATETIME2 NULL DEFAULT (sysutcdatetime()),
    [fecha_ultima_actualizacion] DATETIME2 NULL DEFAULT (sysutcdatetime()),
    [version] INT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Comercial_KPIs_Mensuales_v2] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_Metas]
-- ============================================================
CREATE TABLE [dbo].[Comercial_Metas] (
    [MetaID] INT NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [Sucursal] VARCHAR(100) NOT NULL,
    [Mes] INT NOT NULL,
    [Anio] INT NOT NULL,
    [MetaVentas] DECIMAL(18,2) NULL DEFAULT ((0)),
    [MetaCheques] INT NULL DEFAULT ((0)),
    [MetaPax] INT NULL DEFAULT ((0)),
    [MetaTicketPromedio] DECIMAL(18,2) NULL DEFAULT ((0)),
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Comercial_Metas] PRIMARY KEY ([MetaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_PreciosSugeridos]
-- ============================================================
CREATE TABLE [dbo].[Comercial_PreciosSugeridos] (
    [PrecioSugeridoID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [ProductoID] UNIQUEIDENTIFIER NULL,
    [ServerID] UNIQUEIDENTIFIER NOT NULL,
    [CodigoProducto] VARCHAR(100) NOT NULL,
    [NombreProducto] NVARCHAR(500) NULL,
    [SystemType] VARCHAR(50) NULL,
    [EmpresaID] UNIQUEIDENTIFIER NULL,
    [UnidadNegocioID] UNIQUEIDENTIFIER NULL,
    [ReglaPrecioID] UNIQUEIDENTIFIER NULL,
    [ReglaPrecioRangoID] UNIQUEIDENTIFIER NULL,
    [CostoBotella] DECIMAL(18,4) NULL,
    [FuenteCostoBotella] VARCHAR(50) NULL,
    [MargenMultiplicador] DECIMAL(6,4) NULL,
    [ImpuestoMapeoID] UNIQUEIDENTIFIER NULL,
    [TasaImpuestoAplicada] DECIMAL(6,4) NULL,
    [PrecioBase] DECIMAL(18,4) NULL,
    [ImporteImpuesto] DECIMAL(18,4) NULL,
    [PrecioConImpuesto] DECIMAL(18,4) NULL,
    [MetodoRedondeo] VARCHAR(20) NULL,
    [MultiploRedondeo] INT NULL,
    [PrecioSugerido] DECIMAL(18,2) NULL,
    [EstadoCalculo] VARCHAR(40) NOT NULL,
    [MensajeEstado] NVARCHAR(500) NULL,
    [SyncRunID] VARCHAR(100) NULL,
    [FechaCalculo] DATETIME2 NULL DEFAULT (sysdatetime()),
    [UsuarioCalculo] NVARCHAR(100) NULL,
    [TipoMotorPrecio] VARCHAR(50) NULL DEFAULT ('VINOS_RANGOS'),
    [FuenteBenchmark] VARCHAR(50) NULL,
    [PrecioCompetenciaMin] DECIMAL(18,2) NULL,
    [PrecioCompetenciaPromedio] DECIMAL(18,2) NULL,
    [PrecioCompetenciaMax] DECIMAL(18,2) NULL,
    [PosicionVsCompetencia] VARCHAR(30) NULL,
    [MargenObjetivo] DECIMAL(8,4) NULL,
    [MargenActual] DECIMAL(8,4) NULL,
    [MargenSugerido] DECIMAL(8,4) NULL,
    [JustificacionIA] NVARCHAR(MAX) NULL,
    [ConfianzaIA] VARCHAR(20) NULL,
    [RequiereRevisionHumana] BIT NULL DEFAULT ((1)),
    [FechaAnalisisIA] DATETIME2 NULL,
    [ModeloIAUsado] VARCHAR(100) NULL,
    [VersionRegla] VARCHAR(50) NULL,
    [PayloadAnalisisJSON] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_Comercial_PreciosSugeridos] PRIMARY KEY ([PrecioSugeridoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_PricingAnalisisIA]
-- ============================================================
CREATE TABLE [dbo].[Comercial_PricingAnalisisIA] (
    [AnalisisIAID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [ProductoID] UNIQUEIDENTIFIER NULL,
    [CodigoProducto] NVARCHAR(100) NOT NULL,
    [ServerID] UNIQUEIDENTIFIER NULL,
    [EmpresaID] INT NOT NULL,
    [UnidadNegocioID] INT NOT NULL,
    [TipoAnalisis] VARCHAR(50) NOT NULL,
    [ModeloIAUsado] VARCHAR(50) NOT NULL,
    [VersionModelo] VARCHAR(50) NOT NULL,
    [PromptResumen] NVARCHAR(1000) NULL,
    [DatosEntradaJSON] NVARCHAR(MAX) NULL,
    [RespuestaIAJSON] NVARCHAR(MAX) NULL,
    [JustificacionIA] NVARCHAR(MAX) NULL,
    [ConfianzaIA] VARCHAR(20) NOT NULL,
    [RequiereRevisionHumana] BIT NULL DEFAULT ((0)),
    [PrecioActual] DECIMAL(18,2) NULL,
    [PrecioSugerido] DECIMAL(18,2) NULL,
    [MargenActual] DECIMAL(8,4) NULL,
    [MargenSugerido] DECIMAL(8,4) NULL,
    [CompetidoresUsadosJSON] NVARCHAR(MAX) NULL,
    [FuentesUsadasJSON] NVARCHAR(MAX) NULL,
    [EstadoAnalisis] VARCHAR(30) NOT NULL,
    [UsuarioEjecucion] NVARCHAR(100) NOT NULL,
    [FechaEjecucion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [ListaCompetidoresID] UNIQUEIDENTIFIER NULL,
    CONSTRAINT [PK_Comercial_PricingAnalisisIA] PRIMARY KEY ([AnalisisIAID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_PricingBenchmarkProducto]
-- ============================================================
CREATE TABLE [dbo].[Comercial_PricingBenchmarkProducto] (
    [BenchmarkProductoID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [ProductoID] UNIQUEIDENTIFIER NULL,
    [CodigoProducto] VARCHAR(100) NULL,
    [ServerID] UNIQUEIDENTIFIER NULL,
    [EmpresaID] INT NOT NULL,
    [UnidadNegocioID] INT NULL,
    [CompetidorID] UNIQUEIDENTIFIER NOT NULL,
    [CompetidorMenuItemID] UNIQUEIDENTIFIER NULL,
    [Similitud] DECIMAL(5,2) NULL,
    [TipoComparacion] VARCHAR(30) NOT NULL,
    [ComentarioIA] NVARCHAR(MAX) NULL,
    [ValidadoPorUsuario] BIT NULL DEFAULT ((0)),
    [UsuarioValidacion] NVARCHAR(100) NULL,
    [FechaValidacion] DATETIME2 NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NULL DEFAULT (getdate()),
    [UsuarioCreacion] NVARCHAR(100) NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacion] NVARCHAR(100) NULL,
    CONSTRAINT [PK_Comercial_PricingBenchmarkProducto] PRIMARY KEY ([BenchmarkProductoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_RecetasSnapshot]
-- ============================================================
CREATE TABLE [dbo].[Comercial_RecetasSnapshot] (
    [RecetaSnapshotID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [FechaSnapshot] DATETIME NULL DEFAULT (getdate()),
    [ServerID] UNIQUEIDENTIFIER NULL,
    [EmpresaID] INT NULL,
    [SucursalID] INT NULL,
    [UnidadNegocioID] INT NULL,
    [ProductoClave] VARCHAR(100) NOT NULL,
    [ProductoNombre] NVARCHAR(500) NULL,
    [PrecioVenta] DECIMAL(18,4) NULL,
    [CostoRecetaTotal] DECIMAL(18,4) NULL,
    [MargenPorcentaje] DECIMAL(5,2) NULL,
    [MargenMonto] DECIMAL(18,4) NULL,
    [NumeroInsumos] INT NULL DEFAULT ((0)),
    [HashReceta] VARCHAR(64) NULL,
    [FuenteCalculo] VARCHAR(50) NULL DEFAULT ('SYNC_RECETAS'),
    [SnapshotAnteriorID] UNIQUEIDENTIFIER NULL,
    [VariacionCosto] DECIMAL(18,4) NULL,
    [VariacionCostoPorcentaje] DECIMAL(5,2) NULL,
    [VariacionMargen] DECIMAL(5,2) NULL,
    [EsActual] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    [CreadoPor] VARCHAR(100) NULL DEFAULT ('SISTEMA'),
    [SyncRunID] VARCHAR(100) NULL,
    CONSTRAINT [PK_Comercial_RecetasSnapshot] PRIMARY KEY ([RecetaSnapshotID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_RecetasSnapshotDetalle]
-- ============================================================
CREATE TABLE [dbo].[Comercial_RecetasSnapshotDetalle] (
    [RecetaSnapshotDetalleID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [RecetaSnapshotID] UNIQUEIDENTIFIER NOT NULL,
    [InsumoClave] VARCHAR(100) NOT NULL,
    [InsumoNombre] NVARCHAR(500) NULL,
    [Cantidad] DECIMAL(18,6) NULL,
    [UnidadMedida] VARCHAR(50) NULL,
    [CostoUnitario] DECIMAL(18,4) NULL,
    [CostoTotal] DECIMAL(18,4) NULL,
    [PorcentajeDelCosto] DECIMAL(5,2) NULL,
    [EsElaborado] BIT NULL DEFAULT ((0)),
    [CostoAnterior] DECIMAL(18,4) NULL,
    [VariacionCosto] DECIMAL(18,4) NULL,
    [VariacionCostoPorcentaje] DECIMAL(5,2) NULL,
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    [Orden] INT NULL DEFAULT ((0)),
    CONSTRAINT [PK_Comercial_RecetasSnapshotDetalle] PRIMARY KEY ([RecetaSnapshotDetalleID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_ReglasPrecio]
-- ============================================================
CREATE TABLE [dbo].[Comercial_ReglasPrecio] (
    [ReglaPrecioID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [Codigo] VARCHAR(50) NOT NULL,
    [NombreRegla] NVARCHAR(200) NOT NULL,
    [TipoRegla] VARCHAR(30) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [AplicaAFamiliaID] UNIQUEIDENTIFIER NULL,
    [AplicaASubfamiliaID] UNIQUEIDENTIFIER NULL,
    [AplicaATipoProducto] VARCHAR(50) NULL,
    [EmpresaID] UNIQUEIDENTIFIER NULL,
    [UnidadNegocioID] UNIQUEIDENTIFIER NULL,
    [SucursalID] UNIQUEIDENTIFIER NULL,
    [PaisCodigo] VARCHAR(3) NULL DEFAULT ('MEX'),
    [RegionCodigo] VARCHAR(10) NULL,
    [MetodoRedondeo] VARCHAR(20) NOT NULL DEFAULT ('MAS_CERCANO'),
    [MultiploRedondeo] INT NOT NULL DEFAULT ((5)),
    [PermiteGaps] BIT NULL DEFAULT ((0)),
    [UsaCostoReceta] BIT NULL DEFAULT ((0)),
    [UsaCostoBotella] BIT NULL DEFAULT ((1)),
    [Activo] BIT NULL DEFAULT ((1)),
    [VigenciaDesde] DATE NOT NULL,
    [VigenciaHasta] DATE NULL,
    [FechaCreacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [UsuarioCreacion] NVARCHAR(100) NULL,
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [UsuarioModificacion] NVARCHAR(100) NULL,
    CONSTRAINT [PK_Comercial_ReglasPrecio] PRIMARY KEY ([ReglaPrecioID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_ReglasPrecioRangos]
-- ============================================================
CREATE TABLE [dbo].[Comercial_ReglasPrecioRangos] (
    [ReglaPrecioRangoID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [ReglaPrecioID] UNIQUEIDENTIFIER NOT NULL,
    [LimiteInferior] DECIMAL(18,2) NOT NULL,
    [LimiteSuperior] DECIMAL(18,2) NOT NULL,
    [MargenMultiplicador] DECIMAL(6,4) NOT NULL,
    [Orden] INT NOT NULL,
    [Descripcion] NVARCHAR(200) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [UsuarioCreacion] NVARCHAR(100) NULL,
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [UsuarioModificacion] NVARCHAR(100) NULL,
    CONSTRAINT [PK_Comercial_ReglasPrecioRangos] PRIMARY KEY ([ReglaPrecioRangoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_SimulacionesPrecios]
-- ============================================================
CREATE TABLE [dbo].[Comercial_SimulacionesPrecios] (
    [SimulacionID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [ProductoID] UNIQUEIDENTIFIER NOT NULL,
    [CodigoProducto] VARCHAR(100) NOT NULL,
    [NombreProducto] NVARCHAR(500) NOT NULL,
    [ServerID] UNIQUEIDENTIFIER NOT NULL,
    [SystemType] VARCHAR(50) NOT NULL,
    [PrecioActual] DECIMAL(18,4) NOT NULL,
    [CostoActual] DECIMAL(18,4) NOT NULL,
    [MargenActualPesos] DECIMAL(18,4) NOT NULL,
    [MargenActualPorcentaje] DECIMAL(10,4) NOT NULL,
    [PrecioSimulado] DECIMAL(18,4) NOT NULL,
    [MargenSimuladoPesos] DECIMAL(18,4) NOT NULL,
    [MargenSimuladoPorcentaje] DECIMAL(10,4) NOT NULL,
    [VariacionPesos] DECIMAL(18,4) NOT NULL,
    [VariacionPorcentaje] DECIMAL(10,4) NOT NULL,
    [MargenObjetivo] DECIMAL(10,4) NULL,
    [Recomendacion] VARCHAR(100) NULL,
    [ImpactoEstimado] NVARCHAR(500) NULL,
    [SyncRunID] VARCHAR(100) NULL,
    [ConvertidoASolicitud] BIT NULL DEFAULT ((0)),
    [SolicitudID] UNIQUEIDENTIFIER NULL,
    [UsuarioID] UNIQUEIDENTIFIER NOT NULL,
    [UsuarioEmail] VARCHAR(200) NOT NULL,
    [FechaSimulacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [IPSimulacion] VARCHAR(50) NULL,
    CONSTRAINT [PK_Comercial_SimulacionesPrecios] PRIMARY KEY ([SimulacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_SolicitudesCambioPrecio]
-- ============================================================
CREATE TABLE [dbo].[Comercial_SolicitudesCambioPrecio] (
    [SolicitudID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [FolioSolicitud] VARCHAR(50) NOT NULL,
    [ProductoID] UNIQUEIDENTIFIER NOT NULL,
    [CodigoProducto] VARCHAR(100) NOT NULL,
    [NombreProducto] NVARCHAR(500) NOT NULL,
    [ServerID] UNIQUEIDENTIFIER NOT NULL,
    [SystemType] VARCHAR(50) NOT NULL,
    [FamiliaCodigoFuente] VARCHAR(50) NULL,
    [FamiliaNombre] NVARCHAR(200) NULL,
    [EmpresaID] UNIQUEIDENTIFIER NULL,
    [UnidadNegocioID] UNIQUEIDENTIFIER NULL,
    [PrecioActual] DECIMAL(18,4) NOT NULL,
    [PrecioSolicitado] DECIMAL(18,4) NOT NULL,
    [VariacionPesos] DECIMAL(18,4) NOT NULL,
    [VariacionPorcentaje] DECIMAL(10,4) NOT NULL,
    [CostoActual] DECIMAL(18,4) NOT NULL,
    [MargenActualPesos] DECIMAL(18,4) NOT NULL,
    [MargenActualPorcentaje] DECIMAL(10,4) NOT NULL,
    [MargenSolicitadoPesos] DECIMAL(18,4) NOT NULL,
    [MargenSolicitadoPorcentaje] DECIMAL(10,4) NOT NULL,
    [MargenObjetivo] DECIMAL(10,4) NULL,
    [SyncRunID] VARCHAR(100) NULL,
    [FechaDatosCosto] DATETIME2 NULL,
    [Motivo] NVARCHAR(200) NOT NULL,
    [Justificacion] NVARCHAR(MAX) NULL,
    [Estatus] VARCHAR(20) NOT NULL DEFAULT ('BORRADOR'),
    [SolicitanteUsuarioID] UNIQUEIDENTIFIER NOT NULL,
    [SolicitanteEmail] VARCHAR(200) NOT NULL,
    [SolicitanteNombre] NVARCHAR(200) NULL,
    [FechaSolicitud] DATETIME2 NULL,
    [AutorizadorUsuarioID] UNIQUEIDENTIFIER NULL,
    [AutorizadorEmail] VARCHAR(200) NULL,
    [AutorizadorNombre] NVARCHAR(200) NULL,
    [FechaAutorizacion] DATETIME2 NULL,
    [ComentarioAutorizacion] NVARCHAR(MAX) NULL,
    [ModificadorUsuarioID] UNIQUEIDENTIFIER NULL,
    [ModificadorEmail] VARCHAR(200) NULL,
    [ModificadorNombre] NVARCHAR(200) NULL,
    [FechaAplicacion] DATETIME2 NULL,
    [ComentarioAplicacion] NVARCHAR(MAX) NULL,
    [PrecioAplicado] DECIMAL(18,4) NULL,
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [IPCreacion] VARCHAR(50) NULL,
    CONSTRAINT [PK_Comercial_SolicitudesCambioPrecio] PRIMARY KEY ([SolicitudID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_SolicitudesCambioPrecioHistorial]
-- ============================================================
CREATE TABLE [dbo].[Comercial_SolicitudesCambioPrecioHistorial] (
    [HistorialID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [SolicitudID] UNIQUEIDENTIFIER NOT NULL,
    [Accion] VARCHAR(50) NOT NULL,
    [EstatusAnterior] VARCHAR(20) NULL,
    [EstatusNuevo] VARCHAR(20) NOT NULL,
    [UsuarioID] UNIQUEIDENTIFIER NOT NULL,
    [UsuarioEmail] VARCHAR(200) NOT NULL,
    [UsuarioNombre] NVARCHAR(200) NULL,
    [Comentario] NVARCHAR(MAX) NULL,
    [ValorAnterior] NVARCHAR(MAX) NULL,
    [ValorNuevo] NVARCHAR(MAX) NULL,
    [FechaAccion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [IPAccion] VARCHAR(50) NULL,
    [UserAgent] NVARCHAR(500) NULL,
    CONSTRAINT [PK_Comercial_SolicitudesCambioPrecioHistorial] PRIMARY KEY ([HistorialID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_SyncLog_v2]
-- ============================================================
CREATE TABLE [dbo].[Comercial_SyncLog_v2] (
    [id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [run_id] NVARCHAR(50) NOT NULL,
    [run_timestamp] DATETIME2 NULL DEFAULT (sysutcdatetime()),
    [run_type] NVARCHAR(20) NOT NULL,
    [unidad_negocio_id] NVARCHAR(50) NULL,
    [server_id] NVARCHAR(50) NULL,
    [sucursal_id] NVARCHAR(50) NULL,
    [fecha_inicio] DATE NULL,
    [fecha_fin] DATE NULL,
    [status] NVARCHAR(20) NOT NULL,
    [records_processed] INT NULL DEFAULT ((0)),
    [records_inserted] INT NULL DEFAULT ((0)),
    [records_updated] INT NULL DEFAULT ((0)),
    [records_skipped] INT NULL DEFAULT ((0)),
    [records_errored] INT NULL DEFAULT ((0)),
    [error_code] NVARCHAR(50) NULL,
    [error_message] NVARCHAR(MAX) NULL,
    [duration_seconds] INT NULL,
    [source_connection_status] NVARCHAR(20) NULL,
    [created_at] DATETIME2 NULL DEFAULT (sysutcdatetime()),
    CONSTRAINT [PK_Comercial_SyncLog_v2] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_SyncLog_v2_backup_migracion_codigos_20260513_0558]
-- ============================================================
CREATE TABLE [dbo].[Comercial_SyncLog_v2_backup_migracion_codigos_20260513_0558] (
    [id] UNIQUEIDENTIFIER NOT NULL,
    [run_id] NVARCHAR(50) NOT NULL,
    [run_timestamp] DATETIME2 NULL,
    [run_type] NVARCHAR(20) NOT NULL,
    [unidad_negocio_id] NVARCHAR(50) NULL,
    [server_id] NVARCHAR(50) NULL,
    [sucursal_id] NVARCHAR(50) NULL,
    [fecha_inicio] DATE NULL,
    [fecha_fin] DATE NULL,
    [status] NVARCHAR(20) NOT NULL,
    [records_processed] INT NULL,
    [records_inserted] INT NULL,
    [records_updated] INT NULL,
    [records_skipped] INT NULL,
    [records_errored] INT NULL,
    [error_code] NVARCHAR(50) NULL,
    [error_message] NVARCHAR(MAX) NULL,
    [duration_seconds] INT NULL,
    [source_connection_status] NVARCHAR(20) NULL,
    [created_at] DATETIME2 NULL,
    [fecha_backup] DATETIME NOT NULL,
    [fase_migracion] VARCHAR(25) NOT NULL,
    [criterio_backup] NVARCHAR(50) NULL
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_Ventas_Dia_Abiertas_v2]
-- ============================================================
CREATE TABLE [dbo].[Comercial_Ventas_Dia_Abiertas_v2] (
    [id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [unidad_negocio_id] NVARCHAR(50) NOT NULL,
    [unidad_negocio_nombre] NVARCHAR(100) NOT NULL,
    [server_id] NVARCHAR(50) NOT NULL,
    [sucursal_id] NVARCHAR(50) NOT NULL DEFAULT ('DEFAULT'),
    [sucursal_nombre] NVARCHAR(100) NULL,
    [sistema_origen] NVARCHAR(20) NOT NULL,
    [snapshot_timestamp] DATETIME2 NOT NULL,
    [fecha_operacion] DATE NOT NULL,
    [ventas_abiertas] DECIMAL(18,2) NULL DEFAULT ((0)),
    [tickets_abiertos] INT NULL DEFAULT ((0)),
    [pax_abiertos] INT NULL DEFAULT ((0)),
    [ventas_cerradas_dia] DECIMAL(18,2) NULL DEFAULT ((0)),
    [tickets_cerrados_dia] INT NULL DEFAULT ((0)),
    [pax_cerrados_dia] INT NULL DEFAULT ((0)),
    [total_estimado_dia] DECIMAL(18,2) NULL DEFAULT ((0)),
    [fuente_original] NVARCHAR(50) NOT NULL,
    [sync_run_id] NVARCHAR(50) NULL,
    [fecha_ultima_actualizacion] DATETIME2 NULL DEFAULT (sysutcdatetime()),
    CONSTRAINT [PK_Comercial_Ventas_Dia_Abiertas_v2] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_Ventas_Dia_Abiertas_v2_Backup_FechaOperacion_20260521]
-- ============================================================
CREATE TABLE [dbo].[Comercial_Ventas_Dia_Abiertas_v2_Backup_FechaOperacion_20260521] (
    [id] UNIQUEIDENTIFIER NOT NULL,
    [unidad_negocio_id] NVARCHAR(50) NOT NULL,
    [unidad_negocio_nombre] NVARCHAR(100) NOT NULL,
    [server_id] NVARCHAR(50) NOT NULL,
    [sucursal_id] NVARCHAR(50) NOT NULL,
    [sucursal_nombre] NVARCHAR(100) NULL,
    [sistema_origen] NVARCHAR(20) NOT NULL,
    [snapshot_timestamp] DATETIME2 NOT NULL,
    [fecha_operacion] DATE NOT NULL,
    [ventas_abiertas] DECIMAL(18,2) NULL,
    [tickets_abiertos] INT NULL,
    [pax_abiertos] INT NULL,
    [ventas_cerradas_dia] DECIMAL(18,2) NULL,
    [tickets_cerrados_dia] INT NULL,
    [pax_cerrados_dia] INT NULL,
    [total_estimado_dia] DECIMAL(18,2) NULL,
    [fuente_original] NVARCHAR(50) NOT NULL,
    [sync_run_id] NVARCHAR(50) NULL,
    [fecha_ultima_actualizacion] DATETIME2 NULL
);
GO

-- ============================================================
-- TABLA: [dbo].[Comercial_Ventas_Dia_Abiertas_v2_backup_migracion_codigos_20260513_0558]
-- ============================================================
CREATE TABLE [dbo].[Comercial_Ventas_Dia_Abiertas_v2_backup_migracion_codigos_20260513_0558] (
    [id] UNIQUEIDENTIFIER NOT NULL,
    [unidad_negocio_id] NVARCHAR(50) NOT NULL,
    [unidad_negocio_nombre] NVARCHAR(100) NOT NULL,
    [server_id] NVARCHAR(50) NOT NULL,
    [sucursal_id] NVARCHAR(50) NOT NULL,
    [sucursal_nombre] NVARCHAR(100) NULL,
    [sistema_origen] NVARCHAR(20) NOT NULL,
    [snapshot_timestamp] DATETIME2 NOT NULL,
    [fecha_operacion] DATE NOT NULL,
    [ventas_abiertas] DECIMAL(18,2) NULL,
    [tickets_abiertos] INT NULL,
    [pax_abiertos] INT NULL,
    [ventas_cerradas_dia] DECIMAL(18,2) NULL,
    [tickets_cerrados_dia] INT NULL,
    [pax_cerrados_dia] INT NULL,
    [total_estimado_dia] DECIMAL(18,2) NULL,
    [fuente_original] NVARCHAR(50) NOT NULL,
    [sync_run_id] NVARCHAR(50) NULL,
    [fecha_ultima_actualizacion] DATETIME2 NULL,
    [fecha_backup] DATETIME NOT NULL,
    [fase_migracion] VARCHAR(25) NOT NULL,
    [criterio_backup] NVARCHAR(50) NOT NULL
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras]
-- ============================================================
CREATE TABLE [dbo].[Compras] (
    [CompraID] BIGINT NOT NULL,
    [Serie] VARCHAR(10) NULL,
    [FolioCompra] VARCHAR(30) NOT NULL,
    [PedidoCompraID] BIGINT NULL,
    [OrdenCompraID] BIGINT NULL,
    [EmpresaID] INT NULL,
    [SucursalID] INT NOT NULL,
    [AlmacenID] INT NULL,
    [TipoRegistroCompra] VARCHAR(20) NOT NULL DEFAULT ('DIRECTA'),
    [FechaCompra] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaRecepcion] DATETIME2 NULL,
    [FechaFactura] DATE NULL,
    [FechaVencimiento] DATE NULL,
    [ProveedorID] INT NOT NULL,
    [CompradorUsuarioID] INT NULL,
    [RecibioUsuarioID] INT NULL,
    [CondicionPagoID] SMALLINT NULL,
    [FormaPagoID] SMALLINT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [TipoCambio] DECIMAL(18,6) NOT NULL DEFAULT ((1)),
    [NumeroFactura] VARCHAR(50) NULL,
    [UUIDFactura] VARCHAR(50) NULL,
    [ReferenciaProveedor] VARCHAR(100) NULL,
    [RequiereAutorizacion] BIT NOT NULL DEFAULT ((0)),
    [AutorizacionID] BIGINT NULL,
    [EstatusCompraID] TINYINT NOT NULL DEFAULT ((1)),
    [EsEntradaInventario] BIT NOT NULL DEFAULT ((1)),
    [GeneraCxP] BIT NOT NULL DEFAULT ((1)),
    [Subtotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [DescuentoTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ImpuestoTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Total] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Observaciones] VARCHAR(1000) NULL,
    [ReferenciaExterna] VARCHAR(100) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedAt] DATETIME2 NULL,
    [ModifiedBy] VARCHAR(100) NULL,
    [RowVer] TIMESTAMP NOT NULL,
    CONSTRAINT [PK_Compras] PRIMARY KEY ([CompraID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_ConciliacionSAT]
-- ============================================================
CREATE TABLE [dbo].[Compras_ConciliacionSAT] (
    [ConciliacionSATID] BIGINT NOT NULL,
    [DocumentoFiscalID] BIGINT NOT NULL,
    [CompraID] BIGINT NULL,
    [RecepcionCompraID] BIGINT NULL,
    [EstatusConciliacionSATID] TINYINT NOT NULL DEFAULT ((1)),
    [FechaConciliacion] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [UsuarioID] INT NULL,
    [RFCEmisorCoincide] BIT NOT NULL DEFAULT ((0)),
    [RFCReceptorCoincide] BIT NOT NULL DEFAULT ((0)),
    [FechaCoincide] BIT NOT NULL DEFAULT ((0)),
    [MonedaCoincide] BIT NOT NULL DEFAULT ((0)),
    [TotalCoincide] BIT NOT NULL DEFAULT ((0)),
    [UUIDDuplicado] BIT NOT NULL DEFAULT ((0)),
    [XMLValido] BIT NOT NULL DEFAULT ((1)),
    [PDFEncontrado] BIT NOT NULL DEFAULT ((0)),
    [DiferenciaSubtotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [DiferenciaImpuesto] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [DiferenciaTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Observaciones] VARCHAR(2000) NULL,
    [RevisadoManual] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Compras_ConciliacionSAT] PRIMARY KEY ([ConciliacionSATID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_ConciliacionSATDetalle]
-- ============================================================
CREATE TABLE [dbo].[Compras_ConciliacionSATDetalle] (
    [ConciliacionSATDetalleID] BIGINT NOT NULL,
    [ConciliacionSATID] BIGINT NOT NULL,
    [RecepcionDetalleID] BIGINT NULL,
    [CompraDetalleID] BIGINT NULL,
    [DocumentoFiscalDetalleID] BIGINT NOT NULL,
    [ProductoID] INT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [CantidadSistema] DECIMAL(18,6) NOT NULL DEFAULT ((0)),
    [CantidadXML] DECIMAL(18,6) NOT NULL DEFAULT ((0)),
    [DiferenciaCantidad] DECIMAL(19,6) NULL,
    [CostoSistema] DECIMAL(18,6) NOT NULL DEFAULT ((0)),
    [CostoXML] DECIMAL(18,6) NOT NULL DEFAULT ((0)),
    [DiferenciaCosto] DECIMAL(19,6) NULL,
    [ImporteSistema] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ImporteXML] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [DiferenciaImporte] DECIMAL(19,2) NULL,
    [Coincide] BIT NOT NULL DEFAULT ((0)),
    [Observaciones] VARCHAR(1000) NULL,
    CONSTRAINT [PK_Compras_ConciliacionSATDetalle] PRIMARY KEY ([ConciliacionSATDetalleID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_ConciliacionSATEstatus]
-- ============================================================
CREATE TABLE [dbo].[Compras_ConciliacionSATEstatus] (
    [EstatusConciliacionSATID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(40) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Compras_ConciliacionSATEstatus] PRIMARY KEY ([EstatusConciliacionSATID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_Detalle]
-- ============================================================
CREATE TABLE [dbo].[Compras_Detalle] (
    [DetalleCompraID] BIGINT NOT NULL,
    [CompraID] BIGINT NOT NULL,
    [OrdenDetalleCompraID] BIGINT NULL,
    [PedidoDetalleCompraID] BIGINT NULL,
    [Renglon] INT NOT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [Cantidad] DECIMAL(18,6) NOT NULL,
    [CantidadDevuelta] DECIMAL(18,6) NOT NULL DEFAULT ((0)),
    [CantidadNeta] DECIMAL(19,6) NULL,
    [PrecioUnitario] DECIMAL(18,2) NOT NULL,
    [DescuentoPorcentaje] DECIMAL(9,4) NOT NULL DEFAULT ((0)),
    [DescuentoImporte] NUMERIC(38,6) NULL,
    [TasaImpuesto] DECIMAL(9,4) NOT NULL DEFAULT ((0)),
    [SubtotalLinea] NUMERIC(38,6) NULL,
    [ImpuestoImporte] NUMERIC(38,6) NULL,
    [TotalLinea] NUMERIC(38,6) NULL,
    [Lote] VARCHAR(50) NULL,
    [FechaCaducidad] DATE NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    [RowVer] TIMESTAMP NOT NULL,
    CONSTRAINT [PK_Compras_Detalle] PRIMARY KEY ([DetalleCompraID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_DocumentosFiscales]
-- ============================================================
CREATE TABLE [dbo].[Compras_DocumentosFiscales] (
    [DocumentoFiscalID] BIGINT NOT NULL,
    [SucursalFiscalID] INT NOT NULL,
    [SucursalID] INT NOT NULL,
    [ProveedorID] INT NULL,
    [CompraID] BIGINT NULL,
    [RecepcionCompraID] BIGINT NULL,
    [EstatusDocumentoFiscalID] TINYINT NOT NULL DEFAULT ((1)),
    [UUID] VARCHAR(36) NOT NULL,
    [TipoComprobante] VARCHAR(5) NULL,
    [Serie] VARCHAR(25) NULL,
    [Folio] VARCHAR(40) NULL,
    [FechaEmision] DATETIME2 NULL,
    [RFCEmisor] VARCHAR(13) NOT NULL,
    [NombreEmisor] VARCHAR(200) NULL,
    [RFCReceptor] VARCHAR(13) NOT NULL,
    [NombreReceptor] VARCHAR(200) NULL,
    [Moneda] VARCHAR(10) NULL,
    [TipoCambio] DECIMAL(18,6) NOT NULL DEFAULT ((1)),
    [Subtotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Descuento] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ImpuestoTrasladado] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ImpuestoRetenido] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Total] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [MetodoPago] VARCHAR(10) NULL,
    [FormaPago] VARCHAR(10) NULL,
    [UsoCFDI] VARCHAR(10) NULL,
    [VersionCFDI] VARCHAR(10) NULL,
    [EstatusSAT] VARCHAR(30) NULL,
    [FechaConsultaSAT] DATETIME2 NULL,
    [RutaXML] VARCHAR(500) NULL,
    [RutaPDF] VARCHAR(500) NULL,
    [NombreArchivoXML] VARCHAR(255) NULL,
    [NombreArchivoPDF] VARCHAR(255) NULL,
    [HashXML] VARCHAR(128) NULL,
    [HashPDF] VARCHAR(128) NULL,
    [FechaDescarga] DATETIME2 NULL,
    [OrigenDocumento] VARCHAR(20) NOT NULL DEFAULT ('SAT'),
    [Observaciones] VARCHAR(1000) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [ModifiedAt] DATETIME2 NULL,
    CONSTRAINT [PK_Compras_DocumentosFiscales] PRIMARY KEY ([DocumentoFiscalID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_DocumentosFiscalesDetalle]
-- ============================================================
CREATE TABLE [dbo].[Compras_DocumentosFiscalesDetalle] (
    [DocumentoFiscalDetalleID] BIGINT NOT NULL,
    [DocumentoFiscalID] BIGINT NOT NULL,
    [Renglon] INT NOT NULL,
    [ClaveProdServ] VARCHAR(20) NULL,
    [NoIdentificacion] VARCHAR(100) NULL,
    [DescripcionConcepto] VARCHAR(500) NULL,
    [UnidadSAT] VARCHAR(20) NULL,
    [UnidadInterna] VARCHAR(30) NULL,
    [Cantidad] DECIMAL(18,6) NOT NULL DEFAULT ((0)),
    [ValorUnitario] DECIMAL(18,6) NOT NULL DEFAULT ((0)),
    [Importe] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Descuento] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ProductoID] INT NULL,
    [PresentacionProductoID] BIGINT NULL,
    CONSTRAINT [PK_Compras_DocumentosFiscalesDetalle] PRIMARY KEY ([DocumentoFiscalDetalleID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_DocumentosFiscalesEstatus]
-- ============================================================
CREATE TABLE [dbo].[Compras_DocumentosFiscalesEstatus] (
    [EstatusDocumentoFiscalID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(40) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Compras_DocumentosFiscalesEstatus] PRIMARY KEY ([EstatusDocumentoFiscalID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_Estatus]
-- ============================================================
CREATE TABLE [dbo].[Compras_Estatus] (
    [EstatusCompraID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Compras_Estatus] PRIMARY KEY ([EstatusCompraID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_Eventos_Pendientes]
-- ============================================================
CREATE TABLE [dbo].[Compras_Eventos_Pendientes] (
    [EventoID] INT NOT NULL,
    [EventoTipo] NVARCHAR(50) NOT NULL,
    [ServerID] NVARCHAR(36) NOT NULL,
    [UnidadNegocioID] NVARCHAR(36) NULL,
    [Folio] NVARCHAR(50) NULL,
    [Fecha] DATETIME NULL,
    [DatosJSON] NVARCHAR(MAX) NULL,
    [Procesado] BIT NULL DEFAULT ((0)),
    [ProcesadoAt] DATETIME NULL,
    [InformeGenerado] BIT NULL DEFAULT ((0)),
    [InformeID] NVARCHAR(36) NULL,
    [ErrorMessage] NVARCHAR(500) NULL,
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Compras_Eventos_Pendientes] PRIMARY KEY ([EventoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_Informes_Config]
-- ============================================================
CREATE TABLE [dbo].[Compras_Informes_Config] (
    [ConfigID] INT NOT NULL,
    [EventoTipo] NVARCHAR(50) NOT NULL,
    [InformeTipo] NVARCHAR(100) NOT NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [WebhookURL] NVARCHAR(500) NULL,
    [EmailDestinatarios] NVARCHAR(500) NULL,
    [ConfigJSON] NVARCHAR(MAX) NULL,
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    [UpdatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Compras_Informes_Config] PRIMARY KEY ([ConfigID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_Inventarios_Fisicos_Sync]
-- ============================================================
CREATE TABLE [dbo].[Compras_Inventarios_Fisicos_Sync] (
    [id] INT NOT NULL,
    [unidad_negocio_id] VARCHAR(50) NOT NULL,
    [unidad_negocio_codigo] VARCHAR(20) NULL,
    [server_id] VARCHAR(50) NOT NULL,
    [system_type] VARCHAR(50) NULL,
    [folio] VARCHAR(50) NOT NULL,
    [fecha] DATETIME NULL,
    [almacen] VARCHAR(100) NULL,
    [almacen_id] VARCHAR(50) NULL,
    [sucursal] VARCHAR(100) NULL,
    [sucursal_id] VARCHAR(50) NULL,
    [tipo] VARCHAR(50) NULL,
    [estatus] VARCHAR(50) NULL,
    [total_productos] INT NULL DEFAULT ((0)),
    [sync_source] VARCHAR(20) NULL DEFAULT ('LIVE'),
    [sync_timestamp] DATETIME NULL DEFAULT (getdate()),
    [sync_status] VARCHAR(20) NULL DEFAULT ('ACTIVE'),
    CONSTRAINT [PK_Compras_Inventarios_Fisicos_Sync] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_KPIs_Historico]
-- ============================================================
CREATE TABLE [dbo].[Compras_KPIs_Historico] (
    [id] INT NOT NULL,
    [run_id] NVARCHAR(50) NOT NULL,
    [server_id] NVARCHAR(50) NOT NULL,
    [sucursal_id] NVARCHAR(50) NOT NULL,
    [system_type_normalized] NVARCHAR(50) NOT NULL,
    [fecha] DATE NOT NULL,
    [kpi_tipo] NVARCHAR(50) NOT NULL,
    [inv_conteos_count] INT NULL DEFAULT ((0)),
    [inv_productos_count] INT NULL DEFAULT ((0)),
    [inv_almacenes] NVARCHAR(500) NULL DEFAULT (''),
    [ped_pedidos_count] INT NULL DEFAULT ((0)),
    [ped_total_monto] DECIMAL(18,4) NULL DEFAULT ((0)),
    [ped_productos_count] INT NULL DEFAULT ((0)),
    [oc_ordenes_count] INT NULL DEFAULT ((0)),
    [oc_total_monto] DECIMAL(18,4) NULL DEFAULT ((0)),
    [oc_proveedores_count] INT NULL DEFAULT ((0)),
    [ec_entradas_count] INT NULL DEFAULT ((0)),
    [ec_total_monto] DECIMAL(18,4) NULL DEFAULT ((0)),
    [ec_productos_count] INT NULL DEFAULT ((0)),
    [empresa_id] NVARCHAR(50) NULL DEFAULT (''),
    [empresa_nombre] NVARCHAR(200) NULL DEFAULT (''),
    [created_at] DATETIME NULL DEFAULT (getdate()),
    [updated_at] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Compras_KPIs_Historico] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_Ordenes]
-- ============================================================
CREATE TABLE [dbo].[Compras_Ordenes] (
    [OrdenCompraID] BIGINT NOT NULL,
    [Serie] VARCHAR(10) NULL,
    [FolioOrden] VARCHAR(30) NOT NULL,
    [PedidoCompraID] BIGINT NULL,
    [EmpresaID] INT NULL,
    [SucursalID] INT NOT NULL,
    [AlmacenID] INT NULL,
    [FechaOrden] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaEntregaPrometida] DATE NULL,
    [ProveedorID] INT NOT NULL,
    [CompradorUsuarioID] INT NOT NULL,
    [SolicitanteUsuarioID] INT NULL,
    [CondicionPagoID] SMALLINT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [TipoCambio] DECIMAL(18,6) NOT NULL DEFAULT ((1)),
    [RequiereAutorizacion] BIT NOT NULL DEFAULT ((0)),
    [AutorizacionID] BIGINT NULL,
    [EstatusOrdenCompraID] TINYINT NOT NULL DEFAULT ((1)),
    [AtencionA] VARCHAR(150) NULL,
    [DireccionEntrega] VARCHAR(250) NULL,
    [ReferenciaProveedor] VARCHAR(100) NULL,
    [Observaciones] VARCHAR(1000) NULL,
    [TerminosCondiciones] VARCHAR(2000) NULL,
    [ReferenciaExterna] VARCHAR(100) NULL,
    [Subtotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [DescuentoTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ImpuestoTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Total] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedAt] DATETIME2 NULL,
    [ModifiedBy] VARCHAR(100) NULL,
    [RowVer] TIMESTAMP NOT NULL,
    CONSTRAINT [PK_Compras_Ordenes] PRIMARY KEY ([OrdenCompraID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_OrdenesDetalle]
-- ============================================================
CREATE TABLE [dbo].[Compras_OrdenesDetalle] (
    [DetalleOrdenCompraID] BIGINT NOT NULL,
    [OrdenCompraID] BIGINT NOT NULL,
    [PedidoDetalleCompraID] BIGINT NULL,
    [Renglon] INT NOT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [Cantidad] DECIMAL(18,6) NOT NULL,
    [CantidadRecibida] DECIMAL(18,6) NOT NULL DEFAULT ((0)),
    [CantidadCancelada] DECIMAL(18,6) NOT NULL DEFAULT ((0)),
    [CantidadPendiente] DECIMAL(20,6) NULL,
    [PrecioUnitario] DECIMAL(18,2) NOT NULL,
    [DescuentoPorcentaje] DECIMAL(9,4) NOT NULL DEFAULT ((0)),
    [DescuentoImporte] NUMERIC(38,6) NULL,
    [TasaImpuesto] DECIMAL(9,4) NOT NULL DEFAULT ((0)),
    [SubtotalLinea] NUMERIC(38,6) NULL,
    [ImpuestoImporte] NUMERIC(38,6) NULL,
    [TotalLinea] NUMERIC(38,6) NULL,
    [FechaPromesaLinea] DATE NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    [RowVer] TIMESTAMP NOT NULL,
    CONSTRAINT [PK_Compras_OrdenesDetalle] PRIMARY KEY ([DetalleOrdenCompraID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_OrdenesEstatus]
-- ============================================================
CREATE TABLE [dbo].[Compras_OrdenesEstatus] (
    [EstatusOrdenCompraID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Compras_OrdenesEstatus] PRIMARY KEY ([EstatusOrdenCompraID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_Parametros_Sucursal]
-- ============================================================
CREATE TABLE [dbo].[Compras_Parametros_Sucursal] (
    [ParametroID] INT NOT NULL,
    [ServerID] VARCHAR(100) NOT NULL,
    [SucursalID] VARCHAR(50) NOT NULL,
    [DiasInventario] INT NOT NULL DEFAULT ((10)),
    [ExcluirDomingos] BIT NOT NULL DEFAULT ((1)),
    [DiasInhabiles] NVARCHAR(MAX) NULL,
    [DiasTransitoProveedor] INT NOT NULL DEFAULT ((2)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreadoPor] VARCHAR(100) NULL,
    [ModificadoPor] VARCHAR(100) NULL,
    [FechaCreacion] DATETIME NOT NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME NOT NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Compras_Parametros_Sucursal] PRIMARY KEY ([ParametroID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_Pedidos]
-- ============================================================
CREATE TABLE [dbo].[Compras_Pedidos] (
    [PedidoCompraID] BIGINT NOT NULL,
    [Serie] VARCHAR(10) NULL,
    [FolioPedido] VARCHAR(30) NOT NULL,
    [EmpresaID] INT NULL,
    [SucursalID] INT NOT NULL,
    [AlmacenID] INT NULL,
    [FechaPedido] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaRequerida] DATE NULL,
    [SolicitanteUsuarioID] INT NOT NULL,
    [CompradorUsuarioID] INT NULL,
    [ProveedorSugeridoID] INT NULL,
    [MonedaID] SMALLINT NULL,
    [TipoCambio] DECIMAL(18,6) NOT NULL DEFAULT ((1)),
    [Prioridad] VARCHAR(15) NOT NULL DEFAULT ('MEDIA'),
    [CentroCosto] VARCHAR(50) NULL,
    [Proyecto] VARCHAR(100) NULL,
    [MotivoCompra] VARCHAR(1000) NOT NULL,
    [RequiereAutorizacion] BIT NOT NULL DEFAULT ((0)),
    [AutorizacionID] BIGINT NULL,
    [EstatusPedidoCompraID] TINYINT NOT NULL DEFAULT ((1)),
    [Subtotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [DescuentoTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ImpuestoTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Total] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Observaciones] VARCHAR(1000) NULL,
    [ReferenciaExterna] VARCHAR(100) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedAt] DATETIME2 NULL,
    [ModifiedBy] VARCHAR(100) NULL,
    [RowVer] TIMESTAMP NOT NULL,
    CONSTRAINT [PK_Compras_Pedidos] PRIMARY KEY ([PedidoCompraID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_PedidosDetalle]
-- ============================================================
CREATE TABLE [dbo].[Compras_PedidosDetalle] (
    [DetallePedidoCompraID] BIGINT NOT NULL,
    [PedidoCompraID] BIGINT NOT NULL,
    [Renglon] INT NOT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [Cantidad] DECIMAL(18,6) NOT NULL,
    [CantidadAtendida] DECIMAL(18,6) NOT NULL DEFAULT ((0)),
    [CantidadCancelada] DECIMAL(18,6) NOT NULL DEFAULT ((0)),
    [CantidadPendiente] DECIMAL(20,6) NULL,
    [PrecioEstimado] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [DescuentoPorcentaje] DECIMAL(9,4) NOT NULL DEFAULT ((0)),
    [DescuentoImporte] NUMERIC(38,6) NULL,
    [TasaImpuesto] DECIMAL(9,4) NOT NULL DEFAULT ((0)),
    [SubtotalLinea] NUMERIC(38,6) NULL,
    [ImpuestoImporte] NUMERIC(38,6) NULL,
    [TotalLinea] NUMERIC(38,6) NULL,
    [FechaNecesaria] DATE NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    [RowVer] TIMESTAMP NOT NULL,
    CONSTRAINT [PK_Compras_PedidosDetalle] PRIMARY KEY ([DetallePedidoCompraID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_PedidosEstatus]
-- ============================================================
CREATE TABLE [dbo].[Compras_PedidosEstatus] (
    [EstatusPedidoCompraID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Compras_PedidosEstatus] PRIMARY KEY ([EstatusPedidoCompraID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_Recepciones]
-- ============================================================
CREATE TABLE [dbo].[Compras_Recepciones] (
    [RecepcionCompraID] BIGINT NOT NULL,
    [FolioRecepcion] VARCHAR(30) NOT NULL,
    [CompraID] BIGINT NULL,
    [OrdenCompraID] BIGINT NULL,
    [EmpresaID] INT NULL,
    [SucursalID] INT NOT NULL,
    [AlmacenID] INT NOT NULL,
    [ProveedorID] INT NOT NULL,
    [FechaRecepcion] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaDocumentoProveedor] DATE NULL,
    [DocumentoProveedor] VARCHAR(50) NULL,
    [EstatusRecepcionID] TINYINT NOT NULL DEFAULT ((1)),
    [RecibioUsuarioID] INT NULL,
    [RevisoUsuarioID] INT NULL,
    [MovimientoInventarioID] BIGINT NULL,
    [Subtotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ImpuestoTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Total] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Observaciones] VARCHAR(1000) NULL,
    [TieneIncidencias] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [ModifiedAt] DATETIME2 NULL,
    CONSTRAINT [PK_Compras_Recepciones] PRIMARY KEY ([RecepcionCompraID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_RecepcionesDetalle]
-- ============================================================
CREATE TABLE [dbo].[Compras_RecepcionesDetalle] (
    [RecepcionDetalleID] BIGINT NOT NULL,
    [RecepcionCompraID] BIGINT NOT NULL,
    [CompraDetalleID] BIGINT NULL,
    [OrdenDetalleID] BIGINT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [Renglon] INT NOT NULL,
    [CantidadEsperada] DECIMAL(18,6) NOT NULL DEFAULT ((0)),
    [CantidadRecibida] DECIMAL(18,6) NOT NULL,
    [CantidadRechazada] DECIMAL(18,6) NOT NULL DEFAULT ((0)),
    [CantidadAceptada] DECIMAL(19,6) NULL,
    [CostoUnitario] DECIMAL(18,6) NOT NULL DEFAULT ((0)),
    [SubtotalLinea] DECIMAL(38,12) NULL,
    [Lote] VARCHAR(50) NULL,
    [FechaCaducidad] DATE NULL,
    [TieneIncidencia] BIT NOT NULL DEFAULT ((0)),
    [Observaciones] VARCHAR(500) NULL,
    [MovimientoDetalleID] BIGINT NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Compras_RecepcionesDetalle] PRIMARY KEY ([RecepcionDetalleID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_RecepcionesEstatus]
-- ============================================================
CREATE TABLE [dbo].[Compras_RecepcionesEstatus] (
    [EstatusRecepcionID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Compras_RecepcionesEstatus] PRIMARY KEY ([EstatusRecepcionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_Requisiciones_Sync]
-- ============================================================
CREATE TABLE [dbo].[Compras_Requisiciones_Sync] (
    [id] INT NOT NULL,
    [unidad_negocio_id] VARCHAR(50) NOT NULL,
    [unidad_negocio_codigo] VARCHAR(20) NULL,
    [server_id] VARCHAR(50) NOT NULL,
    [system_type] VARCHAR(50) NULL,
    [tipo] VARCHAR(20) NULL,
    [folio] VARCHAR(50) NOT NULL,
    [fecha] DATETIME NULL,
    [fecha_entrega] DATETIME NULL,
    [proveedor] VARCHAR(200) NULL,
    [proveedor_id] VARCHAR(50) NULL,
    [sucursal] VARCHAR(100) NULL,
    [sucursal_id] VARCHAR(50) NULL,
    [total_productos] INT NULL DEFAULT ((0)),
    [importe] DECIMAL(18,2) NULL DEFAULT ((0)),
    [estatus] VARCHAR(50) NULL,
    [sync_source] VARCHAR(20) NULL DEFAULT ('LIVE'),
    [sync_timestamp] DATETIME NULL DEFAULT (getdate()),
    [sync_status] VARCHAR(20) NULL DEFAULT ('ACTIVE'),
    CONSTRAINT [PK_Compras_Requisiciones_Sync] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_Sync_Checkpoint]
-- ============================================================
CREATE TABLE [dbo].[Compras_Sync_Checkpoint] (
    [CheckpointID] INT NOT NULL,
    [ServerID] NVARCHAR(36) NOT NULL,
    [ServerName] NVARCHAR(100) NULL,
    [SyncType] NVARCHAR(50) NOT NULL,
    [LastFolio] NVARCHAR(50) NULL,
    [LastFecha] DATETIME NULL,
    [LastSyncAt] DATETIME NULL,
    [RecordsFoundLastSync] INT NULL DEFAULT ((0)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    [UpdatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Compras_Sync_Checkpoint] PRIMARY KEY ([CheckpointID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Compras_Sync_Log]
-- ============================================================
CREATE TABLE [dbo].[Compras_Sync_Log] (
    [id] INT NOT NULL,
    [unidad_negocio_id] VARCHAR(50) NULL,
    [server_id] VARCHAR(50) NULL,
    [sync_type] VARCHAR(50) NULL,
    [sync_start] DATETIME NULL,
    [sync_end] DATETIME NULL,
    [records_synced] INT NULL DEFAULT ((0)),
    [status] VARCHAR(20) NULL,
    [error_message] TEXT(2147483647) NULL,
    [created_at] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Compras_Sync_Log] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Config_Asignaciones]
-- ============================================================
CREATE TABLE [dbo].[Config_Asignaciones] (
    [ID] INT NOT NULL,
    [ConfigID] VARCHAR(50) NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [AlmacenID] VARCHAR(50) NULL DEFAULT (''),
    [UsuarioResponsableID] VARCHAR(50) NOT NULL,
    [Prioridad] INT NULL DEFAULT ((1)),
    [Activa] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NULL DEFAULT (getutcdate()),
    [FechaActualizacion] DATETIME2 NULL,
    [UnidadNegocioID] VARCHAR(50) NULL,
    [UnidadNegocioNombre] VARCHAR(200) NULL,
    [AlmacenNombre] VARCHAR(200) NULL,
    [UsuarioResponsableNombre] VARCHAR(200) NULL,
    [UsuarioResponsableEmail] VARCHAR(200) NULL,
    [UsuarioCreacion] VARCHAR(100) NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacion] VARCHAR(100) NULL,
    CONSTRAINT [PK_Config_Asignaciones] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Config_Horarios]
-- ============================================================
CREATE TABLE [dbo].[Config_Horarios] (
    [Id] INT NOT NULL,
    [TenantID] INT NOT NULL,
    [NombrePeriodo] NVARCHAR(50) NULL,
    [HoraInicio] TIME NULL,
    [HoraFin] TIME NULL,
    CONSTRAINT [PK_Config_Horarios] PRIMARY KEY ([Id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Configuracion_Operativa]
-- ============================================================
CREATE TABLE [dbo].[Configuracion_Operativa] (
    [ID] INT NOT NULL,
    [Clave] VARCHAR(100) NOT NULL,
    [Valor] VARCHAR(500) NULL,
    [Tipo] VARCHAR(20) NULL DEFAULT ('string'),
    [Descripcion] VARCHAR(500) NULL,
    [FechaActualizacion] DATETIME2 NULL DEFAULT (getutcdate()),
    CONSTRAINT [PK_Configuracion_Operativa] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ConsultasSQL_Catalogo]
-- ============================================================
CREATE TABLE [dbo].[ConsultasSQL_Catalogo] (
    [ConsultaID] INT NOT NULL,
    [PublicUUID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [CodigoConsulta] VARCHAR(50) NOT NULL,
    [NombreConsulta] NVARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Modulo] VARCHAR(50) NOT NULL,
    [TipoConsulta] VARCHAR(30) NOT NULL DEFAULT ('CONSULTA'),
    [SistemaTipoID] INT NOT NULL,
    [ConsultaSQL] NVARCHAR(MAX) NOT NULL,
    [EsSistema] BIT NOT NULL DEFAULT ((0)),
    [EsPersonalizada] BIT NOT NULL DEFAULT ((0)),
    [EsSincronizable] BIT NOT NULL DEFAULT ((0)),
    [PermiteEjecucionManual] BIT NOT NULL DEFAULT ((1)),
    [SoloLectura] BIT NOT NULL DEFAULT ((1)),
    [RequiereAutorizacion] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [Version] INT NOT NULL DEFAULT ((1)),
    [ConfigOrigen] VARCHAR(50) NOT NULL DEFAULT ('LEGACY_PYTHON'),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [UsuarioCreacionID] NVARCHAR(100) NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacionID] NVARCHAR(100) NULL,
    CONSTRAINT [PK_ConsultasSQL_Catalogo] PRIMARY KEY ([ConsultaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ConsultasSQL_EjecucionesLog]
-- ============================================================
CREATE TABLE [dbo].[ConsultasSQL_EjecucionesLog] (
    [EjecucionID] BIGINT IDENTITY(1,1) NOT NULL,
    [ConsultaID] INT NOT NULL,
    [ServidorID] UNIQUEIDENTIFIER NULL,
    [UsuarioID] NVARCHAR(100) NOT NULL,
    [FechaEjecucion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [ParametrosJSON] NVARCHAR(MAX) NULL,
    [ConsultaSQLEjecutada] NVARCHAR(MAX) NULL,
    [Estado] VARCHAR(20) NOT NULL DEFAULT ('SUCCESS'),
    [DuracionMs] INT NULL,
    [RegistrosDevueltos] INT NULL,
    [ErrorMensaje] NVARCHAR(MAX) NULL,
    [IpOrigen] VARCHAR(50) NULL,
    [UserAgent] NVARCHAR(500) NULL,
    CONSTRAINT [PK_ConsultasSQL_EjecucionesLog] PRIMARY KEY ([EjecucionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ConsultasSQL_Parametros]
-- ============================================================
CREATE TABLE [dbo].[ConsultasSQL_Parametros] (
    [ParametroID] INT NOT NULL,
    [ConsultaID] INT NOT NULL,
    [NombreParametro] VARCHAR(50) NOT NULL,
    [NombreMostrar] NVARCHAR(100) NULL,
    [TipoDato] VARCHAR(20) NOT NULL DEFAULT ('STRING'),
    [Requerido] BIT NOT NULL DEFAULT ((1)),
    [ValorDefault] NVARCHAR(200) NULL,
    [RegexValidacion] NVARCHAR(500) NULL,
    [ValorMinimo] NVARCHAR(100) NULL,
    [ValorMaximo] NVARCHAR(100) NULL,
    [ListaValoresJSON] NVARCHAR(MAX) NULL,
    [OrdenMostrar] INT NOT NULL DEFAULT ((0)),
    [ComponenteUI] VARCHAR(30) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_ConsultasSQL_Parametros] PRIMARY KEY ([ParametroID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ConsultasSQL_Permisos]
-- ============================================================
CREATE TABLE [dbo].[ConsultasSQL_Permisos] (
    [PermisoID] INT NOT NULL,
    [ConsultaID] INT NOT NULL,
    [RolID] NVARCHAR(100) NULL,
    [UsuarioID] NVARCHAR(100) NULL,
    [PuedeVer] BIT NOT NULL DEFAULT ((1)),
    [PuedeEjecutar] BIT NOT NULL DEFAULT ((0)),
    [PuedeEditar] BIT NOT NULL DEFAULT ((0)),
    [PuedeAutorizar] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [UsuarioCreacionID] NVARCHAR(100) NULL,
    CONSTRAINT [PK_ConsultasSQL_Permisos] PRIMARY KEY ([PermisoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ConsultasSQL_Servidores]
-- ============================================================
CREATE TABLE [dbo].[ConsultasSQL_Servidores] (
    [ConsultaServidorID] INT NOT NULL,
    [ConsultaID] INT NOT NULL,
    [ServidorID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] INT NULL,
    [SucursalID] NVARCHAR(50) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [Prioridad] INT NOT NULL DEFAULT ((0)),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [UsuarioCreacionID] NVARCHAR(100) NULL,
    CONSTRAINT [PK_ConsultasSQL_Servidores] PRIMARY KEY ([ConsultaServidorID])
);
GO

-- ============================================================
-- TABLA: [dbo].[ConsultasSQL_Versiones]
-- ============================================================
CREATE TABLE [dbo].[ConsultasSQL_Versiones] (
    [VersionID] INT NOT NULL,
    [ConsultaID] INT NOT NULL,
    [Version] INT NOT NULL,
    [ConsultaSQL] NVARCHAR(MAX) NOT NULL,
    [ParametrosJSON] NVARCHAR(MAX) NULL,
    [MotivoCambio] NVARCHAR(500) NULL,
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [UsuarioCreacionID] NVARCHAR(100) NULL,
    CONSTRAINT [PK_ConsultasSQL_Versiones] PRIMARY KEY ([VersionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Actividades]
-- ============================================================
CREATE TABLE [dbo].[CRM_Actividades] (
    [ActividadID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [TipoActividadID] INT NOT NULL,
    [EntidadTipo] NVARCHAR(20) NOT NULL,
    [EntidadID] UNIQUEIDENTIFIER NOT NULL,
    [Titulo] NVARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [Prioridad] INT NOT NULL DEFAULT ((2)),
    [FechaProgramada] DATETIME2 NOT NULL,
    [FechaFin] DATETIME2 NULL,
    [Duracion] INT NULL,
    [TodoElDia] BIT NOT NULL DEFAULT ((0)),
    [FechaRealizacion] DATETIME2 NULL,
    [ResultadoID] INT NULL,
    [Notas] NVARCHAR(MAX) NULL,
    [AsignadoAUserID] UNIQUEIDENTIFIER NOT NULL,
    [CreadoPorUserID] UNIQUEIDENTIFIER NOT NULL,
    [EstatusActividadID] INT NOT NULL DEFAULT ((1)),
    [TieneRecordatorio] BIT NOT NULL DEFAULT ((0)),
    [MinutosAntes] INT NULL,
    [RecordatorioEnviado] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (getutcdate()),
    [UpdatedAt] DATETIME2 NULL,
    [NotificacionEnviada] BIT NULL DEFAULT ((0)),
    [FechaNotificacion] DATETIME NULL,
    CONSTRAINT [PK_CRM_Actividades] PRIMARY KEY ([ActividadID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_ActividadesHistorial]
-- ============================================================
CREATE TABLE [dbo].[CRM_ActividadesHistorial] (
    [HistorialActividadID] INT NOT NULL,
    [ActividadID] UNIQUEIDENTIFIER NOT NULL,
    [EstatusAnteriorID] INT NULL,
    [EstatusNuevoID] INT NOT NULL,
    [UsuarioModificadorID] UNIQUEIDENTIFIER NOT NULL,
    [FechaCambio] DATETIME2 NULL DEFAULT (getdate()),
    [Comentario] NVARCHAR(500) NULL,
    CONSTRAINT [PK_CRM_ActividadesHistorial] PRIMARY KEY ([HistorialActividadID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Automation_Log]
-- ============================================================
CREATE TABLE [dbo].[CRM_Automation_Log] (
    [LogID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [ReglaID] UNIQUEIDENTIFIER NOT NULL,
    [OportunidadID] UNIQUEIDENTIFIER NULL,
    [TipoTrigger] NVARCHAR(50) NULL,
    [AccionEjecutada] NVARCHAR(100) NULL,
    [Exitoso] BIT NULL DEFAULT ((1)),
    [DetalleJSON] NVARCHAR(MAX) NULL,
    [MensajeError] NVARCHAR(500) NULL,
    [FechaEjecucion] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Automation_Log] PRIMARY KEY ([LogID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Automation_Reglas]
-- ============================================================
CREATE TABLE [dbo].[CRM_Automation_Reglas] (
    [ReglaID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [Nombre] NVARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [PipelineID] INT NULL,
    [TipoTrigger] NVARCHAR(50) NOT NULL,
    [CondicionJSON] NVARCHAR(MAX) NULL,
    [AccionJSON] NVARCHAR(MAX) NOT NULL,
    [Prioridad] INT NULL DEFAULT ((100)),
    [Activa] BIT NULL DEFAULT ((1)),
    [UsuarioCreacionID] UNIQUEIDENTIFIER NULL,
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    [UsuarioModificacionID] UNIQUEIDENTIFIER NULL,
    [FechaModificacion] DATETIME NULL,
    CONSTRAINT [PK_CRM_Automation_Reglas] PRIMARY KEY ([ReglaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Cat_EstatusActividad]
-- ============================================================
CREATE TABLE [dbo].[CRM_Cat_EstatusActividad] (
    [EstatusID] INT NOT NULL,
    [Nombre] NVARCHAR(50) NOT NULL,
    [Color] NVARCHAR(20) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_CRM_Cat_EstatusActividad] PRIMARY KEY ([EstatusID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Cat_EstatusContrato]
-- ============================================================
CREATE TABLE [dbo].[CRM_Cat_EstatusContrato] (
    [EstatusID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [ColorHex] NVARCHAR(7) NULL DEFAULT ('#6B7280'),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Cat_EstatusContrato] PRIMARY KEY ([EstatusID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Cat_EstatusLead]
-- ============================================================
CREATE TABLE [dbo].[CRM_Cat_EstatusLead] (
    [EstatusID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [ColorHex] NVARCHAR(7) NULL DEFAULT ('#6B7280'),
    [EsFinal] BIT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Cat_EstatusLead] PRIMARY KEY ([EstatusID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Cat_EstatusOportunidad]
-- ============================================================
CREATE TABLE [dbo].[CRM_Cat_EstatusOportunidad] (
    [EstatusID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [ColorHex] NVARCHAR(7) NULL DEFAULT ('#6B7280'),
    [EsFinal] BIT NULL DEFAULT ((0)),
    [EsGanada] BIT NULL DEFAULT ((0)),
    [EsPerdida] BIT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Cat_EstatusOportunidad] PRIMARY KEY ([EstatusID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Cat_EstatusPropuesta]
-- ============================================================
CREATE TABLE [dbo].[CRM_Cat_EstatusPropuesta] (
    [EstatusID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [ColorHex] NVARCHAR(7) NULL DEFAULT ('#6B7280'),
    [EsFinal] BIT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Cat_EstatusPropuesta] PRIMARY KEY ([EstatusID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Cat_MotivosGanada]
-- ============================================================
CREATE TABLE [dbo].[CRM_Cat_MotivosGanada] (
    [MotivoID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Cat_MotivosGanada] PRIMARY KEY ([MotivoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Cat_MotivosPerdida]
-- ============================================================
CREATE TABLE [dbo].[CRM_Cat_MotivosPerdida] (
    [MotivoID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Cat_MotivosPerdida] PRIMARY KEY ([MotivoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Cat_OrigenLead]
-- ============================================================
CREATE TABLE [dbo].[CRM_Cat_OrigenLead] (
    [OrigenID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [ColorHex] NVARCHAR(7) NULL DEFAULT ('#6B7280'),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Cat_OrigenLead] PRIMARY KEY ([OrigenID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Cat_Prioridades]
-- ============================================================
CREATE TABLE [dbo].[CRM_Cat_Prioridades] (
    [PrioridadID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [ColorHex] NVARCHAR(7) NULL DEFAULT ('#6B7280'),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Cat_Prioridades] PRIMARY KEY ([PrioridadID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Cat_Sectores]
-- ============================================================
CREATE TABLE [dbo].[CRM_Cat_Sectores] (
    [SectorID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Cat_Sectores] PRIMARY KEY ([SectorID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Cat_TamanosCliente]
-- ============================================================
CREATE TABLE [dbo].[CRM_Cat_TamanosCliente] (
    [TamanoID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [RangoEmpleadosMin] INT NULL,
    [RangoEmpleadosMax] INT NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Cat_TamanosCliente] PRIMARY KEY ([TamanoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Cat_TiposActividad]
-- ============================================================
CREATE TABLE [dbo].[CRM_Cat_TiposActividad] (
    [TipoID] INT NOT NULL,
    [Nombre] NVARCHAR(50) NOT NULL,
    [Icono] NVARCHAR(30) NULL,
    [Color] NVARCHAR(20) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_CRM_Cat_TiposActividad] PRIMARY KEY ([TipoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Cat_TiposPipeline]
-- ============================================================
CREATE TABLE [dbo].[CRM_Cat_TiposPipeline] (
    [TipoID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Cat_TiposPipeline] PRIMARY KEY ([TipoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_ClientesSolicitudesAlta]
-- ============================================================
CREATE TABLE [dbo].[CRM_ClientesSolicitudesAlta] (
    [SolicitudID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [SucursalID] UNIQUEIDENTIFIER NULL,
    [FolioSolicitud] NVARCHAR(20) NOT NULL,
    [OrigenEntidad] NVARCHAR(20) NOT NULL DEFAULT ('CUENTA'),
    [OrigenEntidadID] UNIQUEIDENTIFIER NULL,
    [CuentaID] UNIQUEIDENTIFIER NULL,
    [ClienteIDGenerado] INT NULL,
    [NombreComercial] NVARCHAR(200) NOT NULL,
    [RazonSocial] NVARCHAR(200) NOT NULL,
    [RFC] NVARCHAR(13) NOT NULL,
    [RegimenFiscal] NVARCHAR(100) NULL,
    [UsoCFDI] NVARCHAR(100) NULL,
    [EmailFacturacion] NVARCHAR(150) NULL,
    [TelefonoFacturacion] NVARCHAR(50) NULL,
    [Calle] NVARCHAR(200) NULL,
    [NumeroExterior] NVARCHAR(20) NULL,
    [NumeroInterior] NVARCHAR(20) NULL,
    [Colonia] NVARCHAR(100) NULL,
    [Municipio] NVARCHAR(100) NULL,
    [Ciudad] NVARCHAR(100) NULL,
    [Estado] NVARCHAR(100) NULL,
    [Pais] NVARCHAR(60) NULL DEFAULT ('México'),
    [CodigoPostal] NVARCHAR(10) NULL,
    [ContactoPrincipalNombre] NVARCHAR(200) NULL,
    [ContactoPrincipalEmail] NVARCHAR(150) NULL,
    [ContactoPrincipalTelefono] NVARCHAR(50) NULL,
    [ContactoPrincipalPuesto] NVARCHAR(100) NULL,
    [RequiereCredito] BIT NOT NULL DEFAULT ((0)),
    [LimiteCreditoSolicitado] DECIMAL(18,2) NULL,
    [DiasCreditoSolicitados] INT NULL,
    [CondicionesPagoSolicitadas] NVARCHAR(200) NULL,
    [ObservacionesSolicitante] NVARCHAR(MAX) NULL,
    [EstatusSolicitud] NVARCHAR(20) NOT NULL DEFAULT ('BORRADOR'),
    [SolicitadoPorUserID] UNIQUEIDENTIFIER NOT NULL,
    [RevisadoPorUserID] UNIQUEIDENTIFIER NULL,
    [AutorizadoPorUserID] UNIQUEIDENTIFIER NULL,
    [RechazadoPorUserID] UNIQUEIDENTIFIER NULL,
    [FechaSolicitud] DATETIME2 NULL,
    [FechaEnvio] DATETIME2 NULL,
    [FechaRevision] DATETIME2 NULL,
    [FechaAutorizacion] DATETIME2 NULL,
    [FechaRechazo] DATETIME2 NULL,
    [MotivoRechazo] NVARCHAR(500) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedBy] UNIQUEIDENTIFIER NULL,
    [UpdatedBy] UNIQUEIDENTIFIER NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (getutcdate()),
    [UpdatedAt] DATETIME2 NULL,
    CONSTRAINT [PK_CRM_ClientesSolicitudesAlta] PRIMARY KEY ([SolicitudID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_ClientesSolicitudesAltaHistorial]
-- ============================================================
CREATE TABLE [dbo].[CRM_ClientesSolicitudesAltaHistorial] (
    [HistorialID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [SolicitudID] UNIQUEIDENTIFIER NOT NULL,
    [EstatusAnterior] NVARCHAR(20) NULL,
    [EstatusNuevo] NVARCHAR(20) NOT NULL,
    [Comentario] NVARCHAR(500) NULL,
    [CambiadoPorUserID] UNIQUEIDENTIFIER NOT NULL,
    [FechaCambio] DATETIME2 NOT NULL DEFAULT (getutcdate()),
    CONSTRAINT [PK_CRM_ClientesSolicitudesAltaHistorial] PRIMARY KEY ([HistorialID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Config_PipelineEtapas]
-- ============================================================
CREATE TABLE [dbo].[CRM_Config_PipelineEtapas] (
    [EtapaID] INT NOT NULL,
    [PipelineID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [ProbabilidadDefault] INT NULL DEFAULT ((0)),
    [Orden] INT NOT NULL,
    [ColorHex] NVARCHAR(7) NULL DEFAULT ('#6B7280'),
    [EsEtapaInicial] BIT NULL DEFAULT ((0)),
    [EsEtapaCierre] BIT NULL DEFAULT ((0)),
    [EsCierreGanado] BIT NULL DEFAULT ((0)),
    [EsCierrePerdido] BIT NULL DEFAULT ((0)),
    [DiasMaxSLA] INT NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    [UpdatedAt] DATETIME NULL DEFAULT (getdate()),
    [DiasSLAMaximo] INT NULL,
    CONSTRAINT [PK_CRM_Config_PipelineEtapas] PRIMARY KEY ([EtapaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Config_Pipelines]
-- ============================================================
CREATE TABLE [dbo].[CRM_Config_Pipelines] (
    [PipelineID] INT NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [TipoPipelineID] INT NULL DEFAULT ((1)),
    [EsDefault] BIT NULL DEFAULT ((0)),
    [Orden] INT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    [UpdatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Config_Pipelines] PRIMARY KEY ([PipelineID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Contratos]
-- ============================================================
CREATE TABLE [dbo].[CRM_Contratos] (
    [ContratoID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [CuentaID] UNIQUEIDENTIFIER NOT NULL,
    [OportunidadID] UNIQUEIDENTIFIER NULL,
    [PropuestaID] UNIQUEIDENTIFIER NULL,
    [FolioContrato] NVARCHAR(30) NULL,
    [NombreContrato] NVARCHAR(200) NOT NULL,
    [TipoContratoID] INT NULL,
    [DescripcionContrato] NVARCHAR(MAX) NULL,
    [MontoContrato] DECIMAL(18,2) NULL,
    [MonedaID] INT NULL DEFAULT ((1)),
    [FechaInicio] DATETIME NULL,
    [FechaFin] DATETIME NULL,
    [DuracionMeses] INT NULL,
    [RenovacionAutomatica] BIT NULL DEFAULT ((0)),
    [DiasAvisoRenovacion] INT NULL DEFAULT ((30)),
    [EstatusContratoID] INT NOT NULL DEFAULT ((1)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedBy] UNIQUEIDENTIFIER NULL,
    [UpdatedBy] UNIQUEIDENTIFIER NULL,
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    [UpdatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Contratos] PRIMARY KEY ([ContratoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Cuentas]
-- ============================================================
CREATE TABLE [dbo].[CRM_Cuentas] (
    [CuentaID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [SucursalID] UNIQUEIDENTIFIER NULL,
    [ClienteID] INT NULL,
    [CodigoCuenta] NVARCHAR(20) NULL,
    [TipoCuenta] NVARCHAR(20) NOT NULL DEFAULT ('PROSPECTO'),
    [NombreCuenta] NVARCHAR(200) NOT NULL,
    [RazonSocialSnapshot] NVARCHAR(200) NULL,
    [RFCSnapshot] NVARCHAR(13) NULL,
    [SectorID] INT NULL,
    [TamanoClienteID] INT NULL,
    [EjecutivoResponsableUserID] UNIQUEIDENTIFIER NULL,
    [CustomerSuccessUserID] UNIQUEIDENTIFIER NULL,
    [LeadOrigenID] UNIQUEIDENTIFIER NULL,
    [OrigenCuentaID] INT NULL,
    [ContactoPrincipalNombre] NVARCHAR(200) NULL,
    [ContactoPrincipalEmail] NVARCHAR(150) NULL,
    [ContactoPrincipalTelefono] NVARCHAR(50) NULL,
    [Direccion] NVARCHAR(500) NULL,
    [Ciudad] NVARCHAR(100) NULL,
    [Estado] NVARCHAR(100) NULL,
    [Pais] NVARCHAR(60) NULL DEFAULT ('México'),
    [CodigoPostal] NVARCHAR(10) NULL,
    [SitioWeb] NVARCHAR(200) NULL,
    [RedesSociales] NVARCHAR(500) NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [EstatusCuenta] NVARCHAR(20) NOT NULL DEFAULT ('ACTIVA'),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedBy] UNIQUEIDENTIFIER NULL,
    [UpdatedBy] UNIQUEIDENTIFIER NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (getutcdate()),
    [UpdatedAt] DATETIME2 NULL,
    CONSTRAINT [PK_CRM_Cuentas] PRIMARY KEY ([CuentaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_ERPSyncLog]
-- ============================================================
CREATE TABLE [dbo].[CRM_ERPSyncLog] (
    [ERPSyncID] INT NOT NULL,
    [PedidoID] BIGINT NOT NULL,
    [SistemaERP] VARCHAR(50) NOT NULL,
    [MetodoTransaccion] VARCHAR(50) NOT NULL,
    [PayloadRaw] NVARCHAR(MAX) NOT NULL,
    [EstatusERP] VARCHAR(50) NULL DEFAULT ('Pendiente'),
    [FechaRegistro] DATETIME NULL DEFAULT (getdate()),
    [FechaProcesamiento] DATETIME NULL,
    CONSTRAINT [PK_CRM_ERPSyncLog] PRIMARY KEY ([ERPSyncID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Implementaciones]
-- ============================================================
CREATE TABLE [dbo].[CRM_Implementaciones] (
    [ImplementacionID] INT NOT NULL,
    [PedidoID] BIGINT NOT NULL,
    [CuentaID] UNIQUEIDENTIFIER NOT NULL,
    [NombreProyecto] VARCHAR(255) NOT NULL,
    [FechaKickoff] DATETIME NULL,
    [FechaEntregaEstimada] DATETIME NULL,
    [Estatus] VARCHAR(50) NULL DEFAULT ('Kickoff'),
    [UsuarioLiderID] INT NOT NULL,
    [ProgresoPorcentaje] INT NULL DEFAULT ((0)),
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Implementaciones] PRIMARY KEY ([ImplementacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_ImplementacionesEntregables]
-- ============================================================
CREATE TABLE [dbo].[CRM_ImplementacionesEntregables] (
    [EntregableID] INT NOT NULL,
    [ImplementacionID] INT NOT NULL,
    [NombreEntregable] VARCHAR(255) NOT NULL,
    [Descripcion] VARCHAR(500) NULL,
    [Obligatorio] BIT NULL DEFAULT ((1)),
    [Estatus] VARCHAR(50) NULL DEFAULT ('Pendiente'),
    [FechaLimite] DATETIME NULL,
    [FechaAprobacion] DATETIME NULL,
    [UsuarioAprobadorID] INT NULL,
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_ImplementacionesEntregables] PRIMARY KEY ([EntregableID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Integracion_Conectores]
-- ============================================================
CREATE TABLE [dbo].[CRM_Integracion_Conectores] (
    [ConectorID] INT NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [Codigo] NVARCHAR(50) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [TipoConector] NVARCHAR(50) NOT NULL,
    [ConfiguracionJSON] NVARCHAR(MAX) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [EsPrincipal] BIT NULL DEFAULT ((0)),
    [UltimaSincronizacion] DATETIME NULL,
    [EstadoConexion] NVARCHAR(50) NULL DEFAULT ('PENDIENTE'),
    [MensajeError] NVARCHAR(MAX) NULL,
    [MapeoLeadsJSON] NVARCHAR(MAX) NULL,
    [MapeoOportunidadesJSON] NVARCHAR(MAX) NULL,
    [MapeoCuentasJSON] NVARCHAR(MAX) NULL,
    [MapeoContactosJSON] NVARCHAR(MAX) NULL,
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    [CreatedBy] UNIQUEIDENTIFIER NULL,
    [UpdatedAt] DATETIME NULL DEFAULT (getdate()),
    [UpdatedBy] UNIQUEIDENTIFIER NULL,
    CONSTRAINT [PK_CRM_Integracion_Conectores] PRIMARY KEY ([ConectorID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Integracion_MapeoEtapas]
-- ============================================================
CREATE TABLE [dbo].[CRM_Integracion_MapeoEtapas] (
    [MapeoID] INT NOT NULL,
    [ConectorID] INT NOT NULL,
    [EtapaExterna] NVARCHAR(100) NOT NULL,
    [EtapaLocalID] INT NULL,
    [EtapaLocalNombre] NVARCHAR(100) NULL,
    [MapeoActivo] BIT NULL DEFAULT ((1)),
    [EsDefault] BIT NULL DEFAULT ((0)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Integracion_MapeoEtapas] PRIMARY KEY ([MapeoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Integracion_SyncLog]
-- ============================================================
CREATE TABLE [dbo].[CRM_Integracion_SyncLog] (
    [LogID] BIGINT NOT NULL,
    [ConectorID] INT NOT NULL,
    [TipoEntidad] NVARCHAR(50) NOT NULL,
    [Operacion] NVARCHAR(50) NOT NULL,
    [FechaInicio] DATETIME NOT NULL,
    [FechaFin] DATETIME NULL,
    [Duracion] INT NULL,
    [RegistrosProcesados] INT NULL DEFAULT ((0)),
    [RegistrosCreados] INT NULL DEFAULT ((0)),
    [RegistrosActualizados] INT NULL DEFAULT ((0)),
    [RegistrosError] INT NULL DEFAULT ((0)),
    [RegistrosConflicto] INT NULL DEFAULT ((0)),
    [Estado] NVARCHAR(50) NOT NULL,
    [MensajeError] NVARCHAR(MAX) NULL,
    [DetallesJSON] NVARCHAR(MAX) NULL,
    [EjecutadoPor] UNIQUEIDENTIFIER NULL,
    CONSTRAINT [PK_CRM_Integracion_SyncLog] PRIMARY KEY ([LogID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_IntegracionesConflictos]
-- ============================================================
CREATE TABLE [dbo].[CRM_IntegracionesConflictos] (
    [ConflictoID] INT NOT NULL,
    [SyncLogID] BIGINT NOT NULL,
    [ColumnaConflicto] VARCHAR(100) NOT NULL,
    [ValorHub] NVARCHAR(1000) NULL,
    [ValorExterno] NVARCHAR(1000) NULL,
    [Resuelto] BIT NULL DEFAULT ((0)),
    [ReglaAplicada] VARCHAR(100) NULL,
    [FechaConflicto] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_IntegracionesConflictos] PRIMARY KEY ([ConflictoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_IntegracionesSyncLog]
-- ============================================================
CREATE TABLE [dbo].[CRM_IntegracionesSyncLog] (
    [SyncLogID] BIGINT NOT NULL,
    [SistemaExterno] VARCHAR(50) NOT NULL,
    [EntidadCanonica] VARCHAR(100) NOT NULL,
    [IDExterno] VARCHAR(255) NOT NULL,
    [DataRawPayload] NVARCHAR(MAX) NOT NULL,
    [EstatusSync] VARCHAR(50) NULL DEFAULT ('Pendiente'),
    [FechaRegistro] DATETIME NULL DEFAULT (getdate()),
    [FechaProcesamiento] DATETIME NULL,
    CONSTRAINT [PK_CRM_IntegracionesSyncLog] PRIMARY KEY ([SyncLogID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Leads]
-- ============================================================
CREATE TABLE [dbo].[CRM_Leads] (
    [LeadID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [SucursalID] UNIQUEIDENTIFIER NULL,
    [FolioLead] NVARCHAR(20) NULL,
    [NombreContacto] NVARCHAR(100) NOT NULL,
    [ApellidoPaterno] NVARCHAR(100) NULL,
    [ApellidoMaterno] NVARCHAR(100) NULL,
    [NombreEmpresa] NVARCHAR(200) NULL,
    [Puesto] NVARCHAR(100) NULL,
    [Email] NVARCHAR(150) NULL,
    [Telefono] NVARCHAR(50) NULL,
    [TelefonoMovil] NVARCHAR(50) NULL,
    [OrigenLeadID] INT NULL,
    [EstatusLeadID] INT NOT NULL DEFAULT ((1)),
    [PrioridadID] INT NULL,
    [CalificacionLeadID] INT NULL,
    [EjecutivoAsignadoUserID] UNIQUEIDENTIFIER NULL,
    [FechaAsignacion] DATETIME NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [Presupuesto] DECIMAL(18,2) NULL,
    [MonedaID] INT NULL,
    [FechaEstimadaCierre] DATETIME NULL,
    [ConvertidoACuenta] BIT NULL DEFAULT ((0)),
    [CuentaConvertidaID] UNIQUEIDENTIFIER NULL,
    [ContactoConvertidoID] UNIQUEIDENTIFIER NULL,
    [OportunidadConvertidaID] UNIQUEIDENTIFIER NULL,
    [FechaConversion] DATETIME NULL,
    [Descalificado] BIT NULL DEFAULT ((0)),
    [MotivoDescalificacionID] INT NULL,
    [FechaDescalificacion] DATETIME NULL,
    [NotasDescalificacion] NVARCHAR(500) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedBy] UNIQUEIDENTIFIER NULL,
    [UpdatedBy] UNIQUEIDENTIFIER NULL,
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    [UpdatedAt] DATETIME NULL DEFAULT (getdate()),
    [DeletedAt] DATETIME NULL,
    CONSTRAINT [PK_CRM_Leads] PRIMARY KEY ([LeadID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Oportunidad_Contactos]
-- ============================================================
CREATE TABLE [dbo].[CRM_Oportunidad_Contactos] (
    [ID] INT NOT NULL,
    [OportunidadID] UNIQUEIDENTIFIER NOT NULL,
    [ContactoID] UNIQUEIDENTIFIER NOT NULL,
    [RolContactoID] INT NULL,
    [EsPrincipal] BIT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Oportunidad_Contactos] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Oportunidad_Documentos]
-- ============================================================
CREATE TABLE [dbo].[CRM_Oportunidad_Documentos] (
    [ID] INT NOT NULL,
    [OportunidadID] UNIQUEIDENTIFIER NOT NULL,
    [TipoDocumentoID] INT NULL,
    [NombreDocumento] NVARCHAR(200) NOT NULL,
    [RutaArchivo] NVARCHAR(500) NULL,
    [Extension] NVARCHAR(10) NULL,
    [TamanoBytes] BIGINT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedBy] UNIQUEIDENTIFIER NULL,
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Oportunidad_Documentos] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Oportunidades]
-- ============================================================
CREATE TABLE [dbo].[CRM_Oportunidades] (
    [OportunidadID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [SucursalID] UNIQUEIDENTIFIER NULL,
    [FolioOportunidad] NVARCHAR(20) NULL,
    [CuentaID] UNIQUEIDENTIFIER NULL,
    [ContactoPrincipalID] UNIQUEIDENTIFIER NULL,
    [LeadOrigenID] UNIQUEIDENTIFIER NULL,
    [NombreOportunidad] NVARCHAR(200) NOT NULL,
    [DescripcionOportunidad] NVARCHAR(MAX) NULL,
    [PipelineID] INT NOT NULL DEFAULT ((1)),
    [EtapaActualID] INT NOT NULL DEFAULT ((1)),
    [ProbabilidadActual] INT NULL DEFAULT ((10)),
    [DiasEnEtapaActual] INT NULL DEFAULT ((0)),
    [MontoEstimado] DECIMAL(18,2) NULL,
    [MonedaID] INT NULL DEFAULT ((1)),
    [IngresoRecurrenteEstimado] DECIMAL(18,2) NULL,
    [IngresoNoRecurrenteEstimado] DECIMAL(18,2) NULL,
    [CostoEstimadoImplementacion] DECIMAL(18,2) NULL,
    [MargenEstimado] DECIMAL(18,2) NULL,
    [RequiereAprobacionDescuento] BIT NULL DEFAULT ((0)),
    [PorcentajeDescuento] DECIMAL(5,2) NULL,
    [MontoDescuento] DECIMAL(18,2) NULL,
    [FechaApertura] DATETIME NULL DEFAULT (getdate()),
    [FechaEstimadaCierre] DATETIME NULL,
    [FechaRealCierre] DATETIME NULL,
    [FechaUltimaActividad] DATETIME NULL,
    [FechaProximaActividad] DATETIME NULL,
    [EjecutivoResponsableUserID] UNIQUEIDENTIFIER NULL,
    [PreventaResponsableUserID] UNIQUEIDENTIFIER NULL,
    [GerenteComercialUserID] UNIQUEIDENTIFIER NULL,
    [CustomerSuccessUserID] UNIQUEIDENTIFIER NULL,
    [CompetidorPrincipalID] INT NULL,
    [EstatusCierreID] INT NULL,
    [MotivoGanadaID] INT NULL,
    [MotivoPerdidaID] INT NULL,
    [RazonPerdidaTexto] NVARCHAR(500) NULL,
    [RiesgoOportunidadID] INT NULL,
    [ScoreCierre] INT NULL,
    [RequiereContrato] BIT NULL DEFAULT ((0)),
    [RequiereImplementacion] BIT NULL DEFAULT ((0)),
    [RequiereFacturacionProgramada] BIT NULL DEFAULT ((0)),
    [ObservacionesInternas] NVARCHAR(MAX) NULL,
    [EstatusOportunidadID] INT NOT NULL DEFAULT ((1)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedBy] UNIQUEIDENTIFIER NULL,
    [UpdatedBy] UNIQUEIDENTIFIER NULL,
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    [UpdatedAt] DATETIME NULL DEFAULT (getdate()),
    [DeletedAt] DATETIME NULL,
    CONSTRAINT [PK_CRM_Oportunidades] PRIMARY KEY ([OportunidadID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Oportunidades_HistorialEtapas]
-- ============================================================
CREATE TABLE [dbo].[CRM_Oportunidades_HistorialEtapas] (
    [HistorialID] BIGINT NOT NULL,
    [OportunidadID] UNIQUEIDENTIFIER NOT NULL,
    [EtapaAnteriorID] INT NULL,
    [EtapaNuevaID] INT NOT NULL,
    [ProbabilidadAnterior] INT NULL,
    [ProbabilidadNueva] INT NULL,
    [MontoAnterior] DECIMAL(18,2) NULL,
    [MontoNuevo] DECIMAL(18,2) NULL,
    [DiasEnEtapaAnterior] INT NULL,
    [Comentario] NVARCHAR(500) NULL,
    [CambiadoPor] UNIQUEIDENTIFIER NULL,
    [FechaCambio] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Oportunidades_HistorialEtapas] PRIMARY KEY ([HistorialID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_OportunidadesHistorial]
-- ============================================================
CREATE TABLE [dbo].[CRM_OportunidadesHistorial] (
    [HistorialPipelineID] INT NOT NULL,
    [OportunidadID] UNIQUEIDENTIFIER NOT NULL,
    [EtapaAnteriorID] INT NULL,
    [EtapaNuevaID] INT NOT NULL,
    [MontoAnterior] DECIMAL(18,2) NULL,
    [MontoNuevo] DECIMAL(18,2) NOT NULL,
    [UsuarioModificadorID] UNIQUEIDENTIFIER NOT NULL,
    [FechaCambio] DATETIME NULL DEFAULT (getdate()),
    [Comentario] NVARCHAR(500) NULL,
    CONSTRAINT [PK_CRM_OportunidadesHistorial] PRIMARY KEY ([HistorialPipelineID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_PostventaEncuestas]
-- ============================================================
CREATE TABLE [dbo].[CRM_PostventaEncuestas] (
    [EncuestaID] INT NOT NULL,
    [CuentaID] UNIQUEIDENTIFIER NOT NULL,
    [TicketID] INT NULL,
    [PuntuacionCSAT] INT NOT NULL,
    [Comentarios] NVARCHAR(1000) NULL,
    [FechaRegistro] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_PostventaEncuestas] PRIMARY KEY ([EncuestaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_PostventaTickets]
-- ============================================================
CREATE TABLE [dbo].[CRM_PostventaTickets] (
    [TicketID] INT NOT NULL,
    [CuentaID] UNIQUEIDENTIFIER NOT NULL,
    [FolioTicket] VARCHAR(50) NOT NULL,
    [Asunto] VARCHAR(255) NOT NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [Estatus] VARCHAR(50) NULL DEFAULT ('Abierto'),
    [Prioridad] VARCHAR(30) NULL DEFAULT ('Media'),
    [UsuarioAsignadoID] INT NOT NULL,
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_PostventaTickets] PRIMARY KEY ([TicketID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Propuestas]
-- ============================================================
CREATE TABLE [dbo].[CRM_Propuestas] (
    [PropuestaID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [OportunidadID] UNIQUEIDENTIFIER NOT NULL,
    [FolioPropuesta] NVARCHAR(20) NULL,
    [NombrePropuesta] NVARCHAR(200) NOT NULL,
    [DescripcionPropuesta] NVARCHAR(MAX) NULL,
    [TipoPropuestaID] INT NULL,
    [VersionActual] INT NULL DEFAULT ((1)),
    [MontoTotal] DECIMAL(18,2) NULL,
    [MonedaID] INT NULL DEFAULT ((1)),
    [Descuento] DECIMAL(18,2) NULL,
    [IVA] DECIMAL(18,2) NULL,
    [MontoFinal] DECIMAL(18,2) NULL,
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    [FechaEnvio] DATETIME NULL,
    [FechaVigencia] DATETIME NULL,
    [FechaRespuesta] DATETIME NULL,
    [EstatusPropuestaID] INT NOT NULL DEFAULT ((1)),
    [MotivoRechazoID] INT NULL,
    [NotasRechazo] NVARCHAR(500) NULL,
    [RequiereAprobacion] BIT NULL DEFAULT ((0)),
    [AprobadaPor] UNIQUEIDENTIFIER NULL,
    [FechaAprobacion] DATETIME NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedBy] UNIQUEIDENTIFIER NULL,
    [UpdatedBy] UNIQUEIDENTIFIER NULL,
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    [UpdatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Propuestas] PRIMARY KEY ([PropuestaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Staging_Cuentas]
-- ============================================================
CREATE TABLE [dbo].[CRM_Staging_Cuentas] (
    [StagingID] BIGINT NOT NULL,
    [ConectorID] INT NOT NULL,
    [ExternalID] NVARCHAR(100) NOT NULL,
    [LocalCuentaID] UNIQUEIDENTIFIER NULL,
    [RazonSocial] NVARCHAR(200) NULL,
    [NombreComercial] NVARCHAR(200) NULL,
    [RFC] NVARCHAR(20) NULL,
    [Industria] NVARCHAR(100) NULL,
    [SitioWeb] NVARCHAR(200) NULL,
    [EmailPrincipal] NVARCHAR(150) NULL,
    [TelefonoPrincipal] NVARCHAR(50) NULL,
    [Direccion] NVARCHAR(500) NULL,
    [DatosExternosJSON] NVARCHAR(MAX) NULL,
    [DireccionSync] NVARCHAR(20) NOT NULL,
    [EstadoSync] NVARCHAR(50) NULL DEFAULT ('PENDIENTE'),
    [FechaExterna] DATETIME NULL,
    [FechaLocal] DATETIME NULL,
    [FechaProcesado] DATETIME NULL,
    [Intentos] INT NULL DEFAULT ((0)),
    [MensajeError] NVARCHAR(MAX) NULL,
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    [UpdatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Staging_Cuentas] PRIMARY KEY ([StagingID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Staging_Leads]
-- ============================================================
CREATE TABLE [dbo].[CRM_Staging_Leads] (
    [StagingID] BIGINT NOT NULL,
    [ConectorID] INT NOT NULL,
    [ExternalID] NVARCHAR(100) NOT NULL,
    [LocalLeadID] UNIQUEIDENTIFIER NULL,
    [NombreContacto] NVARCHAR(100) NULL,
    [ApellidoPaterno] NVARCHAR(100) NULL,
    [ApellidoMaterno] NVARCHAR(100) NULL,
    [NombreEmpresa] NVARCHAR(200) NULL,
    [Email] NVARCHAR(150) NULL,
    [Telefono] NVARCHAR(50) NULL,
    [TelefonoMovil] NVARCHAR(50) NULL,
    [Puesto] NVARCHAR(100) NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [Origen] NVARCHAR(100) NULL,
    [Estatus] NVARCHAR(100) NULL,
    [DatosExternosJSON] NVARCHAR(MAX) NULL,
    [DireccionSync] NVARCHAR(20) NOT NULL,
    [EstadoSync] NVARCHAR(50) NULL DEFAULT ('PENDIENTE'),
    [FechaExterna] DATETIME NULL,
    [FechaLocal] DATETIME NULL,
    [FechaProcesado] DATETIME NULL,
    [Intentos] INT NULL DEFAULT ((0)),
    [MensajeError] NVARCHAR(MAX) NULL,
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    [UpdatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Staging_Leads] PRIMARY KEY ([StagingID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Staging_Oportunidades]
-- ============================================================
CREATE TABLE [dbo].[CRM_Staging_Oportunidades] (
    [StagingID] BIGINT NOT NULL,
    [ConectorID] INT NOT NULL,
    [ExternalID] NVARCHAR(100) NOT NULL,
    [LocalOportunidadID] UNIQUEIDENTIFIER NULL,
    [NombreOportunidad] NVARCHAR(200) NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [MontoEstimado] DECIMAL(18,2) NULL,
    [Moneda] NVARCHAR(10) NULL DEFAULT ('MXN'),
    [FechaEstimadaCierre] DATE NULL,
    [Etapa] NVARCHAR(100) NULL,
    [Probabilidad] INT NULL,
    [Estatus] NVARCHAR(100) NULL,
    [ExternalCuentaID] NVARCHAR(100) NULL,
    [ExternalContactoID] NVARCHAR(100) NULL,
    [ExternalLeadID] NVARCHAR(100) NULL,
    [DatosExternosJSON] NVARCHAR(MAX) NULL,
    [DireccionSync] NVARCHAR(20) NOT NULL,
    [EstadoSync] NVARCHAR(50) NULL DEFAULT ('PENDIENTE'),
    [FechaExterna] DATETIME NULL,
    [FechaLocal] DATETIME NULL,
    [FechaProcesado] DATETIME NULL,
    [Intentos] INT NULL DEFAULT ((0)),
    [MensajeError] NVARCHAR(MAX) NULL,
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    [UpdatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Staging_Oportunidades] PRIMARY KEY ([StagingID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Tareas]
-- ============================================================
CREATE TABLE [dbo].[CRM_Tareas] (
    [TareaID] NVARCHAR(50) NOT NULL,
    [EmpresaID] NVARCHAR(50) NOT NULL,
    [OportunidadID] NVARCHAR(50) NULL,
    [ResponsableID] NVARCHAR(50) NULL,
    [Titulo] NVARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(1000) NULL,
    [FechaVencimiento] DATETIME NULL,
    [Prioridad] NVARCHAR(20) NULL DEFAULT ('MEDIA'),
    [EstatusID] INT NULL DEFAULT ((1)),
    [AutoGenerada] BIT NULL DEFAULT ((0)),
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    [FechaCompletada] DATETIME NULL,
    CONSTRAINT [PK_CRM_Tareas] PRIMARY KEY ([TareaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Trigger_Log]
-- ============================================================
CREATE TABLE [dbo].[CRM_Trigger_Log] (
    [LogID] NVARCHAR(50) NOT NULL,
    [TriggerID] NVARCHAR(50) NOT NULL,
    [EntidadID] NVARCHAR(50) NULL,
    [EmpresaID] NVARCHAR(50) NOT NULL,
    [Exitoso] BIT NULL DEFAULT ((0)),
    [ResultadoJSON] NVARCHAR(MAX) NULL,
    [FechaEjecucion] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_CRM_Trigger_Log] PRIMARY KEY ([LogID])
);
GO

-- ============================================================
-- TABLA: [dbo].[CRM_Triggers]
-- ============================================================
CREATE TABLE [dbo].[CRM_Triggers] (
    [TriggerID] NVARCHAR(50) NOT NULL,
    [EmpresaID] NVARCHAR(50) NOT NULL,
    [Nombre] NVARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [TipoEvento] NVARCHAR(50) NOT NULL,
    [CondicionesJSON] NVARCHAR(MAX) NULL,
    [AccionesJSON] NVARCHAR(MAX) NOT NULL,
    [Prioridad] INT NULL DEFAULT ((100)),
    [Activo] BIT NULL DEFAULT ((1)),
    [UsuarioCreacionID] NVARCHAR(50) NULL,
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME NULL,
    CONSTRAINT [PK_CRM_Triggers] PRIMARY KEY ([TriggerID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Fact_Ventas_Consolidadas]
-- ============================================================
CREATE TABLE [dbo].[Fact_Ventas_Consolidadas] (
    [Id] INT NOT NULL,
    [TenantID] INT NOT NULL,
    [Fecha] DATE NOT NULL,
    [Periodo] NVARCHAR(20) NULL,
    [IdProducto] INT NOT NULL,
    [Cantidad] DECIMAL(18,2) NULL,
    [ImporteNeto] DECIMAL(18,2) NULL,
    [Propina] DECIMAL(18,2) NULL,
    [Pax] INT NULL,
    [IdAreaVenta] INT NULL,
    [IdFormaCobro] INT NULL,
    CONSTRAINT [PK_Fact_Ventas_Consolidadas] PRIMARY KEY ([Id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Finanzas_Cat_CuentasBancarias]
-- ============================================================
CREATE TABLE [dbo].[Finanzas_Cat_CuentasBancarias] (
    [CuentaBancariaID] INT NOT NULL,
    [EmpresaID] INT NULL,
    [BancoID] INT NULL,
    [NumeroCuenta] VARCHAR(20) NOT NULL,
    [CLABE] VARCHAR(18) NULL,
    [Alias] VARCHAR(50) NOT NULL,
    [Moneda] VARCHAR(3) NOT NULL DEFAULT ('MXN'),
    [EsCuentaPrincipal] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (getdate()),
    [UsuarioCreacionID] INT NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacionID] INT NULL,
    CONSTRAINT [PK_Finanzas_Cat_CuentasBancarias] PRIMARY KEY ([CuentaBancariaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Finanzas_Cat_EstatusCuadreZ]
-- ============================================================
CREATE TABLE [dbo].[Finanzas_Cat_EstatusCuadreZ] (
    [EstatusCuadreID] TINYINT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Descripcion] NVARCHAR(50) NOT NULL,
    [ColorHex] NVARCHAR(7) NOT NULL,
    [Orden] TINYINT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Finanzas_Cat_EstatusCuadreZ] PRIMARY KEY ([EstatusCuadreID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Finanzas_Cat_EstatusTesoreria]
-- ============================================================
CREATE TABLE [dbo].[Finanzas_Cat_EstatusTesoreria] (
    [EstatusTesoreriaID] TINYINT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Descripcion] NVARCHAR(50) NOT NULL,
    [ColorHex] NVARCHAR(7) NOT NULL,
    [Orden] TINYINT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Finanzas_Cat_EstatusTesoreria] PRIMARY KEY ([EstatusTesoreriaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Finanzas_ConfiguracionTPV_Sucursal]
-- ============================================================
CREATE TABLE [dbo].[Finanzas_ConfiguracionTPV_Sucursal] (
    [ConfiguracionTPVID] INT NOT NULL,
    [SucursalID] INT NOT NULL,
    [ProveedorTPV] VARCHAR(50) NOT NULL DEFAULT ('NetPay'),
    [ComisionDebito] DECIMAL(5,3) NOT NULL DEFAULT ((1.20)),
    [ComisionCredito] DECIMAL(5,3) NOT NULL DEFAULT ((1.50)),
    [ComisionAmex] DECIMAL(5,3) NOT NULL DEFAULT ((2.40)),
    [ComisionInternacional] DECIMAL(5,3) NOT NULL DEFAULT ((2.00)),
    [AplicaIVAComision] BIT NOT NULL DEFAULT ((1)),
    [PorcentajeIVA] DECIMAL(5,2) NOT NULL DEFAULT ((16.00)),
    [DiasDepositoDebito] INT NOT NULL DEFAULT ((1)),
    [DiasDepositoCredito] INT NOT NULL DEFAULT ((1)),
    [DiasDepositoAmex] INT NOT NULL DEFAULT ((2)),
    [DiasDepositoInternacional] INT NOT NULL DEFAULT ((2)),
    [DiasDepositoEfectivo] INT NOT NULL DEFAULT ((1)),
    [EfectivoFinDeSemanaLunes] BIT NOT NULL DEFAULT ((1)),
    [CuentaBancariaID] INT NULL,
    [NumeroAfiliacion] VARCHAR(50) NULL,
    [TerminalID] VARCHAR(50) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Finanzas_ConfiguracionTPV_Sucursal] PRIMARY KEY ([ConfiguracionTPVID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Finanzas_CortesCaja]
-- ============================================================
CREATE TABLE [dbo].[Finanzas_CortesCaja] (
    [CorteCajaID] BIGINT NOT NULL,
    [SucursalID] INT NOT NULL,
    [FechaCorte] DATE NOT NULL,
    [TurnoID] INT NULL,
    [TotalEfectivo] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalTarjetaDebito] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalTarjetaCredito] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalAmex] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalInternacional] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalVales] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalOtros] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ComisionDebito] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ComisionCredito] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ComisionAmex] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ComisionInternacional] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [FechaDepositoEfectivo] DATE NULL,
    [FechaDepositoDebito] DATE NULL,
    [FechaDepositoCredito] DATE NULL,
    [FechaDepositoAmex] DATE NULL,
    [FechaDepositoInternacional] DATE NULL,
    [DepositadoEfectivo] BIT NOT NULL DEFAULT ((0)),
    [DepositadoDebito] BIT NOT NULL DEFAULT ((0)),
    [DepositadoCredito] BIT NOT NULL DEFAULT ((0)),
    [DepositadoAmex] BIT NOT NULL DEFAULT ((0)),
    [DepositadoInternacional] BIT NOT NULL DEFAULT ((0)),
    [EstatusCierreID] TINYINT NOT NULL DEFAULT ((1)),
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (getdate()),
    [UnidadNegocioID] NVARCHAR(50) NULL,
    [UnidadNegocioNombre] NVARCHAR(100) NULL,
    [EmpresaID] NVARCHAR(50) NULL,
    [ServerID] NVARCHAR(50) NULL,
    [SistemaOrigen] NVARCHAR(20) NULL,
    [BaseDatosOrigen] NVARCHAR(100) NULL,
    [TablaOrigen] NVARCHAR(50) NULL,
    [FolioCorte] NVARCHAR(50) NULL,
    [IdOrigen] BIGINT NULL,
    [SucursalOrigenID] NVARCHAR(20) NULL,
    [FechaApertura] DATETIME2 NULL,
    [FechaCierre] DATETIME2 NULL,
    [CajeroID] NVARCHAR(50) NULL,
    [CajeroNombre] NVARCHAR(100) NULL,
    [CajaID] NVARCHAR(50) NULL,
    [CajaNombre] NVARCHAR(100) NULL,
    [Propinas] DECIMAL(18,2) NULL DEFAULT ((0)),
    [Retiros] DECIMAL(18,2) NULL DEFAULT ((0)),
    [FondoInicial] DECIMAL(18,2) NULL DEFAULT ((0)),
    [TotalVenta] DECIMAL(18,2) NULL DEFAULT ((0)),
    [HashOrigen] NVARCHAR(64) NULL,
    [FechaSincronizacion] DATETIME2 NULL,
    [FechaUltimaActualizacion] DATETIME2 NULL,
    [EsDemo] BIT NULL DEFAULT ((0)),
    CONSTRAINT [PK_Finanzas_CortesCaja] PRIMARY KEY ([CorteCajaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Finanzas_CortesCaja_Backup_Demo_20260501]
-- ============================================================
CREATE TABLE [dbo].[Finanzas_CortesCaja_Backup_Demo_20260501] (
    [CorteCajaID] BIGINT NOT NULL,
    [SucursalID] INT NOT NULL,
    [FechaCorte] DATE NOT NULL,
    [TurnoID] INT NULL,
    [TotalEfectivo] DECIMAL(18,2) NOT NULL,
    [TotalTarjetaDebito] DECIMAL(18,2) NOT NULL,
    [TotalTarjetaCredito] DECIMAL(18,2) NOT NULL,
    [TotalAmex] DECIMAL(18,2) NOT NULL,
    [TotalInternacional] DECIMAL(18,2) NOT NULL,
    [TotalVales] DECIMAL(18,2) NOT NULL,
    [TotalOtros] DECIMAL(18,2) NOT NULL,
    [ComisionDebito] DECIMAL(18,2) NOT NULL,
    [ComisionCredito] DECIMAL(18,2) NOT NULL,
    [ComisionAmex] DECIMAL(18,2) NOT NULL,
    [ComisionInternacional] DECIMAL(18,2) NOT NULL,
    [FechaDepositoEfectivo] DATE NULL,
    [FechaDepositoDebito] DATE NULL,
    [FechaDepositoCredito] DATE NULL,
    [FechaDepositoAmex] DATE NULL,
    [FechaDepositoInternacional] DATE NULL,
    [DepositadoEfectivo] BIT NOT NULL,
    [DepositadoDebito] BIT NOT NULL,
    [DepositadoCredito] BIT NOT NULL,
    [DepositadoAmex] BIT NOT NULL,
    [DepositadoInternacional] BIT NOT NULL,
    [EstatusCierreID] TINYINT NOT NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL
);
GO

-- ============================================================
-- TABLA: [dbo].[Finanzas_CortesCaja_DetallePagos]
-- ============================================================
CREATE TABLE [dbo].[Finanzas_CortesCaja_DetallePagos] (
    [DetalleID] BIGINT NOT NULL,
    [CorteCajaID] BIGINT NOT NULL,
    [FormaPago] NVARCHAR(50) NOT NULL,
    [FormaPagoCodigo] NVARCHAR(10) NULL,
    [Importe] DECIMAL(18,2) NOT NULL,
    [Referencia] NVARCHAR(100) NULL,
    [SistemaOrigen] NVARCHAR(20) NULL,
    [IdOrigen] BIGINT NULL,
    [HashOrigen] NVARCHAR(64) NULL,
    [FechaAlta] DATETIME2 NULL DEFAULT (getdate()),
    [Activo] BIT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Finanzas_CortesCaja_DetallePagos] PRIMARY KEY ([DetalleID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Finanzas_CortesCaja_SyncLog]
-- ============================================================
CREATE TABLE [dbo].[Finanzas_CortesCaja_SyncLog] (
    [LogID] BIGINT NOT NULL,
    [FechaInicio] DATETIME2 NOT NULL,
    [FechaFin] DATETIME2 NULL,
    [UnidadNegocioID] NVARCHAR(50) NULL,
    [ServerID] NVARCHAR(50) NULL,
    [SistemaOrigen] NVARCHAR(20) NULL,
    [FechaDesde] DATE NULL,
    [FechaHasta] DATE NULL,
    [RegistrosLeidos] INT NULL DEFAULT ((0)),
    [RegistrosInsertados] INT NULL DEFAULT ((0)),
    [RegistrosActualizados] INT NULL DEFAULT ((0)),
    [RegistrosOmitidos] INT NULL DEFAULT ((0)),
    [RegistrosError] INT NULL DEFAULT ((0)),
    [Estatus] NVARCHAR(20) NULL DEFAULT ('EN_PROCESO'),
    [ErrorMensaje] NVARCHAR(MAX) NULL,
    [DuracionSegundos] INT NULL,
    [UsuarioEjecucion] NVARCHAR(50) NULL,
    [TipoEjecucion] NVARCHAR(20) NULL,
    CONSTRAINT [PK_Finanzas_CortesCaja_SyncLog] PRIMARY KEY ([LogID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Finanzas_CuadresZ]
-- ============================================================
CREATE TABLE [dbo].[Finanzas_CuadresZ] (
    [CuadreZID] BIGINT NOT NULL,
    [UnidadNegocioID] NVARCHAR(50) NOT NULL,
    [UnidadNegocioNombre] NVARCHAR(100) NOT NULL,
    [EmpresaID] NVARCHAR(50) NULL,
    [ServerID] NVARCHAR(50) NOT NULL,
    [SistemaOrigen] NVARCHAR(20) NOT NULL,
    [BaseDatosOrigen] NVARCHAR(100) NULL,
    [FechaOperacion] DATE NOT NULL,
    [FechaCorte] DATE NOT NULL,
    [FechaApertura] DATETIME2 NULL,
    [FechaCierre] DATETIME2 NULL,
    [FolioCorte] NVARCHAR(50) NOT NULL,
    [FolioZ] NVARCHAR(50) NULL,
    [CajaID] NVARCHAR(50) NULL,
    [CajaNombre] NVARCHAR(100) NULL,
    [CajeroID] NVARCHAR(50) NULL,
    [CajeroNombre] NVARCHAR(100) NULL,
    [TurnoID] INT NULL,
    [TotalVenta] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalEfectivo] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalTarjetaDebito] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalTarjetaCredito] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalAmex] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalTarjetaTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalTransferencia] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalVales] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalOtros] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalPropinasTPV] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalPropinasEfectivo] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalRetiros] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [FondoInicial] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalDepositar] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalDeclarado] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Diferencia] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ConteoEfectivo_Billetes1000] INT NOT NULL DEFAULT ((0)),
    [ConteoEfectivo_Billetes500] INT NOT NULL DEFAULT ((0)),
    [ConteoEfectivo_Billetes200] INT NOT NULL DEFAULT ((0)),
    [ConteoEfectivo_Billetes100] INT NOT NULL DEFAULT ((0)),
    [ConteoEfectivo_Billetes50] INT NOT NULL DEFAULT ((0)),
    [ConteoEfectivo_Billetes20] INT NOT NULL DEFAULT ((0)),
    [ConteoEfectivo_Monedas20] INT NOT NULL DEFAULT ((0)),
    [ConteoEfectivo_Monedas10] INT NOT NULL DEFAULT ((0)),
    [ConteoEfectivo_Monedas5] INT NOT NULL DEFAULT ((0)),
    [ConteoEfectivo_Monedas2] INT NOT NULL DEFAULT ((0)),
    [ConteoEfectivo_Monedas1] INT NOT NULL DEFAULT ((0)),
    [ConteoEfectivo_Monedas050] INT NOT NULL DEFAULT ((0)),
    [ConteoEfectivo_Total] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [FichaDepositoURL] NVARCHAR(500) NULL,
    [FichaDepositoFecha] DATE NULL,
    [FichaDepositoMonto] DECIMAL(18,2) NULL,
    [FichaDepositoValidada] BIT NOT NULL DEFAULT ((0)),
    [FichaDepositoBancoID] INT NULL,
    [FichaDepositoCuentaID] INT NULL,
    [EstatusCuadreID] TINYINT NOT NULL DEFAULT ((1)),
    [EstatusTesoreriaID] TINYINT NOT NULL DEFAULT ((1)),
    [Observaciones] NVARCHAR(500) NULL,
    [UsuarioCapturaID] NVARCHAR(50) NULL,
    [UsuarioCapturaNombre] NVARCHAR(100) NULL,
    [FechaCaptura] DATETIME2 NULL,
    [UsuarioValidaID] NVARCHAR(50) NULL,
    [UsuarioValidaNombre] NVARCHAR(100) NULL,
    [FechaValidacion] DATETIME2 NULL,
    [CorteCajaID] BIGINT NULL,
    [FuenteOriginal] NVARCHAR(20) NOT NULL DEFAULT ('MONGODB'),
    [IdOrigen] NVARCHAR(50) NULL,
    [HashOrigen] NVARCHAR(64) NULL,
    [EsDemo] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaSincronizacion] DATETIME2 NULL,
    [FechaUltimaActualizacion] DATETIME2 NULL,
    CONSTRAINT [PK_Finanzas_CuadresZ] PRIMARY KEY ([CuadreZID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Finanzas_CuadresZ_SyncLog]
-- ============================================================
CREATE TABLE [dbo].[Finanzas_CuadresZ_SyncLog] (
    [LogID] BIGINT NOT NULL,
    [JobName] NVARCHAR(50) NOT NULL,
    [TipoOperacion] NVARCHAR(20) NOT NULL,
    [UnidadNegocioID] NVARCHAR(50) NULL,
    [UnidadNegocioNombre] NVARCHAR(100) NULL,
    [FechaDesde] DATE NULL,
    [FechaHasta] DATE NULL,
    [RegistrosLeidos] INT NOT NULL DEFAULT ((0)),
    [RegistrosInsertados] INT NOT NULL DEFAULT ((0)),
    [RegistrosActualizados] INT NOT NULL DEFAULT ((0)),
    [RegistrosOmitidos] INT NOT NULL DEFAULT ((0)),
    [RegistrosError] INT NOT NULL DEFAULT ((0)),
    [MensajeError] NVARCHAR(MAX) NULL,
    [FechaInicio] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaFin] DATETIME2 NULL,
    [DuracionMs] INT NULL,
    [UsuarioID] NVARCHAR(50) NULL,
    [UsuarioNombre] NVARCHAR(100) NULL,
    [Estatus] NVARCHAR(20) NOT NULL DEFAULT ('EN_PROCESO'),
    [Metadata] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_Finanzas_CuadresZ_SyncLog] PRIMARY KEY ([LogID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Finanzas_CuentasPorPagar]
-- ============================================================
CREATE TABLE [dbo].[Finanzas_CuentasPorPagar] (
    [CuentaPorPagarID] BIGINT NOT NULL,
    [DocumentoFiscalID] BIGINT NULL,
    [ProveedorID] INT NOT NULL,
    [SucursalID] INT NOT NULL,
    [NumeroDocumento] VARCHAR(50) NOT NULL,
    [FechaDocumento] DATE NOT NULL,
    [FechaVencimiento] DATE NOT NULL,
    [FechaRecepcion] DATE NULL,
    [MontoOriginal] DECIMAL(18,2) NOT NULL,
    [MontoPagado] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [MonedaID] INT NOT NULL DEFAULT ((1)),
    [TipoCambio] DECIMAL(18,6) NOT NULL DEFAULT ((1)),
    [EstatusPagoID] TINYINT NOT NULL DEFAULT ((1)),
    [DiasCredito] INT NOT NULL DEFAULT ((0)),
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Finanzas_CuentasPorPagar] PRIMARY KEY ([CuentaPorPagarID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Finanzas_Depositos]
-- ============================================================
CREATE TABLE [dbo].[Finanzas_Depositos] (
    [DepositoID] BIGINT NOT NULL,
    [CuentaBancariaID] INT NOT NULL,
    [SucursalID] INT NOT NULL,
    [FechaDeposito] DATE NOT NULL,
    [MontoDeposito] DECIMAL(18,2) NOT NULL,
    [TipoDeposito] VARCHAR(20) NOT NULL,
    [NumeroReferencia] VARCHAR(50) NULL,
    [CorteCajaID] BIGINT NULL,
    [Conciliado] BIT NOT NULL DEFAULT ((0)),
    [FechaConciliacion] DATE NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Finanzas_Depositos] PRIMARY KEY ([DepositoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Finanzas_EstatusCierre]
-- ============================================================
CREATE TABLE [dbo].[Finanzas_EstatusCierre] (
    [EstatusCierreID] TINYINT NOT NULL,
    [Codigo] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Finanzas_EstatusCierre] PRIMARY KEY ([EstatusCierreID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Finanzas_EstatusPago]
-- ============================================================
CREATE TABLE [dbo].[Finanzas_EstatusPago] (
    [EstatusPagoID] TINYINT NOT NULL,
    [Codigo] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [ColorHex] VARCHAR(7) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Finanzas_EstatusPago] PRIMARY KEY ([EstatusPagoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Finanzas_KPIs_Historico]
-- ============================================================
CREATE TABLE [dbo].[Finanzas_KPIs_Historico] (
    [id] INT NOT NULL,
    [run_id] VARCHAR(50) NOT NULL,
    [server_id] VARCHAR(100) NOT NULL,
    [sucursal_id] VARCHAR(100) NOT NULL,
    [system_type_normalized] VARCHAR(50) NOT NULL,
    [fecha] DATE NOT NULL,
    [kpi_tipo] VARCHAR(50) NOT NULL,
    [ventas_efectivo] DECIMAL(18,2) NULL DEFAULT ((0)),
    [ventas_tarjeta_debito] DECIMAL(18,2) NULL DEFAULT ((0)),
    [ventas_tarjeta_credito] DECIMAL(18,2) NULL DEFAULT ((0)),
    [ventas_tarjeta_amex] DECIMAL(18,2) NULL DEFAULT ((0)),
    [ventas_otros] DECIMAL(18,2) NULL DEFAULT ((0)),
    [ventas_total] DECIMAL(18,2) NULL DEFAULT ((0)),
    [propinas] DECIMAL(18,2) NULL DEFAULT ((0)),
    [comision_debito] DECIMAL(18,2) NULL DEFAULT ((0)),
    [comision_credito] DECIMAL(18,2) NULL DEFAULT ((0)),
    [comision_amex] DECIMAL(18,2) NULL DEFAULT ((0)),
    [comision_total] DECIMAL(18,2) NULL DEFAULT ((0)),
    [cxp_facturas_count] INT NULL DEFAULT ((0)),
    [cxp_monto_total] DECIMAL(18,2) NULL DEFAULT ((0)),
    [cxp_monto_alimentos] DECIMAL(18,2) NULL DEFAULT ((0)),
    [cxp_monto_bebidas] DECIMAL(18,2) NULL DEFAULT ((0)),
    [cxp_monto_otros] DECIMAL(18,2) NULL DEFAULT ((0)),
    [cxp_saldo_pendiente] DECIMAL(18,2) NULL DEFAULT ((0)),
    [flujo_efectivo_neto] DECIMAL(18,2) NULL DEFAULT ((0)),
    [empresa_id] VARCHAR(100) NULL,
    [empresa_nombre] NVARCHAR(200) NULL,
    [origen] VARCHAR(50) NULL DEFAULT ('HISTORICAL_LOAD'),
    [fecha_carga] DATETIME NULL DEFAULT (getdate()),
    [fecha_actualizacion] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Finanzas_KPIs_Historico] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Finanzas_Pagos]
-- ============================================================
CREATE TABLE [dbo].[Finanzas_Pagos] (
    [PagoID] BIGINT NOT NULL,
    [CuentaPorPagarID] BIGINT NOT NULL,
    [FechaPago] DATE NOT NULL,
    [MontoPagado] DECIMAL(18,2) NOT NULL,
    [FormaPagoID] INT NULL,
    [CuentaBancariaID] INT NULL,
    [NumeroReferencia] VARCHAR(50) NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Finanzas_Pagos] PRIMARY KEY ([PagoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Finanzas_Presupuestos]
-- ============================================================
CREATE TABLE [dbo].[Finanzas_Presupuestos] (
    [PresupuestoID] INT NOT NULL,
    [SucursalID] INT NOT NULL,
    [Categoria] NVARCHAR(100) NOT NULL,
    [SubCategoria] NVARCHAR(100) NULL,
    [Tipo] NVARCHAR(20) NOT NULL,
    [Monto_Presupuestado] DECIMAL(18,2) NULL DEFAULT ((0)),
    [Monto_Ejecutado] DECIMAL(18,2) NULL DEFAULT ((0)),
    [Anio] INT NOT NULL,
    [Mes] INT NOT NULL,
    [Notas] NVARCHAR(500) NULL,
    [Fecha_Creacion] DATETIME NULL DEFAULT (getdate()),
    [Fecha_Modificacion] DATETIME NULL,
    [Creado_Por] NVARCHAR(100) NULL,
    CONSTRAINT [PK_Finanzas_Presupuestos] PRIMARY KEY ([PresupuestoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Finanzas_PropinasTPV_SyncLog]
-- ============================================================
CREATE TABLE [dbo].[Finanzas_PropinasTPV_SyncLog] (
    [LogID] BIGINT NOT NULL,
    [FechaInicio] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaFin] DATETIME2 NULL,
    [UnidadNegocioID] UNIQUEIDENTIFIER NULL,
    [UnidadNegocioNombre] NVARCHAR(100) NULL,
    [ServerID] NVARCHAR(50) NULL,
    [SistemaOrigen] NVARCHAR(20) NULL,
    [BaseDatosOrigen] NVARCHAR(100) NULL,
    [FechaDesde] DATE NULL,
    [FechaHasta] DATE NULL,
    [RegistrosLeidos] INT NOT NULL DEFAULT ((0)),
    [RegistrosInsertados] INT NOT NULL DEFAULT ((0)),
    [RegistrosActualizados] INT NOT NULL DEFAULT ((0)),
    [RegistrosOmitidos] INT NOT NULL DEFAULT ((0)),
    [RegistrosConError] INT NOT NULL DEFAULT ((0)),
    [TotalPropinasTPV] DECIMAL(18,2) NULL,
    [Estatus] NVARCHAR(20) NOT NULL DEFAULT ('EN_PROGRESO'),
    [ErrorMensaje] NVARCHAR(MAX) NULL,
    [TipoEjecucion] NVARCHAR(20) NOT NULL DEFAULT ('MANUAL'),
    [UsuarioEjecucion] NVARCHAR(100) NULL,
    [HashMuestra] NVARCHAR(64) NULL,
    [DuracionSegundos] INT NULL,
    CONSTRAINT [PK_Finanzas_PropinasTPV_SyncLog] PRIMARY KEY ([LogID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Finanzas_SaldosBancarios]
-- ============================================================
CREATE TABLE [dbo].[Finanzas_SaldosBancarios] (
    [SaldoBancarioID] BIGINT NOT NULL,
    [CuentaBancariaID] INT NOT NULL,
    [FechaSaldo] DATE NOT NULL,
    [SaldoFinal] DECIMAL(18,2) NOT NULL,
    [Moneda] VARCHAR(3) NOT NULL DEFAULT ('MXN'),
    [TipoCambio] DECIMAL(10,4) NULL,
    [FuenteDatos] VARCHAR(20) NOT NULL DEFAULT ('MANUAL'),
    [Observaciones] VARCHAR(500) NULL,
    [EsVigente] BIT NOT NULL DEFAULT ((1)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [Estatus] VARCHAR(20) NOT NULL DEFAULT ('VIGENTE'),
    [UsuarioCreacionID] INT NULL,
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [UsuarioModificacionID] INT NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioCancelacionID] INT NULL,
    [FechaCancelacion] DATETIME2 NULL,
    [MotivoCancelacion] VARCHAR(500) NULL,
    CONSTRAINT [PK_Finanzas_SaldosBancarios] PRIMARY KEY ([SaldoBancarioID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Global_Cat_Bancos]
-- ============================================================
CREATE TABLE [dbo].[Global_Cat_Bancos] (
    [BancoID] INT NOT NULL,
    [CodigoBanco] VARCHAR(10) NOT NULL,
    [NombreBanco] VARCHAR(100) NOT NULL,
    [NombreCorto] VARCHAR(50) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Global_Cat_Bancos] PRIMARY KEY ([BancoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Global_Cat_FormaPagoSAT]
-- ============================================================
CREATE TABLE [dbo].[Global_Cat_FormaPagoSAT] (
    [FormaPagoID] INT NOT NULL,
    [Clave] VARCHAR(5) NOT NULL,
    [Descripcion] VARCHAR(150) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Global_Cat_FormaPagoSAT] PRIMARY KEY ([FormaPagoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Inventario_Almacenes]
-- ============================================================
CREATE TABLE [dbo].[Inventario_Almacenes] (
    [AlmacenID] INT NOT NULL,
    [EmpresaID] INT NULL,
    [SucursalID] INT NOT NULL,
    [CodigoAlmacen] VARCHAR(20) NOT NULL,
    [NombreAlmacen] VARCHAR(120) NOT NULL,
    [TipoAlmacen] VARCHAR(20) NOT NULL,
    [PermiteCompras] BIT NOT NULL DEFAULT ((1)),
    [PermiteVentas] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Inventario_Almacenes] PRIMARY KEY ([AlmacenID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Inventario_Existencias]
-- ============================================================
CREATE TABLE [dbo].[Inventario_Existencias] (
    [ExistenciaID] BIGINT NOT NULL,
    [EmpresaID] INT NULL,
    [SucursalID] INT NOT NULL,
    [AlmacenID] INT NOT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [ExistenciaActual] DECIMAL(18,6) NOT NULL DEFAULT ((0)),
    [CostoPromedio] DECIMAL(18,6) NOT NULL DEFAULT ((0)),
    [UltimaFechaMovimiento] DATETIME2 NULL,
    [UltimoMovimientoDetalleID] BIGINT NULL,
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Inventario_Existencias] PRIMARY KEY ([ExistenciaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Inventario_Movimientos]
-- ============================================================
CREATE TABLE [dbo].[Inventario_Movimientos] (
    [MovimientoID] BIGINT NOT NULL,
    [TipoMovimientoID] TINYINT NOT NULL,
    [EmpresaID] INT NULL,
    [SucursalID] INT NOT NULL,
    [AlmacenID] INT NOT NULL,
    [FechaMovimiento] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [ReferenciaTipo] VARCHAR(30) NOT NULL,
    [ReferenciaID] BIGINT NULL,
    [FolioReferencia] VARCHAR(50) NULL,
    [Observaciones] VARCHAR(1000) NULL,
    [UsuarioID] INT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Inventario_Movimientos] PRIMARY KEY ([MovimientoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Inventario_MovimientosDetalle]
-- ============================================================
CREATE TABLE [dbo].[Inventario_MovimientosDetalle] (
    [MovimientoDetalleID] BIGINT NOT NULL,
    [MovimientoID] BIGINT NOT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [Cantidad] DECIMAL(18,6) NOT NULL,
    [CostoUnitario] DECIMAL(18,6) NOT NULL DEFAULT ((0)),
    [Importe] DECIMAL(37,12) NULL,
    [Lote] VARCHAR(50) NULL,
    [FechaCaducidad] DATE NULL,
    [ReferenciaDetalleTipo] VARCHAR(30) NULL,
    [ReferenciaDetalleID] BIGINT NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Inventario_MovimientosDetalle] PRIMARY KEY ([MovimientoDetalleID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Inventario_TipoMovimiento]
-- ============================================================
CREATE TABLE [dbo].[Inventario_TipoMovimiento] (
    [TipoMovimientoID] TINYINT NOT NULL,
    [Codigo] VARCHAR(30) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [Naturaleza] CHAR(1) NOT NULL,
    [AfectaCostoPromedio] BIT NOT NULL DEFAULT ((1)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Inventario_TipoMovimiento] PRIMARY KEY ([TipoMovimientoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Inventarios_SinAsignar]
-- ============================================================
CREATE TABLE [dbo].[Inventarios_SinAsignar] (
    [ID] INT NOT NULL,
    [RegistroID] VARCHAR(50) NOT NULL,
    [ServerID] VARCHAR(50) NULL,
    [ServerName] VARCHAR(100) NULL,
    [SucursalID] VARCHAR(100) NULL,
    [SucursalNombre] VARCHAR(100) NULL,
    [AlmacenID] VARCHAR(50) NULL,
    [AlmacenNombre] VARCHAR(100) NULL,
    [FolioInventario] VARCHAR(100) NULL,
    [TotalDiferencias] INT NULL DEFAULT ((0)),
    [ValorDiferencias] DECIMAL(18,2) NULL DEFAULT ((0)),
    [FechaDeteccion] DATETIME2 NULL DEFAULT (getutcdate()),
    [Estado] VARCHAR(50) NULL DEFAULT ('PENDIENTE_CONFIGURACION'),
    [Notificado] BIT NULL DEFAULT ((0)),
    CONSTRAINT [PK_Inventarios_SinAsignar] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operaciones_Tablaje_Auditoria]
-- ============================================================
CREATE TABLE [dbo].[Operaciones_Tablaje_Auditoria] (
    [AuditoriaID] BIGINT NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [UnidadNegocioID] UNIQUEIDENTIFIER NULL,
    [EntidadTipo] NVARCHAR(50) NOT NULL,
    [EntidadID] UNIQUEIDENTIFIER NOT NULL,
    [EntidadFolio] NVARCHAR(100) NULL,
    [Accion] NVARCHAR(100) NOT NULL,
    [UsuarioID] UNIQUEIDENTIFIER NOT NULL,
    [UsuarioNombre] NVARCHAR(200) NULL,
    [DireccionIP] NVARCHAR(50) NULL,
    [ValoresAnterioresJSON] NVARCHAR(MAX) NULL,
    [ValoresNuevosJSON] NVARCHAR(MAX) NULL,
    [CamposModificados] NVARCHAR(MAX) NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Modulo] NVARCHAR(50) NULL DEFAULT ('TABLAJERIA'),
    [FechaOperacionMexico] DATE NOT NULL,
    [FechaHoraUTC] DATETIME2 NOT NULL DEFAULT (sysutcdatetime()),
    CONSTRAINT [PK_Operaciones_Tablaje_Auditoria] PRIMARY KEY ([AuditoriaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operaciones_Tablaje_Autorizaciones]
-- ============================================================
CREATE TABLE [dbo].[Operaciones_Tablaje_Autorizaciones] (
    [AutorizacionID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [UnidadNegocioID] UNIQUEIDENTIFIER NULL,
    [TipoAutorizacion] NVARCHAR(100) NOT NULL,
    [EntidadTipo] NVARCHAR(50) NOT NULL,
    [EntidadID] UNIQUEIDENTIFIER NOT NULL,
    [EntidadFolio] NVARCHAR(100) NULL,
    [SolicitanteID] UNIQUEIDENTIFIER NOT NULL,
    [FechaSolicitudUTC] DATETIME2 NOT NULL DEFAULT (sysutcdatetime()),
    [MotivoSolicitud] NVARCHAR(1000) NOT NULL,
    [DatosSolicitudJSON] NVARCHAR(MAX) NULL,
    [Estatus] NVARCHAR(50) NOT NULL DEFAULT ('PENDIENTE'),
    [AutorizadorID] UNIQUEIDENTIFIER NULL,
    [FechaResolucionUTC] DATETIME2 NULL,
    [Comentarios] NVARCHAR(1000) NULL,
    [NivelEscalamiento] INT NOT NULL DEFAULT ((1)),
    [FechaExpiracion] DATETIME2 NULL,
    [FechaOperacionMexico] DATE NOT NULL,
    CONSTRAINT [PK_Operaciones_Tablaje_Autorizaciones] PRIMARY KEY ([AutorizacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operaciones_Tablaje_Costos]
-- ============================================================
CREATE TABLE [dbo].[Operaciones_Tablaje_Costos] (
    [CostoID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [OrdenID] UNIQUEIDENTIFIER NOT NULL,
    [OrdenDetalleID] UNIQUEIDENTIFIER NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [FechaOperacionMexico] DATE NOT NULL,
    [ProductoID] INT NULL,
    [ProductoCodigo] NVARCHAR(50) NULL,
    [ProductoNombre] NVARCHAR(200) NULL,
    [ReglaCosteo] NVARCHAR(50) NOT NULL,
    [CostoInsumoBase] DECIMAL(18,4) NULL,
    [PorcentajeAsignado] DECIMAL(5,2) NULL,
    [CostoAsignado] DECIMAL(18,4) NOT NULL,
    [CantidadProducida] DECIMAL(18,4) NULL,
    [CostoUnitario] DECIMAL(18,4) NULL,
    [MonedaID] INT NOT NULL DEFAULT ((1)),
    [TipoCambio] DECIMAL(18,6) NULL DEFAULT ((1)),
    [EsCostoFinal] BIT NOT NULL DEFAULT ((0)),
    [FechaCalculoUTC] DATETIME2 NOT NULL DEFAULT (sysutcdatetime()),
    [UsuarioCalculoID] UNIQUEIDENTIFIER NULL,
    CONSTRAINT [PK_Operaciones_Tablaje_Costos] PRIMARY KEY ([CostoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operaciones_Tablaje_Documentos]
-- ============================================================
CREATE TABLE [dbo].[Operaciones_Tablaje_Documentos] (
    [DocumentoID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [EntidadTipo] NVARCHAR(50) NOT NULL,
    [EntidadID] UNIQUEIDENTIFIER NOT NULL,
    [TipoDocumento] NVARCHAR(50) NOT NULL,
    [NombreArchivo] NVARCHAR(255) NOT NULL,
    [Extension] NVARCHAR(10) NULL,
    [TamanoBytes] BIGINT NULL,
    [RutaAlmacenamiento] NVARCHAR(500) NULL,
    [URLPublica] NVARCHAR(500) NULL,
    [ContenidoBase64] NVARCHAR(MAX) NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [EsEvidencia] BIT NOT NULL DEFAULT ((0)),
    [FechaSubidaUTC] DATETIME2 NOT NULL DEFAULT (sysutcdatetime()),
    [UsuarioSubidaID] UNIQUEIDENTIFIER NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Operaciones_Tablaje_Documentos] PRIMARY KEY ([DocumentoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operaciones_Tablaje_EventosContables]
-- ============================================================
CREATE TABLE [dbo].[Operaciones_Tablaje_EventosContables] (
    [EventoContableID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [UnidadNegocioID] UNIQUEIDENTIFIER NULL,
    [FechaOperacionMexico] DATE NOT NULL,
    [OrdenID] UNIQUEIDENTIFIER NOT NULL,
    [OrdenFolio] NVARCHAR(50) NULL,
    [TipoEvento] NVARCHAR(100) NOT NULL,
    [ProductoID] INT NULL,
    [ProductoCodigo] NVARCHAR(50) NULL,
    [ProductoNombre] NVARCHAR(200) NULL,
    [Cantidad] DECIMAL(18,4) NULL,
    [UnidadID] INT NULL,
    [Importe] DECIMAL(18,4) NOT NULL,
    [MonedaID] INT NOT NULL DEFAULT ((1)),
    [TipoCambio] DECIMAL(18,6) NULL DEFAULT ((1)),
    [ImporteMXN] DECIMAL(18,4) NULL,
    [CuentaCargoSugerida] NVARCHAR(50) NULL,
    [CuentaAbonoSugerida] NVARCHAR(50) NULL,
    [CentroCostoID] INT NULL,
    [CentroCostoCodigo] NVARCHAR(50) NULL,
    [EstatusContable] NVARCHAR(50) NOT NULL DEFAULT ('PENDIENTE'),
    [PolizaID] NVARCHAR(100) NULL,
    [NumeroPoliza] NVARCHAR(50) NULL,
    [FechaContabilizacion] DATE NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [FechaCreacionUTC] DATETIME2 NOT NULL DEFAULT (sysutcdatetime()),
    [FechaProcesoUTC] DATETIME2 NULL,
    [UsuarioProcesoID] UNIQUEIDENTIFIER NULL,
    [MensajeError] NVARCHAR(500) NULL,
    CONSTRAINT [PK_Operaciones_Tablaje_EventosContables] PRIMARY KEY ([EventoContableID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operaciones_Tablaje_Mermas]
-- ============================================================
CREATE TABLE [dbo].[Operaciones_Tablaje_Mermas] (
    [MermaID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [OrdenID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [UnidadNegocioID] UNIQUEIDENTIFIER NULL,
    [FechaOperacionMexico] DATE NOT NULL,
    [TipoMerma] NVARCHAR(50) NOT NULL,
    [Descripcion] NVARCHAR(200) NULL,
    [CantidadKg] DECIMAL(18,4) NOT NULL,
    [PorcentajeSobreInsumo] DECIMAL(5,2) NULL,
    [MermaEsperadaKg] DECIMAL(18,4) NULL,
    [MermaEsperadaPorcentaje] DECIMAL(5,2) NULL,
    [DesviacionKg] DECIMAL(18,4) NULL,
    [DentroTolerancia] BIT NOT NULL DEFAULT ((1)),
    [CostoMerma] DECIMAL(18,4) NULL,
    [EsRecuperable] BIT NOT NULL DEFAULT ((0)),
    [RequiereAutorizacion] BIT NOT NULL DEFAULT ((0)),
    [AutorizadoPor] UNIQUEIDENTIFIER NULL,
    [FechaAutorizacion] DATETIME2 NULL,
    [Observaciones] NVARCHAR(500) NULL,
    [FechaRegistroUTC] DATETIME2 NOT NULL DEFAULT (sysutcdatetime()),
    [UsuarioRegistroID] UNIQUEIDENTIFIER NULL,
    CONSTRAINT [PK_Operaciones_Tablaje_Mermas] PRIMARY KEY ([MermaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operaciones_Tablaje_Ordenes]
-- ============================================================
CREATE TABLE [dbo].[Operaciones_Tablaje_Ordenes] (
    [OrdenID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [UnidadNegocioID] UNIQUEIDENTIFIER NULL,
    [SucursalID] INT NULL,
    [FolioOrden] NVARCHAR(50) NOT NULL,
    [PlantillaID] UNIQUEIDENTIFIER NULL,
    [PlantillaVersion] INT NOT NULL DEFAULT ((1)),
    [AlmacenOrigenID] INT NULL,
    [AlmacenDestinoID] INT NULL,
    [InsumoBaseID] INT NULL,
    [InsumoBaseCodigo] NVARCHAR(50) NULL,
    [InsumoBaseNombre] NVARCHAR(200) NULL,
    [LoteInsumo] NVARCHAR(100) NULL,
    [CantidadBasePlaneada] DECIMAL(18,4) NOT NULL,
    [UnidadBaseID] INT NULL,
    [CantidadBaseReal] DECIMAL(18,4) NULL,
    [PesoInicialKg] DECIMAL(18,4) NULL,
    [PesoFinalKg] DECIMAL(18,4) NULL,
    [RendimientoEsperadoPorcentaje] DECIMAL(5,2) NULL,
    [RendimientoRealPorcentaje] DECIMAL(5,2) NULL,
    [DesviacionRendimiento] DECIMAL(5,2) NULL,
    [MermaEsperadaPorcentaje] DECIMAL(5,2) NULL,
    [MermaRealPorcentaje] DECIMAL(5,2) NULL,
    [MermaRealKg] DECIMAL(18,4) NULL,
    [CostoInsumoBase] DECIMAL(18,4) NULL,
    [CostoTotalOrden] DECIMAL(18,4) NULL,
    [MonedaID] INT NULL DEFAULT ((1)),
    [EstatusOrden] NVARCHAR(50) NOT NULL DEFAULT ('BORRADOR'),
    [RequiereAutorizacion] BIT NOT NULL DEFAULT ((0)),
    [MotivoAutorizacion] NVARCHAR(500) NULL,
    [AutorizadoPor] UNIQUEIDENTIFIER NULL,
    [FechaAutorizacion] DATETIME2 NULL,
    [FechaOperacionMexico] DATE NOT NULL,
    [FechaProgramada] DATE NULL,
    [FechaInicioEjecucion] DATETIME2 NULL,
    [FechaFinEjecucion] DATETIME2 NULL,
    [FechaCierre] DATETIME2 NULL,
    [ResponsableID] UNIQUEIDENTIFIER NULL,
    [EjecutorID] UNIQUEIDENTIFIER NULL,
    [SupervisorID] UNIQUEIDENTIFIER NULL,
    [OrigenOrden] NVARCHAR(50) NOT NULL DEFAULT ('CAPTURA_DIRECTA'),
    [IDLegacyOrden] NVARCHAR(100) NULL,
    [AfectaInventario] BIT NOT NULL DEFAULT ((1)),
    [MovimientoInventarioGenerado] BIT NOT NULL DEFAULT ((0)),
    [Observaciones] NVARCHAR(1000) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAltaUTC] DATETIME2 NOT NULL DEFAULT (sysutcdatetime()),
    [FechaModificacionUTC] DATETIME2 NULL,
    [UsuarioAltaID] UNIQUEIDENTIFIER NULL,
    [UsuarioModificacionID] UNIQUEIDENTIFIER NULL,
    CONSTRAINT [PK_Operaciones_Tablaje_Ordenes] PRIMARY KEY ([OrdenID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operaciones_Tablaje_OrdenesDetalle]
-- ============================================================
CREATE TABLE [dbo].[Operaciones_Tablaje_OrdenesDetalle] (
    [OrdenDetalleID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [OrdenID] UNIQUEIDENTIFIER NOT NULL,
    [PlantillaDetalleID] UNIQUEIDENTIFIER NULL,
    [ProductoDerivadoID] INT NULL,
    [ProductoDerivadoCodigo] NVARCHAR(50) NULL,
    [ProductoDerivadoNombre] NVARCHAR(200) NOT NULL,
    [TipoDerivado] NVARCHAR(50) NOT NULL,
    [CantidadEsperada] DECIMAL(18,4) NULL,
    [PorcentajeEsperado] DECIMAL(5,2) NULL,
    [CantidadReal] DECIMAL(18,4) NULL,
    [PesoRealKg] DECIMAL(18,4) NULL,
    [PorcentajeReal] DECIMAL(5,2) NULL,
    [DesviacionCantidad] DECIMAL(18,4) NULL,
    [DesviacionPorcentaje] DECIMAL(5,2) NULL,
    [CostoUnitario] DECIMAL(18,4) NULL,
    [CostoTotal] DECIMAL(18,4) NULL,
    [PorcentajeCostoAsignado] DECIMAL(5,2) NULL,
    [UnidadID] INT NULL,
    [UnidadCodigo] NVARCHAR(20) NULL,
    [GeneraMovimiento] BIT NOT NULL DEFAULT ((1)),
    [MovimientoGenerado] BIT NOT NULL DEFAULT ((0)),
    [AlmacenDestinoID] INT NULL,
    [LoteGenerado] NVARCHAR(100) NULL,
    [Observaciones] NVARCHAR(500) NULL,
    [FechaCaptura] DATETIME2 NULL,
    [UsuarioCapturaID] UNIQUEIDENTIFIER NULL,
    CONSTRAINT [PK_Operaciones_Tablaje_OrdenesDetalle] PRIMARY KEY ([OrdenDetalleID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operaciones_Tablaje_Plantillas]
-- ============================================================
CREATE TABLE [dbo].[Operaciones_Tablaje_Plantillas] (
    [PlantillaID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [UnidadNegocioID] UNIQUEIDENTIFIER NULL,
    [SucursalID] INT NULL,
    [AlmacenOrigenID] INT NULL,
    [AlmacenDestinoID] INT NULL,
    [CodigoPlantilla] NVARCHAR(50) NOT NULL,
    [NombrePlantilla] NVARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [TipoTransformacion] NVARCHAR(50) NULL,
    [InsumoBaseID] INT NULL,
    [InsumoBaseCodigo] NVARCHAR(50) NULL,
    [InsumoBaseNombre] NVARCHAR(200) NULL,
    [UnidadBaseID] INT NULL,
    [UnidadBaseCodigo] NVARCHAR(20) NULL,
    [CantidadBaseEstandar] DECIMAL(18,4) NOT NULL DEFAULT ((1)),
    [RendimientoEsperadoPorcentaje] DECIMAL(5,2) NULL,
    [MermaEsperadaPorcentaje] DECIMAL(5,2) NULL,
    [ToleranciaRendimiento] DECIMAL(5,2) NULL DEFAULT ((5.00)),
    [ReglaCosteo] NVARCHAR(50) NULL DEFAULT ('PROPORCIONAL'),
    [CostoBaseReferencia] DECIMAL(18,4) NULL,
    [MonedaID] INT NULL DEFAULT ((1)),
    [OrigenPlantilla] NVARCHAR(50) NOT NULL DEFAULT ('CAPTURA_DIRECTA_EDARSAHUB'),
    [SistemaOrigen] NVARCHAR(50) NULL,
    [ServidorOrigenID] NVARCHAR(100) NULL,
    [BaseDatosOrigen] NVARCHAR(100) NULL,
    [IDLegacyPlantilla] NVARCHAR(100) NULL,
    [HashOrigen] NVARCHAR(64) NULL,
    [VersionActual] INT NOT NULL DEFAULT ((1)),
    [PlantillaPadreID] UNIQUEIDENTIFIER NULL,
    [Estatus] NVARCHAR(50) NOT NULL DEFAULT ('BORRADOR'),
    [RequiereAutorizacion] BIT NOT NULL DEFAULT ((0)),
    [AutorizadoPor] UNIQUEIDENTIFIER NULL,
    [FechaAutorizacion] DATETIME2 NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAltaUTC] DATETIME2 NOT NULL DEFAULT (sysutcdatetime()),
    [FechaModificacionUTC] DATETIME2 NULL,
    [FechaSincronizacionUTC] DATETIME2 NULL,
    [FechaOperacionMexico] DATE NOT NULL,
    [UsuarioAltaID] UNIQUEIDENTIFIER NULL,
    [UsuarioModificacionID] UNIQUEIDENTIFIER NULL,
    CONSTRAINT [PK_Operaciones_Tablaje_Plantillas] PRIMARY KEY ([PlantillaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operaciones_Tablaje_PlantillasDetalle]
-- ============================================================
CREATE TABLE [dbo].[Operaciones_Tablaje_PlantillasDetalle] (
    [PlantillaDetalleID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [PlantillaID] UNIQUEIDENTIFIER NOT NULL,
    [ProductoDerivadoID] INT NULL,
    [ProductoDerivadoCodigo] NVARCHAR(50) NULL,
    [ProductoDerivadoNombre] NVARCHAR(200) NOT NULL,
    [TipoDerivado] NVARCHAR(50) NOT NULL DEFAULT ('PRINCIPAL'),
    [UnidadDerivadoID] INT NULL,
    [UnidadDerivadoCodigo] NVARCHAR(20) NULL,
    [CantidadEsperada] DECIMAL(18,4) NOT NULL,
    [PorcentajeRendimientoEsperado] DECIMAL(5,2) NULL,
    [PorcentajeCostoAsignado] DECIMAL(5,2) NULL,
    [CostoUnitarioFijo] DECIMAL(18,4) NULL,
    [EsMerma] BIT NOT NULL DEFAULT ((0)),
    [EsSubproducto] BIT NOT NULL DEFAULT ((0)),
    [EsProductoVendible] BIT NOT NULL DEFAULT ((1)),
    [EsInventariable] BIT NOT NULL DEFAULT ((1)),
    [GeneraMovimientoInventario] BIT NOT NULL DEFAULT ((1)),
    [OrdenVisual] INT NOT NULL DEFAULT ((0)),
    [Observaciones] NVARCHAR(500) NULL,
    [IDLegacyDetalle] NVARCHAR(100) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAltaUTC] DATETIME2 NOT NULL DEFAULT (sysutcdatetime()),
    [FechaModificacionUTC] DATETIME2 NULL,
    CONSTRAINT [PK_Operaciones_Tablaje_PlantillasDetalle] PRIMARY KEY ([PlantillaDetalleID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operaciones_Tablaje_PlantillasVersiones]
-- ============================================================
CREATE TABLE [dbo].[Operaciones_Tablaje_PlantillasVersiones] (
    [VersionID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [PlantillaID] UNIQUEIDENTIFIER NOT NULL,
    [NumeroVersion] INT NOT NULL,
    [DatosPlantillaJSON] NVARCHAR(MAX) NULL,
    [DatosDetalleJSON] NVARCHAR(MAX) NULL,
    [HashVersion] NVARCHAR(64) NULL,
    [MotivoVersion] NVARCHAR(500) NULL,
    [TipoCambio] NVARCHAR(50) NULL,
    [EsVersionActiva] BIT NOT NULL DEFAULT ((0)),
    [FechaVersionUTC] DATETIME2 NOT NULL DEFAULT (sysutcdatetime()),
    [UsuarioVersionID] UNIQUEIDENTIFIER NULL,
    CONSTRAINT [PK_Operaciones_Tablaje_PlantillasVersiones] PRIMARY KEY ([VersionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operaciones_Tablaje_Rendimientos]
-- ============================================================
CREATE TABLE [dbo].[Operaciones_Tablaje_Rendimientos] (
    [RendimientoID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [OrdenID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [UnidadNegocioID] UNIQUEIDENTIFIER NULL,
    [FechaOperacionMexico] DATE NOT NULL,
    [PlantillaID] UNIQUEIDENTIFIER NULL,
    [NombrePlantilla] NVARCHAR(200) NULL,
    [InsumoBaseID] INT NULL,
    [InsumoBaseNombre] NVARCHAR(200) NULL,
    [CantidadInsumoConsumido] DECIMAL(18,4) NOT NULL,
    [RendimientoEsperadoPorcentaje] DECIMAL(5,2) NULL,
    [RendimientoRealPorcentaje] DECIMAL(5,2) NOT NULL,
    [DesviacionPorcentaje] DECIMAL(5,2) NULL,
    [ClasificacionRendimiento] NVARCHAR(50) NULL,
    [DentroTolerancia] BIT NOT NULL DEFAULT ((1)),
    [CostoInsumo] DECIMAL(18,4) NULL,
    [CostoDerivados] DECIMAL(18,4) NULL,
    [CostoPerdido] DECIMAL(18,4) NULL,
    [FechaRegistroUTC] DATETIME2 NOT NULL DEFAULT (sysutcdatetime()),
    CONSTRAINT [PK_Operaciones_Tablaje_Rendimientos] PRIMARY KEY ([RendimientoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operaciones_Tablaje_SyncErrores]
-- ============================================================
CREATE TABLE [dbo].[Operaciones_Tablaje_SyncErrores] (
    [ErrorID] BIGINT NOT NULL,
    [SyncLogID] BIGINT NOT NULL,
    [TipoEntidad] NVARCHAR(50) NOT NULL,
    [IDLegacy] NVARCHAR(100) NULL,
    [DatosRegistroJSON] NVARCHAR(MAX) NULL,
    [TipoError] NVARCHAR(100) NOT NULL,
    [MensajeError] NVARCHAR(MAX) NOT NULL,
    [StackTrace] NVARCHAR(MAX) NULL,
    [Resuelto] BIT NOT NULL DEFAULT ((0)),
    [FechaResolucion] DATETIME2 NULL,
    [ResolucionNotas] NVARCHAR(500) NULL,
    [FechaErrorUTC] DATETIME2 NOT NULL DEFAULT (sysutcdatetime()),
    CONSTRAINT [PK_Operaciones_Tablaje_SyncErrores] PRIMARY KEY ([ErrorID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operaciones_Tablaje_SyncLog]
-- ============================================================
CREATE TABLE [dbo].[Operaciones_Tablaje_SyncLog] (
    [SyncLogID] BIGINT NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NULL,
    [UnidadNegocioID] UNIQUEIDENTIFIER NULL,
    [ServidorID] NVARCHAR(100) NOT NULL,
    [ServidorNombre] NVARCHAR(200) NULL,
    [SistemaOrigen] NVARCHAR(50) NULL,
    [BaseDatosOrigen] NVARCHAR(100) NULL,
    [TipoEntidad] NVARCHAR(50) NOT NULL,
    [Operacion] NVARCHAR(50) NOT NULL,
    [FechaInicioUTC] DATETIME2 NOT NULL,
    [FechaFinUTC] DATETIME2 NULL,
    [DuracionSegundos] INT NULL,
    [RegistrosLeidos] INT NOT NULL DEFAULT ((0)),
    [RegistrosCreados] INT NOT NULL DEFAULT ((0)),
    [RegistrosActualizados] INT NOT NULL DEFAULT ((0)),
    [RegistrosSinCambios] INT NOT NULL DEFAULT ((0)),
    [RegistrosError] INT NOT NULL DEFAULT ((0)),
    [Estado] NVARCHAR(50) NOT NULL DEFAULT ('EN_PROCESO'),
    [MensajeError] NVARCHAR(MAX) NULL,
    [DetallesJSON] NVARCHAR(MAX) NULL,
    [EjecutadoPor] UNIQUEIDENTIFIER NULL,
    CONSTRAINT [PK_Operaciones_Tablaje_SyncLog] PRIMARY KEY ([SyncLogID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operativo_AuditoriasProgramadas]
-- ============================================================
CREATE TABLE [dbo].[Operativo_AuditoriasProgramadas] (
    [ID] INT NOT NULL,
    [AuditoriaID] VARCHAR(50) NOT NULL,
    [Nombre] VARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [ServerID] VARCHAR(50) NULL,
    [SucursalID] VARCHAR(100) NULL,
    [AlmacenID] VARCHAR(50) NULL,
    [Frecuencia] VARCHAR(50) NOT NULL,
    [DiaSemana] INT NULL,
    [DiaMes] INT NULL,
    [HoraEjecucion] VARCHAR(10) NULL,
    [Timezone] VARCHAR(50) NULL DEFAULT ('America/Mexico_City'),
    [ProximaEjecucion] DATETIME2 NULL,
    [UltimaEjecucion] DATETIME2 NULL,
    [Estado] VARCHAR(50) NULL DEFAULT ('ACTIVA'),
    [UsuarioCreadorID] VARCHAR(50) NULL,
    [FechaCreacion] DATETIME2 NULL DEFAULT (getutcdate()),
    [FechaActualizacion] DATETIME2 NULL,
    [ConfiguracionJSON] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_Operativo_AuditoriasProgramadas] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operativo_BitacoraCompras]
-- ============================================================
CREATE TABLE [dbo].[Operativo_BitacoraCompras] (
    [ID] INT NOT NULL,
    [BitacoraID] VARCHAR(50) NOT NULL,
    [AutomatizacionID] VARCHAR(50) NULL,
    [Accion] VARCHAR(50) NOT NULL,
    [UsuarioID] VARCHAR(50) NULL,
    [UsuarioNombre] VARCHAR(200) NULL,
    [Detalle] NVARCHAR(MAX) NULL,
    [EstadoAnterior] VARCHAR(50) NULL,
    [EstadoNuevo] VARCHAR(50) NULL,
    [Fecha] DATETIME2 NULL DEFAULT (getutcdate()),
    [MetadatosJSON] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_Operativo_BitacoraCompras] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operativo_CargosResponsabilidad]
-- ============================================================
CREATE TABLE [dbo].[Operativo_CargosResponsabilidad] (
    [ID] INT NOT NULL,
    [CargoID] VARCHAR(50) NOT NULL,
    [ResponsabilidadID] VARCHAR(50) NOT NULL,
    [WorkflowID] VARCHAR(50) NOT NULL,
    [SucursalID] VARCHAR(100) NULL,
    [ResponsableID] VARCHAR(50) NULL,
    [ResponsableNombre] VARCHAR(200) NULL,
    [MontoPropuesto] DECIMAL(18,2) NOT NULL,
    [MontoFinal] DECIMAL(18,2) NULL,
    [EstatusCargo] VARCHAR(50) NULL DEFAULT ('PROPUESTO'),
    [FechaPropuesta] DATETIME2 NULL DEFAULT (getutcdate()),
    [FechaAprobacion] DATETIME2 NULL,
    [AprobadoPorID] VARCHAR(50) NULL,
    [FechaRechazo] DATETIME2 NULL,
    [RechazadoPorID] VARCHAR(50) NULL,
    [MotivoRechazo] NVARCHAR(MAX) NULL,
    [FechaDisputa] DATETIME2 NULL,
    [DisputadoPorID] VARCHAR(50) NULL,
    [MotivoDisputa] NVARCHAR(MAX) NULL,
    [FechaResolucion] DATETIME2 NULL,
    [ResueltoPorID] VARCHAR(50) NULL,
    [Comentarios] NVARCHAR(MAX) NULL,
    [MetadatosJSON] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_Operativo_CargosResponsabilidad] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operativo_DocumentosGenerados]
-- ============================================================
CREATE TABLE [dbo].[Operativo_DocumentosGenerados] (
    [ID] INT NOT NULL,
    [DocumentoID] VARCHAR(50) NOT NULL,
    [WorkflowID] VARCHAR(50) NULL,
    [TipoDocumento] VARCHAR(50) NOT NULL,
    [NombreArchivo] VARCHAR(500) NULL,
    [URLDescarga] VARCHAR(1000) NULL,
    [Formato] VARCHAR(20) NULL DEFAULT ('PDF'),
    [TamanioBytes] BIGINT NULL,
    [UsuarioGeneradorID] VARCHAR(50) NULL,
    [Estado] VARCHAR(50) NULL DEFAULT ('GENERADO'),
    [FechaGeneracion] DATETIME2 NULL DEFAULT (getutcdate()),
    [FechaExpiracion] DATETIME2 NULL,
    [MetadatosJSON] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_Operativo_DocumentosGenerados] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operativo_HistorialAsignaciones]
-- ============================================================
CREATE TABLE [dbo].[Operativo_HistorialAsignaciones] (
    [ID] INT NOT NULL,
    [HistorialID] VARCHAR(50) NOT NULL,
    [TareaID] VARCHAR(50) NOT NULL,
    [WorkflowID] VARCHAR(50) NULL,
    [UsuarioAnteriorID] VARCHAR(50) NULL,
    [UsuarioAnteriorNombre] VARCHAR(200) NULL,
    [UsuarioNuevoID] VARCHAR(50) NULL,
    [UsuarioNuevoNombre] VARCHAR(200) NULL,
    [AsignadoPorID] VARCHAR(50) NULL,
    [AsignadoPorNombre] VARCHAR(200) NULL,
    [TipoAsignacion] VARCHAR(50) NULL DEFAULT ('MANUAL'),
    [Motivo] NVARCHAR(MAX) NULL,
    [FechaAsignacion] DATETIME2 NULL DEFAULT (getutcdate()),
    CONSTRAINT [PK_Operativo_HistorialAsignaciones] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operativo_HistorialCargos]
-- ============================================================
CREATE TABLE [dbo].[Operativo_HistorialCargos] (
    [ID] INT NOT NULL,
    [HistorialID] VARCHAR(50) NOT NULL,
    [CargoID] VARCHAR(50) NOT NULL,
    [Accion] VARCHAR(50) NOT NULL,
    [UsuarioID] VARCHAR(50) NOT NULL,
    [UsuarioNombre] VARCHAR(200) NULL,
    [Detalle] NVARCHAR(MAX) NULL,
    [EstadoAnterior] VARCHAR(50) NULL,
    [EstadoNuevo] VARCHAR(50) NULL,
    [Fecha] DATETIME2 NULL DEFAULT (getutcdate()),
    CONSTRAINT [PK_Operativo_HistorialCargos] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operativo_Notificaciones_Log]
-- ============================================================
CREATE TABLE [dbo].[Operativo_Notificaciones_Log] (
    [ID] INT NOT NULL,
    [NotificacionID] VARCHAR(50) NOT NULL,
    [TipoEvento] VARCHAR(50) NOT NULL,
    [WorkflowID] VARCHAR(50) NULL,
    [TareaID] VARCHAR(50) NULL,
    [Destinatario] VARCHAR(200) NULL,
    [DestinatarioEmail] VARCHAR(200) NULL,
    [Titulo] VARCHAR(500) NULL,
    [Mensaje] NVARCHAR(MAX) NULL,
    [Estado] VARCHAR(50) NULL DEFAULT ('PENDIENTE'),
    [Canal] VARCHAR(50) NULL DEFAULT ('EMAIL'),
    [FechaEnvio] DATETIME2 NULL DEFAULT (getutcdate()),
    [FechaLeido] DATETIME2 NULL,
    [ErrorMensaje] NVARCHAR(MAX) NULL,
    [MetadatosJSON] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_Operativo_Notificaciones_Log] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operativo_PedidosProcesados]
-- ============================================================
CREATE TABLE [dbo].[Operativo_PedidosProcesados] (
    [ID] INT NOT NULL,
    [PedidoID] VARCHAR(50) NOT NULL,
    [AutomatizacionID] VARCHAR(50) NOT NULL,
    [ServerID] VARCHAR(50) NULL,
    [SucursalID] VARCHAR(100) NULL,
    [FolioInventario] VARCHAR(100) NULL,
    [Estado] VARCHAR(50) NULL DEFAULT ('PROCESADO'),
    [CantidadItems] INT NULL DEFAULT ((0)),
    [MontoTotal] DECIMAL(18,2) NULL DEFAULT ((0)),
    [FechaProcesamiento] DATETIME2 NULL DEFAULT (getutcdate()),
    [DetalleJSON] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_Operativo_PedidosProcesados] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operativo_ResponsabilidadEconomica]
-- ============================================================
CREATE TABLE [dbo].[Operativo_ResponsabilidadEconomica] (
    [ID] INT NOT NULL,
    [ResponsabilidadID] VARCHAR(50) NOT NULL,
    [WorkflowID] VARCHAR(50) NOT NULL,
    [ServerID] VARCHAR(50) NULL,
    [SucursalID] VARCHAR(100) NULL,
    [SucursalNombre] VARCHAR(100) NULL,
    [ResponsableID] VARCHAR(50) NULL,
    [ResponsableNombre] VARCHAR(200) NULL,
    [MontoTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [MontoJustificado] DECIMAL(18,2) NULL DEFAULT ((0)),
    [MontoNoJustificado] DECIMAL(18,2) NULL DEFAULT ((0)),
    [Estado] VARCHAR(50) NULL DEFAULT ('PENDIENTE'),
    [ExcedeMinimo] BIT NULL DEFAULT ((0)),
    [UmbralMinimo] DECIMAL(18,2) NULL DEFAULT ((500)),
    [FechaCalculo] DATETIME2 NULL DEFAULT (getutcdate()),
    [FechaUltimaActualizacion] DATETIME2 NULL,
    [FechaAprobacion] DATETIME2 NULL,
    [AprobadoPorID] VARCHAR(50) NULL,
    [Comentarios] NVARCHAR(MAX) NULL,
    [MetadatosJSON] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_Operativo_ResponsabilidadEconomica] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Operativo_TareasCompras]
-- ============================================================
CREATE TABLE [dbo].[Operativo_TareasCompras] (
    [ID] INT NOT NULL,
    [TareaID] VARCHAR(50) NOT NULL,
    [AutomatizacionID] VARCHAR(50) NULL,
    [TipoTarea] VARCHAR(50) NOT NULL,
    [Titulo] VARCHAR(500) NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [ServerID] VARCHAR(50) NULL,
    [SucursalID] VARCHAR(100) NULL,
    [SucursalNombre] VARCHAR(100) NULL,
    [UsuarioAsignadoID] VARCHAR(50) NULL,
    [UsuarioAsignadoNombre] VARCHAR(200) NULL,
    [Estado] VARCHAR(50) NULL DEFAULT ('PENDIENTE'),
    [Prioridad] VARCHAR(20) NULL DEFAULT ('NORMAL'),
    [FechaCreacion] DATETIME2 NULL DEFAULT (getutcdate()),
    [FechaLimite] DATETIME2 NULL,
    [FechaCompletada] DATETIME2 NULL,
    [Resultado] NVARCHAR(MAX) NULL,
    [MetadatosJSON] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_Operativo_TareasCompras] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Producto_Catalogo]
-- ============================================================
CREATE TABLE [dbo].[Producto_Catalogo] (
    [ProductoID] INT NOT NULL,
    [CodigoProducto] VARCHAR(30) NOT NULL,
    [SKU] VARCHAR(50) NOT NULL,
    [ClaveAlterna] VARCHAR(50) NULL,
    [CodigoBarras] VARCHAR(100) NULL,
    [NombreProducto] VARCHAR(150) NOT NULL,
    [NombreCorto] VARCHAR(80) NULL,
    [Descripcion] VARCHAR(1000) NULL,
    [LineaProductoID] INT NULL,
    [MarcaProductoID] INT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [TipoProducto] VARCHAR(20) NOT NULL DEFAULT ('PRODUCTO'),
    [EsInventariable] BIT NOT NULL DEFAULT ((1)),
    [EsServicio] BIT NOT NULL DEFAULT ((0)),
    [PermiteVenta] BIT NOT NULL DEFAULT ((1)),
    [PermiteCompra] BIT NOT NULL DEFAULT ((1)),
    [PermiteVentaSinExistencia] BIT NOT NULL DEFAULT ((0)),
    [UnidadInventario] VARCHAR(30) NOT NULL DEFAULT ('PZA'),
    [UnidadVenta] VARCHAR(30) NOT NULL DEFAULT ('PZA'),
    [UnidadCompra] VARCHAR(30) NOT NULL DEFAULT ('PZA'),
    [PrecioVentaBase] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [PrecioCostoBase] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TasaImpuesto] DECIMAL(9,4) NOT NULL DEFAULT ((0)),
    [StockActual] DECIMAL(18,4) NOT NULL DEFAULT ((0)),
    [StockMinimo] DECIMAL(18,4) NOT NULL DEFAULT ((0)),
    [StockMaximo] DECIMAL(18,4) NULL,
    [PuntoReorden] DECIMAL(18,4) NULL,
    [PesoNeto] DECIMAL(18,4) NULL,
    [Volumen] DECIMAL(18,4) NULL,
    [ImagenURL] VARCHAR(500) NULL,
    [Observaciones] VARCHAR(1000) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_Producto_Catalogo] PRIMARY KEY ([ProductoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Producto_Equivalentes]
-- ============================================================
CREATE TABLE [dbo].[Producto_Equivalentes] (
    [ProductoEquivalenteID] BIGINT NOT NULL,
    [ProductoID] INT NOT NULL,
    [ProductoEquivalenteRefID] INT NOT NULL,
    [TipoEquivalencia] VARCHAR(20) NOT NULL DEFAULT ('TOTAL'),
    [FactorEquivalencia] DECIMAL(18,6) NOT NULL DEFAULT ((1)),
    [Observaciones] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Producto_Equivalentes] PRIMARY KEY ([ProductoEquivalenteID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Producto_Familias]
-- ============================================================
CREATE TABLE [dbo].[Producto_Familias] (
    [FamiliaProductoID] INT NOT NULL,
    [CodigoFamilia] VARCHAR(20) NOT NULL,
    [NombreFamilia] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Producto_Familias] PRIMARY KEY ([FamiliaProductoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Producto_Lineas]
-- ============================================================
CREATE TABLE [dbo].[Producto_Lineas] (
    [LineaProductoID] INT NOT NULL,
    [SubFamiliaProductoID] INT NOT NULL,
    [CodigoLinea] VARCHAR(20) NOT NULL,
    [NombreLinea] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Producto_Lineas] PRIMARY KEY ([LineaProductoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Producto_Marcas]
-- ============================================================
CREATE TABLE [dbo].[Producto_Marcas] (
    [MarcaProductoID] INT NOT NULL,
    [CodigoMarca] VARCHAR(20) NOT NULL,
    [NombreMarca] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Producto_Marcas] PRIMARY KEY ([MarcaProductoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Producto_Presentaciones]
-- ============================================================
CREATE TABLE [dbo].[Producto_Presentaciones] (
    [PresentacionProductoID] BIGINT NOT NULL,
    [ProductoID] INT NOT NULL,
    [CodigoPresentacion] VARCHAR(30) NOT NULL,
    [NombrePresentacion] VARCHAR(120) NOT NULL,
    [SKU_Presentacion] VARCHAR(50) NULL,
    [CodigoBarras] VARCHAR(100) NULL,
    [UnidadPresentacion] VARCHAR(30) NOT NULL,
    [FactorConversionInventario] DECIMAL(18,6) NOT NULL DEFAULT ((1)),
    [EsPresentacionVenta] BIT NOT NULL DEFAULT ((1)),
    [EsPresentacionCompra] BIT NOT NULL DEFAULT ((0)),
    [EsPresentacionInventario] BIT NOT NULL DEFAULT ((0)),
    [PrecioVenta] DECIMAL(18,2) NULL,
    [PrecioCosto] DECIMAL(18,2) NULL,
    [PesoNeto] DECIMAL(18,4) NULL,
    [Volumen] DECIMAL(18,4) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Producto_Presentaciones] PRIMARY KEY ([PresentacionProductoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Producto_SubFamilias]
-- ============================================================
CREATE TABLE [dbo].[Producto_SubFamilias] (
    [SubFamiliaProductoID] INT NOT NULL,
    [FamiliaProductoID] INT NOT NULL,
    [CodigoSubFamilia] VARCHAR(20) NOT NULL,
    [NombreSubFamilia] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Producto_SubFamilias] PRIMARY KEY ([SubFamiliaProductoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Producto_Sustitutos]
-- ============================================================
CREATE TABLE [dbo].[Producto_Sustitutos] (
    [ProductoSustitutoID] BIGINT NOT NULL,
    [ProductoID] INT NOT NULL,
    [ProductoSustitutoRefID] INT NOT NULL,
    [Prioridad] TINYINT NOT NULL DEFAULT ((1)),
    [Motivo] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Producto_Sustitutos] PRIMARY KEY ([ProductoSustitutoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Products]
-- ============================================================
CREATE TABLE [dbo].[Products] (
    [Id] INT NOT NULL,
    [CodigoProducto] NVARCHAR(50) NULL,
    [NombreProducto] NVARCHAR(200) NOT NULL,
    [Familia] NVARCHAR(100) NULL,
    [Subfamilia] NVARCHAR(100) NULL,
    [Casa] NVARCHAR(100) NULL,
    [PorcentajeAlcohol] DECIMAL(5,2) NULL,
    [URL_Imagen] NVARCHAR(500) NULL,
    [PrecioBase] DECIMAL(18,2) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Products] PRIMARY KEY ([Id])
);
GO

-- ============================================================
-- TABLA: [dbo].[propinas_tpv_config]
-- ============================================================
CREATE TABLE [dbo].[propinas_tpv_config] (
    [id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [alcance_tipo] VARCHAR(20) NOT NULL DEFAULT ('GLOBAL'),
    [alcance_server_id] VARCHAR(50) NULL,
    [alcance_empresa_id] VARCHAR(50) NULL,
    [alcance_sucursal_id] VARCHAR(50) NULL,
    [vigencia_inicio] DATETIME NOT NULL DEFAULT (getdate()),
    [vigencia_fin] DATETIME NULL,
    [activa] BIT NOT NULL DEFAULT ((1)),
    [porcentaje_comision] DECIMAL(5,4) NOT NULL DEFAULT ((0.0200)),
    [tolerancia_descuadre] DECIMAL(18,2) NOT NULL DEFAULT ((5.00)),
    [dias_para_cuadrar] INT NOT NULL DEFAULT ((1)),
    [soft_concepto_propinas] INT NOT NULL DEFAULT ((9)),
    [soft_conceptos_tarjeta] VARCHAR(50) NOT NULL DEFAULT ('10,11,12'),
    [soft_concepto_efectivo] INT NOT NULL DEFAULT ((2)),
    [created_at] DATETIME NOT NULL DEFAULT (getdate()),
    [created_by] VARCHAR(100) NULL,
    [updated_at] DATETIME NOT NULL DEFAULT (getdate()),
    [updated_by] VARCHAR(100) NULL,
    [motivo_cambio] VARCHAR(500) NULL,
    CONSTRAINT [PK_propinas_tpv_config] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[propinas_tpv_control]
-- ============================================================
CREATE TABLE [dbo].[propinas_tpv_control] (
    [id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [server_id] VARCHAR(50) NOT NULL,
    [sucursal_id] VARCHAR(50) NOT NULL,
    [folio_corte] VARCHAR(50) NOT NULL,
    [fecha_corte] DATE NOT NULL,
    [server_name] VARCHAR(100) NOT NULL,
    [system_type] VARCHAR(20) NOT NULL DEFAULT ('SoftRestaurant'),
    [sucursal_nombre] VARCHAR(100) NULL,
    [empresa_id] VARCHAR(50) NULL,
    [estacion_id] VARCHAR(50) NULL,
    [propinas_totales_corte] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [propinas_efectivo] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [propinas_tpv] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ventas_tarjeta] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ventas_totales] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ventas_efectivo] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [total_cheques] INT NOT NULL DEFAULT ((0)),
    [saldo_corte] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [corte_id_origen] VARCHAR(50) NULL,
    [turno_id_origen] VARCHAR(50) NULL,
    [tipo_dato] VARCHAR(20) NOT NULL DEFAULT ('EXACTO'),
    [metodo_calculo] VARCHAR(100) NULL,
    [confianza] DECIMAL(3,2) NOT NULL DEFAULT ((1.00)),
    [query_origen] VARCHAR(500) NULL,
    [advertencia] VARCHAR(500) NULL,
    [config_aplicada_id] UNIQUEIDENTIFIER NULL,
    [porcentaje_comision] DECIMAL(5,4) NOT NULL DEFAULT ((0.0200)),
    [comision_calculada] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [monto_a_pagar_meseros] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [pago_registrado] BIT NOT NULL DEFAULT ((0)),
    [pago_monto] DECIMAL(18,2) NULL,
    [pago_fecha] DATETIME NULL,
    [pago_metodo] VARCHAR(20) NULL,
    [pago_usuario_id] VARCHAR(50) NULL,
    [pago_usuario_email] VARCHAR(100) NULL,
    [pago_observaciones] VARCHAR(500) NULL,
    [cuadre_estado] VARCHAR(20) NOT NULL DEFAULT ('PENDIENTE'),
    [cuadre_diferencia] DECIMAL(18,2) NULL,
    [cuadre_fecha] DATETIME NULL,
    [cuadre_usuario_id] VARCHAR(50) NULL,
    [cuadre_usuario_email] VARCHAR(100) NULL,
    [cuadre_observaciones] VARCHAR(500) NULL,
    [fecha_sincronizacion] DATETIME NOT NULL DEFAULT (getdate()),
    [sincronizado_por] VARCHAR(100) NULL,
    [created_at] DATETIME NOT NULL DEFAULT (getdate()),
    [updated_at] DATETIME NOT NULL DEFAULT (getdate()),
    [version] INT NOT NULL DEFAULT ((1)),
    [UnidadNegocioID] UNIQUEIDENTIFIER NULL,
    [UnidadNegocioNombre] NVARCHAR(100) NULL,
    [SistemaOrigen] NVARCHAR(20) NULL,
    [BaseDatosOrigen] NVARCHAR(100) NULL,
    [TablaOrigen] NVARCHAR(100) NULL,
    [IdOrigen] NVARCHAR(100) NULL,
    [FolioOrigen] NVARCHAR(100) NULL,
    [HashOrigen] NVARCHAR(64) NULL,
    [EsDemo] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FormaPagoID] NVARCHAR(50) NULL,
    [FormaPagoNombre] NVARCHAR(100) NULL,
    [EsTarjeta] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_propinas_tpv_control] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[propinas_tpv_historial]
-- ============================================================
CREATE TABLE [dbo].[propinas_tpv_historial] (
    [id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [propina_id] UNIQUEIDENTIFIER NOT NULL,
    [accion] VARCHAR(50) NOT NULL,
    [campo_modificado] VARCHAR(100) NULL,
    [valor_anterior] VARCHAR(500) NULL,
    [valor_nuevo] VARCHAR(500) NULL,
    [estado_anterior] VARCHAR(20) NULL,
    [estado_nuevo] VARCHAR(20) NULL,
    [usuario_id] VARCHAR(50) NULL,
    [usuario_email] VARCHAR(100) NULL,
    [ip_origen] VARCHAR(50) NULL,
    [fecha] DATETIME NOT NULL DEFAULT (getdate()),
    [observaciones] VARCHAR(500) NULL,
    CONSTRAINT [PK_propinas_tpv_historial] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_Bancos]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_Bancos] (
    [BancoID] SMALLINT NOT NULL,
    [ClaveBanco] VARCHAR(10) NULL,
    [NombreBanco] VARCHAR(100) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Proveedor_Bancos] PRIMARY KEY ([BancoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_Catalogo]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_Catalogo] (
    [ProveedorID] INT NOT NULL,
    [CodigoProveedor] VARCHAR(20) NOT NULL,
    [RFC] VARCHAR(13) NOT NULL,
    [CURP] VARCHAR(18) NULL,
    [RazonSocial] VARCHAR(200) NOT NULL,
    [NombreComercial] VARCHAR(200) NULL,
    [TipoPersona] CHAR(1) NOT NULL,
    [RegimenFiscalID] SMALLINT NULL,
    [TipoProveedorID] SMALLINT NULL,
    [EstatusProveedorID] TINYINT NOT NULL,
    [DiasCredito] SMALLINT NOT NULL DEFAULT ((0)),
    [LimiteCredito] DECIMAL(18,2) NULL,
    [MonedaID] SMALLINT NOT NULL DEFAULT ((1)),
    [EmailPrincipal] VARCHAR(150) NULL,
    [TelefonoPrincipal] VARCHAR(25) NULL,
    [Ciudad] VARCHAR(100) NULL,
    [Estado] VARCHAR(100) NULL,
    [Pais] VARCHAR(60) NOT NULL DEFAULT ('MEXICO'),
    [CodigoPostal] VARCHAR(10) NULL,
    [PortalHabilitado] BIT NOT NULL DEFAULT ((1)),
    [RequiereOCParaFacturar] BIT NOT NULL DEFAULT ((1)),
    [RequiereXML] BIT NOT NULL DEFAULT ((1)),
    [RequierePDF] BIT NOT NULL DEFAULT ((1)),
    [ExpedienteCompleto] BIT NOT NULL DEFAULT ((0)),
    [EstatusSATID] TINYINT NOT NULL DEFAULT ((1)),
    [RiesgoID] TINYINT NOT NULL DEFAULT ((2)),
    [ScoreActual] DECIMAL(5,2) NULL,
    [FechaUltimaEvaluacion] DATE NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Proveedor_Catalogo] PRIMARY KEY ([ProveedorID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_Categorias]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_Categorias] (
    [ProveedorCategoriaID] BIGINT NOT NULL,
    [ProveedorID] INT NOT NULL,
    [CategoriaProveedorID] INT NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Proveedor_Categorias] PRIMARY KEY ([ProveedorCategoriaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_CategoriasCatalogo]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_CategoriasCatalogo] (
    [CategoriaProveedorID] INT NOT NULL,
    [NombreCategoria] VARCHAR(100) NOT NULL,
    [CategoriaPadreID] INT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Proveedor_CategoriasCatalogo] PRIMARY KEY ([CategoriaProveedorID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_Contactos]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_Contactos] (
    [ContactoID] INT NOT NULL,
    [ProveedorID] INT NOT NULL,
    [Nombre] VARCHAR(150) NOT NULL,
    [Apellidos] VARCHAR(150) NULL,
    [Puesto] VARCHAR(100) NULL,
    [Email] VARCHAR(150) NULL,
    [Telefono] VARCHAR(25) NULL,
    [Extension] VARCHAR(10) NULL,
    [Celular] VARCHAR(25) NULL,
    [TipoContactoID] TINYINT NOT NULL,
    [EsPrincipal] BIT NOT NULL DEFAULT ((0)),
    [RecibeOC] BIT NOT NULL DEFAULT ((0)),
    [RecibeFacturacion] BIT NOT NULL DEFAULT ((0)),
    [RecibePagos] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Proveedor_Contactos] PRIMARY KEY ([ContactoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_CuentasBancarias]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_CuentasBancarias] (
    [CuentaBancariaID] INT NOT NULL,
    [ProveedorID] INT NOT NULL,
    [BancoID] SMALLINT NOT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [TitularCuenta] VARCHAR(200) NOT NULL,
    [RFC_Titular] VARCHAR(13) NULL,
    [Cuenta] VARCHAR(30) NULL,
    [CLABE] VARCHAR(18) NULL,
    [ConvenioCIE] VARCHAR(20) NULL,
    [Sucursal] VARCHAR(100) NULL,
    [EsPrincipal] BIT NOT NULL DEFAULT ((0)),
    [Validada] BIT NOT NULL DEFAULT ((0)),
    [Activa] BIT NOT NULL DEFAULT ((1)),
    [FechaValidacion] DATETIME2 NULL,
    [Observaciones] VARCHAR(500) NULL,
    CONSTRAINT [PK_Proveedor_CuentasBancarias] PRIMARY KEY ([CuentaBancariaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_Documentos]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_Documentos] (
    [DocumentoID] BIGINT NOT NULL,
    [ProveedorID] INT NOT NULL,
    [TipoDocumentoID] SMALLINT NOT NULL,
    [NombreArchivo] VARCHAR(255) NOT NULL,
    [NombreOriginalArchivo] VARCHAR(255) NULL,
    [RutaArchivo] VARCHAR(500) NOT NULL,
    [ExtensionArchivo] VARCHAR(10) NULL,
    [TamanoBytes] BIGINT NULL,
    [FechaEmision] DATE NULL,
    [FechaVencimiento] DATE NULL,
    [Vigente] BIT NOT NULL DEFAULT ((1)),
    [Validado] BIT NOT NULL DEFAULT ((0)),
    [ObservacionesValidacion] VARCHAR(500) NULL,
    [FechaCarga] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaValidacion] DATETIME2 NULL,
    [UsuarioCarga] VARCHAR(100) NULL,
    [UsuarioValidacion] VARCHAR(100) NULL,
    [HashArchivo] VARCHAR(128) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Proveedor_Documentos] PRIMARY KEY ([DocumentoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_EstatusProveedor]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_EstatusProveedor] (
    [EstatusProveedorID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Proveedor_EstatusProveedor] PRIMARY KEY ([EstatusProveedorID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_EstatusSAT]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_EstatusSAT] (
    [EstatusSATID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Proveedor_EstatusSAT] PRIMARY KEY ([EstatusSATID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_EstatusSincronizacion]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_EstatusSincronizacion] (
    [EstatusSincronizacionID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Proveedor_EstatusSincronizacion] PRIMARY KEY ([EstatusSincronizacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_Evaluaciones]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_Evaluaciones] (
    [EvaluacionID] BIGINT NOT NULL,
    [ProveedorID] INT NOT NULL,
    [Periodo] CHAR(7) NOT NULL,
    [FechaEvaluacion] DATE NOT NULL,
    [ScoreCalidad] DECIMAL(5,2) NULL,
    [ScoreEntrega] DECIMAL(5,2) NULL,
    [ScoreServicio] DECIMAL(5,2) NULL,
    [ScorePrecio] DECIMAL(5,2) NULL,
    [ScoreDocumental] DECIMAL(5,2) NULL,
    [ScoreGlobal] DECIMAL(5,2) NULL,
    [Incidencias] INT NOT NULL DEFAULT ((0)),
    [Observaciones] VARCHAR(1000) NULL,
    [UsuarioEvaluacion] VARCHAR(100) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Proveedor_Evaluaciones] PRIMARY KEY ([EvaluacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_Integracion]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_Integracion] (
    [IntegracionID] BIGINT NOT NULL,
    [ProveedorID] INT NOT NULL,
    [SistemaID] TINYINT NOT NULL,
    [ClaveExterna] VARCHAR(50) NOT NULL,
    [UltimaSincronizacion] DATETIME2 NULL,
    [EstatusSincronizacionID] TINYINT NOT NULL,
    [MensajeError] VARCHAR(1000) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Proveedor_Integracion] PRIMARY KEY ([IntegracionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_Monedas]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_Monedas] (
    [MonedaID] SMALLINT NOT NULL,
    [ClaveMoneda] VARCHAR(10) NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Simbolo] VARCHAR(10) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Proveedor_Monedas] PRIMARY KEY ([MonedaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_RegimenFiscal]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_RegimenFiscal] (
    [RegimenFiscalID] SMALLINT NOT NULL,
    [ClaveSAT] VARCHAR(10) NULL,
    [Descripcion] VARCHAR(150) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Proveedor_RegimenFiscal] PRIMARY KEY ([RegimenFiscalID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_RiesgoProveedor]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_RiesgoProveedor] (
    [RiesgoID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Proveedor_RiesgoProveedor] PRIMARY KEY ([RiesgoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_RolUsuarioPortal]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_RolUsuarioPortal] (
    [RolPortalID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Proveedor_RolUsuarioPortal] PRIMARY KEY ([RolPortalID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_SistemasIntegracion]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_SistemasIntegracion] (
    [SistemaID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Proveedor_SistemasIntegracion] PRIMARY KEY ([SistemaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_TipoContacto]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_TipoContacto] (
    [TipoContactoID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Proveedor_TipoContacto] PRIMARY KEY ([TipoContactoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_TipoDocumento]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_TipoDocumento] (
    [TipoDocumentoID] SMALLINT NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [RequiereVigencia] BIT NOT NULL DEFAULT ((0)),
    [EsObligatorio] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Proveedor_TipoDocumento] PRIMARY KEY ([TipoDocumentoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_TipoProveedor]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_TipoProveedor] (
    [TipoProveedorID] SMALLINT NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Proveedor_TipoProveedor] PRIMARY KEY ([TipoProveedorID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Proveedor_UsuariosPortal]
-- ============================================================
CREATE TABLE [dbo].[Proveedor_UsuariosPortal] (
    [UsuarioPortalID] INT NOT NULL,
    [ProveedorID] INT NOT NULL,
    [RolPortalID] TINYINT NOT NULL,
    [NombreUsuario] VARCHAR(150) NOT NULL,
    [Email] VARCHAR(150) NOT NULL,
    [PasswordHash] VARCHAR(255) NULL,
    [UltimoAcceso] DATETIME2 NULL,
    [Bloqueado] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Proveedor_UsuariosPortal] PRIMARY KEY ([UsuarioPortalID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Auditoria_Fiscal]
-- ============================================================
CREATE TABLE [dbo].[RH_Auditoria_Fiscal] (
    [AuditoriaID] INT NOT NULL,
    [ColaboradorID] INT NULL,
    [Semana] INT NULL,
    [Monto_Dispersado_Banco] DECIMAL(18,2) NULL,
    [Monto_Timbrado_XML] DECIMAL(18,2) NULL,
    [Monto_IMSS_EBA_EMA] DECIMAL(18,2) NULL,
    [Diferencia] DECIMAL(19,2) NULL,
    [Alerta_Fraude] INT NOT NULL,
    [PeriodoNominaID] INT NULL,
    [UUID_Recibo] VARCHAR(50) NULL,
    [Observaciones] VARCHAR(500) NULL,
    CONSTRAINT [PK_RH_Auditoria_Fiscal] PRIMARY KEY ([AuditoriaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Ausencias]
-- ============================================================
CREATE TABLE [dbo].[RH_Ausencias] (
    [AusenciaID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [TipoAusenciaID] SMALLINT NOT NULL,
    [FechaInicio] DATE NOT NULL,
    [FechaFin] DATE NOT NULL,
    [Dias] DECIMAL(9,2) NOT NULL,
    [Horas] DECIMAL(9,2) NULL,
    [Estatus] VARCHAR(20) NOT NULL DEFAULT ('CAPTURADA'),
    [FolioExterno] VARCHAR(50) NULL,
    [Observaciones] VARCHAR(500) NULL,
    [AprobadoPor] INT NULL,
    [FechaAprobacion] DATETIME2 NULL,
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_RH_Ausencias] PRIMARY KEY ([AusenciaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Calendario_Laboral]
-- ============================================================
CREATE TABLE [dbo].[RH_Calendario_Laboral] (
    [CalendarioLaboralID] INT NOT NULL,
    [SucursalID] INT NULL,
    [SucursalFiscalID] INT NULL,
    [Fecha] DATE NOT NULL,
    [EsDiaDescanso] BIT NOT NULL DEFAULT ((0)),
    [EsFestivo] BIT NOT NULL DEFAULT ((0)),
    [Descripcion] VARCHAR(150) NULL,
    CONSTRAINT [PK_RH_Calendario_Laboral] PRIMARY KEY ([CalendarioLaboralID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Cat_Areas]
-- ============================================================
CREATE TABLE [dbo].[RH_Cat_Areas] (
    [AreaID] INT NOT NULL,
    [DepartamentoID] INT NOT NULL,
    [CodigoArea] VARCHAR(20) NOT NULL,
    [NombreArea] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_RH_Cat_Areas] PRIMARY KEY ([AreaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Cat_Beneficios]
-- ============================================================
CREATE TABLE [dbo].[RH_Cat_Beneficios] (
    [BeneficioID] INT NOT NULL,
    [CodigoBeneficio] VARCHAR(20) NOT NULL,
    [NombreBeneficio] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [MontoDefault] DECIMAL(18,2) NULL,
    [PorcentajeDefault] DECIMAL(9,4) NULL,
    [IntegraSBC] BIT NOT NULL DEFAULT ((0)),
    [GravadoISR] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_RH_Cat_Beneficios] PRIMARY KEY ([BeneficioID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Cat_ConceptosNomina]
-- ============================================================
CREATE TABLE [dbo].[RH_Cat_ConceptosNomina] (
    [ConceptoNominaID] INT NOT NULL,
    [CodigoConcepto] VARCHAR(30) NOT NULL,
    [NombreConcepto] VARCHAR(150) NOT NULL,
    [TipoConceptoNominaID] SMALLINT NOT NULL,
    [ClaveSAT] VARCHAR(20) NULL,
    [FormulaSQL] VARCHAR(MAX) NULL,
    [EsGravado] BIT NOT NULL DEFAULT ((0)),
    [EsExento] BIT NOT NULL DEFAULT ((0)),
    [IntegraSBC] BIT NOT NULL DEFAULT ((0)),
    [AfectaISR] BIT NOT NULL DEFAULT ((0)),
    [AfectaSubsidio] BIT NOT NULL DEFAULT ((0)),
    [AfectaIMSS] BIT NOT NULL DEFAULT ((0)),
    [AfectaInfonavit] BIT NOT NULL DEFAULT ((0)),
    [EsEditableEnCaptura] BIT NOT NULL DEFAULT ((1)),
    [RequiereUnidades] BIT NOT NULL DEFAULT ((0)),
    [OrdenImpresion] SMALLINT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_RH_Cat_ConceptosNomina] PRIMARY KEY ([ConceptoNominaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Cat_Departamentos]
-- ============================================================
CREATE TABLE [dbo].[RH_Cat_Departamentos] (
    [DepartamentoID] INT NOT NULL,
    [CodigoDepartamento] VARCHAR(20) NOT NULL,
    [NombreDepartamento] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_RH_Cat_Departamentos] PRIMARY KEY ([DepartamentoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Cat_EstatusPeriodoNomina]
-- ============================================================
CREATE TABLE [dbo].[RH_Cat_EstatusPeriodoNomina] (
    [EstatusPeriodoNominaID] SMALLINT NOT NULL,
    [CodigoEstatus] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [OrdenFlujo] SMALLINT NOT NULL,
    [EsFinal] BIT NOT NULL DEFAULT ((0)),
    CONSTRAINT [PK_RH_Cat_EstatusPeriodoNomina] PRIMARY KEY ([EstatusPeriodoNominaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Cat_Jornadas]
-- ============================================================
CREATE TABLE [dbo].[RH_Cat_Jornadas] (
    [JornadaID] SMALLINT NOT NULL,
    [CodigoJornada] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [HorasDiarias] DECIMAL(5,2) NULL,
    [HorasSemanales] DECIMAL(5,2) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_RH_Cat_Jornadas] PRIMARY KEY ([JornadaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Cat_MotivosBaja]
-- ============================================================
CREATE TABLE [dbo].[RH_Cat_MotivosBaja] (
    [MotivoBajaID] SMALLINT NOT NULL,
    [CodigoMotivoBaja] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(150) NOT NULL,
    [RequiereFiniquito] BIT NOT NULL DEFAULT ((1)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_RH_Cat_MotivosBaja] PRIMARY KEY ([MotivoBajaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Cat_Puestos]
-- ============================================================
CREATE TABLE [dbo].[RH_Cat_Puestos] (
    [PuestoID] INT NOT NULL,
    [Descripcion] VARCHAR(100) NULL,
    [Departamento] VARCHAR(50) NULL,
    [Sueldo_Base_Seman_SBC] DECIMAL(18,2) NULL,
    [CodigoPuesto] VARCHAR(20) NULL,
    [DepartamentoID] INT NULL,
    [AreaID] INT NULL,
    [NivelOrganizacional] VARCHAR(50) NULL,
    [EsConfianza] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_RH_Cat_Puestos] PRIMARY KEY ([PuestoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Cat_RegimenContratacion]
-- ============================================================
CREATE TABLE [dbo].[RH_Cat_RegimenContratacion] (
    [RegimenContratacionID] SMALLINT NOT NULL,
    [ClaveSAT] VARCHAR(10) NOT NULL,
    [Descripcion] VARCHAR(150) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_RH_Cat_RegimenContratacion] PRIMARY KEY ([RegimenContratacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Cat_Sucursales]
-- ============================================================
CREATE TABLE [dbo].[RH_Cat_Sucursales] (
    [SucursalID] INT NOT NULL,
    [Nombre_Sucursal] VARCHAR(100) NOT NULL,
    [Ciudad] VARCHAR(50) NULL,
    [Activa] BIT NULL DEFAULT ((1)),
    CONSTRAINT [PK_RH_Cat_Sucursales] PRIMARY KEY ([SucursalID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Cat_SucursalesFiscal]
-- ============================================================
CREATE TABLE [dbo].[RH_Cat_SucursalesFiscal] (
    [SucursalFiscalID] INT NOT NULL,
    [SucursalID] INT NOT NULL,
    [EmpresaID] INT NULL,
    [RFC] VARCHAR(13) NOT NULL,
    [RazonSocial] VARCHAR(200) NOT NULL,
    [RegimenFiscal] VARCHAR(10) NULL,
    [CodigoPostalFiscal] VARCHAR(10) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_RH_Cat_SucursalesFiscal] PRIMARY KEY ([SucursalFiscalID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Cat_TiposAusencia]
-- ============================================================
CREATE TABLE [dbo].[RH_Cat_TiposAusencia] (
    [TipoAusenciaID] SMALLINT NOT NULL,
    [CodigoTipoAusencia] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [GoceSueldo] BIT NOT NULL DEFAULT ((0)),
    [AfectaNomina] BIT NOT NULL DEFAULT ((1)),
    [AfectaAsistencia] BIT NOT NULL DEFAULT ((1)),
    [ClaveSAT] VARCHAR(20) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_RH_Cat_TiposAusencia] PRIMARY KEY ([TipoAusenciaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Cat_TiposConceptoNomina]
-- ============================================================
CREATE TABLE [dbo].[RH_Cat_TiposConceptoNomina] (
    [TipoConceptoNominaID] SMALLINT NOT NULL,
    [CodigoTipoConcepto] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [Naturaleza] CHAR(1) NOT NULL,
    CONSTRAINT [PK_RH_Cat_TiposConceptoNomina] PRIMARY KEY ([TipoConceptoNominaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Cat_TiposContrato]
-- ============================================================
CREATE TABLE [dbo].[RH_Cat_TiposContrato] (
    [TipoContratoID] SMALLINT NOT NULL,
    [CodigoTipoContrato] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [EsIndeterminado] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_RH_Cat_TiposContrato] PRIMARY KEY ([TipoContratoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Cat_TiposPeriodoNomina]
-- ============================================================
CREATE TABLE [dbo].[RH_Cat_TiposPeriodoNomina] (
    [TipoPeriodoNominaID] SMALLINT NOT NULL,
    [CodigoTipoPeriodo] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [DiasPeriodo] SMALLINT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_RH_Cat_TiposPeriodoNomina] PRIMARY KEY ([TipoPeriodoNominaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Cat_Turnos]
-- ============================================================
CREATE TABLE [dbo].[RH_Cat_Turnos] (
    [TurnoID] SMALLINT NOT NULL,
    [CodigoTurno] VARCHAR(20) NOT NULL,
    [NombreTurno] VARCHAR(100) NOT NULL,
    [HoraEntradaProgramada] TIME NULL,
    [HoraSalidaProgramada] TIME NULL,
    [TolEntradaMin] SMALLINT NOT NULL DEFAULT ((0)),
    [TolSalidaMin] SMALLINT NOT NULL DEFAULT ((0)),
    [CruzaMedianoche] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_RH_Cat_Turnos] PRIMARY KEY ([TurnoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Colaboradores_Beneficios]
-- ============================================================
CREATE TABLE [dbo].[RH_Colaboradores_Beneficios] (
    [ColaboradorBeneficioID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [BeneficioID] INT NOT NULL,
    [FechaInicio] DATE NOT NULL,
    [FechaFin] DATE NULL,
    [Monto] DECIMAL(18,2) NULL,
    [Porcentaje] DECIMAL(9,4) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [Observaciones] VARCHAR(250) NULL,
    CONSTRAINT [PK_RH_Colaboradores_Beneficios] PRIMARY KEY ([ColaboradorBeneficioID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Colaboradores_ContactosEmergencia]
-- ============================================================
CREATE TABLE [dbo].[RH_Colaboradores_ContactosEmergencia] (
    [ContactoEmergenciaID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [NombreContacto] VARCHAR(150) NOT NULL,
    [Parentesco] VARCHAR(50) NULL,
    [Telefono] VARCHAR(25) NULL,
    [TelefonoAlterno] VARCHAR(25) NULL,
    [Observaciones] VARCHAR(250) NULL,
    [EsPrincipal] BIT NOT NULL DEFAULT ((0)),
    CONSTRAINT [PK_RH_Colaboradores_ContactosEmergencia] PRIMARY KEY ([ContactoEmergenciaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Colaboradores_Dependientes]
-- ============================================================
CREATE TABLE [dbo].[RH_Colaboradores_Dependientes] (
    [DependienteID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [NombreDependiente] VARCHAR(150) NOT NULL,
    [Parentesco] VARCHAR(50) NULL,
    [FechaNacimiento] DATE NULL,
    [EsBeneficiario] BIT NOT NULL DEFAULT ((0)),
    [PorcentajeBeneficio] DECIMAL(9,4) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_RH_Colaboradores_Dependientes] PRIMARY KEY ([DependienteID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Colaboradores_Documentos]
-- ============================================================
CREATE TABLE [dbo].[RH_Colaboradores_Documentos] (
    [DocumentoColaboradorID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [TipoDocumento] VARCHAR(50) NOT NULL,
    [NombreArchivo] VARCHAR(255) NULL,
    [RutaArchivo] VARCHAR(500) NULL,
    [VigenciaDesde] DATE NULL,
    [VigenciaHasta] DATE NULL,
    [Validado] BIT NOT NULL DEFAULT ((0)),
    [ValidadoPor] INT NULL,
    [FechaValidacion] DATETIME2 NULL,
    [Observaciones] VARCHAR(500) NULL,
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_RH_Colaboradores_Documentos] PRIMARY KEY ([DocumentoColaboradorID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Colaboradores_Domicilios]
-- ============================================================
CREATE TABLE [dbo].[RH_Colaboradores_Domicilios] (
    [DomicilioID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [Calle] VARCHAR(150) NULL,
    [NumeroExterior] VARCHAR(20) NULL,
    [NumeroInterior] VARCHAR(20) NULL,
    [Colonia] VARCHAR(100) NULL,
    [Municipio] VARCHAR(100) NULL,
    [Estado] VARCHAR(100) NULL,
    [Pais] VARCHAR(100) NULL DEFAULT ('MEXICO'),
    [CodigoPostal] VARCHAR(10) NULL,
    [EsPrincipal] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_RH_Colaboradores_Domicilios] PRIMARY KEY ([DomicilioID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Colaboradores_Expediente]
-- ============================================================
CREATE TABLE [dbo].[RH_Colaboradores_Expediente] (
    [ColaboradorID] INT NOT NULL,
    [Nombre_Completo] VARCHAR(255) NOT NULL,
    [CURP] VARCHAR(18) NULL,
    [RFC] VARCHAR(13) NULL,
    [CLABE_Bancaria] VARCHAR(18) NULL,
    [SucursalID] INT NULL,
    [PuestoID] INT NULL,
    [Validacion_IA_RFC] BIT NULL DEFAULT ((0)),
    [Validacion_IA_CURP] BIT NULL DEFAULT ((0)),
    [Validacion_IA_EdoCta] BIT NULL DEFAULT ((0)),
    [Validacion_IA_Contrato] BIT NULL DEFAULT ((0)),
    [Colaborador_Activo] INT NOT NULL,
    [Fecha_Alta] DATETIME NULL DEFAULT (getdate()),
    [Estatus_Laboral] VARCHAR(20) NULL DEFAULT ('RECLUTAMIENTO'),
    [CodigoColaborador] VARCHAR(30) NULL,
    [NumeroEmpleado] VARCHAR(30) NULL,
    [NSS] VARCHAR(15) NULL,
    [FechaNacimiento] DATE NULL,
    [Sexo] CHAR(1) NULL,
    [EstadoCivil] VARCHAR(30) NULL,
    [CorreoPersonal] VARCHAR(150) NULL,
    [CorreoEmpresarial] VARCHAR(150) NULL,
    [TelefonoMovil] VARCHAR(25) NULL,
    [FechaIngreso] DATE NULL,
    [FechaAntiguedad] DATE NULL,
    [FechaBaja] DATE NULL,
    [MotivoBajaID] SMALLINT NULL,
    [SucursalFiscalID] INT NULL,
    [BancoID] SMALLINT NULL,
    [NumeroCuenta] VARCHAR(30) NULL,
    [MetodoPagoSAT] VARCHAR(10) NULL,
    [UsuarioID] INT NULL,
    [ObservacionesRH] VARCHAR(500) NULL,
    CONSTRAINT [PK_RH_Colaboradores_Expediente] PRIMARY KEY ([ColaboradorID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Contratos]
-- ============================================================
CREATE TABLE [dbo].[RH_Contratos] (
    [ContratoID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [GrupoNominaID] INT NOT NULL,
    [PuestoID] INT NOT NULL,
    [SucursalID] INT NOT NULL,
    [SucursalFiscalID] INT NOT NULL,
    [TipoContratoID] SMALLINT NOT NULL,
    [RegimenContratacionID] SMALLINT NULL,
    [JornadaID] SMALLINT NULL,
    [TurnoID] SMALLINT NULL,
    [FechaInicio] DATE NOT NULL,
    [FechaFin] DATE NULL,
    [SalarioDiario] DECIMAL(18,2) NOT NULL,
    [SalarioDiarioIntegrado] DECIMAL(18,2) NULL,
    [SalarioBaseCotizacion] DECIMAL(18,2) NULL,
    [SueldoPeriodo] DECIMAL(18,2) NULL,
    [SalarioVariablePromedio] DECIMAL(18,2) NULL,
    [TipoSalario] VARCHAR(20) NULL,
    [RiesgoPuesto] VARCHAR(20) NULL,
    [CentroCosto] VARCHAR(50) NULL,
    [EsContratoVigente] BIT NOT NULL DEFAULT ((1)),
    [Firmado] BIT NOT NULL DEFAULT ((0)),
    [FechaFirma] DATE NULL,
    [Observaciones] VARCHAR(500) NULL,
    [CreadoPor] INT NULL,
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_RH_Contratos] PRIMARY KEY ([ContratoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Finiquitos]
-- ============================================================
CREATE TABLE [dbo].[RH_Finiquitos] (
    [FiniquitoID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [ContratoID] INT NULL,
    [MotivoBajaID] SMALLINT NULL,
    [FechaBaja] DATE NOT NULL,
    [FechaCalculo] DATE NOT NULL,
    [DiasPendientesPago] DECIMAL(9,2) NOT NULL DEFAULT ((0)),
    [VacacionesPendientesDias] DECIMAL(9,2) NOT NULL DEFAULT ((0)),
    [PrimaVacacionalMonto] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [AguinaldoProporcional] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [IndemnizacionMonto] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [OtrasPercepciones] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [OtrasDeducciones] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [NetoPagar] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Estatus] VARCHAR(20) NOT NULL DEFAULT ('CALCULADO'),
    [AutorizadoPor] INT NULL,
    [PeriodoNominaID] INT NULL,
    [NominaID] INT NULL,
    [Observaciones] VARCHAR(500) NULL,
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_RH_Finiquitos] PRIMARY KEY ([FiniquitoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Finiquitos_Detalle]
-- ============================================================
CREATE TABLE [dbo].[RH_Finiquitos_Detalle] (
    [FiniquitoDetalleID] INT NOT NULL,
    [FiniquitoID] INT NOT NULL,
    [ConceptoNominaID] INT NOT NULL,
    [Importe] DECIMAL(18,2) NOT NULL,
    [ImporteGravado] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ImporteExento] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Observaciones] VARCHAR(300) NULL,
    CONSTRAINT [PK_RH_Finiquitos_Detalle] PRIMARY KEY ([FiniquitoDetalleID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Flujo_Nomina_Sucursal]
-- ============================================================
CREATE TABLE [dbo].[RH_Flujo_Nomina_Sucursal] (
    [FlujoID] INT NOT NULL,
    [SucursalID] INT NULL,
    [Semana_Anio] INT NULL,
    [Estatus_Flujo] VARCHAR(50) NULL,
    [Hora_Entrega_RH] DATETIME NULL,
    [Hora_Validacion_Gerente] DATETIME NULL,
    [Hora_Autorizacion_DG] DATETIME NULL,
    [Hora_Envio_Tesoreria] DATETIME NULL,
    [Hora_Pago_Ejecutado] DATETIME NULL,
    [Motivo_Rechazo_Gerente] VARCHAR(MAX) NULL,
    [Intentos_Reenvio] INT NULL DEFAULT ((1)),
    [PeriodoNominaID] INT NULL,
    CONSTRAINT [PK_RH_Flujo_Nomina_Sucursal] PRIMARY KEY ([FlujoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_GruposNomina]
-- ============================================================
CREATE TABLE [dbo].[RH_GruposNomina] (
    [GrupoNominaID] INT NOT NULL,
    [CodigoGrupoNomina] VARCHAR(20) NOT NULL,
    [NombreGrupoNomina] VARCHAR(100) NOT NULL,
    [TipoPeriodoNominaID] SMALLINT NOT NULL,
    [SucursalFiscalID] INT NOT NULL,
    [DiaPago] SMALLINT NULL,
    [DesfaseDiasPago] SMALLINT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_RH_GruposNomina] PRIMARY KEY ([GrupoNominaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Historial_Puestos]
-- ============================================================
CREATE TABLE [dbo].[RH_Historial_Puestos] (
    [HistorialPuestoID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [ContratoID] INT NULL,
    [PuestoIDAnterior] INT NULL,
    [PuestoIDNuevo] INT NOT NULL,
    [SucursalIDAnterior] INT NULL,
    [SucursalIDNueva] INT NULL,
    [FechaMovimiento] DATE NOT NULL,
    [MotivoMovimiento] VARCHAR(150) NULL,
    [AutorizadoPor] INT NULL,
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_RH_Historial_Puestos] PRIMARY KEY ([HistorialPuestoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Historial_Salarios]
-- ============================================================
CREATE TABLE [dbo].[RH_Historial_Salarios] (
    [HistorialSalarioID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [ContratoID] INT NULL,
    [FechaVigencia] DATE NOT NULL,
    [SalarioDiarioAnterior] DECIMAL(18,2) NULL,
    [SalarioDiarioNuevo] DECIMAL(18,2) NOT NULL,
    [SDIAnterior] DECIMAL(18,2) NULL,
    [SDINuevo] DECIMAL(18,2) NULL,
    [SBCAnterior] DECIMAL(18,2) NULL,
    [SBCNuevo] DECIMAL(18,2) NULL,
    [MotivoCambio] VARCHAR(150) NULL,
    [AutorizadoPor] INT NULL,
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_RH_Historial_Salarios] PRIMARY KEY ([HistorialSalarioID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Homologacion_Equivalencias]
-- ============================================================
CREATE TABLE [dbo].[RH_Homologacion_Equivalencias] (
    [EquivalenciaID] INT NOT NULL,
    [Tipo] VARCHAR(20) NOT NULL,
    [Valor_Origen] NVARCHAR(200) NOT NULL,
    [Valor_Normalizado] NVARCHAR(200) NULL,
    [CatalogoID] INT NULL,
    [Estado] VARCHAR(20) NULL DEFAULT ('Aprobado'),
    [Usuario_Aprobador] VARCHAR(100) NULL,
    [Fecha_Aprobacion] DATETIME NULL DEFAULT (getdate()),
    [Observaciones] NVARCHAR(500) NULL,
    CONSTRAINT [PK_RH_Homologacion_Equivalencias] PRIMARY KEY ([EquivalenciaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Importacion_Bitacora]
-- ============================================================
CREATE TABLE [dbo].[RH_Importacion_Bitacora] (
    [BitacoraID] INT NOT NULL,
    [Fecha_Ejecucion] DATETIME NULL DEFAULT (getdate()),
    [Fuente] VARCHAR(50) NOT NULL,
    [Archivo_Origen] NVARCHAR(255) NULL,
    [Total_Registros_Leidos] INT NULL DEFAULT ((0)),
    [Total_Insertados] INT NULL DEFAULT ((0)),
    [Total_Actualizados] INT NULL DEFAULT ((0)),
    [Total_Duplicados_Omitidos] INT NULL DEFAULT ((0)),
    [Total_Incompletos] INT NULL DEFAULT ((0)),
    [Total_Errores] INT NULL DEFAULT ((0)),
    [Usuario_Ejecutor] NVARCHAR(100) NULL,
    [Duracion_Segundos] INT NULL,
    [Estado] VARCHAR(20) NULL DEFAULT ('En Proceso'),
    [Detalle_JSON] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_RH_Importacion_Bitacora] PRIMARY KEY ([BitacoraID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Importacion_Staging]
-- ============================================================
CREATE TABLE [dbo].[RH_Importacion_Staging] (
    [StagingID] INT NOT NULL,
    [Nombre_Completo] NVARCHAR(200) NOT NULL,
    [CURP] CHAR(18) NULL,
    [RFC] VARCHAR(13) NULL,
    [CLABE_Bancaria] CHAR(18) NULL,
    [Numero_Empleado_Externo] VARCHAR(50) NULL,
    [Sucursal_Nombre] NVARCHAR(100) NULL,
    [SucursalID] INT NULL,
    [Puesto_Nombre] NVARCHAR(100) NULL,
    [PuestoID] INT NULL,
    [Area_Departamento] NVARCHAR(100) NULL,
    [Sexo] CHAR(1) NULL,
    [Edad] INT NULL,
    [Antiguedad] NVARCHAR(50) NULL,
    [Sueldo_Diario] DECIMAL(10,2) NULL,
    [Metodo_Pago] NVARCHAR(50) NULL,
    [Fuente] VARCHAR(50) NOT NULL,
    [Archivo_Origen] NVARCHAR(255) NULL,
    [Linea_Origen] INT NULL,
    [Fecha_Importacion] DATETIME NULL DEFAULT (getdate()),
    [Usuario_Importador] NVARCHAR(100) NULL,
    [Estado] VARCHAR(20) NULL DEFAULT ('Pendiente'),
    [Clasificacion] VARCHAR(30) NULL,
    [Nivel_Confianza] VARCHAR(20) NULL,
    [Accion_Realizada] VARCHAR(20) NULL,
    [ColaboradorID_Destino] INT NULL,
    [ColaboradorID_Match] INT NULL,
    [Mensaje_Error] NVARCHAR(500) NULL,
    [Observaciones] NVARCHAR(MAX) NULL,
    [Usuario_Aprobador] NVARCHAR(100) NULL,
    [Fecha_Aprobacion] DATETIME NULL,
    [Fecha_Procesamiento] DATETIME NULL,
    CONSTRAINT [PK_RH_Importacion_Staging] PRIMARY KEY ([StagingID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_IMSS_Movimientos]
-- ============================================================
CREATE TABLE [dbo].[RH_IMSS_Movimientos] (
    [MovimientoIMSSID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [ContratoID] INT NULL,
    [TipoMovimiento] VARCHAR(30) NOT NULL,
    [FechaMovimiento] DATE NOT NULL,
    [SalarioBaseCotizacion] DECIMAL(18,2) NULL,
    [SalarioDiarioIntegrado] DECIMAL(18,2) NULL,
    [FolioIMSS] VARCHAR(50) NULL,
    [EnviadoIDSE] BIT NOT NULL DEFAULT ((0)),
    [FechaEnvioIDSE] DATETIME2 NULL,
    [ProcesadoSUA] BIT NOT NULL DEFAULT ((0)),
    [FechaProcesadoSUA] DATETIME2 NULL,
    [Observaciones] VARCHAR(500) NULL,
    [CapturadoPor] INT NULL,
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_RH_IMSS_Movimientos] PRIMARY KEY ([MovimientoIMSSID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Incidencias_Nomina]
-- ============================================================
CREATE TABLE [dbo].[RH_Incidencias_Nomina] (
    [IncidenciaID] INT NOT NULL,
    [ColaboradorID] INT NULL,
    [Tipo_Incidencia] VARCHAR(50) NULL,
    [Monto] DECIMAL(18,2) NULL DEFAULT ((0)),
    [Unidades] DECIMAL(5,2) NULL DEFAULT ((0)),
    [Fecha_Incidencia] DATE NULL,
    [Capturado_Por] INT NULL,
    [Fecha_Registro] DATETIME NULL DEFAULT (getdate()),
    [ConceptoNominaID] INT NULL,
    [PeriodoNominaID] INT NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Autorizado] BIT NOT NULL DEFAULT ((0)),
    [AutorizadoPor] INT NULL,
    [FechaAutorizacion] DATETIME2 NULL,
    CONSTRAINT [PK_RH_Incidencias_Nomina] PRIMARY KEY ([IncidenciaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Nomina]
-- ============================================================
CREATE TABLE [dbo].[RH_Nomina] (
    [NominaID] INT NOT NULL,
    [PeriodoNominaID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [ContratoID] INT NULL,
    [SucursalID] INT NOT NULL,
    [SucursalFiscalID] INT NOT NULL,
    [DiasPagados] DECIMAL(9,2) NOT NULL DEFAULT ((0)),
    [HorasPagadas] DECIMAL(9,2) NOT NULL DEFAULT ((0)),
    [Faltas] DECIMAL(9,2) NOT NULL DEFAULT ((0)),
    [Incapacidades] DECIMAL(9,2) NOT NULL DEFAULT ((0)),
    [SalarioDiario] DECIMAL(18,2) NOT NULL,
    [SalarioDiarioIntegrado] DECIMAL(18,2) NULL,
    [SalarioBaseCotizacion] DECIMAL(18,2) NULL,
    [TotalPercepciones] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalDeducciones] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalOtrosPagos] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalGravado] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalExento] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ISR] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [SubsidioEmpleo] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [CuotaIMSS] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [RetencionInfonavit] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [NetoPagar] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [EstatusNomina] VARCHAR(20) NOT NULL DEFAULT ('CAPTURADA'),
    [Procesado] BIT NOT NULL DEFAULT ((0)),
    [Timbrado] BIT NOT NULL DEFAULT ((0)),
    [Pagado] BIT NOT NULL DEFAULT ((0)),
    [FechaCalculo] DATETIME2 NULL,
    [FechaTimbrado] DATETIME2 NULL,
    [FechaPagoReal] DATETIME2 NULL,
    [Observaciones] VARCHAR(500) NULL,
    CONSTRAINT [PK_RH_Nomina] PRIMARY KEY ([NominaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Nomina_Detalle]
-- ============================================================
CREATE TABLE [dbo].[RH_Nomina_Detalle] (
    [NominaDetalleID] INT NOT NULL,
    [NominaID] INT NOT NULL,
    [ConceptoNominaID] INT NOT NULL,
    [Origen] VARCHAR(20) NOT NULL,
    [ReferenciaID] INT NULL,
    [Unidades] DECIMAL(18,4) NULL,
    [ImporteUnitario] DECIMAL(18,6) NULL,
    [Importe] DECIMAL(18,2) NOT NULL,
    [ImporteGravado] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ImporteExento] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Observaciones] VARCHAR(300) NULL,
    CONSTRAINT [PK_RH_Nomina_Detalle] PRIMARY KEY ([NominaDetalleID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Nomina_Dispersion]
-- ============================================================
CREATE TABLE [dbo].[RH_Nomina_Dispersion] (
    [DispersionNominaID] INT NOT NULL,
    [PeriodoNominaID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [NominaID] INT NULL,
    [BancoID] SMALLINT NULL,
    [CLABE] VARCHAR(18) NULL,
    [Cuenta] VARCHAR(30) NULL,
    [Beneficiario] VARCHAR(200) NULL,
    [Importe] DECIMAL(18,2) NOT NULL,
    [ReferenciaBanco] VARCHAR(100) NULL,
    [EstatusDispersion] VARCHAR(30) NOT NULL DEFAULT ('PENDIENTE'),
    [FechaGeneracion] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaAplicacion] DATETIME2 NULL,
    [Observaciones] VARCHAR(500) NULL,
    CONSTRAINT [PK_RH_Nomina_Dispersion] PRIMARY KEY ([DispersionNominaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Nomina_Recibos]
-- ============================================================
CREATE TABLE [dbo].[RH_Nomina_Recibos] (
    [NominaReciboID] INT NOT NULL,
    [NominaID] INT NOT NULL,
    [UUID] VARCHAR(50) NULL,
    [Serie] VARCHAR(20) NULL,
    [Folio] VARCHAR(50) NULL,
    [FechaTimbrado] DATETIME2 NULL,
    [XML_Ruta] VARCHAR(500) NULL,
    [PDF_Ruta] VARCHAR(500) NULL,
    [SelloSAT] VARCHAR(MAX) NULL,
    [CadenaOriginal] VARCHAR(MAX) NULL,
    [EstadoCFDI] VARCHAR(30) NULL,
    [Cancelado] BIT NOT NULL DEFAULT ((0)),
    [FechaCancelacion] DATETIME2 NULL,
    [MotivoCancelacion] VARCHAR(200) NULL,
    [Observaciones] VARCHAR(500) NULL,
    CONSTRAINT [PK_RH_Nomina_Recibos] PRIMARY KEY ([NominaReciboID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Periodos_Nomina]
-- ============================================================
CREATE TABLE [dbo].[RH_Periodos_Nomina] (
    [PeriodoNominaID] INT NOT NULL,
    [GrupoNominaID] INT NOT NULL,
    [EstatusPeriodoNominaID] SMALLINT NOT NULL,
    [Ejercicio] INT NOT NULL,
    [NumeroPeriodo] INT NOT NULL,
    [FechaInicio] DATE NOT NULL,
    [FechaFin] DATE NOT NULL,
    [FechaPago] DATE NOT NULL,
    [FechaCorteIncidencias] DATE NULL,
    [EsAjuste] BIT NOT NULL DEFAULT ((0)),
    [Observaciones] VARCHAR(500) NULL,
    [CerradoPor] INT NULL,
    [FechaCierre] DATETIME2 NULL,
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_RH_Periodos_Nomina] PRIMARY KEY ([PeriodoNominaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Prestamos]
-- ============================================================
CREATE TABLE [dbo].[RH_Prestamos] (
    [PrestamoID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [TipoPrestamo] VARCHAR(30) NOT NULL,
    [FechaPrestamo] DATE NOT NULL,
    [MontoOriginal] DECIMAL(18,2) NOT NULL,
    [SaldoActual] DECIMAL(18,2) NOT NULL,
    [Cuotas] INT NULL,
    [MontoCuota] DECIMAL(18,2) NULL,
    [DescuentoPorPeriodo] DECIMAL(18,2) NULL,
    [Estatus] VARCHAR(20) NOT NULL DEFAULT ('ACTIVO'),
    [AutorizadoPor] INT NULL,
    [Observaciones] VARCHAR(500) NULL,
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_RH_Prestamos] PRIMARY KEY ([PrestamoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Prestamos_Detalle]
-- ============================================================
CREATE TABLE [dbo].[RH_Prestamos_Detalle] (
    [PrestamoDetalleID] INT NOT NULL,
    [PrestamoID] INT NOT NULL,
    [PeriodoNominaID] INT NULL,
    [NominaID] INT NULL,
    [FechaProgramada] DATE NULL,
    [FechaAplicacion] DATE NULL,
    [ImporteProgramado] DECIMAL(18,2) NOT NULL,
    [ImporteAplicado] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Estatus] VARCHAR(20) NOT NULL DEFAULT ('PENDIENTE'),
    [Observaciones] VARCHAR(300) NULL,
    CONSTRAINT [PK_RH_Prestamos_Detalle] PRIMARY KEY ([PrestamoDetalleID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Reloj_Checador]
-- ============================================================
CREATE TABLE [dbo].[RH_Reloj_Checador] (
    [CheckID] INT NOT NULL,
    [ColaboradorID] INT NULL,
    [Tipo_Registro] VARCHAR(10) NULL,
    [FechaHora] DATETIME NULL DEFAULT (getdate()),
    [Geolocalizacion] VARCHAR(100) NULL,
    [Validado_Gerencia] BIT NULL DEFAULT ((0)),
    CONSTRAINT [PK_RH_Reloj_Checador] PRIMARY KEY ([CheckID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Vacaciones_Movimientos]
-- ============================================================
CREATE TABLE [dbo].[RH_Vacaciones_Movimientos] (
    [VacacionMovimientoID] INT NOT NULL,
    [VacacionSaldoID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [TipoMovimiento] VARCHAR(20) NOT NULL,
    [FechaInicio] DATE NULL,
    [FechaFin] DATE NULL,
    [Dias] DECIMAL(9,2) NOT NULL,
    [PrimaVacacionalMonto] DECIMAL(18,2) NULL,
    [PeriodoNominaID] INT NULL,
    [Observaciones] VARCHAR(500) NULL,
    [CapturadoPor] INT NULL,
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_RH_Vacaciones_Movimientos] PRIMARY KEY ([VacacionMovimientoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[RH_Vacaciones_Saldos]
-- ============================================================
CREATE TABLE [dbo].[RH_Vacaciones_Saldos] (
    [VacacionSaldoID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [Ejercicio] INT NOT NULL,
    [Aniversario] INT NOT NULL,
    [DiasOtorgados] DECIMAL(9,2) NOT NULL,
    [DiasTomados] DECIMAL(9,2) NOT NULL DEFAULT ((0)),
    [DiasPagados] DECIMAL(9,2) NOT NULL DEFAULT ((0)),
    [DiasDisponibles] DECIMAL(11,2) NULL,
    [PrimaVacacionalPct] DECIMAL(9,4) NOT NULL DEFAULT ((0.2500)),
    [FechaGeneracion] DATE NOT NULL,
    [FechaVencimiento] DATE NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_RH_Vacaciones_Saldos] PRIMARY KEY ([VacacionSaldoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Scheduler_BitacoraJobs]
-- ============================================================
CREATE TABLE [dbo].[Scheduler_BitacoraJobs] (
    [ID] INT NOT NULL,
    [JobName] VARCHAR(100) NOT NULL,
    [RunID] VARCHAR(50) NOT NULL,
    [Accion] VARCHAR(50) NOT NULL,
    [FechaAccion] DATETIME NULL DEFAULT (getutcdate()),
    [ServerID] VARCHAR(50) NULL,
    [DetallesJSON] NVARCHAR(MAX) NULL,
    [Exito] BIT NULL DEFAULT ((1)),
    [MensajeError] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_Scheduler_BitacoraJobs] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Scheduler_InventariosProcesados]
-- ============================================================
CREATE TABLE [dbo].[Scheduler_InventariosProcesados] (
    [ID] INT NOT NULL,
    [SistemaOrigen] VARCHAR(50) NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [SucursalID] VARCHAR(50) NOT NULL,
    [AlmacenID] VARCHAR(50) NOT NULL,
    [FolioInventario] VARCHAR(100) NOT NULL,
    [Estado] VARCHAR(20) NULL DEFAULT ('EN_PROCESO'),
    [Intentos] INT NULL DEFAULT ((1)),
    [FechaDeteccion] DATETIME NULL DEFAULT (getutcdate()),
    [FechaProcesamiento] DATETIME NULL,
    [FechaUltimoIntento] DATETIME NULL DEFAULT (getutcdate()),
    [ErrorMensaje] NVARCHAR(MAX) NULL,
    [WorkflowID] VARCHAR(50) NULL,
    [DetallesJSON] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_Scheduler_InventariosProcesados] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Scheduler_PedidosProcesados]
-- ============================================================
CREATE TABLE [dbo].[Scheduler_PedidosProcesados] (
    [ID] INT NOT NULL,
    [SistemaOrigen] VARCHAR(50) NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [EmpresaID] VARCHAR(50) NOT NULL,
    [SucursalID] VARCHAR(50) NULL,
    [FolioPedido] VARCHAR(100) NOT NULL,
    [Estado] VARCHAR(20) NULL DEFAULT ('DETECTADO'),
    [FechaDeteccion] DATETIME NULL DEFAULT (getutcdate()),
    [FechaProcesamiento] DATETIME NULL,
    [TipoDocumento] VARCHAR(50) NULL,
    [DetallesJSON] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_Scheduler_PedidosProcesados] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Servidores_Conexiones]
-- ============================================================
CREATE TABLE [dbo].[Servidores_Conexiones] (
    [id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [nombre] NVARCHAR(100) NOT NULL,
    [system_type] NVARCHAR(50) NOT NULL,
    [tipo_conexion] NVARCHAR(20) NOT NULL,
    [host] NVARCHAR(255) NULL,
    [port] INT NULL DEFAULT ((1433)),
    [database_name] NVARCHAR(100) NULL,
    [username] NVARCHAR(100) NULL,
    [password_encrypted] NVARCHAR(500) NULL,
    [api_url] NVARCHAR(500) NULL,
    [api_key_encrypted] NVARCHAR(500) NULL,
    [activo] BIT NULL DEFAULT ((1)),
    [visible_en_operaciones] BIT NULL DEFAULT ((1)),
    [visible_en_listado] BIT NULL DEFAULT ((1)),
    [es_editable_ui] BIT NULL DEFAULT ((1)),
    [es_eliminable_ui] BIT NULL DEFAULT ((1)),
    [empresa_id] NVARCHAR(100) NULL,
    [sucursales] NVARCHAR(MAX) NULL,
    [categorias] NVARCHAR(MAX) NULL,
    [departamentos] NVARCHAR(MAX) NULL,
    [date_calculation_method] NVARCHAR(50) NULL,
    [queries_configured] BIT NULL DEFAULT ((0)),
    [query_ventas] NVARCHAR(MAX) NULL,
    [query_inventario] NVARCHAR(MAX) NULL,
    [query_movimientos] NVARCHAR(MAX) NULL,
    [created_at] DATETIME NULL DEFAULT (getdate()),
    [updated_at] DATETIME NULL DEFAULT (getdate()),
    [created_by] NVARCHAR(100) NULL,
    [updated_by] NVARCHAR(100) NULL,
    [mongodb_id] NVARCHAR(100) NULL,
    [EmpresaID] INT NULL,
    [tipos_movimiento] NVARCHAR(MAX) NULL,
    [fecha_ultima_sincronizacion] DATETIME2 NULL,
    [source_status] VARCHAR(50) NULL,
    [ultimo_error_sync] NVARCHAR(500) NULL,
    CONSTRAINT [PK_Servidores_Conexiones] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Servidores_Conexiones_backup_tipos_enriq_20260513_0840]
-- ============================================================
CREATE TABLE [dbo].[Servidores_Conexiones_backup_tipos_enriq_20260513_0840] (
    [mongodb_id] NVARCHAR(100) NULL,
    [nombre] NVARCHAR(100) NOT NULL,
    [tipos_movimiento_anterior] NVARCHAR(MAX) NULL,
    [fecha_backup] DATETIME NOT NULL,
    [fase] VARCHAR(35) NOT NULL
);
GO

-- ============================================================
-- TABLA: [dbo].[Servidores_Conexiones_backup_tipos_mov_20260513_0729]
-- ============================================================
CREATE TABLE [dbo].[Servidores_Conexiones_backup_tipos_mov_20260513_0729] (
    [id] UNIQUEIDENTIFIER NOT NULL,
    [nombre] NVARCHAR(100) NOT NULL,
    [system_type] NVARCHAR(50) NOT NULL,
    [tipo_conexion] NVARCHAR(20) NOT NULL,
    [host] NVARCHAR(255) NULL,
    [port] INT NULL,
    [database_name] NVARCHAR(100) NULL,
    [username] NVARCHAR(100) NULL,
    [password_encrypted] NVARCHAR(500) NULL,
    [api_url] NVARCHAR(500) NULL,
    [api_key_encrypted] NVARCHAR(500) NULL,
    [activo] BIT NULL,
    [visible_en_operaciones] BIT NULL,
    [visible_en_listado] BIT NULL,
    [es_editable_ui] BIT NULL,
    [es_eliminable_ui] BIT NULL,
    [empresa_id] NVARCHAR(100) NULL,
    [sucursales] NVARCHAR(MAX) NULL,
    [categorias] NVARCHAR(MAX) NULL,
    [departamentos] NVARCHAR(MAX) NULL,
    [date_calculation_method] NVARCHAR(50) NULL,
    [queries_configured] BIT NULL,
    [query_ventas] NVARCHAR(MAX) NULL,
    [query_inventario] NVARCHAR(MAX) NULL,
    [query_movimientos] NVARCHAR(MAX) NULL,
    [created_at] DATETIME NULL,
    [updated_at] DATETIME NULL,
    [created_by] NVARCHAR(100) NULL,
    [updated_by] NVARCHAR(100) NULL,
    [mongodb_id] NVARCHAR(100) NULL,
    [EmpresaID] INT NULL,
    [tipos_movimiento] NVARCHAR(MAX) NULL,
    [fecha_backup] DATETIME NOT NULL,
    [fase_migracion] VARCHAR(24) NOT NULL
);
GO

-- ============================================================
-- TABLA: [dbo].[Servidores_Conexiones_Log]
-- ============================================================
CREATE TABLE [dbo].[Servidores_Conexiones_Log] (
    [log_id] BIGINT NOT NULL,
    [servidor_id] UNIQUEIDENTIFIER NULL,
    [accion] NVARCHAR(20) NULL,
    [datos_anteriores] NVARCHAR(MAX) NULL,
    [datos_nuevos] NVARCHAR(MAX) NULL,
    [usuario] NVARCHAR(100) NULL,
    [fecha] DATETIME NULL DEFAULT (getdate()),
    [ip_origen] NVARCHAR(50) NULL,
    CONSTRAINT [PK_Servidores_Conexiones_Log] PRIMARY KEY ([log_id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Servidores_Status]
-- ============================================================
CREATE TABLE [dbo].[Servidores_Status] (
    [StatusID] INT NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [IsOnline] BIT NULL DEFAULT ((1)),
    [ResponseTimeMs] INT NULL,
    [LastCheck] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Servidores_Status] PRIMARY KEY ([StatusID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sesiones]
-- ============================================================
CREATE TABLE [dbo].[Sesiones] (
    [SesionID] VARCHAR(50) NOT NULL,
    [UsuarioID] VARCHAR(50) NOT NULL,
    [TipoUsuario] VARCHAR(20) NULL DEFAULT ('interno'),
    [RefreshTokenHash] VARCHAR(128) NOT NULL,
    [FamiliaTokenID] VARCHAR(50) NOT NULL,
    [FechaCreacion] DATETIME NULL DEFAULT (getutcdate()),
    [FechaExpiracion] DATETIME NOT NULL,
    [UltimaActividad] DATETIME NULL DEFAULT (getutcdate()),
    [EstaActiva] BIT NULL DEFAULT ((1)),
    [IPCliente] VARCHAR(45) NULL,
    [UserAgent] VARCHAR(500) NULL,
    [FechaModificacion] DATETIME NULL DEFAULT (getutcdate()),
    CONSTRAINT [PK_Sesiones] PRIMARY KEY ([SesionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[SesionesHistorico]
-- ============================================================
CREATE TABLE [dbo].[SesionesHistorico] (
    [HistoricoID] INT NOT NULL,
    [SesionID] VARCHAR(50) NOT NULL,
    [UsuarioID] VARCHAR(50) NOT NULL,
    [TipoUsuario] VARCHAR(20) NULL,
    [Accion] VARCHAR(50) NOT NULL,
    [FechaAccion] DATETIME NULL DEFAULT (getutcdate()),
    [IPCliente] VARCHAR(45) NULL,
    [UserAgent] VARCHAR(500) NULL,
    [DetallesJSON] NVARCHAR(MAX) NULL,
    [AccionRealizadaPor] VARCHAR(50) NULL,
    CONSTRAINT [PK_SesionesHistorico] PRIMARY KEY ([HistoricoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sistema_Capacidades]
-- ============================================================
CREATE TABLE [dbo].[Sistema_Capacidades] (
    [SistemaCapacidadID] INT NOT NULL,
    [SistemaTipoID] INT NOT NULL,
    [CodigoCapacidad] VARCHAR(50) NOT NULL,
    [Descripcion] NVARCHAR(200) NULL,
    [RequiereApiLocal] BIT NULL DEFAULT ((0)),
    [RequiereSqlDirecto] BIT NULL DEFAULT ((1)),
    [ConfiguracionJSON] NVARCHAR(MAX) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    [UpdatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Sistema_Capacidades] PRIMARY KEY ([SistemaCapacidadID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sistema_Catalogo]
-- ============================================================
CREATE TABLE [dbo].[Sistema_Catalogo] (
    [SistemaID] INT NOT NULL,
    [Codigo] NVARCHAR(50) NOT NULL,
    [Descripcion] NVARCHAR(100) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaActualizacion] DATETIME2 NULL,
    [Estado] NVARCHAR(20) NOT NULL DEFAULT ('ACTIVO'),
    [SolicitadoPorUsuarioID] INT NULL,
    [AutorizadoPorUsuarioID] INT NULL,
    [FechaSolicitud] DATETIME2 NULL,
    [FechaAutorizacion] DATETIME2 NULL,
    [SolicitadoPorEmail] NVARCHAR(200) NULL,
    [AutorizadoPorEmail] NVARCHAR(200) NULL,
    CONSTRAINT [PK_Sistema_Catalogo] PRIMARY KEY ([SistemaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sistema_Empresas]
-- ============================================================
CREATE TABLE [dbo].[Sistema_Empresas] (
    [EmpresaID] INT NOT NULL,
    [CodigoEmpresa] VARCHAR(20) NOT NULL,
    [NombreEmpresa] NVARCHAR(100) NOT NULL,
    [NombreComercial] NVARCHAR(100) NULL,
    [RFC] VARCHAR(13) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (getutcdate()),
    [FechaModificacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [UpdatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_Sistema_Empresas] PRIMARY KEY ([EmpresaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sistema_EmpresasAlias]
-- ============================================================
CREATE TABLE [dbo].[Sistema_EmpresasAlias] (
    [EmpresaAliasID] INT NOT NULL,
    [EmpresaID] INT NOT NULL,
    [Alias] NVARCHAR(200) NOT NULL,
    [AliasNormalizado] NVARCHAR(200) NOT NULL,
    [OrigenAlias] VARCHAR(50) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaActualizacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [UpdatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_Sistema_EmpresasAlias] PRIMARY KEY ([EmpresaAliasID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sistema_EmpresasMongoMap]
-- ============================================================
CREATE TABLE [dbo].[Sistema_EmpresasMongoMap] (
    [MapID] INT NOT NULL,
    [EmpresaMongoUUID] VARCHAR(50) NOT NULL,
    [EmpresaMongoLegacyID] VARCHAR(50) NULL,
    [EmpresaID_SQL] INT NOT NULL,
    [CodigoEmpresa] VARCHAR(20) NOT NULL,
    [NombreEmpresa] NVARCHAR(100) NOT NULL,
    [MetodoMapeo] VARCHAR(50) NOT NULL DEFAULT ('CODIGO_EXACTO'),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getutcdate()),
    [FechaActualizacion] DATETIME2 NULL,
    [Observaciones] NVARCHAR(500) NULL,
    [CreatedBy] VARCHAR(100) NOT NULL DEFAULT ('FASE2B21_MIGRATION'),
    CONSTRAINT [PK_Sistema_EmpresasMongoMap] PRIMARY KEY ([MapID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sistema_EmpresasServidores]
-- ============================================================
CREATE TABLE [dbo].[Sistema_EmpresasServidores] (
    [EmpresaServidorID] INT NOT NULL,
    [EmpresaID] INT NOT NULL,
    [ServidorID] UNIQUEIDENTIFIER NOT NULL,
    [SistemaTipoID] INT NULL,
    [RolConexion] VARCHAR(50) NOT NULL,
    [NumeroSucursalSistema] INT NULL,
    [CodigoSucursalSistema] VARCHAR(20) NULL,
    [NombreSucursalSistema] NVARCHAR(100) NULL,
    [Prioridad] INT NOT NULL DEFAULT ((1)),
    [EsPrincipal] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaActualizacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [UpdatedBy] VARCHAR(100) NULL,
    [Observaciones] NVARCHAR(500) NULL,
    CONSTRAINT [PK_Sistema_EmpresasServidores] PRIMARY KEY ([EmpresaServidorID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sistema_HorariosServicioUnidad]
-- ============================================================
CREATE TABLE [dbo].[Sistema_HorariosServicioUnidad] (
    [id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [unidad_negocio_id] NVARCHAR(50) NOT NULL,
    [dia_semana] INT NOT NULL,
    [hora_inicio_operativo] TIME NOT NULL,
    [hora_fin_operativo] TIME NOT NULL,
    [cruza_medianoche] BIT NOT NULL DEFAULT ((0)),
    [activo] BIT NOT NULL DEFAULT ((1)),
    [fecha_creacion] DATETIME2 NULL DEFAULT (sysutcdatetime()),
    [fecha_modificacion] DATETIME2 NULL DEFAULT (sysutcdatetime()),
    CONSTRAINT [PK_Sistema_HorariosServicioUnidad] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sistema_Modulos]
-- ============================================================
CREATE TABLE [dbo].[Sistema_Modulos] (
    [ModuloID] INT NOT NULL,
    [Codigo] NVARCHAR(50) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Icono] NVARCHAR(50) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [EsPrincipal] BIT NULL DEFAULT ((1)),
    [EsSatelite] BIT NULL DEFAULT ((0)),
    [EsPortal] BIT NULL DEFAULT ((0)),
    [URLExterna] NVARCHAR(255) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Sistema_Modulos] PRIMARY KEY ([ModuloID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sistema_ModulosMenus]
-- ============================================================
CREATE TABLE [dbo].[Sistema_ModulosMenus] (
    [MenuID] INT NOT NULL,
    [ModuloID] INT NOT NULL,
    [MenuPadreID] INT NULL,
    [Codigo] NVARCHAR(100) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(255) NULL,
    [Icono] NVARCHAR(50) NULL,
    [Ruta] NVARCHAR(255) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [RequierePermiso] NVARCHAR(100) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Sistema_ModulosMenus] PRIMARY KEY ([MenuID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sistema_ModulosPermisos]
-- ============================================================
CREATE TABLE [dbo].[Sistema_ModulosPermisos] (
    [PermisoID] INT NOT NULL,
    [ModuloID] INT NOT NULL,
    [Codigo] NVARCHAR(100) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(255) NULL,
    [Categoria] NVARCHAR(50) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Sistema_ModulosPermisos] PRIMARY KEY ([PermisoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sistema_ModulosVisibilidad]
-- ============================================================
CREATE TABLE [dbo].[Sistema_ModulosVisibilidad] (
    [ModuloVisibilidadID] INT NOT NULL,
    [SistemaTipoID] INT NOT NULL,
    [CodigoModulo] VARCHAR(50) NOT NULL,
    [DescripcionModulo] NVARCHAR(100) NULL,
    [Visible] BIT NULL DEFAULT ((1)),
    [OrdenMenu] INT NULL DEFAULT ((0)),
    [ConfiguracionJSON] NVARCHAR(MAX) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Sistema_ModulosVisibilidad] PRIMARY KEY ([ModuloVisibilidadID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sistema_ServidorSucursalesConfig]
-- ============================================================
CREATE TABLE [dbo].[Sistema_ServidorSucursalesConfig] (
    [ConfigID] INT NOT NULL,
    [ServidorID] UNIQUEIDENTIFIER NOT NULL,
    [SucursalNombre] NVARCHAR(200) NOT NULL,
    [SucursalCodigo] VARCHAR(50) NULL,
    [SucursalID] INT NULL,
    [VisibleEnOperaciones] BIT NOT NULL DEFAULT ((0)),
    [VisibleEnComercial] BIT NOT NULL DEFAULT ((0)),
    [MongoConfigID] VARCHAR(36) NULL,
    [FuenteMigracion] VARCHAR(50) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [UpdatedBy] VARCHAR(100) NULL,
    [Observaciones] NVARCHAR(500) NULL,
    CONSTRAINT [PK_Sistema_ServidorSucursalesConfig] PRIMARY KEY ([ConfigID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sistema_Sucursales]
-- ============================================================
CREATE TABLE [dbo].[Sistema_Sucursales] (
    [SucursalID] INT NOT NULL,
    [CodigoSucursal] VARCHAR(50) NOT NULL,
    [NombreSucursal] NVARCHAR(200) NOT NULL,
    [EmpresaID] INT NULL,
    [UnidadNegocioID] INT NULL,
    [MongoUUID] VARCHAR(36) NULL,
    [MongoEmpresaUUID] VARCHAR(36) NULL,
    [FuenteMigracion] VARCHAR(50) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [UpdatedBy] VARCHAR(100) NULL,
    [Observaciones] NVARCHAR(500) NULL,
    CONSTRAINT [PK_Sistema_Sucursales] PRIMARY KEY ([SucursalID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sistema_SucursalServidorConfig]
-- ============================================================
CREATE TABLE [dbo].[Sistema_SucursalServidorConfig] (
    [ConfigID] INT NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [SucursalNombre] VARCHAR(200) NOT NULL,
    [VisibleEnOperaciones] BIT NULL DEFAULT ((1)),
    [Activa] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Sistema_SucursalServidorConfig] PRIMARY KEY ([ConfigID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sistema_SucursalServidorMapeo]
-- ============================================================
CREATE TABLE [dbo].[Sistema_SucursalServidorMapeo] (
    [MapeoID] INT NOT NULL,
    [SucursalID] INT NOT NULL,
    [ServidorID] UNIQUEIDENTIFIER NOT NULL,
    [SucursalOrigenID] VARCHAR(100) NULL,
    [MongoSucursalUUID] VARCHAR(36) NULL,
    [MongoServidorUUID] VARCHAR(36) NULL,
    [FuenteMigracion] VARCHAR(50) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [Observaciones] NVARCHAR(500) NULL,
    CONSTRAINT [PK_Sistema_SucursalServidorMapeo] PRIMARY KEY ([MapeoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sistema_Tipos]
-- ============================================================
CREATE TABLE [dbo].[Sistema_Tipos] (
    [SistemaTipoID] INT NOT NULL,
    [CodigoSistema] VARCHAR(50) NOT NULL,
    [NombreSistema] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaActualizacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [UpdatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_Sistema_Tipos] PRIMARY KEY ([SistemaTipoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sistema_TiposVariantes]
-- ============================================================
CREATE TABLE [dbo].[Sistema_TiposVariantes] (
    [VarianteID] INT NOT NULL,
    [SistemaTipoID] INT NOT NULL,
    [VarianteNombre] VARCHAR(50) NOT NULL,
    [EsCanonico] BIT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Sistema_TiposVariantes] PRIMARY KEY ([VarianteID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sistema_TurnosOperativosUnidad]
-- ============================================================
CREATE TABLE [dbo].[Sistema_TurnosOperativosUnidad] (
    [id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [unidad_negocio_id] NVARCHAR(50) NOT NULL,
    [turno_codigo] NVARCHAR(20) NOT NULL,
    [turno_nombre] NVARCHAR(100) NOT NULL,
    [hora_inicio] TIME NOT NULL,
    [hora_fin] TIME NOT NULL,
    [cruza_medianoche] BIT NOT NULL DEFAULT ((0)),
    [aplica_ventas_dia] BIT NOT NULL DEFAULT ((1)),
    [es_turno_principal] BIT NOT NULL DEFAULT ((0)),
    [orden] INT NOT NULL DEFAULT ((0)),
    [activo] BIT NOT NULL DEFAULT ((1)),
    [fecha_creacion] DATETIME2 NULL DEFAULT (sysutcdatetime()),
    [creado_por] NVARCHAR(100) NULL,
    [fecha_modificacion] DATETIME2 NULL,
    [modificado_por] NVARCHAR(100) NULL,
    CONSTRAINT [PK_Sistema_TurnosOperativosUnidad] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sistema_UnidadesNegocioPerfilDigital]
-- ============================================================
CREATE TABLE [dbo].[Sistema_UnidadesNegocioPerfilDigital] (
    [PerfilDigitalID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] INT NOT NULL,
    [UnidadNegocioID] INT NULL,
    [ServerID] UNIQUEIDENTIFIER NULL,
    [NombreComercial] NVARCHAR(200) NULL,
    [ConceptoRestaurante] NVARCHAR(500) NULL,
    [TipoRestaurante] VARCHAR(50) NULL,
    [SegmentoPrecio] VARCHAR(30) NULL,
    [Ciudad] NVARCHAR(100) NULL,
    [Estado] NVARCHAR(100) NULL,
    [Pais] VARCHAR(50) NULL DEFAULT ('México'),
    [ZonaComercial] NVARCHAR(200) NULL,
    [SitioWebOficial] NVARCHAR(500) NULL,
    [UrlMenuDigital] NVARCHAR(500) NULL,
    [UrlReservaciones] NVARCHAR(500) NULL,
    [UrlGoogleMaps] NVARCHAR(500) NULL,
    [UrlInstagram] NVARCHAR(500) NULL,
    [UrlFacebook] NVARCHAR(500) NULL,
    [UrlTripAdvisor] NVARCHAR(500) NULL,
    [UrlOpenTable] NVARCHAR(500) NULL,
    [UrlDelivery] NVARCHAR(500) NULL,
    [TicketPromedioObjetivo] DECIMAL(18,2) NULL,
    [RangoPrecioObjetivo] VARCHAR(30) NULL,
    [Moneda] VARCHAR(10) NULL DEFAULT ('MXN'),
    [DescripcionConcepto] NVARCHAR(MAX) NULL,
    [PalabrasClave] NVARCHAR(1000) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NULL DEFAULT (getdate()),
    [UsuarioCreacion] NVARCHAR(100) NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacion] NVARCHAR(100) NULL,
    CONSTRAINT [PK_Sistema_UnidadesNegocioPerfilDigital] PRIMARY KEY ([PerfilDigitalID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Control_Ejecuciones]
-- ============================================================
CREATE TABLE [dbo].[Sync_Control_Ejecuciones] (
    [SyncControlID] INT NOT NULL,
    [SyncRunID] NVARCHAR(50) NOT NULL,
    [SyncType] NVARCHAR(50) NOT NULL,
    [ServerID] NVARCHAR(50) NULL,
    [EmpresaID] INT NULL,
    [FechaInicio] DATE NOT NULL,
    [FechaFin] DATE NOT NULL,
    [VentanaInicioHoraConfig] INT NOT NULL DEFAULT ((13)),
    [VentanaFinHoraConfig] INT NOT NULL DEFAULT ((11)),
    [IsDryRun] BIT NOT NULL DEFAULT ((1)),
    [RegistrosProcesados] INT NOT NULL DEFAULT ((0)),
    [RegistrosInsertados] INT NOT NULL DEFAULT ((0)),
    [RegistrosActualizados] INT NOT NULL DEFAULT ((0)),
    [RegistrosError] INT NOT NULL DEFAULT ((0)),
    [Status] NVARCHAR(20) NOT NULL DEFAULT ('RUNNING'),
    [ErrorMessage] NVARCHAR(MAX) NULL,
    [StartedAtMexico] DATETIME2 NOT NULL,
    [FinishedAtMexico] DATETIME2 NULL,
    [DurationSeconds] INT NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Sync_Control_Ejecuciones] PRIMARY KEY ([SyncControlID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Customers]
-- ============================================================
CREATE TABLE [dbo].[Sync_Customers] (
    [customer_id] VARCHAR(64) NOT NULL,
    [full_name] NVARCHAR(200) NOT NULL,
    [commercial_name] NVARCHAR(200) NULL,
    [email] VARCHAR(150) NULL,
    [phone] VARCHAR(32) NULL,
    [affiliate_tier] VARCHAR(16) NULL DEFAULT ('BRONZE'),
    [sync_status] VARCHAR(16) NULL DEFAULT ('SYNCHRONIZED'),
    [last_sync] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Sync_Customers] PRIMARY KEY ([customer_id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Impuestos_Origen]
-- ============================================================
CREATE TABLE [dbo].[Sync_Impuestos_Origen] (
    [MapeoID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [ServerID] UNIQUEIDENTIFIER NOT NULL,
    [SystemType] VARCHAR(50) NOT NULL,
    [CodigoImpuestoOrigen] VARCHAR(50) NOT NULL,
    [NombreImpuestoOrigen] NVARCHAR(200) NULL,
    [TasaOrigen] DECIMAL(10,4) NULL,
    [TipoFactorOrigen] VARCHAR(20) NULL,
    [ImpuestoCanonicoID] UNIQUEIDENTIFIER NULL,
    [TasaCanonicoID] UNIQUEIDENTIFIER NULL,
    [EstadoMapeo] VARCHAR(30) NOT NULL,
    [Observaciones] NVARCHAR(500) NULL,
    [SyncRunID] VARCHAR(100) NULL,
    [FechaSincronizacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [FechaCreacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Sync_Impuestos_Origen] PRIMARY KEY ([MapeoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Inventory]
-- ============================================================
CREATE TABLE [dbo].[Sync_Inventory] (
    [sku] VARCHAR(64) NOT NULL,
    [item_name] NVARCHAR(200) NOT NULL,
    [stock_qty] INT NULL DEFAULT ((0)),
    [min_qty_warning] INT NULL DEFAULT ((10)),
    [warehouse] NVARCHAR(100) NOT NULL,
    [last_audit] DATETIME NULL DEFAULT (getdate()),
    [sync_status] VARCHAR(16) NULL DEFAULT ('ONLINE'),
    CONSTRAINT [PK_Sync_Inventory] PRIMARY KEY ([sku])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_KPI_Ventas_Unidades]
-- ============================================================
CREATE TABLE [dbo].[Sync_KPI_Ventas_Unidades] (
    [id] INT NOT NULL,
    [UnidadID] VARCHAR(50) NOT NULL,
    [UnidadNombre] NVARCHAR(100) NOT NULL,
    [Mes] VARCHAR(50) NOT NULL,
    [Anio] INT NOT NULL,
    [Ventas_Reales_M] DECIMAL(18,4) NULL DEFAULT ((0)),
    [Proyeccion_Ventas] DECIMAL(18,4) NULL DEFAULT ((0)),
    [Meta_Mensual] DECIMAL(18,4) NULL DEFAULT ((0)),
    [PorcentajeCumplimiento] DECIMAL(5,2) NULL DEFAULT ((0)),
    [UltimaActualizacion] DATETIME NULL DEFAULT (getdate()),
    [Dias_Con_Ventas] DECIMAL(10,2) NULL DEFAULT ((30.0)),
    [Proyeccion_Anual_Ventas] DECIMAL(18,4) NULL DEFAULT ((0)),
    CONSTRAINT [PK_Sync_KPI_Ventas_Unidades] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Logs]
-- ============================================================
CREATE TABLE [dbo].[Sync_Logs] (
    [id] INT NOT NULL,
    [service] NVARCHAR(100) NOT NULL,
    [type] NVARCHAR(20) NOT NULL,
    [message] NVARCHAR(MAX) NOT NULL,
    [timestamp] DATETIME NULL DEFAULT (getdate()),
    [operador] NVARCHAR(100) NULL DEFAULT ('PYTHON_AUTOGESTIVE_AGENT'),
    CONSTRAINT [PK_Sync_Logs] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Menus]
-- ============================================================
CREATE TABLE [dbo].[Sync_Menus] (
    [id] INT NOT NULL,
    [titulo] NVARCHAR(100) NOT NULL,
    [label] NVARCHAR(100) NOT NULL,
    [icon] NVARCHAR(50) NOT NULL,
    [route] NVARCHAR(100) NOT NULL,
    [active] BIT NULL DEFAULT ((1)),
    [orden] INT NOT NULL,
    [rol_permitido] NVARCHAR(100) NULL DEFAULT ('OPERADOR_EDARSA'),
    [ultima_actualizacion] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Sync_Menus] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Mesas]
-- ============================================================
CREATE TABLE [dbo].[Sync_Mesas] (
    [ID] INT NOT NULL,
    [MesaRegistroID] NVARCHAR(50) NOT NULL,
    [ServerID] NVARCHAR(50) NOT NULL,
    [SucursalID] NVARCHAR(20) NOT NULL,
    [SucursalNombre] NVARCHAR(100) NULL,
    [FechaOperacion] DATE NOT NULL,
    [MesaNumero] NVARCHAR(20) NOT NULL,
    [MesaNombre] NVARCHAR(50) NULL,
    [ZonaID] NVARCHAR(20) NULL,
    [ZonaNombre] NVARCHAR(50) NULL,
    [Capacidad] INT NULL DEFAULT ((4)),
    [TotalCuentas] INT NULL DEFAULT ((0)),
    [TotalComensales] INT NULL DEFAULT ((0)),
    [VentaTotal] DECIMAL(18,2) NULL DEFAULT ((0)),
    [TicketPromedio] DECIMAL(18,2) NULL DEFAULT ((0)),
    [TiempoPromedioOcupacion] INT NULL DEFAULT ((0)),
    [RotacionDia] DECIMAL(8,2) NULL DEFAULT ((0)),
    [EstadoActual] NVARCHAR(20) NULL DEFAULT ('LIBRE'),
    [CuentaActualID] NVARCHAR(50) NULL,
    [MeseroActualID] NVARCHAR(50) NULL,
    [MeseroActualNombre] NVARCHAR(100) NULL,
    [HoraAperturaCuenta] DATETIME2 NULL,
    [FechaSync] DATETIME2 NULL DEFAULT (getutcdate()),
    CONSTRAINT [PK_Sync_Mesas] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Metas_Comerciales]
-- ============================================================
CREATE TABLE [dbo].[Sync_Metas_Comerciales] (
    [ID] INT NOT NULL,
    [MetaID] NVARCHAR(50) NOT NULL,
    [ServerID] NVARCHAR(50) NOT NULL,
    [SucursalID] NVARCHAR(20) NOT NULL,
    [SucursalNombre] NVARCHAR(100) NULL,
    [Anio] INT NOT NULL,
    [Mes] INT NOT NULL,
    [MetaVentaBruta] DECIMAL(18,2) NULL DEFAULT ((0)),
    [MetaVentaNeta] DECIMAL(18,2) NULL DEFAULT ((0)),
    [MetaTicketPromedio] DECIMAL(18,2) NULL DEFAULT ((0)),
    [MetaCuentas] INT NULL DEFAULT ((0)),
    [MetaComensales] INT NULL DEFAULT ((0)),
    [MetaProductosMes] INT NULL DEFAULT ((0)),
    [VentaBrutaActual] DECIMAL(18,2) NULL DEFAULT ((0)),
    [VentaNetaActual] DECIMAL(18,2) NULL DEFAULT ((0)),
    [TicketPromedioActual] DECIMAL(18,2) NULL DEFAULT ((0)),
    [CuentasActual] INT NULL DEFAULT ((0)),
    [ComensalesActual] INT NULL DEFAULT ((0)),
    [PorcentajeCumplimiento] DECIMAL(8,2) NULL DEFAULT ((0)),
    [DiasTranscurridos] INT NULL DEFAULT ((0)),
    [DiasRestantes] INT NULL DEFAULT ((0)),
    [ProyeccionMes] DECIMAL(18,2) NULL DEFAULT ((0)),
    [FechaActualizacion] DATETIME2 NULL DEFAULT (getutcdate()),
    [FechaSync] DATETIME2 NULL DEFAULT (getutcdate()),
    [Activo] BIT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Sync_Metas_Comerciales] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Movimientos_Detalle]
-- ============================================================
CREATE TABLE [dbo].[Sync_Movimientos_Detalle] (
    [ID] INT NOT NULL,
    [MovimientoID] NVARCHAR(50) NOT NULL,
    [ServerID] NVARCHAR(50) NOT NULL,
    [SucursalID] NVARCHAR(20) NOT NULL,
    [FechaOperacion] DATE NOT NULL,
    [FechaHora] DATETIME2 NOT NULL,
    [CuentaID] NVARCHAR(50) NULL,
    [CuentaFolio] NVARCHAR(50) NULL,
    [MesaNumero] NVARCHAR(20) NULL,
    [MeseroID] NVARCHAR(50) NULL,
    [MeseroNombre] NVARCHAR(100) NULL,
    [ProductoID] NVARCHAR(50) NOT NULL,
    [ProductoCodigo] NVARCHAR(50) NULL,
    [ProductoNombre] NVARCHAR(200) NULL,
    [FamiliaID] NVARCHAR(50) NULL,
    [FamiliaNombre] NVARCHAR(100) NULL,
    [SubFamiliaID] NVARCHAR(50) NULL,
    [SubFamiliaNombre] NVARCHAR(100) NULL,
    [Cantidad] DECIMAL(18,4) NULL DEFAULT ((0)),
    [PrecioUnitario] DECIMAL(18,4) NULL DEFAULT ((0)),
    [Descuento] DECIMAL(18,4) NULL DEFAULT ((0)),
    [Impuesto] DECIMAL(18,4) NULL DEFAULT ((0)),
    [Subtotal] DECIMAL(18,4) NULL DEFAULT ((0)),
    [Total] DECIMAL(18,4) NULL DEFAULT ((0)),
    [TipoMovimiento] NVARCHAR(20) NULL DEFAULT ('VENTA'),
    [Cancelado] BIT NULL DEFAULT ((0)),
    [FechaSync] DATETIME2 NULL DEFAULT (getutcdate()),
    CONSTRAINT [PK_Sync_Movimientos_Detalle] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_PAX_Detalle]
-- ============================================================
CREATE TABLE [dbo].[Sync_PAX_Detalle] (
    [ID] INT NOT NULL,
    [PAXRegistroID] NVARCHAR(50) NOT NULL,
    [ServerID] NVARCHAR(50) NOT NULL,
    [SucursalID] NVARCHAR(20) NOT NULL,
    [SucursalNombre] NVARCHAR(100) NULL,
    [FechaOperacion] DATE NOT NULL,
    [FechaHora] DATETIME2 NOT NULL,
    [CuentaID] NVARCHAR(50) NULL,
    [CuentaFolio] NVARCHAR(50) NULL,
    [MesaNumero] NVARCHAR(20) NULL,
    [MeseroID] NVARCHAR(50) NULL,
    [MeseroNombre] NVARCHAR(100) NULL,
    [NumeroComensales] INT NOT NULL,
    [TipoPAX] NVARCHAR(20) NULL DEFAULT ('NORMAL'),
    [VentaCuenta] DECIMAL(18,2) NULL DEFAULT ((0)),
    [ConsumoPromedioPAX] DECIMAL(18,2) NULL DEFAULT ((0)),
    [TiempoMesa] INT NULL DEFAULT ((0)),
    [HoraEntrada] DATETIME2 NULL,
    [HoraSalida] DATETIME2 NULL,
    [Turno] NVARCHAR(20) NULL,
    [DiaSemana] NVARCHAR(20) NULL,
    [FechaSync] DATETIME2 NULL DEFAULT (getutcdate()),
    CONSTRAINT [PK_Sync_PAX_Detalle] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Precios_Historicos]
-- ============================================================
CREATE TABLE [dbo].[Sync_Precios_Historicos] (
    [ID] INT NOT NULL,
    [PrecioHistoricoID] NVARCHAR(50) NOT NULL,
    [ServerID] NVARCHAR(50) NOT NULL,
    [SucursalID] NVARCHAR(20) NOT NULL,
    [ProductoID] NVARCHAR(50) NOT NULL,
    [ProductoCodigo] NVARCHAR(50) NULL,
    [ProductoNombre] NVARCHAR(200) NULL,
    [FechaVigencia] DATE NOT NULL,
    [FechaFinVigencia] DATE NULL,
    [PrecioBase] DECIMAL(18,4) NOT NULL,
    [PrecioFinal] DECIMAL(18,4) NOT NULL,
    [ImpuestoIncluido] BIT NULL DEFAULT ((1)),
    [TasaImpuesto] DECIMAL(8,4) NULL DEFAULT ((0.16)),
    [PrecioAnterior] DECIMAL(18,4) NULL,
    [VariacionPorcentaje] DECIMAL(8,2) NULL,
    [MotivosCambio] NVARCHAR(200) NULL,
    [UsuarioModificacion] NVARCHAR(100) NULL,
    [FechaSync] DATETIME2 NULL DEFAULT (getutcdate()),
    CONSTRAINT [PK_Sync_Precios_Historicos] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Productos]
-- ============================================================
CREATE TABLE [dbo].[Sync_Productos] (
    [ProductoID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [ServerID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] INT NULL,
    [UnidadNegocioID] INT NULL,
    [SystemType] NVARCHAR(50) NOT NULL,
    [CodigoFuente] NVARCHAR(100) NOT NULL,
    [CodigoBarras] NVARCHAR(100) NULL,
    [Nombre] NVARCHAR(300) NOT NULL,
    [NombreCorto] NVARCHAR(100) NULL,
    [Descripcion] NVARCHAR(1000) NULL,
    [FamiliaID] UNIQUEIDENTIFIER NULL,
    [SubFamiliaID] UNIQUEIDENTIFIER NULL,
    [FamiliaCodigoFuente] NVARCHAR(100) NULL,
    [SubFamiliaCodigoFuente] NVARCHAR(100) NULL,
    [FamiliaNombre] NVARCHAR(200) NULL,
    [SubFamiliaNombre] NVARCHAR(200) NULL,
    [TipoProducto] NVARCHAR(50) NULL,
    [EsVendible] BIT NULL DEFAULT ((1)),
    [EsInventariable] BIT NULL DEFAULT ((0)),
    [EsCompuesto] BIT NULL DEFAULT ((0)),
    [TieneReceta] BIT NULL DEFAULT ((0)),
    [TieneSubRecetas] BIT NULL DEFAULT ((0)),
    [UnidadVenta] NVARCHAR(20) NULL,
    [UnidadInventario] NVARCHAR(20) NULL,
    [PrecioVenta] DECIMAL(18,4) NULL DEFAULT ((0)),
    [PrecioSinImpuestos] DECIMAL(18,4) NULL DEFAULT ((0)),
    [TasaImpuesto] DECIMAL(5,2) NULL DEFAULT ((0)),
    [CostoReceta] DECIMAL(18,4) NULL DEFAULT ((0)),
    [CostoPromedio] DECIMAL(18,4) NULL DEFAULT ((0)),
    [UltimoCosto] DECIMAL(18,4) NULL DEFAULT ((0)),
    [CostoEstandar] DECIMAL(18,4) NULL DEFAULT ((0)),
    [MargenBrutoPesos] DECIMAL(18,4) NULL DEFAULT ((0)),
    [MargenBrutoPorcentaje] DECIMAL(5,2) NULL DEFAULT ((0)),
    [MargenObjetivo] DECIMAL(5,2) NULL,
    [CantidadComponentesReceta] INT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [SyncRunID] NVARCHAR(100) NULL,
    [SyncedAtMexico] DATETIME2 NULL DEFAULT (sysdatetime()),
    [FechaUltimoCosteo] DATETIME2 NULL,
    [SourceStatus] NVARCHAR(50) NULL DEFAULT ('SYNCED'),
    [HashOrigen] NVARCHAR(64) NULL,
    [FechaCreacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Sync_Productos] PRIMARY KEY ([ProductoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Productos_Elaborados]
-- ============================================================
CREATE TABLE [dbo].[Sync_Productos_Elaborados] (
    [ElaboradoDetalleID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [InsumoElaboradoID] UNIQUEIDENTIFIER NOT NULL,
    [ServerID] UNIQUEIDENTIFIER NOT NULL,
    [SystemType] NVARCHAR(50) NOT NULL,
    [InsumoElaboradoCodigoFuente] NVARCHAR(100) NOT NULL,
    [InsumoComponenteID] UNIQUEIDENTIFIER NULL,
    [ComponenteCodigoFuente] NVARCHAR(100) NOT NULL,
    [ComponenteNombre] NVARCHAR(300) NOT NULL,
    [Cantidad] DECIMAL(18,6) NOT NULL,
    [UnidadMedida] NVARCHAR(50) NOT NULL,
    [CostoUnitario] DECIMAL(18,6) NULL DEFAULT ((0)),
    [CostoTotal] DECIMAL(18,6) NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [SyncRunID] NVARCHAR(100) NULL,
    [SyncedAtMexico] DATETIME2 NULL DEFAULT (sysdatetime()),
    [SourceStatus] NVARCHAR(50) NULL DEFAULT ('SYNCED'),
    [FechaCreacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Sync_Productos_Elaborados] PRIMARY KEY ([ElaboradoDetalleID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Productos_Familias]
-- ============================================================
CREATE TABLE [dbo].[Sync_Productos_Familias] (
    [FamiliaID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [ServerID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] INT NULL,
    [UnidadNegocioID] INT NULL,
    [SystemType] NVARCHAR(50) NOT NULL,
    [CodigoFuente] NVARCHAR(100) NOT NULL,
    [Nombre] NVARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [SyncRunID] NVARCHAR(100) NULL,
    [SyncedAtMexico] DATETIME2 NULL DEFAULT (sysdatetime()),
    [SourceStatus] NVARCHAR(50) NULL DEFAULT ('SYNCED'),
    [HashOrigen] NVARCHAR(64) NULL,
    [FechaCreacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Sync_Productos_Familias] PRIMARY KEY ([FamiliaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Productos_Insumos]
-- ============================================================
CREATE TABLE [dbo].[Sync_Productos_Insumos] (
    [InsumoID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [ServerID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] INT NULL,
    [SystemType] NVARCHAR(50) NOT NULL,
    [CodigoFuente] NVARCHAR(100) NOT NULL,
    [Nombre] NVARCHAR(300) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [GrupoInsumoCodigoFuente] NVARCHAR(100) NULL,
    [GrupoInsumoNombre] NVARCHAR(200) NULL,
    [UnidadMedida] NVARCHAR(50) NOT NULL,
    [Costo] DECIMAL(18,6) NULL DEFAULT ((0)),
    [CostoPromedio] DECIMAL(18,6) NULL DEFAULT ((0)),
    [UltimoCosto] DECIMAL(18,6) NULL DEFAULT ((0)),
    [CostoEstandar] DECIMAL(18,6) NULL DEFAULT ((0)),
    [CostoConImpuestos] DECIMAL(18,6) NULL DEFAULT ((0)),
    [EsElaborado] BIT NULL DEFAULT ((0)),
    [RendimientoElaborado] DECIMAL(10,4) NULL,
    [MermaPorcentaje] DECIMAL(5,2) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [SyncRunID] NVARCHAR(100) NULL,
    [SyncedAtMexico] DATETIME2 NULL DEFAULT (sysdatetime()),
    [FechaUltimoCosto] DATETIME2 NULL,
    [SourceStatus] NVARCHAR(50) NULL DEFAULT ('SYNCED'),
    [HashOrigen] NVARCHAR(64) NULL,
    [FechaCreacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Sync_Productos_Insumos] PRIMARY KEY ([InsumoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Productos_Recetas]
-- ============================================================
CREATE TABLE [dbo].[Sync_Productos_Recetas] (
    [RecetaDetalleID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [ProductoID] UNIQUEIDENTIFIER NOT NULL,
    [ServerID] UNIQUEIDENTIFIER NOT NULL,
    [SystemType] NVARCHAR(50) NOT NULL,
    [ProductoCodigoFuente] NVARCHAR(100) NOT NULL,
    [InsumoID] UNIQUEIDENTIFIER NULL,
    [SubRecetaProductoID] UNIQUEIDENTIFIER NULL,
    [ComponenteCodigoFuente] NVARCHAR(100) NOT NULL,
    [ComponenteNombre] NVARCHAR(300) NOT NULL,
    [TipoComponente] NVARCHAR(50) NOT NULL,
    [Cantidad] DECIMAL(18,6) NOT NULL,
    [UnidadMedida] NVARCHAR(50) NOT NULL,
    [CostoUnitario] DECIMAL(18,6) NULL DEFAULT ((0)),
    [CostoTotal] DECIMAL(18,6) NULL DEFAULT ((0)),
    [PorcentajeCostoTotal] DECIMAL(5,2) NULL DEFAULT ((0)),
    [NivelExplosion] INT NULL DEFAULT ((1)),
    [OrdenVisual] INT NULL DEFAULT ((0)),
    [EsElaborado] BIT NULL DEFAULT ((0)),
    [RendimientoElaborado] DECIMAL(10,4) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [SyncRunID] NVARCHAR(100) NULL,
    [SyncedAtMexico] DATETIME2 NULL DEFAULT (sysdatetime()),
    [SourceStatus] NVARCHAR(50) NULL DEFAULT ('SYNCED'),
    [FechaCreacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Sync_Productos_Recetas] PRIMARY KEY ([RecetaDetalleID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Productos_SubFamilias]
-- ============================================================
CREATE TABLE [dbo].[Sync_Productos_SubFamilias] (
    [SubFamiliaID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [FamiliaID] UNIQUEIDENTIFIER NULL,
    [ServerID] UNIQUEIDENTIFIER NOT NULL,
    [SystemType] NVARCHAR(50) NOT NULL,
    [CodigoFuente] NVARCHAR(100) NOT NULL,
    [FamiliaCodigoFuente] NVARCHAR(100) NULL,
    [Nombre] NVARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [SyncRunID] NVARCHAR(100) NULL,
    [SyncedAtMexico] DATETIME2 NULL DEFAULT (sysdatetime()),
    [SourceStatus] NVARCHAR(50) NULL DEFAULT ('SYNCED'),
    [HashOrigen] NVARCHAR(64) NULL,
    [FechaCreacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Sync_Productos_SubFamilias] PRIMARY KEY ([SubFamiliaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Purchases]
-- ============================================================
CREATE TABLE [dbo].[Sync_Purchases] (
    [id] VARCHAR(64) NOT NULL,
    [provider_name] NVARCHAR(200) NOT NULL,
    [branch] NVARCHAR(100) NOT NULL,
    [items_detail] NVARCHAR(MAX) NULL,
    [total_amount] NUMERIC(12,2) NOT NULL,
    [status] VARCHAR(32) NULL DEFAULT ('PENDIENTE'),
    [created_at] DATETIME NULL DEFAULT (getdate()),
    [sync_status] VARCHAR(16) NULL DEFAULT ('ONLINE'),
    CONSTRAINT [PK_Sync_Purchases] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Response_Cache]
-- ============================================================
CREATE TABLE [dbo].[Sync_Response_Cache] (
    [id] INT NOT NULL,
    [RequestHash] VARCHAR(64) NOT NULL,
    [ServiceSource] VARCHAR(64) NOT NULL,
    [RequestPayload] NVARCHAR(MAX) NULL,
    [ResponsePayload] NVARCHAR(MAX) NULL,
    [TokenCostFraction] NUMERIC(10,6) NULL DEFAULT ((0.0)),
    [CacheDurationMinutes] INT NULL DEFAULT ((120)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    [ExpiresAt] DATETIME NULL,
    [HitCount] INT NULL DEFAULT ((0)),
    CONSTRAINT [PK_Sync_Response_Cache] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Sales]
-- ============================================================
CREATE TABLE [dbo].[Sync_Sales] (
    [id] VARCHAR(64) NOT NULL,
    [branch] NVARCHAR(100) NOT NULL,
    [customer_id] VARCHAR(64) NULL,
    [items] NVARCHAR(MAX) NULL,
    [total] NUMERIC(18,2) NOT NULL DEFAULT ((0.00)),
    [currency] VARCHAR(3) NULL DEFAULT ('MXN'),
    [status] VARCHAR(32) NULL DEFAULT ('PENDIENTE'),
    [created_at] DATETIME NULL DEFAULT (getdate()),
    [last_modified] DATETIME NULL DEFAULT (getdate()),
    [sync_hash] VARCHAR(64) NULL,
    [IdTransaccion] VARCHAR(64) NULL,
    [UnidadNegocio] NVARCHAR(100) NULL,
    [MontoTotal] NUMERIC(18,2) NULL,
    [Pax] INT NULL,
    [NumeroTicket] VARCHAR(64) NULL,
    [FechaHora] DATETIME NULL,
    CONSTRAINT [PK_Sync_Sales] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Ticket_Perfecto]
-- ============================================================
CREATE TABLE [dbo].[Sync_Ticket_Perfecto] (
    [ID] INT NOT NULL,
    [TicketID] NVARCHAR(50) NOT NULL,
    [ServerID] NVARCHAR(50) NOT NULL,
    [SucursalID] NVARCHAR(20) NOT NULL,
    [SucursalNombre] NVARCHAR(100) NULL,
    [FechaOperacion] DATE NOT NULL,
    [TotalCuentas] INT NULL DEFAULT ((0)),
    [TotalComensales] INT NULL DEFAULT ((0)),
    [VentaTotal] DECIMAL(18,2) NULL DEFAULT ((0)),
    [TicketPromedioReal] DECIMAL(18,2) NULL DEFAULT ((0)),
    [TicketPerfectoObjetivo] DECIMAL(18,2) NULL DEFAULT ((0)),
    [PorcentajeCumplimiento] DECIMAL(8,2) NULL DEFAULT ((0)),
    [CuentasBajoObjetivo] INT NULL DEFAULT ((0)),
    [CuentasSobreObjetivo] INT NULL DEFAULT ((0)),
    [CuentasEnRango] INT NULL DEFAULT ((0)),
    [PromedioEntradas] DECIMAL(8,2) NULL DEFAULT ((0)),
    [PromedioFuertes] DECIMAL(8,2) NULL DEFAULT ((0)),
    [PromedioBebidas] DECIMAL(8,2) NULL DEFAULT ((0)),
    [PromedioPostres] DECIMAL(8,2) NULL DEFAULT ((0)),
    [TiempoPromedioMesa] INT NULL DEFAULT ((0)),
    [RotacionMesas] DECIMAL(8,2) NULL DEFAULT ((0)),
    [FechaSync] DATETIME2 NULL DEFAULT (getutcdate()),
    [MetadatosJSON] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_Sync_Ticket_Perfecto] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Token_Ledger]
-- ============================================================
CREATE TABLE [dbo].[Sync_Token_Ledger] (
    [LedgerID] INT NOT NULL,
    [OperadorID] VARCHAR(64) NULL DEFAULT ('sk-emergent-universal-gate'),
    [ConsuDate] DATE NULL DEFAULT (CONVERT([date],getdate())),
    [TokensInput] INT NULL DEFAULT ((0)),
    [TokensOutput] INT NULL DEFAULT ((0)),
    [EstimatedCostUSD] NUMERIC(12,4) NULL DEFAULT ((0.0000)),
    [AhorroAcumuladoUSD] NUMERIC(12,4) NULL DEFAULT ((0.0000)),
    [HitRatioPercent] NUMERIC(5,2) NULL DEFAULT ((0.00)),
    CONSTRAINT [PK_Sync_Token_Ledger] PRIMARY KEY ([LedgerID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Ventas_Historicas]
-- ============================================================
CREATE TABLE [dbo].[Sync_Ventas_Historicas] (
    [SyncVentaHistoricaID] INT NOT NULL,
    [ServerID] NVARCHAR(50) NOT NULL,
    [EmpresaID] INT NOT NULL,
    [SucursalID] NVARCHAR(50) NULL,
    [UnidadNegocioID] NVARCHAR(50) NULL,
    [SystemType] NVARCHAR(20) NOT NULL,
    [FechaOperacion] DATE NOT NULL,
    [VentanaInicio] TIME NOT NULL,
    [VentanaFin] TIME NOT NULL,
    [CruzaMedianoche] BIT NOT NULL DEFAULT ((1)),
    [VentanaInicioHoraConfig] INT NOT NULL DEFAULT ((13)),
    [VentanaFinHoraConfig] INT NOT NULL DEFAULT ((11)),
    [VentaTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [VentaEfectivo] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [VentaTarjeta] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [VentaOtros] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [NumTickets] INT NOT NULL DEFAULT ((0)),
    [TicketPromedio] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [SyncRunID] NVARCHAR(50) NOT NULL,
    [SourceStatus] NVARCHAR(20) NOT NULL,
    [SourceType] NVARCHAR(20) NOT NULL,
    [SyncedAtMexico] DATETIME2 NOT NULL,
    [RowHash] NVARCHAR(64) NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [UpdatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Sync_Ventas_Historicas] PRIMARY KEY ([SyncVentaHistoricaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Ventas_PorDiaSemana]
-- ============================================================
CREATE TABLE [dbo].[Sync_Ventas_PorDiaSemana] (
    [SyncVentaPorDiaSemanaID] INT NOT NULL,
    [ServerID] NVARCHAR(50) NOT NULL,
    [EmpresaID] INT NOT NULL,
    [SucursalID] NVARCHAR(50) NULL,
    [UnidadNegocioID] NVARCHAR(50) NULL,
    [SystemType] NVARCHAR(20) NOT NULL,
    [FechaInicioPeriodo] DATE NOT NULL,
    [FechaFinPeriodo] DATE NOT NULL,
    [DiaSemana] INT NOT NULL,
    [DiaSemananombre] NVARCHAR(20) NOT NULL,
    [VentanaInicioHoraConfig] INT NOT NULL DEFAULT ((13)),
    [VentanaFinHoraConfig] INT NOT NULL DEFAULT ((11)),
    [VentaPromedio] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [VentaMin] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [VentaMax] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [NumDiasConDatos] INT NOT NULL DEFAULT ((0)),
    [SyncRunID] NVARCHAR(50) NOT NULL,
    [SourceStatus] NVARCHAR(20) NOT NULL,
    [SourceType] NVARCHAR(20) NOT NULL,
    [SyncedAtMexico] DATETIME2 NOT NULL,
    [RowHash] NVARCHAR(64) NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [UpdatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Sync_Ventas_PorDiaSemana] PRIMARY KEY ([SyncVentaPorDiaSemanaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Ventas_PorHora]
-- ============================================================
CREATE TABLE [dbo].[Sync_Ventas_PorHora] (
    [SyncVentaPorHoraID] INT NOT NULL,
    [ServerID] NVARCHAR(50) NOT NULL,
    [EmpresaID] INT NOT NULL,
    [SucursalID] NVARCHAR(50) NULL,
    [UnidadNegocioID] NVARCHAR(50) NULL,
    [SystemType] NVARCHAR(20) NOT NULL,
    [FechaOperacion] DATE NOT NULL,
    [Hora] INT NOT NULL,
    [VentanaInicio] TIME NOT NULL,
    [VentanaFin] TIME NOT NULL,
    [CruzaMedianoche] BIT NOT NULL DEFAULT ((1)),
    [VentanaInicioHoraConfig] INT NOT NULL DEFAULT ((13)),
    [VentanaFinHoraConfig] INT NOT NULL DEFAULT ((11)),
    [VentaHora] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [NumTicketsHora] INT NOT NULL DEFAULT ((0)),
    [SyncRunID] NVARCHAR(50) NOT NULL,
    [SourceStatus] NVARCHAR(20) NOT NULL,
    [SourceType] NVARCHAR(20) NOT NULL,
    [SyncedAtMexico] DATETIME2 NOT NULL,
    [RowHash] NVARCHAR(64) NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [UpdatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Sync_Ventas_PorHora] PRIMARY KEY ([SyncVentaPorHoraID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Vtiger_Contactos]
-- ============================================================
CREATE TABLE [dbo].[Sync_Vtiger_Contactos] (
    [SyncID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [VtigerID] VARCHAR(50) NOT NULL,
    [ContactoNo] VARCHAR(50) NULL,
    [Nombre] NVARCHAR(200) NULL,
    [Apellido] NVARCHAR(200) NULL,
    [Email] NVARCHAR(200) NULL,
    [Telefono] VARCHAR(50) NULL,
    [Celular] VARCHAR(50) NULL,
    [Titulo] NVARCHAR(200) NULL,
    [Departamento] NVARCHAR(200) NULL,
    [CuentaVtigerID] VARCHAR(50) NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [Ciudad] NVARCHAR(100) NULL,
    [Estado] NVARCHAR(100) NULL,
    [Pais] NVARCHAR(100) NULL,
    [UsuarioAsignadoVtiger] VARCHAR(50) NULL,
    [FechaCreacionVtiger] DATETIME NULL,
    [FechaModificacionVtiger] DATETIME NULL,
    [FechaCreacionLocal] DATETIME NULL DEFAULT (getdate()),
    [FechaUltimaSync] DATETIME NULL DEFAULT (getdate()),
    [PendientePush] BIT NULL DEFAULT ((0)),
    [OrigenLocal] BIT NULL DEFAULT ((0)),
    [PendienteDelete] BIT NULL DEFAULT ((0)),
    [PushError] NVARCHAR(500) NULL,
    [FechaUltimoPush] DATETIME NULL,
    CONSTRAINT [PK_Sync_Vtiger_Contactos] PRIMARY KEY ([SyncID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Vtiger_Cuentas]
-- ============================================================
CREATE TABLE [dbo].[Sync_Vtiger_Cuentas] (
    [SyncID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [VtigerID] VARCHAR(50) NOT NULL,
    [CuentaNo] VARCHAR(50) NULL,
    [NombreCuenta] NVARCHAR(500) NULL,
    [Website] NVARCHAR(500) NULL,
    [Telefono] VARCHAR(50) NULL,
    [Fax] VARCHAR(50) NULL,
    [Email] NVARCHAR(200) NULL,
    [Industria] NVARCHAR(100) NULL,
    [TipoCuenta] NVARCHAR(100) NULL,
    [IngresoAnual] DECIMAL(18,2) NULL,
    [NumEmpleados] INT NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [Ciudad] NVARCHAR(100) NULL,
    [Estado] NVARCHAR(100) NULL,
    [Pais] NVARCHAR(100) NULL,
    [UsuarioAsignadoVtiger] VARCHAR(50) NULL,
    [FechaCreacionVtiger] DATETIME NULL,
    [FechaModificacionVtiger] DATETIME NULL,
    [FechaCreacionLocal] DATETIME NULL DEFAULT (getdate()),
    [FechaUltimaSync] DATETIME NULL DEFAULT (getdate()),
    [PendientePush] BIT NULL DEFAULT ((0)),
    [OrigenLocal] BIT NULL DEFAULT ((0)),
    [PendienteDelete] BIT NULL DEFAULT ((0)),
    [PushError] NVARCHAR(500) NULL,
    [FechaUltimoPush] DATETIME NULL,
    CONSTRAINT [PK_Sync_Vtiger_Cuentas] PRIMARY KEY ([SyncID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Vtiger_Leads]
-- ============================================================
CREATE TABLE [dbo].[Sync_Vtiger_Leads] (
    [SyncID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [VtigerID] VARCHAR(50) NOT NULL,
    [LeadNo] VARCHAR(50) NULL,
    [Nombre] NVARCHAR(200) NULL,
    [Apellido] NVARCHAR(200) NULL,
    [Empresa] NVARCHAR(500) NULL,
    [Email] NVARCHAR(200) NULL,
    [Telefono] VARCHAR(50) NULL,
    [Celular] VARCHAR(50) NULL,
    [Website] NVARCHAR(500) NULL,
    [Industria] NVARCHAR(100) NULL,
    [FuenteLead] NVARCHAR(100) NULL,
    [Estatus] NVARCHAR(50) NULL,
    [IngresoAnual] DECIMAL(18,2) NULL,
    [NumEmpleados] INT NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [Ciudad] NVARCHAR(100) NULL,
    [Estado] NVARCHAR(100) NULL,
    [Pais] NVARCHAR(100) NULL,
    [UsuarioAsignadoVtiger] VARCHAR(50) NULL,
    [FechaCreacionVtiger] DATETIME NULL,
    [FechaModificacionVtiger] DATETIME NULL,
    [FechaCreacionLocal] DATETIME NULL DEFAULT (getdate()),
    [FechaUltimaSync] DATETIME NULL DEFAULT (getdate()),
    [PendientePush] BIT NULL DEFAULT ((0)),
    [OrigenLocal] BIT NULL DEFAULT ((0)),
    [PendienteDelete] BIT NULL DEFAULT ((0)),
    [PushError] NVARCHAR(500) NULL,
    [FechaUltimoPush] DATETIME NULL,
    CONSTRAINT [PK_Sync_Vtiger_Leads] PRIMARY KEY ([SyncID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Vtiger_Log]
-- ============================================================
CREATE TABLE [dbo].[Sync_Vtiger_Log] (
    [LogID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [RunID] VARCHAR(50) NOT NULL,
    [Direccion] VARCHAR(20) NULL DEFAULT ('vtiger_to_sql'),
    [FechaInicio] DATETIME NOT NULL,
    [FechaFin] DATETIME NULL,
    [TotalObtenidos] INT NULL DEFAULT ((0)),
    [TotalInsertados] INT NULL DEFAULT ((0)),
    [TotalActualizados] INT NULL DEFAULT ((0)),
    [Errores] INT NULL DEFAULT ((0)),
    [ResultadoJSON] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_Sync_Vtiger_Log] PRIMARY KEY ([LogID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sync_Vtiger_Oportunidades]
-- ============================================================
CREATE TABLE [dbo].[Sync_Vtiger_Oportunidades] (
    [SyncID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [VtigerID] VARCHAR(50) NOT NULL,
    [OportunidadNo] VARCHAR(50) NULL,
    [NombreOportunidad] NVARCHAR(500) NULL,
    [Monto] DECIMAL(18,2) NULL,
    [CuentaVtigerID] VARCHAR(50) NULL,
    [ContactoVtigerID] VARCHAR(50) NULL,
    [FechaCierre] DATE NULL,
    [EtapaVenta] NVARCHAR(100) NULL,
    [Probabilidad] INT NULL,
    [FuenteLead] NVARCHAR(100) NULL,
    [SiguientePaso] NVARCHAR(500) NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [UsuarioAsignadoVtiger] VARCHAR(50) NULL,
    [FechaCreacionVtiger] DATETIME NULL,
    [FechaModificacionVtiger] DATETIME NULL,
    [FechaCreacionLocal] DATETIME NULL DEFAULT (getdate()),
    [FechaUltimaSync] DATETIME NULL DEFAULT (getdate()),
    [PendientePush] BIT NULL DEFAULT ((0)),
    [OrigenLocal] BIT NULL DEFAULT ((0)),
    [PendienteDelete] BIT NULL DEFAULT ((0)),
    [PushError] NVARCHAR(500) NULL,
    [FechaUltimoPush] DATETIME NULL,
    CONSTRAINT [PK_Sync_Vtiger_Oportunidades] PRIMARY KEY ([SyncID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sys_Roles]
-- ============================================================
CREATE TABLE [dbo].[Sys_Roles] (
    [IDRol] INT NOT NULL,
    [NombreRol] VARCHAR(50) NOT NULL,
    [NivelAcceso] INT NOT NULL,
    [EsInterno] BIT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Sys_Roles] PRIMARY KEY ([IDRol])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sys_Scheduler_Jobs]
-- ============================================================
CREATE TABLE [dbo].[Sys_Scheduler_Jobs] (
    [JobID] VARCHAR(50) NOT NULL,
    [JobName] VARCHAR(100) NOT NULL,
    [CronExpression] VARCHAR(50) NOT NULL,
    [JobType] VARCHAR(20) NOT NULL,
    [Status] VARCHAR(20) NULL DEFAULT ('activo'),
    [LastRunDate] DATETIME NULL,
    CONSTRAINT [PK_Sys_Scheduler_Jobs] PRIMARY KEY ([JobID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Sys_Usuarios]
-- ============================================================
CREATE TABLE [dbo].[Sys_Usuarios] (
    [IDUsuario] INT NOT NULL,
    [Username] VARCHAR(100) NOT NULL,
    [PasswordHash] VARCHAR(256) NOT NULL,
    [NombreCompleto] VARCHAR(150) NULL,
    [Email] VARCHAR(150) NULL,
    [IDRol] INT NULL,
    [Estatus] VARCHAR(20) NULL DEFAULT ('ACTIVO'),
    [RFC] VARCHAR(20) NULL,
    [IDContactoVtiger] VARCHAR(50) NULL,
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Sys_Usuarios] PRIMARY KEY ([IDUsuario])
);
GO

-- ============================================================
-- TABLA: [dbo].[Tablajeria_ConfigContable]
-- ============================================================
CREATE TABLE [dbo].[Tablajeria_ConfigContable] (
    [ConfigID] INT NOT NULL,
    [EmpresaID] VARCHAR(50) NOT NULL,
    [CuentaAlmacenInsumos] VARCHAR(50) NULL,
    [CuentaAlmacenProductos] VARCHAR(50) NULL,
    [CuentaProduccionEnProceso] VARCHAR(50) NULL,
    [CuentaCostoVentas] VARCHAR(50) NULL,
    [CuentaMermaOperativa] VARCHAR(50) NULL,
    [CuentaMermaExtraordinaria] VARCHAR(50) NULL,
    [CuentaVariacionCosto] VARCHAR(50) NULL,
    [GenerarPolizaAutomatica] BIT NULL DEFAULT ((1)),
    [AfectarInventarioAutomatico] BIT NULL DEFAULT ((1)),
    [ToleranciaVariacionPorcentaje] DECIMAL(5,2) NULL DEFAULT ((5.00)),
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaModificacion] DATETIME2 NULL DEFAULT (getutcdate()),
    CONSTRAINT [PK_Tablajeria_ConfigContable] PRIMARY KEY ([ConfigID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Tablajeria_CosteoDetalle]
-- ============================================================
CREATE TABLE [dbo].[Tablajeria_CosteoDetalle] (
    [DetalleID] VARCHAR(50) NOT NULL,
    [CosteoID] VARCHAR(50) NOT NULL,
    [OrdenDetalleID] VARCHAR(50) NULL,
    [ProductoCodigo] VARCHAR(50) NULL,
    [ProductoNombre] VARCHAR(200) NULL,
    [TipoDerivado] VARCHAR(20) NULL,
    [CantidadProducida] DECIMAL(18,4) NULL,
    [PorcentajeCostoAsignado] DECIMAL(10,4) NULL,
    [CostoAsignado] DECIMAL(18,2) NULL,
    [CostoUnitario] DECIMAL(18,4) NULL,
    [EsInventariable] BIT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Tablajeria_CosteoDetalle] PRIMARY KEY ([DetalleID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Tablajeria_CosteoProduccion]
-- ============================================================
CREATE TABLE [dbo].[Tablajeria_CosteoProduccion] (
    [CosteoID] VARCHAR(50) NOT NULL,
    [OrdenID] VARCHAR(50) NOT NULL,
    [FechaCosteo] DATETIME2 NULL DEFAULT (getutcdate()),
    [InsumoBaseCodigo] VARCHAR(50) NULL,
    [InsumoBaseNombre] VARCHAR(200) NULL,
    [CantidadInsumoConsumida] DECIMAL(18,4) NULL,
    [CostoUnitarioInsumo] DECIMAL(18,4) NULL,
    [CostoTotalInsumo] DECIMAL(18,2) NULL,
    [CostoManoObra] DECIMAL(18,2) NULL DEFAULT ((0)),
    [CostoIndirectos] DECIMAL(18,2) NULL DEFAULT ((0)),
    [CostoEnergia] DECIMAL(18,2) NULL DEFAULT ((0)),
    [OtrosCostos] DECIMAL(18,2) NULL DEFAULT ((0)),
    [CostoTotalProduccion] DECIMAL(18,2) NULL,
    [CostoUnitarioPromedio] DECIMAL(18,4) NULL,
    [ReglaCosteoAplicada] VARCHAR(20) NULL,
    [UsuarioID] VARCHAR(50) NULL,
    [Observaciones] NVARCHAR(MAX) NULL,
    [EsEstimado] BIT NULL DEFAULT ((0)),
    CONSTRAINT [PK_Tablajeria_CosteoProduccion] PRIMARY KEY ([CosteoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Tablajeria_MovimientosInventario]
-- ============================================================
CREATE TABLE [dbo].[Tablajeria_MovimientosInventario] (
    [MovimientoID] VARCHAR(50) NOT NULL,
    [OrdenID] VARCHAR(50) NOT NULL,
    [TipoMovimiento] VARCHAR(20) NOT NULL,
    [ProductoCodigo] VARCHAR(50) NOT NULL,
    [ProductoNombre] VARCHAR(200) NULL,
    [AlmacenOrigenID] VARCHAR(50) NULL,
    [AlmacenDestinoID] VARCHAR(50) NULL,
    [Cantidad] DECIMAL(18,4) NOT NULL,
    [UnidadMedida] VARCHAR(20) NULL,
    [CostoUnitario] DECIMAL(18,4) NULL,
    [CostoTotal] DECIMAL(18,2) NULL,
    [LoteProducto] VARCHAR(100) NULL,
    [FechaMovimiento] DATETIME2 NULL DEFAULT (getutcdate()),
    [UsuarioID] VARCHAR(50) NULL,
    [Referencia] VARCHAR(100) NULL,
    [Sincronizado] BIT NULL DEFAULT ((0)),
    [FechaSincronizacion] DATETIME2 NULL,
    [ErrorSincronizacion] VARCHAR(500) NULL,
    CONSTRAINT [PK_Tablajeria_MovimientosInventario] PRIMARY KEY ([MovimientoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Tablajeria_PolizasContables]
-- ============================================================
CREATE TABLE [dbo].[Tablajeria_PolizasContables] (
    [PolizaID] VARCHAR(50) NOT NULL,
    [OrdenID] VARCHAR(50) NOT NULL,
    [TipoPoliza] VARCHAR(50) NULL,
    [NumeroPoliza] VARCHAR(50) NULL,
    [FechaPoliza] DATE NULL,
    [Concepto] VARCHAR(500) NULL,
    [MontoTotal] DECIMAL(18,2) NULL,
    [EstatusPoliza] VARCHAR(20) NULL DEFAULT ('PENDIENTE'),
    [FechaCreacion] DATETIME2 NULL DEFAULT (getutcdate()),
    [FechaContabilizacion] DATETIME2 NULL,
    [UsuarioID] VARCHAR(50) NULL,
    [ErrorContabilizacion] VARCHAR(500) NULL,
    CONSTRAINT [PK_Tablajeria_PolizasContables] PRIMARY KEY ([PolizaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Tablajeria_PolizasDetalle]
-- ============================================================
CREATE TABLE [dbo].[Tablajeria_PolizasDetalle] (
    [AsientoID] VARCHAR(50) NOT NULL,
    [PolizaID] VARCHAR(50) NOT NULL,
    [NumeroLinea] INT NULL,
    [CuentaContable] VARCHAR(50) NULL,
    [NombreCuenta] VARCHAR(200) NULL,
    [Concepto] VARCHAR(300) NULL,
    [Debe] DECIMAL(18,2) NULL DEFAULT ((0)),
    [Haber] DECIMAL(18,2) NULL DEFAULT ((0)),
    [Referencia] VARCHAR(100) NULL,
    CONSTRAINT [PK_Tablajeria_PolizasDetalle] PRIMARY KEY ([AsientoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Tareas_Inventario]
-- ============================================================
CREATE TABLE [dbo].[Tareas_Inventario] (
    [ID] INT NOT NULL,
    [TareaID] VARCHAR(50) NOT NULL,
    [WorkflowID] VARCHAR(50) NOT NULL,
    [TipoTarea] VARCHAR(50) NULL DEFAULT ('JUSTIFICAR'),
    [Titulo] VARCHAR(500) NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [EstadoTarea] VARCHAR(50) NULL DEFAULT ('PENDIENTE'),
    [Prioridad] VARCHAR(20) NULL DEFAULT ('MEDIA'),
    [UsuarioAsignadoID] VARCHAR(50) NULL,
    [UsuarioAsignadoNombre] VARCHAR(200) NULL,
    [FechaCreacion] DATETIME2 NULL DEFAULT (getutcdate()),
    [FechaAsignacion] DATETIME2 NULL,
    [FechaLimite] DATETIME2 NULL,
    [FechaActualizacion] DATETIME2 NULL,
    [FechaPrimeraAccion] DATETIME2 NULL,
    [FechaCompletada] DATETIME2 NULL,
    [Ciclo] INT NULL DEFAULT ((1)),
    [EsReasignacion] BIT NULL DEFAULT ((0)),
    [Vencida] BIT NULL DEFAULT ((0)),
    [EstadoSLA] VARCHAR(50) NULL,
    [FechaActualizacionSLA] DATETIME2 NULL,
    [NotificacionWarningEnviada] BIT NULL DEFAULT ((0)),
    [NotificacionVencidoEnviada] BIT NULL DEFAULT ((0)),
    [NotificacionEscaladoEnviada] BIT NULL DEFAULT ((0)),
    [NotasJSON] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_Tareas_Inventario] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Unidades_Negocio]
-- ============================================================
CREATE TABLE [dbo].[Unidades_Negocio] (
    [id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [nombre] NVARCHAR(100) NOT NULL,
    [codigo] NVARCHAR(50) NOT NULL,
    [server_id] NVARCHAR(100) NOT NULL,
    [sucursal_origen_id] NVARCHAR(50) NULL,
    [system_type] NVARCHAR(50) NOT NULL DEFAULT ('SoftRestaurant'),
    [activo] BIT NULL DEFAULT ((1)),
    [orden] INT NULL DEFAULT ((0)),
    [created_at] DATETIME NULL DEFAULT (getdate()),
    [updated_at] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Unidades_Negocio] PRIMARY KEY ([id])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_Acciones]
-- ============================================================
CREATE TABLE [dbo].[Usuario_Acciones] (
    [AccionID] SMALLINT NOT NULL,
    [CodigoAccion] VARCHAR(30) NOT NULL,
    [NombreAccion] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [EsAutorizable] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Usuario_Acciones] PRIMARY KEY ([AccionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_AlmacenesAsignacion]
-- ============================================================
CREATE TABLE [dbo].[Usuario_AlmacenesAsignacion] (
    [AsignacionID] INT NOT NULL,
    [UsuarioID] INT NOT NULL,
    [ServidorID] UNIQUEIDENTIFIER NOT NULL,
    [AlmacenCodigo] VARCHAR(20) NOT NULL,
    [LegacyMongoValue] VARCHAR(100) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME2 NULL,
    [CreadoPor] INT NULL,
    [ModificadoPor] INT NULL,
    [Observaciones] NVARCHAR(500) NULL,
    CONSTRAINT [PK_Usuario_AlmacenesAsignacion] PRIMARY KEY ([AsignacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_Autorizaciones]
-- ============================================================
CREATE TABLE [dbo].[Usuario_Autorizaciones] (
    [AutorizacionID] BIGINT NOT NULL,
    [FolioAutorizacion] VARCHAR(30) NOT NULL,
    [TipoAutorizacionID] SMALLINT NOT NULL,
    [ModuloID] INT NULL,
    [AccionID] SMALLINT NULL,
    [EntidadNombre] VARCHAR(100) NOT NULL,
    [EntidadID] VARCHAR(100) NULL,
    [FolioReferencia] VARCHAR(50) NULL,
    [UsuarioSolicitanteID] INT NOT NULL,
    [FechaSolicitud] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [Monto] DECIMAL(18,2) NULL,
    [MonedaID] SMALLINT NULL,
    [Justificacion] VARCHAR(2000) NOT NULL,
    [EstatusAutorizacion] VARCHAR(20) NOT NULL DEFAULT ('PENDIENTE'),
    [NivelActual] SMALLINT NOT NULL DEFAULT ((1)),
    [NivelFinalRequerido] SMALLINT NULL,
    [FechaResolucionFinal] DATETIME2 NULL,
    [UsuarioResolucionFinalID] INT NULL,
    [ComentariosResolucionFinal] VARCHAR(2000) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_Usuario_Autorizaciones] PRIMARY KEY ([AutorizacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_AutorizacionesDetalle]
-- ============================================================
CREATE TABLE [dbo].[Usuario_AutorizacionesDetalle] (
    [AutorizacionDetalleID] BIGINT NOT NULL,
    [AutorizacionID] BIGINT NOT NULL,
    [NivelAutorizacion] SMALLINT NOT NULL,
    [UsuarioAutorizadorID] INT NOT NULL,
    [RolID] INT NULL,
    [FechaAsignacion] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaResolucion] DATETIME2 NULL,
    [Resultado] VARCHAR(20) NOT NULL DEFAULT ('PENDIENTE'),
    [Comentarios] VARCHAR(2000) NULL,
    [IPResolucion] VARCHAR(64) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Usuario_AutorizacionesDetalle] PRIMARY KEY ([AutorizacionDetalleID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_Catalogo]
-- ============================================================
CREATE TABLE [dbo].[Usuario_Catalogo] (
    [UsuarioID] INT NOT NULL,
    [CodigoUsuario] VARCHAR(30) NOT NULL,
    [Username] VARCHAR(60) NOT NULL,
    [Email] VARCHAR(150) NOT NULL,
    [PasswordHash] VARBINARY(MAX) NULL,
    [PasswordHashTexto] VARCHAR(255) NULL,
    [Nombre] VARCHAR(100) NOT NULL,
    [Apellidos] VARCHAR(150) NULL,
    [NombreCompleto] VARCHAR(251) NULL,
    [Telefono] VARCHAR(25) NULL,
    [Celular] VARCHAR(25) NULL,
    [Puesto] VARCHAR(100) NULL,
    [Departamento] VARCHAR(100) NULL,
    [EsUsuarioPortal] BIT NOT NULL DEFAULT ((1)),
    [RequiereMFA] BIT NOT NULL DEFAULT ((0)),
    [PasswordTemporal] BIT NOT NULL DEFAULT ((1)),
    [DebeCambiarPassword] BIT NOT NULL DEFAULT ((1)),
    [IntentosFallidos] INT NOT NULL DEFAULT ((0)),
    [Bloqueado] BIT NOT NULL DEFAULT ((0)),
    [FechaBloqueo] DATETIME2 NULL,
    [MotivoBloqueo] VARCHAR(250) NULL,
    [UltimoAcceso] DATETIME2 NULL,
    [UltimoCambioPassword] DATETIME2 NULL,
    [FechaExpiracionPassword] DATETIME2 NULL,
    [ZonaHoraria] VARCHAR(60) NULL,
    [Idioma] VARCHAR(20) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedBy] VARCHAR(100) NULL,
    [MongoLegacyID] VARCHAR(50) NULL,
    [PublicUUID] UNIQUEIDENTIFIER NULL,
    CONSTRAINT [PK_Usuario_Catalogo] PRIMARY KEY ([UsuarioID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_EmpresasAsignacion]
-- ============================================================
CREATE TABLE [dbo].[Usuario_EmpresasAsignacion] (
    [UsuarioEmpresaAsignacionID] BIGINT NOT NULL,
    [UsuarioID] INT NOT NULL,
    [EmpresaID] INT NOT NULL,
    [EsPrincipal] BIT NOT NULL DEFAULT ((0)),
    [FechaInicio] DATETIME2 NOT NULL DEFAULT (getutcdate()),
    [FechaFin] DATETIME2 NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (getutcdate()),
    [CreatedBy] VARCHAR(100) NULL,
    [UpdatedAt] DATETIME2 NULL,
    [UpdatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_Usuario_EmpresasAsignacion] PRIMARY KEY ([UsuarioEmpresaAsignacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_LogAccesos]
-- ============================================================
CREATE TABLE [dbo].[Usuario_LogAccesos] (
    [LogAccesoID] BIGINT NOT NULL,
    [UsuarioID] INT NULL,
    [SesionID] BIGINT NULL,
    [TipoEvento] VARCHAR(30) NOT NULL,
    [FechaEvento] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [IPOrigen] VARCHAR(64) NULL,
    [UserAgent] VARCHAR(500) NULL,
    [Resultado] VARCHAR(20) NOT NULL DEFAULT ('OK'),
    [Detalle] VARCHAR(1000) NULL,
    CONSTRAINT [PK_Usuario_LogAccesos] PRIMARY KEY ([LogAccesoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_LogActividades]
-- ============================================================
CREATE TABLE [dbo].[Usuario_LogActividades] (
    [LogActividadID] BIGINT NOT NULL,
    [UsuarioID] INT NOT NULL,
    [SesionID] BIGINT NULL,
    [ModuloID] INT NULL,
    [AccionID] SMALLINT NULL,
    [EntidadNombre] VARCHAR(100) NULL,
    [EntidadID] VARCHAR(100) NULL,
    [FolioReferencia] VARCHAR(50) NULL,
    [FechaActividad] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [ResumenActividad] VARCHAR(250) NOT NULL,
    [DetalleActividad] VARCHAR(2000) NULL,
    [ValoresAntes] NVARCHAR(MAX) NULL,
    [ValoresDespues] NVARCHAR(MAX) NULL,
    [IPOrigen] VARCHAR(64) NULL,
    [Resultado] VARCHAR(20) NOT NULL DEFAULT ('OK'),
    [Criticidad] VARCHAR(20) NOT NULL DEFAULT ('MEDIA'),
    CONSTRAINT [PK_Usuario_LogActividades] PRIMARY KEY ([LogActividadID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_LogRBACVerificacion]
-- ============================================================
CREATE TABLE [dbo].[Usuario_LogRBACVerificacion] (
    [LogID] BIGINT NOT NULL,
    [UsuarioID] INT NULL,
    [PublicUUID] VARCHAR(36) NULL,
    [Email] VARCHAR(150) NULL,
    [PermisoRequerido] VARCHAR(50) NOT NULL,
    [Resultado] VARCHAR(20) NOT NULL,
    [Endpoint] VARCHAR(200) NULL,
    [MetodoHTTP] VARCHAR(10) NULL,
    [IPAddress] VARCHAR(45) NULL,
    [DetallesJSON] NVARCHAR(MAX) NULL,
    [FechaVerificacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Usuario_LogRBACVerificacion] PRIMARY KEY ([LogID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_LogRecuperacion]
-- ============================================================
CREATE TABLE [dbo].[Usuario_LogRecuperacion] (
    [LogRecuperacionID] BIGINT NOT NULL,
    [Evento] VARCHAR(50) NOT NULL,
    [Email] VARCHAR(255) NOT NULL,
    [IPOrigen] VARCHAR(45) NULL,
    [UserAgent] VARCHAR(500) NULL,
    [Resultado] BIT NOT NULL,
    [Detalle] NVARCHAR(MAX) NULL,
    [FechaEvento] DATETIME2 NOT NULL DEFAULT (getutcdate()),
    CONSTRAINT [PK_Usuario_LogRecuperacion] PRIMARY KEY ([LogRecuperacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_MatrizAutorizacion]
-- ============================================================
CREATE TABLE [dbo].[Usuario_MatrizAutorizacion] (
    [MatrizAutorizacionID] BIGINT NOT NULL,
    [TipoAutorizacionID] SMALLINT NOT NULL,
    [NivelAutorizacion] SMALLINT NOT NULL,
    [RolID] INT NOT NULL,
    [UsuarioID] INT NULL,
    [MontoMinimo] DECIMAL(18,2) NULL,
    [MontoMaximo] DECIMAL(18,2) NULL,
    [Prioridad] INT NOT NULL DEFAULT ((1)),
    [RequiereTodosLosNiveles] BIT NOT NULL DEFAULT ((1)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Usuario_MatrizAutorizacion] PRIMARY KEY ([MatrizAutorizacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_MigracionMongoTrace]
-- ============================================================
CREATE TABLE [dbo].[Usuario_MigracionMongoTrace] (
    [TraceID] INT NOT NULL,
    [MongoID] VARCHAR(24) NOT NULL,
    [Email] VARCHAR(150) NOT NULL,
    [UsuarioID_SQL] INT NULL,
    [RolMongoDB] VARCHAR(50) NOT NULL,
    [ActivoMongoDB] BIT NOT NULL,
    [Clasificacion] VARCHAR(20) NOT NULL,
    [FechaMigracion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL DEFAULT ('MIGRACION_FASE_A4'),
    CONSTRAINT [PK_Usuario_MigracionMongoTrace] PRIMARY KEY ([TraceID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_Modulos]
-- ============================================================
CREATE TABLE [dbo].[Usuario_Modulos] (
    [ModuloID] INT NOT NULL,
    [ModuloPadreID] INT NULL,
    [CodigoModulo] VARCHAR(30) NOT NULL,
    [NombreModulo] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [TipoModulo] VARCHAR(20) NOT NULL DEFAULT ('MODULO'),
    [Ruta] VARCHAR(200) NULL,
    [Icono] VARCHAR(100) NULL,
    [OrdenMenu] INT NOT NULL DEFAULT ((0)),
    [EsVisibleMenu] BIT NOT NULL DEFAULT ((1)),
    [RequiereAutorizacion] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Usuario_Modulos] PRIMARY KEY ([ModuloID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_PermisosRolModulo]
-- ============================================================
CREATE TABLE [dbo].[Usuario_PermisosRolModulo] (
    [PermisoRolModuloID] BIGINT NOT NULL,
    [RolID] INT NOT NULL,
    [ModuloID] INT NOT NULL,
    [AccionID] SMALLINT NOT NULL,
    [Permitido] BIT NOT NULL DEFAULT ((1)),
    [RestriccionPropietario] BIT NOT NULL DEFAULT ((0)),
    [RestriccionSucursal] BIT NOT NULL DEFAULT ((0)),
    [RequiereAutorizacion] BIT NOT NULL DEFAULT ((0)),
    [NivelAutorizacionRequerido] SMALLINT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_Usuario_PermisosRolModulo] PRIMARY KEY ([PermisoRolModuloID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_PortalConfiguracion]
-- ============================================================
CREATE TABLE [dbo].[Usuario_PortalConfiguracion] (
    [UsuarioPortalConfiguracionID] BIGINT NOT NULL,
    [UsuarioID] INT NOT NULL,
    [Tema] VARCHAR(30) NULL,
    [ColorAcento] VARCHAR(30) NULL,
    [MenuCompacto] BIT NOT NULL DEFAULT ((0)),
    [DashboardDefault] VARCHAR(100) NULL,
    [RecibeEmailNotificaciones] BIT NOT NULL DEFAULT ((1)),
    [RecibeWhatsAppNotificaciones] BIT NOT NULL DEFAULT ((0)),
    [RecibePushNotificaciones] BIT NOT NULL DEFAULT ((0)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Usuario_PortalConfiguracion] PRIMARY KEY ([UsuarioPortalConfiguracionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_RateLimitRecuperacion]
-- ============================================================
CREATE TABLE [dbo].[Usuario_RateLimitRecuperacion] (
    [RateLimitID] BIGINT NOT NULL,
    [TipoLlave] VARCHAR(20) NOT NULL,
    [ValorLlave] VARCHAR(255) NOT NULL,
    [Contador] INT NOT NULL DEFAULT ((1)),
    [VentanaInicio] DATETIME2 NOT NULL DEFAULT (getutcdate()),
    [VentanaExpiracion] DATETIME2 NOT NULL,
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getutcdate()),
    [FechaModificacion] DATETIME2 NOT NULL DEFAULT (getutcdate()),
    CONSTRAINT [PK_Usuario_RateLimitRecuperacion] PRIMARY KEY ([RateLimitID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_Roles]
-- ============================================================
CREATE TABLE [dbo].[Usuario_Roles] (
    [RolID] INT NOT NULL,
    [CodigoRol] VARCHAR(30) NOT NULL,
    [NombreRol] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [EsRolSistema] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    [NivelJerarquia] INT NOT NULL DEFAULT ((0)),
    CONSTRAINT [PK_Usuario_Roles] PRIMARY KEY ([RolID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_RolesAsignacion]
-- ============================================================
CREATE TABLE [dbo].[Usuario_RolesAsignacion] (
    [UsuarioRolAsignacionID] BIGINT NOT NULL,
    [UsuarioID] INT NOT NULL,
    [RolID] INT NOT NULL,
    [EsPrincipal] BIT NOT NULL DEFAULT ((0)),
    [FechaInicio] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaFin] DATETIME2 NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_Usuario_RolesAsignacion] PRIMARY KEY ([UsuarioRolAsignacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_ServidoresAsignacion]
-- ============================================================
CREATE TABLE [dbo].[Usuario_ServidoresAsignacion] (
    [AsignacionID] INT NOT NULL,
    [UsuarioID] INT NOT NULL,
    [ServidorID] UNIQUEIDENTIFIER NOT NULL,
    [LegacyMongoValue] VARCHAR(100) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME2 NULL,
    [CreadoPor] INT NULL,
    [ModificadoPor] INT NULL,
    [Observaciones] NVARCHAR(500) NULL,
    CONSTRAINT [PK_Usuario_ServidoresAsignacion] PRIMARY KEY ([AsignacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_Sesiones]
-- ============================================================
CREATE TABLE [dbo].[Usuario_Sesiones] (
    [SesionID] BIGINT NOT NULL,
    [UsuarioID] INT NOT NULL,
    [TokenSesion] VARCHAR(255) NULL,
    [FechaInicio] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaUltimaActividad] DATETIME2 NULL,
    [FechaCierre] DATETIME2 NULL,
    [IPOrigen] VARCHAR(64) NULL,
    [UserAgent] VARCHAR(500) NULL,
    [Dispositivo] VARCHAR(150) NULL,
    [Navegador] VARCHAR(100) NULL,
    [SistemaOperativo] VARCHAR(100) NULL,
    [ExitoLogin] BIT NOT NULL DEFAULT ((1)),
    [MotivoFallo] VARCHAR(250) NULL,
    [MFAValidado] BIT NOT NULL DEFAULT ((0)),
    [SesionActiva] BIT NOT NULL DEFAULT ((1)),
    [CerradaPorSistema] BIT NOT NULL DEFAULT ((0)),
    CONSTRAINT [PK_Usuario_Sesiones] PRIMARY KEY ([SesionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_SucursalesAsignacion]
-- ============================================================
CREATE TABLE [dbo].[Usuario_SucursalesAsignacion] (
    [AsignacionID] INT NOT NULL,
    [UsuarioID] INT NOT NULL,
    [ServidorID] UNIQUEIDENTIFIER NOT NULL,
    [SucursalCodigo] VARCHAR(20) NOT NULL,
    [LegacyMongoValue] VARCHAR(100) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME2 NULL,
    [CreadoPor] INT NULL,
    [ModificadoPor] INT NULL,
    [Observaciones] NVARCHAR(500) NULL,
    CONSTRAINT [PK_Usuario_SucursalesAsignacion] PRIMARY KEY ([AsignacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_TiposAutorizacion]
-- ============================================================
CREATE TABLE [dbo].[Usuario_TiposAutorizacion] (
    [TipoAutorizacionID] SMALLINT NOT NULL,
    [CodigoTipoAutorizacion] VARCHAR(30) NOT NULL,
    [NombreTipoAutorizacion] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [ModuloID] INT NULL,
    [AccionID] SMALLINT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Usuario_TiposAutorizacion] PRIMARY KEY ([TipoAutorizacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Usuario_TokensRecuperacion]
-- ============================================================
CREATE TABLE [dbo].[Usuario_TokensRecuperacion] (
    [TokenRecuperacionID] BIGINT NOT NULL,
    [TokenHash] VARCHAR(64) NOT NULL,
    [UsuarioID] INT NOT NULL,
    [Email] VARCHAR(150) NOT NULL,
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getutcdate()),
    [FechaExpiracion] DATETIME2 NOT NULL,
    [FechaUso] DATETIME2 NULL,
    [FechaModificacion] DATETIME2 NULL,
    [Usado] BIT NOT NULL DEFAULT ((0)),
    [Invalidado] BIT NOT NULL DEFAULT ((0)),
    [MotivoInvalidacion] VARCHAR(100) NULL,
    [IPSolicitud] VARCHAR(64) NULL,
    [IPUso] VARCHAR(64) NULL,
    [UserAgentSolicitud] VARCHAR(500) NULL,
    [UserAgentUso] VARCHAR(500) NULL,
    CONSTRAINT [PK_Usuario_TokensRecuperacion] PRIMARY KEY ([TokenRecuperacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Venta_Cat_EstatusRemision]
-- ============================================================
CREATE TABLE [dbo].[Venta_Cat_EstatusRemision] (
    [EstatusID] INT NOT NULL,
    [Nombre] NVARCHAR(50) NOT NULL,
    [Descripcion] NVARCHAR(200) NULL,
    [Color] NVARCHAR(20) NULL,
    [Orden] INT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Venta_Cat_EstatusRemision] PRIMARY KEY ([EstatusID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Venta_CondicionesPago]
-- ============================================================
CREATE TABLE [dbo].[Venta_CondicionesPago] (
    [CondicionPagoID] SMALLINT NOT NULL,
    [CodigoCondicionPago] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [DiasCredito] SMALLINT NOT NULL DEFAULT ((0)),
    [RequiereCredito] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Venta_CondicionesPago] PRIMARY KEY ([CondicionPagoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Venta_Cotizaciones]
-- ============================================================
CREATE TABLE [dbo].[Venta_Cotizaciones] (
    [CotizacionID] BIGINT NOT NULL,
    [Serie] VARCHAR(10) NULL,
    [FolioCotizacion] VARCHAR(30) NOT NULL,
    [FechaCotizacion] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaVigencia] DATE NULL,
    [ClienteID] INT NOT NULL,
    [ClienteDireccionID] INT NULL,
    [ListaPrecioID] INT NULL,
    [CondicionPagoID] SMALLINT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [TipoCambio] DECIMAL(18,6) NOT NULL DEFAULT ((1)),
    [EstatusCotizacionID] TINYINT NOT NULL DEFAULT ((1)),
    [Subtotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [DescuentoTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ImpuestoTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Total] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [AtencionA] VARCHAR(150) NULL,
    [EmailCliente] VARCHAR(150) NULL,
    [TelefonoCliente] VARCHAR(25) NULL,
    [Observaciones] VARCHAR(1000) NULL,
    [TerminosCondiciones] VARCHAR(2000) NULL,
    [ReferenciaExterna] VARCHAR(100) NULL,
    [PedidoID] BIGINT NULL,
    [VentaID] BIGINT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedAt] DATETIME2 NULL,
    [ModifiedBy] VARCHAR(100) NULL,
    [CRM_OportunidadID] UNIQUEIDENTIFIER NULL,
    [CRM_CuentaID] UNIQUEIDENTIFIER NULL,
    [CRM_LeadID] UNIQUEIDENTIFIER NULL,
    [CreatedByUserID] UNIQUEIDENTIFIER NULL,
    [UpdatedByUserID] UNIQUEIDENTIFIER NULL,
    [EstatusComercial] NVARCHAR(20) NULL,
    CONSTRAINT [PK_Venta_Cotizaciones] PRIMARY KEY ([CotizacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Venta_CotizacionesDetalle]
-- ============================================================
CREATE TABLE [dbo].[Venta_CotizacionesDetalle] (
    [DetalleCotizacionID] BIGINT NOT NULL,
    [CotizacionID] BIGINT NOT NULL,
    [Renglon] INT NOT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [Cantidad] DECIMAL(18,4) NOT NULL,
    [PrecioUnitario] DECIMAL(18,4) NOT NULL,
    [DescuentoPorcentaje] DECIMAL(9,4) NOT NULL DEFAULT ((0)),
    [DescuentoImporte] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TasaImpuesto] DECIMAL(9,4) NOT NULL DEFAULT ((0)),
    [ImpuestoImporte] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [SubtotalLinea] DECIMAL(18,2) NULL,
    [TotalLinea] DECIMAL(18,2) NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_Venta_CotizacionesDetalle] PRIMARY KEY ([DetalleCotizacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Venta_CotizacionesEstatus]
-- ============================================================
CREATE TABLE [dbo].[Venta_CotizacionesEstatus] (
    [EstatusCotizacionID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Venta_CotizacionesEstatus] PRIMARY KEY ([EstatusCotizacionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Venta_Detalle]
-- ============================================================
CREATE TABLE [dbo].[Venta_Detalle] (
    [DetalleVentaID] BIGINT NOT NULL,
    [VentaID] BIGINT NOT NULL,
    [Renglon] INT NOT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [Cantidad] DECIMAL(18,4) NOT NULL,
    [PrecioUnitario] DECIMAL(18,4) NOT NULL,
    [DescuentoPorcentaje] DECIMAL(9,4) NOT NULL DEFAULT ((0)),
    [DescuentoImporte] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TasaImpuesto] DECIMAL(9,4) NOT NULL DEFAULT ((0)),
    [ImpuestoImporte] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [SubtotalLinea] DECIMAL(18,2) NULL,
    [TotalLinea] DECIMAL(18,2) NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_Venta_Detalle] PRIMARY KEY ([DetalleVentaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Venta_Encabezado]
-- ============================================================
CREATE TABLE [dbo].[Venta_Encabezado] (
    [VentaID] BIGINT NOT NULL,
    [Serie] VARCHAR(10) NULL,
    [Folio] VARCHAR(30) NOT NULL,
    [FechaVenta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaVencimiento] DATE NULL,
    [ClienteID] INT NOT NULL,
    [ClienteDireccionID] INT NULL,
    [ListaPrecioID] INT NULL,
    [CondicionPagoID] SMALLINT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [TipoCambio] DECIMAL(18,6) NOT NULL DEFAULT ((1)),
    [EstatusVentaID] TINYINT NOT NULL DEFAULT ((1)),
    [Subtotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [DescuentoTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ImpuestoTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Total] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TotalPagado] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [SaldoPendiente] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Observaciones] VARCHAR(1000) NULL,
    [ReferenciaExterna] VARCHAR(100) NULL,
    [NumeroFactura] VARCHAR(50) NULL,
    [UUIDFactura] VARCHAR(50) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedAt] DATETIME2 NULL,
    [ModifiedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_Venta_Encabezado] PRIMARY KEY ([VentaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Venta_Estatus]
-- ============================================================
CREATE TABLE [dbo].[Venta_Estatus] (
    [EstatusVentaID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Venta_Estatus] PRIMARY KEY ([EstatusVentaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Venta_FormaPago]
-- ============================================================
CREATE TABLE [dbo].[Venta_FormaPago] (
    [FormaPagoID] SMALLINT NOT NULL,
    [ClaveFormaPago] VARCHAR(10) NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [RequiereReferencia] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Venta_FormaPago] PRIMARY KEY ([FormaPagoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Venta_ListasPrecios]
-- ============================================================
CREATE TABLE [dbo].[Venta_ListasPrecios] (
    [ListaPrecioID] INT NOT NULL,
    [CodigoListaPrecio] VARCHAR(20) NOT NULL,
    [NombreListaPrecio] VARCHAR(100) NOT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [EsDefault] BIT NOT NULL DEFAULT ((0)),
    [FechaInicio] DATE NULL,
    [FechaFin] DATE NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    CONSTRAINT [PK_Venta_ListasPrecios] PRIMARY KEY ([ListaPrecioID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Venta_ListasPreciosDetalle]
-- ============================================================
CREATE TABLE [dbo].[Venta_ListasPreciosDetalle] (
    [ListaPrecioDetalleID] BIGINT NOT NULL,
    [ListaPrecioID] INT NOT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [Precio] DECIMAL(18,2) NOT NULL,
    [DescuentoPorcentaje] DECIMAL(9,4) NOT NULL DEFAULT ((0)),
    [FechaInicio] DATE NULL,
    [FechaFin] DATE NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    CONSTRAINT [PK_Venta_ListasPreciosDetalle] PRIMARY KEY ([ListaPrecioDetalleID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Venta_Pagos]
-- ============================================================
CREATE TABLE [dbo].[Venta_Pagos] (
    [PagoVentaID] BIGINT NOT NULL,
    [VentaID] BIGINT NOT NULL,
    [FechaPago] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FormaPagoID] SMALLINT NOT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [TipoCambio] DECIMAL(18,6) NOT NULL DEFAULT ((1)),
    [ImportePago] DECIMAL(18,2) NOT NULL,
    [ReferenciaPago] VARCHAR(100) NULL,
    [NumeroAutorizacion] VARCHAR(100) NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Confirmado] BIT NOT NULL DEFAULT ((1)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_Venta_Pagos] PRIMARY KEY ([PagoVentaID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Venta_Pedidos]
-- ============================================================
CREATE TABLE [dbo].[Venta_Pedidos] (
    [PedidoID] BIGINT NOT NULL,
    [Serie] VARCHAR(10) NULL,
    [FolioPedido] VARCHAR(30) NOT NULL,
    [FechaPedido] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaCompromiso] DATE NULL,
    [ClienteID] INT NOT NULL,
    [ClienteDireccionID] INT NULL,
    [ListaPrecioID] INT NULL,
    [CondicionPagoID] SMALLINT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [TipoCambio] DECIMAL(18,6) NOT NULL DEFAULT ((1)),
    [EstatusPedidoID] TINYINT NOT NULL DEFAULT ((1)),
    [Subtotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [DescuentoTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ImpuestoTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Total] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [CotizacionID] BIGINT NULL,
    [VentaID] BIGINT NULL,
    [AtencionA] VARCHAR(150) NULL,
    [Observaciones] VARCHAR(1000) NULL,
    [InstruccionesEntrega] VARCHAR(1000) NULL,
    [ReferenciaExterna] VARCHAR(100) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedAt] DATETIME2 NULL,
    [ModifiedBy] VARCHAR(100) NULL,
    [CRM_OportunidadID] UNIQUEIDENTIFIER NULL,
    [CRM_CuentaID] UNIQUEIDENTIFIER NULL,
    [CreatedByUserID] UNIQUEIDENTIFIER NULL,
    [UpdatedByUserID] UNIQUEIDENTIFIER NULL,
    [EstatusComercial] NVARCHAR(20) NULL,
    CONSTRAINT [PK_Venta_Pedidos] PRIMARY KEY ([PedidoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Venta_PedidosDetalle]
-- ============================================================
CREATE TABLE [dbo].[Venta_PedidosDetalle] (
    [DetallePedidoID] BIGINT NOT NULL,
    [PedidoID] BIGINT NOT NULL,
    [Renglon] INT NOT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [Cantidad] DECIMAL(18,4) NOT NULL,
    [CantidadSurtida] DECIMAL(18,4) NOT NULL DEFAULT ((0)),
    [PrecioUnitario] DECIMAL(18,4) NOT NULL,
    [DescuentoPorcentaje] DECIMAL(9,4) NOT NULL DEFAULT ((0)),
    [DescuentoImporte] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [TasaImpuesto] DECIMAL(9,4) NOT NULL DEFAULT ((0)),
    [ImpuestoImporte] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [SubtotalLinea] DECIMAL(18,2) NULL,
    [TotalLinea] DECIMAL(18,2) NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL,
    CONSTRAINT [PK_Venta_PedidosDetalle] PRIMARY KEY ([DetallePedidoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Venta_PedidosEstatus]
-- ============================================================
CREATE TABLE [dbo].[Venta_PedidosEstatus] (
    [EstatusPedidoID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_Venta_PedidosEstatus] PRIMARY KEY ([EstatusPedidoID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Venta_Remisiones]
-- ============================================================
CREATE TABLE [dbo].[Venta_Remisiones] (
    [RemisionID] BIGINT NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [SucursalID] UNIQUEIDENTIFIER NULL,
    [AlmacenID] INT NULL,
    [FolioRemision] NVARCHAR(20) NOT NULL,
    [PedidoID] BIGINT NULL,
    [CotizacionID] BIGINT NULL,
    [OportunidadID] UNIQUEIDENTIFIER NULL,
    [CuentaID] UNIQUEIDENTIFIER NULL,
    [ClienteID] INT NOT NULL,
    [ContactoID] INT NULL,
    [FechaRemision] DATE NOT NULL,
    [FechaCompromisoEntrega] DATE NULL,
    [FechaEntregaReal] DATETIME2 NULL,
    [EntregadoA] NVARCHAR(200) NULL,
    [RecibidoPor] NVARCHAR(200) NULL,
    [DireccionEntrega] NVARCHAR(500) NULL,
    [MonedaID] INT NULL DEFAULT ((1)),
    [TipoCambio] DECIMAL(18,6) NULL DEFAULT ((1)),
    [Subtotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [DescuentoTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ImpuestosTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Total] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [EstatusRemisionID] INT NOT NULL DEFAULT ((1)),
    [FacturaID] BIGINT NULL,
    [FechaFacturacion] DATETIME2 NULL,
    [DocumentoID] UNIQUEIDENTIFIER NULL,
    [Observaciones] NVARCHAR(MAX) NULL,
    [ObservacionesInternas] NVARCHAR(MAX) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedBy] UNIQUEIDENTIFIER NULL,
    [UpdatedBy] UNIQUEIDENTIFIER NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (getutcdate()),
    [UpdatedAt] DATETIME2 NULL,
    CONSTRAINT [PK_Venta_Remisiones] PRIMARY KEY ([RemisionID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Venta_RemisionesDetalle]
-- ============================================================
CREATE TABLE [dbo].[Venta_RemisionesDetalle] (
    [DetalleID] BIGINT NOT NULL,
    [RemisionID] BIGINT NOT NULL,
    [PedidoDetalleID] BIGINT NULL,
    [ProductoID] INT NULL,
    [ServicioID] INT NULL,
    [Codigo] NVARCHAR(50) NULL,
    [Descripcion] NVARCHAR(500) NOT NULL,
    [Cantidad] DECIMAL(18,4) NOT NULL,
    [UnidadID] INT NULL,
    [UnidadCodigo] NVARCHAR(10) NULL,
    [PrecioUnitario] DECIMAL(18,4) NOT NULL DEFAULT ((0)),
    [DescuentoPorcentaje] DECIMAL(5,2) NULL DEFAULT ((0)),
    [DescuentoImporte] DECIMAL(18,2) NULL DEFAULT ((0)),
    [ImpuestoPorcentaje] DECIMAL(5,2) NULL DEFAULT ((0)),
    [ImpuestoImporte] DECIMAL(18,2) NULL DEFAULT ((0)),
    [Subtotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Total] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [NumeroLote] NVARCHAR(50) NULL,
    [NumeroSerie] NVARCHAR(50) NULL,
    [OrdenLinea] INT NOT NULL DEFAULT ((0)),
    CONSTRAINT [PK_Venta_RemisionesDetalle] PRIMARY KEY ([DetalleID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Venta_RemisionesHistorial]
-- ============================================================
CREATE TABLE [dbo].[Venta_RemisionesHistorial] (
    [HistorialID] BIGINT NOT NULL,
    [RemisionID] BIGINT NOT NULL,
    [EstatusAnteriorID] INT NULL,
    [EstatusNuevoID] INT NOT NULL,
    [Comentario] NVARCHAR(500) NULL,
    [CambiadoPorUserID] UNIQUEIDENTIFIER NOT NULL,
    [FechaCambio] DATETIME2 NOT NULL DEFAULT (getutcdate()),
    CONSTRAINT [PK_Venta_RemisionesHistorial] PRIMARY KEY ([HistorialID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Workflow_DecisionesAuditoria]
-- ============================================================
CREATE TABLE [dbo].[Workflow_DecisionesAuditoria] (
    [ID] INT NOT NULL,
    [DecisionID] VARCHAR(50) NOT NULL,
    [WorkflowID] VARCHAR(50) NOT NULL,
    [TipoDecision] VARCHAR(50) NOT NULL,
    [Decision] VARCHAR(50) NOT NULL,
    [Comentario] NVARCHAR(MAX) NULL,
    [UsuarioID] VARCHAR(50) NOT NULL,
    [UsuarioNombre] VARCHAR(200) NULL,
    [CicloAuditoria] INT NULL DEFAULT ((1)),
    [AccionSiguiente] VARCHAR(100) NULL,
    [FechaDecision] DATETIME2 NULL DEFAULT (getutcdate()),
    [MetadatosJSON] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_Workflow_DecisionesAuditoria] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Workflow_DetalleDiferencias]
-- ============================================================
CREATE TABLE [dbo].[Workflow_DetalleDiferencias] (
    [ID] INT NOT NULL,
    [DetalleID] VARCHAR(50) NOT NULL,
    [WorkflowID] VARCHAR(50) NOT NULL,
    [CodigoProducto] VARCHAR(50) NULL,
    [NombreProducto] VARCHAR(200) NULL,
    [Categoria] VARCHAR(100) NULL,
    [Familia] VARCHAR(100) NULL,
    [SubFamilia] VARCHAR(100) NULL,
    [Unidad] VARCHAR(50) NULL,
    [CostoUnitario] DECIMAL(18,4) NULL DEFAULT ((0)),
    [InvInicialCantidad] DECIMAL(18,4) NULL DEFAULT ((0)),
    [InvFinalCantidad] DECIMAL(18,4) NULL DEFAULT ((0)),
    [InvTeoricoCantidad] DECIMAL(18,4) NULL DEFAULT ((0)),
    [DiferenciaCantidad] DECIMAL(18,4) NULL DEFAULT ((0)),
    [DiferenciaCosto] DECIMAL(18,2) NULL DEFAULT ((0)),
    [DiferenciaPorcentaje] DECIMAL(10,2) NULL DEFAULT ((0)),
    [Movimientos] DECIMAL(18,4) NULL DEFAULT ((0)),
    [Ventas] DECIMAL(18,4) NULL DEFAULT ((0)),
    [EstadoJustificacion] VARCHAR(50) NULL DEFAULT ('pendiente'),
    [RequiereJustificacionCompleta] BIT NULL DEFAULT ((0)),
    [FechaCreacion] DATETIME2 NULL DEFAULT (getutcdate()),
    CONSTRAINT [PK_Workflow_DetalleDiferencias] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Workflow_Inventarios]
-- ============================================================
CREATE TABLE [dbo].[Workflow_Inventarios] (
    [ID] INT NOT NULL,
    [WorkflowID] VARCHAR(50) NOT NULL,
    [ProcesadoID] VARCHAR(500) NULL,
    [FolioInventario] VARCHAR(100) NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [ServerName] VARCHAR(100) NULL,
    [SucursalID] VARCHAR(100) NULL,
    [SucursalNombre] VARCHAR(100) NULL,
    [AlmacenID] VARCHAR(50) NULL,
    [AlmacenNombre] VARCHAR(100) NULL,
    [FoliosInicialesJSON] NVARCHAR(MAX) NULL,
    [FoliosFinalesJSON] NVARCHAR(MAX) NULL,
    [FolioFinalKey] VARCHAR(500) NULL,
    [FechaAnalisisIni] DATE NULL,
    [FechaAnalisisFin] DATE NULL,
    [EstadoWorkflow] VARCHAR(50) NULL DEFAULT ('PENDIENTE_ASIGNACION'),
    [Estado] VARCHAR(50) NULL DEFAULT ('pendiente'),
    [CicloActual] INT NULL DEFAULT ((1)),
    [TotalProductosDiferencia] INT NULL DEFAULT ((0)),
    [ValorTotalDiferencias] DECIMAL(18,2) NULL DEFAULT ((0)),
    [FechaCreacion] DATETIME2 NULL DEFAULT (getutcdate()),
    [FechaUltimaActualizacion] DATETIME2 NULL DEFAULT (getutcdate()),
    [UsuarioCreadorID] VARCHAR(50) NULL,
    [NotasJSON] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_Workflow_Inventarios] PRIMARY KEY ([ID])
);
GO

-- ============================================================
-- TABLA: [dbo].[Workflow_Justificaciones]
-- ============================================================
CREATE TABLE [dbo].[Workflow_Justificaciones] (
    [ID] INT NOT NULL,
    [JustificacionID] VARCHAR(50) NOT NULL,
    [WorkflowID] VARCHAR(50) NOT NULL,
    [DetalleID] VARCHAR(50) NULL,
    [CodigoProducto] VARCHAR(50) NULL,
    [TipoJustificacion] VARCHAR(50) NOT NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [CantidadJustificada] DECIMAL(18,4) NULL,
    [ValorJustificado] DECIMAL(18,2) NULL,
    [EvidenciaURL] VARCHAR(500) NULL,
    [UsuarioID] VARCHAR(50) NOT NULL,
    [UsuarioNombre] VARCHAR(200) NULL,
    [Estado] VARCHAR(50) NULL DEFAULT ('PENDIENTE'),
    [FechaCreacion] DATETIME2 NULL DEFAULT (getutcdate()),
    [FechaRevision] DATETIME2 NULL,
    [RevisadoPorID] VARCHAR(50) NULL,
    [Comentarios] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_Workflow_Justificaciones] PRIMARY KEY ([ID])
);
GO


-- ============================================================
-- VISTAS (10 total)
-- ============================================================

-- VISTA: [Comercial].[v_TableroComercialConsolidado]

    CREATE VIEW Comercial.v_TableroComercialConsolidado AS
    SELECT 
        b.UnidadID,
        b.UnidadNombre,
        ISNULL(s.VentasCalculadas, b.VentasConsolidadas) AS VentasConsolidadas,
        ISNULL(s.PaxCalculados, b.PaxTotal) AS PaxTotal,
        ISNULL(s.ChequesCalculados, b.ChequesEmitidos) AS ChequesEmitidos,
        b.PorcentajeMeta,
        ISNULL(s.UltimaVenta, b.UltimaSincronizacion) AS UltimaActualizacion,
        b.StatusConexion
    FROM Comercial.TableroEjecutivoCache b
    LEFT JOIN (
        SELECT 
            LOWER(REPLACE(branch, ' ', '_')) AS UnidadMapeada,
            SUM(total) AS VentasCalculadas,
            ISNULL(SUM(Pax), COUNT(id) * 3) AS PaxCalculados,
            COUNT(id) AS ChequesCalculados,
            MAX(created_at) AS UltimaVenta
        FROM dbo.Sync_Sales WITH (NOLOCK)
        GROUP BY branch
    ) s ON LOWER(REPLACE(b.UnidadID, '_', '')) = LOWER(REPLACE(s.UnidadMapeada, '_', ''));
    
GO

-- VISTA: [dbo].[Cat_Familias]

    CREATE VIEW Cat_Familias AS
    SELECT DISTINCT
        ROW_NUMBER() OVER (ORDER BY Familia) AS IdFamilia,
        Familia AS Nombre,
        Subfamilia AS Descripcion
    FROM Products
    WHERE Familia IS NOT NULL
    
GO

-- VISTA: [dbo].[Cat_Productos]

    CREATE VIEW Cat_Productos AS
    SELECT 
        Id AS IdProducto,
        NombreProducto AS Nombre,
        Familia,
        Subfamilia,
        Casa AS CasaProductora,
        PorcentajeAlcohol,
        -- IdFamilia calculado para JOINs
        (SELECT TOP 1 f.IdFamilia FROM Cat_Familias f WHERE f.Nombre = Products.Familia) AS IdFamilia
    FROM Products
    
GO

-- VISTA: [dbo].[Sync_Payments]

    CREATE VIEW Sync_Payments AS
    SELECT 
        Id,
        CASE TenantID
            WHEN 1 THEN 'CIENFUEGOS'
            WHEN 2 THEN '130_MERIDA'
            WHEN 3 THEN '130_QUERETARO'
            WHEN 4 THEN 'LA_ESTELAR'
            WHEN 5 THEN 'ORIGEN'
            ELSE CAST(TenantID AS VARCHAR(20))
        END AS UnidadNegocio,
        ImporteNeto AS Monto,
        Propina AS PropinaAportada,
        'Efectivo' AS MetodoPago,
        'Liquidado' AS Estatus,
        Fecha AS FechaPago
    FROM Fact_Ventas_Consolidadas
    
GO

-- VISTA: [dbo].[v_CatalogoUnidadesUnicas]

    CREATE VIEW dbo.v_CatalogoUnidadesUnicas AS
    SELECT 
        LOWER(REPLACE(REPLACE(REPLACE(RTRIM(LTRIM(Unidad)), '°', ''), ' ', ''), 'ñ', 'n')) AS id,
        RTRIM(LTRIM(Unidad)) AS name,
        MAX(UltimaActualizacion) AS fecha_actualizacion
    FROM (
        SELECT DISTINCT branch AS Unidad, last_modified AS UltimaActualizacion 
        FROM dbo.Sync_Sales 
        WHERE branch IS NOT NULL
    ) AS ListadoSucursales
    GROUP BY Unidad;
    
GO

-- VISTA: [dbo].[View_Inteligencia_Comercial]

CREATE   VIEW View_Inteligencia_Comercial
AS
SELECT 
    v.UnidadNegocio,
    p.Id AS IdProducto,
    COALESCE(p.NombreProducto, v.NombreProducto_JSON) AS Producto,
    COALESCE(p.Familia, 'SIN FAMILIA') AS Familia,
    p.Casa AS CasaProductora,
    p.PorcentajeAlcohol,
    SUM(v.Cantidad) AS CantidadTotal,
    SUM(v.TotalLinea) AS IngresoTotal,
    0 AS Propina,
    MAX(v.Pax) AS Pax,
    DATEPART(HOUR, v.FechaHora) AS FranjaHoraria
FROM 
    View_Sync_Sales_Detalle v
LEFT JOIN 
    Products p ON v.CodigoProducto_JSON = p.CodigoProducto
GROUP BY
    v.UnidadNegocio,
    p.Id,
    COALESCE(p.NombreProducto, v.NombreProducto_JSON),
    COALESCE(p.Familia, 'SIN FAMILIA'),
    p.Casa,
    p.PorcentajeAlcohol,
    DATEPART(HOUR, v.FechaHora)

GO

-- VISTA: [dbo].[View_Sync_Sales_Detalle]

CREATE   VIEW View_Sync_Sales_Detalle
AS
SELECT 
    s.IdTransaccion,
    s.UnidadNegocio,
    s.NumeroTicket,
    s.FechaHora,
    s.Pax,
    s.MontoTotal,
    JSON_VALUE(i.value, '$.id') AS CodigoProducto_JSON,
    JSON_VALUE(i.value, '$.name') AS NombreProducto_JSON,
    CAST(JSON_VALUE(i.value, '$.quantity') AS DECIMAL(18,2)) AS Cantidad,
    CAST(JSON_VALUE(i.value, '$.price') AS DECIMAL(18,2)) AS PrecioUnitario,
    CAST(JSON_VALUE(i.value, '$.total') AS DECIMAL(18,2)) AS TotalLinea
FROM 
    Sync_Sales s
CROSS APPLY 
    OPENJSON(s.items) AS i
WHERE 
    s.items IS NOT NULL
    AND s.status != 'CANCELLED'

GO

-- VISTA: [dbo].[vw_CompetidoresPorUnidad]

    CREATE VIEW vw_CompetidoresPorUnidad AS
    SELECT 
        cu.CompetidorUnidadID,
        cu.CompetidorCatalogoID,
        cu.EmpresaID,
        cu.UnidadNegocioID,
        cc.NombreCompetidor,
        cc.TipoRestaurante,
        cc.SegmentoPrecio,
        cc.Ciudad,
        cc.Estado,
        cc.Pais,
        cc.ZonaComercial,
        cc.SitioWeb,
        cc.UrlMenu,
        cc.UrlGoogleMaps,
        cc.UrlInstagram,
        cc.UrlFacebook,
        cc.UrlTripAdvisor,
        cc.UrlOpenTable,
        cc.Notas,
        cu.EsCompetenciaDirecta,
        cu.EsBenchmarkAspiracional,
        cu.TipoRelacion,
        cu.Prioridad,
        cu.DistanciaKm,
        cu.Comentarios,
        cu.Activo,
        cu.FechaCreacion,
        cu.UsuarioCreacion,
        cu.FechaModificacion,
        cu.UsuarioModificacion
    FROM Comercial_CompetidoresUnidad cu
    INNER JOIN Comercial_CompetidoresCatalogo cc 
        ON cu.CompetidorCatalogoID = cc.CompetidorCatalogoID
    WHERE cu.Activo = 1 AND cc.Activo = 1;
    
GO

-- VISTA: [dbo].[vw_RH_Bloqueados_Por_Expediente]

-- =============================================
-- 7. VISTA DE "GENTE SIN CHECAR" (CONTROL DE CANDADO)
-- =============================================
CREATE VIEW vw_RH_Bloqueados_Por_Expediente AS
SELECT ColaboradorID, Nombre_Completo, 
       Validacion_IA_RFC, Validacion_IA_CURP, Validacion_IA_EdoCta, Validacion_IA_Contrato
FROM RH_Colaboradores_Expediente
WHERE Colaborador_Activo = 0;

GO

-- VISTA: [dbo].[Vw_Sync_Sales_Unified]

        CREATE VIEW Vw_Sync_Sales_Unified AS
        -- Combina datos de Sync_Sales (si tiene) y Fact_Ventas_Consolidadas
        SELECT 
            Id,
            CASE TenantID
                WHEN 1 THEN 'CIENFUEGOS'
                WHEN 2 THEN '130_MERIDA'
                WHEN 3 THEN '130_QUERETARO'
                WHEN 4 THEN 'LA_ESTELAR'
                WHEN 5 THEN 'ORIGEN'
                ELSE CAST(TenantID AS VARCHAR(20))
            END AS UnidadNegocio,
            TenantID,
            Fecha AS FechaHora,
            Periodo,
            IdProducto,
            Cantidad,
            ImporteNeto,
            Propina,
            Pax,
            'Activo' AS Estatus
        FROM Fact_Ventas_Consolidadas
        
GO

-- ============================================================
-- FOREIGN KEYS (406 total)
-- ============================================================
ALTER TABLE [dbo].[ActivoFijo_ActivoMedidores] ADD CONSTRAINT [FK_AF_ActivoMedidores_Activo]
    FOREIGN KEY ([ActivoID]) REFERENCES [dbo].[ActivoFijo_Activos]([ActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_ActivoMedidores] ADD CONSTRAINT [FK_AF_ActivoMedidores_Medidor]
    FOREIGN KEY ([MedidorID]) REFERENCES [dbo].[ActivoFijo_Medidores]([MedidorID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Activos] ADD CONSTRAINT [FK_AF_Activos_Clase]
    FOREIGN KEY ([ClaseActivoID]) REFERENCES [dbo].[ActivoFijo_ClaseActivo]([ClaseActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Activos] ADD CONSTRAINT [FK_AF_Activos_EstadoUso]
    FOREIGN KEY ([EstadoUsoActivoID]) REFERENCES [dbo].[ActivoFijo_EstadoUsoActivo]([EstadoUsoActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Activos] ADD CONSTRAINT [FK_AF_Activos_Estatus]
    FOREIGN KEY ([EstatusActivoID]) REFERENCES [dbo].[ActivoFijo_EstatusActivo]([EstatusActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Activos] ADD CONSTRAINT [FK_AF_Activos_MonedaCompra]
    FOREIGN KEY ([MonedaCompraID]) REFERENCES [dbo].[Proveedor_Monedas]([MonedaID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Activos] ADD CONSTRAINT [FK_AF_Activos_Padre]
    FOREIGN KEY ([ActivoPadreID]) REFERENCES [dbo].[ActivoFijo_Activos]([ActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Activos] ADD CONSTRAINT [FK_AF_Activos_Proveedor]
    FOREIGN KEY ([ProveedorID]) REFERENCES [dbo].[Proveedor_Catalogo]([ProveedorID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Activos] ADD CONSTRAINT [FK_AF_Activos_Tipo]
    FOREIGN KEY ([TipoActivoID]) REFERENCES [dbo].[ActivoFijo_TipoActivo]([TipoActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Activos] ADD CONSTRAINT [FK_AF_Activos_Ubicacion]
    FOREIGN KEY ([UbicacionActualID]) REFERENCES [dbo].[ActivoFijo_Ubicaciones]([UbicacionID]);
GO
ALTER TABLE [dbo].[ActivoFijo_ActivosLibros] ADD CONSTRAINT [FK_AF_ActivosLibros_Activo]
    FOREIGN KEY ([ActivoID]) REFERENCES [dbo].[ActivoFijo_Activos]([ActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_ActivosLibros] ADD CONSTRAINT [FK_AF_ActivosLibros_Libro]
    FOREIGN KEY ([LibroDepreciacionID]) REFERENCES [dbo].[ActivoFijo_LibrosDepreciacion]([LibroDepreciacionID]);
GO
ALTER TABLE [dbo].[ActivoFijo_ActivosLibros] ADD CONSTRAINT [FK_AF_ActivosLibros_Metodo]
    FOREIGN KEY ([MetodoDepreciacionID]) REFERENCES [dbo].[ActivoFijo_MetodosDepreciacion]([MetodoDepreciacionID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Alertas] ADD CONSTRAINT [FK_AF_Alertas_Activo]
    FOREIGN KEY ([ActivoID]) REFERENCES [dbo].[ActivoFijo_Activos]([ActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Alertas] ADD CONSTRAINT [FK_AF_Alertas_OT]
    FOREIGN KEY ([OrdenTrabajoID]) REFERENCES [dbo].[ActivoFijo_OrdenesTrabajo]([OrdenTrabajoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Alertas] ADD CONSTRAINT [FK_AF_Alertas_Plan]
    FOREIGN KEY ([PlanMantenimientoID]) REFERENCES [dbo].[ActivoFijo_PlanesMantenimiento]([PlanMantenimientoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Autorizaciones] ADD CONSTRAINT [FK_AF_Autorizaciones_Activo]
    FOREIGN KEY ([ActivoID]) REFERENCES [dbo].[ActivoFijo_Activos]([ActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Autorizaciones] ADD CONSTRAINT [FK_AF_Autorizaciones_Cotizacion]
    FOREIGN KEY ([CotizacionID]) REFERENCES [dbo].[ActivoFijo_Cotizaciones]([CotizacionID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Autorizaciones] ADD CONSTRAINT [FK_AF_Autorizaciones_Moneda]
    FOREIGN KEY ([MonedaID]) REFERENCES [dbo].[Proveedor_Monedas]([MonedaID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Autorizaciones] ADD CONSTRAINT [FK_AF_Autorizaciones_OT]
    FOREIGN KEY ([OrdenTrabajoID]) REFERENCES [dbo].[ActivoFijo_OrdenesTrabajo]([OrdenTrabajoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_BajasActivos] ADD CONSTRAINT [FK_AF_BajasActivos_Activo]
    FOREIGN KEY ([ActivoID]) REFERENCES [dbo].[ActivoFijo_Activos]([ActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_BajasActivos] ADD CONSTRAINT [FK_AF_BajasActivos_Autorizacion]
    FOREIGN KEY ([AutorizacionID]) REFERENCES [dbo].[ActivoFijo_Autorizaciones]([AutorizacionID]);
GO
ALTER TABLE [dbo].[ActivoFijo_BajasActivos] ADD CONSTRAINT [FK_AF_BajasActivos_Tipo]
    FOREIGN KEY ([TipoBajaID]) REFERENCES [dbo].[ActivoFijo_TipoBaja]([TipoBajaID]);
GO
ALTER TABLE [dbo].[ActivoFijo_ClaseActivo] ADD CONSTRAINT [FK_AF_ClaseActivo_TipoActivo]
    FOREIGN KEY ([TipoActivoID]) REFERENCES [dbo].[ActivoFijo_TipoActivo]([TipoActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Cotizaciones] ADD CONSTRAINT [FK_AF_Cotizaciones_Activo]
    FOREIGN KEY ([ActivoID]) REFERENCES [dbo].[ActivoFijo_Activos]([ActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Cotizaciones] ADD CONSTRAINT [FK_AF_Cotizaciones_Moneda]
    FOREIGN KEY ([MonedaID]) REFERENCES [dbo].[Proveedor_Monedas]([MonedaID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Cotizaciones] ADD CONSTRAINT [FK_AF_Cotizaciones_OT]
    FOREIGN KEY ([OrdenTrabajoID]) REFERENCES [dbo].[ActivoFijo_OrdenesTrabajo]([OrdenTrabajoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Cotizaciones] ADD CONSTRAINT [FK_AF_Cotizaciones_Proveedor]
    FOREIGN KEY ([ProveedorID]) REFERENCES [dbo].[Proveedor_Catalogo]([ProveedorID]);
GO
ALTER TABLE [dbo].[ActivoFijo_DepreciacionMovimientos] ADD CONSTRAINT [FK_AF_DepreciacionMovimientos_ActivoLibro]
    FOREIGN KEY ([ActivoLibroID]) REFERENCES [dbo].[ActivoFijo_ActivosLibros]([ActivoLibroID]);
GO
ALTER TABLE [dbo].[ActivoFijo_HistorialAsignaciones] ADD CONSTRAINT [FK_AF_HistorialAsignaciones_Activo]
    FOREIGN KEY ([ActivoID]) REFERENCES [dbo].[ActivoFijo_Activos]([ActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_HistorialAsignaciones] ADD CONSTRAINT [FK_AF_HistorialAsignaciones_Ubicacion]
    FOREIGN KEY ([UbicacionID]) REFERENCES [dbo].[ActivoFijo_Ubicaciones]([UbicacionID]);
GO
ALTER TABLE [dbo].[ActivoFijo_LecturasMedidor] ADD CONSTRAINT [FK_AF_LecturasMedidor_ActivoMedidor]
    FOREIGN KEY ([ActivoMedidorID]) REFERENCES [dbo].[ActivoFijo_ActivoMedidores]([ActivoMedidorID]);
GO
ALTER TABLE [dbo].[ActivoFijo_LibrosDepreciacion] ADD CONSTRAINT [FK_AF_LibrosDepreciacion_Moneda]
    FOREIGN KEY ([MonedaID]) REFERENCES [dbo].[Proveedor_Monedas]([MonedaID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Medidores] ADD CONSTRAINT [FK_AF_Medidores_Tipo]
    FOREIGN KEY ([TipoMedidorID]) REFERENCES [dbo].[ActivoFijo_TipoMedidor]([TipoMedidorID]);
GO
ALTER TABLE [dbo].[ActivoFijo_MovimientosActivo] ADD CONSTRAINT [FK_AF_MovimientosActivo_Activo]
    FOREIGN KEY ([ActivoID]) REFERENCES [dbo].[ActivoFijo_Activos]([ActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_MovimientosActivo] ADD CONSTRAINT [FK_AF_MovimientosActivo_Proveedor]
    FOREIGN KEY ([ProveedorID]) REFERENCES [dbo].[Proveedor_Catalogo]([ProveedorID]);
GO
ALTER TABLE [dbo].[ActivoFijo_MovimientosActivo] ADD CONSTRAINT [FK_AF_MovimientosActivo_UbicacionDestino]
    FOREIGN KEY ([UbicacionDestinoID]) REFERENCES [dbo].[ActivoFijo_Ubicaciones]([UbicacionID]);
GO
ALTER TABLE [dbo].[ActivoFijo_MovimientosActivo] ADD CONSTRAINT [FK_AF_MovimientosActivo_UbicacionOrigen]
    FOREIGN KEY ([UbicacionOrigenID]) REFERENCES [dbo].[ActivoFijo_Ubicaciones]([UbicacionID]);
GO
ALTER TABLE [dbo].[ActivoFijo_OrdenesTrabajo] ADD CONSTRAINT [FK_AF_OrdenesTrabajo_Activo]
    FOREIGN KEY ([ActivoID]) REFERENCES [dbo].[ActivoFijo_Activos]([ActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_OrdenesTrabajo] ADD CONSTRAINT [FK_AF_OrdenesTrabajo_Estatus]
    FOREIGN KEY ([EstatusOTID]) REFERENCES [dbo].[ActivoFijo_EstatusOT]([EstatusOTID]);
GO
ALTER TABLE [dbo].[ActivoFijo_OrdenesTrabajo] ADD CONSTRAINT [FK_AF_OrdenesTrabajo_Plan]
    FOREIGN KEY ([PlanMantenimientoID]) REFERENCES [dbo].[ActivoFijo_PlanesMantenimiento]([PlanMantenimientoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_OrdenesTrabajo] ADD CONSTRAINT [FK_AF_OrdenesTrabajo_Prioridad]
    FOREIGN KEY ([PrioridadOTID]) REFERENCES [dbo].[ActivoFijo_PrioridadOT]([PrioridadOTID]);
GO
ALTER TABLE [dbo].[ActivoFijo_OrdenesTrabajo] ADD CONSTRAINT [FK_AF_OrdenesTrabajo_Proveedor]
    FOREIGN KEY ([ProveedorID]) REFERENCES [dbo].[Proveedor_Catalogo]([ProveedorID]);
GO
ALTER TABLE [dbo].[ActivoFijo_OrdenesTrabajo] ADD CONSTRAINT [FK_AF_OrdenesTrabajo_Tipo]
    FOREIGN KEY ([TipoOTID]) REFERENCES [dbo].[ActivoFijo_TipoOT]([TipoOTID]);
GO
ALTER TABLE [dbo].[ActivoFijo_OrdenesTrabajo] ADD CONSTRAINT [FK_AF_OrdenesTrabajo_Ubicacion]
    FOREIGN KEY ([UbicacionID]) REFERENCES [dbo].[ActivoFijo_Ubicaciones]([UbicacionID]);
GO
ALTER TABLE [dbo].[ActivoFijo_OrdenTrabajoCostos] ADD CONSTRAINT [FK_AF_OrdenTrabajoCostos_Orden]
    FOREIGN KEY ([OrdenTrabajoID]) REFERENCES [dbo].[ActivoFijo_OrdenesTrabajo]([OrdenTrabajoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_OrdenTrabajoCostos] ADD CONSTRAINT [FK_AF_OrdenTrabajoCostos_Proveedor]
    FOREIGN KEY ([ProveedorID]) REFERENCES [dbo].[Proveedor_Catalogo]([ProveedorID]);
GO
ALTER TABLE [dbo].[ActivoFijo_PlanesMantenimiento] ADD CONSTRAINT [FK_AF_PlanesMantenimiento_Activo]
    FOREIGN KEY ([ActivoID]) REFERENCES [dbo].[ActivoFijo_Activos]([ActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_PlanesMantenimiento] ADD CONSTRAINT [FK_AF_PlanesMantenimiento_Clase]
    FOREIGN KEY ([ClaseActivoID]) REFERENCES [dbo].[ActivoFijo_ClaseActivo]([ClaseActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_PlanesMantenimiento] ADD CONSTRAINT [FK_AF_PlanesMantenimiento_Medidor]
    FOREIGN KEY ([MedidorID]) REFERENCES [dbo].[ActivoFijo_Medidores]([MedidorID]);
GO
ALTER TABLE [dbo].[ActivoFijo_PlanesMantenimiento] ADD CONSTRAINT [FK_AF_PlanesMantenimiento_TipoOT]
    FOREIGN KEY ([TipoOTID]) REFERENCES [dbo].[ActivoFijo_TipoOT]([TipoOTID]);
GO
ALTER TABLE [dbo].[ActivoFijo_PlanesMantenimiento] ADD CONSTRAINT [FK_AF_PlanesMantenimiento_Ubicacion]
    FOREIGN KEY ([UbicacionID]) REFERENCES [dbo].[ActivoFijo_Ubicaciones]([UbicacionID]);
GO
ALTER TABLE [dbo].[ActivoFijo_ReemplazosActivos] ADD CONSTRAINT [FK_AF_ReemplazosActivos_Anterior]
    FOREIGN KEY ([ActivoAnteriorID]) REFERENCES [dbo].[ActivoFijo_Activos]([ActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_ReemplazosActivos] ADD CONSTRAINT [FK_AF_ReemplazosActivos_Autorizacion]
    FOREIGN KEY ([AutorizacionID]) REFERENCES [dbo].[ActivoFijo_Autorizaciones]([AutorizacionID]);
GO
ALTER TABLE [dbo].[ActivoFijo_ReemplazosActivos] ADD CONSTRAINT [FK_AF_ReemplazosActivos_Nuevo]
    FOREIGN KEY ([ActivoNuevoID]) REFERENCES [dbo].[ActivoFijo_Activos]([ActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_ReglasClaseLibro] ADD CONSTRAINT [FK_AF_ReglasClaseLibro_Clase]
    FOREIGN KEY ([ClaseActivoID]) REFERENCES [dbo].[ActivoFijo_ClaseActivo]([ClaseActivoID]);
GO
ALTER TABLE [dbo].[ActivoFijo_ReglasClaseLibro] ADD CONSTRAINT [FK_AF_ReglasClaseLibro_Libro]
    FOREIGN KEY ([LibroDepreciacionID]) REFERENCES [dbo].[ActivoFijo_LibrosDepreciacion]([LibroDepreciacionID]);
GO
ALTER TABLE [dbo].[ActivoFijo_ReglasClaseLibro] ADD CONSTRAINT [FK_AF_ReglasClaseLibro_Metodo]
    FOREIGN KEY ([MetodoDepreciacionID]) REFERENCES [dbo].[ActivoFijo_MetodosDepreciacion]([MetodoDepreciacionID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Ubicaciones] ADD CONSTRAINT [FK_AF_Ubicaciones_Padre]
    FOREIGN KEY ([UbicacionPadreID]) REFERENCES [dbo].[ActivoFijo_Ubicaciones]([UbicacionID]);
GO
ALTER TABLE [dbo].[ActivoFijo_Ubicaciones] ADD CONSTRAINT [FK_AF_Ubicaciones_Tipo]
    FOREIGN KEY ([TipoUbicacionID]) REFERENCES [dbo].[ActivoFijo_TipoUbicacion]([TipoUbicacionID]);
GO
ALTER TABLE [dbo].[automatizacion_inventarios_envios] ADD CONSTRAINT [FK_envios_procesado]
    FOREIGN KEY ([procesado_id]) REFERENCES [dbo].[automatizacion_inventarios_folios_procesados]([procesado_id]);
GO
ALTER TABLE [dbo].[CavaSocios_Botellas] ADD CONSTRAINT [FK_CavaSocios_Botellas_Socio]
    FOREIGN KEY ([SocioID]) REFERENCES [dbo].[CavaSocios_Socios]([SocioID]);
GO
ALTER TABLE [dbo].[CavaSocios_Cargos] ADD CONSTRAINT [FK_CavaSocios_Cargos_Botella]
    FOREIGN KEY ([BotellaID]) REFERENCES [dbo].[CavaSocios_Botellas]([BotellaID]);
GO
ALTER TABLE [dbo].[CavaSocios_Cargos] ADD CONSTRAINT [FK_CavaSocios_Cargos_Movimiento]
    FOREIGN KEY ([MovimientoID]) REFERENCES [dbo].[CavaSocios_Movimientos]([MovimientoID]);
GO
ALTER TABLE [dbo].[CavaSocios_Cargos] ADD CONSTRAINT [FK_CavaSocios_Cargos_Socio]
    FOREIGN KEY ([SocioID]) REFERENCES [dbo].[CavaSocios_Socios]([SocioID]);
GO
ALTER TABLE [dbo].[CavaSocios_Movimientos] ADD CONSTRAINT [FK_CavaSocios_Movimientos_Botella]
    FOREIGN KEY ([BotellaID]) REFERENCES [dbo].[CavaSocios_Botellas]([BotellaID]);
GO
ALTER TABLE [dbo].[CavaSocios_Movimientos] ADD CONSTRAINT [FK_CavaSocios_Movimientos_Socio]
    FOREIGN KEY ([SocioID]) REFERENCES [dbo].[CavaSocios_Socios]([SocioID]);
GO
ALTER TABLE [dbo].[Cliente_Catalogo] ADD CONSTRAINT [FK_Cliente_Catalogo_Cliente_Catalogo_Maestro]
    FOREIGN KEY ([ClienteMaestroID]) REFERENCES [dbo].[Cliente_Catalogo]([ClienteID]);
GO
ALTER TABLE [dbo].[Cliente_Catalogo] ADD CONSTRAINT [FK_Cliente_Catalogo_Cliente_Grupos]
    FOREIGN KEY ([GrupoClienteID]) REFERENCES [dbo].[Cliente_Grupos]([GrupoClienteID]);
GO
ALTER TABLE [dbo].[Cliente_Catalogo] ADD CONSTRAINT [FK_Cliente_Catalogo_Proveedor_Monedas]
    FOREIGN KEY ([MonedaID]) REFERENCES [dbo].[Proveedor_Monedas]([MonedaID]);
GO
ALTER TABLE [dbo].[Cliente_Catalogo] ADD CONSTRAINT [FK_Cliente_Catalogo_Venta_CondicionesPago]
    FOREIGN KEY ([CondicionPagoID]) REFERENCES [dbo].[Venta_CondicionesPago]([CondicionPagoID]);
GO
ALTER TABLE [dbo].[Cliente_Catalogo] ADD CONSTRAINT [FK_Cliente_Catalogo_Venta_ListasPrecios]
    FOREIGN KEY ([ListaPrecioID]) REFERENCES [dbo].[Venta_ListasPrecios]([ListaPrecioID]);
GO
ALTER TABLE [dbo].[Cliente_Contactos] ADD CONSTRAINT [FK_Cliente_Contactos_Cliente_Catalogo]
    FOREIGN KEY ([ClienteID]) REFERENCES [dbo].[Cliente_Catalogo]([ClienteID]);
GO
ALTER TABLE [dbo].[Cliente_Direcciones] ADD CONSTRAINT [FK_Cliente_Direcciones_Cliente_Catalogo]
    FOREIGN KEY ([ClienteID]) REFERENCES [dbo].[Cliente_Catalogo]([ClienteID]);
GO
ALTER TABLE [dbo].[Cliente_UsuariosPortal] ADD CONSTRAINT [FK_Cliente_UsuariosPortal_Cliente_Catalogo]
    FOREIGN KEY ([ClienteID]) REFERENCES [dbo].[Cliente_Catalogo]([ClienteID]);
GO
ALTER TABLE [dbo].[Cliente_UsuariosPortal] ADD CONSTRAINT [FK_Cliente_UsuariosPortal_Cliente_Contactos]
    FOREIGN KEY ([ContactoClienteID]) REFERENCES [dbo].[Cliente_Contactos]([ContactoClienteID]);
GO
ALTER TABLE [dbo].[Cliente_UsuariosPortal] ADD CONSTRAINT [FK_Cliente_UsuariosPortal_Cliente_RolUsuarioPortal]
    FOREIGN KEY ([RolPortalClienteID]) REFERENCES [dbo].[Cliente_RolUsuarioPortal]([RolPortalClienteID]);
GO
ALTER TABLE [dbo].[Comercial_Competidores] ADD CONSTRAINT [FK_Competidores_Empresa]
    FOREIGN KEY ([EmpresaID]) REFERENCES [dbo].[Sistema_Empresas]([EmpresaID]);
GO
ALTER TABLE [dbo].[Comercial_CompetidoresListasDetalle] ADD CONSTRAINT [FK_ListaDetalle_Competidor]
    FOREIGN KEY ([CompetidorID]) REFERENCES [dbo].[Comercial_Competidores]([CompetidorID]);
GO
ALTER TABLE [dbo].[Comercial_CompetidoresListasDetalle] ADD CONSTRAINT [FK_ListaDetalle_Lista]
    FOREIGN KEY ([ListaCompetidoresID]) REFERENCES [dbo].[Comercial_CompetidoresListas]([ListaCompetidoresID]);
GO
ALTER TABLE [dbo].[Comercial_CompetidoresMenuItems] ADD CONSTRAINT [FK_CompetidorMenuItem_Competidor]
    FOREIGN KEY ([CompetidorID]) REFERENCES [dbo].[Comercial_Competidores]([CompetidorID]);
GO
ALTER TABLE [dbo].[Comercial_CompetidoresUnidad] ADD CONSTRAINT [FK_CompetidoresUnidad_Catalogo]
    FOREIGN KEY ([CompetidorCatalogoID]) REFERENCES [dbo].[Comercial_CompetidoresCatalogo]([CompetidorCatalogoID]);
GO
ALTER TABLE [dbo].[Comercial_ImpuestosMapeo] ADD CONSTRAINT [FK_ImpuestosMapeo_Canonico]
    FOREIGN KEY ([ImpuestoCanonicoID]) REFERENCES [dbo].[Comercial_ImpuestosCatalogo]([ImpuestoID]);
GO
ALTER TABLE [dbo].[Comercial_ImpuestosMapeo] ADD CONSTRAINT [FK_ImpuestosMapeo_Servidor]
    FOREIGN KEY ([ServerID]) REFERENCES [dbo].[Servidores_Conexiones]([id]);
GO
ALTER TABLE [dbo].[Comercial_ImpuestosOverrides] ADD CONSTRAINT [FK_Overrides_Canonico]
    FOREIGN KEY ([ImpuestoCanonicoID]) REFERENCES [dbo].[Comercial_ImpuestosCatalogo]([ImpuestoID]);
GO
ALTER TABLE [dbo].[Comercial_ImpuestosTasas] ADD CONSTRAINT [FK_ImpuestosTasas_Catalogo]
    FOREIGN KEY ([ImpuestoID]) REFERENCES [dbo].[Comercial_ImpuestosCatalogo]([ImpuestoID]);
GO
ALTER TABLE [dbo].[Comercial_PreciosSugeridos] ADD CONSTRAINT [FK_PrecioSugerido_Regla]
    FOREIGN KEY ([ReglaPrecioID]) REFERENCES [dbo].[Comercial_ReglasPrecio]([ReglaPrecioID]);
GO
ALTER TABLE [dbo].[Comercial_PricingBenchmarkProducto] ADD CONSTRAINT [FK_BenchmarkProducto_Competidor]
    FOREIGN KEY ([CompetidorID]) REFERENCES [dbo].[Comercial_Competidores]([CompetidorID]);
GO
ALTER TABLE [dbo].[Comercial_PricingBenchmarkProducto] ADD CONSTRAINT [FK_BenchmarkProducto_Empresa]
    FOREIGN KEY ([EmpresaID]) REFERENCES [dbo].[Sistema_Empresas]([EmpresaID]);
GO
ALTER TABLE [dbo].[Comercial_PricingBenchmarkProducto] ADD CONSTRAINT [FK_BenchmarkProducto_MenuItem]
    FOREIGN KEY ([CompetidorMenuItemID]) REFERENCES [dbo].[Comercial_CompetidoresMenuItems]([CompetidorMenuItemID]);
GO
ALTER TABLE [dbo].[Comercial_ReglasPrecioRangos] ADD CONSTRAINT [FK_Rangos_Regla]
    FOREIGN KEY ([ReglaPrecioID]) REFERENCES [dbo].[Comercial_ReglasPrecio]([ReglaPrecioID]);
GO
ALTER TABLE [dbo].[Compras] ADD CONSTRAINT [FK_Compras_Autorizacion]
    FOREIGN KEY ([AutorizacionID]) REFERENCES [dbo].[Usuario_Autorizaciones]([AutorizacionID]);
GO
ALTER TABLE [dbo].[Compras] ADD CONSTRAINT [FK_Compras_Comprador]
    FOREIGN KEY ([CompradorUsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Compras] ADD CONSTRAINT [FK_Compras_CondicionPago]
    FOREIGN KEY ([CondicionPagoID]) REFERENCES [dbo].[Venta_CondicionesPago]([CondicionPagoID]);
GO
ALTER TABLE [dbo].[Compras] ADD CONSTRAINT [FK_Compras_Estatus]
    FOREIGN KEY ([EstatusCompraID]) REFERENCES [dbo].[Compras_Estatus]([EstatusCompraID]);
GO
ALTER TABLE [dbo].[Compras] ADD CONSTRAINT [FK_Compras_FormaPago]
    FOREIGN KEY ([FormaPagoID]) REFERENCES [dbo].[Venta_FormaPago]([FormaPagoID]);
GO
ALTER TABLE [dbo].[Compras] ADD CONSTRAINT [FK_Compras_Moneda]
    FOREIGN KEY ([MonedaID]) REFERENCES [dbo].[Proveedor_Monedas]([MonedaID]);
GO
ALTER TABLE [dbo].[Compras] ADD CONSTRAINT [FK_Compras_Orden]
    FOREIGN KEY ([OrdenCompraID]) REFERENCES [dbo].[Compras_Ordenes]([OrdenCompraID]);
GO
ALTER TABLE [dbo].[Compras] ADD CONSTRAINT [FK_Compras_Pedido]
    FOREIGN KEY ([PedidoCompraID]) REFERENCES [dbo].[Compras_Pedidos]([PedidoCompraID]);
GO
ALTER TABLE [dbo].[Compras] ADD CONSTRAINT [FK_Compras_Proveedor]
    FOREIGN KEY ([ProveedorID]) REFERENCES [dbo].[Proveedor_Catalogo]([ProveedorID]);
GO
ALTER TABLE [dbo].[Compras] ADD CONSTRAINT [FK_Compras_Recibio]
    FOREIGN KEY ([RecibioUsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Compras] ADD CONSTRAINT [FK_Compras_Sucursal]
    FOREIGN KEY ([SucursalID]) REFERENCES [dbo].[RH_Cat_Sucursales]([SucursalID]);
GO
ALTER TABLE [dbo].[Compras_ConciliacionSAT] ADD CONSTRAINT [FK_Compras_ConciliacionSAT_Compra]
    FOREIGN KEY ([CompraID]) REFERENCES [dbo].[Compras]([CompraID]);
GO
ALTER TABLE [dbo].[Compras_ConciliacionSAT] ADD CONSTRAINT [FK_Compras_ConciliacionSAT_Documento]
    FOREIGN KEY ([DocumentoFiscalID]) REFERENCES [dbo].[Compras_DocumentosFiscales]([DocumentoFiscalID]);
GO
ALTER TABLE [dbo].[Compras_ConciliacionSAT] ADD CONSTRAINT [FK_Compras_ConciliacionSAT_Estatus]
    FOREIGN KEY ([EstatusConciliacionSATID]) REFERENCES [dbo].[Compras_ConciliacionSATEstatus]([EstatusConciliacionSATID]);
GO
ALTER TABLE [dbo].[Compras_ConciliacionSAT] ADD CONSTRAINT [FK_Compras_ConciliacionSAT_Usuario]
    FOREIGN KEY ([UsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Compras_ConciliacionSATDetalle] ADD CONSTRAINT [FK_Compras_ConciliacionSATDetalle_CompraDetalle]
    FOREIGN KEY ([CompraDetalleID]) REFERENCES [dbo].[Compras_Detalle]([DetalleCompraID]);
GO
ALTER TABLE [dbo].[Compras_ConciliacionSATDetalle] ADD CONSTRAINT [FK_Compras_ConciliacionSATDetalle_Conciliacion]
    FOREIGN KEY ([ConciliacionSATID]) REFERENCES [dbo].[Compras_ConciliacionSAT]([ConciliacionSATID]);
GO
ALTER TABLE [dbo].[Compras_ConciliacionSATDetalle] ADD CONSTRAINT [FK_Compras_ConciliacionSATDetalle_DocDetalle]
    FOREIGN KEY ([DocumentoFiscalDetalleID]) REFERENCES [dbo].[Compras_DocumentosFiscalesDetalle]([DocumentoFiscalDetalleID]);
GO
ALTER TABLE [dbo].[Compras_ConciliacionSATDetalle] ADD CONSTRAINT [FK_Compras_ConciliacionSATDetalle_Presentacion]
    FOREIGN KEY ([PresentacionProductoID]) REFERENCES [dbo].[Producto_Presentaciones]([PresentacionProductoID]);
GO
ALTER TABLE [dbo].[Compras_ConciliacionSATDetalle] ADD CONSTRAINT [FK_Compras_ConciliacionSATDetalle_Producto]
    FOREIGN KEY ([ProductoID]) REFERENCES [dbo].[Producto_Catalogo]([ProductoID]);
GO
ALTER TABLE [dbo].[Compras_ConciliacionSATDetalle] ADD CONSTRAINT [FK_Compras_ConciliacionSATDetalle_RecepcionDetalle]
    FOREIGN KEY ([RecepcionDetalleID]) REFERENCES [dbo].[Compras_RecepcionesDetalle]([RecepcionDetalleID]);
GO
ALTER TABLE [dbo].[Compras_Detalle] ADD CONSTRAINT [FK_Compras_Detalle_Compra]
    FOREIGN KEY ([CompraID]) REFERENCES [dbo].[Compras]([CompraID]);
GO
ALTER TABLE [dbo].[Compras_Detalle] ADD CONSTRAINT [FK_Compras_Detalle_OrdenDetalle]
    FOREIGN KEY ([OrdenDetalleCompraID]) REFERENCES [dbo].[Compras_OrdenesDetalle]([DetalleOrdenCompraID]);
GO
ALTER TABLE [dbo].[Compras_Detalle] ADD CONSTRAINT [FK_Compras_Detalle_PedidoDetalle]
    FOREIGN KEY ([PedidoDetalleCompraID]) REFERENCES [dbo].[Compras_PedidosDetalle]([DetallePedidoCompraID]);
GO
ALTER TABLE [dbo].[Compras_Detalle] ADD CONSTRAINT [FK_Compras_Detalle_Presentacion]
    FOREIGN KEY ([PresentacionProductoID]) REFERENCES [dbo].[Producto_Presentaciones]([PresentacionProductoID]);
GO
ALTER TABLE [dbo].[Compras_Detalle] ADD CONSTRAINT [FK_Compras_Detalle_Producto]
    FOREIGN KEY ([ProductoID]) REFERENCES [dbo].[Producto_Catalogo]([ProductoID]);
GO
ALTER TABLE [dbo].[Compras_DocumentosFiscales] ADD CONSTRAINT [FK_Compras_DocumentosFiscales_Compra]
    FOREIGN KEY ([CompraID]) REFERENCES [dbo].[Compras]([CompraID]);
GO
ALTER TABLE [dbo].[Compras_DocumentosFiscales] ADD CONSTRAINT [FK_Compras_DocumentosFiscales_Estatus]
    FOREIGN KEY ([EstatusDocumentoFiscalID]) REFERENCES [dbo].[Compras_DocumentosFiscalesEstatus]([EstatusDocumentoFiscalID]);
GO
ALTER TABLE [dbo].[Compras_DocumentosFiscales] ADD CONSTRAINT [FK_Compras_DocumentosFiscales_Proveedor]
    FOREIGN KEY ([ProveedorID]) REFERENCES [dbo].[Proveedor_Catalogo]([ProveedorID]);
GO
ALTER TABLE [dbo].[Compras_DocumentosFiscales] ADD CONSTRAINT [FK_Compras_DocumentosFiscales_Sucursal]
    FOREIGN KEY ([SucursalID]) REFERENCES [dbo].[RH_Cat_Sucursales]([SucursalID]);
GO
ALTER TABLE [dbo].[Compras_DocumentosFiscales] ADD CONSTRAINT [FK_Compras_DocumentosFiscales_SucursalFiscal]
    FOREIGN KEY ([SucursalFiscalID]) REFERENCES [dbo].[RH_Cat_SucursalesFiscal]([SucursalFiscalID]);
GO
ALTER TABLE [dbo].[Compras_DocumentosFiscalesDetalle] ADD CONSTRAINT [FK_Compras_DocumentosFiscalesDetalle_Documento]
    FOREIGN KEY ([DocumentoFiscalID]) REFERENCES [dbo].[Compras_DocumentosFiscales]([DocumentoFiscalID]);
GO
ALTER TABLE [dbo].[Compras_DocumentosFiscalesDetalle] ADD CONSTRAINT [FK_Compras_DocumentosFiscalesDetalle_Presentacion]
    FOREIGN KEY ([PresentacionProductoID]) REFERENCES [dbo].[Producto_Presentaciones]([PresentacionProductoID]);
GO
ALTER TABLE [dbo].[Compras_DocumentosFiscalesDetalle] ADD CONSTRAINT [FK_Compras_DocumentosFiscalesDetalle_Producto]
    FOREIGN KEY ([ProductoID]) REFERENCES [dbo].[Producto_Catalogo]([ProductoID]);
GO
ALTER TABLE [dbo].[Compras_Ordenes] ADD CONSTRAINT [FK_Compras_Ordenes_Autorizacion]
    FOREIGN KEY ([AutorizacionID]) REFERENCES [dbo].[Usuario_Autorizaciones]([AutorizacionID]);
GO
ALTER TABLE [dbo].[Compras_Ordenes] ADD CONSTRAINT [FK_Compras_Ordenes_Comprador]
    FOREIGN KEY ([CompradorUsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Compras_Ordenes] ADD CONSTRAINT [FK_Compras_Ordenes_CondicionPago]
    FOREIGN KEY ([CondicionPagoID]) REFERENCES [dbo].[Venta_CondicionesPago]([CondicionPagoID]);
GO
ALTER TABLE [dbo].[Compras_Ordenes] ADD CONSTRAINT [FK_Compras_Ordenes_Estatus]
    FOREIGN KEY ([EstatusOrdenCompraID]) REFERENCES [dbo].[Compras_OrdenesEstatus]([EstatusOrdenCompraID]);
GO
ALTER TABLE [dbo].[Compras_Ordenes] ADD CONSTRAINT [FK_Compras_Ordenes_Moneda]
    FOREIGN KEY ([MonedaID]) REFERENCES [dbo].[Proveedor_Monedas]([MonedaID]);
GO
ALTER TABLE [dbo].[Compras_Ordenes] ADD CONSTRAINT [FK_Compras_Ordenes_Pedido]
    FOREIGN KEY ([PedidoCompraID]) REFERENCES [dbo].[Compras_Pedidos]([PedidoCompraID]);
GO
ALTER TABLE [dbo].[Compras_Ordenes] ADD CONSTRAINT [FK_Compras_Ordenes_Proveedor]
    FOREIGN KEY ([ProveedorID]) REFERENCES [dbo].[Proveedor_Catalogo]([ProveedorID]);
GO
ALTER TABLE [dbo].[Compras_Ordenes] ADD CONSTRAINT [FK_Compras_Ordenes_Solicitante]
    FOREIGN KEY ([SolicitanteUsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Compras_Ordenes] ADD CONSTRAINT [FK_Compras_Ordenes_Sucursal]
    FOREIGN KEY ([SucursalID]) REFERENCES [dbo].[RH_Cat_Sucursales]([SucursalID]);
GO
ALTER TABLE [dbo].[Compras_OrdenesDetalle] ADD CONSTRAINT [FK_Compras_OrdenesDetalle_Orden]
    FOREIGN KEY ([OrdenCompraID]) REFERENCES [dbo].[Compras_Ordenes]([OrdenCompraID]);
GO
ALTER TABLE [dbo].[Compras_OrdenesDetalle] ADD CONSTRAINT [FK_Compras_OrdenesDetalle_PedidoDetalle]
    FOREIGN KEY ([PedidoDetalleCompraID]) REFERENCES [dbo].[Compras_PedidosDetalle]([DetallePedidoCompraID]);
GO
ALTER TABLE [dbo].[Compras_OrdenesDetalle] ADD CONSTRAINT [FK_Compras_OrdenesDetalle_Presentacion]
    FOREIGN KEY ([PresentacionProductoID]) REFERENCES [dbo].[Producto_Presentaciones]([PresentacionProductoID]);
GO
ALTER TABLE [dbo].[Compras_OrdenesDetalle] ADD CONSTRAINT [FK_Compras_OrdenesDetalle_Producto]
    FOREIGN KEY ([ProductoID]) REFERENCES [dbo].[Producto_Catalogo]([ProductoID]);
GO
ALTER TABLE [dbo].[Compras_Pedidos] ADD CONSTRAINT [FK_Compras_Pedidos_Autorizacion]
    FOREIGN KEY ([AutorizacionID]) REFERENCES [dbo].[Usuario_Autorizaciones]([AutorizacionID]);
GO
ALTER TABLE [dbo].[Compras_Pedidos] ADD CONSTRAINT [FK_Compras_Pedidos_Comprador]
    FOREIGN KEY ([CompradorUsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Compras_Pedidos] ADD CONSTRAINT [FK_Compras_Pedidos_Estatus]
    FOREIGN KEY ([EstatusPedidoCompraID]) REFERENCES [dbo].[Compras_PedidosEstatus]([EstatusPedidoCompraID]);
GO
ALTER TABLE [dbo].[Compras_Pedidos] ADD CONSTRAINT [FK_Compras_Pedidos_Moneda]
    FOREIGN KEY ([MonedaID]) REFERENCES [dbo].[Proveedor_Monedas]([MonedaID]);
GO
ALTER TABLE [dbo].[Compras_Pedidos] ADD CONSTRAINT [FK_Compras_Pedidos_ProveedorSugerido]
    FOREIGN KEY ([ProveedorSugeridoID]) REFERENCES [dbo].[Proveedor_Catalogo]([ProveedorID]);
GO
ALTER TABLE [dbo].[Compras_Pedidos] ADD CONSTRAINT [FK_Compras_Pedidos_Solicitante]
    FOREIGN KEY ([SolicitanteUsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Compras_Pedidos] ADD CONSTRAINT [FK_Compras_Pedidos_Sucursal]
    FOREIGN KEY ([SucursalID]) REFERENCES [dbo].[RH_Cat_Sucursales]([SucursalID]);
GO
ALTER TABLE [dbo].[Compras_PedidosDetalle] ADD CONSTRAINT [FK_Compras_PedidosDetalle_Pedido]
    FOREIGN KEY ([PedidoCompraID]) REFERENCES [dbo].[Compras_Pedidos]([PedidoCompraID]);
GO
ALTER TABLE [dbo].[Compras_PedidosDetalle] ADD CONSTRAINT [FK_Compras_PedidosDetalle_Presentacion]
    FOREIGN KEY ([PresentacionProductoID]) REFERENCES [dbo].[Producto_Presentaciones]([PresentacionProductoID]);
GO
ALTER TABLE [dbo].[Compras_PedidosDetalle] ADD CONSTRAINT [FK_Compras_PedidosDetalle_Producto]
    FOREIGN KEY ([ProductoID]) REFERENCES [dbo].[Producto_Catalogo]([ProductoID]);
GO
ALTER TABLE [dbo].[Compras_Recepciones] ADD CONSTRAINT [FK_Compras_Recepciones_Almacen]
    FOREIGN KEY ([AlmacenID]) REFERENCES [dbo].[Inventario_Almacenes]([AlmacenID]);
GO
ALTER TABLE [dbo].[Compras_Recepciones] ADD CONSTRAINT [FK_Compras_Recepciones_Compra]
    FOREIGN KEY ([CompraID]) REFERENCES [dbo].[Compras]([CompraID]);
GO
ALTER TABLE [dbo].[Compras_Recepciones] ADD CONSTRAINT [FK_Compras_Recepciones_Estatus]
    FOREIGN KEY ([EstatusRecepcionID]) REFERENCES [dbo].[Compras_RecepcionesEstatus]([EstatusRecepcionID]);
GO
ALTER TABLE [dbo].[Compras_Recepciones] ADD CONSTRAINT [FK_Compras_Recepciones_Movimiento]
    FOREIGN KEY ([MovimientoInventarioID]) REFERENCES [dbo].[Inventario_Movimientos]([MovimientoID]);
GO
ALTER TABLE [dbo].[Compras_Recepciones] ADD CONSTRAINT [FK_Compras_Recepciones_Orden]
    FOREIGN KEY ([OrdenCompraID]) REFERENCES [dbo].[Compras_Ordenes]([OrdenCompraID]);
GO
ALTER TABLE [dbo].[Compras_Recepciones] ADD CONSTRAINT [FK_Compras_Recepciones_Proveedor]
    FOREIGN KEY ([ProveedorID]) REFERENCES [dbo].[Proveedor_Catalogo]([ProveedorID]);
GO
ALTER TABLE [dbo].[Compras_Recepciones] ADD CONSTRAINT [FK_Compras_Recepciones_Recibio]
    FOREIGN KEY ([RecibioUsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Compras_Recepciones] ADD CONSTRAINT [FK_Compras_Recepciones_Reviso]
    FOREIGN KEY ([RevisoUsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Compras_Recepciones] ADD CONSTRAINT [FK_Compras_Recepciones_Sucursal]
    FOREIGN KEY ([SucursalID]) REFERENCES [dbo].[RH_Cat_Sucursales]([SucursalID]);
GO
ALTER TABLE [dbo].[Compras_RecepcionesDetalle] ADD CONSTRAINT [FK_Compras_RecepcionesDetalle_CompraDetalle]
    FOREIGN KEY ([CompraDetalleID]) REFERENCES [dbo].[Compras_Detalle]([DetalleCompraID]);
GO
ALTER TABLE [dbo].[Compras_RecepcionesDetalle] ADD CONSTRAINT [FK_Compras_RecepcionesDetalle_MovimientoDetalle]
    FOREIGN KEY ([MovimientoDetalleID]) REFERENCES [dbo].[Inventario_MovimientosDetalle]([MovimientoDetalleID]);
GO
ALTER TABLE [dbo].[Compras_RecepcionesDetalle] ADD CONSTRAINT [FK_Compras_RecepcionesDetalle_OrdenDetalle]
    FOREIGN KEY ([OrdenDetalleID]) REFERENCES [dbo].[Compras_OrdenesDetalle]([DetalleOrdenCompraID]);
GO
ALTER TABLE [dbo].[Compras_RecepcionesDetalle] ADD CONSTRAINT [FK_Compras_RecepcionesDetalle_Presentacion]
    FOREIGN KEY ([PresentacionProductoID]) REFERENCES [dbo].[Producto_Presentaciones]([PresentacionProductoID]);
GO
ALTER TABLE [dbo].[Compras_RecepcionesDetalle] ADD CONSTRAINT [FK_Compras_RecepcionesDetalle_Producto]
    FOREIGN KEY ([ProductoID]) REFERENCES [dbo].[Producto_Catalogo]([ProductoID]);
GO
ALTER TABLE [dbo].[Compras_RecepcionesDetalle] ADD CONSTRAINT [FK_Compras_RecepcionesDetalle_Recepcion]
    FOREIGN KEY ([RecepcionCompraID]) REFERENCES [dbo].[Compras_Recepciones]([RecepcionCompraID]);
GO
ALTER TABLE [dbo].[ConsultasSQL_Catalogo] ADD CONSTRAINT [FK_ConsultasSQL_SistemaTipo]
    FOREIGN KEY ([SistemaTipoID]) REFERENCES [dbo].[Sistema_Tipos]([SistemaTipoID]);
GO
ALTER TABLE [dbo].[ConsultasSQL_Parametros] ADD CONSTRAINT [FK_ConsultasSQL_Param_Consulta]
    FOREIGN KEY ([ConsultaID]) REFERENCES [dbo].[ConsultasSQL_Catalogo]([ConsultaID]);
GO
ALTER TABLE [dbo].[ConsultasSQL_Permisos] ADD CONSTRAINT [FK_ConsultasSQL_Perm_Consulta]
    FOREIGN KEY ([ConsultaID]) REFERENCES [dbo].[ConsultasSQL_Catalogo]([ConsultaID]);
GO
ALTER TABLE [dbo].[ConsultasSQL_Servidores] ADD CONSTRAINT [FK_ConsultasSQL_Srv_Consulta]
    FOREIGN KEY ([ConsultaID]) REFERENCES [dbo].[ConsultasSQL_Catalogo]([ConsultaID]);
GO
ALTER TABLE [dbo].[ConsultasSQL_Versiones] ADD CONSTRAINT [FK_ConsultasSQL_Ver_Consulta]
    FOREIGN KEY ([ConsultaID]) REFERENCES [dbo].[ConsultasSQL_Catalogo]([ConsultaID]);
GO
ALTER TABLE [dbo].[CRM_ActividadesHistorial] ADD CONSTRAINT [FK__CRM_Activ__Activ__286EBB3B]
    FOREIGN KEY ([ActividadID]) REFERENCES [dbo].[CRM_Actividades]([ActividadID]);
GO
ALTER TABLE [dbo].[CRM_Implementaciones] ADD CONSTRAINT [FK__CRM_Imple__Cuent__300FDD03]
    FOREIGN KEY ([CuentaID]) REFERENCES [dbo].[CRM_Cuentas]([CuentaID]);
GO
ALTER TABLE [dbo].[CRM_Implementaciones] ADD CONSTRAINT [FK__CRM_Imple__Pedid__2F1BB8CA]
    FOREIGN KEY ([PedidoID]) REFERENCES [dbo].[Venta_Pedidos]([PedidoID]);
GO
ALTER TABLE [dbo].[CRM_ImplementacionesEntregables] ADD CONSTRAINT [FK__CRM_Imple__Imple__36BCDA92]
    FOREIGN KEY ([ImplementacionID]) REFERENCES [dbo].[CRM_Implementaciones]([ImplementacionID]);
GO
ALTER TABLE [dbo].[CRM_IntegracionesConflictos] ADD CONSTRAINT [FK__CRM_Integ__SyncL__4DA03FEA]
    FOREIGN KEY ([SyncLogID]) REFERENCES [dbo].[CRM_IntegracionesSyncLog]([SyncLogID]);
GO
ALTER TABLE [dbo].[CRM_OportunidadesHistorial] ADD CONSTRAINT [FK__CRM_Oport__Oport__21C1BDAC]
    FOREIGN KEY ([OportunidadID]) REFERENCES [dbo].[CRM_Oportunidades]([OportunidadID]);
GO
ALTER TABLE [dbo].[CRM_PostventaEncuestas] ADD CONSTRAINT [FK__CRM_Postv__Cuent__4416D5B0]
    FOREIGN KEY ([CuentaID]) REFERENCES [dbo].[CRM_Cuentas]([CuentaID]);
GO
ALTER TABLE [dbo].[CRM_PostventaEncuestas] ADD CONSTRAINT [FK__CRM_Postv__Ticke__450AF9E9]
    FOREIGN KEY ([TicketID]) REFERENCES [dbo].[CRM_PostventaTickets]([TicketID]);
GO
ALTER TABLE [dbo].[CRM_PostventaTickets] ADD CONSTRAINT [FK__CRM_Postv__Cuent__3D69D821]
    FOREIGN KEY ([CuentaID]) REFERENCES [dbo].[CRM_Cuentas]([CuentaID]);
GO
ALTER TABLE [dbo].[Finanzas_Cat_CuentasBancarias] ADD CONSTRAINT [FK_CuentasBancarias_Banco]
    FOREIGN KEY ([BancoID]) REFERENCES [dbo].[Global_Cat_Bancos]([BancoID]);
GO
ALTER TABLE [dbo].[Finanzas_Cat_CuentasBancarias] ADD CONSTRAINT [FK_CuentasBancarias_UsuarioCreacion]
    FOREIGN KEY ([UsuarioCreacionID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Finanzas_Cat_CuentasBancarias] ADD CONSTRAINT [FK_CuentasBancarias_UsuarioModificacion]
    FOREIGN KEY ([UsuarioModificacionID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Finanzas_CortesCaja_DetallePagos] ADD CONSTRAINT [FK_DetallePagos_Corte]
    FOREIGN KEY ([CorteCajaID]) REFERENCES [dbo].[Finanzas_CortesCaja]([CorteCajaID]);
GO
ALTER TABLE [dbo].[Finanzas_Presupuestos] ADD CONSTRAINT [FK_Presupuesto_Sucursal]
    FOREIGN KEY ([SucursalID]) REFERENCES [dbo].[RH_Cat_Sucursales]([SucursalID]);
GO
ALTER TABLE [dbo].[Finanzas_SaldosBancarios] ADD CONSTRAINT [FK_SaldosBancarios_CuentaBancaria]
    FOREIGN KEY ([CuentaBancariaID]) REFERENCES [dbo].[Finanzas_Cat_CuentasBancarias]([CuentaBancariaID]);
GO
ALTER TABLE [dbo].[Finanzas_SaldosBancarios] ADD CONSTRAINT [FK_SaldosBancarios_UsuarioCancelacion]
    FOREIGN KEY ([UsuarioCancelacionID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Finanzas_SaldosBancarios] ADD CONSTRAINT [FK_SaldosBancarios_UsuarioCreacion]
    FOREIGN KEY ([UsuarioCreacionID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Finanzas_SaldosBancarios] ADD CONSTRAINT [FK_SaldosBancarios_UsuarioModificacion]
    FOREIGN KEY ([UsuarioModificacionID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Inventario_Almacenes] ADD CONSTRAINT [FK_Inventario_Almacenes_Sucursal]
    FOREIGN KEY ([SucursalID]) REFERENCES [dbo].[RH_Cat_Sucursales]([SucursalID]);
GO
ALTER TABLE [dbo].[Inventario_Existencias] ADD CONSTRAINT [FK_Inventario_Existencias_Almacen]
    FOREIGN KEY ([AlmacenID]) REFERENCES [dbo].[Inventario_Almacenes]([AlmacenID]);
GO
ALTER TABLE [dbo].[Inventario_Existencias] ADD CONSTRAINT [FK_Inventario_Existencias_Presentacion]
    FOREIGN KEY ([PresentacionProductoID]) REFERENCES [dbo].[Producto_Presentaciones]([PresentacionProductoID]);
GO
ALTER TABLE [dbo].[Inventario_Existencias] ADD CONSTRAINT [FK_Inventario_Existencias_Producto]
    FOREIGN KEY ([ProductoID]) REFERENCES [dbo].[Producto_Catalogo]([ProductoID]);
GO
ALTER TABLE [dbo].[Inventario_Existencias] ADD CONSTRAINT [FK_Inventario_Existencias_Sucursal]
    FOREIGN KEY ([SucursalID]) REFERENCES [dbo].[RH_Cat_Sucursales]([SucursalID]);
GO
ALTER TABLE [dbo].[Inventario_Movimientos] ADD CONSTRAINT [FK_Inventario_Movimientos_Almacen]
    FOREIGN KEY ([AlmacenID]) REFERENCES [dbo].[Inventario_Almacenes]([AlmacenID]);
GO
ALTER TABLE [dbo].[Inventario_Movimientos] ADD CONSTRAINT [FK_Inventario_Movimientos_Sucursal]
    FOREIGN KEY ([SucursalID]) REFERENCES [dbo].[RH_Cat_Sucursales]([SucursalID]);
GO
ALTER TABLE [dbo].[Inventario_Movimientos] ADD CONSTRAINT [FK_Inventario_Movimientos_Tipo]
    FOREIGN KEY ([TipoMovimientoID]) REFERENCES [dbo].[Inventario_TipoMovimiento]([TipoMovimientoID]);
GO
ALTER TABLE [dbo].[Inventario_Movimientos] ADD CONSTRAINT [FK_Inventario_Movimientos_Usuario]
    FOREIGN KEY ([UsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Inventario_MovimientosDetalle] ADD CONSTRAINT [FK_Inventario_MovimientosDetalle_Movimiento]
    FOREIGN KEY ([MovimientoID]) REFERENCES [dbo].[Inventario_Movimientos]([MovimientoID]);
GO
ALTER TABLE [dbo].[Inventario_MovimientosDetalle] ADD CONSTRAINT [FK_Inventario_MovimientosDetalle_Presentacion]
    FOREIGN KEY ([PresentacionProductoID]) REFERENCES [dbo].[Producto_Presentaciones]([PresentacionProductoID]);
GO
ALTER TABLE [dbo].[Inventario_MovimientosDetalle] ADD CONSTRAINT [FK_Inventario_MovimientosDetalle_Producto]
    FOREIGN KEY ([ProductoID]) REFERENCES [dbo].[Producto_Catalogo]([ProductoID]);
GO
ALTER TABLE [dbo].[Producto_Catalogo] ADD CONSTRAINT [FK_Producto_Catalogo_Producto_Lineas]
    FOREIGN KEY ([LineaProductoID]) REFERENCES [dbo].[Producto_Lineas]([LineaProductoID]);
GO
ALTER TABLE [dbo].[Producto_Catalogo] ADD CONSTRAINT [FK_Producto_Catalogo_Producto_Marcas]
    FOREIGN KEY ([MarcaProductoID]) REFERENCES [dbo].[Producto_Marcas]([MarcaProductoID]);
GO
ALTER TABLE [dbo].[Producto_Catalogo] ADD CONSTRAINT [FK_Producto_Catalogo_Proveedor_Monedas]
    FOREIGN KEY ([MonedaID]) REFERENCES [dbo].[Proveedor_Monedas]([MonedaID]);
GO
ALTER TABLE [dbo].[Producto_Equivalentes] ADD CONSTRAINT [FK_Producto_Equivalentes_Producto_Catalogo]
    FOREIGN KEY ([ProductoID]) REFERENCES [dbo].[Producto_Catalogo]([ProductoID]);
GO
ALTER TABLE [dbo].[Producto_Equivalentes] ADD CONSTRAINT [FK_Producto_Equivalentes_Producto_Catalogo_Equivalente]
    FOREIGN KEY ([ProductoEquivalenteRefID]) REFERENCES [dbo].[Producto_Catalogo]([ProductoID]);
GO
ALTER TABLE [dbo].[Producto_Lineas] ADD CONSTRAINT [FK_Producto_Lineas_Producto_SubFamilias]
    FOREIGN KEY ([SubFamiliaProductoID]) REFERENCES [dbo].[Producto_SubFamilias]([SubFamiliaProductoID]);
GO
ALTER TABLE [dbo].[Producto_Presentaciones] ADD CONSTRAINT [FK_Producto_Presentaciones_Producto_Catalogo]
    FOREIGN KEY ([ProductoID]) REFERENCES [dbo].[Producto_Catalogo]([ProductoID]);
GO
ALTER TABLE [dbo].[Producto_SubFamilias] ADD CONSTRAINT [FK_Producto_SubFamilias_Producto_Familias]
    FOREIGN KEY ([FamiliaProductoID]) REFERENCES [dbo].[Producto_Familias]([FamiliaProductoID]);
GO
ALTER TABLE [dbo].[Producto_Sustitutos] ADD CONSTRAINT [FK_Producto_Sustitutos_Producto_Catalogo]
    FOREIGN KEY ([ProductoID]) REFERENCES [dbo].[Producto_Catalogo]([ProductoID]);
GO
ALTER TABLE [dbo].[Producto_Sustitutos] ADD CONSTRAINT [FK_Producto_Sustitutos_Producto_Catalogo_Sustituto]
    FOREIGN KEY ([ProductoSustitutoRefID]) REFERENCES [dbo].[Producto_Catalogo]([ProductoID]);
GO
ALTER TABLE [dbo].[propinas_tpv_historial] ADD CONSTRAINT [FK_historial_propina]
    FOREIGN KEY ([propina_id]) REFERENCES [dbo].[propinas_tpv_control]([id]);
GO
ALTER TABLE [dbo].[Proveedor_Categorias] ADD CONSTRAINT [FK_Proveedor_Categorias_Categoria]
    FOREIGN KEY ([CategoriaProveedorID]) REFERENCES [dbo].[Proveedor_CategoriasCatalogo]([CategoriaProveedorID]);
GO
ALTER TABLE [dbo].[Proveedor_Categorias] ADD CONSTRAINT [FK_Proveedor_Categorias_Proveedor]
    FOREIGN KEY ([ProveedorID]) REFERENCES [dbo].[Proveedor_Catalogo]([ProveedorID]);
GO
ALTER TABLE [dbo].[Proveedor_CategoriasCatalogo] ADD CONSTRAINT [FK_Cat_CategoriasProveedor_Padre]
    FOREIGN KEY ([CategoriaPadreID]) REFERENCES [dbo].[Proveedor_CategoriasCatalogo]([CategoriaProveedorID]);
GO
ALTER TABLE [dbo].[Proveedor_Contactos] ADD CONSTRAINT [FK_Proveedor_Contactos_Proveedor]
    FOREIGN KEY ([ProveedorID]) REFERENCES [dbo].[Proveedor_Catalogo]([ProveedorID]);
GO
ALTER TABLE [dbo].[Proveedor_Contactos] ADD CONSTRAINT [FK_Proveedor_Contactos_TipoContacto]
    FOREIGN KEY ([TipoContactoID]) REFERENCES [dbo].[Proveedor_TipoContacto]([TipoContactoID]);
GO
ALTER TABLE [dbo].[Proveedor_CuentasBancarias] ADD CONSTRAINT [FK_Proveedor_CuentasBancarias_Banco]
    FOREIGN KEY ([BancoID]) REFERENCES [dbo].[Proveedor_Bancos]([BancoID]);
GO
ALTER TABLE [dbo].[Proveedor_CuentasBancarias] ADD CONSTRAINT [FK_Proveedor_CuentasBancarias_Moneda]
    FOREIGN KEY ([MonedaID]) REFERENCES [dbo].[Proveedor_Monedas]([MonedaID]);
GO
ALTER TABLE [dbo].[Proveedor_CuentasBancarias] ADD CONSTRAINT [FK_Proveedor_CuentasBancarias_Proveedor]
    FOREIGN KEY ([ProveedorID]) REFERENCES [dbo].[Proveedor_Catalogo]([ProveedorID]);
GO
ALTER TABLE [dbo].[Proveedor_Documentos] ADD CONSTRAINT [FK_Proveedor_Documentos_Proveedor]
    FOREIGN KEY ([ProveedorID]) REFERENCES [dbo].[Proveedor_Catalogo]([ProveedorID]);
GO
ALTER TABLE [dbo].[Proveedor_Documentos] ADD CONSTRAINT [FK_Proveedor_Documentos_TipoDocumento]
    FOREIGN KEY ([TipoDocumentoID]) REFERENCES [dbo].[Proveedor_TipoDocumento]([TipoDocumentoID]);
GO
ALTER TABLE [dbo].[Proveedor_Evaluaciones] ADD CONSTRAINT [FK_Proveedor_Evaluaciones_Proveedor]
    FOREIGN KEY ([ProveedorID]) REFERENCES [dbo].[Proveedor_Catalogo]([ProveedorID]);
GO
ALTER TABLE [dbo].[Proveedor_Integracion] ADD CONSTRAINT [FK_Proveedor_Integracion_Estatus]
    FOREIGN KEY ([EstatusSincronizacionID]) REFERENCES [dbo].[Proveedor_EstatusSincronizacion]([EstatusSincronizacionID]);
GO
ALTER TABLE [dbo].[Proveedor_Integracion] ADD CONSTRAINT [FK_Proveedor_Integracion_Proveedor]
    FOREIGN KEY ([ProveedorID]) REFERENCES [dbo].[Proveedor_Catalogo]([ProveedorID]);
GO
ALTER TABLE [dbo].[Proveedor_Integracion] ADD CONSTRAINT [FK_Proveedor_Integracion_Sistema]
    FOREIGN KEY ([SistemaID]) REFERENCES [dbo].[Proveedor_SistemasIntegracion]([SistemaID]);
GO
ALTER TABLE [dbo].[Proveedor_UsuariosPortal] ADD CONSTRAINT [FK_Proveedor_UsuariosPortal_Proveedor]
    FOREIGN KEY ([ProveedorID]) REFERENCES [dbo].[Proveedor_Catalogo]([ProveedorID]);
GO
ALTER TABLE [dbo].[Proveedor_UsuariosPortal] ADD CONSTRAINT [FK_Proveedor_UsuariosPortal_Rol]
    FOREIGN KEY ([RolPortalID]) REFERENCES [dbo].[Proveedor_RolUsuarioPortal]([RolPortalID]);
GO
ALTER TABLE [dbo].[RH_Auditoria_Fiscal] ADD CONSTRAINT [FK__RH_Audito__Colab__7740A8A4]
    FOREIGN KEY ([ColaboradorID]) REFERENCES [dbo].[RH_Colaboradores_Expediente]([ColaboradorID]);
GO
ALTER TABLE [dbo].[RH_Auditoria_Fiscal] ADD CONSTRAINT [FK_RH_Auditoria_Fiscal_PeriodoNomina]
    FOREIGN KEY ([PeriodoNominaID]) REFERENCES [dbo].[RH_Periodos_Nomina]([PeriodoNominaID]);
GO
ALTER TABLE [dbo].[RH_Ausencias] ADD CONSTRAINT [FK_RH_Ausencias_AprobadoPor]
    FOREIGN KEY ([AprobadoPor]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[RH_Ausencias] ADD CONSTRAINT [FK_RH_Ausencias_Colaborador]
    FOREIGN KEY ([ColaboradorID]) REFERENCES [dbo].[RH_Colaboradores_Expediente]([ColaboradorID]);
GO
ALTER TABLE [dbo].[RH_Ausencias] ADD CONSTRAINT [FK_RH_Ausencias_TipoAusencia]
    FOREIGN KEY ([TipoAusenciaID]) REFERENCES [dbo].[RH_Cat_TiposAusencia]([TipoAusenciaID]);
GO
ALTER TABLE [dbo].[RH_Calendario_Laboral] ADD CONSTRAINT [FK_RH_Calendario_Laboral_Sucursal]
    FOREIGN KEY ([SucursalID]) REFERENCES [dbo].[RH_Cat_Sucursales]([SucursalID]);
GO
ALTER TABLE [dbo].[RH_Calendario_Laboral] ADD CONSTRAINT [FK_RH_Calendario_Laboral_SucursalFiscal]
    FOREIGN KEY ([SucursalFiscalID]) REFERENCES [dbo].[RH_Cat_SucursalesFiscal]([SucursalFiscalID]);
GO
ALTER TABLE [dbo].[RH_Cat_Areas] ADD CONSTRAINT [FK_RH_Cat_Areas_Departamento]
    FOREIGN KEY ([DepartamentoID]) REFERENCES [dbo].[RH_Cat_Departamentos]([DepartamentoID]);
GO
ALTER TABLE [dbo].[RH_Cat_ConceptosNomina] ADD CONSTRAINT [FK_RH_Cat_ConceptosNomina_TipoConcepto]
    FOREIGN KEY ([TipoConceptoNominaID]) REFERENCES [dbo].[RH_Cat_TiposConceptoNomina]([TipoConceptoNominaID]);
GO
ALTER TABLE [dbo].[RH_Cat_Puestos] ADD CONSTRAINT [FK_RH_Cat_Puestos_Area]
    FOREIGN KEY ([AreaID]) REFERENCES [dbo].[RH_Cat_Areas]([AreaID]);
GO
ALTER TABLE [dbo].[RH_Cat_Puestos] ADD CONSTRAINT [FK_RH_Cat_Puestos_Departamento]
    FOREIGN KEY ([DepartamentoID]) REFERENCES [dbo].[RH_Cat_Departamentos]([DepartamentoID]);
GO
ALTER TABLE [dbo].[RH_Cat_SucursalesFiscal] ADD CONSTRAINT [FK_RH_Cat_SucursalesFiscal_Sucursal]
    FOREIGN KEY ([SucursalID]) REFERENCES [dbo].[RH_Cat_Sucursales]([SucursalID]);
GO
ALTER TABLE [dbo].[RH_Colaboradores_Beneficios] ADD CONSTRAINT [FK_RH_Colaboradores_Beneficios_Beneficio]
    FOREIGN KEY ([BeneficioID]) REFERENCES [dbo].[RH_Cat_Beneficios]([BeneficioID]);
GO
ALTER TABLE [dbo].[RH_Colaboradores_Beneficios] ADD CONSTRAINT [FK_RH_Colaboradores_Beneficios_Colaborador]
    FOREIGN KEY ([ColaboradorID]) REFERENCES [dbo].[RH_Colaboradores_Expediente]([ColaboradorID]);
GO
ALTER TABLE [dbo].[RH_Colaboradores_ContactosEmergencia] ADD CONSTRAINT [FK_RH_Colaboradores_ContactosEmergencia_Colaborador]
    FOREIGN KEY ([ColaboradorID]) REFERENCES [dbo].[RH_Colaboradores_Expediente]([ColaboradorID]);
GO
ALTER TABLE [dbo].[RH_Colaboradores_Dependientes] ADD CONSTRAINT [FK_RH_Colaboradores_Dependientes_Colaborador]
    FOREIGN KEY ([ColaboradorID]) REFERENCES [dbo].[RH_Colaboradores_Expediente]([ColaboradorID]);
GO
ALTER TABLE [dbo].[RH_Colaboradores_Documentos] ADD CONSTRAINT [FK_RH_Colaboradores_Documentos_Colaborador]
    FOREIGN KEY ([ColaboradorID]) REFERENCES [dbo].[RH_Colaboradores_Expediente]([ColaboradorID]);
GO
ALTER TABLE [dbo].[RH_Colaboradores_Documentos] ADD CONSTRAINT [FK_RH_Colaboradores_Documentos_ValidadoPor]
    FOREIGN KEY ([ValidadoPor]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[RH_Colaboradores_Domicilios] ADD CONSTRAINT [FK_RH_Colaboradores_Domicilios_Colaborador]
    FOREIGN KEY ([ColaboradorID]) REFERENCES [dbo].[RH_Colaboradores_Expediente]([ColaboradorID]);
GO
ALTER TABLE [dbo].[RH_Colaboradores_Expediente] ADD CONSTRAINT [FK__RH_Colabo__Puest__605D434C]
    FOREIGN KEY ([PuestoID]) REFERENCES [dbo].[RH_Cat_Puestos]([PuestoID]);
GO
ALTER TABLE [dbo].[RH_Colaboradores_Expediente] ADD CONSTRAINT [FK__RH_Colabo__Sucur__5F691F13]
    FOREIGN KEY ([SucursalID]) REFERENCES [dbo].[RH_Cat_Sucursales]([SucursalID]);
GO
ALTER TABLE [dbo].[RH_Colaboradores_Expediente] ADD CONSTRAINT [FK_RH_Colaboradores_Expediente_Banco]
    FOREIGN KEY ([BancoID]) REFERENCES [dbo].[Proveedor_Bancos]([BancoID]);
GO
ALTER TABLE [dbo].[RH_Colaboradores_Expediente] ADD CONSTRAINT [FK_RH_Colaboradores_Expediente_MotivoBaja]
    FOREIGN KEY ([MotivoBajaID]) REFERENCES [dbo].[RH_Cat_MotivosBaja]([MotivoBajaID]);
GO
ALTER TABLE [dbo].[RH_Colaboradores_Expediente] ADD CONSTRAINT [FK_RH_Colaboradores_Expediente_SucursalFiscal]
    FOREIGN KEY ([SucursalFiscalID]) REFERENCES [dbo].[RH_Cat_SucursalesFiscal]([SucursalFiscalID]);
GO
ALTER TABLE [dbo].[RH_Colaboradores_Expediente] ADD CONSTRAINT [FK_RH_Colaboradores_Expediente_Usuario]
    FOREIGN KEY ([UsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[RH_Contratos] ADD CONSTRAINT [FK_RH_Contratos_Colaborador]
    FOREIGN KEY ([ColaboradorID]) REFERENCES [dbo].[RH_Colaboradores_Expediente]([ColaboradorID]);
GO
ALTER TABLE [dbo].[RH_Contratos] ADD CONSTRAINT [FK_RH_Contratos_CreadoPor]
    FOREIGN KEY ([CreadoPor]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[RH_Contratos] ADD CONSTRAINT [FK_RH_Contratos_GrupoNomina]
    FOREIGN KEY ([GrupoNominaID]) REFERENCES [dbo].[RH_GruposNomina]([GrupoNominaID]);
GO
ALTER TABLE [dbo].[RH_Contratos] ADD CONSTRAINT [FK_RH_Contratos_Jornada]
    FOREIGN KEY ([JornadaID]) REFERENCES [dbo].[RH_Cat_Jornadas]([JornadaID]);
GO
ALTER TABLE [dbo].[RH_Contratos] ADD CONSTRAINT [FK_RH_Contratos_Puesto]
    FOREIGN KEY ([PuestoID]) REFERENCES [dbo].[RH_Cat_Puestos]([PuestoID]);
GO
ALTER TABLE [dbo].[RH_Contratos] ADD CONSTRAINT [FK_RH_Contratos_RegimenContratacion]
    FOREIGN KEY ([RegimenContratacionID]) REFERENCES [dbo].[RH_Cat_RegimenContratacion]([RegimenContratacionID]);
GO
ALTER TABLE [dbo].[RH_Contratos] ADD CONSTRAINT [FK_RH_Contratos_Sucursal]
    FOREIGN KEY ([SucursalID]) REFERENCES [dbo].[RH_Cat_Sucursales]([SucursalID]);
GO
ALTER TABLE [dbo].[RH_Contratos] ADD CONSTRAINT [FK_RH_Contratos_SucursalFiscal]
    FOREIGN KEY ([SucursalFiscalID]) REFERENCES [dbo].[RH_Cat_SucursalesFiscal]([SucursalFiscalID]);
GO
ALTER TABLE [dbo].[RH_Contratos] ADD CONSTRAINT [FK_RH_Contratos_TipoContrato]
    FOREIGN KEY ([TipoContratoID]) REFERENCES [dbo].[RH_Cat_TiposContrato]([TipoContratoID]);
GO
ALTER TABLE [dbo].[RH_Contratos] ADD CONSTRAINT [FK_RH_Contratos_Turno]
    FOREIGN KEY ([TurnoID]) REFERENCES [dbo].[RH_Cat_Turnos]([TurnoID]);
GO
ALTER TABLE [dbo].[RH_Finiquitos] ADD CONSTRAINT [FK_RH_Finiquitos_AutorizadoPor]
    FOREIGN KEY ([AutorizadoPor]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[RH_Finiquitos] ADD CONSTRAINT [FK_RH_Finiquitos_Colaborador]
    FOREIGN KEY ([ColaboradorID]) REFERENCES [dbo].[RH_Colaboradores_Expediente]([ColaboradorID]);
GO
ALTER TABLE [dbo].[RH_Finiquitos] ADD CONSTRAINT [FK_RH_Finiquitos_Contrato]
    FOREIGN KEY ([ContratoID]) REFERENCES [dbo].[RH_Contratos]([ContratoID]);
GO
ALTER TABLE [dbo].[RH_Finiquitos] ADD CONSTRAINT [FK_RH_Finiquitos_MotivoBaja]
    FOREIGN KEY ([MotivoBajaID]) REFERENCES [dbo].[RH_Cat_MotivosBaja]([MotivoBajaID]);
GO
ALTER TABLE [dbo].[RH_Finiquitos] ADD CONSTRAINT [FK_RH_Finiquitos_Nomina]
    FOREIGN KEY ([NominaID]) REFERENCES [dbo].[RH_Nomina]([NominaID]);
GO
ALTER TABLE [dbo].[RH_Finiquitos] ADD CONSTRAINT [FK_RH_Finiquitos_PeriodoNomina]
    FOREIGN KEY ([PeriodoNominaID]) REFERENCES [dbo].[RH_Periodos_Nomina]([PeriodoNominaID]);
GO
ALTER TABLE [dbo].[RH_Finiquitos_Detalle] ADD CONSTRAINT [FK_RH_Finiquitos_Detalle_ConceptoNomina]
    FOREIGN KEY ([ConceptoNominaID]) REFERENCES [dbo].[RH_Cat_ConceptosNomina]([ConceptoNominaID]);
GO
ALTER TABLE [dbo].[RH_Finiquitos_Detalle] ADD CONSTRAINT [FK_RH_Finiquitos_Detalle_Finiquito]
    FOREIGN KEY ([FiniquitoID]) REFERENCES [dbo].[RH_Finiquitos]([FiniquitoID]);
GO
ALTER TABLE [dbo].[RH_Flujo_Nomina_Sucursal] ADD CONSTRAINT [FK__RH_Flujo___Sucur__737017C0]
    FOREIGN KEY ([SucursalID]) REFERENCES [dbo].[RH_Cat_Sucursales]([SucursalID]);
GO
ALTER TABLE [dbo].[RH_Flujo_Nomina_Sucursal] ADD CONSTRAINT [FK_RH_Flujo_Nomina_Sucursal_PeriodoNomina]
    FOREIGN KEY ([PeriodoNominaID]) REFERENCES [dbo].[RH_Periodos_Nomina]([PeriodoNominaID]);
GO
ALTER TABLE [dbo].[RH_GruposNomina] ADD CONSTRAINT [FK_RH_GruposNomina_SucursalFiscal]
    FOREIGN KEY ([SucursalFiscalID]) REFERENCES [dbo].[RH_Cat_SucursalesFiscal]([SucursalFiscalID]);
GO
ALTER TABLE [dbo].[RH_GruposNomina] ADD CONSTRAINT [FK_RH_GruposNomina_TipoPeriodo]
    FOREIGN KEY ([TipoPeriodoNominaID]) REFERENCES [dbo].[RH_Cat_TiposPeriodoNomina]([TipoPeriodoNominaID]);
GO
ALTER TABLE [dbo].[RH_Historial_Puestos] ADD CONSTRAINT [FK_RH_Historial_Puestos_AutorizadoPor]
    FOREIGN KEY ([AutorizadoPor]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[RH_Historial_Puestos] ADD CONSTRAINT [FK_RH_Historial_Puestos_Colaborador]
    FOREIGN KEY ([ColaboradorID]) REFERENCES [dbo].[RH_Colaboradores_Expediente]([ColaboradorID]);
GO
ALTER TABLE [dbo].[RH_Historial_Puestos] ADD CONSTRAINT [FK_RH_Historial_Puestos_Contrato]
    FOREIGN KEY ([ContratoID]) REFERENCES [dbo].[RH_Contratos]([ContratoID]);
GO
ALTER TABLE [dbo].[RH_Historial_Puestos] ADD CONSTRAINT [FK_RH_Historial_Puestos_PuestoAnterior]
    FOREIGN KEY ([PuestoIDAnterior]) REFERENCES [dbo].[RH_Cat_Puestos]([PuestoID]);
GO
ALTER TABLE [dbo].[RH_Historial_Puestos] ADD CONSTRAINT [FK_RH_Historial_Puestos_PuestoNuevo]
    FOREIGN KEY ([PuestoIDNuevo]) REFERENCES [dbo].[RH_Cat_Puestos]([PuestoID]);
GO
ALTER TABLE [dbo].[RH_Historial_Puestos] ADD CONSTRAINT [FK_RH_Historial_Puestos_SucursalAnterior]
    FOREIGN KEY ([SucursalIDAnterior]) REFERENCES [dbo].[RH_Cat_Sucursales]([SucursalID]);
GO
ALTER TABLE [dbo].[RH_Historial_Puestos] ADD CONSTRAINT [FK_RH_Historial_Puestos_SucursalNueva]
    FOREIGN KEY ([SucursalIDNueva]) REFERENCES [dbo].[RH_Cat_Sucursales]([SucursalID]);
GO
ALTER TABLE [dbo].[RH_Historial_Salarios] ADD CONSTRAINT [FK_RH_Historial_Salarios_AutorizadoPor]
    FOREIGN KEY ([AutorizadoPor]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[RH_Historial_Salarios] ADD CONSTRAINT [FK_RH_Historial_Salarios_Colaborador]
    FOREIGN KEY ([ColaboradorID]) REFERENCES [dbo].[RH_Colaboradores_Expediente]([ColaboradorID]);
GO
ALTER TABLE [dbo].[RH_Historial_Salarios] ADD CONSTRAINT [FK_RH_Historial_Salarios_Contrato]
    FOREIGN KEY ([ContratoID]) REFERENCES [dbo].[RH_Contratos]([ContratoID]);
GO
ALTER TABLE [dbo].[RH_IMSS_Movimientos] ADD CONSTRAINT [FK_RH_IMSS_Movimientos_CapturadoPor]
    FOREIGN KEY ([CapturadoPor]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[RH_IMSS_Movimientos] ADD CONSTRAINT [FK_RH_IMSS_Movimientos_Colaborador]
    FOREIGN KEY ([ColaboradorID]) REFERENCES [dbo].[RH_Colaboradores_Expediente]([ColaboradorID]);
GO
ALTER TABLE [dbo].[RH_IMSS_Movimientos] ADD CONSTRAINT [FK_RH_IMSS_Movimientos_Contrato]
    FOREIGN KEY ([ContratoID]) REFERENCES [dbo].[RH_Contratos]([ContratoID]);
GO
ALTER TABLE [dbo].[RH_Incidencias_Nomina] ADD CONSTRAINT [FK__RH_Incide__Colab__6DB73E6A]
    FOREIGN KEY ([ColaboradorID]) REFERENCES [dbo].[RH_Colaboradores_Expediente]([ColaboradorID]);
GO
ALTER TABLE [dbo].[RH_Incidencias_Nomina] ADD CONSTRAINT [FK_RH_Incidencias_Nomina_AutorizadoPor]
    FOREIGN KEY ([AutorizadoPor]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[RH_Incidencias_Nomina] ADD CONSTRAINT [FK_RH_Incidencias_Nomina_ConceptoNomina]
    FOREIGN KEY ([ConceptoNominaID]) REFERENCES [dbo].[RH_Cat_ConceptosNomina]([ConceptoNominaID]);
GO
ALTER TABLE [dbo].[RH_Incidencias_Nomina] ADD CONSTRAINT [FK_RH_Incidencias_Nomina_PeriodoNomina]
    FOREIGN KEY ([PeriodoNominaID]) REFERENCES [dbo].[RH_Periodos_Nomina]([PeriodoNominaID]);
GO
ALTER TABLE [dbo].[RH_Nomina] ADD CONSTRAINT [FK_RH_Nomina_Colaborador]
    FOREIGN KEY ([ColaboradorID]) REFERENCES [dbo].[RH_Colaboradores_Expediente]([ColaboradorID]);
GO
ALTER TABLE [dbo].[RH_Nomina] ADD CONSTRAINT [FK_RH_Nomina_Contrato]
    FOREIGN KEY ([ContratoID]) REFERENCES [dbo].[RH_Contratos]([ContratoID]);
GO
ALTER TABLE [dbo].[RH_Nomina] ADD CONSTRAINT [FK_RH_Nomina_PeriodoNomina]
    FOREIGN KEY ([PeriodoNominaID]) REFERENCES [dbo].[RH_Periodos_Nomina]([PeriodoNominaID]);
GO
ALTER TABLE [dbo].[RH_Nomina] ADD CONSTRAINT [FK_RH_Nomina_Sucursal]
    FOREIGN KEY ([SucursalID]) REFERENCES [dbo].[RH_Cat_Sucursales]([SucursalID]);
GO
ALTER TABLE [dbo].[RH_Nomina] ADD CONSTRAINT [FK_RH_Nomina_SucursalFiscal]
    FOREIGN KEY ([SucursalFiscalID]) REFERENCES [dbo].[RH_Cat_SucursalesFiscal]([SucursalFiscalID]);
GO
ALTER TABLE [dbo].[RH_Nomina_Detalle] ADD CONSTRAINT [FK_RH_Nomina_Detalle_ConceptoNomina]
    FOREIGN KEY ([ConceptoNominaID]) REFERENCES [dbo].[RH_Cat_ConceptosNomina]([ConceptoNominaID]);
GO
ALTER TABLE [dbo].[RH_Nomina_Detalle] ADD CONSTRAINT [FK_RH_Nomina_Detalle_Nomina]
    FOREIGN KEY ([NominaID]) REFERENCES [dbo].[RH_Nomina]([NominaID]);
GO
ALTER TABLE [dbo].[RH_Nomina_Dispersion] ADD CONSTRAINT [FK_RH_Nomina_Dispersion_Banco]
    FOREIGN KEY ([BancoID]) REFERENCES [dbo].[Proveedor_Bancos]([BancoID]);
GO
ALTER TABLE [dbo].[RH_Nomina_Dispersion] ADD CONSTRAINT [FK_RH_Nomina_Dispersion_Colaborador]
    FOREIGN KEY ([ColaboradorID]) REFERENCES [dbo].[RH_Colaboradores_Expediente]([ColaboradorID]);
GO
ALTER TABLE [dbo].[RH_Nomina_Dispersion] ADD CONSTRAINT [FK_RH_Nomina_Dispersion_Nomina]
    FOREIGN KEY ([NominaID]) REFERENCES [dbo].[RH_Nomina]([NominaID]);
GO
ALTER TABLE [dbo].[RH_Nomina_Dispersion] ADD CONSTRAINT [FK_RH_Nomina_Dispersion_PeriodoNomina]
    FOREIGN KEY ([PeriodoNominaID]) REFERENCES [dbo].[RH_Periodos_Nomina]([PeriodoNominaID]);
GO
ALTER TABLE [dbo].[RH_Nomina_Recibos] ADD CONSTRAINT [FK_RH_Nomina_Recibos_Nomina]
    FOREIGN KEY ([NominaID]) REFERENCES [dbo].[RH_Nomina]([NominaID]);
GO
ALTER TABLE [dbo].[RH_Periodos_Nomina] ADD CONSTRAINT [FK_RH_Periodos_Nomina_CerradoPor]
    FOREIGN KEY ([CerradoPor]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[RH_Periodos_Nomina] ADD CONSTRAINT [FK_RH_Periodos_Nomina_Estatus]
    FOREIGN KEY ([EstatusPeriodoNominaID]) REFERENCES [dbo].[RH_Cat_EstatusPeriodoNomina]([EstatusPeriodoNominaID]);
GO
ALTER TABLE [dbo].[RH_Periodos_Nomina] ADD CONSTRAINT [FK_RH_Periodos_Nomina_GrupoNomina]
    FOREIGN KEY ([GrupoNominaID]) REFERENCES [dbo].[RH_GruposNomina]([GrupoNominaID]);
GO
ALTER TABLE [dbo].[RH_Prestamos] ADD CONSTRAINT [FK_RH_Prestamos_AutorizadoPor]
    FOREIGN KEY ([AutorizadoPor]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[RH_Prestamos] ADD CONSTRAINT [FK_RH_Prestamos_Colaborador]
    FOREIGN KEY ([ColaboradorID]) REFERENCES [dbo].[RH_Colaboradores_Expediente]([ColaboradorID]);
GO
ALTER TABLE [dbo].[RH_Prestamos_Detalle] ADD CONSTRAINT [FK_RH_Prestamos_Detalle_Nomina]
    FOREIGN KEY ([NominaID]) REFERENCES [dbo].[RH_Nomina]([NominaID]);
GO
ALTER TABLE [dbo].[RH_Prestamos_Detalle] ADD CONSTRAINT [FK_RH_Prestamos_Detalle_PeriodoNomina]
    FOREIGN KEY ([PeriodoNominaID]) REFERENCES [dbo].[RH_Periodos_Nomina]([PeriodoNominaID]);
GO
ALTER TABLE [dbo].[RH_Prestamos_Detalle] ADD CONSTRAINT [FK_RH_Prestamos_Detalle_Prestamo]
    FOREIGN KEY ([PrestamoID]) REFERENCES [dbo].[RH_Prestamos]([PrestamoID]);
GO
ALTER TABLE [dbo].[RH_Reloj_Checador] ADD CONSTRAINT [FK__RH_Reloj___Colab__68F2894D]
    FOREIGN KEY ([ColaboradorID]) REFERENCES [dbo].[RH_Colaboradores_Expediente]([ColaboradorID]);
GO
ALTER TABLE [dbo].[RH_Vacaciones_Movimientos] ADD CONSTRAINT [FK_RH_Vacaciones_Movimientos_CapturadoPor]
    FOREIGN KEY ([CapturadoPor]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[RH_Vacaciones_Movimientos] ADD CONSTRAINT [FK_RH_Vacaciones_Movimientos_Colaborador]
    FOREIGN KEY ([ColaboradorID]) REFERENCES [dbo].[RH_Colaboradores_Expediente]([ColaboradorID]);
GO
ALTER TABLE [dbo].[RH_Vacaciones_Movimientos] ADD CONSTRAINT [FK_RH_Vacaciones_Movimientos_Saldo]
    FOREIGN KEY ([VacacionSaldoID]) REFERENCES [dbo].[RH_Vacaciones_Saldos]([VacacionSaldoID]);
GO
ALTER TABLE [dbo].[RH_Vacaciones_Saldos] ADD CONSTRAINT [FK_RH_Vacaciones_Saldos_Colaborador]
    FOREIGN KEY ([ColaboradorID]) REFERENCES [dbo].[RH_Colaboradores_Expediente]([ColaboradorID]);
GO
ALTER TABLE [dbo].[Servidores_Conexiones] ADD CONSTRAINT [FK_Servidores_Conexiones_Sistema_Empresas]
    FOREIGN KEY ([EmpresaID]) REFERENCES [dbo].[Sistema_Empresas]([EmpresaID]);
GO
ALTER TABLE [dbo].[Sistema_Capacidades] ADD CONSTRAINT [FK_SistemaCapacidades_SistemaTipos]
    FOREIGN KEY ([SistemaTipoID]) REFERENCES [dbo].[Sistema_Tipos]([SistemaTipoID]);
GO
ALTER TABLE [dbo].[Sistema_EmpresasAlias] ADD CONSTRAINT [FK_EmpresasAlias_Empresa]
    FOREIGN KEY ([EmpresaID]) REFERENCES [dbo].[Sistema_Empresas]([EmpresaID]);
GO
ALTER TABLE [dbo].[Sistema_EmpresasMongoMap] ADD CONSTRAINT [FK_EmpresaID_SQL]
    FOREIGN KEY ([EmpresaID_SQL]) REFERENCES [dbo].[Sistema_Empresas]([EmpresaID]);
GO
ALTER TABLE [dbo].[Sistema_EmpresasServidores] ADD CONSTRAINT [FK_EmpresasServidores_Empresa]
    FOREIGN KEY ([EmpresaID]) REFERENCES [dbo].[Sistema_Empresas]([EmpresaID]);
GO
ALTER TABLE [dbo].[Sistema_EmpresasServidores] ADD CONSTRAINT [FK_EmpresasServidores_Servidor]
    FOREIGN KEY ([ServidorID]) REFERENCES [dbo].[Servidores_Conexiones]([id]);
GO
ALTER TABLE [dbo].[Sistema_ModulosMenus] ADD CONSTRAINT [FK_Menu_Modulo]
    FOREIGN KEY ([ModuloID]) REFERENCES [dbo].[Sistema_Modulos]([ModuloID]);
GO
ALTER TABLE [dbo].[Sistema_ModulosMenus] ADD CONSTRAINT [FK_Menu_Padre]
    FOREIGN KEY ([MenuPadreID]) REFERENCES [dbo].[Sistema_ModulosMenus]([MenuID]);
GO
ALTER TABLE [dbo].[Sistema_ModulosPermisos] ADD CONSTRAINT [FK_Permiso_Modulo]
    FOREIGN KEY ([ModuloID]) REFERENCES [dbo].[Sistema_Modulos]([ModuloID]);
GO
ALTER TABLE [dbo].[Sistema_ModulosVisibilidad] ADD CONSTRAINT [FK_SistemaModulos_SistemaTipos]
    FOREIGN KEY ([SistemaTipoID]) REFERENCES [dbo].[Sistema_Tipos]([SistemaTipoID]);
GO
ALTER TABLE [dbo].[Sistema_ServidorSucursalesConfig] ADD CONSTRAINT [FK__Sistema_S__Sucur__2B754518]
    FOREIGN KEY ([SucursalID]) REFERENCES [dbo].[Sistema_Sucursales]([SucursalID]);
GO
ALTER TABLE [dbo].[Sistema_Sucursales] ADD CONSTRAINT [FK__Sistema_S__Empre__21EBDADE]
    FOREIGN KEY ([EmpresaID]) REFERENCES [dbo].[Sistema_Empresas]([EmpresaID]);
GO
ALTER TABLE [dbo].[Sistema_SucursalServidorMapeo] ADD CONSTRAINT [FK__Sistema_S__Sucur__26B08FFB]
    FOREIGN KEY ([SucursalID]) REFERENCES [dbo].[Sistema_Sucursales]([SucursalID]);
GO
ALTER TABLE [dbo].[Sistema_TiposVariantes] ADD CONSTRAINT [FK_SistemaTiposVariantes_SistemaTipos]
    FOREIGN KEY ([SistemaTipoID]) REFERENCES [dbo].[Sistema_Tipos]([SistemaTipoID]);
GO
ALTER TABLE [dbo].[Sistema_UnidadesNegocioPerfilDigital] ADD CONSTRAINT [FK_PerfilDigital_Empresa]
    FOREIGN KEY ([EmpresaID]) REFERENCES [dbo].[Sistema_Empresas]([EmpresaID]);
GO
ALTER TABLE [dbo].[Sync_Impuestos_Origen] ADD CONSTRAINT [FK_SyncImpuestos_Canonico]
    FOREIGN KEY ([ImpuestoCanonicoID]) REFERENCES [dbo].[Comercial_ImpuestosCatalogo]([ImpuestoID]);
GO
ALTER TABLE [dbo].[Sync_Impuestos_Origen] ADD CONSTRAINT [FK_SyncImpuestos_Servidor]
    FOREIGN KEY ([ServerID]) REFERENCES [dbo].[Servidores_Conexiones]([id]);
GO
ALTER TABLE [dbo].[Usuario_AlmacenesAsignacion] ADD CONSTRAINT [FK_UsuarioAlmacenes_Servidor]
    FOREIGN KEY ([ServidorID]) REFERENCES [dbo].[Servidores_Conexiones]([id]);
GO
ALTER TABLE [dbo].[Usuario_AlmacenesAsignacion] ADD CONSTRAINT [FK_UsuarioAlmacenes_Usuario]
    FOREIGN KEY ([UsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Usuario_Autorizaciones] ADD CONSTRAINT [FK_Usuario_Autorizaciones_Proveedor_Monedas]
    FOREIGN KEY ([MonedaID]) REFERENCES [dbo].[Proveedor_Monedas]([MonedaID]);
GO
ALTER TABLE [dbo].[Usuario_Autorizaciones] ADD CONSTRAINT [FK_Usuario_Autorizaciones_Usuario_Acciones]
    FOREIGN KEY ([AccionID]) REFERENCES [dbo].[Usuario_Acciones]([AccionID]);
GO
ALTER TABLE [dbo].[Usuario_Autorizaciones] ADD CONSTRAINT [FK_Usuario_Autorizaciones_Usuario_Catalogo_ResolucionFinal]
    FOREIGN KEY ([UsuarioResolucionFinalID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Usuario_Autorizaciones] ADD CONSTRAINT [FK_Usuario_Autorizaciones_Usuario_Catalogo_Solicitante]
    FOREIGN KEY ([UsuarioSolicitanteID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Usuario_Autorizaciones] ADD CONSTRAINT [FK_Usuario_Autorizaciones_Usuario_Modulos]
    FOREIGN KEY ([ModuloID]) REFERENCES [dbo].[Usuario_Modulos]([ModuloID]);
GO
ALTER TABLE [dbo].[Usuario_Autorizaciones] ADD CONSTRAINT [FK_Usuario_Autorizaciones_Usuario_TiposAutorizacion]
    FOREIGN KEY ([TipoAutorizacionID]) REFERENCES [dbo].[Usuario_TiposAutorizacion]([TipoAutorizacionID]);
GO
ALTER TABLE [dbo].[Usuario_AutorizacionesDetalle] ADD CONSTRAINT [FK_Usuario_AutorizacionesDetalle_Usuario_Autorizaciones]
    FOREIGN KEY ([AutorizacionID]) REFERENCES [dbo].[Usuario_Autorizaciones]([AutorizacionID]);
GO
ALTER TABLE [dbo].[Usuario_AutorizacionesDetalle] ADD CONSTRAINT [FK_Usuario_AutorizacionesDetalle_Usuario_Catalogo]
    FOREIGN KEY ([UsuarioAutorizadorID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Usuario_AutorizacionesDetalle] ADD CONSTRAINT [FK_Usuario_AutorizacionesDetalle_Usuario_Roles]
    FOREIGN KEY ([RolID]) REFERENCES [dbo].[Usuario_Roles]([RolID]);
GO
ALTER TABLE [dbo].[Usuario_EmpresasAsignacion] ADD CONSTRAINT [FK_UsuarioEmpresas_Empresa]
    FOREIGN KEY ([EmpresaID]) REFERENCES [dbo].[Sistema_Empresas]([EmpresaID]);
GO
ALTER TABLE [dbo].[Usuario_EmpresasAsignacion] ADD CONSTRAINT [FK_UsuarioEmpresas_Usuario]
    FOREIGN KEY ([UsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Usuario_LogAccesos] ADD CONSTRAINT [FK_Usuario_LogAccesos_Usuario_Catalogo]
    FOREIGN KEY ([UsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Usuario_LogAccesos] ADD CONSTRAINT [FK_Usuario_LogAccesos_Usuario_Sesiones]
    FOREIGN KEY ([SesionID]) REFERENCES [dbo].[Usuario_Sesiones]([SesionID]);
GO
ALTER TABLE [dbo].[Usuario_LogActividades] ADD CONSTRAINT [FK_Usuario_LogActividades_Usuario_Acciones]
    FOREIGN KEY ([AccionID]) REFERENCES [dbo].[Usuario_Acciones]([AccionID]);
GO
ALTER TABLE [dbo].[Usuario_LogActividades] ADD CONSTRAINT [FK_Usuario_LogActividades_Usuario_Catalogo]
    FOREIGN KEY ([UsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Usuario_LogActividades] ADD CONSTRAINT [FK_Usuario_LogActividades_Usuario_Modulos]
    FOREIGN KEY ([ModuloID]) REFERENCES [dbo].[Usuario_Modulos]([ModuloID]);
GO
ALTER TABLE [dbo].[Usuario_LogActividades] ADD CONSTRAINT [FK_Usuario_LogActividades_Usuario_Sesiones]
    FOREIGN KEY ([SesionID]) REFERENCES [dbo].[Usuario_Sesiones]([SesionID]);
GO
ALTER TABLE [dbo].[Usuario_MatrizAutorizacion] ADD CONSTRAINT [FK_Usuario_MatrizAutorizacion_Usuario_Catalogo]
    FOREIGN KEY ([UsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Usuario_MatrizAutorizacion] ADD CONSTRAINT [FK_Usuario_MatrizAutorizacion_Usuario_Roles]
    FOREIGN KEY ([RolID]) REFERENCES [dbo].[Usuario_Roles]([RolID]);
GO
ALTER TABLE [dbo].[Usuario_MatrizAutorizacion] ADD CONSTRAINT [FK_Usuario_MatrizAutorizacion_Usuario_TiposAutorizacion]
    FOREIGN KEY ([TipoAutorizacionID]) REFERENCES [dbo].[Usuario_TiposAutorizacion]([TipoAutorizacionID]);
GO
ALTER TABLE [dbo].[Usuario_Modulos] ADD CONSTRAINT [FK_Usuario_Modulos_Usuario_Modulos_Padre]
    FOREIGN KEY ([ModuloPadreID]) REFERENCES [dbo].[Usuario_Modulos]([ModuloID]);
GO
ALTER TABLE [dbo].[Usuario_PermisosRolModulo] ADD CONSTRAINT [FK_Usuario_PermisosRolModulo_Usuario_Acciones]
    FOREIGN KEY ([AccionID]) REFERENCES [dbo].[Usuario_Acciones]([AccionID]);
GO
ALTER TABLE [dbo].[Usuario_PermisosRolModulo] ADD CONSTRAINT [FK_Usuario_PermisosRolModulo_Usuario_Modulos]
    FOREIGN KEY ([ModuloID]) REFERENCES [dbo].[Usuario_Modulos]([ModuloID]);
GO
ALTER TABLE [dbo].[Usuario_PermisosRolModulo] ADD CONSTRAINT [FK_Usuario_PermisosRolModulo_Usuario_Roles]
    FOREIGN KEY ([RolID]) REFERENCES [dbo].[Usuario_Roles]([RolID]);
GO
ALTER TABLE [dbo].[Usuario_PortalConfiguracion] ADD CONSTRAINT [FK_Usuario_PortalConfiguracion_Usuario_Catalogo]
    FOREIGN KEY ([UsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Usuario_RolesAsignacion] ADD CONSTRAINT [FK_Usuario_RolesAsignacion_Usuario_Catalogo]
    FOREIGN KEY ([UsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Usuario_RolesAsignacion] ADD CONSTRAINT [FK_Usuario_RolesAsignacion_Usuario_Roles]
    FOREIGN KEY ([RolID]) REFERENCES [dbo].[Usuario_Roles]([RolID]);
GO
ALTER TABLE [dbo].[Usuario_ServidoresAsignacion] ADD CONSTRAINT [FK_UsuarioServidores_Servidor]
    FOREIGN KEY ([ServidorID]) REFERENCES [dbo].[Servidores_Conexiones]([id]);
GO
ALTER TABLE [dbo].[Usuario_ServidoresAsignacion] ADD CONSTRAINT [FK_UsuarioServidores_Usuario]
    FOREIGN KEY ([UsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Usuario_Sesiones] ADD CONSTRAINT [FK_Usuario_Sesiones_Usuario_Catalogo]
    FOREIGN KEY ([UsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Usuario_SucursalesAsignacion] ADD CONSTRAINT [FK_UsuarioSucursales_Servidor]
    FOREIGN KEY ([ServidorID]) REFERENCES [dbo].[Servidores_Conexiones]([id]);
GO
ALTER TABLE [dbo].[Usuario_SucursalesAsignacion] ADD CONSTRAINT [FK_UsuarioSucursales_Usuario]
    FOREIGN KEY ([UsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Usuario_TiposAutorizacion] ADD CONSTRAINT [FK_Usuario_TiposAutorizacion_Usuario_Acciones]
    FOREIGN KEY ([AccionID]) REFERENCES [dbo].[Usuario_Acciones]([AccionID]);
GO
ALTER TABLE [dbo].[Usuario_TiposAutorizacion] ADD CONSTRAINT [FK_Usuario_TiposAutorizacion_Usuario_Modulos]
    FOREIGN KEY ([ModuloID]) REFERENCES [dbo].[Usuario_Modulos]([ModuloID]);
GO
ALTER TABLE [dbo].[Usuario_TokensRecuperacion] ADD CONSTRAINT [FK_TokensRecuperacion_Usuario]
    FOREIGN KEY ([UsuarioID]) REFERENCES [dbo].[Usuario_Catalogo]([UsuarioID]);
GO
ALTER TABLE [dbo].[Venta_Cotizaciones] ADD CONSTRAINT [FK_Venta_Cotizaciones_Cliente_Catalogo]
    FOREIGN KEY ([ClienteID]) REFERENCES [dbo].[Cliente_Catalogo]([ClienteID]);
GO
ALTER TABLE [dbo].[Venta_Cotizaciones] ADD CONSTRAINT [FK_Venta_Cotizaciones_Cliente_Direcciones]
    FOREIGN KEY ([ClienteDireccionID]) REFERENCES [dbo].[Cliente_Direcciones]([DireccionClienteID]);
GO
ALTER TABLE [dbo].[Venta_Cotizaciones] ADD CONSTRAINT [FK_Venta_Cotizaciones_Proveedor_Monedas]
    FOREIGN KEY ([MonedaID]) REFERENCES [dbo].[Proveedor_Monedas]([MonedaID]);
GO
ALTER TABLE [dbo].[Venta_Cotizaciones] ADD CONSTRAINT [FK_Venta_Cotizaciones_Venta_CondicionesPago]
    FOREIGN KEY ([CondicionPagoID]) REFERENCES [dbo].[Venta_CondicionesPago]([CondicionPagoID]);
GO
ALTER TABLE [dbo].[Venta_Cotizaciones] ADD CONSTRAINT [FK_Venta_Cotizaciones_Venta_CotizacionesEstatus]
    FOREIGN KEY ([EstatusCotizacionID]) REFERENCES [dbo].[Venta_CotizacionesEstatus]([EstatusCotizacionID]);
GO
ALTER TABLE [dbo].[Venta_Cotizaciones] ADD CONSTRAINT [FK_Venta_Cotizaciones_Venta_Encabezado]
    FOREIGN KEY ([VentaID]) REFERENCES [dbo].[Venta_Encabezado]([VentaID]);
GO
ALTER TABLE [dbo].[Venta_Cotizaciones] ADD CONSTRAINT [FK_Venta_Cotizaciones_Venta_ListasPrecios]
    FOREIGN KEY ([ListaPrecioID]) REFERENCES [dbo].[Venta_ListasPrecios]([ListaPrecioID]);
GO
ALTER TABLE [dbo].[Venta_Cotizaciones] ADD CONSTRAINT [FK_Venta_Cotizaciones_Venta_Pedidos]
    FOREIGN KEY ([PedidoID]) REFERENCES [dbo].[Venta_Pedidos]([PedidoID]);
GO
ALTER TABLE [dbo].[Venta_CotizacionesDetalle] ADD CONSTRAINT [FK_Venta_CotizacionesDetalle_Producto_Catalogo]
    FOREIGN KEY ([ProductoID]) REFERENCES [dbo].[Producto_Catalogo]([ProductoID]);
GO
ALTER TABLE [dbo].[Venta_CotizacionesDetalle] ADD CONSTRAINT [FK_Venta_CotizacionesDetalle_Producto_Presentaciones]
    FOREIGN KEY ([PresentacionProductoID]) REFERENCES [dbo].[Producto_Presentaciones]([PresentacionProductoID]);
GO
ALTER TABLE [dbo].[Venta_CotizacionesDetalle] ADD CONSTRAINT [FK_Venta_CotizacionesDetalle_Venta_Cotizaciones]
    FOREIGN KEY ([CotizacionID]) REFERENCES [dbo].[Venta_Cotizaciones]([CotizacionID]);
GO
ALTER TABLE [dbo].[Venta_Detalle] ADD CONSTRAINT [FK_Venta_Detalle_Producto_Catalogo]
    FOREIGN KEY ([ProductoID]) REFERENCES [dbo].[Producto_Catalogo]([ProductoID]);
GO
ALTER TABLE [dbo].[Venta_Detalle] ADD CONSTRAINT [FK_Venta_Detalle_Producto_Presentaciones]
    FOREIGN KEY ([PresentacionProductoID]) REFERENCES [dbo].[Producto_Presentaciones]([PresentacionProductoID]);
GO
ALTER TABLE [dbo].[Venta_Detalle] ADD CONSTRAINT [FK_Venta_Detalle_Venta_Encabezado]
    FOREIGN KEY ([VentaID]) REFERENCES [dbo].[Venta_Encabezado]([VentaID]);
GO
ALTER TABLE [dbo].[Venta_Encabezado] ADD CONSTRAINT [FK_Venta_Encabezado_Cliente_Catalogo]
    FOREIGN KEY ([ClienteID]) REFERENCES [dbo].[Cliente_Catalogo]([ClienteID]);
GO
ALTER TABLE [dbo].[Venta_Encabezado] ADD CONSTRAINT [FK_Venta_Encabezado_Cliente_Direcciones]
    FOREIGN KEY ([ClienteDireccionID]) REFERENCES [dbo].[Cliente_Direcciones]([DireccionClienteID]);
GO
ALTER TABLE [dbo].[Venta_Encabezado] ADD CONSTRAINT [FK_Venta_Encabezado_Proveedor_Monedas]
    FOREIGN KEY ([MonedaID]) REFERENCES [dbo].[Proveedor_Monedas]([MonedaID]);
GO
ALTER TABLE [dbo].[Venta_Encabezado] ADD CONSTRAINT [FK_Venta_Encabezado_Venta_CondicionesPago]
    FOREIGN KEY ([CondicionPagoID]) REFERENCES [dbo].[Venta_CondicionesPago]([CondicionPagoID]);
GO
ALTER TABLE [dbo].[Venta_Encabezado] ADD CONSTRAINT [FK_Venta_Encabezado_Venta_Estatus]
    FOREIGN KEY ([EstatusVentaID]) REFERENCES [dbo].[Venta_Estatus]([EstatusVentaID]);
GO
ALTER TABLE [dbo].[Venta_Encabezado] ADD CONSTRAINT [FK_Venta_Encabezado_Venta_ListasPrecios]
    FOREIGN KEY ([ListaPrecioID]) REFERENCES [dbo].[Venta_ListasPrecios]([ListaPrecioID]);
GO
ALTER TABLE [dbo].[Venta_ListasPrecios] ADD CONSTRAINT [FK_Venta_ListasPrecios_Proveedor_Monedas]
    FOREIGN KEY ([MonedaID]) REFERENCES [dbo].[Proveedor_Monedas]([MonedaID]);
GO
ALTER TABLE [dbo].[Venta_ListasPreciosDetalle] ADD CONSTRAINT [FK_Venta_ListasPreciosDetalle_Producto_Catalogo]
    FOREIGN KEY ([ProductoID]) REFERENCES [dbo].[Producto_Catalogo]([ProductoID]);
GO
ALTER TABLE [dbo].[Venta_ListasPreciosDetalle] ADD CONSTRAINT [FK_Venta_ListasPreciosDetalle_Producto_Presentaciones]
    FOREIGN KEY ([PresentacionProductoID]) REFERENCES [dbo].[Producto_Presentaciones]([PresentacionProductoID]);
GO
ALTER TABLE [dbo].[Venta_ListasPreciosDetalle] ADD CONSTRAINT [FK_Venta_ListasPreciosDetalle_Venta_ListasPrecios]
    FOREIGN KEY ([ListaPrecioID]) REFERENCES [dbo].[Venta_ListasPrecios]([ListaPrecioID]);
GO
ALTER TABLE [dbo].[Venta_Pagos] ADD CONSTRAINT [FK_Venta_Pagos_Proveedor_Monedas]
    FOREIGN KEY ([MonedaID]) REFERENCES [dbo].[Proveedor_Monedas]([MonedaID]);
GO
ALTER TABLE [dbo].[Venta_Pagos] ADD CONSTRAINT [FK_Venta_Pagos_Venta_Encabezado]
    FOREIGN KEY ([VentaID]) REFERENCES [dbo].[Venta_Encabezado]([VentaID]);
GO
ALTER TABLE [dbo].[Venta_Pagos] ADD CONSTRAINT [FK_Venta_Pagos_Venta_FormaPago]
    FOREIGN KEY ([FormaPagoID]) REFERENCES [dbo].[Venta_FormaPago]([FormaPagoID]);
GO
ALTER TABLE [dbo].[Venta_Pedidos] ADD CONSTRAINT [FK_Venta_Pedidos_Cliente_Catalogo]
    FOREIGN KEY ([ClienteID]) REFERENCES [dbo].[Cliente_Catalogo]([ClienteID]);
GO
ALTER TABLE [dbo].[Venta_Pedidos] ADD CONSTRAINT [FK_Venta_Pedidos_Cliente_Direcciones]
    FOREIGN KEY ([ClienteDireccionID]) REFERENCES [dbo].[Cliente_Direcciones]([DireccionClienteID]);
GO
ALTER TABLE [dbo].[Venta_Pedidos] ADD CONSTRAINT [FK_Venta_Pedidos_Proveedor_Monedas]
    FOREIGN KEY ([MonedaID]) REFERENCES [dbo].[Proveedor_Monedas]([MonedaID]);
GO
ALTER TABLE [dbo].[Venta_Pedidos] ADD CONSTRAINT [FK_Venta_Pedidos_Venta_CondicionesPago]
    FOREIGN KEY ([CondicionPagoID]) REFERENCES [dbo].[Venta_CondicionesPago]([CondicionPagoID]);
GO
ALTER TABLE [dbo].[Venta_Pedidos] ADD CONSTRAINT [FK_Venta_Pedidos_Venta_Cotizaciones]
    FOREIGN KEY ([CotizacionID]) REFERENCES [dbo].[Venta_Cotizaciones]([CotizacionID]);
GO
ALTER TABLE [dbo].[Venta_Pedidos] ADD CONSTRAINT [FK_Venta_Pedidos_Venta_Encabezado]
    FOREIGN KEY ([VentaID]) REFERENCES [dbo].[Venta_Encabezado]([VentaID]);
GO
ALTER TABLE [dbo].[Venta_Pedidos] ADD CONSTRAINT [FK_Venta_Pedidos_Venta_ListasPrecios]
    FOREIGN KEY ([ListaPrecioID]) REFERENCES [dbo].[Venta_ListasPrecios]([ListaPrecioID]);
GO
ALTER TABLE [dbo].[Venta_Pedidos] ADD CONSTRAINT [FK_Venta_Pedidos_Venta_PedidosEstatus]
    FOREIGN KEY ([EstatusPedidoID]) REFERENCES [dbo].[Venta_PedidosEstatus]([EstatusPedidoID]);
GO
ALTER TABLE [dbo].[Venta_PedidosDetalle] ADD CONSTRAINT [FK_Venta_PedidosDetalle_Producto_Catalogo]
    FOREIGN KEY ([ProductoID]) REFERENCES [dbo].[Producto_Catalogo]([ProductoID]);
GO
ALTER TABLE [dbo].[Venta_PedidosDetalle] ADD CONSTRAINT [FK_Venta_PedidosDetalle_Producto_Presentaciones]
    FOREIGN KEY ([PresentacionProductoID]) REFERENCES [dbo].[Producto_Presentaciones]([PresentacionProductoID]);
GO
ALTER TABLE [dbo].[Venta_PedidosDetalle] ADD CONSTRAINT [FK_Venta_PedidosDetalle_Venta_Pedidos]
    FOREIGN KEY ([PedidoID]) REFERENCES [dbo].[Venta_Pedidos]([PedidoID]);
GO

-- ============================================================
-- ÍNDICES (696 total, excluyendo PKs)
-- ============================================================
CREATE NONCLUSTERED INDEX [IX_AF_ActivoMedidores_ActivoID]
    ON [dbo].[ActivoFijo_ActivoMedidores] (ActivoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_ActivoMedidores]
    ON [dbo].[ActivoFijo_ActivoMedidores] (ActivoID, MedidorID);
GO
CREATE NONCLUSTERED INDEX [IX_AF_Activos_ActivoPadreID]
    ON [dbo].[ActivoFijo_Activos] (ActivoPadreID);
GO
CREATE NONCLUSTERED INDEX [IX_AF_Activos_ClaseActivoID]
    ON [dbo].[ActivoFijo_Activos] (ClaseActivoID);
GO
CREATE NONCLUSTERED INDEX [IX_AF_Activos_EstatusActivoID]
    ON [dbo].[ActivoFijo_Activos] (EstatusActivoID);
GO
CREATE NONCLUSTERED INDEX [IX_AF_Activos_NumeroSerie]
    ON [dbo].[ActivoFijo_Activos] (NumeroSerie);
GO
CREATE NONCLUSTERED INDEX [IX_AF_Activos_ProveedorID]
    ON [dbo].[ActivoFijo_Activos] (ProveedorID);
GO
CREATE NONCLUSTERED INDEX [IX_AF_Activos_Sucursal_Area]
    ON [dbo].[ActivoFijo_Activos] (Sucursal, AreaRestaurante);
GO
CREATE NONCLUSTERED INDEX [IX_AF_Activos_UbicacionActualID]
    ON [dbo].[ActivoFijo_Activos] (UbicacionActualID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_Activos_CodigoActivo]
    ON [dbo].[ActivoFijo_Activos] (CodigoActivo);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_Activos_EtiquetaID]
    ON [dbo].[ActivoFijo_Activos] (EtiquetaID);
GO
CREATE NONCLUSTERED INDEX [IX_AF_ActivosLibros_ActivoID]
    ON [dbo].[ActivoFijo_ActivosLibros] (ActivoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_ActivosLibros]
    ON [dbo].[ActivoFijo_ActivosLibros] (ActivoID, LibroDepreciacionID);
GO
CREATE NONCLUSTERED INDEX [IX_AF_Alertas_ActivoID_Leida]
    ON [dbo].[ActivoFijo_Alertas] (ActivoID, Leida);
GO
CREATE NONCLUSTERED INDEX [IX_AF_Alertas_TipoAlerta_Prioridad]
    ON [dbo].[ActivoFijo_Alertas] (TipoAlerta, Prioridad);
GO
CREATE NONCLUSTERED INDEX [IX_AF_Archivos_EntidadTipo_EntidadID]
    ON [dbo].[ActivoFijo_Archivos] (EntidadTipo, EntidadID);
GO
CREATE NONCLUSTERED INDEX [IX_AF_Autorizaciones_ActivoID]
    ON [dbo].[ActivoFijo_Autorizaciones] (ActivoID);
GO
CREATE NONCLUSTERED INDEX [IX_AF_Autorizaciones_EstadoAutorizacion]
    ON [dbo].[ActivoFijo_Autorizaciones] (EstadoAutorizacion);
GO
CREATE NONCLUSTERED INDEX [IX_AF_Autorizaciones_OTID]
    ON [dbo].[ActivoFijo_Autorizaciones] (OrdenTrabajoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_Autorizaciones_Folio]
    ON [dbo].[ActivoFijo_Autorizaciones] (FolioAutorizacion);
GO
CREATE NONCLUSTERED INDEX [IX_AF_BajasActivos_FechaBaja]
    ON [dbo].[ActivoFijo_BajasActivos] (FechaBaja);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_BajasActivos_Activo]
    ON [dbo].[ActivoFijo_BajasActivos] (ActivoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_ClaseActivo_Nombre]
    ON [dbo].[ActivoFijo_ClaseActivo] (Nombre);
GO
CREATE NONCLUSTERED INDEX [IX_AF_Cotizaciones_ActivoID]
    ON [dbo].[ActivoFijo_Cotizaciones] (ActivoID);
GO
CREATE NONCLUSTERED INDEX [IX_AF_Cotizaciones_EstadoCotizacion]
    ON [dbo].[ActivoFijo_Cotizaciones] (EstadoCotizacion);
GO
CREATE NONCLUSTERED INDEX [IX_AF_Cotizaciones_OrdenTrabajoID]
    ON [dbo].[ActivoFijo_Cotizaciones] (OrdenTrabajoID);
GO
CREATE NONCLUSTERED INDEX [IX_AF_Cotizaciones_ProveedorID]
    ON [dbo].[ActivoFijo_Cotizaciones] (ProveedorID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_Cotizaciones_Folio]
    ON [dbo].[ActivoFijo_Cotizaciones] (FolioCotizacion);
GO
CREATE NONCLUSTERED INDEX [IX_AF_DepreciacionMovimientos_ActivoLibroID_Periodo]
    ON [dbo].[ActivoFijo_DepreciacionMovimientos] (ActivoLibroID, Periodo);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_DepreciacionMovimientos]
    ON [dbo].[ActivoFijo_DepreciacionMovimientos] (ActivoLibroID, Periodo, TipoMovimiento);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_EstadoUsoActivo_Nombre]
    ON [dbo].[ActivoFijo_EstadoUsoActivo] (Nombre);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_EstatusActivo_Nombre]
    ON [dbo].[ActivoFijo_EstatusActivo] (Nombre);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_EstatusOT_Nombre]
    ON [dbo].[ActivoFijo_EstatusOT] (Nombre);
GO
CREATE NONCLUSTERED INDEX [IX_AF_HistorialAsignaciones_ActivoID_FechaInicio]
    ON [dbo].[ActivoFijo_HistorialAsignaciones] (ActivoID, FechaInicio);
GO
CREATE NONCLUSTERED INDEX [IX_AF_LecturasMedidor_ActivoMedidorID_FechaLectura]
    ON [dbo].[ActivoFijo_LecturasMedidor] (ActivoMedidorID, FechaLectura);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_LibrosDepreciacion_Codigo]
    ON [dbo].[ActivoFijo_LibrosDepreciacion] (CodigoLibro);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_Medidores_Codigo]
    ON [dbo].[ActivoFijo_Medidores] (CodigoMedidor);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_MetodosDepreciacion_Codigo]
    ON [dbo].[ActivoFijo_MetodosDepreciacion] (CodigoMetodo);
GO
CREATE NONCLUSTERED INDEX [IX_AF_MovimientosActivo_ActivoID_FechaMovimiento]
    ON [dbo].[ActivoFijo_MovimientosActivo] (ActivoID, FechaMovimiento);
GO
CREATE NONCLUSTERED INDEX [IX_AF_OrdenesTrabajo_ActivoID]
    ON [dbo].[ActivoFijo_OrdenesTrabajo] (ActivoID);
GO
CREATE NONCLUSTERED INDEX [IX_AF_OrdenesTrabajo_EstatusOTID_FechaProgramada]
    ON [dbo].[ActivoFijo_OrdenesTrabajo] (EstatusOTID, FechaProgramada);
GO
CREATE NONCLUSTERED INDEX [IX_AF_OrdenesTrabajo_PlanMantenimientoID]
    ON [dbo].[ActivoFijo_OrdenesTrabajo] (PlanMantenimientoID);
GO
CREATE NONCLUSTERED INDEX [IX_AF_OrdenesTrabajo_ProveedorID]
    ON [dbo].[ActivoFijo_OrdenesTrabajo] (ProveedorID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_OrdenesTrabajo_Folio]
    ON [dbo].[ActivoFijo_OrdenesTrabajo] (FolioOT);
GO
CREATE NONCLUSTERED INDEX [IX_AF_OrdenTrabajoCostos_OrdenTrabajoID]
    ON [dbo].[ActivoFijo_OrdenTrabajoCostos] (OrdenTrabajoID);
GO
CREATE NONCLUSTERED INDEX [IX_AF_PlanesMantenimiento_ActivoID]
    ON [dbo].[ActivoFijo_PlanesMantenimiento] (ActivoID);
GO
CREATE NONCLUSTERED INDEX [IX_AF_PlanesMantenimiento_ClaseActivoID]
    ON [dbo].[ActivoFijo_PlanesMantenimiento] (ClaseActivoID);
GO
CREATE NONCLUSTERED INDEX [IX_AF_PlanesMantenimiento_ProximoVencimiento]
    ON [dbo].[ActivoFijo_PlanesMantenimiento] (ProximoVencimiento);
GO
CREATE NONCLUSTERED INDEX [IX_AF_PlanesMantenimiento_UbicacionID]
    ON [dbo].[ActivoFijo_PlanesMantenimiento] (UbicacionID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_PlanesMantenimiento_Codigo]
    ON [dbo].[ActivoFijo_PlanesMantenimiento] (CodigoPlan);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_PrioridadOT_Nombre]
    ON [dbo].[ActivoFijo_PrioridadOT] (Nombre);
GO
CREATE NONCLUSTERED INDEX [IX_AF_ReemplazosActivos_ActivoAnteriorID]
    ON [dbo].[ActivoFijo_ReemplazosActivos] (ActivoAnteriorID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_ReemplazosActivos]
    ON [dbo].[ActivoFijo_ReemplazosActivos] (ActivoAnteriorID, ActivoNuevoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_ReglasClaseLibro]
    ON [dbo].[ActivoFijo_ReglasClaseLibro] (ClaseActivoID, LibroDepreciacionID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_TipoActivo_Nombre]
    ON [dbo].[ActivoFijo_TipoActivo] (Nombre);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_TipoBaja_Nombre]
    ON [dbo].[ActivoFijo_TipoBaja] (Nombre);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_TipoMedidor_Nombre]
    ON [dbo].[ActivoFijo_TipoMedidor] (Nombre);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_TipoOT_Nombre]
    ON [dbo].[ActivoFijo_TipoOT] (Nombre);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_TipoUbicacion_Nombre]
    ON [dbo].[ActivoFijo_TipoUbicacion] (Nombre);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_AF_Ubicaciones_Codigo]
    ON [dbo].[ActivoFijo_Ubicaciones] (CodigoUbicacion);
GO
CREATE NONCLUSTERED INDEX [IX_Alertas_Acknowledged]
    ON [dbo].[Alertas_Sistema] (Acknowledged);
GO
CREATE NONCLUSTERED INDEX [IX_Alertas_Tipo]
    ON [dbo].[Alertas_Sistema] (Tipo);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Alertas___D9EF47E451A4E4AF]
    ON [dbo].[Alertas_Sistema] (AlertaID);
GO
CREATE NONCLUSTERED INDEX [IX_config_servidor]
    ON [dbo].[automatizacion_inventarios_config] (server_id, sucursal_id, almacen_id);
GO
CREATE NONCLUSTERED INDEX [IX_destinatarios_jerarquia]
    ON [dbo].[automatizacion_inventarios_destinatarios] (server_id, sucursal_id, almacen_id, canal, activo);
GO
CREATE NONCLUSTERED INDEX [IX_ejecuciones_fecha]
    ON [dbo].[automatizacion_inventarios_ejecuciones] (fecha_inicio);
GO
CREATE NONCLUSTERED INDEX [IX_envios_procesado]
    ON [dbo].[automatizacion_inventarios_envios] (procesado_id);
GO
CREATE NONCLUSTERED INDEX [IX_folios_hash]
    ON [dbo].[automatizacion_inventarios_folios_procesados] (hash_verificacion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_folios_clave_unica_v2]
    ON [dbo].[automatizacion_inventarios_folios_procesados] (sistema_origen, server_id, sucursal_id, almacen_id, comentario, folio_inventario, fecha_inventario, estado_inventario_origen);
GO
CREATE NONCLUSTERED INDEX [IX_ultimo_folio_servidor]
    ON [dbo].[automatizacion_inventarios_ultimo_folio_conocido] (server_id, sistema_origen);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_ultimo_folio_clave]
    ON [dbo].[automatizacion_inventarios_ultimo_folio_conocido] (sistema_origen, server_id, sucursal_id, almacen_id);
GO
CREATE NONCLUSTERED INDEX [IX_CavaSocios_Botellas_Estatus]
    ON [dbo].[CavaSocios_Botellas] (EstatusBotella);
GO
CREATE NONCLUSTERED INDEX [IX_CavaSocios_Botellas_Socio]
    ON [dbo].[CavaSocios_Botellas] (SocioID);
GO
CREATE NONCLUSTERED INDEX [IX_CavaSocios_Cargos_Estatus]
    ON [dbo].[CavaSocios_Cargos] (EstatusCargo);
GO
CREATE NONCLUSTERED INDEX [IX_CavaSocios_Cargos_Socio]
    ON [dbo].[CavaSocios_Cargos] (SocioID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__CavaSoci__7B9F2137A5004EC5]
    ON [dbo].[CavaSocios_Configuracion] (EmpresaID);
GO
CREATE NONCLUSTERED INDEX [IX_CavaSocios_Movimientos_Botella]
    ON [dbo].[CavaSocios_Movimientos] (BotellaID);
GO
CREATE NONCLUSTERED INDEX [IX_CavaSocios_Movimientos_Fecha]
    ON [dbo].[CavaSocios_Movimientos] (FechaMovimiento);
GO
CREATE NONCLUSTERED INDEX [IX_CavaSocios_Socios_ClienteCRM]
    ON [dbo].[CavaSocios_Socios] (ClienteCRMID);
GO
CREATE NONCLUSTERED INDEX [IX_CavaSocios_Socios_Empresa]
    ON [dbo].[CavaSocios_Socios] (EmpresaID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_CavaSocios_NumeroSocio]
    ON [dbo].[CavaSocios_Socios] (EmpresaID, NumeroSocio);
GO
CREATE NONCLUSTERED INDEX [IX_Cliente_Catalogo_ClienteMaestroID]
    ON [dbo].[Cliente_Catalogo] (ClienteMaestroID);
GO
CREATE NONCLUSTERED INDEX [IX_Cliente_Catalogo_GrupoClienteID]
    ON [dbo].[Cliente_Catalogo] (GrupoClienteID);
GO
CREATE NONCLUSTERED INDEX [IX_Cliente_Catalogo_RazonSocial]
    ON [dbo].[Cliente_Catalogo] (RazonSocial);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Cliente_Catalogo_CodigoCliente]
    ON [dbo].[Cliente_Catalogo] (CodigoCliente);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Cliente_Catalogo_RFC]
    ON [dbo].[Cliente_Catalogo] (RFC);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Cliente_Grupos_CodigoGrupoCliente]
    ON [dbo].[Cliente_Grupos] (CodigoGrupoCliente);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Cliente_Grupos_NombreGrupoCliente]
    ON [dbo].[Cliente_Grupos] (NombreGrupoCliente);
GO
CREATE NONCLUSTERED INDEX [IX_Cliente_UsuariosPortal_ClienteID]
    ON [dbo].[Cliente_UsuariosPortal] (ClienteID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Cliente_UsuariosPortal_Email]
    ON [dbo].[Cliente_UsuariosPortal] (Email);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenDestinatarios_Activo]
    ON [dbo].[Comercial_AlertasMargenDestinatarios] (Activo);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenDestinatarios_Empresa]
    ON [dbo].[Comercial_AlertasMargenDestinatarios] (EmpresaID);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenDestinatarios_Server]
    ON [dbo].[Comercial_AlertasMargenDestinatarios] (ServerID);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenDestinatarios_Severidad]
    ON [dbo].[Comercial_AlertasMargenDestinatarios] (SeveridadMinima);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenEnvios_Alerta]
    ON [dbo].[Comercial_AlertasMargenEnvios] (AlertaMargenEventoID);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenEnvios_Canal]
    ON [dbo].[Comercial_AlertasMargenEnvios] (Canal, EstadoEnvio);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenEnvios_Destinatario]
    ON [dbo].[Comercial_AlertasMargenEnvios] (DestinatarioID);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenEnvios_Estado]
    ON [dbo].[Comercial_AlertasMargenEnvios] (EstadoEnvio);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenEnvios_Fecha]
    ON [dbo].[Comercial_AlertasMargenEnvios] (FechaCreacion);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenEventos_Duplicados]
    ON [dbo].[Comercial_AlertasMargenEventos] (ProductoClave, ServerID, Estado, Severidad);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenEventos_Estado]
    ON [dbo].[Comercial_AlertasMargenEventos] (Estado);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenEventos_Fecha]
    ON [dbo].[Comercial_AlertasMargenEventos] (FechaEvaluacion);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenEventos_Producto]
    ON [dbo].[Comercial_AlertasMargenEventos] (ProductoClave);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenEventos_Regla]
    ON [dbo].[Comercial_AlertasMargenEventos] (ReglaMargenID);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenEventos_Server]
    ON [dbo].[Comercial_AlertasMargenEventos] (ServerID);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenEventos_Severidad]
    ON [dbo].[Comercial_AlertasMargenEventos] (Severidad);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenReglas_Familia]
    ON [dbo].[Comercial_AlertasMargenReglas] (FamiliaCodigo);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenReglas_Grupo]
    ON [dbo].[Comercial_AlertasMargenReglas] (GrupoCodigo);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenReglas_Nivel]
    ON [dbo].[Comercial_AlertasMargenReglas] (NivelAplicacion, Activo);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenReglas_Producto]
    ON [dbo].[Comercial_AlertasMargenReglas] (ProductoClave);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenReglas_Subfamilia]
    ON [dbo].[Comercial_AlertasMargenReglas] (SubfamiliaCodigo);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasMargenReglas_Vigencia]
    ON [dbo].[Comercial_AlertasMargenReglas] (Activo, FechaInicioVigencia, FechaFinVigencia);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasUmbralesSeveridad_Activo]
    ON [dbo].[Comercial_AlertasUmbralesSeveridad] (Activo, Orden);
GO
CREATE NONCLUSTERED INDEX [IX_AlertasUmbralesSeveridad_Severidad]
    ON [dbo].[Comercial_AlertasUmbralesSeveridad] (Severidad);
GO
CREATE NONCLUSTERED INDEX [IX_CompetidoresCatalogo_Activo]
    ON [dbo].[Comercial_CompetidoresCatalogo] (Activo);
GO
CREATE NONCLUSTERED INDEX [IX_CompetidoresCatalogo_Ciudad]
    ON [dbo].[Comercial_CompetidoresCatalogo] (Ciudad);
GO
CREATE NONCLUSTERED INDEX [IX_CompetidoresCatalogo_Nombre]
    ON [dbo].[Comercial_CompetidoresCatalogo] (NombreCompetidor);
GO
CREATE NONCLUSTERED INDEX [IX_CompetidoresListas_Activo]
    ON [dbo].[Comercial_CompetidoresListas] (Activo);
GO
CREATE NONCLUSTERED INDEX [IX_CompetidoresListas_Empresa]
    ON [dbo].[Comercial_CompetidoresListas] (EmpresaID);
GO
CREATE NONCLUSTERED INDEX [IX_CompetidoresListas_Unidad]
    ON [dbo].[Comercial_CompetidoresListas] (UnidadNegocioID);
GO
CREATE NONCLUSTERED INDEX [IX_ListasDetalle_Activo]
    ON [dbo].[Comercial_CompetidoresListasDetalle] (Activo);
GO
CREATE NONCLUSTERED INDEX [IX_ListasDetalle_Competidor]
    ON [dbo].[Comercial_CompetidoresListasDetalle] (CompetidorID);
GO
CREATE NONCLUSTERED INDEX [IX_ListasDetalle_Lista]
    ON [dbo].[Comercial_CompetidoresListasDetalle] (ListaCompetidoresID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_ListaCompetidor_Activo]
    ON [dbo].[Comercial_CompetidoresListasDetalle] (ListaCompetidoresID, CompetidorID);
GO
CREATE NONCLUSTERED INDEX [IX_CompetidoresUnidad_Activo]
    ON [dbo].[Comercial_CompetidoresUnidad] (Activo);
GO
CREATE NONCLUSTERED INDEX [IX_CompetidoresUnidad_Competidor]
    ON [dbo].[Comercial_CompetidoresUnidad] (CompetidorCatalogoID);
GO
CREATE NONCLUSTERED INDEX [IX_CompetidoresUnidad_Empresa]
    ON [dbo].[Comercial_CompetidoresUnidad] (EmpresaID);
GO
CREATE NONCLUSTERED INDEX [IX_CompetidoresUnidad_Unidad]
    ON [dbo].[Comercial_CompetidoresUnidad] (UnidadNegocioID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UK_CompetidoresUnidad_CompetidorUnidad]
    ON [dbo].[Comercial_CompetidoresUnidad] (CompetidorCatalogoID, UnidadNegocioID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Comercial_Dashboard_Cache]
    ON [dbo].[Comercial_Dashboard_Cache] (ServerID, PeriodoKey);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Comercia__06370DACDC10A2B9]
    ON [dbo].[Comercial_ImpuestosCatalogo] (Codigo);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_ImpuestosMapeo_Producto]
    ON [dbo].[Comercial_ImpuestosMapeo] (ServerID, CodigoProducto);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Comercial_KPIs_Cache]
    ON [dbo].[Comercial_KPIs_Cache] (ServerID, PeriodoKey);
GO
CREATE NONCLUSTERED INDEX [IX_KPIs_Diarios_v2_AnioMes]
    ON [dbo].[Comercial_KPIs_Diarios_v2] (anio, mes);
GO
CREATE NONCLUSTERED INDEX [IX_KPIs_Diarios_v2_Fecha]
    ON [dbo].[Comercial_KPIs_Diarios_v2] (fecha_operacion);
GO
CREATE NONCLUSTERED INDEX [IX_KPIs_Diarios_v2_Hash]
    ON [dbo].[Comercial_KPIs_Diarios_v2] (hash_origen);
GO
CREATE NONCLUSTERED INDEX [IX_KPIs_Diarios_v2_Unidad]
    ON [dbo].[Comercial_KPIs_Diarios_v2] (unidad_negocio_id);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_KPIs_Diarios_v2]
    ON [dbo].[Comercial_KPIs_Diarios_v2] (unidad_negocio_id, sucursal_id, fecha_operacion);
GO
CREATE NONCLUSTERED INDEX [IX_Comercial_KPIs_Historico_Fecha]
    ON [dbo].[Comercial_KPIs_Historico] (fecha);
GO
CREATE NONCLUSTERED INDEX [IX_Comercial_KPIs_Historico_RunId]
    ON [dbo].[Comercial_KPIs_Historico] (run_id);
GO
CREATE NONCLUSTERED INDEX [IX_Comercial_KPIs_Historico_Server_Fecha]
    ON [dbo].[Comercial_KPIs_Historico] (server_id, fecha);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UX_Comercial_KPIs_Historico]
    ON [dbo].[Comercial_KPIs_Historico] (server_id, sucursal_id, system_type_normalized, fecha, kpi_tipo);
GO
CREATE NONCLUSTERED INDEX [IX_KPIs_Mensuales_v2_AnioMes]
    ON [dbo].[Comercial_KPIs_Mensuales_v2] (anio, mes);
GO
CREATE NONCLUSTERED INDEX [IX_KPIs_Mensuales_v2_Unidad]
    ON [dbo].[Comercial_KPIs_Mensuales_v2] (unidad_negocio_id);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_KPIs_Mensuales_v2]
    ON [dbo].[Comercial_KPIs_Mensuales_v2] (unidad_negocio_id, sucursal_id, anio, mes);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Comercial_Metas]
    ON [dbo].[Comercial_Metas] (ServerID, Sucursal, Mes, Anio);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_PrecioSugerido_Producto]
    ON [dbo].[Comercial_PreciosSugeridos] (ServerID, CodigoProducto, ReglaPrecioID);
GO
CREATE NONCLUSTERED INDEX [IX_RecetasSnapshot_Actual]
    ON [dbo].[Comercial_RecetasSnapshot] (ProductoClave, ServerID, EsActual);
GO
CREATE NONCLUSTERED INDEX [IX_RecetasSnapshot_Fecha]
    ON [dbo].[Comercial_RecetasSnapshot] (FechaSnapshot);
GO
CREATE NONCLUSTERED INDEX [IX_RecetasSnapshot_Hash]
    ON [dbo].[Comercial_RecetasSnapshot] (HashReceta);
GO
CREATE NONCLUSTERED INDEX [IX_RecetasSnapshot_Producto]
    ON [dbo].[Comercial_RecetasSnapshot] (ProductoClave);
GO
CREATE NONCLUSTERED INDEX [IX_RecetasSnapshot_Server]
    ON [dbo].[Comercial_RecetasSnapshot] (ServerID);
GO
CREATE NONCLUSTERED INDEX [IX_RecetasSnapshotDetalle_Costo]
    ON [dbo].[Comercial_RecetasSnapshotDetalle] (RecetaSnapshotID, CostoTotal);
GO
CREATE NONCLUSTERED INDEX [IX_RecetasSnapshotDetalle_Insumo]
    ON [dbo].[Comercial_RecetasSnapshotDetalle] (InsumoClave);
GO
CREATE NONCLUSTERED INDEX [IX_RecetasSnapshotDetalle_Snapshot]
    ON [dbo].[Comercial_RecetasSnapshotDetalle] (RecetaSnapshotID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Comercia__06370DACA6E08E53]
    ON [dbo].[Comercial_ReglasPrecio] (Codigo);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Rango_Orden]
    ON [dbo].[Comercial_ReglasPrecioRangos] (ReglaPrecioID, Orden);
GO
CREATE NONCLUSTERED INDEX [IX_Simulaciones_Fecha]
    ON [dbo].[Comercial_SimulacionesPrecios] (FechaSimulacion);
GO
CREATE NONCLUSTERED INDEX [IX_Simulaciones_ProductoID]
    ON [dbo].[Comercial_SimulacionesPrecios] (ProductoID);
GO
CREATE NONCLUSTERED INDEX [IX_Simulaciones_Usuario]
    ON [dbo].[Comercial_SimulacionesPrecios] (UsuarioID);
GO
CREATE NONCLUSTERED INDEX [IX_SolicitudesCambioPrecio_Estatus]
    ON [dbo].[Comercial_SolicitudesCambioPrecio] (Estatus);
GO
CREATE NONCLUSTERED INDEX [IX_SolicitudesCambioPrecio_Fecha]
    ON [dbo].[Comercial_SolicitudesCambioPrecio] (FechaSolicitud);
GO
CREATE NONCLUSTERED INDEX [IX_SolicitudesCambioPrecio_ProductoID]
    ON [dbo].[Comercial_SolicitudesCambioPrecio] (ProductoID);
GO
CREATE NONCLUSTERED INDEX [IX_SolicitudesCambioPrecio_ServerID]
    ON [dbo].[Comercial_SolicitudesCambioPrecio] (ServerID);
GO
CREATE NONCLUSTERED INDEX [IX_SolicitudesCambioPrecio_Solicitante]
    ON [dbo].[Comercial_SolicitudesCambioPrecio] (SolicitanteUsuarioID);
GO
CREATE NONCLUSTERED INDEX [IX_HistorialSolicitudes_Fecha]
    ON [dbo].[Comercial_SolicitudesCambioPrecioHistorial] (FechaAccion);
GO
CREATE NONCLUSTERED INDEX [IX_HistorialSolicitudes_SolicitudID]
    ON [dbo].[Comercial_SolicitudesCambioPrecioHistorial] (SolicitudID);
GO
CREATE NONCLUSTERED INDEX [IX_SyncLog_v2_RunId]
    ON [dbo].[Comercial_SyncLog_v2] (run_id);
GO
CREATE NONCLUSTERED INDEX [IX_SyncLog_v2_Status]
    ON [dbo].[Comercial_SyncLog_v2] (status);
GO
CREATE NONCLUSTERED INDEX [IX_SyncLog_v2_Timestamp]
    ON [dbo].[Comercial_SyncLog_v2] (run_timestamp);
GO
CREATE NONCLUSTERED INDEX [IX_SyncLog_v2_Unidad]
    ON [dbo].[Comercial_SyncLog_v2] (unidad_negocio_id);
GO
CREATE NONCLUSTERED INDEX [IX_Ventas_Dia_v2_Snapshot]
    ON [dbo].[Comercial_Ventas_Dia_Abiertas_v2] (snapshot_timestamp);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Ventas_Dia_v2_Unidad]
    ON [dbo].[Comercial_Ventas_Dia_Abiertas_v2] (unidad_negocio_id, sucursal_id);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_Estatus]
    ON [dbo].[Compras] (EstatusCompraID, FechaCompra);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_OrdenCompraID]
    ON [dbo].[Compras] (OrdenCompraID);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_Proveedor_Fecha]
    ON [dbo].[Compras] (ProveedorID, FechaCompra);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_UUIDFactura]
    ON [dbo].[Compras] (UUIDFactura);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_FolioCompra]
    ON [dbo].[Compras] (FolioCompra);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_ConciliacionSAT_Documento]
    ON [dbo].[Compras_ConciliacionSAT] (DocumentoFiscalID, EstatusConciliacionSATID, FechaConciliacion);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_ConciliacionSAT_Recepcion]
    ON [dbo].[Compras_ConciliacionSAT] (RecepcionCompraID, FechaConciliacion);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_ConciliacionSATDetalle_Conciliacion]
    ON [dbo].[Compras_ConciliacionSATDetalle] (ConciliacionSATID, DocumentoFiscalDetalleID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_ConciliacionSATEstatus_Descripcion]
    ON [dbo].[Compras_ConciliacionSATEstatus] (Descripcion);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_Detalle_OrdenDetalle]
    ON [dbo].[Compras_Detalle] (OrdenDetalleCompraID);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_Detalle_PedidoDetalle]
    ON [dbo].[Compras_Detalle] (PedidoDetalleCompraID);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_Detalle_Producto]
    ON [dbo].[Compras_Detalle] (ProductoID, PresentacionProductoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_Detalle_Renglon]
    ON [dbo].[Compras_Detalle] (CompraID, Renglon);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_DocumentosFiscales_Estatus]
    ON [dbo].[Compras_DocumentosFiscales] (EstatusDocumentoFiscalID, FechaDescarga);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_DocumentosFiscales_Proveedor]
    ON [dbo].[Compras_DocumentosFiscales] (UUID, Total, RFCEmisor, RFCReceptor, ProveedorID, FechaEmision);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_DocumentosFiscales_RFCEmisorFecha]
    ON [dbo].[Compras_DocumentosFiscales] (RFCEmisor, FechaEmision);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_DocumentosFiscales_SucursalFecha]
    ON [dbo].[Compras_DocumentosFiscales] (UUID, Total, ProveedorID, EstatusDocumentoFiscalID, SucursalID, FechaEmision);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_DocumentosFiscales_UUID]
    ON [dbo].[Compras_DocumentosFiscales] (UUID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_DocumentosFiscales_UUID]
    ON [dbo].[Compras_DocumentosFiscales] (UUID);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_DocumentosFiscalesDetalle_Documento]
    ON [dbo].[Compras_DocumentosFiscalesDetalle] (DocumentoFiscalID, Renglon);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_DocumentosFiscalesDetalle_Renglon]
    ON [dbo].[Compras_DocumentosFiscalesDetalle] (DocumentoFiscalID, Renglon);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_DocumentosFiscalesEstatus_Descripcion]
    ON [dbo].[Compras_DocumentosFiscalesEstatus] (Descripcion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_Estatus_Descripcion]
    ON [dbo].[Compras_Estatus] (Descripcion);
GO
CREATE NONCLUSTERED INDEX [IX_Eventos_Pendientes]
    ON [dbo].[Compras_Eventos_Pendientes] (Procesado, CreatedAt);
GO
CREATE NONCLUSTERED INDEX [IX_Eventos_Server]
    ON [dbo].[Compras_Eventos_Pendientes] (ServerID, EventoTipo);
GO
CREATE NONCLUSTERED INDEX [IX_InvFisico_Fecha]
    ON [dbo].[Compras_Inventarios_Fisicos_Sync] (fecha);
GO
CREATE NONCLUSTERED INDEX [IX_InvFisico_Server]
    ON [dbo].[Compras_Inventarios_Fisicos_Sync] (server_id);
GO
CREATE NONCLUSTERED INDEX [IX_InvFisico_Unidad]
    ON [dbo].[Compras_Inventarios_Fisicos_Sync] (unidad_negocio_id);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_InvFisico_Folio_Server]
    ON [dbo].[Compras_Inventarios_Fisicos_Sync] (folio, server_id);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_KPIs_Fecha]
    ON [dbo].[Compras_KPIs_Historico] (fecha);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_KPIs_Tipo]
    ON [dbo].[Compras_KPIs_Historico] (kpi_tipo);
GO
CREATE UNIQUE NONCLUSTERED INDEX [IX_Compras_KPIs_Unique]
    ON [dbo].[Compras_KPIs_Historico] (server_id, sucursal_id, fecha, kpi_tipo);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_Ordenes_Autorizacion]
    ON [dbo].[Compras_Ordenes] (AutorizacionID);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_Ordenes_Estatus]
    ON [dbo].[Compras_Ordenes] (EstatusOrdenCompraID, FechaOrden);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_Ordenes_Pedido]
    ON [dbo].[Compras_Ordenes] (PedidoCompraID);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_Ordenes_Proveedor_Fecha]
    ON [dbo].[Compras_Ordenes] (ProveedorID, FechaOrden);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_Ordenes_FolioOrden]
    ON [dbo].[Compras_Ordenes] (FolioOrden);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_OrdenesDetalle_PedidoDetalle]
    ON [dbo].[Compras_OrdenesDetalle] (PedidoDetalleCompraID);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_OrdenesDetalle_Producto]
    ON [dbo].[Compras_OrdenesDetalle] (ProductoID, PresentacionProductoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_OrdenesDetalle_Renglon]
    ON [dbo].[Compras_OrdenesDetalle] (OrdenCompraID, Renglon);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_OrdenesEstatus_Descripcion]
    ON [dbo].[Compras_OrdenesEstatus] (Descripcion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_Parametros_Server_Sucursal]
    ON [dbo].[Compras_Parametros_Sucursal] (ServerID, SucursalID);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_Pedidos_Autorizacion]
    ON [dbo].[Compras_Pedidos] (AutorizacionID);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_Pedidos_Estatus]
    ON [dbo].[Compras_Pedidos] (EstatusPedidoCompraID, FechaPedido);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_Pedidos_Sucursal_Fecha]
    ON [dbo].[Compras_Pedidos] (SucursalID, FechaPedido);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_Pedidos_FolioPedido]
    ON [dbo].[Compras_Pedidos] (FolioPedido);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_PedidosDetalle_Producto]
    ON [dbo].[Compras_PedidosDetalle] (ProductoID, PresentacionProductoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_PedidosDetalle_Renglon]
    ON [dbo].[Compras_PedidosDetalle] (PedidoCompraID, Renglon);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_PedidosEstatus_Descripcion]
    ON [dbo].[Compras_PedidosEstatus] (Descripcion);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_Recepciones_Estatus]
    ON [dbo].[Compras_Recepciones] (EstatusRecepcionID, FechaRecepcion);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_Recepciones_ProveedorFecha]
    ON [dbo].[Compras_Recepciones] (ProveedorID, FechaRecepcion);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_Recepciones_SucursalAlmacenFecha]
    ON [dbo].[Compras_Recepciones] (SucursalID, AlmacenID, FechaRecepcion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_Recepciones_Folio]
    ON [dbo].[Compras_Recepciones] (FolioRecepcion);
GO
CREATE NONCLUSTERED INDEX [IX_Compras_RecepcionesDetalle_Producto]
    ON [dbo].[Compras_RecepcionesDetalle] (ProductoID, PresentacionProductoID, RecepcionCompraID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_RecepcionesDetalle_Renglon]
    ON [dbo].[Compras_RecepcionesDetalle] (RecepcionCompraID, Renglon);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Compras_RecepcionesEstatus_Descripcion]
    ON [dbo].[Compras_RecepcionesEstatus] (Descripcion);
GO
CREATE NONCLUSTERED INDEX [IX_Requi_Fecha]
    ON [dbo].[Compras_Requisiciones_Sync] (fecha);
GO
CREATE NONCLUSTERED INDEX [IX_Requi_Server]
    ON [dbo].[Compras_Requisiciones_Sync] (server_id);
GO
CREATE NONCLUSTERED INDEX [IX_Requi_Unidad]
    ON [dbo].[Compras_Requisiciones_Sync] (unidad_negocio_id);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Requi_Folio_Server]
    ON [dbo].[Compras_Requisiciones_Sync] (folio, server_id, tipo);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Checkpoint_Server_Type]
    ON [dbo].[Compras_Sync_Checkpoint] (ServerID, SyncType);
GO
CREATE NONCLUSTERED INDEX [IX_SyncLog_Date]
    ON [dbo].[Compras_Sync_Log] (created_at);
GO
CREATE NONCLUSTERED INDEX [IX_SyncLog_Server]
    ON [dbo].[Compras_Sync_Log] (server_id);
GO
CREATE NONCLUSTERED INDEX [IX_Config_ServerAlmacen]
    ON [dbo].[Config_Asignaciones] (ServerID, AlmacenID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Config_A__C3BC333D3B751AA0]
    ON [dbo].[Config_Asignaciones] (ConfigID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Configur__E8181E11C0D6A419]
    ON [dbo].[Configuracion_Operativa] (Clave);
GO
CREATE NONCLUSTERED INDEX [IX_ConsultasSQL_Activo]
    ON [dbo].[ConsultasSQL_Catalogo] (Activo);
GO
CREATE NONCLUSTERED INDEX [IX_ConsultasSQL_EsSistema]
    ON [dbo].[ConsultasSQL_Catalogo] (EsSistema);
GO
CREATE NONCLUSTERED INDEX [IX_ConsultasSQL_Modulo]
    ON [dbo].[ConsultasSQL_Catalogo] (Modulo);
GO
CREATE NONCLUSTERED INDEX [IX_ConsultasSQL_Sistema]
    ON [dbo].[ConsultasSQL_Catalogo] (SistemaTipoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_ConsultasSQL_Codigo]
    ON [dbo].[ConsultasSQL_Catalogo] (CodigoConsulta);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_ConsultasSQL_UUID]
    ON [dbo].[ConsultasSQL_Catalogo] (PublicUUID);
GO
CREATE NONCLUSTERED INDEX [IX_ConsultasSQL_Log_Consulta]
    ON [dbo].[ConsultasSQL_EjecucionesLog] (ConsultaID);
GO
CREATE NONCLUSTERED INDEX [IX_ConsultasSQL_Log_Fecha]
    ON [dbo].[ConsultasSQL_EjecucionesLog] (FechaEjecucion);
GO
CREATE NONCLUSTERED INDEX [IX_ConsultasSQL_Log_Usuario]
    ON [dbo].[ConsultasSQL_EjecucionesLog] (UsuarioID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_ConsultasSQL_Param_Nombre]
    ON [dbo].[ConsultasSQL_Parametros] (ConsultaID, NombreParametro);
GO
CREATE NONCLUSTERED INDEX [IX_ConsultasSQL_Perm_Consulta]
    ON [dbo].[ConsultasSQL_Permisos] (ConsultaID);
GO
CREATE NONCLUSTERED INDEX [IX_ConsultasSQL_Perm_Rol]
    ON [dbo].[ConsultasSQL_Permisos] (RolID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_ConsultasSQL_Srv_Unique]
    ON [dbo].[ConsultasSQL_Servidores] (ConsultaID, ServidorID, EmpresaID, SucursalID);
GO
CREATE NONCLUSTERED INDEX [IX_ConsultasSQL_Ver_Consulta]
    ON [dbo].[ConsultasSQL_Versiones] (ConsultaID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_ConsultasSQL_Ver_Unico]
    ON [dbo].[ConsultasSQL_Versiones] (ConsultaID, Version);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Actividades_AsignadoA]
    ON [dbo].[CRM_Actividades] (AsignadoAUserID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Actividades_Empresa]
    ON [dbo].[CRM_Actividades] (EmpresaID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Actividades_Entidad]
    ON [dbo].[CRM_Actividades] (EntidadTipo, EntidadID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Actividades_Estatus]
    ON [dbo].[CRM_Actividades] (EstatusActividadID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Actividades_FechaProgramada]
    ON [dbo].[CRM_Actividades] (FechaProgramada);
GO
CREATE NONCLUSTERED INDEX [IX_Log_Empresa]
    ON [dbo].[CRM_Automation_Log] (EmpresaID);
GO
CREATE NONCLUSTERED INDEX [IX_Log_Fecha]
    ON [dbo].[CRM_Automation_Log] (FechaEjecucion);
GO
CREATE NONCLUSTERED INDEX [IX_Log_Regla]
    ON [dbo].[CRM_Automation_Log] (ReglaID);
GO
CREATE NONCLUSTERED INDEX [IX_Reglas_Activa]
    ON [dbo].[CRM_Automation_Reglas] (Activa);
GO
CREATE NONCLUSTERED INDEX [IX_Reglas_Empresa]
    ON [dbo].[CRM_Automation_Reglas] (EmpresaID);
GO
CREATE NONCLUSTERED INDEX [IX_Reglas_Pipeline]
    ON [dbo].[CRM_Automation_Reglas] (PipelineID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_ClientesSolicitudesAlta_Cuenta]
    ON [dbo].[CRM_ClientesSolicitudesAlta] (CuentaID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_ClientesSolicitudesAlta_Empresa]
    ON [dbo].[CRM_ClientesSolicitudesAlta] (EmpresaID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_ClientesSolicitudesAlta_Estatus]
    ON [dbo].[CRM_ClientesSolicitudesAlta] (EstatusSolicitud);
GO
CREATE UNIQUE NONCLUSTERED INDEX [IX_CRM_ClientesSolicitudesAlta_Folio]
    ON [dbo].[CRM_ClientesSolicitudesAlta] (EmpresaID, FolioSolicitud);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_ClientesSolicitudesAltaHistorial_Solicitud]
    ON [dbo].[CRM_ClientesSolicitudesAltaHistorial] (SolicitudID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_PipelineEtapas_Pipeline]
    ON [dbo].[CRM_Config_PipelineEtapas] (PipelineID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Contratos_Cuenta]
    ON [dbo].[CRM_Contratos] (CuentaID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Contratos_Estatus]
    ON [dbo].[CRM_Contratos] (EstatusContratoID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Contratos_FechaFin]
    ON [dbo].[CRM_Contratos] (FechaFin);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Cuentas_ClienteID]
    ON [dbo].[CRM_Cuentas] (ClienteID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Cuentas_EjecutivoResponsable]
    ON [dbo].[CRM_Cuentas] (EjecutivoResponsableUserID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Cuentas_EmpresaID]
    ON [dbo].[CRM_Cuentas] (EmpresaID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Cuentas_TipoCuenta]
    ON [dbo].[CRM_Cuentas] (TipoCuenta);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Leads_CreatedAt]
    ON [dbo].[CRM_Leads] (CreatedAt);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Leads_Ejecutivo]
    ON [dbo].[CRM_Leads] (EjecutivoAsignadoUserID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Leads_Empresa]
    ON [dbo].[CRM_Leads] (EmpresaID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Leads_Estatus]
    ON [dbo].[CRM_Leads] (EstatusLeadID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_OportunidadContactos_Opp]
    ON [dbo].[CRM_Oportunidad_Contactos] (OportunidadID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_OportunidadDocs_Opp]
    ON [dbo].[CRM_Oportunidad_Documentos] (OportunidadID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Oportunidades_Cuenta]
    ON [dbo].[CRM_Oportunidades] (CuentaID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Oportunidades_Ejecutivo]
    ON [dbo].[CRM_Oportunidades] (EjecutivoResponsableUserID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Oportunidades_Empresa]
    ON [dbo].[CRM_Oportunidades] (EmpresaID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Oportunidades_Estatus]
    ON [dbo].[CRM_Oportunidades] (EstatusOportunidadID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Oportunidades_FechaCierre]
    ON [dbo].[CRM_Oportunidades] (FechaEstimadaCierre);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Oportunidades_Pipeline]
    ON [dbo].[CRM_Oportunidades] (PipelineID, EtapaActualID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_HistorialEtapas_Fecha]
    ON [dbo].[CRM_Oportunidades_HistorialEtapas] (FechaCambio);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_HistorialEtapas_Opp]
    ON [dbo].[CRM_Oportunidades_HistorialEtapas] (OportunidadID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__CRM_Post__00666684B52C8736]
    ON [dbo].[CRM_PostventaTickets] (FolioTicket);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Propuestas_Estatus]
    ON [dbo].[CRM_Propuestas] (EstatusPropuestaID);
GO
CREATE NONCLUSTERED INDEX [IX_CRM_Propuestas_Oportunidad]
    ON [dbo].[CRM_Propuestas] (OportunidadID);
GO
CREATE NONCLUSTERED INDEX [IX_CortesCaja_Demo]
    ON [dbo].[Finanzas_CortesCaja] (EsDemo);
GO
CREATE NONCLUSTERED INDEX [IX_CortesCaja_FechaCorte]
    ON [dbo].[Finanzas_CortesCaja] (FechaCorte, UnidadNegocioID);
GO
CREATE NONCLUSTERED INDEX [IX_CortesCaja_Hash]
    ON [dbo].[Finanzas_CortesCaja] (HashOrigen);
GO
CREATE NONCLUSTERED INDEX [IX_CortesCaja_Origen]
    ON [dbo].[Finanzas_CortesCaja] (SistemaOrigen, IdOrigen);
GO
CREATE NONCLUSTERED INDEX [IX_CortesCaja_UnidadNegocio]
    ON [dbo].[Finanzas_CortesCaja] (UnidadNegocioID, FechaCorte);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_CortesCaja_Origen]
    ON [dbo].[Finanzas_CortesCaja] (SistemaOrigen, ServerID, IdOrigen);
GO
CREATE NONCLUSTERED INDEX [IX_DetallePagos_Corte]
    ON [dbo].[Finanzas_CortesCaja_DetallePagos] (CorteCajaID);
GO
CREATE NONCLUSTERED INDEX [IX_CuadresZ_CorteCajaID]
    ON [dbo].[Finanzas_CuadresZ] (CorteCajaID);
GO
CREATE NONCLUSTERED INDEX [IX_CuadresZ_Estatus]
    ON [dbo].[Finanzas_CuadresZ] (EstatusCuadreID);
GO
CREATE NONCLUSTERED INDEX [IX_CuadresZ_FechaOperacion]
    ON [dbo].[Finanzas_CuadresZ] (FechaOperacion);
GO
CREATE NONCLUSTERED INDEX [IX_CuadresZ_FolioCorte]
    ON [dbo].[Finanzas_CuadresZ] (UnidadNegocioID, FolioCorte);
GO
CREATE UNIQUE NONCLUSTERED INDEX [IX_CuadresZ_HashOrigen]
    ON [dbo].[Finanzas_CuadresZ] (HashOrigen);
GO
CREATE NONCLUSTERED INDEX [IX_CuadresZ_IdOrigen]
    ON [dbo].[Finanzas_CuadresZ] (IdOrigen);
GO
CREATE NONCLUSTERED INDEX [IX_CuadresZ_UnidadFecha]
    ON [dbo].[Finanzas_CuadresZ] (UnidadNegocioID, FechaCorte);
GO
CREATE NONCLUSTERED INDEX [IX_CuadresZ_SyncLog_Fecha]
    ON [dbo].[Finanzas_CuadresZ_SyncLog] (FechaInicio);
GO
CREATE NONCLUSTERED INDEX [IX_CuadresZ_SyncLog_Unidad]
    ON [dbo].[Finanzas_CuadresZ_SyncLog] (UnidadNegocioID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UX_Finanzas_KPIs_Historico]
    ON [dbo].[Finanzas_KPIs_Historico] (server_id, sucursal_id, system_type_normalized, fecha, kpi_tipo);
GO
CREATE NONCLUSTERED INDEX [IX_Presupuestos_Periodo]
    ON [dbo].[Finanzas_Presupuestos] (Anio, Mes);
GO
CREATE NONCLUSTERED INDEX [IX_Presupuestos_Sucursal]
    ON [dbo].[Finanzas_Presupuestos] (SucursalID);
GO
CREATE NONCLUSTERED INDEX [IX_PropinasTPV_SyncLog_Fecha]
    ON [dbo].[Finanzas_PropinasTPV_SyncLog] (FechaInicio);
GO
CREATE NONCLUSTERED INDEX [IX_PropinasTPV_SyncLog_Sistema]
    ON [dbo].[Finanzas_PropinasTPV_SyncLog] (SistemaOrigen, Estatus);
GO
CREATE NONCLUSTERED INDEX [IX_PropinasTPV_SyncLog_Unidad]
    ON [dbo].[Finanzas_PropinasTPV_SyncLog] (UnidadNegocioID, FechaInicio);
GO
CREATE NONCLUSTERED INDEX [IX_SaldosBancarios_CuentaHistorial]
    ON [dbo].[Finanzas_SaldosBancarios] (SaldoFinal, EsVigente, Activo, Estatus, CuentaBancariaID, FechaSaldo);
GO
CREATE NONCLUSTERED INDEX [IX_SaldosBancarios_FechaSaldo]
    ON [dbo].[Finanzas_SaldosBancarios] (CuentaBancariaID, SaldoFinal, EsVigente, Activo, FechaSaldo);
GO
CREATE NONCLUSTERED INDEX [IX_SaldosBancarios_UltimoVigente]
    ON [dbo].[Finanzas_SaldosBancarios] (FechaSaldo, SaldoFinal, CuentaBancariaID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_SaldosBancarios_CuentaFecha_EsVigente]
    ON [dbo].[Finanzas_SaldosBancarios] (CuentaBancariaID, FechaSaldo);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Global_C__EAFB8B884039F1DE]
    ON [dbo].[Global_Cat_Bancos] (CodigoBanco);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Global_C__E8181E11CB985BF5]
    ON [dbo].[Global_Cat_FormaPagoSAT] (Clave);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Inventario_Almacenes_Sucursal_Codigo]
    ON [dbo].[Inventario_Almacenes] (SucursalID, CodigoAlmacen);
GO
CREATE NONCLUSTERED INDEX [IX_Inventario_Existencias_Consulta]
    ON [dbo].[Inventario_Existencias] (ExistenciaActual, CostoPromedio, UltimaFechaMovimiento, SucursalID, AlmacenID, ProductoID, PresentacionProductoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Inventario_Existencias_Clave]
    ON [dbo].[Inventario_Existencias] (SucursalID, AlmacenID, ProductoID, PresentacionProductoID);
GO
CREATE NONCLUSTERED INDEX [IX_Inventario_Movimientos_Ref]
    ON [dbo].[Inventario_Movimientos] (ReferenciaTipo, ReferenciaID, FechaMovimiento);
GO
CREATE NONCLUSTERED INDEX [IX_Inventario_Movimientos_SucursalAlmacenFecha]
    ON [dbo].[Inventario_Movimientos] (SucursalID, AlmacenID, FechaMovimiento);
GO
CREATE NONCLUSTERED INDEX [IX_Inventario_MovimientosDetalle_Producto]
    ON [dbo].[Inventario_MovimientosDetalle] (ProductoID, PresentacionProductoID, MovimientoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Inventario_TipoMovimiento_Codigo]
    ON [dbo].[Inventario_TipoMovimiento] (Codigo);
GO
CREATE NONCLUSTERED INDEX [IX_SinAsignar_Estado]
    ON [dbo].[Inventarios_SinAsignar] (Estado);
GO
CREATE NONCLUSTERED INDEX [IX_SinAsignar_ServerID]
    ON [dbo].[Inventarios_SinAsignar] (ServerID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Inventar__B897313F0C45543A]
    ON [dbo].[Inventarios_SinAsignar] (RegistroID);
GO
CREATE NONCLUSTERED INDEX [IX_OpAudProg_Estado]
    ON [dbo].[Operativo_AuditoriasProgramadas] (Estado);
GO
CREATE NONCLUSTERED INDEX [IX_OpAudProg_ProximaEjecucion]
    ON [dbo].[Operativo_AuditoriasProgramadas] (ProximaEjecucion);
GO
CREATE NONCLUSTERED INDEX [IX_OpAudProg_ServerID]
    ON [dbo].[Operativo_AuditoriasProgramadas] (ServerID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_OpAudProg_AuditoriaID]
    ON [dbo].[Operativo_AuditoriasProgramadas] (AuditoriaID);
GO
CREATE NONCLUSTERED INDEX [IX_OpBitComp_AutomatizacionID]
    ON [dbo].[Operativo_BitacoraCompras] (AutomatizacionID);
GO
CREATE NONCLUSTERED INDEX [IX_OpBitComp_Fecha]
    ON [dbo].[Operativo_BitacoraCompras] (Fecha);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_OpBitComp_BitacoraID]
    ON [dbo].[Operativo_BitacoraCompras] (BitacoraID);
GO
CREATE NONCLUSTERED INDEX [IX_OpCargo_EstatusCargo]
    ON [dbo].[Operativo_CargosResponsabilidad] (EstatusCargo);
GO
CREATE NONCLUSTERED INDEX [IX_OpCargo_FechaPropuesta]
    ON [dbo].[Operativo_CargosResponsabilidad] (FechaPropuesta);
GO
CREATE NONCLUSTERED INDEX [IX_OpCargo_ResponsabilidadID]
    ON [dbo].[Operativo_CargosResponsabilidad] (ResponsabilidadID);
GO
CREATE NONCLUSTERED INDEX [IX_OpCargo_WorkflowID]
    ON [dbo].[Operativo_CargosResponsabilidad] (WorkflowID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_OpCargo_CargoID]
    ON [dbo].[Operativo_CargosResponsabilidad] (CargoID);
GO
CREATE NONCLUSTERED INDEX [IX_OpDocGen_FechaGeneracion]
    ON [dbo].[Operativo_DocumentosGenerados] (FechaGeneracion);
GO
CREATE NONCLUSTERED INDEX [IX_OpDocGen_TipoDocumento]
    ON [dbo].[Operativo_DocumentosGenerados] (TipoDocumento);
GO
CREATE NONCLUSTERED INDEX [IX_OpDocGen_WorkflowID]
    ON [dbo].[Operativo_DocumentosGenerados] (WorkflowID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_OpDocGen_DocumentoID]
    ON [dbo].[Operativo_DocumentosGenerados] (DocumentoID);
GO
CREATE NONCLUSTERED INDEX [IX_OpHist_FechaAsignacion]
    ON [dbo].[Operativo_HistorialAsignaciones] (FechaAsignacion);
GO
CREATE NONCLUSTERED INDEX [IX_OpHist_TareaID]
    ON [dbo].[Operativo_HistorialAsignaciones] (TareaID);
GO
CREATE NONCLUSTERED INDEX [IX_OpHist_WorkflowID]
    ON [dbo].[Operativo_HistorialAsignaciones] (WorkflowID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_OpHist_HistorialID]
    ON [dbo].[Operativo_HistorialAsignaciones] (HistorialID);
GO
CREATE NONCLUSTERED INDEX [IX_OpHistCargo_CargoID]
    ON [dbo].[Operativo_HistorialCargos] (CargoID);
GO
CREATE NONCLUSTERED INDEX [IX_OpHistCargo_Fecha]
    ON [dbo].[Operativo_HistorialCargos] (Fecha);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_OpHistCargo_HistorialID]
    ON [dbo].[Operativo_HistorialCargos] (HistorialID);
GO
CREATE NONCLUSTERED INDEX [IX_OpNotif_Estado]
    ON [dbo].[Operativo_Notificaciones_Log] (Estado);
GO
CREATE NONCLUSTERED INDEX [IX_OpNotif_FechaEnvio]
    ON [dbo].[Operativo_Notificaciones_Log] (FechaEnvio);
GO
CREATE NONCLUSTERED INDEX [IX_OpNotif_TareaID]
    ON [dbo].[Operativo_Notificaciones_Log] (TareaID);
GO
CREATE NONCLUSTERED INDEX [IX_OpNotif_TipoEvento]
    ON [dbo].[Operativo_Notificaciones_Log] (TipoEvento);
GO
CREATE NONCLUSTERED INDEX [IX_OpNotif_WorkflowID]
    ON [dbo].[Operativo_Notificaciones_Log] (WorkflowID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_OpNotif_NotificacionID]
    ON [dbo].[Operativo_Notificaciones_Log] (NotificacionID);
GO
CREATE NONCLUSTERED INDEX [IX_OpPedProc_AutomatizacionID]
    ON [dbo].[Operativo_PedidosProcesados] (AutomatizacionID);
GO
CREATE NONCLUSTERED INDEX [IX_OpPedProc_FechaProcesamiento]
    ON [dbo].[Operativo_PedidosProcesados] (FechaProcesamiento);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_OpPedProc_PedidoID]
    ON [dbo].[Operativo_PedidosProcesados] (PedidoID);
GO
CREATE NONCLUSTERED INDEX [IX_OpResp_Estado]
    ON [dbo].[Operativo_ResponsabilidadEconomica] (Estado);
GO
CREATE NONCLUSTERED INDEX [IX_OpResp_FechaCalculo]
    ON [dbo].[Operativo_ResponsabilidadEconomica] (FechaCalculo);
GO
CREATE NONCLUSTERED INDEX [IX_OpResp_SucursalID]
    ON [dbo].[Operativo_ResponsabilidadEconomica] (SucursalID);
GO
CREATE NONCLUSTERED INDEX [IX_OpResp_WorkflowID]
    ON [dbo].[Operativo_ResponsabilidadEconomica] (WorkflowID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_OpResp_ResponsabilidadID]
    ON [dbo].[Operativo_ResponsabilidadEconomica] (ResponsabilidadID);
GO
CREATE NONCLUSTERED INDEX [IX_OpTareaComp_AutomatizacionID]
    ON [dbo].[Operativo_TareasCompras] (AutomatizacionID);
GO
CREATE NONCLUSTERED INDEX [IX_OpTareaComp_Estado]
    ON [dbo].[Operativo_TareasCompras] (Estado);
GO
CREATE NONCLUSTERED INDEX [IX_OpTareaComp_FechaCreacion]
    ON [dbo].[Operativo_TareasCompras] (FechaCreacion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_OpTareaComp_TareaID]
    ON [dbo].[Operativo_TareasCompras] (TareaID);
GO
CREATE NONCLUSTERED INDEX [IX_Producto_Catalogo_Activo]
    ON [dbo].[Producto_Catalogo] (Activo);
GO
CREATE NONCLUSTERED INDEX [IX_Producto_Catalogo_LineaProductoID]
    ON [dbo].[Producto_Catalogo] (LineaProductoID);
GO
CREATE NONCLUSTERED INDEX [IX_Producto_Catalogo_MarcaProductoID]
    ON [dbo].[Producto_Catalogo] (MarcaProductoID);
GO
CREATE NONCLUSTERED INDEX [IX_Producto_Catalogo_NombreProducto]
    ON [dbo].[Producto_Catalogo] (NombreProducto);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Producto_Catalogo_CodigoProducto]
    ON [dbo].[Producto_Catalogo] (CodigoProducto);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Producto_Catalogo_SKU]
    ON [dbo].[Producto_Catalogo] (SKU);
GO
CREATE NONCLUSTERED INDEX [IX_Producto_Equivalentes_ProductoID]
    ON [dbo].[Producto_Equivalentes] (ProductoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Producto_Equivalentes]
    ON [dbo].[Producto_Equivalentes] (ProductoID, ProductoEquivalenteRefID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Producto_Familias_CodigoFamilia]
    ON [dbo].[Producto_Familias] (CodigoFamilia);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Producto_Familias_NombreFamilia]
    ON [dbo].[Producto_Familias] (NombreFamilia);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Producto_Lineas_CodigoLinea]
    ON [dbo].[Producto_Lineas] (CodigoLinea);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Producto_Lineas_SubFamilia_Nombre]
    ON [dbo].[Producto_Lineas] (SubFamiliaProductoID, NombreLinea);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Producto_Marcas_CodigoMarca]
    ON [dbo].[Producto_Marcas] (CodigoMarca);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Producto_Marcas_NombreMarca]
    ON [dbo].[Producto_Marcas] (NombreMarca);
GO
CREATE NONCLUSTERED INDEX [IX_Producto_Presentaciones_ProductoID]
    ON [dbo].[Producto_Presentaciones] (ProductoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Producto_Presentaciones_CodigoPresentacion]
    ON [dbo].[Producto_Presentaciones] (CodigoPresentacion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Producto_Presentaciones_Producto_Nombre]
    ON [dbo].[Producto_Presentaciones] (ProductoID, NombrePresentacion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Producto_SubFamilias_CodigoSubFamilia]
    ON [dbo].[Producto_SubFamilias] (CodigoSubFamilia);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Producto_SubFamilias_Familia_Nombre]
    ON [dbo].[Producto_SubFamilias] (FamiliaProductoID, NombreSubFamilia);
GO
CREATE NONCLUSTERED INDEX [IX_Producto_Sustitutos_ProductoID]
    ON [dbo].[Producto_Sustitutos] (ProductoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Producto_Sustitutos]
    ON [dbo].[Producto_Sustitutos] (ProductoID, ProductoSustitutoRefID);
GO
CREATE NONCLUSTERED INDEX [IX_config_jerarquia]
    ON [dbo].[propinas_tpv_config] (alcance_tipo, alcance_server_id, activa);
GO
CREATE NONCLUSTERED INDEX [IX_propinas_cuadre]
    ON [dbo].[propinas_tpv_control] (cuadre_estado, fecha_corte);
GO
CREATE NONCLUSTERED INDEX [IX_propinas_fecha_estado]
    ON [dbo].[propinas_tpv_control] (fecha_corte, cuadre_estado);
GO
CREATE NONCLUSTERED INDEX [IX_propinas_servidor]
    ON [dbo].[propinas_tpv_control] (server_id, fecha_corte);
GO
CREATE NONCLUSTERED INDEX [IX_propinas_tpv_control_EsDemo]
    ON [dbo].[propinas_tpv_control] (EsDemo, fecha_corte);
GO
CREATE UNIQUE NONCLUSTERED INDEX [IX_propinas_tpv_control_HashOrigen]
    ON [dbo].[propinas_tpv_control] (HashOrigen);
GO
CREATE NONCLUSTERED INDEX [IX_propinas_tpv_control_SistemaOrigen]
    ON [dbo].[propinas_tpv_control] (SistemaOrigen, UnidadNegocioID);
GO
CREATE NONCLUSTERED INDEX [IX_propinas_tpv_control_UnidadNegocio]
    ON [dbo].[propinas_tpv_control] (UnidadNegocioID, fecha_corte);
GO
CREATE NONCLUSTERED INDEX [IX_propinas_usuarios]
    ON [dbo].[propinas_tpv_control] (pago_usuario_id, cuadre_usuario_id);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UK_propinas_tpv_corte]
    ON [dbo].[propinas_tpv_control] (server_id, sucursal_id, folio_corte, fecha_corte);
GO
CREATE NONCLUSTERED INDEX [IX_historial_propina]
    ON [dbo].[propinas_tpv_historial] (propina_id, fecha);
GO
CREATE NONCLUSTERED INDEX [IX_historial_usuario]
    ON [dbo].[propinas_tpv_historial] (usuario_id, fecha);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Cat_Bancos_NombreBanco]
    ON [dbo].[Proveedor_Bancos] (NombreBanco);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Cat_Proveedores_CodigoProveedor]
    ON [dbo].[Proveedor_Catalogo] (CodigoProveedor);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Cat_Proveedores_RFC]
    ON [dbo].[Proveedor_Catalogo] (RFC);
GO
CREATE NONCLUSTERED INDEX [IX_Proveedor_Categorias_ProveedorID]
    ON [dbo].[Proveedor_Categorias] (ProveedorID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Proveedor_Categorias]
    ON [dbo].[Proveedor_Categorias] (ProveedorID, CategoriaProveedorID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Cat_CategoriasProveedor_Nombre]
    ON [dbo].[Proveedor_CategoriasCatalogo] (NombreCategoria);
GO
CREATE NONCLUSTERED INDEX [IX_Proveedor_Contactos_ProveedorID]
    ON [dbo].[Proveedor_Contactos] (ProveedorID);
GO
CREATE NONCLUSTERED INDEX [IX_Proveedor_Contactos_ProveedorID_Activo]
    ON [dbo].[Proveedor_Contactos] (ProveedorID, Activo);
GO
CREATE NONCLUSTERED INDEX [IX_Proveedor_CuentasBancarias_CLABE]
    ON [dbo].[Proveedor_CuentasBancarias] (CLABE);
GO
CREATE NONCLUSTERED INDEX [IX_Proveedor_CuentasBancarias_ProveedorID]
    ON [dbo].[Proveedor_CuentasBancarias] (ProveedorID);
GO
CREATE NONCLUSTERED INDEX [IX_Proveedor_CuentasBancarias_ProveedorID_Activa]
    ON [dbo].[Proveedor_CuentasBancarias] (ProveedorID, Activa);
GO
CREATE NONCLUSTERED INDEX [IX_Proveedor_Documentos_ProveedorID]
    ON [dbo].[Proveedor_Documentos] (ProveedorID);
GO
CREATE NONCLUSTERED INDEX [IX_Proveedor_Documentos_ProveedorID_TipoDocumentoID]
    ON [dbo].[Proveedor_Documentos] (ProveedorID, TipoDocumentoID);
GO
CREATE NONCLUSTERED INDEX [IX_Proveedor_Documentos_ProveedorID_Vigente]
    ON [dbo].[Proveedor_Documentos] (ProveedorID, Vigente);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Cat_EstatusProveedor_Descripcion]
    ON [dbo].[Proveedor_EstatusProveedor] (Descripcion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Cat_EstatusSAT_Descripcion]
    ON [dbo].[Proveedor_EstatusSAT] (Descripcion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Cat_EstatusSincronizacion_Descripcion]
    ON [dbo].[Proveedor_EstatusSincronizacion] (Descripcion);
GO
CREATE NONCLUSTERED INDEX [IX_Proveedor_Evaluaciones_ProveedorID]
    ON [dbo].[Proveedor_Evaluaciones] (ProveedorID);
GO
CREATE NONCLUSTERED INDEX [IX_Proveedor_Evaluaciones_ProveedorID_Periodo]
    ON [dbo].[Proveedor_Evaluaciones] (ProveedorID, Periodo);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Proveedor_Evaluaciones_Proveedor_Periodo]
    ON [dbo].[Proveedor_Evaluaciones] (ProveedorID, Periodo);
GO
CREATE NONCLUSTERED INDEX [IX_Proveedor_Integracion_ProveedorID]
    ON [dbo].[Proveedor_Integracion] (ProveedorID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Proveedor_Integracion]
    ON [dbo].[Proveedor_Integracion] (SistemaID, ClaveExterna);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Cat_Monedas_ClaveMoneda]
    ON [dbo].[Proveedor_Monedas] (ClaveMoneda);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Cat_RiesgoProveedor_Descripcion]
    ON [dbo].[Proveedor_RiesgoProveedor] (Descripcion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Cat_RolUsuarioPortalProveedor_Descripcion]
    ON [dbo].[Proveedor_RolUsuarioPortal] (Descripcion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Cat_SistemasIntegracion_Descripcion]
    ON [dbo].[Proveedor_SistemasIntegracion] (Descripcion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Cat_TipoContacto_Descripcion]
    ON [dbo].[Proveedor_TipoContacto] (Descripcion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Cat_TipoDocumentoProveedor_Descripcion]
    ON [dbo].[Proveedor_TipoDocumento] (Descripcion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Cat_TipoProveedor_Descripcion]
    ON [dbo].[Proveedor_TipoProveedor] (Descripcion);
GO
CREATE NONCLUSTERED INDEX [IX_Proveedor_UsuariosPortal_Email]
    ON [dbo].[Proveedor_UsuariosPortal] (Email);
GO
CREATE NONCLUSTERED INDEX [IX_Proveedor_UsuariosPortal_ProveedorID]
    ON [dbo].[Proveedor_UsuariosPortal] (ProveedorID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Proveedor_UsuariosPortal_Email]
    ON [dbo].[Proveedor_UsuariosPortal] (Email);
GO
CREATE NONCLUSTERED INDEX [IX_RH_Ausencias_Colaborador_Fechas]
    ON [dbo].[RH_Ausencias] (ColaboradorID, FechaInicio, FechaFin);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_Areas_DepCodigo]
    ON [dbo].[RH_Cat_Areas] (DepartamentoID, CodigoArea);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_Areas_DepNombre]
    ON [dbo].[RH_Cat_Areas] (DepartamentoID, NombreArea);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_Beneficios_Codigo]
    ON [dbo].[RH_Cat_Beneficios] (CodigoBeneficio);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_Beneficios_Nombre]
    ON [dbo].[RH_Cat_Beneficios] (NombreBeneficio);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_ConceptosNomina_Codigo]
    ON [dbo].[RH_Cat_ConceptosNomina] (CodigoConcepto);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_ConceptosNomina_Nombre]
    ON [dbo].[RH_Cat_ConceptosNomina] (NombreConcepto);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_Departamentos_Codigo]
    ON [dbo].[RH_Cat_Departamentos] (CodigoDepartamento);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_Departamentos_Nombre]
    ON [dbo].[RH_Cat_Departamentos] (NombreDepartamento);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_EstatusPeriodoNomina_Codigo]
    ON [dbo].[RH_Cat_EstatusPeriodoNomina] (CodigoEstatus);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_EstatusPeriodoNomina_Descripcion]
    ON [dbo].[RH_Cat_EstatusPeriodoNomina] (Descripcion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_Jornadas_Codigo]
    ON [dbo].[RH_Cat_Jornadas] (CodigoJornada);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_Jornadas_Descripcion]
    ON [dbo].[RH_Cat_Jornadas] (Descripcion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_MotivosBaja_Codigo]
    ON [dbo].[RH_Cat_MotivosBaja] (CodigoMotivoBaja);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_MotivosBaja_Descripcion]
    ON [dbo].[RH_Cat_MotivosBaja] (Descripcion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_RegimenContratacion_ClaveSAT]
    ON [dbo].[RH_Cat_RegimenContratacion] (ClaveSAT);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_RegimenContratacion_Descripcion]
    ON [dbo].[RH_Cat_RegimenContratacion] (Descripcion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_SucursalesFiscal_Sucursal_RFC]
    ON [dbo].[RH_Cat_SucursalesFiscal] (SucursalID, RFC);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_TiposAusencia_Codigo]
    ON [dbo].[RH_Cat_TiposAusencia] (CodigoTipoAusencia);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_TiposAusencia_Descripcion]
    ON [dbo].[RH_Cat_TiposAusencia] (Descripcion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_TiposConceptoNomina_Codigo]
    ON [dbo].[RH_Cat_TiposConceptoNomina] (CodigoTipoConcepto);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_TiposConceptoNomina_Descripcion]
    ON [dbo].[RH_Cat_TiposConceptoNomina] (Descripcion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_TiposContrato_Codigo]
    ON [dbo].[RH_Cat_TiposContrato] (CodigoTipoContrato);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_TiposContrato_Descripcion]
    ON [dbo].[RH_Cat_TiposContrato] (Descripcion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_TiposPeriodoNomina_Codigo]
    ON [dbo].[RH_Cat_TiposPeriodoNomina] (CodigoTipoPeriodo);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_TiposPeriodoNomina_Descripcion]
    ON [dbo].[RH_Cat_TiposPeriodoNomina] (Descripcion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_Turnos_Codigo]
    ON [dbo].[RH_Cat_Turnos] (CodigoTurno);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Cat_Turnos_Nombre]
    ON [dbo].[RH_Cat_Turnos] (NombreTurno);
GO
CREATE UNIQUE NONCLUSTERED INDEX [IX_CURP_Unique_NotNull]
    ON [dbo].[RH_Colaboradores_Expediente] (CURP);
GO
CREATE UNIQUE NONCLUSTERED INDEX [IX_RFC_Unique_NotNull]
    ON [dbo].[RH_Colaboradores_Expediente] (RFC);
GO
CREATE NONCLUSTERED INDEX [IX_RH_Contratos_Colaborador_Vigente]
    ON [dbo].[RH_Contratos] (ColaboradorID, EsContratoVigente, FechaInicio);
GO
CREATE NONCLUSTERED INDEX [IX_RH_Finiquitos_Colaborador_FechaBaja]
    ON [dbo].[RH_Finiquitos] (ColaboradorID, FechaBaja);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_GruposNomina_Codigo]
    ON [dbo].[RH_GruposNomina] (CodigoGrupoNomina);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_GruposNomina_Nombre]
    ON [dbo].[RH_GruposNomina] (NombreGrupoNomina);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Tipo_ValorOrigen]
    ON [dbo].[RH_Homologacion_Equivalencias] (Tipo, Valor_Origen);
GO
CREATE NONCLUSTERED INDEX [IX_Staging_CURP]
    ON [dbo].[RH_Importacion_Staging] (CURP);
GO
CREATE NONCLUSTERED INDEX [IX_Staging_Estado]
    ON [dbo].[RH_Importacion_Staging] (Estado);
GO
CREATE NONCLUSTERED INDEX [IX_Staging_Fecha]
    ON [dbo].[RH_Importacion_Staging] (Fecha_Importacion);
GO
CREATE NONCLUSTERED INDEX [IX_Staging_RFC]
    ON [dbo].[RH_Importacion_Staging] (RFC);
GO
CREATE NONCLUSTERED INDEX [IX_RH_IMSS_Movimientos_Colaborador_Fecha]
    ON [dbo].[RH_IMSS_Movimientos] (ColaboradorID, FechaMovimiento);
GO
CREATE NONCLUSTERED INDEX [IX_RH_Incidencias_Nomina_Colaborador_Fecha]
    ON [dbo].[RH_Incidencias_Nomina] (ColaboradorID, Fecha_Incidencia);
GO
CREATE NONCLUSTERED INDEX [IX_RH_Incidencias_Nomina_Periodo_Autorizado]
    ON [dbo].[RH_Incidencias_Nomina] (PeriodoNominaID, Autorizado);
GO
CREATE NONCLUSTERED INDEX [IX_RH_Nomina_Colaborador]
    ON [dbo].[RH_Nomina] (ColaboradorID, PeriodoNominaID);
GO
CREATE NONCLUSTERED INDEX [IX_RH_Nomina_Periodo_Estatus]
    ON [dbo].[RH_Nomina] (PeriodoNominaID, EstatusNomina, Timbrado, Pagado);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Nomina_Periodo_Colaborador]
    ON [dbo].[RH_Nomina] (PeriodoNominaID, ColaboradorID);
GO
CREATE NONCLUSTERED INDEX [IX_RH_Nomina_Detalle_Nomina]
    ON [dbo].[RH_Nomina_Detalle] (NominaID, ConceptoNominaID);
GO
CREATE NONCLUSTERED INDEX [IX_RH_Nomina_Dispersion_Periodo_Estatus]
    ON [dbo].[RH_Nomina_Dispersion] (PeriodoNominaID, EstatusDispersion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Nomina_Recibos_Nomina]
    ON [dbo].[RH_Nomina_Recibos] (NominaID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Nomina_Recibos_UUID]
    ON [dbo].[RH_Nomina_Recibos] (UUID);
GO
CREATE NONCLUSTERED INDEX [IX_RH_Periodos_Nomina_Grupo_Fecha]
    ON [dbo].[RH_Periodos_Nomina] (GrupoNominaID, FechaInicio, FechaFin, FechaPago);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_RH_Periodos_Nomina_Grupo_Ejercicio_Periodo]
    ON [dbo].[RH_Periodos_Nomina] (GrupoNominaID, Ejercicio, NumeroPeriodo, EsAjuste);
GO
CREATE NONCLUSTERED INDEX [IX_RH_Prestamos_Colaborador_Estatus]
    ON [dbo].[RH_Prestamos] (ColaboradorID, Estatus);
GO
CREATE NONCLUSTERED INDEX [IX_RH_Vacaciones_Saldos_Colaborador_Ejercicio]
    ON [dbo].[RH_Vacaciones_Saldos] (ColaboradorID, Ejercicio, Activo);
GO
CREATE NONCLUSTERED INDEX [IX_Bitacora_Fecha]
    ON [dbo].[Scheduler_BitacoraJobs] (FechaAccion);
GO
CREATE NONCLUSTERED INDEX [IX_Bitacora_Job]
    ON [dbo].[Scheduler_BitacoraJobs] (JobName);
GO
CREATE NONCLUSTERED INDEX [IX_Bitacora_Run]
    ON [dbo].[Scheduler_BitacoraJobs] (RunID);
GO
CREATE NONCLUSTERED INDEX [IX_Inventarios_Estado]
    ON [dbo].[Scheduler_InventariosProcesados] (Estado);
GO
CREATE NONCLUSTERED INDEX [IX_Inventarios_Fecha]
    ON [dbo].[Scheduler_InventariosProcesados] (FechaDeteccion);
GO
CREATE NONCLUSTERED INDEX [IX_Inventarios_Server]
    ON [dbo].[Scheduler_InventariosProcesados] (ServerID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Inventario_Clave]
    ON [dbo].[Scheduler_InventariosProcesados] (SistemaOrigen, ServerID, SucursalID, AlmacenID, FolioInventario);
GO
CREATE NONCLUSTERED INDEX [IX_Pedidos_Estado]
    ON [dbo].[Scheduler_PedidosProcesados] (Estado);
GO
CREATE NONCLUSTERED INDEX [IX_Pedidos_Fecha]
    ON [dbo].[Scheduler_PedidosProcesados] (FechaDeteccion);
GO
CREATE NONCLUSTERED INDEX [IX_Pedidos_Server]
    ON [dbo].[Scheduler_PedidosProcesados] (ServerID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Pedido_Clave]
    ON [dbo].[Scheduler_PedidosProcesados] (SistemaOrigen, ServerID, EmpresaID, FolioPedido);
GO
CREATE NONCLUSTERED INDEX [IX_Servidores_Activo]
    ON [dbo].[Servidores_Conexiones] (activo);
GO
CREATE NONCLUSTERED INDEX [IX_Servidores_SystemType]
    ON [dbo].[Servidores_Conexiones] (system_type);
GO
CREATE NONCLUSTERED INDEX [IX_Servidores_Tipo]
    ON [dbo].[Servidores_Conexiones] (tipo_conexion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Servidor__C56AC887CD597F30]
    ON [dbo].[Servidores_Status] (ServerID);
GO
CREATE NONCLUSTERED INDEX [IX_Sesiones_Activa]
    ON [dbo].[Sesiones] (EstaActiva);
GO
CREATE NONCLUSTERED INDEX [IX_Sesiones_Expiracion]
    ON [dbo].[Sesiones] (FechaExpiracion);
GO
CREATE NONCLUSTERED INDEX [IX_Sesiones_Familia]
    ON [dbo].[Sesiones] (FamiliaTokenID);
GO
CREATE NONCLUSTERED INDEX [IX_Sesiones_Usuario]
    ON [dbo].[Sesiones] (UsuarioID);
GO
CREATE NONCLUSTERED INDEX [IX_SesionesHistorico_Fecha]
    ON [dbo].[SesionesHistorico] (FechaAccion);
GO
CREATE NONCLUSTERED INDEX [IX_SesionesHistorico_Sesion]
    ON [dbo].[SesionesHistorico] (SesionID);
GO
CREATE NONCLUSTERED INDEX [IX_SesionesHistorico_Usuario]
    ON [dbo].[SesionesHistorico] (UsuarioID);
GO
CREATE NONCLUSTERED INDEX [IX_SistemaCapacidades_Codigo]
    ON [dbo].[Sistema_Capacidades] (CodigoCapacidad);
GO
CREATE NONCLUSTERED INDEX [IX_SistemaCapacidades_SistemaTipo]
    ON [dbo].[Sistema_Capacidades] (SistemaTipoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_SistemaCapacidades_TipoCapacidad]
    ON [dbo].[Sistema_Capacidades] (SistemaTipoID, CodigoCapacidad);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Sistema_Catalogo_Codigo]
    ON [dbo].[Sistema_Catalogo] (Codigo);
GO
CREATE NONCLUSTERED INDEX [IX_Sistema_Empresas_Activo]
    ON [dbo].[Sistema_Empresas] (Activo);
GO
CREATE NONCLUSTERED INDEX [IX_Sistema_Empresas_Codigo]
    ON [dbo].[Sistema_Empresas] (CodigoEmpresa);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Sistema_Empresas_Codigo]
    ON [dbo].[Sistema_Empresas] (CodigoEmpresa);
GO
CREATE NONCLUSTERED INDEX [IX_EmpresasAlias_EmpresaID]
    ON [dbo].[Sistema_EmpresasAlias] (EmpresaID, Activo);
GO
CREATE UNIQUE NONCLUSTERED INDEX [IX_EmpresasAlias_Normalizado_Activo]
    ON [dbo].[Sistema_EmpresasAlias] (AliasNormalizado);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_EmpresaMongoUUID]
    ON [dbo].[Sistema_EmpresasMongoMap] (EmpresaMongoUUID);
GO
CREATE NONCLUSTERED INDEX [IX_EmpresasServidores_Empresa]
    ON [dbo].[Sistema_EmpresasServidores] (EmpresaID, Activo);
GO
CREATE NONCLUSTERED INDEX [IX_EmpresasServidores_Servidor]
    ON [dbo].[Sistema_EmpresasServidores] (ServidorID, Activo);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Horario_Unidad_Dia]
    ON [dbo].[Sistema_HorariosServicioUnidad] (unidad_negocio_id, dia_semana);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Sistema___06370DACDE10BF80]
    ON [dbo].[Sistema_Modulos] (Codigo);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Sistema___06370DAC6ACFB05F]
    ON [dbo].[Sistema_ModulosPermisos] (Codigo);
GO
CREATE NONCLUSTERED INDEX [IX_SistemaModulos_Modulo]
    ON [dbo].[Sistema_ModulosVisibilidad] (CodigoModulo);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_SistemaModulos_TipoModulo]
    ON [dbo].[Sistema_ModulosVisibilidad] (SistemaTipoID, CodigoModulo);
GO
CREATE NONCLUSTERED INDEX [IX_Sistema_Tipos_Activo]
    ON [dbo].[Sistema_Tipos] (Activo);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Sistema_Tipos_Codigo]
    ON [dbo].[Sistema_Tipos] (CodigoSistema);
GO
CREATE NONCLUSTERED INDEX [IX_SistemaTiposVariantes_Nombre]
    ON [dbo].[Sistema_TiposVariantes] (VarianteNombre);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_SistemaTiposVariantes_Nombre]
    ON [dbo].[Sistema_TiposVariantes] (VarianteNombre);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UK_TurnoOperativo_Unidad_Turno]
    ON [dbo].[Sistema_TurnosOperativosUnidad] (unidad_negocio_id, turno_codigo);
GO
CREATE NONCLUSTERED INDEX [IX_Sync_Control_Ejecuciones_Run]
    ON [dbo].[Sync_Control_Ejecuciones] (SyncRunID);
GO
CREATE NONCLUSTERED INDEX [IX_Sync_Control_Ejecuciones_Status]
    ON [dbo].[Sync_Control_Ejecuciones] (Status);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Sync_Con__60C7B3FB482BDEB7]
    ON [dbo].[Sync_Control_Ejecuciones] (SyncRunID);
GO
CREATE NONCLUSTERED INDEX [IX_SyncIndex_Customers_Email]
    ON [dbo].[Sync_Customers] (email);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_SyncImpuestos_Origen]
    ON [dbo].[Sync_Impuestos_Origen] (ServerID, CodigoImpuestoOrigen);
GO
CREATE NONCLUSTERED INDEX [IX_SyncIndex_Inventory_Warehouse]
    ON [dbo].[Sync_Inventory] (warehouse);
GO
CREATE NONCLUSTERED INDEX [IX_KPI_Mes_Anio]
    ON [dbo].[Sync_KPI_Ventas_Unidades] (Mes, Anio);
GO
CREATE NONCLUSTERED INDEX [IX_SyncIndex_Logs_Timestamp]
    ON [dbo].[Sync_Logs] (timestamp, service);
GO
CREATE NONCLUSTERED INDEX [IX_Sync_Productos_FamiliaID]
    ON [dbo].[Sync_Productos] (FamiliaID);
GO
CREATE NONCLUSTERED INDEX [IX_Sync_Productos_TieneReceta]
    ON [dbo].[Sync_Productos] (TieneReceta);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UK_Sync_Productos_Server_Codigo]
    ON [dbo].[Sync_Productos] (ServerID, CodigoFuente);
GO
CREATE NONCLUSTERED INDEX [IX_Sync_Elaborados_InsumoElaboradoID]
    ON [dbo].[Sync_Productos_Elaborados] (InsumoElaboradoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UK_Sync_Elaborados_Elab_Comp]
    ON [dbo].[Sync_Productos_Elaborados] (ServerID, InsumoElaboradoCodigoFuente, ComponenteCodigoFuente);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UK_Sync_Familias_Server_Codigo]
    ON [dbo].[Sync_Productos_Familias] (ServerID, CodigoFuente);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UK_Sync_Insumos_Server_Codigo]
    ON [dbo].[Sync_Productos_Insumos] (ServerID, CodigoFuente);
GO
CREATE NONCLUSTERED INDEX [IX_Sync_Recetas_InsumoID]
    ON [dbo].[Sync_Productos_Recetas] (InsumoID);
GO
CREATE NONCLUSTERED INDEX [IX_Sync_Recetas_ProductoID]
    ON [dbo].[Sync_Productos_Recetas] (ProductoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UK_Sync_Recetas_Prod_Comp]
    ON [dbo].[Sync_Productos_Recetas] (ServerID, ProductoCodigoFuente, ComponenteCodigoFuente);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UK_Sync_SubFamilias_Server_Codigo]
    ON [dbo].[Sync_Productos_SubFamilias] (ServerID, CodigoFuente);
GO
CREATE NONCLUSTERED INDEX [IX_Cache_Expires]
    ON [dbo].[Sync_Response_Cache] (ExpiresAt);
GO
CREATE NONCLUSTERED INDEX [IX_Cache_Hash]
    ON [dbo].[Sync_Response_Cache] (RequestHash, ServiceSource);
GO
CREATE NONCLUSTERED INDEX [IX_SyncIndex_Sales_Branch]
    ON [dbo].[Sync_Sales] (branch);
GO
CREATE NONCLUSTERED INDEX [IX_SyncIndex_Sales_CreatedAt]
    ON [dbo].[Sync_Sales] (created_at);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UX_TokenLedger_Date]
    ON [dbo].[Sync_Token_Ledger] (OperadorID, ConsuDate);
GO
CREATE NONCLUSTERED INDEX [IX_Sync_Ventas_Historicas_Fecha]
    ON [dbo].[Sync_Ventas_Historicas] (FechaOperacion);
GO
CREATE NONCLUSTERED INDEX [IX_Sync_Ventas_Historicas_Server]
    ON [dbo].[Sync_Ventas_Historicas] (ServerID, FechaOperacion);
GO
CREATE NONCLUSTERED INDEX [IX_Sync_Ventas_Historicas_SyncRun]
    ON [dbo].[Sync_Ventas_Historicas] (SyncRunID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Sync_Ventas_Historicas_Key]
    ON [dbo].[Sync_Ventas_Historicas] (ServerID, EmpresaID, FechaOperacion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Sync_Ventas_PorDiaSemana_Key]
    ON [dbo].[Sync_Ventas_PorDiaSemana] (ServerID, EmpresaID, FechaInicioPeriodo, FechaFinPeriodo, DiaSemana);
GO
CREATE NONCLUSTERED INDEX [IX_Sync_Ventas_PorHora_Fecha]
    ON [dbo].[Sync_Ventas_PorHora] (FechaOperacion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Sync_Ventas_PorHora_Key]
    ON [dbo].[Sync_Ventas_PorHora] (ServerID, EmpresaID, FechaOperacion, Hora);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Sync_Vti__823CA48718527AC9]
    ON [dbo].[Sync_Vtiger_Contactos] (VtigerID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Sync_Vti__823CA487BCE62382]
    ON [dbo].[Sync_Vtiger_Cuentas] (VtigerID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Sync_Vti__823CA4874941E80C]
    ON [dbo].[Sync_Vtiger_Leads] (VtigerID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Sync_Vti__823CA4872EB5194F]
    ON [dbo].[Sync_Vtiger_Oportunidades] (VtigerID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Sys_Usua__536C85E493EC703A]
    ON [dbo].[Sys_Usuarios] (Username);
GO
CREATE UNIQUE NONCLUSTERED INDEX [IX_ConfigContable_Empresa]
    ON [dbo].[Tablajeria_ConfigContable] (EmpresaID);
GO
CREATE NONCLUSTERED INDEX [IX_CosteoDetalle_CosteoID]
    ON [dbo].[Tablajeria_CosteoDetalle] (CosteoID);
GO
CREATE NONCLUSTERED INDEX [IX_Costeo_OrdenID]
    ON [dbo].[Tablajeria_CosteoProduccion] (OrdenID);
GO
CREATE NONCLUSTERED INDEX [IX_MovInv_OrdenID]
    ON [dbo].[Tablajeria_MovimientosInventario] (OrdenID);
GO
CREATE NONCLUSTERED INDEX [IX_Polizas_OrdenID]
    ON [dbo].[Tablajeria_PolizasContables] (OrdenID);
GO
CREATE NONCLUSTERED INDEX [IX_PolizaDetalle_PolizaID]
    ON [dbo].[Tablajeria_PolizasDetalle] (PolizaID);
GO
CREATE NONCLUSTERED INDEX [IX_Tareas_EstadoTarea]
    ON [dbo].[Tareas_Inventario] (EstadoTarea);
GO
CREATE NONCLUSTERED INDEX [IX_Tareas_FechaLimite]
    ON [dbo].[Tareas_Inventario] (FechaLimite);
GO
CREATE NONCLUSTERED INDEX [IX_Tareas_UsuarioAsignadoID]
    ON [dbo].[Tareas_Inventario] (UsuarioAsignadoID);
GO
CREATE NONCLUSTERED INDEX [IX_Tareas_WorkflowID]
    ON [dbo].[Tareas_Inventario] (WorkflowID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Tareas_I__5CD83670746D84B5]
    ON [dbo].[Tareas_Inventario] (TareaID);
GO
CREATE NONCLUSTERED INDEX [IX_Unidades_Codigo]
    ON [dbo].[Unidades_Negocio] (codigo);
GO
CREATE NONCLUSTERED INDEX [IX_Unidades_ServerID]
    ON [dbo].[Unidades_Negocio] (server_id);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Unidades_Server_Sucursal]
    ON [dbo].[Unidades_Negocio] (server_id, sucursal_origen_id);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Usuario_Acciones_CodigoAccion]
    ON [dbo].[Usuario_Acciones] (CodigoAccion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Usuario_Acciones_NombreAccion]
    ON [dbo].[Usuario_Acciones] (NombreAccion);
GO
CREATE NONCLUSTERED INDEX [IX_UsuarioAlmacenes_Servidor]
    ON [dbo].[Usuario_AlmacenesAsignacion] (ServidorID);
GO
CREATE NONCLUSTERED INDEX [IX_UsuarioAlmacenes_Usuario]
    ON [dbo].[Usuario_AlmacenesAsignacion] (UsuarioID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_UsuarioAlmacenes_Unique]
    ON [dbo].[Usuario_AlmacenesAsignacion] (UsuarioID, ServidorID, AlmacenCodigo);
GO
CREATE NONCLUSTERED INDEX [IX_Usuario_Autorizaciones_EntidadNombre_EntidadID]
    ON [dbo].[Usuario_Autorizaciones] (EntidadNombre, EntidadID);
GO
CREATE NONCLUSTERED INDEX [IX_Usuario_Autorizaciones_TipoAutorizacionID_Estatus]
    ON [dbo].[Usuario_Autorizaciones] (TipoAutorizacionID, EstatusAutorizacion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Usuario_Autorizaciones_FolioAutorizacion]
    ON [dbo].[Usuario_Autorizaciones] (FolioAutorizacion);
GO
CREATE NONCLUSTERED INDEX [IX_Usuario_AutorizacionesDetalle_AutorizacionID]
    ON [dbo].[Usuario_AutorizacionesDetalle] (AutorizacionID);
GO
CREATE NONCLUSTERED INDEX [IX_Usuario_Catalogo_Activo]
    ON [dbo].[Usuario_Catalogo] (Activo);
GO
CREATE NONCLUSTERED INDEX [IX_Usuario_Catalogo_Bloqueado]
    ON [dbo].[Usuario_Catalogo] (Bloqueado);
GO
CREATE UNIQUE NONCLUSTERED INDEX [IX_Usuario_MongoLegacyID]
    ON [dbo].[Usuario_Catalogo] (MongoLegacyID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [IX_Usuario_PublicUUID]
    ON [dbo].[Usuario_Catalogo] (PublicUUID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Usuario_Catalogo_CodigoUsuario]
    ON [dbo].[Usuario_Catalogo] (CodigoUsuario);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Usuario_Catalogo_Email]
    ON [dbo].[Usuario_Catalogo] (Email);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Usuario_Catalogo_Username]
    ON [dbo].[Usuario_Catalogo] (Username);
GO
CREATE NONCLUSTERED INDEX [IX_UsuarioEmpresasAsignacion_Activo]
    ON [dbo].[Usuario_EmpresasAsignacion] (Activo);
GO
CREATE NONCLUSTERED INDEX [IX_UsuarioEmpresasAsignacion_Empresa]
    ON [dbo].[Usuario_EmpresasAsignacion] (EmpresaID);
GO
CREATE NONCLUSTERED INDEX [IX_UsuarioEmpresasAsignacion_Usuario]
    ON [dbo].[Usuario_EmpresasAsignacion] (UsuarioID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_UsuarioEmpresas_Activo]
    ON [dbo].[Usuario_EmpresasAsignacion] (UsuarioID, EmpresaID, Activo);
GO
CREATE NONCLUSTERED INDEX [IX_Usuario_LogAccesos_UsuarioID_FechaEvento]
    ON [dbo].[Usuario_LogAccesos] (UsuarioID, FechaEvento);
GO
CREATE NONCLUSTERED INDEX [IX_Usuario_LogActividades_ModuloID_AccionID]
    ON [dbo].[Usuario_LogActividades] (ModuloID, AccionID);
GO
CREATE NONCLUSTERED INDEX [IX_Usuario_LogActividades_UsuarioID_FechaActividad]
    ON [dbo].[Usuario_LogActividades] (UsuarioID, FechaActividad);
GO
CREATE NONCLUSTERED INDEX [IX_LogRBAC_Fecha]
    ON [dbo].[Usuario_LogRBACVerificacion] (FechaVerificacion);
GO
CREATE NONCLUSTERED INDEX [IX_LogRBAC_Resultado]
    ON [dbo].[Usuario_LogRBACVerificacion] (Resultado, FechaVerificacion);
GO
CREATE NONCLUSTERED INDEX [IX_LogRBAC_Usuario]
    ON [dbo].[Usuario_LogRBACVerificacion] (UsuarioID);
GO
CREATE NONCLUSTERED INDEX [IX_Usuario_LogRecuperacion_Email]
    ON [dbo].[Usuario_LogRecuperacion] (Email, FechaEvento);
GO
CREATE NONCLUSTERED INDEX [IX_Usuario_LogRecuperacion_Evento]
    ON [dbo].[Usuario_LogRecuperacion] (Evento, FechaEvento);
GO
CREATE NONCLUSTERED INDEX [IX_Usuario_LogRecuperacion_Fecha]
    ON [dbo].[Usuario_LogRecuperacion] (FechaEvento);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_MigracionMongoTrace_Email]
    ON [dbo].[Usuario_MigracionMongoTrace] (Email);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_MigracionMongoTrace_MongoID]
    ON [dbo].[Usuario_MigracionMongoTrace] (MongoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Usuario_Modulos_CodigoModulo]
    ON [dbo].[Usuario_Modulos] (CodigoModulo);
GO
CREATE NONCLUSTERED INDEX [IX_Usuario_PermisosRolModulo_RolID_ModuloID]
    ON [dbo].[Usuario_PermisosRolModulo] (RolID, ModuloID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Usuario_PermisosRolModulo]
    ON [dbo].[Usuario_PermisosRolModulo] (RolID, ModuloID, AccionID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Usuario_PortalConfiguracion_Usuario]
    ON [dbo].[Usuario_PortalConfiguracion] (UsuarioID);
GO
CREATE NONCLUSTERED INDEX [IX_Usuario_RateLimitRecuperacion_Expiracion]
    ON [dbo].[Usuario_RateLimitRecuperacion] (VentanaExpiracion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Usuario_RateLimitRecuperacion_Llave]
    ON [dbo].[Usuario_RateLimitRecuperacion] (TipoLlave, ValorLlave);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Usuario_Roles_CodigoRol]
    ON [dbo].[Usuario_Roles] (CodigoRol);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Usuario_Roles_NombreRol]
    ON [dbo].[Usuario_Roles] (NombreRol);
GO
CREATE NONCLUSTERED INDEX [IX_Usuario_RolesAsignacion_RolID]
    ON [dbo].[Usuario_RolesAsignacion] (RolID);
GO
CREATE NONCLUSTERED INDEX [IX_Usuario_RolesAsignacion_UsuarioID]
    ON [dbo].[Usuario_RolesAsignacion] (UsuarioID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Usuario_RolesAsignacion]
    ON [dbo].[Usuario_RolesAsignacion] (UsuarioID, RolID, FechaInicio);
GO
CREATE NONCLUSTERED INDEX [IX_UsuarioServidores_Servidor]
    ON [dbo].[Usuario_ServidoresAsignacion] (ServidorID);
GO
CREATE NONCLUSTERED INDEX [IX_UsuarioServidores_Usuario]
    ON [dbo].[Usuario_ServidoresAsignacion] (UsuarioID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_UsuarioServidores_Unique]
    ON [dbo].[Usuario_ServidoresAsignacion] (UsuarioID, ServidorID);
GO
CREATE NONCLUSTERED INDEX [IX_Usuario_Sesiones_UsuarioID_FechaInicio]
    ON [dbo].[Usuario_Sesiones] (UsuarioID, FechaInicio);
GO
CREATE NONCLUSTERED INDEX [IX_UsuarioSucursales_Servidor]
    ON [dbo].[Usuario_SucursalesAsignacion] (ServidorID);
GO
CREATE NONCLUSTERED INDEX [IX_UsuarioSucursales_Usuario]
    ON [dbo].[Usuario_SucursalesAsignacion] (UsuarioID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_UsuarioSucursales_Unique]
    ON [dbo].[Usuario_SucursalesAsignacion] (UsuarioID, ServidorID, SucursalCodigo);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Usuario_TiposAutorizacion_Codigo]
    ON [dbo].[Usuario_TiposAutorizacion] (CodigoTipoAutorizacion);
GO
CREATE NONCLUSTERED INDEX [IX_TokensRecuperacion_Email]
    ON [dbo].[Usuario_TokensRecuperacion] (Email);
GO
CREATE NONCLUSTERED INDEX [IX_TokensRecuperacion_Expiracion]
    ON [dbo].[Usuario_TokensRecuperacion] (FechaExpiracion);
GO
CREATE NONCLUSTERED INDEX [IX_TokensRecuperacion_Usuario]
    ON [dbo].[Usuario_TokensRecuperacion] (UsuarioID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_TokensRecuperacion_Hash]
    ON [dbo].[Usuario_TokensRecuperacion] (TokenHash);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Venta_CondicionesPago_Codigo]
    ON [dbo].[Venta_CondicionesPago] (CodigoCondicionPago);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Cotizaciones_ClienteID_FechaCotizacion]
    ON [dbo].[Venta_Cotizaciones] (ClienteID, FechaCotizacion);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Cotizaciones_CRM_Cuenta]
    ON [dbo].[Venta_Cotizaciones] (CRM_CuentaID);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Cotizaciones_CRM_Oportunidad]
    ON [dbo].[Venta_Cotizaciones] (CRM_OportunidadID);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Cotizaciones_EstatusCotizacionID]
    ON [dbo].[Venta_Cotizaciones] (EstatusCotizacionID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Venta_Cotizaciones_FolioCotizacion]
    ON [dbo].[Venta_Cotizaciones] (FolioCotizacion);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_CotizacionesDetalle_CotizacionID]
    ON [dbo].[Venta_CotizacionesDetalle] (CotizacionID);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_CotizacionesDetalle_ProductoID]
    ON [dbo].[Venta_CotizacionesDetalle] (ProductoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Venta_CotizacionesDetalle_Cotizacion_Renglon]
    ON [dbo].[Venta_CotizacionesDetalle] (CotizacionID, Renglon);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Venta_CotizacionesEstatus_Descripcion]
    ON [dbo].[Venta_CotizacionesEstatus] (Descripcion);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Detalle_ProductoID]
    ON [dbo].[Venta_Detalle] (ProductoID);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Detalle_VentaID]
    ON [dbo].[Venta_Detalle] (VentaID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Venta_Detalle_Venta_Renglon]
    ON [dbo].[Venta_Detalle] (VentaID, Renglon);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Encabezado_ClienteID_FechaVenta]
    ON [dbo].[Venta_Encabezado] (ClienteID, FechaVenta);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Encabezado_EstatusVentaID]
    ON [dbo].[Venta_Encabezado] (EstatusVentaID);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Encabezado_FechaVenta]
    ON [dbo].[Venta_Encabezado] (FechaVenta);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Venta_Encabezado_Folio]
    ON [dbo].[Venta_Encabezado] (Folio);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Venta_FormaPago_Descripcion]
    ON [dbo].[Venta_FormaPago] (Descripcion);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Venta_ListasPrecios_Codigo]
    ON [dbo].[Venta_ListasPrecios] (CodigoListaPrecio);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Venta_ListasPrecios_Nombre]
    ON [dbo].[Venta_ListasPrecios] (NombreListaPrecio);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_ListasPreciosDetalle_ListaPrecioID]
    ON [dbo].[Venta_ListasPreciosDetalle] (ListaPrecioID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Venta_ListasPreciosDetalle]
    ON [dbo].[Venta_ListasPreciosDetalle] (ListaPrecioID, ProductoID, PresentacionProductoID);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Pagos_VentaID]
    ON [dbo].[Venta_Pagos] (VentaID);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Pedidos_ClienteID_FechaPedido]
    ON [dbo].[Venta_Pedidos] (ClienteID, FechaPedido);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Pedidos_CotizacionID]
    ON [dbo].[Venta_Pedidos] (CotizacionID);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Pedidos_CRM_Cuenta]
    ON [dbo].[Venta_Pedidos] (CRM_CuentaID);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Pedidos_CRM_Oportunidad]
    ON [dbo].[Venta_Pedidos] (CRM_OportunidadID);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Pedidos_EstatusPedidoID]
    ON [dbo].[Venta_Pedidos] (EstatusPedidoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Venta_Pedidos_FolioPedido]
    ON [dbo].[Venta_Pedidos] (FolioPedido);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_PedidosDetalle_PedidoID]
    ON [dbo].[Venta_PedidosDetalle] (PedidoID);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_PedidosDetalle_ProductoID]
    ON [dbo].[Venta_PedidosDetalle] (ProductoID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Venta_PedidosDetalle_Pedido_Renglon]
    ON [dbo].[Venta_PedidosDetalle] (PedidoID, Renglon);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Venta_PedidosEstatus_Descripcion]
    ON [dbo].[Venta_PedidosEstatus] (Descripcion);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Remisiones_Cliente]
    ON [dbo].[Venta_Remisiones] (ClienteID);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Remisiones_Empresa]
    ON [dbo].[Venta_Remisiones] (EmpresaID);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Remisiones_Estatus]
    ON [dbo].[Venta_Remisiones] (EstatusRemisionID);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Remisiones_Fecha]
    ON [dbo].[Venta_Remisiones] (FechaRemision);
GO
CREATE UNIQUE NONCLUSTERED INDEX [IX_Venta_Remisiones_Folio]
    ON [dbo].[Venta_Remisiones] (EmpresaID, FolioRemision);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_Remisiones_Pedido]
    ON [dbo].[Venta_Remisiones] (PedidoID);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_RemisionesDetalle_Producto]
    ON [dbo].[Venta_RemisionesDetalle] (ProductoID);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_RemisionesDetalle_Remision]
    ON [dbo].[Venta_RemisionesDetalle] (RemisionID);
GO
CREATE NONCLUSTERED INDEX [IX_Venta_RemisionesHistorial_Remision]
    ON [dbo].[Venta_RemisionesHistorial] (RemisionID);
GO
CREATE NONCLUSTERED INDEX [IX_WfDec_FechaDecision]
    ON [dbo].[Workflow_DecisionesAuditoria] (FechaDecision);
GO
CREATE NONCLUSTERED INDEX [IX_WfDec_WorkflowID]
    ON [dbo].[Workflow_DecisionesAuditoria] (WorkflowID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_WfDec_DecisionID]
    ON [dbo].[Workflow_DecisionesAuditoria] (DecisionID);
GO
CREATE NONCLUSTERED INDEX [IX_Detalle_CodigoProducto]
    ON [dbo].[Workflow_DetalleDiferencias] (CodigoProducto);
GO
CREATE NONCLUSTERED INDEX [IX_Detalle_WorkflowID]
    ON [dbo].[Workflow_DetalleDiferencias] (WorkflowID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Workflow__6E19D6FBC520DF5A]
    ON [dbo].[Workflow_DetalleDiferencias] (DetalleID);
GO
CREATE NONCLUSTERED INDEX [IX_Workflow_Estado]
    ON [dbo].[Workflow_Inventarios] (Estado);
GO
CREATE NONCLUSTERED INDEX [IX_Workflow_FechaCreacion]
    ON [dbo].[Workflow_Inventarios] (FechaCreacion);
GO
CREATE NONCLUSTERED INDEX [IX_Workflow_ServerID]
    ON [dbo].[Workflow_Inventarios] (ServerID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ__Workflow__5704A64B307FFCD3]
    ON [dbo].[Workflow_Inventarios] (WorkflowID);
GO
CREATE NONCLUSTERED INDEX [IX_WfJust_DetalleID]
    ON [dbo].[Workflow_Justificaciones] (DetalleID);
GO
CREATE NONCLUSTERED INDEX [IX_WfJust_Estado]
    ON [dbo].[Workflow_Justificaciones] (Estado);
GO
CREATE NONCLUSTERED INDEX [IX_WfJust_WorkflowID]
    ON [dbo].[Workflow_Justificaciones] (WorkflowID);
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_WfJust_JustificacionID]
    ON [dbo].[Workflow_Justificaciones] (JustificacionID);
GO