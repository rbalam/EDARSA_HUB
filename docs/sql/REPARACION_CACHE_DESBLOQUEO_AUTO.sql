-- =============================================================================
-- REPARACIÓN SQL: CONTROL DE CACHÉ Y DESBLOQUEO AUTOMÁTICO
-- =============================================================================

-- 1. Forzar la limpieza inmediata de los registros de control colgados
UPDATE control_sincronizaciones
SET 
    estado = 'FALLIDO',
    mensaje_error = 'ERROR_RED_LOCAL: Conexión interrumpida. Usando datos guardados.',
    ultima_sincronizacion = NOW(),
    intentos = 0
WHERE estado IN ('PENDIENTE', 'PROCESANDO')
  AND (sucursal_id = '130' OR sistema = 'EDARSAHUB'); -- Blindamos la sucursal de Mérida y el sistema principal

-- 2. Liberar el progreso del Tablero Ejecutivo para que no se quede con la ruedita girando
UPDATE resumen_unidades_progreso
SET 
    procesando = FALSE,
    ultima_actualizacion = NOW()
WHERE id_sucursal = '130';

COMMIT;
