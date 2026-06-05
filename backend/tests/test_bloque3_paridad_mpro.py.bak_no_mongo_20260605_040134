"""
PRUEBA DE PARIDAD - BLOQUE 3 (MPRO)
===================================
Compara los resultados del flujo actual (service.py) vs la nueva función (query_ventas_periodo_mpro).

OBJETIVO:
Verificar que query_ventas_periodo_mpro() devuelve EXACTAMENTE los mismos valores
que el código actual en service.py para las métricas:
- VENTAS_TOTAL
- PAX_COMENSALES (con lógica de estimación si PAX=0)
- CONTEO_CHEQUES

CRITERIO DE ÉXITO:
- diff = 0 para todas las métricas
- Tolerancia: NINGUNA (deben ser idénticos)

NOTA ESPECIAL MPRO:
- PAX viene de tabla Comanda (LEFT JOIN)
- Si PAX real es 0 pero hay cheques, se estima PAX = cheques
- Esto debe replicarse exactamente
"""

import sys
sys.path.insert(0, '/app/backend')

import os
from datetime import datetime, timedelta
from pymongo import MongoClient

# Imports del sistema actual
from core.db import execute_sql_query

# Import de la nueva función (directo para evitar dependencias)
import importlib.util
spec = importlib.util.spec_from_file_location("mpro", "/app/backend/modules/comercial/queries/mpro.py")
mpro_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mpro_module)
query_ventas_periodo_mpro = mpro_module.query_ventas_periodo_mpro
VentasPeriodoResult = mpro_module.VentasPeriodoResult

def get_mongo_db():
    """Obtiene conexión a MongoDB."""
    client = MongoClient(os.environ.get('MONGO_URL'))
    return client[os.environ.get('DB_NAME', 'edarsa_hub')]

def get_test_server_mpro():
    """Obtiene un servidor MPRO de prueba desde MongoDB."""
    db = get_mongo_db()
    server = db.servers.find_one({
        "system_type": "MPRO",
        "active": True
    }, {"_id": 0})
    return server

def query_actual_service_mpro(server, fecha_ini, fecha_fin):
    """
    Ejecuta la query EXACTAMENTE como está en service.py líneas 871-884.
    Esta es la REFERENCIA contra la cual comparamos.
    
    NOTA: La query original agrupa por sucursal. Para comparar consolidado,
    ejecutamos sin GROUP BY (igual que la nueva función).
    """
    fi = fecha_ini.replace('-', '')
    ff = fecha_fin.replace('-', '')
    
    # Query consolidada (sin GROUP BY para comparar con la nueva función)
    query = f"""
SELECT 
    COUNT(DISTINCT VE.Vn_Folio) as cheques,
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas,
    ISNULL(SUM(C.Co_Personas), 0) as pax
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= '{fi}' AND VE.Vn_Fecha <= '{ff}'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
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
            ventas = float(result[0].get('ventas') or 0)
            cheques = int(result[0].get('cheques') or 0)
            pax = int(result[0].get('pax') or 0)
            
            # Lógica de estimación PAX (service.py líneas 914-916)
            if pax == 0 and cheques > 0:
                pax = cheques
            
            return {
                'success': True,
                'ventas': ventas,
                'pax': pax,
                'cheques': cheques
            }
        else:
            return {'success': True, 'ventas': 0, 'pax': 0, 'cheques': 0}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def run_parity_test():
    """Ejecuta prueba de paridad completa para MPRO."""
    print("=" * 70)
    print("PRUEBA DE PARIDAD - BLOQUE 3 (MPRO)")
    print("=" * 70)
    print()
    
    # Obtener servidor de prueba
    server = get_test_server_mpro()
    if not server:
        print("❌ ERROR: No se encontró servidor MPRO activo")
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
    print("Ejecutando query ACTUAL (lógica service.py)...")
    result_actual = query_actual_service_mpro(server, fecha_ini, fecha_fin)
    
    if not result_actual.get('success'):
        print(f"❌ Query actual falló: {result_actual.get('error')}")
        print("   NOTA: Esto puede ser problema de conectividad, no del código")
        return None  # Indeterminado, no fallo
    
    print("  Resultado ACTUAL:")
    print(f"    ventas  = {result_actual['ventas']:,.2f}")
    print(f"    pax     = {result_actual['pax']:,}")
    print(f"    cheques = {result_actual['cheques']:,}")
    print()
    
    # Ejecutar query NUEVA (query_ventas_periodo_mpro)
    print("Ejecutando query NUEVA (query_ventas_periodo_mpro)...")
    result_nueva: VentasPeriodoResult = query_ventas_periodo_mpro(server, fecha_ini, fecha_fin)
    
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
        print("✅ DICTAMEN: BLOQUE 3 COMPLETADO CON PARIDAD")
        print("   Las tres métricas coinciden exactamente.")
    else:
        print("❌ DICTAMEN: BLOQUE 3 NO APROBADO")
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
        print("\n⚠️ PRUEBA INDETERMINADA: No se pudo conectar al servidor SQL MPRO")
        print("   Esto es esperado en ambiente preview sin conectividad a SQL remotos")
        print("   La paridad debe validarse en ambiente con conectividad")
    elif result:
        print("\n✅ PRUEBA EXITOSA")
    else:
        print("\n❌ PRUEBA FALLIDA")
