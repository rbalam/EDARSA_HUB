# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T16:18:33.215366
- Modo: `migrate`
- Servidor: `<REDACTED_EDARSAHUB_SQL_HOST>`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/migrations/017_registrar_inteligencia_comercial_y_transicionales.sql`

## Resultado
ERROR

## Detalle
```text
Error ejecutando SQL. Se hizo rollback. Detalle: (207, b"Invalid column name 'fecha_registro'.DB-Lib error message 20018, severity 16:\nGeneral SQL Server error: Check messages from the SQL Server\n")
```

## SQL ejecutado / revisado
```sql
/* ============================================================
   MIGRACIÓN: Registrar Módulo INTELIGENCIA_COMERCIAL y
   Marcar Sistema_RBAC_* como TRANSICIONAL
   
   Ejecutar con: edarsahub_sql_runner.py --mode migrate
   ============================================================ */

-- =============================================================
-- BLOQUE 1: Registrar módulo INTELIGENCIA_COMERCIAL
-- =============================================================

-- Verificar si ya existe
IF NOT EXISTS (
    SELECT 1 FROM Usuario_Modulos 
    WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL'
)
BEGIN
    INSERT INTO Usuario_Modulos (
        ModuloPadreID,
        CodigoModulo,
        NombreModulo,
        Descripcion,
        TipoModulo,
        Ruta,
        Icono,
        OrdenMenu,
        EsVisibleMenu,
        RequiereAutorizacion,
        Activo,
        FechaAlta
    ) VALUES (
        NULL,
        'INTELIGENCIA_COMERCIAL',
        'Inteligencia Comercial',
        'Portal de Inteligencia Comercial - KPIs, Ventas, Análisis y Comparativos SQL-first',
        'MODULO',
        '/comercial/inteligencia',
        'chart-line',
        40,
        1, -- EsVisibleMenu
        0, -- RequiereAutorizacion (lectura general)
        1, -- Activo
        GETDATE()
    );
    
    PRINT 'Módulo INTELIGENCIA_COMERCIAL registrado correctamente.';
END
ELSE
BEGIN
    PRINT 'Módulo INTELIGENCIA_COMERCIAL ya existe - sin cambios.';
END

-- =============================================================
-- BLOQUE 2: Registrar tablas Sistema_RBAC_* en Gobierno como TRANSICIONAL
-- =============================================================

-- Sistema_RBAC_Permisos
IF NOT EXISTS (
    SELECT 1 FROM Sistema_Gobierno_Tablas 
    WHERE nombre_tabla = 'Sistema_RBAC_Permisos'
)
BEGIN
    INSERT INTO Sistema_Gobierno_Tablas (
        esquema, nombre_tabla, modulo, categoria, estado,
        fuente_verdad, tabla_reemplazo, observaciones, fecha_registro
    ) VALUES (
        'dbo', 'Sistema_RBAC_Permisos', 'AUTH', 'TRANSICIONAL', 'DEPRECADA',
        'N', 'Usuario_Acciones + Usuario_PermisosRolModulo',
        'Esquema antiguo RBAC. No usar para nuevos desarrollos. Migrar a Usuario_*.',
        GETDATE()
    );
    PRINT 'Sistema_RBAC_Permisos registrada como TRANSICIONAL.';
END

-- Sistema_RBAC_Roles
IF NOT EXISTS (
    SELECT 1 FROM Sistema_Gobierno_Tablas 
    WHERE nombre_tabla = 'Sistema_RBAC_Roles'
)
BEGIN
    INSERT INTO Sistema_Gobierno_Tablas (
        esquema, nombre_tabla, modulo, categoria, estado,
        fuente_verdad, tabla_reemplazo, observaciones, fecha_registro
    ) VALUES (
        'dbo', 'Sistema_RBAC_Roles', 'AUTH', 'TRANSICIONAL', 'DEPRECADA',
        'N', 'Usuario_Roles',
        'Esquema antiguo RBAC. No usar para nuevos desarrollos. Migrar a Usuario_Roles.',
        GETDATE()
    );
    PRINT 'Sistema_RBAC_Roles registrada como TRANSICIONAL.';
END

-- Sistema_RBAC_RolesPermisos
IF NOT EXISTS (
    SELECT 1 FROM Sistema_Gobierno_Tablas 
    WHERE nombre_tabla = 'Sistema_RBAC_RolesPermisos'
)
BEGIN
    INSERT INTO Sistema_Gobierno_Tablas (
        esquema, nombre_tabla, modulo, categoria, estado,
        fuente_verdad, tabla_reemplazo, observaciones, fecha_registro
    ) VALUES (
        'dbo', 'Sistema_RBAC_RolesPermisos', 'AUTH', 'TRANSICIONAL', 'DEPRECADA',
        'N', 'Usuario_PermisosRolModulo',
        'Esquema antiguo RBAC. No usar para nuevos desarrollos. Migrar a Usuario_PermisosRolModulo.',
        GETDATE()
    );
    PRINT 'Sistema_RBAC_RolesPermisos registrada como TRANSICIONAL.';
END

-- =============================================================
-- BLOQUE 3: Registrar vistas canónicas de Inteligencia Comercial
-- =============================================================

