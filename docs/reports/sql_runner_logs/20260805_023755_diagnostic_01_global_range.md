# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:37:55.596194
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_historical_coverage_20260805T023754Z/01_global_range.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, login_name, fecha_min, fecha_max, filas_aproximadas
- Filas: 1
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'fecha_min': datetime.date(2024, 6, 1), 'fecha_max': datetime.date(2026, 7, 7), 'filas_aproximadas': 1249822}
```


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