-- ============================================================================
-- EDARSA HUB - TABLA DE AUDITORÍA FINANCIERA
-- ============================================================================
-- Fecha: Diciembre 2025
-- Propósito: Log estructurado de auditoría funcional y financiera
-- Ubicación: SQL Server EDARSA HUB (fuente oficial, NO MongoDB)
-- ============================================================================

-- ============================================================================
-- TABLA PRINCIPAL: auditoria_financiera
-- ============================================================================

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'auditoria_financiera')
BEGIN
    CREATE TABLE auditoria_financiera (
        -- ============================================
        -- IDENTIFICADORES
        -- ============================================
        id                      BIGINT IDENTITY(1,1)    PRIMARY KEY,
        
        -- ============================================
        -- CONTEXTO DEL USUARIO
        -- ============================================
        usuario_id              NVARCHAR(50)            NOT NULL,
        usuario_email           NVARCHAR(100)           NOT NULL,
        session_id              NVARCHAR(100)           NULL,
        ip_origen               NVARCHAR(50)            NULL,
        
        -- ============================================
        -- CONTEXTO ORGANIZACIONAL
        -- ============================================
        empresa_id              NVARCHAR(50)            NULL,
        sucursal_id             NVARCHAR(50)            NULL,
        origen_sistema          NVARCHAR(20)            NOT NULL DEFAULT 'EDARSA_HUB',
            -- EDARSA_HUB = Operación directa en el sistema
            -- SOFT = Acción relacionada con datos de SoftRestaurant
            -- MPRO = Acción relacionada con datos de MPRO
        
        -- ============================================
        -- CLASIFICACIÓN DE LA ACCIÓN
        -- ============================================
        modulo                  NVARCHAR(50)            NOT NULL,
            -- TESORERIA, CXP, PROPINAS, PRESUPUESTOS, INGRESOS, CONFIG
        entidad                 NVARCHAR(50)            NOT NULL,
            -- cuadre_z, factura, config_propinas, presupuesto, etc.
        entidad_origen          NVARCHAR(100)           NULL,
            -- Tabla de origen si aplica (ej: movtoscaja, cheques)
        accion                  NVARCHAR(20)            NOT NULL,
            -- VIEW, EDIT, CONFIRM, AUTHORIZE
        
        -- ============================================
        -- REFERENCIA AL REGISTRO AFECTADO
        -- ============================================
        registro_id             NVARCHAR(100)           NOT NULL,
        registro_folio          NVARCHAR(50)            NULL,
        
        -- ============================================
        -- CAMBIOS REALIZADOS
        -- ============================================
        campo_modificado        NVARCHAR(100)           NULL,
            -- Campo específico modificado
            -- Si son múltiples campos: se registra "MULTIPLE" y el detalle va en valor_anterior/valor_nuevo como JSON
        valor_anterior          NVARCHAR(MAX)           NULL,
            -- Valor antes del cambio (JSON si es complejo o múltiple)
        valor_nuevo             NVARCHAR(MAX)           NULL,
            -- Valor después del cambio (JSON si es complejo o múltiple)
        
        -- ============================================
        -- RESULTADO Y CONTEXTO
        -- ============================================
        resultado               NVARCHAR(20)            NOT NULL DEFAULT 'OK',
            -- OK = Acción ejecutada correctamente
            -- ERROR = Falló la ejecución
            -- RECHAZADO = Denegado por permisos o validación
        motivo                  NVARCHAR(500)           NULL,
        observaciones           NVARCHAR(MAX)           NULL,
        nivel_riesgo            NVARCHAR(20)            NULL,
            -- BAJO, MEDIO, ALTO, CRITICO
        
        -- ============================================
        -- TIMESTAMPS
        -- ============================================
        created_at              DATETIME                NOT NULL DEFAULT GETDATE(),
        fecha                   AS created_at           -- Alias para compatibilidad
    );

    PRINT 'Tabla auditoria_financiera creada exitosamente';
END
GO

-- ============================================
-- ÍNDICES PARA CONSULTAS FRECUENTES
-- ============================================

-- Por fecha (consultas recientes)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_auditoria_fecha')
    CREATE INDEX IX_auditoria_fecha 
    ON auditoria_financiera (created_at DESC);

-- Por usuario (historial de usuario)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_auditoria_usuario')
    CREATE INDEX IX_auditoria_usuario 
    ON auditoria_financiera (usuario_id, created_at DESC);

-- Por módulo y entidad (auditoría por área)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_auditoria_modulo')
    CREATE INDEX IX_auditoria_modulo 
    ON auditoria_financiera (modulo, entidad, created_at DESC);

-- Por registro específico (historial de un registro)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_auditoria_registro')
    CREATE INDEX IX_auditoria_registro 
    ON auditoria_financiera (registro_id, created_at DESC);

-- Por empresa/sucursal (auditoría organizacional)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_auditoria_empresa')
    CREATE INDEX IX_auditoria_empresa 
    ON auditoria_financiera (empresa_id, sucursal_id, created_at DESC);

-- Por resultado (análisis de errores)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_auditoria_resultado')
    CREATE INDEX IX_auditoria_resultado 
    ON auditoria_financiera (resultado, created_at DESC)
    WHERE resultado != 'OK';

GO

-- ============================================
-- CONSTRAINTS DE VALIDACIÓN
-- ============================================

-- Validar valores de accion
IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_auditoria_accion')
    ALTER TABLE auditoria_financiera
    ADD CONSTRAINT CK_auditoria_accion 
        CHECK (accion IN ('VIEW', 'EDIT', 'CONFIRM', 'AUTHORIZE'));

-- Validar valores de modulo
IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_auditoria_modulo')
    ALTER TABLE auditoria_financiera
    ADD CONSTRAINT CK_auditoria_modulo 
        CHECK (modulo IN ('TESORERIA', 'CXP', 'PROPINAS', 'PRESUPUESTOS', 'INGRESOS', 'CONFIG', 'USUARIOS', 'SISTEMA'));

-- Validar valores de resultado
IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_auditoria_resultado')
    ALTER TABLE auditoria_financiera
    ADD CONSTRAINT CK_auditoria_resultado 
        CHECK (resultado IN ('OK', 'ERROR', 'RECHAZADO'));

-- Validar valores de nivel_riesgo
IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_auditoria_riesgo')
    ALTER TABLE auditoria_financiera
    ADD CONSTRAINT CK_auditoria_riesgo 
        CHECK (nivel_riesgo IS NULL OR nivel_riesgo IN ('BAJO', 'MEDIO', 'ALTO', 'CRITICO'));

-- Validar valores de origen_sistema
IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_auditoria_origen')
    ALTER TABLE auditoria_financiera
    ADD CONSTRAINT CK_auditoria_origen 
        CHECK (origen_sistema IN ('EDARSA_HUB', 'SOFT', 'MPRO'));

GO

-- ============================================
-- DOCUMENTACIÓN DE CAMPOS MÚLTIPLES
-- ============================================
-- Cuando campo_modificado = 'MULTIPLE', los valores se registran así:
-- 
-- valor_anterior: {
--   "campo1": "valor_anterior_1",
--   "campo2": "valor_anterior_2"
-- }
-- 
-- valor_nuevo: {
--   "campo1": "valor_nuevo_1",
--   "campo2": "valor_nuevo_2"
-- }
-- ============================================

PRINT 'Script de auditoría financiera completado';
GO
