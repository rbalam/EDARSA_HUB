-- =============================================================================
-- SCRIPT: LIMPIEZA COMPLETA DE BLOQUEOS (USUARIOS + ROLES)
-- OBJETIVO: Liberar todas las entidades bloqueadas por ediciones fallidas
-- =============================================================================

-- Liberar bloqueos de edición de usuarios
UPDATE usuarios SET editando = FALSE WHERE editando = TRUE;

-- Liberar bloqueos de edición de roles
UPDATE roles_sistema SET editando = FALSE WHERE editando = TRUE;

-- Limpiar cualquier flag de error persistente
DELETE FROM bloqueos_sistema WHERE modulo IN ('usuarios', 'roles');

-- Verificación de estado post-limpieza
SELECT 'usuarios' AS tabla, COUNT(*) AS bloqueados FROM usuarios WHERE editando = TRUE
UNION ALL
SELECT 'roles' AS tabla, COUNT(*) AS bloqueados FROM roles_sistema WHERE editando = TRUE;
