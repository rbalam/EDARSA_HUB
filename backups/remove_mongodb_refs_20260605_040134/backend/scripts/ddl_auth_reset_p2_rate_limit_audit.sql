-- =========================================================================
-- DDL AUTH-RESET-P2: Tablas para Rate Limit y Auditoría de Password Reset
-- =========================================================================
-- FASE: AUTH-RESET-P2
-- FECHA: 2026-05-14
-- OBJETIVO: Eliminar dependencias de MongoDB en password_reset.py
-- NOMENCLATURA: Usuario_* (patrón dominante en EDARSAHUB)
-- =========================================================================

-- =========================================================================
-- TABLA 1: Usuario_RateLimitRecuperacion
-- =========================================================================
-- Propósito: Control de rate limit por IP/email para solicitudes de reset
-- Reemplaza: MongoDB collection rate_limit_password_reset
-- 
-- Lógica:
-- - Clave única por (TipoLlave, ValorLlave) ej: ('ip', '192.168.1.1')
-- - Ventana de tiempo configurable (default 1 hora)
-- - Contador se reinicia automáticamente cuando expira la ventana

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Usuario_RateLimitRecuperacion]') AND type in (N'U'))
BEGIN
    CREATE TABLE Usuario_RateLimitRecuperacion (
        RateLimitID         BIGINT IDENTITY(1,1) PRIMARY KEY,
        TipoLlave           VARCHAR(20) NOT NULL,        -- 'ip' o 'email'
        ValorLlave          VARCHAR(255) NOT NULL,       -- IP o email
        Contador            INT NOT NULL DEFAULT 1,
        VentanaInicio       DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        VentanaExpiracion   DATETIME2 NOT NULL,
        FechaCreacion       DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        FechaModificacion   DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        
        -- Índice único para evitar duplicados
        CONSTRAINT UQ_Usuario_RateLimitRecuperacion_Llave 
            UNIQUE (TipoLlave, ValorLlave)
    );
    
    -- Índice para limpiar registros expirados
    CREATE NONCLUSTERED INDEX IX_Usuario_RateLimitRecuperacion_Expiracion
        ON Usuario_RateLimitRecuperacion (VentanaExpiracion);
    
    PRINT 'Tabla Usuario_RateLimitRecuperacion creada exitosamente';
END
ELSE
BEGIN
    PRINT 'Tabla Usuario_RateLimitRecuperacion ya existe - sin cambios';
END
GO

-- =========================================================================
-- TABLA 2: Usuario_LogRecuperacion
-- =========================================================================
-- Propósito: Auditoría de eventos de recuperación de contraseña
-- Reemplaza: MongoDB collection audit_password_reset
--
-- Eventos:
-- - request_success: Solicitud de reset exitosa
-- - request_user_not_found: Email no encontrado
-- - request_user_inactive: Usuario inactivo
-- - rate_limit_ip: Rate limit por IP alcanzado
-- - rate_limit_email: Rate limit por email alcanzado
-- - reset_success: Password cambiado exitosamente
-- - reset_invalid_token: Token inválido/expirado
-- - reset_weak_password: Password no cumple requisitos
-- - reset_user_not_found: Usuario no encontrado al usar token
-- - reset_update_failed: Error al actualizar password

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Usuario_LogRecuperacion]') AND type in (N'U'))
BEGIN
    CREATE TABLE Usuario_LogRecuperacion (
        LogRecuperacionID   BIGINT IDENTITY(1,1) PRIMARY KEY,
        Evento              VARCHAR(50) NOT NULL,        -- Tipo de evento
        Email               VARCHAR(255) NOT NULL,       -- Email involucrado
        IPOrigen            VARCHAR(45) NULL,            -- IPv4 o IPv6
        UserAgent           VARCHAR(500) NULL,           -- User-Agent del navegador
        Resultado           BIT NOT NULL,                -- 1=éxito, 0=fallo
        Detalle             NVARCHAR(MAX) NULL,          -- JSON con detalles adicionales
        FechaEvento         DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        
        -- Índices para consultas frecuentes
        INDEX IX_Usuario_LogRecuperacion_Fecha (FechaEvento DESC),
        INDEX IX_Usuario_LogRecuperacion_Email (Email, FechaEvento DESC),
        INDEX IX_Usuario_LogRecuperacion_Evento (Evento, FechaEvento DESC)
    );
    
    PRINT 'Tabla Usuario_LogRecuperacion creada exitosamente';
END
ELSE
BEGIN
    PRINT 'Tabla Usuario_LogRecuperacion ya existe - sin cambios';
END
GO

-- =========================================================================
-- FIN DDL AUTH-RESET-P2
-- =========================================================================
