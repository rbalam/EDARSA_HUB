-- ============================================================================
-- EDARSA HUB - CRM ENTERPRISE - SCRIPT 02: CATÁLOGOS CRM
-- ============================================================================
-- Fecha: 2026-05-23
-- Autor: E1 Agent
-- Descripción: Catálogos para el módulo CRM
-- ============================================================================

-- ============================================================================
-- A. CRM_Cat_OrigenLead
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Cat_OrigenLead')
BEGIN
    CREATE TABLE dbo.CRM_Cat_OrigenLead (
        OrigenID INT IDENTITY(1,1) PRIMARY KEY,
        Codigo NVARCHAR(20) NOT NULL,
        Nombre NVARCHAR(100) NOT NULL,
        Descripcion NVARCHAR(500) NULL,
        Orden INT DEFAULT 0,
        ColorHex NVARCHAR(7) DEFAULT '#6B7280',
        Activo BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE()
    );
    
    INSERT INTO dbo.CRM_Cat_OrigenLead (Codigo, Nombre, Orden) VALUES
    ('REFERIDO', 'Referido', 1),
    ('LLAMADA', 'Llamada entrante', 2),
    ('VISITA', 'Visita comercial', 3),
    ('WEB', 'Formulario web', 4),
    ('CAMPANA', 'Campaña marketing', 5),
    ('CLIENTE', 'Cliente actual', 6),
    ('WHATSAPP', 'WhatsApp', 7),
    ('EVENTO', 'Evento/Feria', 8),
    ('LINKEDIN', 'LinkedIn', 9),
    ('CRM_EXTERNO', 'CRM Externo', 10),
    ('OTRO', 'Otro', 99);
    
    PRINT 'Tabla CRM_Cat_OrigenLead creada y poblada';
END

-- ============================================================================
-- B. CRM_Cat_EstatusLead
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Cat_EstatusLead')
BEGIN
    CREATE TABLE dbo.CRM_Cat_EstatusLead (
        EstatusID INT IDENTITY(1,1) PRIMARY KEY,
        Codigo NVARCHAR(20) NOT NULL,
        Nombre NVARCHAR(100) NOT NULL,
        Descripcion NVARCHAR(500) NULL,
        Orden INT DEFAULT 0,
        ColorHex NVARCHAR(7) DEFAULT '#6B7280',
        EsFinal BIT DEFAULT 0,
        Activo BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE()
    );
    
    INSERT INTO dbo.CRM_Cat_EstatusLead (Codigo, Nombre, ColorHex, Orden, EsFinal) VALUES
    ('NUEVO', 'Nuevo', '#3B82F6', 1, 0),
    ('CONTACTADO', 'Contactado', '#8B5CF6', 2, 0),
    ('CALIFICADO', 'Calificado', '#10B981', 3, 0),
    ('DESCALIFICADO', 'Descalificado', '#EF4444', 4, 1),
    ('CONVERTIDO', 'Convertido', '#059669', 5, 1);
    
    PRINT 'Tabla CRM_Cat_EstatusLead creada y poblada';
END

-- ============================================================================
-- C. CRM_Cat_EstatusOportunidad
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Cat_EstatusOportunidad')
BEGIN
    CREATE TABLE dbo.CRM_Cat_EstatusOportunidad (
        EstatusID INT IDENTITY(1,1) PRIMARY KEY,
        Codigo NVARCHAR(20) NOT NULL,
        Nombre NVARCHAR(100) NOT NULL,
        Descripcion NVARCHAR(500) NULL,
        Orden INT DEFAULT 0,
        ColorHex NVARCHAR(7) DEFAULT '#6B7280',
        EsFinal BIT DEFAULT 0,
        EsGanada BIT DEFAULT 0,
        EsPerdida BIT DEFAULT 0,
        Activo BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE()
    );
    
    INSERT INTO dbo.CRM_Cat_EstatusOportunidad (Codigo, Nombre, ColorHex, Orden, EsFinal, EsGanada, EsPerdida) VALUES
    ('ABIERTA', 'Abierta', '#3B82F6', 1, 0, 0, 0),
    ('GANADA', 'Ganada', '#059669', 2, 1, 1, 0),
    ('PERDIDA', 'Perdida', '#EF4444', 3, 1, 0, 1),
    ('PAUSADA', 'Pausada', '#F59E0B', 4, 0, 0, 0),
    ('CANCELADA', 'Cancelada', '#6B7280', 5, 1, 0, 0);
    
    PRINT 'Tabla CRM_Cat_EstatusOportunidad creada y poblada';
END

-- ============================================================================
-- D. CRM_Cat_MotivosPerdida
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Cat_MotivosPerdida')
BEGIN
    CREATE TABLE dbo.CRM_Cat_MotivosPerdida (
        MotivoID INT IDENTITY(1,1) PRIMARY KEY,
        Codigo NVARCHAR(20) NOT NULL,
        Nombre NVARCHAR(100) NOT NULL,
        Descripcion NVARCHAR(500) NULL,
        Orden INT DEFAULT 0,
        Activo BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE()
    );
    
    INSERT INTO dbo.CRM_Cat_MotivosPerdida (Codigo, Nombre, Orden) VALUES
    ('PRECIO', 'Precio', 1),
    ('PRESUPUESTO', 'Falta de presupuesto', 2),
    ('COMPETENCIA', 'Competencia', 3),
    ('NO_RESPONDE', 'No respondió', 4),
    ('PAUSADO', 'Proyecto pausado', 5),
    ('NO_OBJETIVO', 'No era cliente objetivo', 6),
    ('FUERA_ALCANCE', 'Requerimiento fuera de alcance', 7),
    ('TIEMPO', 'Tiempos no alineados', 8),
    ('OTRO', 'Otro', 99);
    
    PRINT 'Tabla CRM_Cat_MotivosPerdida creada y poblada';
END

-- ============================================================================
-- E. CRM_Cat_MotivosGanada
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Cat_MotivosGanada')
BEGIN
    CREATE TABLE dbo.CRM_Cat_MotivosGanada (
        MotivoID INT IDENTITY(1,1) PRIMARY KEY,
        Codigo NVARCHAR(20) NOT NULL,
        Nombre NVARCHAR(100) NOT NULL,
        Descripcion NVARCHAR(500) NULL,
        Orden INT DEFAULT 0,
        Activo BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE()
    );
    
    INSERT INTO dbo.CRM_Cat_MotivosGanada (Codigo, Nombre, Orden) VALUES
    ('PRECIO', 'Mejor precio', 1),
    ('SERVICIO', 'Calidad de servicio', 2),
    ('RELACION', 'Relación comercial', 3),
    ('FUNCIONALIDAD', 'Funcionalidades', 4),
    ('SOPORTE', 'Soporte técnico', 5),
    ('REFERENCIA', 'Referencias de clientes', 6),
    ('INTEGRACION', 'Capacidad de integración', 7),
    ('OTRO', 'Otro', 99);
    
    PRINT 'Tabla CRM_Cat_MotivosGanada creada y poblada';
END

-- ============================================================================
-- F. CRM_Cat_Prioridades
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Cat_Prioridades')
BEGIN
    CREATE TABLE dbo.CRM_Cat_Prioridades (
        PrioridadID INT IDENTITY(1,1) PRIMARY KEY,
        Codigo NVARCHAR(20) NOT NULL,
        Nombre NVARCHAR(100) NOT NULL,
        Descripcion NVARCHAR(500) NULL,
        Orden INT DEFAULT 0,
        ColorHex NVARCHAR(7) DEFAULT '#6B7280',
        Activo BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE()
    );
    
    INSERT INTO dbo.CRM_Cat_Prioridades (Codigo, Nombre, ColorHex, Orden) VALUES
    ('BAJA', 'Baja', '#6B7280', 1),
    ('MEDIA', 'Media', '#3B82F6', 2),
    ('ALTA', 'Alta', '#F59E0B', 3),
    ('CRITICA', 'Crítica', '#EF4444', 4);
    
    PRINT 'Tabla CRM_Cat_Prioridades creada y poblada';
END

