/*
Validación de 20260717_020_comercial_runtime_contract.sql.
Solo SELECT y THROW. No modifica información.
*/

SET NOCOUNT ON;

IF DB_NAME() <> N'EDARSAHUB'
BEGIN
    THROW 51100, 'Base no autorizada.', 1;
END;

DECLARE @view_definition nvarchar(max) =
    OBJECT_DEFINITION(
        OBJECT_ID(
            N'dbo.vw_Comercial_KPIs_Diarios_v2_Runtime'
        )
    );

IF @view_definition IS NULL
BEGIN
    THROW 51101, 'Vista runtime inexistente.', 1;
END;

IF LOWER(@view_definition) LIKE
   N'%comercial_ventas_dia_abiertas_v2%'
BEGIN
    THROW 51102,
        'La vista runtime todavía mezcla ventas abiertas.',
        1;
END;

IF NOT EXISTS (
    SELECT 1
    FROM dbo.Comercial_Metricas_Canonicas
    WHERE codigo = N'ventas'
      AND activo = 1
      AND operacion = N'campo'
      AND campo_base = N'ventas'
)
BEGIN
    THROW 51103, 'Definición de ventas inválida.', 1;
END;

IF EXISTS (
    SELECT 1
    FROM dbo.Comercial_Metricas_Canonicas
    WHERE codigo = N'ventas_sin_propina'
      AND ISNULL(activo, 0) = 1
)
BEGIN
    THROW 51109, 'ventas_sin_propina continúa activa.', 1;
END;

IF EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID(
        N'dbo.vw_Comercial_KPIs_Diarios_v2_Runtime'
    )
      AND name = N'ventas_sin_propina'
)
BEGIN
    THROW 51110, 'La vista runtime aún expone ventas_sin_propina.', 1;
END;

IF NOT EXISTS (
    SELECT 1
    FROM dbo.Comercial_Metricas_Canonicas
    WHERE codigo = N'cheque_promedio'
      AND activo = 1
      AND operacion = N'ratio'
      AND numerador = N'ventas'
      AND denominador = N'cheques'
)
BEGIN
    THROW 51104, 'Definición de cheque_promedio inválida.', 1;
END;

IF NOT EXISTS (
    SELECT 1
    FROM dbo.Comercial_Metricas_Canonicas
    WHERE codigo = N'pax_promedio'
      AND activo = 1
      AND operacion = N'ratio'
      AND numerador = N'ventas'
      AND denominador = N'pax'
)
BEGIN
    THROW 51105, 'Definición de pax_promedio inválida.', 1;
END;


-- 20260717_020 VALIDATE CANONICAL SYNONYMS
IF OBJECT_ID(
    N'dbo.Comercial_Metricas_Sinonimos',
    N'U'
) IS NULL
BEGIN
    THROW 51106,
        'No existe dbo.Comercial_Metricas_Sinonimos.',
        1;
END;

IF EXISTS (
    SELECT 1
    FROM (
        VALUES
            (N'venta_total', N'ventas'),
            (N'ventas_total', N'ventas'),
            (N'ventas_con_iva', N'ventas'),
            (N'ventas_visibles', N'ventas'),

            (N'propina', N'propinas'),
            (N'propinas_total', N'propinas'),

            (N'tickets', N'cheques'),
            (N'comandas', N'cheques'),
            (N'cuentas', N'cheques'),
            (N'tickets_total', N'cheques'),

            (N'comensales', N'pax'),
            (N'pax_total', N'pax'),

            (N'cheque_medio', N'cheque_promedio'),
            (N'ticket_medio', N'ticket_promedio'),

            (N'venta_por_pax', N'pax_promedio'),
            (N'consumo_per_capita', N'pax_promedio'),
            (N'consumo_promedio_pax', N'pax_promedio'),
            (N'venta_pax', N'pax_promedio'),

            (N'personas_por_cheque', N'pax_por_cheque'),
            (N'personas_por_cuenta', N'pax_por_cheque'),
            (N'pax_por_ticket', N'pax_por_cheque'),

            (N'rotacion_por_comensal', N'cheques_por_pax')
    ) expected (
        sinonimo,
        metrica_codigo
    )
    LEFT JOIN dbo.Comercial_Metricas_Sinonimos actual
      ON actual.sinonimo = expected.sinonimo
    WHERE actual.sinonimo IS NULL
       OR actual.metrica_codigo
          <> expected.metrica_codigo
       OR ISNULL(actual.activo, 0) <> 1
)
BEGIN
    THROW 51107,
        'Los sinónimos comerciales no cumplen el contrato canónico.',
        1;
