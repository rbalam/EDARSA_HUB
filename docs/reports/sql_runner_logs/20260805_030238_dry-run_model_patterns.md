# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T03:02:38.357101
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_capacity_model_patterns_20260805T030238Z/model_patterns.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Dry-run ejecutado. No se aplicaron cambios.


## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

SELECT TOP (100)
    DB_NAME() AS database_name,
    s.name AS schema_name,
    o.name AS object_name,
    o.type_desc AS object_type,

    (
        SELECT SUM(ps.row_count)
        FROM sys.dm_db_partition_stats AS ps
        WHERE ps.object_id = o.object_id
          AND ps.index_id IN (0, 1)
    ) AS approximate_rows,

    COUNT(c.column_id) AS column_count,

    MAX(
        CASE
            WHEN LOWER(c.name) LIKE '%unidad%negocio%'
              OR LOWER(c.name) = 'unidadid'
              OR LOWER(c.name) = 'unidad_id'
            THEN 1 ELSE 0
        END
    ) AS has_unidad,

    MAX(
        CASE
            WHEN LOWER(c.name) LIKE '%fecha%inicio%'
              OR LOWER(c.name) LIKE '%vigencia%inicio%'
              OR LOWER(c.name) LIKE '%vigente%desde%'
            THEN 1 ELSE 0
        END
    ) AS has_inicio_vigencia,

    MAX(
        CASE
            WHEN LOWER(c.name) LIKE '%fecha%fin%'
              OR LOWER(c.name) LIKE '%vigencia%fin%'
              OR LOWER(c.name) LIKE '%vigente%hasta%'
            THEN 1 ELSE 0
        END
    ) AS has_fin_vigencia,

    MAX(
        CASE
            WHEN LOWER(c.name) = 'activo'
              OR LOWER(c.name) LIKE '%estado%'
            THEN 1 ELSE 0
        END
    ) AS has_estado,

    MAX(
        CASE
            WHEN LOWER(c.name) LIKE '%created%'
              OR LOWER(c.name) LIKE '%fecha%alta%'
              OR LOWER(c.name) LIKE '%fecha%registro%'
            THEN 1 ELSE 0
        END
    ) AS has_created,

    MAX(
        CASE
            WHEN LOWER(c.name) LIKE '%updated%'
              OR LOWER(c.name) LIKE '%fecha%actualiza%'
            THEN 1 ELSE 0
        END
    ) AS has_updated,

    MAX(
        CASE
            WHEN LOWER(c.name) LIKE '%usuario%'
              OR LOWER(c.name) LIKE '%creado%por%'
              OR LOWER(c.name) LIKE '%modificado%por%'
            THEN 1 ELSE 0
        END
    ) AS has_usuario_auditoria,

    MAX(
        CASE
            WHEN LOWER(o.name) LIKE '%evento%'
              OR LOWER(o.name) LIKE '%histori%'
              OR LOWER(o.name) LIKE '%vigencia%'
            THEN 1 ELSE 0
        END
    ) AS temporal_candidate

FROM sys.objects AS o
INNER JOIN sys.schemas AS s
    ON s.schema_id = o.schema_id
INNER JOIN sys.columns AS c
    ON c.object_id = o.object_id

WHERE
    o.type IN ('U', 'V')
    AND o.is_ms_shipped = 0
    AND (
           LOWER(o.name) LIKE '%unidad%'
        OR LOWER(o.name) LIKE '%empresa%'
        OR LOWER(o.name) LIKE '%evento%'
        OR LOWER(o.name) LIKE '%histori%'
        OR LOWER(o.name) LIKE '%vigencia%'
        OR LOWER(o.name) LIKE '%turno%'
        OR LOWER(o.name) LIKE '%horario%'
        OR LOWER(c.name) LIKE '%vigencia%'
        OR LOWER(c.name) LIKE '%fecha%inicio%'
        OR LOWER(c.name) LIKE '%fecha%fin%'
    )

GROUP BY
    s.name,
    o.name,
    o.type_desc,
    o.object_id

HAVING
       MAX(
           CASE
               WHEN LOWER(c.name) LIKE '%unidad%negocio%'
                 OR LOWER(c.name) = 'unidadid'
                 OR LOWER(c.name) = 'unidad_id'
               THEN 1 ELSE 0
           END
       ) = 1
    OR MAX(
           CASE
               WHEN LOWER(c.name) LIKE '%fecha%inicio%'
                 OR LOWER(c.name) LIKE '%vigencia%inicio%'
                 OR LOWER(c.name) LIKE '%vigente%desde%'
               THEN 1 ELSE 0
           END
       ) = 1
    OR MAX(
           CASE
               WHEN LOWER(c.name) LIKE '%fecha%fin%'
                 OR LOWER(c.name) LIKE '%vigencia%fin%'
                 OR LOWER(c.name) LIKE '%vigente%hasta%'
               THEN 1 ELSE 0
           END
       ) = 1

ORDER BY
    temporal_candidate DESC,
    has_unidad DESC,
    has_inicio_vigencia DESC,
    has_fin_vigencia DESC,
    approximate_rows DESC,
    s.name,
    o.name;

```