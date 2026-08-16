SET NOCOUNT ON;

DECLARE @ModuloID int;
DECLARE @VerID smallint;
DECLARE @ConfigurarID smallint;

SELECT @ModuloID = ModuloID
FROM dbo.Usuario_Modulos
WHERE LOWER(CodigoModulo)
      = 'comercial.costos_margenes'
  AND ISNULL(Activo, 1) = 1;

IF @ModuloID IS NULL
    THROW 51040, 'Modulo Costos/Margenes no existe.', 1;

SELECT @VerID = AccionID
FROM dbo.Usuario_Acciones
WHERE UPPER(CodigoAccion) = 'VER'
  AND ISNULL(Activo, 1) = 1;

SELECT @ConfigurarID = AccionID
FROM dbo.Usuario_Acciones
WHERE UPPER(CodigoAccion) = 'CONFIGURAR'
  AND ISNULL(Activo, 1) = 1;

IF @VerID IS NULL
    THROW 51041, 'VER no existe.', 1;

IF @ConfigurarID IS NULL
    THROW 51042, 'CONFIGURAR no existe.', 1;

/*
    ADMIN_COMERCIAL:
    VER + CONFIGURAR
*/
IF (
    SELECT COUNT_BIG(*)
    FROM dbo.Usuario_PermisosRolModulo prm
    INNER JOIN dbo.Usuario_Roles r
        ON r.RolID = prm.RolID
    WHERE prm.ModuloID = @ModuloID
      AND UPPER(r.CodigoRol) = 'ADMIN_COMERCIAL'
      AND prm.AccionID IN (
          @VerID,
          @ConfigurarID
      )
      AND ISNULL(prm.Activo, 1) = 1
      AND ISNULL(prm.Permitido, 0) = 1
) <> 2
    THROW 51043, 'ADMIN_COMERCIAL no tiene VER + CONFIGURAR.', 1;

/*
    CONFIGURADOR_COMERCIAL:
    VER + CONFIGURAR
*/
IF (
    SELECT COUNT_BIG(*)
    FROM dbo.Usuario_PermisosRolModulo prm
    INNER JOIN dbo.Usuario_Roles r
        ON r.RolID = prm.RolID
    WHERE prm.ModuloID = @ModuloID
      AND UPPER(r.CodigoRol)
          = 'CONFIGURADOR_COMERCIAL'
      AND prm.AccionID IN (
          @VerID,
          @ConfigurarID
      )
      AND ISNULL(prm.Activo, 1) = 1
      AND ISNULL(prm.Permitido, 0) = 1
) <> 2
    THROW 51044, 'CONFIGURADOR_COMERCIAL no tiene VER + CONFIGURAR.', 1;

/*
    SUPERADMIN:
    VER + CONFIGURAR
*/
IF (
    SELECT COUNT_BIG(*)
    FROM dbo.Usuario_PermisosRolModulo prm
    INNER JOIN dbo.Usuario_Roles r
        ON r.RolID = prm.RolID
    WHERE prm.ModuloID = @ModuloID
      AND UPPER(r.CodigoRol) = 'SUPERADMIN'
      AND prm.AccionID IN (
          @VerID,
          @ConfigurarID
      )
      AND ISNULL(prm.Activo, 1) = 1
      AND ISNULL(prm.Permitido, 0) = 1
) <> 2
    THROW 51045, 'SUPERADMIN no tiene VER + CONFIGURAR.', 1;

/*
    No conceder CONFIGURAR por accidente
    a roles generales de lectura.
*/
IF EXISTS
(
    SELECT 1
    FROM dbo.Usuario_PermisosRolModulo prm
    INNER JOIN dbo.Usuario_Roles r
        ON r.RolID = prm.RolID
    WHERE prm.ModuloID = @ModuloID
      AND prm.AccionID = @ConfigurarID
      AND UPPER(r.CodigoRol)
          IN (
              'ADMIN',
              'GERENCIA',
              'GERENTE_UNIDAD',
              'OPERADOR',
              'PRUEBA_RBAC_SQL'
          )
      AND ISNULL(prm.Activo, 1) = 1
      AND ISNULL(prm.Permitido, 0) = 1
)
    THROW 51046, 'Rol no autorizado recibió CONFIGURAR.', 1;

SELECT
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
WHERE prm.ModuloID = @ModuloID
  AND UPPER(r.CodigoRol)
      IN (
          'ADMIN_COMERCIAL',
          'CONFIGURADOR_COMERCIAL',
          'SUPERADMIN'
      )
  AND a.AccionID IN (
      @VerID,
      @ConfigurarID
  )
  AND ISNULL(prm.Activo, 1) = 1
  AND ISNULL(prm.Permitido, 0) = 1
ORDER BY
    r.CodigoRol,
    a.CodigoAccion;

PRINT 'VALIDATION_RBAC_COSTOS_MARGENES_CONFIGURAR=PASS';
