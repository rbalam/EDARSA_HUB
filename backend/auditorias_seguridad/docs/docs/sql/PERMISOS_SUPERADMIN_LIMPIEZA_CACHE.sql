-- =============================================================================
-- SCRIPT: PERMISOS SUPERADMINISTRADOR Y LIMPIEZA CACHÉ SYNC
-- OBJETIVO: Asegurar acceso a módulos críticos y limpiar registros de error
-- =============================================================================

-- 1. Asegurar que los permisos existen para el rol SuperAdministrador
INSERT INTO permisos_roles (rol_id, modulo, permiso)
SELECT r.id, 'proveedores', 'read'
FROM roles_sistema r
WHERE r.nombre_rol = 'SuperAdministrador'
ON CONFLICT DO NOTHING;

INSERT INTO permisos_roles (rol_id, modulo, permiso)
SELECT r.id, 'roles', 'read'
FROM roles_sistema r
WHERE r.nombre_rol = 'SuperAdministrador'
ON CONFLICT DO NOTHING;

-- 2. Limpiar caché de la tabla de control de sincronización
DELETE FROM control_sincronizaciones WHERE estado = 'error';
