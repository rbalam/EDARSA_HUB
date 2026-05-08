-- ============================================================================
-- EDARSA HUB - REFRESH TOKENS SYSTEM
-- ============================================================================
-- Script SQL para crear tablas de sesiones con Refresh Tokens
-- 
-- FASE A: P1-REFRESH-TOKENS
-- Fecha: 2025-04-27
-- Base de datos: EDARSAHUB (SQL Server)
--
-- INSTRUCCIONES DE EJECUCIÓN:
-- 1. Conectarse a SQL Server con permisos de creación de tablas en EDARSAHUB
-- 2. Ejecutar este script completo
-- 3. Verificar que las tablas se crearon con: SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE 'Sesion%'
--
-- NOTA: El script es idempotente (IF NOT EXISTS)
-- ============================================================================

USE EDARSAHUB;
GO

-- ============================================================================
-- TABLA PRINCIPAL: Sesiones
-- ============================================================================
-- Almacena sesiones activas de usuarios internos
-- El refresh_token_hash es el SHA256 del refresh token opaco
-- NUNCA se almacena el refresh token plano

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Sesiones')
BEGIN
    CREATE TABLE Sesiones (
        -- Identificadores
        SesionID                UNIQUEIDENTIFIER    NOT NULL PRIMARY KEY DEFAULT NEWID(),
        UsuarioID               INT                 NOT NULL,           -- ID del usuario en sistema
        TipoUsuario             VARCHAR(20)         NOT NULL DEFAULT 'interno',  -- 'interno' | 'portal' (futuro)
        
        -- Refresh Token (solo hash, NUNCA el token plano)
        RefreshTokenHash        VARCHAR(64)         NOT NULL,           -- SHA256 = 64 caracteres hex
        FamiliaTokenID          UNIQUEIDENTIFIER    NOT NULL,           -- Para detectar replay attacks
        
        -- Timestamps
        FechaCreacion           DATETIME2(3)        NOT NULL DEFAULT GETUTCDATE(),
        FechaExpiracion         DATETIME2(3)        NOT NULL,
        UltimaActividad         DATETIME2(3)        NOT NULL DEFAULT GETUTCDATE(),
        
        -- Estado de revocación
        EstaActiva              BIT                 NOT NULL DEFAULT 1,
        FechaRevocacion         DATETIME2(3)        NULL,
        MotivoRevocacion        VARCHAR(50)         NULL,   -- 'logout' | 'logout_all' | 'token_rotated' | 'replay_detected' | 'security' | 'expired' | 'admin_revoked'
        RevocadoPorUsuarioID    INT                 NULL,   -- Si fue revocada por admin, quién
        
        -- Sesión que reemplazó a esta (por rotación)
        ReemplazadaPorSesionID  UNIQUEIDENTIFIER    NULL,
        
        -- Contexto de seguridad
        IPCliente               VARCHAR(45)         NULL,   -- IPv4 (15) o IPv6 (45)
        UserAgent               VARCHAR(500)        NULL,   -- Browser/cliente
        
        -- Auditoría
        FechaModificacion       DATETIME2(3)        NOT NULL DEFAULT GETUTCDATE()
    );
    
    PRINT 'Tabla Sesiones creada exitosamente';
END
ELSE
BEGIN
    PRINT 'Tabla Sesiones ya existe - no se modificó';
END
GO

-- ============================================================================
-- ÍNDICES PARA Sesiones
-- ============================================================================

-- Índice único para búsqueda por hash de refresh token (solo activos)
-- Esto garantiza que un hash solo puede pertenecer a UNA sesión activa
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Sesiones_TokenHash_Activo')
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX IX_Sesiones_TokenHash_Activo
    ON Sesiones (RefreshTokenHash)
    WHERE EstaActiva = 1;
    
    PRINT 'Índice IX_Sesiones_TokenHash_Activo creado';
END
GO

-- Índice para listar sesiones de un usuario
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Sesiones_Usuario')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Sesiones_Usuario
    ON Sesiones (UsuarioID, EstaActiva, FechaExpiracion DESC);
    
    PRINT 'Índice IX_Sesiones_Usuario creado';
END
GO

-- Índice para detección de replay por familia
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Sesiones_Familia')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Sesiones_Familia
    ON Sesiones (FamiliaTokenID, EstaActiva);
    
    PRINT 'Índice IX_Sesiones_Familia creado';
END
GO

-- Índice para limpieza de sesiones expiradas
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Sesiones_Expiracion')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Sesiones_Expiracion
    ON Sesiones (FechaExpiracion)
    WHERE EstaActiva = 1;
    
    PRINT 'Índice IX_Sesiones_Expiracion creado';
END
GO

