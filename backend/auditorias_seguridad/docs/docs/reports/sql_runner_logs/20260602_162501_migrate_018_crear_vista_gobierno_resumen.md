# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T16:25:01.502466
- Modo: `migrate`
- Servidor: `<REDACTED_EDARSAHUB_SQL_HOST>`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/migrations/018_crear_vista_gobierno_resumen.sql`

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
   VISTA: Sistema_VW_Gobierno_Tablas_Resumen
   Resumen agrupado por módulo, categoría y estado
   ============================================================ */

CREATE OR ALTER VIEW dbo.Sistema_VW_Gobierno_Tablas_Resumen
AS
SELECT
    modulo,
    categoria,
    estado,
    COUNT(*) AS total_tablas,
    SUM(CASE WHEN estado = 'NO_USAR_NUEVO' THEN 1 ELSE 0 END) AS total_no_usar_nuevo,
    SUM(CASE WHEN categoria = 'SIN_CLASIFICAR' THEN 1 ELSE 0 END) AS total_sin_clasificar
FROM dbo.Sistema_Gobierno_Tablas
GROUP BY modulo, categoria, estado;

```