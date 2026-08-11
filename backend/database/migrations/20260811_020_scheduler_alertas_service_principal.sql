/*
EDARSAHUB V1.0
Principal tecnico Scheduler / Alertas Estrategicas.

Objetivo:
- identidad tecnica no interactiva;
- rol dedicado de minimo privilegio;
- permiso unico ALERTAS_VER;
- alcance explicito;
- sin ADMIN / SUPERADMIN;
- sin bypass RBAC.

La migracion es transaccional y fail-closed.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @UsuarioID INT;
    DECLARE @RolID INT;
    DECLARE @ModuloID INT;
    DECLARE @AccionID SMALLINT;

    /* ===== Guardrail contrato funcional ===== */

    SELECT
        @ModuloID = m.ModuloID,
        @AccionID = a.AccionID
    FROM dbo.Usuario_Modulos AS m
    CROSS JOIN dbo.Usuario_Acciones AS a
    WHERE ISNULL(m.Activo,1) = 1
      AND ISNULL(a.Activo,1) = 1
      AND UPPER(LTRIM(RTRIM(m.CodigoModulo))) = 'ALERTAS'
      AND UPPER(LTRIM(RTRIM(a.CodigoAccion))) = 'VER';

    IF @ModuloID IS NULL OR @AccionID IS NULL
        THROW 51000, 'Contrato ALERTAS_VER no encontrado.', 1;

    IF @ModuloID <> 132 OR @AccionID <> 1
        THROW 51000, 'Contrato ALERTAS_VER cambio; revisar antes de migrar.', 1;

    /* ===== Principal tecnico ===== */

    SELECT @UsuarioID = UsuarioID
    FROM dbo.Usuario_Catalogo
    WHERE
           UPPER(LTRIM(RTRIM(ISNULL(CodigoUsuario,''))))
               = 'SYS-SCHED-ALERTAS'
        OR UPPER(LTRIM(RTRIM(ISNULL(Username,''))))
               = 'SYS-SCHED-ALERTAS';

    IF @UsuarioID IS NULL
    BEGIN
        INSERT INTO dbo.Usuario_Catalogo (
            CodigoUsuario,
            Username,
            Email,
            Nombre,
            EsUsuarioPortal,
            RequiereMFA,
            PasswordTemporal,
            DebeCambiarPassword,
            IntentosFallidos,
            Bloqueado,
            Activo,
            PublicUUID
        )
        VALUES (
            'SYS-SCHED-ALERTAS',
            'SYS-SCHED-ALERTAS',
            'sys-sched-alertas@edarsahub.internal',
            'Scheduler Alertas',
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            NEWID()
        );

        SET @UsuarioID = SCOPE_IDENTITY();
    END;

    IF @UsuarioID IS NULL
        THROW 51000, 'No fue posible resolver principal tecnico.', 1;

    /* Fail-closed: nunca reutilizar cuenta humana existente. */

    IF EXISTS (
        SELECT 1
        FROM dbo.Usuario_Catalogo
        WHERE UsuarioID = @UsuarioID
          AND (
                 UPPER(LTRIM(RTRIM(ISNULL(CodigoUsuario,''))))
                     <> 'SYS-SCHED-ALERTAS'
              OR UPPER(LTRIM(RTRIM(ISNULL(Username,''))))
                     <> 'SYS-SCHED-ALERTAS'
              OR ISNULL(EsUsuarioPortal,1) <> 0
          )
    )
        THROW 51000, 'Conflicto de identidad del principal tecnico.', 1;

    /* ===== Rol tecnico ===== */

    SELECT @RolID = RolID
    FROM dbo.Usuario_Roles
    WHERE
        UPPER(LTRIM(RTRIM(ISNULL(CodigoRol,''))))
            = 'SCHEDULER_ALERTAS';

    IF @RolID IS NULL
    BEGIN
        INSERT INTO dbo.Usuario_Roles (
            CodigoRol,
            NombreRol,
            Descripcion,
            EsRolSistema,
            Activo,
            NivelJerarquia
        )
        VALUES (
            'SCHEDULER_ALERTAS',
            'Scheduler Alertas',
            'Rol tecnico no interactivo para evaluacion automatica de alertas.',
            1,
            1,
            10
        );

        SET @RolID = SCOPE_IDENTITY();
    END;

    IF @RolID IS NULL
        THROW 51000, 'No fue posible resolver rol tecnico.', 1;

    /* ===== Asignacion principal -> rol ===== */

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_RolesAsignacion
        WHERE UsuarioID = @UsuarioID
          AND RolID = @RolID
          AND ISNULL(Activo,1) = 1
    )
    BEGIN
        INSERT INTO dbo.Usuario_RolesAsignacion (
            UsuarioID,
            RolID,
            EsPrincipal,
            Activo
        )
        VALUES (
            @UsuarioID,
            @RolID,
            1,
            1
        );
    END;

    /* Principal tecnico no puede tener otro rol activo. */

    IF EXISTS (
        SELECT 1
        FROM dbo.Usuario_RolesAsignacion
        WHERE UsuarioID = @UsuarioID
          AND RolID <> @RolID
          AND ISNULL(Activo,1) = 1
    )
        THROW 51000, 'Principal tecnico posee roles adicionales.', 1;

    /* ===== Permiso minimo ===== */

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_PermisosRolModulo
        WHERE RolID = @RolID
          AND ModuloID = @ModuloID
          AND AccionID = @AccionID
          AND ISNULL(Activo,1) = 1
          AND ISNULL(Permitido,0) = 1
    )
    BEGIN
        INSERT INTO dbo.Usuario_PermisosRolModulo (
            RolID,
            ModuloID,
            AccionID,
            Permitido,
            RestriccionPropietario,
            RestriccionSucursal,
            RequiereAutorizacion,
            Activo
        )
        VALUES (
            @RolID,
            @ModuloID,
            @AccionID,
            1,
            0,
            1,
            0,
            1
        );
    END;

    /* Rol tecnico no puede recibir permisos adicionales. */

    IF EXISTS (
        SELECT 1
        FROM dbo.Usuario_PermisosRolModulo
        WHERE RolID = @RolID
          AND ISNULL(Activo,1) = 1
          AND ISNULL(Permitido,0) = 1
          AND NOT (
              ModuloID = @ModuloID
              AND AccionID = @AccionID
          )
    )
        THROW 51000, 'Rol tecnico posee permisos adicionales.', 1;

    /* El permiso debe permanecer restringido por scope. */

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_PermisosRolModulo
        WHERE RolID = @RolID
          AND ModuloID = @ModuloID
          AND AccionID = @AccionID
          AND ISNULL(Activo,1) = 1
          AND ISNULL(Permitido,0) = 1
          AND ISNULL(RestriccionSucursal,0) = 1
    )
        THROW 51000, 'ALERTAS_VER tecnico no tiene RestriccionSucursal.', 1;

    /* ===== Scope servidores dedicados ===== */

    DECLARE @DedicatedServers TABLE (
        ServidorID UNIQUEIDENTIFIER PRIMARY KEY
    );

    INSERT INTO @DedicatedServers (ServidorID)
    VALUES
        ('6d053c22-523e-48c0-b72b-96081e2d781b'),
        ('a5547321-1139-4d2b-9d53-182ca737b6b6'),
        ('a5ff0e25-f029-43db-b634-d4ac814c904f');

    IF EXISTS (
        SELECT 1
        FROM @DedicatedServers AS ds
        WHERE (
            SELECT COUNT(*)
            FROM dbo.Unidades_Negocio AS u
            WHERE ISNULL(u.activo,0) = 1
              AND TRY_CONVERT(
                    UNIQUEIDENTIFIER,
                    u.server_id
                  ) = ds.ServidorID
        ) <> 1
    )
        THROW 51000, 'Topologia de servidor dedicado cambio.', 1;

    INSERT INTO dbo.Usuario_ServidoresAsignacion (
        UsuarioID,
        ServidorID,
        Activo,
        Observaciones
    )
    SELECT
        @UsuarioID,
        ds.ServidorID,
        1,
        'Scheduler Alertas V1.0 - scope canonico'
    FROM @DedicatedServers AS ds
    WHERE NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_ServidoresAsignacion AS usa
        WHERE usa.UsuarioID = @UsuarioID
          AND usa.ServidorID = ds.ServidorID
          AND ISNULL(usa.Activo,1) = 1
    );

    /* ===== Scope servidor compartido ===== */

    DECLARE @SharedBranches TABLE (
        ServidorID UNIQUEIDENTIFIER NOT NULL,
        SucursalCodigo VARCHAR(100) NOT NULL,
        PRIMARY KEY (ServidorID, SucursalCodigo)
    );

    INSERT INTO @SharedBranches (
        ServidorID,
        SucursalCodigo
    )
    VALUES
        (
            '1b230a06-ffaf-4c70-bd27-b1be3579dea6',
            '0021'
        ),
        (
            '1b230a06-ffaf-4c70-bd27-b1be3579dea6',
            '0023'
        );

    IF EXISTS (
        SELECT 1
        FROM @SharedBranches AS sb
        WHERE NOT EXISTS (
            SELECT 1
            FROM dbo.Unidades_Negocio AS u
            WHERE ISNULL(u.activo,0) = 1
              AND TRY_CONVERT(
                    UNIQUEIDENTIFIER,
                    u.server_id
                  ) = sb.ServidorID
              AND LTRIM(RTRIM(
                    ISNULL(u.sucursal_origen_id,'')
                  )) = sb.SucursalCodigo
        )
    )
        THROW 51000, 'Topologia de servidor compartido cambio.', 1;

    INSERT INTO dbo.Usuario_SucursalesAsignacion (
        UsuarioID,
        ServidorID,
        SucursalCodigo,
        Activo,
        Observaciones
    )
    SELECT
        @UsuarioID,
        sb.ServidorID,
        sb.SucursalCodigo,
        1,
        'Scheduler Alertas V1.0 - scope canonico'
    FROM @SharedBranches AS sb
    WHERE NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_SucursalesAsignacion AS usa
        WHERE usa.UsuarioID = @UsuarioID
          AND usa.ServidorID = sb.ServidorID
          AND usa.SucursalCodigo = sb.SucursalCodigo
          AND ISNULL(usa.Activo,1) = 1
    );

    /*
    No asignar el servidor compartido en Usuario_ServidoresAsignacion.
    Debe resolverse exclusivamente por servidor+sucursal.
    */

    IF EXISTS (
        SELECT 1
        FROM dbo.Usuario_ServidoresAsignacion
        WHERE UsuarioID = @UsuarioID
          AND ServidorID =
              '1b230a06-ffaf-4c70-bd27-b1be3579dea6'
          AND ISNULL(Activo,1) = 1
    )
        THROW 51000, 'Servidor compartido asignado sin discriminacion de sucursal.', 1;

    /* ===== Validacion de cardinalidad del scope ===== */

    IF (
        SELECT COUNT(*)
        FROM dbo.Usuario_ServidoresAsignacion
        WHERE UsuarioID = @UsuarioID
          AND ISNULL(Activo,1) = 1
    ) <> 3
        THROW 51000, 'Scope servidor tecnico inesperado.', 1;

    IF (
        SELECT COUNT(*)
        FROM dbo.Usuario_SucursalesAsignacion
        WHERE UsuarioID = @UsuarioID
          AND ISNULL(Activo,1) = 1
    ) <> 2
        THROW 51000, 'Scope sucursal tecnico inesperado.', 1;

    COMMIT TRANSACTION;

    SELECT
        @UsuarioID AS UsuarioID,
        @RolID AS RolID,
        @ModuloID AS ModuloID,
        @AccionID AS AccionID,
        'PASS' AS Resultado;

END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
