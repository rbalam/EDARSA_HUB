# -*- coding: utf-8 -*-
# consultar_cache_finops.py - Módulo de Mitigación FinOps (Función auxiliar)
import hashlib
import pymssql
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
        timeout=15
    )

def consultar_o_registrar_cache(service_source, p_payload, response_generator_func, cost_usd=0.0015):
    """
    Consulta caché FinOps o registra nueva respuesta.
    Reduce costos evitando llamadas repetidas a APIs externas.
    """
    payload_hash = hashlib.sha256(p_payload.encode('utf-8')).hexdigest()
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Comprobar caché
        cursor.execute("EXEC dbo.sp_CheckAndRetrieveCache %s, %s;", (payload_hash, service_source))
        result = cursor.fetchone()
        
        if result and result[0] == 1:
            print(f"[FINOPS COLD HIT] Retornando respuesta desde caché para {service_source}")
            conn.commit()
            return result[1]
            
        # 2. Si no hay cache, generar respuesta
        print(f"[FINOPS COLD MISS] Generando respuesta fresca de API...")
        fresh_response = response_generator_func(p_payload)
        
        # 3. Guardar en caché y auditar en libro de consumos
        cursor.execute("EXEC dbo.sp_RegisterResponseAndCache %s, %s, %s, %s, %s, %s;", 
                       (payload_hash, service_source, p_payload, fresh_response, cost_usd, 120))
        conn.commit()
        return fresh_response
    except Exception as e:
        conn.rollback()
        print(f"[FINOPS SHIELD ERROR] Fallo: {str(e)}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    # Test
    def mock_generator(payload):
        return f'{{"generated": true, "payload_len": {len(payload)}}}'
    
    result = consultar_o_registrar_cache(
        "TEST_FINOPS_MODULE",
        '{"action": "test_finops"}',
        mock_generator,
        0.002
    )
    print(f"[RESULTADO] {result}")
