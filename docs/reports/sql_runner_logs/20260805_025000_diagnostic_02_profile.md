# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:50:00.812213
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_sync_mesas_audit_20260805T024959Z/02_profile.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, login_name, approximate_rows, active_indexes, column_count, temporal_columns, unit_columns, capacity_columns
- Filas: 1
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'approximate_rows': 0, 'active_indexes': 1, 'column_count': 23, 'temporal_columns': 3, 'unit_columns': 3, 'capacity_columns': 4}
```


## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

SELECT
    DB_NAME() AS database_name,
    SUSER_SNAME() AS login_name,
    (
        SELECT SUM(ps.row_count)
        FROM sys.dm_db_partition_stats AS ps
        WHERE ps.object_id = OBJECT_ID(N'dbo.Sync_Mesas')
          AND ps.index_id IN (0, 1)
    ) AS approximate_rows,
    (
        SELECT COUNT(*)
        FROM sys.indexes AS i
        WHERE i.object_id = OBJECT_ID(N'dbo.Sync_Mesas')
          AND i.index_id > 0
          AND i.is_disabled = 0
    ) AS active_indexes,
    (
        SELECT COUNT(*)
        FROM sys.columns AS c
        WHERE c.object_id = OBJECT_ID(N'dbo.Sync_Mesas')
    ) AS column_count,
    (
        SELECT COUNT(*)
        FROM sys.columns AS c
        WHERE c.object_id = OBJECT_ID(N'dbo.Sync_Mesas')
          AND (
                 LOWER(c.name) LIKE N'%fecha%'
              OR LOWER(c.name) LIKE N'%hora%'
              OR LOWER(c.name) LIKE N'%vigencia%'
          )
    ) AS temporal_columns,
    (
        SELECT COUNT(*)
        FROM sys.columns AS c
        WHERE c.object_id = OBJECT_ID(N'dbo.Sync_Mesas')
          AND (
                 LOWER(c.name) LIKE N'%unidad%'
              OR LOWER(c.name) LIKE N'%sucursal%'
              OR LOWER(c.name) LIKE N'%server%'
          )
    ) AS unit_columns,
    (
        SELECT COUNT(*)
        FROM sys.columns AS c
        WHERE c.object_id = OBJECT_ID(N'dbo.Sync_Mesas')
          AND (
                 LOWER(c.name) LIKE N'%mesa%'
              OR LOWER(c.name) LIKE N'%capacidad%'
              OR LOWER(c.name) LIKE N'%pax%'
              OR LOWER(c.name) LIKE N'%aforo%'
          )
    ) AS capacity_columns;

```