/*
EDARSAHUB - RBAC Fase 2F
Reactiva permisos CARGOS restantes para SUPERADMIN.

Motivo:
- CARGOS_RECHAZAR
- CARGOS_REVERTIR
- CARGOS_CANCELAR

Ahora usan require_explicit_permission(...), por lo que ya no pueden depender
del bypass legacy de require_permission(...).

Reglas:
- Idempotente.
- Solo toca SUPERADMIN / SUPERADMINISTRADOR.
- No toca ADMIN.
- No toca roles operativos.
*/

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
    VALUES
        ('CARGOS', 'RECHAZAR'),
        ('CARGOS', 'REVERTIR'),
        ('CARGOS', 'CANCELAR');

    DECLARE @PermisosReactivados INT = 0;

    UPDATE prm
    SET
        prm.Activo = 1,
        prm.Permitido = 1
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
    WHERE r.Activo = 1
      AND r.CodigoRol IN ('SUPERADMIN', 'SUPERADMINISTRADOR')
      AND (prm.Activo = 0 OR prm.Permitido = 0);

    SET @PermisosReactivados = @@ROWCOUNT;

    SELECT
        'RBAC_SUPERADMIN_CARGOS_REMAINING_ACTIONS' AS paso,
        @PermisosReactivados AS permisos_reactivados;

    SELECT
        r.CodigoRol,
        CONCAT(m.CodigoModulo, '_', a.CodigoAccion) AS Permiso,
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
    WHERE r.CodigoRol IN ('SUPERADMIN', 'SUPERADMINISTRADOR')
    ORDER BY r.CodigoRol, Permiso;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
    THROW 51000, @ErrorMessage, 1;
END CATCH;
