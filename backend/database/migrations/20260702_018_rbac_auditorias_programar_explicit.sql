SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_Acciones
        WHERE CodigoAccion = 'PROGRAMAR'
    )
    BEGIN
        INSERT INTO dbo.Usuario_Acciones (
            CodigoAccion,
            NombreAccion,
            Descripcion,
            EsAutorizable,
            Activo
        )
        VALUES (
            'PROGRAMAR',
            'Programar',
            'Crear, actualizar, activar y desactivar auditorías programadas',
            1,
            1
        );
    END;

    DECLARE @Objetivos TABLE (
        CodigoModulo VARCHAR(100) NOT NULL,
        CodigoAccion VARCHAR(100) NOT NULL,
        PRIMARY KEY (CodigoModulo, CodigoAccion)
    );

    INSERT INTO @Objetivos (CodigoModulo, CodigoAccion)
    VALUES ('AUDITORIAS', 'PROGRAMAR');

    UPDATE prm
    SET
        prm.Activo = 1,
        prm.Permitido = 1
    FROM dbo.Usuario_PermisosRolModulo prm
    JOIN dbo.Usuario_Roles r
        ON r.RolID = prm.RolID
    JOIN dbo.Usuario_Modulos m
        ON m.ModuloID = prm.ModuloID
    JOIN dbo.Usuario_Acciones a
        ON a.AccionID = prm.AccionID
    JOIN @Objetivos o
        ON o.CodigoModulo = m.CodigoModulo
       AND o.CodigoAccion = a.CodigoAccion
    WHERE r.Activo = 1
      AND r.CodigoRol IN ('SUPERADMIN', 'SUPERADMINISTRADOR')
      AND (prm.Activo = 0 OR prm.Permitido = 0);

    DECLARE @PermisosReactivados INT = @@ROWCOUNT;

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
        r.RolID,
        m.ModuloID,
        a.AccionID,
        1,
        0,
        0,
        0,
        NULL,
        1,
        SYSDATETIME(),
        'RBAC_PHASE2G_AUDITORIAS_PROGRAMAR'
    FROM dbo.Usuario_Roles r
    CROSS JOIN @Objetivos o
    JOIN dbo.Usuario_Modulos m
        ON m.CodigoModulo = o.CodigoModulo
       AND m.Activo = 1
    JOIN dbo.Usuario_Acciones a
        ON a.CodigoAccion = o.CodigoAccion
       AND a.Activo = 1
    WHERE r.Activo = 1
      AND r.CodigoRol IN ('SUPERADMIN', 'SUPERADMINISTRADOR')
      AND NOT EXISTS (
          SELECT 1
          FROM dbo.Usuario_PermisosRolModulo prm
          WHERE prm.RolID = r.RolID
            AND prm.ModuloID = m.ModuloID
            AND prm.AccionID = a.AccionID
      );

    DECLARE @PermisosInsertados INT = @@ROWCOUNT;

    SELECT
        'RBAC_AUDITORIAS_PROGRAMAR_EXPLICIT' AS paso,
        CASE
            WHEN EXISTS (
                SELECT 1
                FROM dbo.Usuario_Acciones
                WHERE CodigoAccion = 'PROGRAMAR'
            ) THEN 1 ELSE 0
        END AS accion_programar_existe,
        @PermisosInsertados AS permisos_insertados,
        @PermisosReactivados AS permisos_reactivados;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
    THROW 51000, @ErrorMessage, 1;
END CATCH;
