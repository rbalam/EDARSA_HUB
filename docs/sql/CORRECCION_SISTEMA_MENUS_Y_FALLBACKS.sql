-- ======================================================================================
-- SCRIPT DE BASE DE DATOS: CORRECCION_SISTEMA_MENUS_Y_FALLBACKS.sql
-- PROYECTO: EDARSA HUB ERP - CONFIGURACIÓN DE MENÚS DINÁMICOS SQL-FIRST
-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
-- OBJETIVO: Prevención de errores HTTP 403 y recuperación del flujo de menús en el ERP
-- ======================================================================================

USE [EDARSAHUB];
GO

-- 1. VERIFICAR EXISTENCIA Y CREAR LA TABLA DE CONFIGURACIÓN DE MENÚS SISTEMA
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
ELSE
BEGIN
    PRINT 'La tabla [Sync_Menus] ya existe en el esquema.';
END
GO

-- 2. LIMPIAR E INSERTAR MENÚS PREPARADOS DE ALTA COHERENCIA OPERACIONAL
TRUNCATE TABLE dbo.Sync_Menus;
GO

INSERT INTO dbo.Sync_Menus (titulo, label, icon, route, active, orden, rol_permitido)
VALUES 
(N'Tablero Ejecutivo', N'Tablero Ejecutivo', N'LayoutDashboard', N'kpis', 1, 1, 'OPERADOR_EDARSA'),
(N'Marketing CRM', N'Marketing CRM', N'Users', N'crm', 1, 2, 'OPERADOR_EDARSA'),
(N'Ventas & Flujos (Emergent)', N'Ventas (Emergent)', N'Cpu', N'flows', 1, 3, 'OPERADOR_EDARSA'),
(N'Inventarios FinOps', N'Inventarios FinOps', N'Database', N'costos-placeholder', 1, 4, 'OPERADOR_EDARSA'),
(N'Soporte (Tickets)', N'Soporte Tareas', N'LifeBuoy', N'tickets', 1, 5, 'OPERADOR_EDARSA');

PRINT 'Menús del ERP cargados exitosamente de forma SQL-First.';
GO

-- 3. INTEGRAR REGISTRO DE AUDITORÍA EN LA BITÁCORA CENTRAL (Sync_Logs)
IF OBJECT_ID('dbo.Sync_Logs', 'U') IS NOT NULL
BEGIN
    INSERT INTO dbo.Sync_Logs (service, type, message, timestamp, operador)
    VALUES (
        'SISTEMA_MENUS_DEPLOY',
        'SUCCESS',
        N'Implantación segura de menús en de base de datos Sync_Menus y mapeo de endpoints de la API /api/sistema/menus/usuario.',
        GETDATE(),
        N'SISTEMA_ADMINISTRATIVO_PRIME'
    );
    PRINT 'Suceso registrado en la bitácora Sync_Logs.';
END
GO

-- 4. CONSULTA DE VERIFICACIÓN / CONTROL DE CALIDAD
SELECT 
    id,
    titulo AS [Módulo],
    icon AS [Ícono Lucide],
    route AS [Ruta React],
    active AS [Estado Activo],
    orden AS [Orden de Despliegue],
    rol_permitido AS [Permisos Requeridos]
FROM 
    dbo.Sync_Menus
ORDER BY 
    orden ASC;
GO
