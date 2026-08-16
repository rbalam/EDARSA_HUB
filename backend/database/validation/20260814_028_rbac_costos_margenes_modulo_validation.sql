SET NOCOUNT ON;

PRINT '===== VALIDACION RBAC COSTOS Y MARGENES =====';

DECLARE @ModuloCostosID int;
DECLARE @ModuloComercialID int;
DECLARE @AccionVerID smallint;

SELECT @ModuloCostosID = ModuloID
FROM dbo.Usuario_Modulos
WHERE LOWER(CodigoModulo) = 'comercial.costos_margenes'
  AND ISNULL(Activo, 1) = 1;

IF @ModuloCostosID IS NULL
    THROW 51010, 'Falta modulo comercial.costos_margenes.', 1;

SELECT @ModuloComercialID = ModuloID
FROM dbo.Usuario_Modulos
WHERE LOWER(CodigoModulo) = 'comercial'
  AND ISNULL(Activo, 1) = 1;

IF @ModuloComercialID IS NULL
    THROW 51011, 'Falta modulo comercial.', 1;

SELECT @AccionVerID = AccionID
FROM dbo.Usuario_Acciones
WHERE UPPER(CodigoAccion) = 'VER'
  AND ISNULL(Activo, 1) = 1;

IF @AccionVerID IS NULL
    THROW 51012, 'Falta accion VER.', 1;

IF NOT EXISTS
(
    SELECT 1
    FROM dbo.Usuario_Modulos
    WHERE ModuloID = @ModuloCostosID
      AND ModuloPadreID = @ModuloComercialID
      AND Ruta = '/comercial/costos-margenes'
      AND ISNULL(Activo, 1) = 1
)
    THROW 51013, 'Modulo Costos/Margenes no esta correctamente vinculado.', 1;

/*
    Fuente de lectura actual vs destino.
*/
IF EXISTS
(
    SELECT source.RolID
    FROM dbo.Usuario_PermisosRolModulo source
    WHERE source.ModuloID = @ModuloComercialID
      AND source.AccionID = @AccionVerID
      AND ISNULL(source.Activo, 1) = 1
      AND ISNULL(source.Permitido, 0) = 1

    EXCEPT

    SELECT target.RolID
    FROM dbo.Usuario_PermisosRolModulo target
    WHERE target.ModuloID = @ModuloCostosID
      AND target.AccionID = @AccionVerID
      AND ISNULL(target.Activo, 1) = 1
      AND ISNULL(target.Permitido, 0) = 1
)
    THROW 51014, 'Hay roles con COMERCIAL_VER sin Costos/Margenes_VER.', 1;

IF EXISTS
(
    SELECT target.RolID
    FROM dbo.Usuario_PermisosRolModulo target
    WHERE target.ModuloID = @ModuloCostosID
      AND target.AccionID = @AccionVerID
      AND ISNULL(target.Activo, 1) = 1
      AND ISNULL(target.Permitido, 0) = 1

    EXCEPT

    SELECT source.RolID
    FROM dbo.Usuario_PermisosRolModulo source
    WHERE source.ModuloID = @ModuloComercialID
      AND source.AccionID = @AccionVerID
      AND ISNULL(source.Activo, 1) = 1
      AND ISNULL(source.Permitido, 0) = 1
)
    THROW 51015, 'Costos/Margenes_VER contiene roles no heredados de COMERCIAL_VER.', 1;

/*
    SUPERADMIN no puede quedar por debajo de ADMIN.
*/
IF EXISTS
(
    SELECT 1
    FROM dbo.Usuario_Roles admin_role
    INNER JOIN dbo.Usuario_PermisosRolModulo admin_perm
        ON admin_perm.RolID = admin_role.RolID
       AND admin_perm.ModuloID = @ModuloCostosID
       AND admin_perm.AccionID = @AccionVerID
       AND ISNULL(admin_perm.Activo, 1) = 1
       AND ISNULL(admin_perm.Permitido, 0) = 1
    WHERE UPPER(admin_role.CodigoRol) = 'ADMIN'
)
AND NOT EXISTS
(
    SELECT 1
    FROM dbo.Usuario_Roles super_role
    INNER JOIN dbo.Usuario_PermisosRolModulo super_perm
        ON super_perm.RolID = super_role.RolID
       AND super_perm.ModuloID = @ModuloCostosID
       AND super_perm.AccionID = @AccionVerID
       AND ISNULL(super_perm.Activo, 1) = 1
       AND ISNULL(super_perm.Permitido, 0) = 1
    WHERE UPPER(super_role.CodigoRol) = 'SUPERADMIN'
)
    THROW 51016, 'SUPERADMIN quedo por debajo de ADMIN.', 1;

SELECT
    m.ModuloID,
    m.ModuloPadreID,
    m.CodigoModulo,
    m.NombreModulo,
    m.Ruta,
    m.EsVisibleMenu,
    m.Activo
FROM dbo.Usuario_Modulos m
WHERE m.ModuloID = @ModuloCostosID;

SELECT
    r.RolID,
    r.CodigoRol,
    a.CodigoAccion,
    prm.Permitido,
    prm.RestriccionPropietario,
    prm.RestriccionSucursal,
    prm.RequiereAutorizacion,
    prm.NivelAutorizacionRequerido
FROM dbo.Usuario_PermisosRolModulo prm
INNER JOIN dbo.Usuario_Roles r
    ON r.RolID = prm.RolID
INNER JOIN dbo.Usuario_Acciones a
    ON a.AccionID = prm.AccionID
WHERE prm.ModuloID = @ModuloCostosID
  AND ISNULL(prm.Activo, 1) = 1
ORDER BY
    r.CodigoRol,
    a.CodigoAccion;

PRINT 'VALIDACION_RBAC_COSTOS_MARGENES=PASS';
