SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> 'EDARSAHUB'
    THROW 54200, 'Base inesperada.', 1;

IF SUSER_SNAME() <> 'HRLectura'
    THROW 54201, 'Login inesperado.', 1;

IF USER_NAME() <> 'HRLectura'
    THROW 54202, 'Usuario inesperado.', 1;

BEGIN TRY
    BEGIN TRANSACTION;

    IF COL_LENGTH(
        'dbo.Compras_Pedidos',
        'unidad_negocio_pk'
    ) IS NOT NULL
        THROW 54203, 'Compras_Pedidos.unidad_negocio_pk ya existe.', 1;

    IF COL_LENGTH(
        'dbo.Compras_Ordenes',
        'unidad_negocio_pk'
    ) IS NOT NULL
        THROW 54204, 'Compras_Ordenes.unidad_negocio_pk ya existe.', 1;

    IF COL_LENGTH(
        'dbo.Compras_Recepciones',
        'unidad_negocio_pk'
    ) IS NOT NULL
        THROW 54205, 'Compras_Recepciones.unidad_negocio_pk ya existe.', 1;


    -- =====================================================
    -- 1. CREAR COLUMNAS
    -- =====================================================

    ALTER TABLE dbo.Compras_Pedidos
        ADD unidad_negocio_pk uniqueidentifier NULL;

    ALTER TABLE dbo.Compras_Ordenes
        ADD unidad_negocio_pk uniqueidentifier NULL;

    ALTER TABLE dbo.Compras_Recepciones
        ADD unidad_negocio_pk uniqueidentifier NULL;


    -- =====================================================
    -- 2. PEDIDOS
    -- Empresa -> sucursal activa -> mapping -> unidad UUID
    --
    -- SQL dinamico evita compilacion prematura de la
    -- columna agregada en este mismo batch.
    -- =====================================================

    EXEC sys.sp_executesql N'
        UPDATE p
           SET unidad_negocio_pk=u.id
        FROM dbo.Compras_Pedidos p
        JOIN dbo.Sistema_Sucursales s
          ON s.EmpresaID=p.EmpresaID
         AND ISNULL(s.Activo,0)=1
        JOIN dbo.Sistema_SucursalServidorMapeo m
          ON m.SucursalID=s.SucursalID
         AND ISNULL(m.Activo,0)=1
        JOIN dbo.Unidades_Negocio u
          ON LOWER(CONVERT(nvarchar(100),u.server_id))
             =
             LOWER(CONVERT(nvarchar(100),m.ServidorID))
         AND (
                NULLIF(
                    LTRIM(RTRIM(CONVERT(
                        nvarchar(50),
                        u.sucursal_origen_id
                    ))),
                    ''''
                )
                =
                NULLIF(
                    LTRIM(RTRIM(CONVERT(
                        nvarchar(50),
                        m.SucursalOrigenID
                    ))),
                    ''''
                )
                OR (
                    NULLIF(
                        LTRIM(RTRIM(CONVERT(
                            nvarchar(50),
                            u.sucursal_origen_id
                        ))),
                        ''''
                    ) IS NULL
                    AND
                    NULLIF(
                        LTRIM(RTRIM(CONVERT(
                            nvarchar(50),
                            m.SucursalOrigenID
                        ))),
                        ''''
                    ) IS NULL
                )
             )
         AND ISNULL(u.activo,1)=1;
    ';


    -- =====================================================
    -- 3. ORDENES
    -- Empresa -> sucursal activa -> mapping -> unidad UUID
    -- =====================================================

    EXEC sys.sp_executesql N'
        UPDATE o
           SET unidad_negocio_pk=u.id
        FROM dbo.Compras_Ordenes o
        JOIN dbo.Sistema_Sucursales s
          ON s.EmpresaID=o.EmpresaID
         AND ISNULL(s.Activo,0)=1
        JOIN dbo.Sistema_SucursalServidorMapeo m
          ON m.SucursalID=s.SucursalID
         AND ISNULL(m.Activo,0)=1
        JOIN dbo.Unidades_Negocio u
          ON LOWER(CONVERT(nvarchar(100),u.server_id))
             =
             LOWER(CONVERT(nvarchar(100),m.ServidorID))
         AND (
                NULLIF(
                    LTRIM(RTRIM(CONVERT(
                        nvarchar(50),
                        u.sucursal_origen_id
                    ))),
                    ''''
                )
                =
                NULLIF(
                    LTRIM(RTRIM(CONVERT(
                        nvarchar(50),
                        m.SucursalOrigenID
                    ))),
                    ''''
                )
                OR (
                    NULLIF(
                        LTRIM(RTRIM(CONVERT(
                            nvarchar(50),
                            u.sucursal_origen_id
                        ))),
                        ''''
                    ) IS NULL
                    AND
                    NULLIF(
                        LTRIM(RTRIM(CONVERT(
                            nvarchar(50),
                            m.SucursalOrigenID
                        ))),
                        ''''
                    ) IS NULL
                )
             )
         AND ISNULL(u.activo,1)=1;
    ';


    -- =====================================================
    -- 4. RECEPCIONES
    -- Almacen -> sucursal -> mapping -> unidad UUID
    -- EmpresaID NO decide identidad.
    -- =====================================================

    EXEC sys.sp_executesql N'
        UPDATE r
           SET unidad_negocio_pk=u.id
        FROM dbo.Compras_Recepciones r
        JOIN dbo.Inventario_Almacenes a
          ON a.AlmacenID=r.AlmacenID
        JOIN dbo.Sistema_SucursalServidorMapeo m
          ON m.SucursalID=a.SucursalID
         AND ISNULL(m.Activo,0)=1
        JOIN dbo.Unidades_Negocio u
          ON LOWER(CONVERT(nvarchar(100),u.server_id))
             =
             LOWER(CONVERT(nvarchar(100),m.ServidorID))
         AND (
                NULLIF(
                    LTRIM(RTRIM(CONVERT(
                        nvarchar(50),
                        u.sucursal_origen_id
                    ))),
                    ''''
                )
                =
                NULLIF(
                    LTRIM(RTRIM(CONVERT(
                        nvarchar(50),
                        m.SucursalOrigenID
                    ))),
                    ''''
                )
                OR (
                    NULLIF(
                        LTRIM(RTRIM(CONVERT(
                            nvarchar(50),
                            u.sucursal_origen_id
                        ))),
                        ''''
                    ) IS NULL
                    AND
                    NULLIF(
                        LTRIM(RTRIM(CONVERT(
                            nvarchar(50),
                            m.SucursalOrigenID
                        ))),
                        ''''
                    ) IS NULL
                )
             )
         AND ISNULL(u.activo,1)=1;
    ';


    -- =====================================================
    -- 5. FAIL CLOSED
    -- Tambien dinamico por ser columna nueva.
    -- =====================================================

    EXEC sys.sp_executesql N'
        IF EXISTS (
            SELECT 1
            FROM dbo.Compras_Pedidos
            WHERE unidad_negocio_pk IS NULL
        )
            THROW 54206, ''Pedidos sin unidad UUID.'', 1;

        IF EXISTS (
            SELECT 1
            FROM dbo.Compras_Ordenes
            WHERE unidad_negocio_pk IS NULL
        )
            THROW 54207, ''Ordenes sin unidad UUID.'', 1;

        IF EXISTS (
            SELECT 1
            FROM dbo.Compras_Recepciones
            WHERE unidad_negocio_pk IS NULL
        )
            THROW 54208, ''Recepciones sin unidad UUID.'', 1;
    ';


    -- =====================================================
    -- 6. NOT NULL
    -- Ejecutado dinamicamente para resolver columna nueva.
    -- =====================================================

    EXEC sys.sp_executesql N'
        ALTER TABLE dbo.Compras_Pedidos
        ALTER COLUMN unidad_negocio_pk
            uniqueidentifier NOT NULL;
    ';

    EXEC sys.sp_executesql N'
        ALTER TABLE dbo.Compras_Ordenes
        ALTER COLUMN unidad_negocio_pk
            uniqueidentifier NOT NULL;
    ';

    EXEC sys.sp_executesql N'
        ALTER TABLE dbo.Compras_Recepciones
        ALTER COLUMN unidad_negocio_pk
            uniqueidentifier NOT NULL;
    ';


    -- =====================================================
    -- 7. FK CANONICAS
    -- =====================================================

    EXEC sys.sp_executesql N'
        ALTER TABLE dbo.Compras_Pedidos
        ADD CONSTRAINT FK_Compras_Pedidos_UnidadNegocio
            FOREIGN KEY (unidad_negocio_pk)
            REFERENCES dbo.Unidades_Negocio(id);
    ';

    EXEC sys.sp_executesql N'
        ALTER TABLE dbo.Compras_Ordenes
        ADD CONSTRAINT FK_Compras_Ordenes_UnidadNegocio
            FOREIGN KEY (unidad_negocio_pk)
            REFERENCES dbo.Unidades_Negocio(id);
    ';

    EXEC sys.sp_executesql N'
        ALTER TABLE dbo.Compras_Recepciones
        ADD CONSTRAINT FK_Compras_Recepciones_UnidadNegocio
            FOREIGN KEY (unidad_negocio_pk)
            REFERENCES dbo.Unidades_Negocio(id);
    ';


    -- =====================================================
    -- 8. INDICES
    -- =====================================================

    EXEC sys.sp_executesql N'
        CREATE INDEX IX_Compras_Pedidos_UnidadNegocio
        ON dbo.Compras_Pedidos(unidad_negocio_pk);
    ';

    EXEC sys.sp_executesql N'
        CREATE INDEX IX_Compras_Ordenes_UnidadNegocio
        ON dbo.Compras_Ordenes(unidad_negocio_pk);
    ';

    EXEC sys.sp_executesql N'
        CREATE INDEX IX_Compras_Recepciones_UnidadNegocio
        ON dbo.Compras_Recepciones(unidad_negocio_pk);
    ';


    COMMIT TRANSACTION;

    SELECT
        'MIGRATION_026_OK' AS Estado;

END TRY
BEGIN CATCH

    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;

    THROW;

END CATCH;
