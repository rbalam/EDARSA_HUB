IF OBJECT_ID('dbo.Usuario_PermisosCatalogosFlujo', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Usuario_PermisosCatalogosFlujo (
        UsuarioID INT NOT NULL PRIMARY KEY,
        PuedeSolicitar BIT NOT NULL CONSTRAINT DF_UsuarioPermisosCatalogosFlujo_Solicitar DEFAULT 0,
        PuedeAutorizar BIT NOT NULL CONSTRAINT DF_UsuarioPermisosCatalogosFlujo_Autorizar DEFAULT 0,
        PuedeLiberar BIT NOT NULL CONSTRAINT DF_UsuarioPermisosCatalogosFlujo_Liberar DEFAULT 0,
        Activo BIT NOT NULL CONSTRAINT DF_UsuarioPermisosCatalogosFlujo_Activo DEFAULT 1,
        FechaAlta DATETIME2 NOT NULL CONSTRAINT DF_UsuarioPermisosCatalogosFlujo_FechaAlta DEFAULT SYSUTCDATETIME(),
        FechaModificacion DATETIME2 NULL,
        CreatedBy NVARCHAR(100) NULL,
        ModifiedBy NVARCHAR(100) NULL,
        CONSTRAINT FK_UsuarioPermisosCatalogosFlujo_Usuario
            FOREIGN KEY (UsuarioID) REFERENCES dbo.Usuario_Catalogo(UsuarioID)
    );
END;

IF OBJECT_ID('dbo.Usuario_PermisosCatalogosModulo', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Usuario_PermisosCatalogosModulo (
        UsuarioPermisoCatalogoID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        UsuarioID INT NOT NULL,
        ModuloID INT NOT NULL,
        Permitido BIT NOT NULL CONSTRAINT DF_UsuarioPermisosCatalogosModulo_Permitido DEFAULT 1,
        Activo BIT NOT NULL CONSTRAINT DF_UsuarioPermisosCatalogosModulo_Activo DEFAULT 1,
        FechaAlta DATETIME2 NOT NULL CONSTRAINT DF_UsuarioPermisosCatalogosModulo_FechaAlta DEFAULT SYSUTCDATETIME(),
        FechaModificacion DATETIME2 NULL,
        CreatedBy NVARCHAR(100) NULL,
        ModifiedBy NVARCHAR(100) NULL,
        CONSTRAINT FK_UsuarioPermisosCatalogosModulo_Usuario
            FOREIGN KEY (UsuarioID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
        CONSTRAINT FK_UsuarioPermisosCatalogosModulo_Modulo
            FOREIGN KEY (ModuloID) REFERENCES dbo.Usuario_Modulos(ModuloID)
    );

    CREATE UNIQUE INDEX UX_UsuarioPermisosCatalogosModulo_Usuario_Modulo
        ON dbo.Usuario_PermisosCatalogosModulo(UsuarioID, ModuloID);
END;
