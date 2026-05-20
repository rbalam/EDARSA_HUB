-- ============================================================================
-- CONSULTAS PARA DBA - EJECUTAR CON LOGIN 'sa' EN SERVIDOR ns559627
-- Fecha: 2026-05-20
-- Objetivo: Identificar el proceso externo que escribe FechaOperacion incorrecta
-- ============================================================================

-- CONSULTA 1: SQL Server Agent Jobs Activos
-- ============================================================================
USE msdb;
GO

SELECT 
    j.job_id,
    j.name AS job_name,
    j.enabled,
    SUSER_SNAME(j.owner_sid) AS owner_name,
    j.date_created,
    j.date_modified
FROM dbo.sysjobs j
WHERE j.enabled = 1
ORDER BY j.name;
GO

-- CONSULTA 2: Job Steps que mencionen las tablas afectadas
-- ============================================================================
USE msdb;
GO

SELECT
    j.job_id,
    j.name AS job_name,
    SUSER_SNAME(j.owner_sid) AS owner_name,
    j.enabled,
    s.step_id,
    s.step_name,
    s.subsystem,
    s.database_name,
    s.command
FROM dbo.sysjobs j
INNER JOIN dbo.sysjobsteps s ON j.job_id = s.job_id
WHERE
    s.command LIKE '%Comercial_Ventas_Dia_Abiertas_v2%'
    OR s.command LIKE '%Comercial_SyncLog_v2%'
    OR s.command LIKE '%Ventas_Dia%'
    OR s.command LIKE '%ventas_dia%'
    OR s.command LIKE '%FechaOperacion%'
    OR s.command LIKE '%fecha_operacion%'
    OR s.command LIKE '%ABIERTA-%'
ORDER BY j.name, s.step_id;
GO

-- CONSULTA 3: Schedules de Jobs (buscar los que corren cada ~5-10 minutos)
-- ============================================================================
USE msdb;
GO

SELECT
    j.name AS job_name,
    j.enabled AS job_enabled,
    SUSER_SNAME(j.owner_sid) AS owner_name,
    sch.name AS schedule_name,
    sch.enabled AS schedule_enabled,
    sch.freq_type,
    CASE sch.freq_type
        WHEN 1 THEN 'Once'
        WHEN 4 THEN 'Daily'
        WHEN 8 THEN 'Weekly'
        WHEN 16 THEN 'Monthly'
        WHEN 32 THEN 'Monthly relative'
        WHEN 64 THEN 'SQL Agent Start'
        WHEN 128 THEN 'When idle'
        ELSE CAST(sch.freq_type AS VARCHAR)
    END AS freq_type_desc,
    sch.freq_subday_type,
    CASE sch.freq_subday_type
        WHEN 1 THEN 'At specified time'
        WHEN 2 THEN 'Seconds'
        WHEN 4 THEN 'Minutes'
        WHEN 8 THEN 'Hours'
        ELSE CAST(sch.freq_subday_type AS VARCHAR)
    END AS freq_subday_desc,
    sch.freq_subday_interval,
    sch.active_start_time,
    sch.active_end_time
FROM dbo.sysjobs j
INNER JOIN dbo.sysjobschedules js ON j.job_id = js.job_id
INNER JOIN dbo.sysschedules sch ON js.schedule_id = sch.schedule_id
WHERE j.enabled = 1
ORDER BY j.name, sch.name;
GO

-- CONSULTA 4: Historial de Jobs de HOY (últimas 300 ejecuciones)
-- ============================================================================
USE msdb;
GO

SELECT TOP 300
    j.name AS job_name,
    h.step_id,
    h.step_name,
    h.run_date,
    h.run_time,
    h.run_duration,
    h.run_status,
    CASE h.run_status
        WHEN 0 THEN 'FAILED'
        WHEN 1 THEN 'SUCCESS'
        WHEN 2 THEN 'RETRY'
        WHEN 3 THEN 'CANCELED'
        WHEN 4 THEN 'IN PROGRESS'
        ELSE 'UNKNOWN'
    END AS run_status_desc,
    LEFT(h.message, 200) AS message_preview
FROM dbo.sysjobhistory h
INNER JOIN dbo.sysjobs j ON h.job_id = j.job_id
WHERE h.run_date >= CONVERT(int, CONVERT(varchar, GETDATE(), 112))
ORDER BY h.instance_id DESC;
GO

-- CONSULTA 5: Todos los Job Steps (para buscar cualquier escritura a las tablas)
-- ============================================================================
USE msdb;
GO

SELECT
    j.name AS job_name,
    j.enabled,
    s.step_id,
    s.step_name,
    s.subsystem,
    s.database_name,
    s.command
FROM dbo.sysjobs j
INNER JOIN dbo.sysjobsteps s ON j.job_id = s.job_id
WHERE j.enabled = 1
ORDER BY j.name, s.step_id;
GO

-- ============================================================================
-- FIN DE CONSULTAS
-- Por favor compartir los resultados de todas las consultas
-- ============================================================================
