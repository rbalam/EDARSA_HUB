# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T03:43:27.865696
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_pos_branch_contract_20260805T034327Z/branch_contract.sql`

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
        UPPER(LTRIM(RTRIM(s.system_type))) AS system_type
    FROM dbo.Unidades_Negocio AS u
    INNER JOIN dbo.Servidores_Conexiones AS s
        ON s.id = u.server_id
    WHERE
        u.activo = 1
        AND s.activo = 1
),
kpi_sucursales AS
(
    SELECT
        CONVERT(nvarchar(100), server_id) AS server_id,
        NULLIF(
            LTRIM(RTRIM(CONVERT(nvarchar(100), sucursal_id))),
            N''
        ) AS sucursal_id,
        MAX(NULLIF(LTRIM(RTRIM(sucursal_nombre)), N'')) AS sucursal_nombre,
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
kpi_resumen AS
(
    SELECT
        server_id,
        COUNT(*) AS sucursales_distintas,
        MIN(sucursal_id) AS sucursal_id_unica,
        MIN(sucursal_nombre) AS sucursal_nombre_unica,
        SUM(filas) AS filas,
        MIN(fecha_min) AS fecha_min,
        MAX(fecha_max) AS fecha_max
    FROM kpi_sucursales
    GROUP BY server_id
),
ventas_sucursales AS
(
    SELECT
        CONVERT(nvarchar(100), server_id) AS server_id,
        NULLIF(
            LTRIM(RTRIM(CONVERT(nvarchar(100), sucursal_id))),
            N''
        ) AS sucursal_id,
        MAX(NULLIF(LTRIM(RTRIM(sucursal_nombre)), N'')) AS sucursal_nombre,
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
ventas_resumen AS
(
    SELECT
        server_id,
        COUNT(*) AS sucursales_distintas,
        MIN(sucursal_id) AS sucursal_id_unica,
        MIN(sucursal_nombre) AS sucursal_nombre_unica,
        SUM(filas) AS filas,
        MIN(fecha_min) AS fecha_min,
        MAX(fecha_max) AS fecha_max
    FROM ventas_sucursales
    GROUP BY server_id
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

    COALESCE(k.sucursales_distintas, 0)
        AS kpi_sucursales_distintas,
    k.sucursal_id_unica
        AS kpi_sucursal_id_unica,
    k.sucursal_nombre_unica
        AS kpi_sucursal_nombre_unica,
    COALESCE(k.filas, 0)
        AS kpi_filas,
    k.fecha_min
        AS kpi_fecha_min,
    k.fecha_max
        AS kpi_fecha_max,

    COALESCE(v.sucursales_distintas, 0)
        AS ventas_sucursales_distintas,
    v.sucursal_id_unica
        AS ventas_sucursal_id_unica,
    v.sucursal_nombre_unica
        AS ventas_sucursal_nombre_unica,
    COALESCE(v.filas, 0)
        AS ventas_filas,
    v.fecha_min
        AS ventas_fecha_min,
    v.fecha_max
        AS ventas_fecha_max,

    CASE
        WHEN
            u.system_type IN
            (
                N'MPRO',
                N'MANAGEMENTPRO',
                N'MANAGEMENT_PRO'
            )
            AND u.sucursal_origen_id IS NOT NULL
        THEN u.sucursal_origen_id

        WHEN
            u.system_type LIKE N'SOFTRESTAURANT%'
            AND COALESCE(k.sucursales_distintas, 0) = 1
        THEN k.sucursal_id_unica

        WHEN
            u.system_type LIKE N'SOFTRESTAURANT%'
            AND COALESCE(v.sucursales_distintas, 0) = 1
        THEN v.sucursal_id_unica

        ELSE NULL
    END AS sucursal_id_resuelta,

    CASE
        WHEN
            u.system_type IN
            (
                N'MPRO',
                N'MANAGEMENTPRO',
                N'MANAGEMENT_PRO'
            )
            AND u.sucursal_origen_id IS NOT NULL
        THEN N'POS_RUNTIME_CONTEXT_SUCURSAL_ORIGEN'

        WHEN
            u.system_type LIKE N'SOFTRESTAURANT%'
            AND COALESCE(k.sucursales_distintas, 0) = 1
        THEN N'KPI_CANONICO_SERVER_UNICO'

        WHEN
            u.system_type LIKE N'SOFTRESTAURANT%'
            AND COALESCE(v.sucursales_distintas, 0) = 1
        THEN N'VENTAS_DIA_SERVER_UNICO'

        ELSE N'NO_CONCLUIDO'
    END AS fuente_sucursal_resuelta,

    CASE
        WHEN
            u.system_type LIKE N'SOFTRESTAURANT%'
            AND COALESCE(k.sucursales_distintas, 0) > 1
        THEN N'MULTIPLES_SUCURSALES_KPI'

        WHEN
            u.system_type LIKE N'SOFTRESTAURANT%'
            AND COALESCE(v.sucursales_distintas, 0) > 1
        THEN N'MULTIPLES_SUCURSALES_VENTAS'

        WHEN
            u.system_type IN
            (
                N'MPRO',
                N'MANAGEMENTPRO',
                N'MANAGEMENT_PRO'
            )
            AND u.sucursal_origen_id IS NULL
        THEN N'MPRO_SIN_SUCURSAL_ORIGEN'

        ELSE N'SIN_BLOQUEO'
    END AS validacion_contrato

FROM unidades AS u

LEFT JOIN kpi_resumen AS k
    ON k.server_id = u.server_id

LEFT JOIN ventas_resumen AS v
    ON v.server_id = u.server_id

ORDER BY
    u.unidad_codigo;

```