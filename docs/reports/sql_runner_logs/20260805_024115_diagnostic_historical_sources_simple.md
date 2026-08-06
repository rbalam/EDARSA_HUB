# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:41:15.157197
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_historical_sources_simple_20260805T024114Z/historical_sources_simple.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, login_name, schema_name, object_name, object_type, approximate_rows, column_count, has_fecha, has_hora, has_unidad, has_ticket, has_producto, has_familia, has_importe, has_pax
- Filas: 46
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'object_type': 'USER_TABLE', 'approximate_rows': 1249822, 'column_count': 38, 'has_fecha': 1, 'has_hora': 1, 'has_unidad': 1, 'has_ticket': 1, 'has_producto': 1, 'has_familia': 1, 'has_importe': 1, 'has_pax': 1}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Compras_Inventarios_Fisicos_Detalle_Sync', 'object_type': 'USER_TABLE', 'approximate_rows': 201483, 'column_count': 27, 'has_fecha': 1, 'has_hora': 0, 'has_unidad': 1, 'has_ticket': 1, 'has_producto': 1, 'has_familia': 0, 'has_importe': 1, 'has_pax': 0}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Inventario_MovimientosDetalle', 'object_type': 'USER_TABLE', 'approximate_rows': 171562, 'column_count': 12, 'has_fecha': 1, 'has_hora': 0, 'has_unidad': 0, 'has_ticket': 0, 'has_producto': 1, 'has_familia': 0, 'has_importe': 1, 'has_pax': 0}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Sales', 'object_type': 'USER_TABLE', 'approximate_rows': 112362, 'column_count': 18, 'has_fecha': 1, 'has_hora': 1, 'has_unidad': 1, 'has_ticket': 1, 'has_producto': 1, 'has_familia': 0, 'has_importe': 1, 'has_pax': 1}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_KPIs_Diarios_v2', 'object_type': 'USER_TABLE', 'approximate_rows': 9657, 'column_count': 34, 'has_fecha': 1, 'has_hora': 0, 'has_unidad': 1, 'has_ticket': 1, 'has_producto': 0, 'has_familia': 0, 'has_importe': 1, 'has_pax': 1}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Compras_KPIs_Historico', 'object_type': 'USER_TABLE', 'approximate_rows': 7035, 'column_count': 23, 'has_fecha': 1, 'has_hora': 0, 'has_unidad': 1, 'has_ticket': 0, 'has_producto': 1, 'has_familia': 0, 'has_importe': 1, 'has_pax': 0}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Precios_Historicos', 'object_type': 'USER_TABLE', 'approximate_rows': 5642, 'column_count': 18, 'has_fecha': 1, 'has_hora': 0, 'has_unidad': 1, 'has_ticket': 0, 'has_producto': 1, 'has_familia': 0, 'has_importe': 0, 'has_pax': 0}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Finanzas_KPIs_Historico', 'object_type': 'USER_TABLE', 'approximate_rows': 4707, 'column_count': 30, 'has_fecha': 1, 'has_hora': 0, 'has_unidad': 1, 'has_ticket': 0, 'has_producto': 0, 'has_familia': 0, 'has_importe': 1, 'has_pax': 0}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_KPIs_Historico', 'object_type': 'USER_TABLE', 'approximate_rows': 3647, 'column_count': 22, 'has_fecha': 1, 'has_hora': 0, 'has_unidad': 1, 'has_ticket': 1, 'has_producto': 0, 'has_familia': 0, 'has_importe': 1, 'has_pax': 1}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'SesionesHistorico', 'object_type': 'USER_TABLE', 'approximate_rows': 2658, 'column_count': 10, 'has_fecha': 1, 'has_hora': 0, 'has_unidad': 0, 'has_ticket': 0, 'has_producto': 0, 'has_familia': 0, 'has_importe': 0, 'has_pax': 0}
```


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