-- =============================================================================
-- SCRIPT: DESBLOQUEO DE ROLES Y LIMPIEZA DE TRANSACCIONES PENDIENTES
-- OBJETIVO: Liberar roles bloqueados por ediciones incompletas
-- =============================================================================

-- Ejecuta este query para desbloquear la edición de roles
UPDATE roles_sistema 
SET editando = FALSE 
WHERE editando = TRUE;

-- Verifica que no existan bloqueos de transacciones pendientes
DELETE FROM bloqueos_sistema WHERE modulo = 'roles';

-- Verificar estado actual de roles
SELECT id, nombre_rol, editando, activo 
FROM roles_sistema 
ORDER BY id;
