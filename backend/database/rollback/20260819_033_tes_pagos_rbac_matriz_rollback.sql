SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

DECLARE @ModuloID INT;
DECLARE @TipoAutorizacionID SMALLINT;

DECLARE @AccionAutorizarID SMALLINT;
DECLARE @AccionRechazarID SMALLINT;
DECLARE @AccionEjecutarID SMALLINT;

DECLARE @CountMatches INT;

/* =========================================================================
   1. RESOLUCION DINAMICA DE OBJETOS A REVERTIR
   ========================================================================= */

SELECT @CountMatches = COUNT(*) FROM dbo.Usuario_Modulos WHERE CodigoModulo = 'TES_PAGOS';
IF @CountMatches = 1
    SELECT @ModuloID = ModuloID FROM dbo.Usuario_Modulos WHERE CodigoModulo = 'TES_PAGOS';

SELECT @CountMatches = COUNT(*) FROM dbo.Usuario_TiposAutorizacion WHERE CodigoTipoAutorizacion = 'AUT_TES_PAGOS';
IF @CountMatches = 1
    SELECT @TipoAutorizacionID = TipoAutorizacionID FROM dbo.Usuario_TiposAutorizacion WHERE CodigoTipoAutorizacion = 'AUT_TES_PAGOS';

SELECT @AccionAutorizarID = AccionID FROM dbo.Usuario_Acciones WHERE CodigoAccion = 'AUTORIZAR';
SELECT @AccionRechazarID = AccionID FROM dbo.Usuario_Acciones WHERE CodigoAccion = 'RECHAZAR';
SELECT @AccionEjecutarID = AccionID FROM dbo.Usuario_Acciones WHERE CodigoAccion = 'EJECUTAR';


/* =========================================================================
   2. REVERSION QUIRURGICA TRANSACCIONAL
   ========================================================================= */

BEGIN TRY
    BEGIN TRANSACTION;

    -- 2.1 Revertir matriz de autorizacion AUT_TES_PAGOS
    IF @TipoAutorizacionID IS NOT NULL
    BEGIN
        DELETE FROM dbo.Usuario_MatrizAutorizacion
        WHERE TipoAutorizacionID = @TipoAutorizacionID;
    END;

    -- 2.2 Revertir permisos de TES_PAGOS para AUTORIZAR, RECHAZAR, EJECUTAR
    -- Preservando cualquier permiso VER u otras acciones
    IF @ModuloID IS NOT NULL
    BEGIN
        DELETE FROM dbo.Usuario_PermisosRolModulo
        WHERE ModuloID = @ModuloID
          AND AccionID IN (
              ISNULL(@AccionAutorizarID, -1),
              ISNULL(@AccionRechazarID, -1),
              ISNULL(@AccionEjecutarID, -1)
          );
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO
