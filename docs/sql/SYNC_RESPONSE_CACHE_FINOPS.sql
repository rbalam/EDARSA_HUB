-- ==================================================================================
-- SCRIPT DE OPTIMIZACIÓN: INFRAESTRUCTURA DE RESPALDO Y CACHÉ EDARSAHUB
-- OBJETIVO: Reducir consumo de créditos en Emergent.sh evitando consultas duplicadas.
-- PUERTO DE RED: 1433 (Seguro por TLS 1.3)
-- ==================================================================================

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Sync_Response_Cache]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Sync_Response_Cache] (
        [cache_id] UNIQUEIDENTIFIER DEFAULT NEWID() PRIMARY KEY,
        [request_hash] VARCHAR(64) NOT NULL UNIQUE, -- SHA256 del query / petición
        [endpoint_source] VARCHAR(150) NOT NULL,    -- Ruta o API invocadora
        [cached_data] NVARCHAR(MAX) NOT NULL,      -- Respuesta serializada en JSON
        [tokens_saved] INT DEFAULT 0,               -- Mapeo estimado de créditos FinOps ahorrados
        [expires_at] DATETIME NOT NULL,             -- Límite de tiempo de vigencia
        [last_checked] DATETIME DEFAULT GETDATE()
    );
    
    PRINT '✅ Tabla [Sync_Response_Cache] creada exitosamente en EDARSAHUB.';
END
ELSE
BEGIN
    PRINT 'ℹ️ La infraestructura de caché ya existe en este servidor.';
END
GO

-- Índice de aceleración por Hash de Petición
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = N'IX_Sync_Cache_RequestHash')
BEGIN
    CREATE NONCLUSTERED INDEX [IX_Sync_Cache_RequestHash] 
    ON [dbo].[Sync_Response_Cache] ([request_hash]) 
    INCLUDE ([cached_data], [expires_at]);
    
    PRINT '✅ Índice [IX_Sync_Cache_RequestHash] configurado.';
END
GO

-- Procedimiento Almacenado para verificar y limpiar caché de manera rápida
CREATE OR ALTER PROCEDURE [dbo].[GetOrSetCacheData]
    @RequestQuery NVARCHAR(MAX),
    @EndpointSource VARCHAR(150),
    @PayloadJSON NVARCHAR(MAX),
    @TTLMinutes INT = 15,
    @ResultJSON NVARCHAR(MAX) OUTPUT,
    @IsHit BIT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Generar Hash único SHA256 de forma segura sobre el query de entrada
    DECLARE @HashHex VARCHAR(64);
    SET @HashHex = CONVERT(VARCHAR(64), HASHBYTES('SHA2_256', @RequestQuery), 2);
    
    DECLARE @CurrentTime DATETIME = GETDATE();
    
    -- 1. Intentar recuperar del caché si sigue vigente
    IF EXISTS (SELECT 1 FROM [dbo].[Sync_Response_Cache] WHERE [request_hash] = @HashHex AND [expires_at] > @CurrentTime)
    BEGIN
        SELECT @ResultJSON = [cached_data] 
        FROM [dbo].[Sync_Response_Cache] 
        WHERE [request_hash] = @HashHex;
        
        SET @IsHit = 1;
        
        -- Sumar ahorro de tokens simulado
        UPDATE [dbo].[Sync_Response_Cache]
        SET [tokens_saved] = [tokens_saved] + 2500, -- Promedio de tokens por consulta reducida
            [last_checked] = @CurrentTime
        WHERE [request_hash] = @HashHex;
    END
    ELSE
    BEGIN
        -- 2. Guardar o refrescar caché con el nuevo payload
        SET @IsHit = 0;
        SET @ResultJSON = @PayloadJSON;
        
        -- Registrar nueva vida de expiración
        DECLARE @ExpireTime DATETIME = DATEADD(MINUTE, @TTLMinutes, @CurrentTime);
        
        MERGE [dbo].[Sync_Response_Cache] AS Target
        USING (SELECT @HashHex AS [request_hash]) AS Source
        ON (Target.[request_hash] = Source.[request_hash])
        WHEN MATCHED THEN
            UPDATE SET [cached_data] = @PayloadJSON, [expires_at] = @ExpireTime, [last_checked] = @CurrentTime
        WHEN NOT MATCHED THEN
            INSERT ([request_hash], [endpoint_source], [cached_data], [expires_at])
            VALUES (@HashHex, @EndpointSource, @PayloadJSON, @ExpireTime);
    END
END
GO
