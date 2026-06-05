"""
TEST DE PARIDAD SUB-BLOQUE 5.1
==============================
Valida que el endpoint /comercial/dashboard/{server_id} migrado
produzca respuestas estructuralmente idénticas.

Fecha: 2026-04-23
Endpoint: /comercial/dashboard/{server_id}
Migración: SoftRestaurant - queries de período actual, anterior y año anterior
"""

import sys
import json

def test_estructura_respuesta():
    """Valida que la estructura de respuesta sea la esperada"""
    with open('/tmp/despues_dashboard_sr.json') as f:
        data = json.load(f)
    
    # Campos obligatorios de primer nivel
    campos_requeridos = [
        'source_status', 'source_message', 'server_name', 'server_type',
        'fecha_inicio', 'fecha_fin', 'kpis', 'comparativo', 'alertas'
    ]
    
    for campo in campos_requeridos:
        assert campo in data, f"Falta campo: {campo}"
    
    print("✅ TEST 1: Estructura de respuesta correcta")
    return True


def test_kpis_base():
    """Valida que los KPIs base estén presentes"""
    with open('/tmp/despues_dashboard_sr.json') as f:
        data = json.load(f)
    
    kpis = data.get('kpis', {})
    
    campos_kpi = [
        'ventas_periodo', 'ticket_promedio', 'cheques_total',
        'pax_total', 'pax_promedio', 'consumo_persona',
        'mesas_atendidas', 'rotacion_mesas', 'venta_por_hora'
    ]
    
    for campo in campos_kpi:
        assert campo in kpis, f"Falta KPI: {campo}"
    
    print("✅ TEST 2: KPIs base presentes")
    return True


def test_comparativos():
    """Valida que los comparativos estén presentes"""
    with open('/tmp/despues_dashboard_sr.json') as f:
        data = json.load(f)
    
    comparativo = data.get('comparativo', {})
    
    campos_comp = [
        'vs_periodo_anterior', 'vs_ano_anterior', 'vs_presupuesto',
        'pax_vs_mes_anterior', 'pax_vs_ano_anterior', 'pax_total_vs_ano',
        'cheques_total_vs_ano', 'cheque_vs_ano_anterior', 'rotacion_vs_ano'
    ]
    
    for campo in campos_comp:
        assert campo in comparativo, f"Falta comparativo: {campo}"
    
    print("✅ TEST 3: Comparativos presentes")
    return True


def test_idempotencia():
    """Valida que múltiples llamadas retornen lo mismo"""
    with open('/tmp/despues_dashboard_sr.json') as f:
        d1 = json.load(f)
    
    with open('/tmp/despues2_dashboard_sr.json') as f:
        d2 = json.load(f)
    
    # Comparar KPIs
    assert d1['kpis'] == d2['kpis'], "KPIs difieren entre llamadas"
    
    # Comparar comparativos
    assert d1['comparativo'] == d2['comparativo'], "Comparativos difieren"
    
    print("✅ TEST 4: Idempotencia verificada")
    return True


def test_tipos_datos():
    """Valida que los tipos de datos sean correctos"""
    with open('/tmp/despues_dashboard_sr.json') as f:
        data = json.load(f)
    
    kpis = data.get('kpis', {})
    
    # Verificar tipos numéricos
    assert isinstance(kpis.get('ventas_periodo'), (int, float)), "ventas_periodo debe ser numérico"
    assert isinstance(kpis.get('pax_total'), (int, float)), "pax_total debe ser numérico"
    assert isinstance(kpis.get('cheques_total'), (int, float)), "cheques_total debe ser numérico"
    
    print("✅ TEST 5: Tipos de datos correctos")
    return True


def run_all_tests():
    print("=" * 60)
    print("TEST DE PARIDAD - SUB-BLOQUE 5.1")
    print("=" * 60)
    print()
    
    tests = [
        test_estructura_respuesta,
        test_kpis_base,
        test_comparativos,
        test_idempotencia,
        test_tipos_datos
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"❌ {test.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__}: Error - {e}")
    
    print()
    print("=" * 60)
    print(f"Resultado: {passed}/{len(tests)} tests pasados")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
