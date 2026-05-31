-- =====================================================================
-- SCRIPT DE ACTUALIZACIÓN DE KPI: PROYECCIÓN COMERCIAL (EDARSA HUB)
-- Descripción: Actualiza físicamente el registro de la proyección en la tabla.
-- Fórmula Solicitada: (Ventas / Días con Ventas) * Días Totales del Mes
-- =====================================================================

-- 1. Definición de variables operativas del mes en curso
DECLARE @DiasConVentas DECIMAL(5,2) = 30.0;
DECLARE @DiasTotales DECIMAL(5,2) = 31.0;

-- 2. Transacción segura de actualización
BEGIN TRANSACTION;

BEGIN TRY
    UPDATE [dbo].[Sync_KPI_Ventas_Unidades]
    SET 
        -- Modificación de la columna de proyección con la fórmula corregida
        Proyeccion_Ventas_M = CAST((Ventas_Reales_M / @DiasConVentas) * @DiasTotales AS DECIMAL(18,2))
    WHERE 
        Mes = 'Mayo' 
        AND Anio = 2026;

    -- Si todo es correcto, confirma los cambios
    COMMIT TRANSACTION;
    PRINT 'El KPI de Proyección Comercial para Mayo 2026 ha sido actualizado exitosamente.';
END TRY
BEGIN CATCH
    -- Si ocurre un error, revierte para evitar corrupción de datos
    ROLLBACK TRANSACTION;
    PRINT 'Error detectado. Se ha cancelado la actualización.';
    THROW;
END CATCH;
