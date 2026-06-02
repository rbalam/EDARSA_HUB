/* ============================================================
   MIGRACIÓN: Registrar Módulo INTELIGENCIA_COMERCIAL y
   Marcar Sistema_RBAC_* como TRANSICIONAL
   
   Ejecutar con: edarsahub_sql_runner.py --mode migrate
   ============================================================ */

-- =============================================================
-- BLOQUE 1: Registrar módulo INTELIGENCIA_COMERCIAL
-- =============================================================

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
        1,
        0,
        1,
        GETDATE()
    );
    
    PRINT 'Módulo INTELIGENCIA_COMERCIAL registrado correctamente.';
END
ELSE
BEGIN
    PRINT 'Módulo INTELIGENCIA_COMERCIAL ya existe - sin cambios.';
END

-- =============================================================
-- BLOQUE 2: Registrar tablas Sistema_RBAC_* como TRANSICIONAL
-- =============================================================

-- Sistema_RBAC_Permisos
IF NOT EXISTS (
    SELECT 1 FROM Sistema_Gobierno_Tablas 
    WHERE nombre_tabla = 'Sistema_RBAC_Permisos'
)
BEGIN
    INSERT INTO Sistema_Gobierno_Tablas (
        id, nombre_tabla, esquema, modulo, categoria, estado,
        fuente_verdad, tabla_reemplazo,
        permite_insert, permite_update, permite_delete,
        observaciones, fecha_alta, fecha_ultima_actualizacion
    ) VALUES (
        NEWID(),
        'Sistema_RBAC_Permisos', 'dbo', 'AUTH', 'TRANSICIONAL', 'DEPRECADA',
        'N', 'Usuario_Acciones + Usuario_PermisosRolModulo',
        0, 0, 0,
        'Esquema antiguo RBAC. No usar para nuevos desarrollos. Migrar a Usuario_*.',
        GETDATE(), GETDATE()
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
        id, nombre_tabla, esquema, modulo, categoria, estado,
        fuente_verdad, tabla_reemplazo,
        permite_insert, permite_update, permite_delete,
        observaciones, fecha_alta, fecha_ultima_actualizacion
    ) VALUES (
        NEWID(),
        'Sistema_RBAC_Roles', 'dbo', 'AUTH', 'TRANSICIONAL', 'DEPRECADA',
        'N', 'Usuario_Roles',
        0, 0, 0,
        'Esquema antiguo RBAC. No usar para nuevos desarrollos. Migrar a Usuario_Roles.',
        GETDATE(), GETDATE()
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
        id, nombre_tabla, esquema, modulo, categoria, estado,
        fuente_verdad, tabla_reemplazo,
        permite_insert, permite_update, permite_delete,
        observaciones, fecha_alta, fecha_ultima_actualizacion
    ) VALUES (
        NEWID(),
        'Sistema_RBAC_RolesPermisos', 'dbo', 'AUTH', 'TRANSICIONAL', 'DEPRECADA',
        'N', 'Usuario_PermisosRolModulo',
        0, 0, 0,
        'Esquema antiguo RBAC. No usar para nuevos desarrollos. Migrar a Usuario_PermisosRolModulo.',
        GETDATE(), GETDATE()
    );
    PRINT 'Sistema_RBAC_RolesPermisos registrada como TRANSICIONAL.';
END

-- =============================================================
-- BLOQUE 3: Registrar vistas y tablas canónicas de Inteligencia Comercial
-- =============================================================

-- Comercial_Inteligencia_VW_KPIsEjecutivos
IF NOT EXISTS (
    SELECT 1 FROM Sistema_Gobierno_Tablas 
    WHERE nombre_tabla = 'Comercial_Inteligencia_VW_KPIsEjecutivos'
)
BEGIN
    INSERT INTO Sistema_Gobierno_Tablas (
        id, nombre_tabla, esquema, modulo, categoria, estado,
        fuente_verdad, tabla_reemplazo,
        permite_insert, permite_update, permite_delete,
        observaciones, fecha_alta, fecha_ultima_actualizacion
    ) VALUES (
        NEWID(),
        'Comercial_Inteligencia_VW_KPIsEjecutivos', 'dbo', 'COMERCIAL', 'VISTA', 'ACTIVA',
        'S', NULL,
        0, 0, 0,
        'Vista canónica para KPIs ejecutivos de Inteligencia Comercial. SQL-first, sin conexiones live.',
        GETDATE(), GETDATE()
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
        id, nombre_tabla, esquema, modulo, categoria, estado,
        fuente_verdad, tabla_reemplazo,
        permite_insert, permite_update, permite_delete,
        observaciones, fecha_alta, fecha_ultima_actualizacion
    ) VALUES (
        NEWID(),
        'Comercial_Inteligencia_VW_SyncStatus', 'dbo', 'COMERCIAL', 'VISTA', 'ACTIVA',
        'S', NULL,
        0, 0, 0,
        'Vista de monitoreo de frescura de datos sincronizados.',
        GETDATE(), GETDATE()
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
        id, nombre_tabla, esquema, modulo, categoria, estado,
        fuente_verdad, tabla_reemplazo,
        permite_insert, permite_update, permite_delete,
        observaciones, fecha_alta, fecha_ultima_actualizacion
    ) VALUES (
        NEWID(),
        'Comercial_Ventas_Dia_Abiertas_v2', 'dbo', 'COMERCIAL', 'CORE', 'ACTIVA',
        'S', NULL,
        1, 1, 0,
        'Tabla de ventas diarias por unidad de negocio.',
        GETDATE(), GETDATE()
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
        id, nombre_tabla, esquema, modulo, categoria, estado,
        fuente_verdad, tabla_reemplazo,
        permite_insert, permite_update, permite_delete,
        observaciones, fecha_alta, fecha_ultima_actualizacion
    ) VALUES (
        NEWID(),
        'Sync_Sales', 'dbo', 'COMERCIAL', 'SYNC', 'ACTIVA',
        'S', NULL,
        1, 1, 0,
        'Tabla de sincronización de ventas granulares (tickets/productos). Alimentada por jobs.',
        GETDATE(), GETDATE()
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
        id, nombre_tabla, esquema, modulo, categoria, estado,
        fuente_verdad, tabla_reemplazo,
        permite_insert, permite_update, permite_delete,
        observaciones, fecha_alta, fecha_ultima_actualizacion
    ) VALUES (
        NEWID(),
        'Sync_PAX_Detalle', 'dbo', 'COMERCIAL', 'SYNC', 'ACTIVA',
        'S', NULL,
        1, 1, 0,
        'Tabla de sincronización de PAX detallado. Alimentada por jobs.',
        GETDATE(), GETDATE()
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
        id, nombre_tabla, esquema, modulo, categoria, estado,
        fuente_verdad, tabla_reemplazo,
        permite_insert, permite_update, permite_delete,
        observaciones, fecha_alta, fecha_ultima_actualizacion
    ) VALUES (
        NEWID(),
        'Unidades_Negocio', 'dbo', 'SISTEMA', 'CORE', 'ACTIVA',
        'S', NULL,
        1, 1, 0,
        'Catálogo maestro de unidades de negocio (restaurantes, sucursales).',
        GETDATE(), GETDATE()
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
