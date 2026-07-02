/*
EDARSAHUB - RBAC Fase 2F
Activar permisos SQL explícitos de administración para SUPERADMIN.

Permisos objetivo:
- RBAC_ADMIN
- SCHEDULER_ADMIN
- SCHEDULER_GESTIONAR

Reglas:
- Idempotente.
- Solo toca roles SUPERADMIN / SUPERADMINISTRADOR.
- No asigna permisos administrativos a ADMIN.
- No crea usuarios.
- No toca MongoDB.
- Usa modelo canónico Usuario_Roles + Usuario_Modulos + Usuario_Acciones + Usuario_PermisosRolModulo.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Usuario_Roles', 'U') IS NULL
        THROW 51000, 'No existe dbo.Usuario_Roles.', 1;

    IF OBJECT_ID('dbo.Usuario_Modulos', 'U') IS NULL
        THROW 51000, 'No existe dbo.Usuario_Modulos.', 1;

    IF OBJECT_ID('dbo.Usuario_Acciones', 'U') IS NULL
        THROW 51000, 'No existe dbo.Usuario_Acciones.', 1;

    IF OBJECT_ID('dbo.Usuario_PermisosRolModulo', 'U') IS NULL
        THROW 51000, 'No existe dbo.Usuario_PermisosRolModulo.', 1;

    DECLARE @Objetivos TABLE (
        CodigoModulo VARCHAR(100) NOT NULL,
        CodigoAccion VARCHAR(100) NOT NULL,
        PRIMARY KEY (CodigoModulo, CodigoAccion)
    );

    INSERT INTO @Objetivos (CodigoModulo, CodigoAccion)
    VALUES
        ('RBAC', 'ADMIN'),
        ('SCHEDULER', 'ADMIN'),
        ('SCHEDULER', 'GESTIONAR');

    DECLARE @RolesObjetivo TABLE (
        RolID INT NOT NULL PRIMARY KEY,
        CodigoRol VARCHAR(100) NOT NULL
    );

    INSERT INTO @RolesObjetivo (RolID, CodigoRol)
    SELECT r.RolID, r.CodigoRol
    FROM dbo.Usuario_Roles r
    WHERE r.Activo = 1
      AND r.CodigoRol IN ('SUPERADMIN', 'SUPERADMINISTRADOR');

    IF NOT EXISTS (SELECT 1 FROM @RolesObjetivo)
        THROW 51000, 'No existe rol activo SUPERADMIN/SUPERADMINISTRADOR.', 1;

    IF EXISTS (
        SELECT 1
        FROM @Objetivos o
        LEFT JOIN dbo.Usuario_Modulos m
            ON m.CodigoModulo = o.CodigoModulo
            AND m.Activo = 1
        WHERE m.ModuloID IS NULL
    )
        THROW 51000, 'Falta uno o más módulos activos requeridos: RBAC/SCHEDULER.', 1;

    IF EXISTS (
        SELECT 1
        FROM @Objetivos o
        LEFT JOIN dbo.Usuario_Acciones a
            ON a.CodigoAccion = o.CodigoAccion
            AND a.Activo = 1
        WHERE a.AccionID IS NULL
    )
        THROW 51000, 'Falta una o más acciones activas requeridas: ADMIN/GESTIONAR.', 1;

    DECLARE @PermisosReactivados INT = 0;
    DECLARE @PermisosInsertados INT = 0;

    UPDATE prm
    SET
        prm.Activo = 1,
        prm.Permitido = 1
    FROM dbo.Usuario_PermisosRolModulo prm
    INNER JOIN @RolesObjetivo ro
        ON ro.RolID = prm.RolID
    INNER JOIN dbo.Usuario_Modulos m
        ON m.ModuloID = prm.ModuloID
    INNER JOIN dbo.Usuario_Acciones a
        ON a.AccionID = prm.AccionID
    INNER JOIN @Objetivos o
        ON o.CodigoModulo = m.CodigoModulo
        AND o.CodigoAccion = a.CodigoAccion
    WHERE prm.Activo = 0
       OR prm.Permitido = 0;

    SET @PermisosReactivados = @@ROWCOUNT;

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
    SELECT
        ro.RolID,
        m.ModuloID,
        a.AccionID,
        1,
        0,
        0,
        0,
        NULL,
        1,
        SYSDATETIME(),
        'RBAC_PHASE2F_SUPERADMIN_ADMIN_PERMS'
    FROM @RolesObjetivo ro
    CROSS JOIN @Objetivos o
    INNER JOIN dbo.Usuario_Modulos m
        ON m.CodigoModulo = o.CodigoModulo
        AND m.Activo = 1
    INNER JOIN dbo.Usuario_Acciones a
        ON a.CodigoAccion = o.CodigoAccion
        AND a.Activo = 1
    WHERE NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_PermisosRolModulo prm
        WHERE prm.RolID = ro.RolID
          AND prm.ModuloID = m.ModuloID
          AND prm.AccionID = a.AccionID
    );

    SET @PermisosInsertados = @@ROWCOUNT;

    SELECT
        'RBAC_SUPERADMIN_ADMIN_PERMISSIONS_MIGRATION' AS paso,
        @PermisosInsertados AS permisos_insertados,
        @PermisosReactivados AS permisos_reactivados;

    SELECT
        'RBAC_SUPERADMIN_ADMIN_PERMISSIONS_RESULT' AS paso,
        r.CodigoRol,
        m.CodigoModulo,
        a.CodigoAccion,
        CONCAT(m.CodigoModulo, '_', a.CodigoAccion) AS permiso_normalizado,
        prm.Permitido,
        prm.Activo
    FROM dbo.Usuario_PermisosRolModulo prm
    INNER JOIN dbo.Usuario_Roles r
        ON r.RolID = prm.RolID
    INNER JOIN dbo.Usuario_Modulos m
        ON m.ModuloID = prm.ModuloID
    INNER JOIN dbo.Usuario_Acciones a
        ON a.AccionID = prm.AccionID
    INNER JOIN @Objetivos o
        ON o.CodigoModulo = m.CodigoModulo
        AND o.CodigoAccion = a.CodigoAccion
    WHERE r.CodigoRol IN ('SUPERADMIN', 'SUPERADMINISTRADOR', 'ADMIN')
    ORDER BY r.CodigoRol, m.CodigoModulo, a.CodigoAccion;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
    THROW 51000, @ErrorMessage, 1;
END CATCH;
