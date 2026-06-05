"""
VALIDACIONES POST-CARGA - FASE 2.3
===================================
Ejecutar DESPUÉS de la carga histórica para verificar integridad.

Uso:
    python3 validar_post_carga.py

Criterios de éxito:
    - Duplicados = 0
    - Registros originales >= 38 (intactos)
    - Rango de fechas cubre ~24 meses
"""

import os
import sys
from datetime import datetime
from pymongo import MongoClient

# Configuración
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'edarsa_hub')
CARGA_MARKER = 'carga_historica_fase23'


def main():
    print("=" * 60)
    print("VALIDACIONES POST-CARGA - FASE 2.3")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    
    validaciones_ok = True
    
    # 1. DUPLICADOS (CRÍTICO)
    print("\n1. VERIFICACIÓN DE DUPLICADOS")
    pipeline = [
        {"$group": {
            "_id": {
                "server_id": "$server_id",
                "empresa_id": "$empresa_id",
                "sucursal_id": "$sucursal_id",
                "fecha": "$fecha"
            },
            "count": {"$sum": 1}
        }},
        {"$match": {"count": {"$gt": 1}}}
    ]
    duplicados = list(db.kpis_comercial.aggregate(pipeline))
    
    if len(duplicados) == 0:
        print("   ✅ PASS - Duplicados: 0")
    else:
        print(f"   ❌ FAIL - Duplicados: {len(duplicados)}")
        print("   ⚠️  REQUIERE ROLLBACK INMEDIATO")
        validaciones_ok = False
        for dup in duplicados[:5]:
            print(f"      - {dup['_id']}: {dup['count']} copias")
    
    # 2. CONTEO DE DOCUMENTOS
    print("\n2. CONTEO DE DOCUMENTOS")
    total = db.kpis_comercial.count_documents({})
    nuevos = db.kpis_comercial.count_documents({"created_by": CARGA_MARKER})
    originales = total - nuevos
    
    print(f"   Total documentos: {total}")
    print(f"   Nuevos (carga): {nuevos}")
    print(f"   Originales: {originales}")
    
    if originales >= 38:
        print("   ✅ PASS - Originales intactos (>= 38)")
    else:
        print("   ❌ FAIL - Originales afectados (< 38)")
        validaciones_ok = False
    
    # 3. RANGO DE FECHAS
    print("\n3. RANGO DE FECHAS")
    min_doc = db.kpis_comercial.find_one(sort=[("fecha", 1)])
    max_doc = db.kpis_comercial.find_one(sort=[("fecha", -1)])
    
    fecha_min = min_doc.get('fecha') if min_doc else 'N/A'
    fecha_max = max_doc.get('fecha') if max_doc else 'N/A'
    
    print(f"   Fecha mínima: {fecha_min}")
    print(f"   Fecha máxima: {fecha_max}")
    
    # Verificar cobertura aproximada de 24 meses
    if fecha_min != 'N/A' and fecha_max != 'N/A':
        from datetime import datetime as dt
        try:
            f_min = dt.strptime(fecha_min, '%Y-%m-%d')
            f_max = dt.strptime(fecha_max, '%Y-%m-%d')
            meses = (f_max.year - f_min.year) * 12 + (f_max.month - f_min.month)
            print(f"   Meses cubiertos: ~{meses}")
            if meses >= 20:
                print("   ✅ PASS - Cobertura >= 20 meses")
            else:
                print("   🟡 PARCIAL - Cobertura < 20 meses")
        except Exception:
            print("   ⚠️  No se pudo calcular cobertura")
    
    # 4. DOCUMENTOS POR SERVIDOR
    print("\n4. DOCUMENTOS POR SERVIDOR (nuevos)")
    pipeline_srv = [
        {"$match": {"created_by": CARGA_MARKER}},
        {"$group": {"_id": "$server_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    servidores = list(db.kpis_comercial.aggregate(pipeline_srv))
    
    if servidores:
        for srv in servidores:
            print(f"   {srv['_id'][:20]}...: {srv['count']}")
        print(f"   ✅ {len(servidores)} servidor(es) con datos")
    else:
        print("   ⚠️  Sin documentos nuevos")
    
    # 5. DOCUMENTOS POR ESTADO
    print("\n5. DOCUMENTOS POR ESTADO")
    pipeline_estado = [
        {"$group": {"_id": "$estado_periodo", "count": {"$sum": 1}}}
    ]
    estados = list(db.kpis_comercial.aggregate(pipeline_estado))
    
    for e in estados:
        estado = e['_id'] or 'NULL'
        print(f"   {estado}: {e['count']}")
    
    # 6. VERIFICACIÓN DE IDEMPOTENCIA
    print("\n6. TEST DE IDEMPOTENCIA")
    print("   (Re-ejecutar carga y verificar duplicados = 0)")
    print("   Estado: Pendiente de verificación manual")
    
    # DICTAMEN FINAL
    print("\n" + "=" * 60)
    print("DICTAMEN FINAL")
    print("=" * 60)
    
    if len(duplicados) > 0:
        print("\n❌ FASE 2.3 NO APROBADA - DUPLICADOS DETECTADOS")
        print("   Acción: Ejecutar ROLLBACK inmediato")
        resultado = "ROLLBACK"
    elif not validaciones_ok:
        print("\n❌ FASE 2.3 NO APROBADA - VALIDACIÓN FALLIDA")
        print("   Acción: Revisar errores y considerar rollback")
        resultado = "FALLIDA"
    elif nuevos == 0:
        print("\n🟡 FASE 2.3 SIN DATOS NUEVOS")
        print("   Posible causa: Servidores sin conectividad")
        resultado = "SIN_DATOS"
    elif len(servidores) < 8:
        print(f"\n🟡 FASE 2.3 COMPLETADA CON OBSERVACIONES")
        print(f"   Servidores procesados: {len(servidores)}/8")
        resultado = "PARCIAL"
    else:
        print("\n✅ FASE 2.3 COMPLETADA EXITOSAMENTE")
        print(f"   Documentos nuevos: {nuevos}")
        print(f"   Servidores: {len(servidores)}")
        resultado = "EXITOSA"
    
    print("\n" + "=" * 60)
    
    client.close()
    
    return 0 if resultado in ["EXITOSA", "PARCIAL"] else 1


if __name__ == "__main__":
    sys.exit(main())
