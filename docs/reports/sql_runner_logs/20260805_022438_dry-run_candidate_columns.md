# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:24:38.443444
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_intraday_candidate_columns_20260805T022438Z/candidate_columns.sql`

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
    s.name = 'dbo'
    AND o.name IN (
        'Comercial_Inteligencia_VentasDetalleProducto',
        'Sync_Movimientos_Detalle',
        'Sync_Sales',
        'Sync_PAX_Detalle',
        'Sync_Mesas',
        'View_Inteligencia_Comercial'
    )
ORDER BY
    CASE o.name
        WHEN 'Comercial_Inteligencia_VentasDetalleProducto' THEN 1
        WHEN 'Sync_Movimientos_Detalle' THEN 2
        WHEN 'Sync_Sales' THEN 3
        WHEN 'Sync_PAX_Detalle' THEN 4
        WHEN 'Sync_Mesas' THEN 5
        WHEN 'View_Inteligencia_Comercial' THEN 6
        ELSE 99
    END,
    c.column_id;

```