SET NOCOUNT ON;

DECLARE @DavidID INT;
DECLARE @CarlosID INT;
DECLARE @GerenciaID INT;
DECLARE @DireccionID INT;

SELECT
    @DavidID = UsuarioID
FROM dbo.Usuario_Catalogo
WHERE Email = 'david.ricardez@cienfuegos.mx'
  AND Activo = 1;

SELECT
    @CarlosID = UsuarioID
FROM dbo.Usuario_Catalogo
WHERE Email = 'carlos@alpuntoycoma.mx'
  AND Activo = 1;

SELECT
    @GerenciaID = RolID
FROM dbo.Usuario_Roles
WHERE CodigoRol = 'GERENCIA'
  AND Activo = 1;

SELECT
    @DireccionID = RolID
FROM dbo.Usuario_Roles
WHERE CodigoRol = 'DIRECCION'
  AND Activo = 1;

IF (
    SELECT COUNT(*)
    FROM dbo.Usuario_RolesContexto
    WHERE UsuarioID = @DavidID
      AND RolID = @GerenciaID
      AND Activo = 1
      AND FechaBaja IS NULL
) <> 5
    THROW 51610,
    'David no tiene cinco contextos GERENCIA activos.',
    1;

IF (
    SELECT COUNT(*)
    FROM dbo.Usuario_RolesContexto
    WHERE UsuarioID = @CarlosID
      AND RolID = @DireccionID
      AND Activo = 1
      AND FechaBaja IS NULL
) <> 5
    THROW 51611,
    'Carlos no tiene cinco contextos DIRECCION activos.',
    1;

IF EXISTS (
    SELECT 1
    FROM dbo.Unidades_Negocio AS UN
    WHERE UN.activo = 1
      AND NOT EXISTS (
            SELECT 1
            FROM dbo.Usuario_RolesContexto AS URC
            WHERE URC.UsuarioID = @DavidID
              AND URC.RolID = @GerenciaID
              AND URC.UnidadNegocioID = UN.id
              AND URC.Activo = 1
              AND URC.FechaBaja IS NULL
      )
)
    THROW 51612,
    'Falta GERENCIA de David en una unidad activa.',
    1;

IF EXISTS (
    SELECT 1
    FROM dbo.Unidades_Negocio AS UN
    WHERE UN.activo = 1
      AND NOT EXISTS (
            SELECT 1
            FROM dbo.Usuario_RolesContexto AS URC
            WHERE URC.UsuarioID = @CarlosID
              AND URC.RolID = @DireccionID
              AND URC.UnidadNegocioID = UN.id
              AND URC.Activo = 1
              AND URC.FechaBaja IS NULL
      )
)
    THROW 51613,
    'Falta DIRECCION de Carlos en una unidad activa.',
    1;

SELECT
    U.NombreCompleto,
    U.Email,
    R.CodigoRol,
    UN.codigo AS UnidadCodigo,
    UN.nombre AS UnidadNombre,
    URC.EsRolPrimario,
    URC.Activo
FROM dbo.Usuario_RolesContexto AS URC
INNER JOIN dbo.Usuario_Catalogo AS U
    ON U.UsuarioID = URC.UsuarioID
INNER JOIN dbo.Usuario_Roles AS R
    ON R.RolID = URC.RolID
INNER JOIN dbo.Unidades_Negocio AS UN
    ON UN.id = URC.UnidadNegocioID
WHERE (
        U.UsuarioID = @DavidID
        AND R.RolID = @GerenciaID
      )
   OR (
        U.UsuarioID = @CarlosID
        AND R.RolID = @DireccionID
      )
ORDER BY
    R.CodigoRol,
    UN.orden,
    UN.nombre;
