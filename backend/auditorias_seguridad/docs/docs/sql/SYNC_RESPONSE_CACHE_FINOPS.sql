-- ======================================================================================
-- SCRIPT DE BASE DE DATOS: SYNC_RESPONSE_CACHE_FINOPS.sql
-- PROYECTO: EDARSA HUB ERP - ESCUDO DE MITIGACIÓN Y OPTIMIZACIÓN DE COSTOS FINOPS (SHIELD)
-- MOTOR: Microsoft SQL Server 2019+ (Directo Puerto 1433 - Base de datos EDARSAHUB)
-- ======================================================================================

USE [EDARSAHUB];
GO

IF OBJECT_ID('dbo.Sync_Response_Cache', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sync_Response_Cache (
        RequestHash VARCHAR(64) NOT NULL PRIMARY KEY, -- Hash único (SHA-256) del request/prompt/query
        ServiceSource VARCHAR(64) NOT NULL,            -- GEMINI_API, VTIGER_CRM_QUERY, GPT_4O
        RequestPayload NVARCHAR(MAX) NOT NULL,
        ResponsePayload NVARCHAR(MAX) NOT NULL,
        TokenCostFraction NUMERIC(10, 6) DEFAULT 0.00,  -- Costo monetario real evitado
        HitCount INT DEFAULT 1,
        ExpiresAt DATETIME NOT NULL,                   -- Control de expiración (TTL)
        CreatedAt DATETIME DEFAULT GETDATE(),
        LastHitAt DATETIME DEFAULT GETDATE()
    );
    CREATE NONCLUSTERED INDEX IX_ResponseCache_Expires ON dbo.Sync_Response_Cache (ExpiresAt);
END
GO

IF OBJECT_ID('dbo.Sync_Token_Ledger', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sync_Token_Ledger (
        LedgerID INT IDENTITY(1,1) PRIMARY KEY,
        OperadorID VARCHAR(64) DEFAULT 'sk-emergent-universal-gate',
        ConsuDate DATE DEFAULT CAST(GETDATE() AS DATE),
        TokensInput INT DEFAULT 0,
        TokensOutput INT DEFAULT 0,
        EstimatedCostUSD NUMERIC(12, 4) DEFAULT 0.0000,
        AhorroAcumuladoUSD NUMERIC(12, 4) DEFAULT 0.0000,
        HitRatioPercent NUMERIC(5, 2) DEFAULT 0.00
    );
    CREATE UNIQUE NONCLUSTERED INDEX UX_TokenLedger_Date ON dbo.Sync_Token_Ledger (OperadorID, ConsuDate);
END
GO

-- COMPROBAR CACHÉ (Evita la ejecución e insolvencia si ya está guardado)
IF OBJECT_ID('dbo.sp_CheckAndRetrieveCache', 'P') IS NOT NULL
BEGIN
    DROP PROCEDURE dbo.sp_CheckAndRetrieveCache;
END
GO

CREATE PROCEDURE dbo.sp_CheckAndRetrieveCache
    @RequestHash VARCHAR(64),
    @ServiceSource VARCHAR(64)
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @Now DATETIME = GETDATE();
    
    IF EXISTS (
        SELECT 1 FROM dbo.Sync_Response_Cache WITH (UPDLOCK) 
        WHERE RequestHash = @RequestHash AND ExpiresAt > @Now
    )
    BEGIN
        UPDATE dbo.Sync_Response_Cache
        SET HitCount = HitCount + 1, LastHitAt = @Now
        WHERE RequestHash = @RequestHash;
        
        DECLARE @SavedCost NUMERIC(12, 4);
        SELECT @SavedCost = CAST(TokenCostFraction AS NUMERIC(12, 4)) FROM dbo.Sync_Response_Cache WHERE RequestHash = @RequestHash;
        
        UPDATE dbo.Sync_Token_Ledger
        SET AhorroAcumuladoUSD = AhorroAcumuladoUSD + @SavedCost
        WHERE ConsuDate = CAST(@Now AS DATE);
        
        -- Obtener Payload sin generar costo
        SELECT 1 AS CacheStatus, ResponsePayload FROM dbo.Sync_Response_Cache WHERE RequestHash = @RequestHash;
    END
    ELSE
    BEGIN
        SELECT 0 AS CacheStatus, NULL AS ResponsePayload;
    END
END
GO

-- GUARDAR NUEVA RESPUESTA EN CACHÉ
IF OBJECT_ID('dbo.sp_RegisterResponseAndCache', 'P') IS NOT NULL
BEGIN
    DROP PROCEDURE dbo.sp_RegisterResponseAndCache;
END
GO

CREATE PROCEDURE dbo.sp_RegisterResponseAndCache
    @RequestHash VARCHAR(64),
    @ServiceSource VARCHAR(64),
    @RequestPayload NVARCHAR(MAX),
    @ResponsePayload NVARCHAR(MAX),
    @TokenCostFraction NUMERIC(10, 6),
    @CacheDurationMinutes INT = 120
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @ExpiresAt DATETIME = DATEADD(MINUTE, @CacheDurationMinutes, GETDATE());
    
    MERGE dbo.Sync_Response_Cache AS Target
    USING (SELECT @RequestHash AS RequestHash) AS Source
    ON (Target.RequestHash = Source.RequestHash)
    WHEN MATCHED THEN
        UPDATE SET ResponsePayload = @ResponsePayload, ExpiresAt = @ExpiresAt, TokenCostFraction = @TokenCostFraction, LastHitAt = GETDATE()
    WHEN NOT MATCHED THEN
        INSERT (RequestHash, ServiceSource, RequestPayload, ResponsePayload, TokenCostFraction, HitCount, ExpiresAt, CreatedAt, LastHitAt)
        VALUES (@RequestHash, @ServiceSource, @RequestPayload, @ResponsePayload, @TokenCostFraction, 1, @ExpiresAt, GETDATE(), GETDATE());
END
GO
