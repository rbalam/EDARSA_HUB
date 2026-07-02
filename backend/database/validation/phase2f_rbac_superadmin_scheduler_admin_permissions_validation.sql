/*
Validación RBAC Fase 2F.
Confirma:
- SUPERADMIN tiene RBAC_ADMIN, SCHEDULER_ADMIN, SCHEDULER_GESTIONAR.
- ADMIN no tiene esos permisos administrativos.
*/

SET NOCOUNT ON;

SELECT
    r.CodigoRol,
    m.CodigoModulo,
    a.CodigoAccion,
    CONCAT(m.CodigoModulo, '_', a.CodigoAccion) AS PermisoNormalizado,
    prm.Permitido,
    prm.Activo
FROM dbo.Usuario_Roles r
INNER JOIN dbo.Usuario_PermisosRolModulo prm
    ON prm.RolID = r.RolID
INNER JOIN dbo.Usuario_Modulos m
    ON m.ModuloID = prm.ModuloID
INNER JOIN dbo.Usuario_Acciones a
    ON a.AccionID = prm.AccionID
WHERE r.CodigoRol IN ('SUPERADMIN', 'ADMIN')
  AND (
        (m.CodigoModulo = 'RBAC' AND a.CodigoAccion = 'ADMIN')
     OR (m.CodigoModulo = 'SCHEDULER' AND a.CodigoAccion IN ('ADMIN', 'GESTIONAR'))
  )
ORDER BY r.CodigoRol, m.CodigoModulo, a.CodigoAccion;
