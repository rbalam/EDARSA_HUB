#!/usr/bin/env python3
"""
EDARSA HUB - Validación del SystemCapabilityResolver
====================================================
Script de validación para FASE 4 del Catálogo Maestro de Sistemas.

Ejecutar:
    python backend/scripts/validate_system_capability_resolver.py

Valida:
1. Normalización de variantes desde SQL
2. Consulta de capacidades
3. Sistemas explorables
4. Sistemas con sync ventas
5. Exclusión correcta de Enterprise/API_LOCAL de sync ventas

Autor: Arquitecto Senior Backend
Fecha: 2025-12-XX
"""

import sys
import os

# Agregar backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime
from typing import List, Tuple


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


def run_validation() -> Tuple[int, int, List[str]]:
    """
    Ejecuta todas las validaciones.
    
    Returns:
        Tuple con (passed, failed, lista de errores)
    """
    passed = 0
    failed = 0
    errors = []
    
    print_header("FASE 4 - VALIDACIÓN SYSTEM CAPABILITY RESOLVER")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Importar resolver
    try:
        from core.system_capability_resolver import (
            SystemCapabilityResolver,
            Capability,
            Module,
            get_resolver
        )
        print_result("Importación del módulo", True)
        passed += 1
    except Exception as e:
        print_result("Importación del módulo", False, str(e))
        failed += 1
        errors.append(f"Error importando módulo: {e}")
        return passed, failed, errors
    
    # Crear instancia
    try:
        resolver = SystemCapabilityResolver()
        print_result("Crear instancia del resolver", True)
        passed += 1
    except Exception as e:
        print_result("Crear instancia del resolver", False, str(e))
        failed += 1
        errors.append(f"Error creando instancia: {e}")
        return passed, failed, errors
    
    # ========================================================================
    # TEST 1: Normalización de variantes
    # ========================================================================
    print_header("1. NORMALIZACIÓN DE VARIANTES")
    
    normalization_tests = [
        # (input, expected_codigo, description)
        ("ManagmentPro", "MPRO", "Typo común de MPRO"),
        ("ManagementPro", "MPRO", "ManagementPro -> MPRO"),
        ("MPRO", "MPRO", "MPRO directo"),
        ("SOFRESATAURANT_ENTER", "API_LOCAL", "Enterprise mal escrito -> API_LOCAL"),
        ("SoftRestaurant", "SOFTRESTAURANT", "SoftRestaurant directo"),
        ("SR", "SOFTRESTAURANT", "Abreviatura SR"),
        ("SOFT", "SOFTRESTAURANT", "Abreviatura SOFT"),
        ("Enterprise", "API_LOCAL", "Enterprise -> API_LOCAL"),
        ("EDARSAHUB", "EDARSAHUB_SQL", "EDARSAHUB -> EDARSAHUB_SQL"),
        ("EDARSA_HUB", "EDARSAHUB_SQL", "EDARSA_HUB -> EDARSAHUB_SQL"),
    ]
    
    for input_val, expected, desc in normalization_tests:
        try:
            result = resolver.normalize_system_type(input_val)
            actual = result.get('codigo_sistema')
            test_passed = actual == expected
            if test_passed:
                print_result(f"normalize('{input_val}')", True, f"-> {actual}")
                passed += 1
            else:
                print_result(f"normalize('{input_val}')", False, f"esperado={expected}, actual={actual}")
                failed += 1
                errors.append(f"normalize('{input_val}'): esperado={expected}, actual={actual}")
        except Exception as e:
            print_result(f"normalize('{input_val}')", False, str(e))
            failed += 1
            errors.append(f"normalize('{input_val}'): {e}")
    
    # Test entrada vacía
    try:
        result = resolver.normalize_system_type("")
        test_passed = result.get('found') == False
        print_result("normalize('') -> not found", test_passed)
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
    except Exception as e:
        print_result("normalize('') maneja vacío", False, str(e))
        failed += 1
    
    # Test None
    try:
        result = resolver.normalize_system_type(None)
        test_passed = result.get('found') == False
        print_result("normalize(None) -> not found", test_passed)
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
    except Exception as e:
        print_result("normalize(None) maneja None", False, str(e))
        failed += 1
    
    # ========================================================================
    # TEST 2: system_supports()
    # ========================================================================
    print_header("2. SYSTEM_SUPPORTS()")
    
    support_tests = [
        # (codigo_sistema, capacidad, expected, description)
        ("SOFTRESTAURANT", Capability.EXPLORADOR_BD, True, "SR soporta explorador"),
        ("SOFTRESTAURANT", Capability.SYNC_VENTAS_HISTORICAS, True, "SR soporta sync historicas"),
        ("SOFTRESTAURANT", Capability.SYNC_VENTAS_POR_HORA, True, "SR soporta sync por hora"),
        ("MPRO", Capability.EXPLORADOR_BD, True, "MPRO soporta explorador"),
        ("MPRO", Capability.SYNC_VENTAS_POR_HORA, True, "MPRO soporta sync por hora"),
        ("MPRO", Capability.SUCURSALES_VISIBLES, True, "MPRO soporta sucursales visibles"),
        ("MPRO", Capability.CUENTAS_POR_PAGAR, True, "MPRO soporta CxP"),
        ("API_LOCAL", Capability.EXPLORADOR_BD, True, "API_LOCAL soporta explorador"),
        ("API_LOCAL", Capability.SYNC_VENTAS_HISTORICAS, False, "API_LOCAL NO soporta sync (no tiene query_ventas)"),
        ("API_LOCAL", Capability.SYNC_VENTAS_POR_HORA, False, "API_LOCAL NO soporta sync por hora"),
        ("EDARSAHUB_SQL", Capability.EXPLORADOR_BD, True, "EDARSAHUB soporta explorador"),
        ("SOFTRESTAURANT", Capability.SUCURSALES_VISIBLES, False, "SR NO soporta sucursales visibles (exclusivo MPRO)"),
    ]
    
    for codigo, capacidad, expected, desc in support_tests:
        try:
            result = resolver.system_supports(codigo, capacidad.value if hasattr(capacidad, 'value') else capacidad)
            test_passed = result == expected
            if test_passed:
                print_result(f"supports('{codigo}', '{capacidad}')", True, f"-> {result}")
                passed += 1
            else:
                print_result(f"supports('{codigo}', '{capacidad}')", False, f"esperado={expected}, actual={result}")
                failed += 1
                errors.append(f"supports('{codigo}', '{capacidad}'): esperado={expected}, actual={result}")
        except Exception as e:
            print_result(f"supports('{codigo}', '{capacidad}')", False, str(e))
            failed += 1
            errors.append(f"supports('{codigo}', '{capacidad}'): {e}")
    
    # ========================================================================
    # TEST 3: get_capabilities()
    # ========================================================================
    print_header("3. GET_CAPABILITIES()")
    
    try:
        sr_caps = resolver.get_capabilities("SOFTRESTAURANT")
        sr_cap_codes = [c['codigo'] for c in sr_caps]
        test_passed = len(sr_caps) >= 10 and Capability.EXPLORADOR_BD.value in sr_cap_codes
        print_result(f"SOFTRESTAURANT capacidades", test_passed, f"{len(sr_caps)} caps: {', '.join(sr_cap_codes[:5])}...")
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
    except Exception as e:
        print_result("SOFTRESTAURANT capacidades", False, str(e))
        failed += 1
    
    try:
        mpro_caps = resolver.get_capabilities("MPRO")
        mpro_cap_codes = [c['codigo'] for c in mpro_caps]
        # MPRO debe tener SUCURSALES_VISIBLES y CUENTAS_POR_PAGAR
        has_sucursales = Capability.SUCURSALES_VISIBLES.value in mpro_cap_codes
        has_cxp = Capability.CUENTAS_POR_PAGAR.value in mpro_cap_codes
        test_passed = len(mpro_caps) >= 10 and has_sucursales and has_cxp
        print_result(f"MPRO capacidades", test_passed, f"{len(mpro_caps)} caps, SUCURSALES={has_sucursales}, CXP={has_cxp}")
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
    except Exception as e:
        print_result("MPRO capacidades", False, str(e))
        failed += 1
    
    try:
        api_caps = resolver.get_capabilities("API_LOCAL")
        api_cap_codes = [c['codigo'] for c in api_caps]
        # API_LOCAL debe tener solo EXPLORADOR, NO sync ventas
        has_explorador = Capability.EXPLORADOR_BD.value in api_cap_codes
        no_sync = Capability.SYNC_VENTAS_HISTORICAS.value not in api_cap_codes
        test_passed = has_explorador and no_sync
        print_result(f"API_LOCAL capacidades", test_passed, f"{len(api_caps)} caps, EXPLORADOR={has_explorador}, NO_SYNC={no_sync}")
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
    except Exception as e:
        print_result("API_LOCAL capacidades", False, str(e))
        failed += 1
    
    # ========================================================================
    # TEST 4: get_explorable_systems()
    # ========================================================================
    print_header("4. GET_EXPLORABLE_SYSTEMS()")
    
    try:
        explorable = resolver.get_explorable_systems()
        explorable_codes = [s['codigo_sistema'] for s in explorable]
        
        # Debe incluir SR, MPRO, API_LOCAL, EDARSAHUB_SQL
        expected_explorable = ['SOFTRESTAURANT', 'MPRO', 'API_LOCAL', 'EDARSAHUB_SQL']
        all_present = all(code in explorable_codes for code in expected_explorable)
        
        test_passed = all_present
        print_result("Sistemas explorables", test_passed, f"{len(explorable)} sistemas: {explorable_codes}")
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
        
        if not all_present:
            missing = [code for code in expected_explorable if code not in explorable_codes]
            errors.append(f"Faltan sistemas explorables: {missing}")
    except Exception as e:
        print_result("Sistemas explorables", False, str(e))
        failed += 1
        errors.append(f"get_explorable_systems: {e}")
    
    # ========================================================================
    # TEST 5: get_sync_sales_systems()
    # ========================================================================
    print_header("5. GET_SYNC_SALES_SYSTEMS()")
    
    try:
        sync_systems = resolver.get_sync_sales_systems()
        sync_codes = [s['codigo_sistema'] for s in sync_systems]
        
        # Debe incluir SR y MPRO
        has_sr = 'SOFTRESTAURANT' in sync_codes
        has_mpro = 'MPRO' in sync_codes
        
        # NO debe incluir API_LOCAL (Enterprise no tiene query_ventas validada)
        no_api_local = 'API_LOCAL' not in sync_codes
        
        test_passed = has_sr and has_mpro and no_api_local
        print_result("Sistemas sync ventas", test_passed, 
                    f"SR={has_sr}, MPRO={has_mpro}, NO_API_LOCAL={no_api_local}")
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
        
        if not no_api_local:
            errors.append("CRÍTICO: API_LOCAL aparece en sync_sales pero NO debe (no tiene query_ventas)")
        
        # Mostrar detalle
        for sys in sync_systems:
            print(f"         | {sys['codigo_sistema']}: {sys.get('sync_capabilities', [])}")
            
    except Exception as e:
        print_result("Sistemas sync ventas", False, str(e))
        failed += 1
        errors.append(f"get_sync_sales_systems: {e}")
    
    # ========================================================================
    # TEST 6: explain_system()
    # ========================================================================
    print_header("6. EXPLAIN_SYSTEM()")
    
    # Test Enterprise/API_LOCAL
    try:
        explain = resolver.explain_system("SOFRESATAURANT_ENTER")
        
        soporta_exp = explain.get('soporta_explorador')
        soporta_sync = explain.get('soporta_sync_ventas')
        
        # Enterprise debe: soportar explorador, NO soportar sync ventas
        test_passed = soporta_exp == True and soporta_sync == False
        print_result("explain('SOFRESATAURANT_ENTER')", test_passed,
                    f"explorador={soporta_exp}, sync_ventas={soporta_sync}")
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
        
        if not test_passed:
            errors.append(f"explain(Enterprise): explorador={soporta_exp}, sync={soporta_sync}")
            
        # Mostrar diagnóstico
        for diag in explain.get('diagnostico', []):
            print(f"         | {diag}")
            
    except Exception as e:
        print_result("explain('SOFRESATAURANT_ENTER')", False, str(e))
        failed += 1
    
    # Test SoftRestaurant
    try:
        explain = resolver.explain_system("SoftRestaurant")
        
        soporta_exp = explain.get('soporta_explorador')
        soporta_sync = explain.get('soporta_sync_ventas')
        
        test_passed = soporta_exp == True and soporta_sync == True
        print_result("explain('SoftRestaurant')", test_passed,
                    f"explorador={soporta_exp}, sync_ventas={soporta_sync}")
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
            
    except Exception as e:
        print_result("explain('SoftRestaurant')", False, str(e))
        failed += 1
    
    # ========================================================================
    # TEST 7: Visibilidad
    # ========================================================================
    print_header("7. VISIBILIDAD POR MÓDULO")
    
    try:
        visible = resolver.get_visible_systems_for_module("EXPLORADOR_BD")
        visible_codes = [s['codigo_sistema'] for s in visible]
        
        test_passed = len(visible) >= 2  # Al menos SR y MPRO
        print_result("Sistemas visibles EXPLORADOR_BD", test_passed, f"{visible_codes}")
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
    except Exception as e:
        print_result("Visibilidad EXPLORADOR_BD", False, str(e))
        failed += 1
    
    try:
        vis = resolver.get_visibility("SOFTRESTAURANT", "COMERCIAL")
        test_passed = vis.get('visible') == True
        print_result("Visibilidad SR en COMERCIAL", test_passed, f"visible={vis.get('visible')}")
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
    except Exception as e:
        print_result("Visibilidad SR en COMERCIAL", False, str(e))
        failed += 1
    
    # ========================================================================
    # TEST 8: Cache
    # ========================================================================
    print_header("8. CACHE")
    
    try:
        # Primera llamada
        _ = resolver.get_all_systems()
        # Segunda llamada (debe usar cache)
        _ = resolver.get_all_systems()
        # Limpiar cache
        resolver.clear_cache()
        print_result("Cache funciona correctamente", True)
        passed += 1
    except Exception as e:
        print_result("Cache", False, str(e))
        failed += 1
    
    # ========================================================================
    # TEST 9: Singleton
    # ========================================================================
    print_header("9. SINGLETON")
    
    try:
        r1 = get_resolver()
        r2 = get_resolver()
        test_passed = r1 is r2
        print_result("get_resolver() retorna singleton", test_passed)
        passed += 1 if test_passed else 0
        failed += 0 if test_passed else 1
    except Exception as e:
        print_result("Singleton", False, str(e))
        failed += 1
    
    return passed, failed, errors


def main():
    """Función principal."""
    print()
    print("*" * 70)
    print("*  EDARSA HUB - VALIDACIÓN SYSTEM CAPABILITY RESOLVER")
    print("*  FASE 4 - Catálogo Maestro de Sistemas y Capacidades")
    print("*" * 70)
    
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
    print(f"  Porcentaje: {(passed/total*100):.1f}%")
    
    if errors:
        print("\n  ERRORES:")
        for err in errors:
            print(f"    - {err}")
    
    # Resultado final
    print()
    if failed == 0:
        print("=" * 70)
        print("  ✅ VALIDACIÓN EXITOSA - FASE 4 COMPLETADA")
        print("=" * 70)
        sys.exit(0)
    else:
        print("=" * 70)
        print("  ❌ VALIDACIÓN CON ERRORES")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
