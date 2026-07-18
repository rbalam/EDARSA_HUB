/*
EDARSAHUB V1.0
Contrato Comercial canónico.

IMPORTANTE:
- Este archivo NO repara todavía las filas históricas.
- Elimina el overlay de ventas abiertas de la vista histórica runtime.
- Ventas abiertas permanecen en dbo.Comercial_Ventas_Dia_Abiertas_v2.
- Debe ejecutarse únicamente mediante el runner SQL autorizado.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> N'EDARSAHUB'
BEGIN
    THROW 51000, 'Base no autorizada. Se esperaba EDARSAHUB.', 1;
END;

BEGIN TRANSACTION;

IF OBJECT_ID(
    N'dbo.Comercial_Metricas_Canonicas',
    N'U'
) IS NULL
BEGIN
    THROW 51001, 'No existe dbo.Comercial_Metricas_Canonicas.', 1;
END;

MERGE dbo.Comercial_Metricas_Canonicas AS target
USING (
    VALUES
    (
        N'ventas',
        N'Ventas con IVA',
        N'Venta visible para tableros y reportes; propinas separadas.',
        N'moneda',
        N'campo',
        N'ventas',
        NULL,
        NULL,
        0,
        10
    ),
    (
        N'propinas',
        N'Propinas',
        N'Total de propinas separado de ventas.',
        N'moneda',
        N'campo',
        N'propinas',
        NULL,
        NULL,
        0,
        30
    ),
    (
        N'cheques',
        N'Cheques',
        N'Número de cuentas, tickets o comandas.',
        N'entero',
        N'campo',
        N'cheques',
        NULL,
        NULL,
        0,
        40
    ),
    (
        N'pax',
        N'PAX',
        N'Número de comensales.',
        N'entero',
        N'campo',
        N'pax',
        NULL,
        NULL,
        0,
        50
    ),
    (
        N'cheque_promedio',
        N'Cheque promedio',
        N'Ventas con IVA / cheques.',
        N'moneda',
        N'ratio',
        NULL,
        N'ventas',
        N'cheques',
        0,
        60
    ),
    (
        N'ticket_promedio',
        N'Cheque promedio (alias legacy)',
        N'Alias compatible de cheque_promedio.',
        N'moneda',
        N'ratio',
        NULL,
        N'ventas',
        N'cheques',
        0,
        70
    ),
    (
        N'pax_promedio',
        N'Consumo promedio por PAX',
        N'Ventas con IVA / PAX.',
        N'moneda',
        N'ratio',
        NULL,
        N'ventas',
        N'pax',
        0,
        80
    ),
    (
        N'pax_por_cheque',
        N'PAX por cheque',
        N'PAX / cheques.',
        N'decimal',
        N'ratio',
        NULL,
        N'pax',
        N'cheques',
        0,
        90
    ),
    (
        N'cheques_por_pax',
        N'Cheques por PAX',
        N'Cheques / PAX.',
        N'decimal',
        N'ratio',
        NULL,
        N'cheques',
        N'pax',
        0,
        100
    )
) AS source (
    codigo,
    label,
    descripcion,
    formato,
    operacion,
    campo_base,
    numerador,
    denominador,
    excluye_propina,
    orden
)
ON target.codigo = source.codigo
WHEN MATCHED THEN
    UPDATE SET
        label = source.label,
        descripcion = source.descripcion,
        formato = source.formato,
        operacion = source.operacion,
        campo_base = source.campo_base,
        numerador = source.numerador,
        denominador = source.denominador,
        excluye_propina = source.excluye_propina,
        orden = source.orden,
        version = target.version,
        activo = 1,
        updated_at = SYSUTCDATETIME(),
        modified_by = N'20260717_020'
WHEN NOT MATCHED THEN
    INSERT (
        codigo,
        label,
        descripcion,
        formato,
        operacion,
        campo_base,
        numerador,
        denominador,
        excluye_propina,
        orden,
        version,
        activo,
        created_by
    )
    VALUES (
        source.codigo,
        source.label,
        source.descripcion,
        source.formato,
        source.operacion,
        source.campo_base,
        source.numerador,
        source.denominador,
        source.excluye_propina,
        source.orden,
        1,
        1,
        N'20260717_020'
    );

UPDATE dbo.Comercial_Metricas_Canonicas
SET
    activo = 0,
    updated_at = SYSUTCDATETIME(),
    modified_by = N'20260717_020'
WHERE codigo IN (N'ventas_brutas', N'ventas_sin_propina');


-- 20260717_020 CANONICAL SYNONYMS
IF OBJECT_ID(
    N'dbo.Comercial_Metricas_Sinonimos',
    N'U'
) IS NULL
BEGIN
    THROW 51006,
        'No existe dbo.Comercial_Metricas_Sinonimos.',
        1;
END;

MERGE dbo.Comercial_Metricas_Sinonimos
    WITH (HOLDLOCK) AS target
USING (
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
) AS source (
    sinonimo,
    metrica_codigo
)
ON target.sinonimo = source.sinonimo
WHEN MATCHED THEN
    UPDATE SET
        metrica_codigo = source.metrica_codigo,
        activo = 1
WHEN NOT MATCHED THEN
    INSERT (
        metrica_codigo,
        sinonimo,
        activo
    )
    VALUES (
        source.metrica_codigo,
        source.sinonimo,
        1
    );

-- Alias legacy retirados del contrato público y operativo.
UPDATE dbo.Comercial_Metricas_Sinonimos
SET activo = 0
WHERE sinonimo IN (
    N'venta_neta',
    N'ventas_netas',
    N'ventas_con_propina'
);

IF OBJECT_ID(
    N'dbo.vw_Comercial_KPIs_Diarios_v2_Runtime',
    N'V'
) IS NULL
BEGIN
    THROW 51002, 'No existe la vista runtime comercial.', 1;
END;

IF OBJECT_ID(
    N'dbo.Comercial_KPIs_Diarios_v2',
    N'U'
) IS NULL
BEGIN
    THROW 51003, 'No existe la tabla histórica comercial.', 1;
END;

/*
La migración preserva exactamente las columnas actuales de la vista.
Falla cerrado si alguna columna runtime no existe en la tabla base.
*/
IF EXISTS (
    SELECT 1
    FROM sys.columns view_column
    LEFT JOIN sys.columns base_column
      ON base_column.object_id =
         OBJECT_ID(N'dbo.Comercial_KPIs_Diarios_v2')
     AND base_column.name = view_column.name
    WHERE view_column.object_id =
          OBJECT_ID(
              N'dbo.vw_Comercial_KPIs_Diarios_v2_Runtime'
          )
      AND base_column.column_id IS NULL
)
BEGIN
    THROW 51004,
        'La vista runtime contiene columnas no presentes en la tabla base.',
        1;
