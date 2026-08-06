# EDARSAHUB SQL Runner Report

- Fecha: 2026-08-05T02:48:43.231773
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/var/tmp/edarsahub_sync_mesas_audit_20260805T024842Z/01_columns.sql`

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
  {'database_name': 'EDARSAHUB', 'login_name': 'HRLectura', 'schema_name': 'dbo', 'object_name': 'Sync_Mesas', 'column_count': 23, 'columns_definition': '1:ID:int:NOT_NULL | 2:MesaRegistroID:nvarchar:NOT_NULL | 3:ServerID:nvarchar:NOT_NULL | 4:SucursalID:nvarchar:NOT_NULL | 5:SucursalNombre:nvarchar:NULL | 6:FechaOperacion:date:NOT_NULL | 7:MesaNumero:nvarchar:NOT_NULL | 8:MesaNombre:nvarchar:NULL | 9:ZonaID:nvarchar:NULL | 10:ZonaNombre:nvarchar:NULL | 11:Capacidad:int:NULL | 12:TotalCuentas:int:NULL | 13:TotalComensales:int:NULL | 14:VentaTotal:decimal:NULL | 15:TicketPromedio:decimal:NULL | 16:TiempoPromedioOcupacion:int:NULL | 17:RotacionDia:decimal:NULL | 18:EstadoActual:nvarchar:NULL | 19:CuentaActualID:nvarchar:NULL | 20:MeseroActualID:nvarchar:NULL | 21:MeseroActualNombre:nvarchar:NULL | 22:HoraAperturaCuenta:datetime2:NULL | 23:FechaSync:datetime2:NULL'}
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
    AND o.name = N'Sync_Mesas'
    AND o.type = N'U'
GROUP BY
    s.name,
    o.name;

```