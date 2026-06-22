/*
EDARSAHUB — Finanzas / Conciliaciones / NetPay Robot
Script base idempotente. Revisar diccionario real antes de producción.
SQL Server.
*/

IF OBJECT_ID('dbo.Finanzas_ConciliacionTipos', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Finanzas_ConciliacionTipos (
        TipoConciliacionID INT IDENTITY(1,1) PRIMARY KEY,
        Codigo VARCHAR(50) NOT NULL UNIQUE,
        Nombre NVARCHAR(150) NOT NULL,
        Descripcion NVARCHAR(500) NULL,
        Activo BIT NOT NULL DEFAULT 1,
        CreadoPorUsuarioID INT NULL,
        FechaCreacion DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );
END;

IF NOT EXISTS (SELECT 1 FROM dbo.Finanzas_ConciliacionTipos WHERE Codigo = 'NETPAY')
INSERT INTO dbo.Finanzas_ConciliacionTipos (Codigo, Nombre, Descripcion)
VALUES ('NETPAY', 'NetPay / Adquirente', 'Conciliación Corte Z / NetPay / Banco');

IF NOT EXISTS (SELECT 1 FROM dbo.Finanzas_ConciliacionTipos WHERE Codigo = 'EFECTIVO')
INSERT INTO dbo.Finanzas_ConciliacionTipos (Codigo, Nombre, Descripcion)
VALUES ('EFECTIVO', 'Efectivo', 'Conciliación de efectivo declarado en Cuadre contra depósitos bancarios');

IF NOT EXISTS (SELECT 1 FROM dbo.Finanzas_ConciliacionTipos WHERE Codigo = 'PROPINA_TPV')
INSERT INTO dbo.Finanzas_ConciliacionTipos (Codigo, Nombre, Descripcion)
VALUES ('PROPINA_TPV', 'Propina TPV', 'Conciliación de propinas cobradas por TPV y obligación de pago');

IF OBJECT_ID('dbo.Finanzas_Adquirentes', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Finanzas_Adquirentes (
        AdquirenteID INT IDENTITY(1,1) PRIMARY KEY,
        Codigo VARCHAR(50) NOT NULL UNIQUE,
        Nombre NVARCHAR(150) NOT NULL,
        Activo BIT NOT NULL DEFAULT 1,
        CreadoPorUsuarioID INT NULL,
        FechaCreacion DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );
END;

IF NOT EXISTS (SELECT 1 FROM dbo.Finanzas_Adquirentes WHERE Codigo = 'NETPAY')
INSERT INTO dbo.Finanzas_Adquirentes (Codigo, Nombre) VALUES ('NETPAY', 'NetPay');

IF OBJECT_ID('dbo.Finanzas_AdquirenteConectores', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Finanzas_AdquirenteConectores (
        ConectorID INT IDENTITY(1,1) PRIMARY KEY,
        UnidadNegocioID INT NULL,
        AdquirenteID INT NOT NULL,
        TipoConector VARCHAR(50) NOT NULL, -- PORTAL_ROBOT/API_FUTURA/EXCEL_MANUAL/COPY_PASTE/PDF_EVIDENCIA
        NombreConector NVARCHAR(150) NOT NULL,
        Activo BIT NOT NULL DEFAULT 1,
        ConfigJsonSeguro NVARCHAR(MAX) NULL,
        UltimaEjecucion DATETIME2 NULL,
        UltimoEstatus VARCHAR(50) NULL,
        CreadoPorUsuarioID INT NULL,
        FechaCreacion DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        ModificadoPorUsuarioID INT NULL,
        FechaModificacion DATETIME2 NULL
    );
END;

IF OBJECT_ID('dbo.Finanzas_AdquirenteConectorCredenciales', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Finanzas_AdquirenteConectorCredenciales (
        CredencialID INT IDENTITY(1,1) PRIMARY KEY,
        ConectorID INT NOT NULL,
        TipoCredencial VARCHAR(50) NOT NULL,
        Usuario NVARCHAR(255) NULL,
        SecretoCifrado VARBINARY(MAX) NULL,
        MetadataJsonSeguro NVARCHAR(MAX) NULL,
        FechaUltimaRotacion DATETIME2 NULL,
        Activo BIT NOT NULL DEFAULT 1,
        CreadoPorUsuarioID INT NULL,
        FechaCreacion DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        ModificadoPorUsuarioID INT NULL,
        FechaModificacion DATETIME2 NULL
    );
END;

IF OBJECT_ID('dbo.Finanzas_NetPayRobotConfig', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Finanzas_NetPayRobotConfig (
        RobotConfigID INT IDENTITY(1,1) PRIMARY KEY,
        ConectorID INT NULL,
        UnidadNegocioID INT NULL,
        AdquirenteID INT NULL,
        PortalURL NVARCHAR(500) NOT NULL,
        UsuarioPortal NVARCHAR(255) NOT NULL,
        PasswordCifrado VARBINARY(MAX) NULL,
        MFARequiere BIT NOT NULL DEFAULT 0,
        MFAEstrategia VARCHAR(50) NULL,
        StoreID NVARCHAR(100) NULL,
        CuentaDeposito NVARCHAR(100) NULL,
        Headless BIT NOT NULL DEFAULT 1,
        Activo BIT NOT NULL DEFAULT 1,
        UltimaEjecucion DATETIME2 NULL,
        UltimoEstatus VARCHAR(50) NULL,
        CreadoPorUsuarioID INT NULL,
        FechaCreacion DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        ModificadoPorUsuarioID INT NULL,
        FechaModificacion DATETIME2 NULL
    );
END;

IF OBJECT_ID('dbo.Finanzas_NetPayRobotEjecuciones', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Finanzas_NetPayRobotEjecuciones (
        EjecucionID BIGINT IDENTITY(1,1) PRIMARY KEY,
        EjecucionPadreID BIGINT NULL,
        RobotConfigID INT NULL,
        ConectorID INT NULL,
        UnidadNegocioID INT NULL,
        FechaInicio DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        FechaFin DATETIME2 NULL,
        TipoReporte VARCHAR(50) NOT NULL,
        FechaDesde DATE NOT NULL,
        FechaHasta DATE NOT NULL,
        NumeroBloque INT NULL,
        TotalBloques INT NULL,
        EsBackfill BIT NOT NULL DEFAULT 0,
        Estatus VARCHAR(50) NOT NULL DEFAULT 'INICIADO',
        RegistrosDescargados INT NULL,
        TotalMontoTrx DECIMAL(18,2) NULL,
        TotalMontoDeposito DECIMAL(18,2) NULL,
        TotalComision DECIMAL(18,2) NULL,
        TotalIVAComision DECIMAL(18,2) NULL,
        HashArchivo VARBINARY(32) NULL,
        RutaArchivoOriginal NVARCHAR(500) NULL,
        ErrorCodigo VARCHAR(100) NULL,
        ErrorMensaje NVARCHAR(MAX) NULL,
        CreadoPorUsuarioID INT NULL
    );
END;

IF OBJECT_ID('dbo.Finanzas_NetPayRobotArchivos', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Finanzas_NetPayRobotArchivos (
        ArchivoID BIGINT IDENTITY(1,1) PRIMARY KEY,
        EjecucionID BIGINT NOT NULL,
        UnidadNegocioID INT NULL,
        TipoReporte VARCHAR(50) NOT NULL,
        NombreArchivoOriginal NVARCHAR(255) NOT NULL,
        RutaArchivoSeguro NVARCHAR(500) NOT NULL,
        Extension VARCHAR(20) NOT NULL,
        HashArchivo VARBINARY(32) NOT NULL,
        TamanoBytes BIGINT NULL,
        LayoutDetectado VARCHAR(100) NULL,
        EstatusValidacion VARCHAR(50) NOT NULL DEFAULT 'PENDIENTE',
        FechaDescarga DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );
END;

IF OBJECT_ID('dbo.Finanzas_NetPayRobotEventosLog', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Finanzas_NetPayRobotEventosLog (
        EventoID BIGINT IDENTITY(1,1) PRIMARY KEY,
        EjecucionID BIGINT NULL,
        FechaEvento DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        Nivel VARCHAR(20) NOT NULL,
        CodigoEvento VARCHAR(100) NOT NULL,
        Mensaje NVARCHAR(1000) NOT NULL,
        DetalleTecnicoSeguro NVARCHAR(MAX) NULL
    );
END;

IF OBJECT_ID('dbo.Finanzas_NetPayRobotSelectores', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Finanzas_NetPayRobotSelectores (
        SelectorID INT IDENTITY(1,1) PRIMARY KEY,
        PortalVersion NVARCHAR(50) NULL,
        Paso NVARCHAR(100) NOT NULL,
        SelectorCSS NVARCHAR(500) NULL,
        SelectorXPath NVARCHAR(1000) NULL,
        TextoAlternativo NVARCHAR(500) NULL,
        Activo BIT NOT NULL DEFAULT 1,
        Prioridad INT NOT NULL DEFAULT 100,
        FechaCreacion DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );
END;

IF OBJECT_ID('dbo.Finanzas_AdquirenteImportaciones', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Finanzas_AdquirenteImportaciones (
        ImportacionID BIGINT IDENTITY(1,1) PRIMARY KEY,
        UnidadNegocioID INT NULL,
        AdquirenteID INT NULL,
        FuenteIngesta VARCHAR(50) NOT NULL,
        TipoReporte VARCHAR(80) NOT NULL,
        NombreArchivoOriginal NVARCHAR(255) NULL,
        RutaArchivoSeguro NVARCHAR(500) NULL,
        HashArchivo VARBINARY(32) NULL,
        FechaReporteDesde DATE NULL,
        FechaReporteHasta DATE NULL,
        TotalRegistros INT NOT NULL DEFAULT 0,
        TotalImportado DECIMAL(18,2) NOT NULL DEFAULT 0,
        Estatus VARCHAR(50) NOT NULL DEFAULT 'CARGADO',
        Observaciones NVARCHAR(MAX) NULL,
        CreadoPorUsuarioID INT NULL,
        FechaCreacion DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );
END;

IF OBJECT_ID('dbo.Finanzas_AdquirenteImportacionDetalle', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Finanzas_AdquirenteImportacionDetalle (
        ImportacionDetalleID BIGINT IDENTITY(1,1) PRIMARY KEY,
        ImportacionID BIGINT NOT NULL,
        NumeroFila INT NOT NULL,
        Hoja NVARCHAR(150) NULL,
        RegistroJson NVARCHAR(MAX) NOT NULL,
        HashRegistro VARBINARY(32) NULL,
        Estatus VARCHAR(50) NOT NULL DEFAULT 'STAGING',
        ErrorValidacion NVARCHAR(MAX) NULL,
        FechaCreacion DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );
END;

IF OBJECT_ID('dbo.Finanzas_AdquirenteTransacciones', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Finanzas_AdquirenteTransacciones (
        TransaccionID BIGINT IDENTITY(1,1) PRIMARY KEY,
        ImportacionID BIGINT NULL,
        UnidadNegocioID INT NULL,
        AdquirenteID INT NULL,
        FuenteIngesta VARCHAR(50) NOT NULL,
        FechaTrx DATE NULL,
        HoraTrx TIME NULL,
        FechaOperativa DATE NULL,
        MontoTrx DECIMAL(18,2) NOT NULL DEFAULT 0,
        VentaNeta DECIMAL(18,2) NOT NULL DEFAULT 0,
        Propina DECIMAL(18,2) NOT NULL DEFAULT 0,
        RetiroEfectivo DECIMAL(18,2) NOT NULL DEFAULT 0,
        EstatusTrx NVARCHAR(50) NULL,
        CodigoRespuesta NVARCHAR(20) NULL,
        Motivo NVARCHAR(255) NULL,
        NombreEmpresa NVARCHAR(255) NULL,
        Sucursal NVARCHAR(255) NULL,
        AliasProducto NVARCHAR(255) NULL,
        StoreID NVARCHAR(100) NULL,
        Producto NVARCHAR(255) NULL,
        Banco NVARCHAR(150) NULL,
        Marca NVARCHAR(100) NULL,
        TipoVenta NVARCHAR(100) NULL,
        TipoTarjeta NVARCHAR(100) NULL,
        OrderID NVARCHAR(100) NULL,
        CodigoAutorizacion NVARCHAR(100) NULL,
        Referencia NVARCHAR(150) NULL,
        Comentario NVARCHAR(500) NULL,
        Cajero NVARCHAR(150) NULL,
        HashRegistro VARBINARY(32) NULL,
        Estatus VARCHAR(50) NOT NULL DEFAULT 'PENDIENTE_CONCILIAR',
        FechaCreacion DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );
END;

IF OBJECT_ID('dbo.Finanzas_AdquirenteDepositos', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Finanzas_AdquirenteDepositos (
        DepositoID BIGINT IDENTITY(1,1) PRIMARY KEY,
        ImportacionID BIGINT NULL,
        UnidadNegocioID INT NULL,
        AdquirenteID INT NULL,
        FuenteIngesta VARCHAR(50) NOT NULL,
        FechaDeposito DATE NULL,
        FechaTrx DATE NULL,
        HoraTrx TIME NULL,
        ClaveRastreo NVARCHAR(150) NULL,
        CuentaDeposito NVARCHAR(100) NULL,
        NombreEmpresa NVARCHAR(255) NULL,
        Sucursal NVARCHAR(255) NULL,
        StoreID NVARCHAR(100) NULL,
        Producto NVARCHAR(255) NULL,
        MontoTrx DECIMAL(18,2) NOT NULL DEFAULT 0,
        VentaNeta DECIMAL(18,2) NOT NULL DEFAULT 0,
        Propina DECIMAL(18,2) NOT NULL DEFAULT 0,
        MontoDeposito DECIMAL(18,2) NOT NULL DEFAULT 0,
        ComisionBasePorcentaje DECIMAL(9,6) NULL,
        ComisionBaseImporte DECIMAL(18,2) NOT NULL DEFAULT 0,
        SobreTasaPorcentaje DECIMAL(9,6) NULL,
        SobreTasaImporte DECIMAL(18,2) NOT NULL DEFAULT 0,
        ComisionTotal DECIMAL(18,2) NOT NULL DEFAULT 0,
        IVAComisiones DECIMAL(18,2) NOT NULL DEFAULT 0,
        ComisionesMasIVA DECIMAL(18,2) NOT NULL DEFAULT 0,
        Banco NVARCHAR(150) NULL,
        Marca NVARCHAR(100) NULL,
        TipoVenta NVARCHAR(100) NULL,
        TipoTarjeta NVARCHAR(100) NULL,
        CodigoAutorizacion NVARCHAR(100) NULL,
        OrderID NVARCHAR(100) NULL,
        ReferenciaDepositoStoreID NVARCHAR(200) NULL,
        Referencia NVARCHAR(150) NULL,
        HashRegistro VARBINARY(32) NULL,
        Estatus VARCHAR(50) NOT NULL DEFAULT 'PENDIENTE_BANCO',
        FechaCreacion DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );
END;
