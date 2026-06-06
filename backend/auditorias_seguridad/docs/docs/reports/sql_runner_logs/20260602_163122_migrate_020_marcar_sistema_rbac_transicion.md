# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T16:31:22.666730
- Modo: `migrate`
- Servidor: `<REDACTED_EDARSAHUB_SQL_HOST>`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/migrations/020_marcar_sistema_rbac_transicion.sql`

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
   MARCAR Sistema_RBAC_* COMO STAGING_RBAC_TRANSICION
   Congelar como transición, no usar para nuevos desarrollos.
   ============================================================ */

MERGE dbo.Sistema_Gobierno_Tablas AS tgt
USING (
    SELECT 'Sistema_RBAC_Permisos' AS nombre_tabla
    UNION ALL SELECT 'Sistema_RBAC_Roles'
    UNION ALL SELECT 'Sistema_RBAC_RolesPermisos'
) AS src
ON tgt.esquema = 'dbo'
AND tgt.nombre_tabla = src.nombre_tabla
WHEN MATCHED THEN
    UPDATE SET
        modulo = 'Sistema/RBAC',
        categoria = 'STAGING_RBAC_TRANSICION',
        estado = 'NO_USAR_NUEVO',
        observaciones = 'Modelo RBAC creado para Inteligencia Comercial, pero el esquema canónico existente es Usuario_*; no asignar usuarios aquí.',
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
        observaciones,
        fecha_alta,
        fecha_ultima_actualizacion
    )
    VALUES (
        NEWID(),
        'dbo',
        src.nombre_tabla,
        'Sistema/RBAC',
        'STAGING_RBAC_TRANSICION',
        'NO_USAR_NUEVO',
        'EDARSAHUB SQL',
        0,
        0,
        0,
        'Modelo RBAC de transición; usar Usuario_* como canónico.',
        SYSDATETIME(),
        SYSDATETIME()
    );

PRINT 'Sistema_RBAC_* marcadas como STAGING_RBAC_TRANSICION.';

```