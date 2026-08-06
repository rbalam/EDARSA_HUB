# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:26:38.214130
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_intraday_semantic_coverage_20260805T022637Z/semantic_coverage.sql`

## Resultado
ERROR

## Detalle
```text
Error ejecutando SQL. Se hizo rollback. Detalle: (156, b"Incorrect syntax near the keyword 'AS'.DB-Lib error message 20018, severity 15:\nGeneral SQL Server error: Check messages from the SQL Server\nDB-Lib error message 20018, severity 15:\nGeneral SQL Server error: Check messages from the SQL Server\nDB-Lib error message 20018, severity 15:\nGeneral SQL Server error: Check messages from the SQL Server\nDB-Lib error message 20018, severity 15:\nGeneral SQL Server error: Check messages from the SQL Server\nDB-Lib error message 20018, severity 15:\nGeneral SQL Server error: Check messages from the SQL Server\nDB-Lib error message 20018, severity 15:\nGeneral SQL Server error: Check messages from the SQL Server\nDB-Lib error message 20018, severity 15:\nGeneral SQL Server error: Check messages from the SQL Server\nDB-Lib error message 20018, severity 15:\nGeneral SQL Server error: Check messages from the SQL Server\nDB-Lib error message 20018, severity 15:\nGeneral SQL Server error: Check messages from the SQL Server\nDB-Lib error message 20018, severity 15:\nGeneral SQL Server error: Check messages from the SQL Server\nDB-Lib error message 20018, severity 15:\nGeneral SQL Server error: Check messages from the SQL Server\nDB-Lib error message 20018, severity 15:\nGeneral SQL Server error: Check messages from the SQL Server\n")
```

## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

;WITH Base AS (
    SELECT
        unidad_negocio_id,
        sistema_origen,
        fecha_operacion,
        fecha_hora,
        numero_ticket,
        id_transaccion,
        producto_codigo_fuente,
        familia_nombre,
        subfamilia_nombre,
        es_alcohol,
        cantidad,
        importe_bruto,
        importe_neto,
        descuento,
        propina,
        pax,
        activo,
        cancelado_origen,
        es_kpi_valido,
        fuente_original
    FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
),
UnitCoverage AS (
    SELECT
        COALESCE(unidad_negocio_id, SIN_UNIDAD) AS unidad,
        MIN(fecha_operacion) AS fecha_min,
        MAX(fecha_operacion) AS fecha_max,
        COUNT_BIG(*) AS filas,
        COUNT(DISTINCT fecha_operacion) AS dias,
        COUNT(DISTINCT numero_ticket) AS tickets,
        SUM(CASE WHEN fecha_hora IS NULL THEN 1 ELSE 0 END) AS fecha_hora_null,
        SUM(CASE WHEN es_kpi_valido = 1 THEN 1 ELSE 0 END) AS filas_validas,
        SUM(CASE WHEN cancelado_origen = 1 THEN 1 ELSE 0 END) AS filas_canceladas
    FROM Base
    GROUP BY COALESCE(unidad_negocio_id, SIN_UNIDAD)
),
OriginCoverage AS (
    SELECT
        COALESCE(sistema_origen, SIN_ORIGEN) AS origen,
        COUNT_BIG(*) AS filas,
        MIN(fecha_operacion) AS fecha_min,
        MAX(fecha_operacion) AS fecha_max
    FROM Base
    GROUP BY COALESCE(sistema_origen, SIN_ORIGEN)
),
FamilyCoverage AS (
    SELECT TOP (30)
        COALESCE(familia_nombre, SIN_FAMILIA) AS familia,
        COALESCE(subfamilia_nombre, SIN_SUBFAMILIA) AS subfamilia,
        COUNT_BIG(*) AS filas,
        SUM(CASE WHEN es_alcohol = 1 THEN 1 ELSE 0 END) AS filas_alcohol,
        SUM(COALESCE(importe_neto, 0)) AS importe_neto
    FROM Base
    GROUP BY
        COALESCE(familia_nombre, SIN_FAMILIA),
        COALESCE(subfamilia_nombre, SIN_SUBFAMILIA)
    ORDER BY COUNT_BIG(*) DESC
)
SELECT seccion, clave_1, clave_2, valor
FROM (
    SELECT
        GENERAL AS seccion,
        FILAS AS clave_1,
         AS clave_2,
        CONVERT(nvarchar(100), COUNT_BIG(*)) AS valor
    FROM Base

    UNION ALL
    SELECT GENERAL, FECHA_MIN, ,
        CONVERT(nvarchar(100), MIN(fecha_operacion), 23)
    FROM Base

    UNION ALL
    SELECT GENERAL, FECHA_MAX, ,
        CONVERT(nvarchar(100), MAX(fecha_operacion), 23)
    FROM Base

    UNION ALL
    SELECT GENERAL, TICKETS_DISTINTOS, ,
        CONVERT(nvarchar(100), COUNT(DISTINCT numero_ticket))
    FROM Base

    UNION ALL
    SELECT CALIDAD, FECHA_HORA_NULL, ,
        CONVERT(nvarchar(100), SUM(CASE WHEN fecha_hora IS NULL THEN 1 ELSE 0 END))
    FROM Base

    UNION ALL
    SELECT CALIDAD, FAMILIA_NULL, ,
        CONVERT(nvarchar(100), SUM(CASE WHEN familia_nombre IS NULL THEN 1 ELSE 0 END))
    FROM Base

    UNION ALL
    SELECT CALIDAD, IMPORTE_NETO_NULL, ,
        CONVERT(nvarchar(100), SUM(CASE WHEN importe_neto IS NULL THEN 1 ELSE 0 END))
    FROM Base

    UNION ALL
    SELECT CALIDAD, KPI_VALIDO, ,
        CONVERT(nvarchar(100), SUM(CASE WHEN es_kpi_valido = 1 THEN 1 ELSE 0 END))
    FROM Base

    UNION ALL
    SELECT CALIDAD, CANCELADAS, ,
        CONVERT(nvarchar(100), SUM(CASE WHEN cancelado_origen = 1 THEN 1 ELSE 0 END))
    FROM Base

    UNION ALL
    SELECT
        UNIDAD,
        unidad,
        CONCAT(CONVERT(nvarchar(10), fecha_min, 23), |,
               CONVERT(nvarchar(10), fecha_max, 23)),
        CONCAT(filas=, filas,
               ;dias=, dias,
               ;tickets=, tickets,
               ;hora_null=, fecha_hora_null,
               ;validas=, filas_validas,
               ;canceladas=, filas_canceladas)
    FROM UnitCoverage

    UNION ALL
    SELECT
        ORIGEN,
        origen,
        CONCAT(CONVERT(nvarchar(10), fecha_min, 23), |,
               CONVERT(nvarchar(10), fecha_max, 23)),
        CONCAT(filas=, filas)
    FROM OriginCoverage

    UNION ALL
    SELECT
        FAMILIA,
        familia,
        subfamilia,
        CONCAT(filas=, filas,
               ;alcohol=, filas_alcohol,
               ;importe_neto=, CONVERT(nvarchar(100), importe_neto))
    FROM FamilyCoverage
) AS Resultado
ORDER BY seccion, clave_1, clave_2;

```