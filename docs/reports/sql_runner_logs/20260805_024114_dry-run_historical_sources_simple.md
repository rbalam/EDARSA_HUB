# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:41:14.392856
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_historical_sources_simple_20260805T024114Z/historical_sources_simple.sql`

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
    SUSER_SNAME() AS login_name,
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
            WHEN LOWER(c.name) LIKE '%fecha%'
            THEN 1 ELSE 0
        END
    ) AS has_fecha,

    MAX(
        CASE
            WHEN LOWER(c.name) LIKE '%hora%'
              OR LOWER(c.name) LIKE '%apertura%'
              OR LOWER(c.name) LIKE '%cierre%'
            THEN 1 ELSE 0
        END
    ) AS has_hora,

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
            WHEN LOWER(c.name) LIKE '%ticket%'
              OR LOWER(c.name) LIKE '%cheq%'
              OR LOWER(c.name) LIKE '%folio%'
              OR LOWER(c.name) LIKE '%comanda%'
            THEN 1 ELSE 0
        END
    ) AS has_ticket,

    MAX(
        CASE
            WHEN LOWER(c.name) LIKE '%producto%'
              OR LOWER(c.name) LIKE '%articulo%'
              OR LOWER(c.name) LIKE '%item%'
            THEN 1 ELSE 0
        END
    ) AS has_producto,

    MAX(
        CASE
            WHEN LOWER(c.name) LIKE '%familia%'
              OR LOWER(c.name) LIKE '%categoria%'
              OR LOWER(c.name) LIKE '%clasif%'
            THEN 1 ELSE 0
        END
    ) AS has_familia,

    MAX(
        CASE
            WHEN LOWER(c.name) LIKE '%importe%'
              OR LOWER(c.name) LIKE '%venta%'
              OR LOWER(c.name) LIKE '%total%'
              OR LOWER(c.name) LIKE '%monto%'
            THEN 1 ELSE 0
        END
    ) AS has_importe,

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
           o.name IN (
               'Sync_Movimientos_Detalle',
               'Sync_Sales',
               'View_Sync_Sales_Detalle',
               'Vw_Sync_Sales_Unified',
               'View_Inteligencia_Comercial',
               'Comercial_KPIs_Diarios_v2',
               'vw_Comercial_KPIs_Diarios_v2_Runtime',
               'Comercial_Inteligencia_VentasDetalleProducto'
           )
        OR LOWER(o.name) LIKE '%histor%'
        OR LOWER(o.name) LIKE '%venta%detalle%'
        OR LOWER(o.name) LIKE '%sales%'
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