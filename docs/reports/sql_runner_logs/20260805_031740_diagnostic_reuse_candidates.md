# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T03:17:40.417170
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_capacity_reuse_audit_20260805T031737Z/reuse_candidates.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, login_name, schema_name, object_name, object_type, approximate_rows, column_id, column_name, data_type, max_length, is_nullable
- Filas: 132
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 1, 'column_name': 'ID', 'data_type': 'int', 'max_length': 4, 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 2, 'column_name': 'MesaRegistroID', 'data_type': 'nvarchar', 'max_length': 100, 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 3, 'column_name': 'ServerID', 'data_type': 'nvarchar', 'max_length': 100, 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 4, 'column_name': 'SucursalID', 'data_type': 'nvarchar', 'max_length': 40, 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 5, 'column_name': 'SucursalNombre', 'data_type': 'nvarchar', 'max_length': 200, 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 6, 'column_name': 'FechaOperacion', 'data_type': 'date', 'max_length': 3, 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 7, 'column_name': 'MesaNumero', 'data_type': 'nvarchar', 'max_length': 40, 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 8, 'column_name': 'MesaNombre', 'data_type': 'nvarchar', 'max_length': 100, 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 9, 'column_name': 'ZonaID', 'data_type': 'nvarchar', 'max_length': 40, 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_id': 10, 'column_name': 'ZonaNombre', 'data_type': 'nvarchar', 'max_length': 100, 'is_nullable': True}
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
        o.name IN (
            'Sync_Mesas',
            'Sistema_TurnosOperativosUnidad',
            'Sistema_TurnosOperativosUnidad_Versiones',
            'Sistema_HorariosServicioUnidad',
            'ActivoFijo_HistorialAsignaciones',
            'Comercial_AlertasMargenEventos',
            'Unidades_Negocio'
        )
        OR LOWER(o.name) LIKE '%capacidad%'
        OR LOWER(o.name) LIKE '%aforo%'
        OR LOWER(o.name) LIKE '%mesa%'
        OR LOWER(o.name) LIKE '%vigencia%'
    )
ORDER BY
    CASE o.name
        WHEN 'Sync_Mesas' THEN 1
        WHEN 'Sistema_TurnosOperativosUnidad' THEN 2
        WHEN 'Sistema_TurnosOperativosUnidad_Versiones' THEN 3
        WHEN 'Sistema_HorariosServicioUnidad' THEN 4
        WHEN 'ActivoFijo_HistorialAsignaciones' THEN 5
        WHEN 'Unidades_Negocio' THEN 6
        ELSE 99
    END,
    s.name,
    o.name,
    c.column_id;

```