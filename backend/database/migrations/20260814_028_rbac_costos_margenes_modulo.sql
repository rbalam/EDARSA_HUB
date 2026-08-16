/*
    EDARSAHUB
    RBAC - Modulo canonico Costos y Margenes

    Objetivo:
      1. Crear comercial.costos_margenes bajo comercial.
      2. Conservar exactamente el acceso de lectura actualmente
         otorgado mediante comercial_VER.
      3. NO otorgar CONFIGURAR ni otras acciones sensibles.

    Idempotente y defensivo.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @ModuloPadreID int;
    DECLARE @ModuloCostosID int;
    DECLARE @AccionVerID smallint;

    SELECT @ModuloPadreID = ModuloID
    FROM dbo.Usuario_Modulos
    WHERE LOWER(CodigoModulo) = 'comercial'
      AND ISNULL(Activo, 1) = 1;

    IF @ModuloPadreID IS NULL
        THROW 51000, 'Modulo padre comercial no existe o no esta activo.', 1;

    IF EXISTS (
        SELECT 1
        FROM dbo.Usuario_Modulos
        WHERE LOWER(CodigoModulo) = 'comercial.costos_margenes'
    )
    BEGIN
        SELECT @ModuloCostosID = ModuloID
        FROM dbo.Usuario_Modulos
        WHERE LOWER(CodigoModulo) = 'comercial.costos_margenes';
    END
    ELSE
    BEGIN
        INSERT INTO dbo.Usuario_Modulos
        (
            ModuloPadreID,
            CodigoModulo,
            NombreModulo,
            Descripcion,
            TipoModulo,
            Ruta,
            Icono,
            OrdenMenu,
            EsVisibleMenu,
            RequiereAutorizacion,
            Activo,
            FechaAlta,
            FechaModificacion
        )
        VALUES
        (
            @ModuloPadreID,
            'comercial.costos_margenes',
            'Costos y Margenes',
            'Control RBAC canonico del dominio Costos y Margenes.',
            'SUBMODULO',
            '/comercial/costos-margenes',
            NULL,
            0,
            0,
            0,
            1,
            SYSUTCDATETIME(),
            NULL
        );

        SET @ModuloCostosID = SCOPE_IDENTITY();
    END;

    IF @ModuloCostosID IS NULL
        THROW 51001, 'No fue posible resolver el modulo Costos y Margenes.', 1;

    SELECT @AccionVerID = AccionID
    FROM dbo.Usuario_Acciones
    WHERE UPPER(CodigoAccion) = 'VER'
      AND ISNULL(Activo, 1) = 1;

    IF @AccionVerID IS NULL
        THROW 51002, 'Accion VER no existe o no esta activa.', 1;

    /*
        Conservacion controlada de acceso actual.

        Solo roles que HOY poseen comercial_VER.
        No se hardcodean nombres de rol.
    */
    INSERT INTO dbo.Usuario_PermisosRolModulo
    (
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
        FechaModificacion,
        CreatedBy,
        ModifiedBy
    )
    SELECT
        source_perm.RolID,
        @ModuloCostosID,
        @AccionVerID,
        source_perm.Permitido,
        source_perm.RestriccionPropietario,
        source_perm.RestriccionSucursal,
        source_perm.RequiereAutorizacion,
        source_perm.NivelAutorizacionRequerido,
        1,
        SYSUTCDATETIME(),
        NULL,
        'migration_20260814_028',
        NULL
    FROM dbo.Usuario_PermisosRolModulo source_perm
    INNER JOIN dbo.Usuario_Modulos source_module
        ON source_module.ModuloID = source_perm.ModuloID
    INNER JOIN dbo.Usuario_Acciones source_action
        ON source_action.AccionID = source_perm.AccionID
    INNER JOIN dbo.Usuario_Roles source_role
        ON source_role.RolID = source_perm.RolID
    WHERE LOWER(source_module.CodigoModulo) = 'comercial'
      AND UPPER(source_action.CodigoAccion) = 'VER'
      AND ISNULL(source_perm.Activo, 1) = 1
      AND ISNULL(source_perm.Permitido, 0) = 1
      AND ISNULL(source_module.Activo, 1) = 1
      AND ISNULL(source_action.Activo, 1) = 1
      AND ISNULL(source_role.Activo, 1) = 1
      AND NOT EXISTS
      (
          SELECT 1
          FROM dbo.Usuario_PermisosRolModulo existing_perm
          WHERE existing_perm.RolID = source_perm.RolID
            AND existing_perm.ModuloID = @ModuloCostosID
            AND existing_perm.AccionID = @AccionVerID
            AND ISNULL(existing_perm.Activo, 1) = 1
      );

    /*
        Guardrail:
        esta migracion no debe crear ninguna accion distinta de VER.
    */
    IF EXISTS
    (
        SELECT 1
        FROM dbo.Usuario_PermisosRolModulo prm
        INNER JOIN dbo.Usuario_Acciones a
            ON a.AccionID = prm.AccionID
        WHERE prm.ModuloID = @ModuloCostosID
          AND UPPER(a.CodigoAccion) <> 'VER'
          AND prm.CreatedBy = 'migration_20260814_028'
    )
        THROW 51003, 'La migracion intento otorgar acciones distintas de VER.', 1;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
