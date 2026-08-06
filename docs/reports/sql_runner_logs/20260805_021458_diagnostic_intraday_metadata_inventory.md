# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:14:58.417030
- Modo: `diagnostic`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_intraday_metadata_select_20260805T021457Z/intraday_metadata_inventory.sql`

## Resultado
ERROR

## Detalle
```text
Error ejecutando SQL. Se hizo rollback. Detalle: Variable obligatoria no configurada: EDARSAHUB_SQL_HOST
```

## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

SELECT
    DB_NAME() AS database_name,
    SUSER_SNAME() AS login_name,
    USER_NAME() AS database_user;

;WITH CandidateColumns AS (
    SELECT
        s.name AS schema_name,
        o.name AS object_name,
        o.type_desc,
        c.column_id,
        c.name AS column_name,
        t.name AS data_type,
        c.max_length,
        c.precision,
        c.scale,
        c.is_nullable,
        CASE
            WHEN LOWER(c.name) LIKE %fecha%oper%
              OR LOWER(c.name) IN (fechaoperacion)
            THEN 1 ELSE 0
        END AS has_fecha_operacion,
        CASE
            WHEN LOWER(c.name) LIKE %hora%
              OR LOWER(c.name) LIKE %fecha%venta%
              OR LOWER(c.name) LIKE %apertura%
              OR LOWER(c.name) LIKE %cierre%
            THEN 1 ELSE 0
        END AS has_fecha_hora,
        CASE
            WHEN LOWER(c.name) LIKE %cheq%
              OR LOWER(c.name) LIKE %ticket%
              OR LOWER(c.name) LIKE %folio%
              OR LOWER(c.name) LIKE %comanda%
            THEN 1 ELSE 0
        END AS has_cheque,
        CASE
            WHEN LOWER(c.name) LIKE %producto%
              OR LOWER(c.name) LIKE %articulo%
              OR LOWER(c.name) LIKE %concepto%
              OR LOWER(c.name) LIKE %descripcion%
            THEN 1 ELSE 0
        END AS has_producto,
        CASE
            WHEN LOWER(c.name) LIKE %clasif%
              OR LOWER(c.name) LIKE %categoria%
              OR LOWER(c.name) LIKE %familia%
              OR LOWER(c.name) LIKE %grupo%
              OR LOWER(c.name) LIKE %alimento%
              OR LOWER(c.name) LIKE %bebida%
            THEN 1 ELSE 0
        END AS has_clasificacion,
        CASE
            WHEN LOWER(c.name) LIKE %pax%
              OR LOWER(c.name) LIKE %persona%
              OR LOWER(c.name) LIKE %comensal%
            THEN 1 ELSE 0
        END AS has_pax,
        CASE
            WHEN LOWER(c.name) LIKE %unidad%
              OR LOWER(c.name) LIKE %server%
              OR LOWER(c.name) LIKE %sucursal%
            THEN 1 ELSE 0
        END AS has_unidad,
        CASE
            WHEN LOWER(c.name) LIKE %venta%
              OR LOWER(c.name) LIKE %importe%
              OR LOWER(c.name) LIKE %subtotal%
              OR LOWER(c.name) LIKE %total%
            THEN 1 ELSE 0
        END AS has_ventas
    FROM sys.objects AS o
    INNER JOIN sys.schemas AS s
        ON s.schema_id = o.schema_id
    INNER JOIN sys.columns AS c
        ON c.object_id = o.object_id
    INNER JOIN sys.types AS t
        ON t.user_type_id = c.user_type_id
    WHERE
        o.type IN (U, V)
        AND o.is_ms_shipped = 0
),
CandidateObjects AS (
    SELECT
        schema_name,
        object_name,
        type_desc,
        COUNT(*) AS column_count,
        MAX(has_fecha_operacion) AS has_fecha_operacion,
        MAX(has_fecha_hora) AS has_fecha_hora,
        MAX(has_cheque) AS has_cheque,
        MAX(has_producto) AS has_producto,
        MAX(has_clasificacion) AS has_clasificacion,
        MAX(has_pax) AS has_pax,
        MAX(has_unidad) AS has_unidad,
        MAX(has_ventas) AS has_ventas
    FROM CandidateColumns
    GROUP BY
        schema_name,
        object_name,
        type_desc
)
SELECT TOP (80)
    schema_name,
    object_name,
    type_desc,
    column_count,
    has_fecha_operacion,
    has_fecha_hora,
    has_cheque,
    has_producto,
    has_clasificacion,
    has_pax,
    has_unidad,
    has_ventas
FROM CandidateObjects
WHERE
       LOWER(object_name) LIKE %cheq%
    OR LOWER(object_name) LIKE %ticket%
    OR LOWER(object_name) LIKE %comanda%
    OR LOWER(object_name) LIKE %venta%
    OR LOWER(object_name) LIKE %producto%
    OR LOWER(object_name) LIKE %detalle%
    OR (
        has_fecha_hora = 1
        AND has_ventas = 1
        AND (
            has_cheque = 1
            OR has_producto = 1
        )
    )
ORDER BY
    (
        has_fecha_operacion
        + has_fecha_hora
        + has_cheque
        + has_producto
        + has_clasificacion
        + has_pax
        + has_unidad
        + has_ventas
    ) DESC,
    schema_name,
    object_name;

;WITH RelevantObjects AS (
    SELECT DISTINCT
        o.object_id
    FROM sys.objects AS o
    INNER JOIN sys.columns AS c
        ON c.object_id = o.object_id
    WHERE
        o.type IN (U, V)
        AND o.is_ms_shipped = 0
        AND (
               LOWER(o.name) LIKE %cheq%
            OR LOWER(o.name) LIKE %ticket%
            OR LOWER(o.name) LIKE %comanda%
            OR LOWER(o.name) LIKE %venta%
            OR LOWER(o.name) LIKE %producto%
            OR LOWER(o.name) LIKE %detalle%
            OR LOWER(c.name) LIKE %hora%
            OR LOWER(c.name) LIKE %fecha%oper%
            OR LOWER(c.name) LIKE %producto%
            OR LOWER(c.name) LIKE %clasif%
            OR LOWER(c.name) LIKE %categoria%
            OR LOWER(c.name) LIKE %familia%
            OR LOWER(c.name) LIKE %alimento%
            OR LOWER(c.name) LIKE %bebida%
            OR LOWER(c.name) LIKE %pax%
        )
)
SELECT TOP (250)
    s.name AS schema_name,
    o.name AS object_name,
    o.type_desc,
    c.column_id,
    c.name AS column_name,
    t.name AS data_type,
    c.max_length,
    c.precision,
    c.scale,
    c.is_nullable
FROM RelevantObjects AS r
INNER JOIN sys.objects AS o
    ON o.object_id = r.object_id
INNER JOIN sys.schemas AS s
    ON s.schema_id = o.schema_id
INNER JOIN sys.columns AS c
    ON c.object_id = o.object_id
INNER JOIN sys.types AS t
    ON t.user_type_id = c.user_type_id
WHERE
       LOWER(c.name) LIKE %fecha%
    OR LOWER(c.name) LIKE %hora%
    OR LOWER(c.name) LIKE %cheq%
    OR LOWER(c.name) LIKE %ticket%
    OR LOWER(c.name) LIKE %folio%
    OR LOWER(c.name) LIKE %comanda%
    OR LOWER(c.name) LIKE %producto%
    OR LOWER(c.name) LIKE %articulo%
    OR LOWER(c.name) LIKE %concepto%
    OR LOWER(c.name) LIKE %descripcion%
    OR LOWER(c.name) LIKE %clasif%
    OR LOWER(c.name) LIKE %categoria%
    OR LOWER(c.name) LIKE %familia%
    OR LOWER(c.name) LIKE %grupo%
    OR LOWER(c.name) LIKE %alimento%
    OR LOWER(c.name) LIKE %bebida%
    OR LOWER(c.name) LIKE %pax%
    OR LOWER(c.name) LIKE %persona%
    OR LOWER(c.name) LIKE %unidad%
    OR LOWER(c.name) LIKE %server%
    OR LOWER(c.name) LIKE %sucursal%
    OR LOWER(c.name) LIKE %venta%
    OR LOWER(c.name) LIKE %importe%
    OR LOWER(c.name) LIKE %subtotal%
    OR LOWER(c.name) LIKE %total%
ORDER BY
    s.name,
    o.name,
    c.column_id;

```