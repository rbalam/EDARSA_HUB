/*
    EDARSAHUB
    RBAC Costos y Margenes - VER + CONFIGURAR

    Politica:

    ADMIN_COMERCIAL:
        VER
        CONFIGURAR

    CONFIGURADOR_COMERCIAL:
        VER
        CONFIGURAR

    SUPERADMIN:
        CONFIGURAR
        (VER ya existe por migration 028)

    No concede CONFIGURAR a:
        ADMIN
        GERENCIA
        GERENTE_UNIDAD
        OPERADOR
        PRUEBA_RBAC_SQL

    No crea roles.
    No usa bypass.
    No depende de NivelJerarquia.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @ModuloID int;
    DECLARE @VerID smallint;
    DECLARE @ConfigurarID smallint;

    SELECT @ModuloID = ModuloID
    FROM dbo.Usuario_Modulos
    WHERE LOWER(CodigoModulo)
          = 'comercial.costos_margenes'
      AND ISNULL(Activo, 1) = 1;

    IF @ModuloID IS NULL
        THROW 51030, 'Modulo comercial.costos_margenes no existe.', 1;

    SELECT @VerID = AccionID
    FROM dbo.Usuario_Acciones
    WHERE UPPER(CodigoAccion) = 'VER'
      AND ISNULL(Activo, 1) = 1;

    IF @VerID IS NULL
        THROW 51031, 'Accion VER no existe.', 1;

    SELECT @ConfigurarID = AccionID
    FROM dbo.Usuario_Acciones
    WHERE UPPER(CodigoAccion) = 'CONFIGURAR'
      AND ISNULL(Activo, 1) = 1;

    IF @ConfigurarID IS NULL
        THROW 51032, 'Accion CONFIGURAR no existe.', 1;

    DECLARE @Targets TABLE
    (
        RolID int NOT NULL,
        AccionID smallint NOT NULL,
        PRIMARY KEY (RolID, AccionID)
    );

    /*
        Roles especializados comerciales:
        VER + CONFIGURAR.
    */
    INSERT INTO @Targets
    (
        RolID,
        AccionID
    )
    SELECT
        r.RolID,
        a.AccionID
    FROM dbo.Usuario_Roles r
    CROSS JOIN
    (
        SELECT @VerID AS AccionID
        UNION ALL
        SELECT @ConfigurarID
    ) a
    WHERE UPPER(r.CodigoRol)
          IN (
              'ADMIN_COMERCIAL',
              'CONFIGURADOR_COMERCIAL'
          )
      AND ISNULL(r.Activo, 1) = 1;

    /*
        SUPERADMIN:
        CONFIGURAR explícito.
        VER ya existe.
    */
    INSERT INTO @Targets
    (
        RolID,
        AccionID
    )
    SELECT
        r.RolID,
        @ConfigurarID
    FROM dbo.Usuario_Roles r
    WHERE UPPER(r.CodigoRol) = 'SUPERADMIN'
      AND ISNULL(r.Activo, 1) = 1;

    IF (
        SELECT COUNT_BIG(*)
        FROM @Targets
    ) <> 5
        THROW 51033, 'Target RBAC incompleto; se esperaban 5 combinaciones.', 1;

    /*
        Reactivar una fila existente inactiva si existe.
    */
    UPDATE existing_perm
       SET existing_perm.Permitido = 1,
           existing_perm.Activo = 1,
           existing_perm.RestriccionPropietario = 0,
           existing_perm.RestriccionSucursal = 0,
           existing_perm.RequiereAutorizacion = 0,
           existing_perm.NivelAutorizacionRequerido = NULL,
           existing_perm.FechaModificacion = SYSUTCDATETIME(),
           existing_perm.ModifiedBy = 'migration_20260814_029'
    FROM dbo.Usuario_PermisosRolModulo existing_perm
    INNER JOIN @Targets target
        ON target.RolID = existing_perm.RolID
       AND target.AccionID = existing_perm.AccionID
    WHERE existing_perm.ModuloID = @ModuloID
      AND (
             ISNULL(existing_perm.Activo, 1) = 0
          OR ISNULL(existing_perm.Permitido, 0) = 0
      );

    /*
        Insertar únicamente combinaciones inexistentes.
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
        target.RolID,
        @ModuloID,
        target.AccionID,
        1,
        0,
        0,
        0,
        NULL,
        1,
        SYSUTCDATETIME(),
        NULL,
        'migration_20260814_029',
        NULL
    FROM @Targets target
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.Usuario_PermisosRolModulo existing_perm
        WHERE existing_perm.RolID = target.RolID
          AND existing_perm.ModuloID = @ModuloID
          AND existing_perm.AccionID = target.AccionID
          AND ISNULL(existing_perm.Activo, 1) = 1
          AND ISNULL(existing_perm.Permitido, 0) = 1
    );

    /*
        Guardrail exacto:
        los 5 targets deben existir activos.
    */
    IF (
        SELECT COUNT_BIG(*)
        FROM @Targets target
        INNER JOIN dbo.Usuario_PermisosRolModulo prm
            ON prm.RolID = target.RolID
           AND prm.ModuloID = @ModuloID
           AND prm.AccionID = target.AccionID
           AND ISNULL(prm.Activo, 1) = 1
           AND ISNULL(prm.Permitido, 0) = 1
    ) <> 5
        THROW 51034, 'No quedaron activos los 5 permisos esperados.', 1;

    /*
        ADMIN general NO debe recibir CONFIGURAR.
    */
    IF EXISTS
    (
        SELECT 1
        FROM dbo.Usuario_PermisosRolModulo prm
        INNER JOIN dbo.Usuario_Roles r
            ON r.RolID = prm.RolID
        WHERE prm.ModuloID = @ModuloID
          AND prm.AccionID = @ConfigurarID
          AND UPPER(r.CodigoRol) = 'ADMIN'
          AND ISNULL(prm.Activo, 1) = 1
          AND ISNULL(prm.Permitido, 0) = 1
          AND (
                 prm.CreatedBy = 'migration_20260814_029'
              OR prm.ModifiedBy = 'migration_20260814_029'
          )
    )
        THROW 51035, 'ADMIN recibió CONFIGURAR indebidamente.', 1;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
