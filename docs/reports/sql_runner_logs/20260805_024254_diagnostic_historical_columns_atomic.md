# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:42:54.953949
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_historical_columns_atomic_20260805T024254Z/historical_columns_atomic.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, schema_name, object_name, column_count, columns_definition
- Filas: 3
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Sync_Sales', 'column_count': 18, 'columns_definition': '1:id:varchar:NOT_NULL | 2:branch:nvarchar:NOT_NULL | 3:customer_id:varchar:NULL | 4:items:nvarchar:NULL | 5:total:numeric:NOT_NULL | 6:currency:varchar:NULL | 7:status:varchar:NULL | 8:created_at:datetime:NULL | 9:last_modified:datetime:NULL | 10:sync_hash:varchar:NULL | 11:IdTransaccion:varchar:NULL | 12:UnidadNegocio:nvarchar:NULL | 13:MontoTotal:numeric:NULL | 14:Pax:int:NULL | 15:NumeroTicket:varchar:NULL | 16:FechaHora:datetime:NULL | 17:TipoServicioID:nvarchar:NULL | 18:TipoServicio:nvarchar:NULL'}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Comercial_KPIs_Diarios_v2', 'column_count': 34, 'columns_definition': '1:id:uniqueidentifier:NOT_NULL | 2:unidad_negocio_id:nvarchar:NOT_NULL | 3:unidad_negocio_nombre:nvarchar:NOT_NULL | 4:server_id:nvarchar:NOT_NULL | 5:sucursal_id:nvarchar:NOT_NULL | 6:sucursal_nombre:nvarchar:NULL | 7:sistema_origen:nvarchar:NOT_NULL | 8:fecha_operacion:date:NOT_NULL | 9:anio:int:NOT_NULL | 10:mes:int:NOT_NULL | 11:dia:int:NOT_NULL | 12:ventas_total:decimal:NULL | 13:ventas_sin_propina:decimal:NULL | 14:propinas_total:decimal:NULL | 15:tickets_total:int:NULL | 16:pax_total:int:NULL | 17:ticket_promedio:decimal:NULL | 18:pax_promedio:decimal:NULL | 19:ventas_cerradas:decimal:NULL | 20:ventas_abiertas:decimal:NULL | 21:total_estimado_dia:decimal:NULL | 22:es_venta_abierta:bit:NULL | 23:es_corte_cerrado:bit:NULL | 24:es_demo:bit:NULL | 25:activo:bit:NULL | 26:fuente_original:nvarchar:NOT_NULL | 27:id_origen:nvarchar:NULL | 28:hash_origen:nvarchar:NULL | 29:sync_run_id:nvarchar:NULL | 30:fecha_sincronizacion:datetime2:NULL | 31:fecha_alta:datetime2:NULL | 32:fecha_ultima_actualizacion:datetime2:NULL | 33:version:int:NULL | 34:unidad_negocio_pk:uniqueidentifier:NULL'}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Comercial_KPIs_Historico', 'column_count': 22, 'columns_definition': '1:id:uniqueidentifier:NOT_NULL | 2:run_id:nvarchar:NOT_NULL | 3:server_id:nvarchar:NOT_NULL | 4:sucursal_id:nvarchar:NOT_NULL | 5:sucursal_nombre:nvarchar:NULL | 6:empresa_id:nvarchar:NULL | 7:unidad_negocio_id:nvarchar:NULL | 8:system_type_normalized:nvarchar:NOT_NULL | 9:fecha:date:NOT_NULL | 10:kpi_tipo:nvarchar:NOT_NULL | 11:ventas_total:decimal:NULL | 12:tickets_total:int:NULL | 13:pax_total:int:NULL | 14:ticket_promedio:decimal:NULL | 15:propinas_total:decimal:NULL | 16:source_hash:nvarchar:NULL | 17:source_batch_start:date:NULL | 18:source_batch_end:date:NULL | 19:metadata_json:nvarchar:NULL | 20:version:int:NOT_NULL | 21:created_at:datetime2:NOT_NULL | 22:updated_at:datetime2:NOT_NULL'}
```


## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

SELECT
    DB_NAME() AS database_name,
    s.name AS schema_name,
    o.name AS object_name,
    COUNT(*) AS column_count,
    STRING_AGG(
        CAST(
            CAST(c.column_id AS nvarchar(10))
            + N':' + c.name
            + N':' + t.name
            + N':' +
            CASE
                WHEN c.is_nullable = 1 THEN N'NULL'
                ELSE N'NOT_NULL'
            END
            AS nvarchar(max)
        ),
        N' | '
    ) WITHIN GROUP (
        ORDER BY c.column_id
    ) AS columns_definition
FROM sys.objects AS o
INNER JOIN sys.schemas AS s
    ON s.schema_id = o.schema_id
INNER JOIN sys.columns AS c
    ON c.object_id = o.object_id
INNER JOIN sys.types AS t
    ON t.user_type_id = c.user_type_id
WHERE
    s.name = N'dbo'
    AND o.name IN (
        N'Sync_Sales',
        N'Comercial_KPIs_Diarios_v2',
        N'Comercial_KPIs_Historico'
    )
GROUP BY
    s.name,
    o.name
ORDER BY
    CASE o.name
        WHEN N'Sync_Sales' THEN 1
        WHEN N'Comercial_KPIs_Diarios_v2' THEN 2
        WHEN N'Comercial_KPIs_Historico' THEN 3
        ELSE 99
    END;

```