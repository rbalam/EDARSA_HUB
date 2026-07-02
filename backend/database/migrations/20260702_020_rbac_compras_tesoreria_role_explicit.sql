SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @RolTesoreriaID INT;

    SELECT @RolTesoreriaID = RolID
    FROM dbo.Usuario_Roles
    WHERE CodigoRol = 'TESORERIA';

    IF @RolTesoreriaID IS NULL
    BEGIN
        INSERT INTO dbo.Usuario_Roles (
            CodigoRol,
            NombreRol,
            Descripcion,
            EsRolSistema,
            Activo,
            FechaAlta,
            NivelJerarquia
        )
        VALUES (
            'TESORERIA',
            'Tesorería',
            'Operador de pagos y tesorería',
            1,
            1,
            GETDATE(),
            0
        );

        SET @RolTesoreriaID = SCOPE_IDENTITY();
    END
    ELSE
    BEGIN
        UPDATE dbo.Usuario_Roles
        SET
            Activo = 1,
            NombreRol = COALESCE(NULLIF(NombreRol, ''), 'Tesorería'),
            Descripcion = COALESCE(NULLIF(Descripcion, ''), 'Operador de pagos y tesorería'),
            FechaModificacion = GETDATE()
        WHERE RolID = @RolTesoreriaID;
    END;

    IF NOT EXISTS (SELECT 1 FROM dbo.Usuario_Modulos WHERE CodigoModulo = 'COMPRAS_FACT')
    BEGIN
        RAISERROR('No existe modulo COMPRAS_FACT.', 16, 1);
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
        ('TESORERIA', 'COMPRAS_FACT', 'VER'),
        ('TESORERIA', 'COMPRAS_FACT', 'APROBAR'),

        ('SUPERADMIN', 'COMPRAS_FACT', 'VER'),
        ('SUPERADMIN', 'COMPRAS_FACT', 'CREAR'),
        ('SUPERADMIN', 'COMPRAS_FACT', 'EJECUTAR'),
        ('SUPERADMIN', 'COMPRAS_FACT', 'AUTORIZAR'),
        ('SUPERADMIN', 'COMPRAS_FACT', 'APROBAR'),
        ('SUPERADMIN', 'COMPRAS_FACT', 'CONFIGURAR'),
        ('SUPERADMIN', 'COMPRAS_FACT', 'GESTIONAR'),

        ('SUPERADMINISTRADOR', 'COMPRAS_FACT', 'VER'),
        ('SUPERADMINISTRADOR', 'COMPRAS_FACT', 'CREAR'),
        ('SUPERADMINISTRADOR', 'COMPRAS_FACT', 'EJECUTAR'),
        ('SUPERADMINISTRADOR', 'COMPRAS_FACT', 'AUTORIZAR'),
        ('SUPERADMINISTRADOR', 'COMPRAS_FACT', 'APROBAR'),
        ('SUPERADMINISTRADOR', 'COMPRAS_FACT', 'CONFIGURAR'),
        ('SUPERADMINISTRADOR', 'COMPRAS_FACT', 'GESTIONAR');

    IF EXISTS (
        SELECT 1
        FROM @Objetivos o
        LEFT JOIN dbo.Usuario_Roles r ON r.CodigoRol = o.CodigoRol
        WHERE r.RolID IS NULL
          AND o.CodigoRol <> 'SUPERADMINISTRADOR'
    )
    BEGIN
        RAISERROR('Hay roles objetivo inexistentes.', 16, 1);
        RETURN;
    END;

    IF EXISTS (
        SELECT 1
        FROM @Objetivos o
        LEFT JOIN dbo.Usuario_Acciones a ON a.CodigoAccion = o.CodigoAccion
        WHERE a.AccionID IS NULL
    )
    BEGIN
        RAISERROR('Hay acciones objetivo inexistentes.', 16, 1);
        RETURN;
    END;

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
       AND o.CodigoAccion = a.CodigoAccion;

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
        GETDATE(),
        'RBAC_COMPRAS_TESORERIA_EXPLICIT'
    FROM @Objetivos o
    JOIN dbo.Usuario_Roles r ON r.CodigoRol = o.CodigoRol
    JOIN dbo.Usuario_Modulos m ON m.CodigoModulo = o.CodigoModulo
    JOIN dbo.Usuario_Acciones a ON a.CodigoAccion = o.CodigoAccion
    WHERE NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_PermisosRolModulo prm
        WHERE prm.RolID = r.RolID
          AND prm.ModuloID = m.ModuloID
          AND prm.AccionID = a.AccionID
    );

    COMMIT TRANSACTION;

    SELECT
        r.CodigoRol,
        r.NombreRol,
        r.Activo AS RolActivo,
        CONCAT(m.CodigoModulo, '_', a.CodigoAccion) AS Permiso,
        prm.Permitido,
        prm.Activo
    FROM dbo.Usuario_Roles r
    JOIN dbo.Usuario_PermisosRolModulo prm ON prm.RolID = r.RolID
    JOIN dbo.Usuario_Modulos m ON m.ModuloID = prm.ModuloID
    JOIN dbo.Usuario_Acciones a ON a.AccionID = prm.AccionID
    WHERE r.CodigoRol IN ('TESORERIA', 'SUPERADMIN', 'SUPERADMINISTRADOR')
      AND m.CodigoModulo = 'COMPRAS_FACT'
    ORDER BY r.CodigoRol, Permiso;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
