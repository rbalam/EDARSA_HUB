"""
PRECHECK DE CONECTIVIDAD - FASE 2.3
====================================
Ejecutar ANTES de la carga histórica para verificar conectividad
de cada servidor según su configuración en el menú de Servidores.

Uso:
    python3 precheck_conectividad.py

Requisitos:
    - Variable MONGO_URL configurada
    - Variable DB_NAME configurada (default: edarsa_hub)
    - Acceso a la colección 'servers' en MongoDB
"""

import os
import sys
import json
from datetime import datetime
from pymongo import MongoClient

# Configuración
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'edarsa_hub')

def main():
    print("=" * 70)
    print("PRECHECK DE CONECTIVIDAD - FASE 2.3")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Conectar a MongoDB
    try:
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        client.server_info()  # Forzar conexión
        db = client[DB_NAME]
        print(f"\n✅ MongoDB conectado: {DB_NAME}")
    except Exception as e:
        print(f"\n❌ Error conectando a MongoDB: {e}")
        return 1
    
    # Obtener servidores
    servidores = list(db.servers.find({
        "system_type": {"$in": ["SoftRestaurant", "MPRO"]}
    }))
    
    print(f"Servidores a verificar: {len(servidores)}\n")
    
    if not servidores:
        print("❌ No se encontraron servidores configurados")
        return 1
    
    # Verificar cada servidor
    elegibles = 0
    resultados = []
    
    print("-" * 70)
    print(f"{'SERVIDOR':<25} | {'TIPO':<15} | {'ESTADO':<12} | OBSERVACIÓN")
    print("-" * 70)
    
    for srv in servidores:
        nombre = srv.get('name', 'SIN NOMBRE')
        tipo = srv.get('system_type', 'DESCONOCIDO')
        host = srv.get('host', '')
        port = srv.get('port', '')
        database = srv.get('database', '')
        username = srv.get('username', '')
        password = srv.get('password', '')
        
        estado = "PENDIENTE"
        observacion = ""
        elegible = False
        
        # Verificar configuración
        if not all([host, port, database, username, password]):
            estado = "INCOMPLETO"
            campos_faltantes = []
            if not host: campos_faltantes.append('host')
            if not port: campos_faltantes.append('port')
            if not database: campos_faltantes.append('database')
            if not username: campos_faltantes.append('username')
            if not password: campos_faltantes.append('password')
            observacion = f"Faltan: {', '.join(campos_faltantes)}"
        else:
            # Intentar conexión SQL
            try:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from core.db import execute_sql_query
                
                result = execute_sql_query(
                    host, port, database, username, password,
                    "SELECT 1 as test",
                    timeout=15
                )
                
                if result is not None:
                    estado = "OK"
                    elegible = True
                    elegibles += 1
                    observacion = "Conexión exitosa"
                else:
                    estado = "SIN_DATOS"
                    observacion = "Query sin respuesta"
                    
            except Exception as e:
                estado = "FAIL"
                error = str(e).lower()
                if "timeout" in error or "timed out" in error:
                    observacion = "Timeout - no accesible"
                elif "login" in error or "password" in error:
                    observacion = "Error autenticación"
                elif "connection" in error:
                    observacion = "Sin conectividad de red"
                elif "database" in error:
                    observacion = "BD no existe/sin acceso"
                else:
                    observacion = str(e)[:40]
        
        print(f"{nombre:<25} | {tipo:<15} | {estado:<12} | {observacion}")
        
        resultados.append({
            "servidor": nombre,
            "tipo_sistema": tipo,
            "host": f"{host}:{port}",
            "estado": estado,
            "observacion": observacion,
            "elegible": elegible
        })
    
    print("-" * 70)
    
    # Resumen
    total = len(resultados)
    ok = sum(1 for r in resultados if r['estado'] == 'OK')
    fail = sum(1 for r in resultados if r['estado'] == 'FAIL')
    incompleto = sum(1 for r in resultados if r['estado'] == 'INCOMPLETO')
    
    print(f"\nRESUMEN:")
    print(f"  Total: {total}")
    print(f"  OK: {ok}")
    print(f"  FAIL: {fail}")
    print(f"  INCOMPLETO: {incompleto}")
    print(f"  ELEGIBLES: {elegibles}")
    
    # Recomendación
    print("\n" + "=" * 70)
    print("RECOMENDACIÓN OPERATIVA")
    print("=" * 70)
    
    if elegibles == total:
        print("\n✅ EJECUTAR CARGA TOTAL")
        print(f"   Todos los {total} servidores tienen conectividad OK.")
        recomendacion = "TOTAL"
    elif elegibles > 0:
        print(f"\n🟡 EJECUTAR CARGA PARCIAL CONTROLADA")
        print(f"   {elegibles}/{total} servidores elegibles.")
        print("\n   Servidores a INCLUIR:")
        for r in resultados:
            if r['elegible']:
                print(f"     ✅ {r['servidor']}")
        print("\n   Servidores a EXCLUIR:")
        for r in resultados:
            if not r['elegible']:
                print(f"     ❌ {r['servidor']}: {r['observacion']}")
        recomendacion = "PARCIAL"
    else:
        print("\n❌ POSPONER CARGA")
        print("   Ningún servidor tiene conectividad OK.")
        print("\n   Servidores con problemas:")
        for r in resultados:
            print(f"     - {r['servidor']}: {r['observacion']}")
        recomendacion = "POSPONER"
    
    print("\n" + "=" * 70)
    
    # Guardar resultados
    output = {
        "timestamp": datetime.now().isoformat(),
        "total": total,
        "elegibles": elegibles,
        "recomendacion": recomendacion,
        "servidores": resultados
    }
    
    output_file = f"/tmp/precheck_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nResultados guardados: {output_file}")
    
    client.close()
    
    # Código de salida
    if recomendacion == "POSPONER":
        return 2  # No elegibles
    elif recomendacion == "PARCIAL":
        return 1  # Parcial
    else:
        return 0  # Total OK


if __name__ == "__main__":
    sys.exit(main())
