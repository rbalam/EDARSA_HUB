# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:47:22.005860
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_capacity_inventory_20260805T024721Z/capacity_inventory.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Dry-run ejecutado. No se aplicaron cambios.


## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

SELECT TOP (100)
    DB_NAME() AS database_name,
    s.name AS schema_name,
    o.name AS object_name,
    o.type_desc AS object_type,
    COUNT(c.column_id) AS column_count,
    MAX(CASE WHEN LOWER(c.name) LIKE '%mesa%' THEN 1 ELSE 0 END)
        AS has_mesas,
    MAX(CASE
        WHEN LOWER(c.name) LIKE '%asiento%'
          OR LOWER(c.name) LIKE '%silla%'
        THEN 1 ELSE 0 END) AS has_asientos,
    MAX(CASE
        WHEN LOWER(c.name) LIKE '%pax%'
          OR LOWER(c.name) LIKE '%comensal%'
        THEN 1 ELSE 0 END) AS has_pax,
    MAX(CASE
        WHEN LOWER(c.name) LIKE '%aforo%'
          OR LOWER(c.name) LIKE '%capacidad%'
        THEN 1 ELSE 0 END) AS has_capacidad,
    MAX(CASE
        WHEN LOWER(c.name) LIKE '%area%'
          OR LOWER(c.name) LIKE '%salon%'
          OR LOWER(c.name) LIKE '%terraza%'
        THEN 1 ELSE 0 END) AS has_area,
    MAX(CASE
        WHEN LOWER(c.name) LIKE '%fecha%'
          OR LOWER(c.name) LIKE '%vigencia%'
          OR LOWER(c.name) LIKE '%desde%'
          OR LOWER(c.name) LIKE '%hasta%'
        THEN 1 ELSE 0 END) AS has_vigencia,
    MAX(CASE
        WHEN LOWER(c.name) LIKE '%unidad%'
          OR LOWER(c.name) LIKE '%sucursal%'
        THEN 1 ELSE 0 END) AS has_unidad
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
        OR LOWER(o.name) LIKE '%aforo%'
        OR LOWER(o.name) LIKE '%capacidad%'
        OR LOWER(o.name) LIKE '%salon%'
        OR LOWER(o.name) LIKE '%area%'
        OR LOWER(c.name) LIKE '%mesa%'
        OR LOWER(c.name) LIKE '%asiento%'
        OR LOWER(c.name) LIKE '%silla%'
        OR LOWER(c.name) LIKE '%aforo%'
        OR LOWER(c.name) LIKE '%capacidad%'
    )
GROUP BY
    s.name,
    o.name,
    o.type_desc
ORDER BY
    has_capacidad DESC,
    has_mesas DESC,
    has_asientos DESC,
    has_vigencia DESC,
    s.name,
    o.name;

```