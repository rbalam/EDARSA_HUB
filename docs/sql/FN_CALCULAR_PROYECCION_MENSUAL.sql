USE [EDARSAHUB];
GO

-- Crear la Función Escalar en el esquema auxiliar si no existe
IF OBJECT_ID('dbo.fn_CalcularProyeccionMensual', 'FN') IS NOT NULL
BEGIN
    DROP FUNCTION dbo.fn_CalcularProyeccionMensual;
END
GO

CREATE FUNCTION dbo.fn_CalcularProyeccionMensual (
    @VentasReales DECIMAL(18, 4),
    @DiasConVentas DECIMAL(5, 2),
    @MesNombre NVARCHAR(20),
    @Anio INT
)
RETURNS DECIMAL(18, 4)
AS
BEGIN
    -- Declaramos variables internas
    DECLARE @NumeroMes INT;
    DECLARE @DiasTotales DECIMAL(5, 2);
    DECLARE @Proyeccion DECIMAL(18, 4) = 0.0000;

    -- Traducir el nombre del mes castellano a número (1-12)
    SET @NumeroMes = 
        CASE LOWER(LTRIM(RTRIM(@MesNombre)))
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
            ELSE NULL
        END;

    -- Un mes inválido no se convierte silenciosamente en otro periodo.
    IF @NumeroMes IS NULL
        RETURN NULL;

    -- Un año inválido no se sustituye silenciosamente por otro periodo.
    IF @Anio IS NULL OR @Anio < 1900 OR @Anio > 2100
        RETURN NULL;

    -- Obtener la cantidad de días del mes de forma dinámica (soporta bisiestos)
    SET @DiasTotales = CAST(DAY(EOMONTH(DATEFROMPARTS(@Anio, @NumeroMes, 1))) AS DECIMAL(5, 2));

    -- Proyección = (Ventas / Días Activos) * Días Totales Calendario
    -- NULLIF previene división por cero si aún no hay días registrados
    SET @Proyeccion = (@VentasReales / NULLIF(@DiasConVentas, 0.0)) * @DiasTotales;

    RETURN ISNULL(@Proyeccion, 0.0000);
END;
GO
