-- =============================================================================
-- SCRIPT: REPARACIÓN DE USUARIOS EN ESTADO ERROR O BLOQUEADOS
-- OBJETIVO: Desbloquear usuarios y verificar restricciones
-- =============================================================================

-- Ejecuta este query en tu gestor de base de datos
UPDATE usuarios 
SET estado = 'Activo', editando = FALSE 
WHERE estado = 'Error' OR editando = TRUE;

-- Verifica que el usuario no tenga restricciones
SELECT * FROM usuarios WHERE nombre = 'William Chuc';

-- Verificar todos los usuarios en estado anómalo
SELECT id, nombre, email, estado, editando 
FROM usuarios 
WHERE estado != 'Activo' OR editando = TRUE;
