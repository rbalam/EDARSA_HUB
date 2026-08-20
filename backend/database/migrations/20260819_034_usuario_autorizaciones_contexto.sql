SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

/* =========================================================================
   1. EXTENSION DE SCHEMA: RequiereUnidadNegocio EN Usuario_TiposAutorizacion
   ========================================================================= */

IF COL_LENGTH('dbo.Usuario_TiposAutorizacion', 'RequiereUnidadNegocio') IS NULL
BEGIN
    ALTER TABLE dbo.Usuario_TiposAutorizacion
        ADD RequiereUnidadNegocio BIT NOT NULL
        CONSTRAINT DF_Usuario_TiposAutorizacion_RequiereUnidadNegocio DEFAULT (0);
END;
GO

/* =========================================================================
   2. CONFIGURACION DINAMICA: AUT_TES_PAGOS REQUIERE CONTEXTO DE UNIDAD
   ========================================================================= */

UPDATE dbo.Usuario_TiposAutorizacion
SET RequiereUnidadNegocio = 1
WHERE CodigoTipoAutorizacion = 'AUT_TES_PAGOS';
GO

/* =========================================================================
   3. EXTENSION DEL MOTOR: sp_Usuario_CrearAutorizacion CONTEXTUAL
   ========================================================================= */

CREATE OR ALTER PROCEDURE dbo.sp_Usuario_CrearAutorizacion
    @FolioAutorizacion VARCHAR(30),
    @TipoAutorizacionCodigo VARCHAR(30),
    @EntidadNombre VARCHAR(100),
    @EntidadID VARCHAR(100) = NULL,
    @FolioReferencia VARCHAR(50) = NULL,
    @UsuarioSolicitanteID INT = NULL,
    @Monto DECIMAL(18,2) = NULL,
    @MonedaID SMALLINT = NULL,
    @Justificacion VARCHAR(2000),
    @UnidadNegocioID UNIQUEIDENTIFIER = NULL,
    @AutorizacionID BIGINT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @TipoAutorizacionID SMALLINT;
    DECLARE @ModuloID INT;
    DECLARE @AccionID SMALLINT;
    DECLARE @RequiereUnidadNegocio BIT;
    DECLARE @NivelFinalRequerido SMALLINT;
    DECLARE @DetallesEsperados INT;
    DECLARE @DetallesCreados INT;

    IF @UsuarioSolicitanteID IS NULL
        SELECT @UsuarioSolicitanteID = TRY_CONVERT(INT, SESSION_CONTEXT(N'UsuarioID'));

    IF @UsuarioSolicitanteID IS NULL
        THROW 51032, 'Usuario solicitante requerido.', 1;

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_Catalogo
        WHERE UsuarioID = @UsuarioSolicitanteID
          AND Activo = 1
    )
        THROW 51033, 'Usuario solicitante inexistente o inactivo.', 1;

    SELECT
        @TipoAutorizacionID = TipoAutorizacionID,
        @ModuloID = ModuloID,
        @AccionID = AccionID,
        @RequiereUnidadNegocio = RequiereUnidadNegocio
    FROM dbo.Usuario_TiposAutorizacion
    WHERE CodigoTipoAutorizacion = @TipoAutorizacionCodigo
      AND Activo = 1;

    IF @TipoAutorizacionID IS NULL
        THROW 51034, 'Tipo de autorizacion no existe o esta inactivo.', 1;

    IF @RequiereUnidadNegocio = 1 AND @UnidadNegocioID IS NULL
        THROW 51046, 'La autorizacion requiere especificar una unidad de negocio.', 1;

    IF @UnidadNegocioID IS NOT NULL AND NOT EXISTS (
        SELECT 1
        FROM dbo.Unidades_Negocio
        WHERE id = @UnidadNegocioID
          AND activo = 1
    )
        THROW 51045, 'Unidad de negocio inexistente o inactiva.', 1;

    SELECT @NivelFinalRequerido = MAX(NivelAutorizacion)
    FROM dbo.Usuario_MatrizAutorizacion
    WHERE TipoAutorizacionID = @TipoAutorizacionID
      AND Activo = 1
      AND (
            @Monto IS NULL
            OR (
                (MontoMinimo IS NULL OR @Monto >= MontoMinimo)
                AND (MontoMaximo IS NULL OR @Monto <= MontoMaximo)
            )
      );

    IF @NivelFinalRequerido IS NULL
        THROW 51035, 'No existe matriz de autorizacion aplicable.', 1;

    SELECT @DetallesEsperados = COUNT(*)
    FROM dbo.Usuario_MatrizAutorizacion AS MA
    OUTER APPLY (
        SELECT TOP 1 urc.UsuarioID
        FROM dbo.Usuario_RolesContexto AS urc
        WHERE urc.RolID = MA.RolID
          AND urc.Activo = 1
          AND (urc.FechaBaja IS NULL OR urc.FechaBaja > SYSDATETIME())
          AND (
                (@UnidadNegocioID IS NOT NULL AND (urc.UnidadNegocioID = @UnidadNegocioID OR urc.UnidadNegocioID IS NULL))
                OR (@UnidadNegocioID IS NULL AND urc.UnidadNegocioID IS NULL)
          )
        ORDER BY
            CASE WHEN @UnidadNegocioID IS NOT NULL AND urc.UnidadNegocioID = @UnidadNegocioID THEN 0 ELSE 1 END,
            urc.EsRolPrimario DESC,
            urc.UsuarioRolContextoID
    ) AS RolAsignado
    INNER JOIN dbo.Usuario_Catalogo AS Autorizador
        ON Autorizador.UsuarioID = ISNULL(MA.UsuarioID, RolAsignado.UsuarioID)
       AND Autorizador.Activo = 1
    WHERE MA.TipoAutorizacionID = @TipoAutorizacionID
      AND MA.Activo = 1
      AND (
            @Monto IS NULL
            OR (
                (MA.MontoMinimo IS NULL OR @Monto >= MA.MontoMinimo)
                AND (MA.MontoMaximo IS NULL OR @Monto <= MA.MontoMaximo)
            )
      );

    IF @DetallesEsperados = 0
        THROW 51036, 'La matriz aplicable no tiene autorizadores activos.', 1;

    IF EXISTS (
        SELECT 1
        FROM dbo.Usuario_MatrizAutorizacion AS MA
        OUTER APPLY (
            SELECT TOP 1 urc.UsuarioID
            FROM dbo.Usuario_RolesContexto AS urc
            WHERE urc.RolID = MA.RolID
              AND urc.Activo = 1
              AND (urc.FechaBaja IS NULL OR urc.FechaBaja > SYSDATETIME())
              AND (
                    (@UnidadNegocioID IS NOT NULL AND (urc.UnidadNegocioID = @UnidadNegocioID OR urc.UnidadNegocioID IS NULL))
                    OR (@UnidadNegocioID IS NULL AND urc.UnidadNegocioID IS NULL)
              )
            ORDER BY
                CASE WHEN @UnidadNegocioID IS NOT NULL AND urc.UnidadNegocioID = @UnidadNegocioID THEN 0 ELSE 1 END,
                urc.EsRolPrimario DESC,
                urc.UsuarioRolContextoID
        ) AS RolAsignado
        LEFT JOIN dbo.Usuario_Catalogo AS Autorizador
            ON Autorizador.UsuarioID = ISNULL(MA.UsuarioID, RolAsignado.UsuarioID)
           AND Autorizador.Activo = 1
        WHERE MA.TipoAutorizacionID = @TipoAutorizacionID
          AND MA.Activo = 1
          AND (
                @Monto IS NULL
                OR (
                    (MA.MontoMinimo IS NULL OR @Monto >= MA.MontoMinimo)
                    AND (MA.MontoMaximo IS NULL OR @Monto <= MA.MontoMaximo)
                )
          )
          AND Autorizador.UsuarioID IS NULL
    )
        THROW 51037, 'La matriz aplicable contiene autorizadores inexistentes o inactivos.', 1;

    BEGIN TRY
        BEGIN TRANSACTION;

        INSERT INTO dbo.Usuario_Autorizaciones (
            FolioAutorizacion, TipoAutorizacionID, ModuloID, AccionID,
            EntidadNombre, EntidadID, FolioReferencia, UsuarioSolicitanteID,
            FechaSolicitud, Monto, MonedaID, Justificacion,
            EstatusAutorizacion, NivelActual, NivelFinalRequerido, Activo,
            CreatedAt, CreatedBy
        )
        VALUES (
            @FolioAutorizacion, @TipoAutorizacionID, @ModuloID, @AccionID,
            @EntidadNombre, @EntidadID, @FolioReferencia, @UsuarioSolicitanteID,
            SYSDATETIME(), @Monto, @MonedaID, @Justificacion,
            'PENDIENTE', 1, @NivelFinalRequerido, 1,
            SYSDATETIME(), CONVERT(VARCHAR(100), @UsuarioSolicitanteID)
        );

        SET @AutorizacionID = SCOPE_IDENTITY();

        INSERT INTO dbo.Usuario_AutorizacionesDetalle (
            AutorizacionID, NivelAutorizacion, UsuarioAutorizadorID, RolID,
            FechaAsignacion, Resultado, Activo
        )
        SELECT
            @AutorizacionID,
            MA.NivelAutorizacion,
            ISNULL(MA.UsuarioID, RolAsignado.UsuarioID),
            MA.RolID,
            SYSDATETIME(),
            'PENDIENTE',
            1
        FROM dbo.Usuario_MatrizAutorizacion AS MA
        OUTER APPLY (
            SELECT TOP 1 urc.UsuarioID
            FROM dbo.Usuario_RolesContexto AS urc
            WHERE urc.RolID = MA.RolID
              AND urc.Activo = 1
              AND (urc.FechaBaja IS NULL OR urc.FechaBaja > SYSDATETIME())
              AND (
                    (@UnidadNegocioID IS NOT NULL AND (urc.UnidadNegocioID = @UnidadNegocioID OR urc.UnidadNegocioID IS NULL))
                    OR (@UnidadNegocioID IS NULL AND urc.UnidadNegocioID IS NULL)
              )
            ORDER BY
                CASE WHEN @UnidadNegocioID IS NOT NULL AND urc.UnidadNegocioID = @UnidadNegocioID THEN 0 ELSE 1 END,
                urc.EsRolPrimario DESC,
                urc.UsuarioRolContextoID
        ) AS RolAsignado
        INNER JOIN dbo.Usuario_Catalogo AS Autorizador
            ON Autorizador.UsuarioID = ISNULL(MA.UsuarioID, RolAsignado.UsuarioID)
           AND Autorizador.Activo = 1
        WHERE MA.TipoAutorizacionID = @TipoAutorizacionID
          AND MA.Activo = 1
          AND (
                @Monto IS NULL
                OR (
                    (MA.MontoMinimo IS NULL OR @Monto >= MA.MontoMinimo)
                    AND (MA.MontoMaximo IS NULL OR @Monto <= MA.MontoMaximo)
                )
          );

        SET @DetallesCreados = @@ROWCOUNT;

        IF @DetallesCreados <> @DetallesEsperados
            THROW 51038, 'La solicitud no contiene todos los detalles requeridos.', 1;

        EXEC dbo.sp_Usuario_LogActividad
            @UsuarioID = @UsuarioSolicitanteID,
            @ModuloCodigo = NULL,
            @AccionCodigo = 'AUTORIZAR',
            @EntidadNombre = @EntidadNombre,
            @EntidadID = @EntidadID,
            @FolioReferencia = @FolioReferencia,
            @ResumenActividad = 'Solicitud de autorizacion creada',
            @DetalleActividad = @Justificacion,
            @Resultado = 'OK',
            @Criticidad = 'ALTA';

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO
