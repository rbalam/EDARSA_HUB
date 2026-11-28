/*
EDARSA HUB - Tablajeria R24
Rendimiento por Lote Proveedor y Reclamos

SQL versionado. No ejecutar automaticamente contra Produccion.
EDARSAHUB SQL Server sigue siendo fuente canonica.
*/

IF OBJECT_ID('dbo.Tablajeria_LotesProveedorRendimiento', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Tablajeria_LotesProveedorRendimiento (
        LoteRendimientoID UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
        EmpresaID UNIQUEIDENTIFIER NULL,
        UnidadNegocioID UNIQUEIDENTIFIER NULL,
        SucursalID UNIQUEIDENTIFIER NULL,
        ProveedorID UNIQUEIDENTIFIER NULL,
        ProveedorNombre NVARCHAR(250) NULL,
        LoteProveedor NVARCHAR(120) NULL,
        LoteInterno NVARCHAR(120) NULL,
        OrdenCompraID UNIQUEIDENTIFIER NULL,
        OrdenCompraFolio NVARCHAR(80) NULL,
        RecepcionID UNIQUEIDENTIFIER NULL,
        RecepcionFolio NVARCHAR(80) NULL,
        FacturaID UNIQUEIDENTIFIER NULL,
        FacturaFolio NVARCHAR(80) NULL,
        OrdenTablajeID UNIQUEIDENTIFIER NULL,
        FolioOrdenTablaje NVARCHAR(80) NULL,
        InsumoBaseCodigo NVARCHAR(80) NULL,
        InsumoBaseNombre NVARCHAR(250) NULL,
        CantidadBaseKg DECIMAL(18,4) NULL,
        RendimientoEsperadoPorcentaje DECIMAL(9,4) NULL,
        RendimientoRealPorcentaje DECIMAL(9,4) NULL,
        DesviacionPorcentaje DECIMAL(9,4) NULL,
        MermaRealKg DECIMAL(18,4) NULL,
        CostoUnitario DECIMAL(18,6) NULL,
        ImpactoEconomico DECIMAL(18,4) NULL,
        Semaforo NVARCHAR(20) NOT NULL DEFAULT 'SIN_DATOS',
        Estatus NVARCHAR(30) NOT NULL DEFAULT 'CALCULADO',
        FechaOperacionMexico DATE NULL,
        FechaCalculoUTC DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        Activo BIT NOT NULL DEFAULT 1,
        UsuarioAltaID UNIQUEIDENTIFIER NULL,
        FechaAltaUTC DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );

    CREATE INDEX IX_Tablajeria_LotesProveedorRendimiento_Lote ON dbo.Tablajeria_LotesProveedorRendimiento (EmpresaID, ProveedorID, LoteProveedor, FechaOperacionMexico);
    CREATE INDEX IX_Tablajeria_LotesProveedorRendimiento_Orden ON dbo.Tablajeria_LotesProveedorRendimiento (OrdenTablajeID);
END;
GO

IF OBJECT_ID('dbo.Tablajeria_ReclamosProveedor', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Tablajeria_ReclamosProveedor (
        ReclamoProveedorID UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
        LoteRendimientoID UNIQUEIDENTIFIER NULL,
        EmpresaID UNIQUEIDENTIFIER NULL,
        UnidadNegocioID UNIQUEIDENTIFIER NULL,
        ProveedorID UNIQUEIDENTIFIER NULL,
        ProveedorNombre NVARCHAR(250) NULL,
        FolioReclamo NVARCHAR(80) NOT NULL,
        Motivo NVARCHAR(500) NOT NULL,
        Descripcion NVARCHAR(MAX) NULL,
        ImpactoEconomico DECIMAL(18,4) NULL,
        EvidenciaJSON NVARCHAR(MAX) NULL,
        Estatus NVARCHAR(30) NOT NULL DEFAULT 'ABIERTO',
        Prioridad NVARCHAR(20) NOT NULL DEFAULT 'MEDIA',
        FechaAperturaUTC DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        FechaCierreUTC DATETIME2 NULL,
        UsuarioAltaID UNIQUEIDENTIFIER NULL,
        UsuarioCierreID UNIQUEIDENTIFIER NULL,
        Activo BIT NOT NULL DEFAULT 1
    );

    CREATE UNIQUE INDEX UX_Tablajeria_ReclamosProveedor_Folio ON dbo.Tablajeria_ReclamosProveedor (FolioReclamo);
    CREATE INDEX IX_Tablajeria_ReclamosProveedor_Lote ON dbo.Tablajeria_ReclamosProveedor (LoteRendimientoID, Estatus);
END;
GO

IF OBJECT_ID('dbo.Tablajeria_ReportesLote', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Tablajeria_ReportesLote (
        ReporteLoteID UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
        EmpresaID UNIQUEIDENTIFIER NULL,
        UnidadNegocioID UNIQUEIDENTIFIER NULL,
        NombreReporte NVARCHAR(180) NOT NULL,
        Periodicidad NVARCHAR(30) NOT NULL DEFAULT 'DIARIA',
        DestinatariosJSON NVARCHAR(MAX) NULL,
        CanalesJSON NVARCHAR(MAX) NULL,
        FiltrosJSON NVARCHAR(MAX) NULL,
        Activo BIT NOT NULL DEFAULT 1,
        UltimaEjecucionUTC DATETIME2 NULL,
        ProximaEjecucionUTC DATETIME2 NULL,
        UsuarioAltaID UNIQUEIDENTIFIER NULL,
        FechaAltaUTC DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END;
GO

IF OBJECT_ID('dbo.Tablajeria_NotificacionesLote', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Tablajeria_NotificacionesLote (
        NotificacionLoteID UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
        ReporteLoteID UNIQUEIDENTIFIER NULL,
        LoteRendimientoID UNIQUEIDENTIFIER NULL,
        ReclamoProveedorID UNIQUEIDENTIFIER NULL,
        Canal NVARCHAR(30) NOT NULL,
        Destinatario NVARCHAR(250) NOT NULL,
        Asunto NVARCHAR(250) NULL,
        Mensaje NVARCHAR(MAX) NULL,
        EstatusEnvio NVARCHAR(30) NOT NULL DEFAULT 'PENDIENTE',
        Intentos INT NOT NULL DEFAULT 0,
        ErrorMensaje NVARCHAR(MAX) NULL,
        FechaProgramadaUTC DATETIME2 NULL,
        FechaEnvioUTC DATETIME2 NULL,
        FechaAcuseUTC DATETIME2 NULL,
        Activo BIT NOT NULL DEFAULT 1,
        FechaAltaUTC DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );

    CREATE INDEX IX_Tablajeria_NotificacionesLote_Estatus ON dbo.Tablajeria_NotificacionesLote (EstatusEnvio, FechaProgramadaUTC);
END;
GO
