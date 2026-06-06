-- =============================================================================
-- SCRIPT: REPARACIÓN DEFINITIVA Y PREVENCIÓN DE BUCLES INFINITOS
-- OBJETIVO: Automatizar la liberación de bloqueos en control_sincronizaciones
-- =============================================================================

-- Paso 1: Crear una función inteligente que verifique y destrabe el sistema
CREATE OR REPLACE FUNCTION fn_autoreparar_sincronizacion_colgada()
RETURNS TRIGGER AS $$
BEGIN
    -- Si el estado se queda en 'PENDIENTE' o 'PROCESANDO' por más de 5 minutos
    IF (NEW.estado IN ('PENDIENTE', 'PROCESANDO') AND NEW.ultima_sincronizacion < NOW() - INTERVAL '5 minutes') THEN
        
        -- 1. Forzar la liberación del registro para desbloquear el Frontend
        NEW.estado := 'FALLIDO';
        NEW.mensaje_error := 'TIMEOUT_AUTOMATICO: Conexión con el POS excedió el tiempo límite.';
        NEW.intentos := 0;
        
        -- 2. Asegurar que las tablas de progreso del Tablero Ejecutivo no queden congeladas
        UPDATE resumen_unidades_progreso
        SET 
            procesando = FALSE,
            ultima_actualizacion = NOW()
        WHERE id_sucursal = NEW.sucursal_id;
        
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Paso 2: Crear el disparador (Trigger) que vigila la tabla constantemente
DROP TRIGGER IF EXISTS trg_vigilar_bucle_sincronizacion ON control_sincronizaciones;

CREATE TRIGGER trg_vigilar_bucle_sincronizacion
BEFORE UPDATE ON control_sincronizaciones
FOR EACH ROW
EXECUTE FUNCTION fn_autoreparar_sincronizacion_colgada();

COMMIT;
