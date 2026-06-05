-- =============================================================================
-- EDARSA HUB - Tablas para Workflows y Tareas de Inventario
-- Migración de MongoDB a SQL Server
-- Fecha: Mayo 2026
-- =============================================================================

-- 1. Tabla principal de Workflows de Inventario
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Workflow_Inventarios')
BEGIN
    CREATE TABLE Workflow_Inventarios (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        WorkflowID VARCHAR(50) NOT NULL UNIQUE,
        ProcesadoID VARCHAR(500),                    -- folio_final_key
        FolioInventario VARCHAR(100),
        ServerID VARCHAR(50) NOT NULL,
        ServerName VARCHAR(100),
        SucursalID VARCHAR(100),
        SucursalNombre VARCHAR(100),
        AlmacenID VARCHAR(50),
        AlmacenNombre VARCHAR(100),
        FoliosInicialesJSON NVARCHAR(MAX),          -- JSON array
        FoliosFinalesJSON NVARCHAR(MAX),            -- JSON array
        FolioFinalKey VARCHAR(500),
        FechaAnalisisIni DATE,
        FechaAnalisisFin DATE,
        EstadoWorkflow VARCHAR(50) DEFAULT 'PENDIENTE_ASIGNACION',
        Estado VARCHAR(50) DEFAULT 'pendiente',
        CicloActual INT DEFAULT 1,
        TotalProductosDiferencia INT DEFAULT 0,
        ValorTotalDiferencias DECIMAL(18,2) DEFAULT 0,
        FechaCreacion DATETIME2 DEFAULT GETUTCDATE(),
        FechaUltimaActualizacion DATETIME2 DEFAULT GETUTCDATE(),
        UsuarioCreadorID VARCHAR(50),
        NotasJSON NVARCHAR(MAX)                      -- JSON array
    );
    
    CREATE INDEX IX_Workflow_ServerID ON Workflow_Inventarios(ServerID);
    CREATE INDEX IX_Workflow_Estado ON Workflow_Inventarios(Estado);
    CREATE INDEX IX_Workflow_FechaCreacion ON Workflow_Inventarios(FechaCreacion);
    
    PRINT 'Tabla Workflow_Inventarios creada exitosamente';
END
ELSE
    PRINT 'Tabla Workflow_Inventarios ya existe';

-- 2. Tabla de Tareas de Inventario
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Tareas_Inventario')
BEGIN
    CREATE TABLE Tareas_Inventario (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        TareaID VARCHAR(50) NOT NULL UNIQUE,
        WorkflowID VARCHAR(50) NOT NULL,
        TipoTarea VARCHAR(50) DEFAULT 'JUSTIFICAR',
        Titulo VARCHAR(500),
        Descripcion NVARCHAR(MAX),
        EstadoTarea VARCHAR(50) DEFAULT 'PENDIENTE',
        Prioridad VARCHAR(20) DEFAULT 'MEDIA',
        UsuarioAsignadoID VARCHAR(50),
        UsuarioAsignadoNombre VARCHAR(200),
        FechaCreacion DATETIME2 DEFAULT GETUTCDATE(),
        FechaAsignacion DATETIME2,
        FechaLimite DATETIME2,
        FechaActualizacion DATETIME2,
        FechaPrimeraAccion DATETIME2,
        FechaCompletada DATETIME2,
        Ciclo INT DEFAULT 1,
        EsReasignacion BIT DEFAULT 0,
        Vencida BIT DEFAULT 0,
        EstadoSLA VARCHAR(50),
        FechaActualizacionSLA DATETIME2,
        NotificacionWarningEnviada BIT DEFAULT 0,
        NotificacionVencidoEnviada BIT DEFAULT 0,
        NotificacionEscaladoEnviada BIT DEFAULT 0,
        NotasJSON NVARCHAR(MAX)
    );
    
    CREATE INDEX IX_Tareas_WorkflowID ON Tareas_Inventario(WorkflowID);
    CREATE INDEX IX_Tareas_EstadoTarea ON Tareas_Inventario(EstadoTarea);
    CREATE INDEX IX_Tareas_UsuarioAsignadoID ON Tareas_Inventario(UsuarioAsignadoID);
    CREATE INDEX IX_Tareas_FechaLimite ON Tareas_Inventario(FechaLimite);
    
    PRINT 'Tabla Tareas_Inventario creada exitosamente';
