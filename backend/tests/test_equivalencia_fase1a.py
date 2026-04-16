#!/usr/bin/env python3
"""
Test de Equivalencia - Fase 1A
CAB-003: Automatización de Análisis de Inventarios

Este script verifica que el Core Service produce resultados
IDÉNTICOS al endpoint HTTP.

Criterios Obligatorios:
1. Estructura válida
2. Mismo count
3. Mismo número de registros
4. Mismas llaves por registro
5. Mismos totales críticos

Evidencia Adicional:
- Hash SHA256
- Orden de registros
"""

import json
import hashlib
import sys
from typing import Dict, List, Any


def validar_estructura_basica(data: Dict) -> Dict[str, Any]:
    """Criterio 1: Estructura válida."""
    errores = []
    
    if "data" not in data:
        errores.append("Campo 'data' no existe")
    elif not isinstance(data["data"], list):
        errores.append("Campo 'data' no es una lista")
    
    if "count" not in data:
        errores.append("Campo 'count' no existe")
    elif not isinstance(data["count"], int):
        errores.append("Campo 'count' no es entero")
    
    return {"valido": len(errores) == 0, "errores": errores}


def validar_counts(antes: Dict, despues: Dict) -> Dict[str, Any]:
    """Criterio 2: Mismo count."""
    count_antes = antes.get("count", -1)
    count_despues = despues.get("count", -1)
    
    return {
        "valido": count_antes == count_despues,
        "count_antes": count_antes,
        "count_despues": count_despues,
        "errores": [] if count_antes == count_despues else [
            f"count diferente: ANTES={count_antes}, DESPUÉS={count_despues}"
        ]
    }


def validar_numero_registros(antes: Dict, despues: Dict) -> Dict[str, Any]:
    """Criterio 3: Mismo número de registros."""
    len_antes = len(antes.get("data", []))
    len_despues = len(despues.get("data", []))
    
    return {
        "valido": len_antes == len_despues,
        "registros_antes": len_antes,
        "registros_despues": len_despues,
        "errores": [] if len_antes == len_despues else [
            f"Número de registros diferente: ANTES={len_antes}, DESPUÉS={len_despues}"
        ]
    }


def validar_llaves_todos_registros(antes: Dict, despues: Dict) -> Dict[str, Any]:
    """Criterio 4: Mismas llaves por registro (en TODOS los registros)."""
    items_antes = antes.get("data", [])
    items_despues = despues.get("data", [])
    errores = []
    
    if not items_antes and not items_despues:
        return {"valido": True, "errores": []}
    
    llaves_ref_antes = set(items_antes[0].keys()) if items_antes else set()
    llaves_ref_despues = set(items_despues[0].keys()) if items_despues else set()
    
    if llaves_ref_antes != llaves_ref_despues:
        errores.append(f"Llaves de referencia diferentes")
        errores.append(f"  Solo en ANTES: {sorted(llaves_ref_antes - llaves_ref_despues)}")
        errores.append(f"  Solo en DESPUÉS: {sorted(llaves_ref_despues - llaves_ref_antes)}")
    
    for idx, item in enumerate(items_antes):
        if set(item.keys()) != llaves_ref_antes:
            errores.append(f"ANTES registro {idx}: llaves inconsistentes")
            break
    
    for idx, item in enumerate(items_despues):
        if set(item.keys()) != llaves_ref_despues:
            errores.append(f"DESPUÉS registro {idx}: llaves inconsistentes")
            break
    
    return {
        "valido": len(errores) == 0,
        "llaves": sorted(llaves_ref_antes) if llaves_ref_antes == llaves_ref_despues else None,
        "errores": errores
    }


def validar_totales_criticos(antes: Dict, despues: Dict) -> Dict[str, Any]:
    """Criterio 5: Mismos totales críticos."""
    
    def calcular_totales(data: Dict) -> Dict[str, float]:
        items = data.get("data", [])
        return {
            "suma_inv_inicial": round(sum(float(i.get("Inv_Inicial_Cantidad", 0) or 0) for i in items), 2),
            "suma_inv_final": round(sum(float(i.get("Inv_Final_Cantidad", 0) or 0) for i in items), 2),
            "suma_movimientos": round(sum(float(i.get("Movimientos", 0) or 0) for i in items), 2),
            "suma_ventas": round(sum(float(i.get("Ventas", 0) or 0) for i in items), 2),
            "suma_diferencia_cantidad": round(sum(float(i.get("Diferencia_Cantidad", 0) or 0) for i in items), 2),
            "suma_diferencia_costo": round(sum(float(i.get("Diferencia_Costo", 0) or 0) for i in items), 2),
        }
    
    totales_antes = calcular_totales(antes)
    totales_despues = calcular_totales(despues)
    
    errores = []
    for key in totales_antes:
        if totales_antes[key] != totales_despues[key]:
            errores.append(f"{key}: ANTES={totales_antes[key]}, DESPUÉS={totales_despues[key]}")
    
    return {
        "valido": len(errores) == 0,
        "totales_antes": totales_antes,
        "totales_despues": totales_despues,
        "errores": errores
    }


