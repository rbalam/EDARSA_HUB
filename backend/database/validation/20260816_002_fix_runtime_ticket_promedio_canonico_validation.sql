SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> N'EDARSAHUB'
    THROW 51620, 'Base de datos inesperada', 1;

IF OBJECT_ID(
    N'dbo.vw_Comercial_KPIs_Diarios_v2_Runtime',
    N'V'
) IS NULL
    THROW 51621, 'Runtime view inexistente', 1;

IF EXISTS (
    SELECT 1
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE fuente_original = N'Comercial_Ventas_Dia_Abiertas_v2'
      AND ISNULL(tickets_total, 0) > 0
      AND ABS(
            CONVERT(decimal(38,6), ticket_promedio)
            -
            CONVERT(decimal(38,6), total_estimado_dia)
            / NULLIF(CONVERT(decimal(38,6), tickets_total), 0)
          ) > 0.01
)
    THROW 51622, 'ticket_promedio no cumple ventas/tickets', 1;

IF EXISTS (
    SELECT 1
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE fuente_original = N'Comercial_Ventas_Dia_Abiertas_v2'
      AND ISNULL(pax_total, 0) > 0
      AND ABS(
            CONVERT(decimal(38,6), pax_promedio)
            -
            CONVERT(decimal(38,6), total_estimado_dia)
            / NULLIF(CONVERT(decimal(38,6), pax_total), 0)
          ) > 0.01
)
    THROW 51623, 'pax_promedio no cumple ventas/pax', 1;

PRINT 'RUNTIME_KPI_CANONICAL_VALIDATION=PASS';
