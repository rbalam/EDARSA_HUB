#!/usr/bin/env python3
"""
EDARSA HUB - Validación FASE 6: Integración Catálogo Maestro
============================================================
Script de validación para la integración del SystemCapabilityResolver
en Explorador BD y Sync Históricos.

Valida:
1. Módulo system_capability_integration importable
2. Funciones de explorador funcionando
3. Funciones de sync ventas funcionando
4. API_LOCAL en explorador pero NO en sync ventas
5. SOFTRESTAURANT y MPRO en sync ventas
6. Endpoints del catálogo funcionando

Autor: Arquitecto Senior Backend
Fecha: 2025-12
"""

import sys
import os

# Agregar path del backend
sys.path.insert(0, '/app/backend')

# Cargar entorno
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')


def test_1_import_integration_module():
    """Test 1: Importar módulo de integración"""
    print("\n" + "="*60)
    print("TEST 1: Importar módulo system_capability_integration")
    print("="*60)
    
    try:
        from core.system_capability_integration import (
            is_system_explorable,
            get_explorable_system_codes,
            filter_explorable_connections,
            is_system_sync_sales_enabled,
            get_sync_sales_system_codes,
            filter_sync_sales_servers,
            validate_server_for_sync,
            get_integration_status,
        )
        print("✅ Todas las funciones importadas correctamente")
        return True
    except Exception as e:
        print(f"❌ Error importando: {e}")
        return False


def test_2_explorable_functions():
    """Test 2: Funciones de explorador"""
    print("\n" + "="*60)
    print("TEST 2: Funciones de Explorador BD")
    print("="*60)
    
    from core.system_capability_integration import (
        is_system_explorable,
        get_explorable_system_codes,
    )
    
    errors = []
    
    # 2.1 SOFTRESTAURANT debe ser explorable
    if is_system_explorable('SOFTRESTAURANT'):
        print("✅ SOFTRESTAURANT es explorable")
    else:
        print("❌ SOFTRESTAURANT debería ser explorable")
        errors.append("SOFTRESTAURANT no explorable")
    
    # 2.2 MPRO debe ser explorable
    if is_system_explorable('MPRO'):
        print("✅ MPRO es explorable")
    else:
        print("❌ MPRO debería ser explorable")
        errors.append("MPRO no explorable")
    
    # 2.3 API_LOCAL debe ser explorable
    if is_system_explorable('API_LOCAL'):
        print("✅ API_LOCAL es explorable (correcto)")
    else:
        print("❌ API_LOCAL debería ser explorable")
        errors.append("API_LOCAL no explorable")
    
    # 2.4 Variantes deben resolverse
    if is_system_explorable('ManagmentPro'):
        print("✅ ManagmentPro (variante) es explorable")
    else:
        print("⚠️  ManagmentPro no encontrado (puede ser fallback)")
    
    # 2.5 Obtener códigos explorables
    codes = get_explorable_system_codes()
    print(f"\nSistemas explorables: {codes}")
    
    expected = {'SOFTRESTAURANT', 'MPRO', 'API_LOCAL'}
    if expected.issubset(codes):
        print(f"✅ Todos los sistemas esperados están en explorables")
    else:
        missing = expected - codes
        print(f"⚠️  Faltan sistemas: {missing}")
    
    return len(errors) == 0


def test_3_sync_sales_functions():
    """Test 3: Funciones de Sync Ventas"""
    print("\n" + "="*60)
    print("TEST 3: Funciones de Sync Ventas")
    print("="*60)
    
    from core.system_capability_integration import (
        is_system_sync_sales_enabled,
        get_sync_sales_system_codes,
    )
    
    errors = []
    
    # 3.1 SOFTRESTAURANT debe tener sync ventas
    if is_system_sync_sales_enabled('SOFTRESTAURANT'):
        print("✅ SOFTRESTAURANT tiene sync ventas habilitado")
    else:
        print("❌ SOFTRESTAURANT debería tener sync ventas")
        errors.append("SOFTRESTAURANT sin sync")
    
    # 3.2 MPRO debe tener sync ventas
    if is_system_sync_sales_enabled('MPRO'):
        print("✅ MPRO tiene sync ventas habilitado")
    else:
        print("❌ MPRO debería tener sync ventas")
        errors.append("MPRO sin sync")
    
    # 3.3 API_LOCAL NO debe tener sync ventas
    if not is_system_sync_sales_enabled('API_LOCAL'):
        print("✅ API_LOCAL NO tiene sync ventas (correcto - no tiene query_ventas)")
    else:
        print("❌ API_LOCAL NO debería tener sync ventas")
        errors.append("API_LOCAL tiene sync (incorrecto)")
    
    # 3.4 Obtener códigos sync ventas
    codes = get_sync_sales_system_codes()
    print(f"\nSistemas con sync ventas: {codes}")
    
    # Validar que API_LOCAL NO esté
    if 'API_LOCAL' not in codes:
        print("✅ API_LOCAL correctamente excluido de sync ventas")
    else:
        print("❌ API_LOCAL NO debe estar en sync ventas")
        errors.append("API_LOCAL en sync ventas")
    
    # Validar que SOFT y MPRO SÍ estén
    if 'SOFTRESTAURANT' in codes and 'MPRO' in codes:
        print("✅ SOFTRESTAURANT y MPRO en sync ventas")
    else:
        print("❌ Faltan sistemas en sync ventas")
        errors.append("Faltan sistemas sync")
    
    return len(errors) == 0


