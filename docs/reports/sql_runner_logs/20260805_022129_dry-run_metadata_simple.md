# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:21:29.313702
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_intraday_metadata_simple_20260805T022129Z/metadata_simple.sql`

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
    USER_NAME() AS database_user;

SELECT TOP (300)
    s.name AS schema_name,
    o.name AS object_name,
    o.type_desc AS object_type,
    c.column_id,
    c.name AS column_name,
    t.name AS data_type,
    c.max_length,
    c.precision,
    c.scale,
    c.is_nullable
FROM sys.objects AS o
INNER JOIN sys.schemas AS s
    ON s.schema_id = o.schema_id
INNER JOIN sys.columns AS c
    ON c.object_id = o.object_id
INNER JOIN sys.types AS t
    ON t.user_type_id = c.user_type_id
WHERE
    o.type IN ('U', 'V')
    AND o.is_ms_shipped = 0
    AND (
           LOWER(o.name) LIKE '%venta%'
        OR LOWER(o.name) LIKE '%cheq%'
        OR LOWER(o.name) LIKE '%ticket%'
        OR LOWER(o.name) LIKE '%comanda%'
        OR LOWER(o.name) LIKE '%producto%'
        OR LOWER(o.name) LIKE '%detalle%'
        OR LOWER(c.name) LIKE '%fecha%'
        OR LOWER(c.name) LIKE '%hora%'
        OR LOWER(c.name) LIKE '%cheq%'
        OR LOWER(c.name) LIKE '%ticket%'
        OR LOWER(c.name) LIKE '%comanda%'
        OR LOWER(c.name) LIKE '%producto%'
        OR LOWER(c.name) LIKE '%articulo%'
        OR LOWER(c.name) LIKE '%clasif%'
        OR LOWER(c.name) LIKE '%categoria%'
        OR LOWER(c.name) LIKE '%familia%'
        OR LOWER(c.name) LIKE '%alimento%'
        OR LOWER(c.name) LIKE '%bebida%'
        OR LOWER(c.name) LIKE '%pax%'
        OR LOWER(c.name) LIKE '%persona%'
        OR LOWER(c.name) LIKE '%unidad%'
        OR LOWER(c.name) LIKE '%sucursal%'
        OR LOWER(c.name) LIKE '%importe%'
        OR LOWER(c.name) LIKE '%subtotal%'
        OR LOWER(c.name) LIKE '%total%'
    )
ORDER BY
    s.name,
    o.name,
    c.column_id;

```