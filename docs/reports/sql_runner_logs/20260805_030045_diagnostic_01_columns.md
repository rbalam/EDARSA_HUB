# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T03:00:45.518678
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_sistema_capacidades_audit_20260805T030044Z/01_columns.sql`

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
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sistema_Capacidades', 'column_count': 10, 'columns_definition': '1:SistemaCapacidadID:int:NOT_NULL | 2:SistemaTipoID:int:NOT_NULL | 3:CodigoCapacidad:varchar:NOT_NULL | 4:Descripcion:nvarchar:NULL | 5:RequiereApiLocal:bit:NULL | 6:RequiereSqlDirecto:bit:NULL | 7:ConfiguracionJSON:nvarchar:NULL | 8:Activo:bit:NULL | 9:CreatedAt:datetime:NULL | 10:UpdatedAt:datetime:NULL'}
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
    AND o.name = N'Sistema_Capacidades'
    AND o.type = N'U'
GROUP BY
    s.name,
    o.name;

```