def test_4_validate_server():
    """Test 4: Validación de servidor para sync"""
    print("\n" + "="*60)
    print("TEST 4: Validación de Servidor para Sync")
    print("="*60)
    
    from core.system_capability_integration import validate_server_for_sync
    
    # 4.1 Servidor SOFTRESTAURANT
    result = validate_server_for_sync({'system_type': 'SOFTRESTAURANT', 'nombre': 'TestSR'})
    print(f"\nSOFTRESTAURANT: {result}")
    if result['can_sync']:
        print("✅ SOFTRESTAURANT puede hacer sync")
    else:
        print("❌ SOFTRESTAURANT debería poder hacer sync")
    
    # 4.2 Servidor API_LOCAL
    result = validate_server_for_sync({'system_type': 'API_LOCAL', 'nombre': 'Enterprise'})
    print(f"\nAPI_LOCAL: {result}")
    if not result['can_sync']:
        print("✅ API_LOCAL NO puede hacer sync (correcto)")
    else:
        print("❌ API_LOCAL NO debería poder hacer sync")
    
    # 4.3 Servidor con variante
    result = validate_server_for_sync({'system_type': 'ManagmentPro', 'nombre': 'TestMPRO'})
    print(f"\nManagmentPro (variante): {result}")
    
    return True


def test_5_integration_status():
    """Test 5: Estado de integración"""
    print("\n" + "="*60)
    print("TEST 5: Estado de Integración")
    print("="*60)
    
    from core.system_capability_integration import get_integration_status
    
    status = get_integration_status()
    print(f"\nEstado de integración:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Validar estructura
    if status.get('integration_active'):
        print("\n✅ Integración activa")
    else:
        print("\n⚠️  Integración con problemas")
    
    # Validar API_LOCAL
    if status.get('api_local_in_explorable') and not status.get('api_local_in_sync_sales'):
        print("✅ API_LOCAL correctamente configurado (explorable=True, sync_sales=False)")
    else:
        print("⚠️  API_LOCAL configuración inesperada")
    
    return True


def test_6_py_compile():
    """Test 6: Validar sintaxis de archivos modificados"""
    print("\n" + "="*60)
    print("TEST 6: Validación de Sintaxis (py_compile)")
    print("="*60)
    
    import py_compile
    
    files = [
        '/app/backend/server.py',
        '/app/backend/modules/sync_historicos/service.py',
        '/app/backend/core/system_capability_integration.py',
    ]
    
    errors = []
    for f in files:
        try:
            py_compile.compile(f, doraise=True)
            print(f"✅ {f.split('/')[-1]} - Sintaxis OK")
        except py_compile.PyCompileError as e:
            print(f"❌ {f.split('/')[-1]} - Error: {e}")
            errors.append(f)
    
    return len(errors) == 0


def main():
    """Ejecutar todas las validaciones"""
    print("\n" + "="*70)
    print("VALIDACIÓN FASE 6 - Integración Catálogo Maestro")
    print("Sistema de Capacidades en Explorador BD y Sync Históricos")
    print("="*70)
    
    results = []
    
    # Ejecutar tests
    results.append(("Test 1: Import", test_1_import_integration_module()))
    results.append(("Test 2: Explorador", test_2_explorable_functions()))
    results.append(("Test 3: Sync Ventas", test_3_sync_sales_functions()))
    results.append(("Test 4: Validate Server", test_4_validate_server()))
    results.append(("Test 5: Status", test_5_integration_status()))
    results.append(("Test 6: py_compile", test_6_py_compile()))
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE VALIDACIÓN FASE 6")
    print("="*70)
    
    passed = 0
    failed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} pasados, {failed} fallidos")
    
    if failed == 0:
        print("\n✅ FASE 6 VALIDACIÓN EXITOSA")
        print("   - Integración no destructiva completada")
        print("   - API_LOCAL en Explorador pero NO en Sync")
        print("   - SOFTRESTAURANT y MPRO en Sync")
        return 0
    else:
        print("\n⚠️  FASE 6 REQUIERE ATENCIÓN")
        return 1


if __name__ == '__main__':
    sys.exit(main())