def validar_orden(antes: Dict, despues: Dict) -> Dict[str, Any]:
    """Evidencia adicional: Mismo orden de registros."""
    items_antes = antes.get("data", [])
    items_despues = despues.get("data", [])
    
    codigos_antes = [item.get("Codigo", "") for item in items_antes]
    codigos_despues = [item.get("Codigo", "") for item in items_despues]
    
    errores = []
    if codigos_antes != codigos_despues:
        for i, (c_a, c_d) in enumerate(zip(codigos_antes, codigos_despues)):
            if c_a != c_d:
                errores.append(f"Orden difiere en posición {i}: ANTES='{c_a}', DESPUÉS='{c_d}'")
                break
    
    return {"valido": codigos_antes == codigos_despues, "errores": errores}


def calcular_hash(data: Dict) -> str:
    """Evidencia adicional: Hash SHA256."""
    normalized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(normalized.encode()).hexdigest()


def comparar_respuestas(antes_path: str, despues_path: str) -> Dict[str, Any]:
    """Ejecuta todas las validaciones."""
    
    with open(antes_path, 'r') as f:
        antes = json.load(f)
    with open(despues_path, 'r') as f:
        despues = json.load(f)
    
    print("=" * 70)
    print("PRUEBA DE EQUIVALENCIA - FASE 1A")
    print("=" * 70)
    print("")
    
    criterios_obligatorios = []
    
    # Criterio 1
    print("CRITERIO 1: Estructura válida")
    print("-" * 50)
    est_antes = validar_estructura_basica(antes)
    est_despues = validar_estructura_basica(despues)
    c1_valido = est_antes["valido"] and est_despues["valido"]
    criterios_obligatorios.append(("Estructura válida", c1_valido))
    print(f"   ANTES:   {'✅' if est_antes['valido'] else '❌'}")
    print(f"   DESPUÉS: {'✅' if est_despues['valido'] else '❌'}")
    print("")
    
    # Criterio 2
    print("CRITERIO 2: Mismo count")
    print("-" * 50)
    c2 = validar_counts(antes, despues)
    criterios_obligatorios.append(("Mismo count", c2["valido"]))
    print(f"   ANTES:   {c2['count_antes']}")
    print(f"   DESPUÉS: {c2['count_despues']}")
    print(f"   {'✅ Iguales' if c2['valido'] else '❌ Diferentes'}")
    print("")
    
    # Criterio 3
    print("CRITERIO 3: Mismo número de registros")
    print("-" * 50)
    c3 = validar_numero_registros(antes, despues)
    criterios_obligatorios.append(("Mismo número de registros", c3["valido"]))
    print(f"   ANTES:   {c3['registros_antes']}")
    print(f"   DESPUÉS: {c3['registros_despues']}")
    print(f"   {'✅ Iguales' if c3['valido'] else '❌ Diferentes'}")
    print("")
    
    # Criterio 4
    print("CRITERIO 4: Mismas llaves por registro")
    print("-" * 50)
    c4 = validar_llaves_todos_registros(antes, despues)
    criterios_obligatorios.append(("Mismas llaves", c4["valido"]))
    if c4["valido"]:
        print(f"   ✅ {len(c4['llaves'])} llaves consistentes")
    else:
        for err in c4["errores"]:
            print(f"   ❌ {err}")
    print("")
    
    # Criterio 5
    print("CRITERIO 5: Mismos totales críticos")
    print("-" * 50)
    c5 = validar_totales_criticos(antes, despues)
    criterios_obligatorios.append(("Mismos totales críticos", c5["valido"]))
    for key in c5["totales_antes"]:
        val_a = c5["totales_antes"][key]
        val_d = c5["totales_despues"][key]
        estado = "✅" if val_a == val_d else "❌"
        print(f"   {estado} {key}: {val_a}" + (f" vs {val_d}" if val_a != val_d else ""))
    print("")
    
    # Evidencia adicional
    print("=" * 70)
    print("EVIDENCIA ADICIONAL")
    print("=" * 70)
    print("")
    
    print("Orden de registros:")
    orden = validar_orden(antes, despues)
    print(f"   {'✅ Orden idéntico' if orden['valido'] else '❌ Orden diferente'}")
    print("")
    
    print("Hash SHA256:")
    hash_antes = calcular_hash(antes)
    hash_despues = calcular_hash(despues)
    print(f"   ANTES:   {hash_antes[:32]}...")
    print(f"   DESPUÉS: {hash_despues[:32]}...")
    print(f"   {'✅ Idénticos' if hash_antes == hash_despues else '⚠️  Diferentes'}")
    print("")
    
    # Resultado final
    print("=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)
    print("")
    
    todos_pasan = all(valido for _, valido in criterios_obligatorios)
    
    for nombre, valido in criterios_obligatorios:
        print(f"   {'✅' if valido else '❌'} {nombre}")
    
    print("")
    if todos_pasan:
        print("   " + "=" * 60)
        print("   ✅ FASE 1A APROBADA - Todos los criterios obligatorios pasan")
        print("   " + "=" * 60)
    else:
        print("   " + "=" * 60)
        print("   ❌ FASE 1A NO APROBADA - EJECUTAR ROLLBACK INMEDIATO")
        print("   " + "=" * 60)
    
    return {"aprobado": todos_pasan}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python test_equivalencia_fase1a.py <antes.json> <despues.json>")
        sys.exit(1)
    
    resultado = comparar_respuestas(sys.argv[1], sys.argv[2])
    sys.exit(0 if resultado["aprobado"] else 1)
