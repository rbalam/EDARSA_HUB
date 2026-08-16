SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    /*
        EDARSAHUB
        Configuracion canonica Costos y Margenes / Pricing.

        Reglas:
        - sin defaults funcionales silenciosos;
        - Empresa es nivel base;
        - Unidad de Negocio puede especializar la configuracion de Empresa;
        - margen persistido en porcentaje 0..100;
        - redondeo configurable;
        - usuario separado de configuracion de negocio;
        - no reemplaza Comercial_AlertasMargenReglas;
        - no reemplaza Comercial_ReglasPrecio legacy de vinos;
        - no usa MongoDB;
        - no usa mocks/hardcodes.
    */

    IF OBJECT_ID(
        'dbo.Comercial_CostosMargenesConfiguracion',
        'U'
    ) IS NULL
    BEGIN
        CREATE TABLE dbo.Comercial_CostosMargenesConfiguracion
        (
            ConfiguracionID uniqueidentifier
                NOT NULL
                CONSTRAINT DF_CostosMargenesConfig_ID
                DEFAULT NEWID(),

            EmpresaID int
                NOT NULL,

            UnidadNegocioID uniqueidentifier
                NULL,

            MargenMinimoPorcentaje decimal(5,2)
                NULL,

            MultiploRedondeo decimal(18,4)
                NULL,

            MetodoRedondeo varchar(30)
                NULL,

            Activo bit
                NOT NULL
                CONSTRAINT DF_CostosMargenesConfig_Activo
                DEFAULT (1),

            FechaCreacion datetime2(7)
                NOT NULL
                CONSTRAINT DF_CostosMargenesConfig_FechaCreacion
                DEFAULT SYSDATETIME(),

            FechaModificacion datetime2(7)
                NULL,

            UsuarioCreacionID int
                NULL,

            UsuarioModificacionID int
                NULL,

            CONSTRAINT PK_Comercial_CostosMargenesConfiguracion
                PRIMARY KEY (ConfiguracionID),

            CONSTRAINT FK_CostosMargenesConfig_Empresa
                FOREIGN KEY (EmpresaID)
                REFERENCES dbo.Sistema_Empresas(EmpresaID),


            CONSTRAINT FK_CostosMargenesConfig_Unidad
                FOREIGN KEY (UnidadNegocioID)
                REFERENCES dbo.Unidades_Negocio(id),

            CONSTRAINT FK_CostosMargenesConfig_UsuarioCreacion
                FOREIGN KEY (UsuarioCreacionID)
                REFERENCES dbo.Usuario_Catalogo(UsuarioID),

            CONSTRAINT FK_CostosMargenesConfig_UsuarioModificacion
                FOREIGN KEY (UsuarioModificacionID)
                REFERENCES dbo.Usuario_Catalogo(UsuarioID),

            CONSTRAINT CK_CostosMargenesConfig_Margen
                CHECK (
                    MargenMinimoPorcentaje IS NULL
                    OR (
                        MargenMinimoPorcentaje > 0
                        AND MargenMinimoPorcentaje < 100
                    )
                ),

            CONSTRAINT CK_CostosMargenesConfig_Multiplo
                CHECK (
                    MultiploRedondeo IS NULL
                    OR MultiploRedondeo > 0
                ),

            CONSTRAINT CK_CostosMargenesConfig_Metodo
                CHECK (
                    MetodoRedondeo IS NULL
                    OR MetodoRedondeo IN (
                        'MAS_CERCANO',
                        'HACIA_ARRIBA',
                        'HACIA_ABAJO'
                    )
                )
        );

        /*
            Una sola configuracion activa por alcance organizacional.

            NULL no se sustituye por valores artificiales.
            Los NULL representan herencia desde un nivel superior.
        */
        /*
            Unicidad por nivel de alcance.

            Se separan los tres casos para evitar ambiguedad
            semantica con NULL en claves compuestas:
            - Empresa
            - Empresa + Unidad de Negocio
            - Empresa + Unidad
        */

        CREATE UNIQUE INDEX UX_CostosMargenesConfig_Empresa
        ON dbo.Comercial_CostosMargenesConfiguracion
        (
            EmpresaID
        )
        WHERE
            Activo = 1
            AND UnidadNegocioID IS NULL;


        CREATE UNIQUE INDEX UX_CostosMargenesConfig_Unidad
        ON dbo.Comercial_CostosMargenesConfiguracion
        (
            EmpresaID,
            UnidadNegocioID
        )
        WHERE
            Activo = 1
            AND UnidadNegocioID IS NOT NULL;

        CREATE INDEX IX_CostosMargenesConfig_Empresa
        ON dbo.Comercial_CostosMargenesConfiguracion
        (
            EmpresaID,
            Activo
        );


        CREATE INDEX IX_CostosMargenesConfig_Unidad
        ON dbo.Comercial_CostosMargenesConfiguracion
        (
            UnidadNegocioID,
            Activo
        )
        WHERE UnidadNegocioID IS NOT NULL;
    END;

    /*
        Override personal.

        No contiene valores por default.
        Si una columna es NULL, el resolver continúa hacia
        configuración de negocio.
    */
    IF OBJECT_ID(
        'dbo.Comercial_CostosMargenesConfiguracionUsuario',
        'U'
    ) IS NULL
    BEGIN
        CREATE TABLE dbo.Comercial_CostosMargenesConfiguracionUsuario
        (
            ConfiguracionUsuarioID bigint
                IDENTITY(1,1)
                NOT NULL,

            UsuarioID int
                NOT NULL,

            MargenMinimoPorcentaje decimal(5,2)
                NULL,

            MultiploRedondeo decimal(18,4)
                NULL,

            MetodoRedondeo varchar(30)
                NULL,

            Activo bit
                NOT NULL
                CONSTRAINT DF_CostosMargenesConfigUsuario_Activo
                DEFAULT (1),

            FechaCreacion datetime2(7)
                NOT NULL
                CONSTRAINT DF_CostosMargenesConfigUsuario_FechaCreacion
                DEFAULT SYSDATETIME(),

            FechaModificacion datetime2(7)
                NULL,

            CONSTRAINT PK_Comercial_CostosMargenesConfiguracionUsuario
                PRIMARY KEY (ConfiguracionUsuarioID),

            CONSTRAINT FK_CostosMargenesConfigUsuario_Usuario
                FOREIGN KEY (UsuarioID)
                REFERENCES dbo.Usuario_Catalogo(UsuarioID),

            CONSTRAINT CK_CostosMargenesConfigUsuario_Margen
                CHECK (
                    MargenMinimoPorcentaje IS NULL
                    OR (
                        MargenMinimoPorcentaje > 0
                        AND MargenMinimoPorcentaje < 100
                    )
                ),

            CONSTRAINT CK_CostosMargenesConfigUsuario_Multiplo
                CHECK (
                    MultiploRedondeo IS NULL
                    OR MultiploRedondeo > 0
                ),

            CONSTRAINT CK_CostosMargenesConfigUsuario_Metodo
                CHECK (
                    MetodoRedondeo IS NULL
                    OR MetodoRedondeo IN (
                        'MAS_CERCANO',
                        'HACIA_ARRIBA',
                        'HACIA_ABAJO'
                    )
                )
        );

        CREATE UNIQUE INDEX UX_CostosMargenesConfigUsuario_Activo
        ON dbo.Comercial_CostosMargenesConfiguracionUsuario
        (
            UsuarioID
        )
        WHERE Activo = 1;
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
