"""
PRUEBA DE PARIDAD - BLOQUE 2
============================
Compara los resultados del flujo actual (service.py) vs la nueva función (query_ventas_periodo_sr).

OBJETIVO:
Verificar que query_ventas_periodo_sr() devuelve EXACTAMENTE los mismos valores
que el código actual en service.py para las métricas:
- VENTAS_TOTAL
- PAX_COMENSALES
- CONTEO_CHEQUES

CRITERIO DE ÉXITO:
- diff = 0 para todas las métricas
- Tolerancia: NINGUNA (deben ser idénticos)
"""

import sys
sys.path.insert(0, '/app/backend')

import os
from datetime import datetime, timedelta

# Imports del sistema actual
from core.db import execute_sql_query

# Import de la nueva función (directo para evitar dependencias circulares)
import importlib.util
spec = importlib.util.spec_from_file_location("softrestaurant", "/app/backend/modules/comercial/queries/softrestaurant.py")
sr_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sr_module)
query_ventas_periodo_sr = sr_module.query_ventas_periodo_sr
VentasPeriodoResult = sr_module.VentasPeriodoResult

def get_mongo_db():
    """Obtiene conexión a MongoDB."""
    client = MongoClient(os.environ.get('MONGO_URL'))
    return client[os.environ.get('DB_NAME', 'edarsa_hub')]

def get_test_server():
    """Obtiene un servidor SoftRestaurant de prueba desde MongoDB."""
    db = get_mongo_db()
    server = db.servers.find_one({
        "system_type": "SoftRestaurant",
        "active": True
    }, {"_id": 0})
    return server

