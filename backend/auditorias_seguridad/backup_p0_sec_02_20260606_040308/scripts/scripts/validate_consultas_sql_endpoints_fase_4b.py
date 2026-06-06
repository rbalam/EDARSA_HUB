#!/usr/bin/env python3
"""
FASE 4B: Script de Validación de Endpoints /api/consultas-sql/*
================================================================

Valida:
1. Endpoints existentes siguen funcionando
2. Nuevos endpoints FASE 4B funcionan
3. Seguridad: no expone secretos
4. Bloqueos de SQL peligroso funcionan
5. No regresión en legacy

NO ejecuta pruebas destructivas.
NO ejecuta consultas pesadas.
"""

import sys
import json
import requests
from datetime import datetime

# Configuración
API_BASE = "https://a416fcd5-32f5-4c1e-9c95-aa9ffe6ee45b.preview.emergentagent.com"
CREDENTIALS = {
    "email": "admin@inventario.com",
    "password": "<TEST_PASSWORD>"
}

# Contadores
tests_passed = 0
tests_failed = 0
results = []


def log_test(name: str, passed: bool, details: str = ""):
    global tests_passed, tests_failed
    status = "✅ PASS" if passed else "❌ FAIL"
    if passed:
        tests_passed += 1
    else:
        tests_failed += 1
    print(f"{status}: {name}")
    if details and not passed:
        print(f"       → {details}")
    results.append({
        "test": name,
        "passed": passed,
        "details": details
    })


