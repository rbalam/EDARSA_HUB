-- ============================================================================
-- EDARSA HUB - Migración SQL
-- Tabla: Comercial_KPIs_Historico
-- Base de datos: EDARSAHUB
-- Fecha: 2026-04-26
-- Versión: 1.0
-- ============================================================================
-- 
-- PROPÓSITO:
-- Almacenar KPIs comerciales históricos consolidados de forma definitiva.
-- Esta tabla es el DESTINO FINAL de la carga histórica de 24 meses.
-- MongoDB queda solo como checkpoint/log/cache/staging temporal.
--
-- REGLA MAESTRA:
-- EDARSAHUB SQL es el cerebro. MongoDB NO es destino final.
--
-- ============================================================================

-- Verificar si la tabla existe antes de crear
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Comercial_KPIs_Historico')
BEGIN
    CREATE TABLE Comercial_KPIs_Historico (
        -- Identificador único
        id UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
        
        -- Identificación del run de carga
        run_id NVARCHAR(100) NOT NULL,
        
        -- Identificación del servidor y sucursal
        server_id NVARCHAR(100) NOT NULL,
        sucursal_id NVARCHAR(100) NOT NULL,
        sucursal_nombre NVARCHAR(255) NULL,
        empresa_id NVARCHAR(100) NULL,
        unidad_negocio_id NVARCHAR(100) NULL,
        
        -- Clasificación del sistema
        system_type_normalized NVARCHAR(50) NOT NULL,
        
        -- Fecha del KPI
        fecha DATE NOT NULL,
        
        -- Tipo de KPI (DIARIO, SEMANAL, MENSUAL, etc.)
        kpi_tipo NVARCHAR(50) NOT NULL DEFAULT 'DIARIO',
        
        -- Métricas principales
        ventas_total DECIMAL(18, 2) NULL DEFAULT 0,
        tickets_total INT NULL DEFAULT 0,
        pax_total INT NULL DEFAULT 0,
        ticket_promedio DECIMAL(18, 2) NULL DEFAULT 0,
        propinas_total DECIMAL(18, 2) NULL DEFAULT 0,
        
        -- Trazabilidad de origen
        source_hash NVARCHAR(128) NULL,
        source_batch_start DATE NULL,
        source_batch_end DATE NULL,
        
        -- Metadata adicional (JSON)
        metadata_json NVARCHAR(MAX) NULL,
        
        -- Control de versiones
        version INT NOT NULL DEFAULT 1,
        
        -- Timestamps
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        
        -- Primary Key
        CONSTRAINT PK_Comercial_KPIs_Historico PRIMARY KEY (id)
    );
    
    PRINT 'Tabla Comercial_KPIs_Historico creada exitosamente.';
END
ELSE
BEGIN
    PRINT 'Tabla Comercial_KPIs_Historico ya existe. No se realizaron cambios.';
END
GO

-- ============================================================================
-- ÍNDICE ÚNICO OBLIGATORIO (Control anti-duplicados)
-- ============================================================================

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'UX_Comercial_KPIs_Historico' AND object_id = OBJECT_ID('Comercial_KPIs_Historico'))
BEGIN
    CREATE UNIQUE INDEX UX_Comercial_KPIs_Historico
    ON Comercial_KPIs_Historico (server_id, sucursal_id, system_type_normalized, fecha, kpi_tipo);
    
    PRINT 'Índice único UX_Comercial_KPIs_Historico creado.';
END
ELSE
BEGIN
    PRINT 'Índice único UX_Comercial_KPIs_Historico ya existe.';
END
GO

-- ============================================================================
-- ÍNDICES DE CONSULTA
-- ============================================================================

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Comercial_KPIs_Historico_Fecha' AND object_id = OBJECT_ID('Comercial_KPIs_Historico'))
BEGIN
    CREATE INDEX IX_Comercial_KPIs_Historico_Fecha
    ON Comercial_KPIs_Historico (fecha DESC);
    
    PRINT 'Índice IX_Comercial_KPIs_Historico_Fecha creado.';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Comercial_KPIs_Historico_Server_Fecha' AND object_id = OBJECT_ID('Comercial_KPIs_Historico'))
BEGIN
    CREATE INDEX IX_Comercial_KPIs_Historico_Server_Fecha
    ON Comercial_KPIs_Historico (server_id, fecha DESC);
    
    PRINT 'Índice IX_Comercial_KPIs_Historico_Server_Fecha creado.';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Comercial_KPIs_Historico_RunId' AND object_id = OBJECT_ID('Comercial_KPIs_Historico'))
BEGIN
    CREATE INDEX IX_Comercial_KPIs_Historico_RunId
    ON Comercial_KPIs_Historico (run_id);
    
    PRINT 'Índice IX_Comercial_KPIs_Historico_RunId creado.';
END
GO

-- ============================================================================
-- VERIFICACIÓN FINAL
-- ============================================================================

SELECT 
    TABLE_NAME,
    (SELECT COUNT(*) FROM Comercial_KPIs_Historico) as row_count
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME = 'Comercial_KPIs_Historico';

SELECT 
    i.name as index_name,
    i.is_unique,
    STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) as columns
FROM sys.indexes i
INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE i.object_id = OBJECT_ID('Comercial_KPIs_Historico')
GROUP BY i.name, i.is_unique;

-- ============================================================================
-- FIN DE MIGRACIÓN
-- ============================================================================
