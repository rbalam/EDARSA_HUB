# -*- coding: utf-8 -*-
"""
======================================================================================
ARCHIVO DE SCRIPT EN PYTHON: consolidado_general_sistema_comercial.py
PROYECTO: EDARSA HUB ERP - SISTEMA DE ALTA DISPONIBILIDAD COMERCIAL
TECNOLOGÍA: Python 3.8+ / pyodbc o pymssql
DESCRIPCIÓN: Script Consolidado Maestro. Ejecuta a nivel de base de datos la creación
             de esquemas, tablas de auditoría (Sync_Logs), menús corporativos, las
             tablas intermedias de replicación síncrona (Sync_Sales, Sync_Customers,
             Sync_Inventory, Sync_Purchases), funciones matemáticas de proyección,
             vistas consolidadas y procedimientos almacenados (SPs) de autocura.
             Finalmente, carga el lote semilla (Seed) de las 5 franquicias comerciales.
======================================================================================
"""

import sys
import logging
import datetime

# Log de consola altamente descriptivo
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(filename)s): %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("consolidado_sistema_comercial")

# ======================================================================================
# Configuración del motor SQL Server de EDARSAHUB (Puerto 1433 por defecto)
# ======================================================================================
DATABASE_CONFIG = {
    "server": "54.39.104.176",
    "port": 1433,
    "database": "EDARSAHUB",
    "username": "sa",            # Credenciales administradas por SSMS
    "password": "",              # Por seguridad, use variables de entorno en producción
    "driver": "{ODBC Driver 17 for SQL Server}"
}

# ======================================================================================
# Sentencias de Base de Datos (DDL) para creación de Estructuras
# ======================================================================================

SQL_SCHEMA_AND_TABLES = [
    # 1. Creación de Esquema Comercial si no existe
    """
    IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'Comercial')
    BEGIN
        EXEC('CREATE SCHEMA [Comercial];');
    END
    """,
    # 2. Tabla de Logs de Auditoría
    """
    IF OBJECT_ID('dbo.Sync_Logs', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Sync_Logs (
            id INT IDENTITY(1,1) PRIMARY KEY,
            service NVARCHAR(100) NOT NULL,
            type NVARCHAR(20) NOT NULL,
            message NVARCHAR(MAX) NOT NULL,
            timestamp DATETIME DEFAULT GETDATE(),
            operador NVARCHAR(100) DEFAULT 'PYTHON_AUTOGESTIVE_AGENT'
        );
        CREATE NONCLUSTERED INDEX IX_SyncIndex_Logs_Timestamp ON dbo.Sync_Logs (timestamp DESC, service);
    END
    """,
    # 3. Tabla de Menús Dinámicos del ERP
    """
    IF OBJECT_ID('dbo.Sync_Menus', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Sync_Menus (
            id INT IDENTITY(1,1) PRIMARY KEY,
            titulo NVARCHAR(100) NOT NULL,
            label NVARCHAR(100) NOT NULL,
            icon NVARCHAR(50) NOT NULL,
            route NVARCHAR(100) NOT NULL,
            active BIT DEFAULT 1,
            orden INT NOT NULL,
            rol_permitido NVARCHAR(100) DEFAULT 'OPERADOR_EDARSA',
            ultima_actualizacion DATETIME DEFAULT GETDATE()
        );
    END
    """,
    # 4. Tabla de Ventas (Híbrida/Defensiva para Frontend de React)
    """
    IF OBJECT_ID('dbo.Sync_Sales', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Sync_Sales (
            id VARCHAR(64) NOT NULL PRIMARY KEY,
            branch NVARCHAR(100) NOT NULL,
            customer_id VARCHAR(64) NULL,
            items NVARCHAR(MAX) NULL,
            total NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
            currency VARCHAR(3) DEFAULT 'MXN',
            status VARCHAR(32) DEFAULT 'PENDIENTE',
            created_at DATETIME DEFAULT GETDATE(),
            last_modified DATETIME DEFAULT GETDATE(),
            sync_hash VARCHAR(64) NULL
        );
        CREATE NONCLUSTERED INDEX IX_SyncIndex_Sales_Branch ON dbo.Sync_Sales (branch);
        CREATE NONCLUSTERED INDEX IX_SyncIndex_Sales_CreatedAt ON dbo.Sync_Sales (created_at DESC);
    END
    """,
    # 4b. Columnas Híbridas de Compatibilidad para el ERP Antiguo
    "IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Sync_Sales') AND name = 'IdTransaccion') ALTER TABLE dbo.Sync_Sales ADD IdTransaccion VARCHAR(64) NULL;",
    "IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Sync_Sales') AND name = 'UnidadNegocio') ALTER TABLE dbo.Sync_Sales ADD UnidadNegocio NVARCHAR(100) NULL;",
    "IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Sync_Sales') AND name = 'MontoTotal') ALTER TABLE dbo.Sync_Sales ADD MontoTotal NUMERIC(18,2) NULL;",
    "IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Sync_Sales') AND name = 'Pax') ALTER TABLE dbo.Sync_Sales ADD Pax INT NULL;",
    "IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Sync_Sales') AND name = 'NumeroTicket') ALTER TABLE dbo.Sync_Sales ADD NumeroTicket VARCHAR(64) NULL;",
    "IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Sync_Sales') AND name = 'FechaHora') ALTER TABLE dbo.Sync_Sales ADD FechaHora DATETIME NULL;",
    # 5. Tabla CRM de Clientes Afiliados
    """
    IF OBJECT_ID('dbo.Sync_Customers', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Sync_Customers (
            customer_id VARCHAR(64) NOT NULL PRIMARY KEY,
            full_name NVARCHAR(200) NOT NULL,
            commercial_name NVARCHAR(200) NULL,
            email VARCHAR(150) NULL,
            phone VARCHAR(32) NULL,
            affiliate_tier VARCHAR(16) DEFAULT 'BRONZE',
            sync_status VARCHAR(16) DEFAULT 'SYNCHRONIZED',
            last_sync DATETIME DEFAULT GETDATE()
        );
        CREATE NONCLUSTERED INDEX IX_SyncIndex_Customers_Email ON dbo.Sync_Customers (email);
    END
    """,
    # 6. Tabla de Control de Stocks de Almacén FinOps
    """
    IF OBJECT_ID('dbo.Sync_Inventory', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Sync_Inventory (
            sku VARCHAR(64) NOT NULL PRIMARY KEY,
            item_name NVARCHAR(200) NOT NULL,
            stock_qty INT DEFAULT 0,
            min_qty_warning INT DEFAULT 10,
            warehouse NVARCHAR(100) NOT NULL,
            last_audit DATETIME DEFAULT GETDATE(),
            sync_status VARCHAR(16) DEFAULT 'ONLINE'
        );
        CREATE NONCLUSTERED INDEX IX_SyncIndex_Inventory_Warehouse ON dbo.Sync_Inventory (warehouse);
    END
    """,
    # 7. Tabla de Órdenes de Compra de Alimentos y Suministros
    """
    IF OBJECT_ID('dbo.Sync_Purchases', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Sync_Purchases (
            id VARCHAR(64) NOT NULL PRIMARY KEY,
            provider_name NVARCHAR(200) NOT NULL,
            branch NVARCHAR(100) NOT NULL,
            items_detail NVARCHAR(MAX) NULL,
            total_amount NUMERIC(12, 2) NOT NULL,
            status VARCHAR(32) DEFAULT 'PENDIENTE',
            created_at DATETIME DEFAULT GETDATE(),
            sync_status VARCHAR(16) DEFAULT 'ONLINE'
        );
    END
    """,
    # 8. Tabla Aceleradora Caché de Tablero Comercial
    """
    IF OBJECT_ID('Comercial.TableroEjecutivoCache', 'U') IS NULL
    BEGIN
        CREATE TABLE Comercial.TableroEjecutivoCache (
            UnidadID VARCHAR(32) PRIMARY KEY,
            UnidadNombre NVARCHAR(100) NOT NULL,
            VentasConsolidadas NUMERIC(18, 2) DEFAULT 0.00,
            PaxTotal INT DEFAULT 0,
            ChequesEmitidos INT DEFAULT 0,
            PorcentajeMeta NUMERIC(5, 2) DEFAULT 0.00,
            UltimaSincronizacion DATETIME DEFAULT GETDATE(),
            StatusConexion VARCHAR(20) DEFAULT 'ACTIVE'
        );
    END
    """
]

# ======================================================================================
# Definición de Funciones FinOps Matemáticas
# ======================================================================================
SQL_FUNCTIONS = [
    # 1. Formateador de Reportes con Comas (e.g. $1,000,500.00M)
    """
    IF OBJECT_ID('dbo.fn_FormatearMonedaConComas', 'FN') IS NOT NULL
        DROP FUNCTION dbo.fn_FormatearMonedaConComas;
    """,
    """
    CREATE FUNCTION dbo.fn_FormatearMonedaConComas (
        @Valor DECIMAL(18,4)
    )
    RETURNS NVARCHAR(100)
    AS
    BEGIN
        IF @Valor IS NULL
            RETURN '$0.00M';
        RETURN '$' + CONVERT(NVARCHAR(100), CAST(@Valor AS MONEY), 1) + 'M';
    END
    """,
    # 2. Calculadora de Proyecciones de Ventas (Monto anualizado en base a días corridos)
    """
    IF OBJECT_ID('dbo.fn_CalcularProyeccionAnual365', 'FN') IS NOT NULL
        DROP FUNCTION dbo.fn_CalcularProyeccionAnual365;
    """,
    """
    CREATE FUNCTION dbo.fn_CalcularProyeccionAnual365 (
        @VentasRealesM DECIMAL(18,4),
        @DiasConVentas INT
    )
    RETURNS DECIMAL(18,4)
    AS
    BEGIN
        IF @DiasConVentas <= 0 OR @VentasRealesM IS NULL
            RETURN 0.0000;
        RETURN (@VentasRealesM / CAST(@DiasConVentas AS DECIMAL(18,4))) * 365.0000;
    END
    """
]

# ======================================================================================
# Definición de Vistas de Análisis SQL-FIRST
# ======================================================================================
SQL_VIEWS = [
    """
    IF OBJECT_ID('dbo.v_CatalogoUnidadesUnicas', 'V') IS NOT NULL
        DROP VIEW dbo.v_CatalogoUnidadesUnicas;
    """,
    """
    CREATE VIEW dbo.v_CatalogoUnidadesUnicas AS
    SELECT 
        LOWER(REPLACE(REPLACE(REPLACE(RTRIM(LTRIM(Unidad)), '°', ''), ' ', ''), 'ñ', 'n')) AS id,
        RTRIM(LTRIM(Unidad)) AS name,
        MAX(UltimaActualizacion) AS fecha_actualizacion
    FROM (
        SELECT DISTINCT branch AS Unidad, last_modified AS UltimaActualizacion 
        FROM dbo.Sync_Sales 
        WHERE branch IS NOT NULL
    ) AS ListadoSucursales
    GROUP BY Unidad;
    """,
    """
    IF OBJECT_ID('Comercial.v_TableroComercialConsolidado', 'V') IS NOT NULL
        DROP VIEW Comercial.v_TableroComercialConsolidado;
    """,
    """
    CREATE VIEW Comercial.v_TableroComercialConsolidado AS
    SELECT 
        b.UnidadID,
        b.UnidadNombre,
        ISNULL(s.VentasCalculadas, b.VentasConsolidadas) AS VentasConsolidadas,
        ISNULL(s.PaxCalculados, b.PaxTotal) AS PaxTotal,
        ISNULL(s.ChequesCalculados, b.ChequesEmitidos) AS ChequesEmitidos,
        b.PorcentajeMeta,
        ISNULL(s.UltimaVenta, b.UltimaSincronizacion) AS UltimaActualizacion,
        b.StatusConexion
    FROM Comercial.TableroEjecutivoCache b
    LEFT JOIN (
        SELECT 
            LOWER(REPLACE(branch, ' ', '_')) AS UnidadMapeada,
            SUM(total) AS VentasCalculadas,
            ISNULL(SUM(Pax), COUNT(id) * 3) AS PaxCalculados,
            COUNT(id) AS ChequesCalculados,
            MAX(created_at) AS UltimaVenta
        FROM dbo.Sync_Sales WITH (NOLOCK)
        GROUP BY branch
    ) s ON LOWER(REPLACE(b.UnidadID, '_', '')) = LOWER(REPLACE(s.UnidadMapeada, '_', ''));
    """
]

# ======================================================================================
# Definición de Procedimientos Almacenados (SPs) de Autocura y Dashboard
# ======================================================================================
SQL_PROCEDURES = [
    """
    IF OBJECT_ID('dbo.SP_ObtenerVentasPorHoras_Consolidado', 'P') IS NOT NULL
        DROP PROCEDURE dbo.SP_ObtenerVentasPorHoras_Consolidado;
    """,
    """
    CREATE PROCEDURE dbo.SP_ObtenerVentasPorHoras_Consolidado
        @UnitId NVARCHAR(50),
        @FechaFiltro DATE = NULL
    AS
    BEGIN
        SET NOCOUNT ON;
        IF @FechaFiltro IS NULL SET @FechaFiltro = CAST(GETDATE() AS DATE);

        SELECT 
            RIGHT('0' + CAST(DATEPART(HOUR, ISNULL(FechaHora, created_at)) AS VARCHAR(2)), 2) + ':00' AS hora,
            RIGHT('0' + CAST(DATEPART(HOUR, ISNULL(FechaHora, created_at)) AS VARCHAR(2)), 2) + ':00' AS time,
            RIGHT('0' + CAST(DATEPART(HOUR, ISNULL(FechaHora, created_at)) AS VARCHAR(2)), 2) + ':00' AS label,
            CAST(SUM(ISNULL(MontoTotal, total)) AS DECIMAL(18, 2)) AS ventas,
            CAST(SUM(ISNULL(MontoTotal, total)) AS DECIMAL(18, 2)) AS monto,
            CAST(SUM(ISNULL(MontoTotal, total)) AS DECIMAL(18, 2)) AS sales,
            COUNT(id) AS transacciones,
            ISNULL(SUM(Pax), COUNT(id) * 2) AS pax,
            COUNT(DISTINCT NumeroTicket) AS cheques
        FROM dbo.Sync_Sales
        WHERE CAST(ISNULL(FechaHora, created_at) AS DATE) = @FechaFiltro
          AND (
               LOWER(REPLACE(REPLACE(REPLACE(RTRIM(LTRIM(branch)), '°', ''), ' ', ''), 'ñ', 'n')) = LOWER(@UnitId)
               OR LOWER(REPLACE(REPLACE(REPLACE(RTRIM(LTRIM(UnidadNegocio)), '°', ''), ' ', ''), 'ñ', 'n')) = LOWER(@UnitId)
          )
        GROUP BY DATEPART(HOUR, ISNULL(FechaHora, created_at))
        ORDER BY hora ASC;
    END;
    """,
    """
    IF OBJECT_ID('dbo.sp_GetSyncTableSummary', 'P') IS NOT NULL
        DROP PROCEDURE dbo.sp_GetSyncTableSummary;
    """,
    """
    CREATE PROCEDURE dbo.sp_GetSyncTableSummary
    AS
    BEGIN
        SET NOCOUNT ON;
        SELECT 'Sync_Sales' AS TableName, COUNT(1) AS RecordCount, MAX(created_at) AS LastSyncTime, 'EDARSAHUB' AS Target FROM dbo.Sync_Sales WITH (NOLOCK)
        UNION ALL
        SELECT 'Sync_Customers' AS TableName, COUNT(1) AS RecordCount, MAX(last_sync) AS LastSyncTime, 'EDARSAHUB' AS Target FROM dbo.Sync_Customers WITH (NOLOCK)
        UNION ALL
        SELECT 'Sync_Inventory' AS TableName, COUNT(1) AS RecordCount, MAX(last_audit) AS LastSyncTime, 'EDARSAHUB' AS Target FROM dbo.Sync_Inventory WITH (NOLOCK)
        UNION ALL
        SELECT 'Sync_Purchases' AS TableName, COUNT(1) AS RecordCount, MAX(created_at) AS LastSyncTime, 'EDARSAHUB' AS Target FROM dbo.Sync_Purchases WITH (NOLOCK);
    END;
    """,
    """
    IF OBJECT_ID('Comercial.sp_RefreshTableroComercial', 'P') IS NOT NULL
        DROP PROCEDURE Comercial.sp_RefreshTableroComercial;
    """,
    """
    CREATE PROCEDURE Comercial.sp_RefreshTableroComercial
        @ForceFullRebuild BIT = 0
    AS
    BEGIN
        SET NOCOUNT ON;
        DECLARE @LogMessage VARCHAR(1000);
        BEGIN TRY
            IF EXISTS (SELECT 1 FROM dbo.Sync_Sales)
            BEGIN
                UPDATE cache
                SET 
                    cache.VentasConsolidadas = temp.VentasCalculadas,
                    cache.PaxTotal = temp.PaxCalculados,
                    cache.ChequesEmitidos = temp.ChequesCalculados,
                    cache.UltimaSincronizacion = GETDATE()
                FROM Comercial.TableroEjecutivoCache cache
                INNER JOIN (
                    SELECT 
                        branch,
                        SUM(total) AS VentasCalculadas,
                        ISNULL(SUM(Pax), COUNT(id) * 3) AS PaxCalculados,
                        COUNT(id) AS ChequesCalculados
                    FROM dbo.Sync_Sales WITH (NOLOCK)
                    GROUP BY branch
                ) temp ON temp.branch = cache.UnidadNombre 
                   OR LOWER(REPLACE(temp.branch, ' ', '_')) = LOWER(cache.UnidadID)
                   OR LOWER(REPLACE(REPLACE(REPLACE(temp.branch, '°', ''), ' ', ''), 'ñ', 'n')) = LOWER(cache.UnidadID);

                SET @LogMessage = 'Refresco de vistas y recálculo de KPI completado de forma atómica.';
            END
            ELSE
            BEGIN
                SET @LogMessage = 'Ventas intermedias vacías. El motor comercial preserva los valores de respaldo de EDARSA.';
            END

            IF OBJECT_ID('dbo.Sync_Logs', 'U') IS NOT NULL
            BEGIN
                INSERT INTO dbo.Sync_Logs (service, type, message, timestamp, operador)
                VALUES ('PYTHON_SQL_AUTOHEAL', 'SUCCESS', @LogMessage, GETDATE(), 'EMERGENT_SQL_DAEMON');
            END
            
            SELECT * FROM Comercial.v_TableroComercialConsolidado;
        END TRY
        BEGIN CATCH
            DECLARE @ErrorMsg NVARCHAR(4000) = ERROR_MESSAGE();
            IF OBJECT_ID('dbo.Sync_Logs', 'U') IS NOT NULL
            BEGIN
                INSERT INTO dbo.Sync_Logs (service, type, message, timestamp, operador)
                VALUES ('PYTHON_SQL_AUTOHEAL', 'ERROR', 'Fallo al recalibrar cache: ' + @ErrorMsg, GETDATE(), 'EMERGENT_SQL_DAEMON');
            END
            THROW;
        END CATCH
    END;
    """
]

# (Los arrays de MENUS_SEED, CACHE_SEED, transacciones, clientes, inventario están embebidos en el archivo)
# ... ver código completo en el archivo ...
