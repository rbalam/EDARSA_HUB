/*
EDARSAHUB - RBAC Fase 2
Reasignar usuarios activos del rol vacio USUARIO al rol OPERADOR.

Ejecutar con:
EDARSAHUB_ALLOW_MIGRATIONS=true python backend/tools/edarsahub_sql_runner.py \
  --mode migrate \
  --script backend/database/migrations/20260630_010_reasignar_usuario_a_operador_rbac.sql

Reglas:
- Idempotente.
- No crea usuarios.
- No toca permisos.
- No toca MongoDB.
- Reactiva/asigna OPERADOR a usuarios activos con USUARIO activo.
- Desactiva la asignacion USUARIO solo despues de confirmar OPERADOR activo.
- Desactiva el rol USUARIO solo si ya no quedan asignaciones activas.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Usuario_Catalogo', 'U') IS NULL
        THROW 51000, 'No existe dbo.Usuario_Catalogo.', 1;

    IF OBJECT_ID('dbo.Usuario_Roles', 'U') IS NULL
        THROW 51000, 'No existe dbo.Usuario_Roles.', 1;

    IF OBJECT_ID('dbo.Usuario_RolesAsignacion', 'U') IS NULL
        THROW 51000, 'No existe dbo.Usuario_RolesAsignacion.', 1;

    IF OBJECT_ID('dbo.Usuario_PermisosRolModulo', 'U') IS NULL
        THROW 51000, 'No existe dbo.Usuario_PermisosRolModulo.', 1;

    DECLARE @RolUsuarioID INT;
    DECLARE @RolOperadorID INT;

    SELECT @RolUsuarioID = RolID
    FROM dbo.Usuario_Roles
    WHERE CodigoRol = 'USUARIO'
      AND Activo = 1;

    SELECT @RolOperadorID = RolID
    FROM dbo.Usuario_Roles
    WHERE CodigoRol = 'OPERADOR'
      AND Activo = 1;

    IF @RolUsuarioID IS NULL
        THROW 51000, 'No existe rol activo USUARIO.', 1;

    IF @RolOperadorID IS NULL
        THROW 51000, 'No existe rol activo OPERADOR.', 1;

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_PermisosRolModulo prm
        INNER JOIN dbo.Usuario_Modulos m
            ON m.ModuloID = prm.ModuloID
            AND m.Activo = 1
        INNER JOIN dbo.Usuario_Acciones a
            ON a.AccionID = prm.AccionID
            AND a.Activo = 1
        WHERE prm.RolID = @RolOperadorID
          AND prm.Activo = 1
          AND prm.Permitido = 1
    )
        THROW 51000, 'El rol OPERADOR no tiene permisos activos permitidos.', 1;

    DECLARE @TargetUsers TABLE (
        UsuarioID INT NOT NULL PRIMARY KEY,
        EsPrincipal BIT NOT NULL
    );

    INSERT INTO @TargetUsers (UsuarioID, EsPrincipal)
    SELECT
        u.UsuarioID,
        MAX(CASE WHEN ura.EsPrincipal = 1 THEN 1 ELSE 0 END) AS EsPrincipal
    FROM dbo.Usuario_Catalogo u
    INNER JOIN dbo.Usuario_RolesAsignacion ura
        ON ura.UsuarioID = u.UsuarioID
        AND ura.RolID = @RolUsuarioID
        AND ura.Activo = 1
    WHERE u.Activo = 1
    GROUP BY u.UsuarioID;

    SELECT
        'TARGET_USUARIO_TO_OPERADOR' AS paso,
        COUNT(*) AS usuarios_objetivo
    FROM @TargetUsers;

    UPDATE ura
    SET
        ura.Activo = 1,
        ura.FechaFin = NULL
    FROM dbo.Usuario_RolesAsignacion ura
    INNER JOIN @TargetUsers t
        ON t.UsuarioID = ura.UsuarioID
    WHERE ura.RolID = @RolOperadorID
      AND ura.Activo = 0
      AND NOT EXISTS (
          SELECT 1
          FROM dbo.Usuario_RolesAsignacion active_operador
          WHERE active_operador.UsuarioID = ura.UsuarioID
            AND active_operador.RolID = @RolOperadorID
            AND active_operador.Activo = 1
      );

    INSERT INTO dbo.Usuario_RolesAsignacion (
        UsuarioID,
        RolID,
        EsPrincipal,
        FechaInicio,
        FechaFin,
        Activo,
        CreatedAt,
        CreatedBy
    )
    SELECT
        t.UsuarioID,
        @RolOperadorID,
        t.EsPrincipal,
        SYSDATETIME(),
        NULL,
        1,
        SYSDATETIME(),
        'RBAC_PHASE2_USUARIO_TO_OPERADOR'
    FROM @TargetUsers t
    WHERE NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_RolesAsignacion ura
        WHERE ura.UsuarioID = t.UsuarioID
          AND ura.RolID = @RolOperadorID
          AND ura.Activo = 1
    );

    UPDATE ura
    SET
        ura.Activo = 0,
        ura.FechaFin = COALESCE(ura.FechaFin, SYSDATETIME())
    FROM dbo.Usuario_RolesAsignacion ura
    INNER JOIN @TargetUsers t
        ON t.UsuarioID = ura.UsuarioID
    WHERE ura.RolID = @RolUsuarioID
      AND ura.Activo = 1
      AND EXISTS (
          SELECT 1
          FROM dbo.Usuario_RolesAsignacion active_operador
          WHERE active_operador.UsuarioID = ura.UsuarioID
            AND active_operador.RolID = @RolOperadorID
            AND active_operador.Activo = 1
      );

    IF EXISTS (
        SELECT 1
        FROM @TargetUsers t
        WHERE NOT EXISTS (
            SELECT 1
            FROM dbo.Usuario_RolesAsignacion ura
            WHERE ura.UsuarioID = t.UsuarioID
              AND ura.RolID = @RolOperadorID
              AND ura.Activo = 1
        )
    )
        THROW 51000, 'Hay usuarios objetivo sin asignacion OPERADOR activa.', 1;

    IF EXISTS (
        SELECT 1
        FROM dbo.Usuario_Catalogo u
        INNER JOIN dbo.Usuario_RolesAsignacion ura_usuario
            ON ura_usuario.UsuarioID = u.UsuarioID
            AND ura_usuario.RolID = @RolUsuarioID
            AND ura_usuario.Activo = 1
        WHERE u.Activo = 1
    )
        THROW 51000, 'Aun existen usuarios activos con asignacion USUARIO activa.', 1;

    UPDATE dbo.Usuario_Roles
    SET
        Activo = 0,
        FechaModificacion = SYSDATETIME()
    WHERE RolID = @RolUsuarioID
      AND Activo = 1
      AND NOT EXISTS (
          SELECT 1
          FROM dbo.Usuario_RolesAsignacion ura
          WHERE ura.RolID = @RolUsuarioID
            AND ura.Activo = 1
      );

    SELECT
        'POST_USUARIO_TO_OPERADOR' AS paso,
        (SELECT COUNT(*)
         FROM dbo.Usuario_RolesAsignacion
         WHERE RolID = @RolOperadorID
           AND Activo = 1) AS asignaciones_operador_activas,
        (SELECT COUNT(*)
         FROM dbo.Usuario_RolesAsignacion
         WHERE RolID = @RolUsuarioID
           AND Activo = 1) AS asignaciones_usuario_activas,
        (SELECT Activo
         FROM dbo.Usuario_Roles
         WHERE RolID = @RolUsuarioID) AS rol_usuario_activo;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
