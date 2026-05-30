-- =============================================================================
-- SCRIPT: VALIDACIÓN ESTRUCTURA Y DATOS TABLA USUARIOS
-- OBJETIVO: Diagnosticar problemas de conexión o estructura de la tabla
-- =============================================================================

-- 1. Validar la estructura física y columnas de la tabla de usuarios
SELECT 
    column_name AS columna, 
    data_type AS tipo_dato, 
    is_nullable AS permite_nulos
FROM 
    information_schema.columns 
WHERE 
    table_name IN ('usuarios', 'usuarios_sistema') -- Ajusta si tu tabla tiene otro nombre
ORDER BY 
    ordinal_position;

-- 2. Validar que la tabla contenga datos y la conexión sea directa
SELECT 
    id, 
    nombre, 
    email, 
    estatus 
FROM 
    usuarios -- Ajusta si se llama 'usuarios_sistema'
LIMIT 5;

-- 3. Contar registros totales
SELECT COUNT(*) AS total_usuarios FROM usuarios;

-- 4. Verificar usuarios activos vs inactivos
SELECT estatus, COUNT(*) AS cantidad 
FROM usuarios 
GROUP BY estatus;
