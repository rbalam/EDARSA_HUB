# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:28:35.681949
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_intraday_semantic_retry_20260805T022734Z/semantic_coverage_single.sql`

## Resultado
ERROR

## Detalle
```text
Error ejecutando SQL. Se hizo rollback. Detalle: (20047, b'DB-Lib error message 20003, severity 6:\nAdaptive Server connection timed out\nDB-Lib error message 20047, severity 9:\nDBPROCESS is dead or not enabled\n')
```

## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

SELECT
    DB_NAME() AS database_name,
    SUSER_SNAME() AS login_name,

    COUNT_BIG(*) AS filas_total,
    MIN(fecha_operacion) AS fecha_min,
    MAX(fecha_operacion) AS fecha_max,
    COUNT(DISTINCT fecha_operacion) AS dias_distintos,
    COUNT(DISTINCT numero_ticket) AS tickets_distintos,

    SUM(CASE WHEN fecha_hora IS NULL THEN 1 ELSE 0 END)
        AS fecha_hora_null,

    SUM(CASE WHEN familia_nombre IS NULL THEN 1 ELSE 0 END)
        AS familia_null,

    SUM(CASE WHEN subfamilia_nombre IS NULL THEN 1 ELSE 0 END)
        AS subfamilia_null,

    SUM(CASE WHEN importe_neto IS NULL THEN 1 ELSE 0 END)
        AS importe_neto_null,

    SUM(CASE WHEN es_kpi_valido = 1 THEN 1 ELSE 0 END)
        AS filas_kpi_validas,

    SUM(CASE WHEN cancelado_origen = 1 THEN 1 ELSE 0 END)
        AS filas_canceladas,

    SUM(CASE WHEN activo = 1 THEN 1 ELSE 0 END)
        AS filas_activas,

    SUM(COALESCE(importe_bruto, 0))
        AS importe_bruto_total,

    SUM(COALESCE(importe_neto, 0))
        AS importe_neto_total,

    SUM(COALESCE(descuento, 0))
        AS descuento_total,

    SUM(COALESCE(propina, 0))
        AS propina_total,

    (
        SELECT
            COALESCE(d.unidad_negocio_id, 'SIN_UNIDAD') AS unidad,
            MIN(d.fecha_operacion) AS fecha_min,
            MAX(d.fecha_operacion) AS fecha_max,
            COUNT_BIG(*) AS filas,
            COUNT(DISTINCT d.fecha_operacion) AS dias,
            COUNT(DISTINCT d.numero_ticket) AS tickets,
            SUM(CASE WHEN d.fecha_hora IS NULL THEN 1 ELSE 0 END)
                AS hora_null,
            SUM(CASE WHEN d.es_kpi_valido = 1 THEN 1 ELSE 0 END)
                AS validas,
            SUM(CASE WHEN d.cancelado_origen = 1 THEN 1 ELSE 0 END)
                AS canceladas
        FROM dbo.Comercial_Inteligencia_VentasDetalleProducto AS d
        GROUP BY COALESCE(d.unidad_negocio_id, 'SIN_UNIDAD')
        ORDER BY unidad
        FOR JSON PATH
    ) AS cobertura_unidades_json,

    (
        SELECT
            COALESCE(d.sistema_origen, 'SIN_ORIGEN') AS origen,
            COALESCE(d.fuente_original, 'SIN_FUENTE') AS fuente,
            MIN(d.fecha_operacion) AS fecha_min,
            MAX(d.fecha_operacion) AS fecha_max,
            COUNT_BIG(*) AS filas,
            COUNT(DISTINCT d.numero_ticket) AS tickets
        FROM dbo.Comercial_Inteligencia_VentasDetalleProducto AS d
        GROUP BY
            COALESCE(d.sistema_origen, 'SIN_ORIGEN'),
            COALESCE(d.fuente_original, 'SIN_FUENTE')
        ORDER BY origen, fuente
        FOR JSON PATH
    ) AS cobertura_origenes_json,

    (
        SELECT TOP (30)
            COALESCE(d.familia_nombre, 'SIN_FAMILIA') AS familia,
            COALESCE(d.subfamilia_nombre, 'SIN_SUBFAMILIA')
                AS subfamilia,
            COUNT_BIG(*) AS filas,
            SUM(CASE WHEN d.es_alcohol = 1 THEN 1 ELSE 0 END)
                AS filas_alcohol,
            SUM(COALESCE(d.importe_neto, 0))
                AS importe_neto
        FROM dbo.Comercial_Inteligencia_VentasDetalleProducto AS d
        GROUP BY
            COALESCE(d.familia_nombre, 'SIN_FAMILIA'),
            COALESCE(d.subfamilia_nombre, 'SIN_SUBFAMILIA')
        ORDER BY COUNT_BIG(*) DESC
        FOR JSON PATH
    ) AS familias_principales_json

FROM dbo.Comercial_Inteligencia_VentasDetalleProducto;

```