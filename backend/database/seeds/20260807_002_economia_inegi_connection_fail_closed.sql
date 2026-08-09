SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @ConexionID uniqueidentifier;
    DECLARE @ProveedorID int;

    SELECT
        @ProveedorID = ProveedorEconomicoID
    FROM dbo.Economia_Proveedores
    WHERE Codigo = N'INEGI';

    IF @ProveedorID IS NULL
        THROW 51000,
            'Proveedor INEGI no existe. Ejecutar primero seed 20260807_001.',
            1;

    SELECT
        @ConexionID = ServerConexionID
    FROM dbo.Economia_Proveedores
    WHERE ProveedorEconomicoID = @ProveedorID;

    IF @ConexionID IS NOT NULL
    BEGIN
        IF NOT EXISTS
        (
            SELECT 1
            FROM dbo.Servidores_Conexiones
            WHERE id = @ConexionID
        )
            THROW 51001,
                'INEGI referencia ServerConexionID inexistente.',
                1;

        COMMIT TRANSACTION;
        RETURN;
    END;

    SELECT TOP (1)
        @ConexionID = id
    FROM dbo.Servidores_Conexiones
    WHERE UPPER(LTRIM(RTRIM(system_type))) = N'INEGI'
    ORDER BY created_at, id;

    IF @ConexionID IS NULL
    BEGIN
        SET @ConexionID = NEWID();

        INSERT INTO dbo.Servidores_Conexiones
        (
            id,
            nombre,
            system_type,
            tipo_conexion,
            api_url,
            api_key_encrypted,
            activo,
            visible_en_operaciones,
            visible_en_listado,
            es_editable_ui,
            es_eliminable_ui,
            queries_configured,
            created_at,
            updated_at,
            created_by,
            updated_by
        )
        VALUES
        (
            @ConexionID,
            N'INEGI - API Indicadores',
            N'INEGI',
            N'DATA_SOURCE',
            N'https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml',
            NULL,
            0,
            0,
            0,
            0,
            0,
            0,
            GETDATE(),
            GETDATE(),
            N'SEED_ECONOMIA_INEGI',
            N'SEED_ECONOMIA_INEGI'
        );
    END;

    UPDATE dbo.Economia_Proveedores
    SET ServerConexionID = @ConexionID
    WHERE ProveedorEconomicoID = @ProveedorID
      AND ServerConexionID IS NULL;

    IF EXISTS
    (
        SELECT 1
        FROM dbo.Servidores_Conexiones
        WHERE id = @ConexionID
          AND activo <> 0
    )
        THROW 51002,
            'Guardrail: conexión INEGI no puede quedar activa.',
            1;

    IF EXISTS
    (
        SELECT 1
        FROM dbo.Servidores_Conexiones
        WHERE id = @ConexionID
          AND api_key_encrypted IS NOT NULL
          AND LTRIM(RTRIM(api_key_encrypted)) <> N''
    )
        THROW 51003,
            'Guardrail: seed no puede introducir token INEGI.',
            1;

    IF EXISTS
    (
        SELECT 1
        FROM dbo.Economia_Proveedores
        WHERE ProveedorEconomicoID = @ProveedorID
          AND Activo <> 0
    )
        THROW 51004,
            'Guardrail: proveedor INEGI no puede activarse.',
            1;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
