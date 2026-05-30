-- =============================================================================
-- SCRIPT: DESBLOQUEO MASIVO - USUARIOS Y ROLES
-- OBJETIVO: Liberar todas las entidades bloqueadas por ediciones incompletas
-- =============================================================================

-- Para Usuarios: Ejecutar el script que ya creaste
-- /app/docs/sql/REPARACION_USUARIOS_BLOQUEADOS.sql
UPDATE usuarios SET estado = 'Activo', editando = FALSE WHERE editando = TRUE;

-- Para Roles: Ejecutar el script que ya creaste
-- /app/docs/sql/DESBLOQUEO_ROLES_SISTEMA.sql
UPDATE roles_sistema SET editando = FALSE WHERE editando = TRUE;
DELETE FROM bloqueos_sistema WHERE modulo IN ('usuarios', 'roles');

-- Verificación final
SELECT 'Usuarios desbloqueados' AS entidad, COUNT(*) AS total 
FROM usuarios WHERE editando = FALSE
UNION ALL
SELECT 'Roles desbloqueados' AS entidad, COUNT(*) AS total 
FROM roles_sistema WHERE editando = FALSE;
