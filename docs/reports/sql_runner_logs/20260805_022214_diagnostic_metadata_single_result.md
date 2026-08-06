# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:22:14.801816
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_intraday_metadata_single_20260805T022213Z/metadata_single_result.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, login_name, database_user, schema_name, object_name, object_type, column_id, column_name, data_type, max_length, precision, scale, is_nullable
- Filas: 500
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'Comercial', 'object_name': 'TableroEjecutivoCache', 'object_type': 'USER_TABLE', 'column_id': 1, 'column_name': 'UnidadID', 'data_type': 'varchar', 'max_length': 32, 'precision': 0, 'scale': 0, 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'Comercial', 'object_name': 'TableroEjecutivoCache', 'object_type': 'USER_TABLE', 'column_id': 2, 'column_name': 'UnidadNombre', 'data_type': 'nvarchar', 'max_length': 200, 'precision': 0, 'scale': 0, 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'Comercial', 'object_name': 'TableroEjecutivoCache', 'object_type': 'USER_TABLE', 'column_id': 4, 'column_name': 'PaxTotal', 'data_type': 'int', 'max_length': 4, 'precision': 10, 'scale': 0, 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'Comercial', 'object_name': 'TableroEjecutivoCache', 'object_type': 'USER_TABLE', 'column_id': 5, 'column_name': 'ChequesEmitidos', 'data_type': 'int', 'max_length': 4, 'precision': 10, 'scale': 0, 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'Comercial', 'object_name': 'v_TableroComercialConsolidado', 'object_type': 'VIEW', 'column_id': 1, 'column_name': 'UnidadID', 'data_type': 'varchar', 'max_length': 32, 'precision': 0, 'scale': 0, 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'Comercial', 'object_name': 'v_TableroComercialConsolidado', 'object_type': 'VIEW', 'column_id': 2, 'column_name': 'UnidadNombre', 'data_type': 'nvarchar', 'max_length': 200, 'precision': 0, 'scale': 0, 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'Comercial', 'object_name': 'v_TableroComercialConsolidado', 'object_type': 'VIEW', 'column_id': 4, 'column_name': 'PaxTotal', 'data_type': 'int', 'max_length': 4, 'precision': 10, 'scale': 0, 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'Comercial', 'object_name': 'v_TableroComercialConsolidado', 'object_type': 'VIEW', 'column_id': 5, 'column_name': 'ChequesEmitidos', 'data_type': 'int', 'max_length': 4, 'precision': 10, 'scale': 0, 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'ActivoFijo_ActivoMedidores', 'object_type': 'USER_TABLE', 'column_id': 5, 'column_name': 'FechaUltimaLectura', 'data_type': 'datetime2', 'max_length': 6, 'precision': 19, 'scale': 0, 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'ActivoFijo_Activos', 'object_type': 'USER_TABLE', 'column_id': 23, 'column_name': 'Sucursal', 'data_type': 'varchar', 'max_length': 120, 'precision': 0, 'scale': 0, 'is_nullable': True}
```


## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

SELECT TOP (500)
    DB_NAME() AS database_name,
    SUSER_SNAME() AS login_name,
    USER_NAME() AS database_user,
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
        OR LOWER(c.name) LIKE '%grupo%'
        OR LOWER(c.name) LIKE '%alimento%'
        OR LOWER(c.name) LIKE '%bebida%'
        OR LOWER(c.name) LIKE '%pax%'
        OR LOWER(c.name) LIKE '%persona%'
        OR LOWER(c.name) LIKE '%unidad%'
        OR LOWER(c.name) LIKE '%server%'
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