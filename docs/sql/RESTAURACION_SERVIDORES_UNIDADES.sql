-- =============================================================================
-- SCRIPT: RESTAURACIÓN SERVIDORES / UNIDADES DE NEGOCIO
-- OBJETIVO: Asegurar que las 5 unidades base existan y estén activas
-- =============================================================================

-- 1. Aseguramos que los 5 servidores base existan en la tabla maestra
INSERT INTO servidores (id, nombre, estatus)
SELECT 130, '130° MÉRIDA', TRUE
WHERE NOT EXISTS (SELECT 1 FROM servidores WHERE id = 130);

INSERT INTO servidores (id, nombre, estatus)
SELECT 131, '130° QUERÉTARO', TRUE
WHERE NOT EXISTS (SELECT 1 FROM servidores WHERE id = 131);

INSERT INTO servidores (id, nombre, estatus)
SELECT 132, 'CIENFUEGOS', TRUE
WHERE NOT EXISTS (SELECT 1 FROM servidores WHERE id = 132);

INSERT INTO servidores (id, nombre, estatus)
SELECT 133, 'ORIGEN', TRUE
WHERE NOT EXISTS (SELECT 1 FROM servidores WHERE id = 133);

INSERT INTO servidores (id, nombre, estatus)
SELECT 134, 'LA ESTELAR', TRUE
WHERE NOT EXISTS (SELECT 1 FROM servidores WHERE id = 134);

-- 2. Aseguramos que el usuario administrador (tú) o el sistema tenga acceso a verlos
UPDATE servidores SET estatus = TRUE WHERE id IN (130, 131, 132, 133, 134);

-- 3. Verificación final
SELECT id, nombre, estatus FROM servidores WHERE id IN (130, 131, 132, 133, 134);
