-- EDARSAHUB Database Schema Export
-- Generated: 2026-06-03T00:42:37.289633
-- Total Tables: 422

-- Table: ActivoFijo_ActivoMedidores
CREATE TABLE [ActivoFijo_ActivoMedidores] (
    [ActivoMedidorID] BIGINT NOT NULL,
    [ActivoID] BIGINT NOT NULL,
    [MedidorID] INT NOT NULL,
    [ValorActual] DECIMAL(18,4) NULL,
    [FechaUltimaLectura] DATETIME2 NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: ActivoFijo_Activos
CREATE TABLE [ActivoFijo_Activos] (
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
    [EstadoUsoActivoID] TINYINT NOT NULL,
    [EsComponente] BIT NOT NULL,
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
    [CostoCompra] DECIMAL(18,2) NOT NULL,
    [CostoInstalacion] DECIMAL(18,2) NOT NULL,
    [CostoInicialCapitalizado] DECIMAL(19,2) NULL,
    [VidaUtilMesesManual] SMALLINT NULL,
    [ValorResidualManual] DECIMAL(18,2) NULL,
    [RequiereMantenimiento] BIT NOT NULL,
    [Criticidad] TINYINT NOT NULL,
    [FotoPrincipalURL] VARCHAR(500) NULL,
    [Notas] VARCHAR(2000) NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedAt] DATETIME2 NULL,
    [ModifiedBy] VARCHAR(100) NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: ActivoFijo_ActivosLibros
CREATE TABLE [ActivoFijo_ActivosLibros] (
    [ActivoLibroID] BIGINT NOT NULL,
    [ActivoID] BIGINT NOT NULL,
    [LibroDepreciacionID] SMALLINT NOT NULL,
    [MetodoDepreciacionID] SMALLINT NOT NULL,
    [FechaInicioDepreciacion] DATE NOT NULL,
    [VidaUtilMeses] SMALLINT NOT NULL,
    [ValorOriginal] DECIMAL(18,2) NOT NULL,
    [ValorResidual] DECIMAL(18,2) NOT NULL,
    [DepreciacionAcumulada] DECIMAL(18,2) NOT NULL,
    [ValorLibroActual] DECIMAL(18,2) NOT NULL,
    [UltimoPeriodoDepreciado] CHAR(7) NULL,
    [Suspendida] BIT NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: ActivoFijo_Alertas
CREATE TABLE [ActivoFijo_Alertas] (
    [AlertaID] BIGINT NOT NULL,
    [ActivoID] BIGINT NULL,
    [OrdenTrabajoID] BIGINT NULL,
    [PlanMantenimientoID] BIGINT NULL,
    [TipoAlerta] VARCHAR(30) NOT NULL,
    [Titulo] VARCHAR(200) NOT NULL,
    [Mensaje] VARCHAR(2000) NOT NULL,
    [Prioridad] VARCHAR(10) NOT NULL,
    [Leida] BIT NOT NULL,
    [EnviadaEmail] BIT NOT NULL,
    [EnviadaWhatsApp] BIT NOT NULL,
    [FechaCierre] DATETIME2 NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL
);
GO

-- Table: ActivoFijo_Archivos
CREATE TABLE [ActivoFijo_Archivos] (
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
    [EsPrincipal] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: ActivoFijo_Autorizaciones
CREATE TABLE [ActivoFijo_Autorizaciones] (
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
    [EstadoAutorizacion] VARCHAR(20) NOT NULL,
    [FechaSolicitud] DATETIME2 NOT NULL,
    [FechaResolucion] DATETIME2 NULL,
    [ComentariosResolucion] VARCHAR(2000) NULL,
    [NotificarEmail] BIT NOT NULL,
    [NotificarWhatsApp] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL
);
GO

-- Table: ActivoFijo_BajasActivos
CREATE TABLE [ActivoFijo_BajasActivos] (
    [BajaActivoID] BIGINT NOT NULL,
    [ActivoID] BIGINT NOT NULL,
    [TipoBajaID] TINYINT NOT NULL,
    [FechaBaja] DATE NOT NULL,
    [Motivo] VARCHAR(1000) NOT NULL,
    [ValorVenta] DECIMAL(18,2) NULL,
    [CostoRetiro] DECIMAL(18,2) NULL,
    [Observaciones] VARCHAR(2000) NULL,
    [AutorizacionID] BIGINT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL
);
GO

-- Table: ActivoFijo_ClaseActivo
CREATE TABLE [ActivoFijo_ClaseActivo] (
    [ClaseActivoID] SMALLINT NOT NULL,
    [Nombre] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [TipoActivoID] SMALLINT NULL,
    [Capitalizable] BIT NOT NULL,
    [RequiereSerie] BIT NOT NULL,
    [RequiereEtiqueta] BIT NOT NULL,
    [RequiereMantenimiento] BIT NOT NULL,
    [RequiereDepreciacion] BIT NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: ActivoFijo_Cotizaciones
CREATE TABLE [ActivoFijo_Cotizaciones] (
    [CotizacionID] BIGINT NOT NULL,
    [FolioCotizacion] VARCHAR(30) NOT NULL,
    [ActivoID] BIGINT NOT NULL,
    [OrdenTrabajoID] BIGINT NULL,
    [ProveedorID] INT NOT NULL,
    [TipoCotizacion] VARCHAR(20) NOT NULL,
    [Concepto] VARCHAR(500) NOT NULL,
    [Monto] DECIMAL(18,2) NOT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [FechaCotizacion] DATE NOT NULL,
    [ValidaHasta] DATE NULL,
    [Incluye] VARCHAR(1000) NULL,
    [ArchivoURL] VARCHAR(500) NULL,
    [EstadoCotizacion] VARCHAR(20) NOT NULL,
    [SistemaExterno] VARCHAR(20) NULL,
    [PedidoExternoID] VARCHAR(50) NULL,
    [SucursalSistema] VARCHAR(120) NULL,
    [EsSeleccionada] BIT NOT NULL,
    [Observaciones] VARCHAR(1000) NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL
);
GO

-- Table: ActivoFijo_DepreciacionMovimientos
CREATE TABLE [ActivoFijo_DepreciacionMovimientos] (
    [DepreciacionMovimientoID] BIGINT NOT NULL,
    [ActivoLibroID] BIGINT NOT NULL,
    [Periodo] CHAR(7) NOT NULL,
    [FechaContable] DATE NOT NULL,
    [ImporteDepreciacion] DECIMAL(18,2) NOT NULL,
    [DepreciacionAcumulada] DECIMAL(18,2) NOT NULL,
    [ValorLibroDespues] DECIMAL(18,2) NOT NULL,
    [TipoMovimiento] VARCHAR(20) NOT NULL,
    [Referencia] VARCHAR(100) NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL
);
GO

-- Table: ActivoFijo_EstadoUsoActivo
CREATE TABLE [ActivoFijo_EstadoUsoActivo] (
    [EstadoUsoActivoID] TINYINT NOT NULL,
    [Nombre] VARCHAR(40) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: ActivoFijo_EstatusActivo
CREATE TABLE [ActivoFijo_EstatusActivo] (
    [EstatusActivoID] TINYINT NOT NULL,
    [Nombre] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: ActivoFijo_EstatusOT
CREATE TABLE [ActivoFijo_EstatusOT] (
    [EstatusOTID] TINYINT NOT NULL,
    [Nombre] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: ActivoFijo_HistorialAsignaciones
CREATE TABLE [ActivoFijo_HistorialAsignaciones] (
    [HistorialAsignacionID] BIGINT NOT NULL,
    [ActivoID] BIGINT NOT NULL,
    [UbicacionID] INT NULL,
    [ResponsableNombre] VARCHAR(150) NULL,
    [CentroCosto] VARCHAR(50) NULL,
    [Departamento] VARCHAR(100) NULL,
    [FechaInicio] DATETIME2 NOT NULL,
    [FechaFin] DATETIME2 NULL,
    [Motivo] VARCHAR(200) NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL
);
GO

-- Table: ActivoFijo_LecturasMedidor
CREATE TABLE [ActivoFijo_LecturasMedidor] (
    [LecturaMedidorID] BIGINT NOT NULL,
    [ActivoMedidorID] BIGINT NOT NULL,
    [FechaLectura] DATETIME2 NOT NULL,
    [ValorLectura] DECIMAL(18,4) NOT NULL,
    [OrigenLectura] VARCHAR(20) NOT NULL,
    [Observaciones] VARCHAR(500) NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL
);
GO

-- Table: ActivoFijo_LibrosDepreciacion
CREATE TABLE [ActivoFijo_LibrosDepreciacion] (
    [LibroDepreciacionID] SMALLINT NOT NULL,
    [CodigoLibro] VARCHAR(20) NOT NULL,
    [NombreLibro] VARCHAR(100) NOT NULL,
    [TipoLibro] VARCHAR(20) NOT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: ActivoFijo_Medidores
CREATE TABLE [ActivoFijo_Medidores] (
    [MedidorID] INT NOT NULL,
    [CodigoMedidor] VARCHAR(30) NOT NULL,
    [NombreMedidor] VARCHAR(100) NOT NULL,
    [TipoMedidorID] TINYINT NOT NULL,
    [UnidadMedida] VARCHAR(30) NULL,
    [TieneLimiteAdvertencia] BIT NOT NULL,
    [LimiteAdvertencia] DECIMAL(18,4) NULL,
    [TieneLimiteCritico] BIT NOT NULL,
    [LimiteCritico] DECIMAL(18,4) NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: ActivoFijo_MetodosDepreciacion
CREATE TABLE [ActivoFijo_MetodosDepreciacion] (
    [MetodoDepreciacionID] SMALLINT NOT NULL,
    [CodigoMetodo] VARCHAR(20) NOT NULL,
    [NombreMetodo] VARCHAR(100) NOT NULL,
    [TipoCalculo] VARCHAR(30) NOT NULL,
    [PermiteValorResidual] BIT NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: ActivoFijo_MovimientosActivo
CREATE TABLE [ActivoFijo_MovimientosActivo] (
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
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL
);
GO

-- Table: ActivoFijo_OrdenesTrabajo
CREATE TABLE [ActivoFijo_OrdenesTrabajo] (
    [OrdenTrabajoID] BIGINT NOT NULL,
    [FolioOT] VARCHAR(30) NOT NULL,
    [ActivoID] BIGINT NOT NULL,
    [PlanMantenimientoID] BIGINT NULL,
    [TipoOTID] TINYINT NOT NULL,
    [EstatusOTID] TINYINT NOT NULL,
    [PrioridadOTID] TINYINT NOT NULL,
    [UbicacionID] INT NULL,
    [FechaSolicitud] DATETIME2 NOT NULL,
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
    [CostoManoObra] DECIMAL(18,2) NOT NULL,
    [CostoMateriales] DECIMAL(18,2) NOT NULL,
    [CostoServicios] DECIMAL(18,2) NOT NULL,
    [CostoTotal] DECIMAL(20,2) NULL,
    [RequiereAutorizacion] BIT NOT NULL,
    [Autorizada] BIT NOT NULL,
    [NumeroFacturaProveedor] VARCHAR(50) NULL,
    [UUIDFacturaProveedor] VARCHAR(50) NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedAt] DATETIME2 NULL,
    [ModifiedBy] VARCHAR(100) NULL
);
GO

-- Table: ActivoFijo_OrdenTrabajoCostos
CREATE TABLE [ActivoFijo_OrdenTrabajoCostos] (
    [OrdenTrabajoCostoID] BIGINT NOT NULL,
    [OrdenTrabajoID] BIGINT NOT NULL,
    [TipoCosto] VARCHAR(20) NOT NULL,
    [ProveedorID] INT NULL,
    [Descripcion] VARCHAR(500) NOT NULL,
    [Cantidad] DECIMAL(18,4) NOT NULL,
    [CostoUnitario] DECIMAL(18,4) NOT NULL,
    [Importe] DECIMAL(37,8) NULL,
    [FechaCosto] DATE NOT NULL,
    [FacturaNumero] VARCHAR(50) NULL,
    [UUIDFactura] VARCHAR(50) NULL,
    [Observaciones] VARCHAR(500) NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL
);
GO

-- Table: ActivoFijo_PlanesMantenimiento
CREATE TABLE [ActivoFijo_PlanesMantenimiento] (
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
    [NotificarDiasAntes] INT NOT NULL,
    [RequiereOTAutomatica] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [Notas] VARCHAR(1000) NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedAt] DATETIME2 NULL,
    [ModifiedBy] VARCHAR(100) NULL
);
GO

-- Table: ActivoFijo_PrioridadOT
CREATE TABLE [ActivoFijo_PrioridadOT] (
    [PrioridadOTID] TINYINT NOT NULL,
    [Nombre] VARCHAR(20) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: ActivoFijo_ReemplazosActivos
CREATE TABLE [ActivoFijo_ReemplazosActivos] (
    [ReemplazoActivoID] BIGINT NOT NULL,
    [ActivoAnteriorID] BIGINT NOT NULL,
    [ActivoNuevoID] BIGINT NOT NULL,
    [FechaReemplazo] DATE NOT NULL,
    [Motivo] VARCHAR(1000) NOT NULL,
    [CostoTotal] DECIMAL(18,2) NOT NULL,
    [AutorizacionID] BIGINT NULL,
    [Notas] VARCHAR(2000) NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL
);
GO

-- Table: ActivoFijo_ReglasClaseLibro
CREATE TABLE [ActivoFijo_ReglasClaseLibro] (
    [ReglaClaseLibroID] INT NOT NULL,
    [ClaseActivoID] SMALLINT NOT NULL,
    [LibroDepreciacionID] SMALLINT NOT NULL,
    [MetodoDepreciacionID] SMALLINT NOT NULL,
    [VidaUtilMeses] SMALLINT NOT NULL,
    [PorcentajeResidual] DECIMAL(9,4) NOT NULL,
    [Capitalizable] BIT NOT NULL,
    [Deprecia] BIT NOT NULL,
    [CuentaActivo] VARCHAR(50) NULL,
    [CuentaDepreciacionAcum] VARCHAR(50) NULL,
    [CuentaGastoDepreciacion] VARCHAR(50) NULL,
    [CuentaBaja] VARCHAR(50) NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: ActivoFijo_TipoActivo
CREATE TABLE [ActivoFijo_TipoActivo] (
    [TipoActivoID] SMALLINT NOT NULL,
    [Nombre] VARCHAR(80) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: ActivoFijo_TipoBaja
CREATE TABLE [ActivoFijo_TipoBaja] (
    [TipoBajaID] TINYINT NOT NULL,
    [Nombre] VARCHAR(40) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: ActivoFijo_TipoMedidor
CREATE TABLE [ActivoFijo_TipoMedidor] (
    [TipoMedidorID] TINYINT NOT NULL,
    [Nombre] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: ActivoFijo_TipoOT
CREATE TABLE [ActivoFijo_TipoOT] (
    [TipoOTID] TINYINT NOT NULL,
    [Nombre] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: ActivoFijo_TipoUbicacion
CREATE TABLE [ActivoFijo_TipoUbicacion] (
    [TipoUbicacionID] SMALLINT NOT NULL,
    [Nombre] VARCHAR(60) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: ActivoFijo_Ubicaciones
CREATE TABLE [ActivoFijo_Ubicaciones] (
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
    [Activa] BIT NOT NULL
);
GO

-- Table: Alertas_Sistema
CREATE TABLE [Alertas_Sistema] (
    [ID] INT NOT NULL,
    [AlertaID] VARCHAR(50) NOT NULL,
    [Tipo] VARCHAR(100) NULL,
    [Severidad] VARCHAR(20) NULL,
    [Titulo] VARCHAR(200) NULL,
    [Mensaje] NVARCHAR(MAX) NULL,
    [Modulo] VARCHAR(50) NULL,
    [FechaCreacion] DATETIME2 NULL,
    [DatosJSON] NVARCHAR(MAX) NULL,
    [AccionSugerida] VARCHAR(500) NULL,
    [Acknowledged] BIT NULL,
    [AcknowledgedBy] VARCHAR(50) NULL,
    [AcknowledgedAt] DATETIME2 NULL
);
GO

-- Table: Auditoria_Inventario_Provisional
CREATE TABLE [Auditoria_Inventario_Provisional] (
    [id] INT NOT NULL,
    [unidad_negocio_id] VARCHAR(50) NOT NULL,
    [unidad_negocio_nombre] VARCHAR(100) NULL,
    [server_id] VARCHAR(50) NOT NULL,
    [sucursal] VARCHAR(100) NULL,
    [fecha_captura] DATETIME NULL,
    [fecha_auditoria] DATE NULL,
    [usuario_id] INT NULL,
    [usuario_email] VARCHAR(100) NULL,
    [codigo_producto] VARCHAR(50) NOT NULL,
    [nombre_producto] VARCHAR(200) NULL,
    [cantidad] DECIMAL(18,4) NOT NULL,
    [costo_unitario] DECIMAL(18,4) NULL,
    [total] DECIMAL(18,4) NULL,
    [almacen] VARCHAR(100) NULL,
    [notas] TEXT NULL,
    [estado] VARCHAR(20) NULL,
    [auditoria_ejecutada] BIT NULL,
    [fecha_auditoria_ejecutada] DATETIME NULL,
    [creado_en] DATETIME NULL,
    [actualizado_en] DATETIME NULL
);
GO

-- Table: automatizacion_inventarios_config
CREATE TABLE [automatizacion_inventarios_config] (
    [config_id] UNIQUEIDENTIFIER NOT NULL,
    [server_id] NVARCHAR(50) NOT NULL,
    [sucursal_id] NVARCHAR(20) NULL,
    [almacen_id] NVARCHAR(20) NULL,
    [intervalo_minutos] INT NOT NULL,
    [hora_inicio] TIME NULL,
    [hora_fin] TIME NULL,
    [activo] BIT NOT NULL,
    [created_at] DATETIME NOT NULL,
    [updated_at] DATETIME NULL,
    [created_by] NVARCHAR(100) NULL,
    [updated_by] NVARCHAR(100) NULL
);
GO

-- Table: automatizacion_inventarios_destinatarios
CREATE TABLE [automatizacion_inventarios_destinatarios] (
    [destinatario_id] UNIQUEIDENTIFIER NOT NULL,
    [server_id] NVARCHAR(50) NOT NULL,
    [sucursal_id] NVARCHAR(20) NULL,
    [almacen_id] NVARCHAR(20) NULL,
    [nivel_origen] NVARCHAR(20) NOT NULL,
    [canal] NVARCHAR(20) NOT NULL,
    [tipo_destinatario] NVARCHAR(10) NOT NULL,
    [email] NVARCHAR(255) NULL,
    [telefono] NVARCHAR(20) NULL,
    [nombre_contacto] NVARCHAR(100) NULL,
    [activo] BIT NOT NULL,
    [created_at] DATETIME NOT NULL,
    [updated_at] DATETIME NULL,
    [created_by] NVARCHAR(100) NULL,
    [updated_by] NVARCHAR(100) NULL
);
GO

-- Table: automatizacion_inventarios_ejecuciones
CREATE TABLE [automatizacion_inventarios_ejecuciones] (
    [ejecucion_id] UNIQUEIDENTIFIER NOT NULL,
    [fecha_inicio] DATETIME NOT NULL,
    [fecha_fin] DATETIME NULL,
    [estado] NVARCHAR(20) NOT NULL,
    [servidores_escaneados] INT NULL,
    [folios_detectados] INT NULL,
    [folios_procesados] INT NULL,
    [folios_error] INT NULL,
    [detalle_errores] NVARCHAR(MAX) NULL,
    [created_at] DATETIME NOT NULL,
    [updated_at] DATETIME NULL
);
GO

-- Table: automatizacion_inventarios_envios
CREATE TABLE [automatizacion_inventarios_envios] (
    [envio_id] UNIQUEIDENTIFIER NOT NULL,
    [procesado_id] UNIQUEIDENTIFIER NOT NULL,
    [destinatario_email] NVARCHAR(255) NOT NULL,
    [canal] NVARCHAR(20) NOT NULL,
    [tipo_destinatario] NVARCHAR(10) NOT NULL,
    [fecha_envio] DATETIME NULL,
    [estado] NVARCHAR(20) NOT NULL,
    [intentos] INT NOT NULL,
    [error_detalle] NVARCHAR(MAX) NULL,
    [created_at] DATETIME NOT NULL,
    [updated_at] DATETIME NULL
);
GO

-- Table: automatizacion_inventarios_folios_procesados
CREATE TABLE [automatizacion_inventarios_folios_procesados] (
    [procesado_id] UNIQUEIDENTIFIER NOT NULL,
    [sistema_origen] NVARCHAR(20) NOT NULL,
    [server_id] NVARCHAR(50) NOT NULL,
    [sucursal_id] NVARCHAR(20) NOT NULL,
    [almacen_id] NVARCHAR(20) NOT NULL,
    [folio_inventario] NVARCHAR(50) NOT NULL,
    [fecha_inventario] DATE NOT NULL,
    [hash_verificacion] NVARCHAR(64) NOT NULL,
    [estado] NVARCHAR(20) NOT NULL,
    [heartbeat_at] DATETIME NULL,
    [fecha_procesado] DATETIME NULL,
    [error_detalle] NVARCHAR(MAX) NULL,
    [ruta_archivo_excel] NVARCHAR(500) NULL,
    [created_at] DATETIME NOT NULL,
    [updated_at] DATETIME NULL,
    [created_by] NVARCHAR(100) NULL,
    [updated_by] NVARCHAR(100) NULL,
    [comentario] NVARCHAR(100) NULL,
    [estado_inventario_origen] NVARCHAR(10) NULL
);
GO

-- Table: automatizacion_inventarios_ultimo_folio_conocido
CREATE TABLE [automatizacion_inventarios_ultimo_folio_conocido] (
    [id] UNIQUEIDENTIFIER NOT NULL,
    [sistema_origen] NVARCHAR(20) NOT NULL,
    [server_id] NVARCHAR(50) NOT NULL,
    [sucursal_id] NVARCHAR(20) NOT NULL,
    [almacen_id] NVARCHAR(20) NOT NULL,
    [ultimo_folio] NVARCHAR(50) NOT NULL,
    [fecha_ultimo_folio] DATE NOT NULL,
    [fecha_actualizacion] DATETIME NOT NULL,
    [created_at] DATETIME NOT NULL,
    [updated_at] DATETIME NULL,
    [created_by] NVARCHAR(100) NULL,
    [updated_by] NVARCHAR(100) NULL
);
GO

-- Table: CavaSocios_Botellas
CREATE TABLE [CavaSocios_Botellas] (
    [BotellaID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [SocioID] UNIQUEIDENTIFIER NOT NULL,
    [ProductoCodigo] VARCHAR(50) NULL,
    [ProductoNombre] NVARCHAR(200) NOT NULL,
    [Marca] NVARCHAR(100) NULL,
    [TipoBebida] VARCHAR(50) NULL,
    [Añada] VARCHAR(10) NULL,
    [Capacidad] DECIMAL(10,2) NULL,
    [UbicacionCava] NVARCHAR(50) NULL,
    [ValorDeclarado] DECIMAL(18,2) NULL,
    [EstatusBotella] VARCHAR(30) NULL,
    [FechaIngreso] DATETIME2 NULL,
    [FechaConsumo] DATETIME2 NULL,
    [FechaRetiro] DATETIME2 NULL,
    [NivelActual] DECIMAL(5,2) NULL,
    [FotoIngresoURL] NVARCHAR(500) NULL,
    [FechaCreacion] DATETIME2 NULL,
    [UsuarioCreacionID] UNIQUEIDENTIFIER NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacionID] UNIQUEIDENTIFIER NULL,
    [Observaciones] NVARCHAR(500) NULL
);
GO

-- Table: CavaSocios_Cargos
CREATE TABLE [CavaSocios_Cargos] (
    [CargoID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [SocioID] UNIQUEIDENTIFIER NOT NULL,
    [TipoCargo] VARCHAR(50) NOT NULL,
    [ConceptoCargo] NVARCHAR(200) NOT NULL,
    [Monto] DECIMAL(18,2) NOT NULL,
    [Impuesto] DECIMAL(18,2) NULL,
    [Total] DECIMAL(18,2) NOT NULL,
    [EstatusCargo] VARCHAR(30) NULL,
    [BotellaID] UNIQUEIDENTIFIER NULL,
    [MovimientoID] UNIQUEIDENTIFIER NULL,
    [ReservacionID] UNIQUEIDENTIFIER NULL,
    [FacturaID] UNIQUEIDENTIFIER NULL,
    [FechaCargo] DATETIME2 NULL,
    [FechaPago] DATETIME2 NULL,
    [FechaCreacion] DATETIME2 NULL,
    [UsuarioCreacionID] UNIQUEIDENTIFIER NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacionID] UNIQUEIDENTIFIER NULL,
    [Observaciones] NVARCHAR(500) NULL
);
GO

-- Table: CavaSocios_Configuracion
CREATE TABLE [CavaSocios_Configuracion] (
    [ConfigID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [CapacidadTotalBotellas] INT NULL,
    [TarifaDescorche] DECIMAL(18,2) NULL,
    [TarifaAlmacenajeMensual] DECIMAL(18,2) NULL,
    [DiasGraciaVencimiento] INT NULL,
    [MaximoBotellasEstandar] INT NULL,
    [MaximoBotellasVIP] INT NULL,
    [DiasAnticipacionVencimiento] INT NULL,
    [FechaCreacion] DATETIME2 NULL,
    [UsuarioCreacionID] UNIQUEIDENTIFIER NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacionID] UNIQUEIDENTIFIER NULL
);
GO

-- Table: CavaSocios_Movimientos
CREATE TABLE [CavaSocios_Movimientos] (
    [MovimientoID] UNIQUEIDENTIFIER NOT NULL,
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
    [GeneroCargo] BIT NULL,
    [MontoCargo] DECIMAL(18,2) NULL,
    [CargoConceptoID] UNIQUEIDENTIFIER NULL,
    [MeseroID] UNIQUEIDENTIFIER NULL,
    [AutorizadoPor] UNIQUEIDENTIFIER NULL,
    [SucursalID] UNIQUEIDENTIFIER NULL,
    [FotoEvidenciaURL] NVARCHAR(500) NULL,
    [FechaMovimiento] DATETIME2 NULL,
    [FechaCreacion] DATETIME2 NULL,
    [UsuarioCreacionID] UNIQUEIDENTIFIER NULL,
    [Observaciones] NVARCHAR(500) NULL
);
GO

-- Table: CavaSocios_Socios
CREATE TABLE [CavaSocios_Socios] (
    [SocioID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [NumeroSocio] VARCHAR(50) NOT NULL,
    [NombreCompleto] NVARCHAR(200) NOT NULL,
    [Email] VARCHAR(150) NULL,
    [Telefono] VARCHAR(50) NULL,
    [ClienteCRMID] UNIQUEIDENTIFIER NULL,
    [TipoMembresia] VARCHAR(50) NULL,
    [FechaAltaMembresia] DATE NULL,
    [FechaVencimientoMembresia] DATE NULL,
    [MaximoBotellas] INT NULL,
    [Estatus] VARCHAR(30) NULL,
    [Activo] BIT NULL,
    [FechaCreacion] DATETIME2 NULL,
    [UsuarioCreacionID] UNIQUEIDENTIFIER NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacionID] UNIQUEIDENTIFIER NULL,
    [Observaciones] NVARCHAR(500) NULL
);
GO

-- Table: Cliente_Catalogo
CREATE TABLE [Cliente_Catalogo] (
    [ClienteID] INT NOT NULL,
    [CodigoCliente] VARCHAR(20) NOT NULL,
    [RFC] VARCHAR(13) NOT NULL,
    [CURP] VARCHAR(18) NULL,
    [RazonSocial] VARCHAR(200) NOT NULL,
    [NombreComercial] VARCHAR(200) NULL,
    [TipoPersona] CHAR(1) NOT NULL,
    [ClienteMaestroID] INT NULL,
    [GrupoClienteID] INT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [LimiteCredito] DECIMAL(18,2) NULL,
    [DiasCredito] SMALLINT NOT NULL,
    [DescuentoMaximoPorcentaje] DECIMAL(9,4) NOT NULL,
    [PortalHabilitado] BIT NOT NULL,
    [BloqueadoVenta] BIT NOT NULL,
    [EmailPrincipal] VARCHAR(150) NULL,
    [TelefonoPrincipal] VARCHAR(25) NULL,
    [SitioWeb] VARCHAR(200) NULL,
    [CodigoPostalFiscal] VARCHAR(10) NULL,
    [Ciudad] VARCHAR(100) NULL,
    [Estado] VARCHAR(100) NULL,
    [Pais] VARCHAR(60) NOT NULL,
    [Observaciones] VARCHAR(1000) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
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
    [EsProspecto] BIT NULL,
    [EsPartner] BIT NULL,
    [EsCuentaEstrategica] BIT NULL,
    [FechaUltimaInteraccion] DATETIME NULL,
    [ScoreCuenta] INT NULL,
    [OrigenCuentaID] INT NULL,
    [PublicUUID] UNIQUEIDENTIFIER NULL
);
GO

-- Table: Cliente_Contactos
CREATE TABLE [Cliente_Contactos] (
    [ContactoClienteID] INT NOT NULL,
    [ClienteID] INT NOT NULL,
    [Nombre] VARCHAR(150) NOT NULL,
    [Apellidos] VARCHAR(150) NULL,
    [Puesto] VARCHAR(100) NULL,
    [Email] VARCHAR(150) NULL,
    [Telefono] VARCHAR(25) NULL,
    [Celular] VARCHAR(25) NULL,
    [EsPrincipal] BIT NOT NULL,
    [RecibeCotizaciones] BIT NOT NULL,
    [RecibeFacturacion] BIT NOT NULL,
    [RecibeCobranza] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Cliente_Direcciones
CREATE TABLE [Cliente_Direcciones] (
    [DireccionClienteID] INT NOT NULL,
    [ClienteID] INT NOT NULL,
    [TipoDireccion] VARCHAR(20) NOT NULL,
    [Calle] VARCHAR(150) NULL,
    [NumeroExterior] VARCHAR(20) NULL,
    [NumeroInterior] VARCHAR(20) NULL,
    [Colonia] VARCHAR(100) NULL,
    [Municipio] VARCHAR(100) NULL,
    [Ciudad] VARCHAR(100) NULL,
    [Estado] VARCHAR(100) NULL,
    [Pais] VARCHAR(60) NOT NULL,
    [CodigoPostal] VARCHAR(10) NULL,
    [Referencias] VARCHAR(250) NULL,
    [EsPrincipal] BIT NOT NULL,
    [Activa] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Cliente_Grupos
CREATE TABLE [Cliente_Grupos] (
    [GrupoClienteID] INT NOT NULL,
    [CodigoGrupoCliente] VARCHAR(20) NOT NULL,
    [NombreGrupoCliente] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Cliente_RolUsuarioPortal
CREATE TABLE [Cliente_RolUsuarioPortal] (
    [RolPortalClienteID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Cliente_UsuariosPortal
CREATE TABLE [Cliente_UsuariosPortal] (
    [UsuarioPortalClienteID] INT NOT NULL,
    [ClienteID] INT NOT NULL,
    [RolPortalClienteID] TINYINT NOT NULL,
    [NombreUsuario] VARCHAR(150) NOT NULL,
    [Email] VARCHAR(150) NOT NULL,
    [PasswordHash] VARCHAR(255) NULL,
    [ContactoClienteID] INT NULL,
    [UltimoAcceso] DATETIME2 NULL,
    [Bloqueado] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Comercial_AlertasMargenDestinatarios
CREATE TABLE [Comercial_AlertasMargenDestinatarios] (
    [DestinatarioID] UNIQUEIDENTIFIER NOT NULL,
    [Nombre] NVARCHAR(200) NOT NULL,
    [Email] VARCHAR(200) NULL,
    [TelefonoWhatsApp] VARCHAR(20) NULL,
    [CanalEmail] BIT NULL,
    [CanalWhatsApp] BIT NULL,
    [EmpresaID] INT NULL,
    [SucursalID] INT NULL,
    [ServerID] UNIQUEIDENTIFIER NULL,
    [FamiliaCodigo] VARCHAR(100) NULL,
    [SeveridadMinima] VARCHAR(20) NULL,
    [RecibeResumen] BIT NULL,
    [RecibeDetalle] BIT NULL,
    [FrecuenciaMaximaDiaria] INT NULL,
    [HoraPreferida] VARCHAR(5) NULL,
    [Activo] BIT NULL,
    [FechaCreacion] DATETIME NULL,
    [FechaModificacion] DATETIME NULL,
    [CreadoPor] VARCHAR(100) NULL,
    [ModificadoPor] VARCHAR(100) NULL
);
GO

-- Table: Comercial_AlertasMargenEnvios
CREATE TABLE [Comercial_AlertasMargenEnvios] (
    [EnvioID] UNIQUEIDENTIFIER NOT NULL,
    [AlertaMargenEventoID] UNIQUEIDENTIFIER NOT NULL,
    [DestinatarioID] UNIQUEIDENTIFIER NOT NULL,
    [Canal] VARCHAR(20) NOT NULL,
    [EstadoEnvio] VARCHAR(30) NULL,
    [FechaIntento] DATETIME NULL,
    [FechaEnvio] DATETIME NULL,
    [NumeroIntentos] INT NULL,
    [ProviderMessageID] VARCHAR(200) NULL,
    [ErrorMensajeSeguro] NVARCHAR(500) NULL,
    [FechaCreacion] DATETIME NULL
);
GO

-- Table: Comercial_AlertasMargenEventos
CREATE TABLE [Comercial_AlertasMargenEventos] (
    [AlertaMargenEventoID] UNIQUEIDENTIFIER NOT NULL,
    [FechaEvaluacion] DATETIME NULL,
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
    [Estado] VARCHAR(30) NULL,
    [SnapshotID] UNIQUEIDENTIFIER NULL,
    [VariacionCostoAnterior] DECIMAL(18,4) NULL,
    [VariacionCostoAcumulada] DECIMAL(18,4) NULL,
    [Recomendacion] NVARCHAR(500) NULL,
    [ErrorDatos] BIT NULL,
    [NotasInternas] NVARCHAR(MAX) NULL,
    [FechaCreacion] DATETIME NULL,
    [FechaModificacion] DATETIME NULL,
    [FechaResolucion] DATETIME NULL,
    [ResueltoPor] VARCHAR(100) NULL
);
GO

-- Table: Comercial_AlertasMargenReglas
CREATE TABLE [Comercial_AlertasMargenReglas] (
    [ReglaMargenID] UNIQUEIDENTIFIER NOT NULL,
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
    [SeveridadBase] VARCHAR(20) NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Activo] BIT NULL,
    [FechaInicioVigencia] DATETIME NULL,
    [FechaFinVigencia] DATETIME NULL,
    [FechaCreacion] DATETIME NULL,
    [FechaModificacion] DATETIME NULL,
    [CreadoPor] VARCHAR(100) NULL,
    [ModificadoPor] VARCHAR(100) NULL
);
GO

-- Table: Comercial_AlertasUmbralesSeveridad
CREATE TABLE [Comercial_AlertasUmbralesSeveridad] (
    [UmbralID] UNIQUEIDENTIFIER NOT NULL,
    [Severidad] VARCHAR(20) NOT NULL,
    [PuntosDesde] DECIMAL(5,2) NOT NULL,
    [PuntosHasta] DECIMAL(5,2) NOT NULL,
    [IncluirUtilidadNegativa] BIT NULL,
    [IncluirCostoMayorPrecio] BIT NULL,
    [Descripcion] NVARCHAR(200) NULL,
    [ColorHex] VARCHAR(7) NULL,
    [Activo] BIT NULL,
    [Orden] INT NULL,
    [FechaCreacion] DATETIME NULL,
    [FechaModificacion] DATETIME NULL
);
GO

-- Table: Comercial_Competidores
CREATE TABLE [Comercial_Competidores] (
    [CompetidorID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] INT NOT NULL,
    [UnidadNegocioID] INT NULL,
    [NombreCompetidor] NVARCHAR(200) NOT NULL,
    [TipoRestaurante] VARCHAR(50) NULL,
    [SegmentoPrecio] VARCHAR(30) NULL,
    [Ciudad] NVARCHAR(100) NULL,
    [Estado] NVARCHAR(100) NULL,
    [Pais] VARCHAR(50) NULL,
    [ZonaComercial] NVARCHAR(200) NULL,
    [SitioWeb] NVARCHAR(500) NULL,
    [UrlMenu] NVARCHAR(500) NULL,
    [UrlGoogleMaps] NVARCHAR(500) NULL,
    [UrlInstagram] NVARCHAR(500) NULL,
    [UrlTripAdvisor] NVARCHAR(500) NULL,
    [UrlOpenTable] NVARCHAR(500) NULL,
    [EsCompetenciaDirecta] BIT NULL,
    [EsBenchmarkAspiracional] BIT NULL,
    [DistanciaKm] DECIMAL(10,2) NULL,
    [Prioridad] INT NULL,
    [Activo] BIT NULL,
    [FechaCreacion] DATETIME2 NULL,
    [UsuarioCreacion] NVARCHAR(100) NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacion] NVARCHAR(100) NULL,
    [UrlFacebook] NVARCHAR(500) NULL,
    [Notas] NVARCHAR(1000) NULL
);
GO

-- Table: Comercial_CompetidoresCatalogo
CREATE TABLE [Comercial_CompetidoresCatalogo] (
    [CompetidorCatalogoID] UNIQUEIDENTIFIER NOT NULL,
    [NombreCompetidor] NVARCHAR(200) NOT NULL,
    [TipoRestaurante] VARCHAR(50) NULL,
    [SegmentoPrecio] VARCHAR(30) NULL,
    [Ciudad] NVARCHAR(100) NULL,
    [Estado] NVARCHAR(100) NULL,
    [Pais] VARCHAR(50) NULL,
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
    [Activo] BIT NULL,
    [FechaCreacion] DATETIME2 NULL,
    [UsuarioCreacion] NVARCHAR(100) NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacion] NVARCHAR(100) NULL
);
GO

-- Table: Comercial_CompetidoresListas
CREATE TABLE [Comercial_CompetidoresListas] (
    [ListaCompetidoresID] UNIQUEIDENTIFIER NOT NULL,
    [NombreLista] NVARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [EmpresaID] INT NULL,
    [UnidadNegocioID] INT NULL,
    [Segmento] NVARCHAR(100) NULL,
    [Categoria] NVARCHAR(100) NULL,
    [ColorIdentificador] NVARCHAR(20) NULL,
    [Activo] BIT NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL,
    [CreadoPor] NVARCHAR(100) NOT NULL,
    [ModificadoPor] NVARCHAR(100) NULL
);
GO

-- Table: Comercial_CompetidoresListasDetalle
CREATE TABLE [Comercial_CompetidoresListasDetalle] (
    [ListaDetalleID] UNIQUEIDENTIFIER NOT NULL,
    [ListaCompetidoresID] UNIQUEIDENTIFIER NOT NULL,
    [CompetidorID] UNIQUEIDENTIFIER NOT NULL,
    [Orden] INT NULL,
    [Notas] NVARCHAR(500) NULL,
    [Activo] BIT NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL,
    [CreadoPor] NVARCHAR(100) NOT NULL,
    [ModificadoPor] NVARCHAR(100) NULL
);
GO

-- Table: Comercial_CompetidoresMenuItems
CREATE TABLE [Comercial_CompetidoresMenuItems] (
    [CompetidorMenuItemID] UNIQUEIDENTIFIER NOT NULL,
    [CompetidorID] UNIQUEIDENTIFIER NOT NULL,
    [NombreProductoCompetidor] NVARCHAR(300) NOT NULL,
    [CategoriaCompetidor] NVARCHAR(100) NULL,
    [Descripcion] NVARCHAR(1000) NULL,
    [Precio] DECIMAL(18,2) NULL,
    [Moneda] VARCHAR(10) NULL,
    [FuenteUrl] NVARCHAR(500) NULL,
    [FechaConsulta] DATE NULL,
    [MetodoObtencion] VARCHAR(30) NOT NULL,
    [ConfianzaDato] VARCHAR(20) NULL,
    [EsDatoManual] BIT NULL,
    [EsDatoIA] BIT NULL,
    [PayloadJSON] NVARCHAR(MAX) NULL,
    [Activo] BIT NULL,
    [FechaCreacion] DATETIME2 NULL,
    [UsuarioCreacion] NVARCHAR(100) NULL
);
GO

-- Table: Comercial_CompetidoresUnidad
CREATE TABLE [Comercial_CompetidoresUnidad] (
    [CompetidorUnidadID] UNIQUEIDENTIFIER NOT NULL,
    [CompetidorCatalogoID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] INT NOT NULL,
    [UnidadNegocioID] INT NOT NULL,
    [EsCompetenciaDirecta] BIT NULL,
    [EsBenchmarkAspiracional] BIT NULL,
    [TipoRelacion] VARCHAR(50) NULL,
    [Prioridad] INT NULL,
    [DistanciaKm] DECIMAL(10,2) NULL,
    [Comentarios] NVARCHAR(500) NULL,
    [Activo] BIT NULL,
    [FechaCreacion] DATETIME2 NULL,
    [UsuarioCreacion] NVARCHAR(100) NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacion] NVARCHAR(100) NULL
);
GO

-- Table: Comercial_Dashboard_Cache
CREATE TABLE [Comercial_Dashboard_Cache] (
    [CacheID] INT NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [PeriodoKey] VARCHAR(100) NOT NULL,
    [DataJSON] NVARCHAR(MAX) NULL,
    [UpdatedAt] DATETIME NULL
);
GO

-- Table: Comercial_ImpuestosCatalogo
CREATE TABLE [Comercial_ImpuestosCatalogo] (
    [ImpuestoID] UNIQUEIDENTIFIER NOT NULL,
    [Codigo] VARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [TipoImpuesto] VARCHAR(20) NOT NULL,
    [PaisISO] VARCHAR(3) NULL,
    [Activo] BIT NULL,
    [FechaCreacion] DATETIME2 NULL,
    [FechaModificacion] DATETIME2 NULL,
    [CreadoPor] NVARCHAR(100) NULL,
    [ModificadoPor] NVARCHAR(100) NULL
);
GO

-- Table: Comercial_ImpuestosMapeo
CREATE TABLE [Comercial_ImpuestosMapeo] (
    [MapeoProductoID] UNIQUEIDENTIFIER NOT NULL,
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
    [FechaCreacion] DATETIME2 NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Comercial_ImpuestosOverrides
CREATE TABLE [Comercial_ImpuestosOverrides] (
    [OverrideID] UNIQUEIDENTIFIER NOT NULL,
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
    [Activo] BIT NULL,
    [FechaCreacion] DATETIME2 NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Comercial_ImpuestosTasas
CREATE TABLE [Comercial_ImpuestosTasas] (
    [TasaID] UNIQUEIDENTIFIER NOT NULL,
    [ImpuestoID] UNIQUEIDENTIFIER NOT NULL,
    [Tasa] DECIMAL(10,4) NOT NULL,
    [TipoFactor] VARCHAR(20) NOT NULL,
    [VigenciaDesde] DATE NOT NULL,
    [VigenciaHasta] DATE NULL,
    [Activo] BIT NULL,
    [FechaCreacion] DATETIME2 NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Comercial_Inteligencia_VentasDetalleProducto
CREATE TABLE [Comercial_Inteligencia_VentasDetalleProducto] (
    [id] UNIQUEIDENTIFIER NOT NULL,
    [unidad_negocio_id] NVARCHAR(50) NULL,
    [unidad_negocio_nombre] NVARCHAR(100) NULL,
    [server_id] NVARCHAR(50) NULL,
    [sucursal_id] NVARCHAR(50) NULL,
    [sucursal_nombre] NVARCHAR(100) NULL,
    [sistema_origen] NVARCHAR(20) NULL,
    [fecha_operacion] DATE NOT NULL,
    [fecha_hora] DATETIME2 NULL,
    [numero_ticket] NVARCHAR(64) NOT NULL,
    [id_transaccion] NVARCHAR(64) NOT NULL,
    [producto_codigo_fuente] NVARCHAR(100) NOT NULL,
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
    [fecha_sincronizacion] DATETIME2 NOT NULL,
    [activo] BIT NOT NULL
);
GO

-- Table: Comercial_KPIs_Cache
CREATE TABLE [Comercial_KPIs_Cache] (
    [CacheID] INT NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [PeriodoKey] VARCHAR(100) NOT NULL,
    [KPIsJSON] NVARCHAR(MAX) NULL,
    [UpdatedAt] DATETIME NULL,
    [Status] VARCHAR(20) NULL
);
GO

-- Table: Comercial_KPIs_Diarios_v2
CREATE TABLE [Comercial_KPIs_Diarios_v2] (
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
    [version] INT NULL
);
GO

-- Table: Comercial_KPIs_Diarios_v2_backup_migracion_codigos_20260513_0558
CREATE TABLE [Comercial_KPIs_Diarios_v2_backup_migracion_codigos_20260513_0558] (
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

-- Table: Comercial_KPIs_Historico
CREATE TABLE [Comercial_KPIs_Historico] (
    [id] UNIQUEIDENTIFIER NOT NULL,
    [run_id] NVARCHAR(100) NOT NULL,
    [server_id] NVARCHAR(100) NOT NULL,
    [sucursal_id] NVARCHAR(100) NOT NULL,
    [sucursal_nombre] NVARCHAR(255) NULL,
    [empresa_id] NVARCHAR(100) NULL,
    [unidad_negocio_id] NVARCHAR(100) NULL,
    [system_type_normalized] NVARCHAR(50) NOT NULL,
    [fecha] DATE NOT NULL,
    [kpi_tipo] NVARCHAR(50) NOT NULL,
    [ventas_total] DECIMAL(18,2) NULL,
    [tickets_total] INT NULL,
    [pax_total] INT NULL,
    [ticket_promedio] DECIMAL(18,2) NULL,
    [propinas_total] DECIMAL(18,2) NULL,
    [source_hash] NVARCHAR(128) NULL,
    [source_batch_start] DATE NULL,
    [source_batch_end] DATE NULL,
    [metadata_json] NVARCHAR(MAX) NULL,
    [version] INT NOT NULL,
    [created_at] DATETIME2 NOT NULL,
    [updated_at] DATETIME2 NOT NULL
);
GO

-- Table: Comercial_KPIs_Mensuales_v2
CREATE TABLE [Comercial_KPIs_Mensuales_v2] (
    [id] UNIQUEIDENTIFIER NOT NULL,
    [unidad_negocio_id] NVARCHAR(50) NOT NULL,
    [unidad_negocio_nombre] NVARCHAR(100) NOT NULL,
    [server_id] NVARCHAR(50) NOT NULL,
    [sucursal_id] NVARCHAR(50) NOT NULL,
    [sucursal_nombre] NVARCHAR(100) NULL,
    [sistema_origen] NVARCHAR(20) NOT NULL,
    [anio] INT NOT NULL,
    [mes] INT NOT NULL,
    [dias_con_datos] INT NULL,
    [dias_mes_total] INT NOT NULL,
    [ventas_total] DECIMAL(18,2) NULL,
    [ventas_sin_propina] DECIMAL(18,2) NULL,
    [propinas_total] DECIMAL(18,2) NULL,
    [tickets_total] INT NULL,
    [pax_total] INT NULL,
    [ticket_promedio] DECIMAL(18,2) NULL,
    [pax_promedio] DECIMAL(18,2) NULL,
    [proyeccion_mes] DECIMAL(18,2) NULL,
    [ventas_mes_anterior] DECIMAL(18,2) NULL,
    [var_vs_mes_anterior] DECIMAL(8,2) NULL,
    [ventas_anio_anterior] DECIMAL(18,2) NULL,
    [var_vs_anio_anterior] DECIMAL(8,2) NULL,
    [es_mes_completo] BIT NULL,
    [es_demo] BIT NULL,
    [activo] BIT NULL,
    [sync_run_id] NVARCHAR(50) NULL,
    [fecha_calculo] DATETIME2 NULL,
    [fecha_ultima_actualizacion] DATETIME2 NULL,
    [version] INT NULL
);
GO

-- Table: Comercial_Metas
CREATE TABLE [Comercial_Metas] (
    [MetaID] INT NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [Sucursal] VARCHAR(100) NOT NULL,
    [Mes] INT NOT NULL,
    [Anio] INT NOT NULL,
    [MetaVentas] DECIMAL(18,2) NULL,
    [MetaCheques] INT NULL,
    [MetaPax] INT NULL,
    [MetaTicketPromedio] DECIMAL(18,2) NULL,
    [FechaCreacion] DATETIME NULL,
    [FechaModificacion] DATETIME NULL
);
GO

-- Table: Comercial_PreciosSugeridos
CREATE TABLE [Comercial_PreciosSugeridos] (
    [PrecioSugeridoID] UNIQUEIDENTIFIER NOT NULL,
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
    [FechaCalculo] DATETIME2 NULL,
    [UsuarioCalculo] NVARCHAR(100) NULL,
    [TipoMotorPrecio] VARCHAR(50) NULL,
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
    [RequiereRevisionHumana] BIT NULL,
    [FechaAnalisisIA] DATETIME2 NULL,
    [ModeloIAUsado] VARCHAR(100) NULL,
    [VersionRegla] VARCHAR(50) NULL,
    [PayloadAnalisisJSON] NVARCHAR(MAX) NULL
);
GO

-- Table: Comercial_PricingAnalisisIA
CREATE TABLE [Comercial_PricingAnalisisIA] (
    [AnalisisIAID] UNIQUEIDENTIFIER NOT NULL,
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
    [RequiereRevisionHumana] BIT NULL,
    [PrecioActual] DECIMAL(18,2) NULL,
    [PrecioSugerido] DECIMAL(18,2) NULL,
    [MargenActual] DECIMAL(8,4) NULL,
    [MargenSugerido] DECIMAL(8,4) NULL,
    [CompetidoresUsadosJSON] NVARCHAR(MAX) NULL,
    [FuentesUsadasJSON] NVARCHAR(MAX) NULL,
    [EstadoAnalisis] VARCHAR(30) NOT NULL,
    [UsuarioEjecucion] NVARCHAR(100) NOT NULL,
    [FechaEjecucion] DATETIME2 NOT NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [ListaCompetidoresID] UNIQUEIDENTIFIER NULL
);
GO

-- Table: Comercial_PricingBenchmarkProducto
CREATE TABLE [Comercial_PricingBenchmarkProducto] (
    [BenchmarkProductoID] UNIQUEIDENTIFIER NOT NULL,
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
    [ValidadoPorUsuario] BIT NULL,
    [UsuarioValidacion] NVARCHAR(100) NULL,
    [FechaValidacion] DATETIME2 NULL,
    [Activo] BIT NULL,
    [FechaCreacion] DATETIME2 NULL,
    [UsuarioCreacion] NVARCHAR(100) NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacion] NVARCHAR(100) NULL
);
GO

-- Table: Comercial_RecetasSnapshot
CREATE TABLE [Comercial_RecetasSnapshot] (
    [RecetaSnapshotID] UNIQUEIDENTIFIER NOT NULL,
    [FechaSnapshot] DATETIME NULL,
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
    [NumeroInsumos] INT NULL,
    [HashReceta] VARCHAR(64) NULL,
    [FuenteCalculo] VARCHAR(50) NULL,
    [SnapshotAnteriorID] UNIQUEIDENTIFIER NULL,
    [VariacionCosto] DECIMAL(18,4) NULL,
    [VariacionCostoPorcentaje] DECIMAL(5,2) NULL,
    [VariacionMargen] DECIMAL(5,2) NULL,
    [EsActual] BIT NULL,
    [FechaCreacion] DATETIME NULL,
    [CreadoPor] VARCHAR(100) NULL,
    [SyncRunID] VARCHAR(100) NULL
);
GO

-- Table: Comercial_RecetasSnapshotDetalle
CREATE TABLE [Comercial_RecetasSnapshotDetalle] (
    [RecetaSnapshotDetalleID] UNIQUEIDENTIFIER NOT NULL,
    [RecetaSnapshotID] UNIQUEIDENTIFIER NOT NULL,
    [InsumoClave] VARCHAR(100) NOT NULL,
    [InsumoNombre] NVARCHAR(500) NULL,
    [Cantidad] DECIMAL(18,6) NULL,
    [UnidadMedida] VARCHAR(50) NULL,
    [CostoUnitario] DECIMAL(18,4) NULL,
    [CostoTotal] DECIMAL(18,4) NULL,
    [PorcentajeDelCosto] DECIMAL(5,2) NULL,
    [EsElaborado] BIT NULL,
    [CostoAnterior] DECIMAL(18,4) NULL,
    [VariacionCosto] DECIMAL(18,4) NULL,
    [VariacionCostoPorcentaje] DECIMAL(5,2) NULL,
    [FechaCreacion] DATETIME NULL,
    [Orden] INT NULL
);
GO

-- Table: Comercial_ReglasPrecio
CREATE TABLE [Comercial_ReglasPrecio] (
    [ReglaPrecioID] UNIQUEIDENTIFIER NOT NULL,
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
    [PaisCodigo] VARCHAR(3) NULL,
    [RegionCodigo] VARCHAR(10) NULL,
    [MetodoRedondeo] VARCHAR(20) NOT NULL,
    [MultiploRedondeo] INT NOT NULL,
    [PermiteGaps] BIT NULL,
    [UsaCostoReceta] BIT NULL,
    [UsaCostoBotella] BIT NULL,
    [Activo] BIT NULL,
    [VigenciaDesde] DATE NOT NULL,
    [VigenciaHasta] DATE NULL,
    [FechaCreacion] DATETIME2 NULL,
    [UsuarioCreacion] NVARCHAR(100) NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacion] NVARCHAR(100) NULL
);
GO

-- Table: Comercial_ReglasPrecioRangos
CREATE TABLE [Comercial_ReglasPrecioRangos] (
    [ReglaPrecioRangoID] UNIQUEIDENTIFIER NOT NULL,
    [ReglaPrecioID] UNIQUEIDENTIFIER NOT NULL,
    [LimiteInferior] DECIMAL(18,2) NOT NULL,
    [LimiteSuperior] DECIMAL(18,2) NOT NULL,
    [MargenMultiplicador] DECIMAL(6,4) NOT NULL,
    [Orden] INT NOT NULL,
    [Descripcion] NVARCHAR(200) NULL,
    [Activo] BIT NULL,
    [FechaCreacion] DATETIME2 NULL,
    [UsuarioCreacion] NVARCHAR(100) NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacion] NVARCHAR(100) NULL
);
GO

-- Table: Comercial_SimulacionesPrecios
CREATE TABLE [Comercial_SimulacionesPrecios] (
    [SimulacionID] UNIQUEIDENTIFIER NOT NULL,
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
    [ConvertidoASolicitud] BIT NULL,
    [SolicitudID] UNIQUEIDENTIFIER NULL,
    [UsuarioID] UNIQUEIDENTIFIER NOT NULL,
    [UsuarioEmail] VARCHAR(200) NOT NULL,
    [FechaSimulacion] DATETIME2 NOT NULL,
    [IPSimulacion] VARCHAR(50) NULL
);
GO

-- Table: Comercial_SolicitudesCambioPrecio
CREATE TABLE [Comercial_SolicitudesCambioPrecio] (
    [SolicitudID] UNIQUEIDENTIFIER NOT NULL,
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
    [Estatus] VARCHAR(20) NOT NULL,
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
    [FechaCreacion] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NOT NULL,
    [IPCreacion] VARCHAR(50) NULL
);
GO

-- Table: Comercial_SolicitudesCambioPrecioHistorial
CREATE TABLE [Comercial_SolicitudesCambioPrecioHistorial] (
    [HistorialID] UNIQUEIDENTIFIER NOT NULL,
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
    [FechaAccion] DATETIME2 NOT NULL,
    [IPAccion] VARCHAR(50) NULL,
    [UserAgent] NVARCHAR(500) NULL
);
GO

-- Table: Comercial_SyncLog_v2
CREATE TABLE [Comercial_SyncLog_v2] (
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
    [created_at] DATETIME2 NULL
);
GO

-- Table: Comercial_SyncLog_v2_backup_migracion_codigos_20260513_0558
CREATE TABLE [Comercial_SyncLog_v2_backup_migracion_codigos_20260513_0558] (
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

-- Table: Comercial_Ventas_Dia_Abiertas_v2
CREATE TABLE [Comercial_Ventas_Dia_Abiertas_v2] (
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

-- Table: Comercial_Ventas_Dia_Abiertas_v2_Backup_FechaOperacion_20260521
CREATE TABLE [Comercial_Ventas_Dia_Abiertas_v2_Backup_FechaOperacion_20260521] (
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

-- Table: Comercial_Ventas_Dia_Abiertas_v2_backup_migracion_codigos_20260513_0558
CREATE TABLE [Comercial_Ventas_Dia_Abiertas_v2_backup_migracion_codigos_20260513_0558] (
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

-- Table: Compras
CREATE TABLE [Compras] (
    [CompraID] BIGINT NOT NULL,
    [Serie] VARCHAR(10) NULL,
    [FolioCompra] VARCHAR(30) NOT NULL,
    [PedidoCompraID] BIGINT NULL,
    [OrdenCompraID] BIGINT NULL,
    [EmpresaID] INT NULL,
    [SucursalID] INT NOT NULL,
    [AlmacenID] INT NULL,
    [TipoRegistroCompra] VARCHAR(20) NOT NULL,
    [FechaCompra] DATETIME2 NOT NULL,
    [FechaRecepcion] DATETIME2 NULL,
    [FechaFactura] DATE NULL,
    [FechaVencimiento] DATE NULL,
    [ProveedorID] INT NOT NULL,
    [CompradorUsuarioID] INT NULL,
    [RecibioUsuarioID] INT NULL,
    [CondicionPagoID] SMALLINT NULL,
    [FormaPagoID] SMALLINT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [TipoCambio] DECIMAL(18,6) NOT NULL,
    [NumeroFactura] VARCHAR(50) NULL,
    [UUIDFactura] VARCHAR(50) NULL,
    [ReferenciaProveedor] VARCHAR(100) NULL,
    [RequiereAutorizacion] BIT NOT NULL,
    [AutorizacionID] BIGINT NULL,
    [EstatusCompraID] TINYINT NOT NULL,
    [EsEntradaInventario] BIT NOT NULL,
    [GeneraCxP] BIT NOT NULL,
    [Subtotal] DECIMAL(18,2) NOT NULL,
    [DescuentoTotal] DECIMAL(18,2) NOT NULL,
    [ImpuestoTotal] DECIMAL(18,2) NOT NULL,
    [Total] DECIMAL(18,2) NOT NULL,
    [Observaciones] VARCHAR(1000) NULL,
    [ReferenciaExterna] VARCHAR(100) NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedAt] DATETIME2 NULL,
    [ModifiedBy] VARCHAR(100) NULL,
    [RowVer] TIMESTAMP NOT NULL
);
GO

-- Table: Compras_ConciliacionSAT
CREATE TABLE [Compras_ConciliacionSAT] (
    [ConciliacionSATID] BIGINT NOT NULL,
    [DocumentoFiscalID] BIGINT NOT NULL,
    [CompraID] BIGINT NULL,
    [RecepcionCompraID] BIGINT NULL,
    [EstatusConciliacionSATID] TINYINT NOT NULL,
    [FechaConciliacion] DATETIME2 NOT NULL,
    [UsuarioID] INT NULL,
    [RFCEmisorCoincide] BIT NOT NULL,
    [RFCReceptorCoincide] BIT NOT NULL,
    [FechaCoincide] BIT NOT NULL,
    [MonedaCoincide] BIT NOT NULL,
    [TotalCoincide] BIT NOT NULL,
    [UUIDDuplicado] BIT NOT NULL,
    [XMLValido] BIT NOT NULL,
    [PDFEncontrado] BIT NOT NULL,
    [DiferenciaSubtotal] DECIMAL(18,2) NOT NULL,
    [DiferenciaImpuesto] DECIMAL(18,2) NOT NULL,
    [DiferenciaTotal] DECIMAL(18,2) NOT NULL,
    [Observaciones] VARCHAR(2000) NULL,
    [RevisadoManual] BIT NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Compras_ConciliacionSATDetalle
CREATE TABLE [Compras_ConciliacionSATDetalle] (
    [ConciliacionSATDetalleID] BIGINT NOT NULL,
    [ConciliacionSATID] BIGINT NOT NULL,
    [RecepcionDetalleID] BIGINT NULL,
    [CompraDetalleID] BIGINT NULL,
    [DocumentoFiscalDetalleID] BIGINT NOT NULL,
    [ProductoID] INT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [CantidadSistema] DECIMAL(18,6) NOT NULL,
    [CantidadXML] DECIMAL(18,6) NOT NULL,
    [DiferenciaCantidad] DECIMAL(19,6) NULL,
    [CostoSistema] DECIMAL(18,6) NOT NULL,
    [CostoXML] DECIMAL(18,6) NOT NULL,
    [DiferenciaCosto] DECIMAL(19,6) NULL,
    [ImporteSistema] DECIMAL(18,2) NOT NULL,
    [ImporteXML] DECIMAL(18,2) NOT NULL,
    [DiferenciaImporte] DECIMAL(19,2) NULL,
    [Coincide] BIT NOT NULL,
    [Observaciones] VARCHAR(1000) NULL
);
GO

-- Table: Compras_ConciliacionSATEstatus
CREATE TABLE [Compras_ConciliacionSATEstatus] (
    [EstatusConciliacionSATID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(40) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Compras_Detalle
CREATE TABLE [Compras_Detalle] (
    [DetalleCompraID] BIGINT NOT NULL,
    [CompraID] BIGINT NOT NULL,
    [OrdenDetalleCompraID] BIGINT NULL,
    [PedidoDetalleCompraID] BIGINT NULL,
    [Renglon] INT NOT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [Cantidad] DECIMAL(18,6) NOT NULL,
    [CantidadDevuelta] DECIMAL(18,6) NOT NULL,
    [CantidadNeta] DECIMAL(19,6) NULL,
    [PrecioUnitario] DECIMAL(18,2) NOT NULL,
    [DescuentoPorcentaje] DECIMAL(9,4) NOT NULL,
    [DescuentoImporte] NUMERIC(38,6) NULL,
    [TasaImpuesto] DECIMAL(9,4) NOT NULL,
    [SubtotalLinea] NUMERIC(38,6) NULL,
    [ImpuestoImporte] NUMERIC(38,6) NULL,
    [TotalLinea] NUMERIC(38,6) NULL,
    [Lote] VARCHAR(50) NULL,
    [FechaCaducidad] DATE NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [RowVer] TIMESTAMP NOT NULL
);
GO

-- Table: Compras_DocumentosFiscales
CREATE TABLE [Compras_DocumentosFiscales] (
    [DocumentoFiscalID] BIGINT NOT NULL,
    [SucursalFiscalID] INT NOT NULL,
    [SucursalID] INT NOT NULL,
    [ProveedorID] INT NULL,
    [CompraID] BIGINT NULL,
    [RecepcionCompraID] BIGINT NULL,
    [EstatusDocumentoFiscalID] TINYINT NOT NULL,
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
    [TipoCambio] DECIMAL(18,6) NOT NULL,
    [Subtotal] DECIMAL(18,2) NOT NULL,
    [Descuento] DECIMAL(18,2) NOT NULL,
    [ImpuestoTrasladado] DECIMAL(18,2) NOT NULL,
    [ImpuestoRetenido] DECIMAL(18,2) NOT NULL,
    [Total] DECIMAL(18,2) NOT NULL,
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
    [OrigenDocumento] VARCHAR(20) NOT NULL,
    [Observaciones] VARCHAR(1000) NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [ModifiedAt] DATETIME2 NULL
);
GO

-- Table: Compras_DocumentosFiscalesDetalle
CREATE TABLE [Compras_DocumentosFiscalesDetalle] (
    [DocumentoFiscalDetalleID] BIGINT NOT NULL,
    [DocumentoFiscalID] BIGINT NOT NULL,
    [Renglon] INT NOT NULL,
    [ClaveProdServ] VARCHAR(20) NULL,
    [NoIdentificacion] VARCHAR(100) NULL,
    [DescripcionConcepto] VARCHAR(500) NULL,
    [UnidadSAT] VARCHAR(20) NULL,
    [UnidadInterna] VARCHAR(30) NULL,
    [Cantidad] DECIMAL(18,6) NOT NULL,
    [ValorUnitario] DECIMAL(18,6) NOT NULL,
    [Importe] DECIMAL(18,2) NOT NULL,
    [Descuento] DECIMAL(18,2) NOT NULL,
    [ProductoID] INT NULL,
    [PresentacionProductoID] BIGINT NULL
);
GO

-- Table: Compras_DocumentosFiscalesEstatus
CREATE TABLE [Compras_DocumentosFiscalesEstatus] (
    [EstatusDocumentoFiscalID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(40) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Compras_Estatus
CREATE TABLE [Compras_Estatus] (
    [EstatusCompraID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Compras_Eventos_Pendientes
CREATE TABLE [Compras_Eventos_Pendientes] (
    [EventoID] INT NOT NULL,
    [EventoTipo] NVARCHAR(50) NOT NULL,
    [ServerID] NVARCHAR(36) NOT NULL,
    [UnidadNegocioID] NVARCHAR(36) NULL,
    [Folio] NVARCHAR(50) NULL,
    [Fecha] DATETIME NULL,
    [DatosJSON] NVARCHAR(MAX) NULL,
    [Procesado] BIT NULL,
    [ProcesadoAt] DATETIME NULL,
    [InformeGenerado] BIT NULL,
    [InformeID] NVARCHAR(36) NULL,
    [ErrorMessage] NVARCHAR(500) NULL,
    [CreatedAt] DATETIME NULL
);
GO

-- Table: Compras_Informes_Config
CREATE TABLE [Compras_Informes_Config] (
    [ConfigID] INT NOT NULL,
    [EventoTipo] NVARCHAR(50) NOT NULL,
    [InformeTipo] NVARCHAR(100) NOT NULL,
    [Activo] BIT NULL,
    [WebhookURL] NVARCHAR(500) NULL,
    [EmailDestinatarios] NVARCHAR(500) NULL,
    [ConfigJSON] NVARCHAR(MAX) NULL,
    [CreatedAt] DATETIME NULL,
    [UpdatedAt] DATETIME NULL
);
GO

-- Table: Compras_Inventarios_Fisicos_Sync
CREATE TABLE [Compras_Inventarios_Fisicos_Sync] (
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
    [total_productos] INT NULL,
    [sync_source] VARCHAR(20) NULL,
    [sync_timestamp] DATETIME NULL,
    [sync_status] VARCHAR(20) NULL
);
GO

-- Table: Compras_KPIs_Historico
CREATE TABLE [Compras_KPIs_Historico] (
    [id] INT NOT NULL,
    [run_id] NVARCHAR(50) NOT NULL,
    [server_id] NVARCHAR(50) NOT NULL,
    [sucursal_id] NVARCHAR(50) NOT NULL,
    [system_type_normalized] NVARCHAR(50) NOT NULL,
    [fecha] DATE NOT NULL,
    [kpi_tipo] NVARCHAR(50) NOT NULL,
    [inv_conteos_count] INT NULL,
    [inv_productos_count] INT NULL,
    [inv_almacenes] NVARCHAR(500) NULL,
    [ped_pedidos_count] INT NULL,
    [ped_total_monto] DECIMAL(18,4) NULL,
    [ped_productos_count] INT NULL,
    [oc_ordenes_count] INT NULL,
    [oc_total_monto] DECIMAL(18,4) NULL,
    [oc_proveedores_count] INT NULL,
    [ec_entradas_count] INT NULL,
    [ec_total_monto] DECIMAL(18,4) NULL,
    [ec_productos_count] INT NULL,
    [empresa_id] NVARCHAR(50) NULL,
    [empresa_nombre] NVARCHAR(200) NULL,
    [created_at] DATETIME NULL,
    [updated_at] DATETIME NULL
);
GO

-- Table: Compras_Ordenes
CREATE TABLE [Compras_Ordenes] (
    [OrdenCompraID] BIGINT NOT NULL,
    [Serie] VARCHAR(10) NULL,
    [FolioOrden] VARCHAR(30) NOT NULL,
    [PedidoCompraID] BIGINT NULL,
    [EmpresaID] INT NULL,
    [SucursalID] INT NOT NULL,
    [AlmacenID] INT NULL,
    [FechaOrden] DATETIME2 NOT NULL,
    [FechaEntregaPrometida] DATE NULL,
    [ProveedorID] INT NOT NULL,
    [CompradorUsuarioID] INT NOT NULL,
    [SolicitanteUsuarioID] INT NULL,
    [CondicionPagoID] SMALLINT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [TipoCambio] DECIMAL(18,6) NOT NULL,
    [RequiereAutorizacion] BIT NOT NULL,
    [AutorizacionID] BIGINT NULL,
    [EstatusOrdenCompraID] TINYINT NOT NULL,
    [AtencionA] VARCHAR(150) NULL,
    [DireccionEntrega] VARCHAR(250) NULL,
    [ReferenciaProveedor] VARCHAR(100) NULL,
    [Observaciones] VARCHAR(1000) NULL,
    [TerminosCondiciones] VARCHAR(2000) NULL,
    [ReferenciaExterna] VARCHAR(100) NULL,
    [Subtotal] DECIMAL(18,2) NOT NULL,
    [DescuentoTotal] DECIMAL(18,2) NOT NULL,
    [ImpuestoTotal] DECIMAL(18,2) NOT NULL,
    [Total] DECIMAL(18,2) NOT NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedAt] DATETIME2 NULL,
    [ModifiedBy] VARCHAR(100) NULL,
    [RowVer] TIMESTAMP NOT NULL
);
GO

-- Table: Compras_OrdenesDetalle
CREATE TABLE [Compras_OrdenesDetalle] (
    [DetalleOrdenCompraID] BIGINT NOT NULL,
    [OrdenCompraID] BIGINT NOT NULL,
    [PedidoDetalleCompraID] BIGINT NULL,
    [Renglon] INT NOT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [Cantidad] DECIMAL(18,6) NOT NULL,
    [CantidadRecibida] DECIMAL(18,6) NOT NULL,
    [CantidadCancelada] DECIMAL(18,6) NOT NULL,
    [CantidadPendiente] DECIMAL(20,6) NULL,
    [PrecioUnitario] DECIMAL(18,2) NOT NULL,
    [DescuentoPorcentaje] DECIMAL(9,4) NOT NULL,
    [DescuentoImporte] NUMERIC(38,6) NULL,
    [TasaImpuesto] DECIMAL(9,4) NOT NULL,
    [SubtotalLinea] NUMERIC(38,6) NULL,
    [ImpuestoImporte] NUMERIC(38,6) NULL,
    [TotalLinea] NUMERIC(38,6) NULL,
    [FechaPromesaLinea] DATE NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [RowVer] TIMESTAMP NOT NULL
);
GO

-- Table: Compras_OrdenesEstatus
CREATE TABLE [Compras_OrdenesEstatus] (
    [EstatusOrdenCompraID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Compras_Parametros_Sucursal
CREATE TABLE [Compras_Parametros_Sucursal] (
    [ParametroID] INT NOT NULL,
    [ServerID] VARCHAR(100) NOT NULL,
    [SucursalID] VARCHAR(50) NOT NULL,
    [DiasInventario] INT NOT NULL,
    [ExcluirDomingos] BIT NOT NULL,
    [DiasInhabiles] NVARCHAR(MAX) NULL,
    [DiasTransitoProveedor] INT NOT NULL,
    [Activo] BIT NOT NULL,
    [CreadoPor] VARCHAR(100) NULL,
    [ModificadoPor] VARCHAR(100) NULL,
    [FechaCreacion] DATETIME NOT NULL,
    [FechaModificacion] DATETIME NOT NULL
);
GO

-- Table: Compras_Pedidos
CREATE TABLE [Compras_Pedidos] (
    [PedidoCompraID] BIGINT NOT NULL,
    [Serie] VARCHAR(10) NULL,
    [FolioPedido] VARCHAR(30) NOT NULL,
    [EmpresaID] INT NULL,
    [SucursalID] INT NOT NULL,
    [AlmacenID] INT NULL,
    [FechaPedido] DATETIME2 NOT NULL,
    [FechaRequerida] DATE NULL,
    [SolicitanteUsuarioID] INT NOT NULL,
    [CompradorUsuarioID] INT NULL,
    [ProveedorSugeridoID] INT NULL,
    [MonedaID] SMALLINT NULL,
    [TipoCambio] DECIMAL(18,6) NOT NULL,
    [Prioridad] VARCHAR(15) NOT NULL,
    [CentroCosto] VARCHAR(50) NULL,
    [Proyecto] VARCHAR(100) NULL,
    [MotivoCompra] VARCHAR(1000) NOT NULL,
    [RequiereAutorizacion] BIT NOT NULL,
    [AutorizacionID] BIGINT NULL,
    [EstatusPedidoCompraID] TINYINT NOT NULL,
    [Subtotal] DECIMAL(18,2) NOT NULL,
    [DescuentoTotal] DECIMAL(18,2) NOT NULL,
    [ImpuestoTotal] DECIMAL(18,2) NOT NULL,
    [Total] DECIMAL(18,2) NOT NULL,
    [Observaciones] VARCHAR(1000) NULL,
    [ReferenciaExterna] VARCHAR(100) NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedAt] DATETIME2 NULL,
    [ModifiedBy] VARCHAR(100) NULL,
    [RowVer] TIMESTAMP NOT NULL
);
GO

-- Table: Compras_PedidosDetalle
CREATE TABLE [Compras_PedidosDetalle] (
    [DetallePedidoCompraID] BIGINT NOT NULL,
    [PedidoCompraID] BIGINT NOT NULL,
    [Renglon] INT NOT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [Cantidad] DECIMAL(18,6) NOT NULL,
    [CantidadAtendida] DECIMAL(18,6) NOT NULL,
    [CantidadCancelada] DECIMAL(18,6) NOT NULL,
    [CantidadPendiente] DECIMAL(20,6) NULL,
    [PrecioEstimado] DECIMAL(18,2) NOT NULL,
    [DescuentoPorcentaje] DECIMAL(9,4) NOT NULL,
    [DescuentoImporte] NUMERIC(38,6) NULL,
    [TasaImpuesto] DECIMAL(9,4) NOT NULL,
    [SubtotalLinea] NUMERIC(38,6) NULL,
    [ImpuestoImporte] NUMERIC(38,6) NULL,
    [TotalLinea] NUMERIC(38,6) NULL,
    [FechaNecesaria] DATE NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [RowVer] TIMESTAMP NOT NULL
);
GO

-- Table: Compras_PedidosEstatus
CREATE TABLE [Compras_PedidosEstatus] (
    [EstatusPedidoCompraID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Compras_Recepciones
CREATE TABLE [Compras_Recepciones] (
    [RecepcionCompraID] BIGINT NOT NULL,
    [FolioRecepcion] VARCHAR(30) NOT NULL,
    [CompraID] BIGINT NULL,
    [OrdenCompraID] BIGINT NULL,
    [EmpresaID] INT NULL,
    [SucursalID] INT NOT NULL,
    [AlmacenID] INT NOT NULL,
    [ProveedorID] INT NOT NULL,
    [FechaRecepcion] DATETIME2 NOT NULL,
    [FechaDocumentoProveedor] DATE NULL,
    [DocumentoProveedor] VARCHAR(50) NULL,
    [EstatusRecepcionID] TINYINT NOT NULL,
    [RecibioUsuarioID] INT NULL,
    [RevisoUsuarioID] INT NULL,
    [MovimientoInventarioID] BIGINT NULL,
    [Subtotal] DECIMAL(18,2) NOT NULL,
    [ImpuestoTotal] DECIMAL(18,2) NOT NULL,
    [Total] DECIMAL(18,2) NOT NULL,
    [Observaciones] VARCHAR(1000) NULL,
    [TieneIncidencias] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [ModifiedAt] DATETIME2 NULL
);
GO

-- Table: Compras_RecepcionesDetalle
CREATE TABLE [Compras_RecepcionesDetalle] (
    [RecepcionDetalleID] BIGINT NOT NULL,
    [RecepcionCompraID] BIGINT NOT NULL,
    [CompraDetalleID] BIGINT NULL,
    [OrdenDetalleID] BIGINT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [Renglon] INT NOT NULL,
    [CantidadEsperada] DECIMAL(18,6) NOT NULL,
    [CantidadRecibida] DECIMAL(18,6) NOT NULL,
    [CantidadRechazada] DECIMAL(18,6) NOT NULL,
    [CantidadAceptada] DECIMAL(19,6) NULL,
    [CostoUnitario] DECIMAL(18,6) NOT NULL,
    [SubtotalLinea] DECIMAL(38,12) NULL,
    [Lote] VARCHAR(50) NULL,
    [FechaCaducidad] DATE NULL,
    [TieneIncidencia] BIT NOT NULL,
    [Observaciones] VARCHAR(500) NULL,
    [MovimientoDetalleID] BIGINT NULL,
    [CreatedAt] DATETIME2 NOT NULL
);
GO

-- Table: Compras_RecepcionesEstatus
CREATE TABLE [Compras_RecepcionesEstatus] (
    [EstatusRecepcionID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Compras_Requisiciones_Sync
CREATE TABLE [Compras_Requisiciones_Sync] (
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
    [total_productos] INT NULL,
    [importe] DECIMAL(18,2) NULL,
    [estatus] VARCHAR(50) NULL,
    [sync_source] VARCHAR(20) NULL,
    [sync_timestamp] DATETIME NULL,
    [sync_status] VARCHAR(20) NULL
);
GO

-- Table: Compras_Sync_Checkpoint
CREATE TABLE [Compras_Sync_Checkpoint] (
    [CheckpointID] INT NOT NULL,
    [ServerID] NVARCHAR(36) NOT NULL,
    [ServerName] NVARCHAR(100) NULL,
    [SyncType] NVARCHAR(50) NOT NULL,
    [LastFolio] NVARCHAR(50) NULL,
    [LastFecha] DATETIME NULL,
    [LastSyncAt] DATETIME NULL,
    [RecordsFoundLastSync] INT NULL,
    [CreatedAt] DATETIME NULL,
    [UpdatedAt] DATETIME NULL
);
GO

-- Table: Compras_Sync_Log
CREATE TABLE [Compras_Sync_Log] (
    [id] INT NOT NULL,
    [unidad_negocio_id] VARCHAR(50) NULL,
    [server_id] VARCHAR(50) NULL,
    [sync_type] VARCHAR(50) NULL,
    [sync_start] DATETIME NULL,
    [sync_end] DATETIME NULL,
    [records_synced] INT NULL,
    [status] VARCHAR(20) NULL,
    [error_message] TEXT NULL,
    [created_at] DATETIME NULL
);
GO

-- Table: Config_Asignaciones
CREATE TABLE [Config_Asignaciones] (
    [ID] INT NOT NULL,
    [ConfigID] VARCHAR(50) NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [AlmacenID] VARCHAR(50) NULL,
    [UsuarioResponsableID] VARCHAR(50) NOT NULL,
    [Prioridad] INT NULL,
    [Activa] BIT NULL,
    [FechaCreacion] DATETIME2 NULL,
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

-- Table: Config_Horarios
CREATE TABLE [Config_Horarios] (
    [Id] INT NOT NULL,
    [TenantID] INT NOT NULL,
    [NombrePeriodo] NVARCHAR(50) NULL,
    [HoraInicio] TIME NULL,
    [HoraFin] TIME NULL
);
GO

-- Table: Configuracion_Operativa
CREATE TABLE [Configuracion_Operativa] (
    [ID] INT NOT NULL,
    [Clave] VARCHAR(100) NOT NULL,
    [Valor] VARCHAR(500) NULL,
    [Tipo] VARCHAR(20) NULL,
    [Descripcion] VARCHAR(500) NULL,
    [FechaActualizacion] DATETIME2 NULL
);
GO

-- Table: ConsultasSQL_Catalogo
CREATE TABLE [ConsultasSQL_Catalogo] (
    [ConsultaID] INT NOT NULL,
    [PublicUUID] UNIQUEIDENTIFIER NOT NULL,
    [CodigoConsulta] VARCHAR(50) NOT NULL,
    [NombreConsulta] NVARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Modulo] VARCHAR(50) NOT NULL,
    [TipoConsulta] VARCHAR(30) NOT NULL,
    [SistemaTipoID] INT NOT NULL,
    [ConsultaSQL] NVARCHAR(MAX) NOT NULL,
    [EsSistema] BIT NOT NULL,
    [EsPersonalizada] BIT NOT NULL,
    [EsSincronizable] BIT NOT NULL,
    [PermiteEjecucionManual] BIT NOT NULL,
    [SoloLectura] BIT NOT NULL,
    [RequiereAutorizacion] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [Version] INT NOT NULL,
    [ConfigOrigen] VARCHAR(50) NOT NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [UsuarioCreacionID] NVARCHAR(100) NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacionID] NVARCHAR(100) NULL
);
GO

-- Table: ConsultasSQL_EjecucionesLog
CREATE TABLE [ConsultasSQL_EjecucionesLog] (
    [EjecucionID] BIGINT NOT NULL,
    [ConsultaID] INT NOT NULL,
    [ServidorID] UNIQUEIDENTIFIER NULL,
    [UsuarioID] NVARCHAR(100) NOT NULL,
    [FechaEjecucion] DATETIME2 NOT NULL,
    [ParametrosJSON] NVARCHAR(MAX) NULL,
    [ConsultaSQLEjecutada] NVARCHAR(MAX) NULL,
    [Estado] VARCHAR(20) NOT NULL,
    [DuracionMs] INT NULL,
    [RegistrosDevueltos] INT NULL,
    [ErrorMensaje] NVARCHAR(MAX) NULL,
    [IpOrigen] VARCHAR(50) NULL,
    [UserAgent] NVARCHAR(500) NULL
);
GO

-- Table: ConsultasSQL_Parametros
CREATE TABLE [ConsultasSQL_Parametros] (
    [ParametroID] INT NOT NULL,
    [ConsultaID] INT NOT NULL,
    [NombreParametro] VARCHAR(50) NOT NULL,
    [NombreMostrar] NVARCHAR(100) NULL,
    [TipoDato] VARCHAR(20) NOT NULL,
    [Requerido] BIT NOT NULL,
    [ValorDefault] NVARCHAR(200) NULL,
    [RegexValidacion] NVARCHAR(500) NULL,
    [ValorMinimo] NVARCHAR(100) NULL,
    [ValorMaximo] NVARCHAR(100) NULL,
    [ListaValoresJSON] NVARCHAR(MAX) NULL,
    [OrdenMostrar] INT NOT NULL,
    [ComponenteUI] VARCHAR(30) NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: ConsultasSQL_Permisos
CREATE TABLE [ConsultasSQL_Permisos] (
    [PermisoID] INT NOT NULL,
    [ConsultaID] INT NOT NULL,
    [RolID] NVARCHAR(100) NULL,
    [UsuarioID] NVARCHAR(100) NULL,
    [PuedeVer] BIT NOT NULL,
    [PuedeEjecutar] BIT NOT NULL,
    [PuedeEditar] BIT NOT NULL,
    [PuedeAutorizar] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [UsuarioCreacionID] NVARCHAR(100) NULL
);
GO

-- Table: ConsultasSQL_Servidores
CREATE TABLE [ConsultasSQL_Servidores] (
    [ConsultaServidorID] INT NOT NULL,
    [ConsultaID] INT NOT NULL,
    [ServidorID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] INT NULL,
    [SucursalID] NVARCHAR(50) NULL,
    [Activo] BIT NOT NULL,
    [Prioridad] INT NOT NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [UsuarioCreacionID] NVARCHAR(100) NULL
);
GO

-- Table: ConsultasSQL_Versiones
CREATE TABLE [ConsultasSQL_Versiones] (
    [VersionID] INT NOT NULL,
    [ConsultaID] INT NOT NULL,
    [Version] INT NOT NULL,
    [ConsultaSQL] NVARCHAR(MAX) NOT NULL,
    [ParametrosJSON] NVARCHAR(MAX) NULL,
    [MotivoCambio] NVARCHAR(500) NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [UsuarioCreacionID] NVARCHAR(100) NULL
);
GO

-- Table: CRM_Actividades
CREATE TABLE [CRM_Actividades] (
    [ActividadID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [TipoActividadID] INT NOT NULL,
    [EntidadTipo] NVARCHAR(20) NOT NULL,
    [EntidadID] UNIQUEIDENTIFIER NOT NULL,
    [Titulo] NVARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [Prioridad] INT NOT NULL,
    [FechaProgramada] DATETIME2 NOT NULL,
    [FechaFin] DATETIME2 NULL,
    [Duracion] INT NULL,
    [TodoElDia] BIT NOT NULL,
    [FechaRealizacion] DATETIME2 NULL,
    [ResultadoID] INT NULL,
    [Notas] NVARCHAR(MAX) NULL,
    [AsignadoAUserID] UNIQUEIDENTIFIER NOT NULL,
    [CreadoPorUserID] UNIQUEIDENTIFIER NOT NULL,
    [EstatusActividadID] INT NOT NULL,
    [TieneRecordatorio] BIT NOT NULL,
    [MinutosAntes] INT NULL,
    [RecordatorioEnviado] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [UpdatedAt] DATETIME2 NULL,
    [NotificacionEnviada] BIT NULL,
    [FechaNotificacion] DATETIME NULL
);
GO

-- Table: CRM_ActividadesHistorial
CREATE TABLE [CRM_ActividadesHistorial] (
    [HistorialActividadID] INT NOT NULL,
    [ActividadID] UNIQUEIDENTIFIER NOT NULL,
    [EstatusAnteriorID] INT NULL,
    [EstatusNuevoID] INT NOT NULL,
    [UsuarioModificadorID] UNIQUEIDENTIFIER NOT NULL,
    [FechaCambio] DATETIME2 NULL,
    [Comentario] NVARCHAR(500) NULL
);
GO

-- Table: CRM_Automation_Log
CREATE TABLE [CRM_Automation_Log] (
    [LogID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [ReglaID] UNIQUEIDENTIFIER NOT NULL,
    [OportunidadID] UNIQUEIDENTIFIER NULL,
    [TipoTrigger] NVARCHAR(50) NULL,
    [AccionEjecutada] NVARCHAR(100) NULL,
    [Exitoso] BIT NULL,
    [DetalleJSON] NVARCHAR(MAX) NULL,
    [MensajeError] NVARCHAR(500) NULL,
    [FechaEjecucion] DATETIME NULL
);
GO

-- Table: CRM_Automation_Reglas
CREATE TABLE [CRM_Automation_Reglas] (
    [ReglaID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [Nombre] NVARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [PipelineID] INT NULL,
    [TipoTrigger] NVARCHAR(50) NOT NULL,
    [CondicionJSON] NVARCHAR(MAX) NULL,
    [AccionJSON] NVARCHAR(MAX) NOT NULL,
    [Prioridad] INT NULL,
    [Activa] BIT NULL,
    [UsuarioCreacionID] UNIQUEIDENTIFIER NULL,
    [FechaCreacion] DATETIME NULL,
    [UsuarioModificacionID] UNIQUEIDENTIFIER NULL,
    [FechaModificacion] DATETIME NULL
);
GO

-- Table: CRM_Cat_EstatusActividad
CREATE TABLE [CRM_Cat_EstatusActividad] (
    [EstatusID] INT NOT NULL,
    [Nombre] NVARCHAR(50) NOT NULL,
    [Color] NVARCHAR(20) NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: CRM_Cat_EstatusContrato
CREATE TABLE [CRM_Cat_EstatusContrato] (
    [EstatusID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL,
    [ColorHex] NVARCHAR(7) NULL,
    [Activo] BIT NULL,
    [CreatedAt] DATETIME NULL
);
GO

-- Table: CRM_Cat_EstatusLead
CREATE TABLE [CRM_Cat_EstatusLead] (
    [EstatusID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL,
    [ColorHex] NVARCHAR(7) NULL,
    [EsFinal] BIT NULL,
    [Activo] BIT NULL,
    [CreatedAt] DATETIME NULL
);
GO

-- Table: CRM_Cat_EstatusOportunidad
CREATE TABLE [CRM_Cat_EstatusOportunidad] (
    [EstatusID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL,
    [ColorHex] NVARCHAR(7) NULL,
    [EsFinal] BIT NULL,
    [EsGanada] BIT NULL,
    [EsPerdida] BIT NULL,
    [Activo] BIT NULL,
    [CreatedAt] DATETIME NULL
);
GO

-- Table: CRM_Cat_EstatusPropuesta
CREATE TABLE [CRM_Cat_EstatusPropuesta] (
    [EstatusID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL,
    [ColorHex] NVARCHAR(7) NULL,
    [EsFinal] BIT NULL,
    [Activo] BIT NULL,
    [CreatedAt] DATETIME NULL
);
GO

-- Table: CRM_Cat_MotivosGanada
CREATE TABLE [CRM_Cat_MotivosGanada] (
    [MotivoID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL,
    [Activo] BIT NULL,
    [CreatedAt] DATETIME NULL
);
GO

-- Table: CRM_Cat_MotivosPerdida
CREATE TABLE [CRM_Cat_MotivosPerdida] (
    [MotivoID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL,
    [Activo] BIT NULL,
    [CreatedAt] DATETIME NULL
);
GO

-- Table: CRM_Cat_OrigenLead
CREATE TABLE [CRM_Cat_OrigenLead] (
    [OrigenID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL,
    [ColorHex] NVARCHAR(7) NULL,
    [Activo] BIT NULL,
    [CreatedAt] DATETIME NULL
);
GO

-- Table: CRM_Cat_Prioridades
CREATE TABLE [CRM_Cat_Prioridades] (
    [PrioridadID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL,
    [ColorHex] NVARCHAR(7) NULL,
    [Activo] BIT NULL,
    [CreatedAt] DATETIME NULL
);
GO

-- Table: CRM_Cat_Sectores
CREATE TABLE [CRM_Cat_Sectores] (
    [SectorID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL,
    [Activo] BIT NULL,
    [CreatedAt] DATETIME NULL
);
GO

-- Table: CRM_Cat_TamanosCliente
CREATE TABLE [CRM_Cat_TamanosCliente] (
    [TamanoID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [RangoEmpleadosMin] INT NULL,
    [RangoEmpleadosMax] INT NULL,
    [Orden] INT NULL,
    [Activo] BIT NULL,
    [CreatedAt] DATETIME NULL
);
GO

-- Table: CRM_Cat_TiposActividad
CREATE TABLE [CRM_Cat_TiposActividad] (
    [TipoID] INT NOT NULL,
    [Nombre] NVARCHAR(50) NOT NULL,
    [Icono] NVARCHAR(30) NULL,
    [Color] NVARCHAR(20) NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: CRM_Cat_TiposPipeline
CREATE TABLE [CRM_Cat_TiposPipeline] (
    [TipoID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL,
    [Activo] BIT NULL,
    [CreatedAt] DATETIME NULL
);
GO

-- Table: CRM_ClientesSolicitudesAlta
CREATE TABLE [CRM_ClientesSolicitudesAlta] (
    [SolicitudID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [SucursalID] UNIQUEIDENTIFIER NULL,
    [FolioSolicitud] NVARCHAR(20) NOT NULL,
    [OrigenEntidad] NVARCHAR(20) NOT NULL,
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
    [Pais] NVARCHAR(60) NULL,
    [CodigoPostal] NVARCHAR(10) NULL,
    [ContactoPrincipalNombre] NVARCHAR(200) NULL,
    [ContactoPrincipalEmail] NVARCHAR(150) NULL,
    [ContactoPrincipalTelefono] NVARCHAR(50) NULL,
    [ContactoPrincipalPuesto] NVARCHAR(100) NULL,
    [RequiereCredito] BIT NOT NULL,
    [LimiteCreditoSolicitado] DECIMAL(18,2) NULL,
    [DiasCreditoSolicitados] INT NULL,
    [CondicionesPagoSolicitadas] NVARCHAR(200) NULL,
    [ObservacionesSolicitante] NVARCHAR(MAX) NULL,
    [EstatusSolicitud] NVARCHAR(20) NOT NULL,
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
    [Activo] BIT NOT NULL,
    [CreatedBy] UNIQUEIDENTIFIER NULL,
    [UpdatedBy] UNIQUEIDENTIFIER NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [UpdatedAt] DATETIME2 NULL
);
GO

-- Table: CRM_ClientesSolicitudesAltaHistorial
CREATE TABLE [CRM_ClientesSolicitudesAltaHistorial] (
    [HistorialID] UNIQUEIDENTIFIER NOT NULL,
    [SolicitudID] UNIQUEIDENTIFIER NOT NULL,
    [EstatusAnterior] NVARCHAR(20) NULL,
    [EstatusNuevo] NVARCHAR(20) NOT NULL,
    [Comentario] NVARCHAR(500) NULL,
    [CambiadoPorUserID] UNIQUEIDENTIFIER NOT NULL,
    [FechaCambio] DATETIME2 NOT NULL
);
GO

-- Table: CRM_Config_PipelineEtapas
CREATE TABLE [CRM_Config_PipelineEtapas] (
    [EtapaID] INT NOT NULL,
    [PipelineID] INT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [ProbabilidadDefault] INT NULL,
    [Orden] INT NOT NULL,
    [ColorHex] NVARCHAR(7) NULL,
    [EsEtapaInicial] BIT NULL,
    [EsEtapaCierre] BIT NULL,
    [EsCierreGanado] BIT NULL,
    [EsCierrePerdido] BIT NULL,
    [DiasMaxSLA] INT NULL,
    [Activo] BIT NULL,
    [CreatedAt] DATETIME NULL,
    [UpdatedAt] DATETIME NULL,
    [DiasSLAMaximo] INT NULL
);
GO

-- Table: CRM_Config_Pipelines
CREATE TABLE [CRM_Config_Pipelines] (
    [PipelineID] INT NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [TipoPipelineID] INT NULL,
    [EsDefault] BIT NULL,
    [Orden] INT NULL,
    [Activo] BIT NULL,
    [CreatedAt] DATETIME NULL,
    [UpdatedAt] DATETIME NULL
);
GO

-- Table: CRM_Contratos
CREATE TABLE [CRM_Contratos] (
    [ContratoID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [CuentaID] UNIQUEIDENTIFIER NOT NULL,
    [OportunidadID] UNIQUEIDENTIFIER NULL,
    [PropuestaID] UNIQUEIDENTIFIER NULL,
    [FolioContrato] NVARCHAR(30) NULL,
    [NombreContrato] NVARCHAR(200) NOT NULL,
    [TipoContratoID] INT NULL,
    [DescripcionContrato] NVARCHAR(MAX) NULL,
    [MontoContrato] DECIMAL(18,2) NULL,
    [MonedaID] INT NULL,
    [FechaInicio] DATETIME NULL,
    [FechaFin] DATETIME NULL,
    [DuracionMeses] INT NULL,
    [RenovacionAutomatica] BIT NULL,
    [DiasAvisoRenovacion] INT NULL,
    [EstatusContratoID] INT NOT NULL,
    [Activo] BIT NULL,
    [CreatedBy] UNIQUEIDENTIFIER NULL,
    [UpdatedBy] UNIQUEIDENTIFIER NULL,
    [CreatedAt] DATETIME NULL,
    [UpdatedAt] DATETIME NULL
);
GO

-- Table: CRM_Cuentas
CREATE TABLE [CRM_Cuentas] (
    [CuentaID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [SucursalID] UNIQUEIDENTIFIER NULL,
    [ClienteID] INT NULL,
    [CodigoCuenta] NVARCHAR(20) NULL,
    [TipoCuenta] NVARCHAR(20) NOT NULL,
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
    [Pais] NVARCHAR(60) NULL,
    [CodigoPostal] NVARCHAR(10) NULL,
    [SitioWeb] NVARCHAR(200) NULL,
    [RedesSociales] NVARCHAR(500) NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [EstatusCuenta] NVARCHAR(20) NOT NULL,
    [Activo] BIT NOT NULL,
    [CreatedBy] UNIQUEIDENTIFIER NULL,
    [UpdatedBy] UNIQUEIDENTIFIER NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [UpdatedAt] DATETIME2 NULL
);
GO

-- Table: CRM_ERPSyncLog
CREATE TABLE [CRM_ERPSyncLog] (
    [ERPSyncID] INT NOT NULL,
    [PedidoID] BIGINT NOT NULL,
    [SistemaERP] VARCHAR(50) NOT NULL,
    [MetodoTransaccion] VARCHAR(50) NOT NULL,
    [PayloadRaw] NVARCHAR(MAX) NOT NULL,
    [EstatusERP] VARCHAR(50) NULL,
    [FechaRegistro] DATETIME NULL,
    [FechaProcesamiento] DATETIME NULL
);
GO

-- Table: CRM_Implementaciones
CREATE TABLE [CRM_Implementaciones] (
    [ImplementacionID] INT NOT NULL,
    [PedidoID] BIGINT NOT NULL,
    [CuentaID] UNIQUEIDENTIFIER NOT NULL,
    [NombreProyecto] VARCHAR(255) NOT NULL,
    [FechaKickoff] DATETIME NULL,
    [FechaEntregaEstimada] DATETIME NULL,
    [Estatus] VARCHAR(50) NULL,
    [UsuarioLiderID] INT NOT NULL,
    [ProgresoPorcentaje] INT NULL,
    [FechaCreacion] DATETIME NULL,
    [FechaModificacion] DATETIME NULL
);
GO

-- Table: CRM_ImplementacionesEntregables
CREATE TABLE [CRM_ImplementacionesEntregables] (
    [EntregableID] INT NOT NULL,
    [ImplementacionID] INT NOT NULL,
    [NombreEntregable] VARCHAR(255) NOT NULL,
    [Descripcion] VARCHAR(500) NULL,
    [Obligatorio] BIT NULL,
    [Estatus] VARCHAR(50) NULL,
    [FechaLimite] DATETIME NULL,
    [FechaAprobacion] DATETIME NULL,
    [UsuarioAprobadorID] INT NULL,
    [FechaCreacion] DATETIME NULL
);
GO

-- Table: CRM_Integracion_Conectores
CREATE TABLE [CRM_Integracion_Conectores] (
    [ConectorID] INT NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [Codigo] NVARCHAR(50) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [TipoConector] NVARCHAR(50) NOT NULL,
    [ConfiguracionJSON] NVARCHAR(MAX) NULL,
    [Activo] BIT NULL,
    [EsPrincipal] BIT NULL,
    [UltimaSincronizacion] DATETIME NULL,
    [EstadoConexion] NVARCHAR(50) NULL,
    [MensajeError] NVARCHAR(MAX) NULL,
    [MapeoLeadsJSON] NVARCHAR(MAX) NULL,
    [MapeoOportunidadesJSON] NVARCHAR(MAX) NULL,
    [MapeoCuentasJSON] NVARCHAR(MAX) NULL,
    [MapeoContactosJSON] NVARCHAR(MAX) NULL,
    [CreatedAt] DATETIME NULL,
    [CreatedBy] UNIQUEIDENTIFIER NULL,
    [UpdatedAt] DATETIME NULL,
    [UpdatedBy] UNIQUEIDENTIFIER NULL
);
GO

-- Table: CRM_Integracion_MapeoEtapas
CREATE TABLE [CRM_Integracion_MapeoEtapas] (
    [MapeoID] INT NOT NULL,
    [ConectorID] INT NOT NULL,
    [EtapaExterna] NVARCHAR(100) NOT NULL,
    [EtapaLocalID] INT NULL,
    [EtapaLocalNombre] NVARCHAR(100) NULL,
    [MapeoActivo] BIT NULL,
    [EsDefault] BIT NULL,
    [CreatedAt] DATETIME NULL
);
GO

-- Table: CRM_Integracion_SyncLog
CREATE TABLE [CRM_Integracion_SyncLog] (
    [LogID] BIGINT NOT NULL,
    [ConectorID] INT NOT NULL,
    [TipoEntidad] NVARCHAR(50) NOT NULL,
    [Operacion] NVARCHAR(50) NOT NULL,
    [FechaInicio] DATETIME NOT NULL,
    [FechaFin] DATETIME NULL,
    [Duracion] INT NULL,
    [RegistrosProcesados] INT NULL,
    [RegistrosCreados] INT NULL,
    [RegistrosActualizados] INT NULL,
    [RegistrosError] INT NULL,
    [RegistrosConflicto] INT NULL,
    [Estado] NVARCHAR(50) NOT NULL,
    [MensajeError] NVARCHAR(MAX) NULL,
    [DetallesJSON] NVARCHAR(MAX) NULL,
    [EjecutadoPor] UNIQUEIDENTIFIER NULL
);
GO

-- Table: CRM_IntegracionesConflictos
CREATE TABLE [CRM_IntegracionesConflictos] (
    [ConflictoID] INT NOT NULL,
    [SyncLogID] BIGINT NOT NULL,
    [ColumnaConflicto] VARCHAR(100) NOT NULL,
    [ValorHub] NVARCHAR(1000) NULL,
    [ValorExterno] NVARCHAR(1000) NULL,
    [Resuelto] BIT NULL,
    [ReglaAplicada] VARCHAR(100) NULL,
    [FechaConflicto] DATETIME NULL
);
GO

-- Table: CRM_IntegracionesSyncLog
CREATE TABLE [CRM_IntegracionesSyncLog] (
    [SyncLogID] BIGINT NOT NULL,
    [SistemaExterno] VARCHAR(50) NOT NULL,
    [EntidadCanonica] VARCHAR(100) NOT NULL,
    [IDExterno] VARCHAR(255) NOT NULL,
    [DataRawPayload] NVARCHAR(MAX) NOT NULL,
    [EstatusSync] VARCHAR(50) NULL,
    [FechaRegistro] DATETIME NULL,
    [FechaProcesamiento] DATETIME NULL
);
GO

-- Table: CRM_Leads
CREATE TABLE [CRM_Leads] (
    [LeadID] UNIQUEIDENTIFIER NOT NULL,
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
    [EstatusLeadID] INT NOT NULL,
    [PrioridadID] INT NULL,
    [CalificacionLeadID] INT NULL,
    [EjecutivoAsignadoUserID] UNIQUEIDENTIFIER NULL,
    [FechaAsignacion] DATETIME NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [Presupuesto] DECIMAL(18,2) NULL,
    [MonedaID] INT NULL,
    [FechaEstimadaCierre] DATETIME NULL,
    [ConvertidoACuenta] BIT NULL,
    [CuentaConvertidaID] UNIQUEIDENTIFIER NULL,
    [ContactoConvertidoID] UNIQUEIDENTIFIER NULL,
    [OportunidadConvertidaID] UNIQUEIDENTIFIER NULL,
    [FechaConversion] DATETIME NULL,
    [Descalificado] BIT NULL,
    [MotivoDescalificacionID] INT NULL,
    [FechaDescalificacion] DATETIME NULL,
    [NotasDescalificacion] NVARCHAR(500) NULL,
    [Activo] BIT NULL,
    [CreatedBy] UNIQUEIDENTIFIER NULL,
    [UpdatedBy] UNIQUEIDENTIFIER NULL,
    [CreatedAt] DATETIME NULL,
    [UpdatedAt] DATETIME NULL,
    [DeletedAt] DATETIME NULL
);
GO

-- Table: CRM_Oportunidad_Contactos
CREATE TABLE [CRM_Oportunidad_Contactos] (
    [ID] INT NOT NULL,
    [OportunidadID] UNIQUEIDENTIFIER NOT NULL,
    [ContactoID] UNIQUEIDENTIFIER NOT NULL,
    [RolContactoID] INT NULL,
    [EsPrincipal] BIT NULL,
    [Activo] BIT NULL,
    [CreatedAt] DATETIME NULL
);
GO

-- Table: CRM_Oportunidad_Documentos
CREATE TABLE [CRM_Oportunidad_Documentos] (
    [ID] INT NOT NULL,
    [OportunidadID] UNIQUEIDENTIFIER NOT NULL,
    [TipoDocumentoID] INT NULL,
    [NombreDocumento] NVARCHAR(200) NOT NULL,
    [RutaArchivo] NVARCHAR(500) NULL,
    [Extension] NVARCHAR(10) NULL,
    [TamanoBytes] BIGINT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Activo] BIT NULL,
    [CreatedBy] UNIQUEIDENTIFIER NULL,
    [CreatedAt] DATETIME NULL
);
GO

-- Table: CRM_Oportunidades
CREATE TABLE [CRM_Oportunidades] (
    [OportunidadID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [SucursalID] UNIQUEIDENTIFIER NULL,
    [FolioOportunidad] NVARCHAR(20) NULL,
    [CuentaID] UNIQUEIDENTIFIER NULL,
    [ContactoPrincipalID] UNIQUEIDENTIFIER NULL,
    [LeadOrigenID] UNIQUEIDENTIFIER NULL,
    [NombreOportunidad] NVARCHAR(200) NOT NULL,
    [DescripcionOportunidad] NVARCHAR(MAX) NULL,
    [PipelineID] INT NOT NULL,
    [EtapaActualID] INT NOT NULL,
    [ProbabilidadActual] INT NULL,
    [DiasEnEtapaActual] INT NULL,
    [MontoEstimado] DECIMAL(18,2) NULL,
    [MonedaID] INT NULL,
    [IngresoRecurrenteEstimado] DECIMAL(18,2) NULL,
    [IngresoNoRecurrenteEstimado] DECIMAL(18,2) NULL,
    [CostoEstimadoImplementacion] DECIMAL(18,2) NULL,
    [MargenEstimado] DECIMAL(18,2) NULL,
    [RequiereAprobacionDescuento] BIT NULL,
    [PorcentajeDescuento] DECIMAL(5,2) NULL,
    [MontoDescuento] DECIMAL(18,2) NULL,
    [FechaApertura] DATETIME NULL,
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
    [RequiereContrato] BIT NULL,
    [RequiereImplementacion] BIT NULL,
    [RequiereFacturacionProgramada] BIT NULL,
    [ObservacionesInternas] NVARCHAR(MAX) NULL,
    [EstatusOportunidadID] INT NOT NULL,
    [Activo] BIT NULL,
    [CreatedBy] UNIQUEIDENTIFIER NULL,
    [UpdatedBy] UNIQUEIDENTIFIER NULL,
    [CreatedAt] DATETIME NULL,
    [UpdatedAt] DATETIME NULL,
    [DeletedAt] DATETIME NULL
);
GO

-- Table: CRM_Oportunidades_HistorialEtapas
CREATE TABLE [CRM_Oportunidades_HistorialEtapas] (
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
    [FechaCambio] DATETIME NULL
);
GO

-- Table: CRM_OportunidadesHistorial
CREATE TABLE [CRM_OportunidadesHistorial] (
    [HistorialPipelineID] INT NOT NULL,
    [OportunidadID] UNIQUEIDENTIFIER NOT NULL,
    [EtapaAnteriorID] INT NULL,
    [EtapaNuevaID] INT NOT NULL,
    [MontoAnterior] DECIMAL(18,2) NULL,
    [MontoNuevo] DECIMAL(18,2) NOT NULL,
    [UsuarioModificadorID] UNIQUEIDENTIFIER NOT NULL,
    [FechaCambio] DATETIME NULL,
    [Comentario] NVARCHAR(500) NULL
);
GO

-- Table: CRM_PostventaEncuestas
CREATE TABLE [CRM_PostventaEncuestas] (
    [EncuestaID] INT NOT NULL,
    [CuentaID] UNIQUEIDENTIFIER NOT NULL,
    [TicketID] INT NULL,
    [PuntuacionCSAT] INT NOT NULL,
    [Comentarios] NVARCHAR(1000) NULL,
    [FechaRegistro] DATETIME NULL
);
GO

-- Table: CRM_PostventaTickets
CREATE TABLE [CRM_PostventaTickets] (
    [TicketID] INT NOT NULL,
    [CuentaID] UNIQUEIDENTIFIER NOT NULL,
    [FolioTicket] VARCHAR(50) NOT NULL,
    [Asunto] VARCHAR(255) NOT NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [Estatus] VARCHAR(50) NULL,
    [Prioridad] VARCHAR(30) NULL,
    [UsuarioAsignadoID] INT NOT NULL,
    [FechaCreacion] DATETIME NULL,
    [FechaModificacion] DATETIME NULL
);
GO

-- Table: CRM_Propuestas
CREATE TABLE [CRM_Propuestas] (
    [PropuestaID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [OportunidadID] UNIQUEIDENTIFIER NOT NULL,
    [FolioPropuesta] NVARCHAR(20) NULL,
    [NombrePropuesta] NVARCHAR(200) NOT NULL,
    [DescripcionPropuesta] NVARCHAR(MAX) NULL,
    [TipoPropuestaID] INT NULL,
    [VersionActual] INT NULL,
    [MontoTotal] DECIMAL(18,2) NULL,
    [MonedaID] INT NULL,
    [Descuento] DECIMAL(18,2) NULL,
    [IVA] DECIMAL(18,2) NULL,
    [MontoFinal] DECIMAL(18,2) NULL,
    [FechaCreacion] DATETIME NULL,
    [FechaEnvio] DATETIME NULL,
    [FechaVigencia] DATETIME NULL,
    [FechaRespuesta] DATETIME NULL,
    [EstatusPropuestaID] INT NOT NULL,
    [MotivoRechazoID] INT NULL,
    [NotasRechazo] NVARCHAR(500) NULL,
    [RequiereAprobacion] BIT NULL,
    [AprobadaPor] UNIQUEIDENTIFIER NULL,
    [FechaAprobacion] DATETIME NULL,
    [Activo] BIT NULL,
    [CreatedBy] UNIQUEIDENTIFIER NULL,
    [UpdatedBy] UNIQUEIDENTIFIER NULL,
    [CreatedAt] DATETIME NULL,
    [UpdatedAt] DATETIME NULL
);
GO

-- Table: CRM_Staging_Cuentas
CREATE TABLE [CRM_Staging_Cuentas] (
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
    [EstadoSync] NVARCHAR(50) NULL,
    [FechaExterna] DATETIME NULL,
    [FechaLocal] DATETIME NULL,
    [FechaProcesado] DATETIME NULL,
    [Intentos] INT NULL,
    [MensajeError] NVARCHAR(MAX) NULL,
    [CreatedAt] DATETIME NULL,
    [UpdatedAt] DATETIME NULL
);
GO

-- Table: CRM_Staging_Leads
CREATE TABLE [CRM_Staging_Leads] (
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
    [EstadoSync] NVARCHAR(50) NULL,
    [FechaExterna] DATETIME NULL,
    [FechaLocal] DATETIME NULL,
    [FechaProcesado] DATETIME NULL,
    [Intentos] INT NULL,
    [MensajeError] NVARCHAR(MAX) NULL,
    [CreatedAt] DATETIME NULL,
    [UpdatedAt] DATETIME NULL
);
GO

-- Table: CRM_Staging_Oportunidades
CREATE TABLE [CRM_Staging_Oportunidades] (
    [StagingID] BIGINT NOT NULL,
    [ConectorID] INT NOT NULL,
    [ExternalID] NVARCHAR(100) NOT NULL,
    [LocalOportunidadID] UNIQUEIDENTIFIER NULL,
    [NombreOportunidad] NVARCHAR(200) NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [MontoEstimado] DECIMAL(18,2) NULL,
    [Moneda] NVARCHAR(10) NULL,
    [FechaEstimadaCierre] DATE NULL,
    [Etapa] NVARCHAR(100) NULL,
    [Probabilidad] INT NULL,
    [Estatus] NVARCHAR(100) NULL,
    [ExternalCuentaID] NVARCHAR(100) NULL,
    [ExternalContactoID] NVARCHAR(100) NULL,
    [ExternalLeadID] NVARCHAR(100) NULL,
    [DatosExternosJSON] NVARCHAR(MAX) NULL,
    [DireccionSync] NVARCHAR(20) NOT NULL,
    [EstadoSync] NVARCHAR(50) NULL,
    [FechaExterna] DATETIME NULL,
    [FechaLocal] DATETIME NULL,
    [FechaProcesado] DATETIME NULL,
    [Intentos] INT NULL,
    [MensajeError] NVARCHAR(MAX) NULL,
    [CreatedAt] DATETIME NULL,
    [UpdatedAt] DATETIME NULL
);
GO

-- Table: CRM_Tareas
CREATE TABLE [CRM_Tareas] (
    [TareaID] NVARCHAR(50) NOT NULL,
    [EmpresaID] NVARCHAR(50) NOT NULL,
    [OportunidadID] NVARCHAR(50) NULL,
    [ResponsableID] NVARCHAR(50) NULL,
    [Titulo] NVARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(1000) NULL,
    [FechaVencimiento] DATETIME NULL,
    [Prioridad] NVARCHAR(20) NULL,
    [EstatusID] INT NULL,
    [AutoGenerada] BIT NULL,
    [FechaCreacion] DATETIME NULL,
    [FechaCompletada] DATETIME NULL
);
GO

-- Table: CRM_Trigger_Log
CREATE TABLE [CRM_Trigger_Log] (
    [LogID] NVARCHAR(50) NOT NULL,
    [TriggerID] NVARCHAR(50) NOT NULL,
    [EntidadID] NVARCHAR(50) NULL,
    [EmpresaID] NVARCHAR(50) NOT NULL,
    [Exitoso] BIT NULL,
    [ResultadoJSON] NVARCHAR(MAX) NULL,
    [FechaEjecucion] DATETIME NULL
);
GO

-- Table: CRM_Triggers
CREATE TABLE [CRM_Triggers] (
    [TriggerID] NVARCHAR(50) NOT NULL,
    [EmpresaID] NVARCHAR(50) NOT NULL,
    [Nombre] NVARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [TipoEvento] NVARCHAR(50) NOT NULL,
    [CondicionesJSON] NVARCHAR(MAX) NULL,
    [AccionesJSON] NVARCHAR(MAX) NOT NULL,
    [Prioridad] INT NULL,
    [Activo] BIT NULL,
    [UsuarioCreacionID] NVARCHAR(50) NULL,
    [FechaCreacion] DATETIME NULL,
    [FechaModificacion] DATETIME NULL
);
GO

-- Table: Fact_Ventas_Consolidadas
CREATE TABLE [Fact_Ventas_Consolidadas] (
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

-- Table: Finanzas_Cat_CuentasBancarias
CREATE TABLE [Finanzas_Cat_CuentasBancarias] (
    [CuentaBancariaID] INT NOT NULL,
    [EmpresaID] INT NULL,
    [BancoID] INT NULL,
    [NumeroCuenta] VARCHAR(20) NOT NULL,
    [CLABE] VARCHAR(18) NULL,
    [Alias] VARCHAR(50) NOT NULL,
    [Moneda] VARCHAR(3) NOT NULL,
    [EsCuentaPrincipal] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [UsuarioCreacionID] INT NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacionID] INT NULL
);
GO

-- Table: Finanzas_Cat_EstatusCuadreZ
CREATE TABLE [Finanzas_Cat_EstatusCuadreZ] (
    [EstatusCuadreID] TINYINT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Descripcion] NVARCHAR(50) NOT NULL,
    [ColorHex] NVARCHAR(7) NOT NULL,
    [Orden] TINYINT NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Finanzas_Cat_EstatusTesoreria
CREATE TABLE [Finanzas_Cat_EstatusTesoreria] (
    [EstatusTesoreriaID] TINYINT NOT NULL,
    [Codigo] NVARCHAR(20) NOT NULL,
    [Descripcion] NVARCHAR(50) NOT NULL,
    [ColorHex] NVARCHAR(7) NOT NULL,
    [Orden] TINYINT NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Finanzas_ConfiguracionTPV_Sucursal
CREATE TABLE [Finanzas_ConfiguracionTPV_Sucursal] (
    [ConfiguracionTPVID] INT NOT NULL,
    [SucursalID] INT NOT NULL,
    [ProveedorTPV] VARCHAR(50) NOT NULL,
    [ComisionDebito] DECIMAL(5,3) NOT NULL,
    [ComisionCredito] DECIMAL(5,3) NOT NULL,
    [ComisionAmex] DECIMAL(5,3) NOT NULL,
    [ComisionInternacional] DECIMAL(5,3) NOT NULL,
    [AplicaIVAComision] BIT NOT NULL,
    [PorcentajeIVA] DECIMAL(5,2) NOT NULL,
    [DiasDepositoDebito] INT NOT NULL,
    [DiasDepositoCredito] INT NOT NULL,
    [DiasDepositoAmex] INT NOT NULL,
    [DiasDepositoInternacional] INT NOT NULL,
    [DiasDepositoEfectivo] INT NOT NULL,
    [EfectivoFinDeSemanaLunes] BIT NOT NULL,
    [CuentaBancariaID] INT NULL,
    [NumeroAfiliacion] VARCHAR(50) NULL,
    [TerminalID] VARCHAR(50) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Finanzas_CortesCaja
CREATE TABLE [Finanzas_CortesCaja] (
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
    [FechaAlta] DATETIME2 NOT NULL,
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
    [Propinas] DECIMAL(18,2) NULL,
    [Retiros] DECIMAL(18,2) NULL,
    [FondoInicial] DECIMAL(18,2) NULL,
    [TotalVenta] DECIMAL(18,2) NULL,
    [HashOrigen] NVARCHAR(64) NULL,
    [FechaSincronizacion] DATETIME2 NULL,
    [FechaUltimaActualizacion] DATETIME2 NULL,
    [EsDemo] BIT NULL
);
GO

-- Table: Finanzas_CortesCaja_Backup_Demo_20260501
CREATE TABLE [Finanzas_CortesCaja_Backup_Demo_20260501] (
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

-- Table: Finanzas_CortesCaja_DetallePagos
CREATE TABLE [Finanzas_CortesCaja_DetallePagos] (
    [DetalleID] BIGINT NOT NULL,
    [CorteCajaID] BIGINT NOT NULL,
    [FormaPago] NVARCHAR(50) NOT NULL,
    [FormaPagoCodigo] NVARCHAR(10) NULL,
    [Importe] DECIMAL(18,2) NOT NULL,
    [Referencia] NVARCHAR(100) NULL,
    [SistemaOrigen] NVARCHAR(20) NULL,
    [IdOrigen] BIGINT NULL,
    [HashOrigen] NVARCHAR(64) NULL,
    [FechaAlta] DATETIME2 NULL,
    [Activo] BIT NULL
);
GO

-- Table: Finanzas_CortesCaja_SyncLog
CREATE TABLE [Finanzas_CortesCaja_SyncLog] (
    [LogID] BIGINT NOT NULL,
    [FechaInicio] DATETIME2 NOT NULL,
    [FechaFin] DATETIME2 NULL,
    [UnidadNegocioID] NVARCHAR(50) NULL,
    [ServerID] NVARCHAR(50) NULL,
    [SistemaOrigen] NVARCHAR(20) NULL,
    [FechaDesde] DATE NULL,
    [FechaHasta] DATE NULL,
    [RegistrosLeidos] INT NULL,
    [RegistrosInsertados] INT NULL,
    [RegistrosActualizados] INT NULL,
    [RegistrosOmitidos] INT NULL,
    [RegistrosError] INT NULL,
    [Estatus] NVARCHAR(20) NULL,
    [ErrorMensaje] NVARCHAR(MAX) NULL,
    [DuracionSegundos] INT NULL,
    [UsuarioEjecucion] NVARCHAR(50) NULL,
    [TipoEjecucion] NVARCHAR(20) NULL
);
GO

-- Table: Finanzas_CuadresZ
CREATE TABLE [Finanzas_CuadresZ] (
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
    [TotalVenta] DECIMAL(18,2) NOT NULL,
    [TotalEfectivo] DECIMAL(18,2) NOT NULL,
    [TotalTarjetaDebito] DECIMAL(18,2) NOT NULL,
    [TotalTarjetaCredito] DECIMAL(18,2) NOT NULL,
    [TotalAmex] DECIMAL(18,2) NOT NULL,
    [TotalTarjetaTotal] DECIMAL(18,2) NOT NULL,
    [TotalTransferencia] DECIMAL(18,2) NOT NULL,
    [TotalVales] DECIMAL(18,2) NOT NULL,
    [TotalOtros] DECIMAL(18,2) NOT NULL,
    [TotalPropinasTPV] DECIMAL(18,2) NOT NULL,
    [TotalPropinasEfectivo] DECIMAL(18,2) NOT NULL,
    [TotalRetiros] DECIMAL(18,2) NOT NULL,
    [FondoInicial] DECIMAL(18,2) NOT NULL,
    [TotalDepositar] DECIMAL(18,2) NOT NULL,
    [TotalDeclarado] DECIMAL(18,2) NOT NULL,
    [Diferencia] DECIMAL(18,2) NOT NULL,
    [ConteoEfectivo_Billetes1000] INT NOT NULL,
    [ConteoEfectivo_Billetes500] INT NOT NULL,
    [ConteoEfectivo_Billetes200] INT NOT NULL,
    [ConteoEfectivo_Billetes100] INT NOT NULL,
    [ConteoEfectivo_Billetes50] INT NOT NULL,
    [ConteoEfectivo_Billetes20] INT NOT NULL,
    [ConteoEfectivo_Monedas20] INT NOT NULL,
    [ConteoEfectivo_Monedas10] INT NOT NULL,
    [ConteoEfectivo_Monedas5] INT NOT NULL,
    [ConteoEfectivo_Monedas2] INT NOT NULL,
    [ConteoEfectivo_Monedas1] INT NOT NULL,
    [ConteoEfectivo_Monedas050] INT NOT NULL,
    [ConteoEfectivo_Total] DECIMAL(18,2) NOT NULL,
    [FichaDepositoURL] NVARCHAR(500) NULL,
    [FichaDepositoFecha] DATE NULL,
    [FichaDepositoMonto] DECIMAL(18,2) NULL,
    [FichaDepositoValidada] BIT NOT NULL,
    [FichaDepositoBancoID] INT NULL,
    [FichaDepositoCuentaID] INT NULL,
    [EstatusCuadreID] TINYINT NOT NULL,
    [EstatusTesoreriaID] TINYINT NOT NULL,
    [Observaciones] NVARCHAR(500) NULL,
    [UsuarioCapturaID] NVARCHAR(50) NULL,
    [UsuarioCapturaNombre] NVARCHAR(100) NULL,
    [FechaCaptura] DATETIME2 NULL,
    [UsuarioValidaID] NVARCHAR(50) NULL,
    [UsuarioValidaNombre] NVARCHAR(100) NULL,
    [FechaValidacion] DATETIME2 NULL,
    [CorteCajaID] BIGINT NULL,
    [FuenteOriginal] NVARCHAR(20) NOT NULL,
    [IdOrigen] NVARCHAR(50) NULL,
    [HashOrigen] NVARCHAR(64) NULL,
    [EsDemo] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaSincronizacion] DATETIME2 NULL,
    [FechaUltimaActualizacion] DATETIME2 NULL
);
GO

-- Table: Finanzas_CuadresZ_SyncLog
CREATE TABLE [Finanzas_CuadresZ_SyncLog] (
    [LogID] BIGINT NOT NULL,
    [JobName] NVARCHAR(50) NOT NULL,
    [TipoOperacion] NVARCHAR(20) NOT NULL,
    [UnidadNegocioID] NVARCHAR(50) NULL,
    [UnidadNegocioNombre] NVARCHAR(100) NULL,
    [FechaDesde] DATE NULL,
    [FechaHasta] DATE NULL,
    [RegistrosLeidos] INT NOT NULL,
    [RegistrosInsertados] INT NOT NULL,
    [RegistrosActualizados] INT NOT NULL,
    [RegistrosOmitidos] INT NOT NULL,
    [RegistrosError] INT NOT NULL,
    [MensajeError] NVARCHAR(MAX) NULL,
    [FechaInicio] DATETIME2 NOT NULL,
    [FechaFin] DATETIME2 NULL,
    [DuracionMs] INT NULL,
    [UsuarioID] NVARCHAR(50) NULL,
    [UsuarioNombre] NVARCHAR(100) NULL,
    [Estatus] NVARCHAR(20) NOT NULL,
    [Metadata] NVARCHAR(MAX) NULL
);
GO

-- Table: Finanzas_CuentasPorPagar
CREATE TABLE [Finanzas_CuentasPorPagar] (
    [CuentaPorPagarID] BIGINT NOT NULL,
    [DocumentoFiscalID] BIGINT NULL,
    [ProveedorID] INT NOT NULL,
    [SucursalID] INT NOT NULL,
    [NumeroDocumento] VARCHAR(50) NOT NULL,
    [FechaDocumento] DATE NOT NULL,
    [FechaVencimiento] DATE NOT NULL,
    [FechaRecepcion] DATE NULL,
    [MontoOriginal] DECIMAL(18,2) NOT NULL,
    [MontoPagado] DECIMAL(18,2) NOT NULL,
    [MonedaID] INT NOT NULL,
    [TipoCambio] DECIMAL(18,6) NOT NULL,
    [EstatusPagoID] TINYINT NOT NULL,
    [DiasCredito] INT NOT NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Finanzas_Depositos
CREATE TABLE [Finanzas_Depositos] (
    [DepositoID] BIGINT NOT NULL,
    [CuentaBancariaID] INT NOT NULL,
    [SucursalID] INT NOT NULL,
    [FechaDeposito] DATE NOT NULL,
    [MontoDeposito] DECIMAL(18,2) NOT NULL,
    [TipoDeposito] VARCHAR(20) NOT NULL,
    [NumeroReferencia] VARCHAR(50) NULL,
    [CorteCajaID] BIGINT NULL,
    [Conciliado] BIT NOT NULL,
    [FechaConciliacion] DATE NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL
);
GO

-- Table: Finanzas_EstatusCierre
CREATE TABLE [Finanzas_EstatusCierre] (
    [EstatusCierreID] TINYINT NOT NULL,
    [Codigo] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Finanzas_EstatusPago
CREATE TABLE [Finanzas_EstatusPago] (
    [EstatusPagoID] TINYINT NOT NULL,
    [Codigo] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [ColorHex] VARCHAR(7) NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Finanzas_KPIs_Historico
CREATE TABLE [Finanzas_KPIs_Historico] (
    [id] INT NOT NULL,
    [run_id] VARCHAR(50) NOT NULL,
    [server_id] VARCHAR(100) NOT NULL,
    [sucursal_id] VARCHAR(100) NOT NULL,
    [system_type_normalized] VARCHAR(50) NOT NULL,
    [fecha] DATE NOT NULL,
    [kpi_tipo] VARCHAR(50) NOT NULL,
    [ventas_efectivo] DECIMAL(18,2) NULL,
    [ventas_tarjeta_debito] DECIMAL(18,2) NULL,
    [ventas_tarjeta_credito] DECIMAL(18,2) NULL,
    [ventas_tarjeta_amex] DECIMAL(18,2) NULL,
    [ventas_otros] DECIMAL(18,2) NULL,
    [ventas_total] DECIMAL(18,2) NULL,
    [propinas] DECIMAL(18,2) NULL,
    [comision_debito] DECIMAL(18,2) NULL,
    [comision_credito] DECIMAL(18,2) NULL,
    [comision_amex] DECIMAL(18,2) NULL,
    [comision_total] DECIMAL(18,2) NULL,
    [cxp_facturas_count] INT NULL,
    [cxp_monto_total] DECIMAL(18,2) NULL,
    [cxp_monto_alimentos] DECIMAL(18,2) NULL,
    [cxp_monto_bebidas] DECIMAL(18,2) NULL,
    [cxp_monto_otros] DECIMAL(18,2) NULL,
    [cxp_saldo_pendiente] DECIMAL(18,2) NULL,
    [flujo_efectivo_neto] DECIMAL(18,2) NULL,
    [empresa_id] VARCHAR(100) NULL,
    [empresa_nombre] NVARCHAR(200) NULL,
    [origen] VARCHAR(50) NULL,
    [fecha_carga] DATETIME NULL,
    [fecha_actualizacion] DATETIME NULL
);
GO

-- Table: Finanzas_Pagos
CREATE TABLE [Finanzas_Pagos] (
    [PagoID] BIGINT NOT NULL,
    [CuentaPorPagarID] BIGINT NOT NULL,
    [FechaPago] DATE NOT NULL,
    [MontoPagado] DECIMAL(18,2) NOT NULL,
    [FormaPagoID] INT NULL,
    [CuentaBancariaID] INT NULL,
    [NumeroReferencia] VARCHAR(50) NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL
);
GO

-- Table: Finanzas_Presupuestos
CREATE TABLE [Finanzas_Presupuestos] (
    [PresupuestoID] INT NOT NULL,
    [SucursalID] INT NOT NULL,
    [Categoria] NVARCHAR(100) NOT NULL,
    [SubCategoria] NVARCHAR(100) NULL,
    [Tipo] NVARCHAR(20) NOT NULL,
    [Monto_Presupuestado] DECIMAL(18,2) NULL,
    [Monto_Ejecutado] DECIMAL(18,2) NULL,
    [Anio] INT NOT NULL,
    [Mes] INT NOT NULL,
    [Notas] NVARCHAR(500) NULL,
    [Fecha_Creacion] DATETIME NULL,
    [Fecha_Modificacion] DATETIME NULL,
    [Creado_Por] NVARCHAR(100) NULL
);
GO

-- Table: Finanzas_PropinasTPV_SyncLog
CREATE TABLE [Finanzas_PropinasTPV_SyncLog] (
    [LogID] BIGINT NOT NULL,
    [FechaInicio] DATETIME2 NOT NULL,
    [FechaFin] DATETIME2 NULL,
    [UnidadNegocioID] UNIQUEIDENTIFIER NULL,
    [UnidadNegocioNombre] NVARCHAR(100) NULL,
    [ServerID] NVARCHAR(50) NULL,
    [SistemaOrigen] NVARCHAR(20) NULL,
    [BaseDatosOrigen] NVARCHAR(100) NULL,
    [FechaDesde] DATE NULL,
    [FechaHasta] DATE NULL,
    [RegistrosLeidos] INT NOT NULL,
    [RegistrosInsertados] INT NOT NULL,
    [RegistrosActualizados] INT NOT NULL,
    [RegistrosOmitidos] INT NOT NULL,
    [RegistrosConError] INT NOT NULL,
    [TotalPropinasTPV] DECIMAL(18,2) NULL,
    [Estatus] NVARCHAR(20) NOT NULL,
    [ErrorMensaje] NVARCHAR(MAX) NULL,
    [TipoEjecucion] NVARCHAR(20) NOT NULL,
    [UsuarioEjecucion] NVARCHAR(100) NULL,
    [HashMuestra] NVARCHAR(64) NULL,
    [DuracionSegundos] INT NULL
);
GO

-- Table: Finanzas_SaldosBancarios
CREATE TABLE [Finanzas_SaldosBancarios] (
    [SaldoBancarioID] BIGINT NOT NULL,
    [CuentaBancariaID] INT NOT NULL,
    [FechaSaldo] DATE NOT NULL,
    [SaldoFinal] DECIMAL(18,2) NOT NULL,
    [Moneda] VARCHAR(3) NOT NULL,
    [TipoCambio] DECIMAL(10,4) NULL,
    [FuenteDatos] VARCHAR(20) NOT NULL,
    [Observaciones] VARCHAR(500) NULL,
    [EsVigente] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [Estatus] VARCHAR(20) NOT NULL,
    [UsuarioCreacionID] INT NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [UsuarioModificacionID] INT NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioCancelacionID] INT NULL,
    [FechaCancelacion] DATETIME2 NULL,
    [MotivoCancelacion] VARCHAR(500) NULL
);
GO

-- Table: Global_Cat_Bancos
CREATE TABLE [Global_Cat_Bancos] (
    [BancoID] INT NOT NULL,
    [CodigoBanco] VARCHAR(10) NOT NULL,
    [NombreBanco] VARCHAR(100) NOT NULL,
    [NombreCorto] VARCHAR(50) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL
);
GO

-- Table: Global_Cat_FormaPagoSAT
CREATE TABLE [Global_Cat_FormaPagoSAT] (
    [FormaPagoID] INT NOT NULL,
    [Clave] VARCHAR(5) NOT NULL,
    [Descripcion] VARCHAR(150) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Inventario_Almacenes
CREATE TABLE [Inventario_Almacenes] (
    [AlmacenID] INT NOT NULL,
    [EmpresaID] INT NULL,
    [SucursalID] INT NOT NULL,
    [CodigoAlmacen] VARCHAR(20) NOT NULL,
    [NombreAlmacen] VARCHAR(120) NOT NULL,
    [TipoAlmacen] VARCHAR(20) NOT NULL,
    [PermiteCompras] BIT NOT NULL,
    [PermiteVentas] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Inventario_Existencias
CREATE TABLE [Inventario_Existencias] (
    [ExistenciaID] BIGINT NOT NULL,
    [EmpresaID] INT NULL,
    [SucursalID] INT NOT NULL,
    [AlmacenID] INT NOT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [ExistenciaActual] DECIMAL(18,6) NOT NULL,
    [CostoPromedio] DECIMAL(18,6) NOT NULL,
    [UltimaFechaMovimiento] DATETIME2 NULL,
    [UltimoMovimientoDetalleID] BIGINT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Inventario_Movimientos
CREATE TABLE [Inventario_Movimientos] (
    [MovimientoID] BIGINT NOT NULL,
    [TipoMovimientoID] TINYINT NOT NULL,
    [EmpresaID] INT NULL,
    [SucursalID] INT NOT NULL,
    [AlmacenID] INT NOT NULL,
    [FechaMovimiento] DATETIME2 NOT NULL,
    [ReferenciaTipo] VARCHAR(30) NOT NULL,
    [ReferenciaID] BIGINT NULL,
    [FolioReferencia] VARCHAR(50) NULL,
    [Observaciones] VARCHAR(1000) NULL,
    [UsuarioID] INT NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL
);
GO

-- Table: Inventario_MovimientosDetalle
CREATE TABLE [Inventario_MovimientosDetalle] (
    [MovimientoDetalleID] BIGINT NOT NULL,
    [MovimientoID] BIGINT NOT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [Cantidad] DECIMAL(18,6) NOT NULL,
    [CostoUnitario] DECIMAL(18,6) NOT NULL,
    [Importe] DECIMAL(37,12) NULL,
    [Lote] VARCHAR(50) NULL,
    [FechaCaducidad] DATE NULL,
    [ReferenciaDetalleTipo] VARCHAR(30) NULL,
    [ReferenciaDetalleID] BIGINT NULL,
    [CreatedAt] DATETIME2 NOT NULL
);
GO

-- Table: Inventario_TipoMovimiento
CREATE TABLE [Inventario_TipoMovimiento] (
    [TipoMovimientoID] TINYINT NOT NULL,
    [Codigo] VARCHAR(30) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [Naturaleza] CHAR(1) NOT NULL,
    [AfectaCostoPromedio] BIT NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Inventarios_SinAsignar
CREATE TABLE [Inventarios_SinAsignar] (
    [ID] INT NOT NULL,
    [RegistroID] VARCHAR(50) NOT NULL,
    [ServerID] VARCHAR(50) NULL,
    [ServerName] VARCHAR(100) NULL,
    [SucursalID] VARCHAR(100) NULL,
    [SucursalNombre] VARCHAR(100) NULL,
    [AlmacenID] VARCHAR(50) NULL,
    [AlmacenNombre] VARCHAR(100) NULL,
    [FolioInventario] VARCHAR(100) NULL,
    [TotalDiferencias] INT NULL,
    [ValorDiferencias] DECIMAL(18,2) NULL,
    [FechaDeteccion] DATETIME2 NULL,
    [Estado] VARCHAR(50) NULL,
    [Notificado] BIT NULL
);
GO

-- Table: Operaciones_Tablaje_Auditoria
CREATE TABLE [Operaciones_Tablaje_Auditoria] (
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
    [Modulo] NVARCHAR(50) NULL,
    [FechaOperacionMexico] DATE NOT NULL,
    [FechaHoraUTC] DATETIME2 NOT NULL
);
GO

-- Table: Operaciones_Tablaje_Autorizaciones
CREATE TABLE [Operaciones_Tablaje_Autorizaciones] (
    [AutorizacionID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [UnidadNegocioID] UNIQUEIDENTIFIER NULL,
    [TipoAutorizacion] NVARCHAR(100) NOT NULL,
    [EntidadTipo] NVARCHAR(50) NOT NULL,
    [EntidadID] UNIQUEIDENTIFIER NOT NULL,
    [EntidadFolio] NVARCHAR(100) NULL,
    [SolicitanteID] UNIQUEIDENTIFIER NOT NULL,
    [FechaSolicitudUTC] DATETIME2 NOT NULL,
    [MotivoSolicitud] NVARCHAR(1000) NOT NULL,
    [DatosSolicitudJSON] NVARCHAR(MAX) NULL,
    [Estatus] NVARCHAR(50) NOT NULL,
    [AutorizadorID] UNIQUEIDENTIFIER NULL,
    [FechaResolucionUTC] DATETIME2 NULL,
    [Comentarios] NVARCHAR(1000) NULL,
    [NivelEscalamiento] INT NOT NULL,
    [FechaExpiracion] DATETIME2 NULL,
    [FechaOperacionMexico] DATE NOT NULL
);
GO

-- Table: Operaciones_Tablaje_Costos
CREATE TABLE [Operaciones_Tablaje_Costos] (
    [CostoID] UNIQUEIDENTIFIER NOT NULL,
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
    [MonedaID] INT NOT NULL,
    [TipoCambio] DECIMAL(18,6) NULL,
    [EsCostoFinal] BIT NOT NULL,
    [FechaCalculoUTC] DATETIME2 NOT NULL,
    [UsuarioCalculoID] UNIQUEIDENTIFIER NULL
);
GO

-- Table: Operaciones_Tablaje_Documentos
CREATE TABLE [Operaciones_Tablaje_Documentos] (
    [DocumentoID] UNIQUEIDENTIFIER NOT NULL,
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
    [EsEvidencia] BIT NOT NULL,
    [FechaSubidaUTC] DATETIME2 NOT NULL,
    [UsuarioSubidaID] UNIQUEIDENTIFIER NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Operaciones_Tablaje_EventosContables
CREATE TABLE [Operaciones_Tablaje_EventosContables] (
    [EventoContableID] UNIQUEIDENTIFIER NOT NULL,
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
    [MonedaID] INT NOT NULL,
    [TipoCambio] DECIMAL(18,6) NULL,
    [ImporteMXN] DECIMAL(18,4) NULL,
    [CuentaCargoSugerida] NVARCHAR(50) NULL,
    [CuentaAbonoSugerida] NVARCHAR(50) NULL,
    [CentroCostoID] INT NULL,
    [CentroCostoCodigo] NVARCHAR(50) NULL,
    [EstatusContable] NVARCHAR(50) NOT NULL,
    [PolizaID] NVARCHAR(100) NULL,
    [NumeroPoliza] NVARCHAR(50) NULL,
    [FechaContabilizacion] DATE NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [FechaCreacionUTC] DATETIME2 NOT NULL,
    [FechaProcesoUTC] DATETIME2 NULL,
    [UsuarioProcesoID] UNIQUEIDENTIFIER NULL,
    [MensajeError] NVARCHAR(500) NULL
);
GO

-- Table: Operaciones_Tablaje_Mermas
CREATE TABLE [Operaciones_Tablaje_Mermas] (
    [MermaID] UNIQUEIDENTIFIER NOT NULL,
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
    [DentroTolerancia] BIT NOT NULL,
    [CostoMerma] DECIMAL(18,4) NULL,
    [EsRecuperable] BIT NOT NULL,
    [RequiereAutorizacion] BIT NOT NULL,
    [AutorizadoPor] UNIQUEIDENTIFIER NULL,
    [FechaAutorizacion] DATETIME2 NULL,
    [Observaciones] NVARCHAR(500) NULL,
    [FechaRegistroUTC] DATETIME2 NOT NULL,
    [UsuarioRegistroID] UNIQUEIDENTIFIER NULL
);
GO

-- Table: Operaciones_Tablaje_Ordenes
CREATE TABLE [Operaciones_Tablaje_Ordenes] (
    [OrdenID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] UNIQUEIDENTIFIER NOT NULL,
    [UnidadNegocioID] UNIQUEIDENTIFIER NULL,
    [SucursalID] INT NULL,
    [FolioOrden] NVARCHAR(50) NOT NULL,
    [PlantillaID] UNIQUEIDENTIFIER NULL,
    [PlantillaVersion] INT NOT NULL,
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
    [MonedaID] INT NULL,
    [EstatusOrden] NVARCHAR(50) NOT NULL,
    [RequiereAutorizacion] BIT NOT NULL,
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
    [OrigenOrden] NVARCHAR(50) NOT NULL,
    [IDLegacyOrden] NVARCHAR(100) NULL,
    [AfectaInventario] BIT NOT NULL,
    [MovimientoInventarioGenerado] BIT NOT NULL,
    [Observaciones] NVARCHAR(1000) NULL,
    [Activo] BIT NOT NULL,
    [FechaAltaUTC] DATETIME2 NOT NULL,
    [FechaModificacionUTC] DATETIME2 NULL,
    [UsuarioAltaID] UNIQUEIDENTIFIER NULL,
    [UsuarioModificacionID] UNIQUEIDENTIFIER NULL
);
GO

-- Table: Operaciones_Tablaje_OrdenesDetalle
CREATE TABLE [Operaciones_Tablaje_OrdenesDetalle] (
    [OrdenDetalleID] UNIQUEIDENTIFIER NOT NULL,
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
    [GeneraMovimiento] BIT NOT NULL,
    [MovimientoGenerado] BIT NOT NULL,
    [AlmacenDestinoID] INT NULL,
    [LoteGenerado] NVARCHAR(100) NULL,
    [Observaciones] NVARCHAR(500) NULL,
    [FechaCaptura] DATETIME2 NULL,
    [UsuarioCapturaID] UNIQUEIDENTIFIER NULL
);
GO

-- Table: Operaciones_Tablaje_Plantillas
CREATE TABLE [Operaciones_Tablaje_Plantillas] (
    [PlantillaID] UNIQUEIDENTIFIER NOT NULL,
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
    [CantidadBaseEstandar] DECIMAL(18,4) NOT NULL,
    [RendimientoEsperadoPorcentaje] DECIMAL(5,2) NULL,
    [MermaEsperadaPorcentaje] DECIMAL(5,2) NULL,
    [ToleranciaRendimiento] DECIMAL(5,2) NULL,
    [ReglaCosteo] NVARCHAR(50) NULL,
    [CostoBaseReferencia] DECIMAL(18,4) NULL,
    [MonedaID] INT NULL,
    [OrigenPlantilla] NVARCHAR(50) NOT NULL,
    [SistemaOrigen] NVARCHAR(50) NULL,
    [ServidorOrigenID] NVARCHAR(100) NULL,
    [BaseDatosOrigen] NVARCHAR(100) NULL,
    [IDLegacyPlantilla] NVARCHAR(100) NULL,
    [HashOrigen] NVARCHAR(64) NULL,
    [VersionActual] INT NOT NULL,
    [PlantillaPadreID] UNIQUEIDENTIFIER NULL,
    [Estatus] NVARCHAR(50) NOT NULL,
    [RequiereAutorizacion] BIT NOT NULL,
    [AutorizadoPor] UNIQUEIDENTIFIER NULL,
    [FechaAutorizacion] DATETIME2 NULL,
    [Activo] BIT NOT NULL,
    [FechaAltaUTC] DATETIME2 NOT NULL,
    [FechaModificacionUTC] DATETIME2 NULL,
    [FechaSincronizacionUTC] DATETIME2 NULL,
    [FechaOperacionMexico] DATE NOT NULL,
    [UsuarioAltaID] UNIQUEIDENTIFIER NULL,
    [UsuarioModificacionID] UNIQUEIDENTIFIER NULL
);
GO

-- Table: Operaciones_Tablaje_PlantillasDetalle
CREATE TABLE [Operaciones_Tablaje_PlantillasDetalle] (
    [PlantillaDetalleID] UNIQUEIDENTIFIER NOT NULL,
    [PlantillaID] UNIQUEIDENTIFIER NOT NULL,
    [ProductoDerivadoID] INT NULL,
    [ProductoDerivadoCodigo] NVARCHAR(50) NULL,
    [ProductoDerivadoNombre] NVARCHAR(200) NOT NULL,
    [TipoDerivado] NVARCHAR(50) NOT NULL,
    [UnidadDerivadoID] INT NULL,
    [UnidadDerivadoCodigo] NVARCHAR(20) NULL,
    [CantidadEsperada] DECIMAL(18,4) NOT NULL,
    [PorcentajeRendimientoEsperado] DECIMAL(5,2) NULL,
    [PorcentajeCostoAsignado] DECIMAL(5,2) NULL,
    [CostoUnitarioFijo] DECIMAL(18,4) NULL,
    [EsMerma] BIT NOT NULL,
    [EsSubproducto] BIT NOT NULL,
    [EsProductoVendible] BIT NOT NULL,
    [EsInventariable] BIT NOT NULL,
    [GeneraMovimientoInventario] BIT NOT NULL,
    [OrdenVisual] INT NOT NULL,
    [Observaciones] NVARCHAR(500) NULL,
    [IDLegacyDetalle] NVARCHAR(100) NULL,
    [Activo] BIT NOT NULL,
    [FechaAltaUTC] DATETIME2 NOT NULL,
    [FechaModificacionUTC] DATETIME2 NULL
);
GO

-- Table: Operaciones_Tablaje_PlantillasVersiones
CREATE TABLE [Operaciones_Tablaje_PlantillasVersiones] (
    [VersionID] UNIQUEIDENTIFIER NOT NULL,
    [PlantillaID] UNIQUEIDENTIFIER NOT NULL,
    [NumeroVersion] INT NOT NULL,
    [DatosPlantillaJSON] NVARCHAR(MAX) NULL,
    [DatosDetalleJSON] NVARCHAR(MAX) NULL,
    [HashVersion] NVARCHAR(64) NULL,
    [MotivoVersion] NVARCHAR(500) NULL,
    [TipoCambio] NVARCHAR(50) NULL,
    [EsVersionActiva] BIT NOT NULL,
    [FechaVersionUTC] DATETIME2 NOT NULL,
    [UsuarioVersionID] UNIQUEIDENTIFIER NULL
);
GO

-- Table: Operaciones_Tablaje_Rendimientos
CREATE TABLE [Operaciones_Tablaje_Rendimientos] (
    [RendimientoID] UNIQUEIDENTIFIER NOT NULL,
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
    [DentroTolerancia] BIT NOT NULL,
    [CostoInsumo] DECIMAL(18,4) NULL,
    [CostoDerivados] DECIMAL(18,4) NULL,
    [CostoPerdido] DECIMAL(18,4) NULL,
    [FechaRegistroUTC] DATETIME2 NOT NULL
);
GO

-- Table: Operaciones_Tablaje_SyncErrores
CREATE TABLE [Operaciones_Tablaje_SyncErrores] (
    [ErrorID] BIGINT NOT NULL,
    [SyncLogID] BIGINT NOT NULL,
    [TipoEntidad] NVARCHAR(50) NOT NULL,
    [IDLegacy] NVARCHAR(100) NULL,
    [DatosRegistroJSON] NVARCHAR(MAX) NULL,
    [TipoError] NVARCHAR(100) NOT NULL,
    [MensajeError] NVARCHAR(MAX) NOT NULL,
    [StackTrace] NVARCHAR(MAX) NULL,
    [Resuelto] BIT NOT NULL,
    [FechaResolucion] DATETIME2 NULL,
    [ResolucionNotas] NVARCHAR(500) NULL,
    [FechaErrorUTC] DATETIME2 NOT NULL
);
GO

-- Table: Operaciones_Tablaje_SyncLog
CREATE TABLE [Operaciones_Tablaje_SyncLog] (
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
    [RegistrosLeidos] INT NOT NULL,
    [RegistrosCreados] INT NOT NULL,
    [RegistrosActualizados] INT NOT NULL,
    [RegistrosSinCambios] INT NOT NULL,
    [RegistrosError] INT NOT NULL,
    [Estado] NVARCHAR(50) NOT NULL,
    [MensajeError] NVARCHAR(MAX) NULL,
    [DetallesJSON] NVARCHAR(MAX) NULL,
    [EjecutadoPor] UNIQUEIDENTIFIER NULL
);
GO

-- Table: Operativo_AuditoriasProgramadas
CREATE TABLE [Operativo_AuditoriasProgramadas] (
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
    [Timezone] VARCHAR(50) NULL,
    [ProximaEjecucion] DATETIME2 NULL,
    [UltimaEjecucion] DATETIME2 NULL,
    [Estado] VARCHAR(50) NULL,
    [UsuarioCreadorID] VARCHAR(50) NULL,
    [FechaCreacion] DATETIME2 NULL,
    [FechaActualizacion] DATETIME2 NULL,
    [ConfiguracionJSON] NVARCHAR(MAX) NULL
);
GO

-- Table: Operativo_BitacoraCompras
CREATE TABLE [Operativo_BitacoraCompras] (
    [ID] INT NOT NULL,
    [BitacoraID] VARCHAR(50) NOT NULL,
    [AutomatizacionID] VARCHAR(50) NULL,
    [Accion] VARCHAR(50) NOT NULL,
    [UsuarioID] VARCHAR(50) NULL,
    [UsuarioNombre] VARCHAR(200) NULL,
    [Detalle] NVARCHAR(MAX) NULL,
    [EstadoAnterior] VARCHAR(50) NULL,
    [EstadoNuevo] VARCHAR(50) NULL,
    [Fecha] DATETIME2 NULL,
    [MetadatosJSON] NVARCHAR(MAX) NULL
);
GO

-- Table: Operativo_CargosResponsabilidad
CREATE TABLE [Operativo_CargosResponsabilidad] (
    [ID] INT NOT NULL,
    [CargoID] VARCHAR(50) NOT NULL,
    [ResponsabilidadID] VARCHAR(50) NOT NULL,
    [WorkflowID] VARCHAR(50) NOT NULL,
    [SucursalID] VARCHAR(100) NULL,
    [ResponsableID] VARCHAR(50) NULL,
    [ResponsableNombre] VARCHAR(200) NULL,
    [MontoPropuesto] DECIMAL(18,2) NOT NULL,
    [MontoFinal] DECIMAL(18,2) NULL,
    [EstatusCargo] VARCHAR(50) NULL,
    [FechaPropuesta] DATETIME2 NULL,
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

-- Table: Operativo_DocumentosGenerados
CREATE TABLE [Operativo_DocumentosGenerados] (
    [ID] INT NOT NULL,
    [DocumentoID] VARCHAR(50) NOT NULL,
    [WorkflowID] VARCHAR(50) NULL,
    [TipoDocumento] VARCHAR(50) NOT NULL,
    [NombreArchivo] VARCHAR(500) NULL,
    [URLDescarga] VARCHAR(1000) NULL,
    [Formato] VARCHAR(20) NULL,
    [TamanioBytes] BIGINT NULL,
    [UsuarioGeneradorID] VARCHAR(50) NULL,
    [Estado] VARCHAR(50) NULL,
    [FechaGeneracion] DATETIME2 NULL,
    [FechaExpiracion] DATETIME2 NULL,
    [MetadatosJSON] NVARCHAR(MAX) NULL
);
GO

-- Table: Operativo_HistorialAsignaciones
CREATE TABLE [Operativo_HistorialAsignaciones] (
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
    [TipoAsignacion] VARCHAR(50) NULL,
    [Motivo] NVARCHAR(MAX) NULL,
    [FechaAsignacion] DATETIME2 NULL
);
GO

-- Table: Operativo_HistorialCargos
CREATE TABLE [Operativo_HistorialCargos] (
    [ID] INT NOT NULL,
    [HistorialID] VARCHAR(50) NOT NULL,
    [CargoID] VARCHAR(50) NOT NULL,
    [Accion] VARCHAR(50) NOT NULL,
    [UsuarioID] VARCHAR(50) NOT NULL,
    [UsuarioNombre] VARCHAR(200) NULL,
    [Detalle] NVARCHAR(MAX) NULL,
    [EstadoAnterior] VARCHAR(50) NULL,
    [EstadoNuevo] VARCHAR(50) NULL,
    [Fecha] DATETIME2 NULL
);
GO

-- Table: Operativo_Notificaciones_Log
CREATE TABLE [Operativo_Notificaciones_Log] (
    [ID] INT NOT NULL,
    [NotificacionID] VARCHAR(50) NOT NULL,
    [TipoEvento] VARCHAR(50) NOT NULL,
    [WorkflowID] VARCHAR(50) NULL,
    [TareaID] VARCHAR(50) NULL,
    [Destinatario] VARCHAR(200) NULL,
    [DestinatarioEmail] VARCHAR(200) NULL,
    [Titulo] VARCHAR(500) NULL,
    [Mensaje] NVARCHAR(MAX) NULL,
    [Estado] VARCHAR(50) NULL,
    [Canal] VARCHAR(50) NULL,
    [FechaEnvio] DATETIME2 NULL,
    [FechaLeido] DATETIME2 NULL,
    [ErrorMensaje] NVARCHAR(MAX) NULL,
    [MetadatosJSON] NVARCHAR(MAX) NULL
);
GO

-- Table: Operativo_PedidosProcesados
CREATE TABLE [Operativo_PedidosProcesados] (
    [ID] INT NOT NULL,
    [PedidoID] VARCHAR(50) NOT NULL,
    [AutomatizacionID] VARCHAR(50) NOT NULL,
    [ServerID] VARCHAR(50) NULL,
    [SucursalID] VARCHAR(100) NULL,
    [FolioInventario] VARCHAR(100) NULL,
    [Estado] VARCHAR(50) NULL,
    [CantidadItems] INT NULL,
    [MontoTotal] DECIMAL(18,2) NULL,
    [FechaProcesamiento] DATETIME2 NULL,
    [DetalleJSON] NVARCHAR(MAX) NULL
);
GO

-- Table: Operativo_ResponsabilidadEconomica
CREATE TABLE [Operativo_ResponsabilidadEconomica] (
    [ID] INT NOT NULL,
    [ResponsabilidadID] VARCHAR(50) NOT NULL,
    [WorkflowID] VARCHAR(50) NOT NULL,
    [ServerID] VARCHAR(50) NULL,
    [SucursalID] VARCHAR(100) NULL,
    [SucursalNombre] VARCHAR(100) NULL,
    [ResponsableID] VARCHAR(50) NULL,
    [ResponsableNombre] VARCHAR(200) NULL,
    [MontoTotal] DECIMAL(18,2) NOT NULL,
    [MontoJustificado] DECIMAL(18,2) NULL,
    [MontoNoJustificado] DECIMAL(18,2) NULL,
    [Estado] VARCHAR(50) NULL,
    [ExcedeMinimo] BIT NULL,
    [UmbralMinimo] DECIMAL(18,2) NULL,
    [FechaCalculo] DATETIME2 NULL,
    [FechaUltimaActualizacion] DATETIME2 NULL,
    [FechaAprobacion] DATETIME2 NULL,
    [AprobadoPorID] VARCHAR(50) NULL,
    [Comentarios] NVARCHAR(MAX) NULL,
    [MetadatosJSON] NVARCHAR(MAX) NULL
);
GO

-- Table: Operativo_TareasCompras
CREATE TABLE [Operativo_TareasCompras] (
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
    [Estado] VARCHAR(50) NULL,
    [Prioridad] VARCHAR(20) NULL,
    [FechaCreacion] DATETIME2 NULL,
    [FechaLimite] DATETIME2 NULL,
    [FechaCompletada] DATETIME2 NULL,
    [Resultado] NVARCHAR(MAX) NULL,
    [MetadatosJSON] NVARCHAR(MAX) NULL
);
GO

-- Table: Producto_Catalogo
CREATE TABLE [Producto_Catalogo] (
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
    [TipoProducto] VARCHAR(20) NOT NULL,
    [EsInventariable] BIT NOT NULL,
    [EsServicio] BIT NOT NULL,
    [PermiteVenta] BIT NOT NULL,
    [PermiteCompra] BIT NOT NULL,
    [PermiteVentaSinExistencia] BIT NOT NULL,
    [UnidadInventario] VARCHAR(30) NOT NULL,
    [UnidadVenta] VARCHAR(30) NOT NULL,
    [UnidadCompra] VARCHAR(30) NOT NULL,
    [PrecioVentaBase] DECIMAL(18,2) NOT NULL,
    [PrecioCostoBase] DECIMAL(18,2) NOT NULL,
    [TasaImpuesto] DECIMAL(9,4) NOT NULL,
    [StockActual] DECIMAL(18,4) NOT NULL,
    [StockMinimo] DECIMAL(18,4) NOT NULL,
    [StockMaximo] DECIMAL(18,4) NULL,
    [PuntoReorden] DECIMAL(18,4) NULL,
    [PesoNeto] DECIMAL(18,4) NULL,
    [Volumen] DECIMAL(18,4) NULL,
    [ImagenURL] VARCHAR(500) NULL,
    [Observaciones] VARCHAR(1000) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedBy] VARCHAR(100) NULL
);
GO

-- Table: Producto_Equivalentes
CREATE TABLE [Producto_Equivalentes] (
    [ProductoEquivalenteID] BIGINT NOT NULL,
    [ProductoID] INT NOT NULL,
    [ProductoEquivalenteRefID] INT NOT NULL,
    [TipoEquivalencia] VARCHAR(20) NOT NULL,
    [FactorEquivalencia] DECIMAL(18,6) NOT NULL,
    [Observaciones] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL
);
GO

-- Table: Producto_Familias
CREATE TABLE [Producto_Familias] (
    [FamiliaProductoID] INT NOT NULL,
    [CodigoFamilia] VARCHAR(20) NOT NULL,
    [NombreFamilia] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Producto_Lineas
CREATE TABLE [Producto_Lineas] (
    [LineaProductoID] INT NOT NULL,
    [SubFamiliaProductoID] INT NOT NULL,
    [CodigoLinea] VARCHAR(20) NOT NULL,
    [NombreLinea] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Producto_Marcas
CREATE TABLE [Producto_Marcas] (
    [MarcaProductoID] INT NOT NULL,
    [CodigoMarca] VARCHAR(20) NOT NULL,
    [NombreMarca] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Producto_Presentaciones
CREATE TABLE [Producto_Presentaciones] (
    [PresentacionProductoID] BIGINT NOT NULL,
    [ProductoID] INT NOT NULL,
    [CodigoPresentacion] VARCHAR(30) NOT NULL,
    [NombrePresentacion] VARCHAR(120) NOT NULL,
    [SKU_Presentacion] VARCHAR(50) NULL,
    [CodigoBarras] VARCHAR(100) NULL,
    [UnidadPresentacion] VARCHAR(30) NOT NULL,
    [FactorConversionInventario] DECIMAL(18,6) NOT NULL,
    [EsPresentacionVenta] BIT NOT NULL,
    [EsPresentacionCompra] BIT NOT NULL,
    [EsPresentacionInventario] BIT NOT NULL,
    [PrecioVenta] DECIMAL(18,2) NULL,
    [PrecioCosto] DECIMAL(18,2) NULL,
    [PesoNeto] DECIMAL(18,4) NULL,
    [Volumen] DECIMAL(18,4) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Producto_SubFamilias
CREATE TABLE [Producto_SubFamilias] (
    [SubFamiliaProductoID] INT NOT NULL,
    [FamiliaProductoID] INT NOT NULL,
    [CodigoSubFamilia] VARCHAR(20) NOT NULL,
    [NombreSubFamilia] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Producto_Sustitutos
CREATE TABLE [Producto_Sustitutos] (
    [ProductoSustitutoID] BIGINT NOT NULL,
    [ProductoID] INT NOT NULL,
    [ProductoSustitutoRefID] INT NOT NULL,
    [Prioridad] TINYINT NOT NULL,
    [Motivo] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL
);
GO

-- Table: Products
CREATE TABLE [Products] (
    [Id] INT NOT NULL,
    [CodigoProducto] NVARCHAR(50) NULL,
    [NombreProducto] NVARCHAR(200) NOT NULL,
    [Familia] NVARCHAR(100) NULL,
    [Subfamilia] NVARCHAR(100) NULL,
    [Casa] NVARCHAR(100) NULL,
    [PorcentajeAlcohol] DECIMAL(5,2) NULL,
    [URL_Imagen] NVARCHAR(500) NULL,
    [PrecioBase] DECIMAL(18,2) NULL,
    [Activo] BIT NULL,
    [FechaCreacion] DATETIME NULL
);
GO

-- Table: propinas_tpv_config
CREATE TABLE [propinas_tpv_config] (
    [id] UNIQUEIDENTIFIER NOT NULL,
    [alcance_tipo] VARCHAR(20) NOT NULL,
    [alcance_server_id] VARCHAR(50) NULL,
    [alcance_empresa_id] VARCHAR(50) NULL,
    [alcance_sucursal_id] VARCHAR(50) NULL,
    [vigencia_inicio] DATETIME NOT NULL,
    [vigencia_fin] DATETIME NULL,
    [activa] BIT NOT NULL,
    [porcentaje_comision] DECIMAL(5,4) NOT NULL,
    [tolerancia_descuadre] DECIMAL(18,2) NOT NULL,
    [dias_para_cuadrar] INT NOT NULL,
    [soft_concepto_propinas] INT NOT NULL,
    [soft_conceptos_tarjeta] VARCHAR(50) NOT NULL,
    [soft_concepto_efectivo] INT NOT NULL,
    [created_at] DATETIME NOT NULL,
    [created_by] VARCHAR(100) NULL,
    [updated_at] DATETIME NOT NULL,
    [updated_by] VARCHAR(100) NULL,
    [motivo_cambio] VARCHAR(500) NULL
);
GO

-- Table: propinas_tpv_control
CREATE TABLE [propinas_tpv_control] (
    [id] UNIQUEIDENTIFIER NOT NULL,
    [server_id] VARCHAR(50) NOT NULL,
    [sucursal_id] VARCHAR(50) NOT NULL,
    [folio_corte] VARCHAR(50) NOT NULL,
    [fecha_corte] DATE NOT NULL,
    [server_name] VARCHAR(100) NOT NULL,
    [system_type] VARCHAR(20) NOT NULL,
    [sucursal_nombre] VARCHAR(100) NULL,
    [empresa_id] VARCHAR(50) NULL,
    [estacion_id] VARCHAR(50) NULL,
    [propinas_totales_corte] DECIMAL(18,2) NOT NULL,
    [propinas_efectivo] DECIMAL(18,2) NOT NULL,
    [propinas_tpv] DECIMAL(18,2) NOT NULL,
    [ventas_tarjeta] DECIMAL(18,2) NOT NULL,
    [ventas_totales] DECIMAL(18,2) NOT NULL,
    [ventas_efectivo] DECIMAL(18,2) NOT NULL,
    [total_cheques] INT NOT NULL,
    [saldo_corte] DECIMAL(18,2) NOT NULL,
    [corte_id_origen] VARCHAR(50) NULL,
    [turno_id_origen] VARCHAR(50) NULL,
    [tipo_dato] VARCHAR(20) NOT NULL,
    [metodo_calculo] VARCHAR(100) NULL,
    [confianza] DECIMAL(3,2) NOT NULL,
    [query_origen] VARCHAR(500) NULL,
    [advertencia] VARCHAR(500) NULL,
    [config_aplicada_id] UNIQUEIDENTIFIER NULL,
    [porcentaje_comision] DECIMAL(5,4) NOT NULL,
    [comision_calculada] DECIMAL(18,2) NOT NULL,
    [monto_a_pagar_meseros] DECIMAL(18,2) NOT NULL,
    [pago_registrado] BIT NOT NULL,
    [pago_monto] DECIMAL(18,2) NULL,
    [pago_fecha] DATETIME NULL,
    [pago_metodo] VARCHAR(20) NULL,
    [pago_usuario_id] VARCHAR(50) NULL,
    [pago_usuario_email] VARCHAR(100) NULL,
    [pago_observaciones] VARCHAR(500) NULL,
    [cuadre_estado] VARCHAR(20) NOT NULL,
    [cuadre_diferencia] DECIMAL(18,2) NULL,
    [cuadre_fecha] DATETIME NULL,
    [cuadre_usuario_id] VARCHAR(50) NULL,
    [cuadre_usuario_email] VARCHAR(100) NULL,
    [cuadre_observaciones] VARCHAR(500) NULL,
    [fecha_sincronizacion] DATETIME NOT NULL,
    [sincronizado_por] VARCHAR(100) NULL,
    [created_at] DATETIME NOT NULL,
    [updated_at] DATETIME NOT NULL,
    [version] INT NOT NULL,
    [UnidadNegocioID] UNIQUEIDENTIFIER NULL,
    [UnidadNegocioNombre] NVARCHAR(100) NULL,
    [SistemaOrigen] NVARCHAR(20) NULL,
    [BaseDatosOrigen] NVARCHAR(100) NULL,
    [TablaOrigen] NVARCHAR(100) NULL,
    [IdOrigen] NVARCHAR(100) NULL,
    [FolioOrigen] NVARCHAR(100) NULL,
    [HashOrigen] NVARCHAR(64) NULL,
    [EsDemo] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [FormaPagoID] NVARCHAR(50) NULL,
    [FormaPagoNombre] NVARCHAR(100) NULL,
    [EsTarjeta] BIT NOT NULL
);
GO

-- Table: propinas_tpv_historial
CREATE TABLE [propinas_tpv_historial] (
    [id] UNIQUEIDENTIFIER NOT NULL,
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
    [fecha] DATETIME NOT NULL,
    [observaciones] VARCHAR(500) NULL
);
GO

-- Table: Proveedor_Bancos
CREATE TABLE [Proveedor_Bancos] (
    [BancoID] SMALLINT NOT NULL,
    [ClaveBanco] VARCHAR(10) NULL,
    [NombreBanco] VARCHAR(100) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Proveedor_Catalogo
CREATE TABLE [Proveedor_Catalogo] (
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
    [DiasCredito] SMALLINT NOT NULL,
    [LimiteCredito] DECIMAL(18,2) NULL,
    [MonedaID] SMALLINT NOT NULL,
    [EmailPrincipal] VARCHAR(150) NULL,
    [TelefonoPrincipal] VARCHAR(25) NULL,
    [Ciudad] VARCHAR(100) NULL,
    [Estado] VARCHAR(100) NULL,
    [Pais] VARCHAR(60) NOT NULL,
    [CodigoPostal] VARCHAR(10) NULL,
    [PortalHabilitado] BIT NOT NULL,
    [RequiereOCParaFacturar] BIT NOT NULL,
    [RequiereXML] BIT NOT NULL,
    [RequierePDF] BIT NOT NULL,
    [ExpedienteCompleto] BIT NOT NULL,
    [EstatusSATID] TINYINT NOT NULL,
    [RiesgoID] TINYINT NOT NULL,
    [ScoreActual] DECIMAL(5,2) NULL,
    [FechaUltimaEvaluacion] DATE NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Proveedor_Categorias
CREATE TABLE [Proveedor_Categorias] (
    [ProveedorCategoriaID] BIGINT NOT NULL,
    [ProveedorID] INT NOT NULL,
    [CategoriaProveedorID] INT NOT NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL
);
GO

-- Table: Proveedor_CategoriasCatalogo
CREATE TABLE [Proveedor_CategoriasCatalogo] (
    [CategoriaProveedorID] INT NOT NULL,
    [NombreCategoria] VARCHAR(100) NOT NULL,
    [CategoriaPadreID] INT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Proveedor_Contactos
CREATE TABLE [Proveedor_Contactos] (
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
    [EsPrincipal] BIT NOT NULL,
    [RecibeOC] BIT NOT NULL,
    [RecibeFacturacion] BIT NOT NULL,
    [RecibePagos] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Proveedor_CuentasBancarias
CREATE TABLE [Proveedor_CuentasBancarias] (
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
    [EsPrincipal] BIT NOT NULL,
    [Validada] BIT NOT NULL,
    [Activa] BIT NOT NULL,
    [FechaValidacion] DATETIME2 NULL,
    [Observaciones] VARCHAR(500) NULL
);
GO

-- Table: Proveedor_Documentos
CREATE TABLE [Proveedor_Documentos] (
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
    [Vigente] BIT NOT NULL,
    [Validado] BIT NOT NULL,
    [ObservacionesValidacion] VARCHAR(500) NULL,
    [FechaCarga] DATETIME2 NOT NULL,
    [FechaValidacion] DATETIME2 NULL,
    [UsuarioCarga] VARCHAR(100) NULL,
    [UsuarioValidacion] VARCHAR(100) NULL,
    [HashArchivo] VARCHAR(128) NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Proveedor_EstatusProveedor
CREATE TABLE [Proveedor_EstatusProveedor] (
    [EstatusProveedorID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Proveedor_EstatusSAT
CREATE TABLE [Proveedor_EstatusSAT] (
    [EstatusSATID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Proveedor_EstatusSincronizacion
CREATE TABLE [Proveedor_EstatusSincronizacion] (
    [EstatusSincronizacionID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Proveedor_Evaluaciones
CREATE TABLE [Proveedor_Evaluaciones] (
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
    [Incidencias] INT NOT NULL,
    [Observaciones] VARCHAR(1000) NULL,
    [UsuarioEvaluacion] VARCHAR(100) NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Proveedor_Integracion
CREATE TABLE [Proveedor_Integracion] (
    [IntegracionID] BIGINT NOT NULL,
    [ProveedorID] INT NOT NULL,
    [SistemaID] TINYINT NOT NULL,
    [ClaveExterna] VARCHAR(50) NOT NULL,
    [UltimaSincronizacion] DATETIME2 NULL,
    [EstatusSincronizacionID] TINYINT NOT NULL,
    [MensajeError] VARCHAR(1000) NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Proveedor_Monedas
CREATE TABLE [Proveedor_Monedas] (
    [MonedaID] SMALLINT NOT NULL,
    [ClaveMoneda] VARCHAR(10) NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Simbolo] VARCHAR(10) NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Proveedor_RegimenFiscal
CREATE TABLE [Proveedor_RegimenFiscal] (
    [RegimenFiscalID] SMALLINT NOT NULL,
    [ClaveSAT] VARCHAR(10) NULL,
    [Descripcion] VARCHAR(150) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Proveedor_RiesgoProveedor
CREATE TABLE [Proveedor_RiesgoProveedor] (
    [RiesgoID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Proveedor_RolUsuarioPortal
CREATE TABLE [Proveedor_RolUsuarioPortal] (
    [RolPortalID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Proveedor_SistemasIntegracion
CREATE TABLE [Proveedor_SistemasIntegracion] (
    [SistemaID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Proveedor_TipoContacto
CREATE TABLE [Proveedor_TipoContacto] (
    [TipoContactoID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Proveedor_TipoDocumento
CREATE TABLE [Proveedor_TipoDocumento] (
    [TipoDocumentoID] SMALLINT NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [RequiereVigencia] BIT NOT NULL,
    [EsObligatorio] BIT NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Proveedor_TipoProveedor
CREATE TABLE [Proveedor_TipoProveedor] (
    [TipoProveedorID] SMALLINT NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Proveedor_UsuariosPortal
CREATE TABLE [Proveedor_UsuariosPortal] (
    [UsuarioPortalID] INT NOT NULL,
    [ProveedorID] INT NOT NULL,
    [RolPortalID] TINYINT NOT NULL,
    [NombreUsuario] VARCHAR(150) NOT NULL,
    [Email] VARCHAR(150) NOT NULL,
    [PasswordHash] VARCHAR(255) NULL,
    [UltimoAcceso] DATETIME2 NULL,
    [Bloqueado] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: RH_Auditoria_Fiscal
CREATE TABLE [RH_Auditoria_Fiscal] (
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

-- Table: RH_Ausencias
CREATE TABLE [RH_Ausencias] (
    [AusenciaID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [TipoAusenciaID] SMALLINT NOT NULL,
    [FechaInicio] DATE NOT NULL,
    [FechaFin] DATE NOT NULL,
    [Dias] DECIMAL(9,2) NOT NULL,
    [Horas] DECIMAL(9,2) NULL,
    [Estatus] VARCHAR(20) NOT NULL,
    [FolioExterno] VARCHAR(50) NULL,
    [Observaciones] VARCHAR(500) NULL,
    [AprobadoPor] INT NULL,
    [FechaAprobacion] DATETIME2 NULL,
    [FechaAlta] DATETIME2 NOT NULL
);
GO

-- Table: RH_Calendario_Laboral
CREATE TABLE [RH_Calendario_Laboral] (
    [CalendarioLaboralID] INT NOT NULL,
    [SucursalID] INT NULL,
    [SucursalFiscalID] INT NULL,
    [Fecha] DATE NOT NULL,
    [EsDiaDescanso] BIT NOT NULL,
    [EsFestivo] BIT NOT NULL,
    [Descripcion] VARCHAR(150) NULL
);
GO

-- Table: RH_Cat_Areas
CREATE TABLE [RH_Cat_Areas] (
    [AreaID] INT NOT NULL,
    [DepartamentoID] INT NOT NULL,
    [CodigoArea] VARCHAR(20) NOT NULL,
    [NombreArea] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: RH_Cat_Beneficios
CREATE TABLE [RH_Cat_Beneficios] (
    [BeneficioID] INT NOT NULL,
    [CodigoBeneficio] VARCHAR(20) NOT NULL,
    [NombreBeneficio] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [MontoDefault] DECIMAL(18,2) NULL,
    [PorcentajeDefault] DECIMAL(9,4) NULL,
    [IntegraSBC] BIT NOT NULL,
    [GravadoISR] BIT NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: RH_Cat_ConceptosNomina
CREATE TABLE [RH_Cat_ConceptosNomina] (
    [ConceptoNominaID] INT NOT NULL,
    [CodigoConcepto] VARCHAR(30) NOT NULL,
    [NombreConcepto] VARCHAR(150) NOT NULL,
    [TipoConceptoNominaID] SMALLINT NOT NULL,
    [ClaveSAT] VARCHAR(20) NULL,
    [FormulaSQL] VARCHAR(MAX) NULL,
    [EsGravado] BIT NOT NULL,
    [EsExento] BIT NOT NULL,
    [IntegraSBC] BIT NOT NULL,
    [AfectaISR] BIT NOT NULL,
    [AfectaSubsidio] BIT NOT NULL,
    [AfectaIMSS] BIT NOT NULL,
    [AfectaInfonavit] BIT NOT NULL,
    [EsEditableEnCaptura] BIT NOT NULL,
    [RequiereUnidades] BIT NOT NULL,
    [OrdenImpresion] SMALLINT NOT NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: RH_Cat_Departamentos
CREATE TABLE [RH_Cat_Departamentos] (
    [DepartamentoID] INT NOT NULL,
    [CodigoDepartamento] VARCHAR(20) NOT NULL,
    [NombreDepartamento] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: RH_Cat_EstatusPeriodoNomina
CREATE TABLE [RH_Cat_EstatusPeriodoNomina] (
    [EstatusPeriodoNominaID] SMALLINT NOT NULL,
    [CodigoEstatus] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [OrdenFlujo] SMALLINT NOT NULL,
    [EsFinal] BIT NOT NULL
);
GO

-- Table: RH_Cat_Jornadas
CREATE TABLE [RH_Cat_Jornadas] (
    [JornadaID] SMALLINT NOT NULL,
    [CodigoJornada] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [HorasDiarias] DECIMAL(5,2) NULL,
    [HorasSemanales] DECIMAL(5,2) NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: RH_Cat_MotivosBaja
CREATE TABLE [RH_Cat_MotivosBaja] (
    [MotivoBajaID] SMALLINT NOT NULL,
    [CodigoMotivoBaja] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(150) NOT NULL,
    [RequiereFiniquito] BIT NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: RH_Cat_Puestos
CREATE TABLE [RH_Cat_Puestos] (
    [PuestoID] INT NOT NULL,
    [Descripcion] VARCHAR(100) NULL,
    [Departamento] VARCHAR(50) NULL,
    [Sueldo_Base_Seman_SBC] DECIMAL(18,2) NULL,
    [CodigoPuesto] VARCHAR(20) NULL,
    [DepartamentoID] INT NULL,
    [AreaID] INT NULL,
    [NivelOrganizacional] VARCHAR(50) NULL,
    [EsConfianza] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: RH_Cat_RegimenContratacion
CREATE TABLE [RH_Cat_RegimenContratacion] (
    [RegimenContratacionID] SMALLINT NOT NULL,
    [ClaveSAT] VARCHAR(10) NOT NULL,
    [Descripcion] VARCHAR(150) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: RH_Cat_Sucursales
CREATE TABLE [RH_Cat_Sucursales] (
    [SucursalID] INT NOT NULL,
    [Nombre_Sucursal] VARCHAR(100) NOT NULL,
    [Ciudad] VARCHAR(50) NULL,
    [Activa] BIT NULL
);
GO

-- Table: RH_Cat_SucursalesFiscal
CREATE TABLE [RH_Cat_SucursalesFiscal] (
    [SucursalFiscalID] INT NOT NULL,
    [SucursalID] INT NOT NULL,
    [EmpresaID] INT NULL,
    [RFC] VARCHAR(13) NOT NULL,
    [RazonSocial] VARCHAR(200) NOT NULL,
    [RegimenFiscal] VARCHAR(10) NULL,
    [CodigoPostalFiscal] VARCHAR(10) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: RH_Cat_TiposAusencia
CREATE TABLE [RH_Cat_TiposAusencia] (
    [TipoAusenciaID] SMALLINT NOT NULL,
    [CodigoTipoAusencia] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [GoceSueldo] BIT NOT NULL,
    [AfectaNomina] BIT NOT NULL,
    [AfectaAsistencia] BIT NOT NULL,
    [ClaveSAT] VARCHAR(20) NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: RH_Cat_TiposConceptoNomina
CREATE TABLE [RH_Cat_TiposConceptoNomina] (
    [TipoConceptoNominaID] SMALLINT NOT NULL,
    [CodigoTipoConcepto] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [Naturaleza] CHAR(1) NOT NULL
);
GO

-- Table: RH_Cat_TiposContrato
CREATE TABLE [RH_Cat_TiposContrato] (
    [TipoContratoID] SMALLINT NOT NULL,
    [CodigoTipoContrato] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [EsIndeterminado] BIT NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: RH_Cat_TiposPeriodoNomina
CREATE TABLE [RH_Cat_TiposPeriodoNomina] (
    [TipoPeriodoNominaID] SMALLINT NOT NULL,
    [CodigoTipoPeriodo] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [DiasPeriodo] SMALLINT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: RH_Cat_Turnos
CREATE TABLE [RH_Cat_Turnos] (
    [TurnoID] SMALLINT NOT NULL,
    [CodigoTurno] VARCHAR(20) NOT NULL,
    [NombreTurno] VARCHAR(100) NOT NULL,
    [HoraEntradaProgramada] TIME NULL,
    [HoraSalidaProgramada] TIME NULL,
    [TolEntradaMin] SMALLINT NOT NULL,
    [TolSalidaMin] SMALLINT NOT NULL,
    [CruzaMedianoche] BIT NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: RH_Colaboradores_Beneficios
CREATE TABLE [RH_Colaboradores_Beneficios] (
    [ColaboradorBeneficioID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [BeneficioID] INT NOT NULL,
    [FechaInicio] DATE NOT NULL,
    [FechaFin] DATE NULL,
    [Monto] DECIMAL(18,2) NULL,
    [Porcentaje] DECIMAL(9,4) NULL,
    [Activo] BIT NOT NULL,
    [Observaciones] VARCHAR(250) NULL
);
GO

-- Table: RH_Colaboradores_ContactosEmergencia
CREATE TABLE [RH_Colaboradores_ContactosEmergencia] (
    [ContactoEmergenciaID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [NombreContacto] VARCHAR(150) NOT NULL,
    [Parentesco] VARCHAR(50) NULL,
    [Telefono] VARCHAR(25) NULL,
    [TelefonoAlterno] VARCHAR(25) NULL,
    [Observaciones] VARCHAR(250) NULL,
    [EsPrincipal] BIT NOT NULL
);
GO

-- Table: RH_Colaboradores_Dependientes
CREATE TABLE [RH_Colaboradores_Dependientes] (
    [DependienteID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [NombreDependiente] VARCHAR(150) NOT NULL,
    [Parentesco] VARCHAR(50) NULL,
    [FechaNacimiento] DATE NULL,
    [EsBeneficiario] BIT NOT NULL,
    [PorcentajeBeneficio] DECIMAL(9,4) NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: RH_Colaboradores_Documentos
CREATE TABLE [RH_Colaboradores_Documentos] (
    [DocumentoColaboradorID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [TipoDocumento] VARCHAR(50) NOT NULL,
    [NombreArchivo] VARCHAR(255) NULL,
    [RutaArchivo] VARCHAR(500) NULL,
    [VigenciaDesde] DATE NULL,
    [VigenciaHasta] DATE NULL,
    [Validado] BIT NOT NULL,
    [ValidadoPor] INT NULL,
    [FechaValidacion] DATETIME2 NULL,
    [Observaciones] VARCHAR(500) NULL,
    [FechaAlta] DATETIME2 NOT NULL
);
GO

-- Table: RH_Colaboradores_Domicilios
CREATE TABLE [RH_Colaboradores_Domicilios] (
    [DomicilioID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [Calle] VARCHAR(150) NULL,
    [NumeroExterior] VARCHAR(20) NULL,
    [NumeroInterior] VARCHAR(20) NULL,
    [Colonia] VARCHAR(100) NULL,
    [Municipio] VARCHAR(100) NULL,
    [Estado] VARCHAR(100) NULL,
    [Pais] VARCHAR(100) NULL,
    [CodigoPostal] VARCHAR(10) NULL,
    [EsPrincipal] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL
);
GO

-- Table: RH_Colaboradores_Expediente
CREATE TABLE [RH_Colaboradores_Expediente] (
    [ColaboradorID] INT NOT NULL,
    [Nombre_Completo] VARCHAR(255) NOT NULL,
    [CURP] VARCHAR(18) NULL,
    [RFC] VARCHAR(13) NULL,
    [CLABE_Bancaria] VARCHAR(18) NULL,
    [SucursalID] INT NULL,
    [PuestoID] INT NULL,
    [Validacion_IA_RFC] BIT NULL,
    [Validacion_IA_CURP] BIT NULL,
    [Validacion_IA_EdoCta] BIT NULL,
    [Validacion_IA_Contrato] BIT NULL,
    [Colaborador_Activo] INT NOT NULL,
    [Fecha_Alta] DATETIME NULL,
    [Estatus_Laboral] VARCHAR(20) NULL,
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

-- Table: RH_Contratos
CREATE TABLE [RH_Contratos] (
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
    [EsContratoVigente] BIT NOT NULL,
    [Firmado] BIT NOT NULL,
    [FechaFirma] DATE NULL,
    [Observaciones] VARCHAR(500) NULL,
    [CreadoPor] INT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: RH_Finiquitos
CREATE TABLE [RH_Finiquitos] (
    [FiniquitoID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [ContratoID] INT NULL,
    [MotivoBajaID] SMALLINT NULL,
    [FechaBaja] DATE NOT NULL,
    [FechaCalculo] DATE NOT NULL,
    [DiasPendientesPago] DECIMAL(9,2) NOT NULL,
    [VacacionesPendientesDias] DECIMAL(9,2) NOT NULL,
    [PrimaVacacionalMonto] DECIMAL(18,2) NOT NULL,
    [AguinaldoProporcional] DECIMAL(18,2) NOT NULL,
    [IndemnizacionMonto] DECIMAL(18,2) NOT NULL,
    [OtrasPercepciones] DECIMAL(18,2) NOT NULL,
    [OtrasDeducciones] DECIMAL(18,2) NOT NULL,
    [NetoPagar] DECIMAL(18,2) NOT NULL,
    [Estatus] VARCHAR(20) NOT NULL,
    [AutorizadoPor] INT NULL,
    [PeriodoNominaID] INT NULL,
    [NominaID] INT NULL,
    [Observaciones] VARCHAR(500) NULL,
    [FechaAlta] DATETIME2 NOT NULL
);
GO

-- Table: RH_Finiquitos_Detalle
CREATE TABLE [RH_Finiquitos_Detalle] (
    [FiniquitoDetalleID] INT NOT NULL,
    [FiniquitoID] INT NOT NULL,
    [ConceptoNominaID] INT NOT NULL,
    [Importe] DECIMAL(18,2) NOT NULL,
    [ImporteGravado] DECIMAL(18,2) NOT NULL,
    [ImporteExento] DECIMAL(18,2) NOT NULL,
    [Observaciones] VARCHAR(300) NULL
);
GO

-- Table: RH_Flujo_Nomina_Sucursal
CREATE TABLE [RH_Flujo_Nomina_Sucursal] (
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
    [Intentos_Reenvio] INT NULL,
    [PeriodoNominaID] INT NULL
);
GO

-- Table: RH_GruposNomina
CREATE TABLE [RH_GruposNomina] (
    [GrupoNominaID] INT NOT NULL,
    [CodigoGrupoNomina] VARCHAR(20) NOT NULL,
    [NombreGrupoNomina] VARCHAR(100) NOT NULL,
    [TipoPeriodoNominaID] SMALLINT NOT NULL,
    [SucursalFiscalID] INT NOT NULL,
    [DiaPago] SMALLINT NULL,
    [DesfaseDiasPago] SMALLINT NOT NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: RH_Historial_Puestos
CREATE TABLE [RH_Historial_Puestos] (
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
    [FechaAlta] DATETIME2 NOT NULL
);
GO

-- Table: RH_Historial_Salarios
CREATE TABLE [RH_Historial_Salarios] (
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
    [FechaAlta] DATETIME2 NOT NULL
);
GO

-- Table: RH_Homologacion_Equivalencias
CREATE TABLE [RH_Homologacion_Equivalencias] (
    [EquivalenciaID] INT NOT NULL,
    [Tipo] VARCHAR(20) NOT NULL,
    [Valor_Origen] NVARCHAR(200) NOT NULL,
    [Valor_Normalizado] NVARCHAR(200) NULL,
    [CatalogoID] INT NULL,
    [Estado] VARCHAR(20) NULL,
    [Usuario_Aprobador] VARCHAR(100) NULL,
    [Fecha_Aprobacion] DATETIME NULL,
    [Observaciones] NVARCHAR(500) NULL
);
GO

-- Table: RH_Importacion_Bitacora
CREATE TABLE [RH_Importacion_Bitacora] (
    [BitacoraID] INT NOT NULL,
    [Fecha_Ejecucion] DATETIME NULL,
    [Fuente] VARCHAR(50) NOT NULL,
    [Archivo_Origen] NVARCHAR(255) NULL,
    [Total_Registros_Leidos] INT NULL,
    [Total_Insertados] INT NULL,
    [Total_Actualizados] INT NULL,
    [Total_Duplicados_Omitidos] INT NULL,
    [Total_Incompletos] INT NULL,
    [Total_Errores] INT NULL,
    [Usuario_Ejecutor] NVARCHAR(100) NULL,
    [Duracion_Segundos] INT NULL,
    [Estado] VARCHAR(20) NULL,
    [Detalle_JSON] NVARCHAR(MAX) NULL
);
GO

-- Table: RH_Importacion_Staging
CREATE TABLE [RH_Importacion_Staging] (
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
    [Fecha_Importacion] DATETIME NULL,
    [Usuario_Importador] NVARCHAR(100) NULL,
    [Estado] VARCHAR(20) NULL,
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

-- Table: RH_IMSS_Movimientos
CREATE TABLE [RH_IMSS_Movimientos] (
    [MovimientoIMSSID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [ContratoID] INT NULL,
    [TipoMovimiento] VARCHAR(30) NOT NULL,
    [FechaMovimiento] DATE NOT NULL,
    [SalarioBaseCotizacion] DECIMAL(18,2) NULL,
    [SalarioDiarioIntegrado] DECIMAL(18,2) NULL,
    [FolioIMSS] VARCHAR(50) NULL,
    [EnviadoIDSE] BIT NOT NULL,
    [FechaEnvioIDSE] DATETIME2 NULL,
    [ProcesadoSUA] BIT NOT NULL,
    [FechaProcesadoSUA] DATETIME2 NULL,
    [Observaciones] VARCHAR(500) NULL,
    [CapturadoPor] INT NULL,
    [FechaAlta] DATETIME2 NOT NULL
);
GO

-- Table: RH_Incidencias_Nomina
CREATE TABLE [RH_Incidencias_Nomina] (
    [IncidenciaID] INT NOT NULL,
    [ColaboradorID] INT NULL,
    [Tipo_Incidencia] VARCHAR(50) NULL,
    [Monto] DECIMAL(18,2) NULL,
    [Unidades] DECIMAL(5,2) NULL,
    [Fecha_Incidencia] DATE NULL,
    [Capturado_Por] INT NULL,
    [Fecha_Registro] DATETIME NULL,
    [ConceptoNominaID] INT NULL,
    [PeriodoNominaID] INT NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Autorizado] BIT NOT NULL,
    [AutorizadoPor] INT NULL,
    [FechaAutorizacion] DATETIME2 NULL
);
GO

-- Table: RH_Nomina
CREATE TABLE [RH_Nomina] (
    [NominaID] INT NOT NULL,
    [PeriodoNominaID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [ContratoID] INT NULL,
    [SucursalID] INT NOT NULL,
    [SucursalFiscalID] INT NOT NULL,
    [DiasPagados] DECIMAL(9,2) NOT NULL,
    [HorasPagadas] DECIMAL(9,2) NOT NULL,
    [Faltas] DECIMAL(9,2) NOT NULL,
    [Incapacidades] DECIMAL(9,2) NOT NULL,
    [SalarioDiario] DECIMAL(18,2) NOT NULL,
    [SalarioDiarioIntegrado] DECIMAL(18,2) NULL,
    [SalarioBaseCotizacion] DECIMAL(18,2) NULL,
    [TotalPercepciones] DECIMAL(18,2) NOT NULL,
    [TotalDeducciones] DECIMAL(18,2) NOT NULL,
    [TotalOtrosPagos] DECIMAL(18,2) NOT NULL,
    [TotalGravado] DECIMAL(18,2) NOT NULL,
    [TotalExento] DECIMAL(18,2) NOT NULL,
    [ISR] DECIMAL(18,2) NOT NULL,
    [SubsidioEmpleo] DECIMAL(18,2) NOT NULL,
    [CuotaIMSS] DECIMAL(18,2) NOT NULL,
    [RetencionInfonavit] DECIMAL(18,2) NOT NULL,
    [NetoPagar] DECIMAL(18,2) NOT NULL,
    [EstatusNomina] VARCHAR(20) NOT NULL,
    [Procesado] BIT NOT NULL,
    [Timbrado] BIT NOT NULL,
    [Pagado] BIT NOT NULL,
    [FechaCalculo] DATETIME2 NULL,
    [FechaTimbrado] DATETIME2 NULL,
    [FechaPagoReal] DATETIME2 NULL,
    [Observaciones] VARCHAR(500) NULL
);
GO

-- Table: RH_Nomina_Detalle
CREATE TABLE [RH_Nomina_Detalle] (
    [NominaDetalleID] INT NOT NULL,
    [NominaID] INT NOT NULL,
    [ConceptoNominaID] INT NOT NULL,
    [Origen] VARCHAR(20) NOT NULL,
    [ReferenciaID] INT NULL,
    [Unidades] DECIMAL(18,4) NULL,
    [ImporteUnitario] DECIMAL(18,6) NULL,
    [Importe] DECIMAL(18,2) NOT NULL,
    [ImporteGravado] DECIMAL(18,2) NOT NULL,
    [ImporteExento] DECIMAL(18,2) NOT NULL,
    [Observaciones] VARCHAR(300) NULL
);
GO

-- Table: RH_Nomina_Dispersion
CREATE TABLE [RH_Nomina_Dispersion] (
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
    [EstatusDispersion] VARCHAR(30) NOT NULL,
    [FechaGeneracion] DATETIME2 NOT NULL,
    [FechaAplicacion] DATETIME2 NULL,
    [Observaciones] VARCHAR(500) NULL
);
GO

-- Table: RH_Nomina_Recibos
CREATE TABLE [RH_Nomina_Recibos] (
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
    [Cancelado] BIT NOT NULL,
    [FechaCancelacion] DATETIME2 NULL,
    [MotivoCancelacion] VARCHAR(200) NULL,
    [Observaciones] VARCHAR(500) NULL
);
GO

-- Table: RH_Periodos_Nomina
CREATE TABLE [RH_Periodos_Nomina] (
    [PeriodoNominaID] INT NOT NULL,
    [GrupoNominaID] INT NOT NULL,
    [EstatusPeriodoNominaID] SMALLINT NOT NULL,
    [Ejercicio] INT NOT NULL,
    [NumeroPeriodo] INT NOT NULL,
    [FechaInicio] DATE NOT NULL,
    [FechaFin] DATE NOT NULL,
    [FechaPago] DATE NOT NULL,
    [FechaCorteIncidencias] DATE NULL,
    [EsAjuste] BIT NOT NULL,
    [Observaciones] VARCHAR(500) NULL,
    [CerradoPor] INT NULL,
    [FechaCierre] DATETIME2 NULL,
    [FechaAlta] DATETIME2 NOT NULL
);
GO

-- Table: RH_Prestamos
CREATE TABLE [RH_Prestamos] (
    [PrestamoID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [TipoPrestamo] VARCHAR(30) NOT NULL,
    [FechaPrestamo] DATE NOT NULL,
    [MontoOriginal] DECIMAL(18,2) NOT NULL,
    [SaldoActual] DECIMAL(18,2) NOT NULL,
    [Cuotas] INT NULL,
    [MontoCuota] DECIMAL(18,2) NULL,
    [DescuentoPorPeriodo] DECIMAL(18,2) NULL,
    [Estatus] VARCHAR(20) NOT NULL,
    [AutorizadoPor] INT NULL,
    [Observaciones] VARCHAR(500) NULL,
    [FechaAlta] DATETIME2 NOT NULL
);
GO

-- Table: RH_Prestamos_Detalle
CREATE TABLE [RH_Prestamos_Detalle] (
    [PrestamoDetalleID] INT NOT NULL,
    [PrestamoID] INT NOT NULL,
    [PeriodoNominaID] INT NULL,
    [NominaID] INT NULL,
    [FechaProgramada] DATE NULL,
    [FechaAplicacion] DATE NULL,
    [ImporteProgramado] DECIMAL(18,2) NOT NULL,
    [ImporteAplicado] DECIMAL(18,2) NOT NULL,
    [Estatus] VARCHAR(20) NOT NULL,
    [Observaciones] VARCHAR(300) NULL
);
GO

-- Table: RH_Reloj_Checador
CREATE TABLE [RH_Reloj_Checador] (
    [CheckID] INT NOT NULL,
    [ColaboradorID] INT NULL,
    [Tipo_Registro] VARCHAR(10) NULL,
    [FechaHora] DATETIME NULL,
    [Geolocalizacion] VARCHAR(100) NULL,
    [Validado_Gerencia] BIT NULL
);
GO

-- Table: RH_Vacaciones_Movimientos
CREATE TABLE [RH_Vacaciones_Movimientos] (
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
    [FechaAlta] DATETIME2 NOT NULL
);
GO

-- Table: RH_Vacaciones_Saldos
CREATE TABLE [RH_Vacaciones_Saldos] (
    [VacacionSaldoID] INT NOT NULL,
    [ColaboradorID] INT NOT NULL,
    [Ejercicio] INT NOT NULL,
    [Aniversario] INT NOT NULL,
    [DiasOtorgados] DECIMAL(9,2) NOT NULL,
    [DiasTomados] DECIMAL(9,2) NOT NULL,
    [DiasPagados] DECIMAL(9,2) NOT NULL,
    [DiasDisponibles] DECIMAL(11,2) NULL,
    [PrimaVacacionalPct] DECIMAL(9,4) NOT NULL,
    [FechaGeneracion] DATE NOT NULL,
    [FechaVencimiento] DATE NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Scheduler_BitacoraJobs
CREATE TABLE [Scheduler_BitacoraJobs] (
    [ID] INT NOT NULL,
    [JobName] VARCHAR(100) NOT NULL,
    [RunID] VARCHAR(50) NOT NULL,
    [Accion] VARCHAR(50) NOT NULL,
    [FechaAccion] DATETIME NULL,
    [ServerID] VARCHAR(50) NULL,
    [DetallesJSON] NVARCHAR(MAX) NULL,
    [Exito] BIT NULL,
    [MensajeError] NVARCHAR(MAX) NULL
);
GO

-- Table: Scheduler_InventariosProcesados
CREATE TABLE [Scheduler_InventariosProcesados] (
    [ID] INT NOT NULL,
    [SistemaOrigen] VARCHAR(50) NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [SucursalID] VARCHAR(50) NOT NULL,
    [AlmacenID] VARCHAR(50) NOT NULL,
    [FolioInventario] VARCHAR(100) NOT NULL,
    [Estado] VARCHAR(20) NULL,
    [Intentos] INT NULL,
    [FechaDeteccion] DATETIME NULL,
    [FechaProcesamiento] DATETIME NULL,
    [FechaUltimoIntento] DATETIME NULL,
    [ErrorMensaje] NVARCHAR(MAX) NULL,
    [WorkflowID] VARCHAR(50) NULL,
    [DetallesJSON] NVARCHAR(MAX) NULL
);
GO

-- Table: Scheduler_PedidosProcesados
CREATE TABLE [Scheduler_PedidosProcesados] (
    [ID] INT NOT NULL,
    [SistemaOrigen] VARCHAR(50) NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [EmpresaID] VARCHAR(50) NOT NULL,
    [SucursalID] VARCHAR(50) NULL,
    [FolioPedido] VARCHAR(100) NOT NULL,
    [Estado] VARCHAR(20) NULL,
    [FechaDeteccion] DATETIME NULL,
    [FechaProcesamiento] DATETIME NULL,
    [TipoDocumento] VARCHAR(50) NULL,
    [DetallesJSON] NVARCHAR(MAX) NULL
);
GO

-- Table: Servidores_Conexiones
CREATE TABLE [Servidores_Conexiones] (
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
    [fecha_ultima_sincronizacion] DATETIME2 NULL,
    [source_status] VARCHAR(50) NULL,
    [ultimo_error_sync] NVARCHAR(500) NULL
);
GO

-- Table: Servidores_Conexiones_backup_tipos_enriq_20260513_0840
CREATE TABLE [Servidores_Conexiones_backup_tipos_enriq_20260513_0840] (
    [mongodb_id] NVARCHAR(100) NULL,
    [nombre] NVARCHAR(100) NOT NULL,
    [tipos_movimiento_anterior] NVARCHAR(MAX) NULL,
    [fecha_backup] DATETIME NOT NULL,
    [fase] VARCHAR(35) NOT NULL
);
GO

-- Table: Servidores_Conexiones_backup_tipos_mov_20260513_0729
CREATE TABLE [Servidores_Conexiones_backup_tipos_mov_20260513_0729] (
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

-- Table: Servidores_Conexiones_Log
CREATE TABLE [Servidores_Conexiones_Log] (
    [log_id] BIGINT NOT NULL,
    [servidor_id] UNIQUEIDENTIFIER NULL,
    [accion] NVARCHAR(20) NULL,
    [datos_anteriores] NVARCHAR(MAX) NULL,
    [datos_nuevos] NVARCHAR(MAX) NULL,
    [usuario] NVARCHAR(100) NULL,
    [fecha] DATETIME NULL,
    [ip_origen] NVARCHAR(50) NULL
);
GO

-- Table: Servidores_Status
CREATE TABLE [Servidores_Status] (
    [StatusID] INT NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [IsOnline] BIT NULL,
    [ResponseTimeMs] INT NULL,
    [LastCheck] DATETIME NULL
);
GO

-- Table: Sesiones
CREATE TABLE [Sesiones] (
    [SesionID] VARCHAR(50) NOT NULL,
    [UsuarioID] VARCHAR(50) NOT NULL,
    [TipoUsuario] VARCHAR(20) NULL,
    [RefreshTokenHash] VARCHAR(128) NOT NULL,
    [FamiliaTokenID] VARCHAR(50) NOT NULL,
    [FechaCreacion] DATETIME NULL,
    [FechaExpiracion] DATETIME NOT NULL,
    [UltimaActividad] DATETIME NULL,
    [EstaActiva] BIT NULL,
    [IPCliente] VARCHAR(45) NULL,
    [UserAgent] VARCHAR(500) NULL,
    [FechaModificacion] DATETIME NULL
);
GO

-- Table: SesionesHistorico
CREATE TABLE [SesionesHistorico] (
    [HistoricoID] INT NOT NULL,
    [SesionID] VARCHAR(50) NOT NULL,
    [UsuarioID] VARCHAR(50) NOT NULL,
    [TipoUsuario] VARCHAR(20) NULL,
    [Accion] VARCHAR(50) NOT NULL,
    [FechaAccion] DATETIME NULL,
    [IPCliente] VARCHAR(45) NULL,
    [UserAgent] VARCHAR(500) NULL,
    [DetallesJSON] NVARCHAR(MAX) NULL,
    [AccionRealizadaPor] VARCHAR(50) NULL
);
GO

-- Table: Sistema_Capacidades
CREATE TABLE [Sistema_Capacidades] (
    [SistemaCapacidadID] INT NOT NULL,
    [SistemaTipoID] INT NOT NULL,
    [CodigoCapacidad] VARCHAR(50) NOT NULL,
    [Descripcion] NVARCHAR(200) NULL,
    [RequiereApiLocal] BIT NULL,
    [RequiereSqlDirecto] BIT NULL,
    [ConfiguracionJSON] NVARCHAR(MAX) NULL,
    [Activo] BIT NULL,
    [CreatedAt] DATETIME NULL,
    [UpdatedAt] DATETIME NULL
);
GO

-- Table: Sistema_Catalogo
CREATE TABLE [Sistema_Catalogo] (
    [SistemaID] INT NOT NULL,
    [Codigo] NVARCHAR(50) NOT NULL,
    [Descripcion] NVARCHAR(100) NOT NULL,
    [Activo] BIT NOT NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [FechaActualizacion] DATETIME2 NULL,
    [Estado] NVARCHAR(20) NOT NULL,
    [SolicitadoPorUsuarioID] INT NULL,
    [AutorizadoPorUsuarioID] INT NULL,
    [FechaSolicitud] DATETIME2 NULL,
    [FechaAutorizacion] DATETIME2 NULL,
    [SolicitadoPorEmail] NVARCHAR(200) NULL,
    [AutorizadoPorEmail] NVARCHAR(200) NULL
);
GO

-- Table: Sistema_Empresas
CREATE TABLE [Sistema_Empresas] (
    [EmpresaID] INT NOT NULL,
    [CodigoEmpresa] VARCHAR(20) NOT NULL,
    [NombreEmpresa] NVARCHAR(100) NOT NULL,
    [NombreComercial] NVARCHAR(100) NULL,
    [RFC] VARCHAR(13) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [UpdatedBy] VARCHAR(100) NULL
);
GO

-- Table: Sistema_EmpresasAlias
CREATE TABLE [Sistema_EmpresasAlias] (
    [EmpresaAliasID] INT NOT NULL,
    [EmpresaID] INT NOT NULL,
    [Alias] NVARCHAR(200) NOT NULL,
    [AliasNormalizado] NVARCHAR(200) NOT NULL,
    [OrigenAlias] VARCHAR(50) NULL,
    [Activo] BIT NOT NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [FechaActualizacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [UpdatedBy] VARCHAR(100) NULL
);
GO

-- Table: Sistema_EmpresasMongoMap
CREATE TABLE [Sistema_EmpresasMongoMap] (
    [MapID] INT NOT NULL,
    [EmpresaMongoUUID] VARCHAR(50) NOT NULL,
    [EmpresaMongoLegacyID] VARCHAR(50) NULL,
    [EmpresaID_SQL] INT NOT NULL,
    [CodigoEmpresa] VARCHAR(20) NOT NULL,
    [NombreEmpresa] NVARCHAR(100) NOT NULL,
    [MetodoMapeo] VARCHAR(50) NOT NULL,
    [Activo] BIT NOT NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [FechaActualizacion] DATETIME2 NULL,
    [Observaciones] NVARCHAR(500) NULL,
    [CreatedBy] VARCHAR(100) NOT NULL
);
GO

-- Table: Sistema_EmpresasServidores
CREATE TABLE [Sistema_EmpresasServidores] (
    [EmpresaServidorID] INT NOT NULL,
    [EmpresaID] INT NOT NULL,
    [ServidorID] UNIQUEIDENTIFIER NOT NULL,
    [SistemaTipoID] INT NULL,
    [RolConexion] VARCHAR(50) NOT NULL,
    [NumeroSucursalSistema] INT NULL,
    [CodigoSucursalSistema] VARCHAR(20) NULL,
    [NombreSucursalSistema] NVARCHAR(100) NULL,
    [Prioridad] INT NOT NULL,
    [EsPrincipal] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [FechaActualizacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [UpdatedBy] VARCHAR(100) NULL,
    [Observaciones] NVARCHAR(500) NULL
);
GO

-- Table: Sistema_Gobierno_Tablas
CREATE TABLE [Sistema_Gobierno_Tablas] (
    [id] UNIQUEIDENTIFIER NOT NULL,
    [nombre_tabla] NVARCHAR(128) NOT NULL,
    [esquema] NVARCHAR(128) NOT NULL,
    [modulo] NVARCHAR(100) NOT NULL,
    [categoria] NVARCHAR(50) NOT NULL,
    [estado] NVARCHAR(50) NOT NULL,
    [fuente_verdad] NVARCHAR(100) NULL,
    [tabla_reemplazo] NVARCHAR(128) NULL,
    [permite_insert] BIT NOT NULL,
    [permite_update] BIT NOT NULL,
    [permite_delete] BIT NOT NULL,
    [observaciones] NVARCHAR(MAX) NULL,
    [fecha_alta] DATETIME2 NOT NULL,
    [fecha_ultima_actualizacion] DATETIME2 NOT NULL
);
GO

-- Table: Sistema_HorariosServicioUnidad
CREATE TABLE [Sistema_HorariosServicioUnidad] (
    [id] UNIQUEIDENTIFIER NOT NULL,
    [unidad_negocio_id] NVARCHAR(50) NOT NULL,
    [dia_semana] INT NOT NULL,
    [hora_inicio_operativo] TIME NOT NULL,
    [hora_fin_operativo] TIME NOT NULL,
    [cruza_medianoche] BIT NOT NULL,
    [activo] BIT NOT NULL,
    [fecha_creacion] DATETIME2 NULL,
    [fecha_modificacion] DATETIME2 NULL
);
GO

-- Table: Sistema_Migracion_MongoSQL_Mapeo
CREATE TABLE [Sistema_Migracion_MongoSQL_Mapeo] (
    [id] UNIQUEIDENTIFIER NOT NULL,
    [coleccion_mongo] NVARCHAR(200) NOT NULL,
    [tabla_sql_destino] NVARCHAR(128) NULL,
    [modulo] NVARCHAR(100) NOT NULL,
    [estado] NVARCHAR(50) NOT NULL,
    [prioridad] NVARCHAR(20) NOT NULL,
    [estrategia] NVARCHAR(MAX) NULL,
    [fecha_inicio] DATETIME2 NULL,
    [fecha_fin] DATETIME2 NULL,
    [observaciones] NVARCHAR(MAX) NULL,
    [fecha_alta] DATETIME2 NOT NULL
);
GO

-- Table: Sistema_Modulos
CREATE TABLE [Sistema_Modulos] (
    [ModuloID] INT NOT NULL,
    [Codigo] NVARCHAR(50) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Icono] NVARCHAR(50) NULL,
    [Orden] INT NULL,
    [EsPrincipal] BIT NULL,
    [EsSatelite] BIT NULL,
    [EsPortal] BIT NULL,
    [URLExterna] NVARCHAR(255) NULL,
    [Activo] BIT NULL,
    [FechaCreacion] DATETIME NULL
);
GO

-- Table: Sistema_ModulosMenus
CREATE TABLE [Sistema_ModulosMenus] (
    [MenuID] INT NOT NULL,
    [ModuloID] INT NOT NULL,
    [MenuPadreID] INT NULL,
    [Codigo] NVARCHAR(100) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(255) NULL,
    [Icono] NVARCHAR(50) NULL,
    [Ruta] NVARCHAR(255) NULL,
    [Orden] INT NULL,
    [RequierePermiso] NVARCHAR(100) NULL,
    [Activo] BIT NULL,
    [FechaCreacion] DATETIME NULL
);
GO

-- Table: Sistema_ModulosPermisos
CREATE TABLE [Sistema_ModulosPermisos] (
    [PermisoID] INT NOT NULL,
    [ModuloID] INT NOT NULL,
    [Codigo] NVARCHAR(100) NOT NULL,
    [Nombre] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(255) NULL,
    [Categoria] NVARCHAR(50) NULL,
    [Activo] BIT NULL,
    [FechaCreacion] DATETIME NULL
);
GO

-- Table: Sistema_ModulosVisibilidad
CREATE TABLE [Sistema_ModulosVisibilidad] (
    [ModuloVisibilidadID] INT NOT NULL,
    [SistemaTipoID] INT NOT NULL,
    [CodigoModulo] VARCHAR(50) NOT NULL,
    [DescripcionModulo] NVARCHAR(100) NULL,
    [Visible] BIT NULL,
    [OrdenMenu] INT NULL,
    [ConfiguracionJSON] NVARCHAR(MAX) NULL,
    [Activo] BIT NULL,
    [CreatedAt] DATETIME NULL
);
GO

-- Table: Sistema_RBAC_Permisos
CREATE TABLE [Sistema_RBAC_Permisos] (
    [permiso_id] UNIQUEIDENTIFIER NOT NULL,
    [codigo] NVARCHAR(150) NOT NULL,
    [nombre] NVARCHAR(200) NOT NULL,
    [modulo] NVARCHAR(100) NOT NULL,
    [descripcion] NVARCHAR(500) NULL,
    [activo] BIT NOT NULL,
    [fecha_alta] DATETIME2 NOT NULL,
    [fecha_ultima_actualizacion] DATETIME2 NOT NULL
);
GO

-- Table: Sistema_RBAC_Roles
CREATE TABLE [Sistema_RBAC_Roles] (
    [rol_id] UNIQUEIDENTIFIER NOT NULL,
    [codigo] NVARCHAR(100) NOT NULL,
    [nombre] NVARCHAR(200) NOT NULL,
    [descripcion] NVARCHAR(500) NULL,
    [es_sistema] BIT NOT NULL,
    [activo] BIT NOT NULL,
    [fecha_alta] DATETIME2 NOT NULL,
    [fecha_ultima_actualizacion] DATETIME2 NOT NULL
);
GO

-- Table: Sistema_RBAC_RolesPermisos
CREATE TABLE [Sistema_RBAC_RolesPermisos] (
    [rol_permiso_id] UNIQUEIDENTIFIER NOT NULL,
    [rol_id] UNIQUEIDENTIFIER NOT NULL,
    [permiso_id] UNIQUEIDENTIFIER NOT NULL,
    [activo] BIT NOT NULL,
    [fecha_alta] DATETIME2 NOT NULL
);
GO

-- Table: Sistema_ServidorSucursalesConfig
CREATE TABLE [Sistema_ServidorSucursalesConfig] (
    [ConfigID] INT NOT NULL,
    [ServidorID] UNIQUEIDENTIFIER NOT NULL,
    [SucursalNombre] NVARCHAR(200) NOT NULL,
    [SucursalCodigo] VARCHAR(50) NULL,
    [SucursalID] INT NULL,
    [VisibleEnOperaciones] BIT NOT NULL,
    [VisibleEnComercial] BIT NOT NULL,
    [MongoConfigID] VARCHAR(36) NULL,
    [FuenteMigracion] VARCHAR(50) NULL,
    [Activo] BIT NOT NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [UpdatedBy] VARCHAR(100) NULL,
    [Observaciones] NVARCHAR(500) NULL
);
GO

-- Table: Sistema_Sucursales
CREATE TABLE [Sistema_Sucursales] (
    [SucursalID] INT NOT NULL,
    [CodigoSucursal] VARCHAR(50) NOT NULL,
    [NombreSucursal] NVARCHAR(200) NOT NULL,
    [EmpresaID] INT NULL,
    [UnidadNegocioID] INT NULL,
    [MongoUUID] VARCHAR(36) NULL,
    [MongoEmpresaUUID] VARCHAR(36) NULL,
    [FuenteMigracion] VARCHAR(50) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [UpdatedBy] VARCHAR(100) NULL,
    [Observaciones] NVARCHAR(500) NULL
);
GO

-- Table: Sistema_SucursalServidorConfig
CREATE TABLE [Sistema_SucursalServidorConfig] (
    [ConfigID] INT NOT NULL,
    [ServerID] VARCHAR(50) NOT NULL,
    [SucursalNombre] VARCHAR(200) NOT NULL,
    [VisibleEnOperaciones] BIT NULL,
    [Activa] BIT NULL,
    [FechaCreacion] DATETIME NULL
);
GO

-- Table: Sistema_SucursalServidorMapeo
CREATE TABLE [Sistema_SucursalServidorMapeo] (
    [MapeoID] INT NOT NULL,
    [SucursalID] INT NOT NULL,
    [ServidorID] UNIQUEIDENTIFIER NOT NULL,
    [SucursalOrigenID] VARCHAR(100) NULL,
    [MongoSucursalUUID] VARCHAR(36) NULL,
    [MongoServidorUUID] VARCHAR(36) NULL,
    [FuenteMigracion] VARCHAR(50) NULL,
    [Activo] BIT NOT NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [Observaciones] NVARCHAR(500) NULL
);
GO

-- Table: Sistema_Tipos
CREATE TABLE [Sistema_Tipos] (
    [SistemaTipoID] INT NOT NULL,
    [CodigoSistema] VARCHAR(50) NOT NULL,
    [NombreSistema] NVARCHAR(100) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Activo] BIT NOT NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [FechaActualizacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [UpdatedBy] VARCHAR(100) NULL
);
GO

-- Table: Sistema_TiposVariantes
CREATE TABLE [Sistema_TiposVariantes] (
    [VarianteID] INT NOT NULL,
    [SistemaTipoID] INT NOT NULL,
    [VarianteNombre] VARCHAR(50) NOT NULL,
    [EsCanonico] BIT NULL,
    [Activo] BIT NULL,
    [CreatedAt] DATETIME NULL
);
GO

-- Table: Sistema_TurnosOperativosUnidad
CREATE TABLE [Sistema_TurnosOperativosUnidad] (
    [id] UNIQUEIDENTIFIER NOT NULL,
    [unidad_negocio_id] NVARCHAR(50) NOT NULL,
    [turno_codigo] NVARCHAR(20) NOT NULL,
    [turno_nombre] NVARCHAR(100) NOT NULL,
    [hora_inicio] TIME NOT NULL,
    [hora_fin] TIME NOT NULL,
    [cruza_medianoche] BIT NOT NULL,
    [aplica_ventas_dia] BIT NOT NULL,
    [es_turno_principal] BIT NOT NULL,
    [orden] INT NOT NULL,
    [activo] BIT NOT NULL,
    [fecha_creacion] DATETIME2 NULL,
    [creado_por] NVARCHAR(100) NULL,
    [fecha_modificacion] DATETIME2 NULL,
    [modificado_por] NVARCHAR(100) NULL
);
GO

-- Table: Sistema_UnidadesNegocioPerfilDigital
CREATE TABLE [Sistema_UnidadesNegocioPerfilDigital] (
    [PerfilDigitalID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] INT NOT NULL,
    [UnidadNegocioID] INT NULL,
    [ServerID] UNIQUEIDENTIFIER NULL,
    [NombreComercial] NVARCHAR(200) NULL,
    [ConceptoRestaurante] NVARCHAR(500) NULL,
    [TipoRestaurante] VARCHAR(50) NULL,
    [SegmentoPrecio] VARCHAR(30) NULL,
    [Ciudad] NVARCHAR(100) NULL,
    [Estado] NVARCHAR(100) NULL,
    [Pais] VARCHAR(50) NULL,
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
    [Moneda] VARCHAR(10) NULL,
    [DescripcionConcepto] NVARCHAR(MAX) NULL,
    [PalabrasClave] NVARCHAR(1000) NULL,
    [Activo] BIT NULL,
    [FechaCreacion] DATETIME2 NULL,
    [UsuarioCreacion] NVARCHAR(100) NULL,
    [FechaModificacion] DATETIME2 NULL,
    [UsuarioModificacion] NVARCHAR(100) NULL
);
GO

-- Table: Sync_Control_Ejecuciones
CREATE TABLE [Sync_Control_Ejecuciones] (
    [SyncControlID] INT NOT NULL,
    [SyncRunID] NVARCHAR(50) NOT NULL,
    [SyncType] NVARCHAR(50) NOT NULL,
    [ServerID] NVARCHAR(50) NULL,
    [EmpresaID] INT NULL,
    [FechaInicio] DATE NOT NULL,
    [FechaFin] DATE NOT NULL,
    [VentanaInicioHoraConfig] INT NOT NULL,
    [VentanaFinHoraConfig] INT NOT NULL,
    [IsDryRun] BIT NOT NULL,
    [RegistrosProcesados] INT NOT NULL,
    [RegistrosInsertados] INT NOT NULL,
    [RegistrosActualizados] INT NOT NULL,
    [RegistrosError] INT NOT NULL,
    [Status] NVARCHAR(20) NOT NULL,
    [ErrorMessage] NVARCHAR(MAX) NULL,
    [StartedAtMexico] DATETIME2 NOT NULL,
    [FinishedAtMexico] DATETIME2 NULL,
    [DurationSeconds] INT NULL,
    [CreatedAt] DATETIME2 NOT NULL
);
GO

-- Table: Sync_Customers
CREATE TABLE [Sync_Customers] (
    [customer_id] VARCHAR(64) NOT NULL,
    [full_name] NVARCHAR(200) NOT NULL,
    [commercial_name] NVARCHAR(200) NULL,
    [email] VARCHAR(150) NULL,
    [phone] VARCHAR(32) NULL,
    [affiliate_tier] VARCHAR(16) NULL,
    [sync_status] VARCHAR(16) NULL,
    [last_sync] DATETIME NULL
);
GO

-- Table: Sync_Impuestos_Origen
CREATE TABLE [Sync_Impuestos_Origen] (
    [MapeoID] UNIQUEIDENTIFIER NOT NULL,
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
    [FechaSincronizacion] DATETIME2 NULL,
    [FechaCreacion] DATETIME2 NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Sync_Inventory
CREATE TABLE [Sync_Inventory] (
    [sku] VARCHAR(64) NOT NULL,
    [item_name] NVARCHAR(200) NOT NULL,
    [stock_qty] INT NULL,
    [min_qty_warning] INT NULL,
    [warehouse] NVARCHAR(100) NOT NULL,
    [last_audit] DATETIME NULL,
    [sync_status] VARCHAR(16) NULL
);
GO

-- Table: Sync_KPI_Ventas_Unidades
CREATE TABLE [Sync_KPI_Ventas_Unidades] (
    [id] INT NOT NULL,
    [UnidadID] VARCHAR(50) NOT NULL,
    [UnidadNombre] NVARCHAR(100) NOT NULL,
    [Mes] VARCHAR(50) NOT NULL,
    [Anio] INT NOT NULL,
    [Ventas_Reales_M] DECIMAL(18,4) NULL,
    [Proyeccion_Ventas] DECIMAL(18,4) NULL,
    [Meta_Mensual] DECIMAL(18,4) NULL,
    [PorcentajeCumplimiento] DECIMAL(5,2) NULL,
    [UltimaActualizacion] DATETIME NULL,
    [Dias_Con_Ventas] DECIMAL(10,2) NULL,
    [Proyeccion_Anual_Ventas] DECIMAL(18,4) NULL
);
GO

-- Table: Sync_Logs
CREATE TABLE [Sync_Logs] (
    [id] INT NOT NULL,
    [service] NVARCHAR(100) NOT NULL,
    [type] NVARCHAR(20) NOT NULL,
    [message] NVARCHAR(MAX) NOT NULL,
    [timestamp] DATETIME NULL,
    [operador] NVARCHAR(100) NULL
);
GO

-- Table: Sync_Menus
CREATE TABLE [Sync_Menus] (
    [id] INT NOT NULL,
    [titulo] NVARCHAR(100) NOT NULL,
    [label] NVARCHAR(100) NOT NULL,
    [icon] NVARCHAR(50) NOT NULL,
    [route] NVARCHAR(100) NOT NULL,
    [active] BIT NULL,
    [orden] INT NOT NULL,
    [rol_permitido] NVARCHAR(100) NULL,
    [ultima_actualizacion] DATETIME NULL
);
GO

-- Table: Sync_Mesas
CREATE TABLE [Sync_Mesas] (
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
    [Capacidad] INT NULL,
    [TotalCuentas] INT NULL,
    [TotalComensales] INT NULL,
    [VentaTotal] DECIMAL(18,2) NULL,
    [TicketPromedio] DECIMAL(18,2) NULL,
    [TiempoPromedioOcupacion] INT NULL,
    [RotacionDia] DECIMAL(8,2) NULL,
    [EstadoActual] NVARCHAR(20) NULL,
    [CuentaActualID] NVARCHAR(50) NULL,
    [MeseroActualID] NVARCHAR(50) NULL,
    [MeseroActualNombre] NVARCHAR(100) NULL,
    [HoraAperturaCuenta] DATETIME2 NULL,
    [FechaSync] DATETIME2 NULL
);
GO

-- Table: Sync_Metas_Comerciales
CREATE TABLE [Sync_Metas_Comerciales] (
    [ID] INT NOT NULL,
    [MetaID] NVARCHAR(50) NOT NULL,
    [ServerID] NVARCHAR(50) NOT NULL,
    [SucursalID] NVARCHAR(20) NOT NULL,
    [SucursalNombre] NVARCHAR(100) NULL,
    [Anio] INT NOT NULL,
    [Mes] INT NOT NULL,
    [MetaVentaBruta] DECIMAL(18,2) NULL,
    [MetaVentaNeta] DECIMAL(18,2) NULL,
    [MetaTicketPromedio] DECIMAL(18,2) NULL,
    [MetaCuentas] INT NULL,
    [MetaComensales] INT NULL,
    [MetaProductosMes] INT NULL,
    [VentaBrutaActual] DECIMAL(18,2) NULL,
    [VentaNetaActual] DECIMAL(18,2) NULL,
    [TicketPromedioActual] DECIMAL(18,2) NULL,
    [CuentasActual] INT NULL,
    [ComensalesActual] INT NULL,
    [PorcentajeCumplimiento] DECIMAL(8,2) NULL,
    [DiasTranscurridos] INT NULL,
    [DiasRestantes] INT NULL,
    [ProyeccionMes] DECIMAL(18,2) NULL,
    [FechaActualizacion] DATETIME2 NULL,
    [FechaSync] DATETIME2 NULL,
    [Activo] BIT NULL
);
GO

-- Table: Sync_Movimientos_Detalle
CREATE TABLE [Sync_Movimientos_Detalle] (
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
    [Cantidad] DECIMAL(18,4) NULL,
    [PrecioUnitario] DECIMAL(18,4) NULL,
    [Descuento] DECIMAL(18,4) NULL,
    [Impuesto] DECIMAL(18,4) NULL,
    [Subtotal] DECIMAL(18,4) NULL,
    [Total] DECIMAL(18,4) NULL,
    [TipoMovimiento] NVARCHAR(20) NULL,
    [Cancelado] BIT NULL,
    [FechaSync] DATETIME2 NULL
);
GO

-- Table: Sync_PAX_Detalle
CREATE TABLE [Sync_PAX_Detalle] (
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
    [TipoPAX] NVARCHAR(20) NULL,
    [VentaCuenta] DECIMAL(18,2) NULL,
    [ConsumoPromedioPAX] DECIMAL(18,2) NULL,
    [TiempoMesa] INT NULL,
    [HoraEntrada] DATETIME2 NULL,
    [HoraSalida] DATETIME2 NULL,
    [Turno] NVARCHAR(20) NULL,
    [DiaSemana] NVARCHAR(20) NULL,
    [FechaSync] DATETIME2 NULL
);
GO

-- Table: Sync_Precios_Historicos
CREATE TABLE [Sync_Precios_Historicos] (
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
    [ImpuestoIncluido] BIT NULL,
    [TasaImpuesto] DECIMAL(8,4) NULL,
    [PrecioAnterior] DECIMAL(18,4) NULL,
    [VariacionPorcentaje] DECIMAL(8,2) NULL,
    [MotivosCambio] NVARCHAR(200) NULL,
    [UsuarioModificacion] NVARCHAR(100) NULL,
    [FechaSync] DATETIME2 NULL
);
GO

-- Table: Sync_Productos
CREATE TABLE [Sync_Productos] (
    [ProductoID] UNIQUEIDENTIFIER NOT NULL,
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
    [EsVendible] BIT NULL,
    [EsInventariable] BIT NULL,
    [EsCompuesto] BIT NULL,
    [TieneReceta] BIT NULL,
    [TieneSubRecetas] BIT NULL,
    [UnidadVenta] NVARCHAR(20) NULL,
    [UnidadInventario] NVARCHAR(20) NULL,
    [PrecioVenta] DECIMAL(18,4) NULL,
    [PrecioSinImpuestos] DECIMAL(18,4) NULL,
    [TasaImpuesto] DECIMAL(5,2) NULL,
    [CostoReceta] DECIMAL(18,4) NULL,
    [CostoPromedio] DECIMAL(18,4) NULL,
    [UltimoCosto] DECIMAL(18,4) NULL,
    [CostoEstandar] DECIMAL(18,4) NULL,
    [MargenBrutoPesos] DECIMAL(18,4) NULL,
    [MargenBrutoPorcentaje] DECIMAL(5,2) NULL,
    [MargenObjetivo] DECIMAL(5,2) NULL,
    [CantidadComponentesReceta] INT NULL,
    [Activo] BIT NULL,
    [SyncRunID] NVARCHAR(100) NULL,
    [SyncedAtMexico] DATETIME2 NULL,
    [FechaUltimoCosteo] DATETIME2 NULL,
    [SourceStatus] NVARCHAR(50) NULL,
    [HashOrigen] NVARCHAR(64) NULL,
    [FechaCreacion] DATETIME2 NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Sync_Productos_Elaborados
CREATE TABLE [Sync_Productos_Elaborados] (
    [ElaboradoDetalleID] UNIQUEIDENTIFIER NOT NULL,
    [InsumoElaboradoID] UNIQUEIDENTIFIER NOT NULL,
    [ServerID] UNIQUEIDENTIFIER NOT NULL,
    [SystemType] NVARCHAR(50) NOT NULL,
    [InsumoElaboradoCodigoFuente] NVARCHAR(100) NOT NULL,
    [InsumoComponenteID] UNIQUEIDENTIFIER NULL,
    [ComponenteCodigoFuente] NVARCHAR(100) NOT NULL,
    [ComponenteNombre] NVARCHAR(300) NOT NULL,
    [Cantidad] DECIMAL(18,6) NOT NULL,
    [UnidadMedida] NVARCHAR(50) NOT NULL,
    [CostoUnitario] DECIMAL(18,6) NULL,
    [CostoTotal] DECIMAL(18,6) NULL,
    [Activo] BIT NULL,
    [SyncRunID] NVARCHAR(100) NULL,
    [SyncedAtMexico] DATETIME2 NULL,
    [SourceStatus] NVARCHAR(50) NULL,
    [FechaCreacion] DATETIME2 NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Sync_Productos_Familias
CREATE TABLE [Sync_Productos_Familias] (
    [FamiliaID] UNIQUEIDENTIFIER NOT NULL,
    [ServerID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] INT NULL,
    [UnidadNegocioID] INT NULL,
    [SystemType] NVARCHAR(50) NOT NULL,
    [CodigoFuente] NVARCHAR(100) NOT NULL,
    [Nombre] NVARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL,
    [Activo] BIT NULL,
    [SyncRunID] NVARCHAR(100) NULL,
    [SyncedAtMexico] DATETIME2 NULL,
    [SourceStatus] NVARCHAR(50) NULL,
    [HashOrigen] NVARCHAR(64) NULL,
    [FechaCreacion] DATETIME2 NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Sync_Productos_Insumos
CREATE TABLE [Sync_Productos_Insumos] (
    [InsumoID] UNIQUEIDENTIFIER NOT NULL,
    [ServerID] UNIQUEIDENTIFIER NOT NULL,
    [EmpresaID] INT NULL,
    [SystemType] NVARCHAR(50) NOT NULL,
    [CodigoFuente] NVARCHAR(100) NOT NULL,
    [Nombre] NVARCHAR(300) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [GrupoInsumoCodigoFuente] NVARCHAR(100) NULL,
    [GrupoInsumoNombre] NVARCHAR(200) NULL,
    [UnidadMedida] NVARCHAR(50) NOT NULL,
    [Costo] DECIMAL(18,6) NULL,
    [CostoPromedio] DECIMAL(18,6) NULL,
    [UltimoCosto] DECIMAL(18,6) NULL,
    [CostoEstandar] DECIMAL(18,6) NULL,
    [CostoConImpuestos] DECIMAL(18,6) NULL,
    [EsElaborado] BIT NULL,
    [RendimientoElaborado] DECIMAL(10,4) NULL,
    [MermaPorcentaje] DECIMAL(5,2) NULL,
    [Activo] BIT NULL,
    [SyncRunID] NVARCHAR(100) NULL,
    [SyncedAtMexico] DATETIME2 NULL,
    [FechaUltimoCosto] DATETIME2 NULL,
    [SourceStatus] NVARCHAR(50) NULL,
    [HashOrigen] NVARCHAR(64) NULL,
    [FechaCreacion] DATETIME2 NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Sync_Productos_Recetas
CREATE TABLE [Sync_Productos_Recetas] (
    [RecetaDetalleID] UNIQUEIDENTIFIER NOT NULL,
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
    [CostoUnitario] DECIMAL(18,6) NULL,
    [CostoTotal] DECIMAL(18,6) NULL,
    [PorcentajeCostoTotal] DECIMAL(5,2) NULL,
    [NivelExplosion] INT NULL,
    [OrdenVisual] INT NULL,
    [EsElaborado] BIT NULL,
    [RendimientoElaborado] DECIMAL(10,4) NULL,
    [Activo] BIT NULL,
    [SyncRunID] NVARCHAR(100) NULL,
    [SyncedAtMexico] DATETIME2 NULL,
    [SourceStatus] NVARCHAR(50) NULL,
    [FechaCreacion] DATETIME2 NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Sync_Productos_SubFamilias
CREATE TABLE [Sync_Productos_SubFamilias] (
    [SubFamiliaID] UNIQUEIDENTIFIER NOT NULL,
    [FamiliaID] UNIQUEIDENTIFIER NULL,
    [ServerID] UNIQUEIDENTIFIER NOT NULL,
    [SystemType] NVARCHAR(50) NOT NULL,
    [CodigoFuente] NVARCHAR(100) NOT NULL,
    [FamiliaCodigoFuente] NVARCHAR(100) NULL,
    [Nombre] NVARCHAR(200) NOT NULL,
    [Descripcion] NVARCHAR(500) NULL,
    [Orden] INT NULL,
    [Activo] BIT NULL,
    [SyncRunID] NVARCHAR(100) NULL,
    [SyncedAtMexico] DATETIME2 NULL,
    [SourceStatus] NVARCHAR(50) NULL,
    [HashOrigen] NVARCHAR(64) NULL,
    [FechaCreacion] DATETIME2 NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Sync_Purchases
CREATE TABLE [Sync_Purchases] (
    [id] VARCHAR(64) NOT NULL,
    [provider_name] NVARCHAR(200) NOT NULL,
    [branch] NVARCHAR(100) NOT NULL,
    [items_detail] NVARCHAR(MAX) NULL,
    [total_amount] NUMERIC(12,2) NOT NULL,
    [status] VARCHAR(32) NULL,
    [created_at] DATETIME NULL,
    [sync_status] VARCHAR(16) NULL
);
GO

-- Table: Sync_Response_Cache
CREATE TABLE [Sync_Response_Cache] (
    [id] INT NOT NULL,
    [RequestHash] VARCHAR(64) NOT NULL,
    [ServiceSource] VARCHAR(64) NOT NULL,
    [RequestPayload] NVARCHAR(MAX) NULL,
    [ResponsePayload] NVARCHAR(MAX) NULL,
    [TokenCostFraction] NUMERIC(10,6) NULL,
    [CacheDurationMinutes] INT NULL,
    [CreatedAt] DATETIME NULL,
    [ExpiresAt] DATETIME NULL,
    [HitCount] INT NULL
);
GO

-- Table: Sync_Sales
CREATE TABLE [Sync_Sales] (
    [id] VARCHAR(64) NOT NULL,
    [branch] NVARCHAR(100) NOT NULL,
    [customer_id] VARCHAR(64) NULL,
    [items] NVARCHAR(MAX) NULL,
    [total] NUMERIC(18,2) NOT NULL,
    [currency] VARCHAR(3) NULL,
    [status] VARCHAR(32) NULL,
    [created_at] DATETIME NULL,
    [last_modified] DATETIME NULL,
    [sync_hash] VARCHAR(64) NULL,
    [IdTransaccion] VARCHAR(64) NULL,
    [UnidadNegocio] NVARCHAR(100) NULL,
    [MontoTotal] NUMERIC(18,2) NULL,
    [Pax] INT NULL,
    [NumeroTicket] VARCHAR(64) NULL,
    [FechaHora] DATETIME NULL
);
GO

-- Table: Sync_Ticket_Perfecto
CREATE TABLE [Sync_Ticket_Perfecto] (
    [ID] INT NOT NULL,
    [TicketID] NVARCHAR(50) NOT NULL,
    [ServerID] NVARCHAR(50) NOT NULL,
    [SucursalID] NVARCHAR(20) NOT NULL,
    [SucursalNombre] NVARCHAR(100) NULL,
    [FechaOperacion] DATE NOT NULL,
    [TotalCuentas] INT NULL,
    [TotalComensales] INT NULL,
    [VentaTotal] DECIMAL(18,2) NULL,
    [TicketPromedioReal] DECIMAL(18,2) NULL,
    [TicketPerfectoObjetivo] DECIMAL(18,2) NULL,
    [PorcentajeCumplimiento] DECIMAL(8,2) NULL,
    [CuentasBajoObjetivo] INT NULL,
    [CuentasSobreObjetivo] INT NULL,
    [CuentasEnRango] INT NULL,
    [PromedioEntradas] DECIMAL(8,2) NULL,
    [PromedioFuertes] DECIMAL(8,2) NULL,
    [PromedioBebidas] DECIMAL(8,2) NULL,
    [PromedioPostres] DECIMAL(8,2) NULL,
    [TiempoPromedioMesa] INT NULL,
    [RotacionMesas] DECIMAL(8,2) NULL,
    [FechaSync] DATETIME2 NULL,
    [MetadatosJSON] NVARCHAR(MAX) NULL
);
GO

-- Table: Sync_Token_Ledger
CREATE TABLE [Sync_Token_Ledger] (
    [LedgerID] INT NOT NULL,
    [OperadorID] VARCHAR(64) NULL,
    [ConsuDate] DATE NULL,
    [TokensInput] INT NULL,
    [TokensOutput] INT NULL,
    [EstimatedCostUSD] NUMERIC(12,4) NULL,
    [AhorroAcumuladoUSD] NUMERIC(12,4) NULL,
    [HitRatioPercent] NUMERIC(5,2) NULL
);
GO

-- Table: Sync_Ventas_Historicas
CREATE TABLE [Sync_Ventas_Historicas] (
    [SyncVentaHistoricaID] INT NOT NULL,
    [ServerID] NVARCHAR(50) NOT NULL,
    [EmpresaID] INT NOT NULL,
    [SucursalID] NVARCHAR(50) NULL,
    [UnidadNegocioID] NVARCHAR(50) NULL,
    [SystemType] NVARCHAR(20) NOT NULL,
    [FechaOperacion] DATE NOT NULL,
    [VentanaInicio] TIME NOT NULL,
    [VentanaFin] TIME NOT NULL,
    [CruzaMedianoche] BIT NOT NULL,
    [VentanaInicioHoraConfig] INT NOT NULL,
    [VentanaFinHoraConfig] INT NOT NULL,
    [VentaTotal] DECIMAL(18,2) NOT NULL,
    [VentaEfectivo] DECIMAL(18,2) NOT NULL,
    [VentaTarjeta] DECIMAL(18,2) NOT NULL,
    [VentaOtros] DECIMAL(18,2) NOT NULL,
    [NumTickets] INT NOT NULL,
    [TicketPromedio] DECIMAL(18,2) NOT NULL,
    [SyncRunID] NVARCHAR(50) NOT NULL,
    [SourceStatus] NVARCHAR(20) NOT NULL,
    [SourceType] NVARCHAR(20) NOT NULL,
    [SyncedAtMexico] DATETIME2 NOT NULL,
    [RowHash] NVARCHAR(64) NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [UpdatedAt] DATETIME2 NOT NULL
);
GO

-- Table: Sync_Ventas_PorDiaSemana
CREATE TABLE [Sync_Ventas_PorDiaSemana] (
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
    [VentanaInicioHoraConfig] INT NOT NULL,
    [VentanaFinHoraConfig] INT NOT NULL,
    [VentaPromedio] DECIMAL(18,2) NOT NULL,
    [VentaMin] DECIMAL(18,2) NOT NULL,
    [VentaMax] DECIMAL(18,2) NOT NULL,
    [NumDiasConDatos] INT NOT NULL,
    [SyncRunID] NVARCHAR(50) NOT NULL,
    [SourceStatus] NVARCHAR(20) NOT NULL,
    [SourceType] NVARCHAR(20) NOT NULL,
    [SyncedAtMexico] DATETIME2 NOT NULL,
    [RowHash] NVARCHAR(64) NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [UpdatedAt] DATETIME2 NOT NULL
);
GO

-- Table: Sync_Ventas_PorHora
CREATE TABLE [Sync_Ventas_PorHora] (
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
    [CruzaMedianoche] BIT NOT NULL,
    [VentanaInicioHoraConfig] INT NOT NULL,
    [VentanaFinHoraConfig] INT NOT NULL,
    [VentaHora] DECIMAL(18,2) NOT NULL,
    [NumTicketsHora] INT NOT NULL,
    [SyncRunID] NVARCHAR(50) NOT NULL,
    [SourceStatus] NVARCHAR(20) NOT NULL,
    [SourceType] NVARCHAR(20) NOT NULL,
    [SyncedAtMexico] DATETIME2 NOT NULL,
    [RowHash] NVARCHAR(64) NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [UpdatedAt] DATETIME2 NOT NULL
);
GO

-- Table: Sync_Vtiger_Contactos
CREATE TABLE [Sync_Vtiger_Contactos] (
    [SyncID] UNIQUEIDENTIFIER NOT NULL,
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
    [FechaCreacionLocal] DATETIME NULL,
    [FechaUltimaSync] DATETIME NULL,
    [PendientePush] BIT NULL,
    [OrigenLocal] BIT NULL,
    [PendienteDelete] BIT NULL,
    [PushError] NVARCHAR(500) NULL,
    [FechaUltimoPush] DATETIME NULL
);
GO

-- Table: Sync_Vtiger_Cuentas
CREATE TABLE [Sync_Vtiger_Cuentas] (
    [SyncID] UNIQUEIDENTIFIER NOT NULL,
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
    [FechaCreacionLocal] DATETIME NULL,
    [FechaUltimaSync] DATETIME NULL,
    [PendientePush] BIT NULL,
    [OrigenLocal] BIT NULL,
    [PendienteDelete] BIT NULL,
    [PushError] NVARCHAR(500) NULL,
    [FechaUltimoPush] DATETIME NULL
);
GO

-- Table: Sync_Vtiger_Leads
CREATE TABLE [Sync_Vtiger_Leads] (
    [SyncID] UNIQUEIDENTIFIER NOT NULL,
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
    [FechaCreacionLocal] DATETIME NULL,
    [FechaUltimaSync] DATETIME NULL,
    [PendientePush] BIT NULL,
    [OrigenLocal] BIT NULL,
    [PendienteDelete] BIT NULL,
    [PushError] NVARCHAR(500) NULL,
    [FechaUltimoPush] DATETIME NULL
);
GO

-- Table: Sync_Vtiger_Log
CREATE TABLE [Sync_Vtiger_Log] (
    [LogID] UNIQUEIDENTIFIER NOT NULL,
    [RunID] VARCHAR(50) NOT NULL,
    [Direccion] VARCHAR(20) NULL,
    [FechaInicio] DATETIME NOT NULL,
    [FechaFin] DATETIME NULL,
    [TotalObtenidos] INT NULL,
    [TotalInsertados] INT NULL,
    [TotalActualizados] INT NULL,
    [Errores] INT NULL,
    [ResultadoJSON] NVARCHAR(MAX) NULL
);
GO

-- Table: Sync_Vtiger_Oportunidades
CREATE TABLE [Sync_Vtiger_Oportunidades] (
    [SyncID] UNIQUEIDENTIFIER NOT NULL,
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
    [FechaCreacionLocal] DATETIME NULL,
    [FechaUltimaSync] DATETIME NULL,
    [PendientePush] BIT NULL,
    [OrigenLocal] BIT NULL,
    [PendienteDelete] BIT NULL,
    [PushError] NVARCHAR(500) NULL,
    [FechaUltimoPush] DATETIME NULL
);
GO

-- Table: Sys_Roles
CREATE TABLE [Sys_Roles] (
    [IDRol] INT NOT NULL,
    [NombreRol] VARCHAR(50) NOT NULL,
    [NivelAcceso] INT NOT NULL,
    [EsInterno] BIT NULL
);
GO

-- Table: Sys_Scheduler_Jobs
CREATE TABLE [Sys_Scheduler_Jobs] (
    [JobID] VARCHAR(50) NOT NULL,
    [JobName] VARCHAR(100) NOT NULL,
    [CronExpression] VARCHAR(50) NOT NULL,
    [JobType] VARCHAR(20) NOT NULL,
    [Status] VARCHAR(20) NULL,
    [LastRunDate] DATETIME NULL
);
GO

-- Table: Sys_Usuarios
CREATE TABLE [Sys_Usuarios] (
    [IDUsuario] INT NOT NULL,
    [Username] VARCHAR(100) NOT NULL,
    [PasswordHash] VARCHAR(256) NOT NULL,
    [NombreCompleto] VARCHAR(150) NULL,
    [Email] VARCHAR(150) NULL,
    [IDRol] INT NULL,
    [Estatus] VARCHAR(20) NULL,
    [RFC] VARCHAR(20) NULL,
    [IDContactoVtiger] VARCHAR(50) NULL,
    [FechaCreacion] DATETIME NULL
);
GO

-- Table: Tablajeria_ConfigContable
CREATE TABLE [Tablajeria_ConfigContable] (
    [ConfigID] INT NOT NULL,
    [EmpresaID] VARCHAR(50) NOT NULL,
    [CuentaAlmacenInsumos] VARCHAR(50) NULL,
    [CuentaAlmacenProductos] VARCHAR(50) NULL,
    [CuentaProduccionEnProceso] VARCHAR(50) NULL,
    [CuentaCostoVentas] VARCHAR(50) NULL,
    [CuentaMermaOperativa] VARCHAR(50) NULL,
    [CuentaMermaExtraordinaria] VARCHAR(50) NULL,
    [CuentaVariacionCosto] VARCHAR(50) NULL,
    [GenerarPolizaAutomatica] BIT NULL,
    [AfectarInventarioAutomatico] BIT NULL,
    [ToleranciaVariacionPorcentaje] DECIMAL(5,2) NULL,
    [Activo] BIT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Tablajeria_CosteoDetalle
CREATE TABLE [Tablajeria_CosteoDetalle] (
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
    [EsInventariable] BIT NULL
);
GO

-- Table: Tablajeria_CosteoProduccion
CREATE TABLE [Tablajeria_CosteoProduccion] (
    [CosteoID] VARCHAR(50) NOT NULL,
    [OrdenID] VARCHAR(50) NOT NULL,
    [FechaCosteo] DATETIME2 NULL,
    [InsumoBaseCodigo] VARCHAR(50) NULL,
    [InsumoBaseNombre] VARCHAR(200) NULL,
    [CantidadInsumoConsumida] DECIMAL(18,4) NULL,
    [CostoUnitarioInsumo] DECIMAL(18,4) NULL,
    [CostoTotalInsumo] DECIMAL(18,2) NULL,
    [CostoManoObra] DECIMAL(18,2) NULL,
    [CostoIndirectos] DECIMAL(18,2) NULL,
    [CostoEnergia] DECIMAL(18,2) NULL,
    [OtrosCostos] DECIMAL(18,2) NULL,
    [CostoTotalProduccion] DECIMAL(18,2) NULL,
    [CostoUnitarioPromedio] DECIMAL(18,4) NULL,
    [ReglaCosteoAplicada] VARCHAR(20) NULL,
    [UsuarioID] VARCHAR(50) NULL,
    [Observaciones] NVARCHAR(MAX) NULL,
    [EsEstimado] BIT NULL
);
GO

-- Table: Tablajeria_MovimientosInventario
CREATE TABLE [Tablajeria_MovimientosInventario] (
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
    [FechaMovimiento] DATETIME2 NULL,
    [UsuarioID] VARCHAR(50) NULL,
    [Referencia] VARCHAR(100) NULL,
    [Sincronizado] BIT NULL,
    [FechaSincronizacion] DATETIME2 NULL,
    [ErrorSincronizacion] VARCHAR(500) NULL
);
GO

-- Table: Tablajeria_PolizasContables
CREATE TABLE [Tablajeria_PolizasContables] (
    [PolizaID] VARCHAR(50) NOT NULL,
    [OrdenID] VARCHAR(50) NOT NULL,
    [TipoPoliza] VARCHAR(50) NULL,
    [NumeroPoliza] VARCHAR(50) NULL,
    [FechaPoliza] DATE NULL,
    [Concepto] VARCHAR(500) NULL,
    [MontoTotal] DECIMAL(18,2) NULL,
    [EstatusPoliza] VARCHAR(20) NULL,
    [FechaCreacion] DATETIME2 NULL,
    [FechaContabilizacion] DATETIME2 NULL,
    [UsuarioID] VARCHAR(50) NULL,
    [ErrorContabilizacion] VARCHAR(500) NULL
);
GO

-- Table: Tablajeria_PolizasDetalle
CREATE TABLE [Tablajeria_PolizasDetalle] (
    [AsientoID] VARCHAR(50) NOT NULL,
    [PolizaID] VARCHAR(50) NOT NULL,
    [NumeroLinea] INT NULL,
    [CuentaContable] VARCHAR(50) NULL,
    [NombreCuenta] VARCHAR(200) NULL,
    [Concepto] VARCHAR(300) NULL,
    [Debe] DECIMAL(18,2) NULL,
    [Haber] DECIMAL(18,2) NULL,
    [Referencia] VARCHAR(100) NULL
);
GO

-- Table: Tareas_Inventario
CREATE TABLE [Tareas_Inventario] (
    [ID] INT NOT NULL,
    [TareaID] VARCHAR(50) NOT NULL,
    [WorkflowID] VARCHAR(50) NOT NULL,
    [TipoTarea] VARCHAR(50) NULL,
    [Titulo] VARCHAR(500) NULL,
    [Descripcion] NVARCHAR(MAX) NULL,
    [EstadoTarea] VARCHAR(50) NULL,
    [Prioridad] VARCHAR(20) NULL,
    [UsuarioAsignadoID] VARCHAR(50) NULL,
    [UsuarioAsignadoNombre] VARCHAR(200) NULL,
    [FechaCreacion] DATETIME2 NULL,
    [FechaAsignacion] DATETIME2 NULL,
    [FechaLimite] DATETIME2 NULL,
    [FechaActualizacion] DATETIME2 NULL,
    [FechaPrimeraAccion] DATETIME2 NULL,
    [FechaCompletada] DATETIME2 NULL,
    [Ciclo] INT NULL,
    [EsReasignacion] BIT NULL,
    [Vencida] BIT NULL,
    [EstadoSLA] VARCHAR(50) NULL,
    [FechaActualizacionSLA] DATETIME2 NULL,
    [NotificacionWarningEnviada] BIT NULL,
    [NotificacionVencidoEnviada] BIT NULL,
    [NotificacionEscaladoEnviada] BIT NULL,
    [NotasJSON] NVARCHAR(MAX) NULL
);
GO

-- Table: Unidades_Negocio
CREATE TABLE [Unidades_Negocio] (
    [id] UNIQUEIDENTIFIER NOT NULL,
    [nombre] NVARCHAR(100) NOT NULL,
    [codigo] NVARCHAR(50) NOT NULL,
    [server_id] NVARCHAR(100) NOT NULL,
    [sucursal_origen_id] NVARCHAR(50) NULL,
    [system_type] NVARCHAR(50) NOT NULL,
    [activo] BIT NULL,
    [orden] INT NULL,
    [created_at] DATETIME NULL,
    [updated_at] DATETIME NULL
);
GO

-- Table: Usuario_Acciones
CREATE TABLE [Usuario_Acciones] (
    [AccionID] SMALLINT NOT NULL,
    [CodigoAccion] VARCHAR(30) NOT NULL,
    [NombreAccion] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [EsAutorizable] BIT NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Usuario_AlmacenesAsignacion
CREATE TABLE [Usuario_AlmacenesAsignacion] (
    [AsignacionID] INT NOT NULL,
    [UsuarioID] INT NOT NULL,
    [ServidorID] UNIQUEIDENTIFIER NOT NULL,
    [AlmacenCodigo] VARCHAR(20) NOT NULL,
    [LegacyMongoValue] VARCHAR(100) NULL,
    [Activo] BIT NOT NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL,
    [CreadoPor] INT NULL,
    [ModificadoPor] INT NULL,
    [Observaciones] NVARCHAR(500) NULL
);
GO

-- Table: Usuario_Autorizaciones
CREATE TABLE [Usuario_Autorizaciones] (
    [AutorizacionID] BIGINT NOT NULL,
    [FolioAutorizacion] VARCHAR(30) NOT NULL,
    [TipoAutorizacionID] SMALLINT NOT NULL,
    [ModuloID] INT NULL,
    [AccionID] SMALLINT NULL,
    [EntidadNombre] VARCHAR(100) NOT NULL,
    [EntidadID] VARCHAR(100) NULL,
    [FolioReferencia] VARCHAR(50) NULL,
    [UsuarioSolicitanteID] INT NOT NULL,
    [FechaSolicitud] DATETIME2 NOT NULL,
    [Monto] DECIMAL(18,2) NULL,
    [MonedaID] SMALLINT NULL,
    [Justificacion] VARCHAR(2000) NOT NULL,
    [EstatusAutorizacion] VARCHAR(20) NOT NULL,
    [NivelActual] SMALLINT NOT NULL,
    [NivelFinalRequerido] SMALLINT NULL,
    [FechaResolucionFinal] DATETIME2 NULL,
    [UsuarioResolucionFinalID] INT NULL,
    [ComentariosResolucionFinal] VARCHAR(2000) NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL
);
GO

-- Table: Usuario_AutorizacionesDetalle
CREATE TABLE [Usuario_AutorizacionesDetalle] (
    [AutorizacionDetalleID] BIGINT NOT NULL,
    [AutorizacionID] BIGINT NOT NULL,
    [NivelAutorizacion] SMALLINT NOT NULL,
    [UsuarioAutorizadorID] INT NOT NULL,
    [RolID] INT NULL,
    [FechaAsignacion] DATETIME2 NOT NULL,
    [FechaResolucion] DATETIME2 NULL,
    [Resultado] VARCHAR(20) NOT NULL,
    [Comentarios] VARCHAR(2000) NULL,
    [IPResolucion] VARCHAR(64) NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Usuario_Catalogo
CREATE TABLE [Usuario_Catalogo] (
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
    [EsUsuarioPortal] BIT NOT NULL,
    [RequiereMFA] BIT NOT NULL,
    [PasswordTemporal] BIT NOT NULL,
    [DebeCambiarPassword] BIT NOT NULL,
    [IntentosFallidos] INT NOT NULL,
    [Bloqueado] BIT NOT NULL,
    [FechaBloqueo] DATETIME2 NULL,
    [MotivoBloqueo] VARCHAR(250) NULL,
    [UltimoAcceso] DATETIME2 NULL,
    [UltimoCambioPassword] DATETIME2 NULL,
    [FechaExpiracionPassword] DATETIME2 NULL,
    [ZonaHoraria] VARCHAR(60) NULL,
    [Idioma] VARCHAR(20) NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedBy] VARCHAR(100) NULL,
    [MongoLegacyID] VARCHAR(50) NULL,
    [PublicUUID] UNIQUEIDENTIFIER NULL
);
GO

-- Table: Usuario_EmpresasAsignacion
CREATE TABLE [Usuario_EmpresasAsignacion] (
    [UsuarioEmpresaAsignacionID] BIGINT NOT NULL,
    [UsuarioID] INT NOT NULL,
    [EmpresaID] INT NOT NULL,
    [EsPrincipal] BIT NOT NULL,
    [FechaInicio] DATETIME2 NOT NULL,
    [FechaFin] DATETIME2 NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [UpdatedAt] DATETIME2 NULL,
    [UpdatedBy] VARCHAR(100) NULL
);
GO

-- Table: Usuario_LogAccesos
CREATE TABLE [Usuario_LogAccesos] (
    [LogAccesoID] BIGINT NOT NULL,
    [UsuarioID] INT NULL,
    [SesionID] BIGINT NULL,
    [TipoEvento] VARCHAR(30) NOT NULL,
    [FechaEvento] DATETIME2 NOT NULL,
    [IPOrigen] VARCHAR(64) NULL,
    [UserAgent] VARCHAR(500) NULL,
    [Resultado] VARCHAR(20) NOT NULL,
    [Detalle] VARCHAR(1000) NULL
);
GO

-- Table: Usuario_LogActividades
CREATE TABLE [Usuario_LogActividades] (
    [LogActividadID] BIGINT NOT NULL,
    [UsuarioID] INT NOT NULL,
    [SesionID] BIGINT NULL,
    [ModuloID] INT NULL,
    [AccionID] SMALLINT NULL,
    [EntidadNombre] VARCHAR(100) NULL,
    [EntidadID] VARCHAR(100) NULL,
    [FolioReferencia] VARCHAR(50) NULL,
    [FechaActividad] DATETIME2 NOT NULL,
    [ResumenActividad] VARCHAR(250) NOT NULL,
    [DetalleActividad] VARCHAR(2000) NULL,
    [ValoresAntes] NVARCHAR(MAX) NULL,
    [ValoresDespues] NVARCHAR(MAX) NULL,
    [IPOrigen] VARCHAR(64) NULL,
    [Resultado] VARCHAR(20) NOT NULL,
    [Criticidad] VARCHAR(20) NOT NULL
);
GO

-- Table: Usuario_LogRBACVerificacion
CREATE TABLE [Usuario_LogRBACVerificacion] (
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
    [FechaVerificacion] DATETIME2 NOT NULL
);
GO

-- Table: Usuario_LogRecuperacion
CREATE TABLE [Usuario_LogRecuperacion] (
    [LogRecuperacionID] BIGINT NOT NULL,
    [Evento] VARCHAR(50) NOT NULL,
    [Email] VARCHAR(255) NOT NULL,
    [IPOrigen] VARCHAR(45) NULL,
    [UserAgent] VARCHAR(500) NULL,
    [Resultado] BIT NOT NULL,
    [Detalle] NVARCHAR(MAX) NULL,
    [FechaEvento] DATETIME2 NOT NULL
);
GO

-- Table: Usuario_MatrizAutorizacion
CREATE TABLE [Usuario_MatrizAutorizacion] (
    [MatrizAutorizacionID] BIGINT NOT NULL,
    [TipoAutorizacionID] SMALLINT NOT NULL,
    [NivelAutorizacion] SMALLINT NOT NULL,
    [RolID] INT NOT NULL,
    [UsuarioID] INT NULL,
    [MontoMinimo] DECIMAL(18,2) NULL,
    [MontoMaximo] DECIMAL(18,2) NULL,
    [Prioridad] INT NOT NULL,
    [RequiereTodosLosNiveles] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Usuario_MigracionMongoTrace
CREATE TABLE [Usuario_MigracionMongoTrace] (
    [TraceID] INT NOT NULL,
    [MongoID] VARCHAR(24) NOT NULL,
    [Email] VARCHAR(150) NOT NULL,
    [UsuarioID_SQL] INT NULL,
    [RolMongoDB] VARCHAR(50) NOT NULL,
    [ActivoMongoDB] BIT NOT NULL,
    [Clasificacion] VARCHAR(20) NOT NULL,
    [FechaMigracion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL
);
GO

-- Table: Usuario_Modulos
CREATE TABLE [Usuario_Modulos] (
    [ModuloID] INT NOT NULL,
    [ModuloPadreID] INT NULL,
    [CodigoModulo] VARCHAR(30) NOT NULL,
    [NombreModulo] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [TipoModulo] VARCHAR(20) NOT NULL,
    [Ruta] VARCHAR(200) NULL,
    [Icono] VARCHAR(100) NULL,
    [OrdenMenu] INT NOT NULL,
    [EsVisibleMenu] BIT NOT NULL,
    [RequiereAutorizacion] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Usuario_PermisosRolModulo
CREATE TABLE [Usuario_PermisosRolModulo] (
    [PermisoRolModuloID] BIGINT NOT NULL,
    [RolID] INT NOT NULL,
    [ModuloID] INT NOT NULL,
    [AccionID] SMALLINT NOT NULL,
    [Permitido] BIT NOT NULL,
    [RestriccionPropietario] BIT NOT NULL,
    [RestriccionSucursal] BIT NOT NULL,
    [RequiereAutorizacion] BIT NOT NULL,
    [NivelAutorizacionRequerido] SMALLINT NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedBy] VARCHAR(100) NULL
);
GO

-- Table: Usuario_PortalConfiguracion
CREATE TABLE [Usuario_PortalConfiguracion] (
    [UsuarioPortalConfiguracionID] BIGINT NOT NULL,
    [UsuarioID] INT NOT NULL,
    [Tema] VARCHAR(30) NULL,
    [ColorAcento] VARCHAR(30) NULL,
    [MenuCompacto] BIT NOT NULL,
    [DashboardDefault] VARCHAR(100) NULL,
    [RecibeEmailNotificaciones] BIT NOT NULL,
    [RecibeWhatsAppNotificaciones] BIT NOT NULL,
    [RecibePushNotificaciones] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Usuario_RateLimitRecuperacion
CREATE TABLE [Usuario_RateLimitRecuperacion] (
    [RateLimitID] BIGINT NOT NULL,
    [TipoLlave] VARCHAR(20) NOT NULL,
    [ValorLlave] VARCHAR(255) NOT NULL,
    [Contador] INT NOT NULL,
    [VentanaInicio] DATETIME2 NOT NULL,
    [VentanaExpiracion] DATETIME2 NOT NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NOT NULL
);
GO

-- Table: Usuario_Roles
CREATE TABLE [Usuario_Roles] (
    [RolID] INT NOT NULL,
    [CodigoRol] VARCHAR(30) NOT NULL,
    [NombreRol] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [EsRolSistema] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL,
    [NivelJerarquia] INT NOT NULL
);
GO

-- Table: Usuario_RolesAsignacion
CREATE TABLE [Usuario_RolesAsignacion] (
    [UsuarioRolAsignacionID] BIGINT NOT NULL,
    [UsuarioID] INT NOT NULL,
    [RolID] INT NOT NULL,
    [EsPrincipal] BIT NOT NULL,
    [FechaInicio] DATETIME2 NOT NULL,
    [FechaFin] DATETIME2 NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL
);
GO

-- Table: Usuario_ServidoresAsignacion
CREATE TABLE [Usuario_ServidoresAsignacion] (
    [AsignacionID] INT NOT NULL,
    [UsuarioID] INT NOT NULL,
    [ServidorID] UNIQUEIDENTIFIER NOT NULL,
    [LegacyMongoValue] VARCHAR(100) NULL,
    [Activo] BIT NOT NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL,
    [CreadoPor] INT NULL,
    [ModificadoPor] INT NULL,
    [Observaciones] NVARCHAR(500) NULL
);
GO

-- Table: Usuario_Sesiones
CREATE TABLE [Usuario_Sesiones] (
    [SesionID] BIGINT NOT NULL,
    [UsuarioID] INT NOT NULL,
    [TokenSesion] VARCHAR(255) NULL,
    [FechaInicio] DATETIME2 NOT NULL,
    [FechaUltimaActividad] DATETIME2 NULL,
    [FechaCierre] DATETIME2 NULL,
    [IPOrigen] VARCHAR(64) NULL,
    [UserAgent] VARCHAR(500) NULL,
    [Dispositivo] VARCHAR(150) NULL,
    [Navegador] VARCHAR(100) NULL,
    [SistemaOperativo] VARCHAR(100) NULL,
    [ExitoLogin] BIT NOT NULL,
    [MotivoFallo] VARCHAR(250) NULL,
    [MFAValidado] BIT NOT NULL,
    [SesionActiva] BIT NOT NULL,
    [CerradaPorSistema] BIT NOT NULL
);
GO

-- Table: Usuario_SucursalesAsignacion
CREATE TABLE [Usuario_SucursalesAsignacion] (
    [AsignacionID] INT NOT NULL,
    [UsuarioID] INT NOT NULL,
    [ServidorID] UNIQUEIDENTIFIER NOT NULL,
    [SucursalCodigo] VARCHAR(20) NOT NULL,
    [LegacyMongoValue] VARCHAR(100) NULL,
    [Activo] BIT NOT NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL,
    [CreadoPor] INT NULL,
    [ModificadoPor] INT NULL,
    [Observaciones] NVARCHAR(500) NULL
);
GO

-- Table: Usuario_TiposAutorizacion
CREATE TABLE [Usuario_TiposAutorizacion] (
    [TipoAutorizacionID] SMALLINT NOT NULL,
    [CodigoTipoAutorizacion] VARCHAR(30) NOT NULL,
    [NombreTipoAutorizacion] VARCHAR(100) NOT NULL,
    [Descripcion] VARCHAR(250) NULL,
    [ModuloID] INT NULL,
    [AccionID] SMALLINT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Usuario_TokensRecuperacion
CREATE TABLE [Usuario_TokensRecuperacion] (
    [TokenRecuperacionID] BIGINT NOT NULL,
    [TokenHash] VARCHAR(64) NOT NULL,
    [UsuarioID] INT NOT NULL,
    [Email] VARCHAR(150) NOT NULL,
    [FechaCreacion] DATETIME2 NOT NULL,
    [FechaExpiracion] DATETIME2 NOT NULL,
    [FechaUso] DATETIME2 NULL,
    [FechaModificacion] DATETIME2 NULL,
    [Usado] BIT NOT NULL,
    [Invalidado] BIT NOT NULL,
    [MotivoInvalidacion] VARCHAR(100) NULL,
    [IPSolicitud] VARCHAR(64) NULL,
    [IPUso] VARCHAR(64) NULL,
    [UserAgentSolicitud] VARCHAR(500) NULL,
    [UserAgentUso] VARCHAR(500) NULL
);
GO

-- Table: Venta_Cat_EstatusRemision
CREATE TABLE [Venta_Cat_EstatusRemision] (
    [EstatusID] INT NOT NULL,
    [Nombre] NVARCHAR(50) NOT NULL,
    [Descripcion] NVARCHAR(200) NULL,
    [Color] NVARCHAR(20) NULL,
    [Orden] INT NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Venta_CondicionesPago
CREATE TABLE [Venta_CondicionesPago] (
    [CondicionPagoID] SMALLINT NOT NULL,
    [CodigoCondicionPago] VARCHAR(20) NOT NULL,
    [Descripcion] VARCHAR(100) NOT NULL,
    [DiasCredito] SMALLINT NOT NULL,
    [RequiereCredito] BIT NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Venta_Cotizaciones
CREATE TABLE [Venta_Cotizaciones] (
    [CotizacionID] BIGINT NOT NULL,
    [Serie] VARCHAR(10) NULL,
    [FolioCotizacion] VARCHAR(30) NOT NULL,
    [FechaCotizacion] DATETIME2 NOT NULL,
    [FechaVigencia] DATE NULL,
    [ClienteID] INT NOT NULL,
    [ClienteDireccionID] INT NULL,
    [ListaPrecioID] INT NULL,
    [CondicionPagoID] SMALLINT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [TipoCambio] DECIMAL(18,6) NOT NULL,
    [EstatusCotizacionID] TINYINT NOT NULL,
    [Subtotal] DECIMAL(18,2) NOT NULL,
    [DescuentoTotal] DECIMAL(18,2) NOT NULL,
    [ImpuestoTotal] DECIMAL(18,2) NOT NULL,
    [Total] DECIMAL(18,2) NOT NULL,
    [AtencionA] VARCHAR(150) NULL,
    [EmailCliente] VARCHAR(150) NULL,
    [TelefonoCliente] VARCHAR(25) NULL,
    [Observaciones] VARCHAR(1000) NULL,
    [TerminosCondiciones] VARCHAR(2000) NULL,
    [ReferenciaExterna] VARCHAR(100) NULL,
    [PedidoID] BIGINT NULL,
    [VentaID] BIGINT NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
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

-- Table: Venta_CotizacionesDetalle
CREATE TABLE [Venta_CotizacionesDetalle] (
    [DetalleCotizacionID] BIGINT NOT NULL,
    [CotizacionID] BIGINT NOT NULL,
    [Renglon] INT NOT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [Cantidad] DECIMAL(18,4) NOT NULL,
    [PrecioUnitario] DECIMAL(18,4) NOT NULL,
    [DescuentoPorcentaje] DECIMAL(9,4) NOT NULL,
    [DescuentoImporte] DECIMAL(18,2) NOT NULL,
    [TasaImpuesto] DECIMAL(9,4) NOT NULL,
    [ImpuestoImporte] DECIMAL(18,2) NOT NULL,
    [SubtotalLinea] DECIMAL(18,2) NULL,
    [TotalLinea] DECIMAL(18,2) NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL
);
GO

-- Table: Venta_CotizacionesEstatus
CREATE TABLE [Venta_CotizacionesEstatus] (
    [EstatusCotizacionID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Venta_Detalle
CREATE TABLE [Venta_Detalle] (
    [DetalleVentaID] BIGINT NOT NULL,
    [VentaID] BIGINT NOT NULL,
    [Renglon] INT NOT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [Cantidad] DECIMAL(18,4) NOT NULL,
    [PrecioUnitario] DECIMAL(18,4) NOT NULL,
    [DescuentoPorcentaje] DECIMAL(9,4) NOT NULL,
    [DescuentoImporte] DECIMAL(18,2) NOT NULL,
    [TasaImpuesto] DECIMAL(9,4) NOT NULL,
    [ImpuestoImporte] DECIMAL(18,2) NOT NULL,
    [SubtotalLinea] DECIMAL(18,2) NULL,
    [TotalLinea] DECIMAL(18,2) NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL
);
GO

-- Table: Venta_Encabezado
CREATE TABLE [Venta_Encabezado] (
    [VentaID] BIGINT NOT NULL,
    [Serie] VARCHAR(10) NULL,
    [Folio] VARCHAR(30) NOT NULL,
    [FechaVenta] DATETIME2 NOT NULL,
    [FechaVencimiento] DATE NULL,
    [ClienteID] INT NOT NULL,
    [ClienteDireccionID] INT NULL,
    [ListaPrecioID] INT NULL,
    [CondicionPagoID] SMALLINT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [TipoCambio] DECIMAL(18,6) NOT NULL,
    [EstatusVentaID] TINYINT NOT NULL,
    [Subtotal] DECIMAL(18,2) NOT NULL,
    [DescuentoTotal] DECIMAL(18,2) NOT NULL,
    [ImpuestoTotal] DECIMAL(18,2) NOT NULL,
    [Total] DECIMAL(18,2) NOT NULL,
    [TotalPagado] DECIMAL(18,2) NOT NULL,
    [SaldoPendiente] DECIMAL(18,2) NOT NULL,
    [Observaciones] VARCHAR(1000) NULL,
    [ReferenciaExterna] VARCHAR(100) NULL,
    [NumeroFactura] VARCHAR(50) NULL,
    [UUIDFactura] VARCHAR(50) NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL,
    [ModifiedAt] DATETIME2 NULL,
    [ModifiedBy] VARCHAR(100) NULL
);
GO

-- Table: Venta_Estatus
CREATE TABLE [Venta_Estatus] (
    [EstatusVentaID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Venta_FormaPago
CREATE TABLE [Venta_FormaPago] (
    [FormaPagoID] SMALLINT NOT NULL,
    [ClaveFormaPago] VARCHAR(10) NULL,
    [Descripcion] VARCHAR(50) NOT NULL,
    [RequiereReferencia] BIT NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Venta_ListasPrecios
CREATE TABLE [Venta_ListasPrecios] (
    [ListaPrecioID] INT NOT NULL,
    [CodigoListaPrecio] VARCHAR(20) NOT NULL,
    [NombreListaPrecio] VARCHAR(100) NOT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [EsDefault] BIT NOT NULL,
    [FechaInicio] DATE NULL,
    [FechaFin] DATE NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL,
    [FechaModificacion] DATETIME2 NULL
);
GO

-- Table: Venta_ListasPreciosDetalle
CREATE TABLE [Venta_ListasPreciosDetalle] (
    [ListaPrecioDetalleID] BIGINT NOT NULL,
    [ListaPrecioID] INT NOT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [Precio] DECIMAL(18,2) NOT NULL,
    [DescuentoPorcentaje] DECIMAL(9,4) NOT NULL,
    [FechaInicio] DATE NULL,
    [FechaFin] DATE NULL,
    [Activo] BIT NOT NULL,
    [FechaAlta] DATETIME2 NOT NULL
);
GO

-- Table: Venta_Pagos
CREATE TABLE [Venta_Pagos] (
    [PagoVentaID] BIGINT NOT NULL,
    [VentaID] BIGINT NOT NULL,
    [FechaPago] DATETIME2 NOT NULL,
    [FormaPagoID] SMALLINT NOT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [TipoCambio] DECIMAL(18,6) NOT NULL,
    [ImportePago] DECIMAL(18,2) NOT NULL,
    [ReferenciaPago] VARCHAR(100) NULL,
    [NumeroAutorizacion] VARCHAR(100) NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Confirmado] BIT NOT NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL
);
GO

-- Table: Venta_Pedidos
CREATE TABLE [Venta_Pedidos] (
    [PedidoID] BIGINT NOT NULL,
    [Serie] VARCHAR(10) NULL,
    [FolioPedido] VARCHAR(30) NOT NULL,
    [FechaPedido] DATETIME2 NOT NULL,
    [FechaCompromiso] DATE NULL,
    [ClienteID] INT NOT NULL,
    [ClienteDireccionID] INT NULL,
    [ListaPrecioID] INT NULL,
    [CondicionPagoID] SMALLINT NULL,
    [MonedaID] SMALLINT NOT NULL,
    [TipoCambio] DECIMAL(18,6) NOT NULL,
    [EstatusPedidoID] TINYINT NOT NULL,
    [Subtotal] DECIMAL(18,2) NOT NULL,
    [DescuentoTotal] DECIMAL(18,2) NOT NULL,
    [ImpuestoTotal] DECIMAL(18,2) NOT NULL,
    [Total] DECIMAL(18,2) NOT NULL,
    [CotizacionID] BIGINT NULL,
    [VentaID] BIGINT NULL,
    [AtencionA] VARCHAR(150) NULL,
    [Observaciones] VARCHAR(1000) NULL,
    [InstruccionesEntrega] VARCHAR(1000) NULL,
    [ReferenciaExterna] VARCHAR(100) NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
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

-- Table: Venta_PedidosDetalle
CREATE TABLE [Venta_PedidosDetalle] (
    [DetallePedidoID] BIGINT NOT NULL,
    [PedidoID] BIGINT NOT NULL,
    [Renglon] INT NOT NULL,
    [ProductoID] INT NOT NULL,
    [PresentacionProductoID] BIGINT NULL,
    [Cantidad] DECIMAL(18,4) NOT NULL,
    [CantidadSurtida] DECIMAL(18,4) NOT NULL,
    [PrecioUnitario] DECIMAL(18,4) NOT NULL,
    [DescuentoPorcentaje] DECIMAL(9,4) NOT NULL,
    [DescuentoImporte] DECIMAL(18,2) NOT NULL,
    [TasaImpuesto] DECIMAL(9,4) NOT NULL,
    [ImpuestoImporte] DECIMAL(18,2) NOT NULL,
    [SubtotalLinea] DECIMAL(18,2) NULL,
    [TotalLinea] DECIMAL(18,2) NULL,
    [Observaciones] VARCHAR(500) NULL,
    [Activo] BIT NOT NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [CreatedBy] VARCHAR(100) NULL
);
GO

-- Table: Venta_PedidosEstatus
CREATE TABLE [Venta_PedidosEstatus] (
    [EstatusPedidoID] TINYINT NOT NULL,
    [Descripcion] VARCHAR(30) NOT NULL,
    [Activo] BIT NOT NULL
);
GO

-- Table: Venta_Remisiones
CREATE TABLE [Venta_Remisiones] (
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
    [MonedaID] INT NULL,
    [TipoCambio] DECIMAL(18,6) NULL,
    [Subtotal] DECIMAL(18,2) NOT NULL,
    [DescuentoTotal] DECIMAL(18,2) NOT NULL,
    [ImpuestosTotal] DECIMAL(18,2) NOT NULL,
    [Total] DECIMAL(18,2) NOT NULL,
    [EstatusRemisionID] INT NOT NULL,
    [FacturaID] BIGINT NULL,
    [FechaFacturacion] DATETIME2 NULL,
    [DocumentoID] UNIQUEIDENTIFIER NULL,
    [Observaciones] NVARCHAR(MAX) NULL,
    [ObservacionesInternas] NVARCHAR(MAX) NULL,
    [Activo] BIT NOT NULL,
    [CreatedBy] UNIQUEIDENTIFIER NULL,
    [UpdatedBy] UNIQUEIDENTIFIER NULL,
    [CreatedAt] DATETIME2 NOT NULL,
    [UpdatedAt] DATETIME2 NULL
);
GO

-- Table: Venta_RemisionesDetalle
CREATE TABLE [Venta_RemisionesDetalle] (
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
    [PrecioUnitario] DECIMAL(18,4) NOT NULL,
    [DescuentoPorcentaje] DECIMAL(5,2) NULL,
    [DescuentoImporte] DECIMAL(18,2) NULL,
    [ImpuestoPorcentaje] DECIMAL(5,2) NULL,
    [ImpuestoImporte] DECIMAL(18,2) NULL,
    [Subtotal] DECIMAL(18,2) NOT NULL,
    [Total] DECIMAL(18,2) NOT NULL,
    [NumeroLote] NVARCHAR(50) NULL,
    [NumeroSerie] NVARCHAR(50) NULL,
    [OrdenLinea] INT NOT NULL
);
GO

-- Table: Venta_RemisionesHistorial
CREATE TABLE [Venta_RemisionesHistorial] (
    [HistorialID] BIGINT NOT NULL,
    [RemisionID] BIGINT NOT NULL,
    [EstatusAnteriorID] INT NULL,
    [EstatusNuevoID] INT NOT NULL,
    [Comentario] NVARCHAR(500) NULL,
    [CambiadoPorUserID] UNIQUEIDENTIFIER NOT NULL,
    [FechaCambio] DATETIME2 NOT NULL
);
GO

-- Table: Workflow_DecisionesAuditoria
CREATE TABLE [Workflow_DecisionesAuditoria] (
    [ID] INT NOT NULL,
    [DecisionID] VARCHAR(50) NOT NULL,
    [WorkflowID] VARCHAR(50) NOT NULL,
    [TipoDecision] VARCHAR(50) NOT NULL,
    [Decision] VARCHAR(50) NOT NULL,
    [Comentario] NVARCHAR(MAX) NULL,
    [UsuarioID] VARCHAR(50) NOT NULL,
    [UsuarioNombre] VARCHAR(200) NULL,
    [CicloAuditoria] INT NULL,
    [AccionSiguiente] VARCHAR(100) NULL,
    [FechaDecision] DATETIME2 NULL,
    [MetadatosJSON] NVARCHAR(MAX) NULL
);
GO

-- Table: Workflow_DetalleDiferencias
CREATE TABLE [Workflow_DetalleDiferencias] (
    [ID] INT NOT NULL,
    [DetalleID] VARCHAR(50) NOT NULL,
    [WorkflowID] VARCHAR(50) NOT NULL,
    [CodigoProducto] VARCHAR(50) NULL,
    [NombreProducto] VARCHAR(200) NULL,
    [Categoria] VARCHAR(100) NULL,
    [Familia] VARCHAR(100) NULL,
    [SubFamilia] VARCHAR(100) NULL,
    [Unidad] VARCHAR(50) NULL,
    [CostoUnitario] DECIMAL(18,4) NULL,
    [InvInicialCantidad] DECIMAL(18,4) NULL,
    [InvFinalCantidad] DECIMAL(18,4) NULL,
    [InvTeoricoCantidad] DECIMAL(18,4) NULL,
    [DiferenciaCantidad] DECIMAL(18,4) NULL,
    [DiferenciaCosto] DECIMAL(18,2) NULL,
    [DiferenciaPorcentaje] DECIMAL(10,2) NULL,
    [Movimientos] DECIMAL(18,4) NULL,
    [Ventas] DECIMAL(18,4) NULL,
    [EstadoJustificacion] VARCHAR(50) NULL,
    [RequiereJustificacionCompleta] BIT NULL,
    [FechaCreacion] DATETIME2 NULL
);
GO

-- Table: Workflow_Inventarios
CREATE TABLE [Workflow_Inventarios] (
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
    [EstadoWorkflow] VARCHAR(50) NULL,
    [Estado] VARCHAR(50) NULL,
    [CicloActual] INT NULL,
    [TotalProductosDiferencia] INT NULL,
    [ValorTotalDiferencias] DECIMAL(18,2) NULL,
    [FechaCreacion] DATETIME2 NULL,
    [FechaUltimaActualizacion] DATETIME2 NULL,
    [UsuarioCreadorID] VARCHAR(50) NULL,
    [NotasJSON] NVARCHAR(MAX) NULL
);
GO

-- Table: Workflow_Justificaciones
CREATE TABLE [Workflow_Justificaciones] (
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
    [Estado] VARCHAR(50) NULL,
    [FechaCreacion] DATETIME2 NULL,
    [FechaRevision] DATETIME2 NULL,
    [RevisadoPorID] VARCHAR(50) NULL,
    [Comentarios] NVARCHAR(MAX) NULL
);
GO

