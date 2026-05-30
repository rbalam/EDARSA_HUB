-- =============================================================================
-- SCRIPT: ALTA MÓDULO SUPER CAJA EN 5 UNIDADES DE NEGOCIO
-- OBJETIVO: Habilitar Super Caja para todas las sucursales operativas
-- =============================================================================

-- Asegurar que el módulo está dado de alta primero
INSERT INTO modulos_hub (id, nombre, descripcion, es_satelite, activo)
VALUES ('super-caja', 'Super Caja', 'Módulo de gestión de caja operativa', TRUE, TRUE)
ON CONFLICT (id) DO UPDATE SET activo = TRUE;

-- Vincular el módulo a las 5 unidades de negocio
INSERT INTO configuracion_sucursales_modulos (sucursal_id, modulo_id, activo)
VALUES 
(130, 'super-caja', TRUE), -- Mérida
(131, 'super-caja', TRUE), -- Querétaro (Ajusta el ID 131 si es diferente)
(132, 'super-caja', TRUE), -- Cienfuegos (Ajusta el ID 132 si es diferente)
(133, 'super-caja', TRUE), -- Origen (Ajusta el ID 133 si es diferente)
(134, 'super-caja', TRUE)  -- La Estelar (Ajusta el ID 134 si es diferente)
ON CONFLICT (sucursal_id, modulo_id) 
DO UPDATE SET activo = TRUE;

-- Otorgar permisos de lectura al rol Administrador para todas las unidades
INSERT INTO permisos_roles (rol_id, modulo_id, permiso)
SELECT r.id, 'super-caja', 'read'
FROM roles_sistema r
WHERE r.nombre_rol = 'Administrador'
ON CONFLICT (rol_id, modulo_id, permiso) DO NOTHING;
