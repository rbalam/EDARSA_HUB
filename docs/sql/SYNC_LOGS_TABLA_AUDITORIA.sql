-- ======================================================================================
-- SCRIPT DE BASE DE DATOS: SYNC_LOGS_TABLA_AUDITORIA.sql
-- PROYECTO: EDARSA HUB ERP - SISTEMA DE AUDITORÍA Y MONITOREO EN TIEMPO REAL
-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
-- OBJETIVO: Creación de la tabla de logs de sincronización para soporte de auditoría
-- ======================================================================================

USE [EDARSAHUB];
GO

-- 1. VERIFICAR EXISTENCIA Y CREAR LA TABLA DE LOGS DE AUDITORÍA
IF OBJECT_ID('dbo.Sync_Logs', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sync_Logs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        service NVARCHAR(100) NOT NULL, -- Ej: 'CORRECCION_KPI_PROYECCION_ANUAL', 'SQL_PIPE'
        type NVARCHAR(20) NOT NULL,    -- Ej: 'SUCCESS', 'INFO', 'WARN', 'ERROR'
        message NVARCHAR(MAX) NOT NULL,
        timestamp DATETIME DEFAULT GETDATE(),
        operador NVARCHAR(100) DEFAULT 'SISTEMA_AUTOGESTIVO_FALLBACK'
    );
    
    -- Crear índice para optimizar consultas de auditoría por fecha y servicio
    CREATE NONCLUSTERED INDEX IX_Sync_Logs_Timestamp_Service 
    ON dbo.Sync_Logs (timestamp DESC, service);

    PRINT 'Tabla de auditoría [Sync_Logs] creada exitosamente con sus respectivos índices.';
END
ELSE
BEGIN
    PRINT 'La tabla [Sync_Logs] ya existe en el esquema. Procediendo a registrar calibración...';
END
GO

-- 2. REGISTRAR EVENTO INICIAL DE FALLBACK Y CONTROL DE DATOS SIN CEROS (PREVENCIÓN DE CACHÉ DE COLD START)
INSERT INTO dbo.Sync_Logs (service, type, message, timestamp, operador)
VALUES (
    'CACHE_STORAGE_MONITOR',
    'INFO',
    N'Estrategia de persistencia híbrida LocalStorage activa: Prevención de estados en cero mediante caché local no-volátil de última transacción exitosa.',
    GETDATE(),
    N'SISTEMA_ADMINISTRATIVO_PRIME'
);
GO

-- 3. CONSULTAR ESTADO DE RECIENTES LOGS DE SINCRONIZACIÓN
SELECT TOP 20 
    id, 
    service AS [Módulo / Servicio], 
    type AS [Severidad], 
    message AS [Log de Suceso], 
    timestamp AS [Fecha y Hora], 
    operador AS [Origen]
FROM 
    dbo.Sync_Logs
ORDER BY 
    timestamp DESC;
GO
