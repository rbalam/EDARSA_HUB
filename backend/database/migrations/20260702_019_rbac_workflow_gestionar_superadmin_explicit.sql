SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @Objetivos TABLE (
        CodigoModulo VARCHAR(100) NOT NULL,
        CodigoAccion VARCHAR(100) NOT NULL,
        PRIMARY KEY (CodigoModulo, CodigoAccion)
    );

    INSERT INTO @Objetivos (CodigoModulo, CodigoAccion)
    VALUES ('WORKFLOW', 'GESTIONAR');

    UPDATE prm
    SET
        prm.Activo = 1,
        prm.Permitido = 1
    FROM dbo.Usuario_PermisosRolModulo prm
    JOIN dbo.Usuario_Roles r ON r.RolID = prm.RolID
    JOIN dbo.Usuario_Modulos m ON m.ModuloID = prm.ModuloID
    JOIN dbo.Usuario_Acciones a ON a.AccionID = prm.AccionID
    JOIN @Objetivos o
        ON o.CodigoModulo = m.CodigoModulo
       AND o.CodigoAccion = a.CodigoAccion
    WHERE r.CodigoRol IN ('SUPERADMIN', 'SUPERADMINISTRADOR');

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
        'RBAC_WORKFLOW_GESTIONAR_SUPERADMIN'
    FROM dbo.Usuario_Roles r
    CROSS JOIN @Objetivos o
    JOIN dbo.Usuario_Modulos m ON m.CodigoModulo = o.CodigoModulo
    JOIN dbo.Usuario_Acciones a ON a.CodigoAccion = o.CodigoAccion
    WHERE r.CodigoRol IN ('SUPERADMIN', 'SUPERADMINISTRADOR')
      AND NOT EXISTS (
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
    WHERE r.CodigoRol IN ('SUPERADMIN', 'SUPERADMINISTRADOR')
      AND CONCAT(m.CodigoModulo, '_', a.CodigoAccion) = 'WORKFLOW_GESTIONAR'
    ORDER BY r.CodigoRol;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
