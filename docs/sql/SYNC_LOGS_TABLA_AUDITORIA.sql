-- ======================================================================================
-- REGISTRO DE AUDITORÍA: CONTROL DE CACHÉ OFFLINE Y DISPONIBILIDAD DIGITAL COMERCIAL
-- MOTOR: SQL Server 2012+ (EDARSAHUB)
-- ======================================================================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Sync_Logs')
BEGIN
    CREATE TABLE dbo.Sync_Logs (
        IdLog INT IDENTITY(1,1) PRIMARY KEY,
        service VARCHAR(100),
        type VARCHAR(20),
        message VARCHAR(max),
        timestamp DATETIME DEFAULT GETDATE()
    );
END
GO

-- Registrar el protocolo de blindaje de interrupciones
INSERT INTO dbo.Sync_Logs (service, type, message, timestamp)
VALUES (
    'SHIELD_LOCAL_PERSISTENCE',
    'SUCCESS',
    'Blindaje de Front-End activado: Algoritmo de Fallback LocalStorage cargado. Los tableros evitarán la renderización en ceros ($0) ante fluctuaciones de la API.',
    GETDATE()
);
GO

PRINT 'Protocolo de registro guardado correctamente en EDARSAHUB.';
