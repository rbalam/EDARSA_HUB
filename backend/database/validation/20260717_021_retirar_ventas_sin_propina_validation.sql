/* Validación SELECT/THROW para 20260717_021. */

SET NOCOUNT ON;

IF DB_NAME() <> N'EDARSAHUB'
BEGIN
    THROW 51400, 'Base no autorizada. Se esperaba EDARSAHUB.', 1;
END;

IF COL_LENGTH(
    N'dbo.Comercial_KPIs_Diarios_v2',
    N'ventas_sin_propina'
) IS NOT NULL
BEGIN
    THROW 51401, 'La columna diaria legacy todavía existe.', 1;
END;

IF COL_LENGTH(
    N'dbo.Comercial_KPIs_Mensuales_v2',
    N'ventas_sin_propina'
) IS NOT NULL
BEGIN
    THROW 51402, 'La columna mensual legacy todavía existe.', 1;
END;

IF EXISTS (
    SELECT 1
    FROM sys.views view_object
    WHERE LOWER(OBJECT_DEFINITION(view_object.object_id))
          LIKE N'%ventas_sin_propina%'
)
BEGIN
    THROW 51403, 'Una vista conserva la referencia legacy.', 1;
END;

IF EXISTS (
    SELECT 1
    FROM dbo.Comercial_Metricas_Canonicas
    WHERE codigo = N'ventas_sin_propina'
      AND ISNULL(activo, 0) = 1
)
BEGIN
    THROW 51404, 'La métrica legacy continúa activa.', 1;
END;

IF NOT EXISTS (
    SELECT 1
    FROM dbo.Comercial_Metricas_Canonicas
    WHERE codigo = N'cheque_promedio'
      AND activo = 1
      AND numerador = N'ventas'
      AND denominador = N'cheques'
)
BEGIN
    THROW 51405, 'cheque_promedio no cumple ventas/tickets.', 1;
END;

IF NOT EXISTS (
    SELECT 1
    FROM dbo.Comercial_Metricas_Canonicas
    WHERE codigo = N'ticket_promedio'
      AND activo = 1
      AND numerador = N'ventas'
      AND denominador = N'cheques'
)
BEGIN
    THROW 51406, 'ticket_promedio no es alias de cheque_promedio.', 1;
END;

IF NOT EXISTS (
    SELECT 1
    FROM dbo.Comercial_Metricas_Canonicas
    WHERE codigo = N'pax_promedio'
      AND activo = 1
      AND numerador = N'ventas'
      AND denominador = N'pax'
)
BEGIN
    THROW 51407, 'pax_promedio no cumple ventas/pax.', 1;
END;

SELECT
    codigo,
    numerador,
    denominador,
    activo
FROM dbo.Comercial_Metricas_Canonicas
WHERE codigo IN (
    N'ventas',
    N'ventas_sin_propina',
    N'cheque_promedio',
    N'ticket_promedio',
    N'pax_promedio'
)
ORDER BY codigo;

SELECT
    schema_name(view_object.schema_id) AS schema_name,
    view_object.name AS view_name
FROM sys.views view_object
WHERE OBJECT_DEFINITION(view_object.object_id) LIKE N'%Comercial_KPIs%'
ORDER BY schema_name, view_name;
