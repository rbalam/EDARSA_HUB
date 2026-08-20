SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @DavidID INT;
    DECLARE @CarlosID INT;
    DECLARE @GerenciaID INT;
    DECLARE @DireccionID INT;

    SELECT
        @DavidID = UsuarioID
    FROM dbo.Usuario_Catalogo
    WHERE Email = 'david.ricardez@cienfuegos.mx'
      AND Activo = 1;

    SELECT
        @CarlosID = UsuarioID
    FROM dbo.Usuario_Catalogo
    WHERE Email = 'carlos@alpuntoycoma.mx'
      AND Activo = 1;

    SELECT
        @GerenciaID = RolID
    FROM dbo.Usuario_Roles
    WHERE CodigoRol = 'GERENCIA'
      AND Activo = 1;

    SELECT
        @DireccionID = RolID
    FROM dbo.Usuario_Roles
    WHERE CodigoRol = 'DIRECCION'
      AND Activo = 1;

    IF @DavidID IS NULL
        THROW 51600,
        'David Ricaldes no encontrado o inactivo.',
        1;

    IF @CarlosID IS NULL
        THROW 51601,
        'Carlos Aguirre no encontrado o inactivo.',
        1;

    IF @GerenciaID IS NULL
        THROW 51602,
        'GERENCIA no encontrado o inactivo.',
        1;

    IF @DireccionID IS NULL
        THROW 51603,
        'DIRECCION no encontrado o inactivo.',
        1;

    IF (
        SELECT COUNT(*)
        FROM dbo.Unidades_Negocio
        WHERE activo = 1
    ) <> 5
        THROW 51604,
        'Se esperaban exactamente cinco unidades activas.',
        1;

    INSERT INTO dbo.Usuario_RolesContexto (
        UsuarioID,
        RolID,
        UnidadNegocioID,
        EsRolPrimario,
        Activo,
        FechaAlta,
        FechaBaja
    )
    SELECT
        @DavidID,
        @GerenciaID,
        UN.id,
        0,
        1,
        SYSDATETIME(),
        NULL
    FROM dbo.Unidades_Negocio AS UN
    WHERE UN.activo = 1
      AND NOT EXISTS (
            SELECT 1
            FROM dbo.Usuario_RolesContexto AS URC
            WHERE URC.UsuarioID = @DavidID
              AND URC.RolID = @GerenciaID
              AND URC.UnidadNegocioID = UN.id
              AND URC.Activo = 1
              AND (
                    URC.FechaBaja IS NULL
                    OR URC.FechaBaja > SYSDATETIME()
              )
      );

    INSERT INTO dbo.Usuario_RolesContexto (
        UsuarioID,
        RolID,
        UnidadNegocioID,
        EsRolPrimario,
        Activo,
        FechaAlta,
        FechaBaja
    )
    SELECT
        @CarlosID,
        @DireccionID,
        UN.id,
        0,
        1,
        SYSDATETIME(),
        NULL
    FROM dbo.Unidades_Negocio AS UN
    WHERE UN.activo = 1
      AND NOT EXISTS (
            SELECT 1
            FROM dbo.Usuario_RolesContexto AS URC
            WHERE URC.UsuarioID = @CarlosID
              AND URC.RolID = @DireccionID
              AND URC.UnidadNegocioID = UN.id
              AND URC.Activo = 1
              AND (
                    URC.FechaBaja IS NULL
                    OR URC.FechaBaja > SYSDATETIME()
              )
      );

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
