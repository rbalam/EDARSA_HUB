# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:42:08.800924
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_historical_columns_20260805T024207Z/historical_candidate_columns.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, schema_name, object_name, column_id, column_name, data_type, is_nullable
- Filas: 40
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Sync_Sales', 'column_id': 5, 'column_name': 'total', 'data_type': 'numeric', 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Sync_Sales', 'column_id': 12, 'column_name': 'UnidadNegocio', 'data_type': 'nvarchar', 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Sync_Sales', 'column_id': 13, 'column_name': 'MontoTotal', 'data_type': 'numeric', 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Sync_Sales', 'column_id': 14, 'column_name': 'Pax', 'data_type': 'int', 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Sync_Sales', 'column_id': 15, 'column_name': 'NumeroTicket', 'data_type': 'varchar', 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Sync_Sales', 'column_id': 16, 'column_name': 'FechaHora', 'data_type': 'datetime', 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Comercial_KPIs_Diarios_v2', 'column_id': 2, 'column_name': 'unidad_negocio_id', 'data_type': 'nvarchar', 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Comercial_KPIs_Diarios_v2', 'column_id': 3, 'column_name': 'unidad_negocio_nombre', 'data_type': 'nvarchar', 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Comercial_KPIs_Diarios_v2', 'column_id': 4, 'column_name': 'server_id', 'data_type': 'nvarchar', 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Comercial_KPIs_Diarios_v2', 'column_id': 5, 'column_name': 'sucursal_id', 'data_type': 'nvarchar', 'is_nullable': False}
```


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