END
ELSE
    PRINT 'Tabla Tareas_Inventario ya existe';

-- 3. Tabla de Detalle de Diferencias
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Workflow_DetalleDiferencias')
BEGIN
    CREATE TABLE Workflow_DetalleDiferencias (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        DetalleID VARCHAR(50) NOT NULL UNIQUE,
        WorkflowID VARCHAR(50) NOT NULL,
        CodigoProducto VARCHAR(50),
        NombreProducto VARCHAR(200),
        Categoria VARCHAR(100),
        Familia VARCHAR(100),
        SubFamilia VARCHAR(100),
        Unidad VARCHAR(50),
        CostoUnitario DECIMAL(18,4) DEFAULT 0,
        InvInicialCantidad DECIMAL(18,4) DEFAULT 0,
        InvFinalCantidad DECIMAL(18,4) DEFAULT 0,
        InvTeoricoCantidad DECIMAL(18,4) DEFAULT 0,
        DiferenciaCantidad DECIMAL(18,4) DEFAULT 0,
        DiferenciaCosto DECIMAL(18,2) DEFAULT 0,
        DiferenciaPorcentaje DECIMAL(10,2) DEFAULT 0,
        Movimientos DECIMAL(18,4) DEFAULT 0,
        Ventas DECIMAL(18,4) DEFAULT 0,
        EstadoJustificacion VARCHAR(50) DEFAULT 'pendiente',
        RequiereJustificacionCompleta BIT DEFAULT 0,
        FechaCreacion DATETIME2 DEFAULT GETUTCDATE()
    );
    
    CREATE INDEX IX_Detalle_WorkflowID ON Workflow_DetalleDiferencias(WorkflowID);
    CREATE INDEX IX_Detalle_CodigoProducto ON Workflow_DetalleDiferencias(CodigoProducto);
    
    PRINT 'Tabla Workflow_DetalleDiferencias creada exitosamente';
END
ELSE
    PRINT 'Tabla Workflow_DetalleDiferencias ya existe';

-- 4. Tabla de Inventarios sin Asignar
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Inventarios_SinAsignar')
BEGIN
    CREATE TABLE Inventarios_SinAsignar (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        RegistroID VARCHAR(50) NOT NULL UNIQUE,
        ServerID VARCHAR(50),
        ServerName VARCHAR(100),
        SucursalID VARCHAR(100),
        SucursalNombre VARCHAR(100),
        AlmacenID VARCHAR(50),
        AlmacenNombre VARCHAR(100),
        FolioInventario VARCHAR(100),
        TotalDiferencias INT DEFAULT 0,
        ValorDiferencias DECIMAL(18,2) DEFAULT 0,
        FechaDeteccion DATETIME2 DEFAULT GETUTCDATE(),
        Estado VARCHAR(50) DEFAULT 'PENDIENTE_CONFIGURACION',
        Notificado BIT DEFAULT 0
    );
    
    CREATE INDEX IX_SinAsignar_ServerID ON Inventarios_SinAsignar(ServerID);
    CREATE INDEX IX_SinAsignar_Estado ON Inventarios_SinAsignar(Estado);
    
    PRINT 'Tabla Inventarios_SinAsignar creada exitosamente';
END
ELSE
    PRINT 'Tabla Inventarios_SinAsignar ya existe';

