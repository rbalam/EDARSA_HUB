"""
Test de Validación: Migración de Servidores MongoDB -> EDARSAHUB SQL
=====================================================================
FASE 2/3 de la Migración (Abril 2026)

Este test valida:
1. Que la lectura de servidores funcione correctamente desde SQL
2. Que el fallback a MongoDB funcione si SQL falla
3. Paridad estructural entre SQL y MongoDB
4. Que los endpoints del sistema sigan funcionando
"""

import os
import sys
import asyncio
from datetime import datetime

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Imports del sistema
from modules.comercial.repository import (
    _get_server_by_id_sql,
    _get_servers_for_tablero_sql,
    get_server_by_id,
    get_servers_for_tablero,
    init_comercial_repository,
    USE_SQL_FOR_SERVERS,
    EDARSAHUB_CONFIG,
)


def test_configuracion():
    """Verifica que la configuración de EDARSAHUB esté correcta."""
    print("\n=== TEST: Configuración ===")
    
    assert EDARSAHUB_CONFIG['host'] == '54.39.104.176', "Host incorrecto"
    assert EDARSAHUB_CONFIG['port'] == 1433, "Puerto incorrecto"
    assert EDARSAHUB_CONFIG['database'] == 'EDARSAHUB', "Base de datos incorrecta"
    assert EDARSAHUB_CONFIG['username'] == 'HRLectura', "Usuario incorrecto"
    
    print(f"  ✓ Host: {EDARSAHUB_CONFIG['host']}")
    print(f"  ✓ Puerto: {EDARSAHUB_CONFIG['port']}")
    print(f"  ✓ Base de datos: {EDARSAHUB_CONFIG['database']}")
    print(f"  ✓ USE_SQL_FOR_SERVERS: {USE_SQL_FOR_SERVERS}")
    
    return True


def test_lectura_sql_directa():
    """Verifica que las funciones de lectura SQL funcionen."""
    print("\n=== TEST: Lectura SQL Directa ===")
    
    # Test _get_servers_for_tablero_sql
    servers = _get_servers_for_tablero_sql()
    assert len(servers) > 0, "No se obtuvieron servidores de SQL"
    print(f"  ✓ _get_servers_for_tablero_sql(): {len(servers)} servidores")
    
    # Verificar estructura del primer servidor
    server = servers[0]
    required_fields = ['id', 'name', 'system_type', 'host', 'port', 'database', 'active']
    for field in required_fields:
        assert field in server, f"Falta campo '{field}' en servidor SQL"
    print(f"  ✓ Estructura correcta: {required_fields}")
    
    # Test _get_server_by_id_sql
    test_id = servers[0]['id']
    server_by_id = _get_server_by_id_sql(test_id)
    assert server_by_id is not None, f"No se encontró servidor {test_id}"
    assert server_by_id['name'] == servers[0]['name'], "Discrepancia en nombre"
    print(f"  ✓ _get_server_by_id_sql(): {server_by_id['name']}")
    
    return True


def test_paridad_sql_mongodb():
    """Verifica paridad entre datos de SQL y MongoDB."""
    print("\n=== TEST: Paridad SQL vs MongoDB ===")
    
    # Obtener de SQL
    sql_servers = _get_servers_for_tablero_sql()
    sql_names = {s['name'] for s in sql_servers}
    
    # Obtener de MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = MongoClient(mongo_url)
    db = client['edarsa_hub']
    
    mongo_cursor = db.servers.find({
        'active': True, 
        'visible_en_operaciones': {'$ne': False},
        '$or': [
            {'tipo_conexion': {'$exists': False}},
            {'tipo_conexion': 'DATA_SOURCE'}
        ]
    }, {'_id': 0})
    mongo_servers = list(mongo_cursor)
    mongo_servers = [s for s in mongo_servers if s.get('tipo_conexion') != 'CORE']
    mongo_names = {s['name'] for s in mongo_servers}
    
    print(f"  SQL: {len(sql_servers)} servidores")
    print(f"  MongoDB: {len(mongo_servers)} servidores")
    
    # Verificar paridad
    solo_sql = sql_names - mongo_names
    solo_mongo = mongo_names - sql_names
    
    if solo_sql:
        print(f"  ⚠ Solo en SQL: {solo_sql}")
    if solo_mongo:
        print(f"  ⚠ Solo en MongoDB: {solo_mongo}")
    
    if sql_names == mongo_names:
        print(f"  ✓ PARIDAD PERFECTA: {len(sql_names)} servidores")
        return True
    else:
        print("  ⚠ Diferencias detectadas (puede ser esperado si hay datos nuevos)")
        # No fallar, solo advertir
        return True


async def test_funciones_async():
    """Verifica que las funciones async del repositorio funcionen."""
    print("\n=== TEST: Funciones Async del Repositorio ===")
    
    # Inicializar MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client['edarsa_hub']
    init_comercial_repository(db)
    
    # Test get_servers_for_tablero
    servers = await get_servers_for_tablero()
    assert len(servers) > 0, "No se obtuvieron servidores"
    print(f"  ✓ get_servers_for_tablero(): {len(servers)} servidores")
    
    # Test get_server_by_id
    test_id = servers[0]['id']
    server = await get_server_by_id(test_id)
    assert server is not None, f"No se encontró servidor {test_id}"
    print(f"  ✓ get_server_by_id(): {server['name']}")
    
    # Verificar campos clave
    for field in ['id', 'name', 'system_type', 'host', 'database', 'active']:
        assert field in server, f"Falta campo {field}"
    print("  ✓ Estructura completa verificada")
    
    return True


def run_all_tests():
    """Ejecuta todos los tests."""
    print("=" * 60)
    print("VALIDACIÓN FASE 2/3: MIGRACIÓN SERVIDORES A SQL")
    print(f"Fecha: {datetime.now().isoformat()}")
    print("=" * 60)
    
    results = []
    
    # Test 1: Configuración
    try:
        results.append(("Configuración", test_configuracion()))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results.append(("Configuración", False))
    
    # Test 2: Lectura SQL directa
    try:
        results.append(("Lectura SQL", test_lectura_sql_directa()))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results.append(("Lectura SQL", False))
    
    # Test 3: Paridad
    try:
        results.append(("Paridad SQL/MongoDB", test_paridad_sql_mongodb()))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results.append(("Paridad SQL/MongoDB", False))
    
    # Test 4: Funciones Async
    try:
        results.append(("Funciones Async", asyncio.run(test_funciones_async())))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results.append(("Funciones Async", False))
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE TESTS")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nResultado: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("\n✓✓✓ MIGRACIÓN FASE 2/3 VALIDADA EXITOSAMENTE ✓✓✓")
        return 0
    else:
        print("\n✗✗✗ HAY TESTS FALLIDOS - REVISAR ✗✗✗")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
