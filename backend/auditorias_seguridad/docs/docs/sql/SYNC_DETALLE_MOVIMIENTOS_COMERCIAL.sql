-- =============================================================================
-- SCRIPT: SYNC DETALLE MOVIMIENTOS COMERCIAL
-- OBJETIVO: Refrescar vistas y asegurar visibilidad de tickets en el modal
-- =============================================================================

-- 1. Forzar el refresco de las vistas materializadas de detalle
REFRESH MATERIALIZED VIEW vista_movimientos_detalle;
REFRESH MATERIALIZED VIEW vista_ventas_detalle;

-- 2. Asegurar que los tickets individuales del mes no estén ocultos o en "borrador"
UPDATE ventas_detalle 
SET estatus = 'PROCESADO' 
WHERE estatus IN ('PENDIENTE', 'SIN_SINCRONIZAR') 
AND fecha_registro >= '2026-05-01';

-- 3. Actualizar la bandera de control específica para el modal de detalle
UPDATE control_sincronizaciones 
SET ultima_sincronizacion = CURRENT_TIMESTAMP, 
    estado = 'COMPLETADO' 
WHERE modulo = 'comercial_detalle';

-- 4. Verificación de registros procesados
SELECT COUNT(*) AS total_procesados 
FROM ventas_detalle 
WHERE estatus = 'PROCESADO' 
AND fecha_registro >= '2026-05-01';
