-- ======================================================================================
-- SCRIPT CONSOLIDADO: SYNC_LOGS_Y_MENUS_EDARSAHUB.sql
-- PROYECTO: EDARSA HUB ERP - AUDITORÍA + MENÚS SQL-FIRST
-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
-- ======================================================================================

USE [EDARSAHUB];
GO

-- ======================================================================================
-- PARTE 1: TABLA DE LOGS DE AUDITORÍA
-- ======================================================================================
IF OBJECT_ID('dbo.Sync_Logs', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sync_Logs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        service NVARCHAR(100) NOT NULL,
        type NVARCHAR(20) NOT NULL,
        message NVARCHAR(MAX) NOT NULL,
        timestamp DATETIME DEFAULT GETDATE(),
        operador NVARCHAR(100) DEFAULT 'SISTEMA_AUTOGESTIVO_FALLBACK'
    );
    CREATE NONCLUSTERED INDEX IX_Sync_Logs_Timestamp_Service 
    ON dbo.Sync_Logs (timestamp DESC, service);
    PRINT 'Tabla de auditoría [Sync_Logs] creada exitosamente.';
END
GO

INSERT INTO dbo.Sync_Logs (service, type, message, timestamp, operador)
VALUES (
    'CACHE_STORAGE_MONITOR',
    'INFO',
    N'Estrategia de persistencia híbrida LocalStorage activa: Prevención de estados en cero mediante caché local no-volátil de última transacción exitosa.',
    GETDATE(),
    N'SISTEMA_ADMINISTRATIVO_PRIME'
);
GO

-- ======================================================================================
-- PARTE 2: TABLA DE CONFIGURACIÓN DE MENÚS
-- ======================================================================================
IF OBJECT_ID('dbo.Sync_Menus', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sync_Menus (
        id INT IDENTITY(1,1) PRIMARY KEY,
        titulo NVARCHAR(100) NOT NULL,
        label NVARCHAR(100) NOT NULL,
        icon NVARCHAR(50) NOT NULL,
        route NVARCHAR(100) NOT NULL,
        active BIT DEFAULT 1,
        orden INT NOT NULL,
        rol_permitido NVARCHAR(100) DEFAULT 'OPERADOR_EDARSA',
        ultima_actualizacion DATETIME DEFAULT GETDATE()
    );
    PRINT 'Tabla de configuración de menús [Sync_Menus] creada exitosamente.';
END
GO

TRUNCATE TABLE dbo.Sync_Menus;
GO

INSERT INTO dbo.Sync_Menus (titulo, label, icon, route, active, orden, rol_permitido)
VALUES 
(N'Tablero Ejecutivo', N'Tablero Ejecutivo', N'LayoutDashboard', N'kpis', 1, 1, 'OPERADOR_EDARSA'),
(N'Marketing CRM', N'Marketing CRM', N'Users', N'crm', 1, 2, 'OPERADOR_EDARSA'),
(N'Ventas & Flujos (Emergent)', N'Ventas (Emergent)', N'Cpu', N'flows', 1, 3, 'OPERADOR_EDARSA'),
(N'Inventarios FinOps', N'Inventarios FinOps', N'Database', N'costos-placeholder', 1, 4, 'OPERADOR_EDARSA'),
(N'Soporte (Tickets)', N'Soporte Tareas', N'LifeBuoy', N'tickets', 1, 5, 'OPERADOR_EDARSA');
GO

INSERT INTO dbo.Sync_Logs (service, type, message, timestamp, operador)
VALUES (
    'SISTEMA_MENUS_DEPLOY',
    'SUCCESS',
    N'Implantación segura de menús en base de datos Sync_Menus y mapeo de endpoints de la API /api/sistema/menus/usuario.',
    GETDATE(),
    N'SISTEMA_ADMINISTRATIVO_PRIME'
);
GO

-- ======================================================================================
-- CONSULTAS DE VERIFICACIÓN
-- ======================================================================================
SELECT TOP 5 id, service, type, LEFT(message, 80) AS message, timestamp FROM dbo.Sync_Logs ORDER BY timestamp DESC;
SELECT id, titulo, icon, route, active, orden FROM dbo.Sync_Menus ORDER BY orden;
GO
