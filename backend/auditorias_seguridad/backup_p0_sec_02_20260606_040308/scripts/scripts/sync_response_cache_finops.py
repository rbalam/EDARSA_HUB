# -*- coding: utf-8 -*-
# sync_response_cache_finops.py - Módulo de Mitigación FinOps
import pymssql
import hashlib
import os

DATABASE_CONFIG = {
    "server": os.environ.get('EDARSAHUB_HOST', os.getenv('EDARSAHUB_SQL_HOST')),
    "port": int(os.environ.get('EDARSAHUB_PORT', 1433)),
    "database": os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    "username": os.environ.get('EDARSAHUB_USERNAME', os.getenv('EDARSAHUB_SQL_USER')),
    "password": os.environ.get('EDARSAHUB_PASSWORD', os.getenv('EDARSAHUB_SQL_PASSWORD')),
}

def get_connection():
    return pymssql.connect(
        server=DATABASE_CONFIG['server'],
        port=DATABASE_CONFIG['port'],
        database=DATABASE_CONFIG['database'],
        user=DATABASE_CONFIG['username'],
        password=DATABASE_CONFIG['password'],
        timeout=30
    )

def setup_cache_infrastructure():
    """Crea tabla y SPs de caché si no existen"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Crear tabla de caché
        cursor.execute("""
            IF OBJECT_ID('dbo.Sync_Response_Cache', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.Sync_Response_Cache (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    RequestHash VARCHAR(64) NOT NULL,
                    ServiceSource VARCHAR(64) NOT NULL,
                    RequestPayload NVARCHAR(MAX) NULL,
                    ResponsePayload NVARCHAR(MAX) NULL,
                    TokenCostFraction NUMERIC(10, 6) DEFAULT 0.0,
                    CacheDurationMinutes INT DEFAULT 120,
                    CreatedAt DATETIME DEFAULT GETDATE(),
                    ExpiresAt DATETIME,
                    HitCount INT DEFAULT 0
                );
                CREATE INDEX IX_Cache_Hash ON dbo.Sync_Response_Cache (RequestHash, ServiceSource);
                CREATE INDEX IX_Cache_Expires ON dbo.Sync_Response_Cache (ExpiresAt);
            END
        """)
        conn.commit()
        print("[SETUP] Tabla Sync_Response_Cache verificada")
        
        # Crear SP para verificar caché
        cursor.execute("""
            IF OBJECT_ID('dbo.sp_CheckAndRetrieveCache', 'P') IS NOT NULL
                DROP PROCEDURE dbo.sp_CheckAndRetrieveCache
        """)
        conn.commit()
        
        cursor.execute("""
            CREATE PROCEDURE dbo.sp_CheckAndRetrieveCache
                @RequestHash VARCHAR(64),
                @ServiceSource VARCHAR(64)
            AS
            BEGIN
                SET NOCOUNT ON;
                DECLARE @CacheStatus INT = 0;
                DECLARE @ResponsePayload NVARCHAR(MAX) = NULL;
                
                SELECT @CacheStatus = 1, @ResponsePayload = ResponsePayload
                FROM dbo.Sync_Response_Cache
                WHERE RequestHash = @RequestHash 
                  AND ServiceSource = @ServiceSource
                  AND (ExpiresAt IS NULL OR ExpiresAt > GETDATE());
                
                IF @CacheStatus = 1
                BEGIN
                    UPDATE dbo.Sync_Response_Cache 
                    SET HitCount = HitCount + 1 
                    WHERE RequestHash = @RequestHash AND ServiceSource = @ServiceSource;
                END
                
                SELECT @CacheStatus AS CacheStatus, @ResponsePayload AS ResponsePayload;
            END
        """)
        conn.commit()
        print("[SETUP] SP sp_CheckAndRetrieveCache creado")
        
        # Crear SP para registrar respuesta
        cursor.execute("""
            IF OBJECT_ID('dbo.sp_RegisterResponseAndCache', 'P') IS NOT NULL
                DROP PROCEDURE dbo.sp_RegisterResponseAndCache
        """)
        conn.commit()
        
        cursor.execute("""
            CREATE PROCEDURE dbo.sp_RegisterResponseAndCache
                @RequestHash VARCHAR(64),
                @ServiceSource VARCHAR(64),
                @RequestPayload NVARCHAR(MAX),
                @ResponsePayload NVARCHAR(MAX),
                @TokenCostFraction NUMERIC(10, 6) = 0.0015,
                @CacheDurationMinutes INT = 120
            AS
            BEGIN
                SET NOCOUNT ON;
                
                IF EXISTS (SELECT 1 FROM dbo.Sync_Response_Cache WHERE RequestHash = @RequestHash AND ServiceSource = @ServiceSource)
                BEGIN
                    UPDATE dbo.Sync_Response_Cache
                    SET ResponsePayload = @ResponsePayload,
                        ExpiresAt = DATEADD(MINUTE, @CacheDurationMinutes, GETDATE()),
                        TokenCostFraction = @TokenCostFraction
                    WHERE RequestHash = @RequestHash AND ServiceSource = @ServiceSource;
                END
                ELSE
                BEGIN
                    INSERT INTO dbo.Sync_Response_Cache 
                    (RequestHash, ServiceSource, RequestPayload, ResponsePayload, TokenCostFraction, CacheDurationMinutes, ExpiresAt)
                    VALUES (@RequestHash, @ServiceSource, @RequestPayload, @ResponsePayload, @TokenCostFraction, @CacheDurationMinutes, DATEADD(MINUTE, @CacheDurationMinutes, GETDATE()));
                END
                
                SELECT 'CACHED' AS Status;
            END
        """)
        conn.commit()
        print("[SETUP] SP sp_RegisterResponseAndCache creado")
        
        return True
    except Exception as e:
        conn.rollback()
        print(f"[ERROR SETUP] {str(e)}")
        return False
    finally:
        conn.close()

def check_or_register_cache(service_source, request_payload, response_generator_fn=None, cost_usd=0.0015):
    """
    Verifica caché o registra nueva respuesta.
    Si hay HIT, retorna la respuesta cacheada.
    Si hay MISS, llama al generador y cachea el resultado.
    """
    request_hash = hashlib.sha256(request_payload.encode()).hexdigest()
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Comprobar caché
        cursor.execute("EXEC dbo.sp_CheckAndRetrieveCache %s, %s", (request_hash, service_source))
        row = cursor.fetchone()
        
        if row and row[0] == 1:  # CacheStatus = 1 (HIT)
            print(f"[FINOPS HIT] Caché recuperada para {service_source}")
            conn.close()
            return row[1]  # ResponsePayload
        
        # 2. Si no hay hit, llamar generador
        print(f"[FINOPS MISS] Invocando servicio de forma síncrona.")
        
        if response_generator_fn:
            fresh_response = response_generator_fn(request_payload)
        else:
            fresh_response = f'{{"status": "generated", "source": "{service_source}"}}'
        
        # 3. Registrar en base de datos
        cursor.execute("""
            EXEC dbo.sp_RegisterResponseAndCache %s, %s, %s, %s, %s, %s
        """, (request_hash, service_source, request_payload, fresh_response, cost_usd, 120))
        conn.commit()
        
        print(f"[FINOPS CACHED] Respuesta almacenada para {service_source}")
        return fresh_response
        
    except Exception as e:
        conn.rollback()
        print(f"[ERROR CACHE] {str(e)}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("SYNC RESPONSE CACHE FINOPS - EDARSAHUB")
    print("=" * 60)
    
    # Configurar infraestructura
    setup_cache_infrastructure()
    
    # Test de caché
    print("\n[TEST] Probando sistema de caché...")
    result = check_or_register_cache(
        service_source="TEST_SERVICE",
        request_payload='{"test": "payload", "action": "verify_cache"}',
        cost_usd=0.001
    )
    print(f"[RESULTADO] {result}")
    
    # Verificar HIT
    print("\n[TEST] Verificando HIT de caché...")
    result2 = check_or_register_cache(
        service_source="TEST_SERVICE",
        request_payload='{"test": "payload", "action": "verify_cache"}',
        cost_usd=0.001
    )
    print(f"[RESULTADO] {result2}")