-- ============================================================================
-- G. CRM_Cat_Sectores
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Cat_Sectores')
BEGIN
    CREATE TABLE dbo.CRM_Cat_Sectores (
        SectorID INT IDENTITY(1,1) PRIMARY KEY,
        Codigo NVARCHAR(20) NOT NULL,
        Nombre NVARCHAR(100) NOT NULL,
        Descripcion NVARCHAR(500) NULL,
        Orden INT DEFAULT 0,
        Activo BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE()
    );
    
    INSERT INTO dbo.CRM_Cat_Sectores (Codigo, Nombre, Orden) VALUES
    ('RESTAURANTES', 'Restaurantes', 1),
    ('HOTELES', 'Hotelería', 2),
    ('RETAIL', 'Retail', 3),
    ('MANUFACTURA', 'Manufactura', 4),
    ('SERVICIOS', 'Servicios', 5),
    ('SALUD', 'Salud', 6),
    ('EDUCACION', 'Educación', 7),
    ('GOBIERNO', 'Gobierno', 8),
    ('OTRO', 'Otro', 99);
    
    PRINT 'Tabla CRM_Cat_Sectores creada y poblada';
END

-- ============================================================================
-- H. CRM_Cat_TamanosCliente
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Cat_TamanosCliente')
BEGIN
    CREATE TABLE dbo.CRM_Cat_TamanosCliente (
        TamanoID INT IDENTITY(1,1) PRIMARY KEY,
        Codigo NVARCHAR(20) NOT NULL,
        Nombre NVARCHAR(100) NOT NULL,
        Descripcion NVARCHAR(500) NULL,
        RangoEmpleadosMin INT NULL,
        RangoEmpleadosMax INT NULL,
        Orden INT DEFAULT 0,
        Activo BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE()
    );
    
    INSERT INTO dbo.CRM_Cat_TamanosCliente (Codigo, Nombre, RangoEmpleadosMin, RangoEmpleadosMax, Orden) VALUES
    ('MICRO', 'Micro (1-10)', 1, 10, 1),
    ('PEQUENA', 'Pequeña (11-50)', 11, 50, 2),
    ('MEDIANA', 'Mediana (51-250)', 51, 250, 3),
    ('GRANDE', 'Grande (251-1000)', 251, 1000, 4),
    ('ENTERPRISE', 'Enterprise (1000+)', 1001, NULL, 5);
    
    PRINT 'Tabla CRM_Cat_TamanosCliente creada y poblada';
END

-- ============================================================================
-- I. CRM_Cat_TiposPipeline
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Cat_TiposPipeline')
BEGIN
    CREATE TABLE dbo.CRM_Cat_TiposPipeline (
        TipoID INT IDENTITY(1,1) PRIMARY KEY,
        Codigo NVARCHAR(20) NOT NULL,
        Nombre NVARCHAR(100) NOT NULL,
        Descripcion NVARCHAR(500) NULL,
        Orden INT DEFAULT 0,
        Activo BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE()
    );
    
    INSERT INTO dbo.CRM_Cat_TiposPipeline (Codigo, Nombre, Orden) VALUES
    ('VENTAS', 'Ventas', 1),
    ('RENOVACIONES', 'Renovaciones', 2),
    ('UPSELL', 'Upselling', 3),
    ('PARTNER', 'Partners', 4);
    
    PRINT 'Tabla CRM_Cat_TiposPipeline creada y poblada';
END

