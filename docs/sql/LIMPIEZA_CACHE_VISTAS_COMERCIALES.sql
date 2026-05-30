-- =============================================================================
-- SCRIPT: LIMPIEZA CACHÉ VISTAS MATERIALIZADAS COMERCIALES
-- OBJETIVO: Forzar recarga de datos en el frontend
-- =============================================================================

-- Limpiar caché de vistas materializadas (si existen)
REFRESH MATERIALIZED VIEW CONCURRENTLY vista_ventas_comerciales;

-- Actualizar el timestamp de control para forzar re-lectura del frontend
UPDATE control_sincronizaciones 
SET ultima_actualizacion = NOW() 
WHERE modulo = 'comercial';