-- Comercial_Inteligencia_VW_KPIsEjecutivos
IF NOT EXISTS (
    SELECT 1 FROM Sistema_Gobierno_Tablas 
    WHERE nombre_tabla = 'Comercial_Inteligencia_VW_KPIsEjecutivos'
)
BEGIN
    INSERT INTO Sistema_Gobierno_Tablas (
        esquema, nombre_tabla, modulo, categoria, estado,
        fuente_verdad, tabla_reemplazo, observaciones, fecha_registro
    ) VALUES (
        'dbo', 'Comercial_Inteligencia_VW_KPIsEjecutivos', 'COMERCIAL', 'VISTA', 'ACTIVA',
        'S', NULL,
        'Vista canónica para KPIs ejecutivos de Inteligencia Comercial. SQL-first, sin conexiones live.',
        GETDATE()
    );
    PRINT 'Vista Comercial_Inteligencia_VW_KPIsEjecutivos registrada.';
END

-- Comercial_Inteligencia_VW_SyncStatus
IF NOT EXISTS (
    SELECT 1 FROM Sistema_Gobierno_Tablas 
    WHERE nombre_tabla = 'Comercial_Inteligencia_VW_SyncStatus'
)
BEGIN
    INSERT INTO Sistema_Gobierno_Tablas (
        esquema, nombre_tabla, modulo, categoria, estado,
        fuente_verdad, tabla_reemplazo, observaciones, fecha_registro
    ) VALUES (
        'dbo', 'Comercial_Inteligencia_VW_SyncStatus', 'COMERCIAL', 'VISTA', 'ACTIVA',
        'S', NULL,
        'Vista de monitoreo de frescura de datos sincronizados.',
        GETDATE()
    );
    PRINT 'Vista Comercial_Inteligencia_VW_SyncStatus registrada.';
END

-- Comercial_Ventas_Dia_Abiertas_v2
IF NOT EXISTS (
    SELECT 1 FROM Sistema_Gobierno_Tablas 
    WHERE nombre_tabla = 'Comercial_Ventas_Dia_Abiertas_v2'
)
BEGIN
    INSERT INTO Sistema_Gobierno_Tablas (
        esquema, nombre_tabla, modulo, categoria, estado,
        fuente_verdad, tabla_reemplazo, observaciones, fecha_registro
    ) VALUES (
        'dbo', 'Comercial_Ventas_Dia_Abiertas_v2', 'COMERCIAL', 'CORE', 'ACTIVA',
        'S', NULL,
        'Tabla de ventas diarias por unidad de negocio.',
        GETDATE()
    );
    PRINT 'Tabla Comercial_Ventas_Dia_Abiertas_v2 registrada.';
END

-- Sync_Sales
IF NOT EXISTS (
    SELECT 1 FROM Sistema_Gobierno_Tablas 
    WHERE nombre_tabla = 'Sync_Sales'
)
BEGIN
    INSERT INTO Sistema_Gobierno_Tablas (
        esquema, nombre_tabla, modulo, categoria, estado,
        fuente_verdad, tabla_reemplazo, observaciones, fecha_registro
    ) VALUES (
        'dbo', 'Sync_Sales', 'COMERCIAL', 'SYNC', 'ACTIVA',
        'S', NULL,
        'Tabla de sincronización de ventas granulares (tickets/productos). Alimentada por jobs.',
        GETDATE()
    );
    PRINT 'Tabla Sync_Sales registrada.';
END

-- Sync_PAX_Detalle
IF NOT EXISTS (
    SELECT 1 FROM Sistema_Gobierno_Tablas 
    WHERE nombre_tabla = 'Sync_PAX_Detalle'
)
BEGIN
    INSERT INTO Sistema_Gobierno_Tablas (
        esquema, nombre_tabla, modulo, categoria, estado,
        fuente_verdad, tabla_reemplazo, observaciones, fecha_registro
    ) VALUES (
        'dbo', 'Sync_PAX_Detalle', 'COMERCIAL', 'SYNC', 'ACTIVA',
        'S', NULL,
        'Tabla de sincronización de PAX detallado. Alimentada por jobs.',
        GETDATE()
    );
    PRINT 'Tabla Sync_PAX_Detalle registrada.';
END

-- Unidades_Negocio
IF NOT EXISTS (
    SELECT 1 FROM Sistema_Gobierno_Tablas 
    WHERE nombre_tabla = 'Unidades_Negocio'
)
BEGIN
    INSERT INTO Sistema_Gobierno_Tablas (
        esquema, nombre_tabla, modulo, categoria, estado,
        fuente_verdad, tabla_reemplazo, observaciones, fecha_registro
    ) VALUES (
        'dbo', 'Unidades_Negocio', 'SISTEMA', 'CORE', 'ACTIVA',
        'S', NULL,
        'Catálogo maestro de unidades de negocio (restaurantes, sucursales).',
        GETDATE()
    );
    PRINT 'Tabla Unidades_Negocio registrada.';
END

-- =============================================================
-- VERIFICACIÓN FINAL
-- =============================================================
SELECT 
    'RESULTADO_FINAL' AS diagnostico,
    COUNT(*) AS total_tablas_gobierno
FROM Sistema_Gobierno_Tablas;

SELECT 
    nombre_tabla, modulo, categoria, estado, fuente_verdad
FROM Sistema_Gobierno_Tablas
WHERE nombre_tabla IN (
    'Sistema_RBAC_Permisos', 'Sistema_RBAC_Roles', 'Sistema_RBAC_RolesPermisos',
    'Comercial_Inteligencia_VW_KPIsEjecutivos', 'Comercial_Inteligencia_VW_SyncStatus',
    'Comercial_Ventas_Dia_Abiertas_v2', 'Sync_Sales', 'Sync_PAX_Detalle', 'Unidades_Negocio'
)
ORDER BY nombre_tabla;

SELECT 
    'MODULO_INTELIGENCIA_COMERCIAL' AS verificacion,
    ModuloID, CodigoModulo, NombreModulo, Activo
FROM Usuario_Modulos
WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL';

```