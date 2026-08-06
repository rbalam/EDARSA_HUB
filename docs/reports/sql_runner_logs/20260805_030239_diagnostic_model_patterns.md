# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T03:02:39.206889
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_capacity_model_patterns_20260805T030238Z/model_patterns.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, schema_name, object_name, object_type, approximate_rows, column_count, has_unidad, has_inicio_vigencia, has_fin_vigencia, has_estado, has_created, has_updated, has_usuario_auditoria, temporal_candidate
- Filas: 65
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Comercial_KPIs_Historico', 'object_type': 'USER_TABLE', 'approximate_rows': 3647, 'column_count': 22, 'has_unidad': 1, 'has_inicio_vigencia': 0, 'has_fin_vigencia': 0, 'has_estado': 0, 'has_created': 1, 'has_updated': 1, 'has_usuario_auditoria': 0, 'temporal_candidate': 1}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Sync_Ventas_Historicas', 'object_type': 'USER_TABLE', 'approximate_rows': 33, 'column_count': 25, 'has_unidad': 1, 'has_inicio_vigencia': 0, 'has_fin_vigencia': 0, 'has_estado': 0, 'has_created': 1, 'has_updated': 1, 'has_usuario_auditoria': 0, 'temporal_candidate': 1}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Comercial_AlertasMargenEventos', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_count': 34, 'has_unidad': 1, 'has_inicio_vigencia': 0, 'has_fin_vigencia': 0, 'has_estado': 1, 'has_created': 0, 'has_updated': 0, 'has_usuario_auditoria': 0, 'temporal_candidate': 1}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Compras_Eventos_Pendientes', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_count': 13, 'has_unidad': 1, 'has_inicio_vigencia': 0, 'has_fin_vigencia': 0, 'has_estado': 0, 'has_created': 1, 'has_updated': 0, 'has_usuario_auditoria': 0, 'temporal_candidate': 1}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Operaciones_Tablaje_EventosContables', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_count': 29, 'has_unidad': 1, 'has_inicio_vigencia': 0, 'has_fin_vigencia': 0, 'has_estado': 0, 'has_created': 0, 'has_updated': 0, 'has_usuario_auditoria': 1, 'temporal_candidate': 1}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'ActivoFijo_HistorialAsignaciones', 'object_type': 'USER_TABLE', 'approximate_rows': 0, 'column_count': 11, 'has_unidad': 0, 'has_inicio_vigencia': 1, 'has_fin_vigencia': 1, 'has_estado': 0, 'has_created': 1, 'has_updated': 0, 'has_usuario_auditoria': 0, 'temporal_candidate': 1}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Sync_Precios_Historicos', 'object_type': 'USER_TABLE', 'approximate_rows': 5642, 'column_count': 18, 'has_unidad': 0, 'has_inicio_vigencia': 0, 'has_fin_vigencia': 1, 'has_estado': 0, 'has_created': 0, 'has_updated': 0, 'has_usuario_auditoria': 1, 'temporal_candidate': 1}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Sistema_HorariosServicioUnidad', 'object_type': 'USER_TABLE', 'approximate_rows': 35, 'column_count': 9, 'has_unidad': 1, 'has_inicio_vigencia': 0, 'has_fin_vigencia': 0, 'has_estado': 1, 'has_created': 0, 'has_updated': 0, 'has_usuario_auditoria': 0, 'temporal_candidate': 0}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Sistema_TurnosOperativosUnidad', 'object_type': 'USER_TABLE', 'approximate_rows': 15, 'column_count': 15, 'has_unidad': 1, 'has_inicio_vigencia': 0, 'has_fin_vigencia': 0, 'has_estado': 1, 'has_created': 0, 'has_updated': 0, 'has_usuario_auditoria': 1, 'temporal_candidate': 0}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Sistema_TurnosOperativosUnidad_Versiones', 'object_type': 'USER_TABLE', 'approximate_rows': 15, 'column_count': 20, 'has_unidad': 1, 'has_inicio_vigencia': 0, 'has_fin_vigencia': 0, 'has_estado': 1, 'has_created': 0, 'has_updated': 0, 'has_usuario_auditoria': 1, 'temporal_candidate': 0}
```


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