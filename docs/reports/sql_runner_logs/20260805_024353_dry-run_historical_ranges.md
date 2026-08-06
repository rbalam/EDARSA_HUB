# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:43:53.332332
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_historical_ranges_20260805T024353Z/historical_ranges.sql`

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