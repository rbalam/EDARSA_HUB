/* 
   EDARSAHUB - Diagnóstico Tablas Inteligencia Comercial
   Script: 002_diagnostico_inteligencia.sql
   Modo: diagnostic (solo lectura)
*/

-- 1. Conteo de registros en tablas clave
SELECT 'Sync_Sales' AS Tabla, COUNT(*) AS Registros FROM Sync_Sales
UNION ALL
SELECT 'Sync_PAX_Detalle', COUNT(*) FROM Sync_PAX_Detalle
UNION ALL
SELECT 'Comercial_KPIs_Diarios_v2', COUNT(*) FROM Comercial_KPIs_Diarios_v2
UNION ALL
SELECT 'Sys_Scheduler_Jobs', COUNT(*) FROM Sys_Scheduler_Jobs;

GO

-- 2. Jobs programados
SELECT 
    JobID,
    JobName,
    CronExpression,
    JobType,
    Status,
    LastRunDate
FROM Sys_Scheduler_Jobs
ORDER BY JobName;

GO

-- 3. Últimos KPIs diarios
SELECT TOP 10
    unidad_negocio_nombre,
    fecha_operacion,
    ventas_total,
    pax_total,
    tickets_total,
    ticket_promedio,
    fuente_original,
    fecha_ultima_actualizacion
FROM Comercial_KPIs_Diarios_v2
ORDER BY fecha_operacion DESC, unidad_negocio_nombre;

GO

-- 4. Unidades de negocio activas en KPIs
SELECT DISTINCT
    unidad_negocio_nombre,
    sistema_origen,
    COUNT(*) AS dias_con_datos
FROM Comercial_KPIs_Diarios_v2
WHERE activo = 1
GROUP BY unidad_negocio_nombre, sistema_origen
ORDER BY unidad_negocio_nombre;

GO