-- 5. Tabla de Alertas del Sistema
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Alertas_Sistema')
BEGIN
    CREATE TABLE Alertas_Sistema (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        AlertaID VARCHAR(50) NOT NULL UNIQUE,
        Tipo VARCHAR(100),
        Severidad VARCHAR(20) DEFAULT 'info',
        Titulo VARCHAR(200),
        Mensaje NVARCHAR(MAX),
        Modulo VARCHAR(50),
        FechaCreacion DATETIME2 DEFAULT GETUTCDATE(),
        DatosJSON NVARCHAR(MAX),
        AccionSugerida VARCHAR(500),
        Acknowledged BIT DEFAULT 0,
        AcknowledgedBy VARCHAR(50),
        AcknowledgedAt DATETIME2
    );
    
    CREATE INDEX IX_Alertas_Tipo ON Alertas_Sistema(Tipo);
    CREATE INDEX IX_Alertas_Acknowledged ON Alertas_Sistema(Acknowledged);
    
    PRINT 'Tabla Alertas_Sistema creada exitosamente';
END
ELSE
    PRINT 'Tabla Alertas_Sistema ya existe';

-- 6. Tabla de Configuración Operativa
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Configuracion_Operativa')
BEGIN
    CREATE TABLE Configuracion_Operativa (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        Clave VARCHAR(100) NOT NULL UNIQUE,
        Valor VARCHAR(500),
        Tipo VARCHAR(20) DEFAULT 'string',
        Descripcion VARCHAR(500),
        FechaActualizacion DATETIME2 DEFAULT GETUTCDATE()
    );
    
    -- Insertar valores SLA por defecto
    INSERT INTO Configuracion_Operativa (Clave, Valor, Tipo, Descripcion) VALUES
    ('SLA_JUSTIFICACION_SIMPLE_HORAS', '24', 'number', 'Horas límite para justificación simple'),
    ('SLA_JUSTIFICACION_COMPLETA_HORAS', '48', 'number', 'Horas límite para justificación completa'),
    ('SLA_REVISION_OPERATIVO_HORAS', '24', 'number', 'Horas límite para revisión operativa'),
    ('SLA_AUDITORIA_HORAS', '72', 'number', 'Horas límite para auditoría'),
    ('SLA_UMBRAL_ADVERTENCIA_PORCENTAJE', '50', 'number', 'Umbral advertencia %'),
    ('SLA_UMBRAL_URGENTE_PORCENTAJE', '80', 'number', 'Umbral urgente %'),
    ('SLA_UMBRAL_VENCIDO_PORCENTAJE', '100', 'number', 'Umbral vencido %'),
    ('SLA_UMBRAL_ESCALAMIENTO_PORCENTAJE', '150', 'number', 'Umbral escalamiento %'),
    ('DIAS_LIMITE_TAREA_DEFAULT', '3', 'number', 'Días límite por defecto para tareas');
    
    PRINT 'Tabla Configuracion_Operativa creada con valores por defecto';
END
ELSE
    PRINT 'Tabla Configuracion_Operativa ya existe';

-- 7. Tabla de Config Asignaciones (ya debería existir, verificar)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Config_Asignaciones')
BEGIN
    CREATE TABLE Config_Asignaciones (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        ConfigID VARCHAR(50) NOT NULL UNIQUE,
        ServerID VARCHAR(50) NOT NULL,
        AlmacenID VARCHAR(50) DEFAULT '',
        UsuarioResponsableID VARCHAR(50) NOT NULL,
        Prioridad INT DEFAULT 1,
        Activa BIT DEFAULT 1,
        FechaCreacion DATETIME2 DEFAULT GETUTCDATE(),
        FechaActualizacion DATETIME2
    );
    
    CREATE INDEX IX_Config_ServerAlmacen ON Config_Asignaciones(ServerID, AlmacenID);
    
    PRINT 'Tabla Config_Asignaciones creada exitosamente';
END
ELSE
    PRINT 'Tabla Config_Asignaciones ya existe';

PRINT '=== Migración de tablas completada ===';
