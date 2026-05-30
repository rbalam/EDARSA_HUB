-- =============================================================================
-- SCRIPT: LIMPIEZA CACHÉ + SYNC + VERIFICACIÓN DATOS COMERCIALES
-- OBJETIVO: Refrescar vistas y validar datos recientes del dashboard
-- =============================================================================

-- 1. Limpiar el caché de la vista de reportes comerciales
REFRESH MATERIALIZED VIEW CONCURRENTLY vista_ventas_comerciales;

-- 2. Actualizar el estado de sincronización para que el dashboard vea datos nuevos
UPDATE control_sincronizaciones 
SET ultima_actualizacion = NOW(), estatus = 'ACTIVO'
WHERE modulo = 'comercial';

-- 3. Verificar si existen datos reales para hoy
SELECT id, nombre, fecha, total_ventas 
FROM ventas_diarias 
WHERE fecha >= CURRENT_DATE - INTERVAL '1 day' 
ORDER BY fecha DESC LIMIT 10;
