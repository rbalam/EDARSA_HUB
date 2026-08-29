#!/usr/bin/env python3
"""
EDARSA HUB - Validación de Endpoints Catálogo de Sistemas
=========================================================
Script de validación para FASE 5 del Catálogo Maestro de Sistemas.

Ejecutar:
    python backend/scripts/validate_catalogo_sistemas_endpoints.py

Valida:
1. Backend operativo
2. Login operativo
3. Endpoints responden correctamente
4. API_LOCAL aparece en explorables
5. API_LOCAL NO aparece en sync-ventas
6. Normalización funciona
7. No regresión en otros endpoints

Autor: Arquitecto Senior Backend
Fecha: 2025-12-XX
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import Tuple, List, Dict, Any

# Configuración
API_URL = os.environ.get('API_URL', 'https://erp-crm-enterprise-1.preview.emergentagent.com')
TEST_EMAIL = "admin@inventario.com"
TEST_PASSWORD = "<TEST_PASSWORD>"


def print_header(title: str) -> None:
    """Imprime encabezado de sección."""
    print()
    print("=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_result(test_name: str, passed: bool, details: str = "") -> None:
    """Imprime resultado de un test."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} | {test_name}")
    if details:
        print(f"         | {details}")


def get_token() -> str:
    """Obtiene token de autenticación."""
    try:
        response = requests.post(
            f"{API_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        data = response.json()
        return data.get('token', '')
    except Exception as e:
        print(f"Error obteniendo token: {e}")
        return ""


def run_validation() -> Tuple[int, int, List[str]]:
    """
    Ejecuta todas las validaciones.
    
    Returns:
        Tuple con (passed, failed, lista de errores)
    """
    passed = 0
    failed = 0
    errors = []
    
    print_header("FASE 5 - VALIDACIÓN ENDPOINTS CATÁLOGO SISTEMAS")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"API URL: {API_URL}")
    
    # ========================================================================
    # TEST 1: Backend operativo
    # ========================================================================
    print_header("1. BACKEND OPERATIVO")
    
    try:
        response = requests.get(f"{API_URL}/api/health", timeout=10)
        test_passed = response.status_code == 200
        print_result("GET /api/health", test_passed, f"status={response.status_code}")
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
    except Exception as e:
        print_result("GET /api/health", False, str(e))
        failed += 1
        errors.append(f"Backend no responde: {e}")
        return passed, failed, errors
    
    # ========================================================================
    # TEST 2: Login operativo
    # ========================================================================
    print_header("2. LOGIN OPERATIVO")
    
    token = get_token()
    test_passed = len(token) > 0
    print_result("POST /api/auth/login", test_passed, f"token={token[:30]}..." if token else "NO TOKEN")
    passed += 1 if test_passed else 0
    failed += 0 if test_passed else 1
    
    if not token:
        errors.append("No se pudo obtener token")
        return passed, failed, errors
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # ========================================================================
    # TEST 3: Endpoint /api/catalogos/sistemas
    # ========================================================================
    print_header("3. ENDPOINTS CATÁLOGO SISTEMAS")
    
    # GET /api/catalogos/sistemas-capacidades
    try:
        response = requests.get(f"{API_URL}/api/catalogos/sistemas-capacidades", headers=headers, timeout=30)
        data = response.json()
        test_passed = data.get('success') == True and len(data.get('data', [])) >= 3
        sistemas = [s.get('codigo_sistema') for s in data.get('data', [])]
        print_result("GET /api/catalogos/sistemas-capacidades", test_passed, f"sistemas: {sistemas}")
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
    except Exception as e:
        print_result("GET /api/catalogos/sistemas", False, str(e))
        failed += 1
        errors.append(f"/api/catalogos/sistemas error: {e}")
    
    # GET /api/catalogos/sistemas-capacidades/explorables
    try:
        response = requests.get(f"{API_URL}/api/catalogos/sistemas-capacidades/explorables", headers=headers, timeout=30)
        data = response.json()
        explorables = [s.get('codigo_sistema') for s in data.get('data', [])]
        
        # IMPORTANTE: API_LOCAL debe aparecer aquí
        api_local_in_explorables = 'API_LOCAL' in explorables
        sr_in_explorables = 'SOFTRESTAURANT' in explorables
        mpro_in_explorables = 'MPRO' in explorables
        
        test_passed = api_local_in_explorables and sr_in_explorables and mpro_in_explorables
        print_result(
            "GET /api/catalogos/sistemas-capacidades/explorables", 
            test_passed, 
            f"API_LOCAL={api_local_in_explorables}, SR={sr_in_explorables}, MPRO={mpro_in_explorables}"
        )
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
        
        if not api_local_in_explorables:
            errors.append("API_LOCAL no aparece en explorables")
    except Exception as e:
        print_result("GET /api/catalogos/sistemas/explorables", False, str(e))
        failed += 1
        errors.append(f"/explorables error: {e}")
    
    # GET /api/catalogos/sistemas-capacidades/sync-ventas
    try:
        response = requests.get(f"{API_URL}/api/catalogos/sistemas-capacidades/sync-ventas", headers=headers, timeout=30)
        data = response.json()
        sync_systems = [s.get('codigo_sistema') for s in data.get('data', [])]
        
        # IMPORTANTE: API_LOCAL NO debe aparecer aquí
        api_local_in_sync = 'API_LOCAL' in sync_systems
        sr_in_sync = 'SOFTRESTAURANT' in sync_systems
        mpro_in_sync = 'MPRO' in sync_systems
        
        test_passed = not api_local_in_sync and sr_in_sync and mpro_in_sync
        print_result(
            "GET /api/catalogos/sistemas-capacidades/sync-ventas", 
            test_passed, 
            f"API_LOCAL_EXCLUDED={not api_local_in_sync}, SR={sr_in_sync}, MPRO={mpro_in_sync}"
        )
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
        
        if api_local_in_sync:
            errors.append("CRÍTICO: API_LOCAL aparece en sync-ventas pero NO debe")
    except Exception as e:
        print_result("GET /api/catalogos/sistemas/sync-ventas", False, str(e))
        failed += 1
        errors.append(f"/sync-ventas error: {e}")
    
    # ========================================================================
    # TEST 4: Normalización
    # ========================================================================
    print_header("4. NORMALIZACIÓN")
    
    normalization_tests = [
        ("ManagmentPro", "MPRO"),
        ("SOFRESATAURANT_ENTER", "API_LOCAL"),
        ("SoftRestaurant", "SOFTRESTAURANT"),
        ("SR", "SOFTRESTAURANT"),
    ]
    
    for input_val, expected in normalization_tests:
        try:
            response = requests.get(
                f"{API_URL}/api/catalogos/sistemas-capacidades/normalizar/{input_val}", 
                headers=headers, 
                timeout=30
            )
            data = response.json()
            actual = data.get('data', {}).get('codigo_sistema')
            test_passed = actual == expected
            print_result(f"normalizar('{input_val}')", test_passed, f"-> {actual}")
            passed += 1 if test_passed else 0
            failed += 0 if test_passed else 1
            
            if not test_passed:
                errors.append(f"normalizar('{input_val}'): esperado={expected}, actual={actual}")
        except Exception as e:
            print_result(f"normalizar('{input_val}')", False, str(e))
            failed += 1
    
    # ========================================================================
    # TEST 5: Diagnóstico
    # ========================================================================
    print_header("5. DIAGNÓSTICO")
    
    # Diagnóstico Enterprise
    try:
        response = requests.get(
            f"{API_URL}/api/catalogos/sistemas-capacidades/diagnostico/SOFRESATAURANT_ENTER", 
            headers=headers, 
            timeout=30
        )
        data = response.json()
        result = data.get('data', {})
        soporta_exp = result.get('soporta_explorador')
        soporta_sync = result.get('soporta_sync_ventas')
        
        test_passed = soporta_exp == True and soporta_sync == False
        print_result(
            "diagnostico(Enterprise)", 
            test_passed, 
            f"explorador={soporta_exp}, sync_ventas={soporta_sync}"
        )
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
    except Exception as e:
        print_result("diagnostico(Enterprise)", False, str(e))
        failed += 1
    
    # ========================================================================
    # TEST 6: Capacidades por sistema
    # ========================================================================
    print_header("6. CAPACIDADES POR SISTEMA")
    
    try:
        response = requests.get(
            f"{API_URL}/api/catalogos/sistemas-capacidades/SOFTRESTAURANT/capacidades", 
            headers=headers, 
            timeout=30
        )
        data = response.json()
        caps = [c.get('codigo') for c in data.get('data', [])]
        test_passed = len(caps) >= 10 and 'EXPLORADOR_BD' in caps and 'SYNC_VENTAS_HISTORICAS' in caps
        print_result("GET /sistemas-capacidades/SOFTRESTAURANT/capacidades", test_passed, f"{len(caps)} capacidades")
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
    except Exception as e:
        print_result("GET /SOFTRESTAURANT/capacidades", False, str(e))
        failed += 1
    
    # ========================================================================
    # TEST 7: Sistemas por capacidad
    # ========================================================================
    print_header("7. SISTEMAS POR CAPACIDAD")
    
    try:
        response = requests.get(
            f"{API_URL}/api/catalogos/sistemas-capacidades/capacidades/EXPLORADOR_BD", 
            headers=headers, 
            timeout=30
        )
        data = response.json()
        systems = [s.get('codigo_sistema') for s in data.get('data', [])]
        test_passed = 'SOFTRESTAURANT' in systems and 'MPRO' in systems and 'API_LOCAL' in systems
        print_result("GET /sistemas-capacidades/capacidades/EXPLORADOR_BD", test_passed, f"sistemas: {systems}")
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
    except Exception as e:
        print_result("GET /capacidades/EXPLORADOR_BD", False, str(e))
        failed += 1
    
    # ========================================================================
    # TEST 8: No regresión
    # ========================================================================
    print_header("8. NO REGRESIÓN")
    
    # Explorador BD conexiones
    try:
        response = requests.get(
            f"{API_URL}/api/explorador/conexiones-explorables", 
            headers=headers, 
            timeout=30
        )
        data = response.json()
        num_conexiones = len(data.get('data', []))
        test_passed = num_conexiones >= 10
        print_result("/explorador/conexiones-explorables", test_passed, f"{num_conexiones} conexiones")
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
    except Exception as e:
        print_result("/explorador/conexiones-explorables", False, str(e))
        failed += 1
    
    # Servidores
    try:
        response = requests.get(f"{API_URL}/api/servers", headers=headers, timeout=30)
        data = response.json()
        num_servers = len(data) if isinstance(data, list) else 0
        test_passed = num_servers >= 5
        print_result("/api/servers", test_passed, f"{num_servers} servidores")
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
    except Exception as e:
        print_result("/api/servers", False, str(e))
        failed += 1
    
    # Consultas SQL
    try:
        response = requests.get(f"{API_URL}/api/consultas-sql/disponibles", headers=headers, timeout=30)
        test_passed = response.status_code == 200
        print_result("/api/consultas-sql/disponibles", test_passed, f"status={response.status_code}")
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
    except Exception as e:
        print_result("/api/consultas-sql/disponibles", False, str(e))
        failed += 1
    
    # ========================================================================
    # TEST 9: Sin autenticación
    # ========================================================================
    print_header("9. AUTENTICACIÓN REQUERIDA")
    
    try:
        response = requests.get(f"{API_URL}/api/catalogos/sistemas-capacidades", timeout=10)
        # Debe rechazar sin token
        test_passed = response.status_code in [401, 403]
        print_result("Sin token rechaza correctamente", test_passed, f"status={response.status_code}")
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
    except Exception as e:
        print_result("Validación sin token", False, str(e))
        failed += 1
    
    return passed, failed, errors


