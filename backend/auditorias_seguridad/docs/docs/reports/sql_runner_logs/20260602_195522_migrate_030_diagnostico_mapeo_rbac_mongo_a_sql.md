# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T19:55:22.976345
- Modo: `migrate`
- Servidor: `<REDACTED_EDARSAHUB_SQL_HOST>`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/migrations/030_diagnostico_mapeo_rbac_mongo_a_sql.sql`

## Resultado
ERROR

## Detalle
```text
Error ejecutando SQL. Se hizo rollback. Detalle: Cannot commit transaction: (208, b"Invalid object name 'dbo.Global_Cat_Empresas'.DB-Lib error message 20018, severity 16:\nGeneral SQL Server error: Check messages from the SQL Server\n")
```

## SQL ejecutado / revisado
```sql
/* ============================================================
   EDARSAHUB - DIAGNÓSTICO RBAC MongoDB → Usuario_* SQL
   Archivo: 030_diagnostico_mapeo_rbac_mongo_a_sql.sql

   OBJETIVO:
   - Diagnosticar estructura SQL canónica Usuario_*
   - Confirmar tablas destino
   - Confirmar columnas disponibles
   - No migrar usuarios
   - No insertar usuarios
   - No tocar MongoDB
   ============================================================ */

SET NOCOUNT ON;

PRINT '============================================================';
PRINT 'DIAGNÓSTICO RBAC MongoDB → Usuario_* SQL';
PRINT '============================================================';


/* ============================================================
   1. Validar tablas SQL canónicas Usuario_*
   ============================================================ */

SELECT
    t.TABLE_SCHEMA,
    t.TABLE_NAME,
    t.TABLE_TYPE,
    CASE
        WHEN t.TABLE_NAME IN (
            'Usuario_Catalogo',
            'Usuario_Roles',
            'Usuario_RolesAsignacion',
            'Usuario_Modulos',
            'Usuario_Acciones',
            'Usuario_PermisosRolModulo',
            'Usuario_EmpresasAsignacion',
            'Usuario_SucursalesAsignacion',
            'Usuario_ServidoresAsignacion',
            'Usuario_LogRBACVerificacion'
        )
        THEN 'DESTINO_RBAC_CANONICO'
        ELSE 'USUARIO_RELACIONADA'
    END AS clasificacion
FROM INFORMATION_SCHEMA.TABLES t
WHERE t.TABLE_NAME LIKE 'Usuario_%'
ORDER BY t.TABLE_NAME;


/* ============================================================
   2. Columnas de tablas destino Usuario_*
   ============================================================ */

SELECT
    c.TABLE_SCHEMA,
    c.TABLE_NAME,
    c.COLUMN_NAME,
    c.DATA_TYPE,
    c.CHARACTER_MAXIMUM_LENGTH,
    c.NUMERIC_PRECISION,
    c.NUMERIC_SCALE,
    c.IS_NULLABLE,
    c.ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS c
WHERE c.TABLE_NAME IN (
    'Usuario_Catalogo',
    'Usuario_Roles',
    'Usuario_RolesAsignacion',
    'Usuario_Modulos',
    'Usuario_Acciones',
    'Usuario_PermisosRolModulo',
    'Usuario_EmpresasAsignacion',
    'Usuario_SucursalesAsignacion',
    'Usuario_ServidoresAsignacion',
    'Usuario_LogRBACVerificacion'
)
ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION;


/* ============================================================
   3. Conteo de registros actuales por tabla destino
   ============================================================ */

DECLARE @sql NVARCHAR(MAX) = N'';

SELECT @sql = @sql + '
SELECT ''' + QUOTENAME(s.name) + '.' + QUOTENAME(t.name) + ''' AS tabla, COUNT(*) AS registros FROM ' 
    + QUOTENAME(s.name) + '.' + QUOTENAME(t.name) + ' UNION ALL'
FROM sys.tables t
INNER JOIN sys.schemas s
    ON t.schema_id = s.schema_id
