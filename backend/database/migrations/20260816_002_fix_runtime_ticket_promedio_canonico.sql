-- EDARSAHUB V1.0
-- Forward migration.
-- ticket_promedio = ventas / tickets
-- pax_promedio    = ventas / pax
-- Fuente: definición SQL materializada vigente.
-- No modifica migraciones históricas.
-- Ejecución explícita únicamente.

CREATE OR ALTER VIEW dbo.vw_Comercial_KPIs_Diarios_v2_Runtime AS
WITH snapshot_fecha AS (
    SELECT MAX(fecha_operacion) AS fecha_operacion
    FROM dbo.Comercial_Ventas_Dia_Abiertas_v2
    WHERE ISNULL(total_estimado_dia, 0) > 0
),
snapshot_ranked AS (
    SELECT
        a.*,
        ROW_NUMBER() OVER (
            PARTITION BY a.fecha_operacion, a.unidad_negocio_id
            ORDER BY a.snapshot_timestamp DESC, a.fecha_ultima_actualizacion DESC
        ) AS rn
    FROM dbo.Comercial_Ventas_Dia_Abiertas_v2 a
    INNER JOIN snapshot_fecha sf
        ON sf.fecha_operacion = a.fecha_operacion
),
snapshot AS (
    SELECT *
    FROM snapshot_ranked
    WHERE rn = 1
),
base_overlay AS (
    SELECT
        k.id,
        k.unidad_negocio_pk,
        u.id AS unidad_id,

        k.unidad_negocio_id,
        k.unidad_negocio_nombre,
        u.codigo AS UnidadNegocio,
        u.codigo AS unidad_codigo,
        u.nombre AS unidad_nombre_catalogo,

        k.server_id,
        k.sucursal_id,
        k.sucursal_nombre,
        k.sistema_origen,
        k.fecha_operacion,
        k.anio,
        k.mes,
        k.dia,

        CASE WHEN s.unidad_negocio_id IS NOT NULL THEN ISNULL(s.total_estimado_dia, 0) ELSE k.ventas_total END AS ventas_total,
        CASE WHEN s.unidad_negocio_id IS NOT NULL THEN ISNULL(s.total_estimado_dia, 0) ELSE k.ventas_sin_propina END AS ventas_sin_propina,
        CASE WHEN s.unidad_negocio_id IS NOT NULL THEN ISNULL(s.propinas_total, 0) ELSE k.propinas_total END AS propinas_total,

        CASE
            WHEN s.unidad_negocio_id IS NOT NULL THEN ISNULL(s.tickets_abiertos, 0) + ISNULL(s.tickets_cerrados_dia, 0)
            ELSE k.tickets_total
        END AS tickets_total,

        CASE
            WHEN s.unidad_negocio_id IS NOT NULL THEN ISNULL(s.pax_abiertos, 0) + ISNULL(s.pax_cerrados_dia, 0)
            ELSE k.pax_total
        END AS pax_total,

        CASE
            WHEN s.unidad_negocio_id IS NOT NULL
             AND (ISNULL(s.tickets_abiertos, 0) + ISNULL(s.tickets_cerrados_dia, 0)) > 0
                THEN CAST(ISNULL(s.total_estimado_dia, 0) AS decimal(18,2))
                     / NULLIF((ISNULL(s.tickets_abiertos, 0) + ISNULL(s.tickets_cerrados_dia, 0)), 0)
            ELSE k.ticket_promedio
        END AS ticket_promedio,

        CASE
            WHEN s.unidad_negocio_id IS NOT NULL
             AND (ISNULL(s.pax_abiertos, 0) + ISNULL(s.pax_cerrados_dia, 0)) > 0
                THEN CAST(ISNULL(s.total_estimado_dia, 0) AS decimal(18,2))
                     / NULLIF((ISNULL(s.pax_abiertos, 0) + ISNULL(s.pax_cerrados_dia, 0)), 0)
            ELSE k.pax_promedio
        END AS pax_promedio,

        CASE WHEN s.unidad_negocio_id IS NOT NULL THEN ISNULL(s.ventas_cerradas_dia, 0) ELSE k.ventas_cerradas END AS ventas_cerradas,
        CASE WHEN s.unidad_negocio_id IS NOT NULL THEN ISNULL(s.ventas_abiertas, 0) ELSE k.ventas_abiertas END AS ventas_abiertas,
        CASE WHEN s.unidad_negocio_id IS NOT NULL THEN ISNULL(s.total_estimado_dia, 0) ELSE k.total_estimado_dia END AS total_estimado_dia,

        CASE
            WHEN s.unidad_negocio_id IS NOT NULL AND ISNULL(s.ventas_abiertas, 0) > 0 THEN CAST(1 AS bit)
            ELSE k.es_venta_abierta
        END AS es_venta_abierta,

        CASE
            WHEN s.unidad_negocio_id IS NOT NULL AND ISNULL(s.ventas_abiertas, 0) > 0 THEN CAST(0 AS bit)
            ELSE k.es_corte_cerrado
        END AS es_corte_cerrado,

        CASE
            WHEN s.unidad_negocio_id IS NOT NULL THEN 'Comercial_Ventas_Dia_Abiertas_v2'
            ELSE k.fuente_original
        END AS fuente_original,

        k.id_origen,
        k.hash_origen,
        k.sync_run_id,

        CASE
            WHEN s.unidad_negocio_id IS NOT NULL THEN s.fecha_ultima_actualizacion
            ELSE k.fecha_sincronizacion
        END AS fecha_sincronizacion,

        k.fecha_alta,

        CASE
            WHEN s.unidad_negocio_id IS NOT NULL THEN s.fecha_ultima_actualizacion
            ELSE k.fecha_ultima_actualizacion
        END AS fecha_ultima_actualizacion,

        k.version
    FROM dbo.Comercial_KPIs_Diarios_v2 k
    INNER JOIN dbo.Unidades_Negocio u
        ON u.id = k.unidad_negocio_pk
    LEFT JOIN snapshot s
        ON s.fecha_operacion = k.fecha_operacion
       AND s.unidad_negocio_id = k.unidad_negocio_id
    WHERE ISNULL(k.activo, 1) = 1
      AND ISNULL(k.es_demo, 0) = 0
),
snapshot_only AS (
    SELECT
        NEWID() AS id,
        u.id AS unidad_negocio_pk,
        u.id AS unidad_id,

        s.unidad_negocio_id,
        s.unidad_negocio_nombre,
        u.codigo AS UnidadNegocio,
        u.codigo AS unidad_codigo,
        u.nombre AS unidad_nombre_catalogo,

        s.server_id,
        s.sucursal_id,
        s.sucursal_nombre,
        s.sistema_origen,
        s.fecha_operacion,
        YEAR(s.fecha_operacion) AS anio,
        MONTH(s.fecha_operacion) AS mes,
        DAY(s.fecha_operacion) AS dia,

        ISNULL(s.total_estimado_dia, 0) AS ventas_total,
        ISNULL(s.total_estimado_dia, 0) AS ventas_sin_propina,
        ISNULL(s.propinas_total, 0) AS propinas_total,

        ISNULL(s.tickets_abiertos, 0) + ISNULL(s.tickets_cerrados_dia, 0) AS tickets_total,
        ISNULL(s.pax_abiertos, 0) + ISNULL(s.pax_cerrados_dia, 0) AS pax_total,

        CASE
            WHEN (ISNULL(s.tickets_abiertos, 0) + ISNULL(s.tickets_cerrados_dia, 0)) > 0
                THEN CAST(ISNULL(s.total_estimado_dia, 0) AS decimal(18,2))
                     / NULLIF((ISNULL(s.tickets_abiertos, 0) + ISNULL(s.tickets_cerrados_dia, 0)), 0)
            ELSE CAST(0 AS decimal(18,2))
        END AS ticket_promedio,

        CASE
            WHEN (ISNULL(s.pax_abiertos, 0) + ISNULL(s.pax_cerrados_dia, 0)) > 0
                THEN CAST(ISNULL(s.total_estimado_dia, 0) AS decimal(18,2))
                     / NULLIF((ISNULL(s.pax_abiertos, 0) + ISNULL(s.pax_cerrados_dia, 0)), 0)
            ELSE CAST(0 AS decimal(18,2))
        END AS pax_promedio,

        ISNULL(s.ventas_cerradas_dia, 0) AS ventas_cerradas,
        ISNULL(s.ventas_abiertas, 0) AS ventas_abiertas,
        ISNULL(s.total_estimado_dia, 0) AS total_estimado_dia,

        CASE WHEN ISNULL(s.ventas_abiertas, 0) > 0 THEN CAST(1 AS bit) ELSE CAST(0 AS bit) END AS es_venta_abierta,
        CASE WHEN ISNULL(s.ventas_abiertas, 0) > 0 THEN CAST(0 AS bit) ELSE CAST(1 AS bit) END AS es_corte_cerrado,

        'Comercial_Ventas_Dia_Abiertas_v2' AS fuente_original,
        s.id AS id_origen,
        s.sync_run_id AS hash_origen,
        s.sync_run_id,

        s.fecha_ultima_actualizacion AS fecha_sincronizacion,
        s.snapshot_timestamp AS fecha_alta,
        s.fecha_ultima_actualizacion,
        CAST(1 AS int) AS version
    FROM snapshot s
    INNER JOIN dbo.Unidades_Negocio u
        ON u.codigo = s.unidad_negocio_id
    WHERE NOT EXISTS (
        SELECT 1
        FROM dbo.Comercial_KPIs_Diarios_v2 k
        WHERE k.fecha_operacion = s.fecha_operacion
          AND k.unidad_negocio_id = s.unidad_negocio_id
          AND ISNULL(k.activo, 1) = 1
          AND ISNULL(k.es_demo, 0) = 0
    )
)
SELECT * FROM base_overlay
UNION ALL
SELECT * FROM snapshot_only;
