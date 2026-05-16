-- =============================================================================
-- EDARSA HUB - CATÁLOGO MAESTRO DE SISTEMAS Y CAPACIDADES
-- SEED FASE 3: Carga Inicial de Datos
-- =============================================================================
-- 
-- OBJETIVO: Poblar las tablas de capacidades con sistemas existentes.
-- REGLAS: Idempotente (usa MERGE), no duplica datos.
-- DEPENDENCIA: DDL FASE 2 debe estar ejecutado primero.
--
-- FECHA: 2025-12-XX
-- AUTOR: Arquitecto DBA
-- =============================================================================

USE EDARSAHUB;
GO

-- =============================================================================
-- PASO 1: VERIFICAR PREREQUISITOS
-- =============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Sistema_Capacidades')
BEGIN
    RAISERROR('ERROR: Tabla Sistema_Capacidades no existe. Ejecutar DDL FASE 2 primero.', 16, 1);
    RETURN;
END

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Sistema_Tipos')
BEGIN
    RAISERROR('ERROR: Tabla Sistema_Tipos no existe. Verificar esquema EDARSAHUB.', 16, 1);
    RETURN;
END

PRINT 'Prerequisitos verificados. Iniciando SEED...';
GO


-- =============================================================================
-- PASO 2: OBTENER IDs DE SISTEMAS EXISTENTES
-- =============================================================================

DECLARE @ID_SOFTRESTAURANT INT;
DECLARE @ID_MPRO INT;
DECLARE @ID_SR_ENTERPRISE INT;
DECLARE @ID_SQLSERVER_GENERIC INT;
DECLARE @ID_EDARSAHUB INT;

SELECT @ID_SOFTRESTAURANT = SistemaTipoID FROM Sistema_Tipos WHERE CodigoSistema = 'SOFTRESTAURANT';
SELECT @ID_MPRO = SistemaTipoID FROM Sistema_Tipos WHERE CodigoSistema = 'MPRO' OR CodigoSistema = 'MANAGEMENTPRO';
SELECT @ID_SR_ENTERPRISE = SistemaTipoID FROM Sistema_Tipos WHERE CodigoSistema = 'SOFTRESTAURANT_ENTERPRISE';
SELECT @ID_SQLSERVER_GENERIC = SistemaTipoID FROM Sistema_Tipos WHERE CodigoSistema = 'SQLSERVER_GENERIC';
SELECT @ID_EDARSAHUB = SistemaTipoID FROM Sistema_Tipos WHERE CodigoSistema = 'EDARSAHUB' OR CodigoSistema = 'EDARSAHUB_SQL';

PRINT 'IDs de sistemas obtenidos:';
PRINT '  SOFTRESTAURANT: ' + ISNULL(CAST(@ID_SOFTRESTAURANT AS VARCHAR), 'NO EXISTE');
PRINT '  MPRO: ' + ISNULL(CAST(@ID_MPRO AS VARCHAR), 'NO EXISTE');
PRINT '  SR_ENTERPRISE: ' + ISNULL(CAST(@ID_SR_ENTERPRISE AS VARCHAR), 'NO EXISTE');
PRINT '  SQLSERVER_GENERIC: ' + ISNULL(CAST(@ID_SQLSERVER_GENERIC AS VARCHAR), 'NO EXISTE');
PRINT '  EDARSAHUB: ' + ISNULL(CAST(@ID_EDARSAHUB AS VARCHAR), 'NO EXISTE');


-- =============================================================================
-- PASO 3: INSERTAR CAPACIDADES PARA SOFTRESTAURANT
-- =============================================================================

