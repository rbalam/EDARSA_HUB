-- EDARSA HUB - Tablajería Fase 6: Inventarios, Costeo y Contabilidad

-- 1. Movimientos de Inventario
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Tablajeria_MovimientosInventario')
BEGIN
    CREATE TABLE Tablajeria_MovimientosInventario (
        MovimientoID VARCHAR(50) PRIMARY KEY,
        OrdenID VARCHAR(50) NOT NULL,
        TipoMovimiento VARCHAR(20) NOT NULL,
        ProductoCodigo VARCHAR(50) NOT NULL,
        ProductoNombre VARCHAR(200),
        AlmacenOrigenID VARCHAR(50),
        AlmacenDestinoID VARCHAR(50),
        Cantidad DECIMAL(18,4) NOT NULL,
        UnidadMedida VARCHAR(20),
        CostoUnitario DECIMAL(18,4),
        CostoTotal DECIMAL(18,2),
        LoteProducto VARCHAR(100),
        FechaMovimiento DATETIME2 DEFAULT GETUTCDATE(),
        UsuarioID VARCHAR(50),
        Referencia VARCHAR(100),
        Sincronizado BIT DEFAULT 0,
        FechaSincronizacion DATETIME2,
        ErrorSincronizacion VARCHAR(500)
    );
    CREATE INDEX IX_MovInv_OrdenID ON Tablajeria_MovimientosInventario(OrdenID);
END;

-- 2. Costeo de Producción
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Tablajeria_CosteoProduccion')
BEGIN
    CREATE TABLE Tablajeria_CosteoProduccion (
        CosteoID VARCHAR(50) PRIMARY KEY,
        OrdenID VARCHAR(50) NOT NULL,
        FechaCosteo DATETIME2 DEFAULT GETUTCDATE(),
        InsumoBaseCodigo VARCHAR(50),
        InsumoBaseNombre VARCHAR(200),
        CantidadInsumoConsumida DECIMAL(18,4),
        CostoUnitarioInsumo DECIMAL(18,4),
        CostoTotalInsumo DECIMAL(18,2),
        CostoManoObra DECIMAL(18,2) DEFAULT 0,
        CostoIndirectos DECIMAL(18,2) DEFAULT 0,
        CostoEnergia DECIMAL(18,2) DEFAULT 0,
        OtrosCostos DECIMAL(18,2) DEFAULT 0,
        CostoTotalProduccion DECIMAL(18,2),
        CostoUnitarioPromedio DECIMAL(18,4),
        ReglaCosteoAplicada VARCHAR(20),
        UsuarioID VARCHAR(50),
        Observaciones NVARCHAR(MAX),
        EsEstimado BIT DEFAULT 0
    );
    CREATE INDEX IX_Costeo_OrdenID ON Tablajeria_CosteoProduccion(OrdenID);
END;

-- 3. Detalle Costeo por Producto
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Tablajeria_CosteoDetalle')
BEGIN
    CREATE TABLE Tablajeria_CosteoDetalle (
        DetalleID VARCHAR(50) PRIMARY KEY,
        CosteoID VARCHAR(50) NOT NULL,
        OrdenDetalleID VARCHAR(50),
        ProductoCodigo VARCHAR(50),
        ProductoNombre VARCHAR(200),
        TipoDerivado VARCHAR(20),
        CantidadProducida DECIMAL(18,4),
        PorcentajeCostoAsignado DECIMAL(10,4),
        CostoAsignado DECIMAL(18,2),
        CostoUnitario DECIMAL(18,4),
        EsInventariable BIT DEFAULT 1
    );
    CREATE INDEX IX_CosteoDetalle_CosteoID ON Tablajeria_CosteoDetalle(CosteoID);
END;

-- 4. Pólizas Contables
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Tablajeria_PolizasContables')
BEGIN
    CREATE TABLE Tablajeria_PolizasContables (
        PolizaID VARCHAR(50) PRIMARY KEY,
        OrdenID VARCHAR(50) NOT NULL,
        TipoPoliza VARCHAR(50),
        NumeroPoliza VARCHAR(50),
        FechaPoliza DATE,
        Concepto VARCHAR(500),
        MontoTotal DECIMAL(18,2),
        EstatusPoliza VARCHAR(20) DEFAULT 'PENDIENTE',
        FechaCreacion DATETIME2 DEFAULT GETUTCDATE(),
        FechaContabilizacion DATETIME2,
        UsuarioID VARCHAR(50),
        ErrorContabilizacion VARCHAR(500)
    );
    CREATE INDEX IX_Polizas_OrdenID ON Tablajeria_PolizasContables(OrdenID);
END;

-- 5. Detalle Póliza
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Tablajeria_PolizasDetalle')
BEGIN
    CREATE TABLE Tablajeria_PolizasDetalle (
        AsientoID VARCHAR(50) PRIMARY KEY,
        PolizaID VARCHAR(50) NOT NULL,
        NumeroLinea INT,
        CuentaContable VARCHAR(50),
        NombreCuenta VARCHAR(200),
        Concepto VARCHAR(300),
        Debe DECIMAL(18,2) DEFAULT 0,
        Haber DECIMAL(18,2) DEFAULT 0,
        Referencia VARCHAR(100)
    );
    CREATE INDEX IX_PolizaDetalle_PolizaID ON Tablajeria_PolizasDetalle(PolizaID);
END;

-- 6. Configuración Contable
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Tablajeria_ConfigContable')
BEGIN
    CREATE TABLE Tablajeria_ConfigContable (
        ConfigID INT IDENTITY(1,1) PRIMARY KEY,
        EmpresaID VARCHAR(50) NOT NULL,
        CuentaAlmacenInsumos VARCHAR(50),
        CuentaAlmacenProductos VARCHAR(50),
        CuentaProduccionEnProceso VARCHAR(50),
        CuentaCostoVentas VARCHAR(50),
        CuentaMermaOperativa VARCHAR(50),
        CuentaMermaExtraordinaria VARCHAR(50),
        CuentaVariacionCosto VARCHAR(50),
        GenerarPolizaAutomatica BIT DEFAULT 1,
        AfectarInventarioAutomatico BIT DEFAULT 1,
        ToleranciaVariacionPorcentaje DECIMAL(5,2) DEFAULT 5.00,
        Activo BIT DEFAULT 1,
        FechaModificacion DATETIME2 DEFAULT GETUTCDATE()
    );
    CREATE UNIQUE INDEX IX_ConfigContable_Empresa ON Tablajeria_ConfigContable(EmpresaID);
END;
