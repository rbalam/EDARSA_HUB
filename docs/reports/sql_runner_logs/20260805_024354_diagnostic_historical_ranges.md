# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:43:54.288814
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_historical_ranges_20260805T024353Z/historical_ranges.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, login_name, fuente, nivel_dato, fecha_min, fecha_max, filas, fechas_nulas, unidades_distintas, anios_distintos
- Filas: 3
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'fuente': 'Comercial_KPIs_Diarios_v2', 'nivel_dato': 'KPI_DIARIO_CANONICO', 'fecha_min': datetime.date(2016, 6, 14), 'fecha_max': datetime.date(2026, 8, 4), 'filas': 9657, 'fechas_nulas': 0, 'unidades_distintas': 5, 'anios_distintos': 11}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'fuente': 'Comercial_KPIs_Historico', 'nivel_dato': 'KPI_HISTORICO_AGREGADO', 'fecha_min': datetime.date(2024, 5, 6), 'fecha_max': datetime.date(2026, 4, 26), 'filas': 3647, 'fechas_nulas': 0, 'unidades_distintas': 1, 'anios_distintos': 3}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'fuente': 'Sync_Sales', 'nivel_dato': 'DETALLE_INTRADIA', 'fecha_min': datetime.date(2024, 6, 1), 'fecha_max': datetime.date(2026, 7, 26), 'filas': 112362, 'fechas_nulas': 0, 'unidades_distintas': 5, 'anios_distintos': 3}
```


## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

SELECT
    DB_NAME() AS database_name,
    SUSER_SNAME() AS login_name,
    fuente,
    nivel_dato,
    fecha_min,
    fecha_max,
    filas,
    fechas_nulas,
    unidades_distintas,
    anios_distintos
FROM (
    SELECT
        CAST('Sync_Sales' AS nvarchar(100)) AS fuente,
        CAST('DETALLE_INTRADIA' AS nvarchar(40)) AS nivel_dato,
        MIN(CAST(FechaHora AS date)) AS fecha_min,
        MAX(CAST(FechaHora AS date)) AS fecha_max,
        COUNT_BIG(*) AS filas,
        SUM(CASE WHEN FechaHora IS NULL THEN 1 ELSE 0 END)
            AS fechas_nulas,
        COUNT(DISTINCT UnidadNegocio) AS unidades_distintas,
        COUNT(DISTINCT YEAR(FechaHora)) AS anios_distintos
    FROM dbo.Sync_Sales

    UNION ALL

    SELECT
        CAST('Comercial_KPIs_Diarios_v2' AS nvarchar(100)),
        CAST('KPI_DIARIO_CANONICO' AS nvarchar(40)),
        MIN(fecha_operacion),
        MAX(fecha_operacion),
        COUNT_BIG(*),
        SUM(CASE WHEN fecha_operacion IS NULL THEN 1 ELSE 0 END),
        COUNT(DISTINCT unidad_negocio_id),
        COUNT(DISTINCT YEAR(fecha_operacion))
    FROM dbo.Comercial_KPIs_Diarios_v2

    UNION ALL

    SELECT
        CAST('Comercial_KPIs_Historico' AS nvarchar(100)),
        CAST('KPI_HISTORICO_AGREGADO' AS nvarchar(40)),
        MIN(fecha),
        MAX(fecha),
        COUNT_BIG(*),
        SUM(CASE WHEN fecha IS NULL THEN 1 ELSE 0 END),
        COUNT(DISTINCT unidad_negocio_id),
        COUNT(DISTINCT YEAR(fecha))
    FROM dbo.Comercial_KPIs_Historico
) AS fuentes
ORDER BY fuente;

```