-- =============================================================================
-- SCRIPT: VERIFICACIÓN PROVEEDORES EN SQL CENTRAL
-- OBJETIVO: Validar si la migración de proveedores a SQL está completa
-- =============================================================================

-- Query para verificar si los proveedores ya viven en el cerebro SQL
SELECT count(*), estatus 
FROM proveedores_central 
GROUP BY estatus;

-- Si este query devuelve resultados, la migración es viable y el endpoint funcionará
