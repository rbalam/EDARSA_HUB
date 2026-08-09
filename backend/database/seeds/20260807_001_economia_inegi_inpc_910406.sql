SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    /* ================================================================
       EDARSAHUB Economia WorldClass
       Seed inicial controlado:
       - Pais: Mexico
       - Categoria: Inflacion
       - Proveedor: INEGI
       - Serie: INPC inflacion anual / INEGI 910406

       IMPORTANTE:
       - No contiene secretos.
       - No crea Servidores_Conexiones.
       - No activa proveedor ni serie.
       - Scheduler Economia permanece independiente y fail-closed.
       ================================================================ */

    DECLARE @PaisID int;
    DECLARE @CategoriaID int;
    DECLARE @ProveedorID int;
    DECLARE @MonedaID smallint;

    /* ------------------------------------------------
       1. Moneda canónica existente
       ------------------------------------------------ */

    SELECT @MonedaID = MonedaID
    FROM dbo.Proveedor_Monedas
    WHERE ClaveMoneda = 'MXN'
      AND Activo = 1;

    IF @MonedaID IS NULL
        THROW 51000, 'No existe moneda canonica MXN activa', 1;

    /* ------------------------------------------------
       2. País México
       ISO 3166: MX / MEX / 484
       ------------------------------------------------ */

    SELECT @PaisID = PaisID
    FROM dbo.Economia_Paises
    WHERE CodigoISO2 = 'MX';

    IF @PaisID IS NULL
    BEGIN
        INSERT INTO dbo.Economia_Paises
        (
            CodigoISO2,
            CodigoISO3,
            CodigoNumericoISO,
            Nombre,
            NombreOficial,
            MonedaID,
            RegionCodigo,
            SubregionCodigo,
            Activo
        )
        VALUES
        (
            'MX',
            'MEX',
            '484',
            N'México',
            N'Estados Unidos Mexicanos',
            @MonedaID,
            N'AMERICAS',
            N'LATIN_AMERICA_CARIBBEAN',
            1
        );

        SET @PaisID = CONVERT(int, SCOPE_IDENTITY());
    END;

    /* ------------------------------------------------
       3. Categoría Inflación
       ------------------------------------------------ */

    SELECT @CategoriaID = CategoriaIndicadorID
    FROM dbo.Economia_CategoriasIndicador
    WHERE Codigo = N'INFLACION';

    IF @CategoriaID IS NULL
    BEGIN
        INSERT INTO dbo.Economia_CategoriasIndicador
        (
            Codigo,
            Nombre,
            Descripcion,
            CategoriaPadreID,
            OrdenVisual,
            Activo
        )
        VALUES
        (
            N'INFLACION',
            N'Inflación',
            N'Indicadores de inflación y variaciones de precios.',
            NULL,
            10,
            1
        );

        SET @CategoriaID = CONVERT(int, SCOPE_IDENTITY());
    END;

    /* ------------------------------------------------
       4. Proveedor INEGI
       Fail-closed: Activo = 0 hasta configurar conexión.
       ------------------------------------------------ */

    SELECT @ProveedorID = ProveedorEconomicoID
    FROM dbo.Economia_Proveedores
    WHERE Codigo = N'INEGI';

    IF @ProveedorID IS NULL
    BEGIN
        INSERT INTO dbo.Economia_Proveedores
        (
            Codigo,
            Nombre,
            TipoProveedor,
            PaisID,
            ServerConexionID,
            UrlPublica,
            DocumentacionURL,
            RequiereAutenticacion,
            PermiteBackfill,
            Activo
        )
        VALUES
        (
            N'INEGI',
            N'Instituto Nacional de Estadística y Geografía',
            N'API_OFICIAL',
            @PaisID,
            NULL,
            N'https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml',
            N'https://www.inegi.org.mx/servicios/api_indicadores.html',
            1,
            1,
            0
        );

        SET @ProveedorID = CONVERT(int, SCOPE_IDENTITY());
    END;

    /* ------------------------------------------------
       5. Serie INPC inflación anual
       Serie oficial INEGI: 910406

       Fail-closed: Activo = 0.
       El token deberá resolverse posteriormente desde
       dbo.Servidores_Conexiones.
       ------------------------------------------------ */

    IF NOT EXISTS
    (
        SELECT 1
        FROM dbo.Economia_Series
        WHERE CodigoCanonico = N'MX.INPC.INFLACION_ANUAL'
    )
    BEGIN
        INSERT INTO dbo.Economia_Series
        (
            CodigoCanonico,
            CodigoProveedor,
            Nombre,
            Descripcion,
            CategoriaIndicadorID,
            ProveedorEconomicoID,
            PaisID,
            MonedaID,
            FrecuenciaCodigo,
            UnidadMedidaCodigo,
            TipoValorCodigo,
            Escala,
            EsPorcentaje,
            EsIndice,
            EsTipoCambio,
            MonedaBaseID,
            MonedaCotizadaID,
            SeriePadreID,
            PermiteRevision,
            MetadataJSON,
            Activo
        )
        VALUES
        (
            N'MX.INPC.INFLACION_ANUAL',
            N'910406',
            N'INPC - Inflación anual',
            N'Índice Nacional de Precios al Consumidor. Inflación anual.',
            @CategoriaID,
            @ProveedorID,
            @PaisID,
            @MonedaID,
            N'MENSUAL',
            N'PORCENTAJE',
            N'VARIACION_INTERANUAL',
            1,
            1,
            0,
            0,
            NULL,
            NULL,
            NULL,
            1,
            N'{
              "base_url":"https://www.inegi.org.mx",
              "endpoint":"servicios/xml/INPCA_M_O_H.xml",
              "requires_auth":false,
              "response_format":"xml",
              "timeout_seconds":30,
              "normalizacion":{
                "items_path":"DATASET.SERIE.Obs",
                "fecha_field":"@TimePeriod",
                "valor_field":"@CurrentValue",
                "fecha_format":"%Y/%m"
              }
            }',
            0
        );
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
