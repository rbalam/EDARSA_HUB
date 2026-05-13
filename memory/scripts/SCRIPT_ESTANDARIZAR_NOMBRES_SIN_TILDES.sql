-- =============================================================================
-- SCRIPT: ESTANDARIZACIÓN DE NOMBRES SIN TILDES EN EDARSAHUB
-- =============================================================================
-- FECHA: 2026-05-13
-- AUTOR: Sistema de Migración
-- ESTADO: PROPUESTO - NO EJECUTAR SIN AUTORIZACIÓN EXPLÍCITA
-- =============================================================================
-- OBJETIVO:
-- Eliminar tildes y símbolos especiales (°) de los nombres funcionales de 
-- unidades de negocio en EDARSAHUB para evitar problemas de mapeo entre módulos.
-- =============================================================================
-- REGLAS:
-- 1. El código canónico (Unidades_Negocio.codigo) NO se modifica
-- 2. Solo se modifican campos de nombre/texto visible
-- 3. Script idempotente (puede ejecutarse múltiples veces sin efecto)
-- =============================================================================

-- VALORES A TRANSFORMAR:
-- "130° MÉRIDA"    -> "130 MERIDA"
-- "130° MERIDA"    -> "130 MERIDA"
-- "130° QUERÉTARO" -> "130 QUERETARO"
-- "130° QUERETARO" -> "130 QUERETARO"
-- "130° QRO LOCAL" -> "130 QRO LOCAL"

-- =============================================================================
-- PASO 0: VERIFICACIÓN PREVIA (EJECUTAR PRIMERO)
-- =============================================================================

-- Verificar estado actual ANTES de cambios
SELECT 'ANTES' as estado, 'Unidades_Negocio' as tabla, nombre, codigo, COUNT(*) as registros
FROM Unidades_Negocio
WHERE nombre LIKE '%°%' OR nombre LIKE '%É%' OR nombre LIKE '%Á%'
GROUP BY nombre, codigo

UNION ALL

SELECT 'ANTES', 'Comercial_KPIs_Diarios_v2', unidad_negocio_nombre, unidad_negocio_id, COUNT(*)
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_nombre LIKE '%°%' OR unidad_negocio_nombre LIKE '%É%'
GROUP BY unidad_negocio_nombre, unidad_negocio_id

UNION ALL

SELECT 'ANTES', 'Comercial_Ventas_Dia_Abiertas_v2', unidad_negocio_nombre, server_id, COUNT(*)
FROM Comercial_Ventas_Dia_Abiertas_v2
WHERE unidad_negocio_nombre LIKE '%°%' OR unidad_negocio_nombre LIKE '%É%'
GROUP BY unidad_negocio_nombre, server_id

UNION ALL

SELECT 'ANTES', 'Servidores_Conexiones', nombre, CAST(id as NVARCHAR(50)), COUNT(*)
FROM Servidores_Conexiones
WHERE nombre LIKE '%°%' OR nombre LIKE '%É%'
GROUP BY nombre, id

ORDER BY tabla, nombre;

-- =============================================================================
-- PASO 1: TRANSACCIÓN CONTROLADA
-- =============================================================================

BEGIN TRANSACTION;

-- =============================================================================
-- 1.1 ACTUALIZAR Unidades_Negocio.nombre
-- =============================================================================
-- Registros afectados: 2

UPDATE Unidades_Negocio
SET nombre = REPLACE(REPLACE(REPLACE(nombre, '°', ''), 'É', 'E'), 'Á', 'A')
WHERE nombre LIKE '%°%' OR nombre LIKE '%É%' OR nombre LIKE '%Á%';

-- Verificar cambio
SELECT 'Unidades_Negocio' as tabla, codigo, nombre FROM Unidades_Negocio WHERE codigo IN ('130MID', '130QRO');

-- =============================================================================
-- 1.2 ACTUALIZAR Comercial_KPIs_Diarios_v2.unidad_negocio_nombre
-- =============================================================================
-- Registros afectados: ~1473

