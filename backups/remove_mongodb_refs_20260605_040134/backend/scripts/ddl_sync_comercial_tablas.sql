-- ============================================================================
-- DDL: TABLAS SYNC COMERCIAL FALTANTES
-- EDARSA HUB - FASE A-P1 / DDL COMERCIAL
-- ============================================================================
-- Este script crea las tablas Sync necesarias para migrar los endpoints
-- comerciales LIVE a arquitectura SQL-First NO-LIVE.
--
-- TABLAS A CREAR:
-- 1. Sync_Metas_Comerciales
-- 2. Sync_Ticket_Perfecto
-- 3. Sync_Mesas
-- 4. Sync_Movimientos_Detalle
-- 5. Sync_Precios_Historicos
-- 6. Sync_PAX_Detalle
--
-- REGLA DE ORO: TODO DDL usa IF OBJECT_ID IS NULL para idempotencia
-- ============================================================================

USE EDARSAHUB;
GO

-- ============================================================================
-- 1. Sync_Metas_Comerciales
-- ============================================================================
-- Almacena metas comerciales de venta por sucursal/periodo
IF OBJECT_ID('dbo.Sync_Metas_Comerciales', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sync_Metas_Comerciales (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        MetaID NVARCHAR(50) NOT NULL,
        ServerID NVARCHAR(50) NOT NULL,
        SucursalID NVARCHAR(20) NOT NULL,
        SucursalNombre NVARCHAR(100),
        Anio INT NOT NULL,
        Mes INT NOT NULL,
        MetaVentaBruta DECIMAL(18,2) DEFAULT 0,
        MetaVentaNeta DECIMAL(18,2) DEFAULT 0,
        MetaTicketPromedio DECIMAL(18,2) DEFAULT 0,
        MetaCuentas INT DEFAULT 0,
        MetaComensales INT DEFAULT 0,
        MetaProductosMes INT DEFAULT 0,
        VentaBrutaActual DECIMAL(18,2) DEFAULT 0,
        VentaNetaActual DECIMAL(18,2) DEFAULT 0,
        TicketPromedioActual DECIMAL(18,2) DEFAULT 0,
        CuentasActual INT DEFAULT 0,
        ComensalesActual INT DEFAULT 0,
        PorcentajeCumplimiento DECIMAL(8,2) DEFAULT 0,
        DiasTranscurridos INT DEFAULT 0,
        DiasRestantes INT DEFAULT 0,
        ProyeccionMes DECIMAL(18,2) DEFAULT 0,
        FechaActualizacion DATETIME2 DEFAULT GETUTCDATE(),
        FechaSync DATETIME2 DEFAULT GETUTCDATE(),
        Activo BIT DEFAULT 1,
        CONSTRAINT UQ_Sync_Metas_Comerciales UNIQUE (ServerID, SucursalID, Anio, Mes)
    );
    
    CREATE INDEX IX_Sync_Metas_ServerSucursal ON dbo.Sync_Metas_Comerciales (ServerID, SucursalID);
    CREATE INDEX IX_Sync_Metas_Periodo ON dbo.Sync_Metas_Comerciales (Anio, Mes);
    
    PRINT 'Tabla Sync_Metas_Comerciales creada exitosamente';
END
GO

-- ============================================================================
-- 2. Sync_Ticket_Perfecto
-- ============================================================================
-- Almacena configuración y análisis de ticket perfecto por sucursal
IF OBJECT_ID('dbo.Sync_Ticket_Perfecto', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sync_Ticket_Perfecto (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        TicketID NVARCHAR(50) NOT NULL,
        ServerID NVARCHAR(50) NOT NULL,
        SucursalID NVARCHAR(20) NOT NULL,
        SucursalNombre NVARCHAR(100),
        FechaOperacion DATE NOT NULL,
        TotalCuentas INT DEFAULT 0,
        TotalComensales INT DEFAULT 0,
        VentaTotal DECIMAL(18,2) DEFAULT 0,
        TicketPromedioReal DECIMAL(18,2) DEFAULT 0,
        TicketPerfectoObjetivo DECIMAL(18,2) DEFAULT 0,
        PorcentajeCumplimiento DECIMAL(8,2) DEFAULT 0,
        CuentasBajoObjetivo INT DEFAULT 0,
        CuentasSobreObjetivo INT DEFAULT 0,
        CuentasEnRango INT DEFAULT 0,
        -- Composición promedio
        PromedioEntradas DECIMAL(8,2) DEFAULT 0,
        PromedioFuertes DECIMAL(8,2) DEFAULT 0,
        PromedioBebidas DECIMAL(8,2) DEFAULT 0,
        PromedioPostres DECIMAL(8,2) DEFAULT 0,
        -- Métricas adicionales
        TiempoPromedioMesa INT DEFAULT 0, -- en minutos
        RotacionMesas DECIMAL(8,2) DEFAULT 0,
        FechaSync DATETIME2 DEFAULT GETUTCDATE(),
        MetadatosJSON NVARCHAR(MAX),
        CONSTRAINT UQ_Sync_Ticket_Perfecto UNIQUE (ServerID, SucursalID, FechaOperacion)
    );
    
    CREATE INDEX IX_Sync_TicketPerfecto_ServerSucursal ON dbo.Sync_Ticket_Perfecto (ServerID, SucursalID);
    CREATE INDEX IX_Sync_TicketPerfecto_Fecha ON dbo.Sync_Ticket_Perfecto (FechaOperacion);
    
    PRINT 'Tabla Sync_Ticket_Perfecto creada exitosamente';
END
GO

-- ============================================================================
-- 3. Sync_Mesas
-- ============================================================================
-- Almacena estado y rotación de mesas por sucursal
IF OBJECT_ID('dbo.Sync_Mesas', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sync_Mesas (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        MesaRegistroID NVARCHAR(50) NOT NULL,
        ServerID NVARCHAR(50) NOT NULL,
        SucursalID NVARCHAR(20) NOT NULL,
        SucursalNombre NVARCHAR(100),
        FechaOperacion DATE NOT NULL,
        MesaNumero NVARCHAR(20) NOT NULL,
        MesaNombre NVARCHAR(50),
        ZonaID NVARCHAR(20),
        ZonaNombre NVARCHAR(50),
        Capacidad INT DEFAULT 4,
        -- Métricas del día
        TotalCuentas INT DEFAULT 0,
        TotalComensales INT DEFAULT 0,
        VentaTotal DECIMAL(18,2) DEFAULT 0,
        TicketPromedio DECIMAL(18,2) DEFAULT 0,
        TiempoPromedioOcupacion INT DEFAULT 0, -- minutos
        RotacionDia DECIMAL(8,2) DEFAULT 0,
        -- Estado actual (para sync en tiempo real)
        EstadoActual NVARCHAR(20) DEFAULT 'LIBRE', -- LIBRE, OCUPADA, RESERVADA, CERRADA
        CuentaActualID NVARCHAR(50),
        MeseroActualID NVARCHAR(50),
        MeseroActualNombre NVARCHAR(100),
        HoraAperturaCuenta DATETIME2,
        FechaSync DATETIME2 DEFAULT GETUTCDATE(),
        CONSTRAINT UQ_Sync_Mesas UNIQUE (ServerID, SucursalID, FechaOperacion, MesaNumero)
    );
    
    CREATE INDEX IX_Sync_Mesas_ServerSucursal ON dbo.Sync_Mesas (ServerID, SucursalID);
    CREATE INDEX IX_Sync_Mesas_Fecha ON dbo.Sync_Mesas (FechaOperacion);
    CREATE INDEX IX_Sync_Mesas_Estado ON dbo.Sync_Mesas (EstadoActual);
    
    PRINT 'Tabla Sync_Mesas creada exitosamente';
END
GO

-- ============================================================================
-- 4. Sync_Movimientos_Detalle
-- ============================================================================
-- Almacena detalle de movimientos de productos vendidos
IF OBJECT_ID('dbo.Sync_Movimientos_Detalle', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sync_Movimientos_Detalle (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        MovimientoID NVARCHAR(50) NOT NULL,
        ServerID NVARCHAR(50) NOT NULL,
        SucursalID NVARCHAR(20) NOT NULL,
        FechaOperacion DATE NOT NULL,
        FechaHora DATETIME2 NOT NULL,
        CuentaID NVARCHAR(50),
        CuentaFolio NVARCHAR(50),
        MesaNumero NVARCHAR(20),
        MeseroID NVARCHAR(50),
        MeseroNombre NVARCHAR(100),
        ProductoID NVARCHAR(50) NOT NULL,
        ProductoCodigo NVARCHAR(50),
        ProductoNombre NVARCHAR(200),
        FamiliaID NVARCHAR(50),
        FamiliaNombre NVARCHAR(100),
        SubFamiliaID NVARCHAR(50),
        SubFamiliaNombre NVARCHAR(100),
        Cantidad DECIMAL(18,4) DEFAULT 0,
        PrecioUnitario DECIMAL(18,4) DEFAULT 0,
        Descuento DECIMAL(18,4) DEFAULT 0,
        Impuesto DECIMAL(18,4) DEFAULT 0,
        Subtotal DECIMAL(18,4) DEFAULT 0,
        Total DECIMAL(18,4) DEFAULT 0,
        TipoMovimiento NVARCHAR(20) DEFAULT 'VENTA', -- VENTA, CORTESIA, DEVOLUCION
        Cancelado BIT DEFAULT 0,
        FechaSync DATETIME2 DEFAULT GETUTCDATE()
    );
    
    CREATE INDEX IX_Sync_Movimientos_ServerSucursal ON dbo.Sync_Movimientos_Detalle (ServerID, SucursalID);
    CREATE INDEX IX_Sync_Movimientos_Fecha ON dbo.Sync_Movimientos_Detalle (FechaOperacion);
    CREATE INDEX IX_Sync_Movimientos_Producto ON dbo.Sync_Movimientos_Detalle (ProductoID);
    CREATE INDEX IX_Sync_Movimientos_Cuenta ON dbo.Sync_Movimientos_Detalle (CuentaID);
    
    PRINT 'Tabla Sync_Movimientos_Detalle creada exitosamente';
END
GO

-- ============================================================================
-- 5. Sync_Precios_Historicos
-- ============================================================================
-- Almacena historial de precios para análisis de tendencias
IF OBJECT_ID('dbo.Sync_Precios_Historicos', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sync_Precios_Historicos (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        PrecioHistoricoID NVARCHAR(50) NOT NULL,
        ServerID NVARCHAR(50) NOT NULL,
        SucursalID NVARCHAR(20) NOT NULL,
        ProductoID NVARCHAR(50) NOT NULL,
        ProductoCodigo NVARCHAR(50),
        ProductoNombre NVARCHAR(200),
        FechaVigencia DATE NOT NULL,
        FechaFinVigencia DATE,
        PrecioBase DECIMAL(18,4) NOT NULL,
        PrecioFinal DECIMAL(18,4) NOT NULL,
        ImpuestoIncluido BIT DEFAULT 1,
        TasaImpuesto DECIMAL(8,4) DEFAULT 0.16,
        PrecioAnterior DECIMAL(18,4),
        VariacionPorcentaje DECIMAL(8,2),
        MotivosCambio NVARCHAR(200),
        UsuarioModificacion NVARCHAR(100),
        FechaSync DATETIME2 DEFAULT GETUTCDATE(),
        CONSTRAINT UQ_Sync_Precios_Historicos UNIQUE (ServerID, SucursalID, ProductoID, FechaVigencia)
    );
    
    CREATE INDEX IX_Sync_Precios_ServerSucursal ON dbo.Sync_Precios_Historicos (ServerID, SucursalID);
    CREATE INDEX IX_Sync_Precios_Producto ON dbo.Sync_Precios_Historicos (ProductoID);
    CREATE INDEX IX_Sync_Precios_Fecha ON dbo.Sync_Precios_Historicos (FechaVigencia);
    
    PRINT 'Tabla Sync_Precios_Historicos creada exitosamente';
END
GO

-- ============================================================================
-- 6. Sync_PAX_Detalle
-- ============================================================================
-- Almacena detalle de PAX (comensales) por cuenta/mesa
IF OBJECT_ID('dbo.Sync_PAX_Detalle', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sync_PAX_Detalle (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        PAXRegistroID NVARCHAR(50) NOT NULL,
        ServerID NVARCHAR(50) NOT NULL,
        SucursalID NVARCHAR(20) NOT NULL,
        SucursalNombre NVARCHAR(100),
        FechaOperacion DATE NOT NULL,
        FechaHora DATETIME2 NOT NULL,
        CuentaID NVARCHAR(50),
        CuentaFolio NVARCHAR(50),
        MesaNumero NVARCHAR(20),
        MeseroID NVARCHAR(50),
        MeseroNombre NVARCHAR(100),
        NumeroComensales INT NOT NULL,
        TipoPAX NVARCHAR(20) DEFAULT 'NORMAL', -- NORMAL, NIÑO, CORTESIA
        VentaCuenta DECIMAL(18,2) DEFAULT 0,
        ConsumoPromedioPAX DECIMAL(18,2) DEFAULT 0,
        TiempoMesa INT DEFAULT 0, -- minutos
        HoraEntrada DATETIME2,
        HoraSalida DATETIME2,
        Turno NVARCHAR(20), -- DESAYUNO, COMIDA, CENA
        DiaSemana NVARCHAR(20),
        FechaSync DATETIME2 DEFAULT GETUTCDATE()
    );
    
    CREATE INDEX IX_Sync_PAX_ServerSucursal ON dbo.Sync_PAX_Detalle (ServerID, SucursalID);
    CREATE INDEX IX_Sync_PAX_Fecha ON dbo.Sync_PAX_Detalle (FechaOperacion);
    CREATE INDEX IX_Sync_PAX_Cuenta ON dbo.Sync_PAX_Detalle (CuentaID);
    CREATE INDEX IX_Sync_PAX_Turno ON dbo.Sync_PAX_Detalle (Turno);
    
    PRINT 'Tabla Sync_PAX_Detalle creada exitosamente';
END
GO

-- ============================================================================
-- VERIFICACIÓN FINAL
-- ============================================================================
PRINT '';
PRINT '=== VERIFICACIÓN TABLAS SYNC COMERCIAL ===';

SELECT 
    TABLE_NAME,
    CASE WHEN TABLE_NAME IS NOT NULL THEN 'EXISTE' ELSE 'NO EXISTE' END AS Estado
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME IN (
    'Sync_Metas_Comerciales',
    'Sync_Ticket_Perfecto',
    'Sync_Mesas',
    'Sync_Movimientos_Detalle',
    'Sync_Precios_Historicos',
    'Sync_PAX_Detalle'
)
ORDER BY TABLE_NAME;

PRINT '';
PRINT 'DDL COMERCIAL - TABLAS SYNC COMPLETADO';
GO
