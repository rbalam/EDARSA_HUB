-- 1. Refrescar las vistas materializadas de ventas para acceso inmediato
REFRESH MATERIALIZED VIEW CONCURRENTLY vista_ventas_consolidadas_mes;
REFRESH MATERIALIZED VIEW CONCURRENTLY vista_pax_cheque_promedio;

-- 2. Asegurar que el estado del tablero comercial marque los datos como "Frescos"
UPDATE control_sincronizaciones 
SET ultima_sincronizacion = CURRENT_TIMESTAMP, 
    estado = 'COMPLETADO',
    requiere_calculo = FALSE
WHERE modulo = 'tablero_comercial';

-- 3. Limpiar cualquier query atascado que esté asfixiando el pool
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'active' 
AND query ILIKE '%comercial/dashboard%' 
AND pid <> pg_backend_pid();
