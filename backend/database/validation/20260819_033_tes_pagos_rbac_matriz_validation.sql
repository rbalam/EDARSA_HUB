SET NOCOUNT ON;
GO

IF DB_NAME() <> N'EDARSAHUB'
    THROW 51080, 'Base de datos inesperada. Se esperaba EDARSAHUB.', 1;

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
   1. VALIDACION DE CATALOGOS BASE
   ========================================================================= */

SELECT @CountMatches = COUNT(*) FROM dbo.Usuario_Modulos WHERE CodigoModulo = 'TES_PAGOS' AND Activo = 1;
IF @CountMatches <> 1 THROW 51081, 'Modulo TES_PAGOS no encontrado o inactivo.', 1;
SELECT @ModuloID = ModuloID FROM dbo.Usuario_Modulos WHERE CodigoModulo = 'TES_PAGOS' AND Activo = 1;

SELECT @CountMatches = COUNT(*) FROM dbo.Usuario_TiposAutorizacion WHERE CodigoTipoAutorizacion = 'AUT_TES_PAGOS' AND Activo = 1;
IF @CountMatches <> 1 THROW 51082, 'TipoAutorizacion AUT_TES_PAGOS no encontrado o inactivo.', 1;
SELECT @TipoAutorizacionID = TipoAutorizacionID FROM dbo.Usuario_TiposAutorizacion WHERE CodigoTipoAutorizacion = 'AUT_TES_PAGOS' AND Activo = 1;

SELECT @AccionAutorizarID = AccionID FROM dbo.Usuario_Acciones WHERE CodigoAccion = 'AUTORIZAR' AND Activo = 1;
SELECT @AccionRechazarID = AccionID FROM dbo.Usuario_Acciones WHERE CodigoAccion = 'RECHAZAR' AND Activo = 1;
SELECT @AccionEjecutarID = AccionID FROM dbo.Usuario_Acciones WHERE CodigoAccion = 'EJECUTAR' AND Activo = 1;

IF @AccionAutorizarID IS NULL OR @AccionRechazarID IS NULL OR @AccionEjecutarID IS NULL
    THROW 51083, 'Acciones requeridas inactivas o inexistentes.', 1;

SELECT @RolGerenciaID = RolID FROM dbo.Usuario_Roles WHERE CodigoRol = 'GERENCIA' AND Activo = 1;
SELECT @RolDireccionID = RolID FROM dbo.Usuario_Roles WHERE CodigoRol = 'DIRECCION' AND Activo = 1;
SELECT @RolTesoreriaID = RolID FROM dbo.Usuario_Roles WHERE CodigoRol = 'TESORERIA' AND Activo = 1;
SELECT @RolAdminID = RolID FROM dbo.Usuario_Roles WHERE CodigoRol = 'ADMIN' AND Activo = 1;
SELECT @RolSuperAdminID = RolID FROM dbo.Usuario_Roles WHERE CodigoRol = 'SUPERADMIN' AND Activo = 1;

IF @RolGerenciaID IS NULL OR @RolDireccionID IS NULL OR @RolTesoreriaID IS NULL OR @RolAdminID IS NULL OR @RolSuperAdminID IS NULL
    THROW 51084, 'Roles requeridos inactivos o inexistentes.', 1;


/* =========================================================================
   2. VALIDACION DE PERMISOS EFECTIVOS (11 FILAS EXACTAS)
   ========================================================================= */

-- GERENCIA: AUTORIZAR, RECHAZAR
IF NOT EXISTS (SELECT 1 FROM dbo.Usuario_PermisosRolModulo WHERE RolID = @RolGerenciaID AND ModuloID = @ModuloID AND AccionID = @AccionAutorizarID AND Permitido = 1 AND Activo = 1)
    THROW 51085, 'Falta permiso activo GERENCIA / TES_PAGOS / AUTORIZAR.', 1;