-- ============================================================================
-- J. CRM_Cat_EstatusPropuesta
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Cat_EstatusPropuesta')
BEGIN
    CREATE TABLE dbo.CRM_Cat_EstatusPropuesta (
        EstatusID INT IDENTITY(1,1) PRIMARY KEY,
        Codigo NVARCHAR(20) NOT NULL,
        Nombre NVARCHAR(100) NOT NULL,
        Descripcion NVARCHAR(500) NULL,
        Orden INT DEFAULT 0,
        ColorHex NVARCHAR(7) DEFAULT '#6B7280',
        EsFinal BIT DEFAULT 0,
        Activo BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE()
    );
    
    INSERT INTO dbo.CRM_Cat_EstatusPropuesta (Codigo, Nombre, ColorHex, Orden, EsFinal) VALUES
    ('BORRADOR', 'Borrador', '#6B7280', 1, 0),
    ('REVISION', 'En revisión', '#F59E0B', 2, 0),
    ('APROBADA', 'Aprobada', '#10B981', 3, 0),
    ('ENVIADA', 'Enviada', '#3B82F6', 4, 0),
    ('ACEPTADA', 'Aceptada', '#059669', 5, 1),
    ('RECHAZADA', 'Rechazada', '#EF4444', 6, 1),
    ('VENCIDA', 'Vencida', '#9CA3AF', 7, 1);
    
    PRINT 'Tabla CRM_Cat_EstatusPropuesta creada y poblada';
END

-- ============================================================================
-- K. CRM_Cat_EstatusContrato
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Cat_EstatusContrato')
BEGIN
    CREATE TABLE dbo.CRM_Cat_EstatusContrato (
        EstatusID INT IDENTITY(1,1) PRIMARY KEY,
        Codigo NVARCHAR(20) NOT NULL,
        Nombre NVARCHAR(100) NOT NULL,
        Descripcion NVARCHAR(500) NULL,
        Orden INT DEFAULT 0,
        ColorHex NVARCHAR(7) DEFAULT '#6B7280',
        Activo BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE()
    );
    
    INSERT INTO dbo.CRM_Cat_EstatusContrato (Codigo, Nombre, ColorHex, Orden) VALUES
    ('BORRADOR', 'Borrador', '#6B7280', 1),
    ('REVISION', 'En revisión legal', '#F59E0B', 2),
    ('FIRMADO', 'Firmado', '#10B981', 3),
    ('VIGENTE', 'Vigente', '#059669', 4),
    ('POR_RENOVAR', 'Por renovar', '#3B82F6', 5),
    ('VENCIDO', 'Vencido', '#EF4444', 6),
    ('CANCELADO', 'Cancelado', '#9CA3AF', 7);
    
    PRINT 'Tabla CRM_Cat_EstatusContrato creada y poblada';
END

-- ============================================================================
-- L. SEED: Pipeline Default
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM dbo.CRM_Config_Pipelines WHERE Codigo = 'VENTAS_DEFAULT')
BEGIN
    INSERT INTO dbo.CRM_Config_Pipelines (Codigo, Nombre, Descripcion, TipoPipelineID, EsDefault) 
    VALUES ('VENTAS_DEFAULT', 'Pipeline de Ventas', 'Pipeline estándar de ventas', 1, 1);
    
    DECLARE @PipelineID INT = SCOPE_IDENTITY();
    
    INSERT INTO dbo.CRM_Config_PipelineEtapas (PipelineID, Codigo, Nombre, ProbabilidadDefault, Orden, ColorHex, EsEtapaInicial, EsEtapaCierre, EsCierreGanado, EsCierrePerdido) VALUES
    (@PipelineID, 'NUEVO', 'Nuevo', 10, 1, '#6B7280', 1, 0, 0, 0),
    (@PipelineID, 'CALIFICADO', 'Calificado', 20, 2, '#3B82F6', 0, 0, 0, 0),
    (@PipelineID, 'DIAGNOSTICO', 'Diagnóstico', 40, 3, '#8B5CF6', 0, 0, 0, 0),
    (@PipelineID, 'PROPUESTA', 'Propuesta', 60, 4, '#F59E0B', 0, 0, 0, 0),
    (@PipelineID, 'NEGOCIACION', 'Negociación', 80, 5, '#10B981', 0, 0, 0, 0),
    (@PipelineID, 'GANADO', 'Cierre Ganado', 100, 6, '#059669', 0, 1, 1, 0),
    (@PipelineID, 'PERDIDO', 'Cierre Perdido', 0, 7, '#EF4444', 0, 1, 0, 1);
    
    PRINT 'Pipeline de Ventas Default creado con 7 etapas';
END

PRINT '';
PRINT '============================================';
PRINT 'SCRIPT 02 CATÁLOGOS COMPLETADO';
PRINT '============================================';
