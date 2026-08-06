# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T03:27:52.674014
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_sync_mesas_exact_contract_20260805T032751Z/exact_objects_metadata.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, login_name, database_user, schema_name, object_name, object_type, approximate_rows, column_id, column_name, data_type, max_length, precision, scale, is_nullable, is_identity
- Filas: 207
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 1, 'column_name': 'ID', 'data_type': 'int', 'max_length': 4, 'precision': 10, 'scale': 0, 'is_nullable': False, 'is_identity': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 2, 'column_name': 'MesaRegistroID', 'data_type': 'nvarchar', 'max_length': 100, 'precision': 0, 'scale': 0, 'is_nullable': False, 'is_identity': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 3, 'column_name': 'ServerID', 'data_type': 'nvarchar', 'max_length': 100, 'precision': 0, 'scale': 0, 'is_nullable': False, 'is_identity': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 4, 'column_name': 'SucursalID', 'data_type': 'nvarchar', 'max_length': 40, 'precision': 0, 'scale': 0, 'is_nullable': False, 'is_identity': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 5, 'column_name': 'SucursalNombre', 'data_type': 'nvarchar', 'max_length': 200, 'precision': 0, 'scale': 0, 'is_nullable': True, 'is_identity': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 6, 'column_name': 'FechaOperacion', 'data_type': 'date', 'max_length': 3, 'precision': 10, 'scale': 0, 'is_nullable': False, 'is_identity': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 7, 'column_name': 'MesaNumero', 'data_type': 'nvarchar', 'max_length': 40, 'precision': 0, 'scale': 0, 'is_nullable': False, 'is_identity': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 8, 'column_name': 'MesaNombre', 'data_type': 'nvarchar', 'max_length': 100, 'precision': 0, 'scale': 0, 'is_nullable': True, 'is_identity': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 9, 'column_name': 'ZonaID', 'data_type': 'nvarchar', 'max_length': 40, 'precision': 0, 'scale': 0, 'is_nullable': True, 'is_identity': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 10, 'column_name': 'ZonaNombre', 'data_type': 'nvarchar', 'max_length': 100, 'precision': 0, 'scale': 0, 'is_nullable': True, 'is_identity': False}
```


## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

SELECT
    DB_NAME() AS database_name,
    SUSER_SNAME() AS login_name,
    USER_NAME() AS database_user,
    s.name AS schema_name,
    o.name AS object_name,
    o.type_desc AS object_type,
    (
        SELECT SUM(ps.row_count)
        FROM sys.dm_db_partition_stats AS ps
        WHERE ps.object_id = o.object_id
          AND ps.index_id IN (0, 1)
    ) AS approximate_rows,
    c.column_id,
    c.name AS column_name,
    t.name AS data_type,
    c.max_length,
    c.precision,
    c.scale,
    c.is_nullable,
    c.is_identity
FROM sys.objects AS o
INNER JOIN sys.schemas AS s
    ON s.schema_id = o.schema_id
INNER JOIN sys.columns AS c
    ON c.object_id = o.object_id
INNER JOIN sys.types AS t
    ON t.user_type_id = c.user_type_id
WHERE
    o.type IN (N'U', N'V')
    AND o.is_ms_shipped = 0
    AND o.name IN (
        N'Comercial_KPIs_Diarios_v2',
        N'Comercial_Ventas_Dia_Abiertas_v2',
        N'Servidores_Conexiones',
        N'Sistema_SucursalServidorMapeo',
        N'Sync_Mesas',
        N'Sync_Metas_Comerciales',
        N'Sync_PAX_Detalle',
        N'Sync_Ticket_Perfecto',
        N'Unidades_Negocio'
    )
ORDER BY
    CASE o.name
        WHEN N'Sync_Mesas' THEN 1
        WHEN N'Unidades_Negocio' THEN 2
        WHEN N'Servidores_Conexiones' THEN 3
        ELSE 10
    END,
    s.name,
    o.name,
    c.column_id;

```