WHERE t.name IN (
    'Usuario_Catalogo',
    'Usuario_Roles',
    'Usuario_RolesAsignacion',
    'Usuario_Modulos',
    'Usuario_Acciones',
    'Usuario_PermisosRolModulo',
    'Usuario_EmpresasAsignacion',
    'Usuario_SucursalesAsignacion',
    'Usuario_ServidoresAsignacion',
    'Usuario_LogRBACVerificacion'
);

IF LEN(@sql) > 0
BEGIN
    SET @sql = LEFT(@sql, LEN(@sql) - LEN(' UNION ALL'));
    EXEC sp_executesql @sql;
END;


/* ============================================================
   4. Validar módulo INTELIGENCIA_COMERCIAL
   ============================================================ */

SELECT
    *
FROM dbo.Usuario_Modulos
WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL';


/* ============================================================
   5. Validar permisos activos de INTELIGENCIA_COMERCIAL
   ============================================================ */

DECLARE @ModuloID INT;

SELECT @ModuloID = ModuloID
FROM dbo.Usuario_Modulos
WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL';

SELECT
    r.CodigoRol,
    r.NombreRol,
    a.CodigoAccion,
    a.NombreAccion,
    prm.Activo
FROM dbo.Usuario_PermisosRolModulo prm
INNER JOIN dbo.Usuario_Roles r
    ON r.RolID = prm.RolID
INNER JOIN dbo.Usuario_Acciones a
    ON a.AccionID = prm.AccionID
WHERE prm.ModuloID = @ModuloID
ORDER BY prm.Activo DESC, r.CodigoRol, a.CodigoAccion;


/* ============================================================
   6. Validar roles ideales existentes
   ============================================================ */

SELECT
    r.RolID,
    r.CodigoRol,
    r.NombreRol,
    r.Activo
FROM dbo.Usuario_Roles r
WHERE r.CodigoRol IN (
    'SUPERADMIN',
    'ADMIN_COMERCIAL',
    'DIRECCION',
    'GERENTE_UNIDAD',
    'ANALISTA_COMERCIAL',
    'VISOR_COMERCIAL',
    'CONFIGURADOR_COMERCIAL'
)
ORDER BY r.CodigoRol;


/* ============================================================
   7. Validar roles CRM sin acceso activo a IC
   ============================================================ */

SELECT
    r.CodigoRol,
    a.CodigoAccion,
    prm.Activo
FROM dbo.Usuario_PermisosRolModulo prm
INNER JOIN dbo.Usuario_Roles r
    ON r.RolID = prm.RolID
INNER JOIN dbo.Usuario_Acciones a
    ON a.AccionID = prm.AccionID
WHERE prm.ModuloID = @ModuloID
  AND r.CodigoRol IN ('CRM_ADMIN', 'CRM_EJEC', 'CRM_AUDIT')
ORDER BY r.CodigoRol, a.CodigoAccion;


/* ============================================================
   8. Validar empresas, sucursales y servidores SQL destino
   ============================================================ */

SELECT
    'Global_Cat_Empresas' AS tabla,
    COUNT(*) AS registros
FROM dbo.Global_Cat_Empresas;

SELECT
    'Unidades_Negocio' AS tabla,
    COUNT(*) AS registros
FROM dbo.Unidades_Negocio;

SELECT
    'Servidores_Conexiones' AS tabla,
    COUNT(*) AS registros
FROM dbo.Servidores_Conexiones;

IF OBJECT_ID('dbo.RH_Cat_Sucursales', 'U') IS NOT NULL
BEGIN
    SELECT
        'RH_Cat_Sucursales' AS tabla,
        COUNT(*) AS registros
    FROM dbo.RH_Cat_Sucursales;
END;


/* ============================================================
   9. Matriz destino sugerida Mongo → SQL
   ============================================================ */

SELECT
    *
