SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @RolID INT;
    DECLARE @ModuloID INT;
    DECLARE @AccionID SMALLINT;

    SELECT @RolID = RolID
    FROM dbo.Usuario_Roles
    WHERE CodigoRol = 'SUPERADMIN'
      AND Activo = 1;

    SELECT @ModuloID = ModuloID
    FROM dbo.Usuario_Modulos
    WHERE CodigoModulo = 'SEGURIDAD'
      AND Activo = 1;

    SELECT @AccionID = AccionID
    FROM dbo.Usuario_Acciones
    WHERE CodigoAccion = 'CONFIGURAR'
      AND Activo = 1;

    IF @RolID IS NULL
        THROW 51000, 'Rol SUPERADMIN activo no encontrado', 1;

    IF @ModuloID IS NULL
        THROW 51000, 'Modulo SEGURIDAD activo no encontrado', 1;

    IF @AccionID IS NULL
        THROW 51000, 'Accion CONFIGURAR activa no encontrada', 1;

    IF EXISTS (
        SELECT 1
        FROM dbo.Usuario_PermisosRolModulo
        WHERE RolID = @RolID
          AND ModuloID = @ModuloID
          AND AccionID = @AccionID
    )
    BEGIN
        UPDATE dbo.Usuario_PermisosRolModulo
        SET
            Permitido = 1,
            Activo = 1,
            RestriccionPropietario = 0,
            RestriccionSucursal = 0,
            RequiereAutorizacion = 0,
            NivelAutorizacionRequerido = NULL,
            FechaModificacion = SYSUTCDATETIME(),
            ModifiedBy = 'MIGRATION_20260819_036'
        WHERE RolID = @RolID
          AND ModuloID = @ModuloID
          AND AccionID = @AccionID;
    END
    ELSE
    BEGIN
        INSERT INTO dbo.Usuario_PermisosRolModulo (
            RolID,
            ModuloID,
            AccionID,
            Permitido,
            RestriccionPropietario,
            RestriccionSucursal,
            RequiereAutorizacion,
            NivelAutorizacionRequerido,
            Activo,
            FechaAlta,
            CreatedBy
        )
        VALUES (
            @RolID,
            @ModuloID,
            @AccionID,
            1,
            0,
            0,
            0,
            NULL,
            1,
            SYSUTCDATETIME(),
            'MIGRATION_20260819_036'
        );
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
