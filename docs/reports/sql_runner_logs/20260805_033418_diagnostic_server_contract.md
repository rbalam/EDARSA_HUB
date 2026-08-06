# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T03:34:18.140432
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_sync_mesas_server_contract_20260805T033417Z/server_contract.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, login_name, database_user, schema_name, object_name, object_type, approximate_rows, column_id, column_name, data_type, is_nullable
- Filas: 93
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Servidores_Conexiones', 'object_type': 'USER_TABLE', 'approximate_rows': 25, 'column_id': 1, 'column_name': 'id', 'data_type': 'uniqueidentifier', 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Servidores_Conexiones', 'object_type': 'USER_TABLE', 'approximate_rows': 25, 'column_id': 2, 'column_name': 'nombre', 'data_type': 'nvarchar', 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Servidores_Conexiones', 'object_type': 'USER_TABLE', 'approximate_rows': 25, 'column_id': 3, 'column_name': 'system_type', 'data_type': 'nvarchar', 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Servidores_Conexiones', 'object_type': 'USER_TABLE', 'approximate_rows': 25, 'column_id': 4, 'column_name': 'tipo_conexion', 'data_type': 'nvarchar', 'is_nullable': False}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Servidores_Conexiones', 'object_type': 'USER_TABLE', 'approximate_rows': 25, 'column_id': 5, 'column_name': 'host', 'data_type': 'nvarchar', 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Servidores_Conexiones', 'object_type': 'USER_TABLE', 'approximate_rows': 25, 'column_id': 6, 'column_name': 'port', 'data_type': 'int', 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Servidores_Conexiones', 'object_type': 'USER_TABLE', 'approximate_rows': 25, 'column_id': 7, 'column_name': 'database_name', 'data_type': 'nvarchar', 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Servidores_Conexiones', 'object_type': 'USER_TABLE', 'approximate_rows': 25, 'column_id': 8, 'column_name': 'username', 'data_type': 'nvarchar', 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Servidores_Conexiones', 'object_type': 'USER_TABLE', 'approximate_rows': 25, 'column_id': 9, 'column_name': 'password_encrypted', 'data_type': 'nvarchar', 'is_nullable': True}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'database_user': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Servidores_Conexiones', 'object_type': 'USER_TABLE', 'approximate_rows': 25, 'column_id': 10, 'column_name': 'api_url', 'data_type': 'nvarchar', 'is_nullable': True}
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
    c.is_nullable
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
        N'Servidores_Conexiones',
        N'Sistema_SucursalServidorMapeo',
        N'Comercial_Ventas_Dia_Abiertas_v2',
        N'Sync_Mesas'
    )
ORDER BY
    CASE o.name
        WHEN N'Servidores_Conexiones' THEN 1
        WHEN N'Sistema_SucursalServidorMapeo' THEN 2
        WHEN N'Comercial_Ventas_Dia_Abiertas_v2' THEN 3
        WHEN N'Sync_Mesas' THEN 4
        ELSE 10
    END,
    s.name,
    o.name,
    c.column_id;

SELECT
    COUNT_BIG(*) AS servidores_total,
    SUM(CASE WHEN activo = 1 THEN 1 ELSE 0 END) AS servidores_activos,
    COUNT(DISTINCT id) AS ids_distintos,
    SUM(
        CASE
            WHEN id IS NULL
            THEN 1
            ELSE 0
        END
    ) AS ids_nulos,
    SUM(
        CASE
            WHEN nombre IS NULL OR LTRIM(RTRIM(nombre)) = N''
            THEN 1
            ELSE 0
        END
    ) AS nombres_vacios
FROM dbo.Servidores_Conexiones;

SELECT
    COUNT_BIG(*) AS mapeos_total,
    SUM(CASE WHEN Activo = 1 THEN 1 ELSE 0 END) AS mapeos_activos,
    COUNT(DISTINCT ServidorID) AS servidores_id_mapeados,
    COUNT(DISTINCT MongoServidorUUID) AS mongo_uuid_mapeados,
    COUNT(DISTINCT SucursalID) AS sucursales_distintas
FROM dbo.Sistema_SucursalServidorMapeo;

SELECT
    COUNT_BIG(*) AS ventas_abiertas_total,
    COUNT(DISTINCT server_id) AS servidores_con_ventas,
    COUNT(DISTINCT sucursal_id) AS sucursales_con_ventas,
    MIN(CAST(fecha_operacion AS date)) AS fecha_min,
    MAX(CAST(fecha_operacion AS date)) AS fecha_max
FROM dbo.Comercial_Ventas_Dia_Abiertas_v2;

SELECT
    COUNT_BIG(*) AS sync_mesas_total,
    COUNT(DISTINCT ServerID) AS servidores_sync_mesas,
    COUNT(DISTINCT SucursalID) AS sucursales_sync_mesas,
    MIN(FechaOperacion) AS fecha_min,
    MAX(FechaOperacion) AS fecha_max
FROM dbo.Sync_Mesas;

```