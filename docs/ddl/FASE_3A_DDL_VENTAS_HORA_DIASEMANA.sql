-- ============================================================================
-- FASE 3A: DDL para Ventas por Hora y Ventas por Día de Semana
-- Base de datos: EDARSAHUB
-- Fecha: 2026-05-15
-- Autorizado por: Usuario bajo régimen de Autorización Controlada
-- ============================================================================

-- ============================================================================
-- TABLA 1: Comercial_Ventas_Por_Hora_v2
-- Propósito: Almacenar ventas agregadas por hora operativa
-- Frecuencia de sincronización: cada 5 minutos
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Comercial_Ventas_Por_Hora_v2')
BEGIN
    CREATE TABLE Comercial_Ventas_Por_Hora_v2 (
        -- Identificador único
        VentaPorHoraID UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
        
        -- Identificación de unidad
        UnidadNegocioID NVARCHAR(100) NOT NULL,
        UnidadNegocioNombre NVARCHAR(200) NULL,
        ServerID NVARCHAR(100) NULL,
        EmpresaID NVARCHAR(100) NULL,
        SucursalID NVARCHAR(100) NULL,
        SistemaOrigen NVARCHAR(50) NOT NULL,
        FuenteTipo NVARCHAR(50) NULL,
        
        -- Fecha y hora operativa
        FechaOperacion DATE NOT NULL,
        HoraOperacion TINYINT NOT NULL,  -- 0-23
        OrdenHoraOperativa TINYINT NOT NULL,  -- Orden según jornada (1=primera hora operativa)
        
        -- Métricas principales
        VentaTotal DECIMAL(18,2) NOT NULL DEFAULT 0,
        PaxTotal INT NOT NULL DEFAULT 0,
        ChequesTotal INT NOT NULL DEFAULT 0,
        ChequePromedio DECIMAL(18,2) NULL,
        TicketPromedioPax DECIMAL(18,2) NULL,
        
        -- Desglose A/B (para fase futura)
        AlimentosTotal DECIMAL(18,2) NULL,
        BebidasTotal DECIMAL(18,2) NULL,
        OtrosTotal DECIMAL(18,2) NULL,
        
        -- Saturación (para fase futura)
        CocinaItems INT NULL,
        BarraItems INT NULL,
        
        -- Control de sincronización
        SourceHash NVARCHAR(200) NULL,
        SyncRunID NVARCHAR(100) NULL,
        UltimaSincronizacion DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        
        -- Estado
        Activo BIT NOT NULL DEFAULT 1,
        EsDemo BIT NOT NULL DEFAULT 0,
        
        -- Auditoría
        FechaCreacion DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        FechaModificacion DATETIME2 NULL,
        
        -- Constraints
        CONSTRAINT CK_Comercial_Ventas_Por_Hora_v2_Hora
            CHECK (HoraOperacion BETWEEN 0 AND 23),
        
        CONSTRAINT CK_Comercial_Ventas_Por_Hora_v2_OrdenHora
            CHECK (OrdenHoraOperativa BETWEEN 1 AND 24)
    );
    
    PRINT 'Tabla Comercial_Ventas_Por_Hora_v2 creada exitosamente';
END
GO

-- Llave única: evita duplicados
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UQ_Comercial_Ventas_Por_Hora_v2_Unidad_Fecha_Hora')
BEGIN
    CREATE UNIQUE INDEX UQ_Comercial_Ventas_Por_Hora_v2_Unidad_Fecha_Hora
    ON Comercial_Ventas_Por_Hora_v2 (UnidadNegocioID, FechaOperacion, HoraOperacion)
    WHERE Activo = 1 AND EsDemo = 0;
    
    PRINT 'Índice único UQ_Comercial_Ventas_Por_Hora_v2_Unidad_Fecha_Hora creado';
END
GO

-- Índices de consulta
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Comercial_Ventas_Por_Hora_v2_FechaOperacion')
BEGIN
    CREATE INDEX IX_Comercial_Ventas_Por_Hora_v2_FechaOperacion
    ON Comercial_Ventas_Por_Hora_v2 (FechaOperacion, Activo);
    
    PRINT 'Índice IX_Comercial_Ventas_Por_Hora_v2_FechaOperacion creado';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Comercial_Ventas_Por_Hora_v2_Unidad_Fecha')
BEGIN
    CREATE INDEX IX_Comercial_Ventas_Por_Hora_v2_Unidad_Fecha
    ON Comercial_Ventas_Por_Hora_v2 (UnidadNegocioID, FechaOperacion, Activo);
    
    PRINT 'Índice IX_Comercial_Ventas_Por_Hora_v2_Unidad_Fecha creado';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Comercial_Ventas_Por_Hora_v2_UltimaSincronizacion')
BEGIN
    CREATE INDEX IX_Comercial_Ventas_Por_Hora_v2_UltimaSincronizacion
    ON Comercial_Ventas_Por_Hora_v2 (UltimaSincronizacion DESC);
    
    PRINT 'Índice IX_Comercial_Ventas_Por_Hora_v2_UltimaSincronizacion creado';
