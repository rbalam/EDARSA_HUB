USE [EDARSAHUB];
GO

-- Actualización dinámica de todos los KPIs del año 2026
UPDATE [dbo].[Sync_KPI_Ventas_Unidades]
SET 
    -- Suponiendo que el periodo evaluado tiene 30 días con ventas registrados (ej. Mayo 2026)
    Proyeccion_Ventas = dbo.fn_CalcularProyeccionMensual(Ventas_Reales_M, 30.00, Mes, Anio),
    UltimaActualizacion = GETDATE()
WHERE 
    Anio = 2026;
GO