FROM (
    VALUES
    ('users', 'Usuario_Catalogo', 'Usuarios/RBAC', 'P0', 'Mapear usuarios por email/login. No migrar todavía.'),
    ('rbac_roles', 'Usuario_Roles', 'Usuarios/RBAC', 'P0', 'Mapear roles por código/nombre. Usuario_Roles es canónico.'),
    ('rbac_usuarios_roles', 'Usuario_RolesAsignacion', 'Usuarios/RBAC', 'P0', 'Mapear asignaciones usuario-rol. Requiere usuarios SQL validados.'),
    ('rbac_permisos', 'Usuario_PermisosRolModulo', 'Usuarios/RBAC', 'P0', 'Mapear permisos por módulo/acción. No usar Sistema_RBAC_* como destino final.'),
    ('rbac_audit_log', 'Usuario_LogRBACVerificacion', 'Usuarios/RBAC/Auditoría', 'P1', 'Migrar logs solo después de usuarios y roles.'),
    ('empresas', 'Global_Cat_Empresas', 'Global', 'P0', 'Mapear empresas por RFC/código/nombre.'),
    ('sucursales_catalogo', 'RH_Cat_Sucursales / Unidades_Negocio', 'Global/RH/Unidades', 'P1', 'Validar destino exacto por tipo de sucursal.'),
    ('sucursal_servidor_map', 'Unidades_Negocio / Servidores_Conexiones', 'Sistema/Unidades', 'P0', 'Mapear unidad-servidor desde SQL.')
) AS m(
    coleccion_mongo,
    tabla_sql_destino,
    modulo,
    prioridad,
    regla_mapeo
)
ORDER BY prioridad, coleccion_mongo;


/* ============================================================
   10. Registrar evidencia en Sistema_Migracion_MongoSQL_Mapeo
       Solo si la tabla existe. No migra datos.
   ============================================================ */

IF OBJECT_ID('dbo.Sistema_Migracion_MongoSQL_Mapeo', 'U') IS NOT NULL
BEGIN
    MERGE dbo.Sistema_Migracion_MongoSQL_Mapeo AS tgt
    USING (
        SELECT 'users' AS coleccion_mongo, 'Usuario_Catalogo' AS tabla_sql_destino, 'Usuarios/RBAC' AS modulo, 'P0' AS prioridad, 'PENDIENTE_DIAGNOSTICO' AS estado, 'Diagnosticar usuarios por email/login antes de migrar.' AS estrategia
        UNION ALL SELECT 'rbac_roles', 'Usuario_Roles', 'Usuarios/RBAC', 'P0', 'PENDIENTE_DIAGNOSTICO', 'Mapear roles Mongo contra Usuario_Roles.'
        UNION ALL SELECT 'rbac_usuarios_roles', 'Usuario_RolesAsignacion', 'Usuarios/RBAC', 'P0', 'PENDIENTE_DIAGNOSTICO', 'Mapear asignaciones solo después de validar usuarios.'
        UNION ALL SELECT 'rbac_permisos', 'Usuario_PermisosRolModulo', 'Usuarios/RBAC', 'P0', 'PENDIENTE_DIAGNOSTICO', 'Mapear permisos Mongo contra módulo/acción SQL.'
        UNION ALL SELECT 'rbac_audit_log', 'Usuario_LogRBACVerificacion', 'Usuarios/RBAC/Auditoría', 'P1', 'PENDIENTE_DIAGNOSTICO', 'Migrar logs después de usuarios/roles.'
    ) AS src
    ON tgt.coleccion_mongo = src.coleccion_mongo
    WHEN MATCHED THEN
        UPDATE SET
            tabla_sql_destino = src.tabla_sql_destino,
            modulo = src.modulo,
            prioridad = src.prioridad,
            estado = src.estado,
            estrategia = src.estrategia
    WHEN NOT MATCHED THEN
        INSERT (
            coleccion_mongo,
            tabla_sql_destino,
            modulo,
            prioridad,
            estado,
            estrategia
        )
        VALUES (
            src.coleccion_mongo,
            src.tabla_sql_destino,
            src.modulo,
            src.prioridad,
            src.estado,
            src.estrategia
        );
END;


/* ============================================================
   11. Confirmación final
   ============================================================ */

SELECT
    'DIAGNOSTICO_RBAC_MONGO_A_SQL_COMPLETADO' AS resultado,
    SYSDATETIME() AS fecha_ejecucion,
    'No se migraron usuarios. No se modificó MongoDB.' AS nota;

```