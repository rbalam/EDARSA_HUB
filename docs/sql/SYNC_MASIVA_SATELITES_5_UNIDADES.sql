-- =============================================================================
-- SCRIPT: SINCRONIZACIÓN MASIVA - MÓDULOS SATÉLITES EN 5 UNIDADES
-- OBJETIVO: Asegurar que 'comandero' y 'super-caja' estén activos y vinculados
-- =============================================================================

INSERT INTO unidad_modulos (unidad_id, modulo_id)
VALUES 
(130, 'comandero'), (130, 'super-caja'), -- Mérida
(131, 'comandero'), (131, 'super-caja'), -- Querétaro
(132, 'comandero'), (132, 'super-caja'), -- Cienfuegos
(133, 'comandero'), (133, 'super-caja'), -- Origen
(134, 'comandero'), (134, 'super-caja')  -- La Estelar
ON CONFLICT (unidad_id, modulo_id) DO UPDATE SET estatus = TRUE;

-- Verificación de integridad
SELECT unidad_id, modulo_id, estatus 
FROM unidad_modulos 
WHERE modulo_id IN ('comandero', 'super-caja') 
ORDER BY unidad_id;
