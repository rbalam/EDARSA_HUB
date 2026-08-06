# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:24:39.163181
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_intraday_candidate_columns_20260805T022438Z/candidate_columns.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, login_name, schema_name, object_name, object_type, column_id, column_name, data_type, max_length, precision, scale, is_nullable
- Filas: 139
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'object_type': 'USER_TABLE', 'column_id': 1, 'column_name': 'id', 'data_type': 'uniqueidentifier', 'max_length': 16, 'precision': 0, 'scale': 0, 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'object_type': 'USER_TABLE', 'column_id': 2, 'column_name': 'unidad_negocio_id', 'data_type': 'nvarchar', 'max_length': 100, 'precision': 0, 'scale': 0, 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'object_type': 'USER_TABLE', 'column_id': 3, 'column_name': 'unidad_negocio_nombre', 'data_type': 'nvarchar', 'max_length': 200, 'precision': 0, 'scale': 0, 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'object_type': 'USER_TABLE', 'column_id': 4, 'column_name': 'server_id', 'data_type': 'nvarchar', 'max_length': 100, 'precision': 0, 'scale': 0, 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'object_type': 'USER_TABLE', 'column_id': 5, 'column_name': 'sucursal_id', 'data_type': 'nvarchar', 'max_length': 100, 'precision': 0, 'scale': 0, 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'object_type': 'USER_TABLE', 'column_id': 6, 'column_name': 'sucursal_nombre', 'data_type': 'nvarchar', 'max_length': 200, 'precision': 0, 'scale': 0, 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'object_type': 'USER_TABLE', 'column_id': 7, 'column_name': 'sistema_origen', 'data_type': 'nvarchar', 'max_length': 40, 'precision': 0, 'scale': 0, 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'object_type': 'USER_TABLE', 'column_id': 8, 'column_name': 'fecha_operacion', 'data_type': 'date', 'max_length': 3, 'precision': 10, 'scale': 0, 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'object_type': 'USER_TABLE', 'column_id': 9, 'column_name': 'fecha_hora', 'data_type': 'datetime2', 'max_length': 8, 'precision': 27, 'scale': 7, 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'object_type': 'USER_TABLE', 'column_id': 10, 'column_name': 'numero_ticket', 'data_type': 'nvarchar', 'max_length': 128, 'precision': 0, 'scale': 0, 'is_nullable': False}
```


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