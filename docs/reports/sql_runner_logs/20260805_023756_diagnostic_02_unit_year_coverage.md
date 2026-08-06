# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:37:56.854397
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_historical_coverage_20260805T023754Z/02_unit_year_coverage.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, anio, unidad_id, unidad_nombre, fecha_min, fecha_max, filas, fecha_hora_null, familia_null, importe_neto_null, filas_kpi_validas, filas_canceladas, filas_activas
- Filas: 14
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'anio': 2024, 'unidad_id': '130MID', 'unidad_nombre': '130° MERIDA', 'fecha_min': datetime.date(2024, 6, 1), 'fecha_max': datetime.date(2024, 12, 31), 'filas': 95812, 'fecha_hora_null': 0, 'familia_null': 0, 'importe_neto_null': 0, 'filas_kpi_validas': 95812, 'filas_canceladas': 0, 'filas_activas': 95812}
  {'database_name': 'EDARSAHUB', 'anio': 2024, 'unidad_id': '130QRO', 'unidad_nombre': '130° QUERETARO', 'fecha_min': datetime.date(2024, 6, 1), 'fecha_max': datetime.date(2024, 12, 31), 'filas': 59461, 'fecha_hora_null': 0, 'familia_null': 0, 'importe_neto_null': 0, 'filas_kpi_validas': 59461, 'filas_canceladas': 0, 'filas_activas': 59461}
  {'database_name': 'EDARSAHUB', 'anio': 2024, 'unidad_id': 'CIENFUEGOS', 'unidad_nombre': 'CIENFUEGOS', 'fecha_min': datetime.date(2024, 6, 1), 'fecha_max': datetime.date(2024, 12, 31), 'filas': 140384, 'fecha_hora_null': 0, 'familia_null': 0, 'importe_neto_null': 132, 'filas_kpi_validas': 140384, 'filas_canceladas': 0, 'filas_activas': 140384}
  {'database_name': 'EDARSAHUB', 'anio': 2024, 'unidad_id': 'ORIGEN', 'unidad_nombre': 'ORIGEN', 'fecha_min': datetime.date(2024, 6, 1), 'fecha_max': datetime.date(2024, 12, 31), 'filas': 62355, 'fecha_hora_null': 0, 'familia_null': 0, 'importe_neto_null': 0, 'filas_kpi_validas': 62355, 'filas_canceladas': 0, 'filas_activas': 62355}
  {'database_name': 'EDARSAHUB', 'anio': 2025, 'unidad_id': '130MID', 'unidad_nombre': '130° MERIDA', 'fecha_min': datetime.date(2025, 1, 2), 'fecha_max': datetime.date(2025, 12, 31), 'filas': 161077, 'fecha_hora_null': 0, 'familia_null': 0, 'importe_neto_null': 0, 'filas_kpi_validas': 161077, 'filas_canceladas': 0, 'filas_activas': 161077}
  {'database_name': 'EDARSAHUB', 'anio': 2025, 'unidad_id': '130QRO', 'unidad_nombre': '130° QUERETARO', 'fecha_min': datetime.date(2025, 1, 2), 'fecha_max': datetime.date(2025, 12, 31), 'filas': 99306, 'fecha_hora_null': 0, 'familia_null': 0, 'importe_neto_null': 0, 'filas_kpi_validas': 99306, 'filas_canceladas': 0, 'filas_activas': 99306}
  {'database_name': 'EDARSAHUB', 'anio': 2025, 'unidad_id': 'CIENFUEGOS', 'unidad_nombre': 'CIENFUEGOS', 'fecha_min': datetime.date(2025, 1, 2), 'fecha_max': datetime.date(2025, 12, 31), 'filas': 197842, 'fecha_hora_null': 0, 'familia_null': 0, 'importe_neto_null': 153, 'filas_kpi_validas': 197842, 'filas_canceladas': 0, 'filas_activas': 197842}
  {'database_name': 'EDARSAHUB', 'anio': 2025, 'unidad_id': 'ESTELAR', 'unidad_nombre': 'LA ESTELAR', 'fecha_min': datetime.date(2025, 6, 27), 'fecha_max': datetime.date(2025, 12, 31), 'filas': 56587, 'fecha_hora_null': 0, 'familia_null': 0, 'importe_neto_null': 0, 'filas_kpi_validas': 56587, 'filas_canceladas': 0, 'filas_activas': 56587}
  {'database_name': 'EDARSAHUB', 'anio': 2025, 'unidad_id': 'ORIGEN', 'unidad_nombre': 'ORIGEN', 'fecha_min': datetime.date(2025, 1, 2), 'fecha_max': datetime.date(2025, 12, 31), 'filas': 98967, 'fecha_hora_null': 0, 'familia_null': 0, 'importe_neto_null': 0, 'filas_kpi_validas': 98967, 'filas_canceladas': 0, 'filas_activas': 98967}
  {'database_name': 'EDARSAHUB', 'anio': 2026, 'unidad_id': '130MID', 'unidad_nombre': '130° MERIDA', 'fecha_min': datetime.date(2026, 1, 2), 'fecha_max': datetime.date(2026, 6, 6), 'filas': 66736, 'fecha_hora_null': 0, 'familia_null': 0, 'importe_neto_null': 0, 'filas_kpi_validas': 66736, 'filas_canceladas': 0, 'filas_activas': 66736}
```


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