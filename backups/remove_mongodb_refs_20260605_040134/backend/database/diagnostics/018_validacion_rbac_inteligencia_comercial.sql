/* ============================================================
   VALIDACIÓN FINAL RBAC INTELIGENCIA_COMERCIAL
   ============================================================ */

DECLARE @ModuloIDVal INT;

SELECT @ModuloIDVal = ModuloID
FROM dbo.Usuario_Modulos
WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL';

-- Permisos activos
SELECT
    'PERMISOS_ACTIVOS' AS tipo,
    r.CodigoRol,
    r.NombreRol,
    a.CodigoAccion,
    a.NombreAccion,
    prm.Activo
FROM dbo.Usuario_PermisosRolModulo prm
INNER JOIN dbo.Usuario_Roles r
    ON r.RolID = prm.RolID
INNER JOIN dbo.Usuario_Acciones a
    ON a.AccionID = prm.AccionID
WHERE prm.ModuloID = @ModuloIDVal
  AND prm.Activo = 1
ORDER BY
    r.NivelJerarquia DESC,
    r.CodigoRol,
    a.CodigoAccion;

-- Permisos inactivos (roles excluidos)
SELECT
    'PERMISOS_INACTIVOS' AS tipo,
    r.CodigoRol,
    r.NombreRol,
    a.CodigoAccion,
    prm.Activo
FROM dbo.Usuario_PermisosRolModulo prm
INNER JOIN dbo.Usuario_Roles r
    ON r.RolID = prm.RolID
INNER JOIN dbo.Usuario_Acciones a
    ON a.AccionID = prm.AccionID
WHERE prm.ModuloID = @ModuloIDVal
  AND prm.Activo = 0
ORDER BY r.CodigoRol, a.CodigoAccion;

-- Verificación roles CRM sin permisos activos
SELECT
    'CRM_SIN_PERMISOS_ACTIVOS' AS tipo,
    r.CodigoRol,
    COUNT(*) AS total_inactivos
FROM dbo.Usuario_PermisosRolModulo prm
INNER JOIN dbo.Usuario_Roles r
    ON r.RolID = prm.RolID
WHERE
    prm.ModuloID = @ModuloIDVal
    AND r.CodigoRol IN ('CRM_ADMIN', 'CRM_EJEC', 'CRM_AUDIT')
    AND prm.Activo = 0
GROUP BY r.CodigoRol;
