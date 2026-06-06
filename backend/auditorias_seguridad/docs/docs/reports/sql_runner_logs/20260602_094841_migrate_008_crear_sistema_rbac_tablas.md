# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T09:48:41.556650
- Modo: `migrate`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/migrations/008_crear_sistema_rbac_tablas.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 4
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
- Filas afectadas: 5


## SQL ejecutado / revisado
```sql
/* ============================================================
   MIGRACIÓN: Sistema RBAC - Tablas Base
   Script: 008_crear_sistema_rbac_tablas.sql
   Modo: migrate
   
   Crea estructura canónica RBAC:
   - Sistema_RBAC_Permisos
   - Sistema_RBAC_Roles
   - Sistema_RBAC_RolesPermisos
   ============================================================ */

-- 1. TABLA DE PERMISOS
IF OBJECT_ID('dbo.Sistema_RBAC_Permisos', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sistema_RBAC_Permisos (
        permiso_id UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
        codigo NVARCHAR(150) NOT NULL,
        nombre NVARCHAR(200) NOT NULL,
        modulo NVARCHAR(100) NOT NULL,
        descripcion NVARCHAR(500) NULL,
        activo BIT NOT NULL DEFAULT 1,
        fecha_alta DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        fecha_ultima_actualizacion DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );

    CREATE UNIQUE INDEX UX_Sistema_RBAC_Permisos_Codigo
    ON dbo.Sistema_RBAC_Permisos(codigo);
END;
GO

-- 2. TABLA DE ROLES
IF OBJECT_ID('dbo.Sistema_RBAC_Roles', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sistema_RBAC_Roles (
        rol_id UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
        codigo NVARCHAR(100) NOT NULL,
        nombre NVARCHAR(200) NOT NULL,
        descripcion NVARCHAR(500) NULL,
        es_sistema BIT NOT NULL DEFAULT 0,
        activo BIT NOT NULL DEFAULT 1,
        fecha_alta DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        fecha_ultima_actualizacion DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );

    CREATE UNIQUE INDEX UX_Sistema_RBAC_Roles_Codigo
    ON dbo.Sistema_RBAC_Roles(codigo);
END;
GO

-- 3. TABLA DE RELACIÓN ROLES-PERMISOS
IF OBJECT_ID('dbo.Sistema_RBAC_RolesPermisos', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sistema_RBAC_RolesPermisos (
        rol_permiso_id UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
        rol_id UNIQUEIDENTIFIER NOT NULL,
        permiso_id UNIQUEIDENTIFIER NOT NULL,
        activo BIT NOT NULL DEFAULT 1,
        fecha_alta DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        CONSTRAINT FK_RBAC_RolesPermisos_Rol FOREIGN KEY (rol_id)
            REFERENCES dbo.Sistema_RBAC_Roles(rol_id),
        CONSTRAINT FK_RBAC_RolesPermisos_Permiso FOREIGN KEY (permiso_id)
            REFERENCES dbo.Sistema_RBAC_Permisos(permiso_id)
    );

    CREATE UNIQUE INDEX UX_Sistema_RBAC_RolesPermisos
    ON dbo.Sistema_RBAC_RolesPermisos(rol_id, permiso_id);
END;
GO

-- 4. POBLAR PERMISOS DE INTELIGENCIA COMERCIAL
MERGE dbo.Sistema_RBAC_Permisos AS tgt
USING (
    SELECT 'INTELIGENCIA_COMERCIAL_VER' AS codigo, 'Ver Inteligencia Comercial' AS nombre, 'Comercial' AS modulo
    UNION ALL SELECT 'INTELIGENCIA_COMERCIAL_EXPORTAR', 'Exportar Inteligencia Comercial', 'Comercial'
    UNION ALL SELECT 'INTELIGENCIA_COMERCIAL_CONFIGURAR', 'Configurar Inteligencia Comercial', 'Comercial'
    UNION ALL SELECT 'INTELIGENCIA_COMERCIAL_SYNC', 'Ejecutar Sincronización Inteligencia Comercial', 'Comercial'
    UNION ALL SELECT 'INTELIGENCIA_COMERCIAL_ADMIN', 'Administrar Inteligencia Comercial', 'Comercial'
) AS src
ON tgt.codigo = src.codigo
WHEN MATCHED THEN
    UPDATE SET
        nombre = src.nombre,
        modulo = src.modulo,
        activo = 1,
        fecha_ultima_actualizacion = SYSDATETIME()
WHEN NOT MATCHED THEN
    INSERT (codigo, nombre, modulo, activo)
    VALUES (src.codigo, src.nombre, src.modulo, 1);
GO

```