END;

DECLARE @select_list nvarchar(max);

SELECT
    @select_list = STRING_AGG(
        CONVERT(
            nvarchar(max),
            N'k.' + QUOTENAME(view_column.name)
            + N' AS ' + QUOTENAME(view_column.name)
        ),
        N',' + CHAR(10) + N'    '
    ) WITHIN GROUP (
        ORDER BY view_column.column_id
    )
FROM sys.columns view_column
WHERE view_column.object_id =
      OBJECT_ID(
          N'dbo.vw_Comercial_KPIs_Diarios_v2_Runtime'
      )
  AND view_column.name <> N'ventas_sin_propina';

IF NULLIF(@select_list, N'') IS NULL
BEGIN
    THROW 51005, 'No se pudo construir la vista runtime.', 1;
END;

DECLARE @view_sql nvarchar(max) =
    N'CREATE OR ALTER VIEW '
    + N'dbo.vw_Comercial_KPIs_Diarios_v2_Runtime'
    + N' AS'
    + CHAR(10)
    + N'SELECT'
    + CHAR(10)
    + N'    ' + @select_list
    + CHAR(10)
    + N'FROM dbo.Comercial_KPIs_Diarios_v2 k'
    + CHAR(10)
    + N'WHERE ISNULL(k.activo, 1) = 1'
    + CHAR(10)
    + N'  AND ISNULL(k.es_demo, 0) = 0;';

EXEC sys.sp_executesql @view_sql;

COMMIT TRANSACTION;
