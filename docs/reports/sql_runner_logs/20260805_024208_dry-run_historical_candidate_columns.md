# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:42:08.105950
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_historical_columns_20260805T024207Z/historical_candidate_columns.sql`

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
    c.column_id,
    c.name AS column_name,
    t.name AS data_type,
    c.is_nullable
FROM sys.objects AS o
INNER JOIN sys.schemas AS s
    ON s.schema_id = o.schema_id
INNER JOIN sys.columns AS c
    ON c.object_id = o.object_id
INNER JOIN sys.types AS t
    ON t.user_type_id = c.user_type_id
WHERE
    s.name = 'dbo'
    AND o.name IN (
        'Sync_Sales',
        'Comercial_KPIs_Diarios_v2',
        'Comercial_KPIs_Historico'
    )
    AND (
           LOWER(c.name) LIKE '%fecha%'
        OR LOWER(c.name) LIKE '%hora%'
        OR LOWER(c.name) LIKE '%unidad%'
        OR LOWER(c.name) LIKE '%sucursal%'
        OR LOWER(c.name) LIKE '%server%'
        OR LOWER(c.name) LIKE '%origen%'
        OR LOWER(c.name) LIKE '%venta%'
        OR LOWER(c.name) LIKE '%total%'
        OR LOWER(c.name) LIKE '%ticket%'
        OR LOWER(c.name) LIKE '%cheq%'
        OR LOWER(c.name) LIKE '%pax%'
        OR LOWER(c.name) LIKE '%producto%'
    )
ORDER BY
    CASE o.name
        WHEN 'Sync_Sales' THEN 1
        WHEN 'Comercial_KPIs_Diarios_v2' THEN 2
        WHEN 'Comercial_KPIs_Historico' THEN 3
        ELSE 99
    END,
    c.column_id;

```