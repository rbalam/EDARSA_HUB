/*
EDARSAHUB - RBAC Fase 2F
Desactivar permisos admin/config sensibles en roles no-superadmin.

Permisos objetivo:
- SLA_CONFIGURAR
- RESPONSABILIDAD_GESTIONAR
- AUDITORIAS_GESTIONAR
- NOTIFICACIONES_CONFIGURAR

Reglas:
- Idempotente.
- No toca SUPERADMIN / SUPERADMINISTRADOR.
- No toca CARGOS_* porque son permisos operativos de negocio.
- No crea usuarios.
- No toca MongoDB.
- Usa modelo canónico SQL.
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
        ('SLA', 'CONFIGURAR'),
        ('RESPONSABILIDAD', 'GESTIONAR'),
        ('AUDITORIAS', 'GESTIONAR'),
        ('NOTIFICACIONES', 'CONFIGURAR');

    DECLARE @PermisosDesactivados INT = 0;

    UPDATE prm
    SET
        prm.Activo = 0,
        prm.Permitido = 0
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
      AND r.CodigoRol NOT IN ('SUPERADMIN', 'SUPERADMINISTRADOR')
      AND prm.Activo = 1
      AND prm.Permitido = 1;

    SET @PermisosDesactivados = @@ROWCOUNT;

    SELECT
        'RBAC_DEACTIVATE_NON_SUPERADMIN_ADMIN_CONFIG_PERMISSIONS' AS paso,
        @PermisosDesactivados AS permisos_desactivados;

    SELECT
        'RBAC_NON_SUPERADMIN_ADMIN_CONFIG_REMAINING' AS paso,
        r.CodigoRol,
        r.NombreRol,
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
    WHERE r.Activo = 1
      AND r.CodigoRol NOT IN ('SUPERADMIN', 'SUPERADMINISTRADOR')
      AND prm.Activo = 1
      AND prm.Permitido = 1
    ORDER BY permiso_normalizado, r.CodigoRol;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
    THROW 51000, @ErrorMessage, 1;
END CATCH;
