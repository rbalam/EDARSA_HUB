SET NOCOUNT ON;

DECLARE @TipoAutorizacionID SMALLINT;
DECLARE @RolGerenciaID INT;
DECLARE @RolDireccionID INT;

SELECT
    @TipoAutorizacionID = TipoAutorizacionID
FROM dbo.Usuario_TiposAutorizacion
WHERE CodigoTipoAutorizacion = 'AUT_TES_PAGOS'
  AND Activo = 1;

IF @TipoAutorizacionID IS NULL
    THROW 51420,
    'AUT_TES_PAGOS inexistente o inactivo.',
    1;

SELECT
    @RolGerenciaID = RolID
FROM dbo.Usuario_Roles
WHERE CodigoRol = 'GERENCIA'
  AND Activo = 1;

SELECT
    @RolDireccionID = RolID
FROM dbo.Usuario_Roles
WHERE CodigoRol = 'DIRECCION'
  AND Activo = 1;

IF @RolGerenciaID IS NULL
    THROW 51421,
    'GERENCIA inexistente o inactivo.',
    1;

IF @RolDireccionID IS NULL
    THROW 51422,
    'DIRECCION inexistente o inactivo.',
    1;

IF NOT EXISTS (
    SELECT 1
    FROM dbo.Usuario_TiposAutorizacion
    WHERE TipoAutorizacionID = @TipoAutorizacionID
      AND ModoAutorizacion = 'MANCOMUNADA'
)
    THROW 51423,
    'AUT_TES_PAGOS no esta MANCOMUNADA.',
    1;

IF (
    SELECT COUNT(*)
    FROM dbo.Usuario_MatrizAutorizacion
    WHERE TipoAutorizacionID = @TipoAutorizacionID
      AND Activo = 1
      AND RolID IN (
            @RolGerenciaID,
            @RolDireccionID
      )
      AND MontoMinimo = 0.01
      AND MontoMaximo IS NULL
      AND RequiereTodosLosNiveles = 1
) <> 2
    THROW 51424,
    'La matriz mancomunada no contiene ambas filas canonicas.',
    1;

IF NOT EXISTS (
    SELECT 1
    FROM dbo.Usuario_MatrizAutorizacion
    WHERE TipoAutorizacionID = @TipoAutorizacionID
      AND RolID = @RolGerenciaID
      AND NivelAutorizacion = 1
      AND Activo = 1
)
    THROW 51425,
    'GERENCIA nivel 1 no encontrada.',
    1;

IF NOT EXISTS (
    SELECT 1
    FROM dbo.Usuario_MatrizAutorizacion
    WHERE TipoAutorizacionID = @TipoAutorizacionID
      AND RolID = @RolDireccionID
      AND NivelAutorizacion = 2
      AND Activo = 1
)
    THROW 51426,
    'DIRECCION nivel 2 no encontrada.',
    1;

SELECT
    TA.CodigoTipoAutorizacion,
    TA.ModoAutorizacion,
    MA.NivelAutorizacion,
    R.CodigoRol,
    MA.MontoMinimo,
    MA.MontoMaximo,
    MA.RequiereTodosLosNiveles,
    MA.Prioridad,
    MA.Activo
FROM dbo.Usuario_TiposAutorizacion AS TA
INNER JOIN dbo.Usuario_MatrizAutorizacion AS MA
    ON MA.TipoAutorizacionID =
       TA.TipoAutorizacionID
INNER JOIN dbo.Usuario_Roles AS R
    ON R.RolID = MA.RolID
WHERE TA.TipoAutorizacionID =
      @TipoAutorizacionID
ORDER BY
    MA.NivelAutorizacion,
    MA.Prioridad;
