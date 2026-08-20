SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @TipoAutorizacionID SMALLINT;
    DECLARE @RolGerenciaID INT;
    DECLARE @RolDireccionID INT;

    SELECT
        @TipoAutorizacionID = TipoAutorizacionID
    FROM dbo.Usuario_TiposAutorizacion
    WHERE CodigoTipoAutorizacion = 'AUT_TES_PAGOS'
      AND Activo = 1;

    IF @TipoAutorizacionID IS NULL
        THROW 51410,
        'AUT_TES_PAGOS inexistente o inactivo.',
        1;

    IF (
        SELECT COUNT(*)
        FROM dbo.Usuario_TiposAutorizacion
        WHERE CodigoTipoAutorizacion = 'AUT_TES_PAGOS'
          AND Activo = 1
    ) <> 1
        THROW 51411,
        'AUT_TES_PAGOS no es unico entre tipos activos.',
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
        THROW 51412,
        'Rol GERENCIA inexistente o inactivo.',
        1;

    IF @RolDireccionID IS NULL
        THROW 51413,
        'Rol DIRECCION inexistente o inactivo.',
        1;

    IF (
        SELECT COUNT(*)
        FROM dbo.Usuario_MatrizAutorizacion
        WHERE TipoAutorizacionID = @TipoAutorizacionID
          AND Activo = 1
    ) <> 2
        THROW 51414,
        'AUT_TES_PAGOS debe tener exactamente dos filas activas antes de converger.',
        1;

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_MatrizAutorizacion
        WHERE TipoAutorizacionID = @TipoAutorizacionID
          AND RolID = @RolGerenciaID
          AND NivelAutorizacion = 1
          AND Activo = 1
    )
        THROW 51415,
        'No existe la fila canonica GERENCIA nivel 1.',
        1;

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_MatrizAutorizacion
        WHERE TipoAutorizacionID = @TipoAutorizacionID
          AND RolID = @RolDireccionID
          AND NivelAutorizacion = 2
          AND Activo = 1
    )
        THROW 51416,
        'No existe la fila canonica DIRECCION nivel 2.',
        1;

    UPDATE dbo.Usuario_TiposAutorizacion
    SET ModoAutorizacion = 'MANCOMUNADA'
    WHERE TipoAutorizacionID = @TipoAutorizacionID
      AND ModoAutorizacion <> 'MANCOMUNADA';

    UPDATE dbo.Usuario_MatrizAutorizacion
    SET
        MontoMinimo = 0.01,
        MontoMaximo = NULL,
        RequiereTodosLosNiveles = 1
    WHERE TipoAutorizacionID = @TipoAutorizacionID
      AND RolID IN (
            @RolGerenciaID,
            @RolDireccionID
      )
      AND Activo = 1;

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
        THROW 51417,
        'No convergieron ambas filas de la matriz mancomunada.',
        1;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