IF @ID_SOFTRESTAURANT IS NOT NULL
BEGIN
    PRINT '';
    PRINT 'Insertando capacidades para SOFTRESTAURANT...';
    
    -- Capacidades de Explorador BD
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_SOFTRESTAURANT AND CodigoCapacidad = 'EXPLORADOR_BD')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_SOFTRESTAURANT, 'EXPLORADOR_BD', 'Explorador de Base de Datos', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_SOFTRESTAURANT AND CodigoCapacidad = 'EXPLORADOR_TABLAS')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_SOFTRESTAURANT, 'EXPLORADOR_TABLAS', 'Listar tablas de base de datos', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_SOFTRESTAURANT AND CodigoCapacidad = 'EXPLORADOR_COLUMNAS')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_SOFTRESTAURANT, 'EXPLORADOR_COLUMNAS', 'Listar columnas de tablas', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_SOFTRESTAURANT AND CodigoCapacidad = 'EXPLORADOR_PREVIEW')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_SOFTRESTAURANT, 'EXPLORADOR_PREVIEW', 'Preview de datos de tabla', 1, 0);
    
    -- Capacidades de Sync
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_SOFTRESTAURANT AND CodigoCapacidad = 'SYNC_VENTAS_HISTORICAS')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_SOFTRESTAURANT, 'SYNC_VENTAS_HISTORICAS', 'Sincronización de ventas históricas', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_SOFTRESTAURANT AND CodigoCapacidad = 'SYNC_VENTAS_POR_HORA')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_SOFTRESTAURANT, 'SYNC_VENTAS_POR_HORA', 'Sincronización de ventas por hora', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_SOFTRESTAURANT AND CodigoCapacidad = 'SYNC_VENTAS_DIA_SEMANA')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_SOFTRESTAURANT, 'SYNC_VENTAS_DIA_SEMANA', 'Sincronización de ventas por día de semana', 1, 0);
    
    -- Capacidades de Ventas
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_SOFTRESTAURANT AND CodigoCapacidad = 'VENTAS_DIA')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_SOFTRESTAURANT, 'VENTAS_DIA', 'KPIs de ventas del día', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_SOFTRESTAURANT AND CodigoCapacidad = 'VENTAS_PERIODO')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_SOFTRESTAURANT, 'VENTAS_PERIODO', 'KPIs de ventas por período', 1, 0);
    
    -- Capacidades de Módulos
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_SOFTRESTAURANT AND CodigoCapacidad = 'COMPRAS')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_SOFTRESTAURANT, 'COMPRAS', 'Módulo de compras', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_SOFTRESTAURANT AND CodigoCapacidad = 'INVENTARIOS')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_SOFTRESTAURANT, 'INVENTARIOS', 'Módulo de inventarios', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_SOFTRESTAURANT AND CodigoCapacidad = 'CORTES_Z')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_SOFTRESTAURANT, 'CORTES_Z', 'Cortes de caja Z', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_SOFTRESTAURANT AND CodigoCapacidad = 'PROPINAS_TPV')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_SOFTRESTAURANT, 'PROPINAS_TPV', 'Propinas por TPV', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_SOFTRESTAURANT AND CodigoCapacidad = 'CATALOGO_SQL')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_SOFTRESTAURANT, 'CATALOGO_SQL', 'Catálogo de consultas SQL', 1, 0);
    
    PRINT '  Capacidades SOFTRESTAURANT insertadas.';
END


-- =============================================================================
-- PASO 4: INSERTAR CAPACIDADES PARA MPRO (ManagementPro)
-- =============================================================================

IF @ID_MPRO IS NOT NULL
BEGIN
    PRINT '';
    PRINT 'Insertando capacidades para MPRO...';
    
    -- Capacidades de Explorador BD
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_MPRO AND CodigoCapacidad = 'EXPLORADOR_BD')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_MPRO, 'EXPLORADOR_BD', 'Explorador de Base de Datos', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_MPRO AND CodigoCapacidad = 'EXPLORADOR_TABLAS')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_MPRO, 'EXPLORADOR_TABLAS', 'Listar tablas de base de datos', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_MPRO AND CodigoCapacidad = 'EXPLORADOR_COLUMNAS')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_MPRO, 'EXPLORADOR_COLUMNAS', 'Listar columnas de tablas', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_MPRO AND CodigoCapacidad = 'EXPLORADOR_PREVIEW')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_MPRO, 'EXPLORADOR_PREVIEW', 'Preview de datos de tabla', 1, 0);
    
    -- Capacidades de Sync
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_MPRO AND CodigoCapacidad = 'SYNC_VENTAS_HISTORICAS')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_MPRO, 'SYNC_VENTAS_HISTORICAS', 'Sincronización de ventas históricas', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_MPRO AND CodigoCapacidad = 'SYNC_VENTAS_POR_HORA')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_MPRO, 'SYNC_VENTAS_POR_HORA', 'Sincronización de ventas por hora', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_MPRO AND CodigoCapacidad = 'SYNC_VENTAS_DIA_SEMANA')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_MPRO, 'SYNC_VENTAS_DIA_SEMANA', 'Sincronización de ventas por día de semana', 1, 0);
    
    -- Capacidades de Ventas
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_MPRO AND CodigoCapacidad = 'VENTAS_DIA')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_MPRO, 'VENTAS_DIA', 'KPIs de ventas del día', 1, 1);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_MPRO AND CodigoCapacidad = 'VENTAS_PERIODO')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_MPRO, 'VENTAS_PERIODO', 'KPIs de ventas por período', 1, 0);
    
    -- Capacidades de Módulos
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_MPRO AND CodigoCapacidad = 'COMPRAS')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_MPRO, 'COMPRAS', 'Módulo de compras', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_MPRO AND CodigoCapacidad = 'INVENTARIOS')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_MPRO, 'INVENTARIOS', 'Módulo de inventarios', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_MPRO AND CodigoCapacidad = 'CORTES_Z')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_MPRO, 'CORTES_Z', 'Cortes de caja Z', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_MPRO AND CodigoCapacidad = 'PROPINAS_TPV')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_MPRO, 'PROPINAS_TPV', 'Propinas por TPV', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_MPRO AND CodigoCapacidad = 'CATALOGO_SQL')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_MPRO, 'CATALOGO_SQL', 'Catálogo de consultas SQL', 1, 0);
    
    -- Capacidades EXCLUSIVAS de MPRO
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_MPRO AND CodigoCapacidad = 'SUCURSALES_VISIBLES')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_MPRO, 'SUCURSALES_VISIBLES', 'Configuración de sucursales visibles', 1, 0);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_Capacidades WHERE SistemaTipoID = @ID_MPRO AND CodigoCapacidad = 'CUENTAS_POR_PAGAR')
        INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto, RequiereApiLocal)
        VALUES (@ID_MPRO, 'CUENTAS_POR_PAGAR', 'Cuentas por pagar en Finanzas', 1, 0);
    
    PRINT '  Capacidades MPRO insertadas.';
END


-- =============================================================================
-- PASO 5: INSERTAR VARIANTES DE NOMBRES DE SISTEMAS
-- =============================================================================

IF EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Sistema_TiposVariantes')
BEGIN
    PRINT '';
    PRINT 'Insertando variantes de nombres de sistemas...';
    
    -- Variantes MPRO
    IF @ID_MPRO IS NOT NULL
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM Sistema_TiposVariantes WHERE VarianteNombre = 'MPRO')
            INSERT INTO Sistema_TiposVariantes (SistemaTipoID, VarianteNombre, EsCanonico) VALUES (@ID_MPRO, 'MPRO', 1);
        IF NOT EXISTS (SELECT 1 FROM Sistema_TiposVariantes WHERE VarianteNombre = 'MANAGEMENTPRO')
            INSERT INTO Sistema_TiposVariantes (SistemaTipoID, VarianteNombre, EsCanonico) VALUES (@ID_MPRO, 'MANAGEMENTPRO', 0);
        IF NOT EXISTS (SELECT 1 FROM Sistema_TiposVariantes WHERE VarianteNombre = 'MANAGEMENT_PRO')
            INSERT INTO Sistema_TiposVariantes (SistemaTipoID, VarianteNombre, EsCanonico) VALUES (@ID_MPRO, 'MANAGEMENT_PRO', 0);
        IF NOT EXISTS (SELECT 1 FROM Sistema_TiposVariantes WHERE VarianteNombre = 'MANAGMENT PRO')
            INSERT INTO Sistema_TiposVariantes (SistemaTipoID, VarianteNombre, EsCanonico) VALUES (@ID_MPRO, 'MANAGMENT PRO', 0);
        IF NOT EXISTS (SELECT 1 FROM Sistema_TiposVariantes WHERE VarianteNombre = 'MANAGMENTPRO')
            INSERT INTO Sistema_TiposVariantes (SistemaTipoID, VarianteNombre, EsCanonico) VALUES (@ID_MPRO, 'MANAGMENTPRO', 0);
    END
    
    -- Variantes SOFTRESTAURANT
    IF @ID_SOFTRESTAURANT IS NOT NULL
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM Sistema_TiposVariantes WHERE VarianteNombre = 'SOFTRESTAURANT')
            INSERT INTO Sistema_TiposVariantes (SistemaTipoID, VarianteNombre, EsCanonico) VALUES (@ID_SOFTRESTAURANT, 'SOFTRESTAURANT', 1);
        IF NOT EXISTS (SELECT 1 FROM Sistema_TiposVariantes WHERE VarianteNombre = 'SR')
            INSERT INTO Sistema_TiposVariantes (SistemaTipoID, VarianteNombre, EsCanonico) VALUES (@ID_SOFTRESTAURANT, 'SR', 0);
        IF NOT EXISTS (SELECT 1 FROM Sistema_TiposVariantes WHERE VarianteNombre = 'SOFT')
            INSERT INTO Sistema_TiposVariantes (SistemaTipoID, VarianteNombre, EsCanonico) VALUES (@ID_SOFTRESTAURANT, 'SOFT', 0);
        IF NOT EXISTS (SELECT 1 FROM Sistema_TiposVariantes WHERE VarianteNombre = 'SOFT_RESTAURANT')
            INSERT INTO Sistema_TiposVariantes (SistemaTipoID, VarianteNombre, EsCanonico) VALUES (@ID_SOFTRESTAURANT, 'SOFT_RESTAURANT', 0);
        IF NOT EXISTS (SELECT 1 FROM Sistema_TiposVariantes WHERE VarianteNombre = 'SOFTREST')
            INSERT INTO Sistema_TiposVariantes (SistemaTipoID, VarianteNombre, EsCanonico) VALUES (@ID_SOFTRESTAURANT, 'SOFTREST', 0);
    END
    
    PRINT '  Variantes de nombres insertadas.';
END


-- =============================================================================
-- PASO 6: INSERTAR VISIBILIDAD EN MÓDULOS
-- =============================================================================

PRINT '';
PRINT 'Insertando visibilidad de módulos...';

-- SOFTRESTAURANT - Módulos visibles
IF @ID_SOFTRESTAURANT IS NOT NULL
BEGIN
    IF NOT EXISTS (SELECT 1 FROM Sistema_ModulosVisibilidad WHERE SistemaTipoID = @ID_SOFTRESTAURANT AND CodigoModulo = 'EXPLORADOR_BD')
        INSERT INTO Sistema_ModulosVisibilidad (SistemaTipoID, CodigoModulo, DescripcionModulo, Visible, OrdenMenu)
        VALUES (@ID_SOFTRESTAURANT, 'EXPLORADOR_BD', 'Explorador de Base de Datos', 1, 10);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_ModulosVisibilidad WHERE SistemaTipoID = @ID_SOFTRESTAURANT AND CodigoModulo = 'COMERCIAL')
        INSERT INTO Sistema_ModulosVisibilidad (SistemaTipoID, CodigoModulo, DescripcionModulo, Visible, OrdenMenu)
        VALUES (@ID_SOFTRESTAURANT, 'COMERCIAL', 'Dashboard Comercial', 1, 1);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_ModulosVisibilidad WHERE SistemaTipoID = @ID_SOFTRESTAURANT AND CodigoModulo = 'COMPRAS')
        INSERT INTO Sistema_ModulosVisibilidad (SistemaTipoID, CodigoModulo, DescripcionModulo, Visible, OrdenMenu)
        VALUES (@ID_SOFTRESTAURANT, 'COMPRAS', 'Módulo de Compras', 1, 3);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_ModulosVisibilidad WHERE SistemaTipoID = @ID_SOFTRESTAURANT AND CodigoModulo = 'REPORTES')
        INSERT INTO Sistema_ModulosVisibilidad (SistemaTipoID, CodigoModulo, DescripcionModulo, Visible, OrdenMenu)
        VALUES (@ID_SOFTRESTAURANT, 'REPORTES', 'Reportes de Inventarios', 1, 5);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_ModulosVisibilidad WHERE SistemaTipoID = @ID_SOFTRESTAURANT AND CodigoModulo = 'FINANZAS')
        INSERT INTO Sistema_ModulosVisibilidad (SistemaTipoID, CodigoModulo, DescripcionModulo, Visible, OrdenMenu)
        VALUES (@ID_SOFTRESTAURANT, 'FINANZAS', 'Finanzas y Tesorería', 1, 4);
END

-- MPRO - Módulos visibles
IF @ID_MPRO IS NOT NULL
BEGIN
    IF NOT EXISTS (SELECT 1 FROM Sistema_ModulosVisibilidad WHERE SistemaTipoID = @ID_MPRO AND CodigoModulo = 'EXPLORADOR_BD')
        INSERT INTO Sistema_ModulosVisibilidad (SistemaTipoID, CodigoModulo, DescripcionModulo, Visible, OrdenMenu)
        VALUES (@ID_MPRO, 'EXPLORADOR_BD', 'Explorador de Base de Datos', 1, 10);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_ModulosVisibilidad WHERE SistemaTipoID = @ID_MPRO AND CodigoModulo = 'COMERCIAL')
        INSERT INTO Sistema_ModulosVisibilidad (SistemaTipoID, CodigoModulo, DescripcionModulo, Visible, OrdenMenu)
        VALUES (@ID_MPRO, 'COMERCIAL', 'Dashboard Comercial', 1, 1);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_ModulosVisibilidad WHERE SistemaTipoID = @ID_MPRO AND CodigoModulo = 'COMPRAS')
        INSERT INTO Sistema_ModulosVisibilidad (SistemaTipoID, CodigoModulo, DescripcionModulo, Visible, OrdenMenu)
        VALUES (@ID_MPRO, 'COMPRAS', 'Módulo de Compras', 1, 3);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_ModulosVisibilidad WHERE SistemaTipoID = @ID_MPRO AND CodigoModulo = 'REPORTES')
        INSERT INTO Sistema_ModulosVisibilidad (SistemaTipoID, CodigoModulo, DescripcionModulo, Visible, OrdenMenu)
        VALUES (@ID_MPRO, 'REPORTES', 'Reportes de Inventarios', 1, 5);
    
    IF NOT EXISTS (SELECT 1 FROM Sistema_ModulosVisibilidad WHERE SistemaTipoID = @ID_MPRO AND CodigoModulo = 'FINANZAS')
        INSERT INTO Sistema_ModulosVisibilidad (SistemaTipoID, CodigoModulo, DescripcionModulo, Visible, OrdenMenu)
        VALUES (@ID_MPRO, 'FINANZAS', 'Finanzas y Tesorería', 1, 4);
END

PRINT '  Visibilidad de módulos insertada.';


-- =============================================================================
-- VERIFICACIÓN POST-SEED
-- =============================================================================

PRINT '';
PRINT '=============================================================================';
PRINT 'VERIFICACIÓN POST-SEED';
PRINT '=============================================================================';

SELECT 'CAPACIDADES POR SISTEMA' AS Seccion;
SELECT 
    st.CodigoSistema,
    st.NombreSistema,
    COUNT(*) AS NumCapacidades
FROM Sistema_Capacidades sc
JOIN Sistema_Tipos st ON sc.SistemaTipoID = st.SistemaTipoID
WHERE sc.Activo = 1
GROUP BY st.CodigoSistema, st.NombreSistema
ORDER BY st.CodigoSistema;

SELECT 'DETALLE DE CAPACIDADES' AS Seccion;
SELECT 
    st.CodigoSistema,
    sc.CodigoCapacidad,
    sc.Descripcion,
    CASE WHEN sc.RequiereSqlDirecto = 1 THEN 'SQL' ELSE '' END +
    CASE WHEN sc.RequiereApiLocal = 1 THEN '+API' ELSE '' END AS Requisitos
FROM Sistema_Capacidades sc
JOIN Sistema_Tipos st ON sc.SistemaTipoID = st.SistemaTipoID
WHERE sc.Activo = 1
ORDER BY st.CodigoSistema, sc.CodigoCapacidad;

SELECT 'MÓDULOS VISIBLES POR SISTEMA' AS Seccion;
SELECT 
    st.CodigoSistema,
    smv.CodigoModulo,
    smv.DescripcionModulo,
    smv.OrdenMenu
FROM Sistema_ModulosVisibilidad smv
JOIN Sistema_Tipos st ON smv.SistemaTipoID = st.SistemaTipoID
WHERE smv.Activo = 1 AND smv.Visible = 1
ORDER BY st.CodigoSistema, smv.OrdenMenu;

PRINT '';
PRINT '=============================================================================';
PRINT 'SEED FASE 3 completado exitosamente.';
PRINT 'SIGUIENTE PASO: Implementar SystemCapabilityResolver en backend.';
PRINT '=============================================================================';
GO
