# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T03:27:51.911000
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_sync_mesas_exact_contract_20260805T032751Z/exact_objects_metadata.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Dry-run ejecutado. No se aplicaron cambios.


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