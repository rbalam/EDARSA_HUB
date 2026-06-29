IF OBJECT_ID('dbo.Sync_Productos_Compuestos', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sync_Productos_Compuestos (
        CompuestoDetalleID UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
        ServerID UNIQUEIDENTIFIER NOT NULL,
        SystemType NVARCHAR(100) NOT NULL,
        ProductoCodigoFuente NVARCHAR(200) NOT NULL,
        ComponenteCodigoFuente NVARCHAR(200) NOT NULL,
        ComponenteNombre NVARCHAR(600) NOT NULL,
        FuenteDetalle NVARCHAR(100) NOT NULL,
        Cantidad DECIMAL(18,6) NOT NULL CONSTRAINT DF_Sync_Productos_Compuestos_Cantidad DEFAULT 1,
        UnidadMedida NVARCHAR(100) NOT NULL CONSTRAINT DF_Sync_Productos_Compuestos_Unidad DEFAULT 'UN',
        CostoUnitario DECIMAL(18,6) NULL,
        CostoTotal DECIMAL(18,6) NULL,
        GrupoCodigoFuente NVARCHAR(200) NULL,
        EmpresaCodigoFuente NVARCHAR(200) NULL,
        Activo BIT NULL CONSTRAINT DF_Sync_Productos_Compuestos_Activo DEFAULT 1,
        SyncRunID NVARCHAR(200) NULL,
        SyncedAtMexico DATETIME2 NULL,
        SourceStatus NVARCHAR(100) NULL,
        FechaCreacion DATETIME2 NULL CONSTRAINT DF_Sync_Productos_Compuestos_FechaCreacion DEFAULT SYSDATETIME(),
        FechaModificacion DATETIME2 NULL,
        CONSTRAINT PK_Sync_Productos_Compuestos PRIMARY KEY (CompuestoDetalleID)
    );
END;

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE name = 'UK_Sync_Compuestos_Prod_Comp_Fuente'
      AND object_id = OBJECT_ID('dbo.Sync_Productos_Compuestos')
)
BEGIN
    CREATE UNIQUE INDEX UK_Sync_Compuestos_Prod_Comp_Fuente
    ON dbo.Sync_Productos_Compuestos (
        ServerID,
        ProductoCodigoFuente,
        ComponenteCodigoFuente,
        FuenteDetalle
    );
END;

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE name = 'IX_Sync_Compuestos_Componente'
      AND object_id = OBJECT_ID('dbo.Sync_Productos_Compuestos')
)
BEGIN
    CREATE INDEX IX_Sync_Compuestos_Componente
    ON dbo.Sync_Productos_Compuestos (
        ServerID,
        ComponenteCodigoFuente,
        Activo
    );
END;
