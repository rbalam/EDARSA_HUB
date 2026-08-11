/*
EDARSAHUB V1.0
Rollback principal tecnico Scheduler / Alertas Estrategicas.

Elimina exclusivamente objetos creados por la migracion
20260811_020_scheduler_alertas_service_principal.sql.

Fail-closed ante conflicto con identidad ajena.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @UsuarioID INT;
    DECLARE @RolID INT;

    SELECT @UsuarioID = UsuarioID
    FROM dbo.Usuario_Catalogo
    WHERE
        UPPER(LTRIM(RTRIM(ISNULL(CodigoUsuario,''))))
            = 'SYS-SCHED-ALERTAS'
        AND UPPER(LTRIM(RTRIM(ISNULL(Username,''))))
            = 'SYS-SCHED-ALERTAS';

    SELECT @RolID = RolID
    FROM dbo.Usuario_Roles
    WHERE
        UPPER(LTRIM(RTRIM(ISNULL(CodigoRol,''))))
            = 'SCHEDULER_ALERTAS';

    IF @UsuarioID IS NULL AND @RolID IS NULL
    BEGIN
        COMMIT TRANSACTION;

        SELECT
            'NOOP' AS Resultado,
            'Principal y rol no existen' AS Detalle;

        RETURN;
    END;

    IF @UsuarioID IS NULL OR @RolID IS NULL
        THROW 51000, 'Estado parcial inesperado; rollback manual requerido.', 1;

    /* Evitar borrar una identidad reutilizada para otro fin. */

    IF EXISTS (
        SELECT 1
        FROM dbo.Usuario_RolesAsignacion
        WHERE UsuarioID = @UsuarioID
          AND RolID <> @RolID
          AND ISNULL(Activo,1) = 1
    )
        THROW 51000, 'Principal posee otro rol activo; rollback abortado.', 1;

    DELETE FROM dbo.Usuario_SucursalesAsignacion
    WHERE UsuarioID = @UsuarioID;

    DELETE FROM dbo.Usuario_ServidoresAsignacion
    WHERE UsuarioID = @UsuarioID;

    DELETE FROM dbo.Usuario_RolesAsignacion
    WHERE UsuarioID = @UsuarioID
      AND RolID = @RolID;

    DELETE FROM dbo.Usuario_PermisosRolModulo
    WHERE RolID = @RolID;

    DELETE FROM dbo.Usuario_Roles
    WHERE RolID = @RolID
      AND CodigoRol = 'SCHEDULER_ALERTAS';

    DELETE FROM dbo.Usuario_Catalogo
    WHERE UsuarioID = @UsuarioID
      AND CodigoUsuario = 'SYS-SCHED-ALERTAS'
      AND Username = 'SYS-SCHED-ALERTAS'
      AND ISNULL(EsUsuarioPortal,1) = 0;

    COMMIT TRANSACTION;

    SELECT
        'PASS' AS Resultado,
        'Principal tecnico Scheduler Alertas eliminado' AS Detalle;

END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