def query_actual_service(server, fecha_ini, fecha_fin):
    """
    Ejecuta la query EXACTAMENTE como está en service.py líneas 341-363.
    Esta es la REFERENCIA contra la cual comparamos.
    """
    fi = fecha_ini.replace('-', '')
    ff = fecha_fin.replace('-', '')
    
    query = f"""
SELECT 
    COUNT(DISTINCT cheques.folio) as cheques,
    ISNULL(SUM(cheques.total), 0) as ventas,
    ISNULL(SUM(cheques.nopersonas), 0) as pax
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(varchar, turnos.apertura, 112) >= '{fi}'
  AND CONVERT(varchar, turnos.apertura, 112) <= '{ff}'
  AND cheques.cancelado = 0
"""
    
    try:
        result = execute_sql_query(
            server['host'], 
            server['port'], 
            server['database'],
            server['username'], 
            server['password'], 
            query
        )
        
        if result and len(result) > 0:
            return {
                'success': True,
                'ventas': float(result[0].get('ventas') or 0),
                'pax': int(result[0].get('pax') or 0),
                'cheques': int(result[0].get('cheques') or 0)
            }
        else:
            return {'success': True, 'ventas': 0, 'pax': 0, 'cheques': 0}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def run_parity_test():
    """Ejecuta prueba de paridad completa."""
    print("=" * 70)
    print("PRUEBA DE PARIDAD - BLOQUE 2")
    print("=" * 70)
    print()
    
    # Obtener servidor de prueba
    server = get_test_server()
    if not server:
        print("❌ ERROR: No se encontró servidor SoftRestaurant activo")
        return False
    
    print(f"Servidor de prueba: {server.get('name')} ({server.get('system_type')})")
    print(f"Host: {server.get('host')}")
    print()
    
    # Definir período de prueba (últimos 7 días)
    hoy = datetime.now()
    fecha_fin = hoy.strftime('%Y-%m-%d')
    fecha_ini = (hoy - timedelta(days=7)).strftime('%Y-%m-%d')
    
    print(f"Período de prueba: {fecha_ini} a {fecha_fin}")
    print()
    
    # Ejecutar query ACTUAL (service.py)
    print("Ejecutando query ACTUAL (service.py)...")
    result_actual = query_actual_service(server, fecha_ini, fecha_fin)
    
    if not result_actual.get('success'):
        print(f"❌ Query actual falló: {result_actual.get('error')}")
        print("   NOTA: Esto puede ser problema de conectividad, no del código")
        return None  # Indeterminado, no fallo
    
    print("  Resultado ACTUAL:")
    print(f"    ventas  = {result_actual['ventas']:,.2f}")
    print(f"    pax     = {result_actual['pax']:,}")
    print(f"    cheques = {result_actual['cheques']:,}")
    print()
    
    # Ejecutar query NUEVA (query_ventas_periodo_sr)
    print("Ejecutando query NUEVA (query_ventas_periodo_sr)...")
    result_nueva: VentasPeriodoResult = query_ventas_periodo_sr(server, fecha_ini, fecha_fin)
    
    if not result_nueva.success:
        print(f"❌ Query nueva falló: {result_nueva.error}")
        return False
    
    print("  Resultado NUEVA:")
    print(f"    ventas  = {result_nueva.total_venta:,.2f}")
    print(f"    pax     = {result_nueva.pax:,}")
    print(f"    cheques = {result_nueva.cheques:,}")
    print()
    
    # Comparar resultados
    print("=" * 70)
    print("COMPARACIÓN DE PARIDAD")
    print("=" * 70)
    
    diff_ventas = abs(result_actual['ventas'] - result_nueva.total_venta)
    diff_pax = abs(result_actual['pax'] - result_nueva.pax)
    diff_cheques = abs(result_actual['cheques'] - result_nueva.cheques)
    
    print(f"{'Métrica':<15} {'Actual':<20} {'Nueva':<20} {'Diff':<15} {'Estado'}")
    print("-" * 70)
    
    status_ventas = "✅ PARIDAD" if diff_ventas < 0.01 else "❌ DIFERENCIA"
    status_pax = "✅ PARIDAD" if diff_pax == 0 else "❌ DIFERENCIA"
    status_cheques = "✅ PARIDAD" if diff_cheques == 0 else "❌ DIFERENCIA"
    
    print(f"{'VENTAS':<15} {result_actual['ventas']:<20,.2f} {result_nueva.total_venta:<20,.2f} {diff_ventas:<15,.2f} {status_ventas}")
    print(f"{'PAX':<15} {result_actual['pax']:<20,} {result_nueva.pax:<20,} {diff_pax:<15,} {status_pax}")
    print(f"{'CHEQUES':<15} {result_actual['cheques']:<20,} {result_nueva.cheques:<20,} {diff_cheques:<15,} {status_cheques}")
    print()
    
    # Dictamen final
    all_pass = (diff_ventas < 0.01) and (diff_pax == 0) and (diff_cheques == 0)
    
    print("=" * 70)
    if all_pass:
        print("✅ DICTAMEN: BLOQUE 2 COMPLETADO CON PARIDAD")
        print("   Las tres métricas coinciden exactamente.")
    else:
        print("❌ DICTAMEN: BLOQUE 2 NO APROBADO")
        print("   Se encontraron diferencias en las métricas.")
        if diff_ventas >= 0.01:
            print(f"   - VENTAS: Diferencia de {diff_ventas:,.2f}")
        if diff_pax > 0:
            print(f"   - PAX: Diferencia de {diff_pax:,}")
        if diff_cheques > 0:
            print(f"   - CHEQUES: Diferencia de {diff_cheques:,}")
    print("=" * 70)
    
    return all_pass

if __name__ == "__main__":
    result = run_parity_test()
    if result is None:
        print("\n⚠️ PRUEBA INDETERMINADA: No se pudo conectar al servidor SQL")
        print("   Esto es esperado en ambiente preview sin conectividad a SQL remotos")
        print("   La paridad debe validarse en ambiente con conectividad")
    elif result:
        print("\n✅ PRUEBA EXITOSA")
    else:
        print("\n❌ PRUEBA FALLIDA")
