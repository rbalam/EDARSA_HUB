-- ======================================================================================
-- SCRIPT: FORMULA_PROYECCION_DINAMICA.sql
-- Cálculo dinámico de proyección comercial con variables ajustables
-- ======================================================================================

-- 1. Declaración de Variables Ajustables
DECLARE @MesSeleccionado NVARCHAR(20) = N'Mayo';
DECLARE @AnioSeleccionado INT = 2026;
DECLARE @DiasConVentas DECIMAL(18, 4) = 30.0000;

-- 2. Traducción de nombre del mes a número índice (1-12)
DECLARE @NumeroMes INT = 
    CASE LOWER(@MesSeleccionado)
        WHEN 'enero'      THEN 1
        WHEN 'febrero'    THEN 2
        WHEN 'marzo'      THEN 3
        WHEN 'abril'      THEN 4
        WHEN 'mayo'       THEN 5
        WHEN 'junio'      THEN 6
        WHEN 'julio'      THEN 7
        WHEN 'agosto'     THEN 8
        WHEN 'septiembre' THEN 9
        WHEN 'octubre'    THEN 10
        WHEN 'noviembre'  THEN 11
        WHEN 'diciembre'  THEN 12
        ELSE MONTH(GETDATE())
    END;

-- 3. Cálculo Dinámico de Días Calendario Reales (Ej. Mayo=31, Abril=30, Febrero bisiesto=29/28)
DECLARE @DiasTotales DECIMAL(18, 4) = CAST(DAY(EOMONTH(DATEFROMPARTS(@AnioSeleccionado, @NumeroMes, 1))) AS DECIMAL(18, 4));

-- 4. Aplicación de la Fórmula de Prospección Comercial Lineal
UPDATE [dbo].[Sync_KPI_Ventas_Unidades]
SET 
    Proyeccion_Ventas = CAST((Ventas_Reales_M / NULLIF(@DiasConVentas, 0)) * @DiasTotales AS DECIMAL(18, 4)),
    UltimaActualizacion = GETDATE()
WHERE 
    Mes = @MesSeleccionado AND Anio = @AnioSeleccionado;
