SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @CodigoCanonico nvarchar(150)
        = N'MX.INPC.INFLACION_ANUAL';

    DECLARE @ProveedorCodigo nvarchar(80)
        = N'INEGI';

    DECLARE @SerieID bigint;
    DECLARE @ProveedorID int;
    DECLARE @ConexionID uniqueidentifier;
    DECLARE @MetadataActual nvarchar(max);
    DECLARE @SerieActiva bit;
    DECLARE @ProveedorActivo bit;
    DECLARE @ConexionActiva bit;

    DECLARE @MetadataNueva nvarchar(max) = N'{
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
    }';

    /* ============================================================
       1. Guardrails estructurales
       ============================================================ */

    IF OBJECT_ID(N'dbo.Economia_Series', N'U') IS NULL
        THROW 51000, 'Economia_Series no existe', 1;

    IF OBJECT_ID(N'dbo.Economia_Proveedores', N'U') IS NULL
        THROW 51000, 'Economia_Proveedores no existe', 1;

    IF OBJECT_ID(N'dbo.Economia_Valores', N'U') IS NULL
        THROW 51000, 'Economia_Valores no existe', 1;

    IF OBJECT_ID(N'dbo.Servidores_Conexiones', N'U') IS NULL
        THROW 51000, 'Servidores_Conexiones no existe', 1;

    IF ISJSON(@MetadataNueva) <> 1
        THROW 51000, 'Metadata nueva invalida', 1;

    /* ============================================================
       2. Resolver objetivo por clave canonica, nunca por ID fijo
       ============================================================ */

    IF
    (
        SELECT COUNT_BIG(*)
        FROM dbo.Economia_Series s
        INNER JOIN dbo.Economia_Proveedores p
            ON p.ProveedorEconomicoID = s.ProveedorEconomicoID
        WHERE s.CodigoCanonico = @CodigoCanonico
          AND p.Codigo = @ProveedorCodigo
    ) <> 1
        THROW 51000, 'Serie INEGI objetivo no es unica', 1;

    SELECT
        @SerieID = s.SerieEconomicaID,
        @ProveedorID = p.ProveedorEconomicoID,
        @ConexionID = p.ServerConexionID,
        @MetadataActual = s.MetadataJSON,
        @SerieActiva = s.Activo,
        @ProveedorActivo = p.Activo,
        @ConexionActiva = sc.activo
    FROM dbo.Economia_Series s
    INNER JOIN dbo.Economia_Proveedores p
        ON p.ProveedorEconomicoID = s.ProveedorEconomicoID
    LEFT JOIN dbo.Servidores_Conexiones sc
        ON sc.id = p.ServerConexionID
    WHERE s.CodigoCanonico = @CodigoCanonico
      AND p.Codigo = @ProveedorCodigo;

    IF @SerieID IS NULL
        THROW 51000, 'Serie INEGI no resuelta', 1;

    /* ============================================================
       3. Fail closed
       ============================================================ */

    IF @SerieActiva <> 0
        THROW 51000, 'Serie INEGI debe permanecer inactiva', 1;

    IF @ProveedorActivo <> 0
        THROW 51000, 'Proveedor INEGI debe permanecer inactivo', 1;

    IF @ConexionID IS NULL
        THROW 51000, 'Conexion INEGI no configurada', 1;

    IF ISNULL(@ConexionActiva, 0) <> 0
        THROW 51000, 'Conexion INEGI debe permanecer inactiva', 1;

    /*
       Auditoria previa cerrada:
       actualmente no existen valores para esta serie.
       Abortamos si el estado cambio antes de aplicar la migracion.
    */
    IF EXISTS
    (
        SELECT 1
        FROM dbo.Economia_Valores
        WHERE SerieEconomicaID = @SerieID
    )
        THROW 51000, 'Serie INEGI ya contiene valores; requiere nueva auditoria', 1;

    IF @MetadataActual IS NULL
       OR ISJSON(@MetadataActual) <> 1
        THROW 51000, 'Metadata actual invalida', 1;

    /* ============================================================
       4. Idempotencia: si ya esta migrada, no hacer nada
       ============================================================ */

    IF
        JSON_VALUE(@MetadataActual, '$.base_url')
            = N'https://www.inegi.org.mx'
        AND JSON_VALUE(@MetadataActual, '$.endpoint')
            = N'servicios/xml/INPCA_M_O_H.xml'
        AND JSON_VALUE(@MetadataActual, '$.requires_auth')
            = N'false'
        AND JSON_VALUE(@MetadataActual, '$.response_format')
            = N'xml'
        AND JSON_VALUE(
                @MetadataActual,
                '$.normalizacion.items_path'
            ) = N'DATASET.SERIE.Obs'
        AND JSON_VALUE(
                @MetadataActual,
                '$.normalizacion.fecha_field'
            ) = N'@TimePeriod'
        AND JSON_VALUE(
                @MetadataActual,
                '$.normalizacion.valor_field'
            ) = N'@CurrentValue'
        AND JSON_VALUE(
                @MetadataActual,
                '$.normalizacion.fecha_format'
            ) = N'%Y/%m'
    BEGIN
        COMMIT TRANSACTION;
        RETURN;
    END;

    /* ============================================================
       5. Exigir exactamente el contrato antiguo auditado
       ============================================================ */

    IF JSON_VALUE(@MetadataActual, '$.endpoint')
        <> N'INDICATOR/{codigo}/es/00/false/BISE/2.0/{token}'
        THROW 51000, 'Endpoint anterior no coincide', 1;

    IF JSON_VALUE(@MetadataActual, '$.params.type')
        <> N'json'
        THROW 51000, 'Parametro anterior type no coincide', 1;

    IF JSON_VALUE(@MetadataActual, '$.auth.placement')
        <> N'path'
        THROW 51000, 'Auth anterior placement no coincide', 1;

    IF JSON_VALUE(@MetadataActual, '$.auth.placeholder')
        <> N'token'
        THROW 51000, 'Auth anterior placeholder no coincide', 1;

    IF TRY_CONVERT(
        int,
        JSON_VALUE(@MetadataActual, '$.timeout_seconds')
    ) <> 30
        THROW 51000, 'Timeout anterior no coincide', 1;

    IF JSON_VALUE(
        @MetadataActual,
        '$.normalizacion.items_path'
    ) <> N'Series.0.OBSERVATIONS'
        THROW 51000, 'items_path anterior no coincide', 1;

    IF JSON_VALUE(
        @MetadataActual,
        '$.normalizacion.fecha_field'
    ) <> N'TIME_PERIOD'
        THROW 51000, 'fecha_field anterior no coincide', 1;

    IF JSON_VALUE(
        @MetadataActual,
        '$.normalizacion.valor_field'
    ) <> N'OBS_VALUE'
        THROW 51000, 'valor_field anterior no coincide', 1;

    IF JSON_VALUE(
        @MetadataActual,
        '$.normalizacion.fecha_format'
    ) <> N'%Y/%m'
        THROW 51000, 'fecha_format anterior no coincide', 1;

    IF JSON_VALUE(
        @MetadataActual,
        '$.normalizacion.fuente_id_field'
    ) <> N'OBS_SOURCE'
        THROW 51000, 'fuente_id_field anterior no coincide', 1;

    /* ============================================================
       6. Cambio unico y quirurgico
       ============================================================ */

    UPDATE dbo.Economia_Series
    SET
        MetadataJSON = @MetadataNueva,
        FechaModificacionUTC = SYSUTCDATETIME()
    WHERE SerieEconomicaID = @SerieID
      AND CodigoCanonico = @CodigoCanonico
      AND Activo = 0;

    IF @@ROWCOUNT <> 1
        THROW 51000, 'UPDATE no afecto exactamente una serie', 1;

    /* ============================================================
       7. Postcondiciones
       ============================================================ */

    SELECT
        @MetadataActual = MetadataJSON
    FROM dbo.Economia_Series
    WHERE SerieEconomicaID = @SerieID;

    IF ISJSON(@MetadataActual) <> 1
        THROW 51000, 'Metadata final invalida', 1;

    IF JSON_VALUE(@MetadataActual, '$.endpoint')
        <> N'servicios/xml/INPCA_M_O_H.xml'
        THROW 51000, 'Endpoint final invalido', 1;

    IF JSON_VALUE(@MetadataActual, '$.requires_auth')
        <> N'false'
        THROW 51000, 'Auth final invalido', 1;

    IF JSON_VALUE(@MetadataActual, '$.response_format')
        <> N'xml'
        THROW 51000, 'Formato final invalido', 1;

    IF EXISTS
    (
        SELECT 1
        FROM dbo.Economia_Valores
        WHERE SerieEconomicaID = @SerieID
    )
        THROW 51000, 'La migracion altero valores economicos', 1;

    IF
    (
        SELECT Activo
        FROM dbo.Economia_Series
        WHERE SerieEconomicaID = @SerieID
    ) <> 0
        THROW 51000, 'La migracion activo la serie', 1;

    IF
    (
        SELECT Activo
        FROM dbo.Economia_Proveedores
        WHERE ProveedorEconomicoID = @ProveedorID
    ) <> 0
        THROW 51000, 'La migracion activo el proveedor', 1;

    IF ISNULL(
        (
            SELECT activo
            FROM dbo.Servidores_Conexiones
            WHERE id = @ConexionID
        ),
        0
    ) <> 0
        THROW 51000, 'La migracion activo la conexion', 1;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
