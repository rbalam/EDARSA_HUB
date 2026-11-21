SET XACT_ABORT ON;
SET NOCOUNT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    /* =========================================================
       PREFLIGHT CANONICO A4
       ========================================================= */
    IF DB_NAME() <> N'EDARSAHUB'
        THROW 52000, 'A4 requiere la base canonica EDARSAHUB.', 1;

    IF OBJECT_ID(N'dbo.Gobierno_Persona', N'U') IS NULL
       OR OBJECT_ID(N'dbo.Gobierno_Documento', N'U') IS NULL
       OR OBJECT_ID(N'dbo.Usuario_Catalogo', N'U') IS NULL
       OR OBJECT_ID(N'dbo.Sistema_Empresas', N'U') IS NULL
       OR OBJECT_ID(N'dbo.Cliente_Catalogo', N'U') IS NULL
       OR OBJECT_ID(N'dbo.Sistema_Modulos', N'U') IS NULL
       OR OBJECT_ID(N'dbo.Sistema_ModulosMenus', N'U') IS NULL
       OR OBJECT_ID(N'dbo.Sistema_ModulosPermisos', N'U') IS NULL
    BEGIN
        THROW 52001, 'Faltan dependencias canonicas BOS para ARBITROA A4.', 1;
    END;

    IF COL_LENGTH(N'dbo.Gobierno_Persona', N'PersonaID') IS NULL
       OR COL_LENGTH(N'dbo.Gobierno_Documento', N'DocumentoID') IS NULL
       OR COL_LENGTH(N'dbo.Usuario_Catalogo', N'UsuarioID') IS NULL
       OR COL_LENGTH(N'dbo.Sistema_Empresas', N'EmpresaID') IS NULL
       OR COL_LENGTH(N'dbo.Cliente_Catalogo', N'ClienteID') IS NULL
    BEGIN
        THROW 52002, 'Dependencias BOS incompatibles para ARBITROA A4.', 1;
    END;

    /* =========================================================
       1. ARBITROA_Deportes
       ========================================================= */
    IF OBJECT_ID(N'dbo.ARBITROA_Deportes', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.ARBITROA_Deportes (
            DeporteID INT IDENTITY(1,1) NOT NULL
                CONSTRAINT PK_ARBITROA_Deportes PRIMARY KEY,
            Codigo VARCHAR(40) NOT NULL,
            Nombre NVARCHAR(100) NOT NULL,
            Activo BIT NOT NULL
                CONSTRAINT DF_ARBITROA_Deportes_Activo DEFAULT (1),
            UsuarioAltaID INT NULL,
            FechaAltaUTC DATETIME2(0) NOT NULL
                CONSTRAINT DF_ARBITROA_Deportes_FechaAltaUTC DEFAULT SYSUTCDATETIME(),
            UsuarioActualizacionID INT NULL,
            FechaActualizacionUTC DATETIME2(0) NULL,
            CONSTRAINT UQ_ARBITROA_Deportes_Codigo UNIQUE (Codigo),
            CONSTRAINT FK_ARBITROA_Deportes_UsuarioAlta
                FOREIGN KEY (UsuarioAltaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
            CONSTRAINT FK_ARBITROA_Deportes_UsuarioActualizacion
                FOREIGN KEY (UsuarioActualizacionID) REFERENCES dbo.Usuario_Catalogo(UsuarioID)
        );
    END;

    IF COL_LENGTH(N'dbo.ARBITROA_Deportes', N'DeporteID') IS NULL
       OR COL_LENGTH(N'dbo.ARBITROA_Deportes', N'Codigo') IS NULL
       OR COL_LENGTH(N'dbo.ARBITROA_Deportes', N'Nombre') IS NULL
       OR COL_LENGTH(N'dbo.ARBITROA_Deportes', N'Activo') IS NULL
        THROW 52003, 'ARBITROA_Deportes existe con contrato incompatible.', 1;

    MERGE dbo.ARBITROA_Deportes AS target
    USING (VALUES
        ('FUTBOL', N'Futbol'),
        ('FUTBOL7', N'Futbol 7'),
        ('FUTBOL_RAPIDO', N'Futbol rapido'),
        ('BASQUETBOL', N'Basquetbol'),
        ('VOLEIBOL', N'Voleibol'),
        ('BEISBOL', N'Beisbol')
    ) AS source(Codigo, Nombre)
    ON target.Codigo = source.Codigo
    WHEN MATCHED THEN
        UPDATE SET target.Nombre = source.Nombre, target.Activo = 1
    WHEN NOT MATCHED THEN
        INSERT (Codigo, Nombre, Activo)
        VALUES (source.Codigo, source.Nombre, 1);

    /* =========================================================
       2. ARBITROA_Organizaciones
       ========================================================= */
    IF OBJECT_ID(N'dbo.ARBITROA_Organizaciones', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.ARBITROA_Organizaciones (
            OrganizacionID BIGINT IDENTITY(1,1) NOT NULL
                CONSTRAINT PK_ARBITROA_Organizaciones PRIMARY KEY,
            PublicUUID UNIQUEIDENTIFIER NOT NULL
                CONSTRAINT DF_ARBITROA_Organizaciones_PublicUUID DEFAULT NEWSEQUENTIALID(),
            TipoOrganizacion VARCHAR(30) NOT NULL,
            Codigo VARCHAR(60) NOT NULL,
            Nombre NVARCHAR(200) NOT NULL,
            EmpresaID INT NULL,
            ClienteID INT NULL,
            VigenteDesde DATE NULL,
            VigenteHasta DATE NULL,
            Activo BIT NOT NULL
                CONSTRAINT DF_ARBITROA_Organizaciones_Activo DEFAULT (1),
            UsuarioAltaID INT NULL,
            FechaAltaUTC DATETIME2(0) NOT NULL
                CONSTRAINT DF_ARBITROA_Organizaciones_FechaAltaUTC DEFAULT SYSUTCDATETIME(),
            UsuarioActualizacionID INT NULL,
            FechaActualizacionUTC DATETIME2(0) NULL,
            CONSTRAINT UQ_ARBITROA_Organizaciones_PublicUUID UNIQUE (PublicUUID),
            CONSTRAINT CK_ARBITROA_Organizaciones_Tipo CHECK (
                TipoOrganizacion IN ('SINDICATO','LIGA','ASOCIACION','EMPRESA_SEDE','OTRA')
            ),
            CONSTRAINT CK_ARBITROA_Organizaciones_Vigencia CHECK (
                VigenteHasta IS NULL OR VigenteDesde IS NULL OR VigenteHasta >= VigenteDesde
            ),
            CONSTRAINT FK_ARBITROA_Organizaciones_Empresa
                FOREIGN KEY (EmpresaID) REFERENCES dbo.Sistema_Empresas(EmpresaID),
            CONSTRAINT FK_ARBITROA_Organizaciones_Cliente
                FOREIGN KEY (ClienteID) REFERENCES dbo.Cliente_Catalogo(ClienteID),
            CONSTRAINT FK_ARBITROA_Organizaciones_UsuarioAlta
                FOREIGN KEY (UsuarioAltaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
            CONSTRAINT FK_ARBITROA_Organizaciones_UsuarioActualizacion
                FOREIGN KEY (UsuarioActualizacionID) REFERENCES dbo.Usuario_Catalogo(UsuarioID)
        );

        CREATE UNIQUE INDEX UX_ARBITROA_Organizaciones_Codigo_Activo
            ON dbo.ARBITROA_Organizaciones(Codigo)
            WHERE Activo = 1;
    END;

    /* =========================================================
       3. ARBITROA_Afiliaciones
       ========================================================= */
    IF OBJECT_ID(N'dbo.ARBITROA_Afiliaciones', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.ARBITROA_Afiliaciones (
            AfiliacionID BIGINT IDENTITY(1,1) NOT NULL
                CONSTRAINT PK_ARBITROA_Afiliaciones PRIMARY KEY,
            OrganizacionPadreID BIGINT NOT NULL,
            OrganizacionAfiliadaID BIGINT NOT NULL,
            VigenteDesde DATE NOT NULL,
            VigenteHasta DATE NULL,
            Estado VARCHAR(20) NOT NULL,
            Activo BIT NOT NULL
                CONSTRAINT DF_ARBITROA_Afiliaciones_Activo DEFAULT (1),
            UsuarioAltaID INT NULL,
            FechaAltaUTC DATETIME2(0) NOT NULL
                CONSTRAINT DF_ARBITROA_Afiliaciones_FechaAltaUTC DEFAULT SYSUTCDATETIME(),
            UsuarioActualizacionID INT NULL,
            FechaActualizacionUTC DATETIME2(0) NULL,
            CONSTRAINT CK_ARBITROA_Afiliaciones_Organizaciones CHECK (
                OrganizacionPadreID <> OrganizacionAfiliadaID
            ),
            CONSTRAINT CK_ARBITROA_Afiliaciones_Vigencia CHECK (
                VigenteHasta IS NULL OR VigenteHasta >= VigenteDesde
            ),
            CONSTRAINT CK_ARBITROA_Afiliaciones_Estado CHECK (
                Estado IN ('PENDIENTE','VIGENTE','SUSPENDIDA','TERMINADA')
            ),
            CONSTRAINT FK_ARBITROA_Afiliaciones_Padre
                FOREIGN KEY (OrganizacionPadreID) REFERENCES dbo.ARBITROA_Organizaciones(OrganizacionID),
            CONSTRAINT FK_ARBITROA_Afiliaciones_Afiliada
                FOREIGN KEY (OrganizacionAfiliadaID) REFERENCES dbo.ARBITROA_Organizaciones(OrganizacionID),
            CONSTRAINT FK_ARBITROA_Afiliaciones_UsuarioAlta
                FOREIGN KEY (UsuarioAltaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
            CONSTRAINT FK_ARBITROA_Afiliaciones_UsuarioActualizacion
                FOREIGN KEY (UsuarioActualizacionID) REFERENCES dbo.Usuario_Catalogo(UsuarioID)
        );

        CREATE UNIQUE INDEX UX_ARBITROA_Afiliaciones_Par_Activo
            ON dbo.ARBITROA_Afiliaciones(OrganizacionPadreID, OrganizacionAfiliadaID)
            WHERE Activo = 1;
        CREATE INDEX IX_ARBITROA_Afiliaciones_Padre_Vigencia
            ON dbo.ARBITROA_Afiliaciones(OrganizacionPadreID, VigenteDesde, VigenteHasta);
        CREATE INDEX IX_ARBITROA_Afiliaciones_Afiliada_Vigencia
            ON dbo.ARBITROA_Afiliaciones(OrganizacionAfiliadaID, VigenteDesde, VigenteHasta);
    END;

    /* =========================================================
       4. ARBITROA_OrganizacionPersonas
       ========================================================= */
    IF OBJECT_ID(N'dbo.ARBITROA_OrganizacionPersonas', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.ARBITROA_OrganizacionPersonas (
            OrganizacionPersonaID BIGINT IDENTITY(1,1) NOT NULL
                CONSTRAINT PK_ARBITROA_OrganizacionPersonas PRIMARY KEY,
            OrganizacionID BIGINT NOT NULL,
            PersonaID BIGINT NOT NULL,
            RolDominio VARCHAR(40) NOT NULL,
            VigenteDesde DATE NULL,
            VigenteHasta DATE NULL,
            Activo BIT NOT NULL
                CONSTRAINT DF_ARBITROA_OrganizacionPersonas_Activo DEFAULT (1),
            UsuarioAltaID INT NULL,
            FechaAltaUTC DATETIME2(0) NOT NULL
                CONSTRAINT DF_ARBITROA_OrganizacionPersonas_FechaAltaUTC DEFAULT SYSUTCDATETIME(),
            UsuarioActualizacionID INT NULL,
            FechaActualizacionUTC DATETIME2(0) NULL,
            CONSTRAINT CK_ARBITROA_OrganizacionPersonas_Vigencia CHECK (
                VigenteHasta IS NULL OR VigenteDesde IS NULL OR VigenteHasta >= VigenteDesde
            ),
            CONSTRAINT FK_ARBITROA_OrganizacionPersonas_Organizacion
                FOREIGN KEY (OrganizacionID) REFERENCES dbo.ARBITROA_Organizaciones(OrganizacionID),
            CONSTRAINT FK_ARBITROA_OrganizacionPersonas_Persona
                FOREIGN KEY (PersonaID) REFERENCES dbo.Gobierno_Persona(PersonaID),
            CONSTRAINT FK_ARBITROA_OrganizacionPersonas_UsuarioAlta
                FOREIGN KEY (UsuarioAltaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
            CONSTRAINT FK_ARBITROA_OrganizacionPersonas_UsuarioActualizacion
                FOREIGN KEY (UsuarioActualizacionID) REFERENCES dbo.Usuario_Catalogo(UsuarioID)
        );

        CREATE UNIQUE INDEX UX_ARBITROA_OrganizacionPersonas_Activo
            ON dbo.ARBITROA_OrganizacionPersonas(OrganizacionID, PersonaID, RolDominio)
            WHERE Activo = 1;
        CREATE INDEX IX_ARBITROA_OrganizacionPersonas_Persona
            ON dbo.ARBITROA_OrganizacionPersonas(PersonaID, Activo);
    END;

    /* =========================================================
       5. ARBITROA_Sedes
       ========================================================= */
    IF OBJECT_ID(N'dbo.ARBITROA_Sedes', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.ARBITROA_Sedes (
            SedeID BIGINT IDENTITY(1,1) NOT NULL
                CONSTRAINT PK_ARBITROA_Sedes PRIMARY KEY,
            PublicUUID UNIQUEIDENTIFIER NOT NULL
                CONSTRAINT DF_ARBITROA_Sedes_PublicUUID DEFAULT NEWSEQUENTIALID(),
            OrganizacionPropietariaID BIGINT NULL,
            ClienteID INT NULL,
            Nombre NVARCHAR(200) NOT NULL,
            DireccionTexto NVARCHAR(500) NULL,
            Latitud DECIMAL(9,6) NULL,
            Longitud DECIMAL(9,6) NULL,
            ZonaHorariaIANA VARCHAR(64) NOT NULL,
            EstadoOperativo VARCHAR(30) NULL,
            Activo BIT NOT NULL
                CONSTRAINT DF_ARBITROA_Sedes_Activo DEFAULT (1),
            UsuarioAltaID INT NULL,
            FechaAltaUTC DATETIME2(0) NOT NULL
                CONSTRAINT DF_ARBITROA_Sedes_FechaAltaUTC DEFAULT SYSUTCDATETIME(),
            UsuarioActualizacionID INT NULL,
            FechaActualizacionUTC DATETIME2(0) NULL,
            CONSTRAINT UQ_ARBITROA_Sedes_PublicUUID UNIQUE (PublicUUID),
            CONSTRAINT CK_ARBITROA_Sedes_Latitud CHECK (
                Latitud IS NULL OR (Latitud >= -90 AND Latitud <= 90)
            ),
            CONSTRAINT CK_ARBITROA_Sedes_Longitud CHECK (
                Longitud IS NULL OR (Longitud >= -180 AND Longitud <= 180)
            ),
            CONSTRAINT FK_ARBITROA_Sedes_Organizacion
                FOREIGN KEY (OrganizacionPropietariaID) REFERENCES dbo.ARBITROA_Organizaciones(OrganizacionID),
            CONSTRAINT FK_ARBITROA_Sedes_Cliente
                FOREIGN KEY (ClienteID) REFERENCES dbo.Cliente_Catalogo(ClienteID),
            CONSTRAINT FK_ARBITROA_Sedes_UsuarioAlta
                FOREIGN KEY (UsuarioAltaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
            CONSTRAINT FK_ARBITROA_Sedes_UsuarioActualizacion
                FOREIGN KEY (UsuarioActualizacionID) REFERENCES dbo.Usuario_Catalogo(UsuarioID)
        );

        CREATE INDEX IX_ARBITROA_Sedes_Organizacion
            ON dbo.ARBITROA_Sedes(OrganizacionPropietariaID, Activo);
    END;

    /* =========================================================
       6. ARBITROA_Canchas
       ========================================================= */
    IF OBJECT_ID(N'dbo.ARBITROA_Canchas', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.ARBITROA_Canchas (
            CanchaID BIGINT IDENTITY(1,1) NOT NULL
                CONSTRAINT PK_ARBITROA_Canchas PRIMARY KEY,
            SedeID BIGINT NOT NULL,
            Codigo VARCHAR(60) NOT NULL,
            Nombre NVARCHAR(150) NOT NULL,
            TipoSuperficie VARCHAR(50) NULL,
            CapacidadPersonas INT NULL,
            AtributosJSON NVARCHAR(MAX) NULL,
            Activo BIT NOT NULL
                CONSTRAINT DF_ARBITROA_Canchas_Activo DEFAULT (1),
            UsuarioAltaID INT NULL,
            FechaAltaUTC DATETIME2(0) NOT NULL
                CONSTRAINT DF_ARBITROA_Canchas_FechaAltaUTC DEFAULT SYSUTCDATETIME(),
            UsuarioActualizacionID INT NULL,
            FechaActualizacionUTC DATETIME2(0) NULL,
            CONSTRAINT CK_ARBITROA_Canchas_Capacidad CHECK (
                CapacidadPersonas IS NULL OR CapacidadPersonas >= 0
            ),
            CONSTRAINT CK_ARBITROA_Canchas_AtributosJSON CHECK (
                AtributosJSON IS NULL OR ISJSON(AtributosJSON) = 1
            ),
            CONSTRAINT FK_ARBITROA_Canchas_Sede
                FOREIGN KEY (SedeID) REFERENCES dbo.ARBITROA_Sedes(SedeID),
            CONSTRAINT FK_ARBITROA_Canchas_UsuarioAlta
                FOREIGN KEY (UsuarioAltaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
            CONSTRAINT FK_ARBITROA_Canchas_UsuarioActualizacion
                FOREIGN KEY (UsuarioActualizacionID) REFERENCES dbo.Usuario_Catalogo(UsuarioID)
        );

        CREATE UNIQUE INDEX UX_ARBITROA_Canchas_Sede_Codigo
            ON dbo.ARBITROA_Canchas(SedeID, Codigo);
        CREATE INDEX IX_ARBITROA_Canchas_Sede_Activo
            ON dbo.ARBITROA_Canchas(SedeID, Activo);
    END;

    /* =========================================================
       7. ARBITROA_Reglamentos
       ========================================================= */
    IF OBJECT_ID(N'dbo.ARBITROA_Reglamentos', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.ARBITROA_Reglamentos (
            ReglamentoID BIGINT IDENTITY(1,1) NOT NULL
                CONSTRAINT PK_ARBITROA_Reglamentos PRIMARY KEY,
            OrganizacionID BIGINT NULL,
            DeporteID INT NOT NULL,
            Nombre NVARCHAR(200) NOT NULL,
            NumeroVersion VARCHAR(40) NOT NULL,
            VigenteDesde DATE NULL,
            VigenteHasta DATE NULL,
            DocumentoID BIGINT NULL,
            ConfiguracionJSON NVARCHAR(MAX) NULL,
            Estado VARCHAR(20) NOT NULL,
            Activo BIT NOT NULL
                CONSTRAINT DF_ARBITROA_Reglamentos_Activo DEFAULT (1),
            UsuarioAltaID INT NULL,
            FechaAltaUTC DATETIME2(0) NOT NULL
                CONSTRAINT DF_ARBITROA_Reglamentos_FechaAltaUTC DEFAULT SYSUTCDATETIME(),
            UsuarioActualizacionID INT NULL,
            FechaActualizacionUTC DATETIME2(0) NULL,
            CONSTRAINT CK_ARBITROA_Reglamentos_Vigencia CHECK (
                VigenteHasta IS NULL OR VigenteDesde IS NULL OR VigenteHasta >= VigenteDesde
            ),
            CONSTRAINT CK_ARBITROA_Reglamentos_JSON CHECK (
                ConfiguracionJSON IS NULL OR ISJSON(ConfiguracionJSON) = 1
            ),
            CONSTRAINT CK_ARBITROA_Reglamentos_Estado CHECK (
                Estado IN ('BORRADOR','VIGENTE','SUSTITUIDO','INACTIVO')
            ),
            CONSTRAINT FK_ARBITROA_Reglamentos_Organizacion
                FOREIGN KEY (OrganizacionID) REFERENCES dbo.ARBITROA_Organizaciones(OrganizacionID),
            CONSTRAINT FK_ARBITROA_Reglamentos_Deporte
                FOREIGN KEY (DeporteID) REFERENCES dbo.ARBITROA_Deportes(DeporteID),
            CONSTRAINT FK_ARBITROA_Reglamentos_Documento
                FOREIGN KEY (DocumentoID) REFERENCES dbo.Gobierno_Documento(DocumentoID),
            CONSTRAINT FK_ARBITROA_Reglamentos_UsuarioAlta
                FOREIGN KEY (UsuarioAltaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
            CONSTRAINT FK_ARBITROA_Reglamentos_UsuarioActualizacion
                FOREIGN KEY (UsuarioActualizacionID) REFERENCES dbo.Usuario_Catalogo(UsuarioID)
        );

        CREATE UNIQUE INDEX UX_ARBITROA_Reglamentos_Alcance_Version
            ON dbo.ARBITROA_Reglamentos(OrganizacionID, DeporteID, NumeroVersion);
        CREATE INDEX IX_ARBITROA_Reglamentos_Deporte_Vigencia
            ON dbo.ARBITROA_Reglamentos(DeporteID, Estado, VigenteDesde, VigenteHasta);
    END;

    /* =========================================================
       RBAC / MENU BOS - REGISTRO SATELITE
       ========================================================= */
    DECLARE @ModuloID INT;

    IF (SELECT COUNT(*) FROM dbo.Sistema_Modulos WHERE Codigo = N'ARBITROA') > 1
        THROW 52010, 'Colision: multiples Sistema_Modulos con Codigo ARBITROA.', 1;

    SELECT @ModuloID = ModuloID
    FROM dbo.Sistema_Modulos
    WHERE Codigo = N'ARBITROA';

    IF @ModuloID IS NULL
    BEGIN
        DECLARE @OrdenModulo INT;
        SELECT @OrdenModulo = ISNULL(MAX(Orden), 0) + 1
        FROM dbo.Sistema_Modulos WITH (UPDLOCK, HOLDLOCK);

        INSERT INTO dbo.Sistema_Modulos (
            Codigo, Nombre, Descripcion, Icono, Orden,
            EsPrincipal, EsSatelite, EsPortal, URLExterna, Activo, FechaCreacion
        )
        VALUES (
            N'ARBITROA',
            N'ARBITROA',
            N'Operacion deportiva y arbitral multi-organizacion',
            N'BadgeCheck',
            @OrdenModulo,
            0, 1, 0, NULL, 1, GETDATE()
        );

        SET @ModuloID = CONVERT(INT, SCOPE_IDENTITY());
    END
    ELSE
    BEGIN
        IF EXISTS (
            SELECT 1
            FROM dbo.Sistema_Modulos
            WHERE ModuloID = @ModuloID
              AND (
                    ISNULL(EsSatelite, 0) <> 1
                 OR ISNULL(EsPortal, 0) <> 0
              )
        )
            THROW 52011, 'ARBITROA ya existe con contrato de modulo incompatible.', 1;

        UPDATE dbo.Sistema_Modulos
        SET Nombre = N'ARBITROA',
            Descripcion = N'Operacion deportiva y arbitral multi-organizacion',
            Icono = N'BadgeCheck',
            EsPrincipal = 0,
            EsSatelite = 1,
            EsPortal = 0,
            URLExterna = NULL,
            Activo = 1
        WHERE ModuloID = @ModuloID;
    END;

    IF NOT EXISTS (
        SELECT 1 FROM dbo.Sistema_ModulosPermisos
        WHERE ModuloID = @ModuloID AND Codigo = N'arbitroa.ver'
    )
    BEGIN
        INSERT INTO dbo.Sistema_ModulosPermisos
            (ModuloID, Codigo, Nombre, Descripcion, Categoria, Activo, FechaCreacion)
        VALUES
            (@ModuloID, N'arbitroa.ver', N'Ver ARBITROA',
             N'Permite acceder al modulo ARBITROA', N'ARBITROA', 1, GETDATE());
    END;

    IF NOT EXISTS (
        SELECT 1 FROM dbo.Sistema_ModulosPermisos
        WHERE ModuloID = @ModuloID AND Codigo = N'arbitroa.administrar'
    )
    BEGIN
        INSERT INTO dbo.Sistema_ModulosPermisos
            (ModuloID, Codigo, Nombre, Descripcion, Categoria, Activo, FechaCreacion)
        VALUES
            (@ModuloID, N'arbitroa.administrar', N'Administrar ARBITROA',
             N'Permite administrar la fundacion operativa ARBITROA', N'ARBITROA', 1, GETDATE());
    END;

    IF (
        SELECT COUNT(*)
        FROM dbo.Sistema_ModulosMenus
        WHERE Codigo = N'arbitroa.inicio' OR Ruta = N'/arbitroa'
    ) > 1
        THROW 52012, 'Colision: multiples menus ARBITROA.', 1;

    DECLARE @MenuID INT;
    SELECT TOP (1) @MenuID = MenuID
    FROM dbo.Sistema_ModulosMenus
    WHERE Codigo = N'arbitroa.inicio' OR Ruta = N'/arbitroa'
    ORDER BY MenuID;

    IF @MenuID IS NULL
    BEGIN
        INSERT INTO dbo.Sistema_ModulosMenus (
            ModuloID, MenuPadreID, Codigo, Nombre, Descripcion, Icono,
            Ruta, Orden, RequierePermiso, Activo, FechaCreacion
        )
        SELECT
            @ModuloID, NULL, N'arbitroa.inicio', N'ARBITROA',
            N'Gestion deportiva y arbitral', N'BadgeCheck',
            N'/arbitroa', ISNULL(MAX(Orden), 0) + 1,
            N'ARBITROA', 1, GETDATE()
        FROM dbo.Sistema_ModulosMenus
        WHERE ModuloID = @ModuloID;
    END
    ELSE
    BEGIN
        UPDATE dbo.Sistema_ModulosMenus
        SET ModuloID = @ModuloID,
            MenuPadreID = NULL,
            Codigo = N'arbitroa.inicio',
            Nombre = N'ARBITROA',
            Descripcion = N'Gestion deportiva y arbitral',
            Icono = N'BadgeCheck',
            Ruta = N'/arbitroa',
            RequierePermiso = N'ARBITROA',
            Activo = 1
        WHERE MenuID = @MenuID;
    END;

    COMMIT TRANSACTION;

    SELECT
        N'ARBITROA_A4_FOUNDATION_READY' AS resultado,
        @ModuloID AS sistema_modulo_id;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
