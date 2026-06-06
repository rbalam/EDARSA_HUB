# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T16:31:17.134251
- Modo: `migrate`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/migrations/019_clasificacion_masiva_por_familia.sql`

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
   CLASIFICACIÓN MASIVA CONTROLADA POR FAMILIA
   No marca todo como canónico indiscriminadamente.
   ============================================================ */

-- Requiere campo 'id' como uniqueidentifier con NEWID()
MERGE dbo.Sistema_Gobierno_Tablas AS tgt
USING (
    SELECT
        s.name AS esquema,
        t.name AS nombre_tabla,
        CASE
            WHEN t.name LIKE 'ActivoFijo_%' THEN 'Activo Fijo'
            WHEN t.name LIKE 'CRM_%' THEN 'CRM'
            WHEN t.name LIKE 'Compras_%' THEN 'Compras'
            WHEN t.name LIKE 'Usuario_%' THEN 'Usuarios/RBAC'
            WHEN t.name LIKE 'Proveedor_%' THEN 'Proveedores'
            WHEN t.name LIKE 'Venta_%' THEN 'Comercial/Ventas'
            WHEN t.name LIKE 'Operaciones_%' THEN 'Operaciones'
            WHEN t.name LIKE 'Operativo_%' THEN 'Operaciones'
            WHEN t.name LIKE 'Inventario_%' THEN 'Inventarios'
            WHEN t.name LIKE 'Sistema_%' THEN 'Sistema'
            WHEN t.name LIKE 'Sys_%' THEN 'Sistema Legacy'
            WHEN t.name LIKE 'Scheduler_%' THEN 'Scheduler'
            ELSE 'Pendiente'
        END AS modulo,
        CASE
            WHEN t.name LIKE 'ActivoFijo_%' THEN 'CANONICA'
            WHEN t.name LIKE 'CRM_Staging_%' THEN 'STAGING'
            WHEN t.name LIKE 'CRM_%' THEN 'CANONICA_REVISION'
            WHEN t.name LIKE 'Compras_%' THEN 'CANONICA'
            WHEN t.name LIKE 'Usuario_%' THEN 'CANONICA_RBAC'
            WHEN t.name LIKE 'Proveedor_%' THEN 'CANONICA'
            WHEN t.name LIKE 'Venta_%' THEN 'REVISION_COMERCIAL'
            WHEN t.name LIKE 'Operaciones_%' THEN 'CANONICA_REVISION'
            WHEN t.name LIKE 'Operativo_%' THEN 'CANONICA_REVISION'
            WHEN t.name LIKE 'Inventario_%' THEN 'CANONICA_REVISION'
            WHEN t.name LIKE 'Sistema_%' THEN 'CANONICA_SISTEMA'
            WHEN t.name LIKE 'Sys_%' THEN 'LEGADO_REVISION'
            WHEN t.name LIKE 'Scheduler_%' THEN 'LEGADO_REVISION'
            ELSE 'SIN_CLASIFICAR'
        END AS categoria,
        CASE
            WHEN t.name LIKE 'Sys_%' THEN 'NO_USAR_NUEVO'
            WHEN t.name IN ('Products', 'Fact_Ventas_Consolidadas', 'Config_Horarios') THEN 'NO_USAR_NUEVO'
            WHEN t.name LIKE 'Venta_%' THEN 'REVISION'
            ELSE 'ACTIVA'
        END AS estado,
        'EDARSAHUB SQL' AS fuente_verdad
    FROM sys.tables t
    INNER JOIN sys.schemas s
        ON t.schema_id = s.schema_id
    WHERE NOT EXISTS (
        SELECT 1
        FROM dbo.Sistema_Gobierno_Tablas g
        WHERE g.esquema = s.name
          AND g.nombre_tabla = t.name
    )
) AS src
ON tgt.esquema = src.esquema
AND tgt.nombre_tabla = src.nombre_tabla
WHEN MATCHED THEN
    UPDATE SET
        modulo = src.modulo,
        categoria = src.categoria,
        estado = src.estado,
        fuente_verdad = src.fuente_verdad,
        fecha_ultima_actualizacion = SYSDATETIME()
WHEN NOT MATCHED THEN
    INSERT (
        id,
        esquema,
        nombre_tabla,
        modulo,
        categoria,
        estado,
        fuente_verdad,
        permite_insert,
        permite_update,
        permite_delete,
        fecha_alta,
        fecha_ultima_actualizacion
    )
    VALUES (
        NEWID(),
        src.esquema,
        src.nombre_tabla,
        src.modulo,
        src.categoria,
        src.estado,
        src.fuente_verdad,
        1,
        1,
        0,
        SYSDATETIME(),
        SYSDATETIME()
    );

PRINT 'Clasificación masiva por familia completada.';

```