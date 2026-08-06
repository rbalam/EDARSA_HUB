# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:23:54.250109
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_intraday_candidates_20260805T022352Z/candidate_objects.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecucion completada.

### Batch 1
- Tipo: SELECT
- Columnas: database_name, login_name, schema_name, object_name, object_type, column_count, has_fecha_operacion, has_fecha_hora, has_cheque_ticket, has_producto, has_clasificacion, has_importe, has_pax, has_unidad, capability_score
- Filas: 100
- Preview (primeras 20 filas):
```
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_Inteligencia_VentasDetalleProducto', 'object_type': 'USER_TABLE', 'column_count': 38, 'has_fecha_operacion': 1, 'has_fecha_hora': 1, 'has_cheque_ticket': 1, 'has_producto': 1, 'has_clasificacion': 1, 'has_importe': 1, 'has_pax': 1, 'has_unidad': 1, 'capability_score': 24}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Movimientos_Detalle', 'object_type': 'USER_TABLE', 'column_count': 27, 'has_fecha_operacion': 1, 'has_fecha_hora': 1, 'has_cheque_ticket': 1, 'has_producto': 1, 'has_clasificacion': 1, 'has_importe': 1, 'has_pax': 0, 'has_unidad': 1, 'capability_score': 22}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Sales', 'object_type': 'USER_TABLE', 'column_count': 18, 'has_fecha_operacion': 0, 'has_fecha_hora': 1, 'has_cheque_ticket': 1, 'has_producto': 1, 'has_clasificacion': 0, 'has_importe': 1, 'has_pax': 1, 'has_unidad': 1, 'capability_score': 20}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'View_Inteligencia_Comercial', 'object_type': 'VIEW', 'column_count': 11, 'has_fecha_operacion': 0, 'has_fecha_hora': 1, 'has_cheque_ticket': 0, 'has_producto': 1, 'has_clasificacion': 1, 'has_importe': 1, 'has_pax': 1, 'has_unidad': 1, 'capability_score': 20}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'View_Sync_Sales_Detalle', 'object_type': 'VIEW', 'column_count': 11, 'has_fecha_operacion': 0, 'has_fecha_hora': 1, 'has_cheque_ticket': 1, 'has_producto': 1, 'has_clasificacion': 0, 'has_importe': 1, 'has_pax': 1, 'has_unidad': 1, 'capability_score': 20}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'CRM_Oportunidades', 'object_type': 'USER_TABLE', 'column_count': 49, 'has_fecha_operacion': 0, 'has_fecha_hora': 1, 'has_cheque_ticket': 1, 'has_producto': 1, 'has_clasificacion': 0, 'has_importe': 1, 'has_pax': 0, 'has_unidad': 1, 'capability_score': 18}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Comercial_SolicitudesCambioPrecio', 'object_type': 'USER_TABLE', 'column_count': 44, 'has_fecha_operacion': 0, 'has_fecha_hora': 0, 'has_cheque_ticket': 1, 'has_producto': 1, 'has_clasificacion': 1, 'has_importe': 1, 'has_pax': 0, 'has_unidad': 1, 'capability_score': 17}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'object_type': 'USER_TABLE', 'column_count': 23, 'has_fecha_operacion': 1, 'has_fecha_hora': 1, 'has_cheque_ticket': 1, 'has_producto': 0, 'has_clasificacion': 0, 'has_importe': 1, 'has_pax': 1, 'has_unidad': 1, 'capability_score': 16}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_PAX_Detalle', 'object_type': 'USER_TABLE', 'column_count': 22, 'has_fecha_operacion': 1, 'has_fecha_hora': 1, 'has_cheque_ticket': 1, 'has_producto': 0, 'has_clasificacion': 0, 'has_importe': 1, 'has_pax': 1, 'has_unidad': 1, 'capability_score': 16}
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Vw_Sync_Sales_Unified', 'object_type': 'VIEW', 'column_count': 11, 'has_fecha_operacion': 0, 'has_fecha_hora': 1, 'has_cheque_ticket': 0, 'has_producto': 1, 'has_clasificacion': 0, 'has_importe': 1, 'has_pax': 1, 'has_unidad': 1, 'capability_score': 16}
```


## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

SELECT TOP (100)
    DB_NAME() AS database_name,
    SUSER_SNAME() AS login_name,
    s.name AS schema_name,
    o.name AS object_name,
    o.type_desc AS object_type,
    COUNT(*) AS column_count,
    MAX(CASE WHEN LOWER(c.name) LIKE '%fecha%oper%' THEN 1 ELSE 0 END) AS has_fecha_operacion,
    MAX(CASE WHEN LOWER(c.name) LIKE '%hora%' OR LOWER(c.name) LIKE '%fecha%venta%' OR LOWER(c.name) LIKE '%apertura%' OR LOWER(c.name) LIKE '%cierre%' THEN 1 ELSE 0 END) AS has_fecha_hora,
    MAX(CASE WHEN LOWER(c.name) LIKE '%cheq%' OR LOWER(c.name) LIKE '%ticket%' OR LOWER(c.name) LIKE '%folio%' OR LOWER(c.name) LIKE '%comanda%' THEN 1 ELSE 0 END) AS has_cheque_ticket,
    MAX(CASE WHEN LOWER(c.name) LIKE '%producto%' OR LOWER(c.name) LIKE '%articulo%' OR LOWER(c.name) LIKE '%concepto%' OR LOWER(c.name) LIKE '%item%' OR LOWER(c.name) LIKE '%descripcion%' THEN 1 ELSE 0 END) AS has_producto,
    MAX(CASE WHEN LOWER(c.name) LIKE '%clasif%' OR LOWER(c.name) LIKE '%categoria%' OR LOWER(c.name) LIKE '%familia%' OR LOWER(c.name) LIKE '%grupo%' OR LOWER(c.name) LIKE '%departamento%' OR LOWER(c.name) LIKE '%alimento%' OR LOWER(c.name) LIKE '%bebida%' THEN 1 ELSE 0 END) AS has_clasificacion,
    MAX(CASE WHEN LOWER(c.name) LIKE '%venta%' OR LOWER(c.name) LIKE '%importe%' OR LOWER(c.name) LIKE '%subtotal%' OR LOWER(c.name) LIKE '%total%' OR LOWER(c.name) LIKE '%monto%' OR LOWER(c.name) LIKE '%precio%' THEN 1 ELSE 0 END) AS has_importe,
    MAX(CASE WHEN LOWER(c.name) LIKE '%pax%' OR LOWER(c.name) LIKE '%persona%' OR LOWER(c.name) LIKE '%comensal%' THEN 1 ELSE 0 END) AS has_pax,
    MAX(CASE WHEN LOWER(c.name) LIKE '%unidad%' OR LOWER(c.name) LIKE '%sucursal%' OR LOWER(c.name) LIKE '%server%' OR LOWER(c.name) LIKE '%centro%' THEN 1 ELSE 0 END) AS has_unidad,
    (
      MAX(CASE WHEN LOWER(c.name) LIKE '%hora%' OR LOWER(c.name) LIKE '%fecha%venta%' OR LOWER(c.name) LIKE '%apertura%' OR LOWER(c.name) LIKE '%cierre%' THEN 5 ELSE 0 END)
      + MAX(CASE WHEN LOWER(c.name) LIKE '%cheq%' OR LOWER(c.name) LIKE '%ticket%' OR LOWER(c.name) LIKE '%folio%' OR LOWER(c.name) LIKE '%comanda%' THEN 4 ELSE 0 END)
      + MAX(CASE WHEN LOWER(c.name) LIKE '%producto%' OR LOWER(c.name) LIKE '%articulo%' OR LOWER(c.name) LIKE '%concepto%' OR LOWER(c.name) LIKE '%item%' OR LOWER(c.name) LIKE '%descripcion%' THEN 4 ELSE 0 END)
      + MAX(CASE WHEN LOWER(c.name) LIKE '%clasif%' OR LOWER(c.name) LIKE '%categoria%' OR LOWER(c.name) LIKE '%familia%' OR LOWER(c.name) LIKE '%grupo%' OR LOWER(c.name) LIKE '%departamento%' OR LOWER(c.name) LIKE '%alimento%' OR LOWER(c.name) LIKE '%bebida%' THEN 4 ELSE 0 END)
      + MAX(CASE WHEN LOWER(c.name) LIKE '%venta%' OR LOWER(c.name) LIKE '%importe%' OR LOWER(c.name) LIKE '%subtotal%' OR LOWER(c.name) LIKE '%total%' OR LOWER(c.name) LIKE '%monto%' OR LOWER(c.name) LIKE '%precio%' THEN 3 ELSE 0 END)
      + MAX(CASE WHEN LOWER(c.name) LIKE '%pax%' OR LOWER(c.name) LIKE '%persona%' OR LOWER(c.name) LIKE '%comensal%' THEN 2 ELSE 0 END)
      + MAX(CASE WHEN LOWER(c.name) LIKE '%unidad%' OR LOWER(c.name) LIKE '%sucursal%' OR LOWER(c.name) LIKE '%server%' OR LOWER(c.name) LIKE '%centro%' THEN 2 ELSE 0 END)
    ) AS capability_score
