-- =============================================================================
-- SCRIPT: ALTA INMEDIATA DEL MÓDULO SATÉLITE - SUPER CAJA
-- OBJETIVO: Forzar la aparición del menú en la barra lateral para Mérida
-- =============================================================================

-- Paso 1: Registrar el módulo en la tabla maestra de componentes
INSERT INTO modulos_hub (id_modulo, nombre_modulo, es_satelite, url_slug, icono, activo)
VALUES ('SUPER_CAJA_SAT', 'Super Caja', TRUE, '/super-caja', 'cash-register', TRUE)
ON CONFLICT (id_modulo) DO UPDATE SET activo = TRUE;

-- Paso 2: Habilitar el menú en la sucursal 130° MÉRIDA
INSERT INTO configuracion_sucursales_modulos (id_sucursal, id_modulo, habilitado)
VALUES ('130', 'SUPER_CAJA_SAT', TRUE)
ON CONFLICT (id_sucursal, id_modulo) DO UPDATE SET habilitado = TRUE;

-- Paso 3: Asignar permisos a tu perfil de SuperAdministrador
INSERT INTO permisos_roles (id_rol, id_modulo, puede_leer, puede_escribir)
VALUES ('SuperAdministrador', 'SUPER_CAJA_SAT', TRUE, TRUE)
ON CONFLICT (id_rol, id_modulo) DO UPDATE SET puede_leer = TRUE, puede_escribir = TRUE;

COMMIT;
