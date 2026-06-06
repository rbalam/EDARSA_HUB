-- ============================================================
-- EDARSAHUB_SCHEMA_ONLY.sql
-- Esquema de Base de Datos para Portal Inteligencia Comercial
-- Generado: Junio 2026
-- ============================================================


-- ============================================================
-- TABLA: Sync_Sales
-- ============================================================
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


-- ============================================================
-- TABLA: Sync_PAX_Detalle
-- ============================================================
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


-- ============================================================
-- TABLA: Fact_Ventas_Consolidadas
-- ============================================================
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


-- ============================================================
-- TABLA: Products
-- ============================================================
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


-- ============================================================
-- TABLA: Sync_Productos
-- ============================================================
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


-- ============================================================
-- TABLA: Sync_Productos_Familias
-- ============================================================
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


-- ============================================================
-- TABLA: Sync_Productos_SubFamilias
-- ============================================================
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


-- ============================================================
-- TABLA: Config_Horarios
-- ============================================================
CREATE TABLE [Config_Horarios] (
    [Id] INT NOT NULL,
    [TenantID] INT NOT NULL,
    [NombrePeriodo] NVARCHAR(50) NULL,
    [HoraInicio] TIME NULL,
    [HoraFin] TIME NULL
);
GO


-- ============================================================
-- TABLA: Unidades_Negocio
-- ============================================================
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


-- ============================================================
-- TABLA: Servidores_Conexiones
-- ============================================================
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


-- ============================================================
-- TABLA: Comercial_KPIs_Diarios_v2
-- ============================================================
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


-- ============================================================
-- TABLA: Comercial_Ventas_Dia_Abiertas_v2
-- ============================================================
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


-- ============================================================
-- TABLA: Sys_Scheduler_Jobs
-- ============================================================
CREATE TABLE [Sys_Scheduler_Jobs] (
    [JobID] VARCHAR(50) NOT NULL,
    [JobName] VARCHAR(100) NOT NULL,
    [CronExpression] VARCHAR(50) NOT NULL,
    [JobType] VARCHAR(20) NOT NULL,
    [Status] VARCHAR(20) NULL,
    [LastRunDate] DATETIME NULL
);
GO


-- ============================================================
-- VISTA: View_Inteligencia_Comercial (ESTRUCTURA)
-- ============================================================
-- Columnas:
--   UnidadNegocio      VARCHAR(20)    NULL
--   IdProducto         INT            NOT NULL
--   Producto           NVARCHAR(200)  NOT NULL
--   Familia            NVARCHAR(100)  NULL
--   CasaProductora     NVARCHAR(100)  NULL
--   CantidadTotal      DECIMAL        NULL
--   IngresoTotal       DECIMAL        NULL
--   Propina            DECIMAL        NULL
--   Pax                INT            NULL
--   FranjaHoraria      INT            NULL
-- 
-- NOTA: La vista actual tiene un bug (DATEPART HOUR en tipo DATE)
-- Requiere corrección en la definición original.
GO

-- ============================================================
-- STORED PROCEDURES RELACIONADOS
-- ============================================================
-- Sp_GetDashboardInteligencia

-- ============================================================
-- UNIDADES DE NEGOCIO ACTIVAS
-- ============================================================
-- 130MID          | 130° MERIDA                    | SoftRestaurant
-- 130QRO          | 130° QUERETARO                 | MPRO
-- CIENFUEGOS      | CIENFUEGOS                     | SoftRestaurant
-- ESTELAR         | LA ESTELAR                     | SoftRestaurant
-- ORIGEN          | ORIGEN                         | MPRO
