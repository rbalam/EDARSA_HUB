# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T09:28:15.926658
- Modo: `migrate`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/migrations/005_crear_vista_posibles_duplicidades.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecución completada.

### Batch 1
- Tipo: Comando
- Filas afectadas: -1


## SQL ejecutado / revisado
```sql
/* ============================================================
   MIGRACIÓN: Vista de Posibles Duplicidades de Tablas
   Script: 005_crear_vista_posibles_duplicidades.sql
   Modo: migrate
   
   Detecta tablas con nombres similares que podrían ser duplicadas.
   ============================================================ */

CREATE OR ALTER VIEW dbo.Sistema_VW_PosiblesDuplicidadesTablas
AS
WITH base AS (
    SELECT
        t.name AS nombre_tabla,
        s.name AS esquema,
        LOWER(t.name) AS nombre_lower
    FROM sys.tables t
    INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
)
SELECT
    a.esquema,
    a.nombre_tabla AS tabla_1,
    b.nombre_tabla AS tabla_2,
    CASE
        WHEN REPLACE(REPLACE(a.nombre_lower, '_', ''), 'cat', '') =
             REPLACE(REPLACE(b.nombre_lower, '_', ''), 'cat', '')
        THEN 'ALTA'
        WHEN a.nombre_lower LIKE '%' + b.nombre_lower + '%'
          OR b.nombre_lower LIKE '%' + a.nombre_lower + '%'
        THEN 'MEDIA'
        ELSE 'BAJA'
    END AS riesgo_duplicidad
FROM base a
INNER JOIN base b
    ON a.nombre_tabla < b.nombre_tabla
WHERE
    a.nombre_lower LIKE '%fin%'
    OR a.nombre_lower LIKE '%venta%'
    OR a.nombre_lower LIKE '%producto%'
    OR a.nombre_lower LIKE '%propina%'
    OR a.nombre_lower LIKE '%rh%'
    OR a.nombre_lower LIKE '%sync%';
GO

```