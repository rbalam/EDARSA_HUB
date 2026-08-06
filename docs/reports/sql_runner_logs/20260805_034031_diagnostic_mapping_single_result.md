# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T03:40:31.950185
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_pos_mapping_single_result_20260805T034030Z/mapping_single_result.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, login_name, unidad_negocio_pk, unidad_codigo, unidad_nombre, server_id, system_type, sucursal_origen_id, sucursal_legacy_id, ventas_sucursales_en_server, ventas_filas_en_server, kpi_sucursales_en_server, kpi_filas_en_server, ventas_match_origen, ventas_match_legacy, kpi_match_origen, kpi_match_legacy, ventas_origen_fecha_min, ventas_origen_fecha_max, ventas_legacy_fecha_min, ventas_legacy_fecha_max, kpi_origen_fecha_min, kpi_origen_fecha_max, kpi_legacy_fecha_min, kpi_legacy_fecha_max, mapeo_match_origen, mapeo_match_legacy, contrato_sucursal_candidato
- Filas: 5
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'unidad_negocio_pk': '19E076FB-C6DE-4EA5-84AB-1CAA9E86082C', 'unidad_codigo': '130MID', 'unidad_nombre': '130° MERIDA', 'server_id': 'a5547321-1139-4d2b-9d53-182ca737b6b6', 'system_type': 'SOFTRESTAURANT_PRO', 'sucursal_origen_id': None, 'sucursal_legacy_id': None, 'ventas_sucursales_en_server': 1, 'ventas_filas_en_server': 1, 'kpi_sucursales_en_server': 1, 'kpi_filas_en_server': 3658, 'ventas_match_origen': 0, 'ventas_match_legacy': 0, 'kpi_match_origen': 0, 'kpi_match_legacy': 0, 'ventas_origen_fecha_min': None, 'ventas_origen_fecha_max': None, 'ventas_legacy_fecha_min': None, 'ventas_legacy_fecha_max': None, 'kpi_origen_fecha_min': None, 'kpi_origen_fecha_max': None, 'kpi_legacy_fecha_min': None, 'kpi_legacy_fecha_max': None, 'mapeo_match_origen': 0, 'mapeo_match_legacy': 0, 'contrato_sucursal_candidato': 'NO_CONCLUIDO'}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'unidad_negocio_pk': '9BC05CED-6B2B-4A0A-AA90-CE649B78E12C', 'unidad_codigo': '130QRO', 'unidad_nombre': '130° QUERETARO', 'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6', 'system_type': 'MPRO', 'sucursal_origen_id': '0021', 'sucursal_legacy_id': '21', 'ventas_sucursales_en_server': 0, 'ventas_filas_en_server': 0, 'kpi_sucursales_en_server': 2, 'kpi_filas_en_server': 3299, 'ventas_match_origen': 0, 'ventas_match_legacy': 0, 'kpi_match_origen': 1780, 'kpi_match_legacy': 0, 'ventas_origen_fecha_min': None, 'ventas_origen_fecha_max': None, 'ventas_legacy_fecha_min': None, 'ventas_legacy_fecha_max': None, 'kpi_origen_fecha_min': datetime.date(2021, 9, 17), 'kpi_origen_fecha_max': datetime.date(2026, 8, 3), 'kpi_legacy_fecha_min': None, 'kpi_legacy_fecha_max': None, 'mapeo_match_origen': 1, 'mapeo_match_legacy': 0, 'contrato_sucursal_candidato': 'SUCURSAL_ORIGEN_ID'}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'unidad_negocio_pk': 'B06EE652-0370-4267-B0A8-DA6FC39B590A', 'unidad_codigo': 'CIENFUEGOS', 'unidad_nombre': 'CIENFUEGOS', 'server_id': '6d053c22-523e-48c0-b72b-96081e2d781b', 'system_type': 'SOFTRESTAURANT_PRO', 'sucursal_origen_id': None, 'sucursal_legacy_id': None, 'ventas_sucursales_en_server': 1, 'ventas_filas_en_server': 1, 'kpi_sucursales_en_server': 1, 'kpi_filas_en_server': 2290, 'ventas_match_origen': 0, 'ventas_match_legacy': 0, 'kpi_match_origen': 0, 'kpi_match_legacy': 0, 'ventas_origen_fecha_min': None, 'ventas_origen_fecha_max': None, 'ventas_legacy_fecha_min': None, 'ventas_legacy_fecha_max': None, 'kpi_origen_fecha_min': None, 'kpi_origen_fecha_max': None, 'kpi_legacy_fecha_min': None, 'kpi_legacy_fecha_max': None, 'mapeo_match_origen': 0, 'mapeo_match_legacy': 0, 'contrato_sucursal_candidato': 'NO_CONCLUIDO'}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'unidad_negocio_pk': 'DFB86008-1B81-472A-9E50-8A0821DEC4B2', 'unidad_codigo': 'ESTELAR', 'unidad_nombre': 'LA ESTELAR', 'server_id': 'a5ff0e25-f029-43db-b634-d4ac814c904f', 'system_type': 'SOFTRESTAURANT_PRO', 'sucursal_origen_id': None, 'sucursal_legacy_id': None, 'ventas_sucursales_en_server': 1, 'ventas_filas_en_server': 1, 'kpi_sucursales_en_server': 1, 'kpi_filas_en_server': 410, 'ventas_match_origen': 0, 'ventas_match_legacy': 0, 'kpi_match_origen': 0, 'kpi_match_legacy': 0, 'ventas_origen_fecha_min': None, 'ventas_origen_fecha_max': None, 'ventas_legacy_fecha_min': None, 'ventas_legacy_fecha_max': None, 'kpi_origen_fecha_min': None, 'kpi_origen_fecha_max': None, 'kpi_legacy_fecha_min': None, 'kpi_legacy_fecha_max': None, 'mapeo_match_origen': 0, 'mapeo_match_legacy': 0, 'contrato_sucursal_candidato': 'NO_CONCLUIDO'}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'unidad_negocio_pk': '23CA0B76-6580-4874-BA9B-672B122CA197', 'unidad_codigo': 'ORIGEN', 'unidad_nombre': 'ORIGEN', 'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6', 'system_type': 'MPRO', 'sucursal_origen_id': '0023', 'sucursal_legacy_id': '23', 'ventas_sucursales_en_server': 0, 'ventas_filas_en_server': 0, 'kpi_sucursales_en_server': 2, 'kpi_filas_en_server': 3299, 'ventas_match_origen': 0, 'ventas_match_legacy': 0, 'kpi_match_origen': 1519, 'kpi_match_legacy': 0, 'ventas_origen_fecha_min': None, 'ventas_origen_fecha_max': None, 'ventas_legacy_fecha_min': None, 'ventas_legacy_fecha_max': None, 'kpi_origen_fecha_min': datetime.date(2022, 5, 19), 'kpi_origen_fecha_max': datetime.date(2026, 8, 4), 'kpi_legacy_fecha_min': None, 'kpi_legacy_fecha_max': None, 'mapeo_match_origen': 1, 'mapeo_match_legacy': 0, 'contrato_sucursal_candidato': 'SUCURSAL_ORIGEN_ID'}
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