UPDATE Comercial_KPIs_Diarios_v2
SET unidad_negocio_nombre = REPLACE(REPLACE(REPLACE(unidad_negocio_nombre, '°', ''), 'É', 'E'), 'Á', 'A')
WHERE unidad_negocio_nombre LIKE '%°%' OR unidad_negocio_nombre LIKE '%É%';

-- Verificar cambio
SELECT 'Comercial_KPIs_Diarios_v2' as tabla, unidad_negocio_id, unidad_negocio_nombre, COUNT(*) as registros
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id IN ('130-MER', '130-QRO')
GROUP BY unidad_negocio_id, unidad_negocio_nombre;

-- =============================================================================
-- 1.3 ACTUALIZAR Comercial_Ventas_Dia_Abiertas_v2.unidad_negocio_nombre
-- =============================================================================
-- Registros afectados: 2

UPDATE Comercial_Ventas_Dia_Abiertas_v2
SET unidad_negocio_nombre = REPLACE(REPLACE(REPLACE(unidad_negocio_nombre, '°', ''), 'É', 'E'), 'Á', 'A')
WHERE unidad_negocio_nombre LIKE '%°%' OR unidad_negocio_nombre LIKE '%É%';

-- Verificar cambio
SELECT 'Comercial_Ventas_Dia_Abiertas_v2' as tabla, unidad_negocio_nombre, COUNT(*) as registros
FROM Comercial_Ventas_Dia_Abiertas_v2
GROUP BY unidad_negocio_nombre;

-- =============================================================================
-- 1.4 ACTUALIZAR Servidores_Conexiones.nombre
-- =============================================================================
-- Registros afectados: 2

UPDATE Servidores_Conexiones
SET nombre = REPLACE(REPLACE(REPLACE(nombre, '°', ''), 'É', 'E'), 'Á', 'A')
WHERE nombre LIKE '%°%' OR nombre LIKE '%É%';

-- Verificar cambio
SELECT 'Servidores_Conexiones' as tabla, CAST(id as NVARCHAR(50)) as id, nombre
FROM Servidores_Conexiones
WHERE nombre LIKE '%130%' OR nombre LIKE '%MER%' OR nombre LIKE '%QRO%';

-- =============================================================================
-- PASO 2: VERIFICACIÓN FINAL
-- =============================================================================

-- Contar registros con tildes restantes (debe ser 0)
SELECT 
    'VERIFICACIÓN FINAL' as status,
    (SELECT COUNT(*) FROM Unidades_Negocio WHERE nombre LIKE '%°%' OR nombre LIKE '%É%') as tildes_unidades,
    (SELECT COUNT(*) FROM Comercial_KPIs_Diarios_v2 WHERE unidad_negocio_nombre LIKE '%°%' OR unidad_negocio_nombre LIKE '%É%') as tildes_kpis_diarios,
    (SELECT COUNT(*) FROM Comercial_Ventas_Dia_Abiertas_v2 WHERE unidad_negocio_nombre LIKE '%°%' OR unidad_negocio_nombre LIKE '%É%') as tildes_ventas_abiertas,
    (SELECT COUNT(*) FROM Servidores_Conexiones WHERE nombre LIKE '%°%' OR nombre LIKE '%É%') as tildes_servidores;

-- =============================================================================
-- PASO 3: DECISIÓN - COMMIT O ROLLBACK
-- =============================================================================

-- Si todo está correcto:
-- COMMIT;

-- Si hay algún problema:
-- ROLLBACK;

-- =============================================================================
-- NOTA IMPORTANTE:
-- =============================================================================
-- Este script NO modifica:
-- - Unidades_Negocio.codigo (llave canónica)
-- - unidad_negocio_id en tablas de KPIs
-- - server_id
-- - empresa_id
-- - sucursal_id
--
-- Solo modifica campos de nombre/texto visible.
-- =============================================================================
