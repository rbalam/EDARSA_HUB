# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:25:25.578684
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_intraday_columns_atomic_20260805T022524Z/columns_atomic.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, login_name, schema_name, object_name, column_count, columns_definition
- Filas: 1
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'column_count': 38, 'columns_definition': '1:id:uniqueidentifier:NOT_NULL | 2:unidad_negocio_id:nvarchar:NULL | 3:unidad_negocio_nombre:nvarchar:NULL | 4:server_id:nvarchar:NULL | 5:sucursal_id:nvarchar:NULL | 6:sucursal_nombre:nvarchar:NULL | 7:sistema_origen:nvarchar:NULL | 8:fecha_operacion:date:NOT_NULL | 9:fecha_hora:datetime2:NULL | 10:numero_ticket:nvarchar:NOT_NULL | 11:id_transaccion:nvarchar:NOT_NULL | 12:producto_codigo_fuente:nvarchar:NOT_NULL | 13:producto_id:uniqueidentifier:NULL | 14:producto_nombre:nvarchar:NULL | 15:familia_id:uniqueidentifier:NULL | 16:familia_nombre:nvarchar:NULL | 17:subfamilia_id:uniqueidentifier:NULL | 18:subfamilia_nombre:nvarchar:NULL | 19:casa:nvarchar:NULL | 20:porcentaje_alcohol:decimal:NULL | 21:es_alcohol:bit:NULL | 22:cantidad:decimal:NULL | 23:precio_unitario:decimal:NULL | 24:importe_bruto:decimal:NULL | 25:importe_neto:decimal:NULL | 26:descuento:decimal:NULL | 27:propina:decimal:NULL | 28:pax:int:NULL | 29:sync_run_id:nvarchar:NULL | 30:hash_origen:nvarchar:NULL | 31:fecha_sincronizacion:datetime2:NOT_NULL | 32:activo:bit:NOT_NULL | 33:estado_origen:nvarchar:NULL | 34:cancelado_origen:bit:NULL | 35:es_kpi_valido:bit:NULL | 36:folio_origen:nvarchar:NULL | 37:documento_origen:nvarchar:NULL | 38:fuente_original:nvarchar:NULL'}
```


## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

SELECT
    DB_NAME() AS database_name,
    SUSER_SNAME() AS login_name,
    s.name AS schema_name,
    o.name AS object_name,
    COUNT(*) AS column_count,
    STRING_AGG(
        CAST(
            CONCAT(
                c.column_id, ':',
                c.name, ':',
                t.name, ':',
                CASE WHEN c.is_nullable = 1 THEN 'NULL' ELSE 'NOT_NULL' END
            ) AS nvarchar(max)
        ),
        ' | '
    ) WITHIN GROUP (ORDER BY c.column_id) AS columns_definition
FROM sys.objects AS o
INNER JOIN sys.schemas AS s
    ON s.schema_id = o.schema_id
INNER JOIN sys.columns AS c
    ON c.object_id = o.object_id
INNER JOIN sys.types AS t
    ON t.user_type_id = c.user_type_id
WHERE
    s.name = 'dbo'
    AND o.name = 'Comercial_Inteligencia_VentasDetalleProducto'
    AND o.type = 'U'
GROUP BY
    s.name,
    o.name;

```