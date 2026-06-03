-- EDARSAHUB Database Schema Export
-- Generated: 2026-06-03T06:44:36.450710
-- Tables: 422

USE EDARSAHUB;
GO

-- =================================================
-- Tabla: ActivoFijo_ActivoMedidores
-- Exportado: 2026-06-03T06:44:36.498087
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_ActivoMedidores', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_ActivoMedidores;
GO

CREATE TABLE dbo.ActivoFijo_ActivoMedidores (
    [ActivoMedidorID] BIGINT NOT NULL,
    [ActivoID] BIGINT NOT NULL,
    [MedidorID] INT NOT NULL,
    [ValorActual] DECIMAL(18,4) NULL,
    [FechaUltimaLectura] DATETIME2 NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

CREATE INDEX [IX_AF_ActivoMedidores_ActivoID] ON dbo.ActivoFijo_ActivoMedidores (ActivoID);
ALTER TABLE dbo.ActivoFijo_ActivoMedidores ADD CONSTRAINT [PK_AF_ActivoMedidores] PRIMARY KEY (ActivoMedidorID);
CREATE UNIQUE INDEX [UQ_AF_ActivoMedidores] ON dbo.ActivoFijo_ActivoMedidores (ActivoID, MedidorID);
GO

-- =================================================
-- Tabla: ActivoFijo_Activos
-- Exportado: 2026-06-03T06:44:36.704167
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_Activos', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_Activos;
GO

CREATE TABLE dbo.ActivoFijo_Activos (
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
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

CREATE INDEX [IX_AF_Activos_ActivoPadreID] ON dbo.ActivoFijo_Activos (ActivoPadreID);
CREATE INDEX [IX_AF_Activos_ClaseActivoID] ON dbo.ActivoFijo_Activos (ClaseActivoID);
CREATE INDEX [IX_AF_Activos_EstatusActivoID] ON dbo.ActivoFijo_Activos (EstatusActivoID);
CREATE INDEX [IX_AF_Activos_NumeroSerie] ON dbo.ActivoFijo_Activos (NumeroSerie);
CREATE INDEX [IX_AF_Activos_ProveedorID] ON dbo.ActivoFijo_Activos (ProveedorID);
CREATE INDEX [IX_AF_Activos_Sucursal_Area] ON dbo.ActivoFijo_Activos (Sucursal, AreaRestaurante);
CREATE INDEX [IX_AF_Activos_UbicacionActualID] ON dbo.ActivoFijo_Activos (UbicacionActualID);
ALTER TABLE dbo.ActivoFijo_Activos ADD CONSTRAINT [PK_AF_Activos] PRIMARY KEY (ActivoID);
CREATE UNIQUE INDEX [UQ_AF_Activos_CodigoActivo] ON dbo.ActivoFijo_Activos (CodigoActivo);
CREATE UNIQUE INDEX [UQ_AF_Activos_EtiquetaID] ON dbo.ActivoFijo_Activos (EtiquetaID);
GO

-- =================================================
-- Tabla: ActivoFijo_ActivosLibros
-- Exportado: 2026-06-03T06:44:36.909844
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_ActivosLibros', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_ActivosLibros;
GO

CREATE TABLE dbo.ActivoFijo_ActivosLibros (
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
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

CREATE INDEX [IX_AF_ActivosLibros_ActivoID] ON dbo.ActivoFijo_ActivosLibros (ActivoID);
ALTER TABLE dbo.ActivoFijo_ActivosLibros ADD CONSTRAINT [PK_AF_ActivosLibros] PRIMARY KEY (ActivoLibroID);
CREATE UNIQUE INDEX [UQ_AF_ActivosLibros] ON dbo.ActivoFijo_ActivosLibros (ActivoID, LibroDepreciacionID);
GO

-- =================================================
-- Tabla: ActivoFijo_Alertas
-- Exportado: 2026-06-03T06:44:37.114847
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_Alertas', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_Alertas;
GO

CREATE TABLE dbo.ActivoFijo_Alertas (
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
    [CreatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_AF_Alertas_ActivoID_Leida] ON dbo.ActivoFijo_Alertas (ActivoID, Leida);
CREATE INDEX [IX_AF_Alertas_TipoAlerta_Prioridad] ON dbo.ActivoFijo_Alertas (TipoAlerta, Prioridad);
ALTER TABLE dbo.ActivoFijo_Alertas ADD CONSTRAINT [PK_AF_Alertas] PRIMARY KEY (AlertaID);
GO

-- =================================================
-- Tabla: ActivoFijo_Archivos
-- Exportado: 2026-06-03T06:44:37.320072
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_Archivos', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_Archivos;
GO

CREATE TABLE dbo.ActivoFijo_Archivos (
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
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

CREATE INDEX [IX_AF_Archivos_EntidadTipo_EntidadID] ON dbo.ActivoFijo_Archivos (EntidadTipo, EntidadID);
ALTER TABLE dbo.ActivoFijo_Archivos ADD CONSTRAINT [PK_AF_Archivos] PRIMARY KEY (ArchivoID);
GO

-- =================================================
-- Tabla: ActivoFijo_Autorizaciones
-- Exportado: 2026-06-03T06:44:37.526339
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_Autorizaciones', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_Autorizaciones;
GO

CREATE TABLE dbo.ActivoFijo_Autorizaciones (
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
    [CreatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_AF_Autorizaciones_ActivoID] ON dbo.ActivoFijo_Autorizaciones (ActivoID);
CREATE INDEX [IX_AF_Autorizaciones_EstadoAutorizacion] ON dbo.ActivoFijo_Autorizaciones (EstadoAutorizacion);
CREATE INDEX [IX_AF_Autorizaciones_OTID] ON dbo.ActivoFijo_Autorizaciones (OrdenTrabajoID);
ALTER TABLE dbo.ActivoFijo_Autorizaciones ADD CONSTRAINT [PK_AF_Autorizaciones] PRIMARY KEY (AutorizacionID);
CREATE UNIQUE INDEX [UQ_AF_Autorizaciones_Folio] ON dbo.ActivoFijo_Autorizaciones (FolioAutorizacion);
GO

-- =================================================
-- Tabla: ActivoFijo_BajasActivos
-- Exportado: 2026-06-03T06:44:37.731181
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_BajasActivos', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_BajasActivos;
GO

CREATE TABLE dbo.ActivoFijo_BajasActivos (
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
    [CreatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_AF_BajasActivos_FechaBaja] ON dbo.ActivoFijo_BajasActivos (FechaBaja);
ALTER TABLE dbo.ActivoFijo_BajasActivos ADD CONSTRAINT [PK_AF_BajasActivos] PRIMARY KEY (BajaActivoID);
CREATE UNIQUE INDEX [UQ_AF_BajasActivos_Activo] ON dbo.ActivoFijo_BajasActivos (ActivoID);
GO

-- =================================================
-- Tabla: ActivoFijo_ClaseActivo
-- Exportado: 2026-06-03T06:44:37.936205
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_ClaseActivo', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_ClaseActivo;
GO

CREATE TABLE dbo.ActivoFijo_ClaseActivo (
    [ClaseActivoID] SMALLINT NOT NULL,
    [Nombre] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [TipoActivoID] SMALLINT NULL,
    [Capitalizable] BIT NOT NULL DEFAULT ((1)),
    [RequiereSerie] BIT NOT NULL DEFAULT ((0)),
    [RequiereEtiqueta] BIT NOT NULL DEFAULT ((0)),
    [RequiereMantenimiento] BIT NOT NULL DEFAULT ((0)),
    [RequiereDepreciacion] BIT NOT NULL DEFAULT ((1)),
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.ActivoFijo_ClaseActivo ADD CONSTRAINT [PK_AF_ClaseActivo] PRIMARY KEY (ClaseActivoID);
CREATE UNIQUE INDEX [UQ_AF_ClaseActivo_Nombre] ON dbo.ActivoFijo_ClaseActivo (Nombre);
GO

-- =================================================
-- Tabla: ActivoFijo_Cotizaciones
-- Exportado: 2026-06-03T06:44:38.173621
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_Cotizaciones', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_Cotizaciones;
GO

CREATE TABLE dbo.ActivoFijo_Cotizaciones (
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
    [CreatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_AF_Cotizaciones_ActivoID] ON dbo.ActivoFijo_Cotizaciones (ActivoID);
CREATE INDEX [IX_AF_Cotizaciones_EstadoCotizacion] ON dbo.ActivoFijo_Cotizaciones (EstadoCotizacion);
CREATE INDEX [IX_AF_Cotizaciones_OrdenTrabajoID] ON dbo.ActivoFijo_Cotizaciones (OrdenTrabajoID);
CREATE INDEX [IX_AF_Cotizaciones_ProveedorID] ON dbo.ActivoFijo_Cotizaciones (ProveedorID);
ALTER TABLE dbo.ActivoFijo_Cotizaciones ADD CONSTRAINT [PK_AF_Cotizaciones] PRIMARY KEY (CotizacionID);
CREATE UNIQUE INDEX [UQ_AF_Cotizaciones_Folio] ON dbo.ActivoFijo_Cotizaciones (FolioCotizacion);
GO

-- =================================================
-- Tabla: ActivoFijo_DepreciacionMovimientos
-- Exportado: 2026-06-03T06:44:38.380543
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_DepreciacionMovimientos', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_DepreciacionMovimientos;
GO

CREATE TABLE dbo.ActivoFijo_DepreciacionMovimientos (
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
    [CreatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_AF_DepreciacionMovimientos_ActivoLibroID_Periodo] ON dbo.ActivoFijo_DepreciacionMovimientos (ActivoLibroID, Periodo);
ALTER TABLE dbo.ActivoFijo_DepreciacionMovimientos ADD CONSTRAINT [PK_AF_DepreciacionMovimientos] PRIMARY KEY (DepreciacionMovimientoID);
CREATE UNIQUE INDEX [UQ_AF_DepreciacionMovimientos] ON dbo.ActivoFijo_DepreciacionMovimientos (ActivoLibroID, Periodo, TipoMovimiento);
GO

-- =================================================
-- Tabla: ActivoFijo_EstadoUsoActivo
-- Exportado: 2026-06-03T06:44:38.587094
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_EstadoUsoActivo', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_EstadoUsoActivo;
GO

CREATE TABLE dbo.ActivoFijo_EstadoUsoActivo (
    [EstadoUsoActivoID] TINYINT NOT NULL,
    [Nombre] VARCHAR(40) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.ActivoFijo_EstadoUsoActivo ADD CONSTRAINT [PK_AF_EstadoUsoActivo] PRIMARY KEY (EstadoUsoActivoID);
CREATE UNIQUE INDEX [UQ_AF_EstadoUsoActivo_Nombre] ON dbo.ActivoFijo_EstadoUsoActivo (Nombre);
GO

-- =================================================
-- Tabla: ActivoFijo_EstatusActivo
-- Exportado: 2026-06-03T06:44:38.824963
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_EstatusActivo', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_EstatusActivo;
GO

CREATE TABLE dbo.ActivoFijo_EstatusActivo (
    [EstatusActivoID] TINYINT NOT NULL,
    [Nombre] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.ActivoFijo_EstatusActivo ADD CONSTRAINT [PK_AF_EstatusActivo] PRIMARY KEY (EstatusActivoID);
CREATE UNIQUE INDEX [UQ_AF_EstatusActivo_Nombre] ON dbo.ActivoFijo_EstatusActivo (Nombre);
GO

-- =================================================
-- Tabla: ActivoFijo_EstatusOT
-- Exportado: 2026-06-03T06:44:39.061539
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_EstatusOT', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_EstatusOT;
GO

CREATE TABLE dbo.ActivoFijo_EstatusOT (
    [EstatusOTID] TINYINT NOT NULL,
    [Nombre] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.ActivoFijo_EstatusOT ADD CONSTRAINT [PK_AF_EstatusOT] PRIMARY KEY (EstatusOTID);
CREATE UNIQUE INDEX [UQ_AF_EstatusOT_Nombre] ON dbo.ActivoFijo_EstatusOT (Nombre);
GO

-- =================================================
-- Tabla: ActivoFijo_HistorialAsignaciones
-- Exportado: 2026-06-03T06:44:39.298892
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_HistorialAsignaciones', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_HistorialAsignaciones;
GO

CREATE TABLE dbo.ActivoFijo_HistorialAsignaciones (
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
    [CreatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_AF_HistorialAsignaciones_ActivoID_FechaInicio] ON dbo.ActivoFijo_HistorialAsignaciones (ActivoID, FechaInicio);
ALTER TABLE dbo.ActivoFijo_HistorialAsignaciones ADD CONSTRAINT [PK_AF_HistorialAsignaciones] PRIMARY KEY (HistorialAsignacionID);
GO

-- =================================================
-- Tabla: ActivoFijo_LecturasMedidor
-- Exportado: 2026-06-03T06:44:39.504562
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_LecturasMedidor', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_LecturasMedidor;
GO

CREATE TABLE dbo.ActivoFijo_LecturasMedidor (
    [LecturaMedidorID] BIGINT NOT NULL,
    [ActivoMedidorID] BIGINT NOT NULL,
    [FechaLectura] DATETIME2 NOT NULL,
    [ValorLectura] DECIMAL(18,4) NOT NULL,
    [OrigenLectura] VARCHAR(20) NOT NULL DEFAULT ('MANUAL'),
    [Observaciones] VARCHAR(500) NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_AF_LecturasMedidor_ActivoMedidorID_FechaLectura] ON dbo.ActivoFijo_LecturasMedidor (ActivoMedidorID, FechaLectura);
ALTER TABLE dbo.ActivoFijo_LecturasMedidor ADD CONSTRAINT [PK_AF_LecturasMedidor] PRIMARY KEY (LecturaMedidorID);
GO

-- =================================================
-- Tabla: ActivoFijo_LibrosDepreciacion
-- Exportado: 2026-06-03T06:44:39.708549
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_LibrosDepreciacion', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_LibrosDepreciacion;
GO

CREATE TABLE dbo.ActivoFijo_LibrosDepreciacion (
    [LibroDepreciacionID] SMALLINT NOT NULL,
    [CodigoLibro] VARCHAR(20) NOT NULL,
    [NombreLibro] VARCHAR(100) NOT NULL,
    [TipoLibro] VARCHAR(20) NOT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.ActivoFijo_LibrosDepreciacion ADD CONSTRAINT [PK_AF_LibrosDepreciacion] PRIMARY KEY (LibroDepreciacionID);
CREATE UNIQUE INDEX [UQ_AF_LibrosDepreciacion_Codigo] ON dbo.ActivoFijo_LibrosDepreciacion (CodigoLibro);
GO

-- =================================================
-- Tabla: ActivoFijo_Medidores
-- Exportado: 2026-06-03T06:44:39.944796
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_Medidores', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_Medidores;
GO

CREATE TABLE dbo.ActivoFijo_Medidores (
    [MedidorID] INT NOT NULL,
    [CodigoMedidor] VARCHAR(30) NOT NULL,
    [NombreMedidor] VARCHAR(100) NOT NULL,
    [TipoMedidorID] TINYINT NOT NULL,
    [UnidadMedida] VARCHAR(30) NULL,
    [TieneLimiteAdvertencia] BIT NOT NULL DEFAULT ((0)),
    [LimiteAdvertencia] DECIMAL(18,4) NULL,
    [TieneLimiteCritico] BIT NOT NULL DEFAULT ((0)),
    [LimiteCritico] DECIMAL(18,4) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.ActivoFijo_Medidores ADD CONSTRAINT [PK_AF_Medidores] PRIMARY KEY (MedidorID);
CREATE UNIQUE INDEX [UQ_AF_Medidores_Codigo] ON dbo.ActivoFijo_Medidores (CodigoMedidor);
GO

-- =================================================
-- Tabla: ActivoFijo_MetodosDepreciacion
-- Exportado: 2026-06-03T06:44:40.149936
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_MetodosDepreciacion', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_MetodosDepreciacion;
GO

CREATE TABLE dbo.ActivoFijo_MetodosDepreciacion (
    [MetodoDepreciacionID] SMALLINT NOT NULL,
    [CodigoMetodo] VARCHAR(20) NOT NULL,
    [NombreMetodo] VARCHAR(100) NOT NULL,
    [TipoCalculo] VARCHAR(30) NOT NULL,
    [PermiteValorResidual] BIT NOT NULL DEFAULT ((1)),
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.ActivoFijo_MetodosDepreciacion ADD CONSTRAINT [PK_AF_MetodosDepreciacion] PRIMARY KEY (MetodoDepreciacionID);
CREATE UNIQUE INDEX [UQ_AF_MetodosDepreciacion_Codigo] ON dbo.ActivoFijo_MetodosDepreciacion (CodigoMetodo);
GO

-- =================================================
-- Tabla: ActivoFijo_MovimientosActivo
-- Exportado: 2026-06-03T06:44:40.387140
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_MovimientosActivo', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_MovimientosActivo;
GO

CREATE TABLE dbo.ActivoFijo_MovimientosActivo (
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
    [CreatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_AF_MovimientosActivo_ActivoID_FechaMovimiento] ON dbo.ActivoFijo_MovimientosActivo (ActivoID, FechaMovimiento);
ALTER TABLE dbo.ActivoFijo_MovimientosActivo ADD CONSTRAINT [PK_AF_MovimientosActivo] PRIMARY KEY (MovimientoActivoID);
GO

-- =================================================
-- Tabla: ActivoFijo_OrdenesTrabajo
-- Exportado: 2026-06-03T06:44:40.592339
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_OrdenesTrabajo', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_OrdenesTrabajo;
GO

CREATE TABLE dbo.ActivoFijo_OrdenesTrabajo (
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
    [ModifiedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_AF_OrdenesTrabajo_ActivoID] ON dbo.ActivoFijo_OrdenesTrabajo (ActivoID);
CREATE INDEX [IX_AF_OrdenesTrabajo_EstatusOTID_FechaProgramada] ON dbo.ActivoFijo_OrdenesTrabajo (EstatusOTID, FechaProgramada);
CREATE INDEX [IX_AF_OrdenesTrabajo_PlanMantenimientoID] ON dbo.ActivoFijo_OrdenesTrabajo (PlanMantenimientoID);
CREATE INDEX [IX_AF_OrdenesTrabajo_ProveedorID] ON dbo.ActivoFijo_OrdenesTrabajo (ProveedorID);
ALTER TABLE dbo.ActivoFijo_OrdenesTrabajo ADD CONSTRAINT [PK_AF_OrdenesTrabajo] PRIMARY KEY (OrdenTrabajoID);
CREATE UNIQUE INDEX [UQ_AF_OrdenesTrabajo_Folio] ON dbo.ActivoFijo_OrdenesTrabajo (FolioOT);
GO

-- =================================================
-- Tabla: ActivoFijo_OrdenTrabajoCostos
-- Exportado: 2026-06-03T06:44:40.797581
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_OrdenTrabajoCostos', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_OrdenTrabajoCostos;
GO

CREATE TABLE dbo.ActivoFijo_OrdenTrabajoCostos (
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
    [CreatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_AF_OrdenTrabajoCostos_OrdenTrabajoID] ON dbo.ActivoFijo_OrdenTrabajoCostos (OrdenTrabajoID);
ALTER TABLE dbo.ActivoFijo_OrdenTrabajoCostos ADD CONSTRAINT [PK_AF_OrdenTrabajoCostos] PRIMARY KEY (OrdenTrabajoCostoID);
GO

-- =================================================
-- Tabla: ActivoFijo_PlanesMantenimiento
-- Exportado: 2026-06-03T06:44:41.001670
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_PlanesMantenimiento', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_PlanesMantenimiento;
GO

CREATE TABLE dbo.ActivoFijo_PlanesMantenimiento (
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
    [ModifiedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_AF_PlanesMantenimiento_ActivoID] ON dbo.ActivoFijo_PlanesMantenimiento (ActivoID);
CREATE INDEX [IX_AF_PlanesMantenimiento_ClaseActivoID] ON dbo.ActivoFijo_PlanesMantenimiento (ClaseActivoID);
CREATE INDEX [IX_AF_PlanesMantenimiento_ProximoVencimiento] ON dbo.ActivoFijo_PlanesMantenimiento (ProximoVencimiento);
CREATE INDEX [IX_AF_PlanesMantenimiento_UbicacionID] ON dbo.ActivoFijo_PlanesMantenimiento (UbicacionID);
ALTER TABLE dbo.ActivoFijo_PlanesMantenimiento ADD CONSTRAINT [PK_AF_PlanesMantenimiento] PRIMARY KEY (PlanMantenimientoID);
CREATE UNIQUE INDEX [UQ_AF_PlanesMantenimiento_Codigo] ON dbo.ActivoFijo_PlanesMantenimiento (CodigoPlan);
GO

-- =================================================
-- Tabla: ActivoFijo_PrioridadOT
-- Exportado: 2026-06-03T06:44:41.207080
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_PrioridadOT', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_PrioridadOT;
GO

CREATE TABLE dbo.ActivoFijo_PrioridadOT (
    [PrioridadOTID] TINYINT NOT NULL,
    [Nombre] VARCHAR(20) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.ActivoFijo_PrioridadOT ADD CONSTRAINT [PK_AF_PrioridadOT] PRIMARY KEY (PrioridadOTID);
CREATE UNIQUE INDEX [UQ_AF_PrioridadOT_Nombre] ON dbo.ActivoFijo_PrioridadOT (Nombre);
GO

-- =================================================
-- Tabla: ActivoFijo_ReemplazosActivos
-- Exportado: 2026-06-03T06:44:41.444202
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_ReemplazosActivos', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_ReemplazosActivos;
GO

CREATE TABLE dbo.ActivoFijo_ReemplazosActivos (
    [ReemplazoActivoID] BIGINT NOT NULL,
    [ActivoAnteriorID] BIGINT NOT NULL,
    [ActivoNuevoID] BIGINT NOT NULL,
    [FechaReemplazo] DATE NOT NULL,
    [Motivo] VARCHAR(1000) NOT NULL,
    [CostoTotal] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [AutorizacionID] BIGINT NULL,
    [Notas] VARCHAR(2000) NULL,
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_AF_ReemplazosActivos_ActivoAnteriorID] ON dbo.ActivoFijo_ReemplazosActivos (ActivoAnteriorID);
ALTER TABLE dbo.ActivoFijo_ReemplazosActivos ADD CONSTRAINT [PK_AF_ReemplazosActivos] PRIMARY KEY (ReemplazoActivoID);
CREATE UNIQUE INDEX [UQ_AF_ReemplazosActivos] ON dbo.ActivoFijo_ReemplazosActivos (ActivoAnteriorID, ActivoNuevoID);
GO

-- =================================================
-- Tabla: ActivoFijo_ReglasClaseLibro
-- Exportado: 2026-06-03T06:44:41.648744
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_ReglasClaseLibro', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_ReglasClaseLibro;
GO

CREATE TABLE dbo.ActivoFijo_ReglasClaseLibro (
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
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.ActivoFijo_ReglasClaseLibro ADD CONSTRAINT [PK_AF_ReglasClaseLibro] PRIMARY KEY (ReglaClaseLibroID);
CREATE UNIQUE INDEX [UQ_AF_ReglasClaseLibro] ON dbo.ActivoFijo_ReglasClaseLibro (ClaseActivoID, LibroDepreciacionID);
GO

-- =================================================
-- Tabla: ActivoFijo_TipoActivo
-- Exportado: 2026-06-03T06:44:41.885278
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_TipoActivo', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_TipoActivo;
GO

CREATE TABLE dbo.ActivoFijo_TipoActivo (
    [TipoActivoID] SMALLINT NOT NULL,
    [Nombre] VARCHAR(80) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.ActivoFijo_TipoActivo ADD CONSTRAINT [PK_AF_TipoActivo] PRIMARY KEY (TipoActivoID);
CREATE UNIQUE INDEX [UQ_AF_TipoActivo_Nombre] ON dbo.ActivoFijo_TipoActivo (Nombre);
GO

-- =================================================
-- Tabla: ActivoFijo_TipoBaja
-- Exportado: 2026-06-03T06:44:42.121618
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_TipoBaja', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_TipoBaja;
GO

CREATE TABLE dbo.ActivoFijo_TipoBaja (
    [TipoBajaID] TINYINT NOT NULL,
    [Nombre] VARCHAR(40) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.ActivoFijo_TipoBaja ADD CONSTRAINT [PK_AF_TipoBaja] PRIMARY KEY (TipoBajaID);
CREATE UNIQUE INDEX [UQ_AF_TipoBaja_Nombre] ON dbo.ActivoFijo_TipoBaja (Nombre);
GO

-- =================================================
-- Tabla: ActivoFijo_TipoMedidor
-- Exportado: 2026-06-03T06:44:42.356854
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_TipoMedidor', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_TipoMedidor;
GO

CREATE TABLE dbo.ActivoFijo_TipoMedidor (
    [TipoMedidorID] TINYINT NOT NULL,
    [Nombre] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.ActivoFijo_TipoMedidor ADD CONSTRAINT [PK_AF_TipoMedidor] PRIMARY KEY (TipoMedidorID);
CREATE UNIQUE INDEX [UQ_AF_TipoMedidor_Nombre] ON dbo.ActivoFijo_TipoMedidor (Nombre);
GO

-- =================================================
-- Tabla: ActivoFijo_TipoOT
-- Exportado: 2026-06-03T06:44:42.593485
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_TipoOT', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_TipoOT;
GO

CREATE TABLE dbo.ActivoFijo_TipoOT (
    [TipoOTID] TINYINT NOT NULL,
    [Nombre] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.ActivoFijo_TipoOT ADD CONSTRAINT [PK_AF_TipoOT] PRIMARY KEY (TipoOTID);
CREATE UNIQUE INDEX [UQ_AF_TipoOT_Nombre] ON dbo.ActivoFijo_TipoOT (Nombre);
GO

-- =================================================
-- Tabla: ActivoFijo_TipoUbicacion
-- Exportado: 2026-06-03T06:44:42.829973
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_TipoUbicacion', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_TipoUbicacion;
GO

CREATE TABLE dbo.ActivoFijo_TipoUbicacion (
    [TipoUbicacionID] SMALLINT NOT NULL,
    [Nombre] VARCHAR(60) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.ActivoFijo_TipoUbicacion ADD CONSTRAINT [PK_AF_TipoUbicacion] PRIMARY KEY (TipoUbicacionID);
CREATE UNIQUE INDEX [UQ_AF_TipoUbicacion_Nombre] ON dbo.ActivoFijo_TipoUbicacion (Nombre);
GO

-- =================================================
-- Tabla: ActivoFijo_Ubicaciones
-- Exportado: 2026-06-03T06:44:43.065598
-- =================================================

IF OBJECT_ID('dbo.ActivoFijo_Ubicaciones', 'U') IS NOT NULL
    DROP TABLE dbo.ActivoFijo_Ubicaciones;
GO

CREATE TABLE dbo.ActivoFijo_Ubicaciones (
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
    [Activa] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.ActivoFijo_Ubicaciones ADD CONSTRAINT [PK_AF_Ubicaciones] PRIMARY KEY (UbicacionID);
CREATE UNIQUE INDEX [UQ_AF_Ubicaciones_Codigo] ON dbo.ActivoFijo_Ubicaciones (CodigoUbicacion);
GO

-- =================================================
-- Tabla: Alertas_Sistema
-- Exportado: 2026-06-03T06:44:43.270887
-- =================================================

IF OBJECT_ID('dbo.Alertas_Sistema', 'U') IS NOT NULL
    DROP TABLE dbo.Alertas_Sistema;
GO

CREATE TABLE dbo.Alertas_Sistema (
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
    [AcknowledgedAt] DATETIME2 NULL
);
GO

CREATE INDEX [IX_Alertas_Acknowledged] ON dbo.Alertas_Sistema (Acknowledged);
CREATE INDEX [IX_Alertas_Tipo] ON dbo.Alertas_Sistema (Tipo);
ALTER TABLE dbo.Alertas_Sistema ADD CONSTRAINT [PK__Alertas___3214EC27ECE2D25E] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ__Alertas___D9EF47E451A4E4AF] ON dbo.Alertas_Sistema (AlertaID);
GO

-- =================================================
-- Tabla: Auditoria_Inventario_Provisional
-- Exportado: 2026-06-03T06:44:43.507019
-- =================================================

IF OBJECT_ID('dbo.Auditoria_Inventario_Provisional', 'U') IS NOT NULL
    DROP TABLE dbo.Auditoria_Inventario_Provisional;
GO

CREATE TABLE dbo.Auditoria_Inventario_Provisional (
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
    [notas] TEXT NULL,
    [estado] VARCHAR(20) NULL DEFAULT ('PROVISIONAL'),
    [auditoria_ejecutada] BIT NULL DEFAULT ((0)),
    [fecha_auditoria_ejecutada] DATETIME NULL,
    [creado_en] DATETIME NULL DEFAULT (getdate()),
    [actualizado_en] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.Auditoria_Inventario_Provisional ADD CONSTRAINT [PK__Auditori__3213E83F4DC7B19A] PRIMARY KEY (id);
GO

-- =================================================
-- Tabla: automatizacion_inventarios_config
-- Exportado: 2026-06-03T06:44:43.743379
-- =================================================

IF OBJECT_ID('dbo.automatizacion_inventarios_config', 'U') IS NOT NULL
    DROP TABLE dbo.automatizacion_inventarios_config;
GO

CREATE TABLE dbo.automatizacion_inventarios_config (
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
    [updated_by] NVARCHAR(100) NULL
);
GO

CREATE INDEX [IX_config_servidor] ON dbo.automatizacion_inventarios_config (server_id, sucursal_id, almacen_id);
ALTER TABLE dbo.automatizacion_inventarios_config ADD CONSTRAINT [PK_automatizacion_config] PRIMARY KEY (config_id);
GO

-- =================================================
-- Tabla: automatizacion_inventarios_destinatarios
-- Exportado: 2026-06-03T06:44:43.947632
-- =================================================

IF OBJECT_ID('dbo.automatizacion_inventarios_destinatarios', 'U') IS NOT NULL
    DROP TABLE dbo.automatizacion_inventarios_destinatarios;
GO

CREATE TABLE dbo.automatizacion_inventarios_destinatarios (
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
    [updated_by] NVARCHAR(100) NULL
);
GO

CREATE INDEX [IX_destinatarios_jerarquia] ON dbo.automatizacion_inventarios_destinatarios (server_id, sucursal_id, almacen_id, canal, activo);
ALTER TABLE dbo.automatizacion_inventarios_destinatarios ADD CONSTRAINT [PK_automatizacion_destinatarios] PRIMARY KEY (destinatario_id);
GO

-- =================================================
-- Tabla: automatizacion_inventarios_ejecuciones
-- Exportado: 2026-06-03T06:44:44.152565
-- =================================================

IF OBJECT_ID('dbo.automatizacion_inventarios_ejecuciones', 'U') IS NOT NULL
    DROP TABLE dbo.automatizacion_inventarios_ejecuciones;
GO

CREATE TABLE dbo.automatizacion_inventarios_ejecuciones (
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
    [updated_at] DATETIME NULL
);
GO

CREATE INDEX [IX_ejecuciones_fecha] ON dbo.automatizacion_inventarios_ejecuciones (fecha_inicio);
ALTER TABLE dbo.automatizacion_inventarios_ejecuciones ADD CONSTRAINT [PK_automatizacion_ejecuciones] PRIMARY KEY (ejecucion_id);
GO

-- =================================================
-- Tabla: automatizacion_inventarios_envios
-- Exportado: 2026-06-03T06:44:44.355896
-- =================================================

IF OBJECT_ID('dbo.automatizacion_inventarios_envios', 'U') IS NOT NULL
    DROP TABLE dbo.automatizacion_inventarios_envios;
GO

CREATE TABLE dbo.automatizacion_inventarios_envios (
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
    [updated_at] DATETIME NULL
);
GO

CREATE INDEX [IX_envios_procesado] ON dbo.automatizacion_inventarios_envios (procesado_id);
ALTER TABLE dbo.automatizacion_inventarios_envios ADD CONSTRAINT [PK_automatizacion_envios] PRIMARY KEY (envio_id);
GO

-- =================================================
-- Tabla: automatizacion_inventarios_folios_procesados
-- Exportado: 2026-06-03T06:44:44.560896
-- =================================================

IF OBJECT_ID('dbo.automatizacion_inventarios_folios_procesados', 'U') IS NOT NULL
    DROP TABLE dbo.automatizacion_inventarios_folios_procesados;
GO

CREATE TABLE dbo.automatizacion_inventarios_folios_procesados (
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
    [estado_inventario_origen] NVARCHAR(10) NULL
);
GO

CREATE INDEX [IX_folios_hash] ON dbo.automatizacion_inventarios_folios_procesados (hash_verificacion);
ALTER TABLE dbo.automatizacion_inventarios_folios_procesados ADD CONSTRAINT [PK_automatizacion_folios] PRIMARY KEY (procesado_id);
CREATE UNIQUE INDEX [UQ_folios_clave_unica_v2] ON dbo.automatizacion_inventarios_folios_procesados (sistema_origen, server_id, sucursal_id, almacen_id, comentario, folio_inventario, fecha_inventario, estado_inventario_origen);
GO

-- =================================================
-- Tabla: automatizacion_inventarios_ultimo_folio_conocido
-- Exportado: 2026-06-03T06:44:44.798416
-- =================================================

IF OBJECT_ID('dbo.automatizacion_inventarios_ultimo_folio_conocido', 'U') IS NOT NULL
    DROP TABLE dbo.automatizacion_inventarios_ultimo_folio_conocido;
GO

CREATE TABLE dbo.automatizacion_inventarios_ultimo_folio_conocido (
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
    [updated_by] NVARCHAR(100) NULL
);
GO

CREATE INDEX [IX_ultimo_folio_servidor] ON dbo.automatizacion_inventarios_ultimo_folio_conocido (server_id, sistema_origen);
ALTER TABLE dbo.automatizacion_inventarios_ultimo_folio_conocido ADD CONSTRAINT [PK_automatizacion_ultimo_folio] PRIMARY KEY (id);
CREATE UNIQUE INDEX [UQ_ultimo_folio_clave] ON dbo.automatizacion_inventarios_ultimo_folio_conocido (sistema_origen, server_id, sucursal_id, almacen_id);
GO

-- =================================================
-- Tabla: CavaSocios_Botellas
-- Exportado: 2026-06-03T06:44:45.002850
-- =================================================

IF OBJECT_ID('dbo.CavaSocios_Botellas', 'U') IS NOT NULL
    DROP TABLE dbo.CavaSocios_Botellas;
GO

CREATE TABLE dbo.CavaSocios_Botellas (
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
    [Observaciones] NVARCHAR(500) NULL
);
GO

CREATE INDEX [IX_CavaSocios_Botellas_Estatus] ON dbo.CavaSocios_Botellas (EstatusBotella);
CREATE INDEX [IX_CavaSocios_Botellas_Socio] ON dbo.CavaSocios_Botellas (SocioID);
ALTER TABLE dbo.CavaSocios_Botellas ADD CONSTRAINT [PK__CavaSoci__330B1CFA04F87623] PRIMARY KEY (BotellaID);
GO

-- =================================================
-- Tabla: CavaSocios_Cargos
-- Exportado: 2026-06-03T06:44:45.240213
-- =================================================

IF OBJECT_ID('dbo.CavaSocios_Cargos', 'U') IS NOT NULL
    DROP TABLE dbo.CavaSocios_Cargos;
GO

CREATE TABLE dbo.CavaSocios_Cargos (
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
    [Observaciones] NVARCHAR(500) NULL
);
GO

CREATE INDEX [IX_CavaSocios_Cargos_Estatus] ON dbo.CavaSocios_Cargos (EstatusCargo);
CREATE INDEX [IX_CavaSocios_Cargos_Socio] ON dbo.CavaSocios_Cargos (SocioID);
ALTER TABLE dbo.CavaSocios_Cargos ADD CONSTRAINT [PK__CavaSoci__B4E665ED5ADCE942] PRIMARY KEY (CargoID);
GO

-- =================================================
-- Tabla: CavaSocios_Configuracion
-- Exportado: 2026-06-03T06:44:45.478430
-- =================================================

IF OBJECT_ID('dbo.CavaSocios_Configuracion', 'U') IS NOT NULL
    DROP TABLE dbo.CavaSocios_Configuracion;
GO

CREATE TABLE dbo.CavaSocios_Configuracion (
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
    [UsuarioModificacionID] UNIQUEIDENTIFIER NULL
);
GO

ALTER TABLE dbo.CavaSocios_Configuracion ADD CONSTRAINT [PK__CavaSoci__C3BC333C4361CC37] PRIMARY KEY (ConfigID);
CREATE UNIQUE INDEX [UQ__CavaSoci__7B9F2137A5004EC5] ON dbo.CavaSocios_Configuracion (EmpresaID);
GO

-- =================================================
-- Tabla: CavaSocios_Movimientos
-- Exportado: 2026-06-03T06:44:45.683314
-- =================================================

IF OBJECT_ID('dbo.CavaSocios_Movimientos', 'U') IS NOT NULL
    DROP TABLE dbo.CavaSocios_Movimientos;
GO

CREATE TABLE dbo.CavaSocios_Movimientos (
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
    [Observaciones] NVARCHAR(500) NULL
);
GO

CREATE INDEX [IX_CavaSocios_Movimientos_Botella] ON dbo.CavaSocios_Movimientos (BotellaID);
CREATE INDEX [IX_CavaSocios_Movimientos_Fecha] ON dbo.CavaSocios_Movimientos (FechaMovimiento);
ALTER TABLE dbo.CavaSocios_Movimientos ADD CONSTRAINT [PK__CavaSoci__BF923FCC29B34412] PRIMARY KEY (MovimientoID);
GO

-- =================================================
-- Tabla: CavaSocios_Socios
-- Exportado: 2026-06-03T06:44:45.927457
-- =================================================

IF OBJECT_ID('dbo.CavaSocios_Socios', 'U') IS NOT NULL
    DROP TABLE dbo.CavaSocios_Socios;
GO

CREATE TABLE dbo.CavaSocios_Socios (
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
    [Observaciones] NVARCHAR(500) NULL
);
GO

CREATE INDEX [IX_CavaSocios_Socios_ClienteCRM] ON dbo.CavaSocios_Socios (ClienteCRMID);
CREATE INDEX [IX_CavaSocios_Socios_Empresa] ON dbo.CavaSocios_Socios (EmpresaID);
ALTER TABLE dbo.CavaSocios_Socios ADD CONSTRAINT [PK__CavaSoci__165D08DA1FE212A2] PRIMARY KEY (SocioID);
CREATE UNIQUE INDEX [UQ_CavaSocios_NumeroSocio] ON dbo.CavaSocios_Socios (EmpresaID, NumeroSocio);
GO

-- =================================================
-- Tabla: Cliente_Catalogo
-- Exportado: 2026-06-03T06:44:46.165225
-- =================================================

IF OBJECT_ID('dbo.Cliente_Catalogo', 'U') IS NOT NULL
    DROP TABLE dbo.Cliente_Catalogo;
GO

CREATE TABLE dbo.Cliente_Catalogo (
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
    [PublicUUID] UNIQUEIDENTIFIER NULL DEFAULT (newid())
);
GO

CREATE INDEX [IX_Cliente_Catalogo_ClienteMaestroID] ON dbo.Cliente_Catalogo (ClienteMaestroID);
CREATE INDEX [IX_Cliente_Catalogo_GrupoClienteID] ON dbo.Cliente_Catalogo (GrupoClienteID);
CREATE INDEX [IX_Cliente_Catalogo_RazonSocial] ON dbo.Cliente_Catalogo (RazonSocial);
ALTER TABLE dbo.Cliente_Catalogo ADD CONSTRAINT [PK_Cliente_Catalogo] PRIMARY KEY (ClienteID);
CREATE UNIQUE INDEX [UQ_Cliente_Catalogo_CodigoCliente] ON dbo.Cliente_Catalogo (CodigoCliente);
CREATE UNIQUE INDEX [UQ_Cliente_Catalogo_RFC] ON dbo.Cliente_Catalogo (RFC);
GO

-- =================================================
-- Tabla: Cliente_Contactos
-- Exportado: 2026-06-03T06:44:46.402166
-- =================================================

IF OBJECT_ID('dbo.Cliente_Contactos', 'U') IS NOT NULL
    DROP TABLE dbo.Cliente_Contactos;
GO

CREATE TABLE dbo.Cliente_Contactos (
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
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.Cliente_Contactos ADD CONSTRAINT [PK_Cliente_Contactos] PRIMARY KEY (ContactoClienteID);
GO

-- =================================================
-- Tabla: Cliente_Direcciones
-- Exportado: 2026-06-03T06:44:46.606062
-- =================================================

IF OBJECT_ID('dbo.Cliente_Direcciones', 'U') IS NOT NULL
    DROP TABLE dbo.Cliente_Direcciones;
GO

CREATE TABLE dbo.Cliente_Direcciones (
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
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.Cliente_Direcciones ADD CONSTRAINT [PK_Cliente_Direcciones] PRIMARY KEY (DireccionClienteID);
GO

-- =================================================
-- Tabla: Cliente_Grupos
-- Exportado: 2026-06-03T06:44:46.812738
-- =================================================

IF OBJECT_ID('dbo.Cliente_Grupos', 'U') IS NOT NULL
    DROP TABLE dbo.Cliente_Grupos;
GO

CREATE TABLE dbo.Cliente_Grupos (
    [GrupoClienteID] INT NOT NULL,
    [CodigoGrupoCliente] VARCHAR(20) NOT NULL,
    [NombreGrupoCliente] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.Cliente_Grupos ADD CONSTRAINT [PK_Cliente_Grupos] PRIMARY KEY (GrupoClienteID);
CREATE UNIQUE INDEX [UQ_Cliente_Grupos_CodigoGrupoCliente] ON dbo.Cliente_Grupos (CodigoGrupoCliente);
CREATE UNIQUE INDEX [UQ_Cliente_Grupos_NombreGrupoCliente] ON dbo.Cliente_Grupos (NombreGrupoCliente);
GO

-- =================================================
-- Tabla: Cliente_RolUsuarioPortal
-- Exportado: 2026-06-03T06:44:47.016445
-- =================================================

IF OBJECT_ID('dbo.Cliente_RolUsuarioPortal', 'U') IS NOT NULL
    DROP TABLE dbo.Cliente_RolUsuarioPortal;
GO

CREATE TABLE dbo.Cliente_RolUsuarioPortal (
    [RolPortalClienteID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Cliente_RolUsuarioPortal ADD CONSTRAINT [PK_Cliente_RolUsuarioPortal] PRIMARY KEY (RolPortalClienteID);
GO

-- =================================================
-- Tabla: Cliente_UsuariosPortal
-- Exportado: 2026-06-03T06:44:47.251942
-- =================================================

IF OBJECT_ID('dbo.Cliente_UsuariosPortal', 'U') IS NOT NULL
    DROP TABLE dbo.Cliente_UsuariosPortal;
GO

CREATE TABLE dbo.Cliente_UsuariosPortal (
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
    [FechaModificacion] DATETIME2 NULL
);
GO

CREATE INDEX [IX_Cliente_UsuariosPortal_ClienteID] ON dbo.Cliente_UsuariosPortal (ClienteID);
ALTER TABLE dbo.Cliente_UsuariosPortal ADD CONSTRAINT [PK_Cliente_UsuariosPortal] PRIMARY KEY (UsuarioPortalClienteID);
CREATE UNIQUE INDEX [UQ_Cliente_UsuariosPortal_Email] ON dbo.Cliente_UsuariosPortal (Email);
GO

-- =================================================
-- Tabla: Comercial_AlertasMargenDestinatarios
-- Exportado: 2026-06-03T06:44:47.457207
-- =================================================

IF OBJECT_ID('dbo.Comercial_AlertasMargenDestinatarios', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_AlertasMargenDestinatarios;
GO

CREATE TABLE dbo.Comercial_AlertasMargenDestinatarios (
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
    [ModificadoPor] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_AlertasMargenDestinatarios_Activo] ON dbo.Comercial_AlertasMargenDestinatarios (Activo);
CREATE INDEX [IX_AlertasMargenDestinatarios_Empresa] ON dbo.Comercial_AlertasMargenDestinatarios (EmpresaID);
CREATE INDEX [IX_AlertasMargenDestinatarios_Server] ON dbo.Comercial_AlertasMargenDestinatarios (ServerID);
CREATE INDEX [IX_AlertasMargenDestinatarios_Severidad] ON dbo.Comercial_AlertasMargenDestinatarios (SeveridadMinima);
ALTER TABLE dbo.Comercial_AlertasMargenDestinatarios ADD CONSTRAINT [PK__Comercia__C8526AD99DFB1F88] PRIMARY KEY (DestinatarioID);
GO

-- =================================================
-- Tabla: Comercial_AlertasMargenEnvios
-- Exportado: 2026-06-03T06:44:47.661888
-- =================================================

IF OBJECT_ID('dbo.Comercial_AlertasMargenEnvios', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_AlertasMargenEnvios;
GO

CREATE TABLE dbo.Comercial_AlertasMargenEnvios (
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
    [FechaCreacion] DATETIME NULL DEFAULT (getdate())
);
GO

CREATE INDEX [IX_AlertasMargenEnvios_Alerta] ON dbo.Comercial_AlertasMargenEnvios (AlertaMargenEventoID);
CREATE INDEX [IX_AlertasMargenEnvios_Canal] ON dbo.Comercial_AlertasMargenEnvios (Canal, EstadoEnvio);
CREATE INDEX [IX_AlertasMargenEnvios_Destinatario] ON dbo.Comercial_AlertasMargenEnvios (DestinatarioID);
CREATE INDEX [IX_AlertasMargenEnvios_Estado] ON dbo.Comercial_AlertasMargenEnvios (EstadoEnvio);
CREATE INDEX [IX_AlertasMargenEnvios_Fecha] ON dbo.Comercial_AlertasMargenEnvios (FechaCreacion);
ALTER TABLE dbo.Comercial_AlertasMargenEnvios ADD CONSTRAINT [PK__Comercia__D024E21F0F53B3CC] PRIMARY KEY (EnvioID);
GO

-- =================================================
-- Tabla: Comercial_AlertasMargenEventos
-- Exportado: 2026-06-03T06:44:47.866665
-- =================================================

IF OBJECT_ID('dbo.Comercial_AlertasMargenEventos', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_AlertasMargenEventos;
GO

CREATE TABLE dbo.Comercial_AlertasMargenEventos (
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
    [ResueltoPor] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_AlertasMargenEventos_Duplicados] ON dbo.Comercial_AlertasMargenEventos (ProductoClave, ServerID, Estado, Severidad);
CREATE INDEX [IX_AlertasMargenEventos_Estado] ON dbo.Comercial_AlertasMargenEventos (Estado);
CREATE INDEX [IX_AlertasMargenEventos_Fecha] ON dbo.Comercial_AlertasMargenEventos (FechaEvaluacion);
CREATE INDEX [IX_AlertasMargenEventos_Producto] ON dbo.Comercial_AlertasMargenEventos (ProductoClave);
CREATE INDEX [IX_AlertasMargenEventos_Regla] ON dbo.Comercial_AlertasMargenEventos (ReglaMargenID);
CREATE INDEX [IX_AlertasMargenEventos_Server] ON dbo.Comercial_AlertasMargenEventos (ServerID);
CREATE INDEX [IX_AlertasMargenEventos_Severidad] ON dbo.Comercial_AlertasMargenEventos (Severidad);
ALTER TABLE dbo.Comercial_AlertasMargenEventos ADD CONSTRAINT [PK__Comercia__C7A599C5B21972E0] PRIMARY KEY (AlertaMargenEventoID);
GO

-- =================================================
-- Tabla: Comercial_AlertasMargenReglas
-- Exportado: 2026-06-03T06:44:48.072756
-- =================================================

IF OBJECT_ID('dbo.Comercial_AlertasMargenReglas', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_AlertasMargenReglas;
GO

CREATE TABLE dbo.Comercial_AlertasMargenReglas (
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
    [ModificadoPor] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_AlertasMargenReglas_Familia] ON dbo.Comercial_AlertasMargenReglas (FamiliaCodigo);
CREATE INDEX [IX_AlertasMargenReglas_Grupo] ON dbo.Comercial_AlertasMargenReglas (GrupoCodigo);
CREATE INDEX [IX_AlertasMargenReglas_Nivel] ON dbo.Comercial_AlertasMargenReglas (NivelAplicacion, Activo);
CREATE INDEX [IX_AlertasMargenReglas_Producto] ON dbo.Comercial_AlertasMargenReglas (ProductoClave);
CREATE INDEX [IX_AlertasMargenReglas_Subfamilia] ON dbo.Comercial_AlertasMargenReglas (SubfamiliaCodigo);
CREATE INDEX [IX_AlertasMargenReglas_Vigencia] ON dbo.Comercial_AlertasMargenReglas (Activo, FechaInicioVigencia, FechaFinVigencia);
ALTER TABLE dbo.Comercial_AlertasMargenReglas ADD CONSTRAINT [PK__Comercia__3AF73AD266A101E7] PRIMARY KEY (ReglaMargenID);
GO

-- =================================================
-- Tabla: Comercial_AlertasUmbralesSeveridad
-- Exportado: 2026-06-03T06:44:48.311278
-- =================================================

IF OBJECT_ID('dbo.Comercial_AlertasUmbralesSeveridad', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_AlertasUmbralesSeveridad;
GO

CREATE TABLE dbo.Comercial_AlertasUmbralesSeveridad (
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
    [FechaModificacion] DATETIME NULL
);
GO

CREATE INDEX [IX_AlertasUmbralesSeveridad_Activo] ON dbo.Comercial_AlertasUmbralesSeveridad (Activo, Orden);
CREATE INDEX [IX_AlertasUmbralesSeveridad_Severidad] ON dbo.Comercial_AlertasUmbralesSeveridad (Severidad);
ALTER TABLE dbo.Comercial_AlertasUmbralesSeveridad ADD CONSTRAINT [PK__Comercia__D40D87C1C3F2FD83] PRIMARY KEY (UmbralID);
GO

-- =================================================
-- Tabla: Comercial_Competidores
-- Exportado: 2026-06-03T06:44:48.547977
-- =================================================

IF OBJECT_ID('dbo.Comercial_Competidores', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_Competidores;
GO

CREATE TABLE dbo.Comercial_Competidores (
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
    [Notas] NVARCHAR(1000) NULL
);
GO

ALTER TABLE dbo.Comercial_Competidores ADD CONSTRAINT [PK__Comercia__79384159B5711660] PRIMARY KEY (CompetidorID);
GO

-- =================================================
-- Tabla: Comercial_CompetidoresCatalogo
-- Exportado: 2026-06-03T06:44:48.786697
-- =================================================

IF OBJECT_ID('dbo.Comercial_CompetidoresCatalogo', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_CompetidoresCatalogo;
GO

CREATE TABLE dbo.Comercial_CompetidoresCatalogo (
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
    [UsuarioModificacion] NVARCHAR(100) NULL
);
GO

CREATE INDEX [IX_CompetidoresCatalogo_Activo] ON dbo.Comercial_CompetidoresCatalogo (Activo);
CREATE INDEX [IX_CompetidoresCatalogo_Ciudad] ON dbo.Comercial_CompetidoresCatalogo (Ciudad);
CREATE INDEX [IX_CompetidoresCatalogo_Nombre] ON dbo.Comercial_CompetidoresCatalogo (NombreCompetidor);
ALTER TABLE dbo.Comercial_CompetidoresCatalogo ADD CONSTRAINT [PK__Comercia__02112D5087E35A1A] PRIMARY KEY (CompetidorCatalogoID);
GO

-- =================================================
-- Tabla: Comercial_CompetidoresListas
-- Exportado: 2026-06-03T06:44:49.024980
-- =================================================

IF OBJECT_ID('dbo.Comercial_CompetidoresListas', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_CompetidoresListas;
GO

CREATE TABLE dbo.Comercial_CompetidoresListas (
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
    [ModificadoPor] NVARCHAR(100) NULL
);
GO

CREATE INDEX [IX_CompetidoresListas_Activo] ON dbo.Comercial_CompetidoresListas (Activo);
CREATE INDEX [IX_CompetidoresListas_Empresa] ON dbo.Comercial_CompetidoresListas (EmpresaID);
CREATE INDEX [IX_CompetidoresListas_Unidad] ON dbo.Comercial_CompetidoresListas (UnidadNegocioID);
ALTER TABLE dbo.Comercial_CompetidoresListas ADD CONSTRAINT [PK__Comercia__58B879F4FD155675] PRIMARY KEY (ListaCompetidoresID);
GO

-- =================================================
-- Tabla: Comercial_CompetidoresListasDetalle
-- Exportado: 2026-06-03T06:44:49.263419
-- =================================================

IF OBJECT_ID('dbo.Comercial_CompetidoresListasDetalle', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_CompetidoresListasDetalle;
GO

CREATE TABLE dbo.Comercial_CompetidoresListasDetalle (
    [ListaDetalleID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [ListaCompetidoresID] UNIQUEIDENTIFIER NOT NULL,
    [CompetidorID] UNIQUEIDENTIFIER NOT NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [Notas] NVARCHAR(500) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME2 NULL,
    [CreadoPor] NVARCHAR(100) NOT NULL,
    [ModificadoPor] NVARCHAR(100) NULL
);
GO

CREATE INDEX [IX_ListasDetalle_Activo] ON dbo.Comercial_CompetidoresListasDetalle (Activo);
CREATE INDEX [IX_ListasDetalle_Competidor] ON dbo.Comercial_CompetidoresListasDetalle (CompetidorID);
CREATE INDEX [IX_ListasDetalle_Lista] ON dbo.Comercial_CompetidoresListasDetalle (ListaCompetidoresID);
ALTER TABLE dbo.Comercial_CompetidoresListasDetalle ADD CONSTRAINT [PK__Comercia__51209C9599EEF11B] PRIMARY KEY (ListaDetalleID);
CREATE UNIQUE INDEX [UQ_ListaCompetidor_Activo] ON dbo.Comercial_CompetidoresListasDetalle (ListaCompetidoresID, CompetidorID);
GO

-- =================================================
-- Tabla: Comercial_CompetidoresMenuItems
-- Exportado: 2026-06-03T06:44:49.499222
-- =================================================

IF OBJECT_ID('dbo.Comercial_CompetidoresMenuItems', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_CompetidoresMenuItems;
GO

CREATE TABLE dbo.Comercial_CompetidoresMenuItems (
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
    [UsuarioCreacion] NVARCHAR(100) NULL
);
GO

ALTER TABLE dbo.Comercial_CompetidoresMenuItems ADD CONSTRAINT [PK__Comercia__68FE3FC7A97CB5F7] PRIMARY KEY (CompetidorMenuItemID);
GO

-- =================================================
-- Tabla: Comercial_CompetidoresUnidad
-- Exportado: 2026-06-03T06:44:49.735553
-- =================================================

IF OBJECT_ID('dbo.Comercial_CompetidoresUnidad', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_CompetidoresUnidad;
GO

CREATE TABLE dbo.Comercial_CompetidoresUnidad (
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
    [UsuarioModificacion] NVARCHAR(100) NULL
);
GO

CREATE INDEX [IX_CompetidoresUnidad_Activo] ON dbo.Comercial_CompetidoresUnidad (Activo);
CREATE INDEX [IX_CompetidoresUnidad_Competidor] ON dbo.Comercial_CompetidoresUnidad (CompetidorCatalogoID);
CREATE INDEX [IX_CompetidoresUnidad_Empresa] ON dbo.Comercial_CompetidoresUnidad (EmpresaID);
CREATE INDEX [IX_CompetidoresUnidad_Unidad] ON dbo.Comercial_CompetidoresUnidad (UnidadNegocioID);
ALTER TABLE dbo.Comercial_CompetidoresUnidad ADD CONSTRAINT [PK__Comercia__04B58D67454B9746] PRIMARY KEY (CompetidorUnidadID);
CREATE UNIQUE INDEX [UK_CompetidoresUnidad_CompetidorUnidad] ON dbo.Comercial_CompetidoresUnidad (CompetidorCatalogoID, UnidadNegocioID);
GO

-- =================================================
-- Tabla: Comercial_Dashboard_Cache
-- Exportado: 2026-06-03T06:44:49.973836
-- =================================================

IF OBJECT_ID('dbo.Comercial_Dashboard_Cache', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_Dashboard_Cache;
GO

CREATE TABLE dbo.Comercial_Dashboard_Cache (
    [CacheID] INT NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [PeriodoKey] VARCHAR(100) NOT NULL,
    [DataJSON] NVARCHAR(MAX) NULL,
    [UpdatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.Comercial_Dashboard_Cache ADD CONSTRAINT [PK__Comercia__4EDCCD1344BEFD57] PRIMARY KEY (CacheID);
CREATE UNIQUE INDEX [UQ_Comercial_Dashboard_Cache] ON dbo.Comercial_Dashboard_Cache (ServerID, PeriodoKey);
GO

-- =================================================
-- Tabla: Comercial_ImpuestosCatalogo
-- Exportado: 2026-06-03T06:44:50.180016
-- =================================================

IF OBJECT_ID('dbo.Comercial_ImpuestosCatalogo', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_ImpuestosCatalogo;
GO

CREATE TABLE dbo.Comercial_ImpuestosCatalogo (
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
    [ModificadoPor] NVARCHAR(100) NULL
);
GO

ALTER TABLE dbo.Comercial_ImpuestosCatalogo ADD CONSTRAINT [PK__Comercia__CD9F45DE0B3EEDCF] PRIMARY KEY (ImpuestoID);
CREATE UNIQUE INDEX [UQ__Comercia__06370DACDC10A2B9] ON dbo.Comercial_ImpuestosCatalogo (Codigo);
GO

-- =================================================
-- Tabla: Comercial_ImpuestosMapeo
-- Exportado: 2026-06-03T06:44:50.417499
-- =================================================

IF OBJECT_ID('dbo.Comercial_ImpuestosMapeo', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_ImpuestosMapeo;
GO

CREATE TABLE dbo.Comercial_ImpuestosMapeo (
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
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime())
);
GO

ALTER TABLE dbo.Comercial_ImpuestosMapeo ADD CONSTRAINT [PK__Comercia__DBC96B8658CA5F86] PRIMARY KEY (MapeoProductoID);
CREATE UNIQUE INDEX [UQ_ImpuestosMapeo_Producto] ON dbo.Comercial_ImpuestosMapeo (ServerID, CodigoProducto);
GO

-- =================================================
-- Tabla: Comercial_ImpuestosOverrides
-- Exportado: 2026-06-03T06:44:51.936750
-- =================================================

IF OBJECT_ID('dbo.Comercial_ImpuestosOverrides', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_ImpuestosOverrides;
GO

CREATE TABLE dbo.Comercial_ImpuestosOverrides (
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
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime())
);
GO

ALTER TABLE dbo.Comercial_ImpuestosOverrides ADD CONSTRAINT [PK__Comercia__37B513C4DF3040EB] PRIMARY KEY (OverrideID);
GO

-- =================================================
-- Tabla: Comercial_ImpuestosTasas
-- Exportado: 2026-06-03T06:44:52.140215
-- =================================================

IF OBJECT_ID('dbo.Comercial_ImpuestosTasas', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_ImpuestosTasas;
GO

CREATE TABLE dbo.Comercial_ImpuestosTasas (
    [TasaID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [ImpuestoID] UNIQUEIDENTIFIER NOT NULL,
    [Tasa] DECIMAL(10,4) NOT NULL,
    [TipoFactor] VARCHAR(20) NOT NULL,
    [VigenciaDesde] DATE NOT NULL,
    [VigenciaHasta] DATE NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime())
);
GO

ALTER TABLE dbo.Comercial_ImpuestosTasas ADD CONSTRAINT [PK__Comercia__7DED260DB313FF1E] PRIMARY KEY (TasaID);
GO

-- =================================================
-- Tabla: Comercial_Inteligencia_VentasDetalleProducto
-- Exportado: 2026-06-03T06:44:52.376566
-- =================================================

IF OBJECT_ID('dbo.Comercial_Inteligencia_VentasDetalleProducto', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto;
GO

CREATE TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto (
    [id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [unidad_negocio_id] NVARCHAR(50) NULL,
    [unidad_negocio_nombre] NVARCHAR(100) NULL,
    [server_id] NVARCHAR(50) NULL,
    [sucursal_id] NVARCHAR(50) NULL,
    [sucursal_nombre] NVARCHAR(100) NULL,
    [sistema_origen] NVARCHAR(20) NULL,
    [fecha_operacion] DATE NOT NULL,
    [fecha_hora] DATETIME2 NULL,
    [numero_ticket] NVARCHAR(64) NOT NULL DEFAULT (''),
    [id_transaccion] NVARCHAR(64) NOT NULL DEFAULT (''),
    [producto_codigo_fuente] NVARCHAR(100) NOT NULL DEFAULT (''),
    [producto_id] UNIQUEIDENTIFIER NULL,
    [producto_nombre] NVARCHAR(300) NULL,
    [familia_id] UNIQUEIDENTIFIER NULL,
    [familia_nombre] NVARCHAR(200) NULL,
    [subfamilia_id] UNIQUEIDENTIFIER NULL,
    [subfamilia_nombre] NVARCHAR(200) NULL,
    [casa] NVARCHAR(100) NULL,
    [porcentaje_alcohol] DECIMAL(5,2) NULL,
    [es_alcohol] BIT NULL,
    [cantidad] DECIMAL(18,4) NULL,
    [precio_unitario] DECIMAL(18,4) NULL,
    [importe_bruto] DECIMAL(18,4) NULL,
    [importe_neto] DECIMAL(18,4) NULL,
    [descuento] DECIMAL(18,4) NULL,
    [propina] DECIMAL(18,4) NULL,
    [pax] INT NULL,
    [sync_run_id] NVARCHAR(100) NULL,
    [hash_origen] NVARCHAR(64) NULL,
    [fecha_sincronizacion] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [activo] BIT NOT NULL DEFAULT ((1))
);
GO

CREATE INDEX [IX_Comercial_Intel_VentasDetalle_Fecha] ON dbo.Comercial_Inteligencia_VentasDetalleProducto (fecha_operacion);
CREATE INDEX [IX_Comercial_Intel_VentasDetalle_Producto] ON dbo.Comercial_Inteligencia_VentasDetalleProducto (producto_codigo_fuente, fecha_operacion);
CREATE INDEX [IX_Comercial_Intel_VentasDetalle_Unidad] ON dbo.Comercial_Inteligencia_VentasDetalleProducto (unidad_negocio_nombre, fecha_operacion);
ALTER TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto ADD CONSTRAINT [PK__Comercia__3213E83F57351393] PRIMARY KEY (id);
CREATE UNIQUE INDEX [UX_Comercial_Intel_VentasDetalle_NoDup] ON dbo.Comercial_Inteligencia_VentasDetalleProducto (id_transaccion, numero_ticket, producto_codigo_fuente, fecha_operacion);
GO

-- =================================================
-- Tabla: Comercial_KPIs_Cache
-- Exportado: 2026-06-03T06:44:52.583513
-- =================================================

IF OBJECT_ID('dbo.Comercial_KPIs_Cache', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_KPIs_Cache;
GO

CREATE TABLE dbo.Comercial_KPIs_Cache (
    [CacheID] INT NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [PeriodoKey] VARCHAR(100) NOT NULL,
    [KPIsJSON] NVARCHAR(MAX) NULL,
    [UpdatedAt] DATETIME NULL DEFAULT (getdate()),
    [Status] VARCHAR(20) NULL DEFAULT ('online')
);
GO

ALTER TABLE dbo.Comercial_KPIs_Cache ADD CONSTRAINT [PK__Comercia__4EDCCD1359A398A1] PRIMARY KEY (CacheID);
CREATE UNIQUE INDEX [UQ_Comercial_KPIs_Cache] ON dbo.Comercial_KPIs_Cache (ServerID, PeriodoKey);
GO

-- =================================================
-- Tabla: Comercial_KPIs_Diarios_v2
-- Exportado: 2026-06-03T06:44:52.788665
-- =================================================

IF OBJECT_ID('dbo.Comercial_KPIs_Diarios_v2', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_KPIs_Diarios_v2;
GO

CREATE TABLE dbo.Comercial_KPIs_Diarios_v2 (
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
    [version] INT NULL DEFAULT ((1))
);
GO

CREATE INDEX [IX_KPIs_Diarios_v2_AnioMes] ON dbo.Comercial_KPIs_Diarios_v2 (anio, mes);
CREATE INDEX [IX_KPIs_Diarios_v2_Fecha] ON dbo.Comercial_KPIs_Diarios_v2 (fecha_operacion);
CREATE INDEX [IX_KPIs_Diarios_v2_Hash] ON dbo.Comercial_KPIs_Diarios_v2 (hash_origen);
CREATE INDEX [IX_KPIs_Diarios_v2_Unidad] ON dbo.Comercial_KPIs_Diarios_v2 (unidad_negocio_id);
ALTER TABLE dbo.Comercial_KPIs_Diarios_v2 ADD CONSTRAINT [PK__Comercia__3213E83F6AD04994] PRIMARY KEY (id);
CREATE UNIQUE INDEX [UQ_KPIs_Diarios_v2] ON dbo.Comercial_KPIs_Diarios_v2 (unidad_negocio_id, sucursal_id, fecha_operacion);
GO

-- =================================================
-- Tabla: Comercial_KPIs_Diarios_v2_backup_migracion_codigos_20260513_0558
-- Exportado: 2026-06-03T06:44:53.766673
-- =================================================

IF OBJECT_ID('dbo.Comercial_KPIs_Diarios_v2_backup_migracion_codigos_20260513_0558', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_KPIs_Diarios_v2_backup_migracion_codigos_20260513_0558;
GO

CREATE TABLE dbo.Comercial_KPIs_Diarios_v2_backup_migracion_codigos_20260513_0558 (
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

GO

-- =================================================
-- Tabla: Comercial_KPIs_Historico
-- Exportado: 2026-06-03T06:44:54.447451
-- =================================================

IF OBJECT_ID('dbo.Comercial_KPIs_Historico', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_KPIs_Historico;
GO

CREATE TABLE dbo.Comercial_KPIs_Historico (
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
    [updated_at] DATETIME2 NOT NULL DEFAULT (sysutcdatetime())
);
GO

CREATE INDEX [IX_Comercial_KPIs_Historico_Fecha] ON dbo.Comercial_KPIs_Historico (fecha);
CREATE INDEX [IX_Comercial_KPIs_Historico_RunId] ON dbo.Comercial_KPIs_Historico (run_id);
CREATE INDEX [IX_Comercial_KPIs_Historico_Server_Fecha] ON dbo.Comercial_KPIs_Historico (server_id, fecha);
ALTER TABLE dbo.Comercial_KPIs_Historico ADD CONSTRAINT [PK_Comercial_KPIs_Historico] PRIMARY KEY (id);
CREATE UNIQUE INDEX [UX_Comercial_KPIs_Historico] ON dbo.Comercial_KPIs_Historico (server_id, sucursal_id, system_type_normalized, fecha, kpi_tipo);
GO

-- =================================================
-- Tabla: Comercial_KPIs_Mensuales_v2
-- Exportado: 2026-06-03T06:44:55.800570
-- =================================================

IF OBJECT_ID('dbo.Comercial_KPIs_Mensuales_v2', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_KPIs_Mensuales_v2;
GO

CREATE TABLE dbo.Comercial_KPIs_Mensuales_v2 (
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
    [version] INT NULL DEFAULT ((1))
);
GO

CREATE INDEX [IX_KPIs_Mensuales_v2_AnioMes] ON dbo.Comercial_KPIs_Mensuales_v2 (anio, mes);
CREATE INDEX [IX_KPIs_Mensuales_v2_Unidad] ON dbo.Comercial_KPIs_Mensuales_v2 (unidad_negocio_id);
ALTER TABLE dbo.Comercial_KPIs_Mensuales_v2 ADD CONSTRAINT [PK__Comercia__3213E83F250489E7] PRIMARY KEY (id);
CREATE UNIQUE INDEX [UQ_KPIs_Mensuales_v2] ON dbo.Comercial_KPIs_Mensuales_v2 (unidad_negocio_id, sucursal_id, anio, mes);
GO

-- =================================================
-- Tabla: Comercial_Metas
-- Exportado: 2026-06-03T06:44:56.005195
-- =================================================

IF OBJECT_ID('dbo.Comercial_Metas', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_Metas;
GO

CREATE TABLE dbo.Comercial_Metas (
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
    [FechaModificacion] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.Comercial_Metas ADD CONSTRAINT [PK__Comercia__60EE57F8F546D714] PRIMARY KEY (MetaID);
CREATE UNIQUE INDEX [UQ_Comercial_Metas] ON dbo.Comercial_Metas (ServerID, Sucursal, Mes, Anio);
GO

-- =================================================
-- Tabla: Comercial_PreciosSugeridos
-- Exportado: 2026-06-03T06:44:56.209361
-- =================================================

IF OBJECT_ID('dbo.Comercial_PreciosSugeridos', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_PreciosSugeridos;
GO

CREATE TABLE dbo.Comercial_PreciosSugeridos (
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
    [PayloadAnalisisJSON] NVARCHAR(MAX) NULL
);
GO

ALTER TABLE dbo.Comercial_PreciosSugeridos ADD CONSTRAINT [PK__Comercia__5FE8ED1048F9D030] PRIMARY KEY (PrecioSugeridoID);
CREATE UNIQUE INDEX [UQ_PrecioSugerido_Producto] ON dbo.Comercial_PreciosSugeridos (ServerID, CodigoProducto, ReglaPrecioID);
GO

-- =================================================
-- Tabla: Comercial_PricingAnalisisIA
-- Exportado: 2026-06-03T06:44:56.415645
-- =================================================

IF OBJECT_ID('dbo.Comercial_PricingAnalisisIA', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_PricingAnalisisIA;
GO

CREATE TABLE dbo.Comercial_PricingAnalisisIA (
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
    [ListaCompetidoresID] UNIQUEIDENTIFIER NULL
);
GO

ALTER TABLE dbo.Comercial_PricingAnalisisIA ADD CONSTRAINT [PK__Comercia__CA03D84727C34C3F] PRIMARY KEY (AnalisisIAID);
GO

-- =================================================
-- Tabla: Comercial_PricingBenchmarkProducto
-- Exportado: 2026-06-03T06:44:56.653086
-- =================================================

IF OBJECT_ID('dbo.Comercial_PricingBenchmarkProducto', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_PricingBenchmarkProducto;
GO

CREATE TABLE dbo.Comercial_PricingBenchmarkProducto (
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
    [UsuarioModificacion] NVARCHAR(100) NULL
);
GO

ALTER TABLE dbo.Comercial_PricingBenchmarkProducto ADD CONSTRAINT [PK__Comercia__F5EB3B078298DA94] PRIMARY KEY (BenchmarkProductoID);
GO

-- =================================================
-- Tabla: Comercial_RecetasSnapshot
-- Exportado: 2026-06-03T06:44:56.896559
-- =================================================

IF OBJECT_ID('dbo.Comercial_RecetasSnapshot', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_RecetasSnapshot;
GO

CREATE TABLE dbo.Comercial_RecetasSnapshot (
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
    [SyncRunID] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_RecetasSnapshot_Actual] ON dbo.Comercial_RecetasSnapshot (ProductoClave, ServerID, EsActual);
CREATE INDEX [IX_RecetasSnapshot_Fecha] ON dbo.Comercial_RecetasSnapshot (FechaSnapshot);
CREATE INDEX [IX_RecetasSnapshot_Hash] ON dbo.Comercial_RecetasSnapshot (HashReceta);
CREATE INDEX [IX_RecetasSnapshot_Producto] ON dbo.Comercial_RecetasSnapshot (ProductoClave);
CREATE INDEX [IX_RecetasSnapshot_Server] ON dbo.Comercial_RecetasSnapshot (ServerID);
ALTER TABLE dbo.Comercial_RecetasSnapshot ADD CONSTRAINT [PK__Comercia__13C7E067D0E89B10] PRIMARY KEY (RecetaSnapshotID);
GO

-- =================================================
-- Tabla: Comercial_RecetasSnapshotDetalle
-- Exportado: 2026-06-03T06:44:57.110311
-- =================================================

IF OBJECT_ID('dbo.Comercial_RecetasSnapshotDetalle', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_RecetasSnapshotDetalle;
GO

CREATE TABLE dbo.Comercial_RecetasSnapshotDetalle (
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
    [Orden] INT NULL DEFAULT ((0))
);
GO

CREATE INDEX [IX_RecetasSnapshotDetalle_Costo] ON dbo.Comercial_RecetasSnapshotDetalle (RecetaSnapshotID, CostoTotal);
CREATE INDEX [IX_RecetasSnapshotDetalle_Insumo] ON dbo.Comercial_RecetasSnapshotDetalle (InsumoClave);
CREATE INDEX [IX_RecetasSnapshotDetalle_Snapshot] ON dbo.Comercial_RecetasSnapshotDetalle (RecetaSnapshotID);
ALTER TABLE dbo.Comercial_RecetasSnapshotDetalle ADD CONSTRAINT [PK__Comercia__895A214D01C4E9BB] PRIMARY KEY (RecetaSnapshotDetalleID);
GO

-- =================================================
-- Tabla: Comercial_ReglasPrecio
-- Exportado: 2026-06-03T06:44:57.315341
-- =================================================

IF OBJECT_ID('dbo.Comercial_ReglasPrecio', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_ReglasPrecio;
GO

CREATE TABLE dbo.Comercial_ReglasPrecio (
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
    [UsuarioModificacion] NVARCHAR(100) NULL
);
GO

ALTER TABLE dbo.Comercial_ReglasPrecio ADD CONSTRAINT [PK__Comercia__0BFB5A2D9C4B539F] PRIMARY KEY (ReglaPrecioID);
CREATE UNIQUE INDEX [UQ__Comercia__06370DACA6E08E53] ON dbo.Comercial_ReglasPrecio (Codigo);
GO

-- =================================================
-- Tabla: Comercial_ReglasPrecioRangos
-- Exportado: 2026-06-03T06:44:57.553609
-- =================================================

IF OBJECT_ID('dbo.Comercial_ReglasPrecioRangos', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_ReglasPrecioRangos;
GO

CREATE TABLE dbo.Comercial_ReglasPrecioRangos (
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
    [UsuarioModificacion] NVARCHAR(100) NULL
);
GO

ALTER TABLE dbo.Comercial_ReglasPrecioRangos ADD CONSTRAINT [PK__Comercia__7A53FCFF0E75DEBE] PRIMARY KEY (ReglaPrecioRangoID);
CREATE UNIQUE INDEX [UQ_Rango_Orden] ON dbo.Comercial_ReglasPrecioRangos (ReglaPrecioID, Orden);
GO

-- =================================================
-- Tabla: Comercial_SimulacionesPrecios
-- Exportado: 2026-06-03T06:44:57.790595
-- =================================================

IF OBJECT_ID('dbo.Comercial_SimulacionesPrecios', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_SimulacionesPrecios;
GO

CREATE TABLE dbo.Comercial_SimulacionesPrecios (
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
    [IPSimulacion] VARCHAR(50) NULL
);
GO

CREATE INDEX [IX_Simulaciones_Fecha] ON dbo.Comercial_SimulacionesPrecios (FechaSimulacion);
CREATE INDEX [IX_Simulaciones_ProductoID] ON dbo.Comercial_SimulacionesPrecios (ProductoID);
CREATE INDEX [IX_Simulaciones_Usuario] ON dbo.Comercial_SimulacionesPrecios (UsuarioID);
ALTER TABLE dbo.Comercial_SimulacionesPrecios ADD CONSTRAINT [PK__Comercia__0A61BC9906487F57] PRIMARY KEY (SimulacionID);
GO

-- =================================================
-- Tabla: Comercial_SolicitudesCambioPrecio
-- Exportado: 2026-06-03T06:44:57.996060
-- =================================================

IF OBJECT_ID('dbo.Comercial_SolicitudesCambioPrecio', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_SolicitudesCambioPrecio;
GO

CREATE TABLE dbo.Comercial_SolicitudesCambioPrecio (
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
    [IPCreacion] VARCHAR(50) NULL
);
GO

CREATE INDEX [IX_SolicitudesCambioPrecio_Estatus] ON dbo.Comercial_SolicitudesCambioPrecio (Estatus);
CREATE INDEX [IX_SolicitudesCambioPrecio_Fecha] ON dbo.Comercial_SolicitudesCambioPrecio (FechaSolicitud);
CREATE INDEX [IX_SolicitudesCambioPrecio_ProductoID] ON dbo.Comercial_SolicitudesCambioPrecio (ProductoID);
CREATE INDEX [IX_SolicitudesCambioPrecio_ServerID] ON dbo.Comercial_SolicitudesCambioPrecio (ServerID);
CREATE INDEX [IX_SolicitudesCambioPrecio_Solicitante] ON dbo.Comercial_SolicitudesCambioPrecio (SolicitanteUsuarioID);
ALTER TABLE dbo.Comercial_SolicitudesCambioPrecio ADD CONSTRAINT [PK__Comercia__85E95DA788204E5D] PRIMARY KEY (SolicitudID);
GO

-- =================================================
-- Tabla: Comercial_SolicitudesCambioPrecioHistorial
-- Exportado: 2026-06-03T06:44:58.234838
-- =================================================

IF OBJECT_ID('dbo.Comercial_SolicitudesCambioPrecioHistorial', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_SolicitudesCambioPrecioHistorial;
GO

CREATE TABLE dbo.Comercial_SolicitudesCambioPrecioHistorial (
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
    [UserAgent] NVARCHAR(500) NULL
);
GO

CREATE INDEX [IX_HistorialSolicitudes_Fecha] ON dbo.Comercial_SolicitudesCambioPrecioHistorial (FechaAccion);
CREATE INDEX [IX_HistorialSolicitudes_SolicitudID] ON dbo.Comercial_SolicitudesCambioPrecioHistorial (SolicitudID);
ALTER TABLE dbo.Comercial_SolicitudesCambioPrecioHistorial ADD CONSTRAINT [PK__Comercia__975206EF7724C4D5] PRIMARY KEY (HistorialID);
GO

-- =================================================
-- Tabla: Comercial_SyncLog_v2
-- Exportado: 2026-06-03T06:44:58.471766
-- =================================================

IF OBJECT_ID('dbo.Comercial_SyncLog_v2', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_SyncLog_v2;
GO

CREATE TABLE dbo.Comercial_SyncLog_v2 (
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
    [created_at] DATETIME2 NULL DEFAULT (sysutcdatetime())
);
GO

CREATE INDEX [IX_SyncLog_v2_RunId] ON dbo.Comercial_SyncLog_v2 (run_id);
CREATE INDEX [IX_SyncLog_v2_Status] ON dbo.Comercial_SyncLog_v2 (status);
CREATE INDEX [IX_SyncLog_v2_Timestamp] ON dbo.Comercial_SyncLog_v2 (run_timestamp);
CREATE INDEX [IX_SyncLog_v2_Unidad] ON dbo.Comercial_SyncLog_v2 (unidad_negocio_id);
ALTER TABLE dbo.Comercial_SyncLog_v2 ADD CONSTRAINT [PK__Comercia__3213E83F2D601C70] PRIMARY KEY (id);
GO

-- =================================================
-- Tabla: Comercial_SyncLog_v2_backup_migracion_codigos_20260513_0558
-- Exportado: 2026-06-03T06:45:05.086058
-- =================================================

IF OBJECT_ID('dbo.Comercial_SyncLog_v2_backup_migracion_codigos_20260513_0558', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_SyncLog_v2_backup_migracion_codigos_20260513_0558;
GO

CREATE TABLE dbo.Comercial_SyncLog_v2_backup_migracion_codigos_20260513_0558 (
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

GO

-- =================================================
-- Tabla: Comercial_Ventas_Dia_Abiertas_v2
-- Exportado: 2026-06-03T06:45:05.770384
-- =================================================

IF OBJECT_ID('dbo.Comercial_Ventas_Dia_Abiertas_v2', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_Ventas_Dia_Abiertas_v2;
GO

CREATE TABLE dbo.Comercial_Ventas_Dia_Abiertas_v2 (
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
    [fecha_ultima_actualizacion] DATETIME2 NULL DEFAULT (sysutcdatetime())
);
GO

CREATE INDEX [IX_Ventas_Dia_v2_Snapshot] ON dbo.Comercial_Ventas_Dia_Abiertas_v2 (snapshot_timestamp);
ALTER TABLE dbo.Comercial_Ventas_Dia_Abiertas_v2 ADD CONSTRAINT [PK__Comercia__3213E83F3864FB09] PRIMARY KEY (id);
CREATE UNIQUE INDEX [UQ_Ventas_Dia_v2_Unidad] ON dbo.Comercial_Ventas_Dia_Abiertas_v2 (unidad_negocio_id, sucursal_id);
GO

-- =================================================
-- Tabla: Comercial_Ventas_Dia_Abiertas_v2_Backup_FechaOperacion_20260521
-- Exportado: 2026-06-03T06:45:06.006634
-- =================================================

IF OBJECT_ID('dbo.Comercial_Ventas_Dia_Abiertas_v2_Backup_FechaOperacion_20260521', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_Ventas_Dia_Abiertas_v2_Backup_FechaOperacion_20260521;
GO

CREATE TABLE dbo.Comercial_Ventas_Dia_Abiertas_v2_Backup_FechaOperacion_20260521 (
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

GO

-- =================================================
-- Tabla: Comercial_Ventas_Dia_Abiertas_v2_backup_migracion_codigos_20260513_0558
-- Exportado: 2026-06-03T06:45:06.242972
-- =================================================

IF OBJECT_ID('dbo.Comercial_Ventas_Dia_Abiertas_v2_backup_migracion_codigos_20260513_0558', 'U') IS NOT NULL
    DROP TABLE dbo.Comercial_Ventas_Dia_Abiertas_v2_backup_migracion_codigos_20260513_0558;
GO

CREATE TABLE dbo.Comercial_Ventas_Dia_Abiertas_v2_backup_migracion_codigos_20260513_0558 (
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

GO

-- =================================================
-- Tabla: Compras
-- Exportado: 2026-06-03T06:45:06.479519
-- =================================================

IF OBJECT_ID('dbo.Compras', 'U') IS NOT NULL
    DROP TABLE dbo.Compras;
GO

CREATE TABLE dbo.Compras (
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
    [RowVer] TIMESTAMP NOT NULL
);
GO

CREATE INDEX [IX_Compras_Estatus] ON dbo.Compras (EstatusCompraID, FechaCompra);
CREATE INDEX [IX_Compras_OrdenCompraID] ON dbo.Compras (OrdenCompraID);
CREATE INDEX [IX_Compras_Proveedor_Fecha] ON dbo.Compras (ProveedorID, FechaCompra);
CREATE INDEX [IX_Compras_UUIDFactura] ON dbo.Compras (UUIDFactura);
ALTER TABLE dbo.Compras ADD CONSTRAINT [PK_Compras] PRIMARY KEY (CompraID);
CREATE UNIQUE INDEX [UQ_Compras_FolioCompra] ON dbo.Compras (FolioCompra);
GO

-- =================================================
-- Tabla: Compras_ConciliacionSAT
-- Exportado: 2026-06-03T06:45:06.688313
-- =================================================

IF OBJECT_ID('dbo.Compras_ConciliacionSAT', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_ConciliacionSAT;
GO

CREATE TABLE dbo.Compras_ConciliacionSAT (
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
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

CREATE INDEX [IX_Compras_ConciliacionSAT_Documento] ON dbo.Compras_ConciliacionSAT (DocumentoFiscalID, EstatusConciliacionSATID, FechaConciliacion);
CREATE INDEX [IX_Compras_ConciliacionSAT_Recepcion] ON dbo.Compras_ConciliacionSAT (RecepcionCompraID, FechaConciliacion);
ALTER TABLE dbo.Compras_ConciliacionSAT ADD CONSTRAINT [PK_Compras_ConciliacionSAT] PRIMARY KEY (ConciliacionSATID);
GO

-- =================================================
-- Tabla: Compras_ConciliacionSATDetalle
-- Exportado: 2026-06-03T06:45:06.893864
-- =================================================

IF OBJECT_ID('dbo.Compras_ConciliacionSATDetalle', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_ConciliacionSATDetalle;
GO

CREATE TABLE dbo.Compras_ConciliacionSATDetalle (
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
    [Observaciones] VARCHAR(1000) NULL
);
GO

CREATE INDEX [IX_Compras_ConciliacionSATDetalle_Conciliacion] ON dbo.Compras_ConciliacionSATDetalle (ConciliacionSATID, DocumentoFiscalDetalleID);
ALTER TABLE dbo.Compras_ConciliacionSATDetalle ADD CONSTRAINT [PK_Compras_ConciliacionSATDetalle] PRIMARY KEY (ConciliacionSATDetalleID);
GO

-- =================================================
-- Tabla: Compras_ConciliacionSATEstatus
-- Exportado: 2026-06-03T06:45:07.097910
-- =================================================

IF OBJECT_ID('dbo.Compras_ConciliacionSATEstatus', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_ConciliacionSATEstatus;
GO

CREATE TABLE dbo.Compras_ConciliacionSATEstatus (
    [EstatusConciliacionSATID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(40) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Compras_ConciliacionSATEstatus ADD CONSTRAINT [PK_Compras_ConciliacionSATEstatus] PRIMARY KEY (EstatusConciliacionSATID);
CREATE UNIQUE INDEX [UQ_Compras_ConciliacionSATEstatus_Descripcion] ON dbo.Compras_ConciliacionSATEstatus (Descripcion);
GO

-- =================================================
-- Tabla: Compras_Detalle
-- Exportado: 2026-06-03T06:45:07.333887
-- =================================================

IF OBJECT_ID('dbo.Compras_Detalle', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_Detalle;
GO

CREATE TABLE dbo.Compras_Detalle (
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
    [RowVer] TIMESTAMP NOT NULL
);
GO

CREATE INDEX [IX_Compras_Detalle_OrdenDetalle] ON dbo.Compras_Detalle (OrdenDetalleCompraID);
CREATE INDEX [IX_Compras_Detalle_PedidoDetalle] ON dbo.Compras_Detalle (PedidoDetalleCompraID);
CREATE INDEX [IX_Compras_Detalle_Producto] ON dbo.Compras_Detalle (ProductoID, PresentacionProductoID);
ALTER TABLE dbo.Compras_Detalle ADD CONSTRAINT [PK_Compras_Detalle] PRIMARY KEY (DetalleCompraID);
CREATE UNIQUE INDEX [UQ_Compras_Detalle_Renglon] ON dbo.Compras_Detalle (CompraID, Renglon);
GO

-- =================================================
-- Tabla: Compras_DocumentosFiscales
-- Exportado: 2026-06-03T06:45:07.540364
-- =================================================

IF OBJECT_ID('dbo.Compras_DocumentosFiscales', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_DocumentosFiscales;
GO

CREATE TABLE dbo.Compras_DocumentosFiscales (
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
    [ModifiedAt] DATETIME2 NULL
);
GO

CREATE INDEX [IX_Compras_DocumentosFiscales_Estatus] ON dbo.Compras_DocumentosFiscales (EstatusDocumentoFiscalID, FechaDescarga);
CREATE INDEX [IX_Compras_DocumentosFiscales_Proveedor] ON dbo.Compras_DocumentosFiscales (UUID, Total, RFCEmisor, RFCReceptor, ProveedorID, FechaEmision);
CREATE INDEX [IX_Compras_DocumentosFiscales_RFCEmisorFecha] ON dbo.Compras_DocumentosFiscales (RFCEmisor, FechaEmision);
CREATE INDEX [IX_Compras_DocumentosFiscales_SucursalFecha] ON dbo.Compras_DocumentosFiscales (UUID, Total, ProveedorID, EstatusDocumentoFiscalID, SucursalID, FechaEmision);
CREATE INDEX [IX_Compras_DocumentosFiscales_UUID] ON dbo.Compras_DocumentosFiscales (UUID);
ALTER TABLE dbo.Compras_DocumentosFiscales ADD CONSTRAINT [PK_Compras_DocumentosFiscales] PRIMARY KEY (DocumentoFiscalID);
CREATE UNIQUE INDEX [UQ_Compras_DocumentosFiscales_UUID] ON dbo.Compras_DocumentosFiscales (UUID);
GO

-- =================================================
-- Tabla: Compras_DocumentosFiscalesDetalle
-- Exportado: 2026-06-03T06:45:07.747249
-- =================================================

IF OBJECT_ID('dbo.Compras_DocumentosFiscalesDetalle', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_DocumentosFiscalesDetalle;
GO

CREATE TABLE dbo.Compras_DocumentosFiscalesDetalle (
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
    [PresentacionProductoID] BIGINT NULL
);
GO

CREATE INDEX [IX_Compras_DocumentosFiscalesDetalle_Documento] ON dbo.Compras_DocumentosFiscalesDetalle (DocumentoFiscalID, Renglon);
ALTER TABLE dbo.Compras_DocumentosFiscalesDetalle ADD CONSTRAINT [PK_Compras_DocumentosFiscalesDetalle] PRIMARY KEY (DocumentoFiscalDetalleID);
CREATE UNIQUE INDEX [UQ_Compras_DocumentosFiscalesDetalle_Renglon] ON dbo.Compras_DocumentosFiscalesDetalle (DocumentoFiscalID, Renglon);
GO

-- =================================================
-- Tabla: Compras_DocumentosFiscalesEstatus
-- Exportado: 2026-06-03T06:45:07.952015
-- =================================================

IF OBJECT_ID('dbo.Compras_DocumentosFiscalesEstatus', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_DocumentosFiscalesEstatus;
GO

CREATE TABLE dbo.Compras_DocumentosFiscalesEstatus (
    [EstatusDocumentoFiscalID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(40) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Compras_DocumentosFiscalesEstatus ADD CONSTRAINT [PK_Compras_DocumentosFiscalesEstatus] PRIMARY KEY (EstatusDocumentoFiscalID);
CREATE UNIQUE INDEX [UQ_Compras_DocumentosFiscalesEstatus_Descripcion] ON dbo.Compras_DocumentosFiscalesEstatus (Descripcion);
GO

-- =================================================
-- Tabla: Compras_Estatus
-- Exportado: 2026-06-03T06:45:08.187620
-- =================================================

IF OBJECT_ID('dbo.Compras_Estatus', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_Estatus;
GO

CREATE TABLE dbo.Compras_Estatus (
    [EstatusCompraID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Compras_Estatus ADD CONSTRAINT [PK_Compras_Estatus] PRIMARY KEY (EstatusCompraID);
CREATE UNIQUE INDEX [UQ_Compras_Estatus_Descripcion] ON dbo.Compras_Estatus (Descripcion);
GO

-- =================================================
-- Tabla: Compras_Eventos_Pendientes
-- Exportado: 2026-06-03T06:45:08.424755
-- =================================================

IF OBJECT_ID('dbo.Compras_Eventos_Pendientes', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_Eventos_Pendientes;
GO

CREATE TABLE dbo.Compras_Eventos_Pendientes (
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
    [CreatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

CREATE INDEX [IX_Eventos_Pendientes] ON dbo.Compras_Eventos_Pendientes (Procesado, CreatedAt);
CREATE INDEX [IX_Eventos_Server] ON dbo.Compras_Eventos_Pendientes (ServerID, EventoTipo);
ALTER TABLE dbo.Compras_Eventos_Pendientes ADD CONSTRAINT [PK__Compras___1EEB59014837C836] PRIMARY KEY (EventoID);
GO

-- =================================================
-- Tabla: Compras_Informes_Config
-- Exportado: 2026-06-03T06:45:08.630773
-- =================================================

IF OBJECT_ID('dbo.Compras_Informes_Config', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_Informes_Config;
GO

CREATE TABLE dbo.Compras_Informes_Config (
    [ConfigID] INT NOT NULL,
    [EventoTipo] NVARCHAR(50) NOT NULL,
    [InformeTipo] NVARCHAR(100) NOT NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [WebhookURL] NVARCHAR(500) NULL,
    [EmailDestinatarios] NVARCHAR(500) NULL,
    [ConfigJSON] NVARCHAR(MAX) NULL,
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    [UpdatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.Compras_Informes_Config ADD CONSTRAINT [PK__Compras___C3BC333C32016CFA] PRIMARY KEY (ConfigID);
GO

-- =================================================
-- Tabla: Compras_Inventarios_Fisicos_Sync
-- Exportado: 2026-06-03T06:45:08.834428
-- =================================================

IF OBJECT_ID('dbo.Compras_Inventarios_Fisicos_Sync', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_Inventarios_Fisicos_Sync;
GO

CREATE TABLE dbo.Compras_Inventarios_Fisicos_Sync (
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
    [sync_status] VARCHAR(20) NULL DEFAULT ('ACTIVE')
);
GO

CREATE INDEX [IX_InvFisico_Fecha] ON dbo.Compras_Inventarios_Fisicos_Sync (fecha);
CREATE INDEX [IX_InvFisico_Server] ON dbo.Compras_Inventarios_Fisicos_Sync (server_id);
CREATE INDEX [IX_InvFisico_Unidad] ON dbo.Compras_Inventarios_Fisicos_Sync (unidad_negocio_id);
ALTER TABLE dbo.Compras_Inventarios_Fisicos_Sync ADD CONSTRAINT [PK__Compras___3213E83F5874E971] PRIMARY KEY (id);
CREATE UNIQUE INDEX [UQ_InvFisico_Folio_Server] ON dbo.Compras_Inventarios_Fisicos_Sync (folio, server_id);
GO

-- =================================================
-- Tabla: Compras_KPIs_Historico
-- Exportado: 2026-06-03T06:45:09.115554
-- =================================================

IF OBJECT_ID('dbo.Compras_KPIs_Historico', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_KPIs_Historico;
GO

CREATE TABLE dbo.Compras_KPIs_Historico (
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
    [updated_at] DATETIME NULL DEFAULT (getdate())
);
GO

CREATE INDEX [IX_Compras_KPIs_Fecha] ON dbo.Compras_KPIs_Historico (fecha);
CREATE INDEX [IX_Compras_KPIs_Tipo] ON dbo.Compras_KPIs_Historico (kpi_tipo);
CREATE UNIQUE INDEX [IX_Compras_KPIs_Unique] ON dbo.Compras_KPIs_Historico (server_id, sucursal_id, fecha, kpi_tipo);
ALTER TABLE dbo.Compras_KPIs_Historico ADD CONSTRAINT [PK__Compras___3213E83F86B80690] PRIMARY KEY (id);
GO

-- =================================================
-- Tabla: Compras_Ordenes
-- Exportado: 2026-06-03T06:45:10.739790
-- =================================================

IF OBJECT_ID('dbo.Compras_Ordenes', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_Ordenes;
GO

CREATE TABLE dbo.Compras_Ordenes (
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
    [RowVer] TIMESTAMP NOT NULL
);
GO

CREATE INDEX [IX_Compras_Ordenes_Autorizacion] ON dbo.Compras_Ordenes (AutorizacionID);
CREATE INDEX [IX_Compras_Ordenes_Estatus] ON dbo.Compras_Ordenes (EstatusOrdenCompraID, FechaOrden);
CREATE INDEX [IX_Compras_Ordenes_Pedido] ON dbo.Compras_Ordenes (PedidoCompraID);
CREATE INDEX [IX_Compras_Ordenes_Proveedor_Fecha] ON dbo.Compras_Ordenes (ProveedorID, FechaOrden);
ALTER TABLE dbo.Compras_Ordenes ADD CONSTRAINT [PK_Compras_Ordenes] PRIMARY KEY (OrdenCompraID);
CREATE UNIQUE INDEX [UQ_Compras_Ordenes_FolioOrden] ON dbo.Compras_Ordenes (FolioOrden);
GO

-- =================================================
-- Tabla: Compras_OrdenesDetalle
-- Exportado: 2026-06-03T06:45:10.944438
-- =================================================

IF OBJECT_ID('dbo.Compras_OrdenesDetalle', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_OrdenesDetalle;
GO

CREATE TABLE dbo.Compras_OrdenesDetalle (
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
    [RowVer] TIMESTAMP NOT NULL
);
GO

CREATE INDEX [IX_Compras_OrdenesDetalle_PedidoDetalle] ON dbo.Compras_OrdenesDetalle (PedidoDetalleCompraID);
CREATE INDEX [IX_Compras_OrdenesDetalle_Producto] ON dbo.Compras_OrdenesDetalle (ProductoID, PresentacionProductoID);
ALTER TABLE dbo.Compras_OrdenesDetalle ADD CONSTRAINT [PK_Compras_OrdenesDetalle] PRIMARY KEY (DetalleOrdenCompraID);
CREATE UNIQUE INDEX [UQ_Compras_OrdenesDetalle_Renglon] ON dbo.Compras_OrdenesDetalle (OrdenCompraID, Renglon);
GO

-- =================================================
-- Tabla: Compras_OrdenesEstatus
-- Exportado: 2026-06-03T06:45:11.150137
-- =================================================

IF OBJECT_ID('dbo.Compras_OrdenesEstatus', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_OrdenesEstatus;
GO

CREATE TABLE dbo.Compras_OrdenesEstatus (
    [EstatusOrdenCompraID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Compras_OrdenesEstatus ADD CONSTRAINT [PK_Compras_OrdenesEstatus] PRIMARY KEY (EstatusOrdenCompraID);
CREATE UNIQUE INDEX [UQ_Compras_OrdenesEstatus_Descripcion] ON dbo.Compras_OrdenesEstatus (Descripcion);
GO

-- =================================================
-- Tabla: Compras_Parametros_Sucursal
-- Exportado: 2026-06-03T06:45:11.385929
-- =================================================

IF OBJECT_ID('dbo.Compras_Parametros_Sucursal', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_Parametros_Sucursal;
GO

CREATE TABLE dbo.Compras_Parametros_Sucursal (
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
    [FechaModificacion] DATETIME NOT NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.Compras_Parametros_Sucursal ADD CONSTRAINT [PK__Compras___2B3CE672CB3F7213] PRIMARY KEY (ParametroID);
CREATE UNIQUE INDEX [UQ_Compras_Parametros_Server_Sucursal] ON dbo.Compras_Parametros_Sucursal (ServerID, SucursalID);
GO

-- =================================================
-- Tabla: Compras_Pedidos
-- Exportado: 2026-06-03T06:45:11.624281
-- =================================================

IF OBJECT_ID('dbo.Compras_Pedidos', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_Pedidos;
GO

CREATE TABLE dbo.Compras_Pedidos (
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
    [RowVer] TIMESTAMP NOT NULL
);
GO

CREATE INDEX [IX_Compras_Pedidos_Autorizacion] ON dbo.Compras_Pedidos (AutorizacionID);
CREATE INDEX [IX_Compras_Pedidos_Estatus] ON dbo.Compras_Pedidos (EstatusPedidoCompraID, FechaPedido);
CREATE INDEX [IX_Compras_Pedidos_Sucursal_Fecha] ON dbo.Compras_Pedidos (SucursalID, FechaPedido);
ALTER TABLE dbo.Compras_Pedidos ADD CONSTRAINT [PK_Compras_Pedidos] PRIMARY KEY (PedidoCompraID);
CREATE UNIQUE INDEX [UQ_Compras_Pedidos_FolioPedido] ON dbo.Compras_Pedidos (FolioPedido);
GO

-- =================================================
-- Tabla: Compras_PedidosDetalle
-- Exportado: 2026-06-03T06:45:11.830190
-- =================================================

IF OBJECT_ID('dbo.Compras_PedidosDetalle', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_PedidosDetalle;
GO

CREATE TABLE dbo.Compras_PedidosDetalle (
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
    [RowVer] TIMESTAMP NOT NULL
);
GO

CREATE INDEX [IX_Compras_PedidosDetalle_Producto] ON dbo.Compras_PedidosDetalle (ProductoID, PresentacionProductoID);
ALTER TABLE dbo.Compras_PedidosDetalle ADD CONSTRAINT [PK_Compras_PedidosDetalle] PRIMARY KEY (DetallePedidoCompraID);
CREATE UNIQUE INDEX [UQ_Compras_PedidosDetalle_Renglon] ON dbo.Compras_PedidosDetalle (PedidoCompraID, Renglon);
GO

-- =================================================
-- Tabla: Compras_PedidosEstatus
-- Exportado: 2026-06-03T06:45:12.034747
-- =================================================

IF OBJECT_ID('dbo.Compras_PedidosEstatus', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_PedidosEstatus;
GO

CREATE TABLE dbo.Compras_PedidosEstatus (
    [EstatusPedidoCompraID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Compras_PedidosEstatus ADD CONSTRAINT [PK_Compras_PedidosEstatus] PRIMARY KEY (EstatusPedidoCompraID);
CREATE UNIQUE INDEX [UQ_Compras_PedidosEstatus_Descripcion] ON dbo.Compras_PedidosEstatus (Descripcion);
GO

-- =================================================
-- Tabla: Compras_Recepciones
-- Exportado: 2026-06-03T06:45:12.271064
-- =================================================

IF OBJECT_ID('dbo.Compras_Recepciones', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_Recepciones;
GO

CREATE TABLE dbo.Compras_Recepciones (
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
    [ModifiedAt] DATETIME2 NULL
);
GO

CREATE INDEX [IX_Compras_Recepciones_Estatus] ON dbo.Compras_Recepciones (EstatusRecepcionID, FechaRecepcion);
CREATE INDEX [IX_Compras_Recepciones_ProveedorFecha] ON dbo.Compras_Recepciones (ProveedorID, FechaRecepcion);
CREATE INDEX [IX_Compras_Recepciones_SucursalAlmacenFecha] ON dbo.Compras_Recepciones (SucursalID, AlmacenID, FechaRecepcion);
ALTER TABLE dbo.Compras_Recepciones ADD CONSTRAINT [PK_Compras_Recepciones] PRIMARY KEY (RecepcionCompraID);
CREATE UNIQUE INDEX [UQ_Compras_Recepciones_Folio] ON dbo.Compras_Recepciones (FolioRecepcion);
GO

-- =================================================
-- Tabla: Compras_RecepcionesDetalle
-- Exportado: 2026-06-03T06:45:12.475221
-- =================================================

IF OBJECT_ID('dbo.Compras_RecepcionesDetalle', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_RecepcionesDetalle;
GO

CREATE TABLE dbo.Compras_RecepcionesDetalle (
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
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

CREATE INDEX [IX_Compras_RecepcionesDetalle_Producto] ON dbo.Compras_RecepcionesDetalle (ProductoID, PresentacionProductoID, RecepcionCompraID);
ALTER TABLE dbo.Compras_RecepcionesDetalle ADD CONSTRAINT [PK_Compras_RecepcionesDetalle] PRIMARY KEY (RecepcionDetalleID);
CREATE UNIQUE INDEX [UQ_Compras_RecepcionesDetalle_Renglon] ON dbo.Compras_RecepcionesDetalle (RecepcionCompraID, Renglon);
GO

-- =================================================
-- Tabla: Compras_RecepcionesEstatus
-- Exportado: 2026-06-03T06:45:12.679194
-- =================================================

IF OBJECT_ID('dbo.Compras_RecepcionesEstatus', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_RecepcionesEstatus;
GO

CREATE TABLE dbo.Compras_RecepcionesEstatus (
    [EstatusRecepcionID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Compras_RecepcionesEstatus ADD CONSTRAINT [PK_Compras_RecepcionesEstatus] PRIMARY KEY (EstatusRecepcionID);
CREATE UNIQUE INDEX [UQ_Compras_RecepcionesEstatus_Descripcion] ON dbo.Compras_RecepcionesEstatus (Descripcion);
GO

-- =================================================
-- Tabla: Compras_Requisiciones_Sync
-- Exportado: 2026-06-03T06:45:12.915159
-- =================================================

IF OBJECT_ID('dbo.Compras_Requisiciones_Sync', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_Requisiciones_Sync;
GO

CREATE TABLE dbo.Compras_Requisiciones_Sync (
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
    [sync_status] VARCHAR(20) NULL DEFAULT ('ACTIVE')
);
GO

CREATE INDEX [IX_Requi_Fecha] ON dbo.Compras_Requisiciones_Sync (fecha);
CREATE INDEX [IX_Requi_Server] ON dbo.Compras_Requisiciones_Sync (server_id);
CREATE INDEX [IX_Requi_Unidad] ON dbo.Compras_Requisiciones_Sync (unidad_negocio_id);
ALTER TABLE dbo.Compras_Requisiciones_Sync ADD CONSTRAINT [PK__Compras___3213E83F616A1BE3] PRIMARY KEY (id);
CREATE UNIQUE INDEX [UQ_Requi_Folio_Server] ON dbo.Compras_Requisiciones_Sync (folio, server_id, tipo);
GO

-- =================================================
-- Tabla: Compras_Sync_Checkpoint
-- Exportado: 2026-06-03T06:45:13.122077
-- =================================================

IF OBJECT_ID('dbo.Compras_Sync_Checkpoint', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_Sync_Checkpoint;
GO

CREATE TABLE dbo.Compras_Sync_Checkpoint (
    [CheckpointID] INT NOT NULL,
    [ServerID] NVARCHAR(36) NOT NULL,
    [ServerName] NVARCHAR(100) NULL,
    [SyncType] NVARCHAR(50) NOT NULL,
    [LastFolio] NVARCHAR(50) NULL,
    [LastFecha] DATETIME NULL,
    [LastSyncAt] DATETIME NULL,
    [RecordsFoundLastSync] INT NULL DEFAULT ((0)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    [UpdatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.Compras_Sync_Checkpoint ADD CONSTRAINT [PK__Compras___6C00DF82B118131C] PRIMARY KEY (CheckpointID);
CREATE UNIQUE INDEX [UQ_Checkpoint_Server_Type] ON dbo.Compras_Sync_Checkpoint (ServerID, SyncType);
GO

-- =================================================
-- Tabla: Compras_Sync_Log
-- Exportado: 2026-06-03T06:45:13.327308
-- =================================================

IF OBJECT_ID('dbo.Compras_Sync_Log', 'U') IS NOT NULL
    DROP TABLE dbo.Compras_Sync_Log;
GO

CREATE TABLE dbo.Compras_Sync_Log (
    [id] INT NOT NULL,
    [unidad_negocio_id] VARCHAR(50) NULL,
    [server_id] VARCHAR(50) NULL,
    [sync_type] VARCHAR(50) NULL,
    [sync_start] DATETIME NULL,
    [sync_end] DATETIME NULL,
    [records_synced] INT NULL DEFAULT ((0)),
    [status] VARCHAR(20) NULL,
    [error_message] TEXT NULL,
    [created_at] DATETIME NULL DEFAULT (getdate())
);
GO

CREATE INDEX [IX_SyncLog_Date] ON dbo.Compras_Sync_Log (created_at);
CREATE INDEX [IX_SyncLog_Server] ON dbo.Compras_Sync_Log (server_id);
ALTER TABLE dbo.Compras_Sync_Log ADD CONSTRAINT [PK__Compras___3213E83FB16E4B5F] PRIMARY KEY (id);
GO

-- =================================================
-- Tabla: Config_Asignaciones
-- Exportado: 2026-06-03T06:45:13.565926
-- =================================================

IF OBJECT_ID('dbo.Config_Asignaciones', 'U') IS NOT NULL
    DROP TABLE dbo.Config_Asignaciones;
GO

CREATE TABLE dbo.Config_Asignaciones (
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
    [UsuarioModificacion] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_Config_ServerAlmacen] ON dbo.Config_Asignaciones (ServerID, AlmacenID);
ALTER TABLE dbo.Config_Asignaciones ADD CONSTRAINT [PK__Config_A__3214EC27D6A99813] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ__Config_A__C3BC333D3B751AA0] ON dbo.Config_Asignaciones (ConfigID);
GO

-- =================================================
-- Tabla: Config_Horarios
-- Exportado: 2026-06-03T06:45:13.771564
-- =================================================

IF OBJECT_ID('dbo.Config_Horarios', 'U') IS NOT NULL
    DROP TABLE dbo.Config_Horarios;
GO

CREATE TABLE dbo.Config_Horarios (
    [Id] INT NOT NULL,
    [TenantID] INT NOT NULL,
    [NombrePeriodo] NVARCHAR(50) NULL,
    [HoraInicio] TIME NULL,
    [HoraFin] TIME NULL
);
GO

ALTER TABLE dbo.Config_Horarios ADD CONSTRAINT [PK__Config_H__3214EC07D6DD9F6D] PRIMARY KEY (Id);
GO

-- =================================================
-- Tabla: Configuracion_Operativa
-- Exportado: 2026-06-03T06:45:14.007468
-- =================================================

IF OBJECT_ID('dbo.Configuracion_Operativa', 'U') IS NOT NULL
    DROP TABLE dbo.Configuracion_Operativa;
GO

CREATE TABLE dbo.Configuracion_Operativa (
    [ID] INT NOT NULL,
    [Clave] VARCHAR(100) NOT NULL,
    [Valor] VARCHAR(500) NULL,
    [Tipo] VARCHAR(20) NULL DEFAULT ('string'),
    [Descripcion] VARCHAR(500) NULL,
    [FechaActualizacion] DATETIME2 NULL DEFAULT (getutcdate())
);
GO

ALTER TABLE dbo.Configuracion_Operativa ADD CONSTRAINT [PK__Configur__3214EC275217AE5D] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ__Configur__E8181E11C0D6A419] ON dbo.Configuracion_Operativa (Clave);
GO

-- =================================================
-- Tabla: ConsultasSQL_Catalogo
-- Exportado: 2026-06-03T06:45:14.243716
-- =================================================

IF OBJECT_ID('dbo.ConsultasSQL_Catalogo', 'U') IS NOT NULL
    DROP TABLE dbo.ConsultasSQL_Catalogo;
GO

CREATE TABLE dbo.ConsultasSQL_Catalogo (
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
    [UsuarioModificacionID] NVARCHAR(100) NULL
);
GO

CREATE INDEX [IX_ConsultasSQL_Activo] ON dbo.ConsultasSQL_Catalogo (Activo);
CREATE INDEX [IX_ConsultasSQL_EsSistema] ON dbo.ConsultasSQL_Catalogo (EsSistema);
CREATE INDEX [IX_ConsultasSQL_Modulo] ON dbo.ConsultasSQL_Catalogo (Modulo);
CREATE INDEX [IX_ConsultasSQL_Sistema] ON dbo.ConsultasSQL_Catalogo (SistemaTipoID);
ALTER TABLE dbo.ConsultasSQL_Catalogo ADD CONSTRAINT [PK__Consulta__7D0B7DACC7B4242D] PRIMARY KEY (ConsultaID);
CREATE UNIQUE INDEX [UQ_ConsultasSQL_Codigo] ON dbo.ConsultasSQL_Catalogo (CodigoConsulta);
CREATE UNIQUE INDEX [UQ_ConsultasSQL_UUID] ON dbo.ConsultasSQL_Catalogo (PublicUUID);
GO

-- =================================================
-- Tabla: ConsultasSQL_EjecucionesLog
-- Exportado: 2026-06-03T06:45:14.480434
-- =================================================

IF OBJECT_ID('dbo.ConsultasSQL_EjecucionesLog', 'U') IS NOT NULL
    DROP TABLE dbo.ConsultasSQL_EjecucionesLog;
GO

CREATE TABLE dbo.ConsultasSQL_EjecucionesLog (
    [EjecucionID] BIGINT NOT NULL,
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
    [UserAgent] NVARCHAR(500) NULL
);
GO

CREATE INDEX [IX_ConsultasSQL_Log_Consulta] ON dbo.ConsultasSQL_EjecucionesLog (ConsultaID);
CREATE INDEX [IX_ConsultasSQL_Log_Fecha] ON dbo.ConsultasSQL_EjecucionesLog (FechaEjecucion);
CREATE INDEX [IX_ConsultasSQL_Log_Usuario] ON dbo.ConsultasSQL_EjecucionesLog (UsuarioID);
ALTER TABLE dbo.ConsultasSQL_EjecucionesLog ADD CONSTRAINT [PK__Consulta__4C9F90553A226F2E] PRIMARY KEY (EjecucionID);
GO

-- =================================================
-- Tabla: ConsultasSQL_Parametros
-- Exportado: 2026-06-03T06:45:14.691413
-- =================================================

IF OBJECT_ID('dbo.ConsultasSQL_Parametros', 'U') IS NOT NULL
    DROP TABLE dbo.ConsultasSQL_Parametros;
GO

CREATE TABLE dbo.ConsultasSQL_Parametros (
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
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.ConsultasSQL_Parametros ADD CONSTRAINT [PK__Consulta__2B3CE6723352EDBA] PRIMARY KEY (ParametroID);
CREATE UNIQUE INDEX [UQ_ConsultasSQL_Param_Nombre] ON dbo.ConsultasSQL_Parametros (ConsultaID, NombreParametro);
GO

-- =================================================
-- Tabla: ConsultasSQL_Permisos
-- Exportado: 2026-06-03T06:45:14.928055
-- =================================================

IF OBJECT_ID('dbo.ConsultasSQL_Permisos', 'U') IS NOT NULL
    DROP TABLE dbo.ConsultasSQL_Permisos;
GO

CREATE TABLE dbo.ConsultasSQL_Permisos (
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
    [UsuarioCreacionID] NVARCHAR(100) NULL
);
GO

CREATE INDEX [IX_ConsultasSQL_Perm_Consulta] ON dbo.ConsultasSQL_Permisos (ConsultaID);
CREATE INDEX [IX_ConsultasSQL_Perm_Rol] ON dbo.ConsultasSQL_Permisos (RolID);
ALTER TABLE dbo.ConsultasSQL_Permisos ADD CONSTRAINT [PK__Consulta__96E0C7036CF17AC8] PRIMARY KEY (PermisoID);
GO

-- =================================================
-- Tabla: ConsultasSQL_Servidores
-- Exportado: 2026-06-03T06:45:15.131722
-- =================================================

IF OBJECT_ID('dbo.ConsultasSQL_Servidores', 'U') IS NOT NULL
    DROP TABLE dbo.ConsultasSQL_Servidores;
GO

CREATE TABLE dbo.ConsultasSQL_Servidores (
    [ConsultaServidorID] INT NOT NULL,
    [ConsultaID] INT NOT NULL,
    [ServidorID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] INT NULL,
    [SucursalID] NVARCHAR(50) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [Prioridad] INT NOT NULL DEFAULT ((0)),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [UsuarioCreacionID] NVARCHAR(100) NULL
);
GO

ALTER TABLE dbo.ConsultasSQL_Servidores ADD CONSTRAINT [PK__Consulta__8ABA8CCC2F85CFB0] PRIMARY KEY (ConsultaServidorID);
CREATE UNIQUE INDEX [UQ_ConsultasSQL_Srv_Unique] ON dbo.ConsultasSQL_Servidores (ConsultaID, ServidorID, EmpresaID, SucursalID);
GO

-- =================================================
-- Tabla: ConsultasSQL_Versiones
-- Exportado: 2026-06-03T06:45:15.336592
-- =================================================

IF OBJECT_ID('dbo.ConsultasSQL_Versiones', 'U') IS NOT NULL
    DROP TABLE dbo.ConsultasSQL_Versiones;
GO

CREATE TABLE dbo.ConsultasSQL_Versiones (
    [VersionID] INT NOT NULL,
    [ConsultaID] INT NOT NULL,
    [Version] INT NOT NULL,
    [ConsultaSQL] NVARCHAR(MAX) NOT NULL,
    [ParametrosJSON] NVARCHAR(MAX) NULL,
    [MotivoCambio] NVARCHAR(500) NULL,
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [UsuarioCreacionID] NVARCHAR(100) NULL
);
GO

CREATE INDEX [IX_ConsultasSQL_Ver_Consulta] ON dbo.ConsultasSQL_Versiones (ConsultaID);
ALTER TABLE dbo.ConsultasSQL_Versiones ADD CONSTRAINT [PK__Consulta__16C6402F0483069E] PRIMARY KEY (VersionID);
CREATE UNIQUE INDEX [UQ_ConsultasSQL_Ver_Unico] ON dbo.ConsultasSQL_Versiones (ConsultaID, Version);
GO

-- =================================================
-- Tabla: CRM_Actividades
-- Exportado: 2026-06-03T06:45:15.541215
-- =================================================

IF OBJECT_ID('dbo.CRM_Actividades', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Actividades;
GO

CREATE TABLE dbo.CRM_Actividades (
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
    [FechaNotificacion] DATETIME NULL
);
GO

CREATE INDEX [IX_CRM_Actividades_AsignadoA] ON dbo.CRM_Actividades (AsignadoAUserID);
CREATE INDEX [IX_CRM_Actividades_Empresa] ON dbo.CRM_Actividades (EmpresaID);
CREATE INDEX [IX_CRM_Actividades_Entidad] ON dbo.CRM_Actividades (EntidadTipo, EntidadID);
CREATE INDEX [IX_CRM_Actividades_Estatus] ON dbo.CRM_Actividades (EstatusActividadID);
CREATE INDEX [IX_CRM_Actividades_FechaProgramada] ON dbo.CRM_Actividades (FechaProgramada);
ALTER TABLE dbo.CRM_Actividades ADD CONSTRAINT [PK_CRM_Actividades] PRIMARY KEY (ActividadID);
GO

-- =================================================
-- Tabla: CRM_ActividadesHistorial
-- Exportado: 2026-06-03T06:45:15.747928
-- =================================================

IF OBJECT_ID('dbo.CRM_ActividadesHistorial', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_ActividadesHistorial;
GO

CREATE TABLE dbo.CRM_ActividadesHistorial (
    [HistorialActividadID] INT NOT NULL,
    [ActividadID] UNIQUEIDENTIFIER NOT NULL,
    [EstatusAnteriorID] INT NULL,
    [EstatusNuevoID] INT NOT NULL,
    [UsuarioModificadorID] UNIQUEIDENTIFIER NOT NULL,
    [FechaCambio] DATETIME2 NULL DEFAULT (getdate()),
    [Comentario] NVARCHAR(500) NULL
);
GO

ALTER TABLE dbo.CRM_ActividadesHistorial ADD CONSTRAINT [PK__CRM_Acti__A9B8F330614D98D5] PRIMARY KEY (HistorialActividadID);
GO

-- =================================================
-- Tabla: CRM_Automation_Log
-- Exportado: 2026-06-03T06:45:15.953760
-- =================================================

IF OBJECT_ID('dbo.CRM_Automation_Log', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Automation_Log;
GO

CREATE TABLE dbo.CRM_Automation_Log (
    [LogID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [ReglaID] UNIQUEIDENTIFIER NOT NULL,
    [OportunidadID] UNIQUEIDENTIFIER NULL,
    [TipoTrigger] NVARCHAR(50) NULL,
    [AccionEjecutada] NVARCHAR(100) NULL,
    [Exitoso] BIT NULL DEFAULT ((1)),
    [DetalleJSON] NVARCHAR(MAX) NULL,
    [MensajeError] NVARCHAR(500) NULL,
    [FechaEjecucion] DATETIME NULL DEFAULT (getdate())
);
GO

CREATE INDEX [IX_Log_Empresa] ON dbo.CRM_Automation_Log (EmpresaID);
CREATE INDEX [IX_Log_Fecha] ON dbo.CRM_Automation_Log (FechaEjecucion);
CREATE INDEX [IX_Log_Regla] ON dbo.CRM_Automation_Log (ReglaID);
ALTER TABLE dbo.CRM_Automation_Log ADD CONSTRAINT [PK__CRM_Auto__5E5499A8A76FC511] PRIMARY KEY (LogID);
GO

-- =================================================
-- Tabla: CRM_Automation_Reglas
-- Exportado: 2026-06-03T06:45:16.158284
-- =================================================

IF OBJECT_ID('dbo.CRM_Automation_Reglas', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Automation_Reglas;
GO

CREATE TABLE dbo.CRM_Automation_Reglas (
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
    [FechaModificacion] DATETIME NULL
);
GO

CREATE INDEX [IX_Reglas_Activa] ON dbo.CRM_Automation_Reglas (Activa);
CREATE INDEX [IX_Reglas_Empresa] ON dbo.CRM_Automation_Reglas (EmpresaID);
CREATE INDEX [IX_Reglas_Pipeline] ON dbo.CRM_Automation_Reglas (PipelineID);
ALTER TABLE dbo.CRM_Automation_Reglas ADD CONSTRAINT [PK__CRM_Auto__66A783D349EAD4CE] PRIMARY KEY (ReglaID);
GO

-- =================================================
-- Tabla: CRM_Cat_EstatusActividad
-- Exportado: 2026-06-03T06:45:16.394622
-- =================================================

IF OBJECT_ID('dbo.CRM_Cat_EstatusActividad', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Cat_EstatusActividad;
GO

CREATE TABLE dbo.CRM_Cat_EstatusActividad (
    [EstatusID] INT NOT NULL,
    [Nombre] NVARCHAR(50) NOT NULL,
    [Color] NVARCHAR(20) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.CRM_Cat_EstatusActividad ADD CONSTRAINT [PK_CRM_Cat_EstatusActividad] PRIMARY KEY (EstatusID);
GO

-- =================================================
-- Tabla: CRM_Cat_EstatusContrato
-- Exportado: 2026-06-03T06:45:16.639359
-- =================================================

IF OBJECT_ID('dbo.CRM_Cat_EstatusContrato', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Cat_EstatusContrato;
GO

CREATE TABLE dbo.CRM_Cat_EstatusContrato (
    [EstatusID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [ColorHex] NVARCHAR(7) NULL DEFAULT ('#6B7280'),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_Cat_EstatusContrato ADD CONSTRAINT [PK__CRM_Cat___DE10F26DD5B4BBBF] PRIMARY KEY (EstatusID);
GO

-- =================================================
-- Tabla: CRM_Cat_EstatusLead
-- Exportado: 2026-06-03T06:45:16.875272
-- =================================================

IF OBJECT_ID('dbo.CRM_Cat_EstatusLead', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Cat_EstatusLead;
GO

CREATE TABLE dbo.CRM_Cat_EstatusLead (
    [EstatusID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [ColorHex] NVARCHAR(7) NULL DEFAULT ('#6B7280'),
    [EsFinal] BIT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_Cat_EstatusLead ADD CONSTRAINT [PK__CRM_Cat___DE10F26DCBE1C71D] PRIMARY KEY (EstatusID);
GO

-- =================================================
-- Tabla: CRM_Cat_EstatusOportunidad
-- Exportado: 2026-06-03T06:45:17.110900
-- =================================================

IF OBJECT_ID('dbo.CRM_Cat_EstatusOportunidad', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Cat_EstatusOportunidad;
GO

CREATE TABLE dbo.CRM_Cat_EstatusOportunidad (
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
    [CreatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_Cat_EstatusOportunidad ADD CONSTRAINT [PK__CRM_Cat___DE10F26D369E0B51] PRIMARY KEY (EstatusID);
GO

-- =================================================
-- Tabla: CRM_Cat_EstatusPropuesta
-- Exportado: 2026-06-03T06:45:17.347089
-- =================================================

IF OBJECT_ID('dbo.CRM_Cat_EstatusPropuesta', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Cat_EstatusPropuesta;
GO

CREATE TABLE dbo.CRM_Cat_EstatusPropuesta (
    [EstatusID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [ColorHex] NVARCHAR(7) NULL DEFAULT ('#6B7280'),
    [EsFinal] BIT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_Cat_EstatusPropuesta ADD CONSTRAINT [PK__CRM_Cat___DE10F26DE82E2C75] PRIMARY KEY (EstatusID);
GO

-- =================================================
-- Tabla: CRM_Cat_MotivosGanada
-- Exportado: 2026-06-03T06:45:17.585401
-- =================================================

IF OBJECT_ID('dbo.CRM_Cat_MotivosGanada', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Cat_MotivosGanada;
GO

CREATE TABLE dbo.CRM_Cat_MotivosGanada (
    [MotivoID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_Cat_MotivosGanada ADD CONSTRAINT [PK__CRM_Cat___AE78D2571A115B1B] PRIMARY KEY (MotivoID);
GO

-- =================================================
-- Tabla: CRM_Cat_MotivosPerdida
-- Exportado: 2026-06-03T06:45:17.824704
-- =================================================

IF OBJECT_ID('dbo.CRM_Cat_MotivosPerdida', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Cat_MotivosPerdida;
GO

CREATE TABLE dbo.CRM_Cat_MotivosPerdida (
    [MotivoID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_Cat_MotivosPerdida ADD CONSTRAINT [PK__CRM_Cat___AE78D257770BF15F] PRIMARY KEY (MotivoID);
GO

-- =================================================
-- Tabla: CRM_Cat_OrigenLead
-- Exportado: 2026-06-03T06:45:18.060789
-- =================================================

IF OBJECT_ID('dbo.CRM_Cat_OrigenLead', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Cat_OrigenLead;
GO

CREATE TABLE dbo.CRM_Cat_OrigenLead (
    [OrigenID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [ColorHex] NVARCHAR(7) NULL DEFAULT ('#6B7280'),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_Cat_OrigenLead ADD CONSTRAINT [PK__CRM_Cat___4DDFA27E300B7D79] PRIMARY KEY (OrigenID);
GO

-- =================================================
-- Tabla: CRM_Cat_Prioridades
-- Exportado: 2026-06-03T06:45:18.297340
-- =================================================

IF OBJECT_ID('dbo.CRM_Cat_Prioridades', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Cat_Prioridades;
GO

CREATE TABLE dbo.CRM_Cat_Prioridades (
    [PrioridadID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [ColorHex] NVARCHAR(7) NULL DEFAULT ('#6B7280'),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_Cat_Prioridades ADD CONSTRAINT [PK__CRM_Cat___393917CE05771EB3] PRIMARY KEY (PrioridadID);
GO

-- =================================================
-- Tabla: CRM_Cat_Sectores
-- Exportado: 2026-06-03T06:45:18.534075
-- =================================================

IF OBJECT_ID('dbo.CRM_Cat_Sectores', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Cat_Sectores;
GO

CREATE TABLE dbo.CRM_Cat_Sectores (
    [SectorID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_Cat_Sectores ADD CONSTRAINT [PK__CRM_Cat___755E5789BE542717] PRIMARY KEY (SectorID);
GO

-- =================================================
-- Tabla: CRM_Cat_TamanosCliente
-- Exportado: 2026-06-03T06:45:18.771367
-- =================================================

IF OBJECT_ID('dbo.CRM_Cat_TamanosCliente', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Cat_TamanosCliente;
GO

CREATE TABLE dbo.CRM_Cat_TamanosCliente (
    [TamanoID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [RangoEmpleadosMin] INT NULL,
    [RangoEmpleadosMax] INT NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_Cat_TamanosCliente ADD CONSTRAINT [PK__CRM_Cat___082148F2804BDEF0] PRIMARY KEY (TamanoID);
GO

-- =================================================
-- Tabla: CRM_Cat_TiposActividad
-- Exportado: 2026-06-03T06:45:19.006664
-- =================================================

IF OBJECT_ID('dbo.CRM_Cat_TiposActividad', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Cat_TiposActividad;
GO

CREATE TABLE dbo.CRM_Cat_TiposActividad (
    [TipoID] INT NOT NULL,
    [Nombre] NVARCHAR(50) NOT NULL,
    [Icono] NVARCHAR(30) NULL,
    [Color] NVARCHAR(20) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.CRM_Cat_TiposActividad ADD CONSTRAINT [PK_CRM_Cat_TiposActividad] PRIMARY KEY (TipoID);
GO

-- =================================================
-- Tabla: CRM_Cat_TiposPipeline
-- Exportado: 2026-06-03T06:45:19.243748
-- =================================================

IF OBJECT_ID('dbo.CRM_Cat_TiposPipeline', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Cat_TiposPipeline;
GO

CREATE TABLE dbo.CRM_Cat_TiposPipeline (
    [TipoID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_Cat_TiposPipeline ADD CONSTRAINT [PK__CRM_Cat___97099E97D97C0574] PRIMARY KEY (TipoID);
GO

-- =================================================
-- Tabla: CRM_ClientesSolicitudesAlta
-- Exportado: 2026-06-03T06:45:19.480101
-- =================================================

IF OBJECT_ID('dbo.CRM_ClientesSolicitudesAlta', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_ClientesSolicitudesAlta;
GO

CREATE TABLE dbo.CRM_ClientesSolicitudesAlta (
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
    [UpdatedAt] DATETIME2 NULL
);
GO

CREATE INDEX [IX_CRM_ClientesSolicitudesAlta_Cuenta] ON dbo.CRM_ClientesSolicitudesAlta (CuentaID);
CREATE INDEX [IX_CRM_ClientesSolicitudesAlta_Empresa] ON dbo.CRM_ClientesSolicitudesAlta (EmpresaID);
CREATE INDEX [IX_CRM_ClientesSolicitudesAlta_Estatus] ON dbo.CRM_ClientesSolicitudesAlta (EstatusSolicitud);
CREATE UNIQUE INDEX [IX_CRM_ClientesSolicitudesAlta_Folio] ON dbo.CRM_ClientesSolicitudesAlta (EmpresaID, FolioSolicitud);
ALTER TABLE dbo.CRM_ClientesSolicitudesAlta ADD CONSTRAINT [PK_CRM_ClientesSolicitudesAlta] PRIMARY KEY (SolicitudID);
GO

-- =================================================
-- Tabla: CRM_ClientesSolicitudesAltaHistorial
-- Exportado: 2026-06-03T06:45:19.684727
-- =================================================

IF OBJECT_ID('dbo.CRM_ClientesSolicitudesAltaHistorial', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_ClientesSolicitudesAltaHistorial;
GO

CREATE TABLE dbo.CRM_ClientesSolicitudesAltaHistorial (
    [HistorialID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [SolicitudID] UNIQUEIDENTIFIER NOT NULL,
    [EstatusAnterior] NVARCHAR(20) NULL,
    [EstatusNuevo] NVARCHAR(20) NOT NULL,
    [Comentario] NVARCHAR(500) NULL,
    [CambiadoPorUserID] UNIQUEIDENTIFIER NOT NULL,
    [FechaCambio] DATETIME2 NOT NULL DEFAULT (getutcdate())
);
GO

CREATE INDEX [IX_CRM_ClientesSolicitudesAltaHistorial_Solicitud] ON dbo.CRM_ClientesSolicitudesAltaHistorial (SolicitudID);
ALTER TABLE dbo.CRM_ClientesSolicitudesAltaHistorial ADD CONSTRAINT [PK_CRM_ClientesSolicitudesAltaHistorial] PRIMARY KEY (HistorialID);
GO

-- =================================================
-- Tabla: CRM_Config_PipelineEtapas
-- Exportado: 2026-06-03T06:45:19.890696
-- =================================================

IF OBJECT_ID('dbo.CRM_Config_PipelineEtapas', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Config_PipelineEtapas;
GO

CREATE TABLE dbo.CRM_Config_PipelineEtapas (
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
    [DiasSLAMaximo] INT NULL
);
GO

CREATE INDEX [IX_CRM_PipelineEtapas_Pipeline] ON dbo.CRM_Config_PipelineEtapas (PipelineID);
ALTER TABLE dbo.CRM_Config_PipelineEtapas ADD CONSTRAINT [PK__CRM_Conf__402706842CB4C95C] PRIMARY KEY (EtapaID);
GO

-- =================================================
-- Tabla: CRM_Config_Pipelines
-- Exportado: 2026-06-03T06:45:20.127121
-- =================================================

IF OBJECT_ID('dbo.CRM_Config_Pipelines', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Config_Pipelines;
GO

CREATE TABLE dbo.CRM_Config_Pipelines (
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
    [UpdatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_Config_Pipelines ADD CONSTRAINT [PK__CRM_Conf__DD425CAF22CE2088] PRIMARY KEY (PipelineID);
GO

-- =================================================
-- Tabla: CRM_Contratos
-- Exportado: 2026-06-03T06:45:20.363607
-- =================================================

IF OBJECT_ID('dbo.CRM_Contratos', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Contratos;
GO

CREATE TABLE dbo.CRM_Contratos (
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
    [UpdatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

CREATE INDEX [IX_CRM_Contratos_Cuenta] ON dbo.CRM_Contratos (CuentaID);
CREATE INDEX [IX_CRM_Contratos_Estatus] ON dbo.CRM_Contratos (EstatusContratoID);
CREATE INDEX [IX_CRM_Contratos_FechaFin] ON dbo.CRM_Contratos (FechaFin);
ALTER TABLE dbo.CRM_Contratos ADD CONSTRAINT [PK__CRM_Cont__B238E953F2C13E96] PRIMARY KEY (ContratoID);
GO

-- =================================================
-- Tabla: CRM_Cuentas
-- Exportado: 2026-06-03T06:45:20.568030
-- =================================================

IF OBJECT_ID('dbo.CRM_Cuentas', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Cuentas;
GO

CREATE TABLE dbo.CRM_Cuentas (
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
    [UpdatedAt] DATETIME2 NULL
);
GO

CREATE INDEX [IX_CRM_Cuentas_ClienteID] ON dbo.CRM_Cuentas (ClienteID);
CREATE INDEX [IX_CRM_Cuentas_EjecutivoResponsable] ON dbo.CRM_Cuentas (EjecutivoResponsableUserID);
CREATE INDEX [IX_CRM_Cuentas_EmpresaID] ON dbo.CRM_Cuentas (EmpresaID);
CREATE INDEX [IX_CRM_Cuentas_TipoCuenta] ON dbo.CRM_Cuentas (TipoCuenta);
ALTER TABLE dbo.CRM_Cuentas ADD CONSTRAINT [PK_CRM_Cuentas] PRIMARY KEY (CuentaID);
GO

-- =================================================
-- Tabla: CRM_ERPSyncLog
-- Exportado: 2026-06-03T06:45:20.775109
-- =================================================

IF OBJECT_ID('dbo.CRM_ERPSyncLog', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_ERPSyncLog;
GO

CREATE TABLE dbo.CRM_ERPSyncLog (
    [ERPSyncID] INT NOT NULL,
    [PedidoID] BIGINT NOT NULL,
    [SistemaERP] VARCHAR(50) NOT NULL,
    [MetodoTransaccion] VARCHAR(50) NOT NULL,
    [PayloadRaw] NVARCHAR(MAX) NOT NULL,
    [EstatusERP] VARCHAR(50) NULL DEFAULT ('Pendiente'),
    [FechaRegistro] DATETIME NULL DEFAULT (getdate()),
    [FechaProcesamiento] DATETIME NULL
);
GO

ALTER TABLE dbo.CRM_ERPSyncLog ADD CONSTRAINT [PK__CRM_ERPS__497A129804D70F2E] PRIMARY KEY (ERPSyncID);
GO

-- =================================================
-- Tabla: CRM_Implementaciones
-- Exportado: 2026-06-03T06:45:20.980220
-- =================================================

IF OBJECT_ID('dbo.CRM_Implementaciones', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Implementaciones;
GO

CREATE TABLE dbo.CRM_Implementaciones (
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
    [FechaModificacion] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_Implementaciones ADD CONSTRAINT [PK__CRM_Impl__9ED0E1295ECB20AC] PRIMARY KEY (ImplementacionID);
GO

-- =================================================
-- Tabla: CRM_ImplementacionesEntregables
-- Exportado: 2026-06-03T06:45:21.184836
-- =================================================

IF OBJECT_ID('dbo.CRM_ImplementacionesEntregables', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_ImplementacionesEntregables;
GO

CREATE TABLE dbo.CRM_ImplementacionesEntregables (
    [EntregableID] INT NOT NULL,
    [ImplementacionID] INT NOT NULL,
    [NombreEntregable] VARCHAR(255) NOT NULL,
    [Descripcion] VARCHAR(500) NULL,
    [Obligatorio] BIT NULL DEFAULT ((1)),
    [Estatus] VARCHAR(50) NULL DEFAULT ('Pendiente'),
    [FechaLimite] DATETIME NULL,
    [FechaAprobacion] DATETIME NULL,
    [UsuarioAprobadorID] INT NULL,
    [FechaCreacion] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_ImplementacionesEntregables ADD CONSTRAINT [PK__CRM_Impl__D66E1E079084EA7A] PRIMARY KEY (EntregableID);
GO

-- =================================================
-- Tabla: CRM_Integracion_Conectores
-- Exportado: 2026-06-03T06:45:21.388491
-- =================================================

IF OBJECT_ID('dbo.CRM_Integracion_Conectores', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Integracion_Conectores;
GO

CREATE TABLE dbo.CRM_Integracion_Conectores (
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
    [UpdatedBy] UNIQUEIDENTIFIER NULL
);
GO

ALTER TABLE dbo.CRM_Integracion_Conectores ADD CONSTRAINT [PK__CRM_Inte__E863D9DEE61A6AC5] PRIMARY KEY (ConectorID);
GO

-- =================================================
-- Tabla: CRM_Integracion_MapeoEtapas
-- Exportado: 2026-06-03T06:45:21.626837
-- =================================================

IF OBJECT_ID('dbo.CRM_Integracion_MapeoEtapas', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Integracion_MapeoEtapas;
GO

CREATE TABLE dbo.CRM_Integracion_MapeoEtapas (
    [MapeoID] INT NOT NULL,
    [ConectorID] INT NOT NULL,
    [EtapaExterna] NVARCHAR(100) NOT NULL,
    [EtapaLocalID] INT NULL,
    [EtapaLocalNombre] NVARCHAR(100) NULL,
    [MapeoActivo] BIT NULL DEFAULT ((1)),
    [EsDefault] BIT NULL DEFAULT ((0)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_Integracion_MapeoEtapas ADD CONSTRAINT [PK__CRM_Inte__CC527B089A9B7443] PRIMARY KEY (MapeoID);
GO

-- =================================================
-- Tabla: CRM_Integracion_SyncLog
-- Exportado: 2026-06-03T06:45:21.833005
-- =================================================

IF OBJECT_ID('dbo.CRM_Integracion_SyncLog', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Integracion_SyncLog;
GO

CREATE TABLE dbo.CRM_Integracion_SyncLog (
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
    [EjecutadoPor] UNIQUEIDENTIFIER NULL
);
GO

ALTER TABLE dbo.CRM_Integracion_SyncLog ADD CONSTRAINT [PK__CRM_Inte__5E5499A849C94245] PRIMARY KEY (LogID);
GO

-- =================================================
-- Tabla: CRM_IntegracionesConflictos
-- Exportado: 2026-06-03T06:45:22.068533
-- =================================================

IF OBJECT_ID('dbo.CRM_IntegracionesConflictos', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_IntegracionesConflictos;
GO

CREATE TABLE dbo.CRM_IntegracionesConflictos (
    [ConflictoID] INT NOT NULL,
    [SyncLogID] BIGINT NOT NULL,
    [ColumnaConflicto] VARCHAR(100) NOT NULL,
    [ValorHub] NVARCHAR(1000) NULL,
    [ValorExterno] NVARCHAR(1000) NULL,
    [Resuelto] BIT NULL DEFAULT ((0)),
    [ReglaAplicada] VARCHAR(100) NULL,
    [FechaConflicto] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_IntegracionesConflictos ADD CONSTRAINT [PK__CRM_Inte__1732016156CD0D9B] PRIMARY KEY (ConflictoID);
GO

-- =================================================
-- Tabla: CRM_IntegracionesSyncLog
-- Exportado: 2026-06-03T06:45:22.272090
-- =================================================

IF OBJECT_ID('dbo.CRM_IntegracionesSyncLog', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_IntegracionesSyncLog;
GO

CREATE TABLE dbo.CRM_IntegracionesSyncLog (
    [SyncLogID] BIGINT NOT NULL,
    [SistemaExterno] VARCHAR(50) NOT NULL,
    [EntidadCanonica] VARCHAR(100) NOT NULL,
    [IDExterno] VARCHAR(255) NOT NULL,
    [DataRawPayload] NVARCHAR(MAX) NOT NULL,
    [EstatusSync] VARCHAR(50) NULL DEFAULT ('Pendiente'),
    [FechaRegistro] DATETIME NULL DEFAULT (getdate()),
    [FechaProcesamiento] DATETIME NULL
);
GO

ALTER TABLE dbo.CRM_IntegracionesSyncLog ADD CONSTRAINT [PK__CRM_Inte__A40EB328786D7BDB] PRIMARY KEY (SyncLogID);
GO

-- =================================================
-- Tabla: CRM_Leads
-- Exportado: 2026-06-03T06:45:22.475663
-- =================================================

IF OBJECT_ID('dbo.CRM_Leads', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Leads;
GO

CREATE TABLE dbo.CRM_Leads (
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
    [DeletedAt] DATETIME NULL
);
GO

CREATE INDEX [IX_CRM_Leads_CreatedAt] ON dbo.CRM_Leads (CreatedAt);
CREATE INDEX [IX_CRM_Leads_Ejecutivo] ON dbo.CRM_Leads (EjecutivoAsignadoUserID);
CREATE INDEX [IX_CRM_Leads_Empresa] ON dbo.CRM_Leads (EmpresaID);
CREATE INDEX [IX_CRM_Leads_Estatus] ON dbo.CRM_Leads (EstatusLeadID);
ALTER TABLE dbo.CRM_Leads ADD CONSTRAINT [PK__CRM_Lead__73EF791AD9ADFF08] PRIMARY KEY (LeadID);
GO

-- =================================================
-- Tabla: CRM_Oportunidad_Contactos
-- Exportado: 2026-06-03T06:45:22.679566
-- =================================================

IF OBJECT_ID('dbo.CRM_Oportunidad_Contactos', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Oportunidad_Contactos;
GO

CREATE TABLE dbo.CRM_Oportunidad_Contactos (
    [ID] INT NOT NULL,
    [OportunidadID] UNIQUEIDENTIFIER NOT NULL,
    [ContactoID] UNIQUEIDENTIFIER NOT NULL,
    [RolContactoID] INT NULL,
    [EsPrincipal] BIT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

CREATE INDEX [IX_CRM_OportunidadContactos_Opp] ON dbo.CRM_Oportunidad_Contactos (OportunidadID);
ALTER TABLE dbo.CRM_Oportunidad_Contactos ADD CONSTRAINT [PK__CRM_Opor__3214EC2737999D36] PRIMARY KEY (ID);
GO

-- =================================================
-- Tabla: CRM_Oportunidad_Documentos
-- Exportado: 2026-06-03T06:45:22.882585
-- =================================================

IF OBJECT_ID('dbo.CRM_Oportunidad_Documentos', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Oportunidad_Documentos;
GO

CREATE TABLE dbo.CRM_Oportunidad_Documentos (
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
    [CreatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

CREATE INDEX [IX_CRM_OportunidadDocs_Opp] ON dbo.CRM_Oportunidad_Documentos (OportunidadID);
ALTER TABLE dbo.CRM_Oportunidad_Documentos ADD CONSTRAINT [PK__CRM_Opor__3214EC2752CB9E50] PRIMARY KEY (ID);
GO

-- =================================================
-- Tabla: CRM_Oportunidades
-- Exportado: 2026-06-03T06:45:23.089865
-- =================================================

IF OBJECT_ID('dbo.CRM_Oportunidades', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Oportunidades;
GO

CREATE TABLE dbo.CRM_Oportunidades (
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
    [DeletedAt] DATETIME NULL
);
GO

CREATE INDEX [IX_CRM_Oportunidades_Cuenta] ON dbo.CRM_Oportunidades (CuentaID);
CREATE INDEX [IX_CRM_Oportunidades_Ejecutivo] ON dbo.CRM_Oportunidades (EjecutivoResponsableUserID);
CREATE INDEX [IX_CRM_Oportunidades_Empresa] ON dbo.CRM_Oportunidades (EmpresaID);
CREATE INDEX [IX_CRM_Oportunidades_Estatus] ON dbo.CRM_Oportunidades (EstatusOportunidadID);
CREATE INDEX [IX_CRM_Oportunidades_FechaCierre] ON dbo.CRM_Oportunidades (FechaEstimadaCierre);
CREATE INDEX [IX_CRM_Oportunidades_Pipeline] ON dbo.CRM_Oportunidades (PipelineID, EtapaActualID);
ALTER TABLE dbo.CRM_Oportunidades ADD CONSTRAINT [PK__CRM_Opor__F838276BBC641D71] PRIMARY KEY (OportunidadID);
GO

-- =================================================
-- Tabla: CRM_Oportunidades_HistorialEtapas
-- Exportado: 2026-06-03T06:45:23.294067
-- =================================================

IF OBJECT_ID('dbo.CRM_Oportunidades_HistorialEtapas', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Oportunidades_HistorialEtapas;
GO

CREATE TABLE dbo.CRM_Oportunidades_HistorialEtapas (
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
    [FechaCambio] DATETIME NULL DEFAULT (getdate())
);
GO

CREATE INDEX [IX_CRM_HistorialEtapas_Fecha] ON dbo.CRM_Oportunidades_HistorialEtapas (FechaCambio);
CREATE INDEX [IX_CRM_HistorialEtapas_Opp] ON dbo.CRM_Oportunidades_HistorialEtapas (OportunidadID);
ALTER TABLE dbo.CRM_Oportunidades_HistorialEtapas ADD CONSTRAINT [PK__CRM_Opor__975206EFAC49EBFA] PRIMARY KEY (HistorialID);
GO

-- =================================================
-- Tabla: CRM_OportunidadesHistorial
-- Exportado: 2026-06-03T06:45:23.530666
-- =================================================

IF OBJECT_ID('dbo.CRM_OportunidadesHistorial', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_OportunidadesHistorial;
GO

CREATE TABLE dbo.CRM_OportunidadesHistorial (
    [HistorialPipelineID] INT NOT NULL,
    [OportunidadID] UNIQUEIDENTIFIER NOT NULL,
    [EtapaAnteriorID] INT NULL,
    [EtapaNuevaID] INT NOT NULL,
    [MontoAnterior] DECIMAL(18,2) NULL,
    [MontoNuevo] DECIMAL(18,2) NOT NULL,
    [UsuarioModificadorID] UNIQUEIDENTIFIER NOT NULL,
    [FechaCambio] DATETIME NULL DEFAULT (getdate()),
    [Comentario] NVARCHAR(500) NULL
);
GO

ALTER TABLE dbo.CRM_OportunidadesHistorial ADD CONSTRAINT [PK__CRM_Opor__618938CBA9EC7A6A] PRIMARY KEY (HistorialPipelineID);
GO

-- =================================================
-- Tabla: CRM_PostventaEncuestas
-- Exportado: 2026-06-03T06:45:23.734991
-- =================================================

IF OBJECT_ID('dbo.CRM_PostventaEncuestas', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_PostventaEncuestas;
GO

CREATE TABLE dbo.CRM_PostventaEncuestas (
    [EncuestaID] INT NOT NULL,
    [CuentaID] UNIQUEIDENTIFIER NOT NULL,
    [TicketID] INT NULL,
    [PuntuacionCSAT] INT NOT NULL,
    [Comentarios] NVARCHAR(1000) NULL,
    [FechaRegistro] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_PostventaEncuestas ADD CONSTRAINT [PK__CRM_Post__82FD78C8850F412E] PRIMARY KEY (EncuestaID);
GO

-- =================================================
-- Tabla: CRM_PostventaTickets
-- Exportado: 2026-06-03T06:45:23.938356
-- =================================================

IF OBJECT_ID('dbo.CRM_PostventaTickets', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_PostventaTickets;
GO

CREATE TABLE dbo.CRM_PostventaTickets (
    [TicketID] INT NOT NULL,
    [CuentaID] UNIQUEIDENTIFIER NOT NULL,
    [FolioTicket] VARCHAR(50) NOT NULL,
    [Asunto] VARCHAR(255) NOT NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [Estatus] VARCHAR(50) NULL DEFAULT ('Abierto'),
    [Prioridad] VARCHAR(30) NULL DEFAULT ('Media'),
    [UsuarioAsignadoID] INT NOT NULL,
    [FechaCreacion] DATETIME NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_PostventaTickets ADD CONSTRAINT [PK__CRM_Post__712CC62786BCA517] PRIMARY KEY (TicketID);
CREATE UNIQUE INDEX [UQ__CRM_Post__00666684B52C8736] ON dbo.CRM_PostventaTickets (FolioTicket);
GO

-- =================================================
-- Tabla: CRM_Propuestas
-- Exportado: 2026-06-03T06:45:24.144063
-- =================================================

IF OBJECT_ID('dbo.CRM_Propuestas', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Propuestas;
GO

CREATE TABLE dbo.CRM_Propuestas (
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
    [UpdatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

CREATE INDEX [IX_CRM_Propuestas_Estatus] ON dbo.CRM_Propuestas (EstatusPropuestaID);
CREATE INDEX [IX_CRM_Propuestas_Oportunidad] ON dbo.CRM_Propuestas (OportunidadID);
ALTER TABLE dbo.CRM_Propuestas ADD CONSTRAINT [PK__CRM_Prop__4B067802272694A3] PRIMARY KEY (PropuestaID);
GO

-- =================================================
-- Tabla: CRM_Staging_Cuentas
-- Exportado: 2026-06-03T06:45:24.347857
-- =================================================

IF OBJECT_ID('dbo.CRM_Staging_Cuentas', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Staging_Cuentas;
GO

CREATE TABLE dbo.CRM_Staging_Cuentas (
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
    [UpdatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_Staging_Cuentas ADD CONSTRAINT [PK__CRM_Stag__8C04728074558FF7] PRIMARY KEY (StagingID);
GO

-- =================================================
-- Tabla: CRM_Staging_Leads
-- Exportado: 2026-06-03T06:45:24.584271
-- =================================================

IF OBJECT_ID('dbo.CRM_Staging_Leads', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Staging_Leads;
GO

CREATE TABLE dbo.CRM_Staging_Leads (
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
    [UpdatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_Staging_Leads ADD CONSTRAINT [PK__CRM_Stag__8C047280C0FB368C] PRIMARY KEY (StagingID);
GO

-- =================================================
-- Tabla: CRM_Staging_Oportunidades
-- Exportado: 2026-06-03T06:45:24.821510
-- =================================================

IF OBJECT_ID('dbo.CRM_Staging_Oportunidades', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Staging_Oportunidades;
GO

CREATE TABLE dbo.CRM_Staging_Oportunidades (
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
    [UpdatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_Staging_Oportunidades ADD CONSTRAINT [PK__CRM_Stag__8C04728061B9AD41] PRIMARY KEY (StagingID);
GO

-- =================================================
-- Tabla: CRM_Tareas
-- Exportado: 2026-06-03T06:45:25.024965
-- =================================================

IF OBJECT_ID('dbo.CRM_Tareas', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Tareas;
GO

CREATE TABLE dbo.CRM_Tareas (
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
    [FechaCompletada] DATETIME NULL
);
GO

ALTER TABLE dbo.CRM_Tareas ADD CONSTRAINT [PK__CRM_Tare__5CD836712D6091DF] PRIMARY KEY (TareaID);
GO

-- =================================================
-- Tabla: CRM_Trigger_Log
-- Exportado: 2026-06-03T06:45:25.229082
-- =================================================

IF OBJECT_ID('dbo.CRM_Trigger_Log', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Trigger_Log;
GO

CREATE TABLE dbo.CRM_Trigger_Log (
    [LogID] NVARCHAR(50) NOT NULL,
    [TriggerID] NVARCHAR(50) NOT NULL,
    [EntidadID] NVARCHAR(50) NULL,
    [EmpresaID] NVARCHAR(50) NOT NULL,
    [Exitoso] BIT NULL DEFAULT ((0)),
    [ResultadoJSON] NVARCHAR(MAX) NULL,
    [FechaEjecucion] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.CRM_Trigger_Log ADD CONSTRAINT [PK__CRM_Trig__5E5499A813077901] PRIMARY KEY (LogID);
GO

-- =================================================
-- Tabla: CRM_Triggers
-- Exportado: 2026-06-03T06:45:25.434160
-- =================================================

IF OBJECT_ID('dbo.CRM_Triggers', 'U') IS NOT NULL
    DROP TABLE dbo.CRM_Triggers;
GO

CREATE TABLE dbo.CRM_Triggers (
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
    [FechaModificacion] DATETIME NULL
);
GO

ALTER TABLE dbo.CRM_Triggers ADD CONSTRAINT [PK__CRM_Trig__11321F02A2666B23] PRIMARY KEY (TriggerID);
GO

-- =================================================
-- Tabla: Fact_Ventas_Consolidadas
-- Exportado: 2026-06-03T06:45:25.671192
-- =================================================

IF OBJECT_ID('dbo.Fact_Ventas_Consolidadas', 'U') IS NOT NULL
    DROP TABLE dbo.Fact_Ventas_Consolidadas;
GO

CREATE TABLE dbo.Fact_Ventas_Consolidadas (
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
    [IdFormaCobro] INT NULL
);
GO

ALTER TABLE dbo.Fact_Ventas_Consolidadas ADD CONSTRAINT [PK__Fact_Ven__3214EC074DE923C1] PRIMARY KEY (Id);
GO

-- =================================================
-- Tabla: Finanzas_Cat_CuentasBancarias
-- Exportado: 2026-06-03T06:45:25.999960
-- =================================================

IF OBJECT_ID('dbo.Finanzas_Cat_CuentasBancarias', 'U') IS NOT NULL
    DROP TABLE dbo.Finanzas_Cat_CuentasBancarias;
GO

CREATE TABLE dbo.Finanzas_Cat_CuentasBancarias (
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
    [UsuarioModificacionID] INT NULL
);
GO

ALTER TABLE dbo.Finanzas_Cat_CuentasBancarias ADD CONSTRAINT [PK__Finanzas__C992515F2CD62251] PRIMARY KEY (CuentaBancariaID);
GO

-- =================================================
-- Tabla: Finanzas_Cat_EstatusCuadreZ
-- Exportado: 2026-06-03T06:45:26.235060
-- =================================================

IF OBJECT_ID('dbo.Finanzas_Cat_EstatusCuadreZ', 'U') IS NOT NULL
    DROP TABLE dbo.Finanzas_Cat_EstatusCuadreZ;
GO

CREATE TABLE dbo.Finanzas_Cat_EstatusCuadreZ (
    [EstatusCuadreID] TINYINT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Descripcion] NVARCHAR(50) NOT NULL,
    [ColorHex] NVARCHAR(7) NOT NULL,
    [Orden] TINYINT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Finanzas_Cat_EstatusCuadreZ ADD CONSTRAINT [PK__Finanzas__B4D198D8FACFEAF7] PRIMARY KEY (EstatusCuadreID);
GO

-- =================================================
-- Tabla: Finanzas_Cat_EstatusTesoreria
-- Exportado: 2026-06-03T06:45:26.469948
-- =================================================

IF OBJECT_ID('dbo.Finanzas_Cat_EstatusTesoreria', 'U') IS NOT NULL
    DROP TABLE dbo.Finanzas_Cat_EstatusTesoreria;
GO

CREATE TABLE dbo.Finanzas_Cat_EstatusTesoreria (
    [EstatusTesoreriaID] TINYINT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Descripcion] NVARCHAR(50) NOT NULL,
    [ColorHex] NVARCHAR(7) NOT NULL,
    [Orden] TINYINT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Finanzas_Cat_EstatusTesoreria ADD CONSTRAINT [PK__Finanzas__3A6BDD4993E1E7F3] PRIMARY KEY (EstatusTesoreriaID);
GO

-- =================================================
-- Tabla: Finanzas_ConfiguracionTPV_Sucursal
-- Exportado: 2026-06-03T06:45:26.707555
-- =================================================

IF OBJECT_ID('dbo.Finanzas_ConfiguracionTPV_Sucursal', 'U') IS NOT NULL
    DROP TABLE dbo.Finanzas_ConfiguracionTPV_Sucursal;
GO

CREATE TABLE dbo.Finanzas_ConfiguracionTPV_Sucursal (
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
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.Finanzas_ConfiguracionTPV_Sucursal ADD CONSTRAINT [PK__Finanzas__2CB7D240C326B950] PRIMARY KEY (ConfiguracionTPVID);
GO

-- =================================================
-- Tabla: Finanzas_CortesCaja
-- Exportado: 2026-06-03T06:45:26.945675
-- =================================================

IF OBJECT_ID('dbo.Finanzas_CortesCaja', 'U') IS NOT NULL
    DROP TABLE dbo.Finanzas_CortesCaja;
GO

CREATE TABLE dbo.Finanzas_CortesCaja (
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
    [EsDemo] BIT NULL DEFAULT ((0))
);
GO

CREATE INDEX [IX_CortesCaja_Demo] ON dbo.Finanzas_CortesCaja (EsDemo);
CREATE INDEX [IX_CortesCaja_FechaCorte] ON dbo.Finanzas_CortesCaja (FechaCorte, UnidadNegocioID);
CREATE INDEX [IX_CortesCaja_Hash] ON dbo.Finanzas_CortesCaja (HashOrigen);
CREATE INDEX [IX_CortesCaja_Origen] ON dbo.Finanzas_CortesCaja (SistemaOrigen, IdOrigen);
CREATE INDEX [IX_CortesCaja_UnidadNegocio] ON dbo.Finanzas_CortesCaja (UnidadNegocioID, FechaCorte);
ALTER TABLE dbo.Finanzas_CortesCaja ADD CONSTRAINT [PK__Finanzas__983CC13836415F8B] PRIMARY KEY (CorteCajaID);
CREATE UNIQUE INDEX [UQ_CortesCaja_Origen] ON dbo.Finanzas_CortesCaja (SistemaOrigen, ServerID, IdOrigen);
GO

-- =================================================
-- Tabla: Finanzas_CortesCaja_Backup_Demo_20260501
-- Exportado: 2026-06-03T06:45:28.480965
-- =================================================

IF OBJECT_ID('dbo.Finanzas_CortesCaja_Backup_Demo_20260501', 'U') IS NOT NULL
    DROP TABLE dbo.Finanzas_CortesCaja_Backup_Demo_20260501;
GO

CREATE TABLE dbo.Finanzas_CortesCaja_Backup_Demo_20260501 (
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

GO

-- =================================================
-- Tabla: Finanzas_CortesCaja_DetallePagos
-- Exportado: 2026-06-03T06:45:28.720184
-- =================================================

IF OBJECT_ID('dbo.Finanzas_CortesCaja_DetallePagos', 'U') IS NOT NULL
    DROP TABLE dbo.Finanzas_CortesCaja_DetallePagos;
GO

CREATE TABLE dbo.Finanzas_CortesCaja_DetallePagos (
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
    [Activo] BIT NULL DEFAULT ((1))
);
GO

CREATE INDEX [IX_DetallePagos_Corte] ON dbo.Finanzas_CortesCaja_DetallePagos (CorteCajaID);
ALTER TABLE dbo.Finanzas_CortesCaja_DetallePagos ADD CONSTRAINT [PK__Finanzas__6E19D6FA7E4FB153] PRIMARY KEY (DetalleID);
GO

-- =================================================
-- Tabla: Finanzas_CortesCaja_SyncLog
-- Exportado: 2026-06-03T06:45:28.924854
-- =================================================

IF OBJECT_ID('dbo.Finanzas_CortesCaja_SyncLog', 'U') IS NOT NULL
    DROP TABLE dbo.Finanzas_CortesCaja_SyncLog;
GO

CREATE TABLE dbo.Finanzas_CortesCaja_SyncLog (
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
    [TipoEjecucion] NVARCHAR(20) NULL
);
GO

ALTER TABLE dbo.Finanzas_CortesCaja_SyncLog ADD CONSTRAINT [PK__Finanzas__5E5499A815355164] PRIMARY KEY (LogID);
GO

-- =================================================
-- Tabla: Finanzas_CuadresZ
-- Exportado: 2026-06-03T06:45:30.402064
-- =================================================

IF OBJECT_ID('dbo.Finanzas_CuadresZ', 'U') IS NOT NULL
    DROP TABLE dbo.Finanzas_CuadresZ;
GO

CREATE TABLE dbo.Finanzas_CuadresZ (
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
    [FechaUltimaActualizacion] DATETIME2 NULL
);
GO

CREATE INDEX [IX_CuadresZ_CorteCajaID] ON dbo.Finanzas_CuadresZ (CorteCajaID);
CREATE INDEX [IX_CuadresZ_Estatus] ON dbo.Finanzas_CuadresZ (EstatusCuadreID);
CREATE INDEX [IX_CuadresZ_FechaOperacion] ON dbo.Finanzas_CuadresZ (FechaOperacion);
CREATE INDEX [IX_CuadresZ_FolioCorte] ON dbo.Finanzas_CuadresZ (UnidadNegocioID, FolioCorte);
CREATE UNIQUE INDEX [IX_CuadresZ_HashOrigen] ON dbo.Finanzas_CuadresZ (HashOrigen);
CREATE INDEX [IX_CuadresZ_IdOrigen] ON dbo.Finanzas_CuadresZ (IdOrigen);
CREATE INDEX [IX_CuadresZ_UnidadFecha] ON dbo.Finanzas_CuadresZ (UnidadNegocioID, FechaCorte);
ALTER TABLE dbo.Finanzas_CuadresZ ADD CONSTRAINT [PK__Finanzas__1A264A9E7217C35B] PRIMARY KEY (CuadreZID);
GO

-- =================================================
-- Tabla: Finanzas_CuadresZ_SyncLog
-- Exportado: 2026-06-03T06:45:30.608358
-- =================================================

IF OBJECT_ID('dbo.Finanzas_CuadresZ_SyncLog', 'U') IS NOT NULL
    DROP TABLE dbo.Finanzas_CuadresZ_SyncLog;
GO

CREATE TABLE dbo.Finanzas_CuadresZ_SyncLog (
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
    [Metadata] NVARCHAR(MAX) NULL
);
GO

CREATE INDEX [IX_CuadresZ_SyncLog_Fecha] ON dbo.Finanzas_CuadresZ_SyncLog (FechaInicio);
CREATE INDEX [IX_CuadresZ_SyncLog_Unidad] ON dbo.Finanzas_CuadresZ_SyncLog (UnidadNegocioID);
ALTER TABLE dbo.Finanzas_CuadresZ_SyncLog ADD CONSTRAINT [PK__Finanzas__5E5499A8A01D6F4D] PRIMARY KEY (LogID);
GO

-- =================================================
-- Tabla: Finanzas_CuentasPorPagar
-- Exportado: 2026-06-03T06:45:30.812967
-- =================================================

IF OBJECT_ID('dbo.Finanzas_CuentasPorPagar', 'U') IS NOT NULL
    DROP TABLE dbo.Finanzas_CuentasPorPagar;
GO

CREATE TABLE dbo.Finanzas_CuentasPorPagar (
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
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.Finanzas_CuentasPorPagar ADD CONSTRAINT [PK__Finanzas__2C02C517A1E943BE] PRIMARY KEY (CuentaPorPagarID);
GO

-- =================================================
-- Tabla: Finanzas_Depositos
-- Exportado: 2026-06-03T06:45:31.050308
-- =================================================

IF OBJECT_ID('dbo.Finanzas_Depositos', 'U') IS NOT NULL
    DROP TABLE dbo.Finanzas_Depositos;
GO

CREATE TABLE dbo.Finanzas_Depositos (
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
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.Finanzas_Depositos ADD CONSTRAINT [PK__Finanzas__345C21B856A7FAF5] PRIMARY KEY (DepositoID);
GO

-- =================================================
-- Tabla: Finanzas_EstatusCierre
-- Exportado: 2026-06-03T06:45:31.253597
-- =================================================

IF OBJECT_ID('dbo.Finanzas_EstatusCierre', 'U') IS NOT NULL
    DROP TABLE dbo.Finanzas_EstatusCierre;
GO

CREATE TABLE dbo.Finanzas_EstatusCierre (
    [EstatusCierreID] TINYINT NOT NULL,
    [Codigo] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Finanzas_EstatusCierre ADD CONSTRAINT [PK__Finanzas__E3A4936020BA0FAF] PRIMARY KEY (EstatusCierreID);
GO

-- =================================================
-- Tabla: Finanzas_EstatusPago
-- Exportado: 2026-06-03T06:45:31.488752
-- =================================================

IF OBJECT_ID('dbo.Finanzas_EstatusPago', 'U') IS NOT NULL
    DROP TABLE dbo.Finanzas_EstatusPago;
GO

CREATE TABLE dbo.Finanzas_EstatusPago (
    [EstatusPagoID] TINYINT NOT NULL,
    [Codigo] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [ColorHex] VARCHAR(7) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Finanzas_EstatusPago ADD CONSTRAINT [PK__Finanzas__5CA67D3C9B05D58E] PRIMARY KEY (EstatusPagoID);
GO

-- =================================================
-- Tabla: Finanzas_KPIs_Historico
-- Exportado: 2026-06-03T06:45:31.726012
-- =================================================

IF OBJECT_ID('dbo.Finanzas_KPIs_Historico', 'U') IS NOT NULL
    DROP TABLE dbo.Finanzas_KPIs_Historico;
GO

CREATE TABLE dbo.Finanzas_KPIs_Historico (
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
    [fecha_actualizacion] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.Finanzas_KPIs_Historico ADD CONSTRAINT [PK__Finanzas__3213E83FB2950434] PRIMARY KEY (id);
CREATE UNIQUE INDEX [UX_Finanzas_KPIs_Historico] ON dbo.Finanzas_KPIs_Historico (server_id, sucursal_id, system_type_normalized, fecha, kpi_tipo);
GO

-- =================================================
-- Tabla: Finanzas_Pagos
-- Exportado: 2026-06-03T06:45:32.741425
-- =================================================

IF OBJECT_ID('dbo.Finanzas_Pagos', 'U') IS NOT NULL
    DROP TABLE dbo.Finanzas_Pagos;
GO

CREATE TABLE dbo.Finanzas_Pagos (
    [PagoID] BIGINT NOT NULL,
    [CuentaPorPagarID] BIGINT NOT NULL,
    [FechaPago] DATE NOT NULL,
    [MontoPagado] DECIMAL(18,2) NOT NULL,
    [FormaPagoID] INT NULL,
    [CuentaBancariaID] INT NULL,
    [NumeroReferencia] VARCHAR(50) NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.Finanzas_Pagos ADD CONSTRAINT [PK__Finanzas__F00B61581914A9DE] PRIMARY KEY (PagoID);
GO

-- =================================================
-- Tabla: Finanzas_Presupuestos
-- Exportado: 2026-06-03T06:45:32.945867
-- =================================================

IF OBJECT_ID('dbo.Finanzas_Presupuestos', 'U') IS NOT NULL
    DROP TABLE dbo.Finanzas_Presupuestos;
GO

CREATE TABLE dbo.Finanzas_Presupuestos (
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
    [Creado_Por] NVARCHAR(100) NULL
);
GO

CREATE INDEX [IX_Presupuestos_Periodo] ON dbo.Finanzas_Presupuestos (Anio, Mes);
CREATE INDEX [IX_Presupuestos_Sucursal] ON dbo.Finanzas_Presupuestos (SucursalID);
ALTER TABLE dbo.Finanzas_Presupuestos ADD CONSTRAINT [PK__Finanzas__E2E3631F081C8712] PRIMARY KEY (PresupuestoID);
GO

-- =================================================
-- Tabla: Finanzas_PropinasTPV_SyncLog
-- Exportado: 2026-06-03T06:45:33.150440
-- =================================================

IF OBJECT_ID('dbo.Finanzas_PropinasTPV_SyncLog', 'U') IS NOT NULL
    DROP TABLE dbo.Finanzas_PropinasTPV_SyncLog;
GO

CREATE TABLE dbo.Finanzas_PropinasTPV_SyncLog (
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
    [DuracionSegundos] INT NULL
);
GO

CREATE INDEX [IX_PropinasTPV_SyncLog_Fecha] ON dbo.Finanzas_PropinasTPV_SyncLog (FechaInicio);
CREATE INDEX [IX_PropinasTPV_SyncLog_Sistema] ON dbo.Finanzas_PropinasTPV_SyncLog (SistemaOrigen, Estatus);
CREATE INDEX [IX_PropinasTPV_SyncLog_Unidad] ON dbo.Finanzas_PropinasTPV_SyncLog (UnidadNegocioID, FechaInicio);
ALTER TABLE dbo.Finanzas_PropinasTPV_SyncLog ADD CONSTRAINT [PK__Finanzas__5E5499A81A623369] PRIMARY KEY (LogID);
GO

-- =================================================
-- Tabla: Finanzas_SaldosBancarios
-- Exportado: 2026-06-03T06:45:34.617509
-- =================================================

IF OBJECT_ID('dbo.Finanzas_SaldosBancarios', 'U') IS NOT NULL
    DROP TABLE dbo.Finanzas_SaldosBancarios;
GO

CREATE TABLE dbo.Finanzas_SaldosBancarios (
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
    [MotivoCancelacion] VARCHAR(500) NULL
);
GO

CREATE INDEX [IX_SaldosBancarios_CuentaHistorial] ON dbo.Finanzas_SaldosBancarios (SaldoFinal, EsVigente, Activo, Estatus, CuentaBancariaID, FechaSaldo);
CREATE INDEX [IX_SaldosBancarios_FechaSaldo] ON dbo.Finanzas_SaldosBancarios (CuentaBancariaID, SaldoFinal, EsVigente, Activo, FechaSaldo);
CREATE INDEX [IX_SaldosBancarios_UltimoVigente] ON dbo.Finanzas_SaldosBancarios (FechaSaldo, SaldoFinal, CuentaBancariaID);
ALTER TABLE dbo.Finanzas_SaldosBancarios ADD CONSTRAINT [PK_Finanzas_SaldosBancarios] PRIMARY KEY (SaldoBancarioID);
CREATE UNIQUE INDEX [UQ_SaldosBancarios_CuentaFecha_EsVigente] ON dbo.Finanzas_SaldosBancarios (CuentaBancariaID, FechaSaldo);
GO

-- =================================================
-- Tabla: Global_Cat_Bancos
-- Exportado: 2026-06-03T06:45:34.822362
-- =================================================

IF OBJECT_ID('dbo.Global_Cat_Bancos', 'U') IS NOT NULL
    DROP TABLE dbo.Global_Cat_Bancos;
GO

CREATE TABLE dbo.Global_Cat_Bancos (
    [BancoID] INT NOT NULL,
    [CodigoBanco] VARCHAR(10) NOT NULL,
    [NombreBanco] VARCHAR(100) NOT NULL,
    [NombreCorto] VARCHAR(50) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.Global_Cat_Bancos ADD CONSTRAINT [PK__Global_C__4A8BAC158988E013] PRIMARY KEY (BancoID);
CREATE UNIQUE INDEX [UQ__Global_C__EAFB8B884039F1DE] ON dbo.Global_Cat_Bancos (CodigoBanco);
GO

-- =================================================
-- Tabla: Global_Cat_FormaPagoSAT
-- Exportado: 2026-06-03T06:45:35.057947
-- =================================================

IF OBJECT_ID('dbo.Global_Cat_FormaPagoSAT', 'U') IS NOT NULL
    DROP TABLE dbo.Global_Cat_FormaPagoSAT;
GO

CREATE TABLE dbo.Global_Cat_FormaPagoSAT (
    [FormaPagoID] INT NOT NULL,
    [Clave] VARCHAR(5) NOT NULL,
    [Descripcion] VARCHAR(150) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Global_Cat_FormaPagoSAT ADD CONSTRAINT [PK__Global_C__920B091EF7BCA6E7] PRIMARY KEY (FormaPagoID);
CREATE UNIQUE INDEX [UQ__Global_C__E8181E11CB985BF5] ON dbo.Global_Cat_FormaPagoSAT (Clave);
GO

-- =================================================
-- Tabla: Inventario_Almacenes
-- Exportado: 2026-06-03T06:45:35.292802
-- =================================================

IF OBJECT_ID('dbo.Inventario_Almacenes', 'U') IS NOT NULL
    DROP TABLE dbo.Inventario_Almacenes;
GO

CREATE TABLE dbo.Inventario_Almacenes (
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
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.Inventario_Almacenes ADD CONSTRAINT [PK_Inventario_Almacenes] PRIMARY KEY (AlmacenID);
CREATE UNIQUE INDEX [UQ_Inventario_Almacenes_Sucursal_Codigo] ON dbo.Inventario_Almacenes (SucursalID, CodigoAlmacen);
GO

-- =================================================
-- Tabla: Inventario_Existencias
-- Exportado: 2026-06-03T06:45:35.497443
-- =================================================

IF OBJECT_ID('dbo.Inventario_Existencias', 'U') IS NOT NULL
    DROP TABLE dbo.Inventario_Existencias;
GO

CREATE TABLE dbo.Inventario_Existencias (
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
    [FechaModificacion] DATETIME2 NULL
);
GO

CREATE INDEX [IX_Inventario_Existencias_Consulta] ON dbo.Inventario_Existencias (ExistenciaActual, CostoPromedio, UltimaFechaMovimiento, SucursalID, AlmacenID, ProductoID, PresentacionProductoID);
ALTER TABLE dbo.Inventario_Existencias ADD CONSTRAINT [PK_Inventario_Existencias] PRIMARY KEY (ExistenciaID);
CREATE UNIQUE INDEX [UQ_Inventario_Existencias_Clave] ON dbo.Inventario_Existencias (SucursalID, AlmacenID, ProductoID, PresentacionProductoID);
GO

-- =================================================
-- Tabla: Inventario_Movimientos
-- Exportado: 2026-06-03T06:45:35.701923
-- =================================================

IF OBJECT_ID('dbo.Inventario_Movimientos', 'U') IS NOT NULL
    DROP TABLE dbo.Inventario_Movimientos;
GO

CREATE TABLE dbo.Inventario_Movimientos (
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
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

CREATE INDEX [IX_Inventario_Movimientos_Ref] ON dbo.Inventario_Movimientos (ReferenciaTipo, ReferenciaID, FechaMovimiento);
CREATE INDEX [IX_Inventario_Movimientos_SucursalAlmacenFecha] ON dbo.Inventario_Movimientos (SucursalID, AlmacenID, FechaMovimiento);
ALTER TABLE dbo.Inventario_Movimientos ADD CONSTRAINT [PK_Inventario_Movimientos] PRIMARY KEY (MovimientoID);
GO

-- =================================================
-- Tabla: Inventario_MovimientosDetalle
-- Exportado: 2026-06-03T06:45:35.906778
-- =================================================

IF OBJECT_ID('dbo.Inventario_MovimientosDetalle', 'U') IS NOT NULL
    DROP TABLE dbo.Inventario_MovimientosDetalle;
GO

CREATE TABLE dbo.Inventario_MovimientosDetalle (
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
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

CREATE INDEX [IX_Inventario_MovimientosDetalle_Producto] ON dbo.Inventario_MovimientosDetalle (ProductoID, PresentacionProductoID, MovimientoID);
ALTER TABLE dbo.Inventario_MovimientosDetalle ADD CONSTRAINT [PK_Inventario_MovimientosDetalle] PRIMARY KEY (MovimientoDetalleID);
GO

-- =================================================
-- Tabla: Inventario_TipoMovimiento
-- Exportado: 2026-06-03T06:45:36.111938
-- =================================================

IF OBJECT_ID('dbo.Inventario_TipoMovimiento', 'U') IS NOT NULL
    DROP TABLE dbo.Inventario_TipoMovimiento;
GO

CREATE TABLE dbo.Inventario_TipoMovimiento (
    [TipoMovimientoID] TINYINT NOT NULL,
    [Codigo] VARCHAR(30) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [Naturaleza] CHAR(1) NOT NULL,
    [AfectaCostoPromedio] BIT NOT NULL DEFAULT ((1)),
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Inventario_TipoMovimiento ADD CONSTRAINT [PK_Inventario_TipoMovimiento] PRIMARY KEY (TipoMovimientoID);
CREATE UNIQUE INDEX [UQ_Inventario_TipoMovimiento_Codigo] ON dbo.Inventario_TipoMovimiento (Codigo);
GO

-- =================================================
-- Tabla: Inventarios_SinAsignar
-- Exportado: 2026-06-03T06:45:36.347943
-- =================================================

IF OBJECT_ID('dbo.Inventarios_SinAsignar', 'U') IS NOT NULL
    DROP TABLE dbo.Inventarios_SinAsignar;
GO

CREATE TABLE dbo.Inventarios_SinAsignar (
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
    [Notificado] BIT NULL DEFAULT ((0))
);
GO

CREATE INDEX [IX_SinAsignar_Estado] ON dbo.Inventarios_SinAsignar (Estado);
CREATE INDEX [IX_SinAsignar_ServerID] ON dbo.Inventarios_SinAsignar (ServerID);
ALTER TABLE dbo.Inventarios_SinAsignar ADD CONSTRAINT [PK__Inventar__3214EC27F3F32C29] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ__Inventar__B897313F0C45543A] ON dbo.Inventarios_SinAsignar (RegistroID);
GO

-- =================================================
-- Tabla: Operaciones_Tablaje_Auditoria
-- Exportado: 2026-06-03T06:45:36.584956
-- =================================================

IF OBJECT_ID('dbo.Operaciones_Tablaje_Auditoria', 'U') IS NOT NULL
    DROP TABLE dbo.Operaciones_Tablaje_Auditoria;
GO

CREATE TABLE dbo.Operaciones_Tablaje_Auditoria (
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
    [FechaHoraUTC] DATETIME2 NOT NULL DEFAULT (sysutcdatetime())
);
GO

ALTER TABLE dbo.Operaciones_Tablaje_Auditoria ADD CONSTRAINT [PK__Operacio__095694E3E3EECE8C] PRIMARY KEY (AuditoriaID);
GO

-- =================================================
-- Tabla: Operaciones_Tablaje_Autorizaciones
-- Exportado: 2026-06-03T06:45:36.790834
-- =================================================

IF OBJECT_ID('dbo.Operaciones_Tablaje_Autorizaciones', 'U') IS NOT NULL
    DROP TABLE dbo.Operaciones_Tablaje_Autorizaciones;
GO

CREATE TABLE dbo.Operaciones_Tablaje_Autorizaciones (
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
    [FechaOperacionMexico] DATE NOT NULL
);
GO

ALTER TABLE dbo.Operaciones_Tablaje_Autorizaciones ADD CONSTRAINT [PK__Operacio__08107E3571E7F5FE] PRIMARY KEY (AutorizacionID);
GO

-- =================================================
-- Tabla: Operaciones_Tablaje_Costos
-- Exportado: 2026-06-03T06:45:36.996541
-- =================================================

IF OBJECT_ID('dbo.Operaciones_Tablaje_Costos', 'U') IS NOT NULL
    DROP TABLE dbo.Operaciones_Tablaje_Costos;
GO

CREATE TABLE dbo.Operaciones_Tablaje_Costos (
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
    [UsuarioCalculoID] UNIQUEIDENTIFIER NULL
);
GO

ALTER TABLE dbo.Operaciones_Tablaje_Costos ADD CONSTRAINT [PK__Operacio__501474F5BA858FD5] PRIMARY KEY (CostoID);
GO

-- =================================================
-- Tabla: Operaciones_Tablaje_Documentos
-- Exportado: 2026-06-03T06:45:37.199671
-- =================================================

IF OBJECT_ID('dbo.Operaciones_Tablaje_Documentos', 'U') IS NOT NULL
    DROP TABLE dbo.Operaciones_Tablaje_Documentos;
GO

CREATE TABLE dbo.Operaciones_Tablaje_Documentos (
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
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Operaciones_Tablaje_Documentos ADD CONSTRAINT [PK__Operacio__5DDBFF96A5DADA2C] PRIMARY KEY (DocumentoID);
GO

-- =================================================
-- Tabla: Operaciones_Tablaje_EventosContables
-- Exportado: 2026-06-03T06:45:37.403313
-- =================================================

IF OBJECT_ID('dbo.Operaciones_Tablaje_EventosContables', 'U') IS NOT NULL
    DROP TABLE dbo.Operaciones_Tablaje_EventosContables;
GO

CREATE TABLE dbo.Operaciones_Tablaje_EventosContables (
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
    [MensajeError] NVARCHAR(500) NULL
);
GO

ALTER TABLE dbo.Operaciones_Tablaje_EventosContables ADD CONSTRAINT [PK__Operacio__06192139FD321EAD] PRIMARY KEY (EventoContableID);
GO

-- =================================================
-- Tabla: Operaciones_Tablaje_Mermas
-- Exportado: 2026-06-03T06:45:37.607266
-- =================================================

IF OBJECT_ID('dbo.Operaciones_Tablaje_Mermas', 'U') IS NOT NULL
    DROP TABLE dbo.Operaciones_Tablaje_Mermas;
GO

CREATE TABLE dbo.Operaciones_Tablaje_Mermas (
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
    [UsuarioRegistroID] UNIQUEIDENTIFIER NULL
);
GO

ALTER TABLE dbo.Operaciones_Tablaje_Mermas ADD CONSTRAINT [PK__Operacio__01D892A5864EAFD0] PRIMARY KEY (MermaID);
GO

-- =================================================
-- Tabla: Operaciones_Tablaje_Ordenes
-- Exportado: 2026-06-03T06:45:37.854024
-- =================================================

IF OBJECT_ID('dbo.Operaciones_Tablaje_Ordenes', 'U') IS NOT NULL
    DROP TABLE dbo.Operaciones_Tablaje_Ordenes;
GO

CREATE TABLE dbo.Operaciones_Tablaje_Ordenes (
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
    [UsuarioModificacionID] UNIQUEIDENTIFIER NULL
);
GO

ALTER TABLE dbo.Operaciones_Tablaje_Ordenes ADD CONSTRAINT [PK__Operacio__C088A4E4C892A4C1] PRIMARY KEY (OrdenID);
GO

-- =================================================
-- Tabla: Operaciones_Tablaje_OrdenesDetalle
-- Exportado: 2026-06-03T06:45:38.094354
-- =================================================

IF OBJECT_ID('dbo.Operaciones_Tablaje_OrdenesDetalle', 'U') IS NOT NULL
    DROP TABLE dbo.Operaciones_Tablaje_OrdenesDetalle;
GO

CREATE TABLE dbo.Operaciones_Tablaje_OrdenesDetalle (
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
    [UsuarioCapturaID] UNIQUEIDENTIFIER NULL
);
GO

ALTER TABLE dbo.Operaciones_Tablaje_OrdenesDetalle ADD CONSTRAINT [PK__Operacio__19C585727C91CE8A] PRIMARY KEY (OrdenDetalleID);
GO

-- =================================================
-- Tabla: Operaciones_Tablaje_Plantillas
-- Exportado: 2026-06-03T06:45:38.332405
-- =================================================

IF OBJECT_ID('dbo.Operaciones_Tablaje_Plantillas', 'U') IS NOT NULL
    DROP TABLE dbo.Operaciones_Tablaje_Plantillas;
GO

CREATE TABLE dbo.Operaciones_Tablaje_Plantillas (
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
    [UsuarioModificacionID] UNIQUEIDENTIFIER NULL
);
GO

ALTER TABLE dbo.Operaciones_Tablaje_Plantillas ADD CONSTRAINT [PK__Operacio__C5DEB58CD8D65346] PRIMARY KEY (PlantillaID);
GO

-- =================================================
-- Tabla: Operaciones_Tablaje_PlantillasDetalle
-- Exportado: 2026-06-03T06:45:38.575987
-- =================================================

IF OBJECT_ID('dbo.Operaciones_Tablaje_PlantillasDetalle', 'U') IS NOT NULL
    DROP TABLE dbo.Operaciones_Tablaje_PlantillasDetalle;
GO

CREATE TABLE dbo.Operaciones_Tablaje_PlantillasDetalle (
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
    [FechaModificacionUTC] DATETIME2 NULL
);
GO

ALTER TABLE dbo.Operaciones_Tablaje_PlantillasDetalle ADD CONSTRAINT [PK__Operacio__3F6228CF71B2CEE8] PRIMARY KEY (PlantillaDetalleID);
GO

-- =================================================
-- Tabla: Operaciones_Tablaje_PlantillasVersiones
-- Exportado: 2026-06-03T06:45:38.817608
-- =================================================

IF OBJECT_ID('dbo.Operaciones_Tablaje_PlantillasVersiones', 'U') IS NOT NULL
    DROP TABLE dbo.Operaciones_Tablaje_PlantillasVersiones;
GO

CREATE TABLE dbo.Operaciones_Tablaje_PlantillasVersiones (
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
    [UsuarioVersionID] UNIQUEIDENTIFIER NULL
);
GO

ALTER TABLE dbo.Operaciones_Tablaje_PlantillasVersiones ADD CONSTRAINT [PK__Operacio__16C6402F89308728] PRIMARY KEY (VersionID);
GO

-- =================================================
-- Tabla: Operaciones_Tablaje_Rendimientos
-- Exportado: 2026-06-03T06:45:39.022032
-- =================================================

IF OBJECT_ID('dbo.Operaciones_Tablaje_Rendimientos', 'U') IS NOT NULL
    DROP TABLE dbo.Operaciones_Tablaje_Rendimientos;
GO

CREATE TABLE dbo.Operaciones_Tablaje_Rendimientos (
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
    [FechaRegistroUTC] DATETIME2 NOT NULL DEFAULT (sysutcdatetime())
);
GO

ALTER TABLE dbo.Operaciones_Tablaje_Rendimientos ADD CONSTRAINT [PK__Operacio__39F71683899F036C] PRIMARY KEY (RendimientoID);
GO

-- =================================================
-- Tabla: Operaciones_Tablaje_SyncErrores
-- Exportado: 2026-06-03T06:45:39.260652
-- =================================================

IF OBJECT_ID('dbo.Operaciones_Tablaje_SyncErrores', 'U') IS NOT NULL
    DROP TABLE dbo.Operaciones_Tablaje_SyncErrores;
GO

CREATE TABLE dbo.Operaciones_Tablaje_SyncErrores (
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
    [FechaErrorUTC] DATETIME2 NOT NULL DEFAULT (sysutcdatetime())
);
GO

ALTER TABLE dbo.Operaciones_Tablaje_SyncErrores ADD CONSTRAINT [PK__Operacio__358565CA958316D2] PRIMARY KEY (ErrorID);
GO

-- =================================================
-- Tabla: Operaciones_Tablaje_SyncLog
-- Exportado: 2026-06-03T06:45:39.465584
-- =================================================

IF OBJECT_ID('dbo.Operaciones_Tablaje_SyncLog', 'U') IS NOT NULL
    DROP TABLE dbo.Operaciones_Tablaje_SyncLog;
GO

CREATE TABLE dbo.Operaciones_Tablaje_SyncLog (
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
    [EjecutadoPor] UNIQUEIDENTIFIER NULL
);
GO

ALTER TABLE dbo.Operaciones_Tablaje_SyncLog ADD CONSTRAINT [PK__Operacio__A40EB328C806169D] PRIMARY KEY (SyncLogID);
GO

-- =================================================
-- Tabla: Operativo_AuditoriasProgramadas
-- Exportado: 2026-06-03T06:45:39.702364
-- =================================================

IF OBJECT_ID('dbo.Operativo_AuditoriasProgramadas', 'U') IS NOT NULL
    DROP TABLE dbo.Operativo_AuditoriasProgramadas;
GO

CREATE TABLE dbo.Operativo_AuditoriasProgramadas (
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
    [ConfiguracionJSON] NVARCHAR(MAX) NULL
);
GO

CREATE INDEX [IX_OpAudProg_Estado] ON dbo.Operativo_AuditoriasProgramadas (Estado);
CREATE INDEX [IX_OpAudProg_ProximaEjecucion] ON dbo.Operativo_AuditoriasProgramadas (ProximaEjecucion);
CREATE INDEX [IX_OpAudProg_ServerID] ON dbo.Operativo_AuditoriasProgramadas (ServerID);
ALTER TABLE dbo.Operativo_AuditoriasProgramadas ADD CONSTRAINT [PK__Operativ__3214EC2731BBE610] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ_OpAudProg_AuditoriaID] ON dbo.Operativo_AuditoriasProgramadas (AuditoriaID);
GO

-- =================================================
-- Tabla: Operativo_BitacoraCompras
-- Exportado: 2026-06-03T06:45:39.906061
-- =================================================

IF OBJECT_ID('dbo.Operativo_BitacoraCompras', 'U') IS NOT NULL
    DROP TABLE dbo.Operativo_BitacoraCompras;
GO

CREATE TABLE dbo.Operativo_BitacoraCompras (
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
    [MetadatosJSON] NVARCHAR(MAX) NULL
);
GO

CREATE INDEX [IX_OpBitComp_AutomatizacionID] ON dbo.Operativo_BitacoraCompras (AutomatizacionID);
CREATE INDEX [IX_OpBitComp_Fecha] ON dbo.Operativo_BitacoraCompras (Fecha);
ALTER TABLE dbo.Operativo_BitacoraCompras ADD CONSTRAINT [PK__Operativ__3214EC27FA31480C] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ_OpBitComp_BitacoraID] ON dbo.Operativo_BitacoraCompras (BitacoraID);
GO

-- =================================================
-- Tabla: Operativo_CargosResponsabilidad
-- Exportado: 2026-06-03T06:45:40.111960
-- =================================================

IF OBJECT_ID('dbo.Operativo_CargosResponsabilidad', 'U') IS NOT NULL
    DROP TABLE dbo.Operativo_CargosResponsabilidad;
GO

CREATE TABLE dbo.Operativo_CargosResponsabilidad (
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
    [MetadatosJSON] NVARCHAR(MAX) NULL
);
GO

CREATE INDEX [IX_OpCargo_EstatusCargo] ON dbo.Operativo_CargosResponsabilidad (EstatusCargo);
CREATE INDEX [IX_OpCargo_FechaPropuesta] ON dbo.Operativo_CargosResponsabilidad (FechaPropuesta);
CREATE INDEX [IX_OpCargo_ResponsabilidadID] ON dbo.Operativo_CargosResponsabilidad (ResponsabilidadID);
CREATE INDEX [IX_OpCargo_WorkflowID] ON dbo.Operativo_CargosResponsabilidad (WorkflowID);
ALTER TABLE dbo.Operativo_CargosResponsabilidad ADD CONSTRAINT [PK__Operativ__3214EC2770CB8C6E] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ_OpCargo_CargoID] ON dbo.Operativo_CargosResponsabilidad (CargoID);
GO

-- =================================================
-- Tabla: Operativo_DocumentosGenerados
-- Exportado: 2026-06-03T06:45:40.316078
-- =================================================

IF OBJECT_ID('dbo.Operativo_DocumentosGenerados', 'U') IS NOT NULL
    DROP TABLE dbo.Operativo_DocumentosGenerados;
GO

CREATE TABLE dbo.Operativo_DocumentosGenerados (
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
    [MetadatosJSON] NVARCHAR(MAX) NULL
);
GO

CREATE INDEX [IX_OpDocGen_FechaGeneracion] ON dbo.Operativo_DocumentosGenerados (FechaGeneracion);
CREATE INDEX [IX_OpDocGen_TipoDocumento] ON dbo.Operativo_DocumentosGenerados (TipoDocumento);
CREATE INDEX [IX_OpDocGen_WorkflowID] ON dbo.Operativo_DocumentosGenerados (WorkflowID);
ALTER TABLE dbo.Operativo_DocumentosGenerados ADD CONSTRAINT [PK__Operativ__3214EC2713D7A113] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ_OpDocGen_DocumentoID] ON dbo.Operativo_DocumentosGenerados (DocumentoID);
GO

-- =================================================
-- Tabla: Operativo_HistorialAsignaciones
-- Exportado: 2026-06-03T06:45:40.520035
-- =================================================

IF OBJECT_ID('dbo.Operativo_HistorialAsignaciones', 'U') IS NOT NULL
    DROP TABLE dbo.Operativo_HistorialAsignaciones;
GO

CREATE TABLE dbo.Operativo_HistorialAsignaciones (
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
    [FechaAsignacion] DATETIME2 NULL DEFAULT (getutcdate())
);
GO

CREATE INDEX [IX_OpHist_FechaAsignacion] ON dbo.Operativo_HistorialAsignaciones (FechaAsignacion);
CREATE INDEX [IX_OpHist_TareaID] ON dbo.Operativo_HistorialAsignaciones (TareaID);
CREATE INDEX [IX_OpHist_WorkflowID] ON dbo.Operativo_HistorialAsignaciones (WorkflowID);
ALTER TABLE dbo.Operativo_HistorialAsignaciones ADD CONSTRAINT [PK__Operativ__3214EC279CA8B4D4] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ_OpHist_HistorialID] ON dbo.Operativo_HistorialAsignaciones (HistorialID);
GO

-- =================================================
-- Tabla: Operativo_HistorialCargos
-- Exportado: 2026-06-03T06:45:40.725473
-- =================================================

IF OBJECT_ID('dbo.Operativo_HistorialCargos', 'U') IS NOT NULL
    DROP TABLE dbo.Operativo_HistorialCargos;
GO

CREATE TABLE dbo.Operativo_HistorialCargos (
    [ID] INT NOT NULL,
    [HistorialID] VARCHAR(50) NOT NULL,
    [CargoID] VARCHAR(50) NOT NULL,
    [Accion] VARCHAR(50) NOT NULL,
    [UsuarioID] VARCHAR(50) NOT NULL,
    [UsuarioNombre] VARCHAR(200) NULL,
    [Detalle] NVARCHAR(MAX) NULL,
    [EstadoAnterior] VARCHAR(50) NULL,
    [EstadoNuevo] VARCHAR(50) NULL,
    [Fecha] DATETIME2 NULL DEFAULT (getutcdate())
);
GO

CREATE INDEX [IX_OpHistCargo_CargoID] ON dbo.Operativo_HistorialCargos (CargoID);
CREATE INDEX [IX_OpHistCargo_Fecha] ON dbo.Operativo_HistorialCargos (Fecha);
ALTER TABLE dbo.Operativo_HistorialCargos ADD CONSTRAINT [PK__Operativ__3214EC27CC43D10B] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ_OpHistCargo_HistorialID] ON dbo.Operativo_HistorialCargos (HistorialID);
GO

-- =================================================
-- Tabla: Operativo_Notificaciones_Log
-- Exportado: 2026-06-03T06:45:40.931529
-- =================================================

IF OBJECT_ID('dbo.Operativo_Notificaciones_Log', 'U') IS NOT NULL
    DROP TABLE dbo.Operativo_Notificaciones_Log;
GO

CREATE TABLE dbo.Operativo_Notificaciones_Log (
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
    [MetadatosJSON] NVARCHAR(MAX) NULL
);
GO

CREATE INDEX [IX_OpNotif_Estado] ON dbo.Operativo_Notificaciones_Log (Estado);
CREATE INDEX [IX_OpNotif_FechaEnvio] ON dbo.Operativo_Notificaciones_Log (FechaEnvio);
CREATE INDEX [IX_OpNotif_TareaID] ON dbo.Operativo_Notificaciones_Log (TareaID);
CREATE INDEX [IX_OpNotif_TipoEvento] ON dbo.Operativo_Notificaciones_Log (TipoEvento);
CREATE INDEX [IX_OpNotif_WorkflowID] ON dbo.Operativo_Notificaciones_Log (WorkflowID);
ALTER TABLE dbo.Operativo_Notificaciones_Log ADD CONSTRAINT [PK__Operativ__3214EC2710D5B83C] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ_OpNotif_NotificacionID] ON dbo.Operativo_Notificaciones_Log (NotificacionID);
GO

-- =================================================
-- Tabla: Operativo_PedidosProcesados
-- Exportado: 2026-06-03T06:45:41.137027
-- =================================================

IF OBJECT_ID('dbo.Operativo_PedidosProcesados', 'U') IS NOT NULL
    DROP TABLE dbo.Operativo_PedidosProcesados;
GO

CREATE TABLE dbo.Operativo_PedidosProcesados (
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
    [DetalleJSON] NVARCHAR(MAX) NULL
);
GO

CREATE INDEX [IX_OpPedProc_AutomatizacionID] ON dbo.Operativo_PedidosProcesados (AutomatizacionID);
CREATE INDEX [IX_OpPedProc_FechaProcesamiento] ON dbo.Operativo_PedidosProcesados (FechaProcesamiento);
ALTER TABLE dbo.Operativo_PedidosProcesados ADD CONSTRAINT [PK__Operativ__3214EC27D6F5830C] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ_OpPedProc_PedidoID] ON dbo.Operativo_PedidosProcesados (PedidoID);
GO

-- =================================================
-- Tabla: Operativo_ResponsabilidadEconomica
-- Exportado: 2026-06-03T06:45:41.341697
-- =================================================

IF OBJECT_ID('dbo.Operativo_ResponsabilidadEconomica', 'U') IS NOT NULL
    DROP TABLE dbo.Operativo_ResponsabilidadEconomica;
GO

CREATE TABLE dbo.Operativo_ResponsabilidadEconomica (
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
    [MetadatosJSON] NVARCHAR(MAX) NULL
);
GO

CREATE INDEX [IX_OpResp_Estado] ON dbo.Operativo_ResponsabilidadEconomica (Estado);
CREATE INDEX [IX_OpResp_FechaCalculo] ON dbo.Operativo_ResponsabilidadEconomica (FechaCalculo);
CREATE INDEX [IX_OpResp_SucursalID] ON dbo.Operativo_ResponsabilidadEconomica (SucursalID);
CREATE INDEX [IX_OpResp_WorkflowID] ON dbo.Operativo_ResponsabilidadEconomica (WorkflowID);
ALTER TABLE dbo.Operativo_ResponsabilidadEconomica ADD CONSTRAINT [PK__Operativ__3214EC273AD9BA8B] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ_OpResp_ResponsabilidadID] ON dbo.Operativo_ResponsabilidadEconomica (ResponsabilidadID);
GO

-- =================================================
-- Tabla: Operativo_TareasCompras
-- Exportado: 2026-06-03T06:45:41.546432
-- =================================================

IF OBJECT_ID('dbo.Operativo_TareasCompras', 'U') IS NOT NULL
    DROP TABLE dbo.Operativo_TareasCompras;
GO

CREATE TABLE dbo.Operativo_TareasCompras (
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
    [MetadatosJSON] NVARCHAR(MAX) NULL
);
GO

CREATE INDEX [IX_OpTareaComp_AutomatizacionID] ON dbo.Operativo_TareasCompras (AutomatizacionID);
CREATE INDEX [IX_OpTareaComp_Estado] ON dbo.Operativo_TareasCompras (Estado);
CREATE INDEX [IX_OpTareaComp_FechaCreacion] ON dbo.Operativo_TareasCompras (FechaCreacion);
ALTER TABLE dbo.Operativo_TareasCompras ADD CONSTRAINT [PK__Operativ__3214EC2755FDE1DA] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ_OpTareaComp_TareaID] ON dbo.Operativo_TareasCompras (TareaID);
GO

-- =================================================
-- Tabla: Producto_Catalogo
-- Exportado: 2026-06-03T06:45:41.754026
-- =================================================

IF OBJECT_ID('dbo.Producto_Catalogo', 'U') IS NOT NULL
    DROP TABLE dbo.Producto_Catalogo;
GO

CREATE TABLE dbo.Producto_Catalogo (
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
    [ModifiedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_Producto_Catalogo_Activo] ON dbo.Producto_Catalogo (Activo);
CREATE INDEX [IX_Producto_Catalogo_LineaProductoID] ON dbo.Producto_Catalogo (LineaProductoID);
CREATE INDEX [IX_Producto_Catalogo_MarcaProductoID] ON dbo.Producto_Catalogo (MarcaProductoID);
CREATE INDEX [IX_Producto_Catalogo_NombreProducto] ON dbo.Producto_Catalogo (NombreProducto);
ALTER TABLE dbo.Producto_Catalogo ADD CONSTRAINT [PK_Producto_Catalogo] PRIMARY KEY (ProductoID);
CREATE UNIQUE INDEX [UQ_Producto_Catalogo_CodigoProducto] ON dbo.Producto_Catalogo (CodigoProducto);
CREATE UNIQUE INDEX [UQ_Producto_Catalogo_SKU] ON dbo.Producto_Catalogo (SKU);
GO

-- =================================================
-- Tabla: Producto_Equivalentes
-- Exportado: 2026-06-03T06:45:41.959839
-- =================================================

IF OBJECT_ID('dbo.Producto_Equivalentes', 'U') IS NOT NULL
    DROP TABLE dbo.Producto_Equivalentes;
GO

CREATE TABLE dbo.Producto_Equivalentes (
    [ProductoEquivalenteID] BIGINT NOT NULL,
    [ProductoID] INT NOT NULL,
    [ProductoEquivalenteRefID] INT NOT NULL,
    [TipoEquivalencia] VARCHAR(20) NOT NULL DEFAULT ('TOTAL'),
    [FactorEquivalencia] DECIMAL(18,6) NOT NULL DEFAULT ((1)),
    [Observaciones] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

CREATE INDEX [IX_Producto_Equivalentes_ProductoID] ON dbo.Producto_Equivalentes (ProductoID);
ALTER TABLE dbo.Producto_Equivalentes ADD CONSTRAINT [PK_Producto_Equivalentes] PRIMARY KEY (ProductoEquivalenteID);
CREATE UNIQUE INDEX [UQ_Producto_Equivalentes] ON dbo.Producto_Equivalentes (ProductoID, ProductoEquivalenteRefID);
GO

-- =================================================
-- Tabla: Producto_Familias
-- Exportado: 2026-06-03T06:45:42.163470
-- =================================================

IF OBJECT_ID('dbo.Producto_Familias', 'U') IS NOT NULL
    DROP TABLE dbo.Producto_Familias;
GO

CREATE TABLE dbo.Producto_Familias (
    [FamiliaProductoID] INT NOT NULL,
    [CodigoFamilia] VARCHAR(20) NOT NULL,
    [NombreFamilia] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.Producto_Familias ADD CONSTRAINT [PK_Producto_Familias] PRIMARY KEY (FamiliaProductoID);
CREATE UNIQUE INDEX [UQ_Producto_Familias_CodigoFamilia] ON dbo.Producto_Familias (CodigoFamilia);
CREATE UNIQUE INDEX [UQ_Producto_Familias_NombreFamilia] ON dbo.Producto_Familias (NombreFamilia);
GO

-- =================================================
-- Tabla: Producto_Lineas
-- Exportado: 2026-06-03T06:45:42.366905
-- =================================================

IF OBJECT_ID('dbo.Producto_Lineas', 'U') IS NOT NULL
    DROP TABLE dbo.Producto_Lineas;
GO

CREATE TABLE dbo.Producto_Lineas (
    [LineaProductoID] INT NOT NULL,
    [SubFamiliaProductoID] INT NOT NULL,
    [CodigoLinea] VARCHAR(20) NOT NULL,
    [NombreLinea] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.Producto_Lineas ADD CONSTRAINT [PK_Producto_Lineas] PRIMARY KEY (LineaProductoID);
CREATE UNIQUE INDEX [UQ_Producto_Lineas_CodigoLinea] ON dbo.Producto_Lineas (CodigoLinea);
CREATE UNIQUE INDEX [UQ_Producto_Lineas_SubFamilia_Nombre] ON dbo.Producto_Lineas (SubFamiliaProductoID, NombreLinea);
GO

-- =================================================
-- Tabla: Producto_Marcas
-- Exportado: 2026-06-03T06:45:42.571822
-- =================================================

IF OBJECT_ID('dbo.Producto_Marcas', 'U') IS NOT NULL
    DROP TABLE dbo.Producto_Marcas;
GO

CREATE TABLE dbo.Producto_Marcas (
    [MarcaProductoID] INT NOT NULL,
    [CodigoMarca] VARCHAR(20) NOT NULL,
    [NombreMarca] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.Producto_Marcas ADD CONSTRAINT [PK_Producto_Marcas] PRIMARY KEY (MarcaProductoID);
CREATE UNIQUE INDEX [UQ_Producto_Marcas_CodigoMarca] ON dbo.Producto_Marcas (CodigoMarca);
CREATE UNIQUE INDEX [UQ_Producto_Marcas_NombreMarca] ON dbo.Producto_Marcas (NombreMarca);
GO

-- =================================================
-- Tabla: Producto_Presentaciones
-- Exportado: 2026-06-03T06:45:42.776678
-- =================================================

IF OBJECT_ID('dbo.Producto_Presentaciones', 'U') IS NOT NULL
    DROP TABLE dbo.Producto_Presentaciones;
GO

CREATE TABLE dbo.Producto_Presentaciones (
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
    [FechaModificacion] DATETIME2 NULL
);
GO

CREATE INDEX [IX_Producto_Presentaciones_ProductoID] ON dbo.Producto_Presentaciones (ProductoID);
ALTER TABLE dbo.Producto_Presentaciones ADD CONSTRAINT [PK_Producto_Presentaciones] PRIMARY KEY (PresentacionProductoID);
CREATE UNIQUE INDEX [UQ_Producto_Presentaciones_CodigoPresentacion] ON dbo.Producto_Presentaciones (CodigoPresentacion);
CREATE UNIQUE INDEX [UQ_Producto_Presentaciones_Producto_Nombre] ON dbo.Producto_Presentaciones (ProductoID, NombrePresentacion);
GO

-- =================================================
-- Tabla: Producto_SubFamilias
-- Exportado: 2026-06-03T06:45:42.982840
-- =================================================

IF OBJECT_ID('dbo.Producto_SubFamilias', 'U') IS NOT NULL
    DROP TABLE dbo.Producto_SubFamilias;
GO

CREATE TABLE dbo.Producto_SubFamilias (
    [SubFamiliaProductoID] INT NOT NULL,
    [FamiliaProductoID] INT NOT NULL,
    [CodigoSubFamilia] VARCHAR(20) NOT NULL,
    [NombreSubFamilia] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.Producto_SubFamilias ADD CONSTRAINT [PK_Producto_SubFamilias] PRIMARY KEY (SubFamiliaProductoID);
CREATE UNIQUE INDEX [UQ_Producto_SubFamilias_CodigoSubFamilia] ON dbo.Producto_SubFamilias (CodigoSubFamilia);
CREATE UNIQUE INDEX [UQ_Producto_SubFamilias_Familia_Nombre] ON dbo.Producto_SubFamilias (FamiliaProductoID, NombreSubFamilia);
GO

-- =================================================
-- Tabla: Producto_Sustitutos
-- Exportado: 2026-06-03T06:45:43.187250
-- =================================================

IF OBJECT_ID('dbo.Producto_Sustitutos', 'U') IS NOT NULL
    DROP TABLE dbo.Producto_Sustitutos;
GO

CREATE TABLE dbo.Producto_Sustitutos (
    [ProductoSustitutoID] BIGINT NOT NULL,
    [ProductoID] INT NOT NULL,
    [ProductoSustitutoRefID] INT NOT NULL,
    [Prioridad] TINYINT NOT NULL DEFAULT ((1)),
    [Motivo] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

CREATE INDEX [IX_Producto_Sustitutos_ProductoID] ON dbo.Producto_Sustitutos (ProductoID);
ALTER TABLE dbo.Producto_Sustitutos ADD CONSTRAINT [PK_Producto_Sustitutos] PRIMARY KEY (ProductoSustitutoID);
CREATE UNIQUE INDEX [UQ_Producto_Sustitutos] ON dbo.Producto_Sustitutos (ProductoID, ProductoSustitutoRefID);
GO

-- =================================================
-- Tabla: Products
-- Exportado: 2026-06-03T06:45:43.391629
-- =================================================

IF OBJECT_ID('dbo.Products', 'U') IS NOT NULL
    DROP TABLE dbo.Products;
GO

CREATE TABLE dbo.Products (
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
    [FechaCreacion] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.Products ADD CONSTRAINT [PK__Products__3214EC07D02C0260] PRIMARY KEY (Id);
GO

-- =================================================
-- Tabla: propinas_tpv_config
-- Exportado: 2026-06-03T06:45:43.630918
-- =================================================

IF OBJECT_ID('dbo.propinas_tpv_config', 'U') IS NOT NULL
    DROP TABLE dbo.propinas_tpv_config;
GO

CREATE TABLE dbo.propinas_tpv_config (
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
    [motivo_cambio] VARCHAR(500) NULL
);
GO

CREATE INDEX [IX_config_jerarquia] ON dbo.propinas_tpv_config (alcance_tipo, alcance_server_id, activa);
ALTER TABLE dbo.propinas_tpv_config ADD CONSTRAINT [PK_propinas_tpv_config] PRIMARY KEY (id);
GO

-- =================================================
-- Tabla: propinas_tpv_control
-- Exportado: 2026-06-03T06:45:43.837539
-- =================================================

IF OBJECT_ID('dbo.propinas_tpv_control', 'U') IS NOT NULL
    DROP TABLE dbo.propinas_tpv_control;
GO

CREATE TABLE dbo.propinas_tpv_control (
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
    [EsTarjeta] BIT NOT NULL DEFAULT ((1))
);
GO

CREATE INDEX [IX_propinas_cuadre] ON dbo.propinas_tpv_control (cuadre_estado, fecha_corte);
CREATE INDEX [IX_propinas_fecha_estado] ON dbo.propinas_tpv_control (fecha_corte, cuadre_estado);
CREATE INDEX [IX_propinas_servidor] ON dbo.propinas_tpv_control (server_id, fecha_corte);
CREATE INDEX [IX_propinas_tpv_control_EsDemo] ON dbo.propinas_tpv_control (EsDemo, fecha_corte);
CREATE UNIQUE INDEX [IX_propinas_tpv_control_HashOrigen] ON dbo.propinas_tpv_control (HashOrigen);
CREATE INDEX [IX_propinas_tpv_control_SistemaOrigen] ON dbo.propinas_tpv_control (SistemaOrigen, UnidadNegocioID);
CREATE INDEX [IX_propinas_tpv_control_UnidadNegocio] ON dbo.propinas_tpv_control (UnidadNegocioID, fecha_corte);
CREATE INDEX [IX_propinas_usuarios] ON dbo.propinas_tpv_control (pago_usuario_id, cuadre_usuario_id);
ALTER TABLE dbo.propinas_tpv_control ADD CONSTRAINT [PK_propinas_tpv_control] PRIMARY KEY (id);
CREATE UNIQUE INDEX [UK_propinas_tpv_corte] ON dbo.propinas_tpv_control (server_id, sucursal_id, folio_corte, fecha_corte);
GO

-- =================================================
-- Tabla: propinas_tpv_historial
-- Exportado: 2026-06-03T06:46:09.507632
-- =================================================

IF OBJECT_ID('dbo.propinas_tpv_historial', 'U') IS NOT NULL
    DROP TABLE dbo.propinas_tpv_historial;
GO

CREATE TABLE dbo.propinas_tpv_historial (
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
    [observaciones] VARCHAR(500) NULL
);
GO

CREATE INDEX [IX_historial_propina] ON dbo.propinas_tpv_historial (propina_id, fecha);
CREATE INDEX [IX_historial_usuario] ON dbo.propinas_tpv_historial (usuario_id, fecha);
ALTER TABLE dbo.propinas_tpv_historial ADD CONSTRAINT [PK_propinas_tpv_historial] PRIMARY KEY (id);
GO

-- =================================================
-- Tabla: Proveedor_Bancos
-- Exportado: 2026-06-03T06:46:09.711599
-- =================================================

IF OBJECT_ID('dbo.Proveedor_Bancos', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_Bancos;
GO

CREATE TABLE dbo.Proveedor_Bancos (
    [BancoID] SMALLINT NOT NULL,
    [ClaveBanco] VARCHAR(10) NULL,
    [NombreBanco] VARCHAR(100) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Proveedor_Bancos ADD CONSTRAINT [PK_Cat_Bancos] PRIMARY KEY (BancoID);
CREATE UNIQUE INDEX [UQ_Cat_Bancos_NombreBanco] ON dbo.Proveedor_Bancos (NombreBanco);
GO

-- =================================================
-- Tabla: Proveedor_Catalogo
-- Exportado: 2026-06-03T06:46:09.916105
-- =================================================

IF OBJECT_ID('dbo.Proveedor_Catalogo', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_Catalogo;
GO

CREATE TABLE dbo.Proveedor_Catalogo (
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
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.Proveedor_Catalogo ADD CONSTRAINT [PK_Cat_Proveedores] PRIMARY KEY (ProveedorID);
CREATE UNIQUE INDEX [UQ_Cat_Proveedores_CodigoProveedor] ON dbo.Proveedor_Catalogo (CodigoProveedor);
CREATE UNIQUE INDEX [UQ_Cat_Proveedores_RFC] ON dbo.Proveedor_Catalogo (RFC);
GO

-- =================================================
-- Tabla: Proveedor_Categorias
-- Exportado: 2026-06-03T06:46:10.152130
-- =================================================

IF OBJECT_ID('dbo.Proveedor_Categorias', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_Categorias;
GO

CREATE TABLE dbo.Proveedor_Categorias (
    [ProveedorCategoriaID] BIGINT NOT NULL,
    [ProveedorID] INT NOT NULL,
    [CategoriaProveedorID] INT NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

CREATE INDEX [IX_Proveedor_Categorias_ProveedorID] ON dbo.Proveedor_Categorias (ProveedorID);
ALTER TABLE dbo.Proveedor_Categorias ADD CONSTRAINT [PK_Proveedor_Categorias] PRIMARY KEY (ProveedorCategoriaID);
CREATE UNIQUE INDEX [UQ_Proveedor_Categorias] ON dbo.Proveedor_Categorias (ProveedorID, CategoriaProveedorID);
GO

-- =================================================
-- Tabla: Proveedor_CategoriasCatalogo
-- Exportado: 2026-06-03T06:46:10.356575
-- =================================================

IF OBJECT_ID('dbo.Proveedor_CategoriasCatalogo', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_CategoriasCatalogo;
GO

CREATE TABLE dbo.Proveedor_CategoriasCatalogo (
    [CategoriaProveedorID] INT NOT NULL,
    [NombreCategoria] VARCHAR(100) NOT NULL,
    [CategoriaPadreID] INT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Proveedor_CategoriasCatalogo ADD CONSTRAINT [PK_Cat_CategoriasProveedor] PRIMARY KEY (CategoriaProveedorID);
CREATE UNIQUE INDEX [UQ_Cat_CategoriasProveedor_Nombre] ON dbo.Proveedor_CategoriasCatalogo (NombreCategoria);
GO

-- =================================================
-- Tabla: Proveedor_Contactos
-- Exportado: 2026-06-03T06:46:10.560804
-- =================================================

IF OBJECT_ID('dbo.Proveedor_Contactos', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_Contactos;
GO

CREATE TABLE dbo.Proveedor_Contactos (
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
    [FechaModificacion] DATETIME2 NULL
);
GO

CREATE INDEX [IX_Proveedor_Contactos_ProveedorID] ON dbo.Proveedor_Contactos (ProveedorID);
CREATE INDEX [IX_Proveedor_Contactos_ProveedorID_Activo] ON dbo.Proveedor_Contactos (ProveedorID, Activo);
ALTER TABLE dbo.Proveedor_Contactos ADD CONSTRAINT [PK_Proveedor_Contactos] PRIMARY KEY (ContactoID);
GO

-- =================================================
-- Tabla: Proveedor_CuentasBancarias
-- Exportado: 2026-06-03T06:46:10.767419
-- =================================================

IF OBJECT_ID('dbo.Proveedor_CuentasBancarias', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_CuentasBancarias;
GO

CREATE TABLE dbo.Proveedor_CuentasBancarias (
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
    [Observaciones] VARCHAR(500) NULL
);
GO

CREATE INDEX [IX_Proveedor_CuentasBancarias_CLABE] ON dbo.Proveedor_CuentasBancarias (CLABE);
CREATE INDEX [IX_Proveedor_CuentasBancarias_ProveedorID] ON dbo.Proveedor_CuentasBancarias (ProveedorID);
CREATE INDEX [IX_Proveedor_CuentasBancarias_ProveedorID_Activa] ON dbo.Proveedor_CuentasBancarias (ProveedorID, Activa);
ALTER TABLE dbo.Proveedor_CuentasBancarias ADD CONSTRAINT [PK_Proveedor_CuentasBancarias] PRIMARY KEY (CuentaBancariaID);
GO

-- =================================================
-- Tabla: Proveedor_Documentos
-- Exportado: 2026-06-03T06:46:10.971471
-- =================================================

IF OBJECT_ID('dbo.Proveedor_Documentos', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_Documentos;
GO

CREATE TABLE dbo.Proveedor_Documentos (
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
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

CREATE INDEX [IX_Proveedor_Documentos_ProveedorID] ON dbo.Proveedor_Documentos (ProveedorID);
CREATE INDEX [IX_Proveedor_Documentos_ProveedorID_TipoDocumentoID] ON dbo.Proveedor_Documentos (ProveedorID, TipoDocumentoID);
CREATE INDEX [IX_Proveedor_Documentos_ProveedorID_Vigente] ON dbo.Proveedor_Documentos (ProveedorID, Vigente);
ALTER TABLE dbo.Proveedor_Documentos ADD CONSTRAINT [PK_Proveedor_Documentos] PRIMARY KEY (DocumentoID);
GO

-- =================================================
-- Tabla: Proveedor_EstatusProveedor
-- Exportado: 2026-06-03T06:46:11.176797
-- =================================================

IF OBJECT_ID('dbo.Proveedor_EstatusProveedor', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_EstatusProveedor;
GO

CREATE TABLE dbo.Proveedor_EstatusProveedor (
    [EstatusProveedorID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Proveedor_EstatusProveedor ADD CONSTRAINT [PK_Cat_EstatusProveedor] PRIMARY KEY (EstatusProveedorID);
CREATE UNIQUE INDEX [UQ_Cat_EstatusProveedor_Descripcion] ON dbo.Proveedor_EstatusProveedor (Descripcion);
GO

-- =================================================
-- Tabla: Proveedor_EstatusSAT
-- Exportado: 2026-06-03T06:46:11.413932
-- =================================================

IF OBJECT_ID('dbo.Proveedor_EstatusSAT', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_EstatusSAT;
GO

CREATE TABLE dbo.Proveedor_EstatusSAT (
    [EstatusSATID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Proveedor_EstatusSAT ADD CONSTRAINT [PK_Cat_EstatusSAT] PRIMARY KEY (EstatusSATID);
CREATE UNIQUE INDEX [UQ_Cat_EstatusSAT_Descripcion] ON dbo.Proveedor_EstatusSAT (Descripcion);
GO

-- =================================================
-- Tabla: Proveedor_EstatusSincronizacion
-- Exportado: 2026-06-03T06:46:11.650731
-- =================================================

IF OBJECT_ID('dbo.Proveedor_EstatusSincronizacion', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_EstatusSincronizacion;
GO

CREATE TABLE dbo.Proveedor_EstatusSincronizacion (
    [EstatusSincronizacionID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Proveedor_EstatusSincronizacion ADD CONSTRAINT [PK_Cat_EstatusSincronizacion] PRIMARY KEY (EstatusSincronizacionID);
CREATE UNIQUE INDEX [UQ_Cat_EstatusSincronizacion_Descripcion] ON dbo.Proveedor_EstatusSincronizacion (Descripcion);
GO

-- =================================================
-- Tabla: Proveedor_Evaluaciones
-- Exportado: 2026-06-03T06:46:11.888139
-- =================================================

IF OBJECT_ID('dbo.Proveedor_Evaluaciones', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_Evaluaciones;
GO

CREATE TABLE dbo.Proveedor_Evaluaciones (
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
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

CREATE INDEX [IX_Proveedor_Evaluaciones_ProveedorID] ON dbo.Proveedor_Evaluaciones (ProveedorID);
CREATE INDEX [IX_Proveedor_Evaluaciones_ProveedorID_Periodo] ON dbo.Proveedor_Evaluaciones (ProveedorID, Periodo);
ALTER TABLE dbo.Proveedor_Evaluaciones ADD CONSTRAINT [PK_Proveedor_Evaluaciones] PRIMARY KEY (EvaluacionID);
CREATE UNIQUE INDEX [UQ_Proveedor_Evaluaciones_Proveedor_Periodo] ON dbo.Proveedor_Evaluaciones (ProveedorID, Periodo);
GO

-- =================================================
-- Tabla: Proveedor_Integracion
-- Exportado: 2026-06-03T06:46:12.094379
-- =================================================

IF OBJECT_ID('dbo.Proveedor_Integracion', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_Integracion;
GO

CREATE TABLE dbo.Proveedor_Integracion (
    [IntegracionID] BIGINT NOT NULL,
    [ProveedorID] INT NOT NULL,
    [SistemaID] TINYINT NOT NULL,
    [ClaveExterna] VARCHAR(50) NOT NULL,
    [UltimaSincronizacion] DATETIME2 NULL,
    [EstatusSincronizacionID] TINYINT NOT NULL,
    [MensajeError] VARCHAR(1000) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

CREATE INDEX [IX_Proveedor_Integracion_ProveedorID] ON dbo.Proveedor_Integracion (ProveedorID);
ALTER TABLE dbo.Proveedor_Integracion ADD CONSTRAINT [PK_Proveedor_Integracion] PRIMARY KEY (IntegracionID);
CREATE UNIQUE INDEX [UQ_Proveedor_Integracion] ON dbo.Proveedor_Integracion (SistemaID, ClaveExterna);
GO

-- =================================================
-- Tabla: Proveedor_Monedas
-- Exportado: 2026-06-03T06:46:12.297843
-- =================================================

IF OBJECT_ID('dbo.Proveedor_Monedas', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_Monedas;
GO

CREATE TABLE dbo.Proveedor_Monedas (
    [MonedaID] SMALLINT NOT NULL,
    [ClaveMoneda] VARCHAR(10) NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Simbolo] VARCHAR(10) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Proveedor_Monedas ADD CONSTRAINT [PK_Cat_Monedas] PRIMARY KEY (MonedaID);
CREATE UNIQUE INDEX [UQ_Cat_Monedas_ClaveMoneda] ON dbo.Proveedor_Monedas (ClaveMoneda);
GO

-- =================================================
-- Tabla: Proveedor_RegimenFiscal
-- Exportado: 2026-06-03T06:46:12.532974
-- =================================================

IF OBJECT_ID('dbo.Proveedor_RegimenFiscal', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_RegimenFiscal;
GO

CREATE TABLE dbo.Proveedor_RegimenFiscal (
    [RegimenFiscalID] SMALLINT NOT NULL,
    [ClaveSAT] VARCHAR(10) NULL,
    [Descripcion] VARCHAR(150) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Proveedor_RegimenFiscal ADD CONSTRAINT [PK_Cat_RegimenFiscal] PRIMARY KEY (RegimenFiscalID);
GO

-- =================================================
-- Tabla: Proveedor_RiesgoProveedor
-- Exportado: 2026-06-03T06:46:12.736684
-- =================================================

IF OBJECT_ID('dbo.Proveedor_RiesgoProveedor', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_RiesgoProveedor;
GO

CREATE TABLE dbo.Proveedor_RiesgoProveedor (
    [RiesgoID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Proveedor_RiesgoProveedor ADD CONSTRAINT [PK_Cat_RiesgoProveedor] PRIMARY KEY (RiesgoID);
CREATE UNIQUE INDEX [UQ_Cat_RiesgoProveedor_Descripcion] ON dbo.Proveedor_RiesgoProveedor (Descripcion);
GO

-- =================================================
-- Tabla: Proveedor_RolUsuarioPortal
-- Exportado: 2026-06-03T06:46:12.973837
-- =================================================

IF OBJECT_ID('dbo.Proveedor_RolUsuarioPortal', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_RolUsuarioPortal;
GO

CREATE TABLE dbo.Proveedor_RolUsuarioPortal (
    [RolPortalID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Proveedor_RolUsuarioPortal ADD CONSTRAINT [PK_Cat_RolUsuarioPortalProveedor] PRIMARY KEY (RolPortalID);
CREATE UNIQUE INDEX [UQ_Cat_RolUsuarioPortalProveedor_Descripcion] ON dbo.Proveedor_RolUsuarioPortal (Descripcion);
GO

-- =================================================
-- Tabla: Proveedor_SistemasIntegracion
-- Exportado: 2026-06-03T06:46:13.209854
-- =================================================

IF OBJECT_ID('dbo.Proveedor_SistemasIntegracion', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_SistemasIntegracion;
GO

CREATE TABLE dbo.Proveedor_SistemasIntegracion (
    [SistemaID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Proveedor_SistemasIntegracion ADD CONSTRAINT [PK_Cat_SistemasIntegracion] PRIMARY KEY (SistemaID);
CREATE UNIQUE INDEX [UQ_Cat_SistemasIntegracion_Descripcion] ON dbo.Proveedor_SistemasIntegracion (Descripcion);
GO

-- =================================================
-- Tabla: Proveedor_TipoContacto
-- Exportado: 2026-06-03T06:46:13.445403
-- =================================================

IF OBJECT_ID('dbo.Proveedor_TipoContacto', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_TipoContacto;
GO

CREATE TABLE dbo.Proveedor_TipoContacto (
    [TipoContactoID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Proveedor_TipoContacto ADD CONSTRAINT [PK_Cat_TipoContacto] PRIMARY KEY (TipoContactoID);
CREATE UNIQUE INDEX [UQ_Cat_TipoContacto_Descripcion] ON dbo.Proveedor_TipoContacto (Descripcion);
GO

-- =================================================
-- Tabla: Proveedor_TipoDocumento
-- Exportado: 2026-06-03T06:46:13.680258
-- =================================================

IF OBJECT_ID('dbo.Proveedor_TipoDocumento', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_TipoDocumento;
GO

CREATE TABLE dbo.Proveedor_TipoDocumento (
    [TipoDocumentoID] SMALLINT NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [RequiereVigencia] BIT NOT NULL DEFAULT ((0)),
    [EsObligatorio] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Proveedor_TipoDocumento ADD CONSTRAINT [PK_Cat_TipoDocumentoProveedor] PRIMARY KEY (TipoDocumentoID);
CREATE UNIQUE INDEX [UQ_Cat_TipoDocumentoProveedor_Descripcion] ON dbo.Proveedor_TipoDocumento (Descripcion);
GO

-- =================================================
-- Tabla: Proveedor_TipoProveedor
-- Exportado: 2026-06-03T06:46:13.915256
-- =================================================

IF OBJECT_ID('dbo.Proveedor_TipoProveedor', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_TipoProveedor;
GO

CREATE TABLE dbo.Proveedor_TipoProveedor (
    [TipoProveedorID] SMALLINT NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Proveedor_TipoProveedor ADD CONSTRAINT [PK_Cat_TipoProveedor] PRIMARY KEY (TipoProveedorID);
CREATE UNIQUE INDEX [UQ_Cat_TipoProveedor_Descripcion] ON dbo.Proveedor_TipoProveedor (Descripcion);
GO

-- =================================================
-- Tabla: Proveedor_UsuariosPortal
-- Exportado: 2026-06-03T06:46:14.152239
-- =================================================

IF OBJECT_ID('dbo.Proveedor_UsuariosPortal', 'U') IS NOT NULL
    DROP TABLE dbo.Proveedor_UsuariosPortal;
GO

CREATE TABLE dbo.Proveedor_UsuariosPortal (
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
    [FechaModificacion] DATETIME2 NULL
);
GO

CREATE INDEX [IX_Proveedor_UsuariosPortal_Email] ON dbo.Proveedor_UsuariosPortal (Email);
CREATE INDEX [IX_Proveedor_UsuariosPortal_ProveedorID] ON dbo.Proveedor_UsuariosPortal (ProveedorID);
ALTER TABLE dbo.Proveedor_UsuariosPortal ADD CONSTRAINT [PK_Proveedor_UsuariosPortal] PRIMARY KEY (UsuarioPortalID);
CREATE UNIQUE INDEX [UQ_Proveedor_UsuariosPortal_Email] ON dbo.Proveedor_UsuariosPortal (Email);
GO

-- =================================================
-- Tabla: RH_Auditoria_Fiscal
-- Exportado: 2026-06-03T06:46:14.359784
-- =================================================

IF OBJECT_ID('dbo.RH_Auditoria_Fiscal', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Auditoria_Fiscal;
GO

CREATE TABLE dbo.RH_Auditoria_Fiscal (
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
    [Observaciones] VARCHAR(500) NULL
);
GO

ALTER TABLE dbo.RH_Auditoria_Fiscal ADD CONSTRAINT [PK__RH_Audit__095694E362023797] PRIMARY KEY (AuditoriaID);
GO

-- =================================================
-- Tabla: RH_Ausencias
-- Exportado: 2026-06-03T06:46:14.564067
-- =================================================

IF OBJECT_ID('dbo.RH_Ausencias', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Ausencias;
GO

CREATE TABLE dbo.RH_Ausencias (
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
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

CREATE INDEX [IX_RH_Ausencias_Colaborador_Fechas] ON dbo.RH_Ausencias (ColaboradorID, FechaInicio, FechaFin);
ALTER TABLE dbo.RH_Ausencias ADD CONSTRAINT [PK__RH_Ausen__8FEC340651A45616] PRIMARY KEY (AusenciaID);
GO

-- =================================================
-- Tabla: RH_Calendario_Laboral
-- Exportado: 2026-06-03T06:46:14.770473
-- =================================================

IF OBJECT_ID('dbo.RH_Calendario_Laboral', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Calendario_Laboral;
GO

CREATE TABLE dbo.RH_Calendario_Laboral (
    [CalendarioLaboralID] INT NOT NULL,
    [SucursalID] INT NULL,
    [SucursalFiscalID] INT NULL,
    [Fecha] DATE NOT NULL,
    [EsDiaDescanso] BIT NOT NULL DEFAULT ((0)),
    [EsFestivo] BIT NOT NULL DEFAULT ((0)),
    [Descripcion] VARCHAR(150) NULL
);
GO

ALTER TABLE dbo.RH_Calendario_Laboral ADD CONSTRAINT [PK__RH_Calen__5B92CA621659B2B6] PRIMARY KEY (CalendarioLaboralID);
GO

-- =================================================
-- Tabla: RH_Cat_Areas
-- Exportado: 2026-06-03T06:46:14.975104
-- =================================================

IF OBJECT_ID('dbo.RH_Cat_Areas', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Cat_Areas;
GO

CREATE TABLE dbo.RH_Cat_Areas (
    [AreaID] INT NOT NULL,
    [DepartamentoID] INT NOT NULL,
    [CodigoArea] VARCHAR(20) NOT NULL,
    [NombreArea] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.RH_Cat_Areas ADD CONSTRAINT [PK__RH_Cat_A__70B820281F5AEBA9] PRIMARY KEY (AreaID);
CREATE UNIQUE INDEX [UQ_RH_Cat_Areas_DepCodigo] ON dbo.RH_Cat_Areas (DepartamentoID, CodigoArea);
CREATE UNIQUE INDEX [UQ_RH_Cat_Areas_DepNombre] ON dbo.RH_Cat_Areas (DepartamentoID, NombreArea);
GO

-- =================================================
-- Tabla: RH_Cat_Beneficios
-- Exportado: 2026-06-03T06:46:15.179887
-- =================================================

IF OBJECT_ID('dbo.RH_Cat_Beneficios', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Cat_Beneficios;
GO

CREATE TABLE dbo.RH_Cat_Beneficios (
    [BeneficioID] INT NOT NULL,
    [CodigoBeneficio] VARCHAR(20) NOT NULL,
    [NombreBeneficio] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [MontoDefault] DECIMAL(18,2) NULL,
    [PorcentajeDefault] DECIMAL(9,4) NULL,
    [IntegraSBC] BIT NOT NULL DEFAULT ((0)),
    [GravadoISR] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.RH_Cat_Beneficios ADD CONSTRAINT [PK__RH_Cat_B__A02B32D152A13A4E] PRIMARY KEY (BeneficioID);
CREATE UNIQUE INDEX [UQ_RH_Cat_Beneficios_Codigo] ON dbo.RH_Cat_Beneficios (CodigoBeneficio);
CREATE UNIQUE INDEX [UQ_RH_Cat_Beneficios_Nombre] ON dbo.RH_Cat_Beneficios (NombreBeneficio);
GO

-- =================================================
-- Tabla: RH_Cat_ConceptosNomina
-- Exportado: 2026-06-03T06:46:15.383897
-- =================================================

IF OBJECT_ID('dbo.RH_Cat_ConceptosNomina', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Cat_ConceptosNomina;
GO

CREATE TABLE dbo.RH_Cat_ConceptosNomina (
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
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.RH_Cat_ConceptosNomina ADD CONSTRAINT [PK__RH_Cat_C__BB1C27609E26A73F] PRIMARY KEY (ConceptoNominaID);
CREATE UNIQUE INDEX [UQ_RH_Cat_ConceptosNomina_Codigo] ON dbo.RH_Cat_ConceptosNomina (CodigoConcepto);
CREATE UNIQUE INDEX [UQ_RH_Cat_ConceptosNomina_Nombre] ON dbo.RH_Cat_ConceptosNomina (NombreConcepto);
GO

-- =================================================
-- Tabla: RH_Cat_Departamentos
-- Exportado: 2026-06-03T06:46:15.620121
-- =================================================

IF OBJECT_ID('dbo.RH_Cat_Departamentos', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Cat_Departamentos;
GO

CREATE TABLE dbo.RH_Cat_Departamentos (
    [DepartamentoID] INT NOT NULL,
    [CodigoDepartamento] VARCHAR(20) NOT NULL,
    [NombreDepartamento] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.RH_Cat_Departamentos ADD CONSTRAINT [PK__RH_Cat_D__66BB0E1E9FA7CE57] PRIMARY KEY (DepartamentoID);
CREATE UNIQUE INDEX [UQ_RH_Cat_Departamentos_Codigo] ON dbo.RH_Cat_Departamentos (CodigoDepartamento);
CREATE UNIQUE INDEX [UQ_RH_Cat_Departamentos_Nombre] ON dbo.RH_Cat_Departamentos (NombreDepartamento);
GO

-- =================================================
-- Tabla: RH_Cat_EstatusPeriodoNomina
-- Exportado: 2026-06-03T06:46:15.855675
-- =================================================

IF OBJECT_ID('dbo.RH_Cat_EstatusPeriodoNomina', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Cat_EstatusPeriodoNomina;
GO

CREATE TABLE dbo.RH_Cat_EstatusPeriodoNomina (
    [EstatusPeriodoNominaID] SMALLINT NOT NULL,
    [CodigoEstatus] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [OrdenFlujo] SMALLINT NOT NULL,
    [EsFinal] BIT NOT NULL DEFAULT ((0))
);
GO

ALTER TABLE dbo.RH_Cat_EstatusPeriodoNomina ADD CONSTRAINT [PK__RH_Cat_E__C4A5982C30C38062] PRIMARY KEY (EstatusPeriodoNominaID);
CREATE UNIQUE INDEX [UQ_RH_Cat_EstatusPeriodoNomina_Codigo] ON dbo.RH_Cat_EstatusPeriodoNomina (CodigoEstatus);
CREATE UNIQUE INDEX [UQ_RH_Cat_EstatusPeriodoNomina_Descripcion] ON dbo.RH_Cat_EstatusPeriodoNomina (Descripcion);
GO

-- =================================================
-- Tabla: RH_Cat_Jornadas
-- Exportado: 2026-06-03T06:46:16.093466
-- =================================================

IF OBJECT_ID('dbo.RH_Cat_Jornadas', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Cat_Jornadas;
GO

CREATE TABLE dbo.RH_Cat_Jornadas (
    [JornadaID] SMALLINT NOT NULL,
    [CodigoJornada] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [HorasDiarias] DECIMAL(5,2) NULL,
    [HorasSemanales] DECIMAL(5,2) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.RH_Cat_Jornadas ADD CONSTRAINT [PK__RH_Cat_J__28E6A6BD26AD3715] PRIMARY KEY (JornadaID);
CREATE UNIQUE INDEX [UQ_RH_Cat_Jornadas_Codigo] ON dbo.RH_Cat_Jornadas (CodigoJornada);
CREATE UNIQUE INDEX [UQ_RH_Cat_Jornadas_Descripcion] ON dbo.RH_Cat_Jornadas (Descripcion);
GO

-- =================================================
-- Tabla: RH_Cat_MotivosBaja
-- Exportado: 2026-06-03T06:46:16.297004
-- =================================================

IF OBJECT_ID('dbo.RH_Cat_MotivosBaja', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Cat_MotivosBaja;
GO

CREATE TABLE dbo.RH_Cat_MotivosBaja (
    [MotivoBajaID] SMALLINT NOT NULL,
    [CodigoMotivoBaja] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(150) NOT NULL,
    [RequiereFiniquito] BIT NOT NULL DEFAULT ((1)),
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.RH_Cat_MotivosBaja ADD CONSTRAINT [PK__RH_Cat_M__DCCA224E4AB37626] PRIMARY KEY (MotivoBajaID);
CREATE UNIQUE INDEX [UQ_RH_Cat_MotivosBaja_Codigo] ON dbo.RH_Cat_MotivosBaja (CodigoMotivoBaja);
CREATE UNIQUE INDEX [UQ_RH_Cat_MotivosBaja_Descripcion] ON dbo.RH_Cat_MotivosBaja (Descripcion);
GO

-- =================================================
-- Tabla: RH_Cat_Puestos
-- Exportado: 2026-06-03T06:46:16.532583
-- =================================================

IF OBJECT_ID('dbo.RH_Cat_Puestos', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Cat_Puestos;
GO

CREATE TABLE dbo.RH_Cat_Puestos (
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
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.RH_Cat_Puestos ADD CONSTRAINT [PK__Cat_Pues__F7F6C62469D9723E] PRIMARY KEY (PuestoID);
GO

-- =================================================
-- Tabla: RH_Cat_RegimenContratacion
-- Exportado: 2026-06-03T06:46:16.768410
-- =================================================

IF OBJECT_ID('dbo.RH_Cat_RegimenContratacion', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Cat_RegimenContratacion;
GO

CREATE TABLE dbo.RH_Cat_RegimenContratacion (
    [RegimenContratacionID] SMALLINT NOT NULL,
    [ClaveSAT] VARCHAR(10) NOT NULL,
    [Descripcion] VARCHAR(150) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.RH_Cat_RegimenContratacion ADD CONSTRAINT [PK__RH_Cat_R__66B7571198FFE082] PRIMARY KEY (RegimenContratacionID);
CREATE UNIQUE INDEX [UQ_RH_Cat_RegimenContratacion_ClaveSAT] ON dbo.RH_Cat_RegimenContratacion (ClaveSAT);
CREATE UNIQUE INDEX [UQ_RH_Cat_RegimenContratacion_Descripcion] ON dbo.RH_Cat_RegimenContratacion (Descripcion);
GO

-- =================================================
-- Tabla: RH_Cat_Sucursales
-- Exportado: 2026-06-03T06:46:16.972719
-- =================================================

IF OBJECT_ID('dbo.RH_Cat_Sucursales', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Cat_Sucursales;
GO

CREATE TABLE dbo.RH_Cat_Sucursales (
    [SucursalID] INT NOT NULL,
    [Nombre_Sucursal] VARCHAR(100) NOT NULL,
    [Ciudad] VARCHAR(50) NULL,
    [Activa] BIT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.RH_Cat_Sucursales ADD CONSTRAINT [PK__Cat_Sucu__6CB482811DD98547] PRIMARY KEY (SucursalID);
GO

-- =================================================
-- Tabla: RH_Cat_SucursalesFiscal
-- Exportado: 2026-06-03T06:46:17.208328
-- =================================================

IF OBJECT_ID('dbo.RH_Cat_SucursalesFiscal', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Cat_SucursalesFiscal;
GO

CREATE TABLE dbo.RH_Cat_SucursalesFiscal (
    [SucursalFiscalID] INT NOT NULL,
    [SucursalID] INT NOT NULL,
    [EmpresaID] INT NULL,
    [RFC] VARCHAR(13) NOT NULL,
    [RazonSocial] VARCHAR(200) NOT NULL,
    [RegimenFiscal] VARCHAR(10) NULL,
    [CodigoPostalFiscal] VARCHAR(10) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.RH_Cat_SucursalesFiscal ADD CONSTRAINT [PK_RH_Cat_SucursalesFiscal] PRIMARY KEY (SucursalFiscalID);
CREATE UNIQUE INDEX [UQ_RH_Cat_SucursalesFiscal_Sucursal_RFC] ON dbo.RH_Cat_SucursalesFiscal (SucursalID, RFC);
GO

-- =================================================
-- Tabla: RH_Cat_TiposAusencia
-- Exportado: 2026-06-03T06:46:17.411542
-- =================================================

IF OBJECT_ID('dbo.RH_Cat_TiposAusencia', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Cat_TiposAusencia;
GO

CREATE TABLE dbo.RH_Cat_TiposAusencia (
    [TipoAusenciaID] SMALLINT NOT NULL,
    [CodigoTipoAusencia] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [GoceSueldo] BIT NOT NULL DEFAULT ((0)),
    [AfectaNomina] BIT NOT NULL DEFAULT ((1)),
    [AfectaAsistencia] BIT NOT NULL DEFAULT ((1)),
    [ClaveSAT] VARCHAR(20) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.RH_Cat_TiposAusencia ADD CONSTRAINT [PK__RH_Cat_T__0D6E7F25936B8EC8] PRIMARY KEY (TipoAusenciaID);
CREATE UNIQUE INDEX [UQ_RH_Cat_TiposAusencia_Codigo] ON dbo.RH_Cat_TiposAusencia (CodigoTipoAusencia);
CREATE UNIQUE INDEX [UQ_RH_Cat_TiposAusencia_Descripcion] ON dbo.RH_Cat_TiposAusencia (Descripcion);
GO

-- =================================================
-- Tabla: RH_Cat_TiposConceptoNomina
-- Exportado: 2026-06-03T06:46:17.649727
-- =================================================

IF OBJECT_ID('dbo.RH_Cat_TiposConceptoNomina', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Cat_TiposConceptoNomina;
GO

CREATE TABLE dbo.RH_Cat_TiposConceptoNomina (
    [TipoConceptoNominaID] SMALLINT NOT NULL,
    [CodigoTipoConcepto] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [Naturaleza] CHAR(1) NOT NULL
);
GO

ALTER TABLE dbo.RH_Cat_TiposConceptoNomina ADD CONSTRAINT [PK__RH_Cat_T__A26D0E4D2EE58FAF] PRIMARY KEY (TipoConceptoNominaID);
CREATE UNIQUE INDEX [UQ_RH_Cat_TiposConceptoNomina_Codigo] ON dbo.RH_Cat_TiposConceptoNomina (CodigoTipoConcepto);
CREATE UNIQUE INDEX [UQ_RH_Cat_TiposConceptoNomina_Descripcion] ON dbo.RH_Cat_TiposConceptoNomina (Descripcion);
GO

-- =================================================
-- Tabla: RH_Cat_TiposContrato
-- Exportado: 2026-06-03T06:46:17.888184
-- =================================================

IF OBJECT_ID('dbo.RH_Cat_TiposContrato', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Cat_TiposContrato;
GO

CREATE TABLE dbo.RH_Cat_TiposContrato (
    [TipoContratoID] SMALLINT NOT NULL,
    [CodigoTipoContrato] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [EsIndeterminado] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.RH_Cat_TiposContrato ADD CONSTRAINT [PK__RH_Cat_T__3E0E57A771CB1BDA] PRIMARY KEY (TipoContratoID);
CREATE UNIQUE INDEX [UQ_RH_Cat_TiposContrato_Codigo] ON dbo.RH_Cat_TiposContrato (CodigoTipoContrato);
CREATE UNIQUE INDEX [UQ_RH_Cat_TiposContrato_Descripcion] ON dbo.RH_Cat_TiposContrato (Descripcion);
GO

-- =================================================
-- Tabla: RH_Cat_TiposPeriodoNomina
-- Exportado: 2026-06-03T06:46:18.126585
-- =================================================

IF OBJECT_ID('dbo.RH_Cat_TiposPeriodoNomina', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Cat_TiposPeriodoNomina;
GO

CREATE TABLE dbo.RH_Cat_TiposPeriodoNomina (
    [TipoPeriodoNominaID] SMALLINT NOT NULL,
    [CodigoTipoPeriodo] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [DiasPeriodo] SMALLINT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.RH_Cat_TiposPeriodoNomina ADD CONSTRAINT [PK__RH_Cat_T__3030D06C8C6E262A] PRIMARY KEY (TipoPeriodoNominaID);
CREATE UNIQUE INDEX [UQ_RH_Cat_TiposPeriodoNomina_Codigo] ON dbo.RH_Cat_TiposPeriodoNomina (CodigoTipoPeriodo);
CREATE UNIQUE INDEX [UQ_RH_Cat_TiposPeriodoNomina_Descripcion] ON dbo.RH_Cat_TiposPeriodoNomina (Descripcion);
GO

-- =================================================
-- Tabla: RH_Cat_Turnos
-- Exportado: 2026-06-03T06:46:18.363586
-- =================================================

IF OBJECT_ID('dbo.RH_Cat_Turnos', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Cat_Turnos;
GO

CREATE TABLE dbo.RH_Cat_Turnos (
    [TurnoID] SMALLINT NOT NULL,
    [CodigoTurno] VARCHAR(20) NOT NULL,
    [NombreTurno] VARCHAR(100) NOT NULL,
    [HoraEntradaProgramada] TIME NULL,
    [HoraSalidaProgramada] TIME NULL,
    [TolEntradaMin] SMALLINT NOT NULL DEFAULT ((0)),
    [TolSalidaMin] SMALLINT NOT NULL DEFAULT ((0)),
    [CruzaMedianoche] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.RH_Cat_Turnos ADD CONSTRAINT [PK__RH_Cat_T__AD3E2EB4B41DADED] PRIMARY KEY (TurnoID);
CREATE UNIQUE INDEX [UQ_RH_Cat_Turnos_Codigo] ON dbo.RH_Cat_Turnos (CodigoTurno);
CREATE UNIQUE INDEX [UQ_RH_Cat_Turnos_Nombre] ON dbo.RH_Cat_Turnos (NombreTurno);
GO

-- =================================================
-- Tabla: RH_Colaboradores_Beneficios
-- Exportado: 2026-06-03T06:46:18.568493
-- =================================================

IF OBJECT_ID('dbo.RH_Colaboradores_Beneficios', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Colaboradores_Beneficios;
GO

CREATE TABLE dbo.RH_Colaboradores_Beneficios (
    [ColaboradorBeneficioID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [BeneficioID] INT NOT NULL,
    [FechaInicio] DATE NOT NULL,
    [FechaFin] DATE NULL,
    [Monto] DECIMAL(18,2) NULL,
    [Porcentaje] DECIMAL(9,4) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [Observaciones] VARCHAR(250) NULL
);
GO

ALTER TABLE dbo.RH_Colaboradores_Beneficios ADD CONSTRAINT [PK__RH_Colab__9629FAFFE0C48C11] PRIMARY KEY (ColaboradorBeneficioID);
GO

-- =================================================
-- Tabla: RH_Colaboradores_ContactosEmergencia
-- Exportado: 2026-06-03T06:46:18.774384
-- =================================================

IF OBJECT_ID('dbo.RH_Colaboradores_ContactosEmergencia', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Colaboradores_ContactosEmergencia;
GO

CREATE TABLE dbo.RH_Colaboradores_ContactosEmergencia (
    [ContactoEmergenciaID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [NombreContacto] VARCHAR(150) NOT NULL,
    [Parentesco] VARCHAR(50) NULL,
    [Telefono] VARCHAR(25) NULL,
    [TelefonoAlterno] VARCHAR(25) NULL,
    [Observaciones] VARCHAR(250) NULL,
    [EsPrincipal] BIT NOT NULL DEFAULT ((0))
);
GO

ALTER TABLE dbo.RH_Colaboradores_ContactosEmergencia ADD CONSTRAINT [PK__RH_Colab__9FF0768C041D4486] PRIMARY KEY (ContactoEmergenciaID);
GO

-- =================================================
-- Tabla: RH_Colaboradores_Dependientes
-- Exportado: 2026-06-03T06:46:18.979132
-- =================================================

IF OBJECT_ID('dbo.RH_Colaboradores_Dependientes', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Colaboradores_Dependientes;
GO

CREATE TABLE dbo.RH_Colaboradores_Dependientes (
    [DependienteID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [NombreDependiente] VARCHAR(150) NOT NULL,
    [Parentesco] VARCHAR(50) NULL,
    [FechaNacimiento] DATE NULL,
    [EsBeneficiario] BIT NOT NULL DEFAULT ((0)),
    [PorcentajeBeneficio] DECIMAL(9,4) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.RH_Colaboradores_Dependientes ADD CONSTRAINT [PK__RH_Colab__599965E6AFCFDD57] PRIMARY KEY (DependienteID);
GO

-- =================================================
-- Tabla: RH_Colaboradores_Documentos
-- Exportado: 2026-06-03T06:46:19.188275
-- =================================================

IF OBJECT_ID('dbo.RH_Colaboradores_Documentos', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Colaboradores_Documentos;
GO

CREATE TABLE dbo.RH_Colaboradores_Documentos (
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
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

ALTER TABLE dbo.RH_Colaboradores_Documentos ADD CONSTRAINT [PK__RH_Colab__59380D0852A1A0C7] PRIMARY KEY (DocumentoColaboradorID);
GO

-- =================================================
-- Tabla: RH_Colaboradores_Domicilios
-- Exportado: 2026-06-03T06:46:19.393692
-- =================================================

IF OBJECT_ID('dbo.RH_Colaboradores_Domicilios', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Colaboradores_Domicilios;
GO

CREATE TABLE dbo.RH_Colaboradores_Domicilios (
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
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

ALTER TABLE dbo.RH_Colaboradores_Domicilios ADD CONSTRAINT [PK__RH_Colab__085DF56C835E4BEA] PRIMARY KEY (DomicilioID);
GO

-- =================================================
-- Tabla: RH_Colaboradores_Expediente
-- Exportado: 2026-06-03T06:46:19.598385
-- =================================================

IF OBJECT_ID('dbo.RH_Colaboradores_Expediente', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Colaboradores_Expediente;
GO

CREATE TABLE dbo.RH_Colaboradores_Expediente (
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
    [ObservacionesRH] VARCHAR(500) NULL
);
GO

CREATE UNIQUE INDEX [IX_CURP_Unique_NotNull] ON dbo.RH_Colaboradores_Expediente (CURP);
CREATE UNIQUE INDEX [IX_RFC_Unique_NotNull] ON dbo.RH_Colaboradores_Expediente (RFC);
ALTER TABLE dbo.RH_Colaboradores_Expediente ADD CONSTRAINT [PK__RH_Colab__28AA72C1EFB9BD64] PRIMARY KEY (ColaboradorID);
GO

-- =================================================
-- Tabla: RH_Contratos
-- Exportado: 2026-06-03T06:46:19.875834
-- =================================================

IF OBJECT_ID('dbo.RH_Contratos', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Contratos;
GO

CREATE TABLE dbo.RH_Contratos (
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
    [FechaModificacion] DATETIME2 NULL
);
GO

CREATE INDEX [IX_RH_Contratos_Colaborador_Vigente] ON dbo.RH_Contratos (ColaboradorID, EsContratoVigente, FechaInicio);
ALTER TABLE dbo.RH_Contratos ADD CONSTRAINT [PK__RH_Contr__B238E95315587526] PRIMARY KEY (ContratoID);
GO

-- =================================================
-- Tabla: RH_Finiquitos
-- Exportado: 2026-06-03T06:46:20.082606
-- =================================================

IF OBJECT_ID('dbo.RH_Finiquitos', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Finiquitos;
GO

CREATE TABLE dbo.RH_Finiquitos (
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
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

CREATE INDEX [IX_RH_Finiquitos_Colaborador_FechaBaja] ON dbo.RH_Finiquitos (ColaboradorID, FechaBaja);
ALTER TABLE dbo.RH_Finiquitos ADD CONSTRAINT [PK__RH_Finiq__D73767020AABB154] PRIMARY KEY (FiniquitoID);
GO

-- =================================================
-- Tabla: RH_Finiquitos_Detalle
-- Exportado: 2026-06-03T06:46:20.287853
-- =================================================

IF OBJECT_ID('dbo.RH_Finiquitos_Detalle', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Finiquitos_Detalle;
GO

CREATE TABLE dbo.RH_Finiquitos_Detalle (
    [FiniquitoDetalleID] INT NOT NULL,
    [FiniquitoID] INT NOT NULL,
    [ConceptoNominaID] INT NOT NULL,
    [Importe] DECIMAL(18,2) NOT NULL,
    [ImporteGravado] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [ImporteExento] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Observaciones] VARCHAR(300) NULL
);
GO

ALTER TABLE dbo.RH_Finiquitos_Detalle ADD CONSTRAINT [PK__RH_Finiq__2FCD95C344027D13] PRIMARY KEY (FiniquitoDetalleID);
GO

-- =================================================
-- Tabla: RH_Flujo_Nomina_Sucursal
-- Exportado: 2026-06-03T06:46:20.492569
-- =================================================

IF OBJECT_ID('dbo.RH_Flujo_Nomina_Sucursal', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Flujo_Nomina_Sucursal;
GO

CREATE TABLE dbo.RH_Flujo_Nomina_Sucursal (
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
    [PeriodoNominaID] INT NULL
);
GO

ALTER TABLE dbo.RH_Flujo_Nomina_Sucursal ADD CONSTRAINT [PK__RH_Flujo__11E0519E31595679] PRIMARY KEY (FlujoID);
GO

-- =================================================
-- Tabla: RH_GruposNomina
-- Exportado: 2026-06-03T06:46:20.698595
-- =================================================

IF OBJECT_ID('dbo.RH_GruposNomina', 'U') IS NOT NULL
    DROP TABLE dbo.RH_GruposNomina;
GO

CREATE TABLE dbo.RH_GruposNomina (
    [GrupoNominaID] INT NOT NULL,
    [CodigoGrupoNomina] VARCHAR(20) NOT NULL,
    [NombreGrupoNomina] VARCHAR(100) NOT NULL,
    [TipoPeriodoNominaID] SMALLINT NOT NULL,
    [SucursalFiscalID] INT NOT NULL,
    [DiaPago] SMALLINT NULL,
    [DesfaseDiasPago] SMALLINT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.RH_GruposNomina ADD CONSTRAINT [PK__RH_Grupo__21FBC6A5EA371AF6] PRIMARY KEY (GrupoNominaID);
CREATE UNIQUE INDEX [UQ_RH_GruposNomina_Codigo] ON dbo.RH_GruposNomina (CodigoGrupoNomina);
CREATE UNIQUE INDEX [UQ_RH_GruposNomina_Nombre] ON dbo.RH_GruposNomina (NombreGrupoNomina);
GO

-- =================================================
-- Tabla: RH_Historial_Puestos
-- Exportado: 2026-06-03T06:46:20.904403
-- =================================================

IF OBJECT_ID('dbo.RH_Historial_Puestos', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Historial_Puestos;
GO

CREATE TABLE dbo.RH_Historial_Puestos (
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
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

ALTER TABLE dbo.RH_Historial_Puestos ADD CONSTRAINT [PK__RH_Histo__679773EF9C39F3E3] PRIMARY KEY (HistorialPuestoID);
GO

-- =================================================
-- Tabla: RH_Historial_Salarios
-- Exportado: 2026-06-03T06:46:21.110562
-- =================================================

IF OBJECT_ID('dbo.RH_Historial_Salarios', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Historial_Salarios;
GO

CREATE TABLE dbo.RH_Historial_Salarios (
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
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

ALTER TABLE dbo.RH_Historial_Salarios ADD CONSTRAINT [PK__RH_Histo__58016C821D4C9D4D] PRIMARY KEY (HistorialSalarioID);
GO

-- =================================================
-- Tabla: RH_Homologacion_Equivalencias
-- Exportado: 2026-06-03T06:46:21.319280
-- =================================================

IF OBJECT_ID('dbo.RH_Homologacion_Equivalencias', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Homologacion_Equivalencias;
GO

CREATE TABLE dbo.RH_Homologacion_Equivalencias (
    [EquivalenciaID] INT NOT NULL,
    [Tipo] VARCHAR(20) NOT NULL,
    [Valor_Origen] NVARCHAR(200) NOT NULL,
    [Valor_Normalizado] NVARCHAR(200) NULL,
    [CatalogoID] INT NULL,
    [Estado] VARCHAR(20) NULL DEFAULT ('Aprobado'),
    [Usuario_Aprobador] VARCHAR(100) NULL,
    [Fecha_Aprobacion] DATETIME NULL DEFAULT (getdate()),
    [Observaciones] NVARCHAR(500) NULL
);
GO

ALTER TABLE dbo.RH_Homologacion_Equivalencias ADD CONSTRAINT [PK__RH_Homol__B36E363DB75A3F4F] PRIMARY KEY (EquivalenciaID);
CREATE UNIQUE INDEX [UQ_Tipo_ValorOrigen] ON dbo.RH_Homologacion_Equivalencias (Tipo, Valor_Origen);
GO

-- =================================================
-- Tabla: RH_Importacion_Bitacora
-- Exportado: 2026-06-03T06:46:21.557938
-- =================================================

IF OBJECT_ID('dbo.RH_Importacion_Bitacora', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Importacion_Bitacora;
GO

CREATE TABLE dbo.RH_Importacion_Bitacora (
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
    [Detalle_JSON] NVARCHAR(MAX) NULL
);
GO

ALTER TABLE dbo.RH_Importacion_Bitacora ADD CONSTRAINT [PK__RH_Impor__7ACF9B18EA74F89A] PRIMARY KEY (BitacoraID);
GO

-- =================================================
-- Tabla: RH_Importacion_Staging
-- Exportado: 2026-06-03T06:46:21.796712
-- =================================================

IF OBJECT_ID('dbo.RH_Importacion_Staging', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Importacion_Staging;
GO

CREATE TABLE dbo.RH_Importacion_Staging (
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
    [Fecha_Procesamiento] DATETIME NULL
);
GO

CREATE INDEX [IX_Staging_CURP] ON dbo.RH_Importacion_Staging (CURP);
CREATE INDEX [IX_Staging_Estado] ON dbo.RH_Importacion_Staging (Estado);
CREATE INDEX [IX_Staging_Fecha] ON dbo.RH_Importacion_Staging (Fecha_Importacion);
CREATE INDEX [IX_Staging_RFC] ON dbo.RH_Importacion_Staging (RFC);
ALTER TABLE dbo.RH_Importacion_Staging ADD CONSTRAINT [PK__RH_Impor__8C04728068888378] PRIMARY KEY (StagingID);
GO

-- =================================================
-- Tabla: RH_IMSS_Movimientos
-- Exportado: 2026-06-03T06:46:22.171378
-- =================================================

IF OBJECT_ID('dbo.RH_IMSS_Movimientos', 'U') IS NOT NULL
    DROP TABLE dbo.RH_IMSS_Movimientos;
GO

CREATE TABLE dbo.RH_IMSS_Movimientos (
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
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

CREATE INDEX [IX_RH_IMSS_Movimientos_Colaborador_Fecha] ON dbo.RH_IMSS_Movimientos (ColaboradorID, FechaMovimiento);
ALTER TABLE dbo.RH_IMSS_Movimientos ADD CONSTRAINT [PK__RH_IMSS___8D2E9ACA827B1CAF] PRIMARY KEY (MovimientoIMSSID);
GO

-- =================================================
-- Tabla: RH_Incidencias_Nomina
-- Exportado: 2026-06-03T06:46:22.376896
-- =================================================

IF OBJECT_ID('dbo.RH_Incidencias_Nomina', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Incidencias_Nomina;
GO

CREATE TABLE dbo.RH_Incidencias_Nomina (
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
    [FechaAutorizacion] DATETIME2 NULL
);
GO

CREATE INDEX [IX_RH_Incidencias_Nomina_Colaborador_Fecha] ON dbo.RH_Incidencias_Nomina (ColaboradorID, Fecha_Incidencia);
CREATE INDEX [IX_RH_Incidencias_Nomina_Periodo_Autorizado] ON dbo.RH_Incidencias_Nomina (PeriodoNominaID, Autorizado);
ALTER TABLE dbo.RH_Incidencias_Nomina ADD CONSTRAINT [PK__RH_Incid__E41133C6D8C18977] PRIMARY KEY (IncidenciaID);
GO

-- =================================================
-- Tabla: RH_Nomina
-- Exportado: 2026-06-03T06:46:22.584549
-- =================================================

IF OBJECT_ID('dbo.RH_Nomina', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Nomina;
GO

CREATE TABLE dbo.RH_Nomina (
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
    [Observaciones] VARCHAR(500) NULL
);
GO

CREATE INDEX [IX_RH_Nomina_Colaborador] ON dbo.RH_Nomina (ColaboradorID, PeriodoNominaID);
CREATE INDEX [IX_RH_Nomina_Periodo_Estatus] ON dbo.RH_Nomina (PeriodoNominaID, EstatusNomina, Timbrado, Pagado);
ALTER TABLE dbo.RH_Nomina ADD CONSTRAINT [PK__RH_Nomin__33A37672BE57130D] PRIMARY KEY (NominaID);
CREATE UNIQUE INDEX [UQ_RH_Nomina_Periodo_Colaborador] ON dbo.RH_Nomina (PeriodoNominaID, ColaboradorID);
GO

-- =================================================
-- Tabla: RH_Nomina_Detalle
-- Exportado: 2026-06-03T06:46:22.789649
-- =================================================

IF OBJECT_ID('dbo.RH_Nomina_Detalle', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Nomina_Detalle;
GO

CREATE TABLE dbo.RH_Nomina_Detalle (
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
    [Observaciones] VARCHAR(300) NULL
);
GO

CREATE INDEX [IX_RH_Nomina_Detalle_Nomina] ON dbo.RH_Nomina_Detalle (NominaID, ConceptoNominaID);
ALTER TABLE dbo.RH_Nomina_Detalle ADD CONSTRAINT [PK__RH_Nomin__5CD6A45A5DC028C8] PRIMARY KEY (NominaDetalleID);
GO

-- =================================================
-- Tabla: RH_Nomina_Dispersion
-- Exportado: 2026-06-03T06:46:22.994520
-- =================================================

IF OBJECT_ID('dbo.RH_Nomina_Dispersion', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Nomina_Dispersion;
GO

CREATE TABLE dbo.RH_Nomina_Dispersion (
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
    [Observaciones] VARCHAR(500) NULL
);
GO

CREATE INDEX [IX_RH_Nomina_Dispersion_Periodo_Estatus] ON dbo.RH_Nomina_Dispersion (PeriodoNominaID, EstatusDispersion);
ALTER TABLE dbo.RH_Nomina_Dispersion ADD CONSTRAINT [PK__RH_Nomin__8766C7D8985D37BE] PRIMARY KEY (DispersionNominaID);
GO

-- =================================================
-- Tabla: RH_Nomina_Recibos
-- Exportado: 2026-06-03T06:46:23.199854
-- =================================================

IF OBJECT_ID('dbo.RH_Nomina_Recibos', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Nomina_Recibos;
GO

CREATE TABLE dbo.RH_Nomina_Recibos (
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
    [Observaciones] VARCHAR(500) NULL
);
GO

ALTER TABLE dbo.RH_Nomina_Recibos ADD CONSTRAINT [PK__RH_Nomin__12EF8E2534567782] PRIMARY KEY (NominaReciboID);
CREATE UNIQUE INDEX [UQ_RH_Nomina_Recibos_Nomina] ON dbo.RH_Nomina_Recibos (NominaID);
CREATE UNIQUE INDEX [UQ_RH_Nomina_Recibos_UUID] ON dbo.RH_Nomina_Recibos (UUID);
GO

-- =================================================
-- Tabla: RH_Periodos_Nomina
-- Exportado: 2026-06-03T06:46:23.404287
-- =================================================

IF OBJECT_ID('dbo.RH_Periodos_Nomina', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Periodos_Nomina;
GO

CREATE TABLE dbo.RH_Periodos_Nomina (
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
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

CREATE INDEX [IX_RH_Periodos_Nomina_Grupo_Fecha] ON dbo.RH_Periodos_Nomina (GrupoNominaID, FechaInicio, FechaFin, FechaPago);
ALTER TABLE dbo.RH_Periodos_Nomina ADD CONSTRAINT [PK__RH_Perio__D12EA6A604109DE2] PRIMARY KEY (PeriodoNominaID);
CREATE UNIQUE INDEX [UQ_RH_Periodos_Nomina_Grupo_Ejercicio_Periodo] ON dbo.RH_Periodos_Nomina (GrupoNominaID, Ejercicio, NumeroPeriodo, EsAjuste);
GO

-- =================================================
-- Tabla: RH_Prestamos
-- Exportado: 2026-06-03T06:46:23.609622
-- =================================================

IF OBJECT_ID('dbo.RH_Prestamos', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Prestamos;
GO

CREATE TABLE dbo.RH_Prestamos (
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
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

CREATE INDEX [IX_RH_Prestamos_Colaborador_Estatus] ON dbo.RH_Prestamos (ColaboradorID, Estatus);
ALTER TABLE dbo.RH_Prestamos ADD CONSTRAINT [PK__RH_Prest__AA58A080A4DDBC36] PRIMARY KEY (PrestamoID);
GO

-- =================================================
-- Tabla: RH_Prestamos_Detalle
-- Exportado: 2026-06-03T06:46:23.815070
-- =================================================

IF OBJECT_ID('dbo.RH_Prestamos_Detalle', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Prestamos_Detalle;
GO

CREATE TABLE dbo.RH_Prestamos_Detalle (
    [PrestamoDetalleID] INT NOT NULL,
    [PrestamoID] INT NOT NULL,
    [PeriodoNominaID] INT NULL,
    [NominaID] INT NULL,
    [FechaProgramada] DATE NULL,
    [FechaAplicacion] DATE NULL,
    [ImporteProgramado] DECIMAL(18,2) NOT NULL,
    [ImporteAplicado] DECIMAL(18,2) NOT NULL DEFAULT ((0)),
    [Estatus] VARCHAR(20) NOT NULL DEFAULT ('PENDIENTE'),
    [Observaciones] VARCHAR(300) NULL
);
GO

ALTER TABLE dbo.RH_Prestamos_Detalle ADD CONSTRAINT [PK__RH_Prest__0CD80FB7C0F4479A] PRIMARY KEY (PrestamoDetalleID);
GO

-- =================================================
-- Tabla: RH_Reloj_Checador
-- Exportado: 2026-06-03T06:46:24.019670
-- =================================================

IF OBJECT_ID('dbo.RH_Reloj_Checador', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Reloj_Checador;
GO

CREATE TABLE dbo.RH_Reloj_Checador (
    [CheckID] INT NOT NULL,
    [ColaboradorID] INT NULL,
    [Tipo_Registro] VARCHAR(10) NULL,
    [FechaHora] DATETIME NULL DEFAULT (getdate()),
    [Geolocalizacion] VARCHAR(100) NULL,
    [Validado_Gerencia] BIT NULL DEFAULT ((0))
);
GO

ALTER TABLE dbo.RH_Reloj_Checador ADD CONSTRAINT [PK__RH_Reloj__8681570634FEA89F] PRIMARY KEY (CheckID);
GO

-- =================================================
-- Tabla: RH_Vacaciones_Movimientos
-- Exportado: 2026-06-03T06:46:24.225968
-- =================================================

IF OBJECT_ID('dbo.RH_Vacaciones_Movimientos', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Vacaciones_Movimientos;
GO

CREATE TABLE dbo.RH_Vacaciones_Movimientos (
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
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

ALTER TABLE dbo.RH_Vacaciones_Movimientos ADD CONSTRAINT [PK__RH_Vacac__109827F75DC6B6A8] PRIMARY KEY (VacacionMovimientoID);
GO

-- =================================================
-- Tabla: RH_Vacaciones_Saldos
-- Exportado: 2026-06-03T06:46:24.431748
-- =================================================

IF OBJECT_ID('dbo.RH_Vacaciones_Saldos', 'U') IS NOT NULL
    DROP TABLE dbo.RH_Vacaciones_Saldos;
GO

CREATE TABLE dbo.RH_Vacaciones_Saldos (
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
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

CREATE INDEX [IX_RH_Vacaciones_Saldos_Colaborador_Ejercicio] ON dbo.RH_Vacaciones_Saldos (ColaboradorID, Ejercicio, Activo);
ALTER TABLE dbo.RH_Vacaciones_Saldos ADD CONSTRAINT [PK__RH_Vacac__5B90F6A0B2BB86AC] PRIMARY KEY (VacacionSaldoID);
GO

-- =================================================
-- Tabla: Scheduler_BitacoraJobs
-- Exportado: 2026-06-03T06:46:24.637985
-- =================================================

IF OBJECT_ID('dbo.Scheduler_BitacoraJobs', 'U') IS NOT NULL
    DROP TABLE dbo.Scheduler_BitacoraJobs;
GO

CREATE TABLE dbo.Scheduler_BitacoraJobs (
    [ID] INT NOT NULL,
    [JobName] VARCHAR(100) NOT NULL,
    [RunID] VARCHAR(50) NOT NULL,
    [Accion] VARCHAR(50) NOT NULL,
    [FechaAccion] DATETIME NULL DEFAULT (getutcdate()),
    [ServerID] VARCHAR(50) NULL,
    [DetallesJSON] NVARCHAR(MAX) NULL,
    [Exito] BIT NULL DEFAULT ((1)),
    [MensajeError] NVARCHAR(MAX) NULL
);
GO

CREATE INDEX [IX_Bitacora_Fecha] ON dbo.Scheduler_BitacoraJobs (FechaAccion);
CREATE INDEX [IX_Bitacora_Job] ON dbo.Scheduler_BitacoraJobs (JobName);
CREATE INDEX [IX_Bitacora_Run] ON dbo.Scheduler_BitacoraJobs (RunID);
ALTER TABLE dbo.Scheduler_BitacoraJobs ADD CONSTRAINT [PK__Schedule__3214EC2741691D32] PRIMARY KEY (ID);
GO

-- =================================================
-- Tabla: Scheduler_InventariosProcesados
-- Exportado: 2026-06-03T06:47:31.147205
-- =================================================

IF OBJECT_ID('dbo.Scheduler_InventariosProcesados', 'U') IS NOT NULL
    DROP TABLE dbo.Scheduler_InventariosProcesados;
GO

CREATE TABLE dbo.Scheduler_InventariosProcesados (
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
    [DetallesJSON] NVARCHAR(MAX) NULL
);
GO

CREATE INDEX [IX_Inventarios_Estado] ON dbo.Scheduler_InventariosProcesados (Estado);
CREATE INDEX [IX_Inventarios_Fecha] ON dbo.Scheduler_InventariosProcesados (FechaDeteccion);
CREATE INDEX [IX_Inventarios_Server] ON dbo.Scheduler_InventariosProcesados (ServerID);
ALTER TABLE dbo.Scheduler_InventariosProcesados ADD CONSTRAINT [PK__Schedule__3214EC2701D71945] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ_Inventario_Clave] ON dbo.Scheduler_InventariosProcesados (SistemaOrigen, ServerID, SucursalID, AlmacenID, FolioInventario);
GO

-- =================================================
-- Tabla: Scheduler_PedidosProcesados
-- Exportado: 2026-06-03T06:47:31.353118
-- =================================================

IF OBJECT_ID('dbo.Scheduler_PedidosProcesados', 'U') IS NOT NULL
    DROP TABLE dbo.Scheduler_PedidosProcesados;
GO

CREATE TABLE dbo.Scheduler_PedidosProcesados (
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
    [DetallesJSON] NVARCHAR(MAX) NULL
);
GO

CREATE INDEX [IX_Pedidos_Estado] ON dbo.Scheduler_PedidosProcesados (Estado);
CREATE INDEX [IX_Pedidos_Fecha] ON dbo.Scheduler_PedidosProcesados (FechaDeteccion);
CREATE INDEX [IX_Pedidos_Server] ON dbo.Scheduler_PedidosProcesados (ServerID);
ALTER TABLE dbo.Scheduler_PedidosProcesados ADD CONSTRAINT [PK__Schedule__3214EC27E48F72C9] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ_Pedido_Clave] ON dbo.Scheduler_PedidosProcesados (SistemaOrigen, ServerID, EmpresaID, FolioPedido);
GO

-- =================================================
-- Tabla: Servidores_Conexiones
-- Exportado: 2026-06-03T06:47:31.559195
-- =================================================

IF OBJECT_ID('dbo.Servidores_Conexiones', 'U') IS NOT NULL
    DROP TABLE dbo.Servidores_Conexiones;
GO

CREATE TABLE dbo.Servidores_Conexiones (
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
    [ultimo_error_sync] NVARCHAR(500) NULL
);
GO

CREATE INDEX [IX_Servidores_Activo] ON dbo.Servidores_Conexiones (activo);
CREATE INDEX [IX_Servidores_SystemType] ON dbo.Servidores_Conexiones (system_type);
CREATE INDEX [IX_Servidores_Tipo] ON dbo.Servidores_Conexiones (tipo_conexion);
ALTER TABLE dbo.Servidores_Conexiones ADD CONSTRAINT [PK__Servidor__3213E83FF4F5D577] PRIMARY KEY (id);
GO

-- =================================================
-- Tabla: Servidores_Conexiones_backup_tipos_enriq_20260513_0840
-- Exportado: 2026-06-03T06:47:31.801190
-- =================================================

IF OBJECT_ID('dbo.Servidores_Conexiones_backup_tipos_enriq_20260513_0840', 'U') IS NOT NULL
    DROP TABLE dbo.Servidores_Conexiones_backup_tipos_enriq_20260513_0840;
GO

CREATE TABLE dbo.Servidores_Conexiones_backup_tipos_enriq_20260513_0840 (
    [mongodb_id] NVARCHAR(100) NULL,
    [nombre] NVARCHAR(100) NOT NULL,
    [tipos_movimiento_anterior] NVARCHAR(MAX) NULL,
    [fecha_backup] DATETIME NOT NULL,
    [fase] VARCHAR(35) NOT NULL
);
GO

GO

-- =================================================
-- Tabla: Servidores_Conexiones_backup_tipos_mov_20260513_0729
-- Exportado: 2026-06-03T06:47:32.039671
-- =================================================

IF OBJECT_ID('dbo.Servidores_Conexiones_backup_tipos_mov_20260513_0729', 'U') IS NOT NULL
    DROP TABLE dbo.Servidores_Conexiones_backup_tipos_mov_20260513_0729;
GO

CREATE TABLE dbo.Servidores_Conexiones_backup_tipos_mov_20260513_0729 (
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

GO

-- =================================================
-- Tabla: Servidores_Conexiones_Log
-- Exportado: 2026-06-03T06:47:32.278252
-- =================================================

IF OBJECT_ID('dbo.Servidores_Conexiones_Log', 'U') IS NOT NULL
    DROP TABLE dbo.Servidores_Conexiones_Log;
GO

CREATE TABLE dbo.Servidores_Conexiones_Log (
    [log_id] BIGINT NOT NULL,
    [servidor_id] UNIQUEIDENTIFIER NULL,
    [accion] NVARCHAR(20) NULL,
    [datos_anteriores] NVARCHAR(MAX) NULL,
    [datos_nuevos] NVARCHAR(MAX) NULL,
    [usuario] NVARCHAR(100) NULL,
    [fecha] DATETIME NULL DEFAULT (getdate()),
    [ip_origen] NVARCHAR(50) NULL
);
GO

ALTER TABLE dbo.Servidores_Conexiones_Log ADD CONSTRAINT [PK__Servidor__9E2397E01A9937E1] PRIMARY KEY (log_id);
GO

-- =================================================
-- Tabla: Servidores_Status
-- Exportado: 2026-06-03T06:47:32.516740
-- =================================================

IF OBJECT_ID('dbo.Servidores_Status', 'U') IS NOT NULL
    DROP TABLE dbo.Servidores_Status;
GO

CREATE TABLE dbo.Servidores_Status (
    [StatusID] INT NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [IsOnline] BIT NULL DEFAULT ((1)),
    [ResponseTimeMs] INT NULL,
    [LastCheck] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.Servidores_Status ADD CONSTRAINT [PK__Servidor__C8EE2043EE3CD07C] PRIMARY KEY (StatusID);
CREATE UNIQUE INDEX [UQ__Servidor__C56AC887CD597F30] ON dbo.Servidores_Status (ServerID);
GO

-- =================================================
-- Tabla: Sesiones
-- Exportado: 2026-06-03T06:47:32.722989
-- =================================================

IF OBJECT_ID('dbo.Sesiones', 'U') IS NOT NULL
    DROP TABLE dbo.Sesiones;
GO

CREATE TABLE dbo.Sesiones (
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
    [FechaModificacion] DATETIME NULL DEFAULT (getutcdate())
);
GO

CREATE INDEX [IX_Sesiones_Activa] ON dbo.Sesiones (EstaActiva);
CREATE INDEX [IX_Sesiones_Expiracion] ON dbo.Sesiones (FechaExpiracion);
CREATE INDEX [IX_Sesiones_Familia] ON dbo.Sesiones (FamiliaTokenID);
CREATE INDEX [IX_Sesiones_Usuario] ON dbo.Sesiones (UsuarioID);
ALTER TABLE dbo.Sesiones ADD CONSTRAINT [PK__Sesiones__52FD7C0648E24E48] PRIMARY KEY (SesionID);
GO

-- =================================================
-- Tabla: SesionesHistorico
-- Exportado: 2026-06-03T06:47:33.063788
-- =================================================

IF OBJECT_ID('dbo.SesionesHistorico', 'U') IS NOT NULL
    DROP TABLE dbo.SesionesHistorico;
GO

CREATE TABLE dbo.SesionesHistorico (
    [HistoricoID] INT NOT NULL,
    [SesionID] VARCHAR(50) NOT NULL,
    [UsuarioID] VARCHAR(50) NOT NULL,
    [TipoUsuario] VARCHAR(20) NULL,
    [Accion] VARCHAR(50) NOT NULL,
    [FechaAccion] DATETIME NULL DEFAULT (getutcdate()),
    [IPCliente] VARCHAR(45) NULL,
    [UserAgent] VARCHAR(500) NULL,
    [DetallesJSON] NVARCHAR(MAX) NULL,
    [AccionRealizadaPor] VARCHAR(50) NULL
);
GO

CREATE INDEX [IX_SesionesHistorico_Fecha] ON dbo.SesionesHistorico (FechaAccion);
CREATE INDEX [IX_SesionesHistorico_Sesion] ON dbo.SesionesHistorico (SesionID);
CREATE INDEX [IX_SesionesHistorico_Usuario] ON dbo.SesionesHistorico (UsuarioID);
ALTER TABLE dbo.SesionesHistorico ADD CONSTRAINT [PK__Sesiones__4A561D76A5187902] PRIMARY KEY (HistoricoID);
GO

-- =================================================
-- Tabla: Sistema_Capacidades
-- Exportado: 2026-06-03T06:47:33.339687
-- =================================================

IF OBJECT_ID('dbo.Sistema_Capacidades', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_Capacidades;
GO

CREATE TABLE dbo.Sistema_Capacidades (
    [SistemaCapacidadID] INT NOT NULL,
    [SistemaTipoID] INT NOT NULL,
    [CodigoCapacidad] VARCHAR(50) NOT NULL,
    [Descripcion] NVARCHAR(200) NULL,
    [RequiereApiLocal] BIT NULL DEFAULT ((0)),
    [RequiereSqlDirecto] BIT NULL DEFAULT ((1)),
    [ConfiguracionJSON] NVARCHAR(MAX) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    [UpdatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

CREATE INDEX [IX_SistemaCapacidades_Codigo] ON dbo.Sistema_Capacidades (CodigoCapacidad);
CREATE INDEX [IX_SistemaCapacidades_SistemaTipo] ON dbo.Sistema_Capacidades (SistemaTipoID);
ALTER TABLE dbo.Sistema_Capacidades ADD CONSTRAINT [PK__Sistema___8071A91C95093B9D] PRIMARY KEY (SistemaCapacidadID);
CREATE UNIQUE INDEX [UQ_SistemaCapacidades_TipoCapacidad] ON dbo.Sistema_Capacidades (SistemaTipoID, CodigoCapacidad);
GO

-- =================================================
-- Tabla: Sistema_Catalogo
-- Exportado: 2026-06-03T06:47:33.582029
-- =================================================

IF OBJECT_ID('dbo.Sistema_Catalogo', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_Catalogo;
GO

CREATE TABLE dbo.Sistema_Catalogo (
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
    [AutorizadoPorEmail] NVARCHAR(200) NULL
);
GO

ALTER TABLE dbo.Sistema_Catalogo ADD CONSTRAINT [PK__Sistema___4C36BB66DE7EFC5B] PRIMARY KEY (SistemaID);
CREATE UNIQUE INDEX [UQ_Sistema_Catalogo_Codigo] ON dbo.Sistema_Catalogo (Codigo);
GO

-- =================================================
-- Tabla: Sistema_Empresas
-- Exportado: 2026-06-03T06:47:33.820748
-- =================================================

IF OBJECT_ID('dbo.Sistema_Empresas', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_Empresas;
GO

CREATE TABLE dbo.Sistema_Empresas (
    [EmpresaID] INT NOT NULL,
    [CodigoEmpresa] VARCHAR(20) NOT NULL,
    [NombreEmpresa] NVARCHAR(100) NOT NULL,
    [NombreComercial] NVARCHAR(100) NULL,
    [RFC] VARCHAR(13) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (getutcdate()),
    [FechaModificacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [UpdatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_Sistema_Empresas_Activo] ON dbo.Sistema_Empresas (Activo);
CREATE INDEX [IX_Sistema_Empresas_Codigo] ON dbo.Sistema_Empresas (CodigoEmpresa);
ALTER TABLE dbo.Sistema_Empresas ADD CONSTRAINT [PK_Sistema_Empresas] PRIMARY KEY (EmpresaID);
CREATE UNIQUE INDEX [UQ_Sistema_Empresas_Codigo] ON dbo.Sistema_Empresas (CodigoEmpresa);
GO

-- =================================================
-- Tabla: Sistema_EmpresasAlias
-- Exportado: 2026-06-03T06:47:34.057964
-- =================================================

IF OBJECT_ID('dbo.Sistema_EmpresasAlias', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_EmpresasAlias;
GO

CREATE TABLE dbo.Sistema_EmpresasAlias (
    [EmpresaAliasID] INT NOT NULL,
    [EmpresaID] INT NOT NULL,
    [Alias] NVARCHAR(200) NOT NULL,
    [AliasNormalizado] NVARCHAR(200) NOT NULL,
    [OrigenAlias] VARCHAR(50) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaActualizacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [UpdatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_EmpresasAlias_EmpresaID] ON dbo.Sistema_EmpresasAlias (EmpresaID, Activo);
CREATE UNIQUE INDEX [IX_EmpresasAlias_Normalizado_Activo] ON dbo.Sistema_EmpresasAlias (AliasNormalizado);
ALTER TABLE dbo.Sistema_EmpresasAlias ADD CONSTRAINT [PK__Sistema___1D1B85060AB61A61] PRIMARY KEY (EmpresaAliasID);
GO

-- =================================================
-- Tabla: Sistema_EmpresasMongoMap
-- Exportado: 2026-06-03T06:47:34.297933
-- =================================================

IF OBJECT_ID('dbo.Sistema_EmpresasMongoMap', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_EmpresasMongoMap;
GO

CREATE TABLE dbo.Sistema_EmpresasMongoMap (
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
    [CreatedBy] VARCHAR(100) NOT NULL DEFAULT ('FASE2B21_MIGRATION')
);
GO

ALTER TABLE dbo.Sistema_EmpresasMongoMap ADD CONSTRAINT [PK__Sistema___3265E2FB7144EF00] PRIMARY KEY (MapID);
CREATE UNIQUE INDEX [UQ_EmpresaMongoUUID] ON dbo.Sistema_EmpresasMongoMap (EmpresaMongoUUID);
GO

-- =================================================
-- Tabla: Sistema_EmpresasServidores
-- Exportado: 2026-06-03T06:47:34.537804
-- =================================================

IF OBJECT_ID('dbo.Sistema_EmpresasServidores', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_EmpresasServidores;
GO

CREATE TABLE dbo.Sistema_EmpresasServidores (
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
    [Observaciones] NVARCHAR(500) NULL
);
GO

CREATE INDEX [IX_EmpresasServidores_Empresa] ON dbo.Sistema_EmpresasServidores (EmpresaID, Activo);
CREATE INDEX [IX_EmpresasServidores_Servidor] ON dbo.Sistema_EmpresasServidores (ServidorID, Activo);
ALTER TABLE dbo.Sistema_EmpresasServidores ADD CONSTRAINT [PK__Sistema___5951170C87EAC4B0] PRIMARY KEY (EmpresaServidorID);
GO

-- =================================================
-- Tabla: Sistema_Gobierno_Tablas
-- Exportado: 2026-06-03T06:47:34.778331
-- =================================================

IF OBJECT_ID('dbo.Sistema_Gobierno_Tablas', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_Gobierno_Tablas;
GO

CREATE TABLE dbo.Sistema_Gobierno_Tablas (
    [id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [nombre_tabla] NVARCHAR(128) NOT NULL,
    [esquema] NVARCHAR(128) NOT NULL DEFAULT ('dbo'),
    [modulo] NVARCHAR(100) NOT NULL,
    [categoria] NVARCHAR(50) NOT NULL,
    [estado] NVARCHAR(50) NOT NULL,
    [fuente_verdad] NVARCHAR(100) NULL,
    [tabla_reemplazo] NVARCHAR(128) NULL,
    [permite_insert] BIT NOT NULL DEFAULT ((1)),
    [permite_update] BIT NOT NULL DEFAULT ((1)),
    [permite_delete] BIT NOT NULL DEFAULT ((0)),
    [observaciones] NVARCHAR(MAX) NULL,
    [fecha_alta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [fecha_ultima_actualizacion] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

ALTER TABLE dbo.Sistema_Gobierno_Tablas ADD CONSTRAINT [PK__Sistema___3213E83F8C24019E] PRIMARY KEY (id);
CREATE UNIQUE INDEX [UX_Sistema_Gobierno_Tablas] ON dbo.Sistema_Gobierno_Tablas (esquema, nombre_tabla);
GO

-- =================================================
-- Tabla: Sistema_HorariosServicioUnidad
-- Exportado: 2026-06-03T06:47:35.053053
-- =================================================

IF OBJECT_ID('dbo.Sistema_HorariosServicioUnidad', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_HorariosServicioUnidad;
GO

CREATE TABLE dbo.Sistema_HorariosServicioUnidad (
    [id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [unidad_negocio_id] NVARCHAR(50) NOT NULL,
    [dia_semana] INT NOT NULL,
    [hora_inicio_operativo] TIME NOT NULL,
    [hora_fin_operativo] TIME NOT NULL,
    [cruza_medianoche] BIT NOT NULL DEFAULT ((0)),
    [activo] BIT NOT NULL DEFAULT ((1)),
    [fecha_creacion] DATETIME2 NULL DEFAULT (sysutcdatetime()),
    [fecha_modificacion] DATETIME2 NULL DEFAULT (sysutcdatetime())
);
GO

ALTER TABLE dbo.Sistema_HorariosServicioUnidad ADD CONSTRAINT [PK__Sistema___3213E83FE5EE48C8] PRIMARY KEY (id);
CREATE UNIQUE INDEX [UQ_Horario_Unidad_Dia] ON dbo.Sistema_HorariosServicioUnidad (unidad_negocio_id, dia_semana);
GO

-- =================================================
-- Tabla: Sistema_Migracion_MongoSQL_Mapeo
-- Exportado: 2026-06-03T06:47:35.293345
-- =================================================

IF OBJECT_ID('dbo.Sistema_Migracion_MongoSQL_Mapeo', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_Migracion_MongoSQL_Mapeo;
GO

CREATE TABLE dbo.Sistema_Migracion_MongoSQL_Mapeo (
    [id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [coleccion_mongo] NVARCHAR(200) NOT NULL,
    [tabla_sql_destino] NVARCHAR(128) NULL,
    [modulo] NVARCHAR(100) NOT NULL,
    [estado] NVARCHAR(50) NOT NULL DEFAULT ('PENDIENTE'),
    [prioridad] NVARCHAR(20) NOT NULL DEFAULT ('P2'),
    [estrategia] NVARCHAR(MAX) NULL,
    [fecha_inicio] DATETIME2 NULL,
    [fecha_fin] DATETIME2 NULL,
    [observaciones] NVARCHAR(MAX) NULL,
    [fecha_alta] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

ALTER TABLE dbo.Sistema_Migracion_MongoSQL_Mapeo ADD CONSTRAINT [PK__Sistema___3213E83FE7821EFA] PRIMARY KEY (id);
CREATE UNIQUE INDEX [UX_Sistema_Migracion_MongoSQL_Mapeo_Coleccion] ON dbo.Sistema_Migracion_MongoSQL_Mapeo (coleccion_mongo);
GO

-- =================================================
-- Tabla: Sistema_Modulos
-- Exportado: 2026-06-03T06:47:35.533385
-- =================================================

IF OBJECT_ID('dbo.Sistema_Modulos', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_Modulos;
GO

CREATE TABLE dbo.Sistema_Modulos (
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
    [FechaCreacion] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.Sistema_Modulos ADD CONSTRAINT [PK__Sistema___26CEB88F81BBEED2] PRIMARY KEY (ModuloID);
CREATE UNIQUE INDEX [UQ__Sistema___06370DACDE10BF80] ON dbo.Sistema_Modulos (Codigo);
GO

-- =================================================
-- Tabla: Sistema_ModulosMenus
-- Exportado: 2026-06-03T06:47:35.772552
-- =================================================

IF OBJECT_ID('dbo.Sistema_ModulosMenus', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_ModulosMenus;
GO

CREATE TABLE dbo.Sistema_ModulosMenus (
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
    [FechaCreacion] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.Sistema_ModulosMenus ADD CONSTRAINT [PK__Sistema___C99ED2506562F386] PRIMARY KEY (MenuID);
GO

-- =================================================
-- Tabla: Sistema_ModulosPermisos
-- Exportado: 2026-06-03T06:47:36.010740
-- =================================================

IF OBJECT_ID('dbo.Sistema_ModulosPermisos', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_ModulosPermisos;
GO

CREATE TABLE dbo.Sistema_ModulosPermisos (
    [PermisoID] INT NOT NULL,
    [ModuloID] INT NOT NULL,
    [Codigo] NVARCHAR(100) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(255) NULL,
    [Categoria] NVARCHAR(50) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.Sistema_ModulosPermisos ADD CONSTRAINT [PK__Sistema___96E0C703F5D43229] PRIMARY KEY (PermisoID);
CREATE UNIQUE INDEX [UQ__Sistema___06370DAC6ACFB05F] ON dbo.Sistema_ModulosPermisos (Codigo);
GO

-- =================================================
-- Tabla: Sistema_ModulosVisibilidad
-- Exportado: 2026-06-03T06:47:36.252586
-- =================================================

IF OBJECT_ID('dbo.Sistema_ModulosVisibilidad', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_ModulosVisibilidad;
GO

CREATE TABLE dbo.Sistema_ModulosVisibilidad (
    [ModuloVisibilidadID] INT NOT NULL,
    [SistemaTipoID] INT NOT NULL,
    [CodigoModulo] VARCHAR(50) NOT NULL,
    [DescripcionModulo] NVARCHAR(100) NULL,
    [Visible] BIT NULL DEFAULT ((1)),
    [OrdenMenu] INT NULL DEFAULT ((0)),
    [ConfiguracionJSON] NVARCHAR(MAX) NULL,
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

CREATE INDEX [IX_SistemaModulos_Modulo] ON dbo.Sistema_ModulosVisibilidad (CodigoModulo);
ALTER TABLE dbo.Sistema_ModulosVisibilidad ADD CONSTRAINT [PK__Sistema___FD10AD70339E0053] PRIMARY KEY (ModuloVisibilidadID);
CREATE UNIQUE INDEX [UQ_SistemaModulos_TipoModulo] ON dbo.Sistema_ModulosVisibilidad (SistemaTipoID, CodigoModulo);
GO

-- =================================================
-- Tabla: Sistema_RBAC_Permisos
-- Exportado: 2026-06-03T06:47:36.491075
-- =================================================

IF OBJECT_ID('dbo.Sistema_RBAC_Permisos', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_RBAC_Permisos;
GO

CREATE TABLE dbo.Sistema_RBAC_Permisos (
    [permiso_id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [codigo] NVARCHAR(150) NOT NULL,
    [nombre] NVARCHAR(200) NOT NULL,
    [modulo] NVARCHAR(100) NOT NULL,
    [descripcion] NVARCHAR(500) NULL,
    [activo] BIT NOT NULL DEFAULT ((1)),
    [fecha_alta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [fecha_ultima_actualizacion] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

ALTER TABLE dbo.Sistema_RBAC_Permisos ADD CONSTRAINT [PK__Sistema___60B569CD10A5FF55] PRIMARY KEY (permiso_id);
CREATE UNIQUE INDEX [UX_Sistema_RBAC_Permisos_Codigo] ON dbo.Sistema_RBAC_Permisos (codigo);
GO

-- =================================================
-- Tabla: Sistema_RBAC_Roles
-- Exportado: 2026-06-03T06:47:36.730269
-- =================================================

IF OBJECT_ID('dbo.Sistema_RBAC_Roles', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_RBAC_Roles;
GO

CREATE TABLE dbo.Sistema_RBAC_Roles (
    [rol_id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [codigo] NVARCHAR(100) NOT NULL,
    [nombre] NVARCHAR(200) NOT NULL,
    [descripcion] NVARCHAR(500) NULL,
    [es_sistema] BIT NOT NULL DEFAULT ((0)),
    [activo] BIT NOT NULL DEFAULT ((1)),
    [fecha_alta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [fecha_ultima_actualizacion] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

ALTER TABLE dbo.Sistema_RBAC_Roles ADD CONSTRAINT [PK__Sistema___CF32E44336A3628F] PRIMARY KEY (rol_id);
CREATE UNIQUE INDEX [UX_Sistema_RBAC_Roles_Codigo] ON dbo.Sistema_RBAC_Roles (codigo);
GO

-- =================================================
-- Tabla: Sistema_RBAC_RolesPermisos
-- Exportado: 2026-06-03T06:47:36.973202
-- =================================================

IF OBJECT_ID('dbo.Sistema_RBAC_RolesPermisos', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_RBAC_RolesPermisos;
GO

CREATE TABLE dbo.Sistema_RBAC_RolesPermisos (
    [rol_permiso_id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [rol_id] UNIQUEIDENTIFIER NOT NULL,
    [permiso_id] UNIQUEIDENTIFIER NOT NULL,
    [activo] BIT NOT NULL DEFAULT ((1)),
    [fecha_alta] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

ALTER TABLE dbo.Sistema_RBAC_RolesPermisos ADD CONSTRAINT [PK__Sistema___D26ED78CF0E9D418] PRIMARY KEY (rol_permiso_id);
CREATE UNIQUE INDEX [UX_Sistema_RBAC_RolesPermisos] ON dbo.Sistema_RBAC_RolesPermisos (rol_id, permiso_id);
GO

-- =================================================
-- Tabla: Sistema_ServidorSucursalesConfig
-- Exportado: 2026-06-03T06:47:37.211310
-- =================================================

IF OBJECT_ID('dbo.Sistema_ServidorSucursalesConfig', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_ServidorSucursalesConfig;
GO

CREATE TABLE dbo.Sistema_ServidorSucursalesConfig (
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
    [Observaciones] NVARCHAR(500) NULL
);
GO

ALTER TABLE dbo.Sistema_ServidorSucursalesConfig ADD CONSTRAINT [PK__Sistema___C3BC333C8E40C4D1] PRIMARY KEY (ConfigID);
GO

-- =================================================
-- Tabla: Sistema_Sucursales
-- Exportado: 2026-06-03T06:47:37.451922
-- =================================================

IF OBJECT_ID('dbo.Sistema_Sucursales', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_Sucursales;
GO

CREATE TABLE dbo.Sistema_Sucursales (
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
    [Observaciones] NVARCHAR(500) NULL
);
GO

ALTER TABLE dbo.Sistema_Sucursales ADD CONSTRAINT [PK__Sistema___6CB482819D69E291] PRIMARY KEY (SucursalID);
GO

-- =================================================
-- Tabla: Sistema_SucursalServidorConfig
-- Exportado: 2026-06-03T06:47:37.688475
-- =================================================

IF OBJECT_ID('dbo.Sistema_SucursalServidorConfig', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_SucursalServidorConfig;
GO

CREATE TABLE dbo.Sistema_SucursalServidorConfig (
    [ConfigID] INT NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [SucursalNombre] VARCHAR(200) NOT NULL,
    [VisibleEnOperaciones] BIT NULL DEFAULT ((1)),
    [Activa] BIT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.Sistema_SucursalServidorConfig ADD CONSTRAINT [PK__Sistema___C3BC333C874F3D64] PRIMARY KEY (ConfigID);
GO

-- =================================================
-- Tabla: Sistema_SucursalServidorMapeo
-- Exportado: 2026-06-03T06:47:37.894054
-- =================================================

IF OBJECT_ID('dbo.Sistema_SucursalServidorMapeo', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_SucursalServidorMapeo;
GO

CREATE TABLE dbo.Sistema_SucursalServidorMapeo (
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
    [Observaciones] NVARCHAR(500) NULL
);
GO

ALTER TABLE dbo.Sistema_SucursalServidorMapeo ADD CONSTRAINT [PK__Sistema___CC527B086B87FE62] PRIMARY KEY (MapeoID);
GO

-- =================================================
-- Tabla: Sistema_Tipos
-- Exportado: 2026-06-03T06:47:38.133351
-- =================================================

IF OBJECT_ID('dbo.Sistema_Tipos', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_Tipos;
GO

CREATE TABLE dbo.Sistema_Tipos (
    [SistemaTipoID] INT NOT NULL,
    [CodigoSistema] VARCHAR(50) NOT NULL,
    [NombreSistema] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaActualizacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [UpdatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_Sistema_Tipos_Activo] ON dbo.Sistema_Tipos (Activo);
ALTER TABLE dbo.Sistema_Tipos ADD CONSTRAINT [PK__Sistema___7BA44B9F9A300B86] PRIMARY KEY (SistemaTipoID);
CREATE UNIQUE INDEX [UQ_Sistema_Tipos_Codigo] ON dbo.Sistema_Tipos (CodigoSistema);
GO

-- =================================================
-- Tabla: Sistema_TiposVariantes
-- Exportado: 2026-06-03T06:47:38.373048
-- =================================================

IF OBJECT_ID('dbo.Sistema_TiposVariantes', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_TiposVariantes;
GO

CREATE TABLE dbo.Sistema_TiposVariantes (
    [VarianteID] INT NOT NULL,
    [SistemaTipoID] INT NOT NULL,
    [VarianteNombre] VARCHAR(50) NOT NULL,
    [EsCanonico] BIT NULL DEFAULT ((0)),
    [Activo] BIT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate())
);
GO

CREATE INDEX [IX_SistemaTiposVariantes_Nombre] ON dbo.Sistema_TiposVariantes (VarianteNombre);
ALTER TABLE dbo.Sistema_TiposVariantes ADD CONSTRAINT [PK__Sistema___FE18F96BE8DF9B03] PRIMARY KEY (VarianteID);
CREATE UNIQUE INDEX [UQ_SistemaTiposVariantes_Nombre] ON dbo.Sistema_TiposVariantes (VarianteNombre);
GO

-- =================================================
-- Tabla: Sistema_TurnosOperativosUnidad
-- Exportado: 2026-06-03T06:47:38.611503
-- =================================================

IF OBJECT_ID('dbo.Sistema_TurnosOperativosUnidad', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_TurnosOperativosUnidad;
GO

CREATE TABLE dbo.Sistema_TurnosOperativosUnidad (
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
    [modificado_por] NVARCHAR(100) NULL
);
GO

ALTER TABLE dbo.Sistema_TurnosOperativosUnidad ADD CONSTRAINT [PK__Sistema___3213E83FE66D7F2F] PRIMARY KEY (id);
CREATE UNIQUE INDEX [UK_TurnoOperativo_Unidad_Turno] ON dbo.Sistema_TurnosOperativosUnidad (unidad_negocio_id, turno_codigo);
GO

-- =================================================
-- Tabla: Sistema_UnidadesNegocioPerfilDigital
-- Exportado: 2026-06-03T06:47:38.850531
-- =================================================

IF OBJECT_ID('dbo.Sistema_UnidadesNegocioPerfilDigital', 'U') IS NOT NULL
    DROP TABLE dbo.Sistema_UnidadesNegocioPerfilDigital;
GO

CREATE TABLE dbo.Sistema_UnidadesNegocioPerfilDigital (
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
    [UsuarioModificacion] NVARCHAR(100) NULL
);
GO

ALTER TABLE dbo.Sistema_UnidadesNegocioPerfilDigital ADD CONSTRAINT [PK__Sistema___E9401D4953164F3E] PRIMARY KEY (PerfilDigitalID);
GO

-- =================================================
-- Tabla: Sync_Control_Ejecuciones
-- Exportado: 2026-06-03T06:47:39.090920
-- =================================================

IF OBJECT_ID('dbo.Sync_Control_Ejecuciones', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Control_Ejecuciones;
GO

CREATE TABLE dbo.Sync_Control_Ejecuciones (
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
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

CREATE INDEX [IX_Sync_Control_Ejecuciones_Run] ON dbo.Sync_Control_Ejecuciones (SyncRunID);
CREATE INDEX [IX_Sync_Control_Ejecuciones_Status] ON dbo.Sync_Control_Ejecuciones (Status);
ALTER TABLE dbo.Sync_Control_Ejecuciones ADD CONSTRAINT [PK__Sync_Con__0DEB92E5064AB66F] PRIMARY KEY (SyncControlID);
CREATE UNIQUE INDEX [UQ__Sync_Con__60C7B3FB482BDEB7] ON dbo.Sync_Control_Ejecuciones (SyncRunID);
GO

-- =================================================
-- Tabla: Sync_Customers
-- Exportado: 2026-06-03T06:47:39.891925
-- =================================================

IF OBJECT_ID('dbo.Sync_Customers', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Customers;
GO

CREATE TABLE dbo.Sync_Customers (
    [customer_id] VARCHAR(64) NOT NULL,
    [full_name] NVARCHAR(200) NOT NULL,
    [commercial_name] NVARCHAR(200) NULL,
    [email] VARCHAR(150) NULL,
    [phone] VARCHAR(32) NULL,
    [affiliate_tier] VARCHAR(16) NULL DEFAULT ('BRONZE'),
    [sync_status] VARCHAR(16) NULL DEFAULT ('SYNCHRONIZED'),
    [last_sync] DATETIME NULL DEFAULT (getdate())
);
GO

CREATE INDEX [IX_SyncIndex_Customers_Email] ON dbo.Sync_Customers (email);
ALTER TABLE dbo.Sync_Customers ADD CONSTRAINT [PK__Sync_Cus__CD65CB85AD33061E] PRIMARY KEY (customer_id);
GO

-- =================================================
-- Tabla: Sync_Impuestos_Origen
-- Exportado: 2026-06-03T06:47:40.097467
-- =================================================

IF OBJECT_ID('dbo.Sync_Impuestos_Origen', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Impuestos_Origen;
GO

CREATE TABLE dbo.Sync_Impuestos_Origen (
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
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime())
);
GO

ALTER TABLE dbo.Sync_Impuestos_Origen ADD CONSTRAINT [PK__Sync_Imp__CC527B08D9EB1557] PRIMARY KEY (MapeoID);
CREATE UNIQUE INDEX [UQ_SyncImpuestos_Origen] ON dbo.Sync_Impuestos_Origen (ServerID, CodigoImpuestoOrigen);
GO

-- =================================================
-- Tabla: Sync_Inventory
-- Exportado: 2026-06-03T06:47:40.304565
-- =================================================

IF OBJECT_ID('dbo.Sync_Inventory', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Inventory;
GO

CREATE TABLE dbo.Sync_Inventory (
    [sku] VARCHAR(64) NOT NULL,
    [item_name] NVARCHAR(200) NOT NULL,
    [stock_qty] INT NULL DEFAULT ((0)),
    [min_qty_warning] INT NULL DEFAULT ((10)),
    [warehouse] NVARCHAR(100) NOT NULL,
    [last_audit] DATETIME NULL DEFAULT (getdate()),
    [sync_status] VARCHAR(16) NULL DEFAULT ('ONLINE')
);
GO

CREATE INDEX [IX_SyncIndex_Inventory_Warehouse] ON dbo.Sync_Inventory (warehouse);
ALTER TABLE dbo.Sync_Inventory ADD CONSTRAINT [PK__Sync_Inv__DDDF4BE618D29D8C] PRIMARY KEY (sku);
GO

-- =================================================
-- Tabla: Sync_KPI_Ventas_Unidades
-- Exportado: 2026-06-03T06:47:40.510448
-- =================================================

IF OBJECT_ID('dbo.Sync_KPI_Ventas_Unidades', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_KPI_Ventas_Unidades;
GO

CREATE TABLE dbo.Sync_KPI_Ventas_Unidades (
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
    [Proyeccion_Anual_Ventas] DECIMAL(18,4) NULL DEFAULT ((0))
);
GO

CREATE INDEX [IX_KPI_Mes_Anio] ON dbo.Sync_KPI_Ventas_Unidades (Mes, Anio);
ALTER TABLE dbo.Sync_KPI_Ventas_Unidades ADD CONSTRAINT [PK__Sync_KPI__3213E83F7058331A] PRIMARY KEY (id);
GO

-- =================================================
-- Tabla: Sync_Logs
-- Exportado: 2026-06-03T06:47:40.716618
-- =================================================

IF OBJECT_ID('dbo.Sync_Logs', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Logs;
GO

CREATE TABLE dbo.Sync_Logs (
    [id] INT NOT NULL,
    [service] NVARCHAR(100) NOT NULL,
    [type] NVARCHAR(20) NOT NULL,
    [message] NVARCHAR(MAX) NOT NULL,
    [timestamp] DATETIME NULL DEFAULT (getdate()),
    [operador] NVARCHAR(100) NULL DEFAULT ('PYTHON_AUTOGESTIVE_AGENT')
);
GO

CREATE INDEX [IX_SyncIndex_Logs_Timestamp] ON dbo.Sync_Logs (timestamp, service);
ALTER TABLE dbo.Sync_Logs ADD CONSTRAINT [PK__Sync_Log__3213E83F3CA51312] PRIMARY KEY (id);
GO

-- =================================================
-- Tabla: Sync_Menus
-- Exportado: 2026-06-03T06:47:40.953546
-- =================================================

IF OBJECT_ID('dbo.Sync_Menus', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Menus;
GO

CREATE TABLE dbo.Sync_Menus (
    [id] INT NOT NULL,
    [titulo] NVARCHAR(100) NOT NULL,
    [label] NVARCHAR(100) NOT NULL,
    [icon] NVARCHAR(50) NOT NULL,
    [route] NVARCHAR(100) NOT NULL,
    [active] BIT NULL DEFAULT ((1)),
    [orden] INT NOT NULL,
    [rol_permitido] NVARCHAR(100) NULL DEFAULT ('OPERADOR_EDARSA'),
    [ultima_actualizacion] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.Sync_Menus ADD CONSTRAINT [PK__Sync_Men__3213E83F274E86A2] PRIMARY KEY (id);
GO

-- =================================================
-- Tabla: Sync_Mesas
-- Exportado: 2026-06-03T06:47:41.192533
-- =================================================

IF OBJECT_ID('dbo.Sync_Mesas', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Mesas;
GO

CREATE TABLE dbo.Sync_Mesas (
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
    [FechaSync] DATETIME2 NULL DEFAULT (getutcdate())
);
GO

ALTER TABLE dbo.Sync_Mesas ADD CONSTRAINT [PK__Sync_Mes__3214EC27FBF0ADA7] PRIMARY KEY (ID);
GO

-- =================================================
-- Tabla: Sync_Metas_Comerciales
-- Exportado: 2026-06-03T06:47:41.400198
-- =================================================

IF OBJECT_ID('dbo.Sync_Metas_Comerciales', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Metas_Comerciales;
GO

CREATE TABLE dbo.Sync_Metas_Comerciales (
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
    [Activo] BIT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Sync_Metas_Comerciales ADD CONSTRAINT [PK__Sync_Met__3214EC2798A1A0BB] PRIMARY KEY (ID);
GO

-- =================================================
-- Tabla: Sync_Movimientos_Detalle
-- Exportado: 2026-06-03T06:47:41.609500
-- =================================================

IF OBJECT_ID('dbo.Sync_Movimientos_Detalle', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Movimientos_Detalle;
GO

CREATE TABLE dbo.Sync_Movimientos_Detalle (
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
    [FechaSync] DATETIME2 NULL DEFAULT (getutcdate())
);
GO

ALTER TABLE dbo.Sync_Movimientos_Detalle ADD CONSTRAINT [PK__Sync_Mov__3214EC2798273539] PRIMARY KEY (ID);
GO

-- =================================================
-- Tabla: Sync_PAX_Detalle
-- Exportado: 2026-06-03T06:47:41.819076
-- =================================================

IF OBJECT_ID('dbo.Sync_PAX_Detalle', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_PAX_Detalle;
GO

CREATE TABLE dbo.Sync_PAX_Detalle (
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
    [FechaSync] DATETIME2 NULL DEFAULT (getutcdate())
);
GO

ALTER TABLE dbo.Sync_PAX_Detalle ADD CONSTRAINT [PK__Sync_PAX__3214EC2708F41028] PRIMARY KEY (ID);
GO

-- =================================================
-- Tabla: Sync_Precios_Historicos
-- Exportado: 2026-06-03T06:47:42.026591
-- =================================================

IF OBJECT_ID('dbo.Sync_Precios_Historicos', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Precios_Historicos;
GO

CREATE TABLE dbo.Sync_Precios_Historicos (
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
    [FechaSync] DATETIME2 NULL DEFAULT (getutcdate())
);
GO

ALTER TABLE dbo.Sync_Precios_Historicos ADD CONSTRAINT [PK__Sync_Pre__3214EC2767486F01] PRIMARY KEY (ID);
GO

-- =================================================
-- Tabla: Sync_Productos
-- Exportado: 2026-06-03T06:47:42.233548
-- =================================================

IF OBJECT_ID('dbo.Sync_Productos', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Productos;
GO

CREATE TABLE dbo.Sync_Productos (
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
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime())
);
GO

CREATE INDEX [IX_Sync_Productos_FamiliaID] ON dbo.Sync_Productos (FamiliaID);
CREATE INDEX [IX_Sync_Productos_TieneReceta] ON dbo.Sync_Productos (TieneReceta);
ALTER TABLE dbo.Sync_Productos ADD CONSTRAINT [PK__Sync_Pro__A430AE8391D4493A] PRIMARY KEY (ProductoID);
CREATE UNIQUE INDEX [UK_Sync_Productos_Server_Codigo] ON dbo.Sync_Productos (ServerID, CodigoFuente);
GO

-- =================================================
-- Tabla: Sync_Productos_Elaborados
-- Exportado: 2026-06-03T06:47:44.507216
-- =================================================

IF OBJECT_ID('dbo.Sync_Productos_Elaborados', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Productos_Elaborados;
GO

CREATE TABLE dbo.Sync_Productos_Elaborados (
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
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime())
);
GO

CREATE INDEX [IX_Sync_Elaborados_InsumoElaboradoID] ON dbo.Sync_Productos_Elaborados (InsumoElaboradoID);
ALTER TABLE dbo.Sync_Productos_Elaborados ADD CONSTRAINT [PK__Sync_Pro__61028180FBF1125D] PRIMARY KEY (ElaboradoDetalleID);
CREATE UNIQUE INDEX [UK_Sync_Elaborados_Elab_Comp] ON dbo.Sync_Productos_Elaborados (ServerID, InsumoElaboradoCodigoFuente, ComponenteCodigoFuente);
GO

-- =================================================
-- Tabla: Sync_Productos_Familias
-- Exportado: 2026-06-03T06:47:45.413205
-- =================================================

IF OBJECT_ID('dbo.Sync_Productos_Familias', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Productos_Familias;
GO

CREATE TABLE dbo.Sync_Productos_Familias (
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
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime())
);
GO

ALTER TABLE dbo.Sync_Productos_Familias ADD CONSTRAINT [PK__Sync_Pro__42DFCCE4B6F6CCCB] PRIMARY KEY (FamiliaID);
CREATE UNIQUE INDEX [UK_Sync_Familias_Server_Codigo] ON dbo.Sync_Productos_Familias (ServerID, CodigoFuente);
GO

-- =================================================
-- Tabla: Sync_Productos_Insumos
-- Exportado: 2026-06-03T06:47:45.658211
-- =================================================

IF OBJECT_ID('dbo.Sync_Productos_Insumos', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Productos_Insumos;
GO

CREATE TABLE dbo.Sync_Productos_Insumos (
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
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime())
);
GO

ALTER TABLE dbo.Sync_Productos_Insumos ADD CONSTRAINT [PK__Sync_Pro__C10BE9363B6D8DD8] PRIMARY KEY (InsumoID);
CREATE UNIQUE INDEX [UK_Sync_Insumos_Server_Codigo] ON dbo.Sync_Productos_Insumos (ServerID, CodigoFuente);
GO

-- =================================================
-- Tabla: Sync_Productos_Recetas
-- Exportado: 2026-06-03T06:47:47.689156
-- =================================================

IF OBJECT_ID('dbo.Sync_Productos_Recetas', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Productos_Recetas;
GO

CREATE TABLE dbo.Sync_Productos_Recetas (
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
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime())
);
GO

CREATE INDEX [IX_Sync_Recetas_InsumoID] ON dbo.Sync_Productos_Recetas (InsumoID);
CREATE INDEX [IX_Sync_Recetas_ProductoID] ON dbo.Sync_Productos_Recetas (ProductoID);
ALTER TABLE dbo.Sync_Productos_Recetas ADD CONSTRAINT [PK__Sync_Pro__AA109C649CD213AF] PRIMARY KEY (RecetaDetalleID);
CREATE UNIQUE INDEX [UK_Sync_Recetas_Prod_Comp] ON dbo.Sync_Productos_Recetas (ServerID, ProductoCodigoFuente, ComponenteCodigoFuente);
GO

-- =================================================
-- Tabla: Sync_Productos_SubFamilias
-- Exportado: 2026-06-03T06:47:50.290032
-- =================================================

IF OBJECT_ID('dbo.Sync_Productos_SubFamilias', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Productos_SubFamilias;
GO

CREATE TABLE dbo.Sync_Productos_SubFamilias (
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
    [FechaModificacion] DATETIME2 NULL DEFAULT (sysdatetime())
);
GO

ALTER TABLE dbo.Sync_Productos_SubFamilias ADD CONSTRAINT [PK__Sync_Pro__6F1E09BC430F5618] PRIMARY KEY (SubFamiliaID);
CREATE UNIQUE INDEX [UK_Sync_SubFamilias_Server_Codigo] ON dbo.Sync_Productos_SubFamilias (ServerID, CodigoFuente);
GO

-- =================================================
-- Tabla: Sync_Purchases
-- Exportado: 2026-06-03T06:47:50.536999
-- =================================================

IF OBJECT_ID('dbo.Sync_Purchases', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Purchases;
GO

CREATE TABLE dbo.Sync_Purchases (
    [id] VARCHAR(64) NOT NULL,
    [provider_name] NVARCHAR(200) NOT NULL,
    [branch] NVARCHAR(100) NOT NULL,
    [items_detail] NVARCHAR(MAX) NULL,
    [total_amount] NUMERIC(12,2) NOT NULL,
    [status] VARCHAR(32) NULL DEFAULT ('PENDIENTE'),
    [created_at] DATETIME NULL DEFAULT (getdate()),
    [sync_status] VARCHAR(16) NULL DEFAULT ('ONLINE')
);
GO

ALTER TABLE dbo.Sync_Purchases ADD CONSTRAINT [PK__Sync_Pur__3213E83F1141C86F] PRIMARY KEY (id);
GO

-- =================================================
-- Tabla: Sync_Response_Cache
-- Exportado: 2026-06-03T06:47:50.743228
-- =================================================

IF OBJECT_ID('dbo.Sync_Response_Cache', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Response_Cache;
GO

CREATE TABLE dbo.Sync_Response_Cache (
    [id] INT NOT NULL,
    [RequestHash] VARCHAR(64) NOT NULL,
    [ServiceSource] VARCHAR(64) NOT NULL,
    [RequestPayload] NVARCHAR(MAX) NULL,
    [ResponsePayload] NVARCHAR(MAX) NULL,
    [TokenCostFraction] NUMERIC(10,6) NULL DEFAULT ((0.0)),
    [CacheDurationMinutes] INT NULL DEFAULT ((120)),
    [CreatedAt] DATETIME NULL DEFAULT (getdate()),
    [ExpiresAt] DATETIME NULL,
    [HitCount] INT NULL DEFAULT ((0))
);
GO

CREATE INDEX [IX_Cache_Expires] ON dbo.Sync_Response_Cache (ExpiresAt);
CREATE INDEX [IX_Cache_Hash] ON dbo.Sync_Response_Cache (RequestHash, ServiceSource);
ALTER TABLE dbo.Sync_Response_Cache ADD CONSTRAINT [PK__Sync_Res__3213E83FA247E5CD] PRIMARY KEY (id);
GO

-- =================================================
-- Tabla: Sync_Sales
-- Exportado: 2026-06-03T06:47:50.980597
-- =================================================

IF OBJECT_ID('dbo.Sync_Sales', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Sales;
GO

CREATE TABLE dbo.Sync_Sales (
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
    [FechaHora] DATETIME NULL
);
GO

CREATE INDEX [IX_SyncIndex_Sales_Branch] ON dbo.Sync_Sales (branch);
CREATE INDEX [IX_SyncIndex_Sales_CreatedAt] ON dbo.Sync_Sales (created_at);
ALTER TABLE dbo.Sync_Sales ADD CONSTRAINT [PK__Sync_Sal__3213E83F7FC0676D] PRIMARY KEY (id);
GO

-- =================================================
-- Tabla: Sync_Ticket_Perfecto
-- Exportado: 2026-06-03T06:47:51.345099
-- =================================================

IF OBJECT_ID('dbo.Sync_Ticket_Perfecto', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Ticket_Perfecto;
GO

CREATE TABLE dbo.Sync_Ticket_Perfecto (
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
    [MetadatosJSON] NVARCHAR(MAX) NULL
);
GO

ALTER TABLE dbo.Sync_Ticket_Perfecto ADD CONSTRAINT [PK__Sync_Tic__3214EC27AED552C6] PRIMARY KEY (ID);
GO

-- =================================================
-- Tabla: Sync_Token_Ledger
-- Exportado: 2026-06-03T06:47:51.550578
-- =================================================

IF OBJECT_ID('dbo.Sync_Token_Ledger', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Token_Ledger;
GO

CREATE TABLE dbo.Sync_Token_Ledger (
    [LedgerID] INT NOT NULL,
    [OperadorID] VARCHAR(64) NULL DEFAULT ('sk-emergent-universal-gate'),
    [ConsuDate] DATE NULL DEFAULT (CONVERT([date],getdate())),
    [TokensInput] INT NULL DEFAULT ((0)),
    [TokensOutput] INT NULL DEFAULT ((0)),
    [EstimatedCostUSD] NUMERIC(12,4) NULL DEFAULT ((0.0000)),
    [AhorroAcumuladoUSD] NUMERIC(12,4) NULL DEFAULT ((0.0000)),
    [HitRatioPercent] NUMERIC(5,2) NULL DEFAULT ((0.00))
);
GO

ALTER TABLE dbo.Sync_Token_Ledger ADD CONSTRAINT [PK__Sync_Tok__AE70E0AF0E90C477] PRIMARY KEY (LedgerID);
CREATE UNIQUE INDEX [UX_TokenLedger_Date] ON dbo.Sync_Token_Ledger (OperadorID, ConsuDate);
GO

-- =================================================
-- Tabla: Sync_Ventas_Historicas
-- Exportado: 2026-06-03T06:47:51.758822
-- =================================================

IF OBJECT_ID('dbo.Sync_Ventas_Historicas', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Ventas_Historicas;
GO

CREATE TABLE dbo.Sync_Ventas_Historicas (
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
    [UpdatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

CREATE INDEX [IX_Sync_Ventas_Historicas_Fecha] ON dbo.Sync_Ventas_Historicas (FechaOperacion);
CREATE INDEX [IX_Sync_Ventas_Historicas_Server] ON dbo.Sync_Ventas_Historicas (ServerID, FechaOperacion);
CREATE INDEX [IX_Sync_Ventas_Historicas_SyncRun] ON dbo.Sync_Ventas_Historicas (SyncRunID);
ALTER TABLE dbo.Sync_Ventas_Historicas ADD CONSTRAINT [PK__Sync_Ven__733F57C4F223AD5E] PRIMARY KEY (SyncVentaHistoricaID);
CREATE UNIQUE INDEX [UQ_Sync_Ventas_Historicas_Key] ON dbo.Sync_Ventas_Historicas (ServerID, EmpresaID, FechaOperacion);
GO

-- =================================================
-- Tabla: Sync_Ventas_PorDiaSemana
-- Exportado: 2026-06-03T06:47:51.998374
-- =================================================

IF OBJECT_ID('dbo.Sync_Ventas_PorDiaSemana', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Ventas_PorDiaSemana;
GO

CREATE TABLE dbo.Sync_Ventas_PorDiaSemana (
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
    [UpdatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

ALTER TABLE dbo.Sync_Ventas_PorDiaSemana ADD CONSTRAINT [PK__Sync_Ven__7D316FC0BC3C33B5] PRIMARY KEY (SyncVentaPorDiaSemanaID);
CREATE UNIQUE INDEX [UQ_Sync_Ventas_PorDiaSemana_Key] ON dbo.Sync_Ventas_PorDiaSemana (ServerID, EmpresaID, FechaInicioPeriodo, FechaFinPeriodo, DiaSemana);
GO

-- =================================================
-- Tabla: Sync_Ventas_PorHora
-- Exportado: 2026-06-03T06:47:52.237745
-- =================================================

IF OBJECT_ID('dbo.Sync_Ventas_PorHora', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Ventas_PorHora;
GO

CREATE TABLE dbo.Sync_Ventas_PorHora (
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
    [UpdatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

CREATE INDEX [IX_Sync_Ventas_PorHora_Fecha] ON dbo.Sync_Ventas_PorHora (FechaOperacion);
ALTER TABLE dbo.Sync_Ventas_PorHora ADD CONSTRAINT [PK__Sync_Ven__F78FC55CC6A2664B] PRIMARY KEY (SyncVentaPorHoraID);
CREATE UNIQUE INDEX [UQ_Sync_Ventas_PorHora_Key] ON dbo.Sync_Ventas_PorHora (ServerID, EmpresaID, FechaOperacion, Hora);
GO

-- =================================================
-- Tabla: Sync_Vtiger_Contactos
-- Exportado: 2026-06-03T06:47:52.577627
-- =================================================

IF OBJECT_ID('dbo.Sync_Vtiger_Contactos', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Vtiger_Contactos;
GO

CREATE TABLE dbo.Sync_Vtiger_Contactos (
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
    [FechaUltimoPush] DATETIME NULL
);
GO

ALTER TABLE dbo.Sync_Vtiger_Contactos ADD CONSTRAINT [PK__Sync_Vti__7E50DEA6A434ECF5] PRIMARY KEY (SyncID);
CREATE UNIQUE INDEX [UQ__Sync_Vti__823CA48718527AC9] ON dbo.Sync_Vtiger_Contactos (VtigerID);
GO

-- =================================================
-- Tabla: Sync_Vtiger_Cuentas
-- Exportado: 2026-06-03T06:47:52.817485
-- =================================================

IF OBJECT_ID('dbo.Sync_Vtiger_Cuentas', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Vtiger_Cuentas;
GO

CREATE TABLE dbo.Sync_Vtiger_Cuentas (
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
    [FechaUltimoPush] DATETIME NULL
);
GO

ALTER TABLE dbo.Sync_Vtiger_Cuentas ADD CONSTRAINT [PK__Sync_Vti__7E50DEA6C8B6C8C2] PRIMARY KEY (SyncID);
CREATE UNIQUE INDEX [UQ__Sync_Vti__823CA487BCE62382] ON dbo.Sync_Vtiger_Cuentas (VtigerID);
GO

-- =================================================
-- Tabla: Sync_Vtiger_Leads
-- Exportado: 2026-06-03T06:47:53.055437
-- =================================================

IF OBJECT_ID('dbo.Sync_Vtiger_Leads', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Vtiger_Leads;
GO

CREATE TABLE dbo.Sync_Vtiger_Leads (
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
    [FechaUltimoPush] DATETIME NULL
);
GO

ALTER TABLE dbo.Sync_Vtiger_Leads ADD CONSTRAINT [PK__Sync_Vti__7E50DEA6031ED838] PRIMARY KEY (SyncID);
CREATE UNIQUE INDEX [UQ__Sync_Vti__823CA4874941E80C] ON dbo.Sync_Vtiger_Leads (VtigerID);
GO

-- =================================================
-- Tabla: Sync_Vtiger_Log
-- Exportado: 2026-06-03T06:47:53.293100
-- =================================================

IF OBJECT_ID('dbo.Sync_Vtiger_Log', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Vtiger_Log;
GO

CREATE TABLE dbo.Sync_Vtiger_Log (
    [LogID] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [RunID] VARCHAR(50) NOT NULL,
    [Direccion] VARCHAR(20) NULL DEFAULT ('vtiger_to_sql'),
    [FechaInicio] DATETIME NOT NULL,
    [FechaFin] DATETIME NULL,
    [TotalObtenidos] INT NULL DEFAULT ((0)),
    [TotalInsertados] INT NULL DEFAULT ((0)),
    [TotalActualizados] INT NULL DEFAULT ((0)),
    [Errores] INT NULL DEFAULT ((0)),
    [ResultadoJSON] NVARCHAR(MAX) NULL
);
GO

ALTER TABLE dbo.Sync_Vtiger_Log ADD CONSTRAINT [PK__Sync_Vti__5E5499A816D4D3D3] PRIMARY KEY (LogID);
GO

-- =================================================
-- Tabla: Sync_Vtiger_Oportunidades
-- Exportado: 2026-06-03T06:47:54.005897
-- =================================================

IF OBJECT_ID('dbo.Sync_Vtiger_Oportunidades', 'U') IS NOT NULL
    DROP TABLE dbo.Sync_Vtiger_Oportunidades;
GO

CREATE TABLE dbo.Sync_Vtiger_Oportunidades (
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
    [FechaUltimoPush] DATETIME NULL
);
GO

ALTER TABLE dbo.Sync_Vtiger_Oportunidades ADD CONSTRAINT [PK__Sync_Vti__7E50DEA61BC330A3] PRIMARY KEY (SyncID);
CREATE UNIQUE INDEX [UQ__Sync_Vti__823CA4872EB5194F] ON dbo.Sync_Vtiger_Oportunidades (VtigerID);
GO

-- =================================================
-- Tabla: Sys_Roles
-- Exportado: 2026-06-03T06:47:54.243871
-- =================================================

IF OBJECT_ID('dbo.Sys_Roles', 'U') IS NOT NULL
    DROP TABLE dbo.Sys_Roles;
GO

CREATE TABLE dbo.Sys_Roles (
    [IDRol] INT NOT NULL,
    [NombreRol] VARCHAR(50) NOT NULL,
    [NivelAcceso] INT NOT NULL,
    [EsInterno] BIT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Sys_Roles ADD CONSTRAINT [PK__Sys_Role__A681ACB63EE047CD] PRIMARY KEY (IDRol);
GO

-- =================================================
-- Tabla: Sys_Scheduler_Jobs
-- Exportado: 2026-06-03T06:47:54.481205
-- =================================================

IF OBJECT_ID('dbo.Sys_Scheduler_Jobs', 'U') IS NOT NULL
    DROP TABLE dbo.Sys_Scheduler_Jobs;
GO

CREATE TABLE dbo.Sys_Scheduler_Jobs (
    [JobID] VARCHAR(50) NOT NULL,
    [JobName] VARCHAR(100) NOT NULL,
    [CronExpression] VARCHAR(50) NOT NULL,
    [JobType] VARCHAR(20) NOT NULL,
    [Status] VARCHAR(20) NULL DEFAULT ('activo'),
    [LastRunDate] DATETIME NULL
);
GO

ALTER TABLE dbo.Sys_Scheduler_Jobs ADD CONSTRAINT [PK__Sys_Sche__056690E26F29C1C6] PRIMARY KEY (JobID);
GO

-- =================================================
-- Tabla: Sys_Usuarios
-- Exportado: 2026-06-03T06:47:54.719169
-- =================================================

IF OBJECT_ID('dbo.Sys_Usuarios', 'U') IS NOT NULL
    DROP TABLE dbo.Sys_Usuarios;
GO

CREATE TABLE dbo.Sys_Usuarios (
    [IDUsuario] INT NOT NULL,
    [Username] VARCHAR(100) NOT NULL,
    [PasswordHash] VARCHAR(256) NOT NULL,
    [NombreCompleto] VARCHAR(150) NULL,
    [Email] VARCHAR(150) NULL,
    [IDRol] INT NULL,
    [Estatus] VARCHAR(20) NULL DEFAULT ('ACTIVO'),
    [RFC] VARCHAR(20) NULL,
    [IDContactoVtiger] VARCHAR(50) NULL,
    [FechaCreacion] DATETIME NULL DEFAULT (getdate())
);
GO

ALTER TABLE dbo.Sys_Usuarios ADD CONSTRAINT [PK__Sys_Usua__5231116995FAF11A] PRIMARY KEY (IDUsuario);
CREATE UNIQUE INDEX [UQ__Sys_Usua__536C85E493EC703A] ON dbo.Sys_Usuarios (Username);
GO

-- =================================================
-- Tabla: Tablajeria_ConfigContable
-- Exportado: 2026-06-03T06:47:54.923655
-- =================================================

IF OBJECT_ID('dbo.Tablajeria_ConfigContable', 'U') IS NOT NULL
    DROP TABLE dbo.Tablajeria_ConfigContable;
GO

CREATE TABLE dbo.Tablajeria_ConfigContable (
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
    [FechaModificacion] DATETIME2 NULL DEFAULT (getutcdate())
);
GO

CREATE UNIQUE INDEX [IX_ConfigContable_Empresa] ON dbo.Tablajeria_ConfigContable (EmpresaID);
ALTER TABLE dbo.Tablajeria_ConfigContable ADD CONSTRAINT [PK__Tablajer__C3BC333CFE100A4D] PRIMARY KEY (ConfigID);
GO

-- =================================================
-- Tabla: Tablajeria_CosteoDetalle
-- Exportado: 2026-06-03T06:47:55.129479
-- =================================================

IF OBJECT_ID('dbo.Tablajeria_CosteoDetalle', 'U') IS NOT NULL
    DROP TABLE dbo.Tablajeria_CosteoDetalle;
GO

CREATE TABLE dbo.Tablajeria_CosteoDetalle (
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
    [EsInventariable] BIT NULL DEFAULT ((1))
);
GO

CREATE INDEX [IX_CosteoDetalle_CosteoID] ON dbo.Tablajeria_CosteoDetalle (CosteoID);
ALTER TABLE dbo.Tablajeria_CosteoDetalle ADD CONSTRAINT [PK__Tablajer__6E19D6FA9AD060EA] PRIMARY KEY (DetalleID);
GO

-- =================================================
-- Tabla: Tablajeria_CosteoProduccion
-- Exportado: 2026-06-03T06:47:55.368367
-- =================================================

IF OBJECT_ID('dbo.Tablajeria_CosteoProduccion', 'U') IS NOT NULL
    DROP TABLE dbo.Tablajeria_CosteoProduccion;
GO

CREATE TABLE dbo.Tablajeria_CosteoProduccion (
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
    [EsEstimado] BIT NULL DEFAULT ((0))
);
GO

CREATE INDEX [IX_Costeo_OrdenID] ON dbo.Tablajeria_CosteoProduccion (OrdenID);
ALTER TABLE dbo.Tablajeria_CosteoProduccion ADD CONSTRAINT [PK__Tablajer__21CB371A350ECE24] PRIMARY KEY (CosteoID);
GO

-- =================================================
-- Tabla: Tablajeria_MovimientosInventario
-- Exportado: 2026-06-03T06:47:55.607482
-- =================================================

IF OBJECT_ID('dbo.Tablajeria_MovimientosInventario', 'U') IS NOT NULL
    DROP TABLE dbo.Tablajeria_MovimientosInventario;
GO

CREATE TABLE dbo.Tablajeria_MovimientosInventario (
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
    [ErrorSincronizacion] VARCHAR(500) NULL
);
GO

CREATE INDEX [IX_MovInv_OrdenID] ON dbo.Tablajeria_MovimientosInventario (OrdenID);
ALTER TABLE dbo.Tablajeria_MovimientosInventario ADD CONSTRAINT [PK__Tablajer__BF923FCCE9F88D43] PRIMARY KEY (MovimientoID);
GO

-- =================================================
-- Tabla: Tablajeria_PolizasContables
-- Exportado: 2026-06-03T06:47:55.846422
-- =================================================

IF OBJECT_ID('dbo.Tablajeria_PolizasContables', 'U') IS NOT NULL
    DROP TABLE dbo.Tablajeria_PolizasContables;
GO

CREATE TABLE dbo.Tablajeria_PolizasContables (
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
    [ErrorContabilizacion] VARCHAR(500) NULL
);
GO

CREATE INDEX [IX_Polizas_OrdenID] ON dbo.Tablajeria_PolizasContables (OrdenID);
ALTER TABLE dbo.Tablajeria_PolizasContables ADD CONSTRAINT [PK__Tablajer__25E0497437EFEEBE] PRIMARY KEY (PolizaID);
GO

-- =================================================
-- Tabla: Tablajeria_PolizasDetalle
-- Exportado: 2026-06-03T06:47:56.083288
-- =================================================

IF OBJECT_ID('dbo.Tablajeria_PolizasDetalle', 'U') IS NOT NULL
    DROP TABLE dbo.Tablajeria_PolizasDetalle;
GO

CREATE TABLE dbo.Tablajeria_PolizasDetalle (
    [AsientoID] VARCHAR(50) NOT NULL,
    [PolizaID] VARCHAR(50) NOT NULL,
    [NumeroLinea] INT NULL,
    [CuentaContable] VARCHAR(50) NULL,
    [NombreCuenta] VARCHAR(200) NULL,
    [Concepto] VARCHAR(300) NULL,
    [Debe] DECIMAL(18,2) NULL DEFAULT ((0)),
    [Haber] DECIMAL(18,2) NULL DEFAULT ((0)),
    [Referencia] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_PolizaDetalle_PolizaID] ON dbo.Tablajeria_PolizasDetalle (PolizaID);
ALTER TABLE dbo.Tablajeria_PolizasDetalle ADD CONSTRAINT [PK__Tablajer__04904D3048BBFC52] PRIMARY KEY (AsientoID);
GO

-- =================================================
-- Tabla: Tareas_Inventario
-- Exportado: 2026-06-03T06:47:56.320792
-- =================================================

IF OBJECT_ID('dbo.Tareas_Inventario', 'U') IS NOT NULL
    DROP TABLE dbo.Tareas_Inventario;
GO

CREATE TABLE dbo.Tareas_Inventario (
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
    [NotasJSON] NVARCHAR(MAX) NULL
);
GO

CREATE INDEX [IX_Tareas_EstadoTarea] ON dbo.Tareas_Inventario (EstadoTarea);
CREATE INDEX [IX_Tareas_FechaLimite] ON dbo.Tareas_Inventario (FechaLimite);
CREATE INDEX [IX_Tareas_UsuarioAsignadoID] ON dbo.Tareas_Inventario (UsuarioAsignadoID);
CREATE INDEX [IX_Tareas_WorkflowID] ON dbo.Tareas_Inventario (WorkflowID);
ALTER TABLE dbo.Tareas_Inventario ADD CONSTRAINT [PK__Tareas_I__3214EC2746F0D038] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ__Tareas_I__5CD83670746D84B5] ON dbo.Tareas_Inventario (TareaID);
GO

-- =================================================
-- Tabla: Unidades_Negocio
-- Exportado: 2026-06-03T06:47:56.528655
-- =================================================

IF OBJECT_ID('dbo.Unidades_Negocio', 'U') IS NOT NULL
    DROP TABLE dbo.Unidades_Negocio;
GO

CREATE TABLE dbo.Unidades_Negocio (
    [id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [nombre] NVARCHAR(100) NOT NULL,
    [codigo] NVARCHAR(50) NOT NULL,
    [server_id] NVARCHAR(100) NOT NULL,
    [sucursal_origen_id] NVARCHAR(50) NULL,
    [system_type] NVARCHAR(50) NOT NULL DEFAULT ('SoftRestaurant'),
    [activo] BIT NULL DEFAULT ((1)),
    [orden] INT NULL DEFAULT ((0)),
    [created_at] DATETIME NULL DEFAULT (getdate()),
    [updated_at] DATETIME NULL DEFAULT (getdate())
);
GO

CREATE INDEX [IX_Unidades_Codigo] ON dbo.Unidades_Negocio (codigo);
CREATE INDEX [IX_Unidades_ServerID] ON dbo.Unidades_Negocio (server_id);
ALTER TABLE dbo.Unidades_Negocio ADD CONSTRAINT [PK__Unidades__3213E83FD5638C07] PRIMARY KEY (id);
CREATE UNIQUE INDEX [UQ_Unidades_Server_Sucursal] ON dbo.Unidades_Negocio (server_id, sucursal_origen_id);
GO

-- =================================================
-- Tabla: Usuario_Acciones
-- Exportado: 2026-06-03T06:47:56.767054
-- =================================================

IF OBJECT_ID('dbo.Usuario_Acciones', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_Acciones;
GO

CREATE TABLE dbo.Usuario_Acciones (
    [AccionID] SMALLINT NOT NULL,
    [CodigoAccion] VARCHAR(30) NOT NULL,
    [NombreAccion] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [EsAutorizable] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Usuario_Acciones ADD CONSTRAINT [PK_Usuario_Acciones] PRIMARY KEY (AccionID);
CREATE UNIQUE INDEX [UQ_Usuario_Acciones_CodigoAccion] ON dbo.Usuario_Acciones (CodigoAccion);
CREATE UNIQUE INDEX [UQ_Usuario_Acciones_NombreAccion] ON dbo.Usuario_Acciones (NombreAccion);
GO

-- =================================================
-- Tabla: Usuario_AlmacenesAsignacion
-- Exportado: 2026-06-03T06:47:57.009071
-- =================================================

IF OBJECT_ID('dbo.Usuario_AlmacenesAsignacion', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_AlmacenesAsignacion;
GO

CREATE TABLE dbo.Usuario_AlmacenesAsignacion (
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
    [Observaciones] NVARCHAR(500) NULL
);
GO

CREATE INDEX [IX_UsuarioAlmacenes_Servidor] ON dbo.Usuario_AlmacenesAsignacion (ServidorID);
CREATE INDEX [IX_UsuarioAlmacenes_Usuario] ON dbo.Usuario_AlmacenesAsignacion (UsuarioID);
ALTER TABLE dbo.Usuario_AlmacenesAsignacion ADD CONSTRAINT [PK__Usuario___D82B5BB7DB86A685] PRIMARY KEY (AsignacionID);
CREATE UNIQUE INDEX [UQ_UsuarioAlmacenes_Unique] ON dbo.Usuario_AlmacenesAsignacion (UsuarioID, ServidorID, AlmacenCodigo);
GO

-- =================================================
-- Tabla: Usuario_Autorizaciones
-- Exportado: 2026-06-03T06:47:57.250297
-- =================================================

IF OBJECT_ID('dbo.Usuario_Autorizaciones', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_Autorizaciones;
GO

CREATE TABLE dbo.Usuario_Autorizaciones (
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
    [CreatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_Usuario_Autorizaciones_EntidadNombre_EntidadID] ON dbo.Usuario_Autorizaciones (EntidadNombre, EntidadID);
CREATE INDEX [IX_Usuario_Autorizaciones_TipoAutorizacionID_Estatus] ON dbo.Usuario_Autorizaciones (TipoAutorizacionID, EstatusAutorizacion);
ALTER TABLE dbo.Usuario_Autorizaciones ADD CONSTRAINT [PK_Usuario_Autorizaciones] PRIMARY KEY (AutorizacionID);
CREATE UNIQUE INDEX [UQ_Usuario_Autorizaciones_FolioAutorizacion] ON dbo.Usuario_Autorizaciones (FolioAutorizacion);
GO

-- =================================================
-- Tabla: Usuario_AutorizacionesDetalle
-- Exportado: 2026-06-03T06:47:57.487090
-- =================================================

IF OBJECT_ID('dbo.Usuario_AutorizacionesDetalle', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_AutorizacionesDetalle;
GO

CREATE TABLE dbo.Usuario_AutorizacionesDetalle (
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
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

CREATE INDEX [IX_Usuario_AutorizacionesDetalle_AutorizacionID] ON dbo.Usuario_AutorizacionesDetalle (AutorizacionID);
ALTER TABLE dbo.Usuario_AutorizacionesDetalle ADD CONSTRAINT [PK_Usuario_AutorizacionesDetalle] PRIMARY KEY (AutorizacionDetalleID);
GO

-- =================================================
-- Tabla: Usuario_Catalogo
-- Exportado: 2026-06-03T06:47:57.693492
-- =================================================

IF OBJECT_ID('dbo.Usuario_Catalogo', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_Catalogo;
GO

CREATE TABLE dbo.Usuario_Catalogo (
    [UsuarioID] INT NOT NULL,
    [CodigoUsuario] VARCHAR(30) NOT NULL,
    [Username] VARCHAR(60) NOT NULL,
    [Email] VARCHAR(150) NOT NULL,
    [PasswordHash] VARBINARY NULL,
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
    [PublicUUID] UNIQUEIDENTIFIER NULL
);
GO

CREATE INDEX [IX_Usuario_Catalogo_Activo] ON dbo.Usuario_Catalogo (Activo);
CREATE INDEX [IX_Usuario_Catalogo_Bloqueado] ON dbo.Usuario_Catalogo (Bloqueado);
CREATE UNIQUE INDEX [IX_Usuario_MongoLegacyID] ON dbo.Usuario_Catalogo (MongoLegacyID);
CREATE UNIQUE INDEX [IX_Usuario_PublicUUID] ON dbo.Usuario_Catalogo (PublicUUID);
ALTER TABLE dbo.Usuario_Catalogo ADD CONSTRAINT [PK_Usuario_Catalogo] PRIMARY KEY (UsuarioID);
CREATE UNIQUE INDEX [UQ_Usuario_Catalogo_CodigoUsuario] ON dbo.Usuario_Catalogo (CodigoUsuario);
CREATE UNIQUE INDEX [UQ_Usuario_Catalogo_Email] ON dbo.Usuario_Catalogo (Email);
CREATE UNIQUE INDEX [UQ_Usuario_Catalogo_Username] ON dbo.Usuario_Catalogo (Username);
GO

-- =================================================
-- Tabla: Usuario_EmpresasAsignacion
-- Exportado: 2026-06-03T06:47:57.932378
-- =================================================

IF OBJECT_ID('dbo.Usuario_EmpresasAsignacion', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_EmpresasAsignacion;
GO

CREATE TABLE dbo.Usuario_EmpresasAsignacion (
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
    [UpdatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_UsuarioEmpresasAsignacion_Activo] ON dbo.Usuario_EmpresasAsignacion (Activo);
CREATE INDEX [IX_UsuarioEmpresasAsignacion_Empresa] ON dbo.Usuario_EmpresasAsignacion (EmpresaID);
CREATE INDEX [IX_UsuarioEmpresasAsignacion_Usuario] ON dbo.Usuario_EmpresasAsignacion (UsuarioID);
ALTER TABLE dbo.Usuario_EmpresasAsignacion ADD CONSTRAINT [PK_Usuario_EmpresasAsignacion] PRIMARY KEY (UsuarioEmpresaAsignacionID);
CREATE UNIQUE INDEX [UQ_UsuarioEmpresas_Activo] ON dbo.Usuario_EmpresasAsignacion (UsuarioID, EmpresaID, Activo);
GO

-- =================================================
-- Tabla: Usuario_LogAccesos
-- Exportado: 2026-06-03T06:47:58.171962
-- =================================================

IF OBJECT_ID('dbo.Usuario_LogAccesos', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_LogAccesos;
GO

CREATE TABLE dbo.Usuario_LogAccesos (
    [LogAccesoID] BIGINT NOT NULL,
    [UsuarioID] INT NULL,
    [SesionID] BIGINT NULL,
    [TipoEvento] VARCHAR(30) NOT NULL,
    [FechaEvento] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [IPOrigen] VARCHAR(64) NULL,
    [UserAgent] VARCHAR(500) NULL,
    [Resultado] VARCHAR(20) NOT NULL DEFAULT ('OK'),
    [Detalle] VARCHAR(1000) NULL
);
GO

CREATE INDEX [IX_Usuario_LogAccesos_UsuarioID_FechaEvento] ON dbo.Usuario_LogAccesos (UsuarioID, FechaEvento);
ALTER TABLE dbo.Usuario_LogAccesos ADD CONSTRAINT [PK_Usuario_LogAccesos] PRIMARY KEY (LogAccesoID);
GO

-- =================================================
-- Tabla: Usuario_LogActividades
-- Exportado: 2026-06-03T06:47:58.378516
-- =================================================

IF OBJECT_ID('dbo.Usuario_LogActividades', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_LogActividades;
GO

CREATE TABLE dbo.Usuario_LogActividades (
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
    [Criticidad] VARCHAR(20) NOT NULL DEFAULT ('MEDIA')
);
GO

CREATE INDEX [IX_Usuario_LogActividades_ModuloID_AccionID] ON dbo.Usuario_LogActividades (ModuloID, AccionID);
CREATE INDEX [IX_Usuario_LogActividades_UsuarioID_FechaActividad] ON dbo.Usuario_LogActividades (UsuarioID, FechaActividad);
ALTER TABLE dbo.Usuario_LogActividades ADD CONSTRAINT [PK_Usuario_LogActividades] PRIMARY KEY (LogActividadID);
GO

-- =================================================
-- Tabla: Usuario_LogRBACVerificacion
-- Exportado: 2026-06-03T06:47:58.617571
-- =================================================

IF OBJECT_ID('dbo.Usuario_LogRBACVerificacion', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_LogRBACVerificacion;
GO

CREATE TABLE dbo.Usuario_LogRBACVerificacion (
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
    [FechaVerificacion] DATETIME2 NOT NULL DEFAULT (getdate())
);
GO

CREATE INDEX [IX_LogRBAC_Fecha] ON dbo.Usuario_LogRBACVerificacion (FechaVerificacion);
CREATE INDEX [IX_LogRBAC_Resultado] ON dbo.Usuario_LogRBACVerificacion (Resultado, FechaVerificacion);
CREATE INDEX [IX_LogRBAC_Usuario] ON dbo.Usuario_LogRBACVerificacion (UsuarioID);
ALTER TABLE dbo.Usuario_LogRBACVerificacion ADD CONSTRAINT [PK__Usuario___5E5499A8A7245C33] PRIMARY KEY (LogID);
GO

-- =================================================
-- Tabla: Usuario_LogRecuperacion
-- Exportado: 2026-06-03T06:47:59.116178
-- =================================================

IF OBJECT_ID('dbo.Usuario_LogRecuperacion', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_LogRecuperacion;
GO

CREATE TABLE dbo.Usuario_LogRecuperacion (
    [LogRecuperacionID] BIGINT NOT NULL,
    [Evento] VARCHAR(50) NOT NULL,
    [Email] VARCHAR(255) NOT NULL,
    [IPOrigen] VARCHAR(45) NULL,
    [UserAgent] VARCHAR(500) NULL,
    [Resultado] BIT NOT NULL,
    [Detalle] NVARCHAR(MAX) NULL,
    [FechaEvento] DATETIME2 NOT NULL DEFAULT (getutcdate())
);
GO

CREATE INDEX [IX_Usuario_LogRecuperacion_Email] ON dbo.Usuario_LogRecuperacion (Email, FechaEvento);
CREATE INDEX [IX_Usuario_LogRecuperacion_Evento] ON dbo.Usuario_LogRecuperacion (Evento, FechaEvento);
CREATE INDEX [IX_Usuario_LogRecuperacion_Fecha] ON dbo.Usuario_LogRecuperacion (FechaEvento);
ALTER TABLE dbo.Usuario_LogRecuperacion ADD CONSTRAINT [PK__Usuario___C1187B024240E8DF] PRIMARY KEY (LogRecuperacionID);
GO

-- =================================================
-- Tabla: Usuario_MatrizAutorizacion
-- Exportado: 2026-06-03T06:47:59.354524
-- =================================================

IF OBJECT_ID('dbo.Usuario_MatrizAutorizacion', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_MatrizAutorizacion;
GO

CREATE TABLE dbo.Usuario_MatrizAutorizacion (
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
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.Usuario_MatrizAutorizacion ADD CONSTRAINT [PK_Usuario_MatrizAutorizacion] PRIMARY KEY (MatrizAutorizacionID);
GO

-- =================================================
-- Tabla: Usuario_MigracionMongoTrace
-- Exportado: 2026-06-03T06:47:59.560276
-- =================================================

IF OBJECT_ID('dbo.Usuario_MigracionMongoTrace', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_MigracionMongoTrace;
GO

CREATE TABLE dbo.Usuario_MigracionMongoTrace (
    [TraceID] INT NOT NULL,
    [MongoID] VARCHAR(24) NOT NULL,
    [Email] VARCHAR(150) NOT NULL,
    [UsuarioID_SQL] INT NULL,
    [RolMongoDB] VARCHAR(50) NOT NULL,
    [ActivoMongoDB] BIT NOT NULL,
    [Clasificacion] VARCHAR(20) NOT NULL,
    [FechaMigracion] DATETIME2 NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL DEFAULT ('MIGRACION_FASE_A4')
);
GO

ALTER TABLE dbo.Usuario_MigracionMongoTrace ADD CONSTRAINT [PK__Usuario___70C9CD7CB59E9C23] PRIMARY KEY (TraceID);
CREATE UNIQUE INDEX [UQ_MigracionMongoTrace_Email] ON dbo.Usuario_MigracionMongoTrace (Email);
CREATE UNIQUE INDEX [UQ_MigracionMongoTrace_MongoID] ON dbo.Usuario_MigracionMongoTrace (MongoID);
GO

-- =================================================
-- Tabla: Usuario_Modulos
-- Exportado: 2026-06-03T06:47:59.799717
-- =================================================

IF OBJECT_ID('dbo.Usuario_Modulos', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_Modulos;
GO

CREATE TABLE dbo.Usuario_Modulos (
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
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.Usuario_Modulos ADD CONSTRAINT [PK_Usuario_Modulos] PRIMARY KEY (ModuloID);
CREATE UNIQUE INDEX [UQ_Usuario_Modulos_CodigoModulo] ON dbo.Usuario_Modulos (CodigoModulo);
GO

-- =================================================
-- Tabla: Usuario_PermisosRolModulo
-- Exportado: 2026-06-03T06:48:00.038959
-- =================================================

IF OBJECT_ID('dbo.Usuario_PermisosRolModulo', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_PermisosRolModulo;
GO

CREATE TABLE dbo.Usuario_PermisosRolModulo (
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
    [ModifiedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_Usuario_PermisosRolModulo_RolID_ModuloID] ON dbo.Usuario_PermisosRolModulo (RolID, ModuloID);
ALTER TABLE dbo.Usuario_PermisosRolModulo ADD CONSTRAINT [PK_Usuario_PermisosRolModulo] PRIMARY KEY (PermisoRolModuloID);
CREATE UNIQUE INDEX [UQ_Usuario_PermisosRolModulo] ON dbo.Usuario_PermisosRolModulo (RolID, ModuloID, AccionID);
GO

-- =================================================
-- Tabla: Usuario_PortalConfiguracion
-- Exportado: 2026-06-03T06:48:00.283652
-- =================================================

IF OBJECT_ID('dbo.Usuario_PortalConfiguracion', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_PortalConfiguracion;
GO

CREATE TABLE dbo.Usuario_PortalConfiguracion (
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
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.Usuario_PortalConfiguracion ADD CONSTRAINT [PK_Usuario_PortalConfiguracion] PRIMARY KEY (UsuarioPortalConfiguracionID);
CREATE UNIQUE INDEX [UQ_Usuario_PortalConfiguracion_Usuario] ON dbo.Usuario_PortalConfiguracion (UsuarioID);
GO

-- =================================================
-- Tabla: Usuario_RateLimitRecuperacion
-- Exportado: 2026-06-03T06:48:00.489543
-- =================================================

IF OBJECT_ID('dbo.Usuario_RateLimitRecuperacion', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_RateLimitRecuperacion;
GO

CREATE TABLE dbo.Usuario_RateLimitRecuperacion (
    [RateLimitID] BIGINT NOT NULL,
    [TipoLlave] VARCHAR(20) NOT NULL,
    [ValorLlave] VARCHAR(255) NOT NULL,
    [Contador] INT NOT NULL DEFAULT ((1)),
    [VentanaInicio] DATETIME2 NOT NULL DEFAULT (getutcdate()),
    [VentanaExpiracion] DATETIME2 NOT NULL,
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getutcdate()),
    [FechaModificacion] DATETIME2 NOT NULL DEFAULT (getutcdate())
);
GO

CREATE INDEX [IX_Usuario_RateLimitRecuperacion_Expiracion] ON dbo.Usuario_RateLimitRecuperacion (VentanaExpiracion);
ALTER TABLE dbo.Usuario_RateLimitRecuperacion ADD CONSTRAINT [PK__Usuario___0B5819A563F4BC1B] PRIMARY KEY (RateLimitID);
CREATE UNIQUE INDEX [UQ_Usuario_RateLimitRecuperacion_Llave] ON dbo.Usuario_RateLimitRecuperacion (TipoLlave, ValorLlave);
GO

-- =================================================
-- Tabla: Usuario_Roles
-- Exportado: 2026-06-03T06:48:00.727310
-- =================================================

IF OBJECT_ID('dbo.Usuario_Roles', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_Roles;
GO

CREATE TABLE dbo.Usuario_Roles (
    [RolID] INT NOT NULL,
    [CodigoRol] VARCHAR(30) NOT NULL,
    [NombreRol] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [EsRolSistema] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL,
    [NivelJerarquia] INT NOT NULL DEFAULT ((0))
);
GO

ALTER TABLE dbo.Usuario_Roles ADD CONSTRAINT [PK_Usuario_Roles] PRIMARY KEY (RolID);
CREATE UNIQUE INDEX [UQ_Usuario_Roles_CodigoRol] ON dbo.Usuario_Roles (CodigoRol);
CREATE UNIQUE INDEX [UQ_Usuario_Roles_NombreRol] ON dbo.Usuario_Roles (NombreRol);
GO

-- =================================================
-- Tabla: Usuario_RolesAsignacion
-- Exportado: 2026-06-03T06:48:00.965182
-- =================================================

IF OBJECT_ID('dbo.Usuario_RolesAsignacion', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_RolesAsignacion;
GO

CREATE TABLE dbo.Usuario_RolesAsignacion (
    [UsuarioRolAsignacionID] BIGINT NOT NULL,
    [UsuarioID] INT NOT NULL,
    [RolID] INT NOT NULL,
    [EsPrincipal] BIT NOT NULL DEFAULT ((0)),
    [FechaInicio] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaFin] DATETIME2 NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [CreatedAt] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [CreatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_Usuario_RolesAsignacion_RolID] ON dbo.Usuario_RolesAsignacion (RolID);
CREATE INDEX [IX_Usuario_RolesAsignacion_UsuarioID] ON dbo.Usuario_RolesAsignacion (UsuarioID);
ALTER TABLE dbo.Usuario_RolesAsignacion ADD CONSTRAINT [PK_Usuario_RolesAsignacion] PRIMARY KEY (UsuarioRolAsignacionID);
CREATE UNIQUE INDEX [UQ_Usuario_RolesAsignacion] ON dbo.Usuario_RolesAsignacion (UsuarioID, RolID, FechaInicio);
GO

-- =================================================
-- Tabla: Usuario_ServidoresAsignacion
-- Exportado: 2026-06-03T06:48:01.202982
-- =================================================

IF OBJECT_ID('dbo.Usuario_ServidoresAsignacion', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_ServidoresAsignacion;
GO

CREATE TABLE dbo.Usuario_ServidoresAsignacion (
    [AsignacionID] INT NOT NULL,
    [UsuarioID] INT NOT NULL,
    [ServidorID] UNIQUEIDENTIFIER NOT NULL,
    [LegacyMongoValue] VARCHAR(100) NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaCreacion] DATETIME2 NOT NULL DEFAULT (getdate()),
    [FechaModificacion] DATETIME2 NULL,
    [CreadoPor] INT NULL,
    [ModificadoPor] INT NULL,
    [Observaciones] NVARCHAR(500) NULL
);
GO

CREATE INDEX [IX_UsuarioServidores_Servidor] ON dbo.Usuario_ServidoresAsignacion (ServidorID);
CREATE INDEX [IX_UsuarioServidores_Usuario] ON dbo.Usuario_ServidoresAsignacion (UsuarioID);
ALTER TABLE dbo.Usuario_ServidoresAsignacion ADD CONSTRAINT [PK__Usuario___D82B5BB73457616E] PRIMARY KEY (AsignacionID);
CREATE UNIQUE INDEX [UQ_UsuarioServidores_Unique] ON dbo.Usuario_ServidoresAsignacion (UsuarioID, ServidorID);
GO

-- =================================================
-- Tabla: Usuario_Sesiones
-- Exportado: 2026-06-03T06:48:01.444715
-- =================================================

IF OBJECT_ID('dbo.Usuario_Sesiones', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_Sesiones;
GO

CREATE TABLE dbo.Usuario_Sesiones (
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
    [CerradaPorSistema] BIT NOT NULL DEFAULT ((0))
);
GO

CREATE INDEX [IX_Usuario_Sesiones_UsuarioID_FechaInicio] ON dbo.Usuario_Sesiones (UsuarioID, FechaInicio);
ALTER TABLE dbo.Usuario_Sesiones ADD CONSTRAINT [PK_Usuario_Sesiones] PRIMARY KEY (SesionID);
GO

-- =================================================
-- Tabla: Usuario_SucursalesAsignacion
-- Exportado: 2026-06-03T06:48:01.651270
-- =================================================

IF OBJECT_ID('dbo.Usuario_SucursalesAsignacion', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_SucursalesAsignacion;
GO

CREATE TABLE dbo.Usuario_SucursalesAsignacion (
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
    [Observaciones] NVARCHAR(500) NULL
);
GO

CREATE INDEX [IX_UsuarioSucursales_Servidor] ON dbo.Usuario_SucursalesAsignacion (ServidorID);
CREATE INDEX [IX_UsuarioSucursales_Usuario] ON dbo.Usuario_SucursalesAsignacion (UsuarioID);
ALTER TABLE dbo.Usuario_SucursalesAsignacion ADD CONSTRAINT [PK__Usuario___D82B5BB7E981918D] PRIMARY KEY (AsignacionID);
CREATE UNIQUE INDEX [UQ_UsuarioSucursales_Unique] ON dbo.Usuario_SucursalesAsignacion (UsuarioID, ServidorID, SucursalCodigo);
GO

-- =================================================
-- Tabla: Usuario_TiposAutorizacion
-- Exportado: 2026-06-03T06:48:01.894121
-- =================================================

IF OBJECT_ID('dbo.Usuario_TiposAutorizacion', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_TiposAutorizacion;
GO

CREATE TABLE dbo.Usuario_TiposAutorizacion (
    [TipoAutorizacionID] SMALLINT NOT NULL,
    [CodigoTipoAutorizacion] VARCHAR(30) NOT NULL,
    [NombreTipoAutorizacion] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [ModuloID] INT NULL,
    [AccionID] SMALLINT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Usuario_TiposAutorizacion ADD CONSTRAINT [PK_Usuario_TiposAutorizacion] PRIMARY KEY (TipoAutorizacionID);
CREATE UNIQUE INDEX [UQ_Usuario_TiposAutorizacion_Codigo] ON dbo.Usuario_TiposAutorizacion (CodigoTipoAutorizacion);
GO

-- =================================================
-- Tabla: Usuario_TokensRecuperacion
-- Exportado: 2026-06-03T06:48:02.130916
-- =================================================

IF OBJECT_ID('dbo.Usuario_TokensRecuperacion', 'U') IS NOT NULL
    DROP TABLE dbo.Usuario_TokensRecuperacion;
GO

CREATE TABLE dbo.Usuario_TokensRecuperacion (
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
    [UserAgentUso] VARCHAR(500) NULL
);
GO

CREATE INDEX [IX_TokensRecuperacion_Email] ON dbo.Usuario_TokensRecuperacion (Email);
CREATE INDEX [IX_TokensRecuperacion_Expiracion] ON dbo.Usuario_TokensRecuperacion (FechaExpiracion);
CREATE INDEX [IX_TokensRecuperacion_Usuario] ON dbo.Usuario_TokensRecuperacion (UsuarioID);
ALTER TABLE dbo.Usuario_TokensRecuperacion ADD CONSTRAINT [PK_Usuario_TokensRecuperacion] PRIMARY KEY (TokenRecuperacionID);
CREATE UNIQUE INDEX [UQ_TokensRecuperacion_Hash] ON dbo.Usuario_TokensRecuperacion (TokenHash);
GO

-- =================================================
-- Tabla: Venta_Cat_EstatusRemision
-- Exportado: 2026-06-03T06:48:02.368048
-- =================================================

IF OBJECT_ID('dbo.Venta_Cat_EstatusRemision', 'U') IS NOT NULL
    DROP TABLE dbo.Venta_Cat_EstatusRemision;
GO

CREATE TABLE dbo.Venta_Cat_EstatusRemision (
    [EstatusID] INT NOT NULL,
    [Nombre] NVARCHAR(50) NOT NULL,
    [Descripcion] NVARCHAR(200) NULL,
    [Color] NVARCHAR(20) NULL,
    [Orden] INT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Venta_Cat_EstatusRemision ADD CONSTRAINT [PK_Venta_Cat_EstatusRemision] PRIMARY KEY (EstatusID);
GO

-- =================================================
-- Tabla: Venta_CondicionesPago
-- Exportado: 2026-06-03T06:48:02.605662
-- =================================================

IF OBJECT_ID('dbo.Venta_CondicionesPago', 'U') IS NOT NULL
    DROP TABLE dbo.Venta_CondicionesPago;
GO

CREATE TABLE dbo.Venta_CondicionesPago (
    [CondicionPagoID] SMALLINT NOT NULL,
    [CodigoCondicionPago] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [DiasCredito] SMALLINT NOT NULL DEFAULT ((0)),
    [RequiereCredito] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Venta_CondicionesPago ADD CONSTRAINT [PK_Venta_CondicionesPago] PRIMARY KEY (CondicionPagoID);
CREATE UNIQUE INDEX [UQ_Venta_CondicionesPago_Codigo] ON dbo.Venta_CondicionesPago (CodigoCondicionPago);
GO

-- =================================================
-- Tabla: Venta_Cotizaciones
-- Exportado: 2026-06-03T06:48:02.844548
-- =================================================

IF OBJECT_ID('dbo.Venta_Cotizaciones', 'U') IS NOT NULL
    DROP TABLE dbo.Venta_Cotizaciones;
GO

CREATE TABLE dbo.Venta_Cotizaciones (
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
    [EstatusComercial] NVARCHAR(20) NULL
);
GO

CREATE INDEX [IX_Venta_Cotizaciones_ClienteID_FechaCotizacion] ON dbo.Venta_Cotizaciones (ClienteID, FechaCotizacion);
CREATE INDEX [IX_Venta_Cotizaciones_CRM_Cuenta] ON dbo.Venta_Cotizaciones (CRM_CuentaID);
CREATE INDEX [IX_Venta_Cotizaciones_CRM_Oportunidad] ON dbo.Venta_Cotizaciones (CRM_OportunidadID);
CREATE INDEX [IX_Venta_Cotizaciones_EstatusCotizacionID] ON dbo.Venta_Cotizaciones (EstatusCotizacionID);
ALTER TABLE dbo.Venta_Cotizaciones ADD CONSTRAINT [PK_Venta_Cotizaciones] PRIMARY KEY (CotizacionID);
CREATE UNIQUE INDEX [UQ_Venta_Cotizaciones_FolioCotizacion] ON dbo.Venta_Cotizaciones (FolioCotizacion);
GO

-- =================================================
-- Tabla: Venta_CotizacionesDetalle
-- Exportado: 2026-06-03T06:48:03.051107
-- =================================================

IF OBJECT_ID('dbo.Venta_CotizacionesDetalle', 'U') IS NOT NULL
    DROP TABLE dbo.Venta_CotizacionesDetalle;
GO

CREATE TABLE dbo.Venta_CotizacionesDetalle (
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
    [CreatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_Venta_CotizacionesDetalle_CotizacionID] ON dbo.Venta_CotizacionesDetalle (CotizacionID);
CREATE INDEX [IX_Venta_CotizacionesDetalle_ProductoID] ON dbo.Venta_CotizacionesDetalle (ProductoID);
ALTER TABLE dbo.Venta_CotizacionesDetalle ADD CONSTRAINT [PK_Venta_CotizacionesDetalle] PRIMARY KEY (DetalleCotizacionID);
CREATE UNIQUE INDEX [UQ_Venta_CotizacionesDetalle_Cotizacion_Renglon] ON dbo.Venta_CotizacionesDetalle (CotizacionID, Renglon);
GO

-- =================================================
-- Tabla: Venta_CotizacionesEstatus
-- Exportado: 2026-06-03T06:48:03.259614
-- =================================================

IF OBJECT_ID('dbo.Venta_CotizacionesEstatus', 'U') IS NOT NULL
    DROP TABLE dbo.Venta_CotizacionesEstatus;
GO

CREATE TABLE dbo.Venta_CotizacionesEstatus (
    [EstatusCotizacionID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Venta_CotizacionesEstatus ADD CONSTRAINT [PK_Venta_CotizacionesEstatus] PRIMARY KEY (EstatusCotizacionID);
CREATE UNIQUE INDEX [UQ_Venta_CotizacionesEstatus_Descripcion] ON dbo.Venta_CotizacionesEstatus (Descripcion);
GO

-- =================================================
-- Tabla: Venta_Detalle
-- Exportado: 2026-06-03T06:48:03.496642
-- =================================================

IF OBJECT_ID('dbo.Venta_Detalle', 'U') IS NOT NULL
    DROP TABLE dbo.Venta_Detalle;
GO

CREATE TABLE dbo.Venta_Detalle (
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
    [CreatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_Venta_Detalle_ProductoID] ON dbo.Venta_Detalle (ProductoID);
CREATE INDEX [IX_Venta_Detalle_VentaID] ON dbo.Venta_Detalle (VentaID);
ALTER TABLE dbo.Venta_Detalle ADD CONSTRAINT [PK_Venta_Detalle] PRIMARY KEY (DetalleVentaID);
CREATE UNIQUE INDEX [UQ_Venta_Detalle_Venta_Renglon] ON dbo.Venta_Detalle (VentaID, Renglon);
GO

-- =================================================
-- Tabla: Venta_Encabezado
-- Exportado: 2026-06-03T06:48:03.703141
-- =================================================

IF OBJECT_ID('dbo.Venta_Encabezado', 'U') IS NOT NULL
    DROP TABLE dbo.Venta_Encabezado;
GO

CREATE TABLE dbo.Venta_Encabezado (
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
    [ModifiedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_Venta_Encabezado_ClienteID_FechaVenta] ON dbo.Venta_Encabezado (ClienteID, FechaVenta);
CREATE INDEX [IX_Venta_Encabezado_EstatusVentaID] ON dbo.Venta_Encabezado (EstatusVentaID);
CREATE INDEX [IX_Venta_Encabezado_FechaVenta] ON dbo.Venta_Encabezado (FechaVenta);
ALTER TABLE dbo.Venta_Encabezado ADD CONSTRAINT [PK_Venta_Encabezado] PRIMARY KEY (VentaID);
CREATE UNIQUE INDEX [UQ_Venta_Encabezado_Folio] ON dbo.Venta_Encabezado (Folio);
GO

-- =================================================
-- Tabla: Venta_Estatus
-- Exportado: 2026-06-03T06:48:03.909334
-- =================================================

IF OBJECT_ID('dbo.Venta_Estatus', 'U') IS NOT NULL
    DROP TABLE dbo.Venta_Estatus;
GO

CREATE TABLE dbo.Venta_Estatus (
    [EstatusVentaID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Venta_Estatus ADD CONSTRAINT [PK_Venta_Estatus] PRIMARY KEY (EstatusVentaID);
GO

-- =================================================
-- Tabla: Venta_FormaPago
-- Exportado: 2026-06-03T06:48:04.146946
-- =================================================

IF OBJECT_ID('dbo.Venta_FormaPago', 'U') IS NOT NULL
    DROP TABLE dbo.Venta_FormaPago;
GO

CREATE TABLE dbo.Venta_FormaPago (
    [FormaPagoID] SMALLINT NOT NULL,
    [ClaveFormaPago] VARCHAR(10) NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [RequiereReferencia] BIT NOT NULL DEFAULT ((0)),
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Venta_FormaPago ADD CONSTRAINT [PK_Venta_FormaPago] PRIMARY KEY (FormaPagoID);
CREATE UNIQUE INDEX [UQ_Venta_FormaPago_Descripcion] ON dbo.Venta_FormaPago (Descripcion);
GO

-- =================================================
-- Tabla: Venta_ListasPrecios
-- Exportado: 2026-06-03T06:48:04.383412
-- =================================================

IF OBJECT_ID('dbo.Venta_ListasPrecios', 'U') IS NOT NULL
    DROP TABLE dbo.Venta_ListasPrecios;
GO

CREATE TABLE dbo.Venta_ListasPrecios (
    [ListaPrecioID] INT NOT NULL,
    [CodigoListaPrecio] VARCHAR(20) NOT NULL,
    [NombreListaPrecio] VARCHAR(100) NOT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [EsDefault] BIT NOT NULL DEFAULT ((0)),
    [FechaInicio] DATE NULL,
    [FechaFin] DATE NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime()),
    [FechaModificacion] DATETIME2 NULL
);
GO

ALTER TABLE dbo.Venta_ListasPrecios ADD CONSTRAINT [PK_Venta_ListasPrecios] PRIMARY KEY (ListaPrecioID);
CREATE UNIQUE INDEX [UQ_Venta_ListasPrecios_Codigo] ON dbo.Venta_ListasPrecios (CodigoListaPrecio);
CREATE UNIQUE INDEX [UQ_Venta_ListasPrecios_Nombre] ON dbo.Venta_ListasPrecios (NombreListaPrecio);
GO

-- =================================================
-- Tabla: Venta_ListasPreciosDetalle
-- Exportado: 2026-06-03T06:48:04.633727
-- =================================================

IF OBJECT_ID('dbo.Venta_ListasPreciosDetalle', 'U') IS NOT NULL
    DROP TABLE dbo.Venta_ListasPreciosDetalle;
GO

CREATE TABLE dbo.Venta_ListasPreciosDetalle (
    [ListaPrecioDetalleID] BIGINT NOT NULL,
    [ListaPrecioID] INT NOT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [Precio] DECIMAL(18,2) NOT NULL,
    [DescuentoPorcentaje] DECIMAL(9,4) NOT NULL DEFAULT ((0)),
    [FechaInicio] DATE NULL,
    [FechaFin] DATE NULL,
    [Activo] BIT NOT NULL DEFAULT ((1)),
    [FechaAlta] DATETIME2 NOT NULL DEFAULT (sysdatetime())
);
GO

CREATE INDEX [IX_Venta_ListasPreciosDetalle_ListaPrecioID] ON dbo.Venta_ListasPreciosDetalle (ListaPrecioID);
ALTER TABLE dbo.Venta_ListasPreciosDetalle ADD CONSTRAINT [PK_Venta_ListasPreciosDetalle] PRIMARY KEY (ListaPrecioDetalleID);
CREATE UNIQUE INDEX [UQ_Venta_ListasPreciosDetalle] ON dbo.Venta_ListasPreciosDetalle (ListaPrecioID, ProductoID, PresentacionProductoID);
GO

-- =================================================
-- Tabla: Venta_Pagos
-- Exportado: 2026-06-03T06:48:04.840615
-- =================================================

IF OBJECT_ID('dbo.Venta_Pagos', 'U') IS NOT NULL
    DROP TABLE dbo.Venta_Pagos;
GO

CREATE TABLE dbo.Venta_Pagos (
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
    [CreatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_Venta_Pagos_VentaID] ON dbo.Venta_Pagos (VentaID);
ALTER TABLE dbo.Venta_Pagos ADD CONSTRAINT [PK_Venta_Pagos] PRIMARY KEY (PagoVentaID);
GO

-- =================================================
-- Tabla: Venta_Pedidos
-- Exportado: 2026-06-03T06:48:05.046288
-- =================================================

IF OBJECT_ID('dbo.Venta_Pedidos', 'U') IS NOT NULL
    DROP TABLE dbo.Venta_Pedidos;
GO

CREATE TABLE dbo.Venta_Pedidos (
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
    [EstatusComercial] NVARCHAR(20) NULL
);
GO

CREATE INDEX [IX_Venta_Pedidos_ClienteID_FechaPedido] ON dbo.Venta_Pedidos (ClienteID, FechaPedido);
CREATE INDEX [IX_Venta_Pedidos_CotizacionID] ON dbo.Venta_Pedidos (CotizacionID);
CREATE INDEX [IX_Venta_Pedidos_CRM_Cuenta] ON dbo.Venta_Pedidos (CRM_CuentaID);
CREATE INDEX [IX_Venta_Pedidos_CRM_Oportunidad] ON dbo.Venta_Pedidos (CRM_OportunidadID);
CREATE INDEX [IX_Venta_Pedidos_EstatusPedidoID] ON dbo.Venta_Pedidos (EstatusPedidoID);
ALTER TABLE dbo.Venta_Pedidos ADD CONSTRAINT [PK_Venta_Pedidos] PRIMARY KEY (PedidoID);
CREATE UNIQUE INDEX [UQ_Venta_Pedidos_FolioPedido] ON dbo.Venta_Pedidos (FolioPedido);
GO

-- =================================================
-- Tabla: Venta_PedidosDetalle
-- Exportado: 2026-06-03T06:48:05.252723
-- =================================================

IF OBJECT_ID('dbo.Venta_PedidosDetalle', 'U') IS NOT NULL
    DROP TABLE dbo.Venta_PedidosDetalle;
GO

CREATE TABLE dbo.Venta_PedidosDetalle (
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
    [CreatedBy] VARCHAR(100) NULL
);
GO

CREATE INDEX [IX_Venta_PedidosDetalle_PedidoID] ON dbo.Venta_PedidosDetalle (PedidoID);
CREATE INDEX [IX_Venta_PedidosDetalle_ProductoID] ON dbo.Venta_PedidosDetalle (ProductoID);
ALTER TABLE dbo.Venta_PedidosDetalle ADD CONSTRAINT [PK_Venta_PedidosDetalle] PRIMARY KEY (DetallePedidoID);
CREATE UNIQUE INDEX [UQ_Venta_PedidosDetalle_Pedido_Renglon] ON dbo.Venta_PedidosDetalle (PedidoID, Renglon);
GO

-- =================================================
-- Tabla: Venta_PedidosEstatus
-- Exportado: 2026-06-03T06:48:05.458687
-- =================================================

IF OBJECT_ID('dbo.Venta_PedidosEstatus', 'U') IS NOT NULL
    DROP TABLE dbo.Venta_PedidosEstatus;
GO

CREATE TABLE dbo.Venta_PedidosEstatus (
    [EstatusPedidoID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL DEFAULT ((1))
);
GO

ALTER TABLE dbo.Venta_PedidosEstatus ADD CONSTRAINT [PK_Venta_PedidosEstatus] PRIMARY KEY (EstatusPedidoID);
CREATE UNIQUE INDEX [UQ_Venta_PedidosEstatus_Descripcion] ON dbo.Venta_PedidosEstatus (Descripcion);
GO

-- =================================================
-- Tabla: Venta_Remisiones
-- Exportado: 2026-06-03T06:48:05.696417
-- =================================================

IF OBJECT_ID('dbo.Venta_Remisiones', 'U') IS NOT NULL
    DROP TABLE dbo.Venta_Remisiones;
GO

CREATE TABLE dbo.Venta_Remisiones (
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
    [UpdatedAt] DATETIME2 NULL
);
GO

CREATE INDEX [IX_Venta_Remisiones_Cliente] ON dbo.Venta_Remisiones (ClienteID);
CREATE INDEX [IX_Venta_Remisiones_Empresa] ON dbo.Venta_Remisiones (EmpresaID);
CREATE INDEX [IX_Venta_Remisiones_Estatus] ON dbo.Venta_Remisiones (EstatusRemisionID);
CREATE INDEX [IX_Venta_Remisiones_Fecha] ON dbo.Venta_Remisiones (FechaRemision);
CREATE UNIQUE INDEX [IX_Venta_Remisiones_Folio] ON dbo.Venta_Remisiones (EmpresaID, FolioRemision);
CREATE INDEX [IX_Venta_Remisiones_Pedido] ON dbo.Venta_Remisiones (PedidoID);
ALTER TABLE dbo.Venta_Remisiones ADD CONSTRAINT [PK_Venta_Remisiones] PRIMARY KEY (RemisionID);
GO

-- =================================================
-- Tabla: Venta_RemisionesDetalle
-- Exportado: 2026-06-03T06:48:05.902304
-- =================================================

IF OBJECT_ID('dbo.Venta_RemisionesDetalle', 'U') IS NOT NULL
    DROP TABLE dbo.Venta_RemisionesDetalle;
GO

CREATE TABLE dbo.Venta_RemisionesDetalle (
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
    [OrdenLinea] INT NOT NULL DEFAULT ((0))
);
GO

CREATE INDEX [IX_Venta_RemisionesDetalle_Producto] ON dbo.Venta_RemisionesDetalle (ProductoID);
CREATE INDEX [IX_Venta_RemisionesDetalle_Remision] ON dbo.Venta_RemisionesDetalle (RemisionID);
ALTER TABLE dbo.Venta_RemisionesDetalle ADD CONSTRAINT [PK_Venta_RemisionesDetalle] PRIMARY KEY (DetalleID);
GO

-- =================================================
-- Tabla: Venta_RemisionesHistorial
-- Exportado: 2026-06-03T06:48:06.108115
-- =================================================

IF OBJECT_ID('dbo.Venta_RemisionesHistorial', 'U') IS NOT NULL
    DROP TABLE dbo.Venta_RemisionesHistorial;
GO

CREATE TABLE dbo.Venta_RemisionesHistorial (
    [HistorialID] BIGINT NOT NULL,
    [RemisionID] BIGINT NOT NULL,
    [EstatusAnteriorID] INT NULL,
    [EstatusNuevoID] INT NOT NULL,
    [Comentario] NVARCHAR(500) NULL,
    [CambiadoPorUserID] UNIQUEIDENTIFIER NOT NULL,
    [FechaCambio] DATETIME2 NOT NULL DEFAULT (getutcdate())
);
GO

CREATE INDEX [IX_Venta_RemisionesHistorial_Remision] ON dbo.Venta_RemisionesHistorial (RemisionID);
ALTER TABLE dbo.Venta_RemisionesHistorial ADD CONSTRAINT [PK_Venta_RemisionesHistorial] PRIMARY KEY (HistorialID);
GO

-- =================================================
-- Tabla: Workflow_DecisionesAuditoria
-- Exportado: 2026-06-03T06:48:06.312173
-- =================================================

IF OBJECT_ID('dbo.Workflow_DecisionesAuditoria', 'U') IS NOT NULL
    DROP TABLE dbo.Workflow_DecisionesAuditoria;
GO

CREATE TABLE dbo.Workflow_DecisionesAuditoria (
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
    [MetadatosJSON] NVARCHAR(MAX) NULL
);
GO

CREATE INDEX [IX_WfDec_FechaDecision] ON dbo.Workflow_DecisionesAuditoria (FechaDecision);
CREATE INDEX [IX_WfDec_WorkflowID] ON dbo.Workflow_DecisionesAuditoria (WorkflowID);
ALTER TABLE dbo.Workflow_DecisionesAuditoria ADD CONSTRAINT [PK__Workflow__3214EC2701C5C525] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ_WfDec_DecisionID] ON dbo.Workflow_DecisionesAuditoria (DecisionID);
GO

-- =================================================
-- Tabla: Workflow_DetalleDiferencias
-- Exportado: 2026-06-03T06:48:06.518121
-- =================================================

IF OBJECT_ID('dbo.Workflow_DetalleDiferencias', 'U') IS NOT NULL
    DROP TABLE dbo.Workflow_DetalleDiferencias;
GO

CREATE TABLE dbo.Workflow_DetalleDiferencias (
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
    [FechaCreacion] DATETIME2 NULL DEFAULT (getutcdate())
);
GO

CREATE INDEX [IX_Detalle_CodigoProducto] ON dbo.Workflow_DetalleDiferencias (CodigoProducto);
CREATE INDEX [IX_Detalle_WorkflowID] ON dbo.Workflow_DetalleDiferencias (WorkflowID);
ALTER TABLE dbo.Workflow_DetalleDiferencias ADD CONSTRAINT [PK__Workflow__3214EC27E5AF622E] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ__Workflow__6E19D6FBC520DF5A] ON dbo.Workflow_DetalleDiferencias (DetalleID);
GO

-- =================================================
-- Tabla: Workflow_Inventarios
-- Exportado: 2026-06-03T06:48:06.730193
-- =================================================

IF OBJECT_ID('dbo.Workflow_Inventarios', 'U') IS NOT NULL
    DROP TABLE dbo.Workflow_Inventarios;
GO

CREATE TABLE dbo.Workflow_Inventarios (
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
    [NotasJSON] NVARCHAR(MAX) NULL
);
GO

CREATE INDEX [IX_Workflow_Estado] ON dbo.Workflow_Inventarios (Estado);
CREATE INDEX [IX_Workflow_FechaCreacion] ON dbo.Workflow_Inventarios (FechaCreacion);
CREATE INDEX [IX_Workflow_ServerID] ON dbo.Workflow_Inventarios (ServerID);
ALTER TABLE dbo.Workflow_Inventarios ADD CONSTRAINT [PK__Workflow__3214EC271255D6C2] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ__Workflow__5704A64B307FFCD3] ON dbo.Workflow_Inventarios (WorkflowID);
GO

-- =================================================
-- Tabla: Workflow_Justificaciones
-- Exportado: 2026-06-03T06:48:06.934818
-- =================================================

IF OBJECT_ID('dbo.Workflow_Justificaciones', 'U') IS NOT NULL
    DROP TABLE dbo.Workflow_Justificaciones;
GO

CREATE TABLE dbo.Workflow_Justificaciones (
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
    [Comentarios] NVARCHAR(MAX) NULL
);
GO

CREATE INDEX [IX_WfJust_DetalleID] ON dbo.Workflow_Justificaciones (DetalleID);
CREATE INDEX [IX_WfJust_Estado] ON dbo.Workflow_Justificaciones (Estado);
CREATE INDEX [IX_WfJust_WorkflowID] ON dbo.Workflow_Justificaciones (WorkflowID);
ALTER TABLE dbo.Workflow_Justificaciones ADD CONSTRAINT [PK__Workflow__3214EC2750ECB3A5] PRIMARY KEY (ID);
CREATE UNIQUE INDEX [UQ_WfJust_JustificacionID] ON dbo.Workflow_Justificaciones (JustificacionID);
GO
