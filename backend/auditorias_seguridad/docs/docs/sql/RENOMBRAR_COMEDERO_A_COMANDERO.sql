-- =============================================================================
-- SCRIPT: RENOMBRAR MÓDULO COMEDERO -> COMANDERO
-- OBJETIVO: Actualizar el nombre del módulo satélite en tablas maestras
-- =============================================================================

-- Actualizar el nombre del módulo en la tabla maestra
UPDATE modulos_hub 
SET nombre = 'Comandero' 
WHERE nombre = 'Comedero';

-- Si tienes una tabla de configuración de sucursales, actualízalo también
UPDATE configuracion_sucursales_modulos 
SET nombre_modulo = 'Comandero' 
WHERE nombre_modulo = 'Comedero';
