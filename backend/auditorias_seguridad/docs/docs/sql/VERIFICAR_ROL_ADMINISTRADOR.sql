-- =============================================================================
-- SCRIPT: VERIFICAR ROL ADMINISTRADOR ACTIVO
-- =============================================================================

-- Verifica si el rol existe y está activo
SELECT id, nombre_rol, activo 
FROM roles_sistema 
WHERE nombre_rol = 'Administrador';
