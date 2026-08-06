# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T03:43:28.579613
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_pos_branch_contract_20260805T034327Z/branch_contract.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, login_name, unidad_negocio_pk, unidad_codigo, unidad_nombre, server_id, system_type, sucursal_origen_id, kpi_sucursales_distintas, kpi_sucursal_id_unica, kpi_sucursal_nombre_unica, kpi_filas, kpi_fecha_min, kpi_fecha_max, ventas_sucursales_distintas, ventas_sucursal_id_unica, ventas_sucursal_nombre_unica, ventas_filas, ventas_fecha_min, ventas_fecha_max, sucursal_id_resuelta, fuente_sucursal_resuelta, validacion_contrato
- Filas: 5
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'unidad_negocio_pk': '19E076FB-C6DE-4EA5-84AB-1CAA9E86082C', 'unidad_codigo': '130MID', 'unidad_nombre': '130° MERIDA', 'server_id': 'a5547321-1139-4d2b-9d53-182ca737b6b6', 'system_type': 'SOFTRESTAURANT_PRO', 'sucursal_origen_id': None, 'kpi_sucursales_distintas': 1, 'kpi_sucursal_id_unica': 'DEFAULT', 'kpi_sucursal_nombre_unica': '130° MERIDA', 'kpi_filas': 3658, 'kpi_fecha_min': datetime.date(2016, 6, 14), 'kpi_fecha_max': datetime.date(2026, 8, 3), 'ventas_sucursales_distintas': 1, 'ventas_sucursal_id_unica': 'DEFAULT', 'ventas_sucursal_nombre_unica': '130° MERIDA', 'ventas_filas': 1, 'ventas_fecha_min': datetime.date(2026, 8, 4), 'ventas_fecha_max': datetime.date(2026, 8, 4), 'sucursal_id_resuelta': 'DEFAULT', 'fuente_sucursal_resuelta': 'KPI_CANONICO_SERVER_UNICO', 'validacion_contrato': 'SIN_BLOQUEO'}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'unidad_negocio_pk': '9BC05CED-6B2B-4A0A-AA90-CE649B78E12C', 'unidad_codigo': '130QRO', 'unidad_nombre': '130° QUERETARO', 'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6', 'system_type': 'MPRO', 'sucursal_origen_id': '0021', 'kpi_sucursales_distintas': 2, 'kpi_sucursal_id_unica': '0021', 'kpi_sucursal_nombre_unica': '130° QUERETARO', 'kpi_filas': 3299, 'kpi_fecha_min': datetime.date(2021, 9, 17), 'kpi_fecha_max': datetime.date(2026, 8, 4), 'ventas_sucursales_distintas': 0, 'ventas_sucursal_id_unica': None, 'ventas_sucursal_nombre_unica': None, 'ventas_filas': 0, 'ventas_fecha_min': None, 'ventas_fecha_max': None, 'sucursal_id_resuelta': '0021', 'fuente_sucursal_resuelta': 'POS_RUNTIME_CONTEXT_SUCURSAL_ORIGEN', 'validacion_contrato': 'SIN_BLOQUEO'}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'unidad_negocio_pk': 'B06EE652-0370-4267-B0A8-DA6FC39B590A', 'unidad_codigo': 'CIENFUEGOS', 'unidad_nombre': 'CIENFUEGOS', 'server_id': '6d053c22-523e-48c0-b72b-96081e2d781b', 'system_type': 'SOFTRESTAURANT_PRO', 'sucursal_origen_id': None, 'kpi_sucursales_distintas': 1, 'kpi_sucursal_id_unica': 'DEFAULT', 'kpi_sucursal_nombre_unica': 'CIENFUEGOS', 'kpi_filas': 2290, 'kpi_fecha_min': datetime.date(2019, 12, 23), 'kpi_fecha_max': datetime.date(2026, 8, 4), 'ventas_sucursales_distintas': 1, 'ventas_sucursal_id_unica': 'DEFAULT', 'ventas_sucursal_nombre_unica': 'CIENFUEGOS', 'ventas_filas': 1, 'ventas_fecha_min': datetime.date(2026, 8, 4), 'ventas_fecha_max': datetime.date(2026, 8, 4), 'sucursal_id_resuelta': 'DEFAULT', 'fuente_sucursal_resuelta': 'KPI_CANONICO_SERVER_UNICO', 'validacion_contrato': 'SIN_BLOQUEO'}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'unidad_negocio_pk': 'DFB86008-1B81-472A-9E50-8A0821DEC4B2', 'unidad_codigo': 'ESTELAR', 'unidad_nombre': 'LA ESTELAR', 'server_id': 'a5ff0e25-f029-43db-b634-d4ac814c904f', 'system_type': 'SOFTRESTAURANT_PRO', 'sucursal_origen_id': None, 'kpi_sucursales_distintas': 1, 'kpi_sucursal_id_unica': 'DEFAULT', 'kpi_sucursal_nombre_unica': 'LA ESTELAR', 'kpi_filas': 410, 'kpi_fecha_min': datetime.date(2025, 6, 12), 'kpi_fecha_max': datetime.date(2026, 8, 4), 'ventas_sucursales_distintas': 1, 'ventas_sucursal_id_unica': 'DEFAULT', 'ventas_sucursal_nombre_unica': 'LA ESTELAR', 'ventas_filas': 1, 'ventas_fecha_min': datetime.date(2026, 8, 4), 'ventas_fecha_max': datetime.date(2026, 8, 4), 'sucursal_id_resuelta': 'DEFAULT', 'fuente_sucursal_resuelta': 'KPI_CANONICO_SERVER_UNICO', 'validacion_contrato': 'SIN_BLOQUEO'}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'unidad_negocio_pk': '23CA0B76-6580-4874-BA9B-672B122CA197', 'unidad_codigo': 'ORIGEN', 'unidad_nombre': 'ORIGEN', 'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6', 'system_type': 'MPRO', 'sucursal_origen_id': '0023', 'kpi_sucursales_distintas': 2, 'kpi_sucursal_id_unica': '0021', 'kpi_sucursal_nombre_unica': '130° QUERETARO', 'kpi_filas': 3299, 'kpi_fecha_min': datetime.date(2021, 9, 17), 'kpi_fecha_max': datetime.date(2026, 8, 4), 'ventas_sucursales_distintas': 0, 'ventas_sucursal_id_unica': None, 'ventas_sucursal_nombre_unica': None, 'ventas_filas': 0, 'ventas_fecha_min': None, 'ventas_fecha_max': None, 'sucursal_id_resuelta': '0023', 'fuente_sucursal_resuelta': 'POS_RUNTIME_CONTEXT_SUCURSAL_ORIGEN', 'validacion_contrato': 'SIN_BLOQUEO'}
```


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