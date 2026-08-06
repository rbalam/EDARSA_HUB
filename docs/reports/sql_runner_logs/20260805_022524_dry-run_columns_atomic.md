# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:25:24.793106
- Modo: `dry-run`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/var/tmp/edarsahub_intraday_columns_atomic_20260805T022524Z/columns_atomic.sql`

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