IF NOT EXISTS (SELECT 1 FROM dbo.Usuario_PermisosRolModulo WHERE RolID = @RolGerenciaID AND ModuloID = @ModuloID AND AccionID = @AccionRechazarID AND Permitido = 1 AND Activo = 1)
    THROW 51086, 'Falta permiso activo GERENCIA / TES_PAGOS / RECHAZAR.', 1;

-- DIRECCION: AUTORIZAR, RECHAZAR
IF NOT EXISTS (SELECT 1 FROM dbo.Usuario_PermisosRolModulo WHERE RolID = @RolDireccionID AND ModuloID = @ModuloID AND AccionID = @AccionAutorizarID AND Permitido = 1 AND Activo = 1)
    THROW 51087, 'Falta permiso activo DIRECCION / TES_PAGOS / AUTORIZAR.', 1;

IF NOT EXISTS (SELECT 1 FROM dbo.Usuario_PermisosRolModulo WHERE RolID = @RolDireccionID AND ModuloID = @ModuloID AND AccionID = @AccionRechazarID AND Permitido = 1 AND Activo = 1)
    THROW 51088, 'Falta permiso activo DIRECCION / TES_PAGOS / RECHAZAR.', 1;

-- TESORERIA: EJECUTAR
IF NOT EXISTS (SELECT 1 FROM dbo.Usuario_PermisosRolModulo WHERE RolID = @RolTesoreriaID AND ModuloID = @ModuloID AND AccionID = @AccionEjecutarID AND Permitido = 1 AND Activo = 1)
    THROW 51089, 'Falta permiso activo TESORERIA / TES_PAGOS / EJECUTAR.', 1;

-- TESORERIA NO DEBE TENER AUTORIZAR NI RECHAZAR
IF EXISTS (SELECT 1 FROM dbo.Usuario_PermisosRolModulo WHERE RolID = @RolTesoreriaID AND ModuloID = @ModuloID AND AccionID IN (@AccionAutorizarID, @AccionRechazarID) AND Permitido = 1 AND Activo = 1)
    THROW 51090, 'Violacion de segregacion: TESORERIA no debe tener permiso de autorizar o rechazar.', 1;

-- ADMIN: AUTORIZAR, RECHAZAR, EJECUTAR
IF NOT EXISTS (SELECT 1 FROM dbo.Usuario_PermisosRolModulo WHERE RolID = @RolAdminID AND ModuloID = @ModuloID AND AccionID = @AccionAutorizarID AND Permitido = 1 AND Activo = 1)
    THROW 51091, 'Falta permiso activo ADMIN / TES_PAGOS / AUTORIZAR.', 1;

IF NOT EXISTS (SELECT 1 FROM dbo.Usuario_PermisosRolModulo WHERE RolID = @RolAdminID AND ModuloID = @ModuloID AND AccionID = @AccionRechazarID AND Permitido = 1 AND Activo = 1)
    THROW 51092, 'Falta permiso activo ADMIN / TES_PAGOS / RECHAZAR.', 1;

IF NOT EXISTS (SELECT 1 FROM dbo.Usuario_PermisosRolModulo WHERE RolID = @RolAdminID AND ModuloID = @ModuloID AND AccionID = @AccionEjecutarID AND Permitido = 1 AND Activo = 1)
    THROW 51093, 'Falta permiso activo ADMIN / TES_PAGOS / EJECUTAR.', 1;

-- SUPERADMIN: AUTORIZAR, RECHAZAR, EJECUTAR
IF NOT EXISTS (SELECT 1 FROM dbo.Usuario_PermisosRolModulo WHERE RolID = @RolSuperAdminID AND ModuloID = @ModuloID AND AccionID = @AccionAutorizarID AND Permitido = 1 AND Activo = 1)
    THROW 51094, 'Falta permiso activo SUPERADMIN / TES_PAGOS / AUTORIZAR.', 1;

IF NOT EXISTS (SELECT 1 FROM dbo.Usuario_PermisosRolModulo WHERE RolID = @RolSuperAdminID AND ModuloID = @ModuloID AND AccionID = @AccionRechazarID AND Permitido = 1 AND Activo = 1)
    THROW 51095, 'Falta permiso activo SUPERADMIN / TES_PAGOS / RECHAZAR.', 1;