END;

IF EXISTS (
    SELECT 1
    FROM dbo.Comercial_Metricas_Sinonimos
    WHERE sinonimo IN (
        N'venta_neta',
        N'ventas_netas',
        N'ventas_con_propina'
    )
      AND ISNULL(activo, 0) = 1
)
BEGIN
    THROW 51108,
        'Un alias legacy de venta continúa activo.',
        1;
END;

IF EXISTS (
    SELECT 1
    FROM dbo.Comercial_KPIs_Diarios_v2
    WHERE ISNULL(activo, 1) = 1
      AND ISNULL(es_demo, 0) = 0
      AND ISNULL(tickets_total, 0) > 0
      AND (
          ticket_promedio IS NULL
          OR ABS(
              CONVERT(decimal(38,6), ticket_promedio)
              -
              (
                  CONVERT(decimal(38,6), ISNULL(ventas_total, 0))
                  /
                  NULLIF(
                      CONVERT(decimal(38,6), tickets_total),
                      0
                  )
              )
          ) > 0.01
      )
)
BEGIN
    THROW 51111,
        'Históricos incompatibles con cheque_promedio canónico.',
        1;
END;

IF EXISTS (
    SELECT 1
    FROM dbo.Comercial_KPIs_Diarios_v2
    WHERE ISNULL(activo, 1) = 1
      AND ISNULL(es_demo, 0) = 0
      AND ISNULL(pax_total, 0) > 0
      AND (
          pax_promedio IS NULL
          OR ABS(
              CONVERT(decimal(38,6), pax_promedio)
              -
              (
                  CONVERT(decimal(38,6), ISNULL(ventas_total, 0))
                  /
                  NULLIF(
                      CONVERT(decimal(38,6), pax_total),
                      0
                  )
              )
          ) > 0.01
      )
)
BEGIN
    THROW 51112,
        'Históricos incompatibles con pax_promedio canónico.',
        1;
END;

SELECT
    codigo,
    label,
    operacion,
    campo_base,
    numerador,
    denominador,
    activo,
    version
FROM dbo.Comercial_Metricas_Canonicas
WHERE codigo IN (
    N'ventas',
    N'cheque_promedio',
    N'ticket_promedio',
    N'pax_promedio',
    N'pax_por_cheque',
    N'cheques_por_pax'
)
ORDER BY orden;

SELECT
    sinonimo,
    metrica_codigo,
    activo
FROM dbo.Comercial_Metricas_Sinonimos
WHERE sinonimo IN (
    N'venta_total',
    N'ventas_total',
    N'ventas_con_iva',
    N'ventas_visibles',
    N'cheque_medio',
    N'ticket_medio',
    N'venta_por_pax',
    N'consumo_promedio_pax',
    N'personas_por_cheque',
    N'pax_por_ticket',
    N'venta_neta',
    N'ventas_netas',
    N'ventas_con_propina'
)
ORDER BY sinonimo;

SELECT
    COUNT_BIG(*) AS filas_historicas_activas,
    SUM(
        CASE
            WHEN ISNULL(tickets_total, 0) > 0
             AND ABS(
                CONVERT(decimal(38,6), ticket_promedio)
                -
                (
                    CONVERT(decimal(38,6), ventas_total)
                    /
                    NULLIF(
                        CONVERT(
                            decimal(38,6),
                            tickets_total
                        ),
                        0
                    )
                )
             ) > 0.01
            THEN 1 ELSE 0
        END
    ) AS cheque_promedio_incorrecto,
    SUM(
        CASE
            WHEN ISNULL(pax_total, 0) > 0
             AND ABS(
                CONVERT(decimal(38,6), pax_promedio)
                -
                (
                    CONVERT(decimal(38,6), ventas_total)
                    /
                    NULLIF(
                        CONVERT(
                            decimal(38,6),
                            pax_total
                        ),
                        0
                    )
                )
             ) > 0.01
            THEN 1 ELSE 0
        END
    ) AS pax_promedio_historico_pendiente
FROM dbo.Comercial_KPIs_Diarios_v2
WHERE ISNULL(activo, 1) = 1
  AND ISNULL(es_demo, 0) = 0;

SELECT
    (
        SELECT COUNT_BIG(*)
        FROM dbo.Comercial_KPIs_Diarios_v2
        WHERE ISNULL(activo, 1) = 1
          AND ISNULL(es_demo, 0) = 0
    ) AS base_rows,
    (
        SELECT COUNT_BIG(*)
        FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    ) AS runtime_rows;
