# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:50:57.860926
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_capacity_source_audit_20260805T025056Z/capacity_sources.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Dry-run ejecutado. No se aplicaron cambios.


## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

SELECT TOP (80)
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

    MAX(
        CASE
            WHEN LOWER(c.name) LIKE '%capacidad%'
              OR LOWER(c.name) LIKE '%aforo%'
              OR LOWER(c.name) LIKE '%asiento%'
              OR LOWER(c.name) LIKE '%silla%'
            THEN 1 ELSE 0
        END
    ) AS has_capacidad,

    MAX(
        CASE
            WHEN LOWER(c.name) LIKE '%mesa%'
            THEN 1 ELSE 0
        END
    ) AS has_mesas,

    MAX(
        CASE
            WHEN LOWER(c.name) LIKE '%unidad%'
              OR LOWER(c.name) LIKE '%sucursal%'
              OR LOWER(c.name) LIKE '%server%'
            THEN 1 ELSE 0
        END
    ) AS has_unidad,

    MAX(
        CASE
            WHEN LOWER(c.name) LIKE '%fecha%'
              OR LOWER(c.name) LIKE '%vigencia%'
              OR LOWER(c.name) LIKE '%desde%'
              OR LOWER(c.name) LIKE '%hasta%'
            THEN 1 ELSE 0
        END
    ) AS has_vigencia,

    MAX(
        CASE
            WHEN LOWER(c.name) LIKE '%pax%'
              OR LOWER(c.name) LIKE '%comensal%'
            THEN 1 ELSE 0
        END
    ) AS has_pax

FROM sys.objects AS o
INNER JOIN sys.schemas AS s
    ON s.schema_id = o.schema_id
INNER JOIN sys.columns AS c
    ON c.object_id = o.object_id

WHERE
    o.type IN ('U', 'V')
    AND o.is_ms_shipped = 0
    AND (
           LOWER(o.name) LIKE '%mesa%'
        OR LOWER(o.name) LIKE '%capacidad%'
        OR LOWER(o.name) LIKE '%aforo%'
        OR LOWER(c.name) LIKE '%capacidad%'
        OR LOWER(c.name) LIKE '%aforo%'
        OR LOWER(c.name) LIKE '%asiento%'
        OR LOWER(c.name) LIKE '%silla%'
        OR LOWER(c.name) LIKE '%mesa%'
    )

GROUP BY
    s.name,
    o.name,
    o.type_desc,
    o.object_id

HAVING
    MAX(
        CASE
            WHEN LOWER(c.name) LIKE '%capacidad%'
              OR LOWER(c.name) LIKE '%aforo%'
              OR LOWER(c.name) LIKE '%asiento%'
              OR LOWER(c.name) LIKE '%silla%'
              OR LOWER(c.name) LIKE '%mesa%'
            THEN 1 ELSE 0
        END
    ) = 1

ORDER BY
    CASE
        WHEN (
            SELECT SUM(ps.row_count)
            FROM sys.dm_db_partition_stats AS ps
            WHERE ps.object_id = o.object_id
              AND ps.index_id IN (0, 1)
        ) > 0 THEN 0
        ELSE 1
    END,
    has_unidad DESC,
    has_vigencia DESC,
    has_capacidad DESC,
    has_mesas DESC,
    approximate_rows DESC,
    s.name,
    o.name;

```