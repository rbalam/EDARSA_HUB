# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T09:47:24.839199
- Modo: `migrate`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/migrations/007_crear_tabla_migracion_mongosql_mapeo.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 2
- Mensaje: Ejecución completada.

### Batch 1
- Tipo: Comando
- Filas afectadas: -1

### Batch 2
- Tipo: Comando
- Filas afectadas: 8


## SQL ejecutado / revisado
```sql
/* ============================================================
   MIGRACIÓN: Tabla de Mapeo MongoDB -> SQL
   Script: 007_crear_tabla_migracion_mongosql_mapeo.sql
   Modo: migrate
   
   Registra el estado de migración de colecciones MongoDB a tablas SQL.
   ============================================================ */

IF OBJECT_ID('dbo.Sistema_Migracion_MongoSQL_Mapeo', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sistema_Migracion_MongoSQL_Mapeo (
        id UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
        coleccion_mongo NVARCHAR(200) NOT NULL,
        tabla_sql_destino SYSNAME NULL,
        modulo NVARCHAR(100) NOT NULL,
        estado NVARCHAR(50) NOT NULL DEFAULT 'PENDIENTE',
        prioridad NVARCHAR(20) NOT NULL DEFAULT 'P2',
        estrategia NVARCHAR(MAX) NULL,
        fecha_inicio DATETIME2 NULL,
        fecha_fin DATETIME2 NULL,
        observaciones NVARCHAR(MAX) NULL,
        fecha_alta DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );
    
    CREATE UNIQUE INDEX UX_Sistema_Migracion_MongoSQL_Mapeo_Coleccion
    ON dbo.Sistema_Migracion_MongoSQL_Mapeo(coleccion_mongo);
END;
GO

MERGE dbo.Sistema_Migracion_MongoSQL_Mapeo AS tgt
USING (
    SELECT 'servers' AS coleccion_mongo, 'Servidores_Conexiones' AS tabla_sql_destino, 'Sistema/Conexiones' AS modulo, 'P0' AS prioridad, 'Migrar configuración de servidores a SQL; Mongo solo lectura temporal.' AS estrategia
    UNION ALL SELECT 'empresas', 'Global_Cat_Empresas', 'Global', 'P0', 'Homologar empresas contra catálogo global SQL.'
    UNION ALL SELECT 'sucursales_catalogo', 'RH_Cat_Sucursales', 'Global/RH', 'P1', 'Validar si sucursal pertenece a RH o catálogo global operativo.'
    UNION ALL SELECT 'sucursal_servidor_map', 'Unidades_Negocio', 'Sistema/Unidades', 'P0', 'Unificar mapeo unidad-servidor en SQL.'
    UNION ALL SELECT 'rbac_permisos', NULL, 'RBAC', 'P0', 'Definir tablas SQL RBAC canónicas antes de migrar.'
    UNION ALL SELECT 'rbac_roles', NULL, 'RBAC', 'P0', 'Definir tablas SQL RBAC canónicas antes de migrar.'
    UNION ALL SELECT 'rbac_usuarios_roles', NULL, 'RBAC', 'P0', 'Definir tablas SQL RBAC canónicas antes de migrar.'
    UNION ALL SELECT 'rbac_audit_log', NULL, 'RBAC/Auditoría', 'P1', 'Migrar a auditoría SQL transversal.'
) AS src
ON tgt.coleccion_mongo = src.coleccion_mongo
WHEN MATCHED THEN
    UPDATE SET
        tabla_sql_destino = src.tabla_sql_destino,
        modulo = src.modulo,
        prioridad = src.prioridad,
        estrategia = src.estrategia
WHEN NOT MATCHED THEN
    INSERT (coleccion_mongo, tabla_sql_destino, modulo, prioridad, estrategia)
    VALUES (src.coleccion_mongo, src.tabla_sql_destino, src.modulo, src.prioridad, src.estrategia);
GO

```