def get_auth_token():
    """Obtiene token de autenticación."""
    try:
        resp = requests.post(
            f"{API_BASE}/api/auth/login",
            json=CREDENTIALS,
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("access_token") or data.get("token")
        return None
    except Exception as e:
        print(f"Error obteniendo token: {e}")
        return None


def run_tests():
    global tests_passed, tests_failed
    
    print("\n" + "="*60)
    print("FASE 4B: VALIDACIÓN DE ENDPOINTS CONSULTAS SQL")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"API Base: {API_BASE}")
    print("="*60 + "\n")
    
    # 1. Login
    print("--- AUTENTICACIÓN ---")
    token = get_auth_token()
    log_test("Login funciona", token is not None, "No se pudo obtener token" if not token else "")
    
    if not token:
        print("\n❌ ABORTANDO: No se puede continuar sin autenticación")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. /api/servers legacy
    print("\n--- LEGACY ---")
    try:
        resp = requests.get(f"{API_BASE}/api/servers", headers=headers, timeout=30)
        log_test("/api/servers funciona", resp.status_code == 200, f"Status: {resp.status_code}")
    except Exception as e:
        log_test("/api/servers funciona", False, str(e))
    
    # 3. /api/catalogo/consultas-rich legacy
    try:
        resp = requests.get(f"{API_BASE}/api/catalogo/consultas-rich", headers=headers, timeout=30)
        log_test("/api/catalogo/consultas-rich legacy funciona", resp.status_code == 200, f"Status: {resp.status_code}")
    except Exception as e:
        log_test("/api/catalogo/consultas-rich legacy funciona", False, str(e))
    
    # 4. Endpoints FASE 4 existentes
    print("\n--- ENDPOINTS FASE 4 EXISTENTES ---")
    
    try:
        resp = requests.get(f"{API_BASE}/api/consultas-sql/catalogo", headers=headers, timeout=30)
        data = resp.json() if resp.status_code == 200 else {}
        log_test("GET /api/consultas-sql/catalogo funciona", 
                 resp.status_code == 200 and data.get("success"), 
                 f"Status: {resp.status_code}, Total: {data.get('total', 0)}")
    except Exception as e:
        log_test("GET /api/consultas-sql/catalogo funciona", False, str(e))
    
    try:
        resp = requests.get(f"{API_BASE}/api/consultas-sql/catalogo/SR_VENTAS_DIA", headers=headers, timeout=30)
        data = resp.json() if resp.status_code == 200 else {}
        log_test("GET /api/consultas-sql/catalogo/{codigo} funciona", 
                 resp.status_code == 200 and data.get("success"),
                 f"Status: {resp.status_code}")
    except Exception as e:
        log_test("GET /api/consultas-sql/catalogo/{codigo} funciona", False, str(e))
    
    try:
        resp = requests.get(f"{API_BASE}/api/consultas-sql/sistemas", headers=headers, timeout=30)
        data = resp.json() if resp.status_code == 200 else {}
        log_test("GET /api/consultas-sql/sistemas funciona", 
                 resp.status_code == 200 and data.get("success"),
                 f"Status: {resp.status_code}")
    except Exception as e:
        log_test("GET /api/consultas-sql/sistemas funciona", False, str(e))
    
    try:
        resp = requests.get(f"{API_BASE}/api/consultas-sql/modulos", headers=headers, timeout=30)
        data = resp.json() if resp.status_code == 200 else {}
        log_test("GET /api/consultas-sql/modulos funciona", 
                 resp.status_code == 200 and data.get("success"),
                 f"Status: {resp.status_code}")
    except Exception as e:
        log_test("GET /api/consultas-sql/modulos funciona", False, str(e))
    
    try:
        resp = requests.post(
            f"{API_BASE}/api/consultas-sql/validar",
            headers=headers,
            json={"codigo_consulta": "SR_VENTAS_DIA"},
            timeout=30
        )
        data = resp.json() if resp.status_code == 200 else {}
        log_test("POST /api/consultas-sql/validar funciona", 
                 resp.status_code == 200 and data.get("success"),
                 f"Status: {resp.status_code}, Valid: {data.get('is_valid')}")
    except Exception as e:
        log_test("POST /api/consultas-sql/validar funciona", False, str(e))
    
    # 5. Nuevos endpoints FASE 4B
    print("\n--- NUEVOS ENDPOINTS FASE 4B ---")
    
    try:
        resp = requests.get(f"{API_BASE}/api/consultas-sql/catalogo/SR_VENTAS_DIA/versiones", headers=headers, timeout=30)
        data = resp.json() if resp.status_code == 200 else {}
        log_test("GET /catalogo/{codigo}/versiones funciona", 
                 resp.status_code == 200 and data.get("success"),
                 f"Status: {resp.status_code}, Versiones: {data.get('total_versiones', 0)}")
    except Exception as e:
        log_test("GET /catalogo/{codigo}/versiones funciona", False, str(e))
    
    try:
        resp = requests.get(f"{API_BASE}/api/consultas-sql/catalogo/SR_VENTAS_DIA/servidores", headers=headers, timeout=30)
        data = resp.json() if resp.status_code == 200 else {}
        log_test("GET /catalogo/{codigo}/servidores funciona", 
                 resp.status_code == 200 and data.get("success"),
                 f"Status: {resp.status_code}, Servidores: {data.get('total_servidores', 0)}")
    except Exception as e:
        log_test("GET /catalogo/{codigo}/servidores funciona", False, str(e))
    
    # 6. POST /validar-texto
    print("\n--- VALIDAR-TEXTO (FASE 4B) ---")
    
    try:
        resp = requests.post(
            f"{API_BASE}/api/consultas-sql/validar-texto",
            headers=headers,
            json={"sql_texto": "SELECT TOP 10 * FROM tabla"},
            timeout=30
        )
        data = resp.json() if resp.status_code == 200 else {}
        log_test("validar-texto permite SELECT seguro", 
                 resp.status_code == 200 and data.get("is_valid") == True,
                 f"Status: {resp.status_code}, Valid: {data.get('is_valid')}")
    except Exception as e:
        log_test("validar-texto permite SELECT seguro", False, str(e))
    
    try:
        resp = requests.post(
            f"{API_BASE}/api/consultas-sql/validar-texto",
            headers=headers,
            json={"sql_texto": "DELETE FROM usuarios"},
            timeout=30
        )
        data = resp.json() if resp.status_code == 200 else {}
        log_test("validar-texto bloquea DELETE", 
                 resp.status_code == 200 and data.get("is_valid") == False,
                 f"Status: {resp.status_code}, Valid: {data.get('is_valid')}")
    except Exception as e:
        log_test("validar-texto bloquea DELETE", False, str(e))
    
    try:
        resp = requests.post(
            f"{API_BASE}/api/consultas-sql/validar-texto",
            headers=headers,
            json={"sql_texto": "DROP TABLE usuarios"},
            timeout=30
        )
        data = resp.json() if resp.status_code == 200 else {}
        log_test("validar-texto bloquea DROP", 
                 resp.status_code == 200 and data.get("is_valid") == False,
                 f"Status: {resp.status_code}, Valid: {data.get('is_valid')}")
    except Exception as e:
        log_test("validar-texto bloquea DROP", False, str(e))
    
    try:
        resp = requests.post(
            f"{API_BASE}/api/consultas-sql/validar-texto",
            headers=headers,
            json={"sql_texto": "SELECT 1; DROP TABLE x;--"},
            timeout=30
        )
        data = resp.json() if resp.status_code == 200 else {}
        log_test("validar-texto bloquea múltiples statements", 
                 resp.status_code == 200 and data.get("is_valid") == False,
                 f"Status: {resp.status_code}, Valid: {data.get('is_valid')}")
    except Exception as e:
        log_test("validar-texto bloquea múltiples statements", False, str(e))
    
    # 7. Seguridad /ejecutar
    print("\n--- SEGURIDAD /ejecutar (FASE 4B) ---")
    
    try:
        resp = requests.post(
            f"{API_BASE}/api/consultas-sql/ejecutar",
            headers=headers,
            json={"sql": "SELECT 1"},  # Intento de SQL libre
            timeout=30
        )
        data = resp.json() if resp.status_code == 200 else {}
        # Debe rechazar porque no tiene codigo_consulta ni consulta_id
        log_test("/ejecutar rechaza SQL libre (sin codigo_consulta)", 
                 data.get("status") == "VALIDATION_FAILED",
                 f"Status: {data.get('status')}")
    except Exception as e:
        log_test("/ejecutar rechaza SQL libre (sin codigo_consulta)", False, str(e))
    
    try:
        resp = requests.post(
            f"{API_BASE}/api/consultas-sql/ejecutar",
            headers=headers,
            json={"codigo_consulta": "SR_VENTAS_DIA", "parametros": {"param_no_existe": "x"}},
            timeout=30
        )
        data = resp.json() if resp.status_code == 200 else {}
        log_test("/ejecutar rechaza parámetros no declarados", 
                 data.get("status") == "INVALID_PARAMS",
                 f"Status: {data.get('status')}")
    except Exception as e:
        log_test("/ejecutar rechaza parámetros no declarados", False, str(e))
    
    # 8. Verificar que no expone secretos
    print("\n--- VERIFICACIÓN DE NO EXPOSICIÓN DE SECRETOS ---")
    
    try:
        resp = requests.get(f"{API_BASE}/api/consultas-sql/catalogo/SR_VENTAS_DIA/servidores", headers=headers, timeout=30)
        data = resp.json() if resp.status_code == 200 else {}
        response_text = json.dumps(data).lower()
        no_expone_password = "password" not in response_text or "password\":" not in response_text
        no_expone_apikey = "api_key" not in response_text and "apikey" not in response_text
        log_test("No expone password en servidores", no_expone_password, "")
        log_test("No expone api_key en servidores", no_expone_apikey, "")
    except Exception as e:
        log_test("No expone password en servidores", False, str(e))
        log_test("No expone api_key en servidores", False, str(e))
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    print(f"Tests pasados: {tests_passed}")
    print(f"Tests fallidos: {tests_failed}")
    print(f"Total: {tests_passed + tests_failed}")
    print(f"Porcentaje éxito: {(tests_passed / (tests_passed + tests_failed)) * 100:.1f}%")
    print("="*60)
    
    return tests_failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
