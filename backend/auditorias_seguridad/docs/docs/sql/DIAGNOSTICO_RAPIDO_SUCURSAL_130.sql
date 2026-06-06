-- =============================================================================
-- SCRIPT: DIAGNOSTICO RAPIDO SUCURSAL 130 (MÉRIDA)
-- RUTA: /app/docs/sql/DIAGNOSTICO_RAPIDO_SUCURSAL_130.sql
-- =============================================================================

-- 1.1. Verificar si la sucursal 130 (Mérida) ha registrado transacciones hoy
SELECT 
    id_sucursal, 
    COUNT(*) AS total_tickets_hoy,
    MAX(fecha_venta) AS ultima_venta_registrada,
    SUM(total) AS monto_acumulado_hoy
FROM ventas
WHERE id_sucursal = '130' 
  AND fecha_venta >= CURRENT_DATE
GROUP BY id_sucursal;

-- 1.2. Revisar el estado de sincronización que genera la alerta en el frontend
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
