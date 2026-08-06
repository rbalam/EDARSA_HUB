# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:37:55.791782
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_historical_coverage_20260805T023754Z/02_unit_year_coverage.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Dry-run ejecutado. No se aplicaron cambios.


## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

SELECT
    DB_NAME() AS database_name,
    YEAR(fecha_operacion) AS anio,
    COALESCE(unidad_negocio_id, 'SIN_UNIDAD') AS unidad_id,
    COALESCE(unidad_negocio_nombre, 'SIN_NOMBRE') AS unidad_nombre,
    MIN(fecha_operacion) AS fecha_min,
    MAX(fecha_operacion) AS fecha_max,
    COUNT_BIG(*) AS filas,
    SUM(CASE WHEN fecha_hora IS NULL THEN 1 ELSE 0 END)
        AS fecha_hora_null,
    SUM(CASE WHEN familia_nombre IS NULL THEN 1 ELSE 0 END)
        AS familia_null,
    SUM(CASE WHEN importe_neto IS NULL THEN 1 ELSE 0 END)
        AS importe_neto_null,
    SUM(CASE WHEN es_kpi_valido = 1 THEN 1 ELSE 0 END)
        AS filas_kpi_validas,
    SUM(CASE WHEN cancelado_origen = 1 THEN 1 ELSE 0 END)
        AS filas_canceladas,
    SUM(CASE WHEN activo = 1 THEN 1 ELSE 0 END)
        AS filas_activas
FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
GROUP BY
    YEAR(fecha_operacion),
    COALESCE(unidad_negocio_id, 'SIN_UNIDAD'),
    COALESCE(unidad_negocio_nombre, 'SIN_NOMBRE')
ORDER BY
    anio,
    unidad_nombre;

```