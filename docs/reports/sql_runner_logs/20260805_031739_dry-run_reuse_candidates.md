# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T03:17:39.644958
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_capacity_reuse_audit_20260805T031737Z/reuse_candidates.sql`

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