# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T10:11:12.027406
- Modo: `migrate`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 7
- Mensaje: Ejecución completada.

### Batch 1
- Tipo: Comando
- Filas afectadas: -1

### Batch 2
- Tipo: Comando
- Filas afectadas: -1

### Batch 3
- Tipo: Comando
- Filas afectadas: -1

### Batch 4
- Tipo: Comando
- Filas afectadas: -1

### Batch 5
- Tipo: Comando
- Filas afectadas: -1

### Batch 6
- Tipo: Comando
- Filas afectadas: -1

### Batch 7
- Tipo: Comando
- Filas afectadas: -1


## SQL ejecutado / revisado
```sql
/* ============================================================
   RBAC - ROLES BASE INTELIGENCIA COMERCIAL
   Script: 010_crear_rbac_roles_inteligencia_comercial.sql
   Modo: migrate
   
   EDARSAHUB SQL-FIRST
   Idempotente
   No crea usuarios
   No migra usuarios
   No toca MongoDB
   ============================================================ */

SET NOCOUNT ON;

-- ============================================================
-- 1. Crear roles base
-- ============================================================

MERGE dbo.Sistema_RBAC_Roles AS tgt
USING (
    SELECT 
        'SUPERADMIN' AS codigo,
        'Super Administrador' AS nombre,
        'Acceso total al sistema EDARSAHUB.' AS descripcion,
        1 AS es_sistema

    UNION ALL SELECT
        'ADMIN_COMERCIAL',
        'Administrador Comercial',
        'Administra el módulo Comercial e Inteligencia Comercial.',
        1

    UNION ALL SELECT
        'ANALISTA_COMERCIAL',
        'Analista Comercial',
        'Consulta y exporta reportes de Inteligencia Comercial.',
        1

    UNION ALL SELECT
        'GERENTE_UNIDAD',
        'Gerente de Unidad',
        'Consulta indicadores comerciales de su unidad autorizada.',
        1

    UNION ALL SELECT
        'VISOR_COMERCIAL',
        'Visor Comercial',
        'Consulta básica de Inteligencia Comercial.',
        1

    UNION ALL SELECT
        'CONFIGURADOR_COMERCIAL',
        'Configurador Comercial',
        'Configura parámetros y sincronización comercial.',
        1
) AS src
ON tgt.codigo = src.codigo
WHEN MATCHED THEN
    UPDATE SET
        tgt.nombre = src.nombre,
        tgt.descripcion = src.descripcion,
        tgt.es_sistema = src.es_sistema,
        tgt.activo = 1,
        tgt.fecha_ultima_actualizacion = SYSDATETIME()
WHEN NOT MATCHED THEN
    INSERT (
        codigo,
        nombre,
        descripcion,
        es_sistema,
        activo,
        fecha_alta,
        fecha_ultima_actualizacion
    )
    VALUES (
        src.codigo,
        src.nombre,
        src.descripcion,
        src.es_sistema,
        1,
        SYSDATETIME(),
        SYSDATETIME()
    );
GO


/* ============================================================
   2. Asignar permisos a SUPERADMIN
   ============================================================ */

INSERT INTO dbo.Sistema_RBAC_RolesPermisos (
    rol_id,
    permiso_id,
    activo,
    fecha_alta
)
SELECT
    r.rol_id,
    p.permiso_id,
    1,
    SYSDATETIME()
FROM dbo.Sistema_RBAC_Roles r
CROSS JOIN dbo.Sistema_RBAC_Permisos p
WHERE 
    r.codigo = 'SUPERADMIN'
    AND p.codigo IN (
        'INTELIGENCIA_COMERCIAL_VER',
        'INTELIGENCIA_COMERCIAL_EXPORTAR',
        'INTELIGENCIA_COMERCIAL_CONFIGURAR',
        'INTELIGENCIA_COMERCIAL_SYNC',
        'INTELIGENCIA_COMERCIAL_ADMIN'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM dbo.Sistema_RBAC_RolesPermisos rp
        WHERE rp.rol_id = r.rol_id
          AND rp.permiso_id = p.permiso_id
    );
GO


/* ============================================================
   3. Asignar permisos a ADMIN_COMERCIAL
   ============================================================ */

INSERT INTO dbo.Sistema_RBAC_RolesPermisos (
    rol_id,
    permiso_id,
    activo,
    fecha_alta
)
SELECT
    r.rol_id,
    p.permiso_id,
    1,
    SYSDATETIME()
FROM dbo.Sistema_RBAC_Roles r
CROSS JOIN dbo.Sistema_RBAC_Permisos p
WHERE 
    r.codigo = 'ADMIN_COMERCIAL'
    AND p.codigo IN (
        'INTELIGENCIA_COMERCIAL_VER',
        'INTELIGENCIA_COMERCIAL_EXPORTAR',
        'INTELIGENCIA_COMERCIAL_CONFIGURAR',
        'INTELIGENCIA_COMERCIAL_SYNC',
        'INTELIGENCIA_COMERCIAL_ADMIN'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM dbo.Sistema_RBAC_RolesPermisos rp
        WHERE rp.rol_id = r.rol_id
          AND rp.permiso_id = p.permiso_id
    );
GO


/* ============================================================
   4. Asignar permisos a ANALISTA_COMERCIAL
   ============================================================ */

INSERT INTO dbo.Sistema_RBAC_RolesPermisos (
    rol_id,
    permiso_id,
    activo,
    fecha_alta
)
SELECT
    r.rol_id,
    p.permiso_id,
    1,
    SYSDATETIME()
FROM dbo.Sistema_RBAC_Roles r
CROSS JOIN dbo.Sistema_RBAC_Permisos p
WHERE 
    r.codigo = 'ANALISTA_COMERCIAL'
    AND p.codigo IN (
        'INTELIGENCIA_COMERCIAL_VER',
        'INTELIGENCIA_COMERCIAL_EXPORTAR'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM dbo.Sistema_RBAC_RolesPermisos rp
        WHERE rp.rol_id = r.rol_id
          AND rp.permiso_id = p.permiso_id
    );
GO


/* ============================================================
   5. Asignar permisos a GERENTE_UNIDAD
   ============================================================ */

INSERT INTO dbo.Sistema_RBAC_RolesPermisos (
    rol_id,
    permiso_id,
    activo,
    fecha_alta
)
SELECT
    r.rol_id,
    p.permiso_id,
    1,
    SYSDATETIME()
FROM dbo.Sistema_RBAC_Roles r
CROSS JOIN dbo.Sistema_RBAC_Permisos p
WHERE 
    r.codigo = 'GERENTE_UNIDAD'
    AND p.codigo IN (
        'INTELIGENCIA_COMERCIAL_VER',
        'INTELIGENCIA_COMERCIAL_EXPORTAR'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM dbo.Sistema_RBAC_RolesPermisos rp
        WHERE rp.rol_id = r.rol_id
          AND rp.permiso_id = p.permiso_id
    );
GO


/* ============================================================
   6. Asignar permisos a VISOR_COMERCIAL
   ============================================================ */

INSERT INTO dbo.Sistema_RBAC_RolesPermisos (
    rol_id,
    permiso_id,
    activo,
    fecha_alta
)
SELECT
    r.rol_id,
    p.permiso_id,
    1,
    SYSDATETIME()
FROM dbo.Sistema_RBAC_Roles r
CROSS JOIN dbo.Sistema_RBAC_Permisos p
WHERE 
    r.codigo = 'VISOR_COMERCIAL'
    AND p.codigo IN (
        'INTELIGENCIA_COMERCIAL_VER'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM dbo.Sistema_RBAC_RolesPermisos rp
        WHERE rp.rol_id = r.rol_id
          AND rp.permiso_id = p.permiso_id
    );
GO


/* ============================================================
   7. Asignar permisos a CONFIGURADOR_COMERCIAL
   ============================================================ */

INSERT INTO dbo.Sistema_RBAC_RolesPermisos (
    rol_id,
    permiso_id,
    activo,
    fecha_alta
)
SELECT
    r.rol_id,
    p.permiso_id,
    1,
    SYSDATETIME()
FROM dbo.Sistema_RBAC_Roles r
CROSS JOIN dbo.Sistema_RBAC_Permisos p
WHERE 
    r.codigo = 'CONFIGURADOR_COMERCIAL'
    AND p.codigo IN (
        'INTELIGENCIA_COMERCIAL_VER',
        'INTELIGENCIA_COMERCIAL_CONFIGURAR',
        'INTELIGENCIA_COMERCIAL_SYNC'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM dbo.Sistema_RBAC_RolesPermisos rp
        WHERE rp.rol_id = r.rol_id
          AND rp.permiso_id = p.permiso_id
    );
GO

```