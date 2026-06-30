/*
EDARSAHUB - RBAC Fase 2D
Desactivar roles vacios sin usuarios activos.

Ejecutar con:
EDARSAHUB_ALLOW_MIGRATIONS=true python backend/tools/edarsahub_sql_runner.py \
  --mode migrate \
  --script backend/database/migrations/20260630_011_desactivar_roles_vacios_sin_usuarios_rbac.sql

Reglas:
- Idempotente.
- No crea usuarios.
- No toca permisos.
- No toca MongoDB.
- Solo desactiva roles explicitamente diagnosticados como vacios y sin usuarios activos.
- Si algun rol objetivo tiene permisos o usuarios activos al momento de ejecutar, aborta.
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

    IF OBJECT_ID('dbo.Usuario_Modulos', 'U') IS NULL
        THROW 51000, 'No existe dbo.Usuario_Modulos.', 1;

    IF OBJECT_ID('dbo.Usuario_Acciones', 'U') IS NULL
        THROW 51000, 'No existe dbo.Usuario_Acciones.', 1;

    DECLARE @RolesObjetivo TABLE (
        RolID INT NOT NULL PRIMARY KEY,
        CodigoRol VARCHAR(30) NOT NULL,
        NombreRol VARCHAR(100) NOT NULL
    );

    INSERT INTO @RolesObjetivo (RolID, CodigoRol, NombreRol)
    SELECT
        r.RolID,
        r.CodigoRol,
        r.NombreRol
    FROM dbo.Usuario_Roles r
    WHERE r.Activo = 1
      AND r.CodigoRol IN (
          'COMPRAS',
          'CRM_ADMIN',
          'CRM_AUDIT',
          'CRM_EJEC',
          'GERENTE',
          'TESORERIA',
          'USUARIO',
          'VENTAS'
      );

    SELECT
        'TARGET_EMPTY_ROLES' AS paso,
        COUNT(*) AS roles_objetivo_activos
    FROM @RolesObjetivo;

    IF EXISTS (
        SELECT 1
        FROM @RolesObjetivo ro
        INNER JOIN dbo.Usuario_PermisosRolModulo prm
            ON prm.RolID = ro.RolID
            AND prm.Activo = 1
            AND prm.Permitido = 1
        INNER JOIN dbo.Usuario_Modulos m
            ON m.ModuloID = prm.ModuloID
            AND m.Activo = 1
        INNER JOIN dbo.Usuario_Acciones a
            ON a.AccionID = prm.AccionID
            AND a.Activo = 1
    )
        THROW 51000, 'Un rol objetivo ya tiene permisos activos permitidos. Abortando.', 1;

    IF EXISTS (
        SELECT 1
        FROM @RolesObjetivo ro
        INNER JOIN dbo.Usuario_RolesAsignacion ura
            ON ura.RolID = ro.RolID
            AND ura.Activo = 1
        INNER JOIN dbo.Usuario_Catalogo u
            ON u.UsuarioID = ura.UsuarioID
            AND u.Activo = 1
    )
        THROW 51000, 'Un rol objetivo tiene usuarios activos asignados. Abortando.', 1;

    DECLARE @AsignacionesDesactivadas INT = 0;
    DECLARE @RolesDesactivados INT = 0;

    UPDATE ura
    SET
        ura.Activo = 0,
        ura.FechaFin = COALESCE(ura.FechaFin, SYSDATETIME())
    FROM dbo.Usuario_RolesAsignacion ura
    INNER JOIN @RolesObjetivo ro
        ON ro.RolID = ura.RolID
    LEFT JOIN dbo.Usuario_Catalogo u
        ON u.UsuarioID = ura.UsuarioID
    WHERE ura.Activo = 1
      AND (u.UsuarioID IS NULL OR u.Activo = 0);

    SET @AsignacionesDesactivadas = @@ROWCOUNT;

    IF EXISTS (
        SELECT 1
        FROM @RolesObjetivo ro
        INNER JOIN dbo.Usuario_RolesAsignacion ura
            ON ura.RolID = ro.RolID
            AND ura.Activo = 1
    )
        THROW 51000, 'Quedan asignaciones activas en roles objetivo. Abortando.', 1;

    UPDATE r
    SET
        r.Activo = 0,
        r.FechaModificacion = SYSDATETIME()
    FROM dbo.Usuario_Roles r
    INNER JOIN @RolesObjetivo ro
        ON ro.RolID = r.RolID
    WHERE r.Activo = 1;

    SET @RolesDesactivados = @@ROWCOUNT;

    SELECT
        'POST_EMPTY_ROLES_DEACTIVATION' AS paso,
        @AsignacionesDesactivadas AS asignaciones_desactivadas,
        @RolesDesactivados AS roles_desactivados;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
