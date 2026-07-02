IF OBJECT_ID('dbo.Comercial_MPRO_MenuPOS_Sync', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Comercial_MPRO_MenuPOS_Sync (
        MenuPOSID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        ServerID UNIQUEIDENTIFIER NOT NULL,
        Lista NVARCHAR(50) NOT NULL,
        ProveedorCodigoFuente NVARCHAR(50) NULL,
        ProveedorNombre NVARCHAR(200) NULL,
        ProductoCodigoFuente NVARCHAR(50) NOT NULL,
        ProductoCodigoFuentePadded NVARCHAR(50) NOT NULL,
        ProductoNombre NVARCHAR(300) NULL,
        TipoProducto NVARCHAR(50) NULL,
        FamiliaCodigoFuente NVARCHAR(50) NULL,
        FamiliaNombre NVARCHAR(200) NULL,
        SubFamiliaCodigoFuente NVARCHAR(50) NULL,
        CodigoBarras NVARCHAR(100) NULL,
        UnidadCompra NVARCHAR(50) NULL,
        UnidadVenta NVARCHAR(50) NULL,
        Activo BIT NOT NULL CONSTRAINT DF_Comercial_MPRO_MenuPOS_Sync_Activo DEFAULT 1,
        SourceFile NVARCHAR(200) NULL,
        CreatedAt DATETIME2 NOT NULL CONSTRAINT DF_Comercial_MPRO_MenuPOS_Sync_CreatedAt DEFAULT SYSUTCDATETIME(),
        UpdatedAt DATETIME2 NOT NULL CONSTRAINT DF_Comercial_MPRO_MenuPOS_Sync_UpdatedAt DEFAULT SYSUTCDATETIME()
    );

    CREATE UNIQUE INDEX UX_Comercial_MPRO_MenuPOS_Sync_Server_Lista_Producto
        ON dbo.Comercial_MPRO_MenuPOS_Sync (ServerID, Lista, ProductoCodigoFuentePadded);

    CREATE INDEX IX_Comercial_MPRO_MenuPOS_Sync_Server_Producto
        ON dbo.Comercial_MPRO_MenuPOS_Sync (ServerID, ProductoCodigoFuentePadded);

    CREATE INDEX IX_Comercial_MPRO_MenuPOS_Sync_Server_Lista
        ON dbo.Comercial_MPRO_MenuPOS_Sync (ServerID, Lista);
END;
