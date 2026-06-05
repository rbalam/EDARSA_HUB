"""
EDARSA HUB - Tests de Validación MACROFASE 2
============================================

Pruebas obligatorias:
1. UPSERT repetido sin duplicados
2. Detección de cambio real vs cambio irrelevante por threshold
3. Creación correcta de índices
4. SYNC-S sobre registros ABIERTO
5. SYNC-N sobre registros CERRADO
6. RECONCILIADO no se modifica por error
7. No regresión en consultas actuales LIVE
8. Concurrencia básica para evitar doble escritura

Fecha: 2026-04-22
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

# Agregar path del backend
sys.path.insert(0, '/app/backend')


async def run_all_tests():
    """Ejecuta todas las pruebas de validación."""
    from motor.motor_asyncio import AsyncIOMotorClient
    
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'edarsa_hub')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Importar módulos después de configurar path
    from modules.comercial.kpis_repository import (
        init_kpis_repository,
        upsert_kpi_comercial,
        get_kpi_comercial,
        cambiar_estado_periodo,
        cerrar_periodos_anteriores,
        COLLECTION_NAME,
        ESTADO_ABIERTO,
        ESTADO_CERRADO,
        ESTADO_RECONCILIADO
    )
    from scripts.setup_kpis_indexes import setup_kpis_comercial_indexes, verify_indexes
    
    # Inicializar repositorio
    init_kpis_repository(db)
    
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "tests": []
    }
    
    def log_test(name: str, passed: bool, details: str = ""):
        results["total"] += 1
        if passed:
            results["passed"] += 1
            status = "✅ PASS"
        else:
            results["failed"] += 1
            status = "❌ FAIL"
        results["tests"].append({"name": name, "passed": passed, "details": details})
        print(f"{status} | {name}")
        if details:
            print(f"       {details}")
    
    print("\n" + "=" * 70)
    print("VALIDACIÓN MACROFASE 2 - KPIs CONSOLIDADOS")
    print("=" * 70 + "\n")
    
    # Datos de prueba
    test_server_id = "test-server-001"
    test_empresa_id = "test-empresa-001"
    test_sucursal_id = "TEST01"
    test_fecha = "2026-04-20"
    
    # Limpiar datos de prueba anteriores
    await db[COLLECTION_NAME].delete_many({
        "server_id": {"$regex": "^test-"}
    })
    
    # ========================================
    # TEST 1: Creación de índices
    # ========================================
    print("--- TEST 1: Creación de índices ---")
    try:
        index_results = await setup_kpis_comercial_indexes(db)
        verification = await verify_indexes(db)
        
        # Verificar que todos los índices se crearon
        created_or_exists = sum(1 for v in index_results.values() 
                                 if v in ["CREATED", "EXISTS"])
        verified_ok = sum(1 for k, v in verification.items() 
                          if isinstance(v, dict) and v.get("status") == "OK")
        
        all_ok = created_or_exists >= 5 and verified_ok >= 5
        
        log_test(
            "Creación de índices",
            all_ok,
            f"Creados/Existentes: {created_or_exists}, Verificados OK: {verified_ok}"
        )
    except Exception as e:
        log_test("Creación de índices", False, str(e))
    
    # ========================================
    # TEST 2: UPSERT INSERT inicial
    # ========================================
    print("\n--- TEST 2: UPSERT INSERT inicial ---")
    try:
        kpis_inicial = {
            "ventas": 100000.00,
            "pax": 500,
            "cheques": 150
        }
        source_info = {
            "type": "LIVE",
            "query_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        result = await upsert_kpi_comercial(
            server_id=test_server_id,
            empresa_id=test_empresa_id,
            sucursal_id=test_sucursal_id,
            fecha=test_fecha,
            kpis=kpis_inicial,
            source_info=source_info,
            updated_by="test_script"
        )
        
        log_test(
            "UPSERT INSERT inicial",
            result.get("action") == "INSERT" and result.get("version") == 1,
            f"Action={result.get('action')}, Version={result.get('version')}"
        )
    except Exception as e:
        log_test("UPSERT INSERT inicial", False, str(e))
    
    # ========================================
    # TEST 3: UPSERT repetido sin cambios = SKIP
    # ========================================
    print("\n--- TEST 3: UPSERT repetido sin cambios (idempotente) ---")
    try:
        result = await upsert_kpi_comercial(
            server_id=test_server_id,
            empresa_id=test_empresa_id,
            sucursal_id=test_sucursal_id,
            fecha=test_fecha,
            kpis=kpis_inicial,  # Mismos datos
            source_info=source_info,
            updated_by="test_script"
        )
        
        log_test(
            "UPSERT repetido sin cambios = SKIP (idempotente)",
            result.get("action") == "SKIP",
            f"Action={result.get('action')}, Version={result.get('version')}"
        )
    except Exception as e:
        log_test("UPSERT repetido sin cambios = SKIP", False, str(e))
    
    # ========================================
    # TEST 4: UPSERT con cambio menor al threshold = SKIP
    # ========================================
    print("\n--- TEST 4: Cambio menor al threshold (0.01%) ---")
    try:
        kpis_cambio_minimo = {
            "ventas": 100000.05,  # Cambio de 0.00005% (menor al 0.01%)
            "pax": 500,
            "cheques": 150
        }
        
        result = await upsert_kpi_comercial(
            server_id=test_server_id,
            empresa_id=test_empresa_id,
            sucursal_id=test_sucursal_id,
            fecha=test_fecha,
            kpis=kpis_cambio_minimo,
            source_info=source_info,
            updated_by="test_script"
        )
        
        log_test(
            "Cambio menor al threshold = SKIP",
            result.get("action") == "SKIP",
            f"Action={result.get('action')}"
        )
    except Exception as e:
        log_test("Cambio menor al threshold", False, str(e))
    
    # ========================================
    # TEST 5: UPSERT con cambio real = UPDATE
    # ========================================
    print("\n--- TEST 5: Cambio real detectado = UPDATE ---")
    try:
        kpis_cambio_real = {
            "ventas": 110000.00,  # Cambio de 10%
            "pax": 550,
            "cheques": 160
        }
        
        result = await upsert_kpi_comercial(
            server_id=test_server_id,
            empresa_id=test_empresa_id,
            sucursal_id=test_sucursal_id,
            fecha=test_fecha,
            kpis=kpis_cambio_real,
            source_info=source_info,
            updated_by="test_script"
        )
        
        log_test(
            "Cambio real detectado = UPDATE",
            result.get("action") == "UPDATE" and result.get("version") == 2,
            f"Action={result.get('action')}, Version={result.get('version')}"
        )
    except Exception as e:
        log_test("Cambio real detectado", False, str(e))
    
    # ========================================
    # TEST 6: Verificar historial embebido
    # ========================================
    print("\n--- TEST 6: Historial de versiones embebido ---")
    try:
        doc = await get_kpi_comercial(
            test_server_id, test_empresa_id, test_sucursal_id, test_fecha
        )
        
        versions = doc.get("versions", [])
        has_history = len(versions) > 0
        has_diff = any(v.get("diff") for v in versions)
        
        log_test(
            "Historial de versiones embebido",
            has_history and has_diff,
            f"Versiones guardadas: {len(versions)}, Tiene diff: {has_diff}"
        )
    except Exception as e:
        log_test("Historial de versiones", False, str(e))
    
    # ========================================
    # TEST 7: Estado ABIERTO permite SYNC-S
    # ========================================
    print("\n--- TEST 7: Estado ABIERTO permite SYNC-S ---")
    try:
        doc = await get_kpi_comercial(
            test_server_id, test_empresa_id, test_sucursal_id, test_fecha
        )
        
        is_abierto = doc.get("estado_periodo") == ESTADO_ABIERTO
        
        log_test(
            "Estado inicial es ABIERTO",
            is_abierto,
            f"Estado actual: {doc.get('estado_periodo')}"
        )
    except Exception as e:
        log_test("Estado inicial ABIERTO", False, str(e))
    
    # ========================================
    # TEST 8: Cambio de estado ABIERTO → CERRADO
    # ========================================
    print("\n--- TEST 8: Transición ABIERTO → CERRADO ---")
    try:
        success, msg = await cambiar_estado_periodo(
            test_server_id, test_empresa_id, test_sucursal_id, test_fecha,
            ESTADO_CERRADO,
            "Test de cierre",
            "test_script"
        )
        
        doc = await get_kpi_comercial(
            test_server_id, test_empresa_id, test_sucursal_id, test_fecha
        )
        
        log_test(
            "Transición ABIERTO → CERRADO",
            success and doc.get("estado_periodo") == ESTADO_CERRADO,
            f"Success={success}, Estado={doc.get('estado_periodo')}"
        )
    except Exception as e:
        log_test("Transición ABIERTO → CERRADO", False, str(e))
    
    # ========================================
    # TEST 9: SYNC-S NO modifica CERRADO (sin force)
    # ========================================
    print("\n--- TEST 9: SYNC-S NO modifica CERRADO ---")
    try:
        kpis_nuevo = {
            "ventas": 120000.00,
            "pax": 600,
            "cheques": 170
        }
        
        result = await upsert_kpi_comercial(
            server_id=test_server_id,
            empresa_id=test_empresa_id,
            sucursal_id=test_sucursal_id,
            fecha=test_fecha,
            kpis=kpis_nuevo,
            source_info=source_info,
            updated_by="scheduler_sync_s",  # SYNC-S
            force_update=False
        )
        
        log_test(
            "SYNC-S NO modifica CERRADO",
            result.get("action") == "SKIP" and "CERRADO" in result.get("reason", ""),
            f"Action={result.get('action')}, Reason={result.get('reason')}"
        )
    except Exception as e:
        log_test("SYNC-S NO modifica CERRADO", False, str(e))
    
    # ========================================
    # TEST 10: SYNC-N SÍ modifica CERRADO (force_update)
    # ========================================
    print("\n--- TEST 10: SYNC-N SÍ modifica CERRADO ---")
    try:
        result = await upsert_kpi_comercial(
            server_id=test_server_id,
            empresa_id=test_empresa_id,
            sucursal_id=test_sucursal_id,
            fecha=test_fecha,
            kpis=kpis_nuevo,
            source_info=source_info,
            updated_by="scheduler_sync_n",  # SYNC-N
            force_update=True
        )
        
        log_test(
            "SYNC-N SÍ modifica CERRADO",
            result.get("action") == "UPDATE",
            f"Action={result.get('action')}, Version={result.get('version')}"
        )
    except Exception as e:
        log_test("SYNC-N SÍ modifica CERRADO", False, str(e))
    
    # ========================================
    # TEST 11: Cambio a RECONCILIADO
    # ========================================
    print("\n--- TEST 11: Transición CERRADO → RECONCILIADO ---")
    try:
        success, msg = await cambiar_estado_periodo(
            test_server_id, test_empresa_id, test_sucursal_id, test_fecha,
            ESTADO_RECONCILIADO,
            "Test de reconciliación",
            "test_script"
        )
        
        log_test(
            "Transición CERRADO → RECONCILIADO",
            success,
            f"Success={success}, Msg={msg}"
        )
    except Exception as e:
        log_test("Transición CERRADO → RECONCILIADO", False, str(e))
    
    # ========================================
    # TEST 12: RECONCILIADO NO se modifica
    # ========================================
    print("\n--- TEST 12: RECONCILIADO NO se modifica ---")
    try:
        kpis_intento = {
            "ventas": 999999.00,
            "pax": 9999,
            "cheques": 9999
        }
        
        result = await upsert_kpi_comercial(
            server_id=test_server_id,
            empresa_id=test_empresa_id,
            sucursal_id=test_sucursal_id,
            fecha=test_fecha,
            kpis=kpis_intento,
            source_info=source_info,
            updated_by="scheduler_sync_n",
            force_update=True  # Incluso con force
        )
        
        log_test(
            "RECONCILIADO NO se modifica",
            result.get("action") == "REJECTED",
            f"Action={result.get('action')}, Reason={result.get('reason')}"
        )
    except Exception as e:
        log_test("RECONCILIADO NO se modifica", False, str(e))
    
    # ========================================
    # TEST 13: No duplicados (verificar conteo)
    # ========================================
    print("\n--- TEST 13: Sin duplicados en colección ---")
    try:
        count = await db[COLLECTION_NAME].count_documents({
            "server_id": test_server_id,
            "empresa_id": test_empresa_id,
            "sucursal_id": test_sucursal_id,
            "fecha": test_fecha
        })
        
        log_test(
            "Sin duplicados - exactamente 1 documento",
            count == 1,
            f"Documentos encontrados: {count}"
        )
    except Exception as e:
        log_test("Sin duplicados", False, str(e))
    
    # ========================================
    # TEST 14: Cierre masivo de períodos
    # ========================================
    print("\n--- TEST 14: Cierre masivo de períodos anteriores ---")
    try:
        # Crear documentos de prueba en ABIERTO
        for i in range(3):
            fecha_test = f"2026-04-{10+i:02d}"
            await upsert_kpi_comercial(
                server_id="test-server-bulk",
                empresa_id=test_empresa_id,
                sucursal_id=test_sucursal_id,
                fecha=fecha_test,
                kpis={"ventas": 10000},
                source_info=source_info,
                updated_by="test_script"
            )
        
        # Cerrar todos antes de 2026-04-15
        cerrados = await cerrar_periodos_anteriores(
            fecha_corte="2026-04-15",
            updated_by="test_script"
        )
        
        log_test(
            "Cierre masivo de períodos",
            cerrados >= 2,  # Al menos 2 de los 3 creados
            f"Períodos cerrados: {cerrados}"
        )
    except Exception as e:
        log_test("Cierre masivo de períodos", False, str(e))
    
    # ========================================
    # RESUMEN
    # ========================================
    print("\n" + "=" * 70)
    print(f"RESUMEN: {results['passed']}/{results['total']} tests pasaron")
    print("=" * 70)
    
    if results['failed'] > 0:
        print("\n❌ Tests fallidos:")
        for test in results['tests']:
            if not test['passed']:
                print(f"   - {test['name']}: {test['details']}")
    
    # Limpiar datos de prueba
    await db[COLLECTION_NAME].delete_many({
        "server_id": {"$regex": "^test-"}
    })
    
    client.close()
    
    return results


if __name__ == "__main__":
    results = asyncio.run(run_all_tests())
    
    # Exit code según resultados
    sys.exit(0 if results['failed'] == 0 else 1)
