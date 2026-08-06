# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T03:21:56.949760
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_sync_mesas_root_cause_20260805T032153Z/sync_mesas_state.sql`

## Resultado
ERROR

## Detalle
```text
Error ejecutando SQL. Se hizo rollback. Detalle: (207, b"Invalid column name 'server_id'.DB-Lib error message 20018, severity 16:\nGeneral SQL Server error: Check messages from the SQL Server\nDB-Lib error message 20018, severity 16:\nGeneral SQL Server error: Check messages from the SQL Server\nDB-Lib error message 20018, severity 16:\nGeneral SQL Server error: Check messages from the SQL Server\nDB-Lib error message 20018, severity 16:\nGeneral SQL Server error: Check messages from the SQL Server\nDB-Lib error message 20018, severity 16:\nGeneral SQL Server error: Check messages from the SQL Server\nDB-Lib error message 20018, severity 16:\nGeneral SQL Server error: Check messages from the SQL Server\nDB-Lib error message 20018, severity 16:\nGeneral SQL Server error: Check messages from the SQL Server\nDB-Lib error message 20018, severity 16:\nGeneral SQL Server error: Check messages from the SQL Server\nDB-Lib error message 20018, severity 16:\nGeneral SQL Server error: Check messages from the SQL Server\n")
```

## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

SELECT
    DB_NAME() AS database_name,
    SUSER_SNAME() AS login_name,
    USER_NAME() AS database_user;

SELECT
    OBJECT_ID(N'dbo.Sync_Mesas', N'U') AS sync_mesas_object_id,
    (
        SELECT SUM(ps.row_count)
        FROM sys.dm_db_partition_stats AS ps
        WHERE ps.object_id = OBJECT_ID(N'dbo.Sync_Mesas')
          AND ps.index_id IN (0, 1)
    ) AS sync_mesas_rows,
    (
        SELECT COUNT(*)
        FROM sys.indexes AS i
        WHERE i.object_id = OBJECT_ID(N'dbo.Sync_Mesas')
          AND i.index_id > 0
          AND i.is_disabled = 0
    ) AS sync_mesas_active_indexes;

SELECT
    un.unidad_negocio_id,
    un.codigo AS unidad_codigo,
    un.nombre AS unidad_nombre,
    un.server_id,
    sc.tipo_sistema,
    CASE
        WHEN sc.host IS NULL OR LTRIM(RTRIM(sc.host)) = ''
        THEN 0 ELSE 1
    END AS host_configurado,
    CASE
        WHEN sc.puerto IS NULL
        THEN 0 ELSE 1
    END AS puerto_configurado,
    CASE
        WHEN sc.base_datos IS NULL OR LTRIM(RTRIM(sc.base_datos)) = ''
        THEN 0 ELSE 1
    END AS base_configurada,
    CASE
        WHEN sc.usuario IS NULL OR LTRIM(RTRIM(sc.usuario)) = ''
        THEN 0 ELSE 1
    END AS usuario_configurado,
    CASE
        WHEN sc.password_encrypted IS NULL
          OR DATALENGTH(sc.password_encrypted) = 0
        THEN 0 ELSE 1
    END AS password_configurado,
    sc.activo
FROM dbo.Unidades_Negocio AS un
LEFT JOIN dbo.Servidores_Conexiones AS sc
    ON sc.server_id = un.server_id
WHERE
    un.activo = 1
ORDER BY
    un.codigo,
    sc.tipo_sistema;

```