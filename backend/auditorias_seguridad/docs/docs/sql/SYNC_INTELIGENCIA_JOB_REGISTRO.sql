-- ============================================================
-- SCRIPT: Registro de Job de Sincronización de PAX (Inteligencia Comercial)
-- Archivo: SYNC_INTELIGENCIA_JOB_REGISTRO.sql
-- Tabla destino: Sys_Scheduler_Jobs
-- 
-- NOTA: Este script debe ser ejecutado manualmente por el DBA
--       en SQL Server Management Studio con permisos de escritura.
-- ============================================================

IF NOT EXISTS (SELECT 1 FROM Sys_Scheduler_Jobs WHERE JobID = 'SYNC-INTELIGENCIA-01')
BEGIN
    INSERT INTO Sys_Scheduler_Jobs (
        JobID, 
        JobName, 
        CronExpression, 
        JobType, 
        Status, 
        LastRunDate
    )
    VALUES (
        'SYNC-INTELIGENCIA-01', 
        'inteligencia_comercial_sync', 
        '0 * * * *', 
        'DATA_SYNC', 
        'ACTIVE', 
        GETDATE()
    );
    PRINT '✅ Job SYNC-INTELIGENCIA-01 insertado y activado exitosamente.';
END
ELSE
BEGIN
    UPDATE Sys_Scheduler_Jobs 
    SET 
        JobName = 'inteligencia_comercial_sync', 
        CronExpression = '0 * * * *',
        JobType = 'DATA_SYNC',
        Status = 'ACTIVE'
    WHERE JobID = 'SYNC-INTELIGENCIA-01';
    
    PRINT '✅ Job SYNC-INTELIGENCIA-01 actualizado exitosamente.';
END
GO

-- ============================================================
-- Verificación post-ejecución
-- ============================================================
SELECT 
    JobID,
    JobName,
    CronExpression,
    JobType,
    Status,
    LastRunDate
FROM Sys_Scheduler_Jobs
WHERE JobID = 'SYNC-INTELIGENCIA-01';
GO
