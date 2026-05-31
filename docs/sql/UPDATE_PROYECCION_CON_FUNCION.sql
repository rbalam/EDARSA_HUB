-- ======================================================================================
-- SCRIPT: UPDATE_PROYECCION_CON_FUNCION.sql
-- Actualiza proyección usando función escalar fn_CalcularProyeccionMensual
-- ======================================================================================

-- Actualiza la proyección dinámicamente según el mes y año registrado en cada fila de EDARSA HUB
UPDATE [dbo].[Sync_KPI_Ventas_Unidades]
SET 
    Proyeccion_Ventas = dbo.fn_CalcularProyeccionMensual(Ventas_Reales_M, 30.00, Mes, Anio),
    UltimaActualizacion = GETDATE()
WHERE 
    Anio = 2026;
