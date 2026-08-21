SET NOCOUNT ON;
SET XACT_ABORT ON;

IF COL_LENGTH('dbo.Usuario_Roles', 'EsAccesoTotal') IS NULL
    THROW 51042, 'Falta dbo.Usuario_Roles.EsAccesoTotal.', 1;

IF OBJECT_ID('dbo.TR_Usuario_PermisosRolModulo_AutoGrantAccesoTotal', 'TR') IS NULL
    THROW 51043, 'Falta trigger de auto-grant para roles de acceso total.', 1;

IF NOT EXISTS (
    SELECT 1
    FROM dbo.Usuario_Roles
    WHERE CodigoRol = 'SUPERADMIN'
      AND ISNULL(EsAccesoTotal, 0) = 1
      AND ISNULL(Activo, 1) = 1
)
    THROW 51044, 'SUPERADMIN no esta configurado como acceso total.', 1;

;WITH PermisosCanonicos AS (
    SELECT DISTINCT
        prm.ModuloID,
        prm.AccionID
    FROM dbo.Usuario_PermisosRolModulo AS prm
    INNER JOIN dbo.Usuario_Modulos AS m
        ON m.ModuloID = prm.ModuloID
    INNER JOIN dbo.Usuario_Acciones AS a
        ON a.AccionID = prm.AccionID
    WHERE ISNULL(prm.Activo, 1) = 1
      AND ISNULL(prm.Permitido, 0) = 1
      AND ISNULL(m.Activo, 1) = 1
      AND ISNULL(a.Activo, 1) = 1
),
RolesAccesoTotal AS (
    SELECT RolID
    FROM dbo.Usuario_Roles
    WHERE ISNULL(EsAccesoTotal, 0) = 1
      AND ISNULL(Activo, 1) = 1
),
Gaps AS (
    SELECT
        r.RolID,
        pc.ModuloID,
        pc.AccionID
    FROM RolesAccesoTotal AS r
    CROSS JOIN PermisosCanonicos AS pc
    LEFT JOIN dbo.Usuario_PermisosRolModulo AS prm
        ON prm.RolID = r.RolID
       AND prm.ModuloID = pc.ModuloID
       AND prm.AccionID = pc.AccionID
       AND ISNULL(prm.Activo, 1) = 1
       AND ISNULL(prm.Permitido, 0) = 1
       AND ISNULL(prm.RestriccionPropietario, 0) = 0
       AND ISNULL(prm.RestriccionSucursal, 0) = 0
       AND ISNULL(prm.RequiereAutorizacion, 0) = 0
    WHERE prm.RolID IS NULL
)
SELECT *
INTO #FullAccessGaps
FROM Gaps;

IF EXISTS (SELECT 1 FROM #FullAccessGaps)
BEGIN
    SELECT * FROM #FullAccessGaps ORDER BY RolID, ModuloID, AccionID;
    THROW 51045, 'Existen gaps en la matriz de roles de acceso total.', 1;
END;

/*
  Usuario_Catalogo es la fuente canonica vigente para identidad de usuarios.
  Esta verificacion es evidencia de aceptacion del usuario protegido; no forma
  parte de la autorizacion runtime ni introduce bypass por correo.
*/
IF EXISTS (
    SELECT 1
    FROM dbo.Usuario_Catalogo AS u
    INNER JOIN dbo.Usuario_RolesAsignacion AS ura
        ON ura.UsuarioID = u.UsuarioID
    INNER JOIN dbo.Usuario_Roles AS r
        ON r.RolID = ura.RolID
    WHERE LOWER(LTRIM(RTRIM(u.Email))) = 'ricardo@edarsa.com.mx'
      AND ISNULL(u.Activo, 1) = 1
      AND ISNULL(ura.Activo, 1) = 1
      AND ISNULL(r.Activo, 1) = 1
      AND ISNULL(r.EsAccesoTotal, 0) = 1
)
BEGIN
    SELECT
        'PASS' AS Resultado,
        'ricardo@edarsa.com.mx' AS Usuario,
        COUNT(DISTINCT CONCAT(m.CodigoModulo, '_', a.CodigoAccion)) AS PermisosEfectivos
    FROM dbo.Usuario_Catalogo AS u
    INNER JOIN dbo.Usuario_RolesAsignacion AS ura
        ON ura.UsuarioID = u.UsuarioID
    INNER JOIN dbo.Usuario_Roles AS r
        ON r.RolID = ura.RolID
    INNER JOIN dbo.Usuario_PermisosRolModulo AS prm
        ON prm.RolID = r.RolID
    INNER JOIN dbo.Usuario_Modulos AS m
        ON m.ModuloID = prm.ModuloID
    INNER JOIN dbo.Usuario_Acciones AS a
        ON a.AccionID = prm.AccionID
    WHERE LOWER(LTRIM(RTRIM(u.Email))) = 'ricardo@edarsa.com.mx'
      AND ISNULL(u.Activo, 1) = 1
      AND ISNULL(ura.Activo, 1) = 1
      AND ISNULL(r.Activo, 1) = 1
      AND ISNULL(r.EsAccesoTotal, 0) = 1
      AND ISNULL(prm.Activo, 1) = 1
      AND ISNULL(prm.Permitido, 0) = 1
      AND ISNULL(prm.RestriccionPropietario, 0) = 0
      AND ISNULL(prm.RestriccionSucursal, 0) = 0
      AND ISNULL(prm.RequiereAutorizacion, 0) = 0;
END
ELSE
BEGIN
    THROW 51046, 'Ricardo no tiene una asignacion activa a un rol de acceso total.', 1;
END;

IF NOT EXISTS (
    SELECT 1
    FROM dbo.Usuario_PermisosRolModulo AS prm
    INNER JOIN dbo.Usuario_Roles AS r
        ON r.RolID = prm.RolID
    INNER JOIN dbo.Usuario_Modulos AS m
        ON m.ModuloID = prm.ModuloID
    INNER JOIN dbo.Usuario_Acciones AS a
        ON a.AccionID = prm.AccionID
    WHERE ISNULL(r.EsAccesoTotal, 0) = 1
      AND ISNULL(r.Activo, 1) = 1
      AND m.CodigoModulo = 'COMPRAS_FACT'
      AND a.CodigoAccion = 'EJECUTAR'
      AND ISNULL(prm.Permitido, 0) = 1
      AND ISNULL(prm.Activo, 1) = 1
      AND ISNULL(prm.RestriccionPropietario, 0) = 0
      AND ISNULL(prm.RestriccionSucursal, 0) = 0
      AND ISNULL(prm.RequiereAutorizacion, 0) = 0
)
    THROW 51047, 'El rol de acceso total sigue sin COMPRAS_FACT_EJECUTAR efectivo.', 1;

SELECT
    'VALIDATION_OK' AS Resultado,
    r.CodigoRol,
    m.CodigoModulo,
    a.CodigoAccion,
    prm.Permitido,
    prm.Activo,
    prm.RestriccionPropietario,
    prm.RestriccionSucursal,
    prm.RequiereAutorizacion
FROM dbo.Usuario_PermisosRolModulo AS prm
INNER JOIN dbo.Usuario_Roles AS r
    ON r.RolID = prm.RolID
INNER JOIN dbo.Usuario_Modulos AS m
    ON m.ModuloID = prm.ModuloID
INNER JOIN dbo.Usuario_Acciones AS a
    ON a.AccionID = prm.AccionID
WHERE ISNULL(r.EsAccesoTotal, 0) = 1
  AND m.CodigoModulo = 'COMPRAS_FACT'
ORDER BY r.CodigoRol, a.CodigoAccion;
