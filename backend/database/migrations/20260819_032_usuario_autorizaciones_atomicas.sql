SET NOCOUNT ON;
GO

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
    @AutorizacionID BIGINT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @TipoAutorizacionID SMALLINT;
    DECLARE @ModuloID INT;
    DECLARE @AccionID SMALLINT;
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
        @AccionID = AccionID
    FROM dbo.Usuario_TiposAutorizacion
    WHERE CodigoTipoAutorizacion = @TipoAutorizacionCodigo
      AND Activo = 1;

    IF @TipoAutorizacionID IS NULL
        THROW 51034, 'Tipo de autorizacion no existe o esta inactivo.', 1;

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
        SELECT TOP 1 URA.UsuarioID
        FROM dbo.Usuario_RolesAsignacion AS URA
        WHERE URA.RolID = MA.RolID
          AND URA.Activo = 1
        ORDER BY URA.EsPrincipal DESC, URA.UsuarioRolAsignacionID
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
            SELECT TOP 1 URA.UsuarioID
            FROM dbo.Usuario_RolesAsignacion AS URA
            WHERE URA.RolID = MA.RolID
              AND URA.Activo = 1
            ORDER BY URA.EsPrincipal DESC, URA.UsuarioRolAsignacionID
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
            SELECT TOP 1 URA.UsuarioID
            FROM dbo.Usuario_RolesAsignacion AS URA
            WHERE URA.RolID = MA.RolID
              AND URA.Activo = 1
            ORDER BY URA.EsPrincipal DESC, URA.UsuarioRolAsignacionID
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

CREATE OR ALTER PROCEDURE dbo.sp_Usuario_ResolverAutorizacion
    @AutorizacionID BIGINT,
    @UsuarioAutorizadorID INT = NULL,
    @Resultado VARCHAR(20),
    @Comentarios VARCHAR(2000) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @NivelPendiente SMALLINT;
    DECLARE @NivelFinalRequerido SMALLINT;
    DECLARE @EntidadNombre VARCHAR(100);
    DECLARE @EntidadID VARCHAR(100);
    DECLARE @FolioReferencia VARCHAR(50);

    IF @UsuarioAutorizadorID IS NULL
        SELECT @UsuarioAutorizadorID = TRY_CONVERT(INT, SESSION_CONTEXT(N'UsuarioID'));

    IF @UsuarioAutorizadorID IS NULL
        THROW 51039, 'Usuario autorizador requerido.', 1;

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_Catalogo
        WHERE UsuarioID = @UsuarioAutorizadorID
          AND Activo = 1
    )
        THROW 51040, 'Usuario autorizador inexistente o inactivo.', 1;

    IF @Resultado NOT IN ('AUTORIZADA', 'RECHAZADA')
        THROW 51041, 'Resultado de autorizacion invalido.', 1;

    BEGIN TRY
        BEGIN TRANSACTION;

        SELECT
            @NivelFinalRequerido = NivelFinalRequerido,
            @EntidadNombre = EntidadNombre,
            @EntidadID = EntidadID,
            @FolioReferencia = FolioReferencia
        FROM dbo.Usuario_Autorizaciones WITH (UPDLOCK, HOLDLOCK)
        WHERE AutorizacionID = @AutorizacionID
          AND Activo = 1
          AND EstatusAutorizacion IN ('PENDIENTE', 'EN_PROCESO');

        IF @@ROWCOUNT <> 1
            THROW 51042, 'Autorizacion inexistente o no pendiente.', 1;

        SELECT @NivelPendiente = MIN(NivelAutorizacion)
        FROM dbo.Usuario_AutorizacionesDetalle WITH (UPDLOCK, HOLDLOCK)
        WHERE AutorizacionID = @AutorizacionID
          AND Resultado = 'PENDIENTE'
          AND Activo = 1;

        IF @NivelPendiente IS NULL
            THROW 51043, 'No existe nivel pendiente.', 1;

        UPDATE dbo.Usuario_AutorizacionesDetalle
        SET
            FechaResolucion = SYSDATETIME(),
            Resultado = @Resultado,
            Comentarios = @Comentarios,
            IPResolucion = CONVERT(VARCHAR(64), SESSION_CONTEXT(N'IPOrigen'))
        WHERE AutorizacionID = @AutorizacionID
          AND UsuarioAutorizadorID = @UsuarioAutorizadorID
          AND NivelAutorizacion = @NivelPendiente
          AND Resultado = 'PENDIENTE'
          AND Activo = 1;

        IF @@ROWCOUNT <> 1
            THROW 51044, 'No hay autorizacion pendiente para este usuario.', 1;

        IF @Resultado = 'RECHAZADA'
        BEGIN
            UPDATE dbo.Usuario_Autorizaciones
            SET
                EstatusAutorizacion = 'RECHAZADA',
                FechaResolucionFinal = SYSDATETIME(),
                UsuarioResolucionFinalID = @UsuarioAutorizadorID,
                ComentariosResolucionFinal = @Comentarios
            WHERE AutorizacionID = @AutorizacionID;
        END
        ELSE IF NOT EXISTS (
            SELECT 1
            FROM dbo.Usuario_AutorizacionesDetalle WITH (UPDLOCK, HOLDLOCK)
            WHERE AutorizacionID = @AutorizacionID
              AND Resultado = 'PENDIENTE'
              AND Activo = 1
        )
        BEGIN
            UPDATE dbo.Usuario_Autorizaciones
            SET
                EstatusAutorizacion = 'AUTORIZADA',
                FechaResolucionFinal = SYSDATETIME(),
                UsuarioResolucionFinalID = @UsuarioAutorizadorID,
                ComentariosResolucionFinal = @Comentarios,
                NivelActual = ISNULL(@NivelFinalRequerido, NivelActual)
            WHERE AutorizacionID = @AutorizacionID;
        END
        ELSE
        BEGIN
            UPDATE dbo.Usuario_Autorizaciones
            SET
                EstatusAutorizacion = 'EN_PROCESO',
                NivelActual = @NivelPendiente + 1
            WHERE AutorizacionID = @AutorizacionID;
        END;

        EXEC dbo.sp_Usuario_LogActividad
            @UsuarioID = @UsuarioAutorizadorID,
            @ModuloCodigo = NULL,
            @AccionCodigo = 'AUTORIZAR',
            @EntidadNombre = @EntidadNombre,
            @EntidadID = @EntidadID,
            @FolioReferencia = @FolioReferencia,
            @ResumenActividad = 'Resolucion de autorizacion',
            @DetalleActividad = @Comentarios,
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
