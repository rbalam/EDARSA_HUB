-- =====================================================
-- DIAGNOSTICO_SINCRONIZACION_SUCURSAL_130.sql
-- Verificación de estado de sincronización Mérida
-- =====================================================

-- 1. Verificar la última transacción registrada para esa sucursal
SELECT 
    id_sucursal, 
    nombre_sucursal, 
    MAX(fecha_venta) AS ultima_venta_registrada,
    COUNT(*) AS total_tickets_hoy
FROM ventas
WHERE id_sucursal = '130' -- O el identificador correspondiente a Mérida
  AND fecha_venta >= CURRENT_DATE;

-- 2. Revisar el estado de la tabla que alimenta el componente de sincronización
SELECT 
    sistema, 
    ultima_sincronizacion, 
    estado,
    mensaje_error
FROM control_sincronizaciones
WHERE sistema = 'EDARSAHUB' 
   OR sucursal_id = '130';
