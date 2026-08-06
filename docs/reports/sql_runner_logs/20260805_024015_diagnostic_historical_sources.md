# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:40:15.338913
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_historical_source_inventory_20260805T024014Z/historical_sources.sql`

## Resultado
ERROR

## Detalle
```text
Error ejecutando SQL. Se hizo rollback. Detalle: (102, b"Incorrect syntax near ':'.DB-Lib error message 20018, severity 15:\nGeneral SQL Server error: Check messages from the SQL Server\n")
```

## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

SELECT
    DB_NAME() AS database_name,
    s.name AS schema_name,
    o.name AS object_name,
    o.type_desc AS object_type,
    (
        SELECT SUM(ps.row_count)
        FROM sys.dm_db_partition_stats AS ps
        WHERE ps.object_id = o.object_id
          AND ps.index_id IN (0, 1)
    ) AS approximate_rows,
    COUNT(c.column_id) AS column_count,
    STRING_AGG(
        CAST(
            CONCAT(
                c.column_id, :,
                c.name, :,
                t.name
            ) AS nvarchar(max)
        ),
         | 
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
    o.type IN (U, V)
    AND o.is_ms_shipped = 0
    AND (
        o.name IN (
            Sync_Movimientos_Detalle,
            Sync_Sales,
            View_Sync_Sales_Detalle,
            Vw_Sync_Sales_Unified,
            View_Inteligencia_Comercial,
            Comercial_KPIs_Diarios_v2,
            vw_Comercial_KPIs_Diarios_v2_Runtime
        )
        OR LOWER(o.name) LIKE %histor%
        OR LOWER(o.name) LIKE %venta%detalle%
    )
GROUP BY
    s.name,
    o.name,
    o.type_desc,
    o.object_id
ORDER BY
    approximate_rows DESC,
    s.name,
    o.name;

```