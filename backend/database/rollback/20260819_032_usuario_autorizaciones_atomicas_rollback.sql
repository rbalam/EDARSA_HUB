SET NOCOUNT ON;
GO

IF OBJECT_ID(N'dbo.sp_Usuario_CrearAutorizacion', N'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Usuario_CrearAutorizacion;
GO

CREATE PROCEDURE dbo.sp_Usuario_CrearAutorizacion
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

    DECLARE @TipoAutorizacionID SMALLINT;
    DECLARE @ModuloID INT;
    DECLARE @AccionID SMALLINT;
    DECLARE @NivelFinalRequerido SMALLINT = NULL;

    IF @UsuarioSolicitanteID IS NULL
        SELECT @UsuarioSolicitanteID = TRY_CONVERT(INT, SESSION_CONTEXT(N'UsuarioID'));

    IF @UsuarioSolicitanteID IS NULL
        SET @UsuarioSolicitanteID = 1;

    SELECT
        @TipoAutorizacionID = TipoAutorizacionID,
        @ModuloID = ModuloID,
        @AccionID = AccionID
    FROM dbo.Usuario_TiposAutorizacion
    WHERE CodigoTipoAutorizacion = @TipoAutorizacionCodigo
      AND Activo = 1;

    IF @TipoAutorizacionID IS NULL
    BEGIN
        RAISERROR('Tipo de autorizacion no existe o esta inactivo.',16,1);
        RETURN;
    END

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

    INSERT INTO dbo.Usuario_Autorizaciones
    (
        FolioAutorizacion,
        TipoAutorizacionID,
        ModuloID,
        AccionID,
        EntidadNombre,
        EntidadID,
        FolioReferencia,
        UsuarioSolicitanteID,
        FechaSolicitud,
        Monto,
        MonedaID,
        Justificacion,
        EstatusAutorizacion,
        NivelActual,
        NivelFinalRequerido,
        Activo,
        CreatedAt,
        CreatedBy
    )
    VALUES
    (
        @FolioAutorizacion,
        @TipoAutorizacionID,
        @ModuloID,
        @AccionID,
        @EntidadNombre,
        @EntidadID,
        @FolioReferencia,
        @UsuarioSolicitanteID,
        SYSDATETIME(),
        @Monto,
        @MonedaID,
        @Justificacion,
        'PENDIENTE',
        1,
        @NivelFinalRequerido,
        1,
        SYSDATETIME(),
        CONVERT(VARCHAR(100), @UsuarioSolicitanteID)
    );

    SET @AutorizacionID = SCOPE_IDENTITY();

    INSERT INTO dbo.Usuario_AutorizacionesDetalle
    (
        AutorizacionID,
        NivelAutorizacion,
        UsuarioAutorizadorID,
        RolID,
        FechaAsignacion,
        Resultado,
        Activo
    )
    SELECT
        @AutorizacionID,
        MA.NivelAutorizacion,
        ISNULL(MA.UsuarioID, URA.UsuarioID) AS UsuarioAutorizadorID,
        MA.RolID,
        SYSDATETIME(),
        'PENDIENTE',
        1
    FROM dbo.Usuario_MatrizAutorizacion MA
    OUTER APPLY
    (
        SELECT TOP 1 URX.UsuarioID
        FROM dbo.Usuario_RolesAsignacion URX
        WHERE URX.RolID = MA.RolID
          AND URX.Activo = 1
        ORDER BY URX.EsPrincipal DESC, URX.UsuarioRolAsignacionID
    ) URA
    WHERE MA.TipoAutorizacionID = @TipoAutorizacionID
      AND MA.Activo = 1
      AND (
            @Monto IS NULL
            OR (
                (MA.MontoMinimo IS NULL OR @Monto >= MA.MontoMinimo)
                AND (MA.MontoMaximo IS NULL OR @Monto <= MA.MontoMaximo)
               )
          );

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
END
GO

IF OBJECT_ID(N'dbo.sp_Usuario_ResolverAutorizacion', N'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Usuario_ResolverAutorizacion;
GO

CREATE PROCEDURE dbo.sp_Usuario_ResolverAutorizacion
    @AutorizacionID BIGINT,
    @UsuarioAutorizadorID INT = NULL,
    @Resultado VARCHAR(20),
    @Comentarios VARCHAR(2000) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @NivelPendiente SMALLINT;
    DECLARE @NivelFinalRequerido SMALLINT;
    DECLARE @EntidadNombre VARCHAR(100);
    DECLARE @EntidadID VARCHAR(100);
    DECLARE @FolioReferencia VARCHAR(50);

    IF @UsuarioAutorizadorID IS NULL
        SELECT @UsuarioAutorizadorID = TRY_CONVERT(INT, SESSION_CONTEXT(N'UsuarioID'));

    IF @UsuarioAutorizadorID IS NULL
        SET @UsuarioAutorizadorID = 1;

    SELECT
        @NivelFinalRequerido = NivelFinalRequerido,
        @EntidadNombre = EntidadNombre,
        @EntidadID = EntidadID,
        @FolioReferencia = FolioReferencia
    FROM dbo.Usuario_Autorizaciones
    WHERE AutorizacionID = @AutorizacionID;

    SELECT TOP 1
        @NivelPendiente = NivelAutorizacion
    FROM dbo.Usuario_AutorizacionesDetalle
    WHERE AutorizacionID = @AutorizacionID
      AND UsuarioAutorizadorID = @UsuarioAutorizadorID
      AND Resultado = 'PENDIENTE'
      AND Activo = 1
    ORDER BY NivelAutorizacion;

    IF @NivelPendiente IS NULL
    BEGIN
        RAISERROR('No hay autorizacion pendiente para este usuario.',16,1);
        RETURN;
    END

    UPDATE dbo.Usuario_AutorizacionesDetalle
    SET
        FechaResolucion = SYSDATETIME(),
        Resultado = @Resultado,
        Comentarios = @Comentarios,
        IPResolucion = CONVERT(VARCHAR(64), SESSION_CONTEXT(N'IPOrigen'))
    WHERE AutorizacionID = @AutorizacionID
      AND UsuarioAutorizadorID = @UsuarioAutorizadorID
      AND NivelAutorizacion = @NivelPendiente
      AND Resultado = 'PENDIENTE';

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
    ELSE
    BEGIN
        IF NOT EXISTS
        (
            SELECT 1
            FROM dbo.Usuario_AutorizacionesDetalle
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
                NivelActual = ISNULL(@NivelPendiente,1) + 1
            WHERE AutorizacionID = @AutorizacionID;
        END
    END

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
END
GO

DECLARE @CrearDefinicion NVARCHAR(MAX) =
    OBJECT_DEFINITION(OBJECT_ID(N'dbo.sp_Usuario_CrearAutorizacion'));
DECLARE @ResolverDefinicion NVARCHAR(MAX) =
    OBJECT_DEFINITION(OBJECT_ID(N'dbo.sp_Usuario_ResolverAutorizacion'));
DECLARE @CrearHash VARCHAR(64) = CONVERT(
    VARCHAR(64),
    HASHBYTES('SHA2_256', CONVERT(VARCHAR(MAX), @CrearDefinicion)),
    2
);
DECLARE @ResolverHash VARCHAR(64) = CONVERT(
    VARCHAR(64),
    HASHBYTES('SHA2_256', CONVERT(VARCHAR(MAX), @ResolverDefinicion)),
    2
);

IF @CrearHash <> '36686195682C3E0BEF6F6ACA9733D27E6622A6CF94C78ED6FF881626B595104E'
    THROW 51057, 'Hash de rollback de sp_Usuario_CrearAutorizacion inesperado.', 1;

IF @ResolverHash <> '55DC7C243AF010A4004E396F14B21F2946599648948BFF53F244587B888F2B22'
    THROW 51058, 'Hash de rollback de sp_Usuario_ResolverAutorizacion inesperado.', 1;
