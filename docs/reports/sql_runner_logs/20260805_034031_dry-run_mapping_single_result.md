# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T03:40:31.170778
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_pos_mapping_single_result_20260805T034030Z/mapping_single_result.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Dry-run ejecutado. No se aplicaron cambios.


## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

WITH unidades AS
(
    SELECT
        CONVERT(nvarchar(100), u.id) AS unidad_negocio_pk,
        UPPER(LTRIM(RTRIM(u.codigo))) AS unidad_codigo,
        u.nombre AS unidad_nombre,
        CONVERT(nvarchar(100), u.server_id) AS server_id,
        NULLIF(
            LTRIM(RTRIM(CONVERT(nvarchar(100), u.sucursal_origen_id))),
            N''
        ) AS sucursal_origen_id,
        CONVERT(
            nvarchar(100),
            TRY_CONVERT(int, u.sucursal_origen_id)
        ) AS sucursal_legacy_id,
        UPPER(LTRIM(RTRIM(s.system_type))) AS system_type
    FROM dbo.Unidades_Negocio AS u
    INNER JOIN dbo.Servidores_Conexiones AS s
        ON s.id = u.server_id
    WHERE
        u.activo = 1
        AND s.activo = 1
),
ventas_abiertas AS
(
    SELECT
        CONVERT(nvarchar(100), server_id) AS server_id,
        NULLIF(
            LTRIM(RTRIM(CONVERT(nvarchar(100), sucursal_id))),
            N''
        ) AS sucursal_id,
        COUNT_BIG(*) AS filas,
        MIN(CAST(fecha_operacion AS date)) AS fecha_min,
        MAX(CAST(fecha_operacion AS date)) AS fecha_max
    FROM dbo.Comercial_Ventas_Dia_Abiertas_v2
    GROUP BY
        CONVERT(nvarchar(100), server_id),
        NULLIF(
            LTRIM(RTRIM(CONVERT(nvarchar(100), sucursal_id))),
            N''
        )
),
kpis_diarios AS
(
    SELECT
        CONVERT(nvarchar(100), server_id) AS server_id,
        NULLIF(
            LTRIM(RTRIM(CONVERT(nvarchar(100), sucursal_id))),
            N''
        ) AS sucursal_id,
        COUNT_BIG(*) AS filas,
        MIN(fecha_operacion) AS fecha_min,
        MAX(fecha_operacion) AS fecha_max
    FROM dbo.Comercial_KPIs_Diarios_v2
    GROUP BY
        CONVERT(nvarchar(100), server_id),
        NULLIF(
            LTRIM(RTRIM(CONVERT(nvarchar(100), sucursal_id))),
            N''
        )
),
ventas_por_server AS
(
    SELECT
        server_id,
        COUNT(*) AS sucursales_distintas,
        SUM(filas) AS filas
    FROM ventas_abiertas
    GROUP BY server_id
),
kpis_por_server AS
(
    SELECT
        server_id,
        COUNT(*) AS sucursales_distintas,
        SUM(filas) AS filas
    FROM kpis_diarios
    GROUP BY server_id
),
mapeos AS
(
    SELECT
        CONVERT(nvarchar(100), ServidorID) AS servidor_id,
        NULLIF(
            LTRIM(RTRIM(CONVERT(nvarchar(100), SucursalID))),
            N''
        ) AS sucursal_id,
        NULLIF(
            LTRIM(RTRIM(CONVERT(nvarchar(100), SucursalOrigenID))),
            N''
        ) AS sucursal_origen_id
    FROM dbo.Sistema_SucursalServidorMapeo
    WHERE Activo = 1
)
SELECT
    DB_NAME() AS database_name,
    SUSER_SNAME() AS login_name,

    u.unidad_negocio_pk,
    u.unidad_codigo,
    u.unidad_nombre,
    u.server_id,
    u.system_type,
    u.sucursal_origen_id,
    u.sucursal_legacy_id,

    COALESCE(vps.sucursales_distintas, 0)
        AS ventas_sucursales_en_server,
    COALESCE(vps.filas, 0)
        AS ventas_filas_en_server,

    COALESCE(kps.sucursales_distintas, 0)
        AS kpi_sucursales_en_server,
    COALESCE(kps.filas, 0)
        AS kpi_filas_en_server,

    COALESCE(vao.filas, 0)
        AS ventas_match_origen,
    COALESCE(val.filas, 0)
        AS ventas_match_legacy,

    COALESCE(kdo.filas, 0)
        AS kpi_match_origen,
    COALESCE(kdl.filas, 0)
        AS kpi_match_legacy,

    vao.fecha_min AS ventas_origen_fecha_min,
    vao.fecha_max AS ventas_origen_fecha_max,
    val.fecha_min AS ventas_legacy_fecha_min,
    val.fecha_max AS ventas_legacy_fecha_max,

    kdo.fecha_min AS kpi_origen_fecha_min,
    kdo.fecha_max AS kpi_origen_fecha_max,
    kdl.fecha_min AS kpi_legacy_fecha_min,
    kdl.fecha_max AS kpi_legacy_fecha_max,

    CASE
        WHEN EXISTS
        (
            SELECT 1
            FROM mapeos AS m
            WHERE
                m.servidor_id = u.server_id
                AND
                (
                    m.sucursal_id = u.sucursal_origen_id
                    OR m.sucursal_origen_id = u.sucursal_origen_id
                )
        )
        THEN 1 ELSE 0
    END AS mapeo_match_origen,

    CASE
        WHEN EXISTS
        (
            SELECT 1
            FROM mapeos AS m
            WHERE
                m.servidor_id = u.server_id
                AND
                (
                    m.sucursal_id = u.sucursal_legacy_id
                    OR m.sucursal_origen_id = u.sucursal_legacy_id
                )
        )
        THEN 1 ELSE 0
    END AS mapeo_match_legacy,

    CASE
        WHEN
            COALESCE(vao.filas, 0) > 0
            OR COALESCE(kdo.filas, 0) > 0
        THEN N'SUCURSAL_ORIGEN_ID'

        WHEN
            COALESCE(val.filas, 0) > 0
            OR COALESCE(kdl.filas, 0) > 0
        THEN N'SUCURSAL_LEGACY_ID'

        WHEN
            u.system_type = N'SOFTRESTAURANT'
            AND
            (
                COALESCE(vps.sucursales_distintas, 0) = 1
                OR COALESCE(kps.sucursales_distintas, 0) = 1
            )
        THEN N'SERVER_UNICO_SOFTRESTAURANT'

        ELSE N'NO_CONCLUIDO'
    END AS contrato_sucursal_candidato

FROM unidades AS u

LEFT JOIN ventas_por_server AS vps
    ON vps.server_id = u.server_id

LEFT JOIN kpis_por_server AS kps
    ON kps.server_id = u.server_id

LEFT JOIN ventas_abiertas AS vao
    ON vao.server_id = u.server_id
   AND vao.sucursal_id = u.sucursal_origen_id

LEFT JOIN ventas_abiertas AS val
    ON val.server_id = u.server_id
   AND val.sucursal_id = u.sucursal_legacy_id

LEFT JOIN kpis_diarios AS kdo
    ON kdo.server_id = u.server_id
   AND kdo.sucursal_id = u.sucursal_origen_id

LEFT JOIN kpis_diarios AS kdl
    ON kdl.server_id = u.server_id
   AND kdl.sucursal_id = u.sucursal_legacy_id

ORDER BY
    u.unidad_codigo;

```