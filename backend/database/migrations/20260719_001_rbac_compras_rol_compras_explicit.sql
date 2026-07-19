SET NOCOUNT ON;
SET XACT_ABORT ON;

-- ============================================================================
-- RBAC_COMPRAS_ROL_COMPRAS_EXPLICIT
-- Concede al rol operativo 'COMPRAS' los permisos funcionales del modulo
-- COMPRAS_FACT que ya tienen DIRECCION/GERENTE_OPS/TESORERIA/SUPERADMIN
-- (ver 20260702_020/021/022_rbac_compras_*.sql).
--
-- Motivo: el enforcement de permisos anadido en backend/modules/compras/access.py
-- (require_compras_permission) bloquea con 403 a cualquier usuario sin un
-- permiso COMPRAS_FACT_* concedido. Antes de esta migracion, el rol COMPRAS
-- (usado por los compradores operativos reales) NO tenia ningun permiso
-- COMPRAS_FACT concedido -- aplicar el enforcement sin este grant habria
-- bloqueado el acceso legitimo de ese rol.
--
-- No se conceden AUTORIZAR/APROBAR: esas acciones quedan reservadas a
-- DIRECCION/GERENTE_OPS/TESORERIA/SUPERADMIN por diseno de negocio existente.
-- ============================================================================

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
        ('COMPRAS', 'COMPRAS_FACT', 'VER'),
        ('COMPRAS', 'COMPRAS_FACT', 'CREAR'),
        ('COMPRAS', 'COMPRAS_FACT', 'EJECUTAR'),
        ('COMPRAS', 'COMPRAS_FACT', 'CONFIGURAR'),
        ('COMPRAS', 'COMPRAS_FACT', 'GESTIONAR');

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
        'RBAC_COMPRAS_ROL_COMPRAS_EXPLICIT'
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
    WHERE r.CodigoRol = 'COMPRAS'
      AND m.CodigoModulo = 'COMPRAS_FACT'
    ORDER BY Permiso;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
