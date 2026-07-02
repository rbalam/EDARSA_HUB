SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_Modulos
        WHERE CodigoModulo = 'SYNC_AGENT'
    )
    BEGIN
        INSERT INTO dbo.Usuario_Modulos (
            CodigoModulo,
            NombreModulo,
            Descripcion,
            Icono,
            Ruta,
            Activo
        )
        VALUES (
            'SYNC_AGENT',
            'Sync Agent',
            'Administración de tokens para agentes de sincronización',
            'RefreshCw',
            '/admin/agents',
            1
        );
    END
    ELSE
    BEGIN
        UPDATE dbo.Usuario_Modulos
        SET
            NombreModulo = 'Sync Agent',
            Descripcion = COALESCE(Descripcion, 'Administración de tokens para agentes de sincronización'),
            Activo = 1
        WHERE CodigoModulo = 'SYNC_AGENT';
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_Acciones
        WHERE CodigoAccion = 'GENERAR'
          AND Activo = 1
    )
    BEGIN
        RAISERROR('No existe accion GENERAR activa en dbo.Usuario_Acciones.', 16, 1);
        RETURN;
    END;

    DECLARE @Objetivos TABLE (
        CodigoRol VARCHAR(100) NOT NULL,
        CodigoModulo VARCHAR(100) NOT NULL,
        CodigoAccion VARCHAR(100) NOT NULL,
        PRIMARY KEY (CodigoRol, CodigoModulo, CodigoAccion)
    );

    INSERT INTO @Objetivos (CodigoRol, CodigoModulo, CodigoAccion)
    VALUES
        ('SUPERADMIN', 'SYNC_AGENT', 'GENERAR'),
        ('SUPERADMINISTRADOR', 'SYNC_AGENT', 'GENERAR'),
        ('ADMIN', 'SYNC_AGENT', 'GENERAR'),
        ('ADMINISTRADOR', 'SYNC_AGENT', 'GENERAR'),
        ('SUPERVISOR', 'SYNC_AGENT', 'GENERAR');

    UPDATE prm
    SET
        prm.Activo = 1,
        prm.Permitido = 1
    FROM dbo.Usuario_PermisosRolModulo prm
    JOIN dbo.Usuario_Roles r ON r.RolID = prm.RolID
    JOIN dbo.Usuario_Modulos m ON m.ModuloID = prm.ModuloID
    JOIN dbo.Usuario_Acciones a ON a.AccionID = prm.AccionID
    JOIN @Objetivos o
        ON o.CodigoRol = r.CodigoRol
       AND o.CodigoModulo = m.CodigoModulo
       AND o.CodigoAccion = a.CodigoAccion
    WHERE r.Activo = 1;

    DECLARE @PermisosReactivados INT = @@ROWCOUNT;

    INSERT INTO dbo.Usuario_PermisosRolModulo (
        RolID,
        ModuloID,
        AccionID,
        Permitido,
        RestriccionPropietario,
        RestriccionSucursal,
        RequiereAutorizacion,
        Activo,
        FechaAlta,
        CreatedBy
    )
    SELECT
        r.RolID,
        m.ModuloID,
        a.AccionID,
        1,
        0,
        0,
        0,
        1,
        SYSDATETIME(),
        'RBAC_SYNC_AGENT_GENERAR'
    FROM @Objetivos o
    JOIN dbo.Usuario_Roles r
        ON r.CodigoRol = o.CodigoRol
       AND r.Activo = 1
    JOIN dbo.Usuario_Modulos m
        ON m.CodigoModulo = o.CodigoModulo
       AND m.Activo = 1
    JOIN dbo.Usuario_Acciones a
        ON a.CodigoAccion = o.CodigoAccion
       AND a.Activo = 1
    WHERE NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_PermisosRolModulo prm
        WHERE prm.RolID = r.RolID
          AND prm.ModuloID = m.ModuloID
          AND prm.AccionID = a.AccionID
    );

    DECLARE @PermisosInsertados INT = @@ROWCOUNT;

    COMMIT TRANSACTION;

    SELECT
        'RBAC_SYNC_AGENT_GENERAR' AS paso,
        @PermisosInsertados AS permisos_insertados,
        @PermisosReactivados AS permisos_reactivados;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
