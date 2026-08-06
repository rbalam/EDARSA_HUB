# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:23:52.914832
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_intraday_candidates_20260805T022352Z/candidate_objects.sql`

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