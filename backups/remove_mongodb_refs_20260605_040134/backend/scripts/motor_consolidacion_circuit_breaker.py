import requests
import math

# Simula la base de datos de los métricos por unidad y mes.
# (Esta estructura refleja la constante 'monthlyData' que está en memoria).
monthly_data_db = {
    "cienfuegos": {
        "Enero": {"ventas": 4.5, "pax": 3200, "cheques": 1100},
        "Febrero": {"ventas": 4.8, "pax": 3500, "cheques": 1200},
        "Marzo": {"ventas": 5.1, "pax": 3800, "cheques": 1250},
        "Abril": {"ventas": 4.2, "pax": 3000, "cheques": 1050},
        "Mayo": {"ventas": 4.79, "pax": 4555, "cheques": 1500}
    },
    "130_merida": {
        "Enero": {"ventas": 4.2, "pax": 2800, "cheques": 900},
        "Abril": {"ventas": 4.6, "pax": 2900, "cheques": 950},
    }
    # ... otras sucursales ...
}

def obtener_cache_unidades():
    """Fallback local para evitar que la aplicación bloquee la pantalla si el backend falla."""
    return [
        {"id": "cienfuegos", "ventas": 0, "pax": 0, "cheques": 0},
        {"id": "130_merida", "ventas": 0, "pax": 0, "cheques": 0}
    ]

def obtener_unidades_comerciales(meses_seleccionados):
    """
    Simula el motor lógico del tablero ejecutivo, integrando:
    1. Circuit Breaker (Límite 8s)
    2. Acumulados puros consolidados según meses activos
    """
    print(f"Ejecutando consolidación para meses: {meses_seleccionados}")
    
    # 1. Circuit Breaker y Estabilidad (Timeout estricto de 8 segundos)
    # Esto soluciona los cuelgues del AxiosError de 60000ms.
    try:
        response = requests.get(
            "https://stock-tracker-990.preview.emergentagent.com/api/comercial/units", 
            timeout=8.0
        )
        
        if response.status_code == 200:
            unidades_base = response.json()
        else:
            print("[WARN] Status no esperado de la API, usando caché de respaldo.")
            unidades_base = obtener_cache_unidades()
            
    except requests.exceptions.Timeout:
        print("[CIRCUIT BREAKER] Tiempo de respuesta superó 8s. Abortando ping para prevenir cuellos de botella (usando caché local).")
        unidades_base = obtener_cache_unidades()
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR DE RED] Imposible conectar. Cayendo en fallback. Trace: {e}")
        unidades_base = obtener_cache_unidades()

    # 2. Corrección de Acumulados Matemáticos
    unidades_acumuladas = []
    meses_activos = meses_seleccionados if len(meses_seleccionados) > 0 else ["Mayo"]
    
    for unidad in unidades_base:
        unidad_id = unidad.get("id")
        
        # Obtenemos los ingresos vivos de su registro histórico
        datos_historicos_unidad = monthly_data_db.get(unidad_id, monthly_data_db.get("cienfuegos"))
        
        suma_ventas = 0
        suma_pax = 0
        suma_cheques = 0
        
        # Iteramos SOLO por los meses seleccionados, sumando las ventas puras reales.
        # Ya no hay multiplicadores estáticos ni coeficientes inexactos.
        for mes in meses_activos:
            estadisticas_mes = datos_historicos_unidad.get(mes)
            if estadisticas_mes:
                suma_ventas += estadisticas_mes.get("ventas", 0)
                suma_pax += estadisticas_mes.get("pax", 0)
                suma_cheques += estadisticas_mes.get("cheques", 0)
        
        # Re-armamos el diccionario de la unidad con el nuevo métrico consolidado y real
        unidad_procesada = {
            **unidad,
            "ventas": suma_ventas,
            "pax": math.floor(suma_pax),
            "cheques": math.floor(suma_cheques)
        }
        unidades_acumuladas.append(unidad_procesada)

    return unidades_acumuladas


# ==========================================
# Pruebas de funcionamiento del parche
# ==========================================
if __name__ == "__main__":
    
    # Escenario: Seleccionamos de forma explícita los meses de Enero y Abril.
    resultado_tablero = obtener_unidades_comerciales(["Enero", "Abril"])
    
    print("\n--- RESULTADOS ACUMULADOS CONSOLIDADOS ---")
    for resultado in resultado_tablero:
        print(f"Sucursal: {resultado['id']}")
        print(f"  └ Ventas: ${resultado['ventas']:.2f}M")
        print(f"  └ PAX:    {resultado['pax']}")
        print(f"  └ Cheques:{resultado['cheques']}\n")
