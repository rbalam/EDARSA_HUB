# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:42:54.252473
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_historical_columns_atomic_20260805T024254Z/historical_columns_atomic.sql`

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
    s.name AS schema_name,
    o.name AS object_name,
    COUNT(*) AS column_count,
    STRING_AGG(
        CAST(
            CAST(c.column_id AS nvarchar(10))
            + N':' + c.name
            + N':' + t.name
            + N':' +
            CASE
                WHEN c.is_nullable = 1 THEN N'NULL'
                ELSE N'NOT_NULL'
            END
            AS nvarchar(max)
        ),
        N' | '
    ) WITHIN GROUP (
        ORDER BY c.column_id
    ) AS columns_definition
FROM sys.objects AS o
INNER JOIN sys.schemas AS s
    ON s.schema_id = o.schema_id
INNER JOIN sys.columns AS c
    ON c.object_id = o.object_id
INNER JOIN sys.types AS t
    ON t.user_type_id = c.user_type_id
WHERE
    s.name = N'dbo'
    AND o.name IN (
        N'Sync_Sales',
        N'Comercial_KPIs_Diarios_v2',
        N'Comercial_KPIs_Historico'
    )
GROUP BY
    s.name,
    o.name
ORDER BY
    CASE o.name
        WHEN N'Sync_Sales' THEN 1
        WHEN N'Comercial_KPIs_Diarios_v2' THEN 2
        WHEN N'Comercial_KPIs_Historico' THEN 3
        ELSE 99
    END;

```