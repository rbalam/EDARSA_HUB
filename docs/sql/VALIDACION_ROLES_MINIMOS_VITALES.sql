-- =============================================================================
-- SCRIPT: VALIDACION Y POBLADO DE ROLES MINIMOS VITALES
-- OBJETIVO: Asegurar que la UI no falle por falta de roles en la BD
-- =============================================================================

-- 1. Validar que la tabla tiene registros
SELECT COUNT(*) FROM roles_sistema;

-- 2. Si el conteo es 0, inyectamos los roles mínimos vitales para que la UI deje de fallar
INSERT INTO roles_sistema (id, nombre_rol, activo) 
VALUES 
(1, 'Administrador', TRUE),
(2, 'Usuario', TRUE)
ON CONFLICT (id) DO NOTHING;

-- 3. Verificar permisos (si esto falla, es el origen del Error 500)
SELECT * FROM permisos_roles WHERE rol_id IN (1, 2);