IF NOT EXISTS (SELECT 1 FROM dbo.Usuario_PermisosRolModulo WHERE RolID = @RolSuperAdminID AND ModuloID = @ModuloID AND AccionID = @AccionEjecutarID AND Permitido = 1 AND Activo = 1)
    THROW 51096, 'Falta permiso activo SUPERADMIN / TES_PAGOS / EJECUTAR.', 1;

-- CONTEO EXACTO DE PERMISOS PARA LAS 3 ACCIONES
DECLARE @TotalTargetPerms INT;
SELECT @TotalTargetPerms = COUNT(*)
FROM dbo.Usuario_PermisosRolModulo
WHERE ModuloID = @ModuloID
  AND AccionID IN (@AccionAutorizarID, @AccionRechazarID, @AccionEjecutarID)
  AND Activo = 1
  AND Permitido = 1;

IF @TotalTargetPerms <> 11
    THROW 51097, 'El total de permisos activos para TES_PAGOS difiere de 11.', 1;


/* =========================================================================
   3. VALIDACION DE MATRIZ DE AUTORIZACION (2 FILAS EXACTAS)
   ========================================================================= */

-- Nivel 1: GERENCIA ($0.00 a $50,000.00)
IF NOT EXISTS (
    SELECT 1
    FROM dbo.Usuario_MatrizAutorizacion
    WHERE TipoAutorizacionID = @TipoAutorizacionID
      AND NivelAutorizacion = 1
      AND RolID = @RolGerenciaID
      AND UsuarioID IS NULL
      AND MontoMinimo = 0.00
      AND MontoMaximo = 50000.00
      AND Prioridad = 1
      AND RequiereTodosLosNiveles = 0
      AND Activo = 1
)
    THROW 51098, 'Fila de Nivel 1 en Usuario_MatrizAutorizacion no coincide con el contrato.', 1;

-- Nivel 2: DIRECCION (>$50,000.00)
IF NOT EXISTS (
    SELECT 1
    FROM dbo.Usuario_MatrizAutorizacion
    WHERE TipoAutorizacionID = @TipoAutorizacionID
      AND NivelAutorizacion = 2
      AND RolID = @RolDireccionID
      AND UsuarioID IS NULL
      AND MontoMinimo = 50000.01
      AND MontoMaximo IS NULL
      AND Prioridad = 1
      AND RequiereTodosLosNiveles = 0
      AND Activo = 1
)
    THROW 51099, 'Fila de Nivel 2 en Usuario_MatrizAutorizacion no coincide con el contrato.', 1;

-- ADMIN y SUPERADMIN NO deben pertenecer a la matriz operativa
IF EXISTS (
    SELECT 1
    FROM dbo.Usuario_MatrizAutorizacion
    WHERE TipoAutorizacionID = @TipoAutorizacionID
      AND RolID IN (@RolAdminID, @RolSuperAdminID)
)
    THROW 51100, 'Violacion: ADMIN o SUPERADMIN detectados en la matriz operativa.', 1;

-- Total de filas activas en la matriz para AUT_TES_PAGOS
DECLARE @TotalMatrixRows INT;
SELECT @TotalMatrixRows = COUNT(*)
FROM dbo.Usuario_MatrizAutorizacion
WHERE TipoAutorizacionID = @TipoAutorizacionID
  AND Activo = 1;

IF @TotalMatrixRows <> 2
    THROW 51101, 'El total de filas en Usuario_MatrizAutorizacion difiere de 2.', 1;

-- Resumen de validacion
SELECT
    'VALIDATION_SUCCESS' AS Status,
    @TotalTargetPerms AS PermisosActivosTesPagos,
    @TotalMatrixRows AS FilasMatrizAutTesPagos,
    SYSDATETIME() AS ValidatedAt;
GO
