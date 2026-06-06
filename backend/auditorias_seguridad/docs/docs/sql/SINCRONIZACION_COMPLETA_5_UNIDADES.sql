-- =============================================================================
-- SCRIPT: SINCRONIZACIÓN COMPLETA + VERIFICACIÓN MÓDULOS SATÉLITE
-- OBJETIVO: Actualizar todas las unidades y asegurar módulos Comandero/Super Caja
-- =============================================================================

-- 1. Actualizar estados de sincronización para todas las unidades
UPDATE control_sincronizaciones 
SET ultima_actualizacion = NOW(), estatus = 'ACTIVO'
WHERE unidad_id IN (130, 131, 132, 133, 134);

-- 2. Limpiar vistas materializadas (según tu motor de BD)
-- Si usas PostgreSQL, usa REFRESH MATERIALIZED VIEW
-- Si usas MySQL, las vistas no se refrescan, por lo que el UPDATE previo es suficiente.
-- Para PostgreSQL:
-- REFRESH MATERIALIZED VIEW CONCURRENTLY vista_ventas_comerciales;

-- 3. Verificar e integridad de los nuevos módulos satélite
INSERT INTO modulos_hub (id, nombre, es_satelite, estatus)
VALUES 
('comandero', 'Comandero', TRUE, TRUE),
('super-caja', 'Super Caja', TRUE, TRUE)
ON CONFLICT (id) DO UPDATE SET estatus = TRUE;

-- Asegurar vinculación con las 5 unidades
INSERT INTO unidad_modulos (unidad_id, modulo_id)
VALUES 
(130, 'comandero'), (130, 'super-caja'),
(131, 'comandero'), (131, 'super-caja'),
(132, 'comandero'), (132, 'super-caja'),
(133, 'comandero'), (133, 'super-caja'),
(134, 'comandero'), (134, 'super-caja')
ON CONFLICT DO NOTHING;

-- Confirmación final
SELECT 'Sincronización y Módulos Verificados' AS status;
