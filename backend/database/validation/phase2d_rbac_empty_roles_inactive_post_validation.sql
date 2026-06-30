/*
Fase 2D RBAC/Menu post-validation.

Solo lectura. Ejecutar despues de la migracion:
python backend/tools/edarsahub_sql_runner.py --mode validate --script backend/database/validation/phase2d_rbac_empty_roles_inactive_post_validation.sql
*/

SET NOCOUNT ON;
GO

SELECT
    r.RolID,
    r.CodigoRol,
    r.NombreRol,
    r.Activo,
    COUNT(DISTINCT ura.UsuarioRolAsignacionID) AS asignaciones_activas,
    COUNT(DISTINCT CASE WHEN u.Activo = 1 THEN u.UsuarioID END) AS usuarios_activos_asignados,
    COUNT(DISTINCT prm.PermisoRolModuloID) AS permisos_permitidos
FROM dbo.Usuario_Roles r
LEFT JOIN dbo.Usuario_RolesAsignacion ura
    ON ura.RolID = r.RolID
    AND ura.Activo = 1
LEFT JOIN dbo.Usuario_Catalogo u
    ON u.UsuarioID = ura.UsuarioID
LEFT JOIN dbo.Usuario_PermisosRolModulo prm
    ON prm.RolID = r.RolID
    AND prm.Activo = 1
    AND prm.Permitido = 1
WHERE r.CodigoRol IN (
    'COMPRAS',
    'CRM_ADMIN',
    'CRM_AUDIT',
    'CRM_EJEC',
    'GERENTE',
    'TESORERIA',
    'USUARIO',
    'VENTAS'
)
GROUP BY
    r.RolID,
    r.CodigoRol,
    r.NombreRol,
    r.Activo
ORDER BY
    r.CodigoRol;
GO

SELECT
    r.RolID,
    r.CodigoRol,
    r.NombreRol,
    'ROL_VACIO_OBJETIVO_AUN_ACTIVO' AS hallazgo
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
  )
ORDER BY r.CodigoRol;
GO

SELECT
    r.RolID,
    r.CodigoRol,
    r.NombreRol,
    ura.UsuarioRolAsignacionID,
    ura.UsuarioID,
    'ASIGNACION_ACTIVA_EN_ROL_VACIO_INACTIVO' AS hallazgo
FROM dbo.Usuario_Roles r
INNER JOIN dbo.Usuario_RolesAsignacion ura
    ON ura.RolID = r.RolID
    AND ura.Activo = 1
WHERE r.CodigoRol IN (
    'COMPRAS',
    'CRM_ADMIN',
    'CRM_AUDIT',
    'CRM_EJEC',
    'GERENTE',
    'TESORERIA',
    'USUARIO',
    'VENTAS'
)
ORDER BY
    r.CodigoRol,
    ura.UsuarioID;
GO

WITH LegacyMap AS (
    SELECT *
    FROM (VALUES
        ('SuperAdministrador', 'SUPERADMIN'),
        ('Administrador', 'SUPERADMIN'),
        ('Supervisor', 'SUPERVISOR'),
        ('Usuario', 'OPERADOR'),
        ('Gerente', 'GERENTE_OPS'),
        ('Director', 'DIRECCION'),
        ('Auditor', 'AUDITOR'),
        ('Visor', 'OPERADOR')
    ) AS v(RolLegacy, CodigoRolDestino)
),
RolePermissionCounts AS (
    SELECT
        r.RolID,
        r.CodigoRol,
        r.NombreRol,
        r.NivelJerarquia,
        COUNT(prm.PermisoRolModuloID) AS permisos_permitidos
    FROM dbo.Usuario_Roles r
    LEFT JOIN dbo.Usuario_PermisosRolModulo prm
        ON prm.RolID = r.RolID
        AND prm.Activo = 1
        AND prm.Permitido = 1
    WHERE r.Activo = 1
    GROUP BY
        r.RolID,
        r.CodigoRol,
        r.NombreRol,
        r.NivelJerarquia
)
SELECT
    lm.RolLegacy,
    lm.CodigoRolDestino,
    rpc.RolID,
    rpc.NombreRol,
    rpc.NivelJerarquia,
    COALESCE(rpc.permisos_permitidos, 0) AS permisos_permitidos,
    CASE
        WHEN rpc.RolID IS NULL THEN 'CRITICO_ROL_DESTINO_NO_EXISTE'
        WHEN rpc.permisos_permitidos = 0 THEN 'CRITICO_ROL_DESTINO_SIN_PERMISOS'
        ELSE 'OK'
    END AS estado_mapeo_legacy
FROM LegacyMap lm
LEFT JOIN RolePermissionCounts rpc
    ON rpc.CodigoRol = lm.CodigoRolDestino
ORDER BY lm.RolLegacy;
GO
