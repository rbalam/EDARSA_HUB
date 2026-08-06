# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:47:22.832099
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_capacity_inventory_20260805T024721Z/capacity_inventory.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, schema_name, object_name, object_type, column_count, has_mesas, has_asientos, has_pax, has_capacidad, has_area, has_vigencia, has_unidad
- Filas: 16
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'column_count': 23, 'has_mesas': 1, 'has_asientos': 0, 'has_pax': 1, 'has_capacidad': 1, 'has_area': 0, 'has_vigencia': 1, 'has_unidad': 1}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'ActivoFijo_Activos', 'object_type': 'USER_TABLE', 'column_count': 1, 'has_mesas': 0, 'has_asientos': 0, 'has_pax': 0, 'has_capacidad': 1, 'has_area': 0, 'has_vigencia': 0, 'has_unidad': 0}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'CavaSocios_Botellas', 'object_type': 'USER_TABLE', 'column_count': 1, 'has_mesas': 0, 'has_asientos': 0, 'has_pax': 0, 'has_capacidad': 1, 'has_area': 0, 'has_vigencia': 0, 'has_unidad': 0}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'CavaSocios_Configuracion', 'object_type': 'USER_TABLE', 'column_count': 1, 'has_mesas': 0, 'has_asientos': 0, 'has_pax': 0, 'has_capacidad': 1, 'has_area': 0, 'has_vigencia': 0, 'has_unidad': 0}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'RH_Nomina', 'object_type': 'USER_TABLE', 'column_count': 1, 'has_mesas': 0, 'has_asientos': 0, 'has_pax': 0, 'has_capacidad': 1, 'has_area': 0, 'has_vigencia': 0, 'has_unidad': 0}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Sistema_Capacidades', 'object_type': 'USER_TABLE', 'column_count': 10, 'has_mesas': 0, 'has_asientos': 0, 'has_pax': 0, 'has_capacidad': 1, 'has_area': 0, 'has_vigencia': 0, 'has_unidad': 0}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Compras_OrdenesDetalle', 'object_type': 'USER_TABLE', 'column_count': 1, 'has_mesas': 1, 'has_asientos': 0, 'has_pax': 0, 'has_capacidad': 0, 'has_area': 0, 'has_vigencia': 1, 'has_unidad': 0}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Sync_Movimientos_Detalle', 'object_type': 'USER_TABLE', 'column_count': 1, 'has_mesas': 1, 'has_asientos': 0, 'has_pax': 0, 'has_capacidad': 0, 'has_area': 0, 'has_vigencia': 0, 'has_unidad': 0}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Sync_PAX_Detalle', 'object_type': 'USER_TABLE', 'column_count': 2, 'has_mesas': 1, 'has_asientos': 0, 'has_pax': 0, 'has_capacidad': 0, 'has_area': 0, 'has_vigencia': 0, 'has_unidad': 0}
  {'database_name': 'EDARSAHUB', 'schema_name': 'dbo', 'object_name': 'Sync_Ticket_Perfecto', 'object_type': 'USER_TABLE', 'column_count': 2, 'has_mesas': 1, 'has_asientos': 0, 'has_pax': 0, 'has_capacidad': 0, 'has_area': 0, 'has_vigencia': 0, 'has_unidad': 0}
```


## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

SELECT TOP (100)
    DB_NAME() AS database_name,
    s.name AS schema_name,
    o.name AS object_name,
    o.type_desc AS object_type,
    COUNT(c.column_id) AS column_count,
    MAX(CASE WHEN LOWER(c.name) LIKE '%mesa%' THEN 1 ELSE 0 END)
        AS has_mesas,
    MAX(CASE
        WHEN LOWER(c.name) LIKE '%asiento%'
          OR LOWER(c.name) LIKE '%silla%'
        THEN 1 ELSE 0 END) AS has_asientos,
    MAX(CASE
        WHEN LOWER(c.name) LIKE '%pax%'
          OR LOWER(c.name) LIKE '%comensal%'
        THEN 1 ELSE 0 END) AS has_pax,
    MAX(CASE
        WHEN LOWER(c.name) LIKE '%aforo%'
          OR LOWER(c.name) LIKE '%capacidad%'
        THEN 1 ELSE 0 END) AS has_capacidad,
    MAX(CASE
        WHEN LOWER(c.name) LIKE '%area%'
          OR LOWER(c.name) LIKE '%salon%'
          OR LOWER(c.name) LIKE '%terraza%'
        THEN 1 ELSE 0 END) AS has_area,
    MAX(CASE
        WHEN LOWER(c.name) LIKE '%fecha%'
          OR LOWER(c.name) LIKE '%vigencia%'
          OR LOWER(c.name) LIKE '%desde%'
          OR LOWER(c.name) LIKE '%hasta%'
        THEN 1 ELSE 0 END) AS has_vigencia,
    MAX(CASE
        WHEN LOWER(c.name) LIKE '%unidad%'
          OR LOWER(c.name) LIKE '%sucursal%'
        THEN 1 ELSE 0 END) AS has_unidad
FROM sys.objects AS o
INNER JOIN sys.schemas AS s
    ON s.schema_id = o.schema_id
INNER JOIN sys.columns AS c
    ON c.object_id = o.object_id
WHERE
    o.type IN ('U', 'V')
    AND o.is_ms_shipped = 0
    AND (
           LOWER(o.name) LIKE '%mesa%'
        OR LOWER(o.name) LIKE '%aforo%'
        OR LOWER(o.name) LIKE '%capacidad%'
        OR LOWER(o.name) LIKE '%salon%'
        OR LOWER(o.name) LIKE '%area%'
        OR LOWER(c.name) LIKE '%mesa%'
        OR LOWER(c.name) LIKE '%asiento%'
        OR LOWER(c.name) LIKE '%silla%'
        OR LOWER(c.name) LIKE '%aforo%'
        OR LOWER(c.name) LIKE '%capacidad%'
    )
GROUP BY
    s.name,
    o.name,
    o.type_desc
ORDER BY
    has_capacidad DESC,
    has_mesas DESC,
    has_asientos DESC,
    has_vigencia DESC,
    s.name,
    o.name;

```