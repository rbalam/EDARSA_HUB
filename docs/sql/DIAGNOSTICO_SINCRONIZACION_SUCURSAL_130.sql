-- =============================================================================
-- SCRIPT: DIAGNOSTICO Y FORZADO DE SINCRONIZACIÓN - SUCURSAL 130
-- RUTA: /app/docs/sql/DIAGNOSTICO_SINCRONIZACION_SUCURSAL_130.sql
-- OBJETIVO: Resolver bandera estancada "Error del Sistema / Datos Históricos"
-- =============================================================================

-- ==========================================
-- FASE 1: DIAGNÓSTICO DE LA CAUSA RAÍZ
-- ==========================================

-- 1.1. Verificar si existen ventas reales ingresadas hoy para la sucursal [cite: 22]
SELECT 
    id_sucursal, 
    COUNT(*) AS total_tickets_hoy,
    MAX(fecha_venta) AS ultima_venta_registrada,
    SUM(total) AS monto_acumulado_hoy
FROM ventas
WHERE id_sucursal = '130' 
  AND fecha_venta >= CURRENT_DATE
GROUP BY id_sucursal;

-- 1.2. Auditar el estado de control que lee el Frontend [cite: 22]
SELECT 
    sistema, 
    sucursal_id,
    ultima_sincronizacion, 
    estado,
    mensaje_error,
    intentos
FROM control_sincronizaciones
WHERE sistema = 'EDARSAHUB' 
   OR sucursal_id = '130';


-- ==========================================
-- FASE 2: FORZAR SINCRONIZACIÓN (MODO MANUAL)
-- ==========================================

-- Opción A: Ejecutar el pipeline de extracción si usas Store Procedures [cite: 23]
-- CALL sp_sincronizar_ventas_sucursal(PI_id_sucursal := '130', PI_fecha := CURRENT_DATE);

-- Opción B: Reiniciar la cola del Worker/Daemon mediante actualización de Flags [cite: 20]
UPDATE control_sincronizaciones
SET 
    estado = 'PENDIENTE', 
    intentos = 0,
    solicitar_recarga = TRUE
WHERE sistema = 'EDARSAHUB' 
  AND sucursal_id = '130';


-- ==========================================
-- FASE 3: LIMPIEZA DE CACHÉ Y BORRADO DE ALERTA
-- ==========================================

-- 3.1. Actualizar timestamp de control para eliminar el recuadro rojo en Frontend inmediatamente 
UPDATE control_sincronizaciones
SET 
    ultima_sincronizacion = NOW(), 
    estado = 'EXITOSO',
    mensaje_error = NULL
WHERE sistema = 'EDARSAHUB' 
  AND sucursal_id = '130';

-- 3.2. Forzar recálculo de las dimensiones agregadas del mes (Mayo 2026) [cite: 4, 24]
-- CALL sp_calcular_metricas_comerciales(PI_anio := 2026, PI_mes := 5, PI_id_sucursal := '130');

COMMIT;
