/*
EDARSA HUB - Tablajeria UAT Scope Fix Lonja Individual + Plantillas
SQL versionado. NO ejecutar automaticamente contra Produccion.
EDARSAHUB SQL Server sigue siendo fuente canonica.
*/

IF OBJECT_ID('dbo.Tablajeria_LonjasDisponibles', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Tablajeria_LonjasDisponibles (
        LonjaID UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
        EmpresaID UNIQUEIDENTIFIER NULL,
        UnidadNegocioID UNIQUEIDENTIFIER NULL,
        SucursalID UNIQUEIDENTIFIER NULL,
        AlmacenOrigenID UNIQUEIDENTIFIER NULL,
        AlmacenDestinoID UNIQUEIDENTIFIER NULL,
        LoteProveedor NVARCHAR(120) NULL,
        LoteInterno NVARCHAR(120) NULL,
        InsumoBaseCodigo NVARCHAR(80) NOT NULL,
        InsumoBaseNombre NVARCHAR(250) NULL,
        PesoLonjaKg DECIMAL(18,4) NOT NULL,
        CostoUnitario DECIMAL(18,6) NULL,
        CostoTotal DECIMAL(18,4) NULL,
        Estatus NVARCHAR(30) NOT NULL DEFAULT 'DISPONIBLE',
        OrdenTablajeID UNIQUEIDENTIFIER NULL,
        FechaRecepcionUTC DATETIME2 NULL,
        FechaProcesadaUTC DATETIME2 NULL,
        Activo BIT NOT NULL DEFAULT 1,
        UsuarioAltaID UNIQUEIDENTIFIER NULL,
        FechaAltaUTC DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END;
GO

IF COL_LENGTH('dbo.Operaciones_Tablaje_PlantillasDetalle', 'SkuKgCodigo') IS NULL
BEGIN
    ALTER TABLE dbo.Operaciones_Tablaje_PlantillasDetalle ADD
        SkuKgCodigo NVARCHAR(80) NULL,
        SkuPiezaCodigo NVARCHAR(80) NULL,
        UnidadPesoCodigo NVARCHAR(20) NULL,
        UnidadPiezaCodigo NVARCHAR(20) NULL,
        GramajePorPiezaGramos DECIMAL(18,4) NULL,
        CostoFijo BIT NOT NULL CONSTRAINT DF_TablajeDetalle_CostoFijo DEFAULT 0,
        CostoFijoUnitario DECIMAL(18,6) NULL,
        ProrrateaCosto BIT NOT NULL CONSTRAINT DF_TablajeDetalle_ProrrateaCosto DEFAULT 1;
END;
GO

IF COL_LENGTH('dbo.Operaciones_Tablaje_Ordenes', 'LonjaID') IS NULL
BEGIN
    ALTER TABLE dbo.Operaciones_Tablaje_Ordenes ADD
        LonjaID UNIQUEIDENTIFIER NULL,
        LoteRendimientoID UNIQUEIDENTIFIER NULL,
        AlmacenOrigenID UNIQUEIDENTIFIER NULL,
        AlmacenDestinoID UNIQUEIDENTIFIER NULL,
        PesoLonjaKg DECIMAL(18,4) NULL;
END;
GO

IF COL_LENGTH('dbo.Operaciones_Tablaje_OrdenesDetalle', 'PiezasReales') IS NULL
BEGIN
    ALTER TABLE dbo.Operaciones_Tablaje_OrdenesDetalle ADD
        PiezasReales DECIMAL(18,4) NULL,
        GramajePorPiezaGramos DECIMAL(18,4) NULL,
        SkuKgCodigo NVARCHAR(80) NULL,
        SkuPiezaCodigo NVARCHAR(80) NULL,
        CostoFijo BIT NOT NULL CONSTRAINT DF_TablajeOrdenDetalle_CostoFijo DEFAULT 0,
        CostoFijoUnitario DECIMAL(18,6) NULL,
        ProrrateaCosto BIT NOT NULL CONSTRAINT DF_TablajeOrdenDetalle_ProrrateaCosto DEFAULT 1;
END;
GO
