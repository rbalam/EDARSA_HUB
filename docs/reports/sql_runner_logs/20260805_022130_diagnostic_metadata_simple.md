# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:21:30.373631
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_intraday_metadata_simple_20260805T022129Z/metadata_simple.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, login_name, database_user
- Filas: 1
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura'}
```


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