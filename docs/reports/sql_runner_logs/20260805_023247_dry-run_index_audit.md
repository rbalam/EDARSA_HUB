# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:32:47.580071
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_intraday_index_audit_20260805T023247Z/index_audit.sql`

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
    SUM(CASE WHEN p.index_id IN (0, 1) THEN p.rows ELSE 0 END)
        AS approximate_rows,
    CAST(
        SUM(a.total_pages) * 8.0 / 1024.0
        AS decimal(18, 2)
    ) AS total_size_mb,
    i.index_id,
    COALESCE(i.name, HEAP) AS index_name,
    i.type_desc AS index_type,
    i.is_unique,
    i.is_primary_key,
    STRING_AGG(
        CAST(
            CONCAT(
                ic.key_ordinal, :,
                c.name, :,
                CASE
                    WHEN ic.is_included_column = 1
                    THEN INCLUDE
                    ELSE KEY
                END
            ) AS nvarchar(max)
        ),
         | 
    ) WITHIN GROUP (
        ORDER BY
            ic.is_included_column,
            ic.key_ordinal,
            ic.index_column_id
    ) AS index_columns
FROM sys.objects AS o
INNER JOIN sys.schemas AS s
    ON s.schema_id = o.schema_id
INNER JOIN sys.indexes AS i
    ON i.object_id = o.object_id
INNER JOIN sys.partitions AS p
    ON p.object_id = i.object_id
    AND p.index_id = i.index_id
INNER JOIN sys.allocation_units AS a
    ON a.container_id = p.partition_id
LEFT JOIN sys.index_columns AS ic
    ON ic.object_id = i.object_id
    AND ic.index_id = i.index_id
LEFT JOIN sys.columns AS c
    ON c.object_id = ic.object_id
    AND c.column_id = ic.column_id
WHERE
    s.name = dbo
    AND o.name = Comercial_Inteligencia_VentasDetalleProducto
    AND o.type = U
GROUP BY
    s.name,
    o.name,
    i.index_id,
    i.name,
    i.type_desc,
    i.is_unique,
    i.is_primary_key
ORDER BY
    i.index_id;

```