-- ============================================================================
-- TABLA DE AUDITORÍA: SesionesHistorico
-- ============================================================================
-- Registro inmutable de todas las acciones sobre sesiones
-- Para auditoría de seguridad y compliance

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'SesionesHistorico')
BEGIN
    CREATE TABLE SesionesHistorico (
        -- Identificador
        HistoricoID             BIGINT IDENTITY(1,1) PRIMARY KEY,
        
        -- Referencia a sesión
        SesionID                UNIQUEIDENTIFIER    NOT NULL,
        UsuarioID               INT                 NOT NULL,
        TipoUsuario             VARCHAR(20)         NOT NULL,
        
        -- Acción realizada
        Accion                  VARCHAR(30)         NOT NULL,   
        -- Valores posibles:
        -- 'login'              = Sesión creada (nuevo login)
        -- 'refresh'            = Token refrescado
        -- 'logout'             = Usuario cerró sesión voluntariamente
        -- 'logout_all'         = Usuario cerró todas sus sesiones
        -- 'token_rotated'      = Refresh token fue rotado (sesión anterior inactiva)
        -- 'replay_detected'    = Intento de reutilizar refresh token rotado
        -- 'expired'            = Sesión expiró naturalmente
        -- 'admin_revoked'      = Admin revocó la sesión
        -- 'security_revoked'   = Revocada por motivo de seguridad
        
        -- Timestamp
        FechaAccion             DATETIME2(3)        NOT NULL DEFAULT GETUTCDATE(),
        
        -- Contexto
        IPCliente               VARCHAR(45)         NULL,
        UserAgent               VARCHAR(500)        NULL,
        
        -- Detalles adicionales (JSON opcional)
        DetallesJSON            NVARCHAR(MAX)       NULL,
        
        -- Metadata de la acción
        AccionRealizadaPor      INT                 NULL    -- ID del usuario que realizó la acción (si aplica)
    );
    
    PRINT 'Tabla SesionesHistorico creada exitosamente';
END
ELSE
BEGIN
    PRINT 'Tabla SesionesHistorico ya existe - no se modificó';
END
GO

-- ============================================================================
-- ÍNDICES PARA SesionesHistorico
-- ============================================================================

-- Índice para consultar historial por usuario
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_SesionesHist_Usuario')
BEGIN
    CREATE NONCLUSTERED INDEX IX_SesionesHist_Usuario
    ON SesionesHistorico (UsuarioID, FechaAccion DESC);
    
    PRINT 'Índice IX_SesionesHist_Usuario creado';
END
GO

-- Índice para consultar historial por sesión
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_SesionesHist_Sesion')
BEGIN
    CREATE NONCLUSTERED INDEX IX_SesionesHist_Sesion
    ON SesionesHistorico (SesionID, FechaAccion DESC);
    
    PRINT 'Índice IX_SesionesHist_Sesion creado';
END
GO

-- Índice para alertas de seguridad (replay, revocaciones)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_SesionesHist_Seguridad')
BEGIN
    CREATE NONCLUSTERED INDEX IX_SesionesHist_Seguridad
    ON SesionesHistorico (Accion, FechaAccion DESC)
    WHERE Accion IN ('replay_detected', 'security_revoked', 'admin_revoked');
    
    PRINT 'Índice IX_SesionesHist_Seguridad creado';
END
GO

-- ============================================================================
-- PROCEDIMIENTO: Limpiar sesiones expiradas (opcional, para jobs)
-- ============================================================================

IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'sp_LimpiarSesionesExpiradas')
BEGIN
    DROP PROCEDURE sp_LimpiarSesionesExpiradas;
END
GO

CREATE PROCEDURE sp_LimpiarSesionesExpiradas
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @sesionesAfectadas INT;
    
    -- Marcar como expiradas las sesiones vencidas que aún están activas
    UPDATE Sesiones
    SET 
        EstaActiva = 0,
        FechaRevocacion = GETUTCDATE(),
        MotivoRevocacion = 'expired',
        FechaModificacion = GETUTCDATE()
    WHERE 
        EstaActiva = 1
        AND FechaExpiracion < GETUTCDATE();
    
    SET @sesionesAfectadas = @@ROWCOUNT;
    
    -- Registrar en histórico
    IF @sesionesAfectadas > 0
    BEGIN
        INSERT INTO SesionesHistorico (SesionID, UsuarioID, TipoUsuario, Accion, FechaAccion, DetallesJSON)
        SELECT 
            SesionID,
            UsuarioID,
            TipoUsuario,
            'expired',
            GETUTCDATE(),
            '{"cleanup_job": true}'
        FROM Sesiones
        WHERE 
            MotivoRevocacion = 'expired'
            AND FechaRevocacion >= DATEADD(SECOND, -5, GETUTCDATE());  -- Las recién marcadas
    END
    
    SELECT @sesionesAfectadas AS SesionesExpiradas;
END
GO

PRINT 'Procedimiento sp_LimpiarSesionesExpiradas creado';
GO

-- ============================================================================
-- VERIFICACIÓN FINAL
-- ============================================================================

SELECT 'Tablas creadas:' AS Info;
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE 'Sesion%';

SELECT 'Índices creados:' AS Info;
SELECT i.name AS IndexName, t.name AS TableName
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.name LIKE 'Sesion%' AND i.name IS NOT NULL;

PRINT '';
PRINT '============================================================================';
PRINT 'SCRIPT COMPLETADO EXITOSAMENTE';
PRINT 'Tablas creadas: Sesiones, SesionesHistorico';
PRINT 'Procedimiento creado: sp_LimpiarSesionesExpiradas';
PRINT '';
PRINT 'PRÓXIMOS PASOS:';
PRINT '1. Verificar que las tablas existen con las queries de arriba';
PRINT '2. Configurar job de limpieza (opcional): EXEC sp_LimpiarSesionesExpiradas';
PRINT '3. Probar inserción manual si se desea validar permisos';
PRINT '============================================================================';
GO
