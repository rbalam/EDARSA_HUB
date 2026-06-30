/*
Fase 2C RBAC/Menu post-validation.

Solo lectura. Ejecutar despues de la migracion:
python backend/tools/edarsahub_sql_runner.py --mode validate --script backend/database/validation/phase2c_rbac_usuario_operador_post_validation.sql
*/

SET NOCOUNT ON;
GO

SELECT
    r.CodigoRol,
    r.NombreRol,
    r.Activo,
    COUNT(DISTINCT CASE WHEN u.UsuarioID IS NOT NULL THEN u.UsuarioID END) AS usuarios_activos_asignados,
    COUNT(DISTINCT prm.PermisoRolModuloID) AS permisos_permitidos
FROM dbo.Usuario_Roles r
LEFT JOIN dbo.Usuario_RolesAsignacion ura
    ON ura.RolID = r.RolID
    AND ura.Activo = 1
LEFT JOIN dbo.Usuario_Catalogo u
    ON u.UsuarioID = ura.UsuarioID
    AND u.Activo = 1
LEFT JOIN dbo.Usuario_PermisosRolModulo prm
    ON prm.RolID = r.RolID
    AND prm.Activo = 1
    AND prm.Permitido = 1
WHERE r.CodigoRol IN ('USUARIO', 'OPERADOR')
GROUP BY
    r.CodigoRol,
    r.NombreRol,
    r.Activo
ORDER BY r.CodigoRol;
GO

SELECT
    u.UsuarioID,
    u.Email,
    u.Username,
    u.NombreCompleto,
    'USUARIO_ACTIVO_CON_ROL_USUARIO_ACTIVO' AS hallazgo
FROM dbo.Usuario_Catalogo u
INNER JOIN dbo.Usuario_RolesAsignacion ura
    ON ura.UsuarioID = u.UsuarioID
    AND ura.Activo = 1
INNER JOIN dbo.Usuario_Roles r
    ON r.RolID = ura.RolID
    AND r.CodigoRol = 'USUARIO'
WHERE u.Activo = 1
ORDER BY u.Email;
GO

SELECT
    u.UsuarioID,
    u.Email,
    u.Username,
    u.NombreCompleto,
    'USUARIO_ACTIVO_SIN_OPERADOR_TRAS_MIGRACION' AS hallazgo
FROM dbo.Usuario_Catalogo u
WHERE u.Activo = 1
  AND EXISTS (
      SELECT 1
      FROM dbo.Usuario_RolesAsignacion ura
      INNER JOIN dbo.Usuario_Roles r
          ON r.RolID = ura.RolID
          AND r.CodigoRol = 'USUARIO'
      WHERE ura.UsuarioID = u.UsuarioID
  )
  AND NOT EXISTS (
      SELECT 1
      FROM dbo.Usuario_RolesAsignacion ura
      INNER JOIN dbo.Usuario_Roles r
          ON r.RolID = ura.RolID
          AND r.CodigoRol = 'OPERADOR'
      WHERE ura.UsuarioID = u.UsuarioID
        AND ura.Activo = 1
  )
ORDER BY u.Email;
GO
