# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:36:00.756374
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_intraday_index_simple_20260805T023600Z/index_columns.sql`

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
    s.name AS schema_name,
    o.name AS object_name,
    (
        SELECT SUM(ps.row_count)
        FROM sys.dm_db_partition_stats AS ps
        WHERE ps.object_id = o.object_id
          AND ps.index_id IN (0, 1)
    ) AS approximate_rows,
    i.index_id,
    COALESCE(i.name, 'HEAP') AS index_name,
    i.type_desc AS index_type,
    i.is_unique,
    i.is_primary_key,
    ic.key_ordinal,
    ic.index_column_id,
    ic.is_included_column,
    c.column_id,
    c.name AS column_name
FROM sys.objects AS o
INNER JOIN sys.schemas AS s
    ON s.schema_id = o.schema_id
INNER JOIN sys.indexes AS i
    ON i.object_id = o.object_id
LEFT JOIN sys.index_columns AS ic
    ON ic.object_id = i.object_id
   AND ic.index_id = i.index_id
LEFT JOIN sys.columns AS c
    ON c.object_id = ic.object_id
   AND c.column_id = ic.column_id
WHERE
    s.name = 'dbo'
    AND o.name = 'Comercial_Inteligencia_VentasDetalleProducto'
    AND o.type = 'U'
ORDER BY
    i.index_id,
    ic.is_included_column,
    ic.key_ordinal,
    ic.index_column_id;

```