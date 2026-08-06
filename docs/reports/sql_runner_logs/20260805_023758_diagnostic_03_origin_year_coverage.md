# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:37:58.074768
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_historical_coverage_20260805T023754Z/03_origin_year_coverage.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, anio, sistema_origen, fuente_original, fecha_min, fecha_max, filas, fecha_hora_null, filas_kpi_validas, filas_canceladas
- Filas: 6
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'anio': 2024, 'sistema_origen': 'MPRO', 'fuente_original': 'SIN_FUENTE', 'fecha_min': datetime.date(2024, 6, 1), 'fecha_max': datetime.date(2024, 12, 31), 'filas': 121816, 'fecha_hora_null': 0, 'filas_kpi_validas': 121816, 'filas_canceladas': 0}
  {'database_name': 'EDARSAHUB', 'anio': 2024, 'sistema_origen': 'SoftRestaurant', 'fuente_original': 'SIN_FUENTE', 'fecha_min': datetime.date(2024, 6, 1), 'fecha_max': datetime.date(2024, 12, 31), 'filas': 236196, 'fecha_hora_null': 0, 'filas_kpi_validas': 236196, 'filas_canceladas': 0}
  {'database_name': 'EDARSAHUB', 'anio': 2025, 'sistema_origen': 'MPRO', 'fuente_original': 'SIN_FUENTE', 'fecha_min': datetime.date(2025, 1, 2), 'fecha_max': datetime.date(2025, 12, 31), 'filas': 198273, 'fecha_hora_null': 0, 'filas_kpi_validas': 198273, 'filas_canceladas': 0}
  {'database_name': 'EDARSAHUB', 'anio': 2025, 'sistema_origen': 'SoftRestaurant', 'fuente_original': 'SIN_FUENTE', 'fecha_min': datetime.date(2025, 1, 2), 'fecha_max': datetime.date(2025, 12, 31), 'filas': 415506, 'fecha_hora_null': 0, 'filas_kpi_validas': 415506, 'filas_canceladas': 0}
  {'database_name': 'EDARSAHUB', 'anio': 2026, 'sistema_origen': 'MPRO', 'fuente_original': 'SIN_FUENTE', 'fecha_min': datetime.date(2026, 1, 2), 'fecha_max': datetime.date(2026, 7, 7), 'filas': 100759, 'fecha_hora_null': 0, 'filas_kpi_validas': 100759, 'filas_canceladas': 0}
  {'database_name': 'EDARSAHUB', 'anio': 2026, 'sistema_origen': 'SoftRestaurant', 'fuente_original': 'SIN_FUENTE', 'fecha_min': datetime.date(2026, 1, 1), 'fecha_max': datetime.date(2026, 6, 6), 'filas': 177272, 'fecha_hora_null': 0, 'filas_kpi_validas': 177272, 'filas_canceladas': 0}
```


## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

SELECT
    DB_NAME() AS database_name,
    YEAR(fecha_operacion) AS anio,
    COALESCE(sistema_origen, 'SIN_ORIGEN') AS sistema_origen,
    COALESCE(fuente_original, 'SIN_FUENTE') AS fuente_original,
    MIN(fecha_operacion) AS fecha_min,
    MAX(fecha_operacion) AS fecha_max,
    COUNT_BIG(*) AS filas,
    SUM(CASE WHEN fecha_hora IS NULL THEN 1 ELSE 0 END)
        AS fecha_hora_null,
    SUM(CASE WHEN es_kpi_valido = 1 THEN 1 ELSE 0 END)
        AS filas_kpi_validas,
    SUM(CASE WHEN cancelado_origen = 1 THEN 1 ELSE 0 END)
        AS filas_canceladas
FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
GROUP BY
    YEAR(fecha_operacion),
    COALESCE(sistema_origen, 'SIN_ORIGEN'),
    COALESCE(fuente_original, 'SIN_FUENTE')
ORDER BY
    anio,
    sistema_origen,
    fuente_original;

```