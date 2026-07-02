SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @Objetivos TABLE (
        CodigoRol VARCHAR(100) NOT NULL,
        CodigoModulo VARCHAR(100) NOT NULL,
        CodigoAccion VARCHAR(100) NOT NULL,
        PRIMARY KEY (CodigoRol, CodigoModulo, CodigoAccion)
    );

    INSERT INTO @Objetivos (CodigoRol, CodigoModulo, CodigoAccion)
    VALUES
        ('DIRECCION', 'COMPRAS_FACT', 'VER'),
        ('DIRECCION', 'COMPRAS_FACT', 'EJECUTAR'),
        ('DIRECCION', 'COMPRAS_FACT', 'AUTORIZAR'),
        ('DIRECCION', 'COMPRAS_FACT', 'APROBAR'),
        ('DIRECCION', 'COMPRAS_FACT', 'CONFIGURAR'),

        ('GERENTE_OPS', 'COMPRAS_FACT', 'VER'),
        ('GERENTE_OPS', 'COMPRAS_FACT', 'EJECUTAR'),
        ('GERENTE_OPS', 'COMPRAS_FACT', 'AUTORIZAR'),
        ('GERENTE_OPS', 'COMPRAS_FACT', 'CONFIGURAR');

    IF EXISTS (
        SELECT 1
        FROM @Objetivos o
        LEFT JOIN dbo.Usuario_Roles r ON r.CodigoRol = o.CodigoRol AND r.Activo = 1
        WHERE r.RolID IS NULL
    )
    BEGIN
        RAISERROR('Hay roles objetivo inexistentes o inactivos.', 16, 1);
        RETURN;
    END;

    IF EXISTS (
        SELECT 1
        FROM @Objetivos o
        LEFT JOIN dbo.Usuario_Modulos m ON m.CodigoModulo = o.CodigoModulo AND m.Activo = 1
        WHERE m.ModuloID IS NULL
    )
    BEGIN
        RAISERROR('Hay modulos objetivo inexistentes o inactivos.', 16, 1);
        RETURN;
    END;

    IF EXISTS (
        SELECT 1
        FROM @Objetivos o
        LEFT JOIN dbo.Usuario_Acciones a ON a.CodigoAccion = o.CodigoAccion AND a.Activo = 1
        WHERE a.AccionID IS NULL
    )
    BEGIN
        RAISERROR('Hay acciones objetivo inexistentes o inactivas.', 16, 1);
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
        'RBAC_COMPRAS_OPERATIVO_EXPLICIT'
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
        CONCAT(m.CodigoModulo, '_', a.CodigoAccion) AS Permiso,
        prm.Permitido,
        prm.Activo
    FROM dbo.Usuario_Roles r
    JOIN dbo.Usuario_PermisosRolModulo prm ON prm.RolID = r.RolID
    JOIN dbo.Usuario_Modulos m ON m.ModuloID = prm.ModuloID
    JOIN dbo.Usuario_Acciones a ON a.AccionID = prm.AccionID
    WHERE r.CodigoRol IN ('DIRECCION', 'GERENTE_OPS', 'TESORERIA', 'SUPERADMIN', 'ADMIN')
      AND m.CodigoModulo = 'COMPRAS_FACT'
    ORDER BY r.CodigoRol, Permiso;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
