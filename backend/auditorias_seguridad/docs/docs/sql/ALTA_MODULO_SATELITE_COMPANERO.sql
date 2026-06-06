-- =============================================================================
-- SCRIPT: ALTA INMEDIATA DEL MÓDULO SATÉLITE (COMPAÑERO / COMEDERO)
-- OBJETIVO: Forzar la aparición del menú en la barra lateral para la Sucursal 130
-- =============================================================================

-- Paso 1: Registrar el módulo satélite en el sistema
INSERT INTO modulos_hub (id_modulo, nombre_modulo, es_satelite, url_slug, icono, activo)
VALUES ('COMPANERO_SAT', 'Compañero', TRUE, '/companero', 'users', TRUE)
ON CONFLICT (id_modulo) DO UPDATE SET activo = TRUE;

-- Paso 2: Habilitar el nuevo menú específicamente en la sucursal 130° MÉRIDA
INSERT INTO configuracion_sucursales_modulos (id_sucursal, id_modulo, habilitado)
VALUES ('130', 'COMPANERO_SAT', TRUE)
ON CONFLICT (id_sucursal, id_modulo) DO UPDATE SET habilitado = TRUE;

-- Paso 3: Asegurar que tu usuario (Ricardo Balam Garcia) tenga permiso total de ver el menú
INSERT INTO permisos_roles (id_rol, id_modulo, puede_leer, puede_escribir)
VALUES ('SuperAdministrador', 'COMPANERO_SAT', TRUE, TRUE)
ON CONFLICT (id_rol, id_modulo) DO UPDATE SET puede_leer = TRUE, puede_escribir = TRUE;

COMMIT;
