SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

DECLARE @ModuloID INT;
DECLARE @TipoAutorizacionID SMALLINT;

DECLARE @AccionAutorizarID SMALLINT;
DECLARE @AccionRechazarID SMALLINT;
DECLARE @AccionEjecutarID SMALLINT;

DECLARE @RolGerenciaID INT;
DECLARE @RolDireccionID INT;
DECLARE @RolTesoreriaID INT;
DECLARE @RolAdminID INT;
DECLARE @RolSuperAdminID INT;

DECLARE @CountMatches INT;

/* =========================================================================
   1. RESOLUCION DINAMICA FAIL-CLOSED DE MODULO Y TIPO DE AUTORIZACION
   ========================================================================= */

SELECT @CountMatches = COUNT(*)
FROM dbo.Usuario_Modulos
WHERE CodigoModulo = 'TES_PAGOS' AND Activo = 1;

IF @CountMatches <> 1
    THROW 51060, 'Resolucion ambigua o inexistente para modulo TES_PAGOS.', 1;

SELECT @ModuloID = ModuloID
FROM dbo.Usuario_Modulos
WHERE CodigoModulo = 'TES_PAGOS' AND Activo = 1;


SELECT @CountMatches = COUNT(*)
FROM dbo.Usuario_TiposAutorizacion
WHERE CodigoTipoAutorizacion = 'AUT_TES_PAGOS' AND Activo = 1;

IF @CountMatches <> 1
    THROW 51061, 'Resolucion ambigua o inexistente para tipo de autorizacion AUT_TES_PAGOS.', 1;

SELECT @TipoAutorizacionID = TipoAutorizacionID
FROM dbo.Usuario_TiposAutorizacion
WHERE CodigoTipoAutorizacion = 'AUT_TES_PAGOS' AND Activo = 1;


/* =========================================================================
   2. RESOLUCION DINAMICA FAIL-CLOSED DE ACCIONES
   ========================================================================= */

SELECT @CountMatches = COUNT(*) FROM dbo.Usuario_Acciones WHERE CodigoAccion = 'AUTORIZAR' AND Activo = 1;
IF @CountMatches <> 1 THROW 51062, 'Resolucion ambigua o inexistente para accion AUTORIZAR.', 1;
SELECT @AccionAutorizarID = AccionID FROM dbo.Usuario_Acciones WHERE CodigoAccion = 'AUTORIZAR' AND Activo = 1;

SELECT @CountMatches = COUNT(*) FROM dbo.Usuario_Acciones WHERE CodigoAccion = 'RECHAZAR' AND Activo = 1;
IF @CountMatches <> 1 THROW 51063, 'Resolucion ambigua o inexistente para accion RECHAZAR.', 1;
SELECT @AccionRechazarID = AccionID FROM dbo.Usuario_Acciones WHERE CodigoAccion = 'RECHAZAR' AND Activo = 1;

SELECT @CountMatches = COUNT(*) FROM dbo.Usuario_Acciones WHERE CodigoAccion = 'EJECUTAR' AND Activo = 1;
IF @CountMatches <> 1 THROW 51064, 'Resolucion ambigua o inexistente para accion EJECUTAR.', 1;
SELECT @AccionEjecutarID = AccionID FROM dbo.Usuario_Acciones WHERE CodigoAccion = 'EJECUTAR' AND Activo = 1;


/* =========================================================================
   3. RESOLUCION DINAMICA FAIL-CLOSED DE ROLES
   ========================================================================= */

SELECT @CountMatches = COUNT(*) FROM dbo.Usuario_Roles WHERE CodigoRol = 'GERENCIA' AND Activo = 1;
IF @CountMatches <> 1 THROW 51065, 'Resolucion ambigua o inexistente para rol GERENCIA.', 1;
SELECT @RolGerenciaID = RolID FROM dbo.Usuario_Roles WHERE CodigoRol = 'GERENCIA' AND Activo = 1;

SELECT @CountMatches = COUNT(*) FROM dbo.Usuario_Roles WHERE CodigoRol = 'DIRECCION' AND Activo = 1;
IF @CountMatches <> 1 THROW 51066, 'Resolucion ambigua o inexistente para rol DIRECCION.', 1;
SELECT @RolDireccionID = RolID FROM dbo.Usuario_Roles WHERE CodigoRol = 'DIRECCION' AND Activo = 1;

SELECT @CountMatches = COUNT(*) FROM dbo.Usuario_Roles WHERE CodigoRol = 'TESORERIA' AND Activo = 1;
IF @CountMatches <> 1 THROW 51067, 'Resolucion ambigua o inexistente para rol TESORERIA.', 1;
SELECT @RolTesoreriaID = RolID FROM dbo.Usuario_Roles WHERE CodigoRol = 'TESORERIA' AND Activo = 1;