def main():
    """Función principal."""
    print()
    print("*" * 70)
    print("*  EDARSA HUB - VALIDACIÓN ENDPOINTS CATÁLOGO SISTEMAS")
    print("*  FASE 5 - Catálogo Maestro de Sistemas y Capacidades")
    print("*" * 70)
    
    # Obtener API_URL desde frontend/.env
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    global API_URL
                    API_URL = line.split('=', 1)[1].strip()
                    break
    except Exception:
        pass
    
    print(f"API URL: {API_URL}")
    
    try:
        passed, failed, errors = run_validation()
    except Exception as e:
        print(f"\n❌ ERROR FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Resumen
    print_header("RESUMEN DE VALIDACIÓN")
    total = passed + failed
    print(f"  Total tests: {total}")
    print(f"  Pasaron: {passed} ✅")
    print(f"  Fallaron: {failed} ❌")
    print(f"  Porcentaje: {(passed/total*100):.1f}%" if total > 0 else "  Porcentaje: N/A")
    
    if errors:
        print("\n  ERRORES:")
        for err in errors:
            print(f"    - {err}")
    
    # Resultado final
    print()
    if failed == 0:
        print("=" * 70)
        print("  ✅ VALIDACIÓN EXITOSA - FASE 5 COMPLETADA")
        print("=" * 70)
        sys.exit(0)
    else:
        print("=" * 70)
        print("  ❌ VALIDACIÓN CON ERRORES")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
