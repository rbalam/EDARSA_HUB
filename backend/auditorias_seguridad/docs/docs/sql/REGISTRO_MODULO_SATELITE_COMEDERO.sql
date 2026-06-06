-- =============================================================================
-- SCRIPT: REGISTRO DE MÓDULO SATÉLITE - COMEDERO
-- OBJETIVO: Dar de alta el acceso y navegación para el nuevo módulo
-- =============================================================================

-- 1. Insertar el nuevo módulo satélite en la tabla maestra de módulos
INSERT INTO modulos_hub (id_modulo, nombre_modulo, es_satelite, url_slug, icono, activo)
VALUES ('COMEDERO_01', 'Comedero', TRUE, '/comedero', 'utensils', TRUE)
ON CONFLICT (id_modulo) DO NOTHING; -- O tu equivalente según el motor de BD

-- 2. Asignar visibilidad del módulo satélite a la sucursal de Mérida (130)
INSERT INTO configuracion_sucursales_modulos (id_sucursal, id_modulo, habilitado)
VALUES ('130', 'COMEDERO_01', TRUE)
ON CONFLICT (id_sucursal, id_modulo) DO UPDATE SET habilitado = TRUE;

-- 3. Dar permisos al rol de SuperAdministrador (Ricardo Balam Garcia)
INSERT INTO permisos_roles (id_rol, id_modulo, puede_leer, puede_escribir)
VALUES ('SuperAdministrador', 'COMEDERO_01', TRUE, TRUE)
ON CONFLICT (id_rol, id_modulo) DO UPDATE SET puede_leer = TRUE, puede_escribir = TRUE;

COMMIT;