END
GO

-- ============================================================================
-- TABLA 2: Comercial_Ventas_DiaSemana_v2
-- Propósito: Almacenar ventas agregadas por día de semana
-- Frecuencia de sincronización: cada 5 minutos
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Comercial_Ventas_DiaSemana_v2')
BEGIN
    CREATE TABLE Comercial_Ventas_DiaSemana_v2 (
        -- Identificador único
        VentaDiaSemanaID UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
        
        -- Identificación de unidad
        UnidadNegocioID NVARCHAR(100) NOT NULL,
        UnidadNegocioNombre NVARCHAR(200) NULL,
        ServerID NVARCHAR(100) NULL,
        EmpresaID NVARCHAR(100) NULL,
        SucursalID NVARCHAR(100) NULL,
        SistemaOrigen NVARCHAR(50) NOT NULL,
        FuenteTipo NVARCHAR(50) NULL,
        
        -- Período de agregación
        FechaInicioPeriodo DATE NOT NULL,
        FechaFinPeriodo DATE NOT NULL,
        TipoPeriodo NVARCHAR(20) NOT NULL DEFAULT 'SEMANA',  -- SEMANA, MES, AÑO
        
        -- Día de semana (ISO: 1=Lunes ... 7=Domingo)
        DiaSemana TINYINT NOT NULL,
        NombreDiaSemana NVARCHAR(30) NOT NULL,
        
        -- Métricas principales
        VentaTotal DECIMAL(18,2) NOT NULL DEFAULT 0,
        PaxTotal INT NOT NULL DEFAULT 0,
        ChequesTotal INT NOT NULL DEFAULT 0,
        ChequePromedio DECIMAL(18,2) NULL,
        TicketPromedioPax DECIMAL(18,2) NULL,
        DiasContados INT NOT NULL DEFAULT 1,  -- Cuántos días de ese tipo se sumaron
        
        -- Desglose A/B (para fase futura)
        AlimentosTotal DECIMAL(18,2) NULL,
        BebidasTotal DECIMAL(18,2) NULL,
        OtrosTotal DECIMAL(18,2) NULL,
        
        -- Control de sincronización
        SourceHash NVARCHAR(200) NULL,
        SyncRunID NVARCHAR(100) NULL,
        UltimaSincronizacion DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        
        -- Estado
        Activo BIT NOT NULL DEFAULT 1,
        EsDemo BIT NOT NULL DEFAULT 0,
        
        -- Auditoría
        FechaCreacion DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        FechaModificacion DATETIME2 NULL,
        
        -- Constraints
        CONSTRAINT CK_Comercial_Ventas_DiaSemana_v2_DiaSemana
            CHECK (DiaSemana BETWEEN 1 AND 7)
    );
    
    PRINT 'Tabla Comercial_Ventas_DiaSemana_v2 creada exitosamente';
END
GO

-- Llave única: evita duplicados
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UQ_Comercial_Ventas_DiaSemana_v2_Unidad_Periodo_Dia')
BEGIN
    CREATE UNIQUE INDEX UQ_Comercial_Ventas_DiaSemana_v2_Unidad_Periodo_Dia
    ON Comercial_Ventas_DiaSemana_v2 (UnidadNegocioID, FechaInicioPeriodo, FechaFinPeriodo, DiaSemana)
    WHERE Activo = 1 AND EsDemo = 0;
    
    PRINT 'Índice único UQ_Comercial_Ventas_DiaSemana_v2_Unidad_Periodo_Dia creado';
END
GO

-- Índices de consulta
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Comercial_Ventas_DiaSemana_v2_Periodo')
BEGIN
    CREATE INDEX IX_Comercial_Ventas_DiaSemana_v2_Periodo
    ON Comercial_Ventas_DiaSemana_v2 (FechaInicioPeriodo, FechaFinPeriodo, Activo);
    
    PRINT 'Índice IX_Comercial_Ventas_DiaSemana_v2_Periodo creado';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Comercial_Ventas_DiaSemana_v2_Unidad_Periodo')
BEGIN
    CREATE INDEX IX_Comercial_Ventas_DiaSemana_v2_Unidad_Periodo
    ON Comercial_Ventas_DiaSemana_v2 (UnidadNegocioID, FechaInicioPeriodo, FechaFinPeriodo, Activo);
    
    PRINT 'Índice IX_Comercial_Ventas_DiaSemana_v2_Unidad_Periodo creado';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Comercial_Ventas_DiaSemana_v2_DiaSemana')
BEGIN
    CREATE INDEX IX_Comercial_Ventas_DiaSemana_v2_DiaSemana
    ON Comercial_Ventas_DiaSemana_v2 (DiaSemana, Activo);
    
    PRINT 'Índice IX_Comercial_Ventas_DiaSemana_v2_DiaSemana creado';
END
GO

-- ============================================================================
-- FIN DEL SCRIPT DDL
-- ============================================================================
PRINT '=== DDL FASE 3A COMPLETADO ===';
GO
