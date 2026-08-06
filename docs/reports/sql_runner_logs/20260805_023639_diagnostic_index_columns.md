# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:36:39.193083
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_intraday_index_simple_20260805T023638Z/index_columns.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, login_name, schema_name, object_name, approximate_rows, index_id, index_name, index_type, is_unique, is_primary_key, key_ordinal, index_column_id, is_included_column, column_id, column_name
- Filas: 22
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'approximate_rows': 1249822, 'index_id': 1, 'index_name': 'PK__Comercia__3213E83F57351393', 'index_type': 'CLUSTERED', 'is_unique': True, 'is_primary_key': True, 'key_ordinal': 1, 'index_column_id': 1, 'is_included_column': False, 'column_id': 1, 'column_name': 'id'}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'approximate_rows': 1249822, 'index_id': 2, 'index_name': 'IX_Comercial_Intel_VentasDetalle_Fecha', 'index_type': 'NONCLUSTERED', 'is_unique': False, 'is_primary_key': False, 'key_ordinal': 1, 'index_column_id': 1, 'is_included_column': False, 'column_id': 8, 'column_name': 'fecha_operacion'}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'approximate_rows': 1249822, 'index_id': 3, 'index_name': 'IX_Comercial_Intel_VentasDetalle_Unidad', 'index_type': 'NONCLUSTERED', 'is_unique': False, 'is_primary_key': False, 'key_ordinal': 1, 'index_column_id': 1, 'is_included_column': False, 'column_id': 3, 'column_name': 'unidad_negocio_nombre'}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'approximate_rows': 1249822, 'index_id': 3, 'index_name': 'IX_Comercial_Intel_VentasDetalle_Unidad', 'index_type': 'NONCLUSTERED', 'is_unique': False, 'is_primary_key': False, 'key_ordinal': 2, 'index_column_id': 2, 'is_included_column': False, 'column_id': 8, 'column_name': 'fecha_operacion'}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'approximate_rows': 1249822, 'index_id': 4, 'index_name': 'IX_Comercial_Intel_VentasDetalle_Producto', 'index_type': 'NONCLUSTERED', 'is_unique': False, 'is_primary_key': False, 'key_ordinal': 1, 'index_column_id': 1, 'is_included_column': False, 'column_id': 12, 'column_name': 'producto_codigo_fuente'}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'approximate_rows': 1249822, 'index_id': 4, 'index_name': 'IX_Comercial_Intel_VentasDetalle_Producto', 'index_type': 'NONCLUSTERED', 'is_unique': False, 'is_primary_key': False, 'key_ordinal': 2, 'index_column_id': 2, 'is_included_column': False, 'column_id': 8, 'column_name': 'fecha_operacion'}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'approximate_rows': 1249822, 'index_id': 5, 'index_name': 'UX_Comercial_Intel_VentasDetalle_NoDup', 'index_type': 'NONCLUSTERED', 'is_unique': True, 'is_primary_key': False, 'key_ordinal': 1, 'index_column_id': 1, 'is_included_column': False, 'column_id': 11, 'column_name': 'id_transaccion'}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'approximate_rows': 1249822, 'index_id': 5, 'index_name': 'UX_Comercial_Intel_VentasDetalle_NoDup', 'index_type': 'NONCLUSTERED', 'is_unique': True, 'is_primary_key': False, 'key_ordinal': 2, 'index_column_id': 2, 'is_included_column': False, 'column_id': 10, 'column_name': 'numero_ticket'}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'approximate_rows': 1249822, 'index_id': 5, 'index_name': 'UX_Comercial_Intel_VentasDetalle_NoDup', 'index_type': 'NONCLUSTERED', 'is_unique': True, 'is_primary_key': False, 'key_ordinal': 3, 'index_column_id': 3, 'is_included_column': False, 'column_id': 12, 'column_name': 'producto_codigo_fuente'}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'approximate_rows': 1249822, 'index_id': 5, 'index_name': 'UX_Comercial_Intel_VentasDetalle_NoDup', 'index_type': 'NONCLUSTERED', 'is_unique': True, 'is_primary_key': False, 'key_ordinal': 4, 'index_column_id': 4, 'is_included_column': False, 'column_id': 8, 'column_name': 'fecha_operacion'}
```


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