SELECT @CountMatches = COUNT(*) FROM dbo.Usuario_Roles WHERE CodigoRol = 'ADMIN' AND Activo = 1;
IF @CountMatches <> 1 THROW 51068, 'Resolucion ambigua o inexistente para rol ADMIN.', 1;
SELECT @RolAdminID = RolID FROM dbo.Usuario_Roles WHERE CodigoRol = 'ADMIN' AND Activo = 1;

SELECT @CountMatches = COUNT(*) FROM dbo.Usuario_Roles WHERE CodigoRol = 'SUPERADMIN' AND Activo = 1;
IF @CountMatches <> 1 THROW 51069, 'Resolucion ambigua o inexistente para rol SUPERADMIN.', 1;
SELECT @RolSuperAdminID = RolID FROM dbo.Usuario_Roles WHERE CodigoRol = 'SUPERADMIN' AND Activo = 1;


/* =========================================================================
   4. APLICACION TRANSACCIONAL E IDEMPOTENTE
   ========================================================================= */

BEGIN TRY
    BEGIN TRANSACTION;

    -- 4.1 Permisos en dbo.Usuario_PermisosRolModulo (11 filas exactas)
    CREATE TABLE #TargetPermisos (
        RolID INT NOT NULL,
        ModuloID INT NOT NULL,
        AccionID SMALLINT NOT NULL
    );

    INSERT INTO #TargetPermisos (RolID, ModuloID, AccionID) VALUES
        (@RolGerenciaID, @ModuloID, @AccionAutorizarID),
        (@RolGerenciaID, @ModuloID, @AccionRechazarID),
        (@RolDireccionID, @ModuloID, @AccionAutorizarID),
        (@RolDireccionID, @ModuloID, @AccionRechazarID),
        (@RolTesoreriaID, @ModuloID, @AccionEjecutarID),
        (@RolAdminID, @ModuloID, @AccionAutorizarID),
        (@RolAdminID, @ModuloID, @AccionRechazarID),
        (@RolAdminID, @ModuloID, @AccionEjecutarID),
        (@RolSuperAdminID, @ModuloID, @AccionAutorizarID),
        (@RolSuperAdminID, @ModuloID, @AccionRechazarID),
        (@RolSuperAdminID, @ModuloID, @AccionEjecutarID);

    -- Insertar permisos faltantes
    INSERT INTO dbo.Usuario_PermisosRolModulo (
        RolID,
        ModuloID,
        AccionID,
        Permitido,
        RestriccionPropietario,
        RestriccionSucursal,
        RequiereAutorizacion,
        NivelAutorizacionRequerido,
        Activo,
        FechaAlta,
        CreatedBy
    )
    SELECT
        tp.RolID,
        tp.ModuloID,
        tp.AccionID,
        1, -- Permitido
        0, -- RestriccionPropietario
        0, -- RestriccionSucursal
        0, -- RequiereAutorizacion
        NULL, -- NivelAutorizacionRequerido
        1, -- Activo
        SYSDATETIME(),
        'MIGRATION_20260819_033'
    FROM #TargetPermisos tp
    WHERE NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_PermisosRolModulo prm
        WHERE prm.RolID = tp.RolID
          AND prm.ModuloID = tp.ModuloID
          AND prm.AccionID = tp.AccionID
    );

    -- Reactivar/Asegurar permisos si ya existian previamente
    UPDATE prm
    SET
        prm.Permitido = 1,
        prm.Activo = 1,
        prm.RequiereAutorizacion = 0,
        prm.FechaModificacion = SYSDATETIME(),
        prm.ModifiedBy = 'MIGRATION_20260819_033'
    FROM dbo.Usuario_PermisosRolModulo prm
    INNER JOIN #TargetPermisos tp
        ON prm.RolID = tp.RolID
       AND prm.ModuloID = tp.ModuloID
       AND prm.AccionID = tp.AccionID
    WHERE prm.Permitido <> 1 OR prm.Activo <> 1 OR prm.RequiereAutorizacion <> 0;

    DROP TABLE #TargetPermisos;


    -- 4.2 Matriz de Autorizacion en dbo.Usuario_MatrizAutorizacion (2 filas exactas)

    -- Nivel 1: GERENCIA ($0.00 a $50,000.00)
    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_MatrizAutorizacion
        WHERE TipoAutorizacionID = @TipoAutorizacionID
          AND NivelAutorizacion = 1
          AND RolID = @RolGerenciaID
    )
    BEGIN
        INSERT INTO dbo.Usuario_MatrizAutorizacion (
            TipoAutorizacionID,
            NivelAutorizacion,
            RolID,
            UsuarioID,
            MontoMinimo,
            MontoMaximo,
            Prioridad,
            RequiereTodosLosNiveles,
            Activo,
            FechaAlta
        )
        VALUES (
            @TipoAutorizacionID,
            1,
            @RolGerenciaID,
            NULL, -- Resolucion dinamica contextual por unidad
            0.00,
            50000.00,
            1,
            0,
            1,
            SYSDATETIME()
        );
    END
    ELSE
    BEGIN
        UPDATE dbo.Usuario_MatrizAutorizacion
        SET
            UsuarioID = NULL,
            MontoMinimo = 0.00,
            MontoMaximo = 50000.00,
            Prioridad = 1,
            RequiereTodosLosNiveles = 0,
            Activo = 1,
            FechaModificacion = SYSDATETIME()
        WHERE TipoAutorizacionID = @TipoAutorizacionID
          AND NivelAutorizacion = 1
          AND RolID = @RolGerenciaID;
    END;

    -- Nivel 2: DIRECCION (>$50,000.00 / MontoMinimo=50000.01, MontoMaximo=NULL)
    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_MatrizAutorizacion
        WHERE TipoAutorizacionID = @TipoAutorizacionID
          AND NivelAutorizacion = 2
          AND RolID = @RolDireccionID
    )
    BEGIN
        INSERT INTO dbo.Usuario_MatrizAutorizacion (
            TipoAutorizacionID,
            NivelAutorizacion,
            RolID,
            UsuarioID,
            MontoMinimo,
            MontoMaximo,
            Prioridad,
            RequiereTodosLosNiveles,
            Activo,
            FechaAlta
        )
        VALUES (
            @TipoAutorizacionID,
            2,
            @RolDireccionID,
            NULL, -- Resolucion dinamica contextual por unidad
            50000.01,
            NULL,
            1,
            0,
            1,
            SYSDATETIME()
        );
    END
    ELSE
    BEGIN
        UPDATE dbo.Usuario_MatrizAutorizacion
        SET
            UsuarioID = NULL,
            MontoMinimo = 50000.01,
            MontoMaximo = NULL,
            Prioridad = 1,
            RequiereTodosLosNiveles = 0,
            Activo = 1,
            FechaModificacion = SYSDATETIME()
        WHERE TipoAutorizacionID = @TipoAutorizacionID
          AND NivelAutorizacion = 2
          AND RolID = @RolDireccionID;
    END;


    /* =====================================================================
       4.3 POST-CHECK FAIL-CLOSED IN-TRANSACTION
       ===================================================================== */

    -- Confirmar exactamente 11 permisos activos para el modulo TES_PAGOS en estas 3 acciones
    DECLARE @ActivePermCount INT;
    SELECT @ActivePermCount = COUNT(*)
    FROM dbo.Usuario_PermisosRolModulo
    WHERE ModuloID = @ModuloID
      AND AccionID IN (@AccionAutorizarID, @AccionRechazarID, @AccionEjecutarID)
      AND Activo = 1
      AND Permitido = 1;

    IF @ActivePermCount <> 11
        THROW 51070, 'El conteo de permisos activos para TES_PAGOS difiere del contrato esperado (11).', 1;

    -- Confirmar exactamente 2 filas activas en matriz AUT_TES_PAGOS
    DECLARE @ActiveMatrixCount INT;
    SELECT @ActiveMatrixCount = COUNT(*)
    FROM dbo.Usuario_MatrizAutorizacion
    WHERE TipoAutorizacionID = @TipoAutorizacionID
      AND Activo = 1;

    IF @ActiveMatrixCount <> 2
        THROW 51071, 'El conteo de filas en Usuario_MatrizAutorizacion difiere del contrato esperado (2).', 1;

    -- Confirmar que ADMIN y SUPERADMIN NO fueron insertados en la matriz
    IF EXISTS (
        SELECT 1
        FROM dbo.Usuario_MatrizAutorizacion
        WHERE TipoAutorizacionID = @TipoAutorizacionID
          AND RolID IN (@RolAdminID, @RolSuperAdminID)
    )
        THROW 51072, 'Violacion: ADMIN o SUPERADMIN no deben pertenecer a la matriz operativa AUT_TES_PAGOS.', 1;

    -- Confirmar que UsuarioID es estrictamente NULL en la matriz
    IF EXISTS (
        SELECT 1
        FROM dbo.Usuario_MatrizAutorizacion
        WHERE TipoAutorizacionID = @TipoAutorizacionID
          AND UsuarioID IS NOT NULL
    )
        THROW 51073, 'Violacion: UsuarioID en Usuario_MatrizAutorizacion debe ser estrictamente NULL.', 1;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO
