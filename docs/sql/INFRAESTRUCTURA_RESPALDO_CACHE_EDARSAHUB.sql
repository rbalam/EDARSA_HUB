-- ======================================================================================
-- SCRIPT DE BASE DE DATOS: INFRAESTRUCTURA_RESPALDO_CACHE_EDARSAHUB.sql
-- PROYECTO: EDARSA HUB ERP - MOTOR RESILIENTE Y ALTA DISPONIBILIDAD (EDGE OFFLINE CACHE)
-- MOTOR: Microsoft SQL Server 2019+ (Directo Puerto 1433 - Base de datos EDARSAHUB)
-- ======================================================================================

USE [EDARSAHUB];
GO

-- 1. TABLA INTERMEDIA: Sync_Sales
IF OBJECT_ID('dbo.Sync_Sales', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sync_Sales (
        id VARCHAR(64) NOT NULL PRIMARY KEY,
        branch NVARCHAR(100) NOT NULL,
        customer_id VARCHAR(64) NULL,
        items NVARCHAR(MAX) NULL,
        total NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
        currency VARCHAR(3) DEFAULT 'USD',
        status VARCHAR(32) DEFAULT 'PENDIENTE',
        created_at DATETIME DEFAULT GETDATE(),
        last_modified DATETIME DEFAULT GETDATE(),
        sync_hash VARCHAR(64) NULL
    );
    CREATE NONCLUSTERED INDEX IX_SyncIndex_Sales_Branch ON dbo.Sync_Sales (branch);
    CREATE NONCLUSTERED INDEX IX_SyncIndex_Sales_CreatedAt ON dbo.Sync_Sales (created_at DESC);
END
GO

-- 2. TABLA INTERMEDIA: Sync_Customers
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
GO

-- 3. TABLA INTERMEDIA: Sync_Inventory
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
END
GO

-- 4. TABLA INTERMEDIA: Sync_Purchases
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
GO

-- 5. PROCEDIMIENTO EXTRA DE CONTEO Y AUDITORÍA DE BROKER
IF OBJECT_ID('dbo.sp_GetSyncTableSummary', 'P') IS NOT NULL
BEGIN
    DROP PROCEDURE dbo.sp_GetSyncTableSummary;
END
GO

CREATE PROCEDURE dbo.sp_GetSyncTableSummary
AS
BEGIN
    SET NOCOUNT ON;
    SELECT 'Sync_Sales' AS TableName, COUNT(1) AS RecordCount, MAX(created_at) AS LastSyncTime, 'EDARSAHUB (SQL 1433)' AS DatabaseTarget FROM dbo.Sync_Sales WITH (NOLOCK)
    UNION ALL
    SELECT 'Sync_Customers' AS TableName, COUNT(1) AS RecordCount, MAX(last_sync) AS LastSyncTime, 'EDARSAHUB (SQL 1433)' AS DatabaseTarget FROM dbo.Sync_Customers WITH (NOLOCK)
    UNION ALL
    SELECT 'Sync_Inventory' AS TableName, COUNT(1) AS RecordCount, MAX(last_audit) AS LastSyncTime, 'EDARSAHUB (SQL 1433)' AS DatabaseTarget FROM dbo.Sync_Inventory WITH (NOLOCK)
    UNION ALL
    SELECT 'Sync_Purchases' AS TableName, COUNT(1) AS RecordCount, MAX(created_at) AS LastSyncTime, 'EDARSAHUB (SQL 1433)' AS DatabaseTarget FROM dbo.Sync_Purchases WITH (NOLOCK);
END
GO