FROM sys.objects AS o
INNER JOIN sys.schemas AS s
    ON s.schema_id = o.schema_id
INNER JOIN sys.columns AS c
    ON c.object_id = o.object_id
WHERE
    o.type IN ('U', 'V')
    AND o.is_ms_shipped = 0
GROUP BY
    s.name,
    o.name,
    o.type_desc
HAVING
    (
      MAX(CASE WHEN LOWER(c.name) LIKE '%hora%' OR LOWER(c.name) LIKE '%fecha%venta%' OR LOWER(c.name) LIKE '%apertura%' OR LOWER(c.name) LIKE '%cierre%' THEN 1 ELSE 0 END)
      + MAX(CASE WHEN LOWER(c.name) LIKE '%cheq%' OR LOWER(c.name) LIKE '%ticket%' OR LOWER(c.name) LIKE '%folio%' OR LOWER(c.name) LIKE '%comanda%' THEN 1 ELSE 0 END)
      + MAX(CASE WHEN LOWER(c.name) LIKE '%producto%' OR LOWER(c.name) LIKE '%articulo%' OR LOWER(c.name) LIKE '%concepto%' OR LOWER(c.name) LIKE '%item%' OR LOWER(c.name) LIKE '%descripcion%' THEN 1 ELSE 0 END)
      + MAX(CASE WHEN LOWER(c.name) LIKE '%clasif%' OR LOWER(c.name) LIKE '%categoria%' OR LOWER(c.name) LIKE '%familia%' OR LOWER(c.name) LIKE '%grupo%' OR LOWER(c.name) LIKE '%departamento%' OR LOWER(c.name) LIKE '%alimento%' OR LOWER(c.name) LIKE '%bebida%' THEN 1 ELSE 0 END)
      + MAX(CASE WHEN LOWER(c.name) LIKE '%venta%' OR LOWER(c.name) LIKE '%importe%' OR LOWER(c.name) LIKE '%subtotal%' OR LOWER(c.name) LIKE '%total%' OR LOWER(c.name) LIKE '%monto%' OR LOWER(c.name) LIKE '%precio%' THEN 1 ELSE 0 END)
      + MAX(CASE WHEN LOWER(c.name) LIKE '%pax%' OR LOWER(c.name) LIKE '%persona%' OR LOWER(c.name) LIKE '%comensal%' THEN 1 ELSE 0 END)
      + MAX(CASE WHEN LOWER(c.name) LIKE '%unidad%' OR LOWER(c.name) LIKE '%sucursal%' OR LOWER(c.name) LIKE '%server%' OR LOWER(c.name) LIKE '%centro%' THEN 1 ELSE 0 END)
    ) >= 2
ORDER BY
    capability_score DESC,
    s.name,
    o.name;

```