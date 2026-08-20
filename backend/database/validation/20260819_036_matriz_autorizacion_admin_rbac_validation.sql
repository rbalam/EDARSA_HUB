SET NOCOUNT ON;

SELECT
    r.CodigoRol,
    m.CodigoModulo,
    a.CodigoAccion,
    prm.Permitido,
    prm.Activo,
    prm.RestriccionPropietario,
    prm.RestriccionSucursal,
    prm.RequiereAutorizacion,
    prm.CreatedBy,
    prm.ModifiedBy
FROM dbo.Usuario_Roles r
INNER JOIN dbo.Usuario_PermisosRolModulo prm
    ON prm.RolID = r.RolID
INNER JOIN dbo.Usuario_Modulos m
    ON m.ModuloID = prm.ModuloID
INNER JOIN dbo.Usuario_Acciones a
    ON a.AccionID = prm.AccionID
WHERE r.CodigoRol = 'SUPERADMIN'
  AND m.CodigoModulo = 'SEGURIDAD'
  AND a.CodigoAccion = 'CONFIGURAR';

SELECT
    CASE
        WHEN COUNT(*) = 1
         AND MAX(CAST(prm.Permitido AS INT)) = 1
         AND MAX(CAST(prm.Activo AS INT)) = 1
        THEN 'PASS'
        ELSE 'FAIL'
    END AS SEGURIDAD_CONFIGURAR_SUPERADMIN
FROM dbo.Usuario_Roles r
INNER JOIN dbo.Usuario_PermisosRolModulo prm
    ON prm.RolID = r.RolID
INNER JOIN dbo.Usuario_Modulos m
    ON m.ModuloID = prm.ModuloID
INNER JOIN dbo.Usuario_Acciones a
    ON a.AccionID = prm.AccionID
WHERE r.CodigoRol = 'SUPERADMIN'
  AND m.CodigoModulo = 'SEGURIDAD'
  AND a.CodigoAccion = 'CONFIGURAR';
