# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:37:54.901012
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_historical_coverage_20260805T023754Z/01_global_range.sql`

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
    SUSER_SNAME() AS login_name,
    (
        SELECT TOP (1) fecha_operacion
        FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
        ORDER BY fecha_operacion ASC
    ) AS fecha_min,
    (
        SELECT TOP (1) fecha_operacion
        FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
        ORDER BY fecha_operacion DESC
    ) AS fecha_max,
    (
        SELECT SUM(row_count)
        FROM sys.dm_db_partition_stats
        WHERE object_id = OBJECT_ID(
            'dbo.Comercial_Inteligencia_VentasDetalleProducto'
        )
        AND index_id IN (0, 1)
    ) AS filas